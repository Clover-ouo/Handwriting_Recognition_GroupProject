import { useCallback, useMemo, useState } from 'react';
import {
  Camera as CameraIcon,
  History,
  Image as ImageIcon,
  Loader2,
  PencilLine,
  Sparkles,
  Volume2,
  VolumeX,
} from 'lucide-react';
import { DrawCanvas } from './components/DrawCanvas';
import { ImageUploader } from './components/ImageUploader';
import { CameraCapture } from './components/CameraCapture';
import { ResultArea } from './components/ResultArea';
import { HistoryPanel } from './components/HistoryPanel';
import { UI_CONSTANTS } from './config/constants';
import {
  ApiClientError,
  convertLatexToSpeechText,
  inferLatexFromImage,
} from './services/apiClient';
import type { HistoryItem } from './types/history';

type InputMode = 'draw' | 'upload' | 'camera';
type RecognizeStatus = 'idle' | 'recognizing' | 'success' | 'error';

export default function App() {
  const [mode, setMode] = useState<InputMode>('draw');
  const [voiceGuidance, setVoiceGuidance] = useState(false);
  const [status, setStatus] = useState<RecognizeStatus>('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const [activeImageFile, setActiveImageFile] = useState<File | null>(null);
  const [result, setResult] = useState<{ latex: string; speech: string } | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);

  const speak = useCallback((text: string) => {
    if (!('speechSynthesis' in window) || text.trim() === '') {
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.rate = UI_CONSTANTS.SPEECH_RATE_DEFAULT;
    utterance.pitch = UI_CONSTANTS.SPEECH_PITCH_DEFAULT;
    utterance.volume = UI_CONSTANTS.SPEECH_VOLUME_DEFAULT;
    window.speechSynthesis.speak(utterance);
  }, []);

  const statusText = useMemo(() => {
    if (status === 'recognizing') return '🔄 Recognizing formula...';
    if (status === 'error') return `❌ ${errorMessage}`;
    if (status === 'success') return '✅ Recognition complete.';
    return '✅ Ready — upload, draw or capture a formula';
  }, [errorMessage, status]);

  const onRecognize = async () => {
    if (!activeImageFile || status === 'recognizing') return;
    setStatus('recognizing');
    setErrorMessage('');
    if (voiceGuidance) {
      speak('Recognizing formula, please wait.');
    }

    try {
      const inferResponse = await inferLatexFromImage(
        activeImageFile,
        UI_CONSTANTS.RECOGNIZE_IMAGE_HEIGHT,
        UI_CONSTANTS.RECOGNIZE_IMAGE_WIDTH,
      );
      const speechResponse = await convertLatexToSpeechText(inferResponse.latex);
      const currentResult = {
        latex: inferResponse.latex,
        speech: speechResponse.sentence,
      };
      setResult(currentResult);
      setStatus('success');
      setHistory((previous) =>
        [
          {
            id: crypto.randomUUID(),
            latex: currentResult.latex,
            speech: currentResult.speech,
            timestamp: Date.now(),
          },
          ...previous,
        ].slice(0, UI_CONSTANTS.MAX_HISTORY_ITEMS),
      );
      if (voiceGuidance) {
        speak('Recognition complete. The result is ready.');
      }
    } catch (error) {
      const message =
        error instanceof ApiClientError
          ? error.message
          : 'Unable to recognize formula. Please try again.';
      setStatus('error');
      setErrorMessage(message);
      if (voiceGuidance) {
        speak(`Error. ${message}`);
      }
    }
  };

  const isRecognizeDisabled = status === 'recognizing' || !activeImageFile;

  return (
    <div className="min-h-screen bg-gray-50 px-4 py-10 font-sans md:px-8">
      <div className="mx-auto flex w-full max-w-5xl flex-col items-center">
        <header className="mb-10 flex w-full flex-col items-center justify-between gap-4 md:flex-row">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-600 shadow-lg shadow-blue-200">
              <Sparkles className="text-white" size={24} />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Math Formula Recognizer</h1>
              <p className="text-sm text-gray-500">
                Convert handwriting & images to LaTeX, then speak naturally
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsHistoryOpen(true)}
              className="flex items-center gap-2 rounded-full border border-gray-200 bg-white px-4 py-2 font-medium text-gray-700 shadow-sm transition-all hover:bg-gray-50 hover:text-blue-600 focus:outline-none focus:ring-4 focus:ring-blue-100"
              aria-label="View Recognition History"
            >
              <History size={18} />
              <span className="hidden sm:inline">History</span>
            </button>
            <button
              onClick={() => setVoiceGuidance((previous) => !previous)}
              className={`flex items-center gap-2 rounded-full px-4 py-2 font-medium shadow-sm transition-all focus:outline-none focus:ring-4 focus:ring-blue-100 ${
                voiceGuidance
                  ? 'bg-blue-100 text-blue-700 hover:bg-blue-200'
                  : 'border border-gray-200 bg-white text-gray-600 hover:bg-gray-50'
              }`}
              aria-pressed={voiceGuidance}
              aria-label={voiceGuidance ? 'Disable voice guidance' : 'Enable voice guidance'}
            >
              {voiceGuidance ? <Volume2 size={18} /> : <VolumeX size={18} />}
              <span className="hidden sm:inline">Voice Guidance</span>
              <span className="sm:hidden">Voice</span>
            </button>
          </div>
        </header>

        <main className="flex w-full flex-col items-center">
          <div
            className="mb-8 flex w-full max-w-md rounded-xl border border-gray-100 bg-white p-1 shadow-sm"
            role="tablist"
          >
            <button
              role="tab"
              aria-selected={mode === 'draw'}
              onClick={() => {
                setMode('draw');
                setActiveImageFile(null);
                setStatus('idle');
              }}
              className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-3 text-sm font-medium transition-all md:text-base ${
                mode === 'draw'
                  ? 'bg-blue-50 text-blue-700 shadow-sm'
                  : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'
              }`}
            >
              <PencilLine size={18} className="hidden sm:inline" />
              Draw
            </button>
            <button
              role="tab"
              aria-selected={mode === 'upload'}
              onClick={() => {
                setMode('upload');
                setActiveImageFile(null);
                setStatus('idle');
              }}
              className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-3 text-sm font-medium transition-all md:text-base ${
                mode === 'upload'
                  ? 'bg-blue-50 text-blue-700 shadow-sm'
                  : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'
              }`}
            >
              <ImageIcon size={18} className="hidden sm:inline" />
              Upload
            </button>
            <button
              role="tab"
              aria-selected={mode === 'camera'}
              onClick={() => {
                setMode('camera');
                setActiveImageFile(null);
                setStatus('idle');
              }}
              className={`flex flex-1 items-center justify-center gap-2 rounded-lg px-4 py-3 text-sm font-medium transition-all md:text-base ${
                mode === 'camera'
                  ? 'bg-blue-50 text-blue-700 shadow-sm'
                  : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'
              }`}
            >
              <CameraIcon size={18} className="hidden sm:inline" />
              Camera
            </button>
          </div>

          <div className="flex min-h-[300px] w-full flex-col rounded-2xl border border-gray-100 bg-white p-4 shadow-lg md:p-6">
            {mode === 'draw' && (
              <DrawCanvas
                onImageReady={setActiveImageFile}
                voiceGuidance={voiceGuidance}
                speak={speak}
              />
            )}
            {mode === 'upload' && (
              <ImageUploader
                onImageSelected={setActiveImageFile}
                voiceGuidance={voiceGuidance}
                speak={speak}
              />
            )}
            {mode === 'camera' && (
              <CameraCapture
                onPhotoCapture={setActiveImageFile}
                voiceGuidance={voiceGuidance}
                speak={speak}
              />
            )}

            <div className="mt-6 flex justify-center">
              <button
                onClick={() => void onRecognize()}
                disabled={isRecognizeDisabled}
                className={`flex w-full max-w-sm items-center justify-center gap-2 rounded-xl px-8 py-4 text-lg font-bold text-white shadow-lg transition-all focus:outline-none focus:ring-4 focus:ring-blue-200 ${
                  isRecognizeDisabled
                    ? 'cursor-not-allowed bg-gray-300 text-gray-500 shadow-none'
                    : 'bg-blue-600 hover:-translate-y-0.5 hover:bg-blue-700'
                }`}
              >
                {status === 'recognizing' ? (
                  <>
                    <Loader2 className="animate-spin" size={24} />
                    Recognizing...
                  </>
                ) : (
                  'Recognize Formula'
                )}
              </button>
            </div>
          </div>

          {result && (
            <ResultArea
              latex={result.latex}
              speechText={result.speech}
              onSpeak={speak}
              status={statusText}
            />
          )}
        </main>

        <HistoryPanel
          isOpen={isHistoryOpen}
          onClose={() => setIsHistoryOpen(false)}
          history={history}
          onSelect={(item) => {
            setResult({ latex: item.latex, speech: item.speech });
            setStatus('success');
            setIsHistoryOpen(false);
          }}
          voiceGuidance={voiceGuidance}
          speak={speak}
        />
      </div>
    </div>
  );
}
