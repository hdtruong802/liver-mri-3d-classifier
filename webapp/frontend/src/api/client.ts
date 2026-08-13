/** Gọi API. Cùng origin qua proxy của Vite, nên không cần CORS. */

import type {
  CaseDetail,
  CaseSummary,
  MetaResponse,
  PredictResult,
  UploadPredictionResult,
  UploadValidationResult,
} from '@/api/types';

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, init);
  } catch {
    // Lỗi mạng: nêu đúng vấn đề và cách khắc phục, không nói chung chung.
    throw new ApiError('Không kết nối được backend. Chạy: uvicorn webapp.backend.main:app --reload', 0);
  }
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      /* phản hồi không phải JSON — giữ nguyên detail mặc định */
    }
    throw new ApiError(detail, response.status);
  }
  return (await response.json()) as T;
}

export const getMeta = () => request<MetaResponse>('/api/meta');
export const listCases = () => request<CaseSummary[]>('/api/cases');
export const getCase = (caseId: string) => request<CaseDetail>(`/api/cases/${encodeURIComponent(caseId)}`);

export const predictCase = (caseId: string) =>
  request<PredictResult>(`/api/cases/${encodeURIComponent(caseId)}/predict`, { method: 'POST' });

export function validateUpload(archive: File): Promise<UploadValidationResult> {
  const form = new FormData();
  form.append('archive', archive, archive.name);
  return request<UploadValidationResult>('/api/validate-upload', { method: 'POST', body: form });
}

export function predictUpload(archive: File): Promise<UploadPredictionResult> {
  const form = new FormData();
  form.append('archive', archive, archive.name);
  return request<UploadPredictionResult>('/api/predict-upload', { method: 'POST', body: form });
}

/** URL ảnh hợp nhất trên lưới crop E4: MRI → heatmap → nhãn người chú giải. */
export function modelViewUrl(
  caseId: string,
  phaseToken: string,
  z: number,
  annotation: boolean,
  heatmap: boolean,
): string {
  const params = new URLSearchParams({
    phase: phaseToken,
    z: String(z),
    annotation: String(annotation),
    heatmap: String(heatmap),
  });
  return `/api/cases/${encodeURIComponent(caseId)}/model-view?${params}`;
}

/** MRI fallback khi ca chưa có artefact crop E4/heatmap đã kiểm tra. */
export function sliceUrl(caseId: string, phaseToken: string, z: number, annotation: boolean): string {
  const params = new URLSearchParams({
    phase: phaseToken,
    z: String(z),
    mask: String(annotation),
  });
  return `/api/cases/${encodeURIComponent(caseId)}/slice?${params}`;
}

/** MRI nguồn tạm thời của một bộ ZIP vừa suy luận xong. */
export function uploadSliceUrl(uploadId: string, phaseToken: string, z: number, annotation: boolean): string {
  const params = new URLSearchParams({
    phase: phaseToken,
    z: String(z),
    mask: String(annotation),
  });
  return `/api/uploads/${encodeURIComponent(uploadId)}/slice?${params}`;
}
