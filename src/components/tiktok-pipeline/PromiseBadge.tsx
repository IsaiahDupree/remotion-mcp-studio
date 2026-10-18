import React from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion';

interface PromiseBadgeProps {
  tipCount: number;      // e.g. 3
  durationSec: number;   // total video duration
  accentColor: string;
  fontFamily: string;
}

export const PromiseBadge: React.FC<PromiseBadgeProps> = ({
  tipCount,
  durationSec,
  accentColor,
  fontFamily,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Pop in at frame 8 via spring
  const popProgress = spring({
    frame: frame - 8,
    fps,
    config: { stiffness: 350, damping: 18 },
  });
  const scale = interpolate(popProgress, [0, 1], [0.6, 1.0]);
  const opacity = interpolate(popProgress, [0, 1], [0, 1]);

  // Fade out in last 20% of video
  const fadeOutStart = durationSec * fps * 0.8;
  const exitOpacity = interpolate(frame, [fadeOutStart, fadeOutStart + 15], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const label = tipCount === 1
    ? `1 tip · ${Math.round(durationSec)}s`
    : `${tipCount} tips · ${Math.round(durationSec)}s`;

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 140,
        left: 28,
        display: 'flex',
        alignItems: 'center',
        gap: 8,
        opacity: opacity * exitOpacity,
        transform: `scale(${scale})`,
        transformOrigin: 'bottom left',
        pointerEvents: 'none',
        zIndex: 94,
      }}
    >
      <div
        style={{
          backgroundColor: `${accentColor}22`,
          border: `1.5px solid ${accentColor}60`,
          borderRadius: 20,
          padding: '8px 16px',
          backdropFilter: 'blur(6px)',
          display: 'flex',
          alignItems: 'center',
          gap: 8,
        }}
      >
        {/* Pulsing dot */}
        <div
          style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            backgroundColor: accentColor,
            boxShadow: `0 0 6px ${accentColor}`,
            flexShrink: 0,
          }}
        />
        <span
          style={{
            fontFamily,
            fontSize: 22,
            fontWeight: 600,
            color: '#ffffff',
            letterSpacing: '0.01em',
          }}
        >
          {label}
        </span>
      </div>
    </div>
  );
};
