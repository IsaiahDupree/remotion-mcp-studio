/**
 * F1027: TopNameBar Component: 8% Height at Top
 * F1028: TopNameBar Brand Name in Archivo Black Font
 */

import React from 'react';
import { useVideoConfig } from 'remotion';

interface TopNameBarProps {
  brandName: string;
}

export const TopNameBar: React.FC<TopNameBarProps> = ({ brandName }) => {
  const { width, height } = useVideoConfig();

  // F1027: 8% height at top
  const barHeight = height * 0.08;
  const fontSize = barHeight * 0.5;

  return (
    <div
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        height: barHeight,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(0, 0, 0, 0.3)',
        backdropFilter: 'blur(10px)',
        zIndex: 5, // F1039: Layer ordering - TopNameBar should be on top
      }}
    >
      {/* F1028: Brand name in Archivo Black font */}
      <span
        style={{
          fontFamily: 'Archivo Black, sans-serif',
          fontSize: `${fontSize}px`,
          color: '#FFFFFF',
          fontWeight: 900,
          letterSpacing: '0.05em',
          textTransform: 'uppercase',
        }}
      >
        {brandName}
      </span>
    </div>
  );
};
