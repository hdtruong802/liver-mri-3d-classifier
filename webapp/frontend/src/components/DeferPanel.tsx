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
 *
 * ## Vì sao panel này có HAI chế độ
 *
 * `defer_basis` quyết định đại lượng nào được so với ngưỡng, và **chiều so sánh ngược
 * nhau**:
 *
 * - `confidence` — thấp hơn ngưỡng thì từ chối. Dùng cho nhánh mô phỏng.
 * - `epistemic` — CAO hơn ngưỡng thì từ chối. Dùng cho dự đoán out-of-fold thật.
 *
 * Trộn hai cái vào một cách hiển thị là nói sai. Ca `MR207769` có confidence 62% và
 * bị từ chối; nếu panel cứ vẽ "confidence dưới ngưỡng 17%" thì con số trên màn hình
 * mâu thuẫn với nhau và người đọc sẽ kết luận app hỏng. Lý do thật: mức bất đồng giữa
 * các lượt dự đoán cao, và đó là đại lượng duy nhất đo được là có tác dụng xếp hạng ca
 * khó (WORKLOG S-087: max-prob cho −0.003, P=0.88; epistemic cho +0.035, P=0.030).
 */

import { AlertTriangle, ShieldCheck } from 'lucide-react';

import type { PredictResult } from '@/api/types';
import { percent } from '@/format';

/** Thang hiển thị của trục epistemic. Bất định vượt mức này là đã rất cao. */
const EPISTEMIC_FULL_SCALE = 0.5;

export function DeferPanel({
  result,
  provisional,
}: {
  result: PredictResult;
  provisional: boolean;
}) {
  const num = provisional ? 'provisional' : '';
  const byEpistemic = result.defer_basis === 'epistemic';

  // Vị trí trên trục 0–100%. Confidence vốn đã là tỉ lệ; epistemic là nat nên phải
  // quy về thang hiển thị, và có thể vượt trần -> kẹp lại.
  const toPercent = (v: number) =>
    byEpistemic ? Math.min(100, (v / EPISTEMIC_FULL_SCALE) * 100) : v * 100;

  const scoreLabel = byEpistemic ? 'Bất định giữa các lượt' : 'Confidence';
  const scoreText = byEpistemic ? result.defer_score.toFixed(3) : `${percent(result.defer_score)}%`;
  const thresholdText = byEpistemic
    ? result.defer_threshold.toFixed(3)
    : `${percent(result.defer_threshold)}%`;

  // Khoảng cách tới ngưỡng, luôn tính theo hướng "dương = an toàn".
  const margin = byEpistemic
    ? result.defer_threshold - result.defer_score
    : result.defer_score - result.defer_threshold;
  const marginText = byEpistemic
    ? Math.abs(margin).toFixed(3)
    : `${percent(Math.abs(margin))} điểm`;

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
            {byEpistemic ? (
              result.defer ? (
                <>
                  Các lượt dự đoán <strong className="text-warn-soft">bất đồng với nhau</strong>{' '}
                  (<span className={`font-mono ${num}`}>{scoreText}</span>, trên ngưỡng{' '}
                  {thresholdText}). Ca này được chuyển cho bác sĩ đọc. Đây là hành vi đúng, không
                  phải lỗi.
                </>
              ) : (
                <>
                  Các lượt dự đoán <strong className="text-ok-soft">đồng thuận</strong>{' '}
                  (<span className={`font-mono ${num}`}>{scoreText}</span>, dưới ngưỡng{' '}
                  {thresholdText}). Kết quả vẫn cần đối chiếu lâm sàng.
                </>
              )
            ) : result.defer ? (
              <>
                Confidence <span className={num}>{scoreText}</span> nằm dưới ngưỡng {thresholdText}.
                Ca này được chuyển cho bác sĩ đọc thay vì nhận một nhãn tự động.
              </>
            ) : (
              <>
                Confidence <span className={num}>{scoreText}</span> đạt ngưỡng {thresholdText}. Kết
                quả vẫn cần đối chiếu lâm sàng.
              </>
            )}
          </p>

          {/* Chỗ dễ hiểu nhầm nhất của cả màn hình: xác suất cao mà vẫn bị từ chối.
              Nói thẳng ra, đừng để người đọc tự suy. */}
          {byEpistemic && result.defer && result.confidence >= 0.6 && (
            <p className="mt-2 max-w-measure text-data text-slate-400">
              Lưu ý: xác suất hiển thị {percent(result.confidence)}% <em>không</em> mâu thuẫn với
              quyết định này. Quyết định từ chối dựa trên mức bất đồng giữa các lượt dự đoán, không
              dựa trên xác suất — hai đại lượng khác nhau, và chỉ đại lượng thứ nhất được đo là có
              tác dụng phát hiện ca khó.
            </p>
          )}
        </div>
      </div>

      {/* Thanh so ngưỡng. Với epistemic, thanh dài ra là XẤU đi — nhãn hai đầu nói rõ
          chiều, vì một thanh tiến triển mặc định được đọc là "càng dài càng tốt". */}
      <div>
        <div className="relative h-2 rounded-full bg-pacs-700">
          <div
            className={`h-full rounded-full ${result.defer ? 'bg-warn' : 'bg-ok'}`}
            style={{ width: `${toPercent(result.defer_score)}%` }}
          />
          <span
            className="absolute top-[-4px] h-4 w-0.5 bg-slate-300"
            style={{ left: `${toPercent(result.defer_threshold)}%` }}
            aria-hidden="true"
          />
        </div>
        {byEpistemic && (
          <div className="mt-1 flex justify-between text-data text-slate-500">
            <span>đồng thuận</span>
            <span>bất đồng</span>
          </div>
        )}
        <div className="mt-2 flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
          <span className="text-data text-slate-400">
            Ngưỡng <span className="font-mono text-slate-300">{thresholdText}</span>
          </span>
          <span className="text-data text-slate-400">
            {scoreLabel} <span className={`font-mono text-slate-300 ${num}`}>{scoreText}</span>{' '}
            <span className={result.defer ? 'text-warn-soft' : 'text-ok-soft'}>
              ({margin >= 0 ? 'còn cách' : 'vượt'} {marginText})
            </span>
          </span>
        </div>
      </div>

      <p className="max-w-measure border-t border-white/10 pt-3 text-data text-slate-400">
        {byEpistemic ? (
          <>
            Ngưỡng là phân vị bất định ở mức coverage 80% trên tập validation — chọn trước, không
            chỉnh theo kết quả. Ở mức này, từ chối bắt được 39/117 ca model đoán sai và từ chối nhầm
            40/277 ca đoán đúng.
          </>
        ) : (
          <>
            Ngưỡng thật sẽ được khoá trên tập validation từ đường risk-coverage, không chọn tay. Giá
            trị đang dùng chỉ để dựng giao diện.
          </>
        )}
      </p>
    </section>
  );
}
