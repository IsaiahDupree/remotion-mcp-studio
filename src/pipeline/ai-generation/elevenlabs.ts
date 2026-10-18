// F0133: ElevenLabs API client initialization

import { env } from './env';

const ELEVENLABS_BASE_URL = 'https://api.elevenlabs.io';

export interface VoiceSettings {
  stability: number;
  similarity_boost: number;
  style?: number;
  use_speaker_boost?: boolean;
}

export interface GenerateVoiceoverOptions {
  voice_id?: string;
  model_id?: string;
  voice_settings?: Partial<VoiceSettings>;
  speed?: number; // F0144: Speed adjustment for duration control (0.25 to 4.0)
}

class ElevenLabsClient {
  private apiKey: string | undefined;

  constructor(apiKey?: string) {
    this.apiKey = apiKey;
  }

  /**
   * Checks if ElevenLabs is configured
   */
  isConfigured(): boolean {
    return !!this.apiKey && !this.apiKey.includes('your_') && !this.apiKey.includes('_here');
  }

  /**
   * Generate voiceover from text
   * F0134: ElevenLabs voice settings - stability 0.5
   * F1136: Default voice from env variable
   */
  async generateVoiceover(
    text: string,
    options: GenerateVoiceoverOptions = {}
  ): Promise<ArrayBuffer> {
    if (!this.isConfigured()) {
      throw new Error('ELEVENLABS_API_KEY not configured');
    }

    const voiceId = options.voice_id || env.elevenlabsDefaultVoiceId; // F1136: Default from env
    const modelId = options.model_id || 'eleven_monolingual_v1';

    // F0134: Default voice settings with stability 0.5
    // F0136: style 0.0 (neutral, no exaggeration)
    // F0137: use_speaker_boost true (clarity enhancement)
    const voiceSettings: VoiceSettings = {
      stability: options.voice_settings?.stability ?? 0.5,
      similarity_boost: options.voice_settings?.similarity_boost ?? 0.75,
      style: options.voice_settings?.style ?? 0.0, // F0136: neutral style
      use_speaker_boost: options.voice_settings?.use_speaker_boost ?? true, // F0137: boost enabled
    };

    // F0144: Build request body with optional speed parameter
    const requestBody: {
      text: string;
      model_id: string;
      voice_settings: VoiceSettings;
      speed?: number;
    } = {
      text,
      model_id: modelId,
      voice_settings: voiceSettings,
    };

    // Add speed if provided (valid range 0.25 to 4.0)
    if (options.speed !== undefined) {
      requestBody.speed = Math.max(0.25, Math.min(4.0, options.speed));
    }

    const response = await fetch(
      `${ELEVENLABS_BASE_URL}/v1/text-to-speech/${voiceId}`,
      {
        method: 'POST',
        headers: {
          'xi-api-key': this.apiKey!,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      }
    );

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`ElevenLabs API error (${response.status}): ${errorText}`);
    }

