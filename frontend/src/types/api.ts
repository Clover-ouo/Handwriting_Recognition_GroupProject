export interface ImageSize {
  height: number;
  width: number;
}

export interface ModelInfo {
  checkpoint: string;
  vocab: string;
  device: string;
}

export interface InferenceResponse {
  request_id: string;
  latex: string;
  image_size: ImageSize;
  model: ModelInfo;
  duration_ms: number;
}

export interface LatexToSpeechResponse {
  request_id: string;
  sentence: string;
  llm: {
    provider: string;
    model: string;
  };
  duration_ms: number;
}

export interface ApiErrorPayload {
  error?: {
    code?: string;
    message?: string;
    details?: string;
    request_id?: string;
  };
  detail?: {
    code?: string;
    message?: string;
  };
}
