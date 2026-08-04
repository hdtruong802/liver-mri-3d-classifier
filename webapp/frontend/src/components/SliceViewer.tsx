/**
 * Bộ xem ảnh MRI — khối 9 của bố cục, đúng chỗ `SliceViewer` của bản bolt vốn nằm.
 *
 * Ảnh là ảnh MRI **THẬT**, render từ file NIfTI ở backend. Bản bolt có một module 308
 * dòng sinh ảnh bụng giả bằng thuật toán; nó đã bị bỏ và không được dựng lại.
 * `PRODUCT.md` gọi dữ liệu giả trông như thật là rủi ro nghiêm trọng nhất của dự án,
 * và một ảnh MRI giả còn nguy hiểm hơn một con số giả vì không ai kiểm được bằng mắt.
 *
 * ## Quy ước thao tác
 *
 * Bám phản xạ của bác sĩ chẩn đoán hình ảnh (`PRODUCT.md` — người dùng đích), không
 * bám thói quen của web:
 *
 * - **Lăn chuột = chuyển lát.** Trong mọi phần mềm PACS, lăn chuột là đi qua khối.
 * - **Ctrl + lăn = zoom.** Quy ước của trình duyệt, ai cũng biết sẵn.
 * - **Kéo = di chuyển ảnh.** Trước đây kéo là chuyển lát; đổi vì zoom mà không pan
 *   được thì zoom sâu vô dụng — tổn thương ở rìa trôi ra ngoài khung.
 *
 * Chuyển lát vẫn còn bốn đường khác: nút mũi tên, thanh trượt, phím mũi tên, và nút
 * "Đi tới tổn thương".
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { ChevronLeft, ChevronRight, Flame, Layers, Maximize2, Scan, Target } from 'lucide-react';

import { sliceUrl } from '@/api/client';
import type { CaseVolumeInfo, ClassInfo, GradCamInfo, PhaseInfo } from '@/api/types';
import { AttentionPanel } from '@/components/AttentionPanel';
import { EmptyState } from '@/components/Provenance';

interface Props {
  caseId: string;
  phases: PhaseInfo[];
  volumes: CaseVolumeInfo[];
  classes: ClassInfo[];
  gradcam: GradCamInfo | null;
}

const MIN_SCALE = 1;
const MAX_SCALE = 8;

/** Gom danh sách chỉ số lát thành các đoạn liên tục `[đầu, cuối]`. */
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

