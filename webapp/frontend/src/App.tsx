import { useCallback, useEffect, useRef, useState, type ChangeEvent } from 'react';
import { AlertTriangle, LoaderCircle, PanelLeftClose, PanelLeftOpen, Stethoscope } from 'lucide-react';

import { ApiError, getMeta, predictUpload, validateUpload } from '@/api/client';
import type { MetaResponse, PredictResult, UploadValidationResult, UploadViewInfo } from '@/api/types';
import { ClassProbabilityChart } from '@/components/ClassProbabilityChart';
import { DeferPanel } from '@/components/DeferPanel';
import { EmptyState } from '@/components/Provenance';
import { ResultSummary } from '@/components/ResultCards';
import { SliceViewer } from '@/components/SliceViewer';
import { ThemeToggle } from '@/components/ThemeToggle';
import { UploadDropzone, UploadPanel, type UploadStage } from '@/components/UploadWorkspace';

type MobileView = 'data' | 'images' | 'results';

function toMessage(cause: unknown): string {
  return cause instanceof ApiError ? cause.message : 'Không thể xử lý bộ MRI này. Hãy kiểm tra lại file ZIP rồi thử lại.';
}

export default function App() {
  const archiveInputRef = useRef<HTMLInputElement>(null);
  const uploadRunRef = useRef(0);
  const processingStartedAtRef = useRef<number | null>(null);
  const [meta, setMeta] = useState<MetaResponse | null>(null);
  const [metaError, setMetaError] = useState<string | null>(null);
  const [archive, setArchive] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<UploadValidationResult | null>(null);
  const [uploadView, setUploadView] = useState<UploadViewInfo | null>(null);
  const [prediction, setPrediction] = useState<PredictResult | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [processingElapsedMs, setProcessingElapsedMs] = useState<number | null>(null);
  const [uploadStage, setUploadStage] = useState<UploadStage>('idle');
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [mobileView, setMobileView] = useState<MobileView>('images');

  useEffect(() => {
    getMeta().then(setMeta).catch((cause: unknown) => setMetaError(toMessage(cause)));
  }, []);

  const chooseArchive = useCallback(() => archiveInputRef.current?.click(), []);

  const selectArchive = (event: ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0] ?? null;
    if (!selected) return;
    uploadRunRef.current += 1;
    setArchive(selected);
    setUploadResult(null);
    setUploadView(null);
    setPrediction(null);
    setUploadError(null);
    setProcessingElapsedMs(null);
    processingStartedAtRef.current = null;
    setUploadStage('idle');
    setMobileView('data');
    event.target.value = '';
  };

  const runPrediction = async (runId: number) => {
    if (!archive) return;
    setUploadStage('predicting');
    setUploadError(null);
    setPrediction(null);
    setUploadView(null);
    try {
      const response = await predictUpload(archive);
      if (runId !== uploadRunRef.current) return;
      setUploadResult(response);
      if (response.prediction && response.upload_view) {
        setPrediction(response.prediction);
        setUploadView(response.upload_view);
        if (processingStartedAtRef.current !== null) {
          setProcessingElapsedMs(performance.now() - processingStartedAtRef.current);
        }
        setUploadStage('complete');
        setMobileView('images');
      } else {
        setUploadStage('prediction_error');
        setUploadError(response.message);
        setMobileView('data');
      }
    } catch (cause) {
      if (runId !== uploadRunRef.current) return;
      setUploadError(toMessage(cause));
      setUploadStage('prediction_error');
      setMobileView('data');
    }
  };

  const runInference = async () => {
    if (!archive || uploadStage === 'checking' || uploadStage === 'predicting') return;
    const runId = uploadRunRef.current + 1;
    uploadRunRef.current = runId;
    setUploadStage('checking');
    setUploadError(null);
    setUploadResult(null);
    setPrediction(null);
    setUploadView(null);
    setProcessingElapsedMs(null);
    processingStartedAtRef.current = performance.now();
    try {
      const validation = await validateUpload(archive);
      if (runId !== uploadRunRef.current) return;
      setUploadResult(validation);
      if (!validation.inference_ready) {
        setUploadStage('validation_error');
        setMobileView('data');
        return;
      }
    } catch (cause) {
      if (runId !== uploadRunRef.current) return;
      setUploadError(toMessage(cause));
      setUploadStage('validation_error');
      setMobileView('data');
      return;
    }

    await runPrediction(runId);
  };

  const retryPrediction = () => {
    if (!archive || busy) return;
    const runId = uploadRunRef.current + 1;
    uploadRunRef.current = runId;
    processingStartedAtRef.current = performance.now();
    void runPrediction(runId);
  };

  const busy = uploadStage === 'checking' || uploadStage === 'predicting';

  const sessionName = prediction?.case_id ?? archive?.name ?? 'Chưa có bộ MRI';

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar__brand">
          <span className="brand-mark"><Stethoscope aria-hidden="true" /></span>
          <div>
            <h1>Phân loại tổn thương gan trên MRI đa thì</h1>
            <p>Chỉ dùng cho nghiên cứu · Không dùng để chẩn đoán</p>
          </div>
        </div>
        <p className="topbar__session" title={sessionName}>{sessionName}</p>
        <div className="topbar__actions">
          <ThemeToggle />
        </div>
      </header>
      <input
        ref={archiveInputRef}
        className="sr-only"
        type="file"
        accept=".zip,application/zip"
        onChange={selectArchive}
        aria-label="Chọn file ZIP bộ MRI"
      />

      <nav className="workspace-tabs" aria-label="Điều hướng workspace">
        <WorkspaceTab active={mobileView === 'data'} onClick={() => setMobileView('data')}>Dữ liệu</WorkspaceTab>
        <WorkspaceTab active={mobileView === 'images'} onClick={() => setMobileView('images')}>Ảnh MRI</WorkspaceTab>
        <WorkspaceTab active={mobileView === 'results'} onClick={() => setMobileView('results')}>Kết quả</WorkspaceTab>
      </nav>

      <main className="workspace">
        <aside className={`workspace-data ${leftCollapsed ? 'workspace-data--collapsed' : ''} ${mobileView === 'data' ? 'is-mobile-active' : ''}`}>
          <button
            type="button"
            className="panel-collapse-control"
            onClick={() => setLeftCollapsed((value) => !value)}
            aria-label={leftCollapsed ? 'Hiện panel dữ liệu' : 'Thu gọn panel dữ liệu'}
            title={leftCollapsed ? 'Hiện panel dữ liệu' : 'Thu gọn panel dữ liệu'}
          >
            {leftCollapsed ? <PanelLeftOpen aria-hidden="true" /> : <PanelLeftClose aria-hidden="true" />}
          </button>
          <div className="workspace-data__content">
            {metaError ? <StatusError message={metaError} /> : null}
            <UploadPanel
              archive={archive}
              result={uploadResult}
              stage={uploadStage}
              error={uploadError}
            />
          </div>
        </aside>

        <section className={`workspace-viewer ${mobileView === 'images' ? 'is-mobile-active' : ''}`} aria-label="Không gian xem ảnh MRI">
          {uploadView && meta ? (
            <SliceViewer
              caseId={uploadView.upload_id}
              phases={meta.phases}
              modelHeatmap={null}
              volumes={uploadView.volumes}
              source="upload"
            />
          ) : (
            <UploadDropzone
              archive={archive}
              stage={uploadStage}
              error={uploadError}
              onChoose={chooseArchive}
              onRun={runInference}
              onRetryPrediction={retryPrediction}
            />
          )}
        </section>

        <aside className={`workspace-results ${mobileView === 'results' ? 'is-mobile-active' : ''}`}>
          {prediction ? (
            <div className="results-panel animate-fade-in">
              <div className="results-panel__heading">
                <div>
                  <h2>Kết quả AI dự đoán</h2>
                  <p>{prediction.case_id}</p>
                  {processingElapsedMs !== null ? <p>Tải & xử lý: {formatElapsedTime(processingElapsedMs)}</p> : null}
                </div>
              </div>
              <ResultSummary result={prediction} />
              <ClassProbabilityChart probs={prediction.probs} />
              <DeferPanel result={prediction} />
            </div>
          ) : (
            <div className="results-empty">
              <ProcessingEmptyState stage={uploadStage} />
            </div>
          )}
        </aside>
      </main>
    </div>
  );
}

