/**
 * DIRECTION CONTRACT
 *
 * THESIS: Một bản demo tự vẽ ra độ tin cậy của chính nó. Từ chối mặc định của thể
 * loại — dashboard PACS nền đen với gauge phát sáng — và dựng output của model thành
 * một tấm hải đồ đã khảo sát, có khai báo chỗ nào đo kỹ và chỗ nào chưa ai đo.
 *
 * OWN-WORLD: Giấy hải đồ #F5F6F4, dải marginalia buff #E4D8B8, ba dải lam mã hoá mức
 * tin cậy, mực đen ngả lam, magenta #C0247E dành riêng cho `defer`. Archivo Narrow
 * cho nhãn, Archivo cho số, chữ số bảng khắp nơi. Bo góc 0, đổ bóng 0, hairline, gạch
 * chéo 45° nghĩa là chưa có dữ liệu, chữ đứng so với chữ nghiêng mang nghĩa số đo
 * thật so với số minh hoạ.
 *
 * STORY: Người review mở một ca, thấy ảnh MRI thật, đọc bảy sounding xác suất, rồi
 * gặp panel Zone of Confidence nói cho họ biết đọc số này được tới đâu — kèm overprint
 * magenta khi model từ chối quyết.
 *
 * FIRST VIEWPORT: Dải marginalia dính trên cùng mang RUO, định danh ca và provenance.
 * Dưới đó hai cột: trái là bộ chuyển lát với ảnh MRI thật, phải là trường sounding rồi
 * tới panel Zone of Confidence. Hành động chính nằm ở khối chọn ca.
 *
 * FORM: hải đồ đo sâu, ứng viên 4 trên 7 trong danh sách grounded, staging "wound
 * medium" cho bộ chuyển lát, seed 9b1535ee.
 */

import { useCallback, useEffect, useState } from 'react';

import { ApiError, getCase, getMeta, listCases, predictCase, predictUpload } from '@/api/client';
import type { CaseDetail, CaseSummary, MetaResponse, PredictResult } from '@/api/types';
import { isProvisional } from '@/api/types';
import { CasePicker } from '@/components/CasePicker';
import { MarkBenign, MarkCaution, MarkMalignant, MarkSquare } from '@/components/ChartMarks';
import { ConfidenceZone } from '@/components/ConfidenceZone';
import { ProvenanceTag, Unsurveyed } from '@/components/Provenance';
import { SliceTransport } from '@/components/SliceTransport';
import { SoundingField } from '@/components/SoundingField';
import { UploadPanel } from '@/components/UploadPanel';

