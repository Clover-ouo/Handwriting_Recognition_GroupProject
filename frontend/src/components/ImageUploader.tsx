import { useRef, useState } from 'react';
import { UploadCloud, X } from 'lucide-react';

interface ImageUploaderProps {
  onImageSelected: (file: File | null) => void;
  voiceGuidance: boolean;
  speak: (text: string) => void;
}

export function ImageUploader({ onImageSelected, voiceGuidance, speak }: ImageUploaderProps) {
  const [dragActive, setDragActive] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = (file: File) => {
    if (!file.type.startsWith('image/')) {
      if (voiceGuidance) {
        speak('Error: Please upload an image file');
      }
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      setPreviewUrl(reader.result as string);
      onImageSelected(file);
      if (voiceGuidance) {
        speak('Image uploaded successfully. Ready to recognize.');
      }
    };
    reader.readAsDataURL(file);
  };

  return (
    <div
      className={`relative h-64 w-full cursor-pointer overflow-hidden rounded-xl border-2 border-dashed transition-colors md:h-96 ${
        dragActive
          ? 'border-blue-500 bg-blue-50'
          : 'border-gray-300 bg-gray-50 hover:bg-gray-100'
      }`}
      onDragEnter={(event) => {
        event.preventDefault();
        setDragActive(true);
      }}
      onDragLeave={(event) => {
        event.preventDefault();
        setDragActive(false);
      }}
      onDragOver={(event) => {
        event.preventDefault();
        setDragActive(true);
      }}
      onDrop={(event) => {
        event.preventDefault();
        setDragActive(false);
        if (event.dataTransfer.files?.[0]) {
          handleFile(event.dataTransfer.files[0]);
        }
      }}
      onClick={() => fileInputRef.current?.click()}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          fileInputRef.current?.click();
        }
      }}
      tabIndex={0}
      role="button"
      aria-label="Upload formula image"
    >
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={(event) => {
          if (event.target.files?.[0]) {
            handleFile(event.target.files[0]);
          }
        }}
        className="hidden"
      />

      {previewUrl ? (
        <div className="group relative flex h-full w-full items-center justify-center bg-gray-900/5 p-4">
          <img
            src={previewUrl}
            alt="Preview of uploaded formula"
            className="max-h-full max-w-full rounded-lg object-contain drop-shadow-md"
          />
          <button
            onClick={(event) => {
              event.stopPropagation();
              setPreviewUrl(null);
              onImageSelected(null);
              if (fileInputRef.current) {
                fileInputRef.current.value = '';
              }
            }}
            className="absolute right-4 top-4 rounded-full bg-white p-2 text-gray-700 opacity-0 shadow-lg transition-opacity group-hover:opacity-100 focus:opacity-100 focus:outline-none focus:ring-2 focus:ring-red-500"
            aria-label="Remove image"
          >
            <X size={20} />
          </button>
        </div>
      ) : (
        <div className="flex h-full flex-col items-center justify-center p-6 text-center text-gray-500">
          <div className="mb-4 rounded-full bg-white p-4 shadow-sm">
            <UploadCloud size={40} className="text-blue-500" />
          </div>
          <p className="mb-1 text-lg font-medium text-gray-700">Click to upload or drag & drop</p>
          <p className="text-sm">PNG, JPG, JPEG, WEBP</p>
        </div>
      )}
    </div>
  );
}
