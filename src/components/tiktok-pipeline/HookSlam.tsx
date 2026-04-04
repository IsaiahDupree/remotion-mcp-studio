import React from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate, Easing } from 'remotion';
import { ThemeConfig } from '../../compositions/tiktok-pipeline/types';
import { chromaticTextShadow } from './Vignette';

interface HookSlamProps {
  text: string;
  emoji?: string;
  subtext?: string;
  style_: 'stamp' | 'stat' | 'question' | 'glitch' | 'bold_center';
  theme: ThemeConfig;
}

export const HookSlam: React.FC<HookSlamProps> = ({
  text,
  emoji,
  subtext,
  style_,
  theme,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Spring slam: text punches in from 130% → 100%
  const slamProgress = spring({
    frame,
    fps,
    config: { stiffness: 480, damping: 28, mass: 0.8 },
  });

  const scale = interpolate(slamProgress, [0, 1], [1.35, 1.0]);

  // Opacity: instant on frame 0
  const opacity = interpolate(frame, [0, 3], [0, 1], {
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.quad),
  });

  // Screen flash: white overlay fades out in first 8 frames
  const flashOpacity = interpolate(frame, [0, 8], [0.5, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.quad),
  });

  // Micro-zoom on background: 1.0 → 1.06 over 90 frames (Ken Burns)
  const microZoom = interpolate(frame, [0, 90], [1.0, 1.06], {
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.ease),
  });

  // Accent underline width grows in
  const underlineWidth = interpolate(frame, [10, 30], [0, 140], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });

  // Subtext spring in with delay
  const subtextProgress = spring({
    frame: frame - 18,
    fps,
    config: { stiffness: 250, damping: 20 },
  });
  const subtextY = interpolate(subtextProgress, [0, 1], [25, 0]);
  const subtextOpacity = interpolate(subtextProgress, [0, 1], [0, 1]);

  const isStatStyle = style_ === 'stat';
  const fontSize = 92;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '60px 50px',
        textAlign: 'center',
        transform: `scale(${microZoom})`,
        transformOrigin: 'center center',
      }}
    >
      {/* Screen flash */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundColor: '#ffffff',
          opacity: flashOpacity,
          pointerEvents: 'none',
        }}
      />

      {/* Accent top bar */}
      <div
        style={{
          position: 'absolute',
          top: 0, left: 0, right: 0,
          height: 6,
          background: theme.accent,
          boxShadow: `0 0 20px ${theme.accent}80`,
        }}
      />

      {/* Emoji */}
      {emoji && (
        <div
          style={{
            fontSize: 76,
            marginBottom: 16,
            opacity,
            transform: `scale(${scale})`,
          }}
        >
          {emoji}
        </div>
      )}

      {/* Main hook text — per-word stagger (T-02) */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'center',
          gap: '0 16px',
          transform: `scale(${scale})`,
          transformOrigin: 'center center',
        }}
      >
        {text.split(' ').map((word, wi) => {
          const wordSlamProgress = spring({
            frame: frame - wi * 5,
            fps,
            config: { stiffness: 480, damping: 28, mass: 0.8 },
          });
          const wordScale = interpolate(wordSlamProgress, [0, 1], [1.35, 1.0]);
          const wordOpacity = interpolate(
            Math.max(0, frame - wi * 5),
            [0, 3],
            [0, 1],
            { extrapolateRight: 'clamp' }
          );
          return (
            <span
              key={wi}
              style={{
                fontFamily: theme.fontFamily,
                fontSize,
                fontWeight: 900,
                color: isStatStyle ? theme.accent : theme.primary,
                lineHeight: 1.05,
                letterSpacing: '-0.02em',
                display: 'inline-block',
                opacity: wordOpacity,
                transform: `scale(${wordScale})`,
                transformOrigin: 'center bottom',
                textShadow: isStatStyle
                  ? `0 0 30px ${theme.accent}60, ${chromaticTextShadow(1.5)}`
                  : `2px 2px 12px rgba(0,0,0,0.8)`,
                WebkitTextStroke: '2px rgba(0,0,0,0.3)',
              }}
            >
              {word}
            </span>
          );
        })}
      </div>

      {/* Accent underline */}
      <div
        style={{
          width: underlineWidth,
          height: 5,
          backgroundColor: theme.accent,
          borderRadius: 3,
          marginTop: 20,
          boxShadow: `0 0 12px ${theme.accent}80`,
        }}
      />

      {/* Subtext */}
      {subtext && (
        <div
          style={{
            marginTop: 28,
            padding: '12px 28px',
            backgroundColor: `${theme.accent}18`,
            borderRadius: 12,
            border: `1px solid ${theme.accent}40`,
            opacity: subtextOpacity,
            transform: `translateY(${subtextY}px)`,
          }}
        >
          <p
            style={{
              fontFamily: theme.fontFamily,
              fontSize: 34,
              fontWeight: 500,
              color: theme.secondary,
              margin: 0,
              lineHeight: 1.4,
            }}
          >
            {subtext}
          </p>
        </div>
      )}
    </div>
  );
};
