import { Clock, X, ChevronRight } from 'lucide-react';
import { BlockMath } from 'react-katex';
import type { HistoryItem } from '../types/history';

interface HistoryPanelProps {
  isOpen: boolean;
  onClose: () => void;
  history: HistoryItem[];
  onSelect: (item: HistoryItem) => void;
  voiceGuidance: boolean;
  speak: (text: string) => void;
}

export function HistoryPanel({
  isOpen,
  onClose,
  history,
  onSelect,
  voiceGuidance,
  speak,
}: HistoryPanelProps) {
  if (!isOpen) return null;

  return (
    <>
      <div className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm" onClick={onClose} aria-hidden />
      <div
        className="fixed right-0 top-0 z-50 flex h-full w-full max-w-sm flex-col bg-white shadow-2xl"
        role="dialog"
        aria-labelledby="history-title"
      >
        <div className="flex items-center justify-between border-b border-gray-100 bg-gray-50/80 p-6">
          <div className="flex items-center gap-3 text-gray-800">
            <Clock size={20} className="text-blue-500" />
            <h2 id="history-title" className="text-lg font-semibold">
              Recognition History
            </h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-2 text-gray-500 transition-colors hover:bg-gray-200 hover:text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Close history"
          >
            <X size={20} />
          </button>
        </div>

        <div className="flex-1 space-y-4 overflow-y-auto p-4">
          {history.length === 0 ? (
            <div
              className="flex h-full flex-col items-center justify-center space-y-4 text-gray-400"
              tabIndex={0}
              onFocus={() => voiceGuidance && speak('History is empty.')}
            >
              <Clock size={48} className="text-gray-600 opacity-20" />
              <p>No formulas recognized yet.</p>
            </div>
          ) : (
            history.map((item, index) => (
              <button
                key={item.id}
                onClick={() => onSelect(item)}
                className="group flex w-full items-center justify-between rounded-xl border border-gray-200 bg-white p-4 text-left transition-all hover:border-blue-400 hover:shadow-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                aria-label={`View formula ${index + 1}`}
              >
                <div className="flex-1 overflow-hidden pr-4">
                  <div className="mb-2 flex items-center gap-1 text-xs text-gray-400">
                    {new Date(item.timestamp).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </div>
                  <div className="flex min-h-[60px] items-center justify-center overflow-x-hidden rounded-lg bg-gray-50 p-3">
                    <BlockMath math={item.latex} />
                  </div>
                </div>
                <ChevronRight
                  size={20}
                  className="flex-shrink-0 text-gray-300 transition-colors group-hover:text-blue-500"
                />
              </button>
            ))
          )}
        </div>
      </div>
    </>
  );
}
