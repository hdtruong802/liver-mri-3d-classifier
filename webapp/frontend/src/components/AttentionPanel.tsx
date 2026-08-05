/**
 * Bản đồ chú ý của mô hình — phần "dựa vào đâu" của kết quả.
 *
 * ## Ba điều panel này bắt buộc phải nói ra
 *
 * 1. **Ảnh ở đây khác ảnh ở bộ xem trên.** Mô hình chưa từng thấy lát gốc 480×480;
 *    nó nhận khối 112×112×32 đã cắt bám tổn thương. Không nói ra thì người xem sẽ so
 *    hai ảnh với nhau và kết luận sai.
 * 2. **Độ phân giải GỐC của bản đồ.** Một bản đồ 7×7×2 nội suy lên 112×112×32 trông
 *    mịn tới từng voxel. Giấu con số đó đi là để người xem tin hơn mức dữ liệu cho phép.
 * 3. **Đây là phỏng đoán, không phải nhãn.** Khác hẳn vùng tổn thương ở bộ xem trên
 *    (do người chú giải khoanh). Với ca mô hình đoán sai, bản đồ này *nên* trông sai —
 *    đó là thông tin, không phải lỗi.
 *
 * Màu `attention` hổ phách, cố ý cách xa `annotation` fuchsia của mask
 * (`webapp/DESIGN.md`).
 */

import { useEffect, useState } from 'react';
import { Flame } from 'lucide-react';

import { gradcamUrl } from '@/api/client';
import type { ClassInfo, GradCamInfo } from '@/api/types';
import { EmptyState } from '@/components/Provenance';
import { percent } from '@/format';

interface Props {
  caseId: string;
  gradcam: GradCamInfo | null;
  classes: ClassInfo[];
  phaseLabels: string[];
}

export function AttentionPanel({ caseId, gradcam, classes, phaseLabels }: Props) {
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
        detail={
          gradcam?.note ??
          'Ô này để trống có nhãn thay vì hiển thị một overlay bịa.'
        }
        icon={Flame}
      />
    );
  }

  const nameOf = (index: number | null) =>
    index === null ? '—' : (classes.find((c) => c.index === index)?.label_vi ?? String(index));
  const wrong =
    gradcam.true_class_index !== null && gradcam.true_class_index !== gradcam.pred_class_index;
  const trueMapMissing = wrong && gradcam.true_map_status === 'suy-bien';
  const native = gradcam.native_shape.join('×');

  return (
    <div className="space-y-4">
      <p className="max-w-measure text-data text-slate-400">
        Đây là khối <span className="font-mono text-slate-300">112×112×32</span> mà mô hình{' '}
        <strong className="text-slate-300">thực sự nhìn</strong> — đã cắt bám tổn thương và căn
        từng thì — <em>không phải</em> lát gốc ở bộ xem trên. Vùng hổ phách là chỗ mô hình nhạy;
        đây là <strong className="text-attention-soft">phỏng đoán của mô hình</strong>, khác với
        vùng tổn thương do người chú giải khoanh.
      </p>

      {trueMapMissing && (
        <p className="inset-box max-w-measure border-l-2 border-warn px-3 py-2 text-data text-slate-300">
          Mô hình đoán <strong>{nameOf(gradcam.pred_class_index)}</strong> trong khi lớp thật là{' '}
          <strong>{nameOf(gradcam.true_class_index)}</strong>. Không dựng được bản đồ cho lớp thật:{' '}
          <strong className="text-warn-soft">
            không voxel nào trong khối đóng góp dương cho lớp đó
          </strong>
          . Đây là một phát hiện chứ không phải lỗi hiển thị — mô hình không chỉ chọn nhầm, nó
          không tìm thấy bằng chứng nào cho đáp án đúng.
        </p>
      )}

      {wrong && !trueMapMissing && (
        <div role="group" aria-label="Chọn lớp để giải thích" className="flex flex-wrap gap-2">
          {(['pred', 'true'] as const).map((option) => (
            <button
              key={option}
              type="button"
              aria-pressed={target === option}
              onClick={() => setTarget(option)}
              className={[
                'rounded-control border px-3 py-1.5 text-data font-semibold transition',
                target === option
                  ? 'border-attention bg-attention/15 text-attention-soft'
                  : 'border-pacs-700 bg-pacs-800 text-slate-400 hover:text-white',
              ].join(' ')}
            >
              {option === 'pred'
                ? `Lớp đã đoán — ${nameOf(gradcam.pred_class_index)}`
                : `Lớp thật — ${nameOf(gradcam.true_class_index)}`}
            </button>
          ))}
        </div>
      )}

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
          <span>Lát trong khối crop — đánh số riêng, không khớp lát ở bộ xem trên.</span>
          <span className="font-mono text-slate-300">
            {z + 1} / {total}
          </span>
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

      {/* Chú giải dải màu, kèm mốc số. Màu không bao giờ là tuyến mã hoá duy nhất. */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <span className="text-data text-slate-400">Mức nhạy</span>
        <span
          className="h-2 w-40 rounded-full bg-gradient-to-r from-transparent to-attention"
          aria-hidden="true"
        />
        <span className="font-mono text-data text-slate-400">thấp → cao</span>
      </div>

      <dl className="grid grid-cols-2 gap-3 text-data sm:grid-cols-3">
        <Fact label="Tầng đặc trưng" value={gradcam.layer} />
        <Fact label="Độ phân giải gốc" value={native} warn />
        <Fact label="Model" value={gradcam.fold} />
      </dl>
      <p className="max-w-measure text-data text-slate-400">
        Bản đồ được tính ở kích thước <span className="font-mono text-warn-soft">{native}</span>{' '}
        rồi nội suy lên lưới crop. Nó <strong>không</strong> mịn tới từng voxel như ảnh trông
        thấy. Model dùng để giải thích là model của <span className="font-mono">{gradcam.fold}</span>
        , tức fold chưa từng train trên ca này.
      </p>

      {gradcam.phase_importance.length > 0 && (
        <PhaseImportance values={gradcam.phase_importance} labels={phaseLabels} />
      )}
    </div>
  );
}

