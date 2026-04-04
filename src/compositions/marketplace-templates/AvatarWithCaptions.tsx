/**
 * AvatarWithCaptions.tsx
 *
 * Full-screen avatar video composited over a background with:
 * - Transparent avatar (from green-screen removal via FFmpeg)
 * - Animated title text at top
 * - Word-by-word karaoke captions at bottom
 * - Optional gradient overlay for readability
 *
 * Pipeline:
 * 1. HeyGen generates avatar with green screen (#00b140)
 * 2. FFmpeg converts: colorkey → transparent WebM
 * 3. This composition layers avatar over any background
 */

import React, { useMemo } from 'react';
import {
  AbsoluteFill,
  Audio,
  OffthreadVideo,
  Img,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Sequence,
  staticFile,
} from 'remotion';
import { z } from 'zod';
import { loadFont } from '@remotion/google-fonts/Inter';

const { fontFamily } = loadFont();

// ── Schema ───────────────────────────────────────────────────────────────────

const WordTimingSchema = z.object({
  word: z.string(),
  start: z.number().describe('Start time in seconds'),
  end: z.number().describe('End time in seconds'),
});

export const avatarWithCaptionsSchema = z.object({
  avatarVideoSrc: z
    .string()
    .default('avatar-transparent.webm')
    .describe('Path to transparent avatar WebM (after green screen removal)'),
  backgroundType: z
    .enum(['color', 'image', 'video'])
    .default('color')
    .describe('Background type'),
  backgroundValue: z
    .string()
    .default('#0a0a1a')
    .describe('Background color hex, image URL, or video URL'),
  title: z
    .string()
    .default('Remotion MCP Studio')
    .describe('Title text shown at top'),
  subtitle: z
    .string()
    .default('')
    .describe('Optional subtitle below title'),
  captions: z
    .array(WordTimingSchema)
    .default([])
    .describe('Word-level caption timings from HeyGen/Whisper'),
  captionStyle: z
    .enum(['tiktok', 'centered', 'minimal'])
    .default('tiktok')
    .describe('Caption visual style'),
  accentColor: z.string().default('#3b82f6').describe('Accent color for highlights'),
  avatarScale: z.number().default(1.0).describe('Avatar size multiplier (0.5-2.0)'),
  avatarPosition: z
    .enum(['center', 'bottom', 'left', 'right'])
    .default('center')
    .describe('Avatar position in frame'),
  showGradientOverlay: z.boolean().default(true).describe('Dark gradient at top/bottom for readability'),
  audioSrc: z
    .string()
    .default('')
    .describe('Path to audio file (extracted from HeyGen video)'),
  durationInSeconds: z.number().default(15).describe('Video duration in seconds'),
});

export type AvatarWithCaptionsProps = z.infer<typeof avatarWithCaptionsSchema>;

export const avatarWithCaptionsDefaultProps: AvatarWithCaptionsProps =
  avatarWithCaptionsSchema.parse({});

// ── Caption Component ────────────────────────────────────────────────────────

const KaraokeCaptions: React.FC<{
  captions: z.infer<typeof WordTimingSchema>[];
  style: string;
  accentColor: string;
  frame: number;
  fps: number;
}> = ({ captions, style, accentColor, frame, fps }) => {
  const currentTimeSec = frame / fps;

  // Find current window of words (show ~6 words at a time)
  const activeIdx = captions.findIndex(
    (w) => currentTimeSec >= w.start && currentTimeSec <= w.end
  );

  if (activeIdx === -1 && currentTimeSec > (captions[captions.length - 1]?.end || 0)) {
    return null;
  }

  // Show a window of words around the active word
  const windowSize = 6;
  const windowStart = Math.max(0, activeIdx - Math.floor(windowSize / 2));
  const windowEnd = Math.min(captions.length, windowStart + windowSize);
  const visibleWords = captions.slice(windowStart, windowEnd);

  const containerStyle: React.CSSProperties = {
    position: 'absolute',
    bottom: style === 'centered' ? '40%' : 160,
    left: 0,
    right: 0,
    display: 'flex',
    justifyContent: 'center',
    flexWrap: 'wrap',
    gap: 8,
    padding: '0 60px',
  };

  return (
    <div style={containerStyle}>
      {visibleWords.map((word, i) => {
        const globalIdx = windowStart + i;
        const isActive =
          currentTimeSec >= word.start && currentTimeSec <= word.end;
        const isPast = currentTimeSec > word.end;

        const wordStyle: React.CSSProperties = {
          fontFamily,
          fontSize: style === 'tiktok' ? 64 : 52,
          fontWeight: 800,
          color: isActive ? '#ffffff' : isPast ? 'rgba(255,255,255,0.5)' : 'rgba(255,255,255,0.7)',
          textShadow: isActive
            ? `0 0 20px ${accentColor}, 0 4px 12px rgba(0,0,0,0.8)`
            : '0 2px 8px rgba(0,0,0,0.7)',
          transform: isActive ? 'scale(1.15)' : 'scale(1)',
          transition: 'all 0.1s ease',
          backgroundColor: isActive && style === 'tiktok'
            ? accentColor
            : 'transparent',
          padding: isActive && style === 'tiktok' ? '4px 12px' : '4px 4px',
          borderRadius: 8,
          lineHeight: 1.3,
        };

        return (
          <span key={globalIdx} style={wordStyle}>
            {word.word}
          </span>
        );
      })}
    </div>
  );
};

