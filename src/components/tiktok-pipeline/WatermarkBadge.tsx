import React from 'react';
import { Img, staticFile } from 'remotion';

export const WatermarkBadge: React.FC = () => {
  return (
    <div
      style={{
        position: 'absolute',
        top: 32,
        right: 28,
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        opacity: 0.8,
        backgroundColor: 'rgba(0,0,0,0.35)',
        borderRadius: 20,
        padding: '8px 14px 8px 10px',
        backdropFilter: 'blur(4px)',
        pointerEvents: 'none',
        zIndex: 95,
      }}
    >
      <Img
        src={staticFile('everreach/branding/appstore-icon-1024-flat.png')}
        style={{ width: 34, height: 34, borderRadius: 8, objectFit: 'cover' }}
      />
      <span
        style={{
          fontFamily: 'Poppins, Inter, sans-serif',
          fontSize: 22,
          fontWeight: 700,
          color: '#ffffff',
          letterSpacing: '-0.01em',
        }}
      >
        EverReach
      </span>
    </div>
  );
};
