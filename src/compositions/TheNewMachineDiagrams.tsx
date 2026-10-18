import React from 'react';
import {
  AbsoluteFill,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {BRAND, type DiagramComponent, type DiagramCue} from './TheNewMachineEpisode';

// ──────────────────────────────────────────────────────────────────────────────
// The New Machine — diagram component library
//
// Driven by `props.diagrams[]` from the pipeline (compile_props.py).
// Each cue picks a component by name and a `buildTimings: number[]` (ms,
// relative to cue start) that staggers the reveal of inner pieces.
//
// Visual language: thin cyan strokes on near-black panel, amber accents on
// "old machine" elements, monospace labels. Every diagram fades in on a
// hairline grid and builds piece-by-piece on the build timings.
// ──────────────────────────────────────────────────────────────────────────────

const msToFrames = (ms: number, fps: number) => Math.round((ms / 1000) * fps);

const useLocalMs = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return (frame / fps) * 1000;
};

const useStepIndex = (timings: number[]) => {
  const ms = useLocalMs();
  let idx = -1;
  for (let i = 0; i < timings.length; i++) {
    if (ms >= timings[i]) idx = i;
  }
  return idx;
};

const Reveal: React.FC<{at: number; children: React.ReactNode; from?: 'down' | 'up' | 'fade'}> = ({
  at,
  children,
  from = 'down',
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const startFrame = msToFrames(at, fps);
  if (frame < startFrame) return null;
  const t = spring({frame: frame - startFrame, fps, config: {damping: 18, mass: 0.6}});
  const dy = from === 'down' ? (1 - t) * 14 : from === 'up' ? -(1 - t) * 14 : 0;
  return <div style={{opacity: t, transform: `translateY(${dy}px)`}}>{children}</div>;
};

const PanelFrame: React.FC<{title?: string; children: React.ReactNode}> = ({title, children}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = spring({frame, fps, config: {damping: 22}});
  return (
    <AbsoluteFill
      style={{
        background: BRAND.bg,
        backgroundImage:
          `linear-gradient(${BRAND.bgPanel} 1px, transparent 1px),` +
          `linear-gradient(90deg, ${BRAND.bgPanel} 1px, transparent 1px)`,
        backgroundSize: '64px 64px',
        opacity: t,
        padding: 80,
        display: 'flex',
        flexDirection: 'column',
        gap: 32,
      }}
    >
      {title && (
        <div
          style={{
            fontFamily: BRAND.fontMono,
            fontSize: 22,
            letterSpacing: 4,
            textTransform: 'uppercase',
            color: BRAND.muted,
          }}
        >
          {title}
        </div>
      )}
      <div style={{flex: 1, position: 'relative'}}>{children}</div>
    </AbsoluteFill>
  );
};

// ── AgentLoop ────────────────────────────────────────────────────────────────
// Four-node loop: Read → Reason → Act → (loop back to Read), with a side branch
// to "Notify human" gated by a risk threshold. Build timings reveal each node.
type AgentLoopProps = {
  title?: string;
  nodes?: string[];
  branch?: string;
};

export const AgentLoop: React.FC<AgentLoopProps & {buildTimings: number[]}> = ({
  title = 'The agent loop',
  nodes = ['Read', 'Reason', 'Act', 'Observe'],
  branch = 'Notify human (if risk > threshold)',
  buildTimings,
}) => {
  const step = useStepIndex(buildTimings);
  const radius = 240;
  const cx = 540;
  const cy = 360;
  const positions = nodes.map((_, i) => {
    const a = (i / nodes.length) * Math.PI * 2 - Math.PI / 2;
    return {x: cx + Math.cos(a) * radius, y: cy + Math.sin(a) * radius};
  });

  return (
    <PanelFrame title={title}>
      <svg width="100%" height="100%" viewBox="0 0 1080 720" style={{overflow: 'visible'}}>
        {positions.map((p, i) => {
          const next = positions[(i + 1) % positions.length];
          const visible = step >= i + 1;
          return (
            <g key={`edge-${i}`} opacity={visible ? 1 : 0.08} style={{transition: 'opacity 400ms'}}>
              <defs>
                <marker id={`arr-${i}`} viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" orient="auto">
                  <path d="M0,0 L10,5 L0,10 Z" fill={BRAND.cyan} />
                </marker>
              </defs>
              <path
                d={`M ${p.x} ${p.y} A ${radius} ${radius} 0 0 1 ${next.x} ${next.y}`}
                fill="none"
                stroke={BRAND.cyan}
                strokeWidth={2}
                markerEnd={`url(#arr-${i})`}
              />
            </g>
          );
        })}
        {positions.map((p, i) => (
          <foreignObject key={`node-${i}`} x={p.x - 90} y={p.y - 36} width={180} height={72}>
            <Reveal at={buildTimings[i] ?? 0}>
              <div
                style={{
                  width: 180,
                  height: 72,
                  borderRadius: 8,
                  border: `1px solid ${BRAND.cyan}`,
                  background: BRAND.bgPanel,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: BRAND.text,
                  fontFamily: BRAND.fontDisplay,
                  fontSize: 26,
                  letterSpacing: 0.5,
                  boxShadow: `0 0 24px rgba(63,224,208,0.18)`,
                }}
              >
                {nodes[i]}
              </div>
            </Reveal>
          </foreignObject>
        ))}
      </svg>
      <div style={{position: 'absolute', left: 0, right: 0, bottom: 0}}>
        <Reveal at={buildTimings[buildTimings.length - 1] ?? 0}>
          <div
            style={{
              fontFamily: BRAND.fontMono,
              fontSize: 20,
              color: BRAND.amber,
              letterSpacing: 2,
              textTransform: 'uppercase',
            }}
          >
            ↳ {branch}
          </div>
        </Reveal>
      </div>
    </PanelFrame>
  );
};

// ── OldNewSplit ──────────────────────────────────────────────────────────────
// Two columns: amber "Old machine" vs cyan "New machine". Items reveal by
// build timing — left first, right second to drive the contrast beat.
type OldNewSplitProps = {
  title?: string;
  oldLabel?: string;
  newLabel?: string;
  oldItems: string[];
  newItems: string[];
};

export const OldNewSplit: React.FC<OldNewSplitProps & {buildTimings: number[]}> = ({
  title = 'Old machine / new machine',
  oldLabel = 'Old machine',
  newLabel = 'New machine',
  oldItems,
  newItems,
  buildTimings,
}) => {
  return (
    <PanelFrame title={title}>
      <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 64, height: '100%'}}>
        <Column accent={BRAND.amber} label={oldLabel} items={oldItems} startMs={buildTimings[0] ?? 0} stepMs={120} />
        <Column accent={BRAND.cyan} label={newLabel} items={newItems} startMs={buildTimings[1] ?? (buildTimings[0] ?? 0) + 800} stepMs={120} />
      </div>
    </PanelFrame>
  );
};

