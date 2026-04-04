/**
 * F1034: Gradient Vignette Overlay: Top and Bottom
 */

import React from 'react';

export const GradientVignette: React.FC = () => {
  return (
    <>
      {/* Top gradient vignette */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '30%',
          background: 'linear-gradient(180deg, rgba(0,0,0,0.4) 0%, transparent 100%)',
          pointerEvents: 'none',
          zIndex: 2, // F1039: Layer ordering
        }}
      />

      {/* Bottom gradient vignette */}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: '30%',
          background: 'linear-gradient(0deg, rgba(0,0,0,0.4) 0%, transparent 100%)',
          pointerEvents: 'none',
          zIndex: 2, // F1039: Layer ordering
        }}
      />
    </>
  );
};
