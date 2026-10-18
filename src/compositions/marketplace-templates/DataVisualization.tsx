import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
} from 'remotion';
import { z } from 'zod';
import { loadFont as loadInter } from '@remotion/google-fonts/Inter';
import { loadFont as loadPoppins } from '@remotion/google-fonts/Poppins';

// =============================================================================
// DataVisualization — Animated bar/stat counter (vertical 1080x1920 @ 30fps)
// ~10 seconds (300 frames)
// =============================================================================

const inter = loadInter('normal', { weights: ['600', '700', '800', '900'] });
const poppins = loadPoppins('normal', { weights: ['400', '500', '600'] });

// ── Zod Schema ───────────────────────────────────────────────────────────────

const statItemSchema = z.object({
  label: z.string(),
  value: z.number(),
  maxValue: z.number(),
  color: z.string().default('#6366f1'),
});

export const dataVisualizationSchema = z.object({
  title: z.string().default('Q4 Performance'),
  stats: z.array(statItemSchema).default([
    { label: 'Revenue', value: 84, maxValue: 100, color: '#6366f1' },
    { label: 'Users', value: 67, maxValue: 100, color: '#22c55e' },
    { label: 'Conversion', value: 42, maxValue: 100, color: '#f59e0b' },
    { label: 'Retention', value: 91, maxValue: 100, color: '#ec4899' },
  ]),
  style: z
    .enum(['bars', 'circles', 'counters'])
    .default('bars')
    .describe('Visualization style'),
  accentColor: z.string().default('#6366f1'),
});

export type DataVisualizationProps = z.infer<typeof dataVisualizationSchema>;

export const dataVisualizationDefaultProps: DataVisualizationProps = {
  title: 'Q4 Performance',
  stats: [
    { label: 'Revenue', value: 84, maxValue: 100, color: '#6366f1' },
    { label: 'Users', value: 67, maxValue: 100, color: '#22c55e' },
    { label: 'Conversion', value: 42, maxValue: 100, color: '#f59e0b' },
    { label: 'Retention', value: 91, maxValue: 100, color: '#ec4899' },
  ],
  style: 'bars',
  accentColor: '#6366f1',
};

// ── Bar Style ────────────────────────────────────────────────────────────────