// ── Title Component ──────────────────────────────────────────────────────────

const AnimatedTitle: React.FC<{
  title: string;
  subtitle: string;
  accentColor: string;
  frame: number;
  fps: number;
}> = ({ title, subtitle, accentColor, frame, fps }) => {
  const titleProgress = spring({ frame, fps, config: { damping: 14, stiffness: 120 } });
  const subtitleProgress = spring({
    frame: Math.max(0, frame - 10),
    fps,
    config: { damping: 14, stiffness: 100 },
  });

  // Fade out after 4 seconds
  const fadeOut = interpolate(frame, [fps * 3.5, fps * 4.5], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        top: 100,
        left: 0,
        right: 0,
        textAlign: 'center',
        padding: '0 40px',
        opacity: fadeOut,
      }}
    >
      <div
        style={{
          fontFamily,
          fontSize: 56,
          fontWeight: 900,
          color: '#ffffff',
          textShadow: `0 0 30px ${accentColor}40, 0 4px 16px rgba(0,0,0,0.6)`,
          transform: `translateY(${interpolate(titleProgress, [0, 1], [40, 0])}px)`,
          opacity: titleProgress,
          letterSpacing: -1,
        }}
      >
        {title}
      </div>
      {subtitle && (
        <div
          style={{
            fontFamily,
            fontSize: 32,
            fontWeight: 500,
            color: 'rgba(255,255,255,0.8)',
            marginTop: 12,
            transform: `translateY(${interpolate(subtitleProgress, [0, 1], [20, 0])}px)`,
            opacity: subtitleProgress,
          }}
        >
          {subtitle}
        </div>
      )}
    </div>
  );
};

// ── Main Composition ─────────────────────────────────────────────────────────

export const AvatarWithCaptions: React.FC<AvatarWithCaptionsProps> = (props) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  const avatarPositionStyle = useMemo((): React.CSSProperties => {
    const scale = props.avatarScale;
    switch (props.avatarPosition) {
      case 'bottom':
        return {
          position: 'absolute',
          bottom: 0,
          left: '50%',
          transform: `translateX(-50%) scale(${scale})`,
          transformOrigin: 'bottom center',
          width: '100%',
          height: '100%',
        };
      case 'left':
        return {
          position: 'absolute',
          top: 0,
          left: 0,
          transform: `scale(${scale})`,
          transformOrigin: 'top left',
          width: '100%',
          height: '100%',
        };
      case 'right':
        return {
          position: 'absolute',
          top: 0,
          right: 0,
          transform: `scale(${scale})`,
          transformOrigin: 'top right',
          width: '100%',
          height: '100%',
        };
      case 'center':
      default:
        return {
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          transform: `scale(${scale})`,
          transformOrigin: 'center center',
        };
    }
  }, [props.avatarScale, props.avatarPosition]);

  return (
    <AbsoluteFill style={{ backgroundColor: '#000000' }}>
      {/* Background Layer */}
      {props.backgroundType === 'color' && (
        <AbsoluteFill style={{ backgroundColor: props.backgroundValue }} />
      )}
      {props.backgroundType === 'image' && (
        <Img
          src={props.backgroundValue}
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        />
      )}
      {props.backgroundType === 'video' && (
        <OffthreadVideo
          src={props.backgroundValue}
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        />
      )}

      {/* Gradient Overlay for readability */}
      {props.showGradientOverlay && (
        <AbsoluteFill>
          {/* Top gradient */}
          <div
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              height: '30%',
              background:
                'linear-gradient(180deg, rgba(0,0,0,0.7) 0%, transparent 100%)',
            }}
          />
          {/* Bottom gradient */}
          <div
            style={{
              position: 'absolute',
              bottom: 0,
              left: 0,
              right: 0,
              height: '35%',
              background:
                'linear-gradient(0deg, rgba(0,0,0,0.8) 0%, transparent 100%)',
            }}
          />
        </AbsoluteFill>
      )}

      {/* Audio Track (extracted from HeyGen video) */}
      {props.audioSrc && (
        <Audio src={staticFile(props.audioSrc)} volume={1} />
      )}

      {/* Avatar Layer (transparent WebM) */}
      <div style={avatarPositionStyle}>
        <OffthreadVideo
          src={staticFile(props.avatarVideoSrc)}
          transparent
          style={{ width: '100%', height: '100%', objectFit: 'contain' }}
        />
      </div>

      {/* Title */}
      {props.title && (
        <AnimatedTitle
          title={props.title}
          subtitle={props.subtitle}
          accentColor={props.accentColor}
          frame={frame}
          fps={fps}
        />
      )}

      {/* Captions */}
      {props.captions.length > 0 && (
        <KaraokeCaptions
          captions={props.captions}
          style={props.captionStyle}
          accentColor={props.accentColor}
          frame={frame}
          fps={fps}
        />
      )}
    </AbsoluteFill>
  );
};
