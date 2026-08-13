/**
 * Đánh dấu nguồn gốc con số — cơ chế trung thực của cả ứng dụng.
 *
 * `PRODUCT.md` mục *Evidence on Hand*: "Số placeholder trông giống số thật là rủi ro
 * nghiêm trọng nhất của dự án này — người review sẽ tưởng đó là kết quả."
 *
 * Badge chữ cho biết kết quả đánh giá độc lập hay suy luận trực tiếp. Upload ZIP V1 không đi qua
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
    <span
      className={`provenance-badge ${className}`}
      title={provenance.source === 'oof' ? 'Model chưa học ca này trong lượt huấn luyện tương ứng.' : provenance.note}
    >
      {provenance.source === 'oof' ? 'Kết quả đánh giá độc lập' : 'Suy luận trực tiếp'}
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
    <div className="empty-state">
      <Icon aria-hidden="true" />
      <p>{label}</p>
      {detail ? <p>{detail}</p> : null}
    </div>
  );
}
