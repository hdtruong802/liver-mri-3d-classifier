/**
 * Bộ chuyển lát — staging "wound medium" (băng từ hai cuộn).
 *
 * Cuộn qua một khối 3D chính là quay qua một môi trường tuyến tính: muốn tới lát 40
 * thì phải đi qua 39 lát trước đó. Hai chỉ báo cuộn cho biết còn bao nhiêu lát ở mỗi
 * phía — readout thật hơn một thanh trượt trơn, vốn không nói gì về vị trí tương đối
 * trong khối.
 *
 * Đây là chỗ DUY NHẤT trong app được phép có chuyển động liên tục
 * (`webapp/DESIGN.md`, mục Motion), vì ở đây chuyển động chính là dữ liệu.
 *
 * Ảnh là ảnh MRI THẬT, render từ NIfTI ở backend. Bản bolt sinh ảnh bụng giả bằng
 * thuật toán; module đó đã bị bỏ và không được dựng lại.
 */

import { useCallback, useEffect, useRef, useState } from 'react';

import { sliceUrl } from '@/api/client';
import type { CaseVolumeInfo, PhaseInfo } from '@/api/types';
import { Unsurveyed } from '@/components/Provenance';

interface Props {
  caseId: string;
  phases: PhaseInfo[];
  volumes: CaseVolumeInfo[];
}

export function SliceTransport({ caseId, phases, volumes }: Props) {
  const available = phases.filter((p) => volumes.some((v) => v.file_token === p.file_token));
  const [token, setToken] = useState(() => available.find((p) => p.file_token === 'C+V')?.file_token ?? available[0]?.file_token ?? '');

  const volume = volumes.find((v) => v.file_token === token);
  const total = volume?.n_slices ?? 0;
  const [z, setZ] = useState(() => Math.floor(total / 2));
  const [failed, setFailed] = useState(false);
  const dragging = useRef(false);
  const dragOrigin = useRef({ x: 0, z: 0 });

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

  useEffect(() => setFailed(false), [token, z]);

  const clamp = useCallback((value: number) => Math.max(0, Math.min(total - 1, value)), [total]);

  const onPointerDown = (event: React.PointerEvent<HTMLDivElement>) => {
    dragging.current = true;
    dragOrigin.current = { x: event.clientX, z };
    event.currentTarget.setPointerCapture(event.pointerId);
  };
  const onPointerMove = (event: React.PointerEvent<HTMLDivElement>) => {
    if (!dragging.current || total < 2) return;
    const width = event.currentTarget.clientWidth || 1;
    const travelled = ((event.clientX - dragOrigin.current.x) / width) * total;
    setZ(clamp(Math.round(dragOrigin.current.z + travelled)));
  };
  const onPointerUp = (event: React.PointerEvent<HTMLDivElement>) => {
    dragging.current = false;
    event.currentTarget.releasePointerCapture(event.pointerId);
  };

  if (available.length === 0 || !volume) {
    return (
      <Unsurveyed
        label="Chưa có volume để hiển thị"
        detail="Dữ liệu bệnh nhân không nằm trong repo. Đặt LLDMMRI_SAMPLE_DIR trỏ tới thư mục chứa 8 file .nii của ca."
      />
    );
  }

  const before = z;
  const after = total - 1 - z;

  return (
    <section aria-labelledby="transport-heading" className="plate p-lg">
      <div className="mb-md flex flex-wrap items-baseline justify-between gap-md border-b-hair border-rule pb-sm">
        <h2 id="transport-heading" className="font-narrow text-headline text-ink">
          Ảnh MRI theo thì
        </h2>
        <p className="font-narrow text-marginalia text-ink-secondary">
          ảnh thật, đọc từ file gốc · {volume.shape[0]}×{volume.shape[1]}×{volume.shape[2]} voxel ·{' '}
          {volume.spacing_mm.map((s) => s.toFixed(2).replace('.', ',')).join(' × ')} mm
        </p>
      </div>

      {/* Tám thì. Thì đang xem nhấn bằng nét đậm 2px, không bằng màu.
          Dùng `aria-pressed` chứ không phải tablist: không có `tabpanel` thật ở đây,
          và một tablist thiếu panel là ARIA sai — tệ hơn là không khai gì. */}
      <div role="group" aria-label="Chọn thì MRI" className="mb-md flex flex-wrap gap-0">
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
                'border-hair border-hairline px-sm py-xs font-narrow text-legend',
                '-ml-px first:ml-0',
                active
                  ? 'border-b-mark border-b-ink bg-land font-semibold text-ink'
                  : 'bg-paper text-ink-secondary hover:text-ink',
              ].join(' ')}
            >
              {phase.label_vi}
            </button>
          );
        })}
      </div>

      <div
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        className="relative cursor-ew-resize touch-none select-none border-hair border-hairline bg-ink active:cursor-grabbing"
      >
        {failed ? (
          <Unsurveyed label="Không đọc được lát này" detail={`Thì ${token}, lát ${z}.`} />
        ) : (
          <img
            key={`${token}-${z}`}
            src={sliceUrl(caseId, token, z)}
            alt={`Lát ${z + 1} trên ${total}, thì ${token}, ảnh MRI thật của ca ${caseId}`}
            onError={() => setFailed(true)}
            draggable={false}
            className="mx-auto block max-h-[52vh] w-auto max-w-full"
          />
        )}
      </div>

      {/* Hai cuộn: bên trái là phần đã quay qua, bên phải là phần còn lại. Tổng chiều
          dài không đổi, nên tỉ lệ giữa hai bên chính là vị trí trong khối. */}
      <div className="mt-md flex items-center gap-sm" aria-hidden="true">
        <span className="h-[6px] flex-1 bg-shoal-1">
          <span
            className="ml-auto block h-full bg-shoal-3"
            style={{ width: `${total > 1 ? (before / (total - 1)) * 100 : 0}%` }}
          />
        </span>
        <span className="shrink-0 font-narrow text-legend text-ink">
          {z + 1} / {total}
        </span>
        <span className="h-[6px] flex-1 bg-shoal-1">
          <span
            className="block h-full bg-shoal-3"
            style={{ width: `${total > 1 ? (after / (total - 1)) * 100 : 0}%` }}
          />
        </span>
      </div>

      <label className="mt-sm block">
        <span className="font-narrow text-marginalia text-ink-secondary">
          Vị trí lát trong khối. Kéo ngang trên ảnh, hoặc dùng phím mũi tên.
        </span>
        <input
          type="range"
          min={0}
          max={Math.max(total - 1, 0)}
          value={z}
          onChange={(event) => setZ(clamp(Number(event.target.value)))}
          aria-label={`Lát ${z + 1} trên ${total}`}
          className="mt-xs h-[6px] w-full appearance-none bg-shoal-2 accent-ink"
        />
      </label>

      <p className="mt-sm font-narrow text-marginalia text-ink-tertiary">
        Còn {before} lát phía trên, {after} lát phía dưới.
      </p>
    </section>
  );
}
