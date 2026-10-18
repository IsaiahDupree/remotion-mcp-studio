import React from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion';
import { createTikTokStyleCaptions } from '@remotion/captions';
import type { Caption } from '@remotion/captions';
import { WordTiming } from '../../compositions/tiktok-pipeline/types';

interface CaptionOverlayProps {
  wordTimings: WordTiming[];
  accentColor: string;
  fontFamily: string;
  captionSpeed?: 'fast' | 'medium' | 'slow';
}

function wordTimingsToCaption(timings: WordTiming[]): Caption[] {
  return timings.map((w) => ({
    text: w.word + ' ',
    startMs: Math.round(w.start * 1000),
    endMs: Math.round(w.end * 1000),
    timestampMs: Math.round(w.start * 1000),
    confidence: null,
  }));
}

export const CaptionOverlay: React.FC<CaptionOverlayProps> = ({
  wordTimings,
  accentColor,
  fontFamily,
  captionSpeed = 'medium',
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (!wordTimings || wordTimings.length === 0) return null;

  const currentMs = (frame / fps) * 1000;

  // combineTokensWithinMilliseconds tuned by content speed
  const combineMs = captionSpeed === 'fast' ? 900 : captionSpeed === 'slow' ? 1800 : 1400;

  const captions = wordTimingsToCaption(wordTimings);

  const { pages } = createTikTokStyleCaptions({
    captions,
    combineTokensWithinMilliseconds: combineMs,
  });

  // TikTokPage: { startMs, durationMs, tokens: TikTokToken[] }
  // TikTokToken: { fromMs, toMs, text }
  const activePage = pages.find(
    (page) => currentMs >= page.startMs && currentMs < page.startMs + page.durationMs
  );

  if (!activePage) return null;

  const pageEndMs = activePage.startMs + activePage.durationMs;
  const pageStartFrame = Math.round((activePage.startMs / 1000) * fps);
  const pageEndFrame = Math.round((pageEndMs / 1000) * fps);
  const pageDurationFrames = pageEndFrame - pageStartFrame;

  // enter - exit spring arc: 0→1→0 (T-01 from research)
  const enter = spring({
    fps,
    frame: frame - pageStartFrame,
    config: { stiffness: 280, damping: 22 },
  });
  const exit = spring({
    fps,
    frame: frame - pageStartFrame - pageDurationFrames,
    config: { stiffness: 280, damping: 22 },
  });
  const pageAnimation = Math.max(0, Math.min(1, enter - exit));

  const pageY = interpolate(pageAnimation, [0, 1], [20, 0]);

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 190,
        left: 0,
        right: 0,
        display: 'flex',
        justifyContent: 'center',
        pointerEvents: 'none',
        zIndex: 85,
        padding: '0 40px',
      }}
    >
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: 8,
          justifyContent: 'center',
          maxWidth: '88%',
          opacity: pageAnimation,
          transform: `translateY(${pageY}px)`,
        }}
      >
        {activePage.tokens.map((token, i) => {
          // TikTokToken uses fromMs / toMs
          const tokenDurationMs = token.toMs - token.fromMs;
          const isActive =
            currentMs >= token.fromMs &&
            currentMs < token.toMs;
          const isPast = currentMs >= token.toMs;

          const tokenStartFrame = Math.round((token.fromMs / 1000) * fps);
          const wordProgress = spring({
            frame: frame - tokenStartFrame,
            fps,
            config: { stiffness: 400, damping: 20 },
          });
          const wordScale = isActive
            ? interpolate(wordProgress, [0, 1], [1.0, 1.12])
            : 1;
          const glowBlur = isActive
            ? interpolate(wordProgress, [0, 1], [0, 14])
            : 0;

          // suppress unused warning for tokenDurationMs
          void tokenDurationMs;

          return (
            <span
              key={i}
              style={{
                fontFamily,
                fontSize: 70,
                fontWeight: 900,
                color: isActive ? accentColor : '#ffffff',
                opacity: isPast ? 0.38 : 1,
                display: 'inline-block',
                transform: `scale(${wordScale})`,
                transformOrigin: 'center bottom',
                textShadow: isActive
                  ? `0 0 ${glowBlur}px ${accentColor}95, 2px 2px 10px rgba(0,0,0,0.95)`
                  : '2px 2px 10px rgba(0,0,0,0.9)',
                WebkitTextStroke: '2px rgba(0,0,0,0.45)',
                lineHeight: 1.15,
                letterSpacing: '-0.01em',
              }}
            >
              {token.text}
            </span>
          );
        })}
      </div>
    </div>
  );
};
