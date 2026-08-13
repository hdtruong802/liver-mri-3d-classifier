import type { PredictResult } from '@/api/types';
import { percent } from '@/format';

export function ResultSummary({ result }: { result: PredictResult }) {
  const predicted = result.probs.find((entry) => entry.class_index === result.pred_class_index);
  const malignancyPercent = Math.round(result.malignant_prob * 100);

  return (
    <section className="prediction-summary" aria-label="Tóm tắt dự đoán">
      <div className="prediction-summary__primary">
        <p className="section-label">Lớp dự đoán</p>
        <strong>{predicted?.label_vi ?? result.pred_class_name}</strong>
        <span>{percent(result.confidence)}%</span>
      </div>
      <div className="prediction-summary__malignancy">
        <div>
          <p className="section-label">Nhóm ác tính</p>
          <strong>{malignancyPercent}%</strong>
        </div>
        <div className="metric-track" role="progressbar" aria-label="Xác suất nhóm ác tính" aria-valuemin={0} aria-valuemax={100} aria-valuenow={malignancyPercent}>
          <span style={{ width: `${malignancyPercent}%` }} />
        </div>
        <p>Tổng xác suất ICC, di căn và HCC; không phải khuyến nghị lâm sàng.</p>
      </div>
    </section>
  );
}
