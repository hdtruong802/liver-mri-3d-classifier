import { AlertTriangle, CircleAlert, ShieldCheck } from 'lucide-react';

import type { PredictResult } from '@/api/types';

export function DeferPanel({ result }: { result: PredictResult }) {
  const state = result.defer === null
    ? {
        title: 'Chưa áp dụng cơ chế từ chối ca',
        copy: 'Kết quả được tạo từ bộ MRI vừa tải lên. Hệ thống chưa áp dụng trạng thái nhận hoặc từ chối ca; cần được người có chuyên môn đối chiếu.',
        icon: <CircleAlert aria-hidden="true" />,
        tone: 'neutral',
      }
    : result.defer
    ? {
        title: 'AI chưa tự nhận kết quả ca này',
        copy: 'Dự đoán này chưa đủ tin cậy để AI tự nhận. Cần được người có chuyên môn đối chiếu trước khi sử dụng.',
        icon: <AlertTriangle aria-hidden="true" />,
        tone: 'warning',
      }
    : {
        title: 'Kết quả AI đủ độ tin cậy để tham khảo',
        copy: 'Hệ thống đánh giá dự đoán này thuộc nhóm có độ tin cậy phù hợp để trả kết quả. Bác sĩ vẫn cần đối chiếu ảnh MRI và thông tin lâm sàng; không sử dụng riêng kết quả này để chẩn đoán.',
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
          <h3 id="defer-heading">{state.title}</h3>
          <p>{state.copy}</p>
        </div>
      </div>
    </section>
  );
}
