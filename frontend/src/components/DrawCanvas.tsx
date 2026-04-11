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
  const [isDrawing, setIsDrawing] = useState(false);
  const [isEmpty, setIsEmpty] = useState(true);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.lineWidth = 4;
    ctx.strokeStyle = '#000000';
  }, []);

  useEffect(() => {
    const resizeCanvas = () => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const parent = canvas.parentElement;
      if (!parent) return;
      if (canvas.width === 0) {
        canvas.width = parent.clientWidth;
      }
      if (canvas.height === 0) {
        const isMobile = window.innerWidth <= 768;
        canvas.height = isMobile
          ? UI_CONSTANTS.DRAW_CANVAS_HEIGHT_MOBILE
          : UI_CONSTANTS.DRAW_CANVAS_HEIGHT_DESKTOP;
      }
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    return () => window.removeEventListener('resize', resizeCanvas);
  }, []);

  const toFile = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    canvas.toBlob((blob) => {
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
    const ctx = canvasRef.current?.getContext('2d');
    if (!ctx) return;
    ctx.beginPath();
    ctx.moveTo(coords.x, coords.y);
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
    ctx.lineTo(coords.x, coords.y);
    ctx.stroke();
    toFile();
  };

  const stopDrawing = () => {
    const ctx = canvasRef.current?.getContext('2d');
    if (ctx) {
      ctx.closePath();
    }
    setIsDrawing(false);
    if (!isEmpty) {
      toFile();
    }
  };

  const clearCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
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
