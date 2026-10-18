export interface WordTiming {
  word: string;
  start: number; // seconds
  end: number;   // seconds
}

export type ColorTheme = 'dark' | 'tiktok' | 'everreach' | 'neon' | 'minimal';

export interface ContentBrief {
  id: string;
  format: string;
  hook_text: string;
  hook_style?: 'stamp' | 'stat' | 'question' | 'glitch' | 'bold_center';
  hook_emoji?: string;
  hook_subtext?: string;
  body_points?: string[];
  cta_text?: string;
  color_theme?: ColorTheme;
  duration_sec?: number;
  audio?: {
    voiceover?: string;       // staticFile path like "voiceovers/vo_xxx.mp3" or https:// URL
    music_path?: string;      // staticFile path or https:// URL
    volume_music?: number;    // default 0.25
    volume_voice?: number;    // default 1.0
    word_timings?: WordTiming[];
  };
  // Optional per-section overrides
  sections?: Array<{
    type: 'hook' | 'points' | 'phone_frame' | 'outro' | 'stat';
    duration_sec?: number;
    content?: Record<string, unknown>;
  }>;
}

export interface ThemeConfig {
  background: string;
  primary: string;
  secondary: string;
  accent: string;
  fontFamily: string;
}
