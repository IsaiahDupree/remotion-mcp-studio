import React from 'react';

interface VignetteProps {
  strength?: number; // 0-1, default 0.55
  chromaticAberration?: boolean; // default true - adds R/B split on text via className
}

export const Vignette: React.FC<VignetteProps> = ({
  strength = 0.55,
}) => {
  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background: `radial-gradient(ellipse at center, transparent 45%, rgba(0,0,0,${strength}) 100%)`,
        pointerEvents: 'none',
        zIndex: 91,
      }}
    />
  );
};

// Helper: apply chromatic aberration text shadow to any text element
export function chromaticTextShadow(intensity: number = 1): string {
  const px = intensity;
  return `-${px}px 0 ${px}px rgba(255,0,0,0.35), ${px}px 0 ${px}px rgba(0,0,255,0.35)`;
}