export function SliceViewer({ caseId, phases, volumes, classes, gradcam }: Props) {
  const available = phases.filter((phase) =>
    volumes.some((volume) => volume.file_token === phase.file_token),
  );
  const [token, setToken] = useState(
    () => available.find((p) => p.file_token === 'C+V')?.file_token ?? available[0]?.file_token ?? '',
  );

  const volume = volumes.find((v) => v.file_token === token);
  const total = volume?.n_slices ?? 0;
  const [z, setZ] = useState(() => Math.floor(total / 2));
  const [failed, setFailed] = useState(false);
  const [showMask, setShowMask] = useState(false);
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });

  const frameRef = useRef<HTMLDivElement>(null);
  const dragging = useRef(false);
  const dragOrigin = useRef({ x: 0, y: 0, offset: { x: 0, y: 0 } });

  // Đổi thì thì giữ vị trí TƯƠNG ĐỐI trong khối, không giữ chỉ số tuyệt đối: tám thì
  // có số lát khác nhau, nên lát 40 của T2WI không phải cùng chỗ giải phẫu với lát 40
  // của C+V. Giữ tỉ lệ là xấp xỉ đúng hơn, dù vẫn chỉ là xấp xỉ.
  const previous = useRef({ token, total });
  useEffect(() => {
    if (previous.current.token === token || total === 0) {
      previous.current = { token, total };
      return;
    }
    const ratio = previous.current.total > 1 ? z / (previous.current.total - 1) : 0.5;
    setZ(Math.round(ratio * (total - 1)));
    previous.current = { token, total };
  }, [token, total, z]);

  useEffect(() => setFailed(false), [token, z, showMask]);

  const clamp = useCallback((value: number) => Math.max(0, Math.min(total - 1, value)), [total]);
  const step = useCallback((delta: number) => setZ((current) => clamp(current + delta)), [clamp]);

  /** Kẹp offset để ảnh không kéo được ra khỏi khung — ở scale 1 thì đứng yên hẳn. */
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

  // Lăn chuột phải gắn thủ công với `passive: false`. `onWheel` của React là passive,
  // nên `preventDefault()` trong đó không có tác dụng và cả trang sẽ cuộn theo.
  useEffect(() => {
    const frame = frameRef.current;
    if (!frame) return;

    const onWheel = (event: WheelEvent) => {
      event.preventDefault();

      // `ctrlKey` cũng bật khi người dùng chụm hai ngón trên trackpad — trình duyệt
      // dịch cử chỉ đó thành Ctrl+wheel. Nhờ vậy pinch-to-zoom chạy mà không cần code.
      if (!event.ctrlKey) {
        step(event.deltaY > 0 ? 1 : -1);
        return;
      }

      const rect = frame.getBoundingClientRect();
      const cursorX = event.clientX - rect.left - rect.width / 2;
      const cursorY = event.clientY - rect.top - rect.height / 2;

      setScale((current) => {
        const next = Math.max(
          MIN_SCALE,
          Math.min(MAX_SCALE, current * (event.deltaY > 0 ? 0.9 : 1 / 0.9)),
        );
        if (next === current) return current;
        // Giữ nguyên điểm đang nằm dưới con trỏ: điểm ảnh tại con trỏ là
        // (cursor - offset) / scale, và nó phải không đổi sau khi scale.
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
  }, [step, clampOffset]);

  const onPointerDown = (event: React.PointerEvent<HTMLDivElement>) => {
    dragging.current = true;
    dragOrigin.current = { x: event.clientX, y: event.clientY, offset };
    event.currentTarget.setPointerCapture(event.pointerId);
  };
  const onPointerMove = (event: React.PointerEvent<HTMLDivElement>) => {
    if (!dragging.current) return;
    setOffset(
      clampOffset(
        {
          x: dragOrigin.current.offset.x + (event.clientX - dragOrigin.current.x),
          y: dragOrigin.current.offset.y + (event.clientY - dragOrigin.current.y),
        },
        scale,
      ),
    );
  };
  const onPointerUp = (event: React.PointerEvent<HTMLDivElement>) => {
    dragging.current = false;
    event.currentTarget.releasePointerCapture(event.pointerId);
  };

  const lesionSlices = useMemo(() => volume?.mask_slices ?? [], [volume]);
  const segments = useMemo(() => toSegments(lesionSlices), [lesionSlices]);

  /** Lát giữa của đoạn tổn thương DÀI NHẤT — chỗ nhiều khả năng thấy rõ nhất. */
  const lesionAnchor = useMemo(() => {
    if (segments.length === 0) return null;
    const longest = segments.reduce((a, b) => (b[1] - b[0] > a[1] - a[0] ? b : a));
    return Math.round((longest[0] + longest[1]) / 2);
  }, [segments]);

  if (available.length === 0 || !volume) {
    return (
      <div className="panel p-5">
        <EmptyState
          label="Chưa có volume để hiển thị"
          detail="Dữ liệu bệnh nhân nằm ngoài repo. Đặt LLDMMRI_SAMPLE_DIR trỏ tới thư mục chứa 8 file .nii của ca."
        />
      </div>
    );
  }

  const hasMask = volume.has_mask;
  const before = z;
  const after = total - 1 - z;
  const zoomed = scale > 1.001;
  // Backend render `normalized.T[::-1]`, nên bề rộng ảnh là shape[0], chiều cao shape[1].
  const aspect = volume.shape[1] > 0 ? volume.shape[0] / volume.shape[1] : 1;
  const onLesionSlice = lesionSlices.includes(z);

  return (
    <section aria-labelledby="viewer-heading" className="panel p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <Layers className="h-4 w-4 text-accent" aria-hidden="true" />
          <h3 id="viewer-heading" className="label">
            Ảnh MRI theo thì
          </h3>
          <span className="chip border border-ok/40 bg-ok/10 text-ok-soft">ảnh thật</span>
          {hasMask && (
            <button
              type="button"
              aria-pressed={showMask}
              onClick={() => setShowMask((v) => !v)}
              title="Nhãn tổn thương của bộ dữ liệu, do người chú giải — không phải model vẽ ra"
              className={[
                'inline-flex items-center gap-1.5 rounded-control border px-2.5 py-1',
                'text-data font-semibold transition',
                showMask
                  ? 'border-annotation bg-annotation/15 text-annotation-soft'
                  : 'border-pacs-700 bg-pacs-800 text-slate-400 hover:text-white',
              ].join(' ')}
            >
              <Scan className="h-3.5 w-3.5" aria-hidden="true" />
              {showMask ? 'Đang hiện vùng tổn thương' : 'Hiện vùng tổn thương'}
            </button>
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
        <p className="font-mono text-data text-slate-400">
          {volume.shape.join('×')} voxel ·{' '}
          {volume.spacing_mm.map((s) => s.toFixed(2).replace('.', ',')).join(' × ')} mm
        </p>
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
              className={[
                'rounded-control border px-3 py-1.5 text-data font-semibold transition',
                active
                  ? 'border-accent bg-accent/15 text-accent-glow'
                  : 'border-pacs-700 bg-pacs-800 text-slate-400 hover:text-white',
              ].join(' ')}
            >
              {phase.label_vi}
            </button>
          );
        })}
      </div>

      {/* Khung ôm đúng tỉ lệ của khối, canh giữa. Trước đây ảnh bị chặn chiều cao trong
          một khung full-width nên hai bên là hai mảng đen rộng gấp nhiều lần chính ảnh. */}
      <div
        ref={frameRef}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        style={{ aspectRatio: String(aspect), maxHeight: '72vh' }}
        className={[
          'relative mx-auto w-full touch-none select-none overflow-hidden',
          'rounded-control border border-pacs-700 bg-black',
          // Chỉ mời kéo khi có gì để kéo: ở 1× ảnh vừa khung nên pan không đổi gì,
          // và con trỏ "grab" lúc đó là một lời hứa suông. `cursor` kế thừa được
          // nên đặt ở đây là đủ cho cả ảnh bên trong.
          zoomed ? 'cursor-grab active:cursor-grabbing' : 'cursor-default',
        ].join(' ')}
      >
        {failed ? (
          <EmptyState label="Không đọc được lát này" detail={`Thì ${token}, lát ${z + 1}.`} />
        ) : (
          <img
            key={`${token}-${z}-${showMask ? 'm' : ''}`}
            src={sliceUrl(caseId, token, z, showMask && hasMask)}
            alt={
              `Lát ${z + 1} trên ${total}, thì ${token}, ảnh MRI thật của ca ${caseId}` +
              (showMask && hasMask ? ', có phủ nhãn tổn thương do người chú giải' : '')
            }
            onError={() => setFailed(true)}
            draggable={false}
            // Không transition: đây là thao tác trực tiếp, không phải hiệu ứng
            // (`webapp/DESIGN.md` §Motion — ngân sách chuyển động nhỏ).
            style={{ transform: `translate(${offset.x}px, ${offset.y}px) scale(${scale})` }}
            className="h-full w-full object-contain"
          />
        )}
      </div>

      {/* Hai cuộn băng: trái là phần đã quay qua, phải là phần còn lại. Nút mũi tên
          nằm ngay cạnh chỉ số lát vì đó là chỗ mắt đang nhìn khi cần đi từng lát —
          đặt chúng ra rìa panel sẽ bắt mắt phải rời khỏi con số rồi quay lại. */}
      <div className="mt-4 flex items-center gap-3">
        <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-pacs-700" aria-hidden="true">
          <span
            className="ml-auto block h-full bg-accent"
            style={{ width: `${total > 1 ? (before / (total - 1)) * 100 : 0}%` }}
          />
        </span>

        <div className="flex shrink-0 items-center gap-1">
          <StepButton
            direction="prev"
            disabled={z <= 0}
            onClick={() => step(-1)}
            label="Lát trước"
          />
          <span className="min-w-[4.5rem] text-center font-mono text-data font-semibold text-white">
            {z + 1} / {total}
          </span>
          <StepButton
            direction="next"
            disabled={z >= total - 1}
            onClick={() => step(1)}
            label="Lát sau"
          />
        </div>

        <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-pacs-700" aria-hidden="true">
          <span
            className="block h-full bg-accent"
            style={{ width: `${total > 1 ? (after / (total - 1)) * 100 : 0}%` }}
          />
        </span>
      </div>

      <label className="mt-3 block">
        <span className="text-data text-slate-400">
          Vị trí lát trong khối. Lăn chuột để đổi lát · Ctrl + lăn để phóng to · kéo để di
          chuyển ảnh.
        </span>
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
          onJump={() => lesionAnchor !== null && setZ(clamp(lesionAnchor))}
        />
      )}

      <div className="mt-4 border-t border-pacs-700 pt-4">
        <p className="mb-2 flex items-center gap-2 label">
          <Flame className="h-3.5 w-3.5 text-accent" aria-hidden="true" />
          Vùng mô hình đang nhìn
        </p>
        <AttentionPanel
          caseId={caseId}
          gradcam={gradcam}
          classes={classes}
          phaseLabels={phases.map((p) => p.label_vi)}
        />
      </div>
    </section>
  );
}

