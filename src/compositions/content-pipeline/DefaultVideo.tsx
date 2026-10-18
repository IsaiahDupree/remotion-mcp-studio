/**
 * F1026: AbsoluteFill Root with Black Background
 * F1044: Composition Width/Height Constants for 9:16
 * Main composition that combines all video elements
 */

import React, { useEffect } from 'react';
import { AbsoluteFill, Sequence, useVideoConfig, Video, continueRender, delayRender } from 'remotion';
import { CaptionPage as CaptionPageComponent } from './components/CaptionPage';
import { TopNameBar } from './components/TopNameBar';
import { SummaryStrap } from './components/SummaryStrap';
import { GradientVignette } from './components/GradientVignette';
import { RemotionInputProps } from '../../pipeline/ai-generation/ai-types';
import { chunkWordsToCaptionPages } from '../../pipeline/ai-generation/caption-timing';
import { loadIsaiahFonts } from '../../lib/isaiahFonts';

// F1044: Composition Width/Height Constants for 9:16 aspect ratio
export const COMPOSITION_WIDTH = 1080;
export const COMPOSITION_HEIGHT = 1920;

export const DefaultVideo: React.FC<RemotionInputProps> = ({
  transcriptWords,
  summaryStrapText,
  durationInSeconds,
  brandName,
  sourceVideoUrl,
  videoStartMs,
  videoEndMs,
}) => {
  const { fps } = useVideoConfig(); // F1057: fps from useVideoConfig

  // F1067: delayRender/continueRender pattern for font loading
  useEffect(() => {
    const handle = delayRender('Loading fonts');

    loadIsaiahFonts()
      .then(() => {
        continueRender(handle);
        console.log('✓ Fonts loaded, rendering can continue');
      })
      .catch((error) => {
        console.warn('⚠ Font loading failed, continuing with system fonts:', error);
        continueRender(handle); // F1068: Graceful fallback
      });
  }, []);

  // Chunk words into caption pages
  const captionPages = chunkWordsToCaptionPages(
    transcriptWords,
    6,
    durationInSeconds
  );

  // Convert times to frames
  const hookDurationFrames = Math.min(60, fps * 3); // 3 seconds or 60 frames

  return (
    // F1026: AbsoluteFill root with black background
    <AbsoluteFill style={{ backgroundColor: '#000000' }}>
      {/* F1047, F1058: Background video with startFrom/endAt, rendered below all overlays */}
      {sourceVideoUrl && (
        <AbsoluteFill style={{ zIndex: 1 }}>
          <Video
            src={sourceVideoUrl}
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
            }}
            muted
            startFrom={videoStartMs ? Math.round((videoStartMs / 1000) * fps) : undefined}
            endAt={videoEndMs ? Math.round((videoEndMs / 1000) * fps) : undefined}
          />
        </AbsoluteFill>
      )}

      {/* Gradient vignette overlay */}
      <GradientVignette />

      {/* Top name bar */}
      <TopNameBar brandName={brandName} />

      {/* Summary strap (hook) - shows at beginning */}
      <Sequence from={0} durationInFrames={hookDurationFrames}>
        <SummaryStrap
          hookText={summaryStrapText}
          durationFrames={hookDurationFrames}
        />
      </Sequence>

      {/* Caption pages */}
      {captionPages.map((page, index) => {
        const startFrame = Math.floor(page.startTime * fps);
        const endFrame = Math.floor(page.endTime * fps);

        return (
          <Sequence
            key={index}
            from={startFrame}
            durationInFrames={endFrame - startFrame}
          >
            <CaptionPageComponent
              words={page.words}
              startFrame={startFrame}
              endFrame={endFrame}
            />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
