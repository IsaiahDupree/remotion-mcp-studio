/**
 * F1030: SummaryStrap Component: 8–20% Vertical Zone
 * F1031: SummaryStrap Hook Text Prop
 */

import React from 'react';
import { useVideoConfig, useCurrentFrame, interpolate } from 'remotion';

interface SummaryStrapProps {
  hookText: string;
  durationFrames?: number;
}

export const SummaryStrap: React.FC<SummaryStrapProps> = ({
  hookText,
  durationFrames = 60,
}) => {
  const { width, height } = useVideoConfig();
  const frame = useCurrentFrame();

  // F1030: 8–20% vertical zone (positioned at 10% from top)
  const topPosition = height * 0.1;
  const zoneHeight = height * 0.12; // 12% zone height
  const fontSize = width * 0.045;

  // Fade in/out animation
  const opacity = interpolate(
    frame,
    [0, 10, durationFrames - 10, durationFrames],
    [0, 1, 1, 0],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }
  );

  // Slide in from left
  const translateX = interpolate(frame, [0, 15], [-width, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  if (frame > durationFrames) {
    return null;
  }

  return (
    <div
      style={{
        position: 'absolute',
        top: topPosition,
        left: 0,
        right: 0,
        height: zoneHeight,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '0 40px',
        opacity,
        transform: `translateX(${translateX}px)`,
        zIndex: 3, // F1039: Layer ordering
      }}
    >
      {/* F1031: Hook text prop */}
      <div
        style={{
          backgroundColor: '#7DFF63',
          padding: `${fontSize * 0.4}px ${fontSize * 0.8}px`,
          borderRadius: fontSize * 0.3,
          maxWidth: '85%',
        }}
      >
        <p
          style={{
            fontFamily: 'Space Grotesk, sans-serif',
            fontSize: `${fontSize}px`,
            fontWeight: 700,
            color: '#000000',
            margin: 0,
            textAlign: 'center',
            lineHeight: 1.3,
          }}
        >
          {hookText}
        </p>
      </div>
    </div>
  );
};
