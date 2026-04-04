import React from 'react';
import { useCurrentFrame } from 'remotion';

interface FilmGrainProps {
  opacity?: number;       // default 0.06
  blendMode?: string;     // default 'overlay'
  animationSpeed?: number; // default 7 (shift every N frames)
}

export const FilmGrain: React.FC<FilmGrainProps> = ({
  opacity = 0.06,
  blendMode = 'overlay',
  animationSpeed = 7,
}) => {
  const frame = useCurrentFrame();
  // Shift grain pattern every animationSpeed frames — grain "flickers" like film
  const shift = (frame % animationSpeed) * 23;
  const size = 150 + shift;

  const svgDataUrl = `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='${size}' height='${size}'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E")`;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        opacity,
        backgroundImage: svgDataUrl,
        backgroundSize: `${size}px ${size}px`,
        mixBlendMode: blendMode as React.CSSProperties['mixBlendMode'],
        pointerEvents: 'none',
        zIndex: 90,
      }}
    />
  );
};
