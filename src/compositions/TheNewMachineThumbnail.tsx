import React from 'react';
import {AbsoluteFill} from 'remotion';
import {BRAND} from './TheNewMachineEpisode';

// ──────────────────────────────────────────────────────────────────────────────
// The New Machine — YouTube thumbnail (1280×720).
//
// Brand language:
//   - Hairline grid background
//   - Section-accent glow behind the headline
//   - Bold all-caps headline (Inter Tight 700)
//   - Optional contrast tag (e.g. "OLD MACHINE" / "NEW MACHINE")
//   - Bottom-right wordmark + dot grid bug
//
// Used as a Remotion `still` target. Driven by `pipeline/generate_thumbnail.py`,
// which writes the PNG to `episodes/<slug>/thumbnail.png`. The upload stage
// then attaches it to the YouTube video automatically.
// ──────────────────────────────────────────────────────────────────────────────

export type ThumbnailProps = {
  headline: string;
  contrastTag?: string;          // e.g. "OLD MACHINE" or "NO EMPLOYEES"
  contrastColor?: 'amber' | 'cyan' | 'danger' | 'power';
  episodeId?: string;
};

export const theNewMachineThumbnailDefaultProps: ThumbnailProps = {
  headline: 'The Company\nWith No Employees',
  contrastTag: 'NO EMPLOYEES',
  contrastColor: 'cyan',
  episodeId: 'EP002',
};

const accentMap = {
  amber:  BRAND.amber,
  cyan:   BRAND.cyan,
  danger: BRAND.danger,
  power:  BRAND.power,
};

export const TheNewMachineThumbnail: React.FC<ThumbnailProps> = ({
  headline,
  contrastTag,
  contrastColor = 'cyan',
  episodeId,
}) => {
  const accent = accentMap[contrastColor] ?? BRAND.cyan;

  return (
    <AbsoluteFill
      style={{
        background: BRAND.bg,
        backgroundImage:
          `radial-gradient(circle at 70% 50%, ${accent}22 0%, transparent 55%),` +
          `linear-gradient(${BRAND.bgPanel} 1px, transparent 1px),` +
          `linear-gradient(90deg, ${BRAND.bgPanel} 1px, transparent 1px)`,
        backgroundSize: '100% 100%, 64px 64px, 64px 64px',
        padding: 72,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
      }}
    >
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start'}}>
        {episodeId && (
          <div
            style={{
              fontFamily: BRAND.fontMono,
              fontSize: 22,
              letterSpacing: 6,
              color: BRAND.muted,
            }}
          >
            {episodeId} / THE NEW MACHINE
          </div>
        )}
        {contrastTag && (
          <div
            style={{
              fontFamily: BRAND.fontMono,
              fontSize: 22,
              letterSpacing: 6,
              color: accent,
              border: `1px solid ${accent}`,
              padding: '8px 16px',
              borderRadius: 2,
              boxShadow: `0 0 24px ${accent}55`,
            }}
          >
            {contrastTag}
          </div>
        )}
      </div>

      <div style={{maxWidth: 1100}}>
        <div
          style={{
            fontFamily: BRAND.fontDisplay,
            fontWeight: 700,
            fontSize: 132,
            lineHeight: 0.96,
            letterSpacing: -2,
            color: BRAND.text,
            textShadow: '0 8px 40px rgba(0,0,0,0.95)',
            whiteSpace: 'pre-wrap',
          }}
        >
          {headline}
        </div>
        <div
          style={{
            marginTop: 22,
            width: 180,
            height: 3,
            background: accent,
            boxShadow: `0 0 16px ${accent}`,
          }}
        />
      </div>

      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end'}}>
        <div
          style={{
            fontFamily: BRAND.fontDisplay,
            fontWeight: 700,
            fontSize: 28,
            letterSpacing: 6,
            color: BRAND.text,
          }}
        >
          THE NEW MACHINE
        </div>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 10px)',
            gap: 6,
          }}
        >
          {Array.from({length: 9}).map((_, i) => (
            <div
              key={i}
              style={{
                width: 10,
                height: 10,
                borderRadius: 2,
                background: i === 4 ? accent : BRAND.muted,
                boxShadow: i === 4 ? `0 0 10px ${accent}` : 'none',
              }}
            />
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

export default TheNewMachineThumbnail;
