import type { PredictResult } from '@/api/types';
import { percent } from '@/format';

export function ResultSummary({ result }: { result: PredictResult }) {
  const predicted = result.probs.find((entry) => entry.class_index === result.pred_class_index);
  const malignancyPercent = Math.round(result.malignant_prob * 100);

  return (
    <section aria-label="Tóm tắt dự đoán" className="workstation-section">
      <div className="grid divide-y divide-pacs-700 lg:grid-cols-3 lg:divide-x lg:divide-y-0">
        <div className="py-4 lg:pr-6">
          <p className="label">Lớp dự đoán</p>
          <p className="mt-2 text-2xl font-bold text-white">{predicted?.label_vi ?? result.pred_class_name}</p>
        </div>
        <div className="py-4 lg:px-6">
          <p className="label">Xác suất dự đoán</p>
          <p className="mt-2 font-mono text-xl font-semibold text-accent">{percent(result.confidence)}%</p>
        </div>
        <div className="py-4 lg:pl-6">
          <div className="flex items-baseline justify-between gap-3">
            <p className="label">Nhóm ác tính</p>
            <p className="font-mono text-xl font-semibold text-attention-soft">{malignancyPercent}%</p>
          </div>
          <div
            className="mt-2 h-0.5 overflow-hidden bg-pacs-700"
            role="progressbar"
            aria-label="Xác suất nhóm ác tính"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={malignancyPercent}
          >
            <span className="block h-full bg-attention" style={{ width: `${malignancyPercent}%` }} />
          </div>
          <p className="mt-2 text-data text-slate-400">Tổng xác suất ICC, di căn và HCC; không phải khuyến nghị lâm sàng.</p>
        </div>
      </div>
    </section>
  );
}