/**
 * Dải đánh dấu lát nào có tổn thương, canh thẳng với thanh trượt ngay trên nó.
 *
 * Vẽ từng **đoạn liên tục** chứ không vẽ một dải từ lát đầu tới lát cuối: các lát có
 * tổn thương có thể đứt quãng (nhiều ổ, hoặc một ổ bị lát cắt bỏ sót ở giữa), và vẽ
 * liền một dải sẽ khẳng định sai rằng mọi lát ở giữa đều có tổn thương.
 *
 * Màu `annotation` trùng với màu mask trên ảnh, để mắt nối được hai thứ với nhau. Đi
 * kèm nhãn chữ vì màu không bao giờ là tuyến duy nhất (`webapp/DESIGN.md`).
 */
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
            style={{
              left: `${(start / span) * 100}%`,
              width: `${Math.max(((end - start) / span) * 100, 0.6)}%`,
            }}
          />
        ))}
      </div>

      <div className="mt-2 flex flex-wrap items-center justify-between gap-x-4 gap-y-2">
        <p className="text-data text-slate-400">
          <span className="text-annotation-soft">Vùng tổn thương</span> ở {count}/{total} lát (
          {first + 1}–{last + 1}) · do người chú giải khoanh, không phải mô hình tìm ra
          {onLesionSlice && (
            <span className="ml-2 text-annotation-soft">▸ lát đang xem có tổn thương</span>
          )}
        </p>
        <button
          type="button"
          onClick={onJump}
          className="inline-flex shrink-0 items-center gap-1.5 rounded-control border border-pacs-600 bg-pacs-800 px-2.5 py-1 text-data font-semibold text-slate-300 transition hover:border-annotation hover:text-annotation-soft"
        >
          <Target className="h-3.5 w-3.5" aria-hidden="true" />
          Đi tới tổn thương
        </button>
      </div>
    </div>
  );
}

/**
 * Nút đi một lát. Tách thành component riêng để hai nút không thể lệch nhau về kích
 * thước hay trạng thái disabled — hai nút điều hướng trông khác nhau là lỗi dễ lọt.
 *
 * Vô hiệu ở hai đầu khối chứ không cuộn vòng: lát 1 và lát cuối là biên giải phẫu
 * thật, nhảy từ đỉnh gan xuống đáy sẽ đọc như một ảnh khác.
 */
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
      className={[
        'grid h-8 w-8 place-items-center rounded-control border transition',
        disabled
          ? 'border-pacs-700 bg-pacs-800 text-slate-400 opacity-40'
          : 'border-pacs-600 bg-pacs-800 text-slate-300 hover:border-accent hover:text-accent-glow',
      ].join(' ')}
    >
      <Icon className="h-4 w-4" aria-hidden="true" />
    </button>
  );
}
