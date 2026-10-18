import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Sequence,
  Img,
} from 'remotion';
import { z } from 'zod';
import { loadFont as loadInter } from '@remotion/google-fonts/Inter';
import { loadFont as loadPoppins } from '@remotion/google-fonts/Poppins';

// =============================================================================
// TestimonialCard — Customer testimonial video
// 1080x1080 square (Instagram) @ 30fps, ~8 seconds (240 frames)
// =============================================================================

const inter = loadInter('normal', { weights: ['600', '700', '800', '900'] });
const poppins = loadPoppins('normal', { weights: ['400', '500', '600'] });

// ── Zod Schema ───────────────────────────────────────────────────────────────

export const testimonialCardSchema = z.object({
  quote: z.string().default(
    'This product completely transformed our workflow. We went from spending hours on manual tasks to automating everything in minutes.'
  ),
  authorName: z.string().default('Sarah Chen'),
  authorTitle: z.string().default('VP of Engineering, TechCorp'),
  authorImageUrl: z
    .string()
    .url()
    .default('https://placehold.co/120x120/6366f1/fff?text=SC'),
  rating: z.number().min(1).max(5).default(5).describe('Star rating 1-5'),
  companyLogo: z
    .string()
    .url()
    .optional()
    .default('https://placehold.co/160x40/fff/333?text=TechCorp'),
  accentColor: z.string().default('#6366f1'),
});

export type TestimonialCardProps = z.infer<typeof testimonialCardSchema>;

export const testimonialCardDefaultProps: TestimonialCardProps = {
  quote:
    'This product completely transformed our workflow. We went from spending hours on manual tasks to automating everything in minutes.',
  authorName: 'Sarah Chen',
  authorTitle: 'VP of Engineering, TechCorp',
  authorImageUrl: 'https://placehold.co/120x120/6366f1/fff?text=SC',
  rating: 5,
  companyLogo: 'https://placehold.co/160x40/fff/333?text=TechCorp',
  accentColor: '#6366f1',
};

// ── Star Component ───────────────────────────────────────────────────────────

const Star: React.FC<{
  filled: boolean;
  fillProgress: number;
  size: number;
  color: string;
}> = ({ filled, fillProgress, size, color }) => {
  const points = React.useMemo(() => {
    // 5-pointed star SVG path
    const outerRadius = size / 2;
    const innerRadius = outerRadius * 0.4;
    const cx = size / 2;
    const cy = size / 2;
    const pts: string[] = [];
    for (let i = 0; i < 10; i++) {
      const r = i % 2 === 0 ? outerRadius : innerRadius;
      const angle = (Math.PI / 2) * -1 + (Math.PI / 5) * i;
      pts.push(`${cx + r * Math.cos(angle)},${cy + r * Math.sin(angle)}`);
    }
    return pts.join(' ');
  }, [size]);

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {/* Background star */}
      <polygon points={points} fill="rgba(255,255,255,0.15)" />
      {/* Filled star with clip */}
      {filled && (
        <g>
          <clipPath id={`star-clip-${Math.random().toString(36).slice(2)}`}>
            <rect x={0} y={0} width={size * fillProgress} height={size} />
          </clipPath>
          <polygon
            points={points}
            fill={color}
            clipPath={`url(#star-clip-${Math.random().toString(36).slice(2)})`}
            style={{ filter: `drop-shadow(0 0 6px ${color}66)` }}
          />
          {/* Full fill fallback — simpler approach */}
          <polygon
            points={points}
            fill={color}
            opacity={fillProgress}
            style={{ filter: `drop-shadow(0 0 6px ${color}66)` }}
          />
        </g>
      )}
    </svg>
  );
};

const StarRating: React.FC<{
  rating: number;
  accentColor: string;
  startFrame: number;
}> = ({ rating, accentColor, startFrame }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const starSize = 48;

  return (
    <div style={{ display: 'flex', gap: 8 }}>
      {Array.from({ length: 5 }, (_, i) => {
        const delay = startFrame + i * 8;
        const fillProg = spring({
          frame: Math.max(0, frame - delay),
          fps,
          config: { damping: 8, stiffness: 120 },
        });
        const scale = spring({
          frame: Math.max(0, frame - delay),
          fps,
          config: { damping: 6, stiffness: 150, mass: 0.5 },
        });

        return (
          <div
            key={i}
            style={{
              transform: `scale(${i < rating ? scale : 0.8})`,
              display: 'inline-block',
            }}
          >
            <Star
              filled={i < rating}
              fillProgress={fillProg}
              size={starSize}
              color={accentColor}
            />
          </div>
        );
      })}
    </div>
  );
};

// ── Quote Marks ──────────────────────────────────────────────────────────────

const QuoteMarks: React.FC<{ accentColor: string }> = ({ accentColor }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({
    frame,
    fps,
    config: { damping: 10, stiffness: 80 },
  });
  const opacity = interpolate(frame, [0, 15], [0, 0.15], {
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        top: 140,
        left: 60,
        fontFamily: 'Georgia, serif',
        fontSize: 240,
        color: accentColor,
        opacity,
        transform: `scale(${scale})`,
        lineHeight: 1,
        userSelect: 'none',
      }}
    >
      &ldquo;
    </div>
  );
};

