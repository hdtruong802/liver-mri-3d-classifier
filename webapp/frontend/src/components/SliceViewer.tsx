/**
 * MRI viewer for the exact E4 crop space. The server renders one composed PNG
 * in a fixed order: MRI → predicted-class sensitivity heatmap → human label.
 * No raw-NIfTI overlay is allowed here because E4 aligns each phase separately.
 */

import { useCallback, useEffect, useMemo, useRef, useState, type PointerEvent } from 'react';
import { ChevronLeft, ChevronRight, Flame, Maximize2, Scan, Target } from 'lucide-react';

import { modelViewUrl, sliceUrl } from '@/api/client';
import type { CaseVolumeInfo, ModelHeatmapInfo, PhaseInfo } from '@/api/types';
import { EmptyState } from '@/components/Provenance';

interface Props {
  caseId: string;
  phases: PhaseInfo[];
  modelHeatmap: ModelHeatmapInfo | null;
  volumes: CaseVolumeInfo[];
}

const MIN_SCALE = 1;
const MAX_SCALE = 8;

function toSegments(indices: number[]): Array<[number, number]> {
  const sorted = [...indices].sort((a, b) => a - b);
  const segments: Array<[number, number]> = [];
  for (const index of sorted) {
    const last = segments[segments.length - 1];
    if (last && index === last[1] + 1) last[1] = index;
    else segments.push([index, index]);
  }
  return segments;
}

