import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {BRAND, type Scene} from './TheNewMachineEpisode';

// ──────────────────────────────────────────────────────────────────────────────
// The New Machine — vertical Shorts composition (1080×1920, 30fps).
//
// One Short = one clip + one burned-in hook line + an end CTA.
// Six visual styles, accent-keyed: cold_open | diagram | quote | warning |
// opportunity | future_scene.
//
// Driven by `pipeline/build_shorts.py`, which carves a 25–60s window out of
// the long-form scenes (typically the cold open, a quote moment, or a warning
// beat) and emits one props file per Short into `episodes/<slug>/artifacts/shorts/`.
// ──────────────────────────────────────────────────────────────────────────────

export type ShortType =
  | 'cold_open'
  | 'diagram'
  | 'quote'
  | 'warning'
  | 'opportunity'
  | 'future_scene';

export type ShortProps = {
  shortType: ShortType;
  episodeId?: string;
  title: string;
  hook: string;
  body?: string;
  scenes: Scene[];
  voiceoverUrl?: string;
  ctaText?: string;
};

export const theNewMachineShortDefaultProps: ShortProps = {
  shortType: 'cold_open',
  episodeId: 'EP001',
  title: 'AI Agents Are About to Replace Dashboards',
  hook: 'Dashboards are proof your software still needs a babysitter.',
  body: '',
  scenes: [{startMs: 0, endMs: 30000, imageUrl: '', motion: 'push'}],
  voiceoverUrl: '',
  ctaText: 'Full breakdown on The New Machine.',
};

const accentForType: Record<ShortType, string> = {
  cold_open:    BRAND.cyan,
  diagram:      BRAND.cyan,
  quote:        BRAND.text,
  warning:      BRAND.danger,
  opportunity:  BRAND.power,
  future_scene: BRAND.amber,
};

const labelForType: Record<ShortType, string> = {
  cold_open:    'COLD OPEN',
  diagram:      'NEW MACHINE',
  quote:        'QUOTE',
  warning:      'WARNING',
  opportunity:  'OPPORTUNITY',
  future_scene: 'FUTURE',
};

const resolveUrl = (u: string | undefined): string => {
  if (!u) return '';
  if (/^(https?:|file:|data:)/.test(u)) return u;
  return staticFile(u);
};