const Column: React.FC<{accent: string; label: string; items: string[]; startMs: number; stepMs: number}> = ({
  accent,
  label,
  items,
  startMs,
  stepMs,
}) => (
  <div style={{display: 'flex', flexDirection: 'column', gap: 18}}>
    <Reveal at={startMs}>
      <div
        style={{
          fontFamily: BRAND.fontDisplay,
          fontSize: 36,
          color: accent,
          letterSpacing: -0.2,
          borderBottom: `1px solid ${accent}55`,
          paddingBottom: 8,
        }}
      >
        {label}
      </div>
    </Reveal>
    {items.map((it, i) => (
      <Reveal key={i} at={startMs + (i + 1) * stepMs}>
        <div
          style={{
            fontFamily: BRAND.fontBody,
            fontSize: 26,
            color: BRAND.text,
            display: 'flex',
            gap: 14,
            alignItems: 'baseline',
          }}
        >
          <span style={{color: accent, fontFamily: BRAND.fontMono, fontSize: 20}}>—</span>
          <span>{it}</span>
        </div>
      </Reveal>
    ))}
  </div>
);

// ── StackDiagram ─────────────────────────────────────────────────────────────
// Vertical stack of layered tiles (e.g., agent stack: acquisition / support /
// billing / content / observability). Each layer reveals on its build timing.
type StackDiagramProps = {
  title?: string;
  layers: {label: string; sublabel?: string; accent?: 'cyan' | 'amber' | 'power'}[];
};

