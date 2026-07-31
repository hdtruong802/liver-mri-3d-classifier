/**
 * Panel `defer` — khối 8 phải của bố cục.
 *
 * `PRODUCT.md` Product Principle 2: "Từ chối là kết quả hợp lệ, không phải lỗi. Khi
 * model `defer`, đó là hành vi đúng và phải được trình bày như một kết quả có giá trị,
 * không phải một thất bại cần giấu." Vì thế panel này chiếm trọn chiều cao cột và là
 * thứ nổi bật nhất trong hàng.
 *
 * Ba tín hiệu độc lập khi `defer` bật: màu, nhãn chữ, icon. Không bao giờ chỉ một —
 * `webapp/DESIGN.md`, The Never-Colour-Alone Rule.
 */

import { AlertTriangle, ShieldCheck } from 'lucide-react';

import type { PredictResult } from '@/api/types';
import { percent } from '@/format';

export function DeferPanel({
  result,
  provisional,
}: {
  result: PredictResult;
  provisional: boolean;
}) {
  const num = provisional ? 'provisional' : '';
  const margin = result.confidence - result.defer_threshold;

  return (
    <section
      aria-labelledby="defer-heading"
      className={[
        'flex flex-col justify-center gap-4 rounded-panel border p-5 lg:col-span-5',
        result.defer ? 'border-warn/50 bg-warn/10' : 'border-ok/40 bg-ok/5',
      ].join(' ')}
    >
      <div className="flex items-start gap-3">
        <span
          className={`grid h-11 w-11 shrink-0 place-items-center rounded-control ${
            result.defer ? 'bg-warn/20' : 'bg-ok/20'
          }`}
        >
          {result.defer ? (
            <AlertTriangle className="h-6 w-6 text-warn" aria-hidden="true" />
          ) : (
            <ShieldCheck className="h-6 w-6 text-ok" aria-hidden="true" />
          )}
        </span>
        <div>
          <h3
            id="defer-heading"
            className={`text-base font-bold ${result.defer ? 'text-warn-soft' : 'text-ok-soft'}`}
          >
            {result.defer ? 'Mô hình từ chối quyết ca này' : 'Mô hình nhận quyết ca này'}
          </h3>
          <p className="mt-1 max-w-measure text-sm text-slate-300">
            {result.defer ? (
              <>
                Confidence <span className={num}>{percent(result.confidence)}%</span> nằm dưới ngưỡng{' '}
                {percent(result.defer_threshold)}%. Theo thiết kế, ca này được chuyển cho bác sĩ đọc
                thay vì nhận một nhãn tự động. Đây là hành vi đúng, không phải lỗi.
              </>
            ) : (
              <>
                Confidence <span className={num}>{percent(result.confidence)}%</span> đạt ngưỡng{' '}
                {percent(result.defer_threshold)}%. Kết quả vẫn cần đối chiếu lâm sàng.
              </>
            )}
          </p>
        </div>
      </div>

      {/* Thanh so ngưỡng: vị trí confidence trên trục 0–100 với vạch ngưỡng có nhãn số. */}
      <div>
        <div className="relative h-2 rounded-full bg-pacs-700">
          <div
            className={`h-full rounded-full ${result.defer ? 'bg-warn' : 'bg-ok'}`}
            style={{ width: `${result.confidence * 100}%` }}
          />
          <span
            className="absolute top-[-4px] h-4 w-0.5 bg-slate-300"
            style={{ left: `${result.defer_threshold * 100}%` }}
            aria-hidden="true"
          />
        </div>
        <div className="mt-2 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
          <span className="text-data text-slate-400">
            Ngưỡng defer <span className="font-mono text-slate-300">{percent(result.defer_threshold)}%</span>
          </span>
          <span className="text-data text-slate-400">
            Hiện tại{' '}
            <span className={`font-mono text-slate-300 ${num}`}>{percent(result.confidence)}%</span>
            {'  '}
            <span className={result.defer ? 'text-warn-soft' : 'text-ok-soft'}>
              ({margin >= 0 ? '+' : '−'}
              {percent(Math.abs(margin))} điểm)
            </span>
          </span>
        </div>
      </div>

      <p className="max-w-measure border-t border-white/10 pt-3 text-data text-slate-400">
        Ngưỡng thật sẽ được khoá trên tập validation từ đường risk-coverage, không chọn tay. Giá trị
        đang dùng chỉ để dựng giao diện.
      </p>
    </section>
  );
}
