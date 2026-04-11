import { useCallback, useEffect, useRef, useState } from 'react';
import { Camera, Check, RefreshCw, VideoOff } from 'lucide-react';
import { UI_CONSTANTS } from '../config/constants';

interface CameraCaptureProps {
  onPhotoCapture: (file: File | null) => void;
  voiceGuidance: boolean;
  speak: (text: string) => void;
}

export function CameraCapture({ onPhotoCapture, voiceGuidance, speak }: CameraCaptureProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [photo, setPhoto] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const stopCamera = useCallback(() => {
    if (!stream) return;
    stream.getTracks().forEach((track) => track.stop());
    setStream(null);
  }, [stream]);

  const startCamera = useCallback(async () => {
    setError(null);
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
      });
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
      if (voiceGuidance) {
        speak('Camera started. Align your formula and click capture.');
      }
    } catch {
      setError('Failed to access camera. Please check permissions.');
      if (voiceGuidance) {
        speak('Failed to access camera. Please check permissions.');
      }
    }
  }, [speak, voiceGuidance]);

  useEffect(() => {
    startCamera();
    return () => {
      stopCamera();
    };
  }, [startCamera, stopCamera]);

  const capturePhoto = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return;
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const dataUrl = canvas.toDataURL('image/jpeg');
    setPhoto(dataUrl);
    stopCamera();

    canvas.toBlob(
      (blob) => {
        if (!blob) return;
        onPhotoCapture(new File([blob], 'captured-formula.jpg', { type: 'image/jpeg' }));
      },
      'image/jpeg',
      UI_CONSTANTS.CAMERA_CAPTURE_QUALITY,
    );

    if (voiceGuidance) {
      speak('Photo captured. Ready to recognize or you can retake.');
    }
  };

  return (
    <div className="relative flex h-64 w-full flex-col items-center justify-center overflow-hidden rounded-xl bg-gray-900 md:h-96">
      {error ? (
        <div className="flex flex-col items-center p-6 text-center text-gray-300">
          <VideoOff size={48} className="mb-4 text-red-400" />
          <p>{error}</p>
          <button
            onClick={startCamera}
            className="mt-4 rounded-lg bg-gray-800 px-4 py-2 text-white transition-colors hover:bg-gray-700"
          >
            Try Again
          </button>
        </div>
      ) : photo ? (
        <div className="relative flex h-full w-full items-center justify-center bg-black">
          <img src={photo} alt="Captured formula" className="max-h-full max-w-full object-contain" />
          <div className="absolute bottom-4 left-0 right-0 flex justify-center gap-4">
            <button
              onClick={() => {
                setPhoto(null);
                onPhotoCapture(null);
                startCamera();
              }}
              className="flex items-center gap-2 rounded-full bg-gray-800 px-4 py-2 text-white shadow-lg transition-colors hover:bg-gray-700"
            >
              <RefreshCw size={18} />
              Retake
            </button>
            <div className="flex cursor-default items-center gap-2 rounded-full bg-green-600 px-4 py-2 text-white shadow-lg">
              <Check size={18} />
              Captured
            </div>
          </div>
        </div>
      ) : (
        <div className="relative h-full w-full">
          <video ref={videoRef} autoPlay playsInline muted className="h-full w-full object-cover" />
          <div className="absolute bottom-4 left-0 right-0 flex justify-center">
            <button
              onClick={capturePhoto}
              className="flex h-16 w-16 items-center justify-center rounded-full bg-white text-gray-900 shadow-lg ring-4 ring-gray-900/20 transition-colors hover:bg-gray-200"
              aria-label="Capture photo"
            >
              <Camera size={28} />
            </button>
          </div>
        </div>
      )}
      <canvas ref={canvasRef} className="hidden" />
    </div>
  );
}
