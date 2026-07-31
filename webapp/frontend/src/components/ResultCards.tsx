/**
 * Ba thẻ kết quả trên cùng — khối 7 của bố cục, tỉ lệ cột 5 / 4 / 3 như ảnh tham chiếu.
 *
 * Hai chỗ nội dung khác bản bolt, đều vì lý do sự thật chứ không phải thẩm mỹ:
 *
 *   - Thẻ donut: bản bolt kết bằng "Nguy cơ ác tính cao — cần sinh thiết". Đó là câu
 *     CHỈ ĐỊNH LÂM SÀNG, vi phạm RUO (`AGENTS.md` §3.1). Thay bằng câu mô tả đúng con
 *     số đang hiển thị là gì.
 *   - Thẻ bất định: bản bolt vẽ hai thanh `Epistemic` và `Aleatoric`. Pipeline này
 *     KHÔNG phân rã bất định như vậy, nên báo hai chỉ số đó là bịa một đại lượng chưa
 *     từng được đo. Giữ nguyên hình dáng thẻ, đổi sang hai đại lượng thật sự tính
 *     được: `confidence` (max-prob) và entropy chuẩn hoá.
 */

import { Activity, Brain, ShieldAlert, ShieldCheck, TrendingUp } from 'lucide-react';

import type { PredictResult } from '@/api/types';
import { colorOfClass } from '@/catalog';
import { decimal, percent } from '@/format';

const NUM_CLASSES = 7;
const MAX_ENTROPY = Math.log(NUM_CLASSES); // ~1,9459 nat khi phân phối đều

interface CardProps {
  result: PredictResult;
  provisional: boolean;
}

/** Lớp dự đoán. 5 cột. */
export function PredictionCard({ result, provisional }: CardProps) {
  const leader = result.probs.find((p) => p.class_index === result.pred_class_index);
  if (!leader) return null;
  const color = colorOfClass(leader.class_index);
  const Icon = leader.malignant ? ShieldAlert : ShieldCheck;

  return (
    <section aria-labelledby="pred-heading" className="panel p-5 lg:col-span-5">
      <div className="mb-4 flex items-center gap-2">
        <Activity className="h-4 w-4 text-accent" aria-hidden="true" />
        <h3 id="pred-heading" className="label">
          Lớp dự đoán
        </h3>
      </div>

      <div className="flex items-center gap-4">
        <span
          className="grid h-16 w-16 shrink-0 place-items-center rounded-panel border-2"
          style={{ borderColor: color }}
        >
          <Icon className="h-8 w-8" style={{ color }} aria-hidden="true" />
        </span>
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h2 className={`text-2xl font-bold text-white ${provisional ? 'provisional' : ''}`}>
              {leader.label_vi}
            </h2>
            <span
              className="chip border"
              style={{ borderColor: `${color}66`, color, backgroundColor: `${color}1A` }}
            >
              {leader.malignant ? 'ác tính' : 'lành tính'}
            </span>
          </div>
          <p className="mt-1 text-data text-slate-400">{leader.class_name.replace(/_/g, ' ')}</p>
        </div>
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-3">
        <div className="inset-box px-3 py-2">
          <dt className="text-data text-slate-400">Mô hình</dt>
          <dd className="font-mono text-data text-slate-300">
            {result.provenance.model_version ?? 'chưa nạp checkpoint'}
          </dd>
        </div>
        <div className="inset-box px-3 py-2">
          <dt className="text-data text-slate-400">Thời gian suy luận</dt>
          <dd className="font-mono text-data text-slate-300">
            {result.inference_ms === null ? 'không đo' : `${result.inference_ms} ms`}
          </dd>
        </div>
      </dl>
    </section>
  );
}

