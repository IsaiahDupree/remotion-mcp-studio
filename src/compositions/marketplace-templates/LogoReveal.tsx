import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Sequence,
  Img,
} from 'remotion';
import { z } from 'zod';
import { loadFont as loadInter } from '@remotion/google-fonts/Inter';
import { loadFont as loadPoppins } from '@remotion/google-fonts/Poppins';

// =============================================================================
// LogoReveal — Animated logo reveal / intro
// 1920x1080 @ 30fps, ~5 seconds (150 frames)
// =============================================================================

const inter = loadInter('normal', { weights: ['700', '800'] });
const poppins = loadPoppins('normal', { weights: ['400', '500'] });

// ── Zod Schema ───────────────────────────────────────────────────────────────

export const logoRevealSchema = z.object({
  logoUrl: z.string().url().describe('URL to the company logo image'),
  companyName: z.string().default('Acme Corp'),
  tagline: z.string().default('Building the future'),
  style: z
    .enum(['minimal', 'cinematic', 'glitch', 'neon'])
    .default('minimal')
    .describe('Visual style preset'),
  accentColor: z.string().default('#6366f1'),
  duration: z.number().min(2).max(15).default(5).describe('Duration in seconds'),
});

export type LogoRevealProps = z.infer<typeof logoRevealSchema>;

export const logoRevealDefaultProps: LogoRevealProps = {
  logoUrl: 'https://placehold.co/400x400/111/fff?text=LOGO',
  companyName: 'Acme Corp',
  tagline: 'Building the future',
  style: 'minimal',
  accentColor: '#6366f1',
  duration: 5,
};

// ── Helpers ──────────────────────────────────────────────────────────────────

function hexToRgb(hex: string) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return { r, g, b };
}

// ── Animated Gradient Background ─────────────────────────────────────────────

const GradientBg: React.FC<{
  accentColor: string;
  style: LogoRevealProps['style'];
}> = ({ accentColor, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const time = frame / fps;

  const { r, g, b } = hexToRgb(accentColor);

  if (style === 'neon') {
    const hueShift = interpolate(frame, [0, 150], [0, 60]);
    return (
      <AbsoluteFill
        style={{
          background: `
            radial-gradient(ellipse at 30% 50%, rgba(${r},${g},${b},0.4) 0%, transparent 60%),
            radial-gradient(ellipse at 70% 50%, rgba(${Math.min(r + 80, 255)},${Math.max(g - 40, 0)},${b},0.3) 0%, transparent 60%),
            linear-gradient(135deg, #0a0a0a 0%, #111 100%)
          `,
          filter: `hue-rotate(${hueShift}deg)`,
        }}
      />
    );
  }

  if (style === 'cinematic') {
    const vignette = interpolate(frame, [0, 60], [0.8, 0.5], {
      extrapolateRight: 'clamp',
    });
    return (
      <AbsoluteFill
        style={{
          background: `
            radial-gradient(ellipse at center, rgba(${r},${g},${b},0.15) 0%, transparent 70%),
            linear-gradient(180deg, #0a0a0a 0%, #1a1a2e 50%, #0a0a0a 100%)
          `,
        }}
      >
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: `radial-gradient(ellipse at center, transparent 40%, rgba(0,0,0,${vignette}) 100%)`,
          }}
        />
      </AbsoluteFill>
    );
  }

  if (style === 'glitch') {
    const glitchOffset = Math.sin(time * 40) > 0.9 ? Math.random() * 10 : 0;
    return (
      <AbsoluteFill
        style={{
          background: '#0a0a0a',
          transform: `translateX(${glitchOffset}px)`,
        }}
      >
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: `repeating-linear-gradient(
              0deg,
              transparent,
              transparent 2px,
              rgba(${r},${g},${b},0.03) 2px,
              rgba(${r},${g},${b},0.03) 4px
            )`,
          }}
        />
      </AbsoluteFill>
    );
  }

  // minimal
  const gradAngle = interpolate(frame, [0, 150], [135, 180]);
  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(${gradAngle}deg, #fafafa 0%, #f0f0f0 50%, #e8e8e8 100%)`,
      }}
    />
  );
};

// ── Particles (cinematic + neon) ─────────────────────────────────────────────

