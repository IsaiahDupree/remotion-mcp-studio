// F0131: POST /api/voiceover/generate endpoint registration
// F0214: API route timeout protection
// F1272: Explicitly use Node.js runtime for heavy operations
export const runtime = 'nodejs';
export const maxDuration = 60; // 60 seconds for ElevenLabs API calls

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { elevenlabsClient } from '@/lib/elevenlabs';
import { supabaseAdmin } from '@/lib/supabase';
import { extractUserId } from '@/lib/auth';
import { parseBuffer } from 'music-metadata'; // F0142: Audio duration extraction
import { env } from '@/lib/env'; // F1136: Default voice

// F0132 + F1136: Voiceover request body validation with env-based default voice
const voiceoverGenerateSchema = z.object({
  script_id: z.string().uuid('script_id must be a valid UUID'),
  voice_id: z.string().optional().default(env.elevenlabsDefaultVoiceId), // F1136: Default from env
  model_id: z.string().optional().default('eleven_monolingual_v1'),
  stability: z.number().min(0).max(1).optional(),
  similarity_boost: z.number().min(0).max(1).optional(),
});

type VoiceoverGenerateInput = z.infer<typeof voiceoverGenerateSchema>;

export async function POST(request: NextRequest) {
  try {
    // Bearer token authentication with JWT support
    const authResult = await extractUserId(request);

    if (!authResult.success) {
      return NextResponse.json(
        {
          error: authResult.error || 'Authentication failed',
          code: authResult.code || 'UNAUTHORIZED',
          request_id: crypto.randomUUID(),
        },
        { status: 401 }
      );
    }

    const userId = authResult.user_id!;

    const body = await request.json();
    const validationResult = voiceoverGenerateSchema.safeParse(body);

    if (!validationResult.success) {
      return NextResponse.json(
        {
          error: 'Validation failed',
          code: 'VALIDATION_ERROR',
          request_id: crypto.randomUUID(),
          details: validationResult.error.flatten(),
        },
        { status: 422 }
      );
    }

    const input: VoiceoverGenerateInput = validationResult.data;

    // Check if ElevenLabs is configured
    if (!elevenlabsClient.isConfigured()) {
      return NextResponse.json(
        {
          error: 'Voiceover service not configured',
          code: 'SERVICE_UNAVAILABLE',
          request_id: crypto.randomUUID(),
        },
        { status: 503 }
      );
    }

    // Fetch script
    const { data: scriptRecord, error: scriptError } = await supabaseAdmin
      .from('content_scripts')
      .select('id, script_text, hook, body_points, cta, estimated_duration_sec, word_count')
      .eq('id', input.script_id)
      .single();

    if (scriptError || !scriptRecord) {
      return NextResponse.json(
        {
          error: 'Script not found',
          code: 'SCRIPT_NOT_FOUND',
          request_id: crypto.randomUUID(),
        },
        { status: 404 }
      );
    }

    // F0155: Voiceover text character limit enforcement (5000 chars for ElevenLabs)
    if (scriptRecord.script_text.length > 5000) {
      return NextResponse.json(
        {
          error: 'Script text exceeds 5000 character limit for voiceover generation',
          code: 'TEXT_TOO_LONG',
          request_id: crypto.randomUUID(),
          details: {
            length: scriptRecord.script_text.length,
            limit: 5000,
          },
        },
        { status: 422 }
      );
    }

    // F0141: duration_sec estimate from word count (average 2.5 words per second)
    const estimatedDurationSec = Math.ceil((scriptRecord.word_count || 0) / 2.5);

    // Create voiceover job record
    const { data: voiceoverJob, error: jobError } = await supabaseAdmin
      .from('voiceover_jobs')
      .insert({
        script_id: input.script_id,
        voice_id: input.voice_id,
        model_id: input.model_id,
        status: 'QUEUED',
      })
      .select()
      .single();

    if (jobError) {
      console.error('Database error creating voiceover job:', jobError);
      return NextResponse.json(
        {
          error: 'Failed to create voiceover job',
          code: 'DB_ERROR',
          request_id: crypto.randomUUID(),
        },
        { status: 500 }
      );
    }

    // Generate voiceover with timeout and error handling
    try {
      // Update status to PROCESSING
      await supabaseAdmin
        .from('voiceover_jobs')
        .update({ status: 'PROCESSING', started_at: new Date().toISOString() })
        .eq('id', voiceoverJob.id);

      // F1137/F1147: Check if script is long and needs segmentation
      const isLongScript = scriptRecord.script_text.length > 4800;

      // F0153: 60-second timeout on voiceover generation
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 60000);

      let audioBuffer: ArrayBuffer;
      try {
        if (isLongScript) {
          // F1137-F1141: Use long script generation with segmentation and ffmpeg concat
          const result = await Promise.race([
            elevenlabsClient.generateVoiceoverLongScript(
              scriptRecord.script_text,
              {
                voice_id: input.voice_id,
                model_id: input.model_id,
                voice_settings: {
                  stability: input.stability,
                  similarity_boost: input.similarity_boost,
                },
              },
              voiceoverJob.id // F1140: Pass job ID for temp file naming
            ),
            new Promise<never>((_, reject) => {
              controller.signal.addEventListener('abort', () => {
                reject(new Error('Voiceover generation timeout (60 seconds exceeded)'));
              });
            })
          ]);
          audioBuffer = result.audioBuffer;
          console.log(`Generated long voiceover with ${result.segments.length} segments, total ${result.totalDurationSec}s`);
        } else {
          // F0134: Standard single-call generation for short scripts
          audioBuffer = await Promise.race([
            elevenlabsClient.generateVoiceover(
              scriptRecord.script_text,
              {
                voice_id: input.voice_id,
                model_id: input.model_id,
                voice_settings: {
                  stability: input.stability,
                  similarity_boost: input.similarity_boost,
                },
              }
            ),
            new Promise<never>((_, reject) => {
              controller.signal.addEventListener('abort', () => {
                reject(new Error('Voiceover generation timeout (60 seconds exceeded)'));
              });
            })
          ]);
        }
        clearTimeout(timeoutId);
      } catch (genError) {
        clearTimeout(timeoutId);

        // F0151: ElevenLabs 401 error handling (authentication failed)
        if (genError instanceof Error && genError.message.includes('401')) {
          await supabaseAdmin
            .from('voiceover_jobs')
            .update({
              status: 'FAILED',
              error_message: 'ElevenLabs authentication failed. Check API key.',
              completed_at: new Date().toISOString(),
            })
            .eq('id', voiceoverJob.id);

          return NextResponse.json(
            {
              error: 'ElevenLabs authentication failed',
              code: 'ELEVENLABS_AUTH_ERROR',
              request_id: crypto.randomUUID(),
            },
            { status: 401 }
          );
        }

        // F0152: ElevenLabs 429 error handling (rate limit)
        if (genError instanceof Error && genError.message.includes('429')) {
          await supabaseAdmin
            .from('voiceover_jobs')
            .update({
              status: 'FAILED',
              error_message: 'ElevenLabs rate limit exceeded',
              completed_at: new Date().toISOString(),
            })
            .eq('id', voiceoverJob.id);

          return NextResponse.json(
            {
              error: 'Rate limit exceeded',
              code: 'RATE_LIMIT_EXCEEDED',
              request_id: crypto.randomUUID(),
            },
            {
              status: 429,
              headers: {
                'Retry-After': '60', // Default 60 seconds
              },
            }
          );
        }

        throw genError;
      }

      // F0139: Save ElevenLabs audio stream to Supabase Storage
      // F1147: For long scripts, upload concatenated output to voiceovers/{user_id}/{job_id}.mp3
      // F0845: Retry up to 3 times with 2-second delay
      const fileName = `${voiceoverJob.id}.mp3`;
      const storagePath = `voiceovers/${userId}/${fileName}`; // F1147: Include user_id folder

      let uploadError = null;
      let uploadAttempts = 0;
      const maxAttempts = 3;

      while (uploadAttempts < maxAttempts) {
        uploadAttempts++;

        const { error } = await supabaseAdmin
          .storage
          .from('audio')
          .upload(storagePath, Buffer.from(audioBuffer), {
            contentType: 'audio/mpeg',
            upsert: true,
          });

        if (!error) {
          console.log(`[Voiceover] Audio upload successful on attempt ${uploadAttempts}`);
          uploadError = null;
          break;
        }

        uploadError = error;

        if (uploadAttempts < maxAttempts) {
          console.warn(`[Voiceover] Upload attempt ${uploadAttempts} failed, retrying in 2s...`, error);
          await new Promise(resolve => setTimeout(resolve, 2000));
        }
      }

      if (uploadError) {
        // F0845: Mark as FAILED with error_code='audio_storage_failed'
        await supabaseAdmin
          .from('voiceover_jobs')
          .update({
            status: 'FAILED',
            error_code: 'audio_storage_failed',
            error_message: `Storage upload failed after ${maxAttempts} attempts: ${uploadError.message}`,
          })
          .eq('id', voiceoverJob.id);

        throw new Error(`Failed to upload audio to storage after ${maxAttempts} attempts: ${uploadError.message}`);
      }

      // F0140: Get public URL for voiceover audio file
      const { data: publicUrlData } = supabaseAdmin
        .storage
        .from('audio')
        .getPublicUrl(storagePath);

      if (!publicUrlData?.publicUrl) {
        throw new Error('Failed to get public URL from Supabase Storage');
      }

      const audioUrl = publicUrlData.publicUrl;

      // F0142: Extract actual audio duration from MP3 metadata
      let actualDurationSec = estimatedDurationSec; // Default to estimate
      try {
        const metadata = await parseBuffer(Buffer.from(audioBuffer), { mimeType: 'audio/mpeg' });
        if (metadata.format.duration) {
          actualDurationSec = Math.round(metadata.format.duration * 100) / 100; // Round to 2 decimals
          console.log(`Audio duration: ${actualDurationSec}s (estimated: ${estimatedDurationSec}s)`);
        }
      } catch (metadataError) {
        console.warn('Failed to extract audio duration from metadata:', metadataError);
        // Continue with estimated duration
      }

      // F0143: Warn if duration deviation >10%
      const deviation = Math.abs(actualDurationSec - estimatedDurationSec) / estimatedDurationSec;
      if (deviation > 0.10) {
        console.warn(
          `⚠️  Audio duration deviation: ${(deviation * 100).toFixed(1)}% ` +
          `(actual: ${actualDurationSec}s, estimated: ${estimatedDurationSec}s)`
        );
      }

      // F0144: If deviation >20%, retry with speed adjustment (one retry max)
      if (deviation > 0.20) {
        console.log(
          `🔄 Retrying voiceover with speed adjustment (deviation: ${(deviation * 100).toFixed(1)}%)`
        );

        // Calculate corrected speed: speed = estimated / actual
        const correctedSpeed = estimatedDurationSec / actualDurationSec;
        console.log(`Adjusted speed: ${correctedSpeed.toFixed(2)}x`);

        try {
          // Retry generation with speed parameter
          const retryBuffer = await elevenlabsClient.generateVoiceover(
            scriptRecord.script_text,
            {
              voice_id: input.voice_id,
              model_id: input.model_id,
              voice_settings: {
                stability: input.stability,
                similarity_boost: input.similarity_boost,
              },
              speed: correctedSpeed, // F0144: Speed adjustment
            }
          );

          // Upload retry result to storage (overwrite original)
          const { error: retryUploadError } = await supabaseAdmin
            .storage
            .from('audio')
            .upload(storagePath, Buffer.from(retryBuffer), {
              contentType: 'audio/mpeg',
              upsert: true,
            });

          if (!retryUploadError) {
            // Extract duration from retry
            try {
              const retryMetadata = await parseBuffer(Buffer.from(retryBuffer), { mimeType: 'audio/mpeg' });
              if (retryMetadata.format.duration) {
                const retryDuration = Math.round(retryMetadata.format.duration * 100) / 100;
                console.log(`✅ Retry duration: ${retryDuration}s (original: ${actualDurationSec}s)`);
                // Use retry duration for final result
                actualDurationSec = retryDuration;
                audioBuffer = retryBuffer; // Update buffer reference
              }
            } catch (retryMetadataError) {
              console.warn('Failed to extract retry audio duration:', retryMetadataError);
              // Use retry result anyway, keep previous duration
            }
          }
        } catch (retryError) {
          console.error('Speed retry failed, using original audio:', retryError);
          // Continue with original audio if retry fails
        }
      }

      // Update job with completion
      await supabaseAdmin
        .from('voiceover_jobs')
        .update({
          status: 'COMPLETED',
          audio_url: audioUrl,
          audio_duration_sec: actualDurationSec, // F0142: Store actual duration
          estimated_duration_sec: estimatedDurationSec,
          chars_billed: scriptRecord.script_text.length, // F0147: Track characters billed
          completed_at: new Date().toISOString(),
        })
        .eq('id', voiceoverJob.id);

      // F0150: Voiceover generate success response envelope
      return NextResponse.json({
        voiceover_id: voiceoverJob.id,
        audio_url: audioUrl,
        estimated_duration_sec: estimatedDurationSec,
        actual_duration_sec: actualDurationSec, // F0142: Return actual duration
        chars_billed: scriptRecord.script_text.length,
        voice_id: input.voice_id,
      });

    } catch (error) {
      // Update job with error
      await supabaseAdmin
        .from('voiceover_jobs')
        .update({
          status: 'FAILED',
          error_message: error instanceof Error ? error.message : 'Unknown error',
          completed_at: new Date().toISOString(),
        })
        .eq('id', voiceoverJob.id);

      throw error;
    }

  } catch (error) {
    console.error('Voiceover generation error:', error);
    return NextResponse.json(
      {
        error: error instanceof Error ? error.message : 'Internal server error',
        code: 'INTERNAL_ERROR',
        request_id: crypto.randomUUID(),
      },
      { status: 500 }
    );
  }
}

// Return 405 for non-POST requests
export async function GET() {
  return NextResponse.json(
    {
      error: 'Method not allowed',
      code: 'METHOD_NOT_ALLOWED',
      request_id: crypto.randomUUID(),
    },
    { status: 405 }
  );
}
