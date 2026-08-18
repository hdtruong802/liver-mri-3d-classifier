import { AlertTriangle, CircleAlert, ShieldCheck } from 'lucide-react';

import type { PredictResult } from '@/api/types';

export function DeferPanel({ result }: { result: PredictResult }) {
  const state = result.defer === null
    ? {
        title: 'Chưa đánh giá trạng thái',
        copy: 'Hệ thống chưa có cơ sở để xác định trạng thái cho kết quả này. Cần được người có chuyên môn đối chiếu.',
        icon: <CircleAlert aria-hidden="true" />,
        tone: 'neutral',
      }
    : result.defer
    ? {
        title: 'Cần đối chiếu chuyên môn',
        copy: 'Hệ thống chưa tự trả kết quả cho ca này. Cần được người có chuyên môn đối chiếu ảnh MRI và thông tin lâm sàng.',
        icon: <AlertTriangle aria-hidden="true" />,
        tone: 'warning',
      }
    : {
        title: 'Có thể tham khảo',
        copy: 'Kết quả có thể dùng để tham khảo nghiên cứu. Bác sĩ vẫn cần đối chiếu ảnh MRI và thông tin lâm sàng; không sử dụng riêng kết quả này để chẩn đoán.',
        icon: <ShieldCheck aria-hidden="true" />,
        tone: 'success',
      };

  return (
    <section
      aria-labelledby="defer-heading"
      className={`defer-panel defer-panel--${state.tone}`}
    >
      <div className="flex items-start gap-3">
        <div className="mt-0.5 shrink-0">{state.icon}</div>
        <div>
          <p className="defer-panel__label">Trạng thái kết quả</p>
          <h3 id="defer-heading">{state.title}</h3>
          <p>{state.copy}</p>
        </div>
      </div>
    </section>
  );
}
