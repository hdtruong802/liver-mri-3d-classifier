import type { PredictResult } from '@/api/types';
import { percent } from '@/format';

export function ResultSummary({ result }: { result: PredictResult }) {
  const predicted = result.probs.find((entry) => entry.class_index === result.pred_class_index);
  const malignancyPercent = Math.round(result.malignant_prob * 100);
  const uncertaintyPercent = normalizedUncertainty(result.uncertainty.entropy, result.probs.length);

  return (
    <section className="prediction-summary" aria-label="Tóm tắt dự đoán">
      <div className="prediction-summary__primary">
        <p className="section-label">Lớp dự đoán</p>
        <strong>{predicted?.label_vi ?? result.pred_class_name}</strong>
        <span>{percent(result.confidence)}%</span>
      </div>
      <div className="prediction-summary__uncertainty">
        <div>
          <p className="section-label">Độ không chắc chắn của dự đoán</p>
          <strong>{uncertaintyPercent}%</strong>
        </div>
        <div
          className="uncertainty-scale"
          role="progressbar"
          aria-label="Độ không chắc chắn của dự đoán"
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={uncertaintyPercent}
          aria-valuetext={`${uncertaintyPercent}%, từ ít phân tán đến phân tán hơn`}
        >
          <span style={{ width: `${uncertaintyPercent}%` }} />
        </div>
        <div className="uncertainty-scale__legend" aria-hidden="true">
          <span>Ít phân tán</span>
          <span>Phân tán hơn</span>
        </div>
        <p>Thanh cao hơn nghĩa là xác suất đang được chia cho nhiều khả năng hơn.</p>
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

function normalizedUncertainty(entropy: number, classCount: number): number {
  const maximum = Math.log(classCount);
  if (!Number.isFinite(entropy) || !Number.isFinite(maximum) || maximum <= 0) return 0;
  return Math.round(Math.min(1, Math.max(0, entropy / maximum)) * 100);
}