export default function App() {
  const [meta, setMeta] = useState<MetaResponse | null>(null);
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [detail, setDetail] = useState<CaseDetail | null>(null);
  const [result, setResult] = useState<PredictResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getMeta(), listCases()])
      .then(([m, c]) => {
        setMeta(m);
        setCases(c);
      })
      .catch((e: ApiError) => setError(e.message));
  }, []);

  const openCase = useCallback(async (caseId: string) => {
    setBusy(true);
    setError(null);
    try {
      const [caseDetail, prediction] = await Promise.all([getCase(caseId), predictCase(caseId)]);
      setDetail(caseDetail);
      setResult(prediction);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
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
    } catch (e) {
      setError(e instanceof ApiError ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }, []);

  const provisional = result ? isProvisional(result.provenance) : true;

  return (
    <div className="min-h-full bg-paper">
      {/* Dải marginalia: khối title-block của hải đồ. Dính trên cùng, không bao giờ
          cuộn khuất — RUO phải có mặt trên mọi bề mặt có kết quả. */}
      <header className="sticky top-0 z-10 border-b-hair border-rule bg-land">
        <div className="mx-auto flex max-w-chart flex-wrap items-baseline justify-between gap-x-lg gap-y-xs px-lg py-sm">
          <p className="flex items-center gap-sm font-narrow text-marginalia text-ink">
            <MarkSquare className="h-[11px] w-[11px]" />
            {meta?.ruo_notice ?? 'Research Use Only: chưa kiểm định lâm sàng'}
          </p>
          <p className="font-narrow text-marginalia text-ink-secondary">
            {result ? (
              <>
                Ca {result.case_id} · <ProvenanceTag provenance={result.provenance} />
              </>
            ) : (
              'Chưa chọn ca'
            )}
          </p>
        </div>
      </header>

      <main className="mx-auto max-w-chart px-lg py-lg">
        <div className="mb-xl max-w-measure">
          <h1 className="font-narrow text-chart-title text-ink">
            Model biết chỗ nào nó không đọc được
          </h1>
          <p className="mt-sm text-body text-ink-secondary">
            Bộ phân loại bảy lớp tổn thương gan trên MRI 3D tám thì. Đóng góp không nằm ở
            accuracy mà ở chỗ nó báo được mức tin cậy của từng ca và từ chối những ca nó
            không chắc, thay vì luôn trả về một nhãn.
          </p>
        </div>

        {error ? (
          <div
            role="alert"
            className="mb-lg flex items-start gap-sm border-hair border-caution bg-paper p-md"
          >
            <MarkCaution className="mt-[3px] h-[14px] w-[14px] shrink-0 text-caution" />
            <p className="max-w-measure text-body text-ink">{error}</p>
          </div>
        ) : null}

        <div className="grid grid-cols-1 gap-lg lg:grid-cols-12">
          <div className="lg:col-span-5">
            <CasePicker cases={cases} selected={detail?.case_id ?? null} busy={busy} onSelect={openCase} />
          </div>
          <div className="lg:col-span-7">
            {meta ? (
              <UploadPanel phases={meta.phases} busy={busy} onSubmit={runUpload} />
            ) : (
              <Unsurveyed label="Đang nạp danh sách thì từ backend" />
            )}
          </div>
        </div>

        {result ? (
          <div className="mt-xl grid grid-cols-1 gap-lg lg:grid-cols-12">
            <div className="lg:col-span-7">
              {detail && meta ? (
                <SliceTransport caseId={detail.case_id} phases={meta.phases} volumes={detail.volumes} />
              ) : (
                <Unsurveyed
                  label="Không có ảnh cho kết quả này"
                  detail="Đường tải lên chưa lưu volume ở server. Chọn một ca demo dựng sẵn để xem ảnh."
                />
              )}

              <div className="mt-lg plate p-lg">
                <h2 className="mb-sm font-narrow text-headline text-ink">Vùng model đang nhìn</h2>
                <Unsurveyed
                  label="Chưa khảo sát: Grad-CAM chưa xây dựng"
                  detail="Bản đồ chú ý 3D thuộc giai đoạn sau. Vùng gạch chéo nghĩa là chưa có dữ liệu, không phải không có tín hiệu."
                />
              </div>
            </div>

            <div className="flex flex-col gap-lg lg:col-span-5">
              <div className="plate p-lg">
                <SoundingField probs={result.probs} provisional={provisional} />
              </div>
              <ConfidenceZone result={result} provisional={provisional} />
            </div>
          </div>
        ) : null}
      </main>

      {/* Chân hải đồ: chú giải ký hiệu. Mọi ký hiệu dùng trên mặt đều phải có ở đây. */}
      <footer className="mt-xxl border-t-hair border-rule bg-land">
        <div className="mx-auto max-w-chart px-lg py-lg">
          <h2 className="mb-md font-narrow text-legend text-ink">Chú giải</h2>
          <dl className="grid grid-cols-1 gap-md sm:grid-cols-2 lg:grid-cols-4">
            <div className="flex items-baseline gap-sm">
              <MarkMalignant className="h-[11px] w-[11px] shrink-0 text-ink" />
              <div>
                <dt className="font-narrow text-marginalia text-ink">nhóm ác tính</dt>
                <dd className="font-narrow text-marginalia text-ink-secondary">ICC, di căn, HCC</dd>
              </div>
            </div>
            <div className="flex items-baseline gap-sm">
              <MarkBenign className="h-[11px] w-[11px] shrink-0 text-ink" />
              <div>
                <dt className="font-narrow text-marginalia text-ink">nhóm lành tính</dt>
                <dd className="font-narrow text-marginalia text-ink-secondary">
                  u máu, áp-xe, nang, FNH
                </dd>
              </div>
            </div>
            <div className="flex items-baseline gap-sm">
              <MarkCaution className="h-[11px] w-[11px] shrink-0 text-caution" />
              <div>
                <dt className="font-narrow text-marginalia text-ink">defer</dt>
                <dd className="font-narrow text-marginalia text-ink-secondary">
                  model từ chối quyết, chuyển bác sĩ
                </dd>
              </div>
            </div>
            <div className="flex items-baseline gap-sm">
              <span className="unsurveyed mt-[2px] block h-[11px] w-[11px] shrink-0 border-hair border-dashed border-ink-tertiary" />
              <div>
                <dt className="font-narrow text-marginalia text-ink">gạch chéo</dt>
                <dd className="font-narrow text-marginalia text-ink-secondary">chưa có dữ liệu</dd>
              </div>
            </div>
          </dl>

          <p className="mt-lg max-w-measure border-t-hair border-rule pt-md font-narrow text-marginalia text-ink-secondary">
            <span className="italic">Chữ nghiêng</span> đánh dấu con số minh hoạ, chưa phải kết quả
            đo được. Trên hải đồ, chữ nghiêng nghĩa là đối tượng chìm hoặc ngập nước, tức chỉ đôi
            khi mới thấy.
          </p>
          <p className="mt-sm max-w-measure font-narrow text-marginalia text-ink-secondary">
            Research Use Only. Công cụ này chưa được kiểm định lâm sàng và không dùng để chẩn đoán.
          </p>
        </div>
      </footer>
    </div>
  );
}
