/**
 * Bảng tra màu lớp và icon thì.
 *
 * KHÔNG khai lại taxonomy hay danh sách thì ở đây — hai thứ đó đến từ
 * `GET /api/meta`, gốc là `src/data/taxonomy.py` và `configs/data.yaml`. File này chỉ
 * gắn thuộc tính trình bày vào `class_index` và `file_token` mà backend trả về.
 *
 * Nếu backend đổi taxonomy, `colorOfClass` rơi về màu trung tính thay vì vẽ sai màu.
 */

import {
  Activity,
  Combine,
  Droplet,
  Split,
  Syringe,
  Timer,
  Waves,
  Wind,
  type LucideIcon,
} from 'lucide-react';

/**
 * Bảy màu lớp. Nhóm ác dùng dải ấm, nhóm lành dùng dải lạnh — tuyến mã hoá THỨ HAI,
 * luôn đi kèm nhãn chữ và nhãn nhóm (`webapp/DESIGN.md`, The Never-Colour-Alone Rule).
 * Khoá theo `class_index` của `taxonomy.py`.
 */
const CLASS_COLORS: Record<number, string> = {
  0: '#14B8A6', // u máu — lành
  1: '#FB7185', // ICC — ác
  2: '#A3E635', // áp-xe — lành
  3: '#F97316', // di căn — ác
  4: '#38BDF8', // nang — lành
  5: '#22C55E', // FNH — lành
  6: '#EF4444', // HCC — ác
};

const NEUTRAL = '#94A3B8';

export function colorOfClass(classIndex: number): string {
  return CLASS_COLORS[classIndex] ?? NEUTRAL;
}

/**
 * Icon cho từng thì. `Combine` và `Split` cho In/Out Phase là chọn có nghĩa: in-phase
 * là lúc tín hiệu mỡ và nước cộng vào nhau, out-of-phase là lúc chúng triệt tiêu.
 */
const PHASE_ICONS: Record<string, LucideIcon> = {
  'C-pre': Activity,
  'C+A': Syringe,
  'C+V': Droplet,
  'C+Delay': Timer,
  T2WI: Waves,
  DWI: Wind,
  InPhase: Combine,
  OutPhase: Split,
};

export function iconOfPhase(fileToken: string): LucideIcon {
  return PHASE_ICONS[fileToken] ?? Activity;
}
