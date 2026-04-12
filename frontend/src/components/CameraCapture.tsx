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
  const streamRef = useRef<MediaStream | null>(null);
  const [photo, setPhoto] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const stopCamera = useCallback(() => {
    if (!streamRef.current) return;
    streamRef.current.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  }, []);

  const attachStreamToVideo = async (mediaStream: MediaStream): Promise<void> => {
    const video = videoRef.current;
    if (!video) return;
    video.srcObject = mediaStream;
    await new Promise<void>((resolve) => {
      const onReady = () => {
        video.removeEventListener('loadedmetadata', onReady);
        resolve();
      };
      video.addEventListener('loadedmetadata', onReady);
      window.setTimeout(() => {
        video.removeEventListener('loadedmetadata', onReady);
        resolve();
      }, 1200);
    });
    await video.play().catch(() => {
      // Some browsers block autoplay; stream can still be displayed once user interacts.
    });
  };

  const requestStream = async (): Promise<MediaStream> => {
    const mediaDevices = navigator.mediaDevices;
    if (!mediaDevices?.getUserMedia) {
      throw new Error('Camera API is not supported in this browser.');
    }
    const constraintsCandidates: MediaStreamConstraints[] = [
      { video: { facingMode: 'environment' }, audio: false },
      { video: true, audio: false },
    ];
    let lastError: unknown = null;
    for (const constraints of constraintsCandidates) {
      try {
        return await mediaDevices.getUserMedia(constraints);
      } catch (errorObject) {
        lastError = errorObject;
      }
    }
    throw lastError instanceof Error
      ? lastError
      : new Error('No camera stream available from current browser/device.');
  };

  const startCamera = useCallback(async () => {
    setError(null);
    stopCamera();
    try {
      const mediaStream = await requestStream();
      streamRef.current = mediaStream;
      await attachStreamToVideo(mediaStream);
      if (voiceGuidance) {
        speak('Camera started. Align your formula and click capture.');
      }
    } catch (errorObject) {
      const message = errorObject instanceof Error ? errorObject.message : 'Unknown camera error.';
      const normalizedMessage = `Failed to access camera. ${message}`;
      console.error('Camera start failed:', errorObject);
      setPhoto(null);
      setError(message);
      if (voiceGuidance) {
        speak(normalizedMessage);
      }
    }
  }, [speak, stopCamera, voiceGuidance]);

  useEffect(() => {
    void startCamera();
    return () => stopCamera();
  }, [startCamera, stopCamera]);

  const capturePhoto = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.videoWidth === 0 || video.videoHeight === 0) {
      setError('Camera is not ready yet. Please wait a moment and try again.');
      return;
    }
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
