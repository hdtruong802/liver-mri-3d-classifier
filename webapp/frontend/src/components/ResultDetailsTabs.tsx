import { lazy, Suspense, useState, type KeyboardEvent, type ReactNode } from 'react';

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

  const moveToTab = (event: KeyboardEvent<HTMLButtonElement>, current: Tab) => {
    const index = tabs.indexOf(current);
    const nextIndex = event.key === 'Home'
      ? 0
      : event.key === 'End'
        ? tabs.length - 1
        : event.key === 'ArrowRight'
          ? (index + 1) % tabs.length
          : event.key === 'ArrowLeft'
            ? (index - 1 + tabs.length) % tabs.length
            : null;

    if (nextIndex === null) return;
    event.preventDefault();
    const next = tabs[nextIndex];
    setActive(next);
    document.getElementById(`result-${next}-tab`)?.focus();
  };

  return (
    <section aria-label="Kết quả ca demo" className="mt-6">
      <div className="flex justify-end border-b border-pacs-700">
        <div role="tablist" aria-label="Chi tiết kết quả" className="flex gap-1">
          <TabButton active={active === 'probabilities'} onClick={() => setActive('probabilities')} onKeyDown={moveToTab} id="probabilities">
            Dự đoán
          </TabButton>
          <TabButton active={active === 'images'} onClick={() => setActive('images')} onKeyDown={moveToTab} id="images">
            Ảnh MRI
          </TabButton>
        </div>
      </div>

      {tabs.map((tab) => (
        <div
          key={tab}
          role="tabpanel"
          id={`result-${tab}-panel`}
          aria-labelledby={`result-${tab}-tab`}
          hidden={active !== tab}
          className="mt-4"
        >
          {tab === 'probabilities' ? (
            <Suspense fallback={<p className="panel p-5 text-sm text-slate-400">Đang tải biểu đồ…</p>}>
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
  onKeyDown,
  id,
  children,
}: {
  active: boolean;
  onClick: () => void;
  onKeyDown: (event: KeyboardEvent<HTMLButtonElement>, current: Tab) => void;
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
      tabIndex={active ? 0 : -1}
      onClick={onClick}
      onKeyDown={(event) => onKeyDown(event, id)}
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
