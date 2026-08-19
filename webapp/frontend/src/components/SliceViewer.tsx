/**
 * MRI viewer for an uploaded study. The server renders the source NIfTI slice,
 * optionally overlaid with the annotation the user supplied in the same ZIP.
 *
 * The overlay is never a segmentation produced by this project — the model is a
 * classifier (AGENTS.md §3.9). The heatmap layer and the prebuilt demo-case path
 * were removed in WORKLOG S-197: both needed offline artefacts that the repo does
 * not ship, and the heatmap directory had not existed for some time.
 */

import { useCallback, useEffect, useMemo, useRef, useState, type PointerEvent } from 'react';
import { ArrowLeft, ArrowRight, FileUp, ImageOff, Scan } from 'lucide-react';

import { uploadSliceUrl } from '@/api/client';
import type { CaseVolumeInfo, PhaseInfo } from '@/api/types';
import { EmptyState } from '@/components/Provenance';

interface Props {
  /** Id của bộ ZIP vừa suy luận xong; ảnh chỉ sống trong bộ nhớ tạm của server. */
  caseId: string;
  phases: PhaseInfo[];
  volumes: CaseVolumeInfo[];
  onChooseUpload?: () => void;
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

export function SliceViewer({ caseId, phases, volumes, onChooseUpload }: Props) {
  const volumeByToken = useMemo(
    () => new Map(volumes.map((volume) => [volume.file_token, volume])),
    [volumes],
  );
  const available = useMemo(
    () => phases.filter((phase) => volumeByToken.has(phase.file_token)),
    [phases, volumeByToken],
  );
  const [token, setToken] = useState('C-pre');
  const activeVolume = volumeByToken.get(token);
  const total = activeVolume?.n_slices ?? 0;
  const [z, setZ] = useState(0);
  const [failed, setFailed] = useState(false);
  const [showAnnotation, setShowAnnotation] = useState(false);
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

  const lesionSlices = activeVolume?.mask_slices ?? [];
  const segments = useMemo(() => toSegments(lesionSlices), [lesionSlices]);

  // Mở ở giữa dải nhãn dài nhất của C-pre, thay vì lát 0 — lát đầu thường ngoài gan.
  useEffect(() => {
    if (initialSliceSet.current || total <= 0) return;
    const cPreSlices = volumeByToken.get('C-pre')?.mask_slices ?? [];
    const cPreSegments = toSegments(cPreSlices);
    const longest = cPreSegments.reduce<Array<[number, number]>[number] | null>(
      (best, current) => (!best || current[1] - current[0] > best[1] - best[0] ? current : best),
      null,
    );
    setZ(longest ? Math.round((longest[0] + longest[1]) / 2) : Math.floor(total / 2));
    initialSliceSet.current = true;
  }, [total, volumeByToken]);

  useEffect(() => setZ((current) => clamp(current)), [clamp]);
  useEffect(() => setFailed(false), [token, z, showAnnotation]);
  useEffect(() => {
    if (!activeVolume?.has_mask) setShowAnnotation(false);
  }, [activeVolume?.has_mask]);

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
  useEffect(() => {
    const frame = frameRef.current;
    if (!frame) return;
    const onWheel = (event: WheelEvent) => {
      event.preventDefault();
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
  }, [clampOffset]);

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
      <section className="mri-viewer mri-viewer--empty">
        <EmptyState
          label="Chưa có ảnh MRI để hiển thị"
          detail="Ảnh của bộ MRI tải lên đã hết hạn hoặc server đã khởi động lại. Hãy tải ZIP lên lại."
          icon={ImageOff}
        />
      </section>
    );
  }

  const onLesionSlice = lesionSlices.includes(z);
  const zoomed = scale > 1.001;
  const imageUrl = uploadSliceUrl(caseId, token, z, showAnnotation);
  const annotationAvailable = activeVolume?.has_mask === true;

