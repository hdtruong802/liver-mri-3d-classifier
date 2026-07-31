/**
 * Trường sounding — phân phối 7 lớp, thiết bị chính của màn hình kết quả.
 *
 * Trên hải đồ, độ sâu không được vẽ thành bề mặt đã làm mượt: từng con số đo thật
 * được IN RA, dày đặc, khắp mặt biển. Con số là nội dung, dải màu chỉ là phụ trợ.
 * Đó đúng là nguyên tắc "số liệu là nhân vật chính" của dự án này, nên bảng xác suất
 * được dựng như một trường sounding chứ không phải một bar chart.
 *
 * Ba điều tránh, đều là chỗ bản bolt hỏng:
 *   - mỗi lớp một màu riêng (7 hex) — phá ngân sách màu, và vô nghĩa với người mù màu;
 *   - lớp dẫn đầu nhấn bằng màu — ở đây nhấn bằng CỠ CHỮ và ĐỘ ĐẬM NÉT;
 *   - giấu các lớp xác suất thấp — hải đồ không giấu sounding nông, và một xác suất
 *     0,3% vẫn là thông tin về hình dạng phân phối.
 */

import type { ClassProbability } from '@/api/types';
import { MarkBenign, MarkMalignant } from '@/components/ChartMarks';
import { groupLabel, percent } from '@/format';

interface Props {
  probs: ClassProbability[];
  /** Số giả lập thì mọi con số ở đây phải nghiêng. */
  provisional: boolean;
}

export function SoundingField({ probs, provisional }: Props) {
  // Sắp giảm dần: người review cần tìm lớp dẫn đầu trong một nhịp mắt. Thứ tự
  // taxonomy giữ được tính "vị trí cố định" của hải đồ nhưng đắt hơn khi quét.
  const ordered = [...probs].sort((a, b) => b.probability - a.probability);
  const leader = ordered[0];

  return (
    <section aria-labelledby="sounding-heading">
      <div className="mb-md flex items-baseline justify-between gap-md border-b-hair border-rule pb-sm">
        <h2 id="sounding-heading" className="font-narrow text-headline text-ink">
          Xác suất từng lớp
        </h2>
        <p className="font-narrow text-marginalia text-ink-tertiary">
          {probs.length} lớp tổn thương · tổng bằng 100%
        </p>
      </div>

      <ol className="flex flex-col">
        {ordered.map((entry) => {
          const isLeader = entry.class_index === leader.class_index;
          return (
            <li
              key={entry.class_index}
              className="grid grid-cols-[12px_1fr_auto] items-baseline gap-x-md border-b-hair border-hairline py-sm last:border-b-0"
            >
              <span className={isLeader ? 'text-ink' : 'text-ink-tertiary'}>
                {entry.malignant ? (
                  <MarkMalignant className="h-[12px] w-[12px]" />
                ) : (
                  <MarkBenign className="h-[12px] w-[12px]" />
                )}
              </span>

              <span className="min-w-0">
                <span
                  className={`font-narrow ${isLeader ? 'text-headline text-ink' : 'text-body text-ink-secondary'}`}
                >
                  {entry.label_vi}
                </span>{' '}
                <span className="font-narrow text-marginalia text-ink-tertiary">
                  {groupLabel(entry.malignant)}
                </span>
                {isLeader ? (
                  <span className="ml-sm font-narrow text-marginalia text-ink-secondary">
                    lớp dẫn đầu
                  </span>
                ) : null}
              </span>

              <span
                className={[
                  'justify-self-end',
                  isLeader ? 'text-sounding-lead font-medium text-ink' : 'text-sounding text-ink-secondary',
                  provisional ? 'provisional' : '',
                ].join(' ')}
              >
                {percent(entry.probability)}
                <span className="ml-[2px] font-narrow text-marginalia text-ink-tertiary">%</span>
              </span>

              {/* Dải đo: phụ trợ, cao 4px, không bao giờ cạnh tranh với con số. */}
              <span className="col-start-2 col-span-2 mt-xs h-[4px] bg-shoal-1" aria-hidden="true">
                <span
                  className={`block h-full ${isLeader ? 'bg-shoal-3' : 'bg-shoal-2'}`}
                  style={{ width: `${Math.max(entry.probability * 100, 0.4)}%` }}
                />
              </span>
            </li>
          );
        })}
      </ol>
    </section>
  );
}
