import React from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion';
import { ThemeConfig } from '../../compositions/tiktok-pipeline/types';

interface BodyContentProps {
  points: string[];
  theme: ThemeConfig;
  style: 'numbered' | 'checklist' | 'bullets';
  sectionDurationFrames: number;
}

export const BodyContent: React.FC<BodyContentProps> = ({
  points,
  theme,
  style,
  sectionDurationFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const framesPerPoint = sectionDurationFrames / Math.max(points.length, 1);

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'flex-start',
        justifyContent: 'center',
        padding: '80px 60px',
        gap: 32,
      }}
    >
      {points.map((point, i) => {
        const revealFrame = i * framesPerPoint;
        const progress = spring({
          frame: frame - revealFrame,
          fps,
          config: { stiffness: 280, damping: 22 },
        });

        const slideY = interpolate(progress, [0, 1], [30, 0]);
        const opacity = interpolate(progress, [0, 1], [0, 1]);

        const flashFrame = frame - revealFrame;
        const accentWidth = interpolate(flashFrame, [0, 15], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });

        // Per-word stagger (T-02): each word delayed by 5 frames × index
        const words = point.split(' ');

        return (
          <div
            key={i}
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 24,
              opacity,
              transform: `translateY(${slideY}px)`,
            }}
          >
            {/* Number / check indicator */}
            <div
              style={{
                width: 52,
                height: 52,
                borderRadius: style === 'numbered' ? 12 : '50%',
                backgroundColor: `${theme.accent}25`,
                border: `2px solid ${theme.accent}`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                flexShrink: 0,
                marginTop: 4,
                boxShadow: `0 0 12px ${theme.accent}30`,
              }}
            >
              <span
                style={{
                  fontFamily: theme.fontFamily,
                  fontSize: 26,
                  fontWeight: 800,
                  color: theme.accent,
                  lineHeight: 1,
                }}
              >
                {style === 'checklist' ? '✓' : `${i + 1}`}
              </span>
            </div>

            {/* Point text with per-word stagger */}
            <div style={{ flex: 1 }}>
              <p
                style={{
                  fontFamily: theme.fontFamily,
                  fontSize: 44,
                  fontWeight: 700,
                  color: theme.primary,
                  margin: 0,
                  lineHeight: 1.3,
                  letterSpacing: '-0.01em',
                  textShadow: '1px 1px 6px rgba(0,0,0,0.7)',
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: '0 10px',
                }}
              >
                {words.map((word, wi) => {
                  const wordDelay = revealFrame + wi * 5;
                  const wOpacity = interpolate(
                    frame - wordDelay,
                    [0, 12],
                    [0, 1],
                    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
                  );
                  const wSpring = spring({
                    fps,
                    frame: frame - wordDelay,
                    config: { stiffness: 200, damping: 18 },
                  });
                  const wY = interpolate(wSpring, [0, 1], [-20, 0]);
                  return (
                    <span
                      key={wi}
                      style={{
                        display: 'inline-block',
                        opacity: wOpacity,
                        transform: `translateY(${wY}px)`,
                      }}
                    >
                      {word}
                    </span>
                  );
                })}
              </p>
              {/* Underline accent sweep */}
              <div
                style={{
                  height: 2,
                  width: `${accentWidth * 100}%`,
                  backgroundColor: theme.accent,
                  marginTop: 6,
                  borderRadius: 1,
                  opacity: 0.5,
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};
