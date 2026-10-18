import React from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate, measureSpring, Img, staticFile } from 'remotion';
import { ThemeConfig } from '../../compositions/tiktok-pipeline/types';

interface OutroSlideProps {
  title: string;
  ctaText: string;
  appName?: string;
  theme: ThemeConfig;
  sectionDurationFrames?: number;
}

export const OutroSlide: React.FC<OutroSlideProps> = ({
  title,
  ctaText,
  appName = 'EverReach',
  theme,
  sectionDurationFrames = 150,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Slide-level exit animation: content fades + slides down as section ends
  const exitStartFrame = Math.max(0, sectionDurationFrames - 20);
  const slideExit = spring({
    fps,
    frame: frame - exitStartFrame,
    config: { stiffness: 200, damping: 18 },
  });
  const slideExitOpacity = Math.max(0, 1 - slideExit);
  const slideExitY = interpolate(slideExit, [0, 1], [0, 30]);

  // Measure when title spring settles → chain CTA off it
  const titleFrames = measureSpring({ fps, config: { stiffness: 250, damping: 22 } });
  // Measure when CTA spring settles → chain badge off it
  const ctaFrames = measureSpring({ fps, config: { stiffness: 300, damping: 18, mass: 0.8 } });

  const titleProgress = spring({
    frame: frame - 5,
    fps,
    config: { stiffness: 250, damping: 22 },
  });
  const titleY = interpolate(titleProgress, [0, 1], [40, 0]);
  const titleOpacity = interpolate(titleProgress, [0, 1], [0, 1]);

  const ctaProgress = spring({
    frame: frame - (5 + titleFrames),
    fps,
    config: { stiffness: 300, damping: 18, mass: 0.8 },
  });
  const ctaScale = interpolate(ctaProgress, [0, 1], [0.8, 1.0]);
  const ctaOpacity = interpolate(ctaProgress, [0, 1], [0, 1]);

  // Continuous CTA float — ramps in with spring, then oscillates
  const floatRamp = spring({ frame: frame - (5 + titleFrames), fps, config: { stiffness: 50, damping: 20 } });
  const floatY = Math.sin(frame / 14) * 6 * floatRamp;

  const badgeProgress = spring({
    frame: frame - (5 + titleFrames + ctaFrames),
    fps,
    config: { stiffness: 200, damping: 20 },
  });
  const badgeY = interpolate(badgeProgress, [0, 1], [30, 0]);
  const badgeOpacity = interpolate(badgeProgress, [0, 1], [0, 1]);

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '80px 60px',
        gap: 0,
        textAlign: 'center',
        opacity: slideExitOpacity,
        transform: `translateY(${slideExitY}px)`,
      }}
    >
      {/* App icon */}
      <div style={{ marginBottom: 36, opacity: titleOpacity }}>
        <Img
          src={staticFile('everreach/branding/appstore-icon-1024-flat.png')}
          style={{
            width: 110,
            height: 110,
            borderRadius: 24,
            objectFit: 'cover',
            boxShadow: `0 12px 40px ${theme.accent}50`,
          }}
        />
      </div>

      {/* Title */}
      <h2
        style={{
          fontFamily: theme.fontFamily,
          fontSize: 74,
          fontWeight: 800,
          color: theme.primary,
          margin: 0,
          marginBottom: 48,
          lineHeight: 1.1,
          opacity: titleOpacity,
          transform: `translateY(${titleY}px)`,
          letterSpacing: '-0.02em',
        }}
      >
        {title}
      </h2>

      {/* CTA button */}
      <div
        style={{
          padding: '24px 56px',
          backgroundColor: theme.accent,
          borderRadius: 50,
          boxShadow: `0 12px 40px ${theme.accent}50`,
          opacity: ctaOpacity,
          transform: `scale(${ctaScale}) translateY(${floatY}px)`,
        }}
      >
        <p
          style={{
            fontFamily: theme.fontFamily,
            fontSize: 32,
            fontWeight: 700,
            color: '#ffffff',
            margin: 0,
          }}
        >
          {ctaText}
        </p>
      </div>

      {/* App Store badge */}
      <div
        style={{
          marginTop: 48,
          display: 'flex',
          alignItems: 'center',
          gap: 14,
          backgroundColor: 'rgba(255,255,255,0.08)',
          border: '1px solid rgba(255,255,255,0.15)',
          borderRadius: 18,
          padding: '14px 28px',
          opacity: badgeOpacity,
          transform: `translateY(${badgeY}px)`,
        }}
      >
        <Img
          src={staticFile('everreach/branding/appstore-icon-1024-flat.png')}
          style={{ width: 44, height: 44, borderRadius: 10, objectFit: 'cover' }}
        />
        <div style={{ display: 'flex', flexDirection: 'column', gap: 2, textAlign: 'left' }}>
          <span
            style={{
              fontFamily: theme.fontFamily,
              fontSize: 17,
              color: 'rgba(255,255,255,0.65)',
              fontWeight: 500,
            }}
          >
            Available on the
          </span>
          <span
            style={{
              fontFamily: theme.fontFamily,
              fontSize: 27,
              fontWeight: 800,
              color: '#ffffff',
              letterSpacing: '-0.01em',
            }}
          >
            App Store
          </span>
        </div>
      </div>

      {/* Free label */}
      <p
        style={{
          fontFamily: theme.fontFamily,
          fontSize: 20,
          color: 'rgba(255,255,255,0.4)',
          marginTop: 18,
          opacity: badgeOpacity,
        }}
      >
        {appName} · Free to download
      </p>
    </div>
  );
};
