import type {
  ApiErrorPayload,
  InferenceResponse,
  LatexToSpeechResponse,
} from '../types/api';

const ENV = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000',
  apiPrefix: import.meta.env.VITE_API_PREFIX ?? '/api/v1',
  ttsDefaultLanguage: import.meta.env.VITE_TTS_DEFAULT_LANGUAGE ?? 'en',
} as const;

const API_PATHS = {
  inferFromImage: '/latex/from-image',
  latexToSpeechText: '/speech-text/from-latex',
} as const;

const DEFAULT_ERROR_MESSAGE = 'Request failed. Please try again.';

export class ApiClientError extends Error {
  readonly code?: string;

  constructor(message: string, code?: string) {
    super(message);
    this.name = 'ApiClientError';
    this.code = code;
  }
}

function normalizePath(base: string, suffix: string): string {
  const normalizedBase = base.endsWith('/') ? base.slice(0, -1) : base;
  const normalizedSuffix = suffix.startsWith('/') ? suffix : `/${suffix}`;
  return `${normalizedBase}${normalizedSuffix}`;
}

function buildApiUrl(path: string): string {
  const withPrefix = normalizePath(ENV.apiPrefix, path);
  return normalizePath(ENV.apiBaseUrl, withPrefix);
}

async function parseApiError(response: Response): Promise<ApiClientError> {
  let payload: ApiErrorPayload | null = null;
  try {
    payload = (await response.json()) as ApiErrorPayload;
  } catch {
    return new ApiClientError(DEFAULT_ERROR_MESSAGE);
  }

  const detail = payload.detail;
  if (detail?.message) {
    return new ApiClientError(detail.message, detail.code);
  }

  const error = payload.error;
  if (error?.message) {
    return new ApiClientError(error.message, error.code);
  }

  return new ApiClientError(DEFAULT_ERROR_MESSAGE);
}

export async function inferLatexFromImage(
  file: File,
  imageHeight: number,
  imageWidth: number,
): Promise<InferenceResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const url = new URL(buildApiUrl(API_PATHS.inferFromImage));
  url.searchParams.set('image_height', String(imageHeight));
  url.searchParams.set('image_width', String(imageWidth));

  const response = await fetch(url.toString(), {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw await parseApiError(response);
  }
  return (await response.json()) as InferenceResponse;
}

export async function convertLatexToSpeechText(
  latex: string,
  language: string = ENV.ttsDefaultLanguage,
): Promise<LatexToSpeechResponse> {
  const response = await fetch(buildApiUrl(API_PATHS.latexToSpeechText), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ latex, language }),
  });

  if (!response.ok) {
    throw await parseApiError(response);
  }
  return (await response.json()) as LatexToSpeechResponse;
}

export const appEnv = ENV;
