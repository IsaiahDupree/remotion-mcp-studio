// F0156: POST /api/publish/upload-media endpoint registration
// Upload rendered video to Blotato and create publish job

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { supabaseAdmin } from '@/lib/supabase';
import { extractUserId } from '@/lib/auth';
import { env } from '@/lib/env';
import { validateAndCheckUrl } from '@/lib/url-validation';
import { promises as fs } from 'fs';
import path from 'path';

// F0157: upload-media request body validation
const uploadMediaSchema = z.object({
  output_url: z.string().url('output_url must be a valid URL'),
  render_job_id: z.string().uuid('render_job_id must be a valid UUID').optional(),
  platforms: z.array(z.enum(['youtube', 'instagram', 'tiktok', 'linkedin', 'facebook'])),
  caption: z.string().optional(),
  title: z.string().optional(),
  hashtags: z.array(z.string()).optional(),
});

type UploadMediaInput = z.infer<typeof uploadMediaSchema>;

export async function POST(request: NextRequest) {
  try {
    // Bearer token authentication
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
    const validationResult = uploadMediaSchema.safeParse(body);

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

    const input: UploadMediaInput = validationResult.data;

    // Check if Blotato API key is configured
    if (!env.blatoApiKey || env.blatoApiKey.includes('your_')) {
      return NextResponse.json(
        {
          error: 'Blotato API not configured',
          code: 'SERVICE_UNAVAILABLE',
          request_id: crypto.randomUUID(),
        },
        { status: 503 }
      );
    }

    // F0236: SSRF prevention - validate URL is not a private IP
    // F0237: Content-Length check before download - check file size
    const urlValidation = await validateAndCheckUrl(input.output_url, 500 * 1024 * 1024);

    if (!urlValidation.valid) {
      return NextResponse.json(
        {
          error: urlValidation.error || 'Invalid URL',
          code: 'INVALID_URL',
          request_id: crypto.randomUUID(),
        },
        { status: 422 }
      );
    }

    console.log(`URL validation passed: ${input.output_url} (${(urlValidation.size! / 1024 / 1024).toFixed(2)}MB)`);

    // F0158: Download video from output_url to temp file
    const tempFileName = `${crypto.randomUUID()}.mp4`;
    const tempFilePath = path.join('/tmp', tempFileName);

    console.log(`Downloading video from ${input.output_url} to ${tempFilePath}`);

    const downloadResponse = await fetch(input.output_url, {
      signal: AbortSignal.timeout(60000), // 60-second timeout
    });

    if (!downloadResponse.ok) {
      throw new Error(`Failed to download video: ${downloadResponse.statusText}`);
    }

    const videoBuffer = Buffer.from(await downloadResponse.arrayBuffer());

    // F0165: Supported video format validation: mp4 and mov
    const contentType = downloadResponse.headers.get('content-type') || '';
    const urlExt = input.output_url.split('.').pop()?.toLowerCase();
    const isValidFormat =
      contentType.includes('video/mp4') ||
      contentType.includes('video/quicktime') ||
      urlExt === 'mp4' ||
      urlExt === 'mov';

    if (!isValidFormat) {
      return NextResponse.json(
        {
          error: 'Unsupported video format. Only mp4 and mov are supported.',
          code: 'unsupported_format',
          request_id: crypto.randomUUID(),
          details: {
            contentType,
            extension: urlExt,
          },
        },
        { status: 422 }
      );
    }

    // F0164: Max video size validation: 500MB
    const maxSizeBytes = 500 * 1024 * 1024; // 500MB
    if (videoBuffer.length > maxSizeBytes) {
      return NextResponse.json(
        {
          error: `Video size exceeds ${maxSizeBytes / 1024 / 1024}MB limit`,
          code: 'VIDEO_TOO_LARGE',
          request_id: crypto.randomUUID(),
          details: {
            size: videoBuffer.length,
            limit: maxSizeBytes,
          },
        },
        { status: 422 }
      );
    }

    await fs.writeFile(tempFilePath, videoBuffer);

    // F0159, F0160, F0161, F0162: Upload to Blotato with retry
    // F0163: Ensure temp file cleanup via try-finally
    let mediaId: string | null = null;

    try {
      const maxAttempts = 3;
      let lastError: Error | null = null;

      for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
          console.log(`Blotato upload attempt ${attempt}/${maxAttempts}`);

          const formData = new FormData();
          const fileBlob = new Blob([videoBuffer], { type: 'video/mp4' });
          formData.append('file', fileBlob, 'video.mp4');

          // F0160: Blotato API key header: blotato-api-key (not Authorization Bearer)
          const uploadResponse = await fetch('https://backend.blotato.com/v2/media', {
            method: 'POST',
            headers: {
              'blotato-api-key': env.blatoApiKey,
            },
            body: formData,
          });

          if (!uploadResponse.ok) {
            const errorText = await uploadResponse.text();
            throw new Error(`Blotato upload failed (${uploadResponse.status}): ${errorText}`);
          }

          const uploadData = await uploadResponse.json();
          mediaId = uploadData.id || uploadData.mediaId;

          if (!mediaId) {
            throw new Error('Blotato response missing media ID');
          }

          console.log(`Blotato upload successful: mediaId=${mediaId}`);
          break; // Success!

        } catch (error) {
          lastError = error as Error;
          console.error(`Blotato upload attempt ${attempt} failed:`, error);

          if (attempt < maxAttempts) {
            // Exponential backoff: 1s, 2s, 4s
            await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, attempt - 1)));
          }
        }
      }

      if (!mediaId) {
        throw lastError || new Error('Failed to upload media to Blotato after 3 attempts');
      }

    } finally {
      // F0163: Clean up temp file after upload (success or failure)
      try {
        await fs.unlink(tempFilePath);
        console.log(`Temp file cleaned up: ${tempFilePath}`);
      } catch (cleanupError) {
        // Log cleanup failure but don't affect job status
        console.error(`Failed to clean up temp file ${tempFilePath}:`, cleanupError);
      }
    }

    // F0161: Store Blotato mediaId in publish_jobs Supabase row
    const { data: publishJob, error: dbError } = await supabaseAdmin
      .from('publish_jobs')
      .insert({
        user_id: userId,
        render_job_id: input.render_job_id || null,
        media_id: mediaId,
        platforms: input.platforms,
        caption: input.caption || '',
        title: input.title || '',
        hashtags: input.hashtags || [],
        status: 'PENDING',
      })
      .select()
      .single();

    if (dbError) {
      console.error('Database error creating publish job:', dbError);
      return NextResponse.json(
        {
          error: 'Failed to create publish job',
          code: 'DB_ERROR',
          request_id: crypto.randomUUID(),
        },
        { status: 500 }
      );
    }

    // F0166: upload-media success response: { mediaId, publish_job_id }
    return NextResponse.json({
      mediaId: mediaId,
      publish_job_id: publishJob.id,
    });

  } catch (error) {
    console.error('Upload media error:', error);
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
