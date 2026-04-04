/**
 * F1005: CaptionPage Component Phrase Block Rendering
 * F1006: Karaoke Pop Mode Active Word Highlight
 * F1008: Caption Position at Bottom 8% of Frame
 * F1009: Caption Background Color #7DFF63 Green
 * F1010: Caption Text Color Black
 * F1011: Caption Font: Space Grotesk SemiBold
 * F1012: Caption Font Size: width * 0.052
 */

import React from 'react';
import { useCurrentFrame, useVideoConfig, spring } from 'remotion';
import { TranscriptWord } from '../../../pipeline/ai-generation/ai-types';
import { getActiveWordIndex } from '../../../pipeline/ai-generation/caption-timing';

interface CaptionPageProps {
  words: TranscriptWord[];
  startFrame: number;
  endFrame: number;
}

export const CaptionPage: React.FC<CaptionPageProps> = ({
  words,
  startFrame,
  endFrame,
}) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();

  // Calculate current time in seconds
  const currentTimeInSeconds = frame / fps;

  // F1006: Get active word index for karaoke highlighting
  const activeWordIndex = getActiveWordIndex(words, currentTimeInSeconds);

  // F1012: Caption font size based on width
  const fontSize = width * 0.052;

  // F1008: Caption position at bottom 8% of frame
  const bottomPosition = height * 0.08;

  // Spring animation for word pop effect
  const popSpring = (wordIndex: number) => {
    if (wordIndex !== activeWordIndex) return 1;

    const wordStartTime = words[wordIndex].startInSeconds;
    const wordStartFrame = wordStartTime * fps;
    const framesSinceWordStart = frame - wordStartFrame;

    return spring({
      frame: framesSinceWordStart,
      fps,
      config: {
        damping: 100,
        stiffness: 200,
        mass: 0.5,
      },
      from: 1,
      to: 1.2,
    });
  };

  // Page fade in/out
  const opacity = (() => {
    const fadeFrames = 3;
    if (frame < startFrame + fadeFrames) {
      return (frame - startFrame) / fadeFrames;
    }
    if (frame > endFrame - fadeFrames) {
      return (endFrame - frame) / fadeFrames;
    }
    return 1;
  })();

  if (frame < startFrame || frame > endFrame) {
    return null;
  }

  return (
    <div
      style={{
        position: 'absolute',
        bottom: bottomPosition,
        left: 0,
        right: 0,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '0 20px',
        opacity,
        zIndex: 4, // F1039: Layer ordering
      }}
    >
      {/* F1005: Phrase block rendering */}
      <div
        style={{
          // F1009: Caption background color #7DFF63 green
          backgroundColor: '#7DFF63',
          padding: `${fontSize * 0.3}px ${fontSize * 0.6}px`,
          borderRadius: fontSize * 0.2,
          display: 'flex',
          flexWrap: 'wrap',
          gap: `${fontSize * 0.25}px`,
          justifyContent: 'center',
          alignItems: 'center',
          maxWidth: '90%',
        }}
      >
        {words.map((word, index) => {
          const isActive = index === activeWordIndex;
          const scale = popSpring(index);

          return (
            <span
              key={index}
              style={{
                // F1010: Caption text color black
                color: '#000000',
                // F1011: Caption font Space Grotesk SemiBold
                fontFamily: 'Space Grotesk, sans-serif',
                fontWeight: 600,
                // F1012: Font size
                fontSize: `${fontSize}px`,
                lineHeight: 1.2,
                // F1006: Karaoke pop mode - active word highlight
                transform: `scale(${scale})`,
                transition: 'transform 0.1s ease-out',
                opacity: isActive ? 1 : 0.85,
                display: 'inline-block',
              }}
            >
              {word.word}
            </span>
          );
        })}
      </div>
    </div>
  );
};
