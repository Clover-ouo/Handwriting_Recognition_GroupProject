import { useEffect, useRef, useState } from 'react';
import type { MouseEvent, TouchEvent } from 'react';
import { Pen, Trash2 } from 'lucide-react';
import { UI_CONSTANTS } from '../config/constants';

interface DrawCanvasProps {
  onImageReady: (file: File | null) => void;
  voiceGuidance: boolean;
  speak: (text: string) => void;
}

export function DrawCanvas({ onImageReady, voiceGuidance, speak }: DrawCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const lastPointRef = useRef<{ x: number; y: number } | null>(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [isEmpty, setIsEmpty] = useState(true);

  const setupContext = () => {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    const ctx = canvas.getContext('2d');
    if (!ctx) return null;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.lineWidth = UI_CONSTANTS.DRAW_STROKE_WIDTH;
    ctx.strokeStyle = UI_CONSTANTS.DRAW_STROKE_COLOR;
    return ctx;
  };

  useEffect(() => {
    setupContext();
  }, []);

  useEffect(() => {
    const resizeCanvas = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const rect = canvas.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      const nextWidth = Math.max(1, Math.floor(rect.width * dpr));
      const nextHeight = Math.max(1, Math.floor(rect.height * dpr));
      if (canvas.width === nextWidth && canvas.height === nextHeight) return;

      const previous = document.createElement('canvas');
      previous.width = canvas.width;
      previous.height = canvas.height;
      const previousCtx = previous.getContext('2d');
      if (previousCtx) {
        previousCtx.drawImage(canvas, 0, 0);
      }

      canvas.width = nextWidth;
      canvas.height = nextHeight;

      const ctx = setupContext();
      if (!ctx) return;
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.scale(dpr, dpr);
      ctx.fillStyle = UI_CONSTANTS.DRAW_BACKGROUND_FILL;
      ctx.fillRect(0, 0, rect.width, rect.height);
      if (previous.width > 0 && previous.height > 0) {
        ctx.drawImage(previous, 0, 0, rect.width, rect.height);
      }
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    return () => window.removeEventListener('resize', resizeCanvas);
  }, []);

  const toFile = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const exportCanvas = document.createElement('canvas');
    exportCanvas.width = canvas.width;
    exportCanvas.height = canvas.height;
    const exportCtx = exportCanvas.getContext('2d');
    if (!exportCtx) return;
    exportCtx.fillStyle = UI_CONSTANTS.DRAW_BACKGROUND_FILL;
    exportCtx.fillRect(0, 0, exportCanvas.width, exportCanvas.height);
    exportCtx.drawImage(canvas, 0, 0);
    exportCanvas.toBlob((blob) => {
      if (!blob) return;
      onImageReady(new File([blob], 'drawn-formula.png', { type: 'image/png' }));
    }, 'image/png');
  };

  const getCoordinates = (
    event: MouseEvent<HTMLCanvasElement> | TouchEvent<HTMLCanvasElement>,
  ): { x: number; y: number } | null => {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    const rect = canvas.getBoundingClientRect();
    if ('touches' in event) {
      return {
        x: event.touches[0].clientX - rect.left,
        y: event.touches[0].clientY - rect.top,
      };
    }
    return {
      x: event.clientX - rect.left,
      y: event.clientY - rect.top,
    };
  };

  const startDrawing = (
    event: MouseEvent<HTMLCanvasElement> | TouchEvent<HTMLCanvasElement>,
  ) => {
    event.preventDefault();
    const coords = getCoordinates(event);
    if (!coords) return;
    lastPointRef.current = coords;
    setIsDrawing(true);
    if (isEmpty) {
      setIsEmpty(false);
    }
  };

  const draw = (
    event: MouseEvent<HTMLCanvasElement> | TouchEvent<HTMLCanvasElement>,
  ) => {
    event.preventDefault();
    if (!isDrawing) return;
    const coords = getCoordinates(event);
    if (!coords) return;
    const ctx = canvasRef.current?.getContext('2d');
    if (!ctx) return;
    const from = lastPointRef.current ?? coords;
    ctx.beginPath();
    ctx.moveTo(from.x, from.y);
    ctx.lineTo(coords.x, coords.y);
    ctx.stroke();
    lastPointRef.current = coords;
  };

  const stopDrawing = () => {
    const ctx = canvasRef.current?.getContext('2d');
    if (ctx) {
      ctx.closePath();
    }
    setIsDrawing(false);
    lastPointRef.current = null;
    if (!isEmpty) {
      toFile();
    }
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const dpr = window.devicePixelRatio || 1;
    const displayWidth = canvas.width / dpr;
    const displayHeight = canvas.height / dpr;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.fillStyle = UI_CONSTANTS.DRAW_BACKGROUND_FILL;
    ctx.fillRect(0, 0, displayWidth, displayHeight);
    setIsEmpty(true);
    onImageReady(null);
    if (voiceGuidance) {
      speak('Canvas cleared');
    }
  };

  return (
    <div className="flex h-full w-full flex-col gap-4">
      <div
        className="relative h-64 w-full touch-none overflow-hidden rounded-xl border-2 border-dashed border-gray-300 bg-white shadow-inner md:h-96"
        onMouseEnter={() =>
          voiceGuidance && speak('Drawing area. Use your mouse or finger to write a formula.')
        }
      >
        <canvas
          ref={canvasRef}
          className="absolute left-0 top-0 h-full w-full cursor-crosshair"
          onMouseDown={startDrawing}
          onMouseMove={draw}
          onMouseUp={stopDrawing}
          onMouseLeave={stopDrawing}
          onTouchStart={startDrawing}
          onTouchMove={draw}
          onTouchEnd={stopDrawing}
          aria-label="Whiteboard for drawing math formulas"
          role="img"
        />

        {isEmpty && (
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center text-gray-400">
            <span className="flex items-center gap-2">
              <Pen size={20} /> Write your formula here
            </span>
          </div>
        )}
      </div>

      <div className="flex justify-end">
        <button
          onClick={clearCanvas}
          disabled={isEmpty}
          onFocus={() => voiceGuidance && speak('Clear drawing button')}
          className="flex items-center gap-2 rounded-lg bg-red-50 px-4 py-2 text-sm font-medium text-red-600 transition-colors hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-400 disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="Clear drawing"
        >
          <Trash2 size={16} />
          Clear
        </button>
      </div>
    </div>
  );
}
