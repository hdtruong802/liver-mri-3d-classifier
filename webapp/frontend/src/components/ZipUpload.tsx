import { useRef, useState, type ChangeEvent } from 'react';
import { Archive, CheckCircle2, CircleAlert, FileUp, Play, XCircle } from 'lucide-react';

import { ApiError, predictUpload } from '@/api/client';
import type { PredictResult, UploadPhaseState, UploadValidationResult } from '@/api/types';

const stateLabel: Record<UploadPhaseState, string> = {
  ready: 'đủ',
  missing: 'thiếu',
  duplicate: 'trùng',
};

export function ZipUpload({ onPrediction }: { onPrediction: (result: PredictResult) => void }) {
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

  const run = async () => {
    if (!archive) return;
    setBusy(true);
    setError(null);
    try {
      const response = await predictUpload(archive);
      setResult(response);
      if (response.prediction) onPrediction(response.prediction);
    } catch (cause) {
      setResult(null);
      setError(cause instanceof ApiError ? cause.message : String(cause));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section aria-labelledby="upload-heading" className="workstation-section mt-8 py-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <Archive className="h-5 w-5 text-accent" aria-hidden="true" />
            <h2 id="upload-heading" className="text-lg font-bold text-white">
              Tải bộ MRI lên
            </h2>
          </div>
          <p className="mt-2 max-w-measure text-sm text-slate-300">
            ZIP cần 8 ảnh MRI trong <span className="font-mono">images/</span> và 8 mask tổn thương cùng thì trong{' '}
            <span className="font-mono">masks/</span>. Mỗi file là <span className="font-mono">.nii</span> hoặc{' '}
            <span className="font-mono">.nii.gz</span>, tên file phải có token thì MRI.
          </p>
        </div>
        <span className="chip border border-pacs-700 bg-pacs-800 text-slate-300">8 ảnh + 8 mask</span>
      </div>

      <input
        ref={inputRef}
        className="sr-only"
        type="file"
        accept=".zip,application/zip"
        onChange={onSelect}
        aria-label="Chọn file ZIP bộ MRI"
      />

      <div className="workstation-inset mt-5 flex flex-wrap items-center gap-3 border-dashed p-4">
        <FileUp className="h-5 w-5 shrink-0 text-accent" aria-hidden="true" />
        <div className="min-w-0 flex-1">
          <p className="truncate font-mono text-sm font-semibold text-white">
            {archive ? archive.name : 'Chưa chọn bộ MRI'}
          </p>
          <p className="text-data text-slate-400">
            {archive ? 'Sẵn sàng kiểm tra cấu trúc và chạy AI nếu bộ file đủ.' : 'Chọn một file ZIP để bắt đầu.'}
          </p>
        </div>
        <button type="button" onClick={chooseArchive} className="btn-ghost">
          {archive ? 'Đổi file ZIP' : 'Chọn file ZIP'}
        </button>
        <button type="button" onClick={run} disabled={!archive || busy} className="btn-primary">
          <Play className="h-4 w-4" aria-hidden="true" />
          {busy ? 'Đang kiểm tra và chạy AI…' : 'Kiểm tra và chạy AI'}
        </button>
      </div>

      {error ? <p role="alert" className="mt-3 text-sm text-danger">{error}</p> : null}

      {result ? (
        <div className="mt-5">
          <div
            className={`mb-3 flex items-start gap-2 rounded-control border px-3 py-2 text-sm ${
              result.inference_ready
                ? 'border-ok/40 bg-ok/10 text-ok-soft'
                : result.valid
                ? 'border-warn/40 bg-warn/10 text-warn-soft'
                : 'border-danger/40 bg-danger/10 text-slate-200'
            }`}
          >
            {result.inference_ready ? (
              <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            ) : result.valid ? (
              <CircleAlert className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
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

          <ul aria-label="Bảng kiểm ảnh MRI và mask của 8 thì" className="divide-y divide-pacs-700 overflow-hidden rounded-control border border-pacs-700">
            {result.phases.map((phase) => (
              <li key={phase.file_token} className="grid grid-cols-[minmax(4.5rem,0.7fr)_minmax(0,1fr)_auto] items-center gap-3 px-3 py-2 text-sm sm:grid-cols-[minmax(5rem,0.7fr)_minmax(0,1.5fr)_auto_minmax(0,1.5fr)_auto]">
                <span className="font-semibold text-slate-200">{phase.label_vi}</span>
                <span className="truncate font-mono text-data text-slate-400">
                  {phase.filename ?? 'chưa nhận diện'}
                </span>
                <span className={phase.state === 'ready' ? 'text-ok-soft' : 'text-danger'}>
                  ảnh {stateLabel[phase.state]}
                </span>
                <span className="col-start-2 truncate font-mono text-data text-slate-400 sm:col-start-auto">
                  {phase.mask_filename ?? 'chưa nhận diện'}
                </span>
                <span className={phase.mask_state === 'ready' ? 'text-ok-soft' : 'text-danger'}>
                  mask {stateLabel[phase.mask_state]}
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
