/**
 * Đánh dấu nguồn gốc con số — cơ chế trung thực của cả ứng dụng.
 *
 * `PRODUCT.md` mục *Evidence on Hand*: "Số placeholder trông giống số thật là rủi ro
 * nghiêm trọng nhất của dự án này — người review sẽ tưởng đó là kết quả."
 *
 * Ở đây có HAI tín hiệu độc lập cho cùng một sự thật, và đó là cố ý:
 *   1. nhãn chữ — đọc được, dịch được, screen reader đọc được;
 *   2. chữ nghiêng cộng gạch chéo — sống sót qua bản in đen trắng.
 * Một tín hiệu hỏng thì tín hiệu kia vẫn giữ. Màu KHÔNG nằm trong hai tín hiệu này.
 */

import type { Provenance } from '@/api/types';
import { isProvisional } from '@/api/types';

export function ProvenanceTag({ provenance }: { provenance: Provenance }) {
  if (!isProvisional(provenance)) {
    return (
      <span className="font-narrow text-marginalia text-ink-secondary">
        Nguồn: {provenance.source === 'oof' ? 'prediction out-of-fold trên validation' : 'suy luận trực tiếp'}
        {provenance.model_version ? ` · ${provenance.model_version}` : ''}
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-xs border-hair border-dashed border-ink-tertiary px-sm py-xs font-narrow text-marginalia italic text-ink-secondary">
      Minh hoạ: chưa có dữ liệu thật
    </span>
  );
}

/**
 * Vùng chưa khảo sát — quy ước hải đồ cho "chưa ai đo chỗ này".
 *
 * Nhãn chữ là BẮT BUỘC, không phải tuỳ chọn. Một vùng gạch chéo không chữ chỉ nói
 * "có gì đó ở đây", không nói "chưa có dữ liệu".
 */
export function Unsurveyed({ label, detail }: { label: string; detail?: string }) {
  return (
    <div className="unsurveyed flex min-h-[7rem] flex-col items-center justify-center border-hair border-dashed border-ink-tertiary p-md text-center">
      <p className="bg-paper px-sm font-narrow text-legend italic text-ink-secondary">{label}</p>
      {detail ? (
        <p className="mt-xs max-w-measure bg-paper px-sm font-narrow text-marginalia text-ink-tertiary">
          {detail}
        </p>
      ) : null}
    </div>
  );
}
