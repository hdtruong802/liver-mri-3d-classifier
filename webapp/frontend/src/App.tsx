/**
 * DIRECTION CONTRACT
 *
 * THESIS: Bàn đọc tối của một trạm chẩn đoán hình ảnh, dựng theo bố cục bản bolt.new
 * gốc. Điều bố cục đó không tự có, và là điều bề mặt này bắt buộc phải làm: người xem
 * phân biệt được ngay đâu là dữ liệu thật, đâu là số minh hoạ.
 *
 * OWN-WORLD: Nền mực xanh đen #070A13, panel #0F1525 bo 1rem viền mảnh, một sắc cyan
 * #22D3EE làm accent duy nhất. Inter cho giao diện, JetBrains Mono cho định danh và
 * giá trị đo. Bảy màu lớp chỉ sống trong biểu đồ và dải chú giải. Ảnh MRI là thứ sáng
 * nhất màn hình.
 *
 * STORY: Người review chọn một ca demo, thấy tám thì đã đủ, chạy phân tích, rồi đọc
 * ba thẻ kết quả và biểu đồ bảy lớp — mọi con số đều mang badge "minh hoạ" và in
 * nghiêng vì chưa có checkpoint. Panel defer nói cho họ biết mô hình có nhận quyết ca
 * này hay không.
 *
 * FIRST VIEWPORT: Header dính trên; ngay dưới là dải RUO không thể cuộn khuất; rồi dải
 * thông tin ca, bộ chọn ca demo, và lưới 8 thẻ thì 4×2. Hành động chính là nút chạy
 * phân tích ở cuối lưới.
 *
 * FORM: bố cục bản bolt.new, người dùng chốt sau khi xem bản dựng trước; theme tối
 * theo yêu cầu. Hệ đầy đủ ở `webapp/DESIGN.md`.
 */

import { useCallback, useEffect, useMemo, useState } from 'react';
import { Activity, AlertTriangle, RotateCcw, Stethoscope } from 'lucide-react';