// ── Main Component ───────────────────────────────────────────────────────────

export const TestimonialCard: React.FC<TestimonialCardProps> = ({
  quote,
  authorName,
  authorTitle,
  authorImageUrl,
  rating,
  companyLogo,
  accentColor,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Word-by-word text reveal
  const words = quote.split(' ');
  const typeStartFrame = 30;
  const wordsPerFrame = 0.12; // ~3.6 words per second at 30fps
  const visibleWords = Math.floor(
    interpolate(
      frame - typeStartFrame,
      [0, words.length / wordsPerFrame],
      [0, words.length],
      { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
    )
  );

  // Stars start
  const starsFrame = 20;

  // Author info slide up
  const authorFrame = typeStartFrame + Math.round(words.length / wordsPerFrame) + 15;
  const authorSlide = spring({
    frame: Math.max(0, frame - authorFrame),
    fps,
    config: { damping: 14, stiffness: 80 },
  });
  const authorOpacity = interpolate(
    frame,
    [authorFrame, authorFrame + 10],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Company logo
  const logoFrame = authorFrame + 20;
  const logoOpacity = interpolate(
    frame,
    [logoFrame, logoFrame + 15],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Final fade
  const fadeOut = interpolate(
    frame,
    [durationInFrames - 20, durationInFrames],
    [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Background subtle animation
  const bgShift = interpolate(frame, [0, durationInFrames], [0, 20]);

  return (
    <AbsoluteFill
      style={{
        background: `
          radial-gradient(ellipse at 80% 20%, ${accentColor}15 0%, transparent 50%),
          radial-gradient(ellipse at 20% 80%, ${accentColor}10 0%, transparent 50%),
          linear-gradient(${135 + bgShift}deg, #0f0f1a 0%, #1a1a2e 50%, #0f0f1a 100%)
        `,
        opacity: fadeOut,
      }}
    >
      {/* Decorative quote marks */}
      <QuoteMarks accentColor={accentColor} />

      {/* Main content */}
      <div
        style={{
          position: 'absolute',
          top: 100,
          left: 70,
          right: 70,
          bottom: 100,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Star rating */}
        <Sequence from={starsFrame}>
          <div style={{ marginBottom: 40, marginTop: 60 }}>
            <StarRating
              rating={rating}
              accentColor={accentColor === '#6366f1' ? '#fbbf24' : accentColor}
              startFrame={0}
            />
          </div>
        </Sequence>

        {/* Quote text */}
        <div
          style={{
            fontFamily: poppins.fontFamily,
            fontWeight: 500,
            fontSize: 36,
            color: '#ffffff',
            lineHeight: 1.5,
            flex: 1,
            display: 'flex',
            flexWrap: 'wrap',
            alignContent: 'flex-start',
            gap: '4px 8px',
            marginTop: 20,
          }}
        >
          {words.map((word, i) => {
            const isVisible = i < visibleWords;
            const justAppeared =
              i === visibleWords - 1 || i === visibleWords - 2;
            return (
              <span
                key={i}
                style={{
                  opacity: isVisible ? 1 : 0,
                  color: justAppeared ? '#ffffff' : 'rgba(255,255,255,0.85)',
                  fontWeight: justAppeared ? 700 : 500,
                }}
              >
                {word}
              </span>
            );
          })}
        </div>

        {/* Author info */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 20,
            opacity: authorOpacity,
            transform: `translateY(${(1 - authorSlide) * 30}px)`,
            marginTop: 'auto',
          }}
        >
          <Img
            src={authorImageUrl}
            style={{
              width: 64,
              height: 64,
              borderRadius: '50%',
              objectFit: 'cover',
              border: `3px solid ${accentColor}`,
            }}
          />
          <div>
            <div
              style={{
                fontFamily: inter.fontFamily,
                fontWeight: 700,
                fontSize: 26,
                color: '#ffffff',
              }}
            >
              {authorName}
            </div>
            <div
              style={{
                fontFamily: poppins.fontFamily,
                fontWeight: 400,
                fontSize: 20,
                color: 'rgba(255,255,255,0.5)',
                marginTop: 2,
              }}
            >
              {authorTitle}
            </div>
          </div>
        </div>

        {/* Company logo */}
        {companyLogo && (
          <div
            style={{
              marginTop: 24,
              opacity: logoOpacity,
              display: 'flex',
              justifyContent: 'flex-start',
            }}
          >
            <Img
              src={companyLogo}
              style={{
                height: 32,
                objectFit: 'contain',
                filter: 'brightness(0.7) contrast(0.8)',
              }}
            />
          </div>
        )}
      </div>

      {/* Bottom accent bar */}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: 4,
          background: `linear-gradient(90deg, ${accentColor}, ${accentColor}66, ${accentColor})`,
        }}
      />
    </AbsoluteFill>
  );
};
