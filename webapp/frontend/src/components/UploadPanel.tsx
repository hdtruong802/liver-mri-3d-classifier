/**
 * Tải lên 8 file — ĐƯỜNG PHỤ.
 *
 * Giữ lại từ bản bolt vì kiến trúc thông tin của nó đúng: lưới 8 thì có trạng thái
 * đủ/thiếu, và cổng chặn không cho chạy khi chưa đủ. Sửa hai chỗ:
 *   - danh sách thì lấy từ `GET /api/meta`, không tự khai (bản bolt khai ADC và HBP,
 *     hai thì không có trong LLD-MMRI);
 *   - nêu rõ giới hạn của đường này thay vì để người dùng tưởng nó tương đương
 *     đường ca demo.
 *
 * Nhận diện thì theo token tên file, không theo thứ tự chọn — contract plan §8.1.
 */

import { useMemo, useState } from 'react';

import type { PhaseInfo } from '@/api/types';

interface Props {
  phases: PhaseInfo[];
  busy: boolean;
  onSubmit: (files: File[]) => void;
}

function matchPhase(filename: string, phases: PhaseInfo[]): PhaseInfo | undefined {
  const stem = filename.replace(/\.nii(\.gz)?$/i, '').toLowerCase();
  // Token dài trước token ngắn: 'InPhase' là hậu tố của 'OutPhase'.
  return [...phases]
    .sort((a, b) => b.file_token.length - a.file_token.length)
    .find((p) => stem.includes(p.file_token.toLowerCase()));
}

export function UploadPanel({ phases, busy, onSubmit }: Props) {
  const [files, setFiles] = useState<File[]>([]);

  const byToken = useMemo(() => {
    const map = new Map<string, File>();
    for (const file of files) {
      const phase = matchPhase(file.name, phases);
      if (phase && !map.has(phase.file_token)) map.set(phase.file_token, file);
    }
    return map;
  }, [files, phases]);

  const unmatched = files.filter((f) => !matchPhase(f.name, phases));
  const complete = byToken.size === phases.length;

  return (
    <section aria-labelledby="upload-heading" className="plate p-lg">
      <div className="mb-md border-b-hair border-rule pb-sm">
        <h2 id="upload-heading" className="font-narrow text-headline text-ink">
          Tải lên bộ 8 thì
        </h2>
        <p className="mt-xs max-w-measure text-body text-ink-secondary">
          Đường phụ. Thì được nhận diện theo token trong tên file, không theo thứ tự bạn chọn.
        </p>
        <p className="mt-xs max-w-measure border-hair border-dashed border-ink-tertiary p-sm font-narrow text-legend italic text-ink-secondary">
          Giới hạn đã biết: model được huấn luyện trên vùng cắt bám tổn thương. Đường này chưa có
          ROI của tổn thương nên chưa chạy đúng như lúc train. Dùng ca demo dựng sẵn để xem hành vi
          thật của model.
        </p>
      </div>

      <label className="mb-md inline-block border-hair border-ink bg-land px-md py-sm font-narrow text-legend text-ink hover:bg-shoal-1">
        Chọn file .nii
        <input
          type="file"
          multiple
          accept=".nii,.nii.gz"
          disabled={busy}
          onChange={(event) => setFiles(Array.from(event.target.files ?? []))}
          className="sr-only"
        />
      </label>

      <ol className="grid grid-cols-1 gap-0 border-hair border-hairline sm:grid-cols-2">
        {phases.map((phase) => {
          const file = byToken.get(phase.file_token);
          return (
            <li
              key={phase.file_token}
              className="flex items-baseline justify-between gap-sm border-b-hair border-hairline px-sm py-xs"
            >
              <span className="flex items-baseline gap-sm">
                <span className={`font-narrow text-legend ${file ? 'text-ink' : 'text-ink-tertiary'}`}>
                  {phase.label_vi}
                </span>
                <span className="font-narrow text-marginalia text-ink-tertiary">
                  {phase.description_vi}
                </span>
              </span>
              <span
                className={`shrink-0 font-narrow text-marginalia ${file ? 'text-ink' : 'italic text-ink-tertiary'}`}
              >
                {file ? 'đủ' : 'thiếu'}
              </span>
            </li>
          );
        })}
      </ol>

      {unmatched.length > 0 ? (
        <p className="mt-sm font-narrow text-legend text-caution">
          {unmatched.length} file không nhận ra thì: {unmatched.map((f) => f.name).join(', ')}. Tên file
          phải chứa một trong các token {phases.map((p) => p.file_token).join(', ')}.
        </p>
      ) : null}

      <div className="mt-md flex flex-wrap items-center gap-md border-t-hair border-hairline pt-md">
        <button
          type="button"
          disabled={!complete || busy}
          onClick={() => onSubmit([...byToken.values()])}
          className="border-hair border-ink bg-ink px-md py-sm font-narrow text-legend text-paper disabled:border-hairline disabled:bg-paper disabled:text-ink-tertiary"
        >
          {busy ? 'đang chạy…' : 'Chạy suy luận'}
        </button>
        <span className="font-narrow text-marginalia text-ink-secondary">
          {byToken.size} / {phases.length} thì
          {complete ? '' : ' — cần đủ 8 thì mới chạy được'}
        </span>
      </div>
    </section>
  );
}