import { ApiError, getCase, getMeta, listCases, predictCase, predictUpload } from '@/api/client';
import type { CaseDetail, CaseSummary, MetaResponse, PredictResult } from '@/api/types';
import { isProvisional } from '@/api/types';
import { CaseStrip } from '@/components/CaseStrip';
import { ClassLegend, ClassProbabilityChart } from '@/components/ClassProbabilityChart';
import { DeferPanel } from '@/components/DeferPanel';
import { PhaseGrid } from '@/components/PhaseGrid';
import { ProvenanceBadge } from '@/components/Provenance';
import { MalignancyGauge, PredictionCard, UncertaintyCard } from '@/components/ResultCards';
import { SliceViewer } from '@/components/SliceViewer';

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

  const runUpload = useCallback(async (files: File[]) => {
    setBusy(true);
    setError(null);
    try {
      setDetail(null);
      setResult(await predictUpload(files));
    } catch (cause) {
      setError(cause instanceof ApiError ? cause.message : String(cause));
    } finally {
      setBusy(false);
    }
  }, []);

  const reset = useCallback(() => {
    setDetail(null);
    setResult(null);
    setError(null);
  }, []);

  const provisional = result ? isProvisional(result.provenance) : true;
  const referenceVolume = useMemo(
    () => detail?.volumes.find((v) => v.file_token === 'C+V') ?? detail?.volumes[0] ?? null,
    [detail],
  );

  return (
    <div className="min-h-full">
      {/* 1. Header */}
      <header className="sticky top-0 z-30 border-b border-pacs-700 bg-pacs-900/95 backdrop-blur">
        <div className="mx-auto flex max-w-shell flex-wrap items-center justify-between gap-4 px-6 py-3">
          <div className="flex items-center gap-3">
            <span className="grid h-10 w-10 place-items-center rounded-control border border-accent/40 bg-accent/10">
              <Stethoscope className="h-5 w-5 text-accent" aria-hidden="true" />
            </span>
            <div>
              <h1 className="text-base font-bold leading-tight text-white">
                Phân loại tổn thương gan trên MRI đa thì
              </h1>
              <p className="text-data text-slate-400">
                Bảy lớp tổn thương · tám thì · bản demo research
              </p>
            </div>
          </div>

          {/* Chỗ bản bolt để "Model online" cùng số phiên bản bịa. Thay bằng trạng
              thái thật của lớp suy luận. */}
          <div className="flex flex-wrap items-center gap-3">
            <span className="chip border border-warn/40 bg-warn/10 text-warn-soft">
              chưa nạp checkpoint
            </span>
            <span className="font-mono text-data text-slate-400">
              {meta ? `${meta.classes.length} lớp · ${meta.phases.length} thì` : 'đang nạp'}
            </span>
          </div>
        </div>

        {/* 2. Dải RUO. Khối duy nhất thêm so với bản tham chiếu, và là ràng buộc
            (AGENTS.md §3.1, PRODUCT.md Brand Commitment 1) chứ không phải lựa chọn. */}
        <div className="border-t border-pacs-700 bg-pacs-950">
          <p className="mx-auto flex max-w-shell items-center gap-2 px-6 py-2 label text-slate-400">
            <span
              className="inline-block h-2 w-2 border border-slate-400"
              aria-hidden="true"
            />
            {meta?.ruo_notice ?? 'Research Use Only: chưa kiểm định lâm sàng'} · không dùng để chẩn
            đoán
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-shell px-6 py-6">
        {/* 3. Dải thông tin ca */}
        <div className="panel flex flex-wrap items-center gap-x-10 gap-y-4 px-5 py-4">
          <Field label="Ca" value={detail?.case_id ?? result?.case_id ?? 'chưa chọn'} mono />
          <Field label="Nguồn" value={detail ? 'LLD-MMRI' : '—'} />
          <Field
            label="Số lát"
            value={referenceVolume ? `${referenceVolume.n_slices} lát` : '—'}
            mono
          />
          <Field
            label="Thì đã có"
            value={detail ? `${detail.volumes.length}/${meta?.phases.length ?? 8} thì` : '—'}
          />
          <div className="ml-auto flex items-center gap-3">
            {result ? <ProvenanceBadge provenance={result.provenance} /> : null}
            <button type="button" onClick={reset} disabled={busy} className="btn-ghost">
              <RotateCcw className="h-4 w-4" aria-hidden="true" />
              Xoá kết quả
            </button>
          </div>
        </div>

        {error ? (
          <div
            role="alert"
            className="mt-6 flex items-start gap-3 rounded-panel border border-danger/50 bg-danger/10 p-4"
          >
            <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-danger" aria-hidden="true" />
            <p className="max-w-measure text-sm text-slate-300">{error}</p>
          </div>
        ) : null}

        {/* 4. Bộ chọn ca demo */}
        <CaseStrip cases={cases} selected={detail?.case_id ?? null} busy={busy} onSelect={openCase} />

        {/* 5 + 6. Lưới 8 thì và thanh chạy phân tích */}
        {meta ? <PhaseGrid phases={meta.phases} busy={busy} onSubmit={runUpload} /> : null}

        {/* 7 → 10. Kết quả */}
        {result ? (
          <section aria-labelledby="results-heading" className="mt-8 animate-fade-in">
            <div className="mb-4 flex items-center gap-2">
              <Activity className="h-5 w-5 text-accent" aria-hidden="true" />
              <h2 id="results-heading" className="text-lg font-bold text-white">
                Kết quả phân tích
              </h2>
            </div>

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-12">
              <PredictionCard result={result} provisional={provisional} />
              <MalignancyGauge result={result} provisional={provisional} />
              <UncertaintyCard result={result} provisional={provisional} />
            </div>

            <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-12">
              <ClassProbabilityChart probs={result.probs} provisional={provisional} />
              <DeferPanel result={result} provisional={provisional} />
            </div>

            <div className="mt-6">
              {detail && meta ? (
                <SliceViewer caseId={detail.case_id} phases={meta.phases} volumes={detail.volumes} />
              ) : null}
            </div>

            <ClassLegend probs={result.probs} />
          </section>
        ) : null}
      </main>

      <footer className="mt-10 border-t border-pacs-700 bg-pacs-900">
        <div className="mx-auto max-w-shell space-y-2 px-6 py-6">
          <p className="max-w-measure text-data text-slate-400">
            <span className="italic">Chữ nghiêng</span> và badge "minh hoạ" đánh dấu con số chưa
            phải kết quả đo được. Chưa có checkpoint, nên mọi giá trị suy luận trên màn hình này là
            số giả lập dùng để dựng và kiểm giao diện.
          </p>
          <p className="max-w-measure text-data text-slate-400">
            Research Use Only. Công cụ chưa được kiểm định lâm sàng và không dùng để chẩn đoán.
          </p>
        </div>
      </footer>
    </div>
  );
}

function Field({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div>
      <p className="label">{label}</p>
      <p className={`text-sm font-semibold text-white ${mono ? 'font-mono' : ''}`}>{value}</p>
    </div>
  );
}
