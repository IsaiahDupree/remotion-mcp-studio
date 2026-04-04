import React from 'react';
import { useCurrentFrame, useVideoConfig, staticFile } from 'remotion';
import { useWindowedAudioData, visualizeAudio } from '@remotion/media-utils';

interface AudioPulseProps {
  src: string;       // music track path or URL
  accentColor: string;
  intensity?: number; // 0-1, default 0.6
}

export const AudioPulse: React.FC<AudioPulseProps> = ({
  src,
  accentColor,
  intensity = 0.6,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const audioData = useWindowedAudioData({
    src: src.startsWith('http') ? src : staticFile(src),
    frame,
    fps,
    windowInSeconds: 3,
  });

  if (!audioData) return null;

  // Get frequency data — 32 samples (bass = indices 0-4)
  const frequencyData = visualizeAudio({
    fps,
    frame,
    audioData,
    numberOfSamples: 32,
    smoothing: true,
  });

  // Average bass energy (first 4 bins = kick/bass frequencies)
  const bassEnergy = frequencyData.slice(0, 4).reduce((a, b) => a + b, 0) / 4;
  const pulseScale = 1 + bassEnergy * intensity * 0.08;
  const pulseOpacity = 0.06 + bassEnergy * intensity * 0.12;

  // Hex to rgb helper
  const hexToRgb = (hex: string) => {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `${r}, ${g}, ${b}`;
  };

  const rgb = accentColor.startsWith('#') && accentColor.length >= 7
    ? hexToRgb(accentColor)
    : '123, 58, 237';

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background: `radial-gradient(ellipse at center, rgba(${rgb}, ${pulseOpacity}) 0%, transparent 65%)`,
        transform: `scale(${pulseScale})`,
        transformOrigin: 'center center',
        pointerEvents: 'none',
        zIndex: 1,
      }}
    />
  );
};