export const StackDiagram: React.FC<StackDiagramProps & {buildTimings: number[]}> = ({
  title = 'The stack',
  layers,
  buildTimings,
}) => {
  return (
    <PanelFrame title={title}>
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 12,
          maxWidth: 760,
          margin: '0 auto',
          paddingTop: 16,
        }}
      >
        {layers.map((layer, i) => {
          const accent =
            layer.accent === 'amber' ? BRAND.amber : layer.accent === 'power' ? BRAND.power : BRAND.cyan;
          return (
            <Reveal key={i} at={buildTimings[i] ?? i * 250} from="up">
              <div
                style={{
                  border: `1px solid ${accent}`,
                  borderLeft: `4px solid ${accent}`,
                  background: BRAND.bgPanel,
                  padding: '18px 24px',
                  borderRadius: 6,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  boxShadow: `0 0 20px ${accent}22`,
                }}
              >
                <div
                  style={{
                    color: BRAND.text,
                    fontFamily: BRAND.fontDisplay,
                    fontSize: 28,
                    letterSpacing: 0.3,
                  }}
                >
                  {layer.label}
                </div>
                {layer.sublabel && (
                  <div
                    style={{
                      color: BRAND.muted,
                      fontFamily: BRAND.fontMono,
                      fontSize: 18,
                      letterSpacing: 1.5,
                      textTransform: 'uppercase',
                    }}
                  >
                    {layer.sublabel}
                  </div>
                )}
              </div>
            </Reveal>
          );
        })}
      </div>
    </PanelFrame>
  );
};

// ── WinnersLosers ────────────────────────────────────────────────────────────
type WinnersLosersProps = {
  title?: string;
  winners: string[];
  losers: string[];
};

export const WinnersLosers: React.FC<WinnersLosersProps & {buildTimings: number[]}> = ({
  title = 'Power shift',
  winners,
  losers,
  buildTimings,
}) => {
  return (
    <PanelFrame title={title}>
      <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 64, height: '100%'}}>
        <Column accent={BRAND.power} label="↑ Winners" items={winners} startMs={buildTimings[0] ?? 0} stepMs={140} />
        <Column accent={BRAND.danger} label="↓ Losers" items={losers} startMs={buildTimings[1] ?? (buildTimings[0] ?? 0) + 800} stepMs={140} />
      </div>
    </PanelFrame>
  );
};

// ── Timeline ─────────────────────────────────────────────────────────────────
// Horizontal year markers with event labels. Events reveal in order.
type TimelineProps = {
  title?: string;
  events: {year: string | number; label: string}[];
};