/** Xác suất nhóm ác, donut. 4 cột. */
export function MalignancyGauge({ result, provisional }: CardProps) {
  const value = result.malignant_prob;
  const radius = 52;
  const circumference = 2 * Math.PI * radius;

  return (
    <section aria-labelledby="mal-heading" className="panel p-5 lg:col-span-4">
      <div className="mb-4 flex items-center gap-2">
        <TrendingUp className="h-4 w-4 text-danger" aria-hidden="true" />
        <h3 id="mal-heading" className="label">
          Xác suất nhóm ác
        </h3>
      </div>

      <div className="flex flex-col items-center gap-3">
        <div className="relative h-32 w-32">
          <svg viewBox="0 0 120 120" className="h-full w-full -rotate-90" aria-hidden="true">
            <circle cx="60" cy="60" r={radius} fill="none" stroke="#1C2540" strokeWidth="10" />
            <circle
              cx="60"
              cy="60"
              r={radius}
              fill="none"
              stroke="#FB7185"
              strokeWidth="10"
              strokeLinecap="round"
              strokeDasharray={`${value * circumference} ${circumference}`}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`text-metric font-bold text-white ${provisional ? 'provisional' : ''}`}>
              {percent(value, 0)}%
            </span>
            <span className="text-data text-slate-400">nhóm ác</span>
          </div>
        </div>
        {/* Câu MÔ TẢ con số, không phải khuyến nghị hành động. */}
        <p className="max-w-measure text-center text-data text-slate-400">
          Tổng xác suất ba lớp ác tính: ICC, di căn, HCC. Không phải một khuyến nghị lâm sàng.
        </p>
      </div>
    </section>
  );
}

/** Mức bất định. 3 cột. */
export function UncertaintyCard({ result, provisional }: CardProps) {
  const normalisedEntropy = Math.min(result.uncertainty.entropy / MAX_ENTROPY, 1);
  const num = provisional ? 'provisional' : '';

  return (
    <section aria-labelledby="unc-heading" className="panel p-5 lg:col-span-3">
      <div className="mb-4 flex items-center gap-2">
        <Brain className="h-4 w-4 text-accent" aria-hidden="true" />
        <h3 id="unc-heading" className="label">
          Mức bất định
        </h3>
      </div>

      <div className="space-y-4">
        <Meter
          label="Confidence"
          hint="xác suất của lớp dẫn đầu"
          value={result.confidence}
          display={`${percent(result.confidence)}%`}
          color="#22D3EE"
          numClass={num}
        />
        <Meter
          label="Entropy chuẩn hoá"
          hint="0 là chắc chắn, 1 là phân phối đều"
          value={normalisedEntropy}
          display={decimal(normalisedEntropy, 2)}
          color="#FBBF24"
          numClass={num}
        />

        <div className="inset-box px-3 py-2">
          <p className="text-data text-slate-400">Shannon entropy</p>
          <p className={`font-mono text-sm text-slate-300 ${num}`}>
            {decimal(result.uncertainty.entropy)} nat
          </p>
        </div>
        <div className="inset-box px-3 py-2">
          <p className="text-data text-slate-400">Độ lệch chuẩn ensemble</p>
          <p className="font-mono text-data italic text-slate-400">
            {result.uncertainty.ensemble_std === null
              ? 'chưa có, đang chạy một model đơn lẻ'
              : decimal(result.uncertainty.ensemble_std)}
          </p>
        </div>
      </div>
    </section>
  );
}

function Meter({
  label,
  hint,
  value,
  display,
  color,
  numClass,
}: {
  label: string;
  hint: string;
  value: number;
  display: string;
  color: string;
  numClass: string;
}) {
  return (
    <div>
      <div className="mb-1 flex items-baseline justify-between gap-2">
        <span className="text-data text-slate-300">{label}</span>
        <span className={`text-data font-semibold text-white ${numClass}`}>{display}</span>
      </div>
      <div
        className="h-2 overflow-hidden rounded-full bg-pacs-700"
        role="meter"
        aria-valuenow={Math.round(value * 100)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${label}: ${display}`}
      >
        <div
          className="h-full rounded-full"
          style={{ width: `${value * 100}%`, backgroundColor: color }}
        />
      </div>
      <p className="mt-1 text-data text-slate-400">{hint}</p>
    </div>
  );
}