export function SliceViewer({ caseId, phases, modelHeatmap, volumes }: Props) {
  const hasModelHeatmap = modelHeatmap?.available === true;
  const volumeByToken = useMemo(
    () => new Map(volumes.map((volume) => [volume.file_token, volume])),
    [volumes],
  );
  const available = useMemo(
    () =>
      hasModelHeatmap
        ? phases.filter((phase) => modelHeatmap?.phase_tokens.includes(phase.file_token) ?? false)
        : phases.filter((phase) => volumeByToken.has(phase.file_token)),
    [hasModelHeatmap, modelHeatmap, phases, volumeByToken],
  );
  const [token, setToken] = useState('C-pre');
  const activeVolume = volumeByToken.get(token);
  const total = hasModelHeatmap ? modelHeatmap?.n_slices ?? 0 : activeVolume?.n_slices ?? 0;
  const [z, setZ] = useState(0);
  const [failed, setFailed] = useState(false);
  const [showAnnotation, setShowAnnotation] = useState(false);
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });

  const frameRef = useRef<HTMLDivElement>(null);
  const dragging = useRef(false);
  const initialSliceSet = useRef(false);
  const dragOrigin = useRef({ x: 0, y: 0, offset: { x: 0, y: 0 } });

  useEffect(() => {
    initialSliceSet.current = false;
  }, [caseId]);

  useEffect(() => {
    if (available.some((phase) => phase.file_token === token)) return;
    setToken(available.find((phase) => phase.file_token === 'C-pre')?.file_token ?? available[0]?.file_token ?? '');
  }, [available, token]);

  const clamp = useCallback((value: number) => Math.max(0, Math.min(total - 1, value)), [total]);
  const step = useCallback((delta: number) => setZ((current) => clamp(current + delta)), [clamp]);

  const lesionSlices = hasModelHeatmap
    ? modelHeatmap?.lesion_slices[token] ?? []
    : activeVolume?.mask_slices ?? [];
  const segments = useMemo(() => toSegments(lesionSlices), [lesionSlices]);
  const firstLesionSlice = lesionSlices[0] ?? null;

  // The first usable view opens at the longest C-pre annotation span. Switching
  // phase preserves z: all eight artefact crops use the same E4 dimensions.
  useEffect(() => {
    if (initialSliceSet.current || total <= 0) return;
    const cPreSlices = hasModelHeatmap
      ? modelHeatmap?.lesion_slices['C-pre'] ?? []
      : volumeByToken.get('C-pre')?.mask_slices ?? [];
    const cPreSegments = toSegments(cPreSlices);
    const longest = cPreSegments.reduce<Array<[number, number]>[number] | null>(
      (best, current) => (!best || current[1] - current[0] > best[1] - best[0] ? current : best),
      null,
    );
    setZ(longest ? Math.round((longest[0] + longest[1]) / 2) : Math.floor(total / 2));
    initialSliceSet.current = true;
  }, [hasModelHeatmap, modelHeatmap, total, volumeByToken]);

  useEffect(() => setZ((current) => clamp(current)), [clamp]);
  useEffect(() => setFailed(false), [token, z, showAnnotation, showHeatmap]);
  useEffect(() => {
    if (!hasModelHeatmap) setShowHeatmap(false);
  }, [hasModelHeatmap]);
  useEffect(() => {
    if (!hasModelHeatmap && !activeVolume?.has_mask) setShowAnnotation(false);
  }, [activeVolume?.has_mask, hasModelHeatmap]);

  const clampOffset = useCallback((next: { x: number; y: number }, atScale: number) => {
    const frame = frameRef.current;
    if (!frame || atScale <= 1) return { x: 0, y: 0 };
    const maxX = (frame.clientWidth * (atScale - 1)) / 2;
    const maxY = (frame.clientHeight * (atScale - 1)) / 2;
    return {
      x: Math.max(-maxX, Math.min(maxX, next.x)),
      y: Math.max(-maxY, Math.min(maxY, next.y)),
    };
  }, []);
  const resetView = useCallback(() => {
    setScale(1);
    setOffset({ x: 0, y: 0 });
  }, []);

  useEffect(() => {
    const frame = frameRef.current;
    if (!frame) return;
    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
      if (!event.ctrlKey) {
        step(event.deltaY > 0 ? 1 : -1);
        return;
      }
      const rect = frame.getBoundingClientRect();
      const cursorX = event.clientX - rect.left - rect.width / 2;
      const cursorY = event.clientY - rect.top - rect.height / 2;
      setScale((current) => {
        const next = Math.max(MIN_SCALE, Math.min(MAX_SCALE, current * (event.deltaY > 0 ? 0.9 : 1 / 0.9)));
        if (next === current) return current;
        setOffset((currentOffset) =>
          clampOffset(
            {
              x: cursorX - ((cursorX - currentOffset.x) * next) / current,
              y: cursorY - ((cursorY - currentOffset.y) * next) / current,
            },
            next,
          ),
        );
        return next;
      });
    };
    frame.addEventListener('wheel', onWheel, { passive: false });
    return () => frame.removeEventListener('wheel', onWheel);
  }, [clampOffset, step]);

  const onPointerDown = (event: PointerEvent<HTMLDivElement>) => {
    dragging.current = true;
    dragOrigin.current = { x: event.clientX, y: event.clientY, offset };
    event.currentTarget.setPointerCapture(event.pointerId);
  };
  const onPointerMove = (event: PointerEvent<HTMLDivElement>) => {
    if (!dragging.current) return;
    setOffset(
      clampOffset(
        {
          x: dragOrigin.current.offset.x + event.clientX - dragOrigin.current.x,
          y: dragOrigin.current.offset.y + event.clientY - dragOrigin.current.y,
        },
        scale,
      ),
    );
  };
  const onPointerUp = (event: PointerEvent<HTMLDivElement>) => {
    dragging.current = false;
    event.currentTarget.releasePointerCapture(event.pointerId);
  };

  if (available.length === 0 || !token || total <= 0) {
    return (
      <section className="panel p-5">
        <EmptyState
          label="Chưa có ảnh MRI cho ca này"
          detail="Backend chưa tìm thấy đủ volume MRI. Kiểm tra LLDMMRI_SAMPLE_DIR trước khi xem ảnh."
          icon={Flame}
        />
      </section>
    );
  }

  const onLesionSlice = lesionSlices.includes(z);
  const before = z;
  const after = total - 1 - z;
  const zoomed = scale > 1.001;
  const imageUrl = hasModelHeatmap
    ? modelViewUrl(caseId, token, z, showAnnotation, showHeatmap)
    : sliceUrl(caseId, token, z, showAnnotation);
  const annotationAvailable = hasModelHeatmap || activeVolume?.has_mask === true;

  return (
    <section aria-label="Khám phá ảnh MRI" className="panel p-5">
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <Toggle
            active={showAnnotation}
            onClick={() => setShowAnnotation((value) => !value)}
            icon={Scan}
            activeLabel="Đang hiện vùng tổn thương"
            inactiveLabel="Hiện vùng tổn thương"
            activeClass="border-annotation bg-annotation/15 text-annotation-soft"
            title="Nhãn dataset do người chú giải khoanh, không phải output segmentation của model"
            disabled={!annotationAvailable}
          />
          {hasModelHeatmap && (
            <Toggle
              active={showHeatmap}
              onClick={() => setShowHeatmap((value) => !value)}
              icon={Flame}
              activeLabel="Đang hiện heatmap"
              inactiveLabel="Hiện heatmap"
              activeClass="border-attention bg-attention/15 text-attention-soft"
              title="Độ nhạy cục bộ của model với lớp đã dự đoán"
            />
          )}
          {zoomed && (
            <button
              type="button"
              onClick={resetView}
              className="inline-flex items-center gap-1.5 rounded-control border border-pacs-600 bg-pacs-800 px-2.5 py-1 text-data font-semibold text-slate-300 transition hover:border-accent hover:text-accent-glow"
            >
              <Maximize2 className="h-3.5 w-3.5" aria-hidden="true" />
              Vừa khung ({scale.toFixed(1)}×)
            </button>
          )}
        </div>
      </div>

      <div role="group" aria-label="Chọn thì MRI" className="mb-4 flex flex-wrap gap-2">
        {available.map((phase) => {
          const active = phase.file_token === token;
          return (
            <button
              key={phase.file_token}
              type="button"
              aria-pressed={active}
              title={phase.description_vi}
              onClick={() => setToken(phase.file_token)}
              className={`rounded-control border px-3 py-1.5 text-data font-semibold transition ${
                active
                  ? 'border-accent bg-accent/15 text-accent-glow'
                  : 'border-pacs-700 bg-pacs-800 text-slate-400 hover:text-white'
              }`}
            >
              {phase.label_vi}
            </button>
          );
        })}
      </div>

      <div
        ref={frameRef}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        style={{ aspectRatio: '1 / 1', width: 'min(100%, 72vh)' }}
        className={`relative mx-auto touch-none select-none overflow-hidden rounded-control border border-pacs-700 bg-black ${
          zoomed ? 'cursor-grab active:cursor-grabbing' : 'cursor-default'
        }`}
      >
        {failed ? (
          <EmptyState label="Không đọc được lát này" detail={`Thì ${token}, lát ${z + 1}.`} />
        ) : (
          <img
            key={`${token}-${z}-${showAnnotation}-${showHeatmap}`}
            src={imageUrl}
            alt={`MRI, thì ${token}, lát ${z + 1} trên ${total}${showHeatmap ? ', có heatmap độ nhạy model' : ''}${showAnnotation ? ', có nhãn vùng tổn thương do người chú giải' : ''}`}
            onError={() => setFailed(true)}
            draggable={false}
            style={{ transform: `translate(${offset.x}px, ${offset.y}px) scale(${scale})` }}
            className="h-full w-full object-contain"
          />
        )}
      </div>

      {hasModelHeatmap && (
        <p className="mt-3 max-w-measure text-data text-slate-400">
          Heatmap thể hiện độ nhạy cục bộ của model với lớp đã dự đoán; không phải vùng tổn thương do model khoanh và không mang ý nghĩa chẩn đoán.
        </p>
      )}

      <div className="mt-4 flex items-center gap-3">
        <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-pacs-700" aria-hidden="true">
          <span className="ml-auto block h-full bg-accent" style={{ width: `${total > 1 ? (before / (total - 1)) * 100 : 0}%` }} />
        </span>
        <div className="flex shrink-0 items-center gap-1">
          <StepButton direction="prev" disabled={z <= 0} onClick={() => step(-1)} label="Lát trước" />
          <span className="min-w-[4.5rem] text-center font-mono text-data font-semibold text-white">{z + 1} / {total}</span>
          <StepButton direction="next" disabled={z >= total - 1} onClick={() => step(1)} label="Lát sau" />
        </div>
        <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-pacs-700" aria-hidden="true">
          <span className="block h-full bg-accent" style={{ width: `${total > 1 ? (after / (total - 1)) * 100 : 0}%` }} />
        </span>
      </div>

      <label className="mt-3 block">
        <span className="text-sm font-semibold text-annotation-soft">Vị trí lát</span>
        <span className="text-data text-slate-400">. Lăn chuột để đổi lát · Ctrl + lăn để phóng to · kéo để di chuyển ảnh.</span>
        <input
          type="range"
          min={0}
          max={Math.max(total - 1, 0)}
          value={z}
          onChange={(event) => setZ(clamp(Number(event.target.value)))}
          aria-label={`Lát ${z + 1} trên ${total}`}
          className="mt-2 h-1.5 w-full appearance-none rounded-full bg-pacs-700 accent-accent"
        />
      </label>

      {segments.length > 0 && (
        <LesionTrack
          segments={segments}
          total={total}
          count={lesionSlices.length}
          onLesionSlice={onLesionSlice}
          onJump={() => firstLesionSlice !== null && setZ(clamp(firstLesionSlice))}
        />
      )}
    </section>
  );
}