export const Timeline: React.FC<TimelineProps & {buildTimings: number[]}> = ({
  title = 'Timeline',
  events,
  buildTimings,
}) => {
  return (
    <PanelFrame title={title}>
      <div style={{position: 'relative', height: '100%', padding: '60px 40px'}}>
        <div
          style={{
            position: 'absolute',
            left: 60,
            right: 60,
            top: '50%',
            height: 1,
            background: BRAND.cyan,
            opacity: 0.4,
          }}
        />
        <div
          style={{
            position: 'absolute',
            left: 60,
            right: 60,
            top: '50%',
            display: 'flex',
            justifyContent: 'space-between',
            transform: 'translateY(-50%)',
          }}
        >
          {events.map((ev, i) => (
            <Reveal key={i} at={buildTimings[i] ?? i * 200}>
              <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12}}>
                <div
                  style={{
                    width: 14,
                    height: 14,
                    borderRadius: 7,
                    background: BRAND.cyan,
                    boxShadow: `0 0 16px ${BRAND.cyan}`,
                  }}
                />
                <div style={{fontFamily: BRAND.fontMono, fontSize: 18, color: BRAND.muted, letterSpacing: 2}}>
                  {ev.year}
                </div>
                <div
                  style={{
                    fontFamily: BRAND.fontBody,
                    fontSize: 22,
                    color: BRAND.text,
                    maxWidth: 220,
                    textAlign: 'center',
                  }}
                >
                  {ev.label}
                </div>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </PanelFrame>
  );
};

// ── ApprovalQueue ────────────────────────────────────────────────────────────
// Vertical list of pending decisions with status pills. Useful for "human
// approval queue" and "agent confidence" beats.
type ApprovalQueueProps = {
  title?: string;
  items: {label: string; status?: 'pending' | 'approved' | 'risky'}[];
};

export const ApprovalQueue: React.FC<ApprovalQueueProps & {buildTimings: number[]}> = ({
  title = 'Human approval queue',
  items,
  buildTimings,
}) => {
  const statusStyle = (s?: string) =>
    s === 'approved'
      ? {label: 'APPROVED', color: BRAND.power}
      : s === 'risky'
      ? {label: 'HIGH RISK', color: BRAND.danger}
      : {label: 'PENDING', color: BRAND.amber};
  return (
    <PanelFrame title={title}>
      <div style={{display: 'flex', flexDirection: 'column', gap: 14, maxWidth: 880, margin: '0 auto', paddingTop: 16}}>
        {items.map((it, i) => {
          const st = statusStyle(it.status);
          return (
            <Reveal key={i} at={buildTimings[i] ?? i * 220}>
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr auto',
                  alignItems: 'center',
                  gap: 24,
                  border: `1px solid ${BRAND.muted}55`,
                  background: BRAND.bgPanel,
                  padding: '16px 22px',
                  borderRadius: 4,
                }}
              >
                <div style={{fontFamily: BRAND.fontBody, fontSize: 24, color: BRAND.text}}>{it.label}</div>
                <div
                  style={{
                    fontFamily: BRAND.fontMono,
                    fontSize: 16,
                    letterSpacing: 2,
                    color: st.color,
                    border: `1px solid ${st.color}`,
                    padding: '4px 10px',
                    borderRadius: 2,
                  }}
                >
                  {st.label}
                </div>
              </div>
            </Reveal>
          );
        })}
      </div>
    </PanelFrame>
  );
};

// ── Funnel ───────────────────────────────────────────────────────────────────
// Inverted-trapezoid funnel with stage labels and counts.
type FunnelProps = {
  title?: string;
  stages: {label: string; value: number | string}[];
};

export const Funnel: React.FC<FunnelProps & {buildTimings: number[]}> = ({
  title = 'Funnel',
  stages,
  buildTimings,
}) => {
  const top = 800;
  const step = (top - 240) / Math.max(1, stages.length - 1);
  return (
    <PanelFrame title={title}>
      <svg width="100%" height="100%" viewBox="0 0 1080 720" preserveAspectRatio="xMidYMid meet">
        {stages.map((s, i) => {
          const y = 80 + i * 90;
          const w = top - i * step;
          const x = (1080 - w) / 2;
          return (
            <g key={i}>
              <foreignObject x={0} y={y} width={1080} height={70}>
                <Reveal at={buildTimings[i] ?? i * 250}>
                  <div style={{display: 'flex', justifyContent: 'center'}}>
                    <div
                      style={{
                        width: w,
                        height: 64,
                        background: BRAND.bgPanel,
                        border: `1px solid ${BRAND.cyan}`,
                        clipPath: 'polygon(2% 0, 98% 0, 96% 100%, 4% 100%)',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '0 60px',
                        color: BRAND.text,
                        fontFamily: BRAND.fontDisplay,
                        fontSize: 24,
                        boxShadow: `0 0 20px rgba(63,224,208,0.18)`,
                      }}
                    >
                      <span>{s.label}</span>
                      <span style={{fontFamily: BRAND.fontMono, color: BRAND.cyan, fontSize: 20, letterSpacing: 1.5}}>
                        {s.value}
                      </span>
                    </div>
                  </div>
                </Reveal>
              </foreignObject>
            </g>
          );
        })}
      </svg>
    </PanelFrame>
  );
};

// ── MapTopology ──────────────────────────────────────────────────────────────
// Abstract topology of nodes connected by lines (e.g., data centers, regions).
type MapTopologyProps = {
  title?: string;
  nodes: {x: number; y: number; label: string; accent?: 'cyan' | 'amber' | 'power'}[];
  edges: [number, number][];
};

