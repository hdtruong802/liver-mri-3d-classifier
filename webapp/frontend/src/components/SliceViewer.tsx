/**
 * Bộ xem ảnh MRI — khối 9 của bố cục, đúng chỗ `SliceViewer` của bản bolt vốn nằm.
 *
 * Ảnh là ảnh MRI **THẬT**, render từ file NIfTI ở backend. Bản bolt có một module 308
 * dòng sinh ảnh bụng giả bằng thuật toán; nó đã bị bỏ và không được dựng lại.
 * `PRODUCT.md` gọi dữ liệu giả trông như thật là rủi ro nghiêm trọng nhất của dự án,
 * và một ảnh MRI giả còn nguy hiểm hơn một con số giả vì không ai kiểm được bằng mắt.
 *
 * Cuộn qua khối 3D được dựng như quay một băng từ giữa hai cuộn: hai chỉ báo cho biết
 * còn bao nhiêu lát mỗi phía. Đây là chỗ duy nhất trong app có chuyển động liên tục,
 * vì ở đây chuyển động chính là dữ liệu.
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import { Flame, Layers } from 'lucide-react';

import { sliceUrl } from '@/api/client';
import type { CaseVolumeInfo, PhaseInfo } from '@/api/types';
import { EmptyState } from '@/components/Provenance';

interface Props {
  caseId: string;
  phases: PhaseInfo[];
  volumes: CaseVolumeInfo[];
}

export function SliceViewer({ caseId, phases, volumes }: Props) {
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
      <div className="panel p-5">
        <EmptyState
          label="Chưa có volume để hiển thị"
          detail="Dữ liệu bệnh nhân nằm ngoài repo. Đặt LLDMMRI_SAMPLE_DIR trỏ tới thư mục chứa 8 file .nii của ca."
        />
      </div>
    );
  }

  const before = z;
  const after = total - 1 - z;

  return (
    <section aria-labelledby="viewer-heading" className="panel p-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <Layers className="h-4 w-4 text-accent" aria-hidden="true" />
          <h3 id="viewer-heading" className="label">
            Ảnh MRI theo thì
          </h3>
          <span className="chip border border-ok/40 bg-ok/10 text-ok-soft">ảnh thật</span>
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

      <div
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        className="relative cursor-ew-resize touch-none select-none overflow-hidden rounded-control border border-pacs-700 bg-black active:cursor-grabbing"
      >
        {failed ? (
          <EmptyState label="Không đọc được lát này" detail={`Thì ${token}, lát ${z + 1}.`} />
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

      {/* Hai cuộn băng: trái là phần đã quay qua, phải là phần còn lại. */}
      <div className="mt-4 flex items-center gap-3" aria-hidden="true">
        <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-pacs-700">
          <span
            className="ml-auto block h-full bg-accent"
            style={{ width: `${total > 1 ? (before / (total - 1)) * 100 : 0}%` }}
          />
        </span>
        <span className="shrink-0 font-mono text-data font-semibold text-white">
          {z + 1} / {total}
        </span>
        <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-pacs-700">
          <span
            className="block h-full bg-accent"
            style={{ width: `${total > 1 ? (after / (total - 1)) * 100 : 0}%` }}
          />
        </span>
      </div>

      <label className="mt-3 block">
        <span className="text-data text-slate-400">
          Vị trí lát trong khối. Kéo ngang trên ảnh, hoặc dùng phím mũi tên.
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

      <div className="mt-4 border-t border-pacs-700 pt-4">
        <p className="mb-2 flex items-center gap-2 label">
          <Flame className="h-3.5 w-3.5 text-accent" aria-hidden="true" />
          Vùng mô hình đang nhìn
        </p>
        <EmptyState
          label="Grad-CAM chưa xây dựng"
          detail="Bản đồ chú ý 3D thuộc giai đoạn sau. Ô này để trống có nhãn thay vì hiển thị một overlay bịa."
          icon={Flame}
        />
      </div>
    </section>
  );
}
