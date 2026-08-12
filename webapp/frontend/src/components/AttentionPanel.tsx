import { useEffect, useState } from 'react';
import { Flame } from 'lucide-react';

import { gradcamUrl } from '@/api/client';
import type { ClassInfo, GradCamInfo } from '@/api/types';
import { EmptyState } from '@/components/Provenance';

interface Props {
  caseId: string;
  gradcam: GradCamInfo | null;
  classes: ClassInfo[];
}

export function AttentionPanel({ caseId, gradcam, classes }: Props) {
  const [z, setZ] = useState(0);
  const [target, setTarget] = useState<'pred' | 'true'>('pred');
  const [failed, setFailed] = useState(false);

  const total = gradcam?.n_slices ?? 0;
  useEffect(() => setZ(Math.floor(total / 2)), [total]);
  useEffect(() => setFailed(false), [z, target]);

  if (!gradcam?.available) {
    return (
      <EmptyState
        label="Chưa tính bản đồ chú ý"
        detail={gradcam?.note ?? 'Chỗ này để trống thay vì hiển thị một overlay không có dữ liệu.'}
        icon={Flame}
      />
    );
  }

  const nameOf = (index: number | null) =>
    index === null ? '—' : (classes.find((entry) => entry.index === index)?.label_vi ?? String(index));
  const wrong =
    gradcam.true_class_index !== null && gradcam.true_class_index !== gradcam.pred_class_index;
  const trueMapMissing = wrong && gradcam.true_map_status === 'suy-bien';

  return (
    <div className="space-y-4">
      <p className="max-w-measure text-data text-slate-400">
        Vùng hổ phách là nơi mô hình nhạy khi tạo dự đoán; khác với vùng fuchsia trong bộ xem MRI,
        do người chú giải khoanh. Đây là diễn giải của mô hình, không phải nhãn tổn thương.
      </p>

      {trueMapMissing ? (
        <p className="inset-box max-w-measure border-l-2 border-warn px-3 py-2 text-data text-slate-300">
          Mô hình đoán <strong>{nameOf(gradcam.pred_class_index)}</strong>, còn nhãn tham chiếu là{' '}
          <strong>{nameOf(gradcam.true_class_index)}</strong>. Không có bản đồ cho nhãn tham chiếu vì
          mô hình không tạo được tín hiệu dương đủ để dựng bản đồ.
        </p>
      ) : null}

      {wrong && !trueMapMissing ? (
        <div role="group" aria-label="Chọn lớp để khám phá" className="flex flex-wrap gap-2">
          {(['pred', 'true'] as const).map((option) => (
            <button
              key={option}
              type="button"
              aria-pressed={target === option}
              onClick={() => setTarget(option)}
              className={`rounded-control border px-3 py-1.5 text-data font-semibold transition ${
                target === option
                  ? 'border-attention bg-attention/15 text-attention-soft'
                  : 'border-pacs-700 bg-pacs-800 text-slate-400 hover:text-white'
              }`}
            >
              {option === 'pred'
                ? `Lớp đã đoán · ${nameOf(gradcam.pred_class_index)}`
                : `Nhãn tham chiếu · ${nameOf(gradcam.true_class_index)}`}
            </button>
          ))}
        </div>
      ) : null}

      <div className="mx-auto aspect-square w-full max-w-[26rem] overflow-hidden rounded-control border border-pacs-700 bg-black">
        {failed ? (
          <EmptyState label="Không đọc được lát này" detail={`Lát ${z + 1} / ${total}.`} />
        ) : (
          <img
            key={`${target}-${z}`}
            src={gradcamUrl(caseId, z, target)}
            alt={`Bản đồ chú ý của mô hình, lát ${z + 1} trên ${total}, ca ${caseId}`}
            onError={() => setFailed(true)}
            draggable={false}
            className="h-full w-full object-contain"
          />
        )}
      </div>

      <label className="block">
        <span className="flex flex-wrap items-baseline justify-between gap-x-4 text-data text-slate-400">
          <span>Lát bản đồ chú ý</span>
          <span className="font-mono text-slate-300">{z + 1} / {total}</span>
        </span>
        <input
          type="range"
          min={0}
          max={Math.max(total - 1, 0)}
          value={z}
          onChange={(event) => setZ(Number(event.target.value))}
          aria-label={`Lát ${z + 1} trên ${total}`}
          className="mt-2 h-1.5 w-full appearance-none rounded-full bg-pacs-700 accent-attention"
        />
      </label>

      <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-data text-slate-400">
        <span>Mức chú ý</span>
        <span className="h-2 w-40 rounded-full bg-gradient-to-r from-transparent to-attention" aria-hidden="true" />
        <span className="font-mono">thấp → cao</span>
      </div>
    </div>
  );
}
