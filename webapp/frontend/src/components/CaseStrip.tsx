/**
 * Dải chọn ca demo — ĐƯỜNG ĐI CHÍNH, đặt ngay trên lưới 8 thì.
 *
 * `PRODUCT.md` mục *Operating Context*: "Ca demo dựng sẵn (3–5 ca) là đường đi chính,
 * không phải phương án dự phòng." Lý do kỹ thuật: pipeline huấn luyện cắt bám tổn
 * thương (`crop_mode: lesion_tight`), nên suy luận cần ROI. Tám file .nii thô người
 * dùng tải lên chưa đủ để chạy đúng như lúc train.
 */

import { FolderOpen, Loader2 } from 'lucide-react';

import type { CaseSummary } from '@/api/types';

interface Props {
  cases: CaseSummary[];
  selected: string | null;
  busy: boolean;
  onSelect: (caseId: string) => void;
}

export function CaseStrip({ cases, selected, busy, onSelect }: Props) {
  const noneAvailable = cases.length > 0 && cases.every((item) => !item.available);

  return (
    <section aria-labelledby="cases-heading" className="mt-6">
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <FolderOpen className="h-5 w-5 text-accent" aria-hidden="true" />
        <h2 id="cases-heading" className="text-lg font-bold text-white">
          Ca demo dựng sẵn
        </h2>
      </div>

      <div className="border-y border-pacs-700">
        {cases.map((item) => {
          const active = item.case_id === selected;
          return (
            <button
              key={item.case_id}
              type="button"
              disabled={!item.available || busy}
              aria-current={active ? 'true' : undefined}
              onClick={() => onSelect(item.case_id)}
              className={[
                'grid w-full gap-3 border-b border-pacs-700 px-4 py-3 text-left transition last:border-b-0 sm:grid-cols-[10rem_minmax(0,1fr)_auto] sm:items-center sm:gap-5',
                active
                  ? 'bg-pacs-900'
                  : 'hover:bg-pacs-900/60',
                item.available && !busy ? '' : 'cursor-not-allowed opacity-70',
              ].join(' ')}
            >
              <span className={`font-mono text-sm font-semibold ${active ? 'text-accent-glow' : 'text-white'}`}>{item.case_id}</span>
              <span className="min-w-0">
                <span className="block text-sm font-semibold text-slate-200">{item.label_vi}</span>
                <span className="mt-1 block text-data leading-5 text-slate-400">
                  {item.source_note}
                </span>
              </span>
              <span
                className={
                  active
                    ? 'chip shrink-0 bg-accent/20 text-accent-glow'
                    : 'chip shrink-0 border border-pacs-600 bg-pacs-800 text-slate-400'
                }
              >
                {busy && active ? (
                  <>
                    <Loader2 className="h-3 w-3 animate-spin" aria-hidden="true" />
                    đang đọc
                  </>
                ) : item.available ? (
                  active ? 'đang xem' : 'chọn để đọc'
                ) : (
                  'không có dữ liệu'
                )}
              </span>
            </button>
          );
        })}
      </div>

      {noneAvailable ? (
        <p className="workstation-inset mt-3 max-w-measure border-dashed p-4 text-data text-slate-400">
          Không ca nào có dữ liệu trên máy này. Thư mục <code className="font-mono">data/</code> nằm
          ngoài git vì chứa ảnh MRI của bệnh nhân thật. Đặt biến{' '}
          <code className="font-mono">LLDMMRI_SAMPLE_DIR</code> trỏ tới thư mục chứa 8 file{' '}
          <code className="font-mono">.nii</code> của một ca.
        </p>
      ) : null}
    </section>
  );
}
