import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Sequence,
  Video,
  staticFile,
  useVideoConfig,
  interpolate,
  useCurrentFrame,
} from 'remotion';
import { ContentBrief, WordTiming } from './types';
import { getTheme } from './themes';
import { FilmGrain } from '../../components/tiktok-pipeline/FilmGrain';
import { Vignette } from '../../components/tiktok-pipeline/Vignette';
import { WatermarkBadge } from '../../components/tiktok-pipeline/WatermarkBadge';
import { CaptionOverlay } from '../../components/tiktok-pipeline/CaptionOverlay';
import { AudioPulse } from '../../components/tiktok-pipeline/AudioPulse';
import { HookSlam } from '../../components/tiktok-pipeline/HookSlam';
import { BodyContent } from '../../components/tiktok-pipeline/BodyContent';
import { PhoneFrame } from '../../components/tiktok-pipeline/PhoneFrame';
import { OutroSlide } from '../../components/tiktok-pipeline/OutroSlide';
import { PromiseBadge } from '../../components/tiktok-pipeline/PromiseBadge';

interface TikTokVideoProps {
  brief?: ContentBrief;
}

const EVERREACH_SCREENSHOTS = [
  'everreach/screenshots/01-contacts-list.png',
  'everreach/screenshots/02-contact-detail.png',
  'everreach/screenshots/03-voice-note.png',
  'everreach/screenshots/04-search-tags.png',
  'everreach/screenshots/05-warmth-score.png',
  'everreach/screenshots/06-goal-compose.png',
];

const BROLL_VIDEOS = [
  'assets/broll/pexels_1851190.mp4',
];

// Map screenshot to a matching notification message
const SCREENSHOT_NOTIFICATIONS: Record<string, string> = {
  '01-contacts-list.png': '🔥 3 warm leads need follow-up today',
  '02-contact-detail.png': '✅ Sarah replied — respond now',
  '03-voice-note.png': '🎙️ New voice note from a warm contact',
  '04-search-tags.png': '🔍 4 contacts match your follow-up tags',
  '05-warmth-score.png': '📈 Your network warmth score improved',
  '06-goal-compose.png': '💡 AI drafted your next follow-up',
};