// ── Background (image OR brand-tinted gradient) ─────────────────────────────
const ShortBackground: React.FC<{scene: Scene; accent: string}> = ({scene, accent}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const t = frame / Math.max(durationInFrames, 1);
  const scale = scene.motion === 'pull'
    ? interpolate(t, [0, 1], [1.15, 1.0])
    : interpolate(t, [0, 1], [1.0, 1.15]);

  if (scene.imageUrl) {
    return (
      <AbsoluteFill style={{background: BRAND.bg}}>
        <Img
          src={resolveUrl(scene.imageUrl)}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${scale})`,
            filter: 'saturate(0.92) contrast(1.05)',
          }}
        />
        <AbsoluteFill style={{
          background: 'linear-gradient(180deg, rgba(7,9,12,0.5) 0%, rgba(7,9,12,0) 30%, rgba(7,9,12,0) 65%, rgba(7,9,12,0.92) 100%)',
        }} />
      </AbsoluteFill>
    );
  }

  // Fallback: vertical brand panel with hairline grid + accent glow.
  const r = parseInt(accent.slice(1, 3), 16);
  const g = parseInt(accent.slice(3, 5), 16);
  const b = parseInt(accent.slice(5, 7), 16);
  const tintRgba = `rgba(${r}, ${g}, ${b}, 0.10)`;
  return (
    <AbsoluteFill
      style={{
        background:
          `radial-gradient(circle at 50% 35%, ${tintRgba} 0%, transparent 55%),` +
          `radial-gradient(circle at 50% 60%, ${BRAND.bgPanel} 0%, ${BRAND.bg} 75%),` +
          `linear-gradient(${BRAND.bgPanel} 1px, transparent 1px),` +
          `linear-gradient(90deg, ${BRAND.bgPanel} 1px, transparent 1px)`,
        backgroundSize: '100% 100%, 100% 100%, 96px 96px, 96px 96px',
      }}
    />
  );
};

// ── Type pill (top, accent-keyed) ───────────────────────────────────────────
const TypePill: React.FC<{shortType: ShortType; accent: string; episodeId?: string}> = ({
  shortType, accent, episodeId,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = spring({frame, fps, config: {damping: 22}});
  return (
    <div style={{
      position: 'absolute',
      top: 96, left: 60, right: 60,
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      opacity: t,
    }}>
      <div style={{
        fontFamily: BRAND.fontMono,
        fontSize: 22,
        letterSpacing: 4,
        color: accent,
        border: `1px solid ${accent}`,
        padding: '8px 14px',
        borderRadius: 2,
        boxShadow: `0 0 20px ${accent}55`,
      }}>
        {labelForType[shortType]}
      </div>
      {episodeId && (
        <div style={{
          fontFamily: BRAND.fontMono,
          fontSize: 22,
          letterSpacing: 4,
          color: BRAND.muted,
        }}>
          {episodeId}
        </div>
      )}
    </div>
  );
};

// ── Hook (burned-in headline, mid-frame) ────────────────────────────────────
const HookText: React.FC<{text: string; accent: string}> = ({text, accent}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const opacity = interpolate(frame, [0, fps * 0.4], [0, 1], {extrapolateRight: 'clamp'});
  const ty = interpolate(frame, [0, fps * 0.4], [16, 0], {extrapolateRight: 'clamp'});
  return (
    <div style={{
      position: 'absolute',
      top: 360,
      left: 60, right: 60,
      color: BRAND.text,
      fontFamily: BRAND.fontDisplay,
      fontWeight: 700,
      fontSize: 92,
      lineHeight: 1.05,
      letterSpacing: -0.5,
      textShadow: '0 8px 40px rgba(0,0,0,0.95)',
      borderLeft: `6px solid ${accent}`,
      paddingLeft: 28,
      opacity,
      transform: `translateY(${ty}px)`,
    }}>
      {text}
    </div>
  );
};

// ── Body line (smaller, optional, supporting) ───────────────────────────────
const BodyLine: React.FC<{text?: string}> = ({text}) => {
  if (!text) return null;
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const opacity = interpolate(frame, [fps * 0.4, fps * 0.9], [0, 1], {extrapolateRight: 'clamp'});
  return (
    <div style={{
      position: 'absolute',
      top: 920,
      left: 60, right: 60,
      color: BRAND.text,
      fontFamily: BRAND.fontBody,
      fontSize: 44,
      fontWeight: 500,
      lineHeight: 1.35,
      letterSpacing: 0.3,
      opacity,
      textShadow: '0 4px 20px rgba(0,0,0,0.9)',
    }}>
      {text}
    </div>
  );
};

// ── CTA + wordmark + dot grid (last 4s) ─────────────────────────────────────
const Outro: React.FC<{ctaText: string; accent: string}> = ({ctaText, accent}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const showFrom = durationInFrames - fps * 4;
  if (frame < showFrom) return null;
  const t = interpolate(frame, [showFrom, showFrom + fps * 0.4], [0, 1], {extrapolateRight: 'clamp'});
  return (
    <div style={{
      position: 'absolute',
      bottom: 380,
      left: 60, right: 60,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      gap: 18,
      opacity: t,
      transform: `translateY(${(1 - t) * 12}px)`,
    }}>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 12px)',
        gap: 8,
      }}>
        {Array.from({length: 9}).map((_, i) => (
          <div key={i} style={{
            width: 12, height: 12, borderRadius: 2,
            background: i === 4 ? accent : BRAND.muted,
            boxShadow: i === 4 ? `0 0 12px ${accent}` : 'none',
          }} />
        ))}
      </div>
      <div style={{
        textAlign: 'center',
        color: BRAND.text,
        fontFamily: BRAND.fontDisplay,
        fontSize: 44,
        fontWeight: 600,
        lineHeight: 1.15,
      }}>
        {ctaText}
      </div>
      <div style={{
        fontFamily: BRAND.fontDisplay,
        fontWeight: 700,
        fontSize: 24,
        letterSpacing: 6,
        color: BRAND.muted,
      }}>
        THE NEW MACHINE
      </div>
    </div>
  );
};

// ── Progress bar (bottom edge) ──────────────────────────────────────────────
const ProgressBar: React.FC<{accent: string}> = ({accent}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const pct = (frame / Math.max(1, durationInFrames)) * 100;
  return (
    <div style={{
      position: 'absolute',
      left: 0, right: 0, bottom: 0,
      height: 4,
      background: 'rgba(255,255,255,0.08)',
    }}>
      <div style={{
        height: '100%',
        width: `${pct}%`,
        background: accent,
        boxShadow: `0 0 12px ${accent}`,
      }} />
    </div>
  );
};

// ── Main composition ─────────────────────────────────────────────────────────
export const TheNewMachineShort: React.FC<ShortProps> = ({
  shortType, episodeId, hook, body, scenes, voiceoverUrl, ctaText,
}) => {
  const {fps} = useVideoConfig();
  const accent = accentForType[shortType] ?? BRAND.cyan;
  const msToFrames = (ms: number) => Math.round((ms / 1000) * fps);

  return (
    <AbsoluteFill style={{background: BRAND.bg}}>
      {voiceoverUrl ? <Audio src={resolveUrl(voiceoverUrl)} /> : null}

      {scenes.map((scene, i) => {
        const fromFrame = msToFrames(scene.startMs);
        const durationFrames = Math.max(1, msToFrames(scene.endMs - scene.startMs));
        return (
          <Sequence key={i} from={fromFrame} durationInFrames={durationFrames}>
            <ShortBackground scene={scene} accent={accent} />
          </Sequence>
        );
      })}

      <TypePill shortType={shortType} accent={accent} episodeId={episodeId} />
      <HookText text={hook} accent={accent} />
      <BodyLine text={body} />
      <Outro ctaText={ctaText ?? 'Full episode on The New Machine.'} accent={accent} />
      <ProgressBar accent={accent} />
    </AbsoluteFill>
  );
};

export default TheNewMachineShort;
