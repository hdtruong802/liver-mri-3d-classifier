/**
 * Biểu đồ xác suất 7 lớp — khối 8 trái của bố cục.
 *
 * Bảy cột, mỗi lớp một màu, sắp giảm dần. Ba chỗ khác bản bolt:
 *
 *   - **7 lớp, không phải 6.** Bản bolt khai một taxonomy riêng: thiếu ICC và áp-xe,
 *     thừa một lớp "Healthy" không tồn tại trong bài toán. Ở đây danh sách đến từ
 *     `GET /api/meta`, gốc là `src/data/taxonomy.py`.
 *   - **Màu không đi một mình.** Mỗi cột có nhãn tên lớp bên dưới; khử màu vẫn đọc được.
 *   - **Không giấu cột thấp.** Một xác suất 0,3% vẫn là thông tin về hình dạng phân
 *     phối, nên trục Y cố định 0–100 và mọi cột đều được vẽ.
 */

import {
  Bar,
  BarChart,
  Cell,
  LabelList,
  ResponsiveContainer,
  XAxis,
  YAxis,
} from 'recharts';
import { BarChart3 } from 'lucide-react';

import type { ClassProbability } from '@/api/types';
import { colorOfClass } from '@/catalog';
import { percent } from '@/format';

interface Row {
  name: string;
  value: number;
  color: string;
}

export function ClassProbabilityChart({ probs }: { probs: ClassProbability[] }) {
  const rows: Row[] = [...probs]
    .sort((a, b) => b.probability - a.probability)
    .map((entry) => ({
      name: entry.label_vi,
      value: Number((entry.probability * 100).toFixed(1)),
      color: colorOfClass(entry.class_index),
    }));

  return (
    <section aria-labelledby="probs-heading" className="workstation-section py-5">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-4 w-4 text-accent" aria-hidden="true" />
          <h3 id="probs-heading" className="label">
            Xác suất từng lớp
          </h3>
        </div>
        <span className="text-data text-slate-400">
          {probs.length} lớp (100%)
        </span>
      </div>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} margin={{ top: 20, right: 8, left: -12, bottom: 4 }}>
            <XAxis
              dataKey="name"
              tick={{ fill: 'var(--chart-label)', fontSize: 11 }}
              axisLine={{ stroke: 'var(--chart-grid)' }}
              tickLine={false}
              interval={0}
            />
            <YAxis
              domain={[0, 100]}
              unit="%"
              tick={{ fill: 'var(--chart-label)', fontSize: 11 }}
              axisLine={false}
              tickLine={false}
            />
            <Bar dataKey="value" radius={[4, 4, 0, 0]} maxBarSize={56} isAnimationActive={false}>
              {rows.map((row) => (
                <Cell key={row.name} fill={row.color} />
              ))}
              <LabelList
                dataKey="value"
                position="top"
                formatter={(value) => `${percent(Number(value ?? 0) / 100, 1)}%`}
                style={{
                  fill: 'var(--chart-value)',
                  fontSize: 11,
                  fontWeight: 600,
                  fontStyle: 'normal',
                }}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