  return (
    <section aria-label="Khám phá ảnh MRI" className="mri-viewer">
      <div className="viewer-toolbar">
        <div className="viewer-toolbar__controls">
          {onChooseUpload ? (
            <button
              type="button"
              onClick={onChooseUpload}
              className="viewer-control viewer-control--upload"
              title="Chọn một bộ MRI ZIP khác. Kết quả và ảnh hiện tại sẽ được thay thế."
            >
              <FileUp aria-hidden="true" />
              Tải bộ MRI khác
            </button>
          ) : null}
          <div role="group" aria-label="Chọn thì MRI" className="viewer-phase-group">
            {available.map((phase) => {
              const active = phase.file_token === token;
              return (
                <button
                  key={phase.file_token}
                  type="button"
                  aria-pressed={active}
                  title={phase.description_vi}
                  onClick={() => setToken(phase.file_token)}
                  className={`viewer-phase ${active ? 'viewer-phase--active' : ''}`}
                >
                  {phase.label_vi}
                </button>
              );
            })}
          </div>
          <Toggle
            active={showAnnotation}
            onClick={() => setShowAnnotation((value) => !value)}
            icon={Scan}
            activeLabel="Đang hiện vùng tổn thương"
            inactiveLabel="Hiện vùng tổn thương"
            tone="annotation"
            title="Ảnh MRI gốc của bộ vừa tải lên. Vùng fuchsia là nhãn tổn thương do người tải lên cung cấp, không phải output segmentation của model."
            disabled={!annotationAvailable}
          />
        </div>
      </div>

      <div className="mri-canvas-slot">
        <div
          ref={frameRef}
          tabIndex={0}
          onKeyDown={(event) => {
          if (event.key === 'ArrowLeft') {
            event.preventDefault();
            step(-1);
          }
          if (event.key === 'ArrowRight') {
            event.preventDefault();
            step(1);
          }
          }}
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onPointerCancel={onPointerUp}
          className={`mri-frame ${
          zoomed ? 'cursor-grab active:cursor-grabbing' : 'cursor-default'
          }`}
        >
        {failed ? (
          <EmptyState label="Không đọc được lát này" detail={`Thì ${token}, lát ${z + 1}.`} />
        ) : (
          <img
            key={`${token}-${z}-${showAnnotation}`}
            src={imageUrl}
            alt={`MRI, thì ${token}, lát ${z + 1} trên ${total}${showAnnotation ? ', có nhãn vùng tổn thương do người tải lên cung cấp' : ''}`}
            onError={() => setFailed(true)}
            draggable={false}
            style={{ transform: `translate(${offset.x}px, ${offset.y}px) scale(${scale})` }}
            className="h-full w-full object-contain"
          />
        )}
        </div>
      </div>

      <UnifiedSliceNavigation
        total={total}
        z={z}
        segments={segments}
        lesionCount={lesionSlices.length}
        onLesionSlice={onLesionSlice}
        onChange={(next) => setZ(clamp(next))}
        onStep={step}
      />
    </section>
  );
}

function UnifiedSliceNavigation({
  total,
  z,
  segments,
  lesionCount,
  onLesionSlice,
  onChange,
  onStep,
}: {
  total: number;
  z: number;
  segments: Array<[number, number]>;
  lesionCount: number;
  onLesionSlice: boolean;
  onChange: (next: number) => void;
  onStep: (delta: number) => void;
}) {
  const span = Math.max(total - 1, 1);
  const summary = lesionCount > 0
    ? `${lesionCount}/${total} lát có tổn thương${onLesionSlice ? ' · đang xem' : ''}`
    : 'Không có vùng tổn thương';

  return (
    <div className="viewer-navigation viewer-navigation--unified" title="Lăn chuột để phóng to hoặc thu nhỏ · Kéo để di chuyển ảnh">
      <span className="slice-position__label">Vị trí lát</span>
      <StepButton direction="prev" disabled={z <= 0} onClick={() => onStep(-1)} label="Lát trước" />
      <label className="slice-range-wrap">
        <span className="sr-only">Vị trí lát. {summary}</span>
        <span className="slice-lesion-track" aria-hidden="true">
          {segments.map(([start, end]) => (
            <span
              key={start}
              style={{
                left: `${(start / span) * 100}%`,
                width: `${Math.max(((end - start) / span) * 100, 0.6)}%`,
              }}
            />
          ))}
        </span>
        <input
          type="range"
          min={0}
          max={Math.max(total - 1, 0)}
          value={z}
          onChange={(event) => onChange(Number(event.target.value))}
          aria-label={`Vị trí lát ${z + 1} trên ${total}`}
          className="slice-range"
        />
      </label>
      <span className="slice-counter" aria-live="polite">{z + 1} / {total}</span>
      <StepButton direction="next" disabled={z >= total - 1} onClick={() => onStep(1)} label="Lát sau" />
      {lesionCount > 0 && <span className={`slice-lesion-summary ${onLesionSlice ? 'is-current' : ''}`}>{summary}</span>}
    </div>
  );
}

function Toggle({
  active,
  onClick,
  icon: Icon,
  activeLabel,
  inactiveLabel,
  tone,
  title,
  disabled = false,
}: {
  active: boolean;
  onClick: () => void;
  icon: typeof Scan;
  activeLabel: string;
  inactiveLabel: string;
  tone: 'annotation' | 'attention';
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
      className={`viewer-control viewer-control--${tone} ${active ? 'viewer-control--active' : ''} ${disabled ? 'is-disabled' : ''}`}
    >
      <Icon className="h-3.5 w-3.5" aria-hidden="true" />
      {active ? activeLabel : inactiveLabel}
    </button>
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
  const Icon = direction === 'prev' ? ArrowLeft : ArrowRight;
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      title={label}
      className={`slice-step-button ${disabled ? 'is-disabled' : ''}`}
    >
      <Icon className="h-4 w-4" aria-hidden="true" />
    </button>
  );
}
