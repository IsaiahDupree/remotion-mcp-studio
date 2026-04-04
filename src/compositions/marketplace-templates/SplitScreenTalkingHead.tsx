import React from 'react';
import {
  AbsoluteFill,
  useCurrentFrame,
  useVideoConfig,
  interpolate,
  spring,
  Sequence,
  OffthreadVideo,
} from 'remotion';
import { z } from 'zod';
import { loadFont as loadInter } from '@remotion/google-fonts/Inter';
import { loadFont as loadPoppins } from '@remotion/google-fonts/Poppins';
import { loadFont as loadFiraCode } from '@remotion/google-fonts/FiraCode';

// =============================================================================
// SplitScreenTalkingHead — Avatar + content split
// 1080x1920 vertical, dynamic duration
// =============================================================================

const inter = loadInter('normal', { weights: ['600', '700', '800'] });
const poppins = loadPoppins('normal', { weights: ['400', '500', '600'] });
const firaCode = loadFiraCode('normal', { weights: ['400', '500'] });

// ── Zod Schema ───────────────────────────────────────────────────────────────

const wordTimingSchema = z.object({
  word: z.string(),
  start: z.number().describe('Start time in seconds'),
  end: z.number().describe('End time in seconds'),
});

const bulletContentSchema = z.object({
  type: z.literal('bullets'),
  items: z.array(z.string()),
});

const imageContentSchema = z.object({
  type: z.literal('image'),
  imageUrl: z.string().url(),
  caption: z.string().optional(),
});

const codeContentSchema = z.object({
  type: z.literal('code'),
  code: z.string(),
  language: z.string().default('typescript'),
});

const chartContentSchema = z.object({
  type: z.literal('chart'),
  data: z.array(
    z.object({
      label: z.string(),
      value: z.number(),
      color: z.string().default('#6366f1'),
    })
  ),
});

const contentDataSchema = z.discriminatedUnion('type', [
  bulletContentSchema,
  imageContentSchema,
  codeContentSchema,
  chartContentSchema,
]);

export const splitScreenTalkingHeadSchema = z.object({
  avatarVideoUrl: z.string().url().describe('Avatar video URL'),
  contentData: contentDataSchema.default({
    type: 'bullets',
    items: [
      'Increased conversion by 40%',
      'Reduced churn to under 5%',
      'Scaled to 10M users',
      'Revenue grew 3x YoY',
    ],
  }),
  title: z.string().default('Key Results'),
  captionWords: z.array(wordTimingSchema).default([
    { word: 'Here', start: 0.2, end: 0.5 },
    { word: 'are', start: 0.5, end: 0.7 },
    { word: 'the', start: 0.7, end: 0.9 },
    { word: 'key', start: 0.9, end: 1.2 },
    { word: 'results', start: 1.2, end: 1.8 },
    { word: 'from', start: 1.8, end: 2.1 },
    { word: 'this', start: 2.1, end: 2.3 },
    { word: 'quarter.', start: 2.3, end: 2.9 },
  ]),
  layout: z
    .enum(['left', 'right'])
    .default('left')
    .describe('Avatar position: left or right'),
  accentColor: z.string().default('#6366f1'),
});

export type SplitScreenTalkingHeadProps = z.infer<typeof splitScreenTalkingHeadSchema>;

export const splitScreenTalkingHeadDefaultProps: SplitScreenTalkingHeadProps = {
  avatarVideoUrl: 'https://placehold.co/540x960/222/fff?text=Avatar',
  contentData: {
    type: 'bullets',
    items: [
      'Increased conversion by 40%',
      'Reduced churn to under 5%',
      'Scaled to 10M users',
      'Revenue grew 3x YoY',
    ],
  },
  title: 'Key Results',
  captionWords: [
    { word: 'Here', start: 0.2, end: 0.5 },
    { word: 'are', start: 0.5, end: 0.7 },
    { word: 'the', start: 0.7, end: 0.9 },
    { word: 'key', start: 0.9, end: 1.2 },
    { word: 'results', start: 1.2, end: 1.8 },
    { word: 'from', start: 1.8, end: 2.1 },
    { word: 'this', start: 2.1, end: 2.3 },
    { word: 'quarter.', start: 2.3, end: 2.9 },
  ],
  layout: 'left',
  accentColor: '#6366f1',
};

// ── Bullet List Content ──────────────────────────────────────────────────────