export const MapTopology: React.FC<MapTopologyProps & {buildTimings: number[]}> = ({
  title = 'Topology',
  nodes,
  edges,
  buildTimings,
}) => {
  const step = useStepIndex(buildTimings);
  return (
    <PanelFrame title={title}>
      <svg width="100%" height="100%" viewBox="0 0 1080 720" preserveAspectRatio="xMidYMid meet">
        {edges.map(([a, b], i) => {
          const visible = step >= Math.max(a, b);
          const na = nodes[a];
          const nb = nodes[b];
          if (!na || !nb) return null;
          return (
            <line
              key={i}
              x1={na.x}
              y1={na.y}
              x2={nb.x}
              y2={nb.y}
              stroke={BRAND.cyan}
              strokeWidth={1.2}
              opacity={visible ? 0.6 : 0.08}
            />
          );
        })}
        {nodes.map((n, i) => {
          const accent = n.accent === 'amber' ? BRAND.amber : n.accent === 'power' ? BRAND.power : BRAND.cyan;
          return (
            <foreignObject key={i} x={n.x - 80} y={n.y - 24} width={160} height={48}>
              <Reveal at={buildTimings[i] ?? i * 200}>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 8,
                    background: BRAND.bgPanel,
                    border: `1px solid ${accent}`,
                    borderRadius: 4,
                    padding: '6px 10px',
                    width: 'fit-content',
                    margin: '0 auto',
                  }}
                >
                  <div style={{width: 8, height: 8, borderRadius: 4, background: accent, boxShadow: `0 0 10px ${accent}`}} />
                  <div style={{fontFamily: BRAND.fontMono, fontSize: 16, color: BRAND.text, letterSpacing: 1}}>{n.label}</div>
                </div>
              </Reveal>
            </foreignObject>
          );
        })}
      </svg>
    </PanelFrame>
  );
};

// ── XRayReveal ───────────────────────────────────────────────────────────────
// Surface label on top, hidden machinery underneath, separated by a moving
// scan line. Use for "the invisible layer underneath the storefront" beats.
type XRayRevealProps = {
  title?: string;
  surfaceLabel: string;
  hiddenItems: string[];
};

export const XRayReveal: React.FC<XRayRevealProps & {buildTimings: number[]}> = ({
  title = 'Underneath',
  surfaceLabel,
  hiddenItems,
  buildTimings,
}) => {
  const ms = useLocalMs();
  const totalMs = (buildTimings[buildTimings.length - 1] ?? 2000) + 1000;
  const scanX = interpolate(ms, [0, totalMs], [0, 1080], {extrapolateRight: 'clamp'});
  return (
    <PanelFrame title={title}>
      <svg width="100%" height="100%" viewBox="0 0 1080 720" preserveAspectRatio="xMidYMid meet">
        <rect x={0} y={0} width={1080} height={300} fill={BRAND.bgPanel} stroke={BRAND.amber} strokeWidth={1} opacity={0.6} />
        <foreignObject x={0} y={120} width={1080} height={80}>
          <div
            style={{
              textAlign: 'center',
              fontFamily: BRAND.fontDisplay,
              fontSize: 38,
              color: BRAND.amber,
              letterSpacing: 0.5,
            }}
          >
            {surfaceLabel}
          </div>
        </foreignObject>
        <line x1={scanX} y1={0} x2={scanX} y2={720} stroke={BRAND.cyan} strokeWidth={1.5} opacity={0.7} />
        <foreignObject x={60} y={340} width={960} height={360}>
          <div style={{display: 'flex', flexDirection: 'column', gap: 14}}>
            {hiddenItems.map((h, i) => (
              <Reveal key={i} at={buildTimings[i] ?? i * 200}>
                <div
                  style={{
                    fontFamily: BRAND.fontMono,
                    fontSize: 22,
                    color: BRAND.cyan,
                    letterSpacing: 1,
                    borderLeft: `2px solid ${BRAND.cyan}`,
                    paddingLeft: 14,
                  }}
                >
                  → {h}
                </div>
              </Reveal>
            ))}
          </div>
        </foreignObject>
      </svg>
    </PanelFrame>
  );
};

