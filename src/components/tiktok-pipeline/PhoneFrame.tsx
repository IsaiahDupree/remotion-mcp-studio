import React from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate, measureSpring, Img, staticFile, Easing } from 'remotion';
import { ThemeConfig } from '../../compositions/tiktok-pipeline/types';

interface PhoneFrameProps {
  screenshotPath: string;
  notificationText?: string;
  theme: ThemeConfig;
}

export const PhoneFrame: React.FC<PhoneFrameProps> = ({
  screenshotPath,
  notificationText,
  theme,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const isVertical = height > width;

  // Measure when phone bounce settles → start screen exactly then
  const phoneLandFrames = measureSpring({ fps, config: { stiffness: 180, damping: 14 } });
  // Measure when screen fade settles → start notification exactly then
  const screenFadeFrames = measureSpring({ fps, config: { stiffness: 300, damping: 22 } });

  // Phone bounces in from below
  const bounceProgress = spring({
    frame,
    fps,
    config: { stiffness: 180, damping: 14 },
  });
  const phoneY = interpolate(bounceProgress, [0, 1], [120, 0]);
  const phoneOpacity = interpolate(bounceProgress, [0, 1], [0, 1]);

  // Screen fades in after phone lands
  const screenProgress = spring({
    frame: frame - phoneLandFrames,
    fps,
    config: { stiffness: 300, damping: 22 },
  });
  const screenOpacity = interpolate(screenProgress, [0, 1], [0, 1]);

  // Notification slides in
  const notifProgress = spring({
    frame: frame - phoneLandFrames - screenFadeFrames,
    fps,
    config: { stiffness: 350, damping: 20 },
  });
  const notifY = interpolate(notifProgress, [0, 1], [-80, 0]);
  const notifOpacity = interpolate(notifProgress, [0, 1], [0, 1]);

  // Micro-zoom on phone (Ken Burns)
  const microZoom = interpolate(frame, [0, 90], [1.0, 1.04], {
    extrapolateRight: 'clamp',
  });

  const phoneH = isVertical ? height * 0.7 : height * 0.82;
  const phoneW = phoneH * 0.46;
  const screenH = phoneH * 0.83;
  const screenW = phoneW * 0.88;
  const cornerR = phoneW * 0.12;

  const imgSrc = screenshotPath.startsWith('http')
    ? screenshotPath
    : staticFile(screenshotPath);

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        transform: `scale(${microZoom})`,
      }}
    >
      <div
        style={{
          opacity: phoneOpacity,
          transform: `translateY(${phoneY}px)`,
        }}
      >
        {/* Phone shell */}
        <div
          style={{
            width: phoneW,
            height: phoneH,
            backgroundColor: '#1c1c1e',
            borderRadius: cornerR,
            border: '3px solid #3a3a3c',
            boxShadow: `0 40px 100px rgba(0,0,0,0.75), 0 0 40px ${theme.accent}30`,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          {/* Dynamic island */}
          <div
            style={{
              position: 'absolute',
              top: phoneH * 0.02,
              width: phoneW * 0.3,
              height: phoneH * 0.025,
              backgroundColor: '#000',
              borderRadius: 20,
              zIndex: 10,
            }}
          />

          {/* Screen */}
          <div
            style={{
              width: screenW,
              height: screenH,
              backgroundColor: '#000',
              borderRadius: cornerR * 0.7,
              overflow: 'hidden',
              opacity: screenOpacity,
              position: 'relative',
            }}
          >
            {/* Status bar */}
            <div
              style={{
                height: 28,
                backgroundColor: 'rgba(0,0,0,0.8)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0 12px',
                fontSize: 10,
                color: '#fff',
                fontFamily: 'monospace',
              }}
            >
              <span>9:41</span>
              <span>● ● ●</span>
            </div>

            {/* App screenshot */}
            <Img
              src={imgSrc}
              style={{ width: '100%', height: '100%', objectFit: 'cover' }}
            />

            {/* Notification */}
            {notificationText && (
              <div
                style={{
                  position: 'absolute',
                  top: 36,
                  left: 8,
                  right: 8,
                  opacity: notifOpacity,
                  transform: `translateY(${notifY}px)`,
                  backgroundColor: 'rgba(30,30,30,0.96)',
                  backdropFilter: 'blur(8px)',
                  borderRadius: 12,
                  padding: '10px 14px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                }}
              >
                <div
                  style={{
                    width: 28,
                    height: 28,
                    borderRadius: 8,
                    backgroundColor: theme.accent,
                    flexShrink: 0,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: 14,
                  }}
                >
                  ⏰
                </div>
                <p
                  style={{
                    fontFamily: theme.fontFamily,
                    fontSize: 11,
                    color: '#fff',
                    margin: 0,
                    lineHeight: 1.3,
                  }}
                >
                  {notificationText}
                </p>
              </div>
            )}
          </div>

          {/* Home indicator */}
          <div
            style={{
              position: 'absolute',
              bottom: phoneH * 0.015,
              width: phoneW * 0.35,
              height: 4,
              backgroundColor: '#fff',
              borderRadius: 2,
              opacity: 0.5,
            }}
          />
        </div>
      </div>
    </div>
  );
};
