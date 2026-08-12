import { AlertTriangle, ShieldCheck } from 'lucide-react';

import type { PredictResult } from '@/api/types';
import { ProvenanceBadge } from '@/components/Provenance';

export function DeferPanel({ result }: { result: PredictResult }) {
  const state = result.defer
    ? {
        title: 'Mô hình từ chối quyết ca này',
        copy: 'Mức bất định của ca này vượt ngưỡng đã khóa trước trên validation. Ca được đánh dấu để cần đối chiếu chuyên môn; đây là một kết quả hợp lệ của hệ.',
        icon: <AlertTriangle className="h-6 w-6 text-warn" aria-hidden="true" />,
        shell: 'border-warn/50 bg-warn/10',
        text: 'text-warn-soft',
        iconShell: 'bg-warn/20',
      }
    : {
        title: 'Mô hình nhận quyết ca này',
        copy: 'Mức bất định của ca này nằm dưới ngưỡng đã khóa trước trên validation. Kết quả vẫn chỉ dành cho mục đích nghiên cứu.',
        icon: <ShieldCheck className="h-6 w-6 text-ok" aria-hidden="true" />,
        shell: 'border-ok/40 bg-ok/5',
        text: 'text-ok-soft',
        iconShell: 'bg-ok/20',
      };

  return (
    <section
      aria-labelledby="defer-heading"
      className={`flex flex-col justify-between gap-4 rounded-panel border p-5 lg:col-span-5 ${state.shell}`}
    >
      <div className="flex items-start gap-3">
        <span className={`grid h-11 w-11 shrink-0 place-items-center rounded-control ${state.iconShell}`}>
          {state.icon}
        </span>
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