const BulletContent: React.FC<{
  items: string[];
  accentColor: string;
}> = ({ items, accentColor }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
      {items.map((item, i) => {
        const delay = 20 + i * 25;
        const slideIn = spring({
          frame: Math.max(0, frame - delay),
          fps,
          config: { damping: 14, stiffness: 80 },
        });
        const opacity = interpolate(
          frame,
          [delay, delay + 10],
          [0, 1],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );

        return (
          <div
            key={i}
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 14,
              opacity,
              transform: `translateX(${(1 - slideIn) * 40}px)`,
            }}
          >
            <div
              style={{
                width: 10,
                height: 10,
                borderRadius: '50%',
                background: accentColor,
                marginTop: 10,
                flexShrink: 0,
                boxShadow: `0 0 10px ${accentColor}66`,
              }}
            />
            <span
              style={{
                fontFamily: poppins.fontFamily,
                fontWeight: 500,
                fontSize: 26,
                color: '#ffffff',
                lineHeight: 1.4,
              }}
            >
              {item}
            </span>
          </div>
        );
      })}
    </div>
  );
};

// ── Code Content ─────────────────────────────────────────────────────────────

const CodeContent: React.FC<{ code: string }> = ({ code }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const lines = code.split('\n');
  const visibleLines = Math.floor(
    interpolate(frame, [20, 20 + lines.length * 8], [0, lines.length], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    })
  );

  return (
    <div
      style={{
        background: '#1e1e2e',
        borderRadius: 16,
        padding: 24,
        border: '1px solid rgba(255,255,255,0.1)',
        overflow: 'hidden',
      }}
    >
      {/* Window dots */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#ff5f57' }} />
        <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#febc2e' }} />
        <div style={{ width: 12, height: 12, borderRadius: '50%', background: '#28c840' }} />
      </div>
      <pre
        style={{
          fontFamily: firaCode.fontFamily,
          fontSize: 18,
          color: '#cdd6f4',
          margin: 0,
          lineHeight: 1.6,
          whiteSpace: 'pre-wrap',
        }}
      >
        {lines.slice(0, visibleLines).join('\n')}
        {visibleLines < lines.length && Math.floor(frame / 8) % 2 === 0 && (
          <span style={{ color: '#89b4fa' }}>|</span>
        )}
      </pre>
    </div>
  );
};

// ── Chart Content ────────────────────────────────────────────────────────────

const ChartContent: React.FC<{
  data: Array<{ label: string; value: number; color: string }>;
}> = ({ data }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const maxVal = Math.max(...data.map((d) => d.value));

  return (
    <div style={{ display: 'flex', alignItems: 'flex-end', gap: 16, height: 300 }}>
      {data.map((item, i) => {
        const delay = 20 + i * 15;
        const heightProg = spring({
          frame: Math.max(0, frame - delay),
          fps,
          config: { damping: 15, stiffness: 60 },
        });
        const barHeight = (item.value / maxVal) * 260 * heightProg;

        return (
          <div
            key={i}
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              flex: 1,
            }}
          >
            <span
              style={{
                fontFamily: inter.fontFamily,
                fontWeight: 700,
                fontSize: 20,
                color: item.color,
                marginBottom: 8,
              }}
            >
              {Math.round(item.value * heightProg)}
            </span>
            <div
              style={{
                width: '100%',
                height: barHeight,
                background: `linear-gradient(180deg, ${item.color}, ${item.color}88)`,
                borderRadius: '8px 8px 0 0',
                boxShadow: `0 0 20px ${item.color}33`,
              }}
            />
            <span
              style={{
                fontFamily: poppins.fontFamily,
                fontWeight: 500,
                fontSize: 16,
                color: 'rgba(255,255,255,0.6)',
                marginTop: 8,
                textAlign: 'center',
              }}
            >
              {item.label}
            </span>
          </div>
        );
      })}
    </div>
  );
};

// ── Captions Overlay ─────────────────────────────────────────────────────────