const Particles: React.FC<{ accentColor: string; count: number }> = ({
  accentColor,
  count,
}) => {
  const frame = useCurrentFrame();
  const particles = React.useMemo(() => {
    return Array.from({ length: count }, (_, i) => ({
      x: (i * 137.508) % 100,
      y: (i * 97.3) % 100,
      size: 2 + (i % 4),
      speed: 0.3 + (i % 5) * 0.15,
    }));
  }, [count]);

  return (
    <AbsoluteFill style={{ overflow: 'hidden' }}>
      {particles.map((p, i) => {
        const y = (p.y + frame * p.speed * 0.3) % 120 - 10;
        const opacity = interpolate(
          frame,
          [0, 30, 120, 150],
          [0, 0.6, 0.6, 0],
          { extrapolateRight: 'clamp' }
        );
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: `${p.x}%`,
              top: `${y}%`,
              width: p.size,
              height: p.size,
              borderRadius: '50%',
              background: accentColor,
              opacity: opacity * (0.3 + (i % 3) * 0.2),
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

// ── Main Component ───────────────────────────────────────────────────────────

export const LogoReveal: React.FC<LogoRevealProps> = ({
  logoUrl,
  companyName,
  tagline,
  style,
  accentColor,
  duration,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const isDark = style !== 'minimal';
  const textColor = isDark ? '#ffffff' : '#111111';
  const subtextColor = isDark ? 'rgba(255,255,255,0.7)' : 'rgba(0,0,0,0.6)';

  // Logo spring scale
  const logoScale = spring({
    frame,
    fps,
    config: { damping: 12, stiffness: 80, mass: 0.8 },
  });

  // Logo opacity
  const logoOpacity = interpolate(frame, [0, 10], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Company name — typewriter effect
  const nameStartFrame = Math.round(fps * 0.8);
  const charsVisible = Math.floor(
    interpolate(
      frame - nameStartFrame,
      [0, companyName.length * 2],
      [0, companyName.length],
      { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
    )
  );
  const displayedName = frame >= nameStartFrame ? companyName.slice(0, charsVisible) : '';
  const showCursor =
    frame >= nameStartFrame &&
    frame < nameStartFrame + companyName.length * 2 + 20 &&
    Math.floor(frame / 8) % 2 === 0;

  // Tagline fade in
  const taglineStartFrame = Math.round(fps * 2.2);
  const taglineOpacity = interpolate(
    frame,
    [taglineStartFrame, taglineStartFrame + 20],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );
  const taglineY = interpolate(
    frame,
    [taglineStartFrame, taglineStartFrame + 20],
    [15, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Glitch effect on logo
  const glitchActive = style === 'glitch' && Math.sin(frame * 0.7) > 0.92;
  const glitchTransform = glitchActive
    ? `scale(${logoScale}) translate(${Math.random() * 6 - 3}px, ${Math.random() * 6 - 3}px)`
    : `scale(${logoScale})`;

  // Final fade out
  const totalFrames = Math.round(duration * fps);
  const fadeOut = interpolate(
    frame,
    [totalFrames - 20, totalFrames],
    [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  return (
    <AbsoluteFill style={{ opacity: fadeOut }}>
      <GradientBg accentColor={accentColor} style={style} />

      {(style === 'cinematic' || style === 'neon') && (
        <Particles accentColor={accentColor} count={30} />
      )}

      {/* Center content */}
      <AbsoluteFill
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        {/* Logo */}
        <div
          style={{
            opacity: logoOpacity,
            transform: glitchTransform,
            marginBottom: 32,
          }}
        >
          <Img
            src={logoUrl}
            style={{
              width: 200,
              height: 200,
              objectFit: 'contain',
              filter:
                style === 'neon'
                  ? `drop-shadow(0 0 20px ${accentColor}) drop-shadow(0 0 40px ${accentColor})`
                  : style === 'cinematic'
                  ? 'drop-shadow(0 4px 20px rgba(0,0,0,0.5))'
                  : 'none',
            }}
          />
        </div>

        {/* Company name */}
        <div
          style={{
            fontFamily: inter.fontFamily,
            fontWeight: 800,
            fontSize: 64,
            color: textColor,
            letterSpacing: style === 'minimal' ? -2 : 2,
            textTransform: style === 'glitch' ? 'uppercase' : 'none',
            textShadow:
              style === 'neon' ? `0 0 30px ${accentColor}` : 'none',
            minHeight: 80,
          }}
        >
          {displayedName}
          {showCursor && (
            <span style={{ color: accentColor, fontWeight: 400 }}>|</span>
          )}
        </div>

        {/* Tagline */}
        <div
          style={{
            fontFamily: poppins.fontFamily,
            fontWeight: 400,
            fontSize: 28,
            color: subtextColor,
            opacity: taglineOpacity,
            transform: `translateY(${taglineY}px)`,
            marginTop: 12,
            letterSpacing: style === 'minimal' ? 0 : 3,
            textTransform: style !== 'minimal' ? 'uppercase' : 'none',
          }}
        >
          {tagline}
        </div>

        {/* Accent line */}
        {style === 'minimal' && (
          <div
            style={{
              width: interpolate(frame, [fps * 1.5, fps * 2.5], [0, 120], {
                extrapolateLeft: 'clamp',
                extrapolateRight: 'clamp',
              }),
              height: 3,
              background: accentColor,
              borderRadius: 2,
              marginTop: 24,
            }}
          />
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
