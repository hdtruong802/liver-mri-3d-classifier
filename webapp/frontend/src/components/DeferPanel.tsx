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
        title: 'Mô hình từ chối quyết ca này',
        copy: 'Mô hình chưa đủ chắc chắn để đưa ra dự đoán cho ca này. Cần xem kết quả cùng đánh giá của người có chuyên môn.',
        icon: <AlertTriangle aria-hidden="true" />,
        tone: 'warning',
      }
    : {
        title: 'Mô hình nhận quyết ca này',
        copy: 'Mô hình có thể đưa ra dự đoán cho ca này. Kết quả chỉ phục vụ mục đích nghiên cứu, không dùng để chẩn đoán.',
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
