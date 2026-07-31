/** Gọi API. Cùng origin qua proxy của Vite, nên không cần CORS. */

import type { CaseDetail, CaseSummary, MetaResponse, PredictResult } from '@/api/types';

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

export function predictUpload(files: File[]): Promise<PredictResult> {
  const form = new FormData();
  for (const file of files) form.append('files', file, file.name);
  return request<PredictResult>('/api/predict', { method: 'POST', body: form });
}

/** URL ảnh một lát. Ảnh MRI thật, render từ NIfTI ở backend. */
export function sliceUrl(caseId: string, phaseToken: string, z: number): string {
  const params = new URLSearchParams({ phase: phaseToken, z: String(z) });
  return `/api/cases/${encodeURIComponent(caseId)}/slice?${params}`;
}
