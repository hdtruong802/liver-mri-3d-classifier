import { lazy, Suspense, useState, type ReactNode } from 'react';

import type { ClassProbability } from '@/api/types';

type Tab = 'probabilities' | 'images';

const tabs: Tab[] = ['probabilities', 'images'];

const ClassProbabilityChart = lazy(async () => {
  const module = await import('@/components/ClassProbabilityChart');
  return { default: module.ClassProbabilityChart };
});

export function ResultDetailsTabs({
  probs,
  imageExplorer,
}: {
  probs: ClassProbability[];
  imageExplorer: ReactNode;
}) {
  const [active, setActive] = useState<Tab>('probabilities');

  return (
    <section aria-label="Kết quả ca demo" className="mt-6">
      <div className="flex justify-end border-b border-pacs-700">
        <div aria-label="Chi tiết kết quả" className="flex gap-1">
          <TabButton active={active === 'probabilities'} onClick={() => setActive('probabilities')} id="probabilities">
            Dự đoán
          </TabButton>
          <TabButton active={active === 'images'} onClick={() => setActive('images')} id="images">
            Ảnh MRI
          </TabButton>
        </div>
      </div>

      {tabs.map((tab) => (
        <div
          key={tab}
          id={`result-${tab}-panel`}
          hidden={active !== tab}
          className="mt-4"
        >
          {tab === 'probabilities' ? (
            <Suspense fallback={<p className="workstation-section py-5 text-sm text-slate-400">Đang tải biểu đồ…</p>}>
              <ClassProbabilityChart probs={probs} />
            </Suspense>
          ) : active === 'images' ? imageExplorer : null}
        </div>
      ))}
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
      aria-pressed={active}
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
