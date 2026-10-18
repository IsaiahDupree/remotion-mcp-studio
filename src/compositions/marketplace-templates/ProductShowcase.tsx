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
// ProductShowcase — E-commerce product showcase (vertical 1080x1920 @ 30fps)
// ~15 seconds (450 frames)
// =============================================================================

const inter = loadInter('normal', { weights: ['600', '700', '800', '900'] });
const poppins = loadPoppins('normal', { weights: ['400', '500', '600'] });

// ── Zod Schema ───────────────────────────────────────────────────────────────

export const productShowcaseSchema = z.object({
  productImageUrl: z.string().url().describe('Product image URL'),
  productName: z.string().default('Premium Headphones'),
  price: z.number().min(0).default(79.99),
  originalPrice: z.number().min(0).optional().default(129.99),
  features: z
    .array(z.string())
    .default([
      'Active Noise Cancellation',
      '40-Hour Battery Life',
      'Premium Hi-Fi Sound',
      'Comfortable Memory Foam',
    ]),
  ctaText: z.string().default('Shop Now'),
  brandColor: z.string().default('#1a1a2e'),
  badge: z.string().optional().default('SALE'),
});

export type ProductShowcaseProps = z.infer<typeof productShowcaseSchema>;

export const productShowcaseDefaultProps: ProductShowcaseProps = {
  productImageUrl: 'https://placehold.co/800x800/222/fff?text=Product',
  productName: 'Premium Headphones',
  price: 79.99,
  originalPrice: 129.99,
  features: [
    'Active Noise Cancellation',
    '40-Hour Battery Life',
    'Premium Hi-Fi Sound',
    'Comfortable Memory Foam',
  ],
  ctaText: 'Shop Now',
  brandColor: '#1a1a2e',
  badge: 'SALE',
};

// ── Price Counter ────────────────────────────────────────────────────────────

