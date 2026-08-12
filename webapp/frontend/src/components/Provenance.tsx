/**
 * Đánh dấu nguồn gốc con số — cơ chế trung thực của cả ứng dụng.
 *
 * `PRODUCT.md` mục *Evidence on Hand*: "Số placeholder trông giống số thật là rủi ro
 * nghiêm trọng nhất của dự án này — người review sẽ tưởng đó là kết quả."
 *
 * Badge chữ cho biết prediction OOF hay suy luận trực tiếp. Upload ZIP V1 không đi qua
 * component này vì nó không tạo prediction.
 */

import { ImageOff } from 'lucide-react';

import type { Provenance } from '@/api/types';

export function ProvenanceBadge({
  provenance,
  className = '',
}: {
  provenance: Provenance;
  className?: string;
}) {
  return (
    <span className={`chip border border-ok/40 bg-ok/10 text-ok-soft ${className}`} title={provenance.note}>
      {provenance.source === 'oof' ? 'prediction out-of-fold' : 'suy luận trực tiếp'}
      {provenance.model_version ? ` · ${provenance.model_version}` : ''}
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