// ── SankeyFlow ───────────────────────────────────────────────────────────────
// Simplified sankey: source columns flowing into destination columns with
// proportional band thickness. Use for "where the money / attention flows".
type SankeyFlowProps = {
  title?: string;
  sources: {label: string; value: number}[];
  targets: {label: string; value: number}[];
};

export const SankeyFlow: React.FC<SankeyFlowProps & {buildTimings: number[]}> = ({
  title = 'Where it flows',
  sources,
  targets,
  buildTimings,
}) => {
  const total = Math.max(1, sources.reduce((s, n) => s + n.value, 0));
  const left = 80;
  const right = 1000;
  const top = 80;
  const totalH = 560;

  let yL = top;
  const sBands = sources.map((s) => {
    const h = (s.value / total) * totalH;
    const band = {y: yL, h, label: s.label};
    yL += h + 6;
    return band;
  });
  let yR = top;
  const tTotal = Math.max(1, targets.reduce((s, n) => s + n.value, 0));
  const tBands = targets.map((t) => {
    const h = (t.value / tTotal) * totalH;
    const band = {y: yR, h, label: t.label};
    yR += h + 6;
    return band;
  });

  return (
    <PanelFrame title={title}>
      <svg width="100%" height="100%" viewBox="0 0 1080 720" preserveAspectRatio="xMidYMid meet">
        {sBands.map((b, i) => (
          <foreignObject key={`s-${i}`} x={0} y={b.y} width={left - 12} height={b.h}>
            <Reveal at={buildTimings[0] ?? 0}>
              <div
                style={{
                  height: b.h,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'flex-end',
                  paddingRight: 12,
                  fontFamily: BRAND.fontMono,
                  fontSize: 16,
                  color: BRAND.muted,
                  letterSpacing: 1,
                }}
              >
                {b.label}
              </div>
            </Reveal>
          </foreignObject>
        ))}
        {sBands.map((b, i) => {
          const t = tBands[i % tBands.length];
          return (
            <path
              key={`p-${i}`}
              d={`M ${left} ${b.y} C ${(left + right) / 2} ${b.y}, ${(left + right) / 2} ${t.y}, ${right} ${t.y}
                  L ${right} ${t.y + t.h} C ${(left + right) / 2} ${t.y + t.h}, ${(left + right) / 2} ${b.y + b.h}, ${left} ${b.y + b.h} Z`}
              fill={BRAND.cyan}
              opacity={0.18}
            />
          );
        })}
        {tBands.map((b, i) => (
          <foreignObject key={`t-${i}`} x={right + 12} y={b.y} width={1080 - right - 12} height={b.h}>
            <Reveal at={buildTimings[1] ?? (buildTimings[0] ?? 0) + 600}>
              <div
                style={{
                  height: b.h,
                  display: 'flex',
                  alignItems: 'center',
                  fontFamily: BRAND.fontDisplay,
                  fontSize: 20,
                  color: BRAND.text,
                }}
              >
                {b.label}
              </div>
            </Reveal>
          </foreignObject>
        ))}
      </svg>
    </PanelFrame>
  );
};

// ── Registry + layer ─────────────────────────────────────────────────────────
const REGISTRY: Partial<Record<DiagramComponent, React.FC<any>>> = {
  AgentLoop,
  OldNewSplit,
  StackDiagram,
  WinnersLosers,
  Timeline,
  ApprovalQueue,
  Funnel,
  MapTopology,
  XRayReveal,
  SankeyFlow,
};

export const DiagramLayer: React.FC<{cues: DiagramCue[]}> = ({cues}) => {
  const {fps} = useVideoConfig();
  return (
    <>
      {cues.map((cue, i) => {
        const Comp = REGISTRY[cue.component];
        if (!Comp) return null;
        const fromFrame = msToFrames(cue.startMs, fps);
        const durationFrames = Math.max(1, msToFrames(cue.endMs - cue.startMs, fps));
        // Build timings are absolute ms in the global timeline; convert to local ms.
        const localBuild = (cue.buildTimings ?? []).map((t) => Math.max(0, t - cue.startMs));
        return (
          <Sequence key={i} from={fromFrame} durationInFrames={durationFrames}>
            <Comp {...(cue.props as any)} buildTimings={localBuild} />
          </Sequence>
        );
      })}
    </>
  );
};

export default DiagramLayer;
