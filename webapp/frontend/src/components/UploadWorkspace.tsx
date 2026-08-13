import { Archive, CheckCircle2, CircleAlert, FileUp, LoaderCircle, Play, XCircle } from 'lucide-react';

import type { UploadPhaseState, UploadValidationResult } from '@/api/types';

const stateLabel: Record<UploadPhaseState, string> = {
  ready: 'sẵn sàng',
  missing: 'thiếu',
  duplicate: 'trùng',
};

export type UploadStage = 'idle' | 'checking' | 'predicting' | 'complete' | 'validation_error' | 'prediction_error';

interface UploadProps {
  archive: File | null;
  result: UploadValidationResult | null;
  stage: UploadStage;
  error: string | null;
}

interface UploadActions {
  onChoose: () => void;
  onRun: () => void;
  onRetryPrediction: () => void;
}

function isWorking(stage: UploadStage) {
  return stage === 'checking' || stage === 'predicting';
}

export function UploadProgress({ stage, compact = false }: { stage: UploadStage; compact?: boolean }) {
  if (stage !== 'checking' && stage !== 'predicting') return null;
  const label = stage === 'checking' ? 'Đang kiểm tra bộ MRI' : 'AI đang dự đoán';
  return (
    <p className={`upload-progress ${compact ? 'upload-progress--compact' : ''}`} role="status" aria-live="polite">
      <LoaderCircle className="upload-spinner" aria-hidden="true" />
      <span>{label}</span>
    </p>
  );
}

export function UploadPanel({ archive, result, stage, error }: UploadProps) {
  return (
    <section className="side-section" aria-labelledby="upload-panel-heading">
      <div className="side-section__heading">
        <Archive aria-hidden="true" />
        <h2 id="upload-panel-heading">Bộ ảnh MRI</h2>
      </div>
      <p className="side-section__copy">
        Tệp ZIP cần có 8 thì MRI và 8 nhãn vùng tổn thương tương ứng. Mỗi tệp có định dạng <code>.nii</code> hoặc <code>.nii.gz</code>.
      </p>

      <div className="upload-file-row">
        <span className="upload-file-row__name">{archive ? archive.name : 'Chưa chọn file ZIP'}</span>
      </div>
      <UploadProgress stage={stage} compact />
      <UploadStatus result={result} error={error} />
    </section>
  );
}

export function UploadDropzone({ archive, stage, error, onChoose, onRun, onRetryPrediction }: Omit<UploadProps, 'result'> & UploadActions) {
  const working = isWorking(stage);
  const validationFailed = stage === 'validation_error';
  const predictionFailed = stage === 'prediction_error';
  const title = stage === 'checking' ? 'Đang kiểm tra bộ MRI' : stage === 'predicting' ? 'AI đang dự đoán' : validationFailed ? 'Bộ MRI cần được kiểm tra lại' : predictionFailed ? 'Chưa thể dự đoán AI' : archive ? 'Bộ MRI đã sẵn sàng' : 'Tải bộ MRI (.zip)';
  const detail = working
    ? stage === 'checking' ? 'Đang kiểm tra đủ 8 ảnh MRI và 8 nhãn vùng tổn thương.' : 'Bộ MRI hợp lệ. AI đang phân tích ảnh.'
    : validationFailed ? 'Xem lỗi kiểm tra ở cột Dữ liệu, rồi chọn một ZIP khác.'
      : predictionFailed ? 'Bộ MRI đã hợp lệ. Bạn có thể thử chạy dự đoán lại.'
        : archive ? archive.name : 'Chọn một ZIP gồm 8 ảnh MRI và 8 nhãn vùng tổn thương tương ứng để xem ảnh và chạy dự đoán.';

  return (
    <div className={`viewer-dropzone ${archive ? 'viewer-dropzone--selected' : ''}`}>
      {working ? <LoaderCircle className="upload-spinner" aria-hidden="true" /> : validationFailed || predictionFailed ? <CircleAlert aria-hidden="true" /> : <FileUp aria-hidden="true" />}
      <h2>{title}</h2>
      <p>{detail}</p>
      {error ? <p className="upload-error" role="alert">{error}</p> : null}
      <div className="viewer-dropzone__actions">
        <button type="button" className="control-button" onClick={onChoose} disabled={working}>
          {archive ? 'Đổi bộ MRI' : 'Tải bộ MRI (.zip)'}
        </button>
        {archive && stage === 'idle' ? (
          <button type="button" className="primary-button" onClick={onRun}>
            <Play aria-hidden="true" />
            Kiểm tra và chạy AI
          </button>
        ) : null}
        {archive && predictionFailed ? (
          <button type="button" className="primary-button" onClick={onRetryPrediction}>
            <Play aria-hidden="true" />
            Thử lại dự đoán
          </button>
        ) : null}
      </div>
    </div>
  );
}

function UploadStatus({ result, error }: Pick<UploadProps, 'result' | 'error'>) {
  if (!result && !error) return null;

  const tone = result?.inference_ready ? 'success' : result?.valid ? 'warning' : 'danger';
  const Icon = result?.inference_ready ? CheckCircle2 : result?.valid ? CircleAlert : XCircle;
  const message = result?.inference_ready ? 'Bộ MRI và nhãn tổn thương đã đầy đủ. Sẵn sàng dự đoán.' : result?.message;
  return (
    <div className="upload-status">
      {error ? <p className="upload-error" role="alert">{error}</p> : null}
      {result ? (
        <>
          <div className={`status-message status-message--${tone}`}>
            <Icon aria-hidden="true" />
            <div>
              <p>{message}</p>
              {result.errors.map((item) => <p key={item}>{item}</p>)}
            </div>
          </div>
          <ul className="phase-checklist" aria-label="Bảng kiểm ảnh MRI và nhãn tổn thương của 8 thì">
            {result.phases.map((phase) => (
              <li key={phase.file_token}>
                <strong>{phase.label_vi}</strong>
                <span title={phase.filename ?? undefined}>{phase.filename ?? 'Chưa nhận diện ảnh'}</span>
                <b className={phase.state === 'ready' ? 'is-success' : 'is-danger'}>Ảnh: {stateLabel[phase.state]}</b>
                <span title={phase.mask_filename ?? undefined}>{phase.mask_filename ?? 'Chưa nhận diện nhãn'}</span>
                <b className={phase.mask_state === 'ready' ? 'is-success' : 'is-danger'}>Nhãn: {stateLabel[phase.mask_state]}</b>
              </li>
            ))}
          </ul>
        </>
      ) : null}
    </div>
  );
}
