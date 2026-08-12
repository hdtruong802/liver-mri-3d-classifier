import { useState, type ReactNode } from 'react';

import type { ClassProbability } from '@/api/types';
import { ClassProbabilityChart } from '@/components/ClassProbabilityChart';

type Tab = 'probabilities' | 'images';

export function ResultDetailsTabs({
  probs,
  imageExplorer,
}: {
  probs: ClassProbability[];
  imageExplorer: ReactNode;
}) {
  const [active, setActive] = useState<Tab>('probabilities');

  return (
    <section aria-labelledby="details-heading" className="mt-6">
      <div className="flex flex-wrap items-end justify-between gap-3 border-b border-pacs-700">
        <h2 id="details-heading" className="pb-3 text-lg font-bold text-white">Chi tiết ca demo</h2>
        <div role="tablist" aria-label="Chi tiết kết quả" className="flex gap-1">
          <TabButton active={active === 'probabilities'} onClick={() => setActive('probabilities')} id="probabilities">
            Xác suất
          </TabButton>
          <TabButton active={active === 'images'} onClick={() => setActive('images')} id="images">
            Khám phá ảnh
          </TabButton>
        </div>
      </div>

      <div
        role="tabpanel"
        id={`result-${active}-panel`}
        aria-labelledby={`result-${active}-tab`}
        className="mt-4"
      >
        {active === 'probabilities' ? <ClassProbabilityChart probs={probs} /> : imageExplorer}
      </div>
    </section>
  );
}

function TabButton({
  active,
  onClick,
  id,
  children,
}: {
  active: boolean;
  onClick: () => void;
  id: Tab;
  children: ReactNode;
}) {
  return (
    <button
      id={`result-${id}-tab`}
      type="button"
      role="tab"
      aria-selected={active}
      aria-controls={`result-${id}-panel`}
      onClick={onClick}
      className={`border-b-2 px-3 py-3 text-sm font-semibold transition-colors ${
        active
          ? 'border-accent text-accent'
          : 'border-transparent text-slate-400 hover:text-slate-200'
      }`}
    >
      {children}
    </button>
  );
}
