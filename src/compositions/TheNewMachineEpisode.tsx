import React from 'react';
import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {DiagramLayer} from './TheNewMachineDiagrams';

// ──────────────────────────────────────────────────────────────────────────────
// The New Machine — long-form documentary composition
//
// Brand spec: TheNewMachine/visuals/brand-spec.md
// Composition contract: TheNewMachine/remotion/README.md
//
// Pieces, top→bottom in render order:
//   - Scene background (image OR section-tinted gradient fallback)
//   - Caption layer (lower third)
//   - Diagram layer (cued by props.diagrams[])
//   - Section badge (lower-left, always visible per section)
//   - Chapter card (1.5s reveal at section transitions)
//   - Title card (briefly during the title section)
//   - Intro stem (3s post-cold-open: dot grid + wordmark)
//   - Beat overlay (textOverlay for cued beats)
//   - Channel bug (post-30s, bottom-right)
//   - Outro (last 8s: wordmark + subscribe + next-ep tile)
// ──────────────────────────────────────────────────────────────────────────────

// ── Brand tokens (mirror visuals/brand-spec.md) ──────────────────────────────
export const BRAND = {
  bg:       '#07090C',
  bgPanel:  '#10141A',
  text:     '#E8ECF1',
  muted:    '#8A93A0',
  cyan:     '#3FE0D0',
  amber:    '#F5A623',
  danger:   '#E04F5F',
  power:    '#A0FF00',
  fontDisplay: '"Inter Tight", "Inter", system-ui, sans-serif',
  fontBody:    '"Inter", system-ui, sans-serif',
  fontMono:    '"JetBrains Mono", "Courier New", monospace',
};

// ── Composition contract ─────────────────────────────────────────────────────
export type Scene = {
  startMs: number;
  endMs: number;
  imageUrl: string;
  caption?: string;
  motion?: 'push' | 'pull' | 'drift';
  section?: string;
  cue?: string;
};

export type DiagramComponent =
  | 'AgentLoop' | 'OldNewSplit' | 'StackDiagram' | 'Timeline'
  | 'WinnersLosers' | 'MapTopology' | 'ApprovalQueue' | 'Funnel'
  | 'XRayReveal' | 'SankeyFlow';

export type DiagramCue = {
  startMs: number;
  endMs: number;
  component: DiagramComponent;
  props: Record<string, unknown>;
  buildTimings: number[];
};

export type Beat = {
  atMs: number;
  type: 'visual_change' | 'pattern_interrupt' | 'chapter_turn' | 'reveal' | 'open_loop' | 'hook_landing';
  soundCue?: 'sub_bass' | 'click_cascade' | 'glitch' | 'riser' | 'hum_drop';
  textOverlay?: string;
};

export type EpisodeProps = {
  episodeId: string;
  title: string;
  scenes: Scene[];
  voiceoverUrl: string;
  diagrams: DiagramCue[];
  retentionBeats: Beat[];
  nextEpisodeTitle?: string;
};

// ── Defaults ─────────────────────────────────────────────────────────────────
export const theNewMachineEpisodeDefaultProps: EpisodeProps = {
  episodeId: 'EP001',
  title: 'AI Agents Are About to Replace Dashboards',
  voiceoverUrl: '',
  scenes: [
    {startMs: 0,     endMs: 8000,  imageUrl: '', caption: 'A manager opens five dashboards every morning.', motion: 'push',  section: 'title'},
    {startMs: 8000,  endMs: 16000, imageUrl: '', caption: 'Sales. Email. Analytics. CRM. Project management.', motion: 'drift', section: 'title'},
    {startMs: 16000, endMs: 25000, imageUrl: '', caption: 'It is actually the bottleneck.', motion: 'pull',  section: 'title'},
  ],
  diagrams: [],
  retentionBeats: [{atMs: 25000, type: 'hook_landing', soundCue: 'sub_bass'}],
  nextEpisodeTitle: 'The Company With No Employees',
};