const Captions: React.FC<{
  words: SplitScreenTalkingHeadProps['captionWords'];
}> = ({ words }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  // Show a window of words around current time
  const activeWords = words.filter(
    (w) => w.start <= currentTime + 0.1 && w.end >= currentTime - 2
  );

  if (activeWords.length === 0) return null;

  return (
    <div
      style={{
        position: 'absolute',
        bottom: 60,
        left: 40,
        right: 40,
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'center',
        gap: '4px 8px',
        padding: '16px 24px',
        background: 'rgba(0,0,0,0.7)',
        backdropFilter: 'blur(10px)',
        borderRadius: 16,
      }}
    >
      {activeWords.map((w, i) => {
        const isActive = currentTime >= w.start && currentTime <= w.end;
        return (
          <span
            key={`${w.word}-${i}`}
            style={{
              fontFamily: inter.fontFamily,
              fontWeight: isActive ? 800 : 600,
              fontSize: 28,
              color: isActive ? '#ffffff' : 'rgba(255,255,255,0.5)',
              transition: 'color 0.1s',
            }}
          >
            {w.word}
          </span>
        );
      })}
    </div>
  );
};

// ── Main Component ───────────────────────────────────────────────────────────

export const SplitScreenTalkingHead: React.FC<SplitScreenTalkingHeadProps> = ({
  avatarVideoUrl,
  contentData,
  title,
  captionWords,
  layout,
  accentColor,
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const isAvatarLeft = layout === 'left';

  // Title animation
  const titleScale = spring({
    frame,
    fps,
    config: { damping: 12, stiffness: 80 },
  });
  const titleOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Divider line animation
  const dividerHeight = interpolate(frame, [10, 40], [0, 100], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Determine if the avatarVideoUrl is a placeholder/image vs real video
  const isPlaceholder =
    avatarVideoUrl.includes('placehold') || avatarVideoUrl.endsWith('.png') || avatarVideoUrl.endsWith('.jpg');

  const avatarSection = (
    <div
      style={{
        position: 'relative',
        width: '100%',
        height: '50%',
        overflow: 'hidden',
      }}
    >
      {isPlaceholder ? (
        <div
          style={{
            width: '100%',
            height: '100%',
            background: '#222',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontFamily: inter.fontFamily,
            fontSize: 28,
            color: 'rgba(255,255,255,0.3)',
          }}
        >
          Avatar Video
        </div>
      ) : (
        <OffthreadVideo
          src={avatarVideoUrl}
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        />
      )}

      {/* Captions overlay */}
      <Captions words={captionWords} />
    </div>
  );

  const contentSection = (
    <div
      style={{
        width: '100%',
        height: '50%',
        background: '#111118',
        display: 'flex',
        flexDirection: 'column',
        padding: '40px 40px',
      }}
    >
      {/* Title */}
      <div
        style={{
          fontFamily: inter.fontFamily,
          fontWeight: 800,
          fontSize: 40,
          color: '#ffffff',
          opacity: titleOpacity,
          transform: `scale(${titleScale})`,
          marginBottom: 8,
        }}
      >
        {title}
      </div>

      {/* Accent line */}
      <div
        style={{
          width: 80,
          height: 3,
          background: accentColor,
          borderRadius: 2,
          marginBottom: 28,
        }}
      />

      {/* Content area */}
      <div style={{ flex: 1, overflow: 'hidden' }}>
        {contentData.type === 'bullets' && (
          <BulletContent items={contentData.items} accentColor={accentColor} />
        )}
        {contentData.type === 'code' && <CodeContent code={contentData.code} />}
        {contentData.type === 'chart' && <ChartContent data={contentData.data} />}
        {contentData.type === 'image' && (
          <div
            style={{
              width: '100%',
              height: '100%',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
            }}
          >
            <img
              src={contentData.imageUrl}
              style={{
                maxWidth: '100%',
                maxHeight: '80%',
                objectFit: 'contain',
                borderRadius: 12,
              }}
            />
            {contentData.caption && (
              <span
                style={{
                  fontFamily: poppins.fontFamily,
                  fontWeight: 400,
                  fontSize: 22,
                  color: 'rgba(255,255,255,0.6)',
                  marginTop: 12,
                }}
              >
                {contentData.caption}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );

  return (
    <AbsoluteFill style={{ background: '#0a0a0f' }}>
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          height: '100%',
          width: '100%',
        }}
      >
        {isAvatarLeft ? (
          <>
            {avatarSection}
            {contentSection}
          </>
        ) : (
          <>
            {contentSection}
            {avatarSection}
          </>
        )}
      </div>

      {/* Divider line */}
      <div
        style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: `${dividerHeight}%`,
          height: 2,
          background: `linear-gradient(90deg, transparent, ${accentColor}, transparent)`,
        }}
      />
    </AbsoluteFill>
  );
};
