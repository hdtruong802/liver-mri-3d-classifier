/**
 * Đánh dấu nguồn gốc con số — cơ chế trung thực của cả ứng dụng.
 *
 * `PRODUCT.md` mục *Evidence on Hand*: "Số placeholder trông giống số thật là rủi ro
 * nghiêm trọng nhất của dự án này — người review sẽ tưởng đó là kết quả."
 *
 * HAI tín hiệu độc lập cho cùng một sự thật, cố ý:
 *   1. badge chữ — đọc được, dịch được, screen reader đọc được;
 *   2. chữ nghiêng (`.provisional`) — sống sót qua bản khử màu.
 * Màu KHÔNG nằm trong hai tín hiệu này. Một tín hiệu hỏng thì tín hiệu kia vẫn giữ.
 */

import { FlaskConical, ImageOff } from 'lucide-react';

import type { Provenance } from '@/api/types';
import { isProvisional } from '@/api/types';

export function ProvenanceBadge({
  provenance,
  className = '',
}: {
  provenance: Provenance;
  className?: string;
}) {
  if (!isProvisional(provenance)) {
    return (
      <span className={`chip border border-ok/40 bg-ok/10 text-ok-soft ${className}`}>
        {provenance.source === 'oof' ? 'prediction out-of-fold' : 'suy luận trực tiếp'}
        {provenance.model_version ? ` · ${provenance.model_version}` : ''}
      </span>
    );
  }
  return (
    <span
      className={`chip border border-warn/40 bg-warn/10 italic text-warn-soft ${className}`}
      title={provenance.note}
    >
      <FlaskConical className="h-3 w-3 shrink-0" aria-hidden="true" />
      minh hoạ, chưa có model
    </span>
  );
}

/**
 * Trạng thái rỗng có nhãn. Dùng cho mọi chỗ chưa có dữ liệu thật.
 *
 * Không bao giờ thay bằng ảnh hay số bịa: bản bolt gốc có một module sinh ảnh MRI giả
 * trông như thật, và nó đã bị bỏ vì đúng lý do này.
 */
export function EmptyState({
  label,
  detail,
  icon: Icon = ImageOff,
}: {
  label: string;
  detail?: string;
  icon?: typeof ImageOff;
}) {
  return (
    <div className="flex min-h-[8rem] flex-col items-center justify-center gap-2 rounded-control border border-dashed border-pacs-600 bg-pacs-900 p-5 text-center">
      <Icon className="h-6 w-6 text-slate-400" aria-hidden="true" />
      <p className="text-sm font-medium text-slate-300">{label}</p>
      {detail ? <p className="max-w-measure text-data text-slate-400">{detail}</p> : null}
    </div>
  );
}