function Fact({ label, value, warn }: { label: string; value: string; warn?: boolean }) {
  return (
    <div className="inset-box px-3 py-2">
      <dt className="text-data text-slate-400">{label}</dt>
      <dd className={`font-mono text-sm ${warn ? 'text-warn-soft' : 'text-slate-300'}`}>
        {value || '—'}
      </dd>
    </div>
  );
}

/**
 * Độ nhạy của kết quả với từng thì MRI.
 *
 * Nhãn cảnh báo không phải để cho khiêm tốn: "độ nhạy" và "đóng góp" là hai câu hỏi
 * khác nhau. Số ở đây trả lời "đổi nhẹ thì này thì logit đổi bao nhiêu", KHÔNG trả lời
 * "bỏ hẳn thì này thì mất bao nhiêu điểm" — câu sau phải train lại mới biết.
 */
function PhaseImportance({ values, labels }: { values: number[]; labels: string[] }) {
  const peak = Math.max(...values, 1e-9);
  return (
    <div className="border-t border-pacs-700 pt-4">
      <p className="label mb-1">Mô hình nhạy với thì nào</p>
      <p className="mb-3 max-w-measure text-data text-slate-400">
        Là <strong className="text-slate-300">độ nhạy</strong>, không phải phép loại bỏ: nó không
        nói bỏ hẳn một thì đi thì mất bao nhiêu điểm — muốn biết điều đó phải train lại.
      </p>
      <ul className="space-y-1.5">
        {values.map((value, index) => (
          <li key={labels[index] ?? index} className="flex items-center gap-3">
            <span className="w-20 shrink-0 text-data text-slate-400">
              {labels[index] ?? `thì ${index + 1}`}
            </span>
            <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-pacs-700">
              <span
                className="block h-full bg-attention"
                style={{ width: `${(value / peak) * 100}%` }}
              />
            </span>
            <span className="w-12 shrink-0 text-right font-mono text-data text-slate-300">
              {percent(value)}%
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
