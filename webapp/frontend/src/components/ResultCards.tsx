import { Target } from 'lucide-react';

import type { PredictResult } from '@/api/types';
import { percent } from '@/format';

export function PredictionCard({ result }: { result: PredictResult }) {
  const predicted = result.probs.find((entry) => entry.class_index === result.pred_class_index);

  return (
    <section aria-labelledby="prediction-heading" className="panel p-5 lg:col-span-4">
      <div className="flex items-center gap-2">
        <Target className="h-4 w-4 text-accent" aria-hidden="true" />
        <h3 id="prediction-heading" className="label">Lớp dự đoán</h3>
      </div>
      <p className="mt-4 text-2xl font-bold text-white">{predicted?.label_vi ?? result.pred_class_name}</p>
      <p className="mt-1 text-data text-slate-400">Xác suất đã hiệu chỉnh</p>
      <p className="font-mono text-xl font-semibold text-accent">{percent(result.confidence)}%</p>
    </section>
  );
}

export function MalignancyGauge({ result }: { result: PredictResult }) {
  const percentValue = Math.round(result.malignant_prob * 100);
  const style = {
    background: `conic-gradient(#F59E0B ${percentValue * 3.6}deg, #1C2540 0deg)`,
  };

  return (
    <section aria-labelledby="malignancy-heading" className="panel p-5 lg:col-span-3">
      <h3 id="malignancy-heading" className="label">Xác suất nhóm ác</h3>
      <div className="mt-3 flex items-center gap-4">
        <div className="grid h-16 w-16 shrink-0 place-items-center rounded-full" style={style}>
          <div className="grid h-12 w-12 place-items-center rounded-full bg-pacs-900 font-mono text-sm font-semibold text-white">
            {percentValue}%
          </div>
        </div>
        <p className="text-data text-slate-400">
          Tổng xác suất ICC, di căn và HCC; không phải khuyến nghị lâm sàng.
        </p>
      </div>
    </section>
  );
}