    return response.arrayBuffer();
  }

  /**
   * Get available voices
   */
  async getVoices(): Promise<any[]> {
    if (!this.isConfigured()) {
      throw new Error('ELEVENLABS_API_KEY not configured');
    }

    const response = await fetch(`${ELEVENLABS_BASE_URL}/v1/voices`, {
      headers: {
        'xi-api-key': this.apiKey!,
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`ElevenLabs API error (${response.status}): ${errorText}`);
    }

    const data = await response.json();
    return data.voices || [];
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: 'healthy' | 'unhealthy'; error?: string }> {
    if (!this.isConfigured()) {
      return { status: 'unhealthy', error: 'ELEVENLABS_API_KEY not configured' };
    }

    try {
      await this.getVoices();
      return { status: 'healthy' };
    } catch (error) {
      return {
        status: 'unhealthy',
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * F1149: Validate API key on startup
   * Calls GET /v1/user to verify the API key is valid
   * Logs a warning if invalid but allows server to continue
   */
  async validateApiKey(): Promise<{ valid: boolean; error?: string }> {
    if (!this.isConfigured()) {
      return {
        valid: false,
        error: 'ELEVENLABS_API_KEY not configured or contains placeholder value',
      };
    }

    try {
      const response = await fetch(`${ELEVENLABS_BASE_URL}/v1/user`, {
        headers: {
          'xi-api-key': this.apiKey!,
        },
      });

      if (!response.ok) {
        const errorText = await response.text();
        return {
          valid: false,
          error: `ElevenLabs API key invalid (${response.status}): ${errorText}`,
        };
      }

      // API key is valid
      return { valid: true };
    } catch (error) {
      return {
        valid: false,
        error: error instanceof Error ? error.message : 'Unknown error validating API key',
      };
    }
  }

  /**
   * F1137: Check if script is too long (>4800 chars) and split if needed
   * F1138: Split at sentence boundaries for natural audio segmentation
   */
  splitLongScript(text: string, maxCharsPerSegment: number = 4800): string[] {
    if (text.length <= maxCharsPerSegment) {
      return [text];
    }

    const segments: string[] = [];
    let currentSegment = '';

    // F1138: Split at sentence boundaries
    const sentences = text.match(/[^.!?]+[.!?]+/g) || [text];

    for (const sentence of sentences) {
      // If single sentence is too long, force-split at comma or space
      if (sentence.length > maxCharsPerSegment) {
        if (currentSegment) {
          segments.push(currentSegment.trim());
          currentSegment = '';
        }

        // Try to split at commas first
        const parts = sentence.split(',');
        let acc = '';
        for (const part of parts) {
          if ((acc + part).length > maxCharsPerSegment) {
            if (acc) segments.push(acc.trim());
            acc = part;
          } else {
            acc += (acc ? ',' : '') + part;
          }
        }
        if (acc) segments.push(acc.trim());
        continue;
      }

      // Try to add sentence to current segment
      if ((currentSegment + sentence).length <= maxCharsPerSegment) {
        currentSegment += sentence;
      } else {
        if (currentSegment) {
          segments.push(currentSegment.trim());
        }
        currentSegment = sentence;
      }
    }

    if (currentSegment) {
      segments.push(currentSegment.trim());
    }

    return segments.length > 0 ? segments : [text];
  }

  /**
   * F1141: Concatenate MP3 segments using ffmpeg concat demuxer
   * Creates a concat_list.txt and runs: ffmpeg -f concat -safe 0 -i concat_list.txt -c copy output.mp3
   */
  private async concatWithFfmpeg(
    segmentPaths: string[],
    outputPath: string
  ): Promise<void> {
    const { promises: fs } = await import('fs');
    const { spawn } = await import('child_process');
    const path = await import('path');

    // F1141: Build ffmpeg concat demuxer input file
    const concatListPath = path.join('/tmp', `concat_list_${Date.now()}.txt`);
    const concatContent = segmentPaths.map(p => `file '${p}'`).join('\n');
    await fs.writeFile(concatListPath, concatContent);

    console.log(`✓ Created ffmpeg concat list at ${concatListPath}`);

    // F1141: Run ffmpeg -f concat -safe 0 -i concat_list.txt -c copy output.mp3
    return new Promise<void>((resolve, reject) => {
      const ffmpeg = spawn('ffmpeg', [
        '-f', 'concat',
        '-safe', '0',
        '-i', concatListPath,
        '-c', 'copy',
        outputPath,
        '-y', // Overwrite output file if exists
      ]);

      let stderr = '';

      ffmpeg.stderr?.on('data', (data) => {
        stderr += data.toString();
      });

      ffmpeg.on('close', async (code) => {
        // Clean up concat list file
        try {
          await fs.unlink(concatListPath);
        } catch (err) {
          console.warn('Failed to delete concat list:', err);
        }

        if (code === 0) {
          console.log(`✓ FFmpeg concat completed: ${outputPath}`);
          resolve();
        } else {
          reject(new Error(`FFmpeg concat failed with code ${code}: ${stderr}`));
        }
      });

      ffmpeg.on('error', (err) => {
        reject(new Error(`FFmpeg spawn error: ${err.message}`));
      });
    });
  }

  /**
   * F1139: Generate voiceover for long scripts by splitting and concatenating
   * Runs all segment API calls in parallel (F1139)
   * F1140: Download each audio segment to /tmp for filesystem persistence
   * F1141: Use ffmpeg concat demuxer for proper audio concatenation
   * F1142: Returns combined audio with total duration = sum of segments
   */
  async generateVoiceoverLongScript(
    text: string,
    options: GenerateVoiceoverOptions = {},
    jobId?: string
  ): Promise<{
    audioBuffer: ArrayBuffer;
    segments: Array<{ text: string; durationSec: number; filepath?: string }>;
    totalDurationSec: number;
  }> {
    const { promises: fs } = await import('fs');
    const path = await import('path');

    // Split script if needed
    const segments = this.splitLongScript(text);

    // F1145: Max Segments Guard - Warn if segments > 5
    if (segments.length > 5) {
      throw new Error(
        `Script too long: exceeds 5 segment maximum (${segments.length} segments required). ` +
        `Maximum script length is approximately 24000 characters (5 × 4800 chars/segment).`
      );
    }

    if (segments.length === 1) {
      // Single segment, no splitting needed
      const buffer = await this.generateVoiceover(text, options);

      // F1140: Save single segment to /tmp if jobId provided
      let filepath: string | undefined;
      if (jobId) {
        filepath = path.join('/tmp', `voiceover_${jobId}_seg0.mp3`);
        await fs.writeFile(filepath, Buffer.from(buffer));
        console.log(`✓ Saved single voiceover segment to ${filepath}`);
      }

      return {
        audioBuffer: buffer,
        segments: [{ text: segments[0], durationSec: 0, filepath }],
        totalDurationSec: 0,
      };
    }

    // F1139: Run all segment API calls in parallel
    const segmentPromises = segments.map((segment, index) =>
      this.generateVoiceover(segment, options)
        .then(async (buffer) => {
          // F1140: Download each audio segment to /tmp
          let filepath: string | undefined;
          if (jobId) {
            filepath = path.join('/tmp', `voiceover_${jobId}_seg${index}.mp3`);
            await fs.writeFile(filepath, Buffer.from(buffer));
            console.log(`✓ Saved voiceover segment ${index + 1}/${segments.length} to ${filepath}`);
          }
          return { buffer, index, filepath };
        })
        .catch(err => {
          console.error(`Segment ${index + 1} generation failed:`, err);
          return null;
        })
    );

    const audioResults = await Promise.all(segmentPromises);
    const validResults = audioResults.filter((item): item is { buffer: ArrayBuffer; index: number; filepath?: string } => item !== null);

    if (validResults.length === 0) {
      throw new Error('All segment generations failed');
    }

    // F1141: Use ffmpeg concat demuxer instead of binary concatenation
    const segmentPaths = validResults.map(r => r.filepath).filter((p): p is string => !!p);

    if (segmentPaths.length !== validResults.length) {
      throw new Error('Cannot concat: some segments were not saved to disk (missing jobId?)');
    }

    const outputPath = path.join('/tmp', `voiceover_${jobId}_final.mp3`);
    await this.concatWithFfmpeg(segmentPaths, outputPath);

    // Read concatenated file back into buffer
    const concatenatedBuffer = await fs.readFile(outputPath);

    // F1147: Upload concatenated voiceover to Supabase Storage
    // Note: This requires importing supabaseAdmin, which should be done at the top
    // For now, we'll just ensure the final file is available for the caller to upload

    // Build segment metadata
    const segmentData: Array<{ text: string; durationSec: number; filepath?: string }> = [];
    for (const { index, filepath } of validResults) {
      // F1142: Total duration = sum of segment durations (estimated)
      const segmentWordCount = segments[index].split(/\s+/).length;
      const segmentDurationSec = Math.ceil(segmentWordCount / 2.5);

      segmentData.push({
        text: segments[index],
        durationSec: segmentDurationSec,
        filepath,
      });
    }

    const totalDurationSec = segmentData.reduce((sum, seg) => sum + seg.durationSec, 0);

    return {
      audioBuffer: concatenatedBuffer.buffer,
      segments: segmentData,
      totalDurationSec,
    };
  }
}

// Export singleton instance
export const elevenlabsClient = new ElevenLabsClient(env.elevenlabsApiKey);
