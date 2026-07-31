/**
 * Một thẻ thì trong lưới 4×2.
 *
 * Cấu trúc port từ `UploadDropzone.tsx` của bản bolt: icon, số thứ tự, tên thì, mô tả,
 * chip file kèm dấu tích, chân thẻ có token và badge trạng thái.
 *
 * Hai chỗ khác bản gốc:
 *   - danh sách thì đến từ `GET /api/meta`, không tự khai. Bản bolt khai `ADC Map` và
 *     `Hepatobiliary Phase`, hai thì KHÔNG có trong LLD-MMRI.
 *   - trạng thái luôn kèm chữ ("đủ" / "thiếu"), không chỉ mã hoá bằng màu viền.
 */

import { useRef, useState } from 'react';
import { Check, UploadCloud, X } from 'lucide-react';

import type { PhaseInfo } from '@/api/types';
import { iconOfPhase } from '@/catalog';

interface Props {
  phase: PhaseInfo;
  file: File | null;
  disabled: boolean;
  onFile: (file: File) => void;
  onClear: () => void;
}

export function PhaseCard({ phase, file, disabled, onFile, onClear }: Props) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const Icon = iconOfPhase(phase.file_token);
  const filled = file !== null;

  return (
    <div
      onDragOver={(event) => {
        event.preventDefault();
        if (!disabled) setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(event) => {
        event.preventDefault();
        setDragging(false);
        const dropped = event.dataTransfer.files?.[0];
        if (dropped && !disabled) onFile(dropped);
      }}
      className={[
        'flex flex-col gap-3 rounded-panel border p-4 transition',
        filled
          ? 'border-ok/40 bg-ok/5'
          : dragging
            ? 'border-accent bg-accent/10 shadow-glow'
            : 'border-pacs-700 bg-pacs-850',
      ].join(' ')}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".nii,.nii.gz"
        className="sr-only"
        disabled={disabled}
        onChange={(event) => {
          const picked = event.target.files?.[0];
          if (picked) onFile(picked);
          event.target.value = '';
        }}
      />

      <div className="flex items-start justify-between gap-2">
        <div className="flex min-w-0 items-center gap-3">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-control border border-pacs-700 bg-pacs-800">
            <Icon className="h-5 w-5 text-accent" aria-hidden="true" />
          </span>
          <div className="min-w-0">
            <p className="flex items-baseline gap-2">
              <span className="font-mono text-data text-slate-400">#{phase.index + 1}</span>
              <span className="truncate text-sm font-semibold text-white">{phase.label_vi}</span>
            </p>
            <p className="truncate text-data text-slate-400">{phase.description_vi}</p>
          </div>
        </div>

        {filled ? (
          <button
            type="button"
            onClick={onClear}
            disabled={disabled}
            aria-label={`Bỏ file của thì ${phase.label_vi}`}
            className="grid h-7 w-7 shrink-0 place-items-center rounded-control border border-pacs-700 bg-pacs-800 text-slate-400 transition hover:border-danger/50 hover:text-danger"
          >
            <X className="h-4 w-4" aria-hidden="true" />
          </button>
        ) : null}
      </div>

      <div className="flex min-h-[68px] flex-1 items-center justify-center">
        {filled ? (
          <div className="flex w-full items-center gap-2.5 rounded-control bg-ok/10 px-3 py-2.5">
            <Check className="h-4 w-4 shrink-0 text-ok" aria-hidden="true" />
            <div className="min-w-0 flex-1">
              <p className="truncate font-mono text-data text-ok-soft">{file.name}</p>
              <p className="text-data text-slate-400">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
            </div>
          </div>
        ) : (
          <button
            type="button"
            disabled={disabled}
            onClick={() => inputRef.current?.click()}
            className="flex w-full flex-col items-center gap-1.5 rounded-control border border-dashed border-pacs-600 py-3 text-slate-400 transition hover:border-accent hover:text-accent disabled:cursor-not-allowed disabled:hover:border-pacs-600 disabled:hover:text-slate-400"
          >
            <UploadCloud className="h-6 w-6" aria-hidden="true" />
            <span className="text-data">Kéo thả hoặc chọn file .nii</span>
          </button>
        )}
      </div>

      <div className="flex items-center justify-between gap-2 border-t border-pacs-700 pt-3">
        <span className="font-mono text-data text-slate-400">{phase.file_token}</span>
        <span
          className={
            filled ? 'chip bg-ok/15 text-ok-soft' : 'chip border border-pacs-600 bg-pacs-800 text-slate-400'
          }
        >
          {filled ? 'đủ' : 'thiếu'}
        </span>
      </div>
    </div>
  );
}
