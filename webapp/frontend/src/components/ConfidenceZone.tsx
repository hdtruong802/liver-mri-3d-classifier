/**
 * Sơ đồ Zone of Confidence — panel `defer`.
 *
 * Hải đồ có một khối riêng nói tấm bản đồ này đáng tin tới đâu ở từng vùng: Zone of
 * Confidence, ZOC A1 tới D, cộng vùng chưa khảo sát. Người đi biển đọc nó để biết
 * chỗ nào không nên đi vào. Đây đúng là selective prediction, đã là quy ước xuất bản
 * có thật, nên panel `defer` được dựng theo nó chứ không theo một gauge tròn.
 *
 * `PRODUCT.md` Product Principle 2: "Từ chối là kết quả hợp lệ, không phải lỗi. Khi
 * model `defer`, đó là hành vi đúng và phải được trình bày như một kết quả có giá
 * trị, không phải một thất bại cần giấu." Vì thế panel này được phép to nhất màn hình.
 *
 * Khi `defer` bật: BA tín hiệu độc lập — overprint magenta, nhãn chữ, ký hiệu hình
 * thoi. Không bao giờ chỉ một.
 */

import type { PredictResult } from '@/api/types';
import { MarkCaution } from '@/components/ChartMarks';
import { decimal, percent } from '@/format';

/** Năm dải tin cậy, theo tinh thần ZOC A1..D của hải đồ. Lam đậm = cảnh giác cao hơn. */
const ZONES = [
  { id: 'A1', floor: 0.85, label: 'rất cao', band: 'bg-paper' },
  { id: 'A2', floor: 0.7, label: 'cao', band: 'bg-shoal-1' },
  { id: 'B', floor: 0.55, label: 'trung bình', band: 'bg-shoal-2' },
  { id: 'C', floor: 0.35, label: 'thấp', band: 'bg-shoal-3' },
  { id: 'D', floor: 0.0, label: 'rất thấp', band: 'bg-shoal-3' },
] as const;

function zoneOf(confidence: number) {
  return ZONES.find((z) => confidence >= z.floor) ?? ZONES[ZONES.length - 1];
}

export function ConfidenceZone({ result, provisional }: { result: PredictResult; provisional: boolean }) {
  const zone = zoneOf(result.confidence);
  const num = provisional ? 'provisional' : '';

  return (
    <section
      aria-labelledby="zoc-heading"
      className={`plate p-lg ${result.defer ? 'overprint-caution' : ''}`}
    >
      <div className="mb-md flex items-baseline justify-between gap-md border-b-hair border-rule pb-sm">
        <h2 id="zoc-heading" className="font-narrow text-headline text-ink">
          Mức tin cậy của ca này
        </h2>
        <p className="font-narrow text-marginalia text-ink-tertiary">
          dải {zone.id} · {zone.label}
        </p>
      </div>

      {/* Kết luận defer đứng trước mọi con số: đây là thông tin quan trọng nhất. */}
      {result.defer ? (
        <div className="mb-md flex items-start gap-sm border-hair border-caution bg-paper p-md">
          <MarkCaution className="mt-[3px] h-[16px] w-[16px] shrink-0 text-caution" />
          <div>
            <p className="font-narrow text-headline text-caution">Model từ chối quyết ca này</p>
            <p className="mt-xs max-w-measure text-body text-ink-secondary">
              Confidence <span className={num}>{percent(result.confidence)}%</span> nằm dưới ngưỡng{' '}
              <span>{percent(result.defer_threshold)}%</span>. Theo thiết kế, ca này được chuyển cho
              bác sĩ đọc thay vì nhận một nhãn tự động. Đây là hành vi đúng, không phải lỗi.
            </p>
          </div>
        </div>
      ) : (
        <div className="mb-md border-hair border-hairline bg-paper p-md">
          <p className="font-narrow text-headline text-ink">Model nhận quyết ca này</p>
          <p className="mt-xs max-w-measure text-body text-ink-secondary">
            Confidence <span className={num}>{percent(result.confidence)}%</span> đạt ngưỡng{' '}
            <span>{percent(result.defer_threshold)}%</span>. Kết quả vẫn cần đối chiếu lâm sàng.
          </p>
        </div>
      )}

      {/* Thang dải tin cậy. Mỗi dải có nhãn chữ riêng — màu không làm việc một mình. */}
      <ol className="flex flex-col border-hair border-hairline">
        {ZONES.map((z) => {
          const active = z.id === zone.id;
          return (
            <li
              key={z.id}
              aria-current={active ? 'true' : undefined}
              className={`flex items-baseline justify-between gap-md border-b-hair border-hairline px-sm py-xs last:border-b-0 ${z.band}`}
            >
              <span className="flex items-baseline gap-sm">
                <span
                  className={`font-narrow text-legend ${active ? 'font-semibold text-ink' : 'text-ink-secondary'}`}
                >
                  {z.id}
                </span>
                <span className={`font-narrow text-marginalia ${active ? 'text-ink' : 'text-ink-tertiary'}`}>
                  {z.label}
                </span>
                {active ? (
                  <span className="font-narrow text-marginalia text-ink">← ca này</span>
                ) : null}
              </span>
              <span className={`font-narrow text-marginalia ${active ? 'text-ink' : 'text-ink-tertiary'}`}>
                ≥ {percent(z.floor, 0)}%
              </span>
            </li>
          );
        })}
      </ol>

      {/* Đường đẳng sâu = ngưỡng defer. Trên hải đồ, đường đẳng sâu có nhãn số. */}
      <p className="mt-sm border-t-mark border-dashed border-rule pt-sm font-narrow text-marginalia text-ink-secondary">
        Đường ngưỡng defer: {percent(result.defer_threshold)}%. Ngưỡng thật sẽ được khoá trên
        validation từ đường risk-coverage, không chọn tay.
      </p>

      <dl className="mt-md grid grid-cols-2 gap-md border-t-hair border-hairline pt-md">
        <div>
          <dt className="font-narrow text-marginalia text-ink-tertiary">Shannon entropy</dt>
          <dd className={`text-sounding text-ink ${num}`}>
            {decimal(result.uncertainty.entropy)}
            <span className="ml-xs font-narrow text-marginalia text-ink-tertiary">nat</span>
          </dd>
        </div>
        <div>
          <dt className="font-narrow text-marginalia text-ink-tertiary">Xác suất nhóm ác</dt>
          <dd className={`text-sounding text-ink ${num}`}>
            {percent(result.malignant_prob)}
            <span className="ml-[2px] font-narrow text-marginalia text-ink-tertiary">%</span>
          </dd>
        </div>
        <div className="col-span-2">
          <dt className="font-narrow text-marginalia text-ink-tertiary">
            Độ lệch chuẩn giữa các thành viên ensemble
          </dt>
          <dd className="font-narrow text-legend italic text-ink-secondary">
            {result.uncertainty.ensemble_std === null
              ? 'chưa có, đang chạy một model đơn lẻ'
              : decimal(result.uncertainty.ensemble_std)}
          </dd>
        </div>
      </dl>
    </section>
  );
}
