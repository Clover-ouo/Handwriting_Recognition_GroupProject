import { useState } from 'react';
import { BlockMath } from 'react-katex';
import { CheckCircle2, Copy, Volume2 } from 'lucide-react';

interface ResultAreaProps {
  latex: string;
  speechText: string;
  onSpeak: (text: string) => void;
  status: string;
}

export function ResultArea({ latex, speechText, onSpeak, status }: ResultAreaProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(latex);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="mt-8 w-full overflow-hidden rounded-xl border border-gray-100 bg-white shadow-lg">
      <div className="border-b border-gray-100 bg-gray-50/50 p-6">
        <h3 className="mb-4 text-lg font-semibold text-gray-800">Rendered Result</h3>
        <div className="flex min-h-[120px] justify-center overflow-x-auto rounded-lg border border-gray-200 bg-white p-8 shadow-inner">
          <BlockMath math={latex} />
        </div>
      </div>

      <div className="p-6">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-800">LaTeX Code</h3>
          <div className="flex gap-3">
            <button
              onClick={() => onSpeak(speechText)}
              className="flex items-center gap-2 rounded-lg bg-blue-50 px-4 py-2 text-sm font-medium text-blue-700 transition-colors hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-400"
              aria-label="Listen to formula"
            >
              <Volume2 size={16} />
              Listen
            </button>
            <button
              onClick={handleCopy}
              className={`flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-gray-400 ${
                copied
                  ? 'bg-green-50 text-green-700'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
              aria-label="Copy LaTeX code"
            >
              {copied ? <CheckCircle2 size={16} /> : <Copy size={16} />}
              {copied ? 'Copied!' : 'Copy'}
            </button>
          </div>
        </div>

        <textarea
          readOnly
          value={latex}
          className="h-32 w-full resize-none rounded-lg border border-gray-200 bg-gray-50 p-4 font-mono text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          aria-label="LaTeX source code"
        />
        <div className="mt-4 inline-block rounded-full bg-[#d9e2ef] px-4 py-2 text-sm text-gray-700">
          {status}
        </div>
      </div>
    </div>
  );
}