const BarChart: React.FC<{
  stats: DataVisualizationProps['stats'];
  staggerDelay: number;
}> = ({ stats, staggerDelay }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 40, width: '100%' }}>
      {stats.map((stat, i) => {
        const delay = 60 + i * staggerDelay;
        const progress = spring({
          frame: Math.max(0, frame - delay),
          fps,
          config: { damping: 20, stiffness: 40, mass: 1 },
        });
        const labelOpacity = interpolate(
          frame,
          [delay - 10, delay],
          [0, 1],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );
        const barWidth = (stat.value / stat.maxValue) * 100 * progress;
        const countValue = Math.round(stat.value * progress);

        return (
          <div key={i} style={{ opacity: labelOpacity }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                marginBottom: 12,
              }}
            >
              <span
                style={{
                  fontFamily: poppins.fontFamily,
                  fontWeight: 500,
                  fontSize: 30,
                  color: 'rgba(255,255,255,0.8)',
                }}
              >
                {stat.label}
              </span>
              <span
                style={{
                  fontFamily: inter.fontFamily,
                  fontWeight: 800,
                  fontSize: 34,
                  color: stat.color,
                }}
              >
                {countValue}%
              </span>
            </div>
            <div
              style={{
                width: '100%',
                height: 24,
                background: 'rgba(255,255,255,0.08)',
                borderRadius: 12,
                overflow: 'hidden',
              }}
            >
              <div
                style={{
                  width: `${barWidth}%`,
                  height: '100%',
                  background: `linear-gradient(90deg, ${stat.color}, ${stat.color}cc)`,
                  borderRadius: 12,
                  boxShadow: `0 0 20px ${stat.color}44`,
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};

// ── Circle Style ─────────────────────────────────────────────────────────────

const CircleChart: React.FC<{
  stats: DataVisualizationProps['stats'];
  staggerDelay: number;
}> = ({ stats, staggerDelay }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const circleSize = 180;
  const strokeWidth = 14;
  const radius = (circleSize - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  return (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: 40,
        justifyContent: 'center',
      }}
    >
      {stats.map((stat, i) => {
        const delay = 60 + i * staggerDelay;
        const progress = spring({
          frame: Math.max(0, frame - delay),
          fps,
          config: { damping: 20, stiffness: 40, mass: 1 },
        });
        const labelOpacity = interpolate(
          frame,
          [delay - 10, delay],
          [0, 1],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );
        const fraction = (stat.value / stat.maxValue) * progress;
        const dashOffset = circumference * (1 - fraction);
        const countValue = Math.round(stat.value * progress);

        return (
          <div
            key={i}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              opacity: labelOpacity,
              width: circleSize + 20,
            }}
          >
            <svg
              width={circleSize}
              height={circleSize}
              style={{ transform: 'rotate(-90deg)' }}
            >
              <circle
                cx={circleSize / 2}
                cy={circleSize / 2}
                r={radius}
                fill="none"
                stroke="rgba(255,255,255,0.08)"
                strokeWidth={strokeWidth}
              />
              <circle
                cx={circleSize / 2}
                cy={circleSize / 2}
                r={radius}
                fill="none"
                stroke={stat.color}
                strokeWidth={strokeWidth}
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={dashOffset}
                style={{ filter: `drop-shadow(0 0 8px ${stat.color}66)` }}
              />
            </svg>
            <span
              style={{
                fontFamily: inter.fontFamily,
                fontWeight: 800,
                fontSize: 38,
                color: stat.color,
                marginTop: -circleSize / 2 - 20,
                position: 'relative',
                transform: 'rotate(0deg)',
              }}
            >
              {countValue}%
            </span>
            <span
              style={{
                fontFamily: poppins.fontFamily,
                fontWeight: 500,
                fontSize: 24,
                color: 'rgba(255,255,255,0.7)',
                marginTop: circleSize / 2 - 20,
              }}
            >
              {stat.label}
            </span>
          </div>
        );
      })}
    </div>
  );
};

// ── Counter Style ────────────────────────────────────────────────────────────

const CounterDisplay: React.FC<{
  stats: DataVisualizationProps['stats'];
  staggerDelay: number;
}> = ({ stats, staggerDelay }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 48, width: '100%' }}>
      {stats.map((stat, i) => {
        const delay = 60 + i * staggerDelay;
        const progress = spring({
          frame: Math.max(0, frame - delay),
          fps,
          config: { damping: 20, stiffness: 40, mass: 1 },
        });
        const scale = spring({
          frame: Math.max(0, frame - delay),
          fps,
          config: { damping: 12, stiffness: 100 },
        });
        const labelOpacity = interpolate(
          frame,
          [delay - 10, delay],
          [0, 1],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );
        const countValue = Math.round(stat.value * progress);

        return (
          <div
            key={i}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              opacity: labelOpacity,
            }}
          >
            <span
              style={{
                fontFamily: inter.fontFamily,
                fontWeight: 900,
                fontSize: 80,
                color: stat.color,
                transform: `scale(${scale})`,
                display: 'inline-block',
                textShadow: `0 0 40px ${stat.color}44`,
              }}
            >
              {countValue}
              <span style={{ fontSize: 48 }}>%</span>
            </span>
            <span
              style={{
                fontFamily: poppins.fontFamily,
                fontWeight: 500,
                fontSize: 28,
                color: 'rgba(255,255,255,0.6)',
                marginTop: 4,
                textTransform: 'uppercase',
                letterSpacing: 3,
              }}
            >
              {stat.label}
            </span>
          </div>
        );
      })}
    </div>
  );
};

// ── Main Component ───────────────────────────────────────────────────────────

export const DataVisualization: React.FC<DataVisualizationProps> = ({
  title,
  stats,
  style,
  accentColor,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Title animation
  const titleScale = spring({
    frame,
    fps,
    config: { damping: 12, stiffness: 80 },
  });
  const titleOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Decorative line under title
  const lineWidth = interpolate(frame, [15, 45], [0, 200], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Stagger delay between items
  const staggerDelay = 30;

  // Final fade
  const fadeOut = interpolate(
    frame,
    [durationInFrames - 20, durationInFrames],
    [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  return (
    <AbsoluteFill
      style={{
        background: 'linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 50%, #0f0f1a 100%)',
        opacity: fadeOut,
      }}
    >
      {/* Subtle grid overlay */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: `
            linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px)
          `,
          backgroundSize: '60px 60px',
        }}
      />

      {/* Content */}
      <div
        style={{
          position: 'absolute',
          top: 120,
          left: 60,
          right: 60,
          bottom: 120,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        {/* Title */}
        <div
          style={{
            fontFamily: inter.fontFamily,
            fontWeight: 800,
            fontSize: 56,
            color: '#ffffff',
            opacity: titleOpacity,
            transform: `scale(${titleScale})`,
            textAlign: 'center',
            marginBottom: 12,
          }}
        >
          {title}
        </div>

        {/* Accent line */}
        <div
          style={{
            width: lineWidth,
            height: 4,
            background: `linear-gradient(90deg, transparent, ${accentColor}, transparent)`,
            borderRadius: 2,
            marginBottom: 60,
          }}
        />

        {/* Charts */}
        <div style={{ width: '100%', flex: 1, display: 'flex', alignItems: 'center' }}>
          {style === 'bars' && (
            <BarChart stats={stats} staggerDelay={staggerDelay} />
          )}
          {style === 'circles' && (
            <CircleChart stats={stats} staggerDelay={staggerDelay} />
          )}
          {style === 'counters' && (
            <CounterDisplay stats={stats} staggerDelay={staggerDelay} />
          )}
        </div>
      </div>
    </AbsoluteFill>
  );
};
