import { useCallback, useEffect, useRef, useState, type ChangeEvent } from 'react';
import { AlertTriangle, PanelLeftClose, PanelLeftOpen, Stethoscope } from 'lucide-react';

import { ApiError, getMeta, predictUpload } from '@/api/client';
import type { MetaResponse, PredictResult, UploadPredictionResult, UploadViewInfo } from '@/api/types';
import { ClassProbabilityChart } from '@/components/ClassProbabilityChart';
import { DeferPanel } from '@/components/DeferPanel';
import { EmptyState, ProvenanceBadge } from '@/components/Provenance';
import { ResultSummary } from '@/components/ResultCards';
import { SliceViewer } from '@/components/SliceViewer';
import { ThemeToggle } from '@/components/ThemeToggle';
import { UploadDropzone, UploadPanel } from '@/components/UploadWorkspace';

type MobileView = 'data' | 'images' | 'results';

function toMessage(cause: unknown): string {
  return cause instanceof ApiError ? cause.message : 'Không thể xử lý bộ MRI này. Hãy kiểm tra lại file ZIP rồi thử lại.';
}

export default function App() {
  const archiveInputRef = useRef<HTMLInputElement>(null);
  const [meta, setMeta] = useState<MetaResponse | null>(null);
  const [metaError, setMetaError] = useState<string | null>(null);
  const [archive, setArchive] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<UploadPredictionResult | null>(null);
  const [uploadView, setUploadView] = useState<UploadViewInfo | null>(null);
  const [prediction, setPrediction] = useState<PredictResult | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [mobileView, setMobileView] = useState<MobileView>('images');

  useEffect(() => {
    getMeta().then(setMeta).catch((cause: unknown) => setMetaError(toMessage(cause)));
  }, []);

  const chooseArchive = useCallback(() => archiveInputRef.current?.click(), []);

  const selectArchive = (event: ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files?.[0] ?? null;
    if (!selected) return;
    setArchive(selected);
    setUploadResult(null);
    setUploadView(null);
    setPrediction(null);
    setUploadError(null);
    setMobileView('data');
    event.target.value = '';
  };

  const runInference = async () => {
    if (!archive || busy) return;
    setBusy(true);
    setUploadError(null);
    setPrediction(null);
    setUploadView(null);
    try {
      const response = await predictUpload(archive);
      setUploadResult(response);
      if (response.prediction && response.upload_view) {
        setPrediction(response.prediction);
        setUploadView(response.upload_view);
        setMobileView('images');
      } else {
        setMobileView('data');
      }
    } catch (cause) {
      setUploadResult(null);
      setUploadError(toMessage(cause));
      setMobileView('data');
    } finally {
      setBusy(false);
    }
  };

  const sessionName = prediction?.case_id ?? archive?.name ?? 'Chưa có bộ MRI';

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar__brand">
          <span className="brand-mark"><Stethoscope aria-hidden="true" /></span>
          <div>
            <h1>Phân loại tổn thương gan trên MRI đa thì</h1>
            <p>Bản demo nghiên cứu</p>
          </div>
        </div>
        <p className="topbar__session" title={sessionName}>{sessionName}</p>
        <div className="topbar__actions">
          <ThemeToggle />
        </div>
      </header>
      <div className="ruo-bar">
        {meta?.ruo_notice ?? 'Research Use Only: chưa kiểm định lâm sàng'}, không dùng để chẩn đoán
      </div>

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
              busy={busy}
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
            <UploadDropzone archive={archive} busy={busy} onChoose={chooseArchive} onRun={runInference} />
          )}
        </section>

        <aside className={`workspace-results ${mobileView === 'results' ? 'is-mobile-active' : ''}`}>
          {prediction ? (
            <div className="results-panel animate-fade-in">
              <div className="results-panel__heading">
                <div>
                  <h2>Kết quả AI</h2>
                  <p>{prediction.case_id}</p>
                </div>
                <ProvenanceBadge provenance={prediction.provenance} />
              </div>
              <ResultSummary result={prediction} />
              <ClassProbabilityChart probs={prediction.probs} />
              <DeferPanel result={prediction} />
            </div>
          ) : (
            <div className="results-empty">
              <EmptyState label={busy ? 'AI đang xử lý bộ MRI' : 'Chưa có kết quả'} detail={busy ? 'Ảnh sẽ xuất hiện ngay khi suy luận hoàn tất.' : 'Tải bộ MRI để xem dự đoán và xác suất từng lớp.'} />
            </div>
          )}
        </aside>
      </main>
    </div>
  );
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
