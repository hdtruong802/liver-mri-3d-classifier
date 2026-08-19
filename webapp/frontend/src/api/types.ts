/**
 * Kiểu dữ liệu API, phản chiếu `webapp/backend/schemas.py`.
 *
 * Taxonomy và danh sách thì KHÔNG được khai báo lại ở đây — chúng đến từ
 * `GET /api/meta` lúc chạy. Bản bolt tự khai một taxonomy riêng và nó sai: 6 lớp
 * kèm một lớp "gan khoẻ mạnh" không tồn tại, thiếu ICC và áp-xe. Nguồn sự thật duy
 * nhất là `src/data/taxonomy.py`, đi qua backend.
 */

/** Con số trong phản hồi từ đâu ra. Quyết định cách frontend được phép vẽ nó. */
export type ProvenanceSource = 'oof' | 'live';

export interface Provenance {
  source: ProvenanceSource;
  /** null khi chưa có model. Không bao giờ dựng chuỗi phiên bản ở phía client. */
  model_version: string | null;
  note: string;
}

export interface Uncertainty {
  /** Shannon entropy, đơn vị nat. */
  entropy: number;
  /**
   * Bất định epistemic — mutual information giữa các lượt MC-dropout, đơn vị nat.
   * null khi chỉ có một lượt. null ≠ 0: 0 nghĩa là các lượt đồng thuận tuyệt đối.
   */
  epistemic: number | null;
  /** Độ lệch chuẩn giữa thành viên ensemble. KHÁC `epistemic` cả định nghĩa lẫn đơn vị. */
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
  defer: boolean | null;
  /**
   * Đại lượng nào được so với ngưỡng. Chiều so sánh NGƯỢC NHAU giữa hai giá trị:
   * `confidence` thấp thì từ chối, `epistemic` cao thì từ chối. Đừng giả định một
   * chiều — một ca có thể bị từ chối dù confidence 0,94 (WORKLOG S-087).
   */
  defer_basis: 'confidence' | 'epistemic' | null;
  /** Giá trị của chính đại lượng nêu ở `defer_basis`. KHÔNG phải lúc nào cũng bằng `confidence`. */
  defer_score: number | null;
  /** Ngưỡng khoá trên validation, cùng đơn vị với `defer_score`. */
  defer_threshold: number | null;
  confidence: number;
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

export type UploadPhaseState = 'ready' | 'missing' | 'duplicate';

export interface UploadPhaseValidation {
  index: number;
  file_token: string;
  label_vi: string;
  filename: string | null;
  state: UploadPhaseState;
  mask_filename: string | null;
  mask_state: UploadPhaseState;
}

/** Chỉ là kiểm tra manifest ZIP; cố ý không chứa prediction hoặc uncertainty. */
export interface UploadValidationResult {
  archive_name: string;
  valid: boolean;
  inference_ready: boolean;
  message: string;
  errors: string[];
  phases: UploadPhaseValidation[];
}

export interface UploadPredictionResult extends UploadValidationResult {
  prediction: PredictResult | null;
  upload_view: UploadViewInfo | null;
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
  /**
   * Có nhãn segmentation OFFICIAL của LLD-MMRI không. Đây là nhãn do người chú giải,
   * KHÔNG phải đầu ra của model — dự án không làm segmentation. Mọi chỗ hiển thị nó
   * phải nói rõ, nếu không người xem sẽ tưởng model tự khoanh được tổn thương.
   */
  has_mask: boolean;
  /**
   * Chỉ số lát (0-based) có tổn thương, để đánh dấu trên thanh trượt. Cùng nguồn với
   * `has_mask`: nhãn của người chú giải, KHÔNG phải vùng model tìm ra.
   */
  mask_slices: number[];
}

/** Crop ROI UniFormer chỉ giữ trong bộ nhớ tạm sau một lần upload thành công. */
export interface UploadViewInfo {
  upload_id: string;
  volumes: CaseVolumeInfo[];
  expires_in_seconds: number;
  note: string;
}
