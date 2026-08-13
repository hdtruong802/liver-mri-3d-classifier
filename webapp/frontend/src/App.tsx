import { useCallback, useEffect, useState } from 'react';
import { AlertTriangle, Stethoscope } from 'lucide-react';

import { ApiError, getMeta } from '@/api/client';
import type { MetaResponse, PredictResult, UploadViewInfo } from '@/api/types';
import { DeferPanel } from '@/components/DeferPanel';
import { ProvenanceBadge } from '@/components/Provenance';
import { ResultSummary } from '@/components/ResultCards';
import { ResultDetailsTabs } from '@/components/ResultDetailsTabs';
import { SliceViewer } from '@/components/SliceViewer';
import { ZipUpload } from '@/components/ZipUpload';

export default function App() {
  const [meta, setMeta] = useState<MetaResponse | null>(null);
  const [uploadView, setUploadView] = useState<UploadViewInfo | null>(null);
  const [result, setResult] = useState<PredictResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getMeta()
      .then(setMeta)
      .catch((cause: ApiError) => setError(cause.message));
  }, []);

  const showUploadPrediction = useCallback((prediction: PredictResult, view: UploadViewInfo) => {
    setUploadView(view);
    setResult(prediction);
    setError(null);
  }, []);

  return (
    <div className="min-h-full">
      <header className="sticky top-0 z-30 border-b border-pacs-700 bg-pacs-900">
        <div className="mx-auto flex max-w-shell items-center gap-2 px-6 py-3">
          <Stethoscope className="h-5 w-5 shrink-0 text-accent" aria-hidden="true" />
          <div>
            <h1 className="text-base font-bold leading-tight text-white">
              Phân loại tổn thương gan trên MRI đa thì
            </h1>
            <p className="text-data text-slate-400">Bản demo nghiên cứu</p>
          </div>
        </div>
        <div className="border-t border-pacs-700 bg-pacs-950">
          <p className="mx-auto flex max-w-shell items-center gap-2 px-6 py-2 label text-slate-400">
            {/* <span className="inline-block h-2 w-2 border border-slate-400" aria-hidden="true" /> */}
            {meta?.ruo_notice ?? 'Research Use Only: chưa kiểm định lâm sàng'}, không dùng để chẩn đoán
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-shell px-6 py-6">
        {error ? (
          <div
            role="alert"
            className="mb-6 flex items-start gap-3 rounded-[6px] border border-danger/50 bg-danger/10 p-4"
          >
            <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-danger" aria-hidden="true" />
            <p className="max-w-measure text-sm text-slate-300">{error}</p>
          </div>
        ) : null}

        {meta ? <ZipUpload onPrediction={showUploadPrediction} /> : null}

        {result ? (
          <section aria-labelledby="results-heading" className="mt-8 animate-fade-in">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="label">Bộ MRI đã tải lên</p>
                <h2 id="results-heading" className="font-mono text-lg font-bold text-white">
                  {result.case_id}
                </h2>
              </div>
              <ProvenanceBadge provenance={result.provenance} />
            </div>

            <ResultSummary result={result} />
            <DeferPanel result={result} />

            {uploadView && meta ? (
              <ResultDetailsTabs
                probs={result.probs}
                imageExplorer={
                  <SliceViewer
                    caseId={uploadView.upload_id}
                    phases={meta.phases}
                    modelHeatmap={null}
                    volumes={uploadView.volumes}
                    source="upload"
                  />
                }
              />
            ) : null}
          </section>
        ) : null}
      </main>
    </div>
  );
}
