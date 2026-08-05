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
  defer: boolean;
  /**
   * Đại lượng nào được so với ngưỡng. Chiều so sánh NGƯỢC NHAU giữa hai giá trị:
   * `confidence` thấp thì từ chối, `epistemic` cao thì từ chối. Đừng giả định một
   * chiều — một ca có thể bị từ chối dù confidence 0,94 (WORKLOG S-087).
   */
  defer_basis: 'confidence' | 'epistemic';
  /** Giá trị của chính đại lượng nêu ở `defer_basis`. KHÔNG phải lúc nào cũng bằng `confidence`. */
  defer_score: number;
  /** Ngưỡng khoá trên validation, cùng đơn vị với `defer_score`. */
  defer_threshold: number;
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

/**
 * Bản đồ chú ý của MÔ HÌNH. Khác hẳn `CaseVolumeInfo.has_mask` — cái đó là vùng
 * người chú giải khoanh (ground truth), cái này là chỗ mô hình nhạy (phỏng đoán).
 */
export interface GradCamInfo {
  available: boolean;
  /** Số lát của khối crop — KHÁC số lát của ảnh gốc ở bộ xem chính. */
  n_slices: number;
  /** Kích thước THẬT trước khi nội suy, ví dụ [7, 7, 2]. Phải hiển thị. */
  native_shape: number[];
  layer: string;
  fold: string;
  pred_class_index: number | null;
  /** Chỉ khác `pred_class_index` khi mô hình đoán sai; khi đó có thêm target 'true'. */
  true_class_index: number | null;
  /** Tổng bằng 1. Là saliency, KHÔNG phải ablation. */
  phase_importance: number[];
  /**
   * 'ok' | 'suy-bien' | 'khong-can'. `suy-bien` nghĩa là mô hình KHÔNG tìm thấy bằng
   * chứng nào cho lớp thật — là phát hiện, không phải lỗi hiển thị.
   */
  true_map_status: string;
  note: string;
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
  gradcam: GradCamInfo | null;
  provenance: Provenance;
}

/** Số giả lập phải được đánh dấu bằng hai tín hiệu độc lập: chữ nghiêng và nhãn chữ. */
export function isProvisional(provenance: Provenance): boolean {
  return provenance.source === 'simulated';
}
