/**
 * Lưới 8 thì cộng thanh chạy phân tích — khối 5 và 6 của bố cục.
 *
 * Nhận diện thì theo **token trong tên file**, không theo thứ tự chọn (contract
 * `docs/liver_mri_3d_classification_plan.md` §8.1). Khớp token DÀI trước token ngắn:
 * `InPhase` là hậu tố của `OutPhase`, khớp ngược lại sẽ gán sai thì một cách im lặng
 * và hoán hai kênh đầu vào của model.
 */

import { useMemo, useState } from 'react';
import { AlertTriangle, CheckCircle2, Layers, Loader2, Sparkles } from 'lucide-react';

import type { PhaseInfo } from '@/api/types';
import { PhaseCard } from '@/components/PhaseCard';

interface Props {
  phases: PhaseInfo[];
  busy: boolean;
  onSubmit: (files: File[]) => void;
}

function matchPhase(filename: string, phases: PhaseInfo[]): PhaseInfo | undefined {
  const stem = filename.replace(/\.nii(\.gz)?$/i, '').toLowerCase();
  return [...phases]
    .sort((a, b) => b.file_token.length - a.file_token.length)
    .find((phase) => stem.includes(phase.file_token.toLowerCase()));
}

export function PhaseGrid({ phases, busy, onSubmit }: Props) {
  const [files, setFiles] = useState<Record<string, File>>({});
  const [rejected, setRejected] = useState<string[]>([]);

  const filledCount = Object.keys(files).length;
  const complete = filledCount === phases.length;

  const assign = (fallback: PhaseInfo, file: File) => {
    const matched = matchPhase(file.name, phases);
    if (matched && matched.file_token !== fallback.file_token) {
      // Tên file nói nó là thì khác với ô người dùng vừa thả vào. Tin tên file, đúng
      // như contract, và nói ra chứ không im lặng gán.
      setRejected((prev) => [
        ...prev.filter((m) => !m.startsWith(file.name)),
        `${file.name} được nhận là thì ${matched.label_vi} theo tên file, không phải ${fallback.label_vi}.`,
      ]);
    }
    const target = matched ?? fallback;
    setFiles((prev) => ({ ...prev, [target.file_token]: file }));
  };

  const clear = (token: string) =>
    setFiles((prev) => {
      const next = { ...prev };
      delete next[token];
      return next;
    });

  const ordered = useMemo(() => phases.map((phase) => ({ phase, file: files[phase.file_token] ?? null })), [phases, files]);

  return (
    <section aria-labelledby="phases-heading" className="mt-6">
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Layers className="h-5 w-5 text-accent" aria-hidden="true" />
        <h2 id="phases-heading" className="text-lg font-bold text-white">
          Tải lên dữ liệu theo từng thì
        </h2>
        <span className="chip border border-pacs-600 bg-pacs-800 text-slate-400">
          {phases.length} chuỗi xung bắt buộc
        </span>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {ordered.map(({ phase, file }) => (
          <PhaseCard
            key={phase.file_token}
            phase={phase}
            file={file}
            disabled={busy}
            onFile={(picked) => assign(phase, picked)}
            onClear={() => clear(phase.file_token)}
          />
        ))}
      </div>

      {rejected.length > 0 ? (
        <ul className="mt-3 space-y-1">
          {rejected.map((message) => (
            <li key={message} className="text-data text-warn-soft">
              {message}
            </li>
          ))}
        </ul>
      ) : null}

      <div className="panel-elevated mt-5 flex flex-col gap-4 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-start gap-3">
          <span
            className={`grid h-11 w-11 shrink-0 place-items-center rounded-control ${
              complete ? 'bg-ok/15' : 'bg-pacs-700'
            }`}
          >
            {complete ? (
              <CheckCircle2 className="h-6 w-6 text-ok" aria-hidden="true" />
            ) : (
              <AlertTriangle className="h-6 w-6 text-warn" aria-hidden="true" />
            )}
          </span>
          <div>
            <p className="text-sm font-semibold text-white">
              {complete ? 'Đủ 8 thì, chạy được' : `Còn thiếu ${phases.length - filledCount} thì`}
            </p>
            <p className="max-w-measure text-data text-slate-400">
              Đường này chưa có ROI của tổn thương nên chưa chạy đúng như lúc huấn luyện. Dùng ca
              demo dựng sẵn ở trên để xem hành vi thật của mô hình.
            </p>
          </div>
        </div>

        <button
          type="button"
          disabled={!complete || busy}
          onClick={() => onSubmit(Object.values(files))}
          className="btn-primary w-full sm:w-auto"
        >
          {busy ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
              Đang chạy
            </>
          ) : (
            <>
              <Sparkles className="h-4 w-4" aria-hidden="true" />
              Chạy phân tích
            </>
          )}
        </button>
      </div>
    </section>
  );
}