// ── Section metadata ─────────────────────────────────────────────────────────
type SectionMeta = {label: string; color: string; show: boolean};

const SECTION_TABLE: Record<string, SectionMeta> = {
  title:           {label: '',                color: BRAND.cyan,   show: false},
  old_machine:     {label: 'OLD MACHINE',     color: BRAND.amber,  show: true},
  new_machine:     {label: 'NEW MACHINE',     color: BRAND.cyan,   show: true},
  under_hood:      {label: 'UNDER THE HOOD',  color: BRAND.cyan,   show: true},
  power_shift:     {label: 'POWER SHIFT',     color: BRAND.power,  show: true},
  failure_mode:    {label: 'FAILURE MODE',    color: BRAND.danger, show: true},
  future_scenario: {label: 'FUTURE SCENARIO', color: BRAND.cyan,   show: true},
  takeaway:        {label: 'TAKEAWAY',        color: BRAND.power,  show: true},
  open_loop:       {label: '',                color: BRAND.cyan,   show: false},
};

const sectionMeta = (s?: string): SectionMeta =>
  (s && SECTION_TABLE[s]) || {label: '', color: BRAND.cyan, show: false};

// Compute first-occurrence boundaries for each section.
// Returns [{section, startMs, endMs}], one per section, in scene order.
type SectionBoundary = {section: string; startMs: number; endMs: number};

const computeSectionBoundaries = (scenes: Scene[]): SectionBoundary[] => {
  const out: SectionBoundary[] = [];
  let cur: SectionBoundary | null = null;
  for (const s of scenes) {
    const sec = s.section || '';
    if (!cur || cur.section !== sec) {
      if (cur) out.push(cur);
      cur = {section: sec, startMs: s.startMs, endMs: s.endMs};
    } else {
      cur.endMs = s.endMs;
    }
  }
  if (cur) out.push(cur);
  return out;
};

const sectionAt = (boundaries: SectionBoundary[], ms: number): string | null => {
  for (const b of boundaries) {
    if (ms >= b.startMs && ms < b.endMs) return b.section;
  }
  return null;
};

// ── Helpers ──────────────────────────────────────────────────────────────────
const useMs = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (frame / fps) * 1000;
};

const msToFrames = (ms: number, fps: number) => Math.round((ms / 1000) * fps);

const resolveUrl = (u: string | undefined): string => {
  if (!u) return '';
  if (/^(https?:|file:|data:)/.test(u)) return u;
  return staticFile(u);
};

