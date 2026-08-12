import { useRef, useState, type ChangeEvent } from 'react';
import { Archive, CheckCircle2, FileUp, XCircle } from 'lucide-react';

import { ApiError, validateUpload } from '@/api/client';
import type { UploadPhaseState, UploadValidationResult } from '@/api/types';

const stateLabel: Record<UploadPhaseState, string> = {
  ready: 'đủ',
  missing: 'thiếu',
  duplicate: 'trùng',
};

export function ZipUpload() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [archive, setArchive] = useState<File | null>(null);
  const [result, setResult] = useState<UploadValidationResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const chooseArchive = () => inputRef.current?.click();

  const onSelect = (event: ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0] ?? null;
    setArchive(selected);
    setResult(null);
    setError(null);
  };

  const validate = async () => {
    if (!archive) return;
    setBusy(true);
    setError(null);
    try {
      setResult(await validateUpload(archive));
    } catch (cause) {
      setResult(null);
      setError(cause instanceof ApiError ? cause.message : String(cause));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section aria-labelledby="upload-heading" className="mt-8 panel p-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Archive className="h-5 w-5 text-accent" aria-hidden="true" />
            <h2 id="upload-heading" className="text-lg font-bold text-white">
              Tải bộ MRI (.zip)
            </h2>
          </div>
          <p className="mt-2 max-w-measure text-sm text-slate-300">
            ZIP phải chứa đúng một file <span className="font-mono">.nii</span> hoặc{' '}
            <span className="font-mono">.nii.gz</span> cho mỗi 8 thì bắt buộc. Thư mục bên trong
            không quan trọng; tên file phải cho phép nhận diện thì.
          </p>
        </div>
        <span className="chip border border-pacs-700 bg-pacs-800 text-slate-300">8 thì bắt buộc</span>
      </div>

      <input
        ref={inputRef}
        className="sr-only"
        type="file"
        accept=".zip,application/zip"
        onChange={onSelect}
        aria-label="Chọn file ZIP bộ MRI"
      />

      <div className="mt-5 flex flex-wrap items-center gap-3 rounded-control border border-dashed border-pacs-600 bg-pacs-950/50 p-4">
        <FileUp className="h-5 w-5 shrink-0 text-accent" aria-hidden="true" />
        <div className="min-w-0 flex-1">
          <p className="truncate font-mono text-sm font-semibold text-white">
            {archive ? archive.name : 'Chưa chọn file ZIP'}
          </p>
          <p className="text-data text-slate-400">
            {archive ? 'Sẵn sàng kiểm tra cấu trúc 8 thì.' : 'Không hỗ trợ folder picker ở V1.'}
          </p>
        </div>
        <button type="button" onClick={chooseArchive} className="btn-ghost">
          {archive ? 'Đổi ZIP' : 'Chọn ZIP'}
        </button>
        <button type="button" onClick={validate} disabled={!archive || busy} className="btn-primary">
          {busy ? 'Đang kiểm tra…' : 'Kiểm tra bộ MRI'}
        </button>
      </div>

      {error ? <p role="alert" className="mt-3 text-sm text-danger">{error}</p> : null}

      {result ? (
        <div className="mt-5">
          <div
            className={`mb-3 flex items-start gap-2 rounded-control border px-3 py-2 text-sm ${
              result.valid
                ? 'border-ok/40 bg-ok/10 text-ok-soft'
                : 'border-danger/40 bg-danger/10 text-slate-200'
            }`}
          >
            {result.valid ? (
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            ) : (
              <XCircle className="mt-0.5 h-4 w-4 shrink-0 text-danger" aria-hidden="true" />
            )}
            <div>
              <p>{result.message}</p>
              {result.errors.map((item) => (
                <p key={item} className="mt-1 text-data text-slate-300">{item}</p>
              ))}
            </div>
          </div>

          <ul aria-label="Bảng kiểm 8 thì MRI" className="divide-y divide-pacs-700 overflow-hidden rounded-control border border-pacs-700">
            {result.phases.map((phase) => (
              <li key={phase.file_token} className="grid grid-cols-[minmax(5rem,0.8fr)_minmax(0,2fr)_auto] items-center gap-3 px-3 py-2 text-sm">
                <span className="font-semibold text-slate-200">{phase.label_vi}</span>
                <span className="truncate font-mono text-data text-slate-400">
                  {phase.filename ?? 'chưa nhận diện'}
                </span>
                <span className={phase.state === 'ready' ? 'text-ok-soft' : 'text-danger'}>
                  {stateLabel[phase.state]}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
