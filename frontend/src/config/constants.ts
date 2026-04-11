export const UI_CONSTANTS = {
  DRAW_CANVAS_HEIGHT_DESKTOP: 384,
  DRAW_CANVAS_HEIGHT_MOBILE: 256,
  CAMERA_CAPTURE_QUALITY: 0.92,
  MAX_HISTORY_ITEMS: 20,
  RECOGNIZE_IMAGE_HEIGHT: 128,
  RECOGNIZE_IMAGE_WIDTH: 512,
  STATUS_RESET_DELAY_MS: 2000,
  SPEECH_RATE_DEFAULT: 0.95,
  SPEECH_PITCH_DEFAULT: 1.0,
  SPEECH_VOLUME_DEFAULT: 1.0,
  SPEECH_PREVIEW_TEXT_MAX_LENGTH: 45,
} as const;

export const TTS_PRESET_LATEX = [
  {
    id: 'quadratic',
    label: '📐 Quadratic Formula',
    latex: '\\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}',
  },
  {
    id: 'calculus',
    label: '🧮 Calculus',
    latex: '\\int_a^b x^2 dx = \\left[\\frac{x^3}{3}\\right]_a^b',
  },
  {
    id: 'equation',
    label: '✅ Equation: x = 5',
    latex: 'x = 5',
  },
] as const;