// ── Scene background ─────────────────────────────────────────────────────────
const SceneBackground: React.FC<{scene: Scene}> = ({scene}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const durationFrames = msToFrames(scene.endMs - scene.startMs, fps);

  const t = frame / Math.max(durationFrames, 1);
  let scale = 1.0;
  let translateX = 0;
  if (scene.motion === 'push') scale = interpolate(t, [0, 1], [1.0, 1.06]);
  if (scene.motion === 'pull') scale = interpolate(t, [0, 1], [1.06, 1.0]);
  if (scene.motion === 'drift') translateX = interpolate(t, [0, 1], [-12, 12]);

  if (scene.imageUrl) {
    return (
      <AbsoluteFill style={{background: BRAND.bg}}>
        <Img
          src={resolveUrl(scene.imageUrl)}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            transform: `scale(${scale}) translateX(${translateX}px)`,
            filter: 'saturate(0.92) contrast(1.05)',
          }}
        />
        <AbsoluteFill style={{
          background: 'linear-gradient(180deg, rgba(7,9,12,0.45) 0%, rgba(7,9,12,0) 35%, rgba(7,9,12,0) 60%, rgba(7,9,12,0.85) 100%)',
        }} />
      </AbsoluteFill>
    );
  }

  // Fallback: section-tinted radial with a faint hairline grid + drifting glow.
  const meta = sectionMeta(scene.section);
  const tintRgba = (() => {
    const c = meta.color;
    const r = parseInt(c.slice(1, 3), 16);
    const g = parseInt(c.slice(3, 5), 16);
    const b = parseInt(c.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, 0.10)`;
  })();
  const driftX = interpolate(t, [0, 1], [-30, 30]);
  return (
    <AbsoluteFill
      style={{
        background:
          `radial-gradient(circle at 50% 60%, ${BRAND.bgPanel} 0%, ${BRAND.bg} 70%),` +
          `linear-gradient(${BRAND.bgPanel} 1px, transparent 1px),` +
          `linear-gradient(90deg, ${BRAND.bgPanel} 1px, transparent 1px)`,
        backgroundSize: '100% 100%, 96px 96px, 96px 96px',
        backgroundBlendMode: 'normal, screen, screen',
        opacity: 1,
      }}
    >
      <AbsoluteFill style={{
        background: `radial-gradient(circle at ${50 + driftX / 4}% 50%, ${tintRgba} 0%, transparent 55%)`,
      }} />
    </AbsoluteFill>
  );
};

// ── Caption layer ────────────────────────────────────────────────────────────
const Caption: React.FC<{scene: Scene}> = ({scene}) => {
  if (!scene.caption) return null;
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = spring({frame, fps, config: {damping: 22}});
  return (
    <div
      style={{
        position: 'absolute',
        left: 0, right: 0, bottom: 120,
        textAlign: 'center',
        color: BRAND.text,
        fontFamily: BRAND.fontBody,
        fontSize: 38,
        fontWeight: 500,
        lineHeight: 1.35,
        letterSpacing: 0.3,
        textShadow: '0 2px 16px rgba(0,0,0,0.95)',
        padding: '0 160px',
        opacity: t,
        transform: `translateY(${(1 - t) * 8}px)`,
      }}
    >
      {scene.caption}
    </div>
  );
};

// ── Section badge (always visible during a labeled section) ─────────────────
const SectionBadge: React.FC<{section?: string}> = ({section}) => {
  const meta = sectionMeta(section);
  if (!meta.show) return null;
  return (
    <div
      style={{
        position: 'absolute',
        left: 64, bottom: 64,
        display: 'flex',
        alignItems: 'center',
        gap: 12,
        opacity: 0.85,
      }}
    >
      <div style={{
        width: 6, height: 6, borderRadius: 3,
        background: meta.color,
        boxShadow: `0 0 10px ${meta.color}`,
      }} />
      <div style={{
        fontFamily: BRAND.fontMono,
        fontSize: 18,
        letterSpacing: 4,
        color: meta.color,
      }}>
        {meta.label}
      </div>
    </div>
  );
};

// ── Chapter card (1.5s flash at every section change after the title) ───────
const ChapterCards: React.FC<{boundaries: SectionBoundary[]}> = ({boundaries}) => {
  const ms = useMs();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  // Skip the very first section (cold open shouldn't be interrupted)
  const cards = boundaries.slice(1).filter((b) => sectionMeta(b.section).show);
  const active = cards.find((b) => ms >= b.startMs && ms < b.startMs + 1500);
  if (!active) return null;
  const meta = sectionMeta(active.section);
  const localFrame = frame - msToFrames(active.startMs, fps);
  const t = spring({frame: localFrame, fps, config: {damping: 24, mass: 0.6}});
  const fade = interpolate(localFrame, [msToFrames(1100, fps), msToFrames(1500, fps)], [1, 0], {extrapolateRight: 'clamp'});
  return (
    <div style={{
      position: 'absolute',
      inset: 0,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      pointerEvents: 'none',
      opacity: Math.min(t, fade),
    }}>
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 18,
      }}>
        <div style={{
          width: 8, height: 8, borderRadius: 4,
          background: meta.color,
          boxShadow: `0 0 16px ${meta.color}`,
        }} />
        <div style={{
          fontFamily: BRAND.fontMono,
          fontSize: 22,
          letterSpacing: 8,
          color: meta.color,
        }}>
          {meta.label}
        </div>
        <div style={{
          width: 80, height: 1,
          background: meta.color,
          opacity: 0.6,
        }} />
      </div>
    </div>
  );
};

// ── Title card (during cold-open / title section) ───────────────────────────
const TitleCard: React.FC<{title: string; coldOpenEndsMs: number}> = ({title, coldOpenEndsMs}) => {
  const ms = useMs();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  // Show title during the last 4s of the cold open
  const showFromMs = Math.max(0, coldOpenEndsMs - 4000);
  if (ms < showFromMs || ms > coldOpenEndsMs) return null;
  const localFrame = frame - msToFrames(showFromMs, fps);
  const t = spring({frame: localFrame, fps, config: {damping: 18}});
  return (
    <div style={{
      position: 'absolute',
      inset: 0,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      pointerEvents: 'none',
    }}>
      <div style={{
        opacity: t,
        transform: `translateY(${(1 - t) * 12}px)`,
        color: BRAND.text,
        fontFamily: BRAND.fontDisplay,
        fontWeight: 700,
        fontSize: 78,
        lineHeight: 1.05,
        letterSpacing: -0.5,
        textAlign: 'center',
        maxWidth: 1500,
        textShadow: '0 6px 30px rgba(0,0,0,0.95)',
      }}>
        {title}
      </div>
    </div>
  );
};

// ── Intro stem (3s post-cold-open: dot grid + wordmark) ─────────────────────
// Per brand-spec: intro plays AFTER cold open, not before.
const IntroStem: React.FC<{startMs: number}> = ({startMs}) => {
  const ms = useMs();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const endMs = startMs + 3000;
  if (ms < startMs || ms >= endMs) return null;
  const localMs = ms - startMs;
  const localFrame = frame - msToFrames(startMs, fps);

  // Black hold + dot grid + wordmark in 3 phases (per brand-spec):
  //   0.0–0.6s: black with hum (no audio yet, just visual hold)
  //   0.6–1.6s: 3x3 dot grid powers up sequentially, ending on cyan center
  //   1.6–2.6s: wordmark slides up under grid, underscore draws L→R
  //   2.6–3.0s: bass-hit fade to cold-open continuation

  const fadeOut = interpolate(localMs, [2600, 3000], [1, 0], {extrapolateRight: 'clamp'});

  // Dot grid: which dots are lit at time localMs?
  const dotOrder = [0, 1, 2, 5, 8, 7, 6, 3, 4]; // perimeter sweep, ending center
  const litCount = Math.min(9, Math.max(0, Math.floor((localMs - 600) / 110)));

  // Wordmark spring (1600ms in)
  const wordmarkFrame = localFrame - msToFrames(1600, fps);
  const wt = spring({frame: Math.max(0, wordmarkFrame), fps, config: {damping: 22}});
  // Underscore draws over 1.0s after wordmark appears
  const underscorePct = interpolate(localMs, [1900, 2600], [0, 100], {extrapolateRight: 'clamp', extrapolateLeft: 'clamp'});

  return (
    <AbsoluteFill style={{
      background: BRAND.bg,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 44,
      opacity: fadeOut,
    }}>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 14px)',
        gridTemplateRows: 'repeat(3, 14px)',
        gap: 10,
      }}>
        {Array.from({length: 9}).map((_, i) => {
          const lit = dotOrder.indexOf(i) < litCount;
          const isCenter = i === 4;
          const color = isCenter && lit ? BRAND.cyan : lit ? BRAND.muted : '#22272F';
          return (
            <div key={i} style={{
              width: 14, height: 14, borderRadius: 2,
              background: color,
              boxShadow: isCenter && lit ? `0 0 14px ${BRAND.cyan}` : 'none',
              transition: 'background 200ms',
            }} />
          );
        })}
      </div>
      <div style={{
        opacity: wt,
        transform: `translateY(${(1 - wt) * 10}px)`,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 8,
      }}>
        <div style={{
          fontFamily: BRAND.fontDisplay,
          fontWeight: 700,
          fontSize: 38,
          letterSpacing: 8,
          color: BRAND.text,
        }}>
          THE NEW MACHINE
        </div>
        <div style={{
          width: 320,
          height: 1,
          background: 'transparent',
          position: 'relative',
        }}>
          <div style={{
            position: 'absolute',
            left: 0, top: 0,
            width: `${underscorePct}%`,
            height: 1,
            background: BRAND.cyan,
            boxShadow: `0 0 8px ${BRAND.cyan}`,
          }} />
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ── Channel watermark (after 30s, bottom-right, suppressed during outro) ────
const Bug: React.FC<{outroStartMs: number}> = ({outroStartMs}) => {
  const ms = useMs();
  if (ms < 30000 || ms >= outroStartMs) return null;
  return (
    <div style={{
      position: 'absolute',
      right: 36, bottom: 36,
      display: 'grid',
      gridTemplateColumns: 'repeat(3, 6px)',
      gap: 4,
      opacity: 0.65,
    }}>
      {Array.from({length: 9}).map((_, i) => (
        <div key={i} style={{
          width: 6, height: 6, borderRadius: 1,
          background: i === 4 ? BRAND.cyan : BRAND.muted,
          boxShadow: i === 4 ? `0 0 8px ${BRAND.cyan}` : 'none',
        }} />
      ))}
    </div>
  );
};

// ── Beat overlay ─────────────────────────────────────────────────────────────
const BeatOverlay: React.FC<{beats: Beat[]}> = ({beats}) => {
  const ms = useMs();
  const active = beats.find((b) => Math.abs(ms - b.atMs) < 250);
  if (!active?.textOverlay) return null;
  return (
    <div style={{
      position: 'absolute',
      left: 96, top: 96,
      color: BRAND.cyan,
      fontFamily: BRAND.fontMono,
      fontSize: 22,
      letterSpacing: 1.5,
      textTransform: 'uppercase',
      textShadow: `0 0 12px ${BRAND.cyan}`,
    }}>
      {active.textOverlay}
    </div>
  );
};

// ── Outro (last 8s: subscribe + next-ep tile + wordmark) ────────────────────
const Outro: React.FC<{startMs: number; nextEpisodeTitle?: string}> = ({startMs, nextEpisodeTitle}) => {
  const ms = useMs();
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (ms < startMs) return null;
  const localFrame = frame - msToFrames(startMs, fps);
  const t = spring({frame: localFrame, fps, config: {damping: 22, mass: 0.7}});
  const localMs = ms - startMs;
  // Final 1s fade-to-black
  const tail = interpolate(localMs, [7000, 8000], [1, 0], {extrapolateRight: 'clamp'});

  return (
    <AbsoluteFill style={{
      background: `radial-gradient(circle at 50% 50%, rgba(16,20,26,0.96) 0%, rgba(7,9,12,1) 80%)`,
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      gap: 64,
      opacity: Math.min(t, tail),
    }}>
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 14,
      }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 10px)',
          gap: 8,
        }}>
          {Array.from({length: 9}).map((_, i) => (
            <div key={i} style={{
              width: 10, height: 10, borderRadius: 2,
              background: i === 4 ? BRAND.cyan : BRAND.muted,
              boxShadow: i === 4 ? `0 0 12px ${BRAND.cyan}` : 'none',
            }} />
          ))}
        </div>
        <div style={{
          fontFamily: BRAND.fontDisplay,
          fontWeight: 700,
          fontSize: 32,
          letterSpacing: 6,
          color: BRAND.text,
        }}>
          THE NEW MACHINE
        </div>
      </div>

      <div style={{display: 'grid', gridTemplateColumns: '420px 1fr', gap: 32, maxWidth: 1280}}>
        <div style={{
          border: `1px solid ${BRAND.cyan}55`,
          background: BRAND.bgPanel,
          padding: 26,
          borderRadius: 6,
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
          minHeight: 180,
        }}>
          <div style={{
            fontFamily: BRAND.fontMono,
            fontSize: 14,
            letterSpacing: 4,
            color: BRAND.muted,
          }}>
            SUBSCRIBE
          </div>
          <div style={{
            fontFamily: BRAND.fontDisplay,
            fontSize: 28,
            color: BRAND.text,
            lineHeight: 1.2,
          }}>
            One documentary a week on the systems behind the future.
          </div>
        </div>
        <div style={{
          border: `1px solid ${BRAND.cyan}`,
          background: BRAND.bgPanel,
          padding: 26,
          borderRadius: 6,
          display: 'flex',
          flexDirection: 'column',
          gap: 12,
          minHeight: 180,
          boxShadow: `0 0 32px rgba(63,224,208,0.18)`,
        }}>
          <div style={{
            fontFamily: BRAND.fontMono,
            fontSize: 14,
            letterSpacing: 4,
            color: BRAND.cyan,
          }}>
            NEXT EPISODE  →
          </div>
          <div style={{
            fontFamily: BRAND.fontDisplay,
            fontSize: 36,
            color: BRAND.text,
            lineHeight: 1.15,
          }}>
            {nextEpisodeTitle || 'Continue the series.'}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ── Main composition ─────────────────────────────────────────────────────────
export const TheNewMachineEpisode: React.FC<EpisodeProps> = (props) => {
  const {fps} = useVideoConfig();
  const {scenes, voiceoverUrl, retentionBeats, title, diagrams, nextEpisodeTitle} = props;

  const boundaries = React.useMemo(() => computeSectionBoundaries(scenes), [scenes]);

  // Outro plays AFTER the last scene (Root.tsx adds 8s tail in calculateMetadata).
  const lastSceneEndMs = scenes.length ? scenes[scenes.length - 1].endMs : 0;
  const outroStartMs = lastSceneEndMs;

  // Cold open ends when the title section ends (first non-title section start),
  // or 25s if no section info is present.
  const titleBoundary = boundaries.find((b) => b.section === 'title');
  const coldOpenEndsMs = titleBoundary ? titleBoundary.endMs : 25000;
  const introStartMs = coldOpenEndsMs;

  // Section badge tracks the current section.
  const ms = (useCurrentFrame() / fps) * 1000;
  const currentSection = sectionAt(boundaries, ms) ?? '';

  return (
    <AbsoluteFill style={{background: BRAND.bg}}>
      {voiceoverUrl ? <Audio src={resolveUrl(voiceoverUrl)} /> : null}

      {scenes.map((scene, i) => {
        const fromFrame = msToFrames(scene.startMs, fps);
        const durationFrames = Math.max(1, msToFrames(scene.endMs - scene.startMs, fps));
        return (
          <Sequence key={i} from={fromFrame} durationInFrames={durationFrames}>
            <SceneBackground scene={scene} />
            <Caption scene={scene} />
          </Sequence>
        );
      })}

      <DiagramLayer cues={diagrams ?? []} />
      <SectionBadge section={currentSection} />
      <ChapterCards boundaries={boundaries} />
      <TitleCard title={title} coldOpenEndsMs={coldOpenEndsMs} />
      <IntroStem startMs={introStartMs} />
      <BeatOverlay beats={retentionBeats} />
      <Bug outroStartMs={outroStartMs} />
      <Outro startMs={outroStartMs} nextEpisodeTitle={nextEpisodeTitle} />
    </AbsoluteFill>
  );
};

export default TheNewMachineEpisode;
