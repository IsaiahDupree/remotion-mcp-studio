import { ThemeConfig, ColorTheme } from './types';

export const THEMES: Record<ColorTheme, ThemeConfig> = {
  dark: {
    background: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #0a0a0a 100%)',
    primary: '#ffffff',
    secondary: '#a1a1aa',
    accent: '#3b82f6',
    fontFamily: 'Inter, system-ui, sans-serif',
  },
  tiktok: {
    background: 'linear-gradient(135deg, #010101 0%, #1a0005 100%)',
    primary: '#ffffff',
    secondary: '#e5e5e5',
    accent: '#fe2c55',
    fontFamily: 'Inter, system-ui, sans-serif',
  },
  everreach: {
    background: 'linear-gradient(135deg, #1a0533 0%, #2d1b69 50%, #1a0533 100%)',
    primary: '#ffffff',
    secondary: '#c4b5fd',
    accent: '#7c3aed',
    fontFamily: 'Poppins, Inter, system-ui, sans-serif',
  },
  neon: {
    background: 'linear-gradient(135deg, #0a0a0a 0%, #0d0d1a 100%)',
    primary: '#00ff88',
    secondary: '#00ccff',
    accent: '#ff00ff',
    fontFamily: 'Inter, system-ui, sans-serif',
  },
  minimal: {
    background: '#f5f5f5',
    primary: '#111111',
    secondary: '#555555',
    accent: '#000000',
    fontFamily: 'Inter, system-ui, sans-serif',
  },
};

export function getTheme(colorTheme?: string): ThemeConfig {
  return THEMES[(colorTheme as ColorTheme) ?? 'dark'] ?? THEMES.dark;
}
