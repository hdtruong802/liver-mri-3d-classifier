/**
 * Kiểu dữ liệu API, phản chiếu `webapp/backend/schemas.py`.
 *
 * Taxonomy và danh sách thì KHÔNG được khai báo lại ở đây — chúng đến từ
 * `GET /api/meta` lúc chạy. Bản bolt tự khai một taxonomy riêng và nó sai: 6 lớp
 * kèm một lớp "gan khoẻ mạnh" không tồn tại, thiếu ICC và áp-xe. Nguồn sự thật duy
 * nhất là `src/data/taxonomy.py`, đi qua backend.
 */

/** Con số trong phản hồi từ đâu ra. Quyết định cách frontend được phép vẽ nó. */
export type ProvenanceSource = 'simulated' | 'oof' | 'live';

export interface Provenance {
  source: ProvenanceSource;
  /** null khi chưa có model. Không bao giờ dựng chuỗi phiên bản ở phía client. */
  model_version: string | null;
  note: string;
}

export interface Uncertainty {
  /** Shannon entropy, đơn vị nat. */
  entropy: number;
  /** null khi chạy một model đơn lẻ. null ≠ 0: 0 nghĩa là ensemble đồng thuận tuyệt đối. */
  ensemble_std: number | null;
}

export interface ClassProbability {
  class_index: number;
  class_name: string;
  label_vi: string;
  malignant: boolean;
  probability: number;
}

export interface PredictResult {
  case_id: string;
  pred_class_index: number;
  pred_class_name: string;
  probs: ClassProbability[];
  malignant_prob: number;
  uncertainty: Uncertainty;
  defer: boolean;
  defer_threshold: number;
  confidence: number;
  heatmap_slices: string[];
  inference_ms: number | null;
  provenance: Provenance;
}

export interface PhaseInfo {
  index: number;
  name: string;
  file_token: string;
  label_vi: string;
  description_vi: string;
}

export interface ClassInfo {
  index: number;
  name: string;
  label_vi: string;
  malignant: boolean;
}

export interface MetaResponse {
  classes: ClassInfo[];
  phases: PhaseInfo[];
  ruo_notice: string;
  default_defer_threshold: number;
}

export interface CaseVolumeInfo {
  phase_name: string;
  file_token: string;
  shape: [number, number, number];
  spacing_mm: [number, number, number];
  n_slices: number;
}

export interface CaseSummary {
  case_id: string;
  label_vi: string;
  source_note: string;
  /** false khi thư mục dữ liệu không có trên máy này (data/ bị gitignore). */
  available: boolean;
}

export interface CaseDetail {
  case_id: string;
  label_vi: string;
  source_note: string;
  volumes: CaseVolumeInfo[];
  reference_phase: string;
  provenance: Provenance;
}

/** Số giả lập phải được đánh dấu bằng hai tín hiệu độc lập: chữ nghiêng và nhãn chữ. */
export function isProvisional(provenance: Provenance): boolean {
  return provenance.source === 'simulated';
}
