/**
 * Ký hiệu hải đồ, vẽ tay bằng SVG theo ngữ pháp của thế giới này.
 *
 * Không dùng thư viện icon. `webapp/DESIGN.md`: "mọi ký hiệu mượn từ hải đồ phải
 * mang một nghĩa của dữ liệu; ký hiệu nào chỉ để trông giống hải đồ thì bỏ."
 *
 * Ba ký hiệu, ba nghĩa, hết. Mỗi cái luôn đi kèm nhãn chữ ở nơi dùng — hình dạng là
 * tuyến tín hiệu thứ hai, không phải tuyến duy nhất.
 */

interface MarkProps {
  className?: string;
  /** Mô tả cho screen reader. Bỏ trống khi ký hiệu chỉ lặp lại nhãn chữ ngay cạnh. */
  title?: string;
}

function Frame({ title, className, children }: MarkProps & { children: React.ReactNode }) {
  return (
    <svg
      viewBox="0 0 12 12"
      className={className}
      aria-hidden={title ? undefined : true}
      role={title ? 'img' : undefined}
      focusable="false"
    >
      {title ? <title>{title}</title> : null}
      {children}
    </svg>
  );
}

/** Nhóm ác tính. Tam giác đặc — trên hải đồ là mối nguy nổi trên mặt nước. */
export function MarkMalignant(props: MarkProps) {
  return (
    <Frame {...props}>
      <path d="M6 1.5 L11 10.5 L1 10.5 Z" fill="currentColor" />
    </Frame>
  );
}

/** Nhóm lành tính. Vòng tròn rỗng — vị trí đo, không phải mối nguy. */
export function MarkBenign(props: MarkProps) {
  return (
    <Frame {...props}>
      <circle cx="6" cy="6" r="4" fill="none" stroke="currentColor" strokeWidth="1.4" />
    </Frame>
  );
}

/** Cảnh báo. Hình thoi rỗng có chấm giữa — ký hiệu chú ý trên hải đồ. */
export function MarkCaution(props: MarkProps) {
  return (
    <Frame {...props}>
      <path d="M6 1 L11 6 L6 11 L1 6 Z" fill="none" stroke="currentColor" strokeWidth="1.4" />
      <circle cx="6" cy="6" r="1.2" fill="currentColor" />
    </Frame>
  );
}

/** Ô vuông rỗng của dải RUO. */
export function MarkSquare(props: MarkProps) {
  return (
    <Frame {...props}>
      <rect x="1.5" y="1.5" width="9" height="9" fill="none" stroke="currentColor" strokeWidth="1.4" />
    </Frame>
  );
}
