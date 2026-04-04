/**
 * Shared TypeScript Type Definitions
 *
 * F1013: TranscriptWord Type Definition
 * F1110: Render Job Status Enum
 * F0291: PENDING_APPROVAL status enum extension
 * F0468: API error response schema
 */

// F1013: TranscriptWord Type Definition
export interface TranscriptWord {
  word: string;
  start: number; // Start time in seconds
  end: number; // End time in seconds
  startInSeconds: number; // Alias used by caption components
  confidence?: number; // 0-1 confidence score
}

// Remotion composition input props (migrated from remotion-props)
export interface RemotionInputProps {
  transcriptWords: TranscriptWord[];
  summaryStrapText: string;
  durationInSeconds: number;
  brandName: string;
  sourceVideoUrl?: string;
  videoStartMs?: number;
  videoEndMs?: number;
}

export interface Transcript {
  text: string;
  words: TranscriptWord[];
  language?: string;
  duration_sec?: number;
}

// F1110: Render Job Status Enum
export enum RenderJobStatus {
  QUEUED = 'QUEUED',
  PROCESSING = 'PROCESSING',
  COMPLETE = 'COMPLETE',
  FAILED = 'FAILED',
}

// F0291: Extended Content Job Status with PENDING_APPROVAL
export enum ExtendedContentJobStatus {
  QUEUED = 'QUEUED',
  RESEARCHING = 'RESEARCHING',
  SCRIPTING = 'SCRIPTING',
  PENDING_APPROVAL = 'PENDING_APPROVAL', // F0291: Manual review gate
  RENDERING = 'RENDERING',
  VOICEOVER = 'VOICEOVER',
  PUBLISHING = 'PUBLISHING',
  LIVE = 'LIVE',
  FAILED = 'FAILED',
}

// Platform types
export type Platform = 'youtube' | 'instagram' | 'tiktok' | 'linkedin';

export type Tone =
  | 'educational'
  | 'entertaining'
  | 'inspirational'
  | 'controversial'
  | 'storytelling';

// F0468: API Error Response Schema
export interface APIErrorResponse {
  error: string;
  code: string;
  request_id?: string;
  message?: string;
  details?: Record<string, any>;
  timestamp?: string;
}

export interface APISuccessResponse<T = any> {
  success: true;
  data: T;
  request_id?: string;
  timestamp?: string;
}

// Script types
export interface Script {
  id: string;
  topic: string;
  platform: Platform;
  tone: Tone;
  hook: string;
  hook_type?: string;
  body_points: string[];
  cta: string;
  cta_type?: string;
  word_count: number;
  estimated_duration_sec: number;
  readability_score?: number;
  script_text: string;
  visual_suggestions?: string[];
  created_at: string;
}

// Research types
export interface ResearchFinding {
  id: string;
  topic: string;
  stats?: Array<{
    value: string;
    description: string;
    source?: string;
    source_url?: string;
  }>;
  quotes?: Array<{
    text: string;
    attribution?: string;
    source?: string;
    source_url?: string;
  }>;
  citations?: string[];
  answer?: string;
  created_at: string;
}

// Render types
export interface RenderJob {
  id: string;
  script_id: string;
  composition_id: string;
  status: RenderJobStatus;
  progress_pct?: number;
  output_url?: string;
  error?: string;
  current_frame?: number;
  total_frames?: number;
  estimated_completion_sec?: number;
  created_at: string;
  completed_at?: string;
}

// Voiceover types
export interface VoiceoverJob {
  id: string;
  script_id: string;
  voice_id: string;
  status: 'QUEUED' | 'PROCESSING' | 'COMPLETE' | 'FAILED';
  audio_url?: string;
  duration_sec?: number;
  error?: string;
  created_at: string;
  completed_at?: string;
}

export interface Voice {
  voice_id: string;
  name: string;
  category?: string;
  description?: string;
  preview_url?: string;
  labels?: Record<string, string>;
}

// Publish types
export interface PublishJob {
  id: string;
  platforms: Platform[];
  caption: string;
  hashtags?: string[];
  scheduled_for?: string;
  video_url?: string;
  script_id?: string;
  status: 'QUEUED' | 'PROCESSING' | 'COMPLETE' | 'FAILED';
  created_at: string;
  completed_at?: string;
}

export interface PublishResult {
  platform: Platform;
  status: 'success' | 'failed';
  post_id?: string;
  post_url?: string;
  error?: string;
}

// Pipeline types
export interface PipelineRun {
  run_id: string;
  topic?: string;
  overall_status: 'pending' | 'in_progress' | 'complete' | 'failed';
  stages: {
    research?: PipelineStage;
    script?: PipelineStage;
    render?: PipelineStage;
    voiceover?: PipelineStage;
    publish?: PipelineStage;
  };
  created_at: string;
  completed_at?: string;
  total_duration_sec?: number;
}

export interface PipelineStage {
  name: string;
  status: 'pending' | 'in_progress' | 'complete' | 'failed';
  started_at?: string;
  completed_at?: string;
  error?: string;
  progress_pct?: number;
  metadata?: Record<string, any>;
}

// Job Events types (for audit/tracking)
export interface JobEvent {
  id: string;
  job_id: string;
  event_type: string;
  status: string;
  message?: string;
  metadata?: Record<string, any>;
  created_at: string;
}

// Health Check types
export interface ServiceHealth {
  status: 'healthy' | 'degraded' | 'unhealthy';
  latency_ms?: number;
  error?: string;
}

export interface HealthCheckResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  services: {
    anthropic?: ServiceHealth;
    perplexity?: ServiceHealth;
    elevenlabs?: ServiceHealth;
    blotato?: ServiceHealth;
    supabase?: ServiceHealth;
  };
  version: string;
}
