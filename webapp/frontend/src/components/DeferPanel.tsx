import { AlertTriangle, CircleAlert, ShieldCheck } from 'lucide-react';

import type { PredictResult } from '@/api/types';
import { ProvenanceBadge } from '@/components/Provenance';

export function DeferPanel({ result }: { result: PredictResult }) {
  const state = result.defer === null
    ? {
        title: 'Chưa áp dụng cơ chế từ chối ca',
        copy: 'Bộ MRI này được suy luận trực tiếp từ file tải lên. Cơ chế từ chối chỉ được kiểm tra cho tập đánh giá độc lập, nên không áp dụng cho kết quả này.',
        icon: <CircleAlert className="h-6 w-6 text-accent" aria-hidden="true" />,
        shell: 'border-pacs-600 bg-pacs-850',
        text: 'text-slate-100',
      }
    : result.defer
    ? {
        title: 'Mô hình từ chối quyết ca này',
        copy: 'Mô hình chưa đủ chắc chắn để đưa ra dự đoán cho ca này. Cần xem kết quả cùng đánh giá của người có chuyên môn.',
        icon: <AlertTriangle className="h-6 w-6 text-warn" aria-hidden="true" />,
        shell: 'border-warn/50 bg-warn/10',
        text: 'text-warn-soft',
      }
    : {
        title: 'Mô hình nhận quyết ca này',
        copy: 'Mô hình có thể đưa ra dự đoán cho ca này. Kết quả chỉ phục vụ mục đích nghiên cứu, không dùng để chẩn đoán.',
        icon: <ShieldCheck className="h-6 w-6 text-ok" aria-hidden="true" />,
        shell: 'border-ok/40 bg-ok/5',
        text: 'text-ok-soft',
      };

  return (
    <section
      aria-labelledby="defer-heading"
      className={`mt-4 rounded-[6px] border p-4 ${state.shell}`}
    >
      <div className="flex items-start gap-3">
        <div className="mt-0.5 shrink-0">{state.icon}</div>
        <div>
          <h3 id="defer-heading" className={`text-base font-bold ${state.text}`}>{state.title}</h3>
          <p className="mt-2 max-w-measure text-sm text-slate-300">{state.copy}</p>
        </div>
      </div>
      <div className="border-t border-white/10 pt-3">
        <ProvenanceBadge provenance={result.provenance} />
      </div>
    </section>
  );
}