function Toggle({
  active,
  onClick,
  icon: Icon,
  activeLabel,
  inactiveLabel,
  activeClass,
  title,
  disabled = false,
}: {
  active: boolean;
  onClick: () => void;
  icon: typeof Scan;
  activeLabel: string;
  inactiveLabel: string;
  activeClass: string;
  title: string;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onClick}
      title={title}
      disabled={disabled}
      className={`inline-flex items-center gap-1.5 rounded-control border px-2.5 py-1 text-data font-semibold transition ${
        active ? activeClass : 'border-pacs-700 bg-pacs-800 text-slate-400 hover:text-white'
      } ${
        disabled ? 'cursor-not-allowed opacity-45 hover:text-slate-400' : ''
      }`}
    >
      <Icon className="h-3.5 w-3.5" aria-hidden="true" />
      {active ? activeLabel : inactiveLabel}
    </button>
  );
}

function LesionTrack({
  segments,
  total,
  count,
  onLesionSlice,
  onJump,
}: {
  segments: Array<[number, number]>;
  total: number;
  count: number;
  onLesionSlice: boolean;
  onJump: () => void;
}) {
  const span = Math.max(total - 1, 1);
  const first = segments[0][0];
  const last = segments[segments.length - 1][1];
  return (
    <div className="mt-3">
      <div className="relative h-1.5 w-full overflow-hidden rounded-full bg-pacs-800" aria-hidden="true">
        {segments.map(([start, end]) => (
          <span
            key={start}
            className="absolute top-0 h-full bg-annotation"
            style={{ left: `${(start / span) * 100}%`, width: `${Math.max(((end - start) / span) * 100, 0.6)}%` }}
          />
        ))}
      </div>
      <div className="mt-2 flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <p className="text-data text-slate-400">
          <span className="text-annotation-soft">Vùng tổn thương</span> ở {count}/{total} lát ({first + 1}–{last + 1}) · do người chú giải khoanh, không phải model tìm ra
          {onLesionSlice && <span className="ml-2 text-annotation-soft">▸ lát đang xem có tổn thương</span>}
        </p>
        <button
          type="button"
          onClick={onJump}
          className="inline-flex shrink-0 items-center gap-1.5 rounded-control border border-pacs-600 bg-pacs-800 px-2.5 py-1 text-data font-semibold text-slate-300 transition hover:border-annotation hover:text-annotation-soft"
        >
          <Target className="h-3.5 w-3.5" aria-hidden="true" />
          Đến lát tổn thương đầu tiên
        </button>
      </div>
    </div>
  );
}

function StepButton({
  direction,
  disabled,
  onClick,
  label,
}: {
  direction: 'prev' | 'next';
  disabled: boolean;
  onClick: () => void;
  label: string;
}) {
  const Icon = direction === 'prev' ? ChevronLeft : ChevronRight;
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      title={label}
      className={`grid h-8 w-8 place-items-center rounded-control border transition ${
        disabled
          ? 'border-pacs-700 bg-pacs-800 text-slate-400 opacity-40'
          : 'border-pacs-600 bg-pacs-800 text-slate-300 hover:border-accent hover:text-accent-glow'
      }`}
    >
      <Icon className="h-4 w-4" aria-hidden="true" />
    </button>
  );
}