function formatElapsedTime(elapsedMs: number): string {
  const seconds = elapsedMs / 1000;
  if (seconds < 60) return `${new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 1 }).format(seconds)} giây`;
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.round(seconds % 60);
  return `${minutes} phút ${remainingSeconds} giây`;
}

function ProcessingEmptyState({ stage }: { stage: UploadStage }) {
  if (stage === 'checking' || stage === 'predicting') {
    const label = stage === 'checking' ? 'Đang kiểm tra bộ MRI' : 'Đang chạy dự đoán AI';
    const detail = stage === 'checking'
      ? 'Đang kiểm tra đủ 8 ảnh MRI và 8 mask.'
      : 'Bộ MRI hợp lệ. Kết quả sẽ xuất hiện khi suy luận hoàn tất.';
    return (
      <div className="processing-empty-state" role="status" aria-live="polite">
        <LoaderCircle className="upload-spinner" aria-hidden="true" />
        <p>{label}</p>
        <p>{detail}</p>
      </div>
    );
  }

  if (stage === 'validation_error') {
    return <EmptyState label="Bộ MRI chưa hợp lệ" detail="Xem các mục cần chỉnh ở cột Dữ liệu, rồi chọn ZIP khác." />;
  }
  if (stage === 'prediction_error') {
    return <EmptyState label="Chưa thể dự đoán AI" detail="Bộ MRI đã được kiểm tra. Hãy thử lại dự đoán hoặc chọn ZIP khác." />;
  }
  return <EmptyState label="Chưa có kết quả" detail="Tải bộ MRI để xem dự đoán và xác suất từng lớp." />;
}

function WorkspaceTab({ active, onClick, children }: { active: boolean; onClick: () => void; children: string }) {
  return (
    <button type="button" aria-pressed={active} onClick={onClick} className={active ? 'is-active' : ''}>
      {children}
    </button>
  );
}

function StatusError({ message }: { message: string }) {
  return (
    <div className="status-message status-message--danger" role="alert">
      <AlertTriangle aria-hidden="true" />
      <p>{message}</p>
    </div>
  );
}
