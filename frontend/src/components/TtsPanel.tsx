import { useState } from 'react';
import { TTS_PRESET_LATEX, UI_CONSTANTS } from '../config/constants';

interface TtsPanelProps {
  onConvertAndSpeakLatex: (latex: string) => Promise<void>;
  onSpeakTextDirectly: (text: string) => void;
}

export function TtsPanel({ onConvertAndSpeakLatex, onSpeakTextDirectly }: TtsPanelProps) {
  const [customPhrase, setCustomPhrase] = useState(
    'E=mc squared, the theory of relativity',
  );
  const [status, setStatus] = useState('✅ Ready — click any button for English audio');

  const updateStatus = (message: string) => {
    setStatus(message);
    if (message.includes('finished') || message.includes('Ready')) {
      window.setTimeout(() => {
        setStatus((current) =>
          current === message ? '✅ Ready — click any button for English audio' : current,
        );
      }, UI_CONSTANTS.STATUS_RESET_DELAY_MS);
    }
  };

  const speakLatex = async (latex: string) => {
    updateStatus('🔄 Converting LaTeX to spoken text...');
    try {
      await onConvertAndSpeakLatex(latex);
      updateStatus('✅ Speaking finished.');
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Speech failed.';
      updateStatus(`❌ ${message}`);
    }
  };

  return (
    <section className="mt-8 w-full rounded-[56px] bg-white/95 px-6 py-8 text-center shadow-[0_25px_45px_-12px_rgba(0,0,0,0.25),0_4px_12px_rgba(0,0,0,0.05)] backdrop-blur-[2px]">
      <h2 className="text-2xl font-semibold text-slate-800">🔊 English Speech Buttons</h2>
      <div className="mb-7 inline-block border-b border-slate-300 pb-1.5 text-sm font-medium text-slate-600">
        Click any button → hear English pronunciation
      </div>

      <div className="my-8 flex flex-wrap justify-center gap-4">
        {TTS_PRESET_LATEX.map((preset) => (
          <button
            key={preset.id}
            onClick={() => void speakLatex(preset.latex)}
            className="min-w-[140px] rounded-[80px] border border-white/60 bg-white px-6 py-4 text-lg font-medium text-slate-900 shadow-[0_5px_12px_rgba(0,0,0,0.08),0_1px_2px_rgba(0,0,0,0.05)] transition hover:-translate-y-0.5 hover:bg-slate-50 hover:shadow-[0_14px_24px_-10px_rgba(0,0,0,0.2)] active:translate-y-0.5 active:bg-indigo-50"
          >
            {preset.label}
          </button>
        ))}
      </div>

      <div className="mt-8 flex flex-wrap items-center justify-center gap-3 rounded-[64px] bg-[#e6edf4] px-5 py-4">
        <input
          type="text"
          value={customPhrase}
          onChange={(event) => setCustomPhrase(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              event.preventDefault();
              if (customPhrase.trim() === '') {
                onSpeakTextDirectly('Please type some English text first.');
                updateStatus('⚠️ No text to speak. Please enter English words.');
                return;
              }
              onSpeakTextDirectly(customPhrase.trim());
              updateStatus('✅ Speaking finished.');
            }
          }}
          className="min-w-[220px] flex-[2] rounded-[48px] border-none bg-white px-5 py-3 text-center font-mono text-base outline-none ring-slate-800/20 focus:ring-2"
          placeholder="Type any English sentence here..."
        />
        <button
          onClick={() => {
            if (customPhrase.trim() === '') {
              onSpeakTextDirectly('Please type some English text first.');
              updateStatus('⚠️ No text to speak. Please enter English words.');
              return;
            }
            onSpeakTextDirectly(customPhrase.trim());
            updateStatus('✅ Speaking finished.');
          }}
          className="rounded-[48px] bg-[#1e3a5f] px-5 py-3 text-base font-medium text-white shadow-[0_2px_5px_rgba(0,0,0,0.1)] transition active:scale-95 active:bg-[#0f2b44]"
        >
          🔊 Speak this
        </button>
      </div>

      <div className="mt-7 inline-block rounded-[40px] bg-[#d9e2ef] px-5 py-2 text-sm text-slate-800">
        {status}
      </div>
      <footer className="mt-7 text-xs text-slate-600">
        💡 Uses browser&apos;s Web Speech API | English (US) voice
      </footer>
    </section>
  );
}
