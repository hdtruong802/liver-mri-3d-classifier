import { useCallback, useEffect, useState } from 'react';
import { AlertTriangle, Stethoscope } from 'lucide-react';

import { ApiError, getCase, getMeta, listCases, predictCase } from '@/api/client';
import type { CaseDetail, CaseSummary, MetaResponse, PredictResult } from '@/api/types';
import { CaseStrip } from '@/components/CaseStrip';
import { DeferPanel } from '@/components/DeferPanel';
import { ProvenanceBadge } from '@/components/Provenance';
import { ResultSummary } from '@/components/ResultCards';
import { ResultDetailsTabs } from '@/components/ResultDetailsTabs';
import { SliceViewer } from '@/components/SliceViewer';
import { ZipUpload } from '@/components/ZipUpload';

export default function App() {
  const [meta, setMeta] = useState<MetaResponse | null>(null);
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [detail, setDetail] = useState<CaseDetail | null>(null);
  const [result, setResult] = useState<PredictResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getMeta(), listCases()])
      .then(([metaResponse, caseList]) => {
        setMeta(metaResponse);
        setCases(caseList);
      })
      .catch((cause: ApiError) => setError(cause.message));
  }, []);

  const openCase = useCallback(async (caseId: string) => {
    setBusy(true);
    setError(null);
    try {
      const [caseDetail, prediction] = await Promise.all([getCase(caseId), predictCase(caseId)]);
      setDetail(caseDetail);
      setResult(prediction);
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : String(cause));
    } finally {
      setBusy(false);
    }
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
            <span className="inline-block h-2 w-2 border border-slate-400" aria-hidden="true" />
            {meta?.ruo_notice ?? 'Research Use Only: chưa kiểm định lâm sàng'} · không dùng để chẩn đoán
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-shell px-6 py-6">
        {error ? (
          <div
            role="alert"
            className="mb-6 flex items-start gap-3 rounded-frame border border-danger/50 bg-danger/10 p-4"
          >
            <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-danger" aria-hidden="true" />
            <p className="max-w-measure text-sm text-slate-300">{error}</p>
          </div>
        ) : null}

        <CaseStrip cases={cases} selected={detail?.case_id ?? null} busy={busy} onSelect={openCase} />

        {meta ? <ZipUpload /> : null}

        {result ? (
          <section aria-labelledby="results-heading" className="mt-8 animate-fade-in">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="label">Ca demo đã chọn</p>
                <h2 id="results-heading" className="font-mono text-lg font-bold text-white">
                  {result.case_id}
                </h2>
              </div>
              <ProvenanceBadge provenance={result.provenance} />
            </div>

            <ResultSummary result={result} />
            <DeferPanel result={result} />

            {detail && meta ? (
              <ResultDetailsTabs
                probs={result.probs}
                imageExplorer={
                  <SliceViewer
                    caseId={detail.case_id}
                    phases={meta.phases}
                    modelHeatmap={detail.model_heatmap}
                    volumes={detail.volumes}
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