export const TikTokVideo: React.FC<TikTokVideoProps> = ({ brief }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  if (!brief) {
    return (
      <AbsoluteFill style={{ backgroundColor: '#0a0a0a', alignItems: 'center', justifyContent: 'center' }}>
        <p style={{ color: '#fff', fontFamily: 'Inter', fontSize: 32 }}>No brief provided</p>
      </AbsoluteFill>
    );
  }

  const theme = getTheme(brief.color_theme);

  // --- Layout: distribute sections across total duration ---
  const totalSec = brief.duration_sec ?? 30;
  const totalFrames = Math.round(totalSec * fps);

  const bodyPoints = brief.body_points ?? [];
  const hasCta = Boolean(brief.cta_text);

  // Time budget (seconds)
  const hookSec = Math.min(5, totalSec * 0.18);
  const outroSec = Math.max(4, totalSec * 0.2);
  const phoneSec = bodyPoints.length > 0 ? Math.min(6, totalSec * 0.18) : 0;
  const bodySec = totalSec - hookSec - outroSec - phoneSec;

  // Convert to frames
  const hookFrames = Math.round(hookSec * fps);
  const bodyFrames = Math.round(bodySec * fps);
  const phoneFrames = Math.round(phoneSec * fps);
  const outroFrames = totalFrames - hookFrames - bodyFrames - phoneFrames;

  // Screenshot + broll selection (deterministic from brief id)
  const idHash = brief.id
    ? brief.id.split('').reduce((a, c) => a + c.charCodeAt(0), 0)
    : 0;
  const screenshotPath = EVERREACH_SCREENSHOTS[idHash % EVERREACH_SCREENSHOTS.length];
  const screenshotFile = screenshotPath.split('/').pop() ?? '';
  const notificationText = SCREENSHOT_NOTIFICATIONS[screenshotFile] ?? '⏰ Time to reconnect with someone';
  const brollPath = BROLL_VIDEOS[idHash % BROLL_VIDEOS.length];

  // B-roll fades: subtle during body section, hidden during hook/outro
  const brollFadeInEnd = hookFrames + 15;
  const brollFadeOutStart = hookFrames + bodyFrames - 15;
  const brollOpacity = interpolate(
    frame,
    [hookFrames, brollFadeInEnd, brollFadeOutStart, hookFrames + bodyFrames],
    [0, 0.14, 0.14, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  // Audio sources
  const voiceover = brief.audio?.voiceover;
  const musicPath = brief.audio?.music_path;
  const wordTimings: WordTiming[] = brief.audio?.word_timings ?? [];

  const voiceSrc = voiceover
    ? (voiceover.startsWith('http') ? voiceover : staticFile(voiceover))
    : null;
  const musicSrc = musicPath
    ? (musicPath.startsWith('http') ? musicPath : staticFile(musicPath))
    : null;

  return (
    <AbsoluteFill
      style={{
        background: theme.background,
        overflow: 'hidden',
      }}
    >
      {/* === PERSISTENT BACKGROUND LAYERS === */}

      {/* Bass-reactive audio pulse (behind everything) */}
      {musicSrc && (
        <AudioPulse src={musicPath!} accentColor={theme.accent} intensity={0.7} />
      )}

      {/* B-roll ambient video — subtle overlay during body section */}
      <AbsoluteFill
        style={{
          opacity: brollOpacity,
          mixBlendMode: 'screen',
          pointerEvents: 'none',
        }}
      >
        <Video
          src={staticFile(brollPath)}
          loop
          muted
          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
        />
      </AbsoluteFill>

      {/* Film grain overlay */}
      <FilmGrain opacity={0.065} animationSpeed={7} />

      {/* Vignette for cinematic focus */}
      <Vignette strength={0.55} />

      {/* === CONTENT SECTIONS (sequential) === */}

      {/* Hook */}
      <Sequence from={0} durationInFrames={hookFrames} name="hook">
        <HookSlam
          text={brief.hook_text}
          emoji={brief.hook_emoji}
          subtext={brief.hook_subtext}
          style_={brief.hook_style ?? 'stamp'}
          theme={theme}
        />
      </Sequence>

      {/* Body points */}
      {bodyPoints.length > 0 && bodyFrames > 0 && (
        <Sequence from={hookFrames} durationInFrames={bodyFrames} name="body">
          <BodyContent
            points={bodyPoints}
            theme={theme}
            style={brief.format?.includes('checklist') ? 'checklist' : 'numbered'}
            sectionDurationFrames={bodyFrames}
          />
        </Sequence>
      )}

      {/* Phone frame with EverReach screenshot */}
      {phoneSec > 0 && (
        <Sequence
          from={hookFrames + bodyFrames}
          durationInFrames={phoneFrames}
          name="phone_frame"
        >
          <AbsoluteFill style={{ background: theme.background }}>
            <PhoneFrame
              screenshotPath={screenshotPath}
              notificationText={notificationText}
              theme={theme}
            />
          </AbsoluteFill>
        </Sequence>
      )}

      {/* Outro */}
      <Sequence
        from={hookFrames + bodyFrames + phoneFrames}
        durationInFrames={outroFrames}
        name="outro"
      >
        <AbsoluteFill style={{ background: theme.background }}>
          <OutroSlide
            title={brief.cta_text ? 'Start for free today' : 'EverReach'}
            ctaText={brief.cta_text ?? 'Download EverReach — link in bio.'}
            appName="EverReach"
            theme={theme}
          />
        </AbsoluteFill>
      </Sequence>

      {/* === PERSISTENT OVERLAY LAYERS === */}

      {/* Word-level captions overlay (full video duration) */}
      {wordTimings.length > 0 && (
        <CaptionOverlay
          wordTimings={wordTimings}
          accentColor={theme.accent}
          fontFamily={theme.fontFamily}
        />
      )}

      {/* EverReach watermark badge (top-right) */}
      <WatermarkBadge />

      {/* Promise countdown badge — bottom-left, fades after 80% of video */}
      {(brief.body_points ?? []).length > 0 && (
        <PromiseBadge
          tipCount={(brief.body_points ?? []).length}
          durationSec={totalSec}
          accentColor={theme.accent}
          fontFamily={theme.fontFamily}
        />
      )}

      {/* === AUDIO === */}
      {voiceSrc && (
        <Audio src={voiceSrc} volume={brief.audio?.volume_voice ?? 1.0} />
      )}
      {musicSrc && (
        <Audio src={musicSrc} volume={brief.audio?.volume_music ?? 0.25} />
      )}
    </AbsoluteFill>
  );
};
