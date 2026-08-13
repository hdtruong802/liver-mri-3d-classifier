import { BarChart3 } from 'lucide-react';

import type { ClassProbability } from '@/api/types';
import { colorOfClass } from '@/catalog';
import { percent } from '@/format';

export function ClassProbabilityChart({ probs }: { probs: ClassProbability[] }) {
  const rows = [...probs].sort((a, b) => b.probability - a.probability);

  return (
    <section className="probability-list" aria-labelledby="probs-heading">
      <div className="probability-list__heading">
        <BarChart3 aria-hidden="true" />
        <h3 id="probs-heading">Dự đoán từng lớp</h3>
      </div>
      <ul>
        {rows.map((entry) => {
          const value = Math.max(0, Math.min(100, entry.probability * 100));
          return (
            <li key={entry.class_index}>
              <div className="probability-list__row">
                <span>{entry.label_vi}</span>
                <strong>{percent(entry.probability)}%</strong>
              </div>
              <div className="probability-list__track" aria-hidden="true">
                <span style={{ width: `${value}%`, backgroundColor: colorOfClass(entry.class_index) }} />
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
