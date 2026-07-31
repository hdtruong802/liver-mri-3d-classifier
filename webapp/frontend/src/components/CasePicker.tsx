/**
 * Bộ chọn ca demo — ĐƯỜNG ĐI CHÍNH của bản demo.
 *
 * `PRODUCT.md` mục *Operating Context*: "Ca demo dựng sẵn (3–5 ca) là đường đi chính,
 * không phải phương án dự phòng."
 *
 * Lý do kỹ thuật, không phải tiện lợi: pipeline train cắt bám tổn thương
 * (`crop_mode: lesion_tight`), nên suy luận cần ROI của tổn thương. Tám file .nii thô
 * người dùng tải lên chưa đủ để chạy đúng như lúc train.
 */

import type { CaseSummary } from '@/api/types';

interface Props {
  cases: CaseSummary[];
  selected: string | null;
  busy: boolean;
  onSelect: (caseId: string) => void;
}

export function CasePicker({ cases, selected, busy, onSelect }: Props) {
  return (
    <section aria-labelledby="cases-heading" className="plate p-lg">
      <div className="mb-md border-b-hair border-rule pb-sm">
        <h2 id="cases-heading" className="font-narrow text-headline text-ink">
          Ca demo dựng sẵn
        </h2>
        <p className="mt-xs max-w-measure text-body text-ink-secondary">
          Đường đi chính. Model được huấn luyện trên vùng cắt bám tổn thương, nên nó cần
          ROI của tổn thương chứ không chỉ tám file thô.
        </p>
      </div>

      <ul className="flex flex-col gap-sm">
        {cases.map((item) => {
          const active = item.case_id === selected;
          return (
            <li key={item.case_id}>
              <button
                type="button"
                disabled={!item.available || busy}
                onClick={() => onSelect(item.case_id)}
                aria-current={active ? 'true' : undefined}
                className={[
                  'flex w-full flex-col items-start gap-xs border-hair p-md text-left',
                  active ? 'border-ink bg-land' : 'border-hairline bg-paper',
                  item.available && !busy ? 'hover:border-rule' : 'cursor-not-allowed',
                ].join(' ')}
              >
                <span className="flex w-full flex-wrap items-baseline justify-between gap-sm">
                  <span className="font-narrow text-headline text-ink">{item.case_id}</span>
                  <span className="font-narrow text-marginalia text-ink-secondary">
                    {item.available ? (active ? 'đang xem' : 'chọn để đọc') : 'không có dữ liệu trên máy này'}
                  </span>
                </span>
                <span className="font-narrow text-legend text-ink-secondary">{item.label_vi}</span>
                <span className="max-w-measure text-body text-ink-secondary">{item.source_note}</span>
              </button>
            </li>
          );
        })}
      </ul>

      {cases.every((c) => !c.available) ? (
        <p className="mt-md border-hair border-dashed border-ink-tertiary p-md font-narrow text-legend italic text-ink-secondary">
          Không ca nào có dữ liệu trên máy này. Thư mục <code>data/</code> nằm ngoài git vì chứa
          ảnh bệnh nhân thật. Đặt biến <code>LLDMMRI_SAMPLE_DIR</code> trỏ tới thư mục chứa 8 file
          <code> .nii</code> của một ca.
        </p>
      ) : null}
    </section>
  );
}
