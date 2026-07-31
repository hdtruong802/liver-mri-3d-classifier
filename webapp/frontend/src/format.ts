/** Định dạng số. Tiếng Việt dùng dấu phẩy thập phân, khớp với report và slide. */

export function percent(value: number, digits = 1): string {
  return (value * 100).toFixed(digits).replace('.', ',');
}

export function decimal(value: number, digits = 3): string {
  return value.toFixed(digits).replace('.', ',');
}

/** Nhãn "ác" / "lành" bằng chữ. Màu và hình dạng chỉ là tín hiệu bổ sung. */
export function groupLabel(malignant: boolean): string {
  return malignant ? 'ác' : 'lành';
}
