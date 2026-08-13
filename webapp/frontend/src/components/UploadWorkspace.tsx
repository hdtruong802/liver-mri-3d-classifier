import { Archive, CheckCircle2, CircleAlert, FileUp, Play, XCircle } from 'lucide-react';

import type { UploadPhaseState, UploadValidationResult } from '@/api/types';

const stateLabel: Record<UploadPhaseState, string> = {
  ready: 'đủ',
  missing: 'thiếu',
  duplicate: 'trùng',
};

interface UploadProps {
  archive: File | null;
  result: UploadValidationResult | null;
  busy: boolean;
  error: string | null;
  onChoose: () => void;
  onRun: () => void;
}

export function UploadPanel({ archive, result, busy, error, onChoose, onRun }: UploadProps) {
  return (
    <section className="side-section" aria-labelledby="upload-panel-heading">
      <div className="side-section__heading">
        <Archive aria-hidden="true" />
        <h2 id="upload-panel-heading">Bộ MRI</h2>
      </div>
      <p className="side-section__copy">
        ZIP gồm 8 ảnh trong <code>images/</code> và 8 mask tương ứng trong <code>masks/</code>. Mỗi file là <code>.nii</code> hoặc <code>.nii.gz</code>.
      </p>

      <div className="upload-file-row">
        <span className="upload-file-row__name">{archive ? archive.name : 'Chưa chọn file ZIP'}</span>
        <button type="button" className="control-button" onClick={onChoose} disabled={busy}>
          {archive ? 'Đổi file' : 'Chọn ZIP'}
        </button>
      </div>
      <button type="button" className="primary-button upload-run" onClick={onRun} disabled={!archive || busy}>
        <Play aria-hidden="true" />
        {busy ? 'Đang chạy AI…' : 'Kiểm tra và chạy AI'}
      </button>

      <UploadStatus result={result} error={error} />
    </section>
  );
}

export function UploadDropzone({ archive, busy, onChoose, onRun }: Pick<UploadProps, 'archive' | 'busy' | 'onChoose' | 'onRun'>) {
  return (
    <div className={`viewer-dropzone ${archive ? 'viewer-dropzone--selected' : ''}`}>
      <FileUp aria-hidden="true" />
      <h2>{archive ? 'Bộ MRI đã sẵn sàng' : 'Tải bộ MRI (.zip)'}</h2>
      <p>
        {archive
          ? archive.name
          : 'Chọn một ZIP gồm 8 ảnh MRI và 8 mask tổn thương tương ứng để xem ảnh nguồn và chạy suy luận.'}
      </p>
      <div className="viewer-dropzone__actions">
        <button type="button" className="control-button" onClick={onChoose} disabled={busy}>
          {archive ? 'Đổi file ZIP' : 'Chọn file ZIP'}
        </button>
        {archive ? (
          <button type="button" className="primary-button" onClick={onRun} disabled={busy}>
            <Play aria-hidden="true" />
            {busy ? 'Đang chạy AI…' : 'Chạy AI'}
          </button>
        ) : null}
      </div>
    </div>
  );
}

function UploadStatus({ result, error }: Pick<UploadProps, 'result' | 'error'>) {
  if (error) return <p className="upload-error" role="alert">{error}</p>;
  if (!result) return null;

  const tone = result.inference_ready ? 'success' : result.valid ? 'warning' : 'danger';
  const Icon = result.inference_ready ? CheckCircle2 : result.valid ? CircleAlert : XCircle;
  return (
    <div className="upload-status">
      <div className={`status-message status-message--${tone}`}>
        <Icon aria-hidden="true" />
        <div>
          <p>{result.message}</p>
          {result.errors.map((item) => <p key={item}>{item}</p>)}
        </div>
      </div>
      <ul className="phase-checklist" aria-label="Bảng kiểm ảnh MRI và mask của 8 thì">
        {result.phases.map((phase) => (
          <li key={phase.file_token}>
            <strong>{phase.label_vi}</strong>
            <span title={phase.filename ?? undefined}>{phase.filename ?? 'Chưa nhận diện ảnh'}</span>
            <b className={phase.state === 'ready' ? 'is-success' : 'is-danger'}>Ảnh {stateLabel[phase.state]}</b>
            <span title={phase.mask_filename ?? undefined}>{phase.mask_filename ?? 'Chưa nhận diện mask'}</span>
            <b className={phase.mask_state === 'ready' ? 'is-success' : 'is-danger'}>Mask {stateLabel[phase.mask_state]}</b>
          </li>
        ))}
      </ul>
    </div>
  );
}