const AnimatedPrice: React.FC<{
  price: number;
  startFrame: number;
  color: string;
}> = ({ price, startFrame, color }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = interpolate(
    frame - startFrame,
    [0, 40],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const displayPrice = (price * progress).toFixed(2);
  const scale = spring({
    frame: Math.max(0, frame - startFrame),
    fps,
    config: { damping: 10, stiffness: 100 },
  });

  return (
    <span
      style={{
        fontFamily: inter.fontFamily,
        fontWeight: 900,
        fontSize: 72,
        color,
        transform: `scale(${scale})`,
        display: 'inline-block',
      }}
    >
      ${displayPrice}
    </span>
  );
};

// ── Badge ────────────────────────────────────────────────────────────────────

const Badge: React.FC<{ text: string; color: string }> = ({ text, color }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({
    frame,
    fps,
    config: { damping: 8, stiffness: 120 },
  });

  const rotation = interpolate(frame, [0, 15], [-12, -8], {
    extrapolateRight: 'clamp',
  });

  return (
    <div
      style={{
        position: 'absolute',
        top: 40,
        right: 40,
        background: color,
        color: '#fff',
        fontFamily: inter.fontFamily,
        fontWeight: 800,
        fontSize: 28,
        padding: '12px 24px',
        borderRadius: 12,
        transform: `scale(${scale}) rotate(${rotation}deg)`,
        boxShadow: `0 4px 20px ${color}66`,
        zIndex: 10,
      }}
    >
      {text}
    </div>
  );
};

// ── Main Component ───────────────────────────────────────────────────────────

export const ProductShowcase: React.FC<ProductShowcaseProps> = ({
  productImageUrl,
  productName,
  price,
  originalPrice,
  features,
  ctaText,
  brandColor,
  badge,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  // Ken Burns on product image
  const imageScale = interpolate(frame, [0, durationInFrames], [1.0, 1.2], {
    extrapolateRight: 'clamp',
  });
  const imageX = interpolate(frame, [0, durationInFrames], [0, -30]);
  const imageY = interpolate(frame, [0, durationInFrames], [0, -15]);

  // Product image entrance
  const imageOpacity = interpolate(frame, [0, 20], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Product name
  const nameFrame = 30;
  const nameSlide = spring({
    frame: Math.max(0, frame - nameFrame),
    fps,
    config: { damping: 14, stiffness: 80 },
  });
  const nameOpacity = interpolate(frame, [nameFrame, nameFrame + 10], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Price section start
  const priceFrame = 90;

  // Original price strikethrough
  const originalPriceOpacity = interpolate(
    frame,
    [priceFrame, priceFrame + 15],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // CTA button
  const ctaFrame = 330;
  const ctaScale = spring({
    frame: Math.max(0, frame - ctaFrame),
    fps,
    config: { damping: 10, stiffness: 100 },
  });

  // Pulse on CTA
  const ctaPulse =
    frame > ctaFrame + 30
      ? 1 + Math.sin((frame - ctaFrame) * 0.15) * 0.03
      : 1;

  // Final fade out
  const fadeOut = interpolate(
    frame,
    [durationInFrames - 20, durationInFrames],
    [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(180deg, ${brandColor} 0%, ${brandColor}ee 100%)`,
        opacity: fadeOut,
      }}
    >
      {/* Badge */}
      {badge && (
        <Sequence from={5}>
          <Badge text={badge} color="#ef4444" />
        </Sequence>
      )}

      {/* Product image — top half */}
      <div
        style={{
          position: 'absolute',
          top: 80,
          left: 0,
          right: 0,
          height: '45%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          overflow: 'hidden',
          opacity: imageOpacity,
        }}
      >
        <Img
          src={productImageUrl}
          style={{
            width: '70%',
            height: '100%',
            objectFit: 'contain',
            transform: `scale(${imageScale}) translate(${imageX}px, ${imageY}px)`,
            filter: 'drop-shadow(0 20px 40px rgba(0,0,0,0.4))',
          }}
        />
      </div>

      {/* Content — bottom half */}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: '52%',
          padding: '0 60px 80px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'flex-start',
        }}
      >
        {/* Product name */}
        <div
          style={{
            fontFamily: inter.fontFamily,
            fontWeight: 800,
            fontSize: 52,
            color: '#ffffff',
            opacity: nameOpacity,
            transform: `translateY(${(1 - nameSlide) * 30}px)`,
            lineHeight: 1.1,
            marginBottom: 20,
          }}
        >
          {productName}
        </div>

        {/* Price section */}
        <Sequence from={priceFrame}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 16, marginBottom: 32 }}>
            <AnimatedPrice price={price} startFrame={0} color="#22c55e" />
            {originalPrice && originalPrice > price && (
              <span
                style={{
                  fontFamily: inter.fontFamily,
                  fontWeight: 600,
                  fontSize: 36,
                  color: 'rgba(255,255,255,0.4)',
                  textDecoration: 'line-through',
                  opacity: originalPriceOpacity,
                }}
              >
                ${originalPrice.toFixed(2)}
              </span>
            )}
          </div>
        </Sequence>

        {/* Features */}
        {features.map((feature, i) => {
          const featureFrame = 150 + i * 30;
          const slideIn = spring({
            frame: Math.max(0, frame - featureFrame),
            fps,
            config: { damping: 14, stiffness: 80 },
          });
          const featureOpacity = interpolate(
            frame,
            [featureFrame, featureFrame + 10],
            [0, 1],
            { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
          );
          return (
            <div
              key={i}
              style={{
                fontFamily: poppins.fontFamily,
                fontWeight: 500,
                fontSize: 30,
                color: 'rgba(255,255,255,0.9)',
                opacity: featureOpacity,
                transform: `translateX(${(1 - slideIn) * 60}px)`,
                marginBottom: 14,
                display: 'flex',
                alignItems: 'center',
                gap: 12,
              }}
            >
              <span style={{ color: '#22c55e', fontSize: 24 }}>&#10003;</span>
              {feature}
            </div>
          );
        })}

        {/* CTA Button */}
        <Sequence from={ctaFrame}>
          <div
            style={{
              marginTop: 'auto',
              alignSelf: 'center',
              background: '#ffffff',
              color: brandColor,
              fontFamily: inter.fontFamily,
              fontWeight: 800,
              fontSize: 34,
              padding: '20px 64px',
              borderRadius: 60,
              transform: `scale(${ctaScale * ctaPulse})`,
              boxShadow: '0 8px 30px rgba(0,0,0,0.3)',
              textTransform: 'uppercase',
              letterSpacing: 2,
            }}
          >
            {ctaText}
          </div>
        </Sequence>
      </div>
    </AbsoluteFill>
  );
};
