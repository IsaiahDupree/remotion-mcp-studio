// F0168: POST /api/publish endpoint registration
// Publishes rendered video to multiple platforms via Blotato API

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { supabaseAdmin } from '@/lib/supabase';
import { extractUserId } from '@/lib/auth';
import { env } from '@/lib/env';
import { startPollingInBackground } from '@/lib/blotato-polling';
import { checkUserRateLimit } from '@/lib/rate-limit';

// F0169: Publish request body validation
const publishSchema = z.object({
  render_job_id: z.string().uuid('render_job_id must be a valid UUID'),
  platforms: z
    .array(z.enum(['instagram', 'tiktok', 'youtube', 'linkedin', 'facebook']))
    .min(1, 'At least one platform is required'),
  caption: z.string(),
  hashtags: z.array(z.string()).optional(),
  scheduled_for: z.string().datetime().optional(), // F0177: Optional scheduledFor field
});

type PublishInput = z.infer<typeof publishSchema>;

// F0175: Platform character limits
const PLATFORM_CAPTION_LIMITS: Record<string, number> = {
  instagram: 2200,
  tiktok: 2200,
  youtube: 5000,
  linkedin: 3000,
  facebook: 63206,
};

// F0171: Platform account IDs from environment
function getPlatformAccountId(platform: string): string | null {
  const accountIds: Record<string, string | undefined> = {
    instagram: env.blatoAccountInstagram,
    tiktok: env.blatoAccountTiktok,
    youtube: env.blatoAccountYoutube,
    linkedin: env.blatoAccountLinkedin,
    facebook: env.blatoAccountFacebook,
  };
  return accountIds[platform] || null;
}

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

    // F0467: Rate limiting check (10 requests per minute for publish endpoints)
    const rateLimitResult = await checkUserRateLimit(userId, true); // true = batch/publish endpoint

    if (!rateLimitResult.allowed) {
      // F0467: Calculate Retry-After in seconds
      const retryAfterSeconds = rateLimitResult.resetAt
        ? Math.ceil((rateLimitResult.resetAt.getTime() - Date.now()) / 1000)
        : 60;

      return NextResponse.json(
        {
          error: 'Rate limit exceeded',
          code: 'RATE_LIMIT_EXCEEDED',
          request_id: crypto.randomUUID(),
          retry_after: rateLimitResult.resetAt?.toISOString(),
          retry_after_seconds: retryAfterSeconds,
        },
        {
          status: 429,
          headers: {
            'X-RateLimit-Limit': '10',
            'X-RateLimit-Remaining': '0',
            'X-RateLimit-Reset': rateLimitResult.resetAt?.toISOString() || '',
            'Retry-After': retryAfterSeconds.toString(), // F0467: Standard HTTP Retry-After header in seconds
          },
        }
      );
    }

    const body = await request.json();
    const validationResult = publishSchema.safeParse(body);

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

    const input: PublishInput = validationResult.data;

    // Check Blotato API key
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

    // F0170: Retrieve mediaId from publish_jobs for render_job_id
    const { data: publishJobs, error: jobError } = await supabaseAdmin
      .from('publish_jobs')
      .select('id, media_id')
      .eq('render_job_id', input.render_job_id)
      .order('created_at', { ascending: false })
      .limit(1);

    if (jobError) {
      console.error('Database error fetching publish job:', jobError);
      return NextResponse.json(
        {
          error: 'Database error',
          code: 'DB_ERROR',
          request_id: crypto.randomUUID(),
        },
        { status: 500 }
      );
    }

    if (!publishJobs || publishJobs.length === 0 || !publishJobs[0].media_id) {
      return NextResponse.json(
        {
          error: 'Media not uploaded for this render job',
          code: 'media_not_uploaded',
          request_id: crypto.randomUUID(),
          details: {
            render_job_id: input.render_job_id,
          },
        },
        { status: 404 }
      );
    }

    const publishJobId = publishJobs[0].id;
    const mediaId = publishJobs[0].media_id;

    // F0176: Append hashtags to caption
    let fullCaption = input.caption;
    if (input.hashtags && input.hashtags.length > 0) {
      const hashtagsText = input.hashtags.map(tag => `#${tag.replace(/^#+/, '')}`).join(' ');
      fullCaption = `${input.caption}\n\n${hashtagsText}`;
    }

    // F0172: Post to Blotato /v2/posts for each platform
    // F1349: Collect publish_results for batch insert to avoid N+1 queries
    const results: Array<{
      platform: string;
      post_submission_id: string | null;
      status: 'SUCCESS' | 'FAILED';
      error?: string;
    }> = [];
    const publishResultsToInsert: Array<any> = [];

    for (const platform of input.platforms) {
      try {
        const accountId = getPlatformAccountId(platform);

        if (!accountId) {
          // Platform not configured
          results.push({
            platform,
            post_submission_id: null,
            status: 'FAILED',
            error: `No account ID configured for ${platform}`,
          });

          // F1349: Collect for batch insert
          publishResultsToInsert.push({
            publish_job_id: publishJobId,
            platform,
            account_id: null,
            post_submission_id: null,
            status: 'FAILED',
            error_message: `No account ID configured for ${platform}`,
          });

          continue;
        }

        // F0175: Truncate caption to platform limit
        const limit = PLATFORM_CAPTION_LIMITS[platform] || 5000;
        let platformCaption = fullCaption;
        if (platformCaption.length > limit) {
          platformCaption = platformCaption.substring(0, limit - 3) + '...';
        }

        // Build Blotato /v2/posts payload
        const postPayload: any = {
          mediaId,
          text: platformCaption,
          accountId,
        };

        // F0177: Add scheduledFor if provided
        if (input.scheduled_for) {
          postPayload.scheduledFor = input.scheduled_for;
        }

        // Make request to Blotato
        const postResponse = await fetch('https://backend.blotato.com/v2/posts', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'blotato-api-key': env.blatoApiKey,
          },
          body: JSON.stringify(postPayload),
        });

        if (!postResponse.ok) {
          const errorText = await postResponse.text();

          // F0180: Blotato 401 error handling
          if (postResponse.status === 401) {
            console.error(`❌ ALERT: Blotato authentication failed for ${platform}. Check API key.`);
            results.push({
              platform,
              post_submission_id: null,
              status: 'FAILED',
              error: 'Blotato authentication failed',
            });

            // F1349: Collect for batch insert
            publishResultsToInsert.push({
              publish_job_id: publishJobId,
              platform,
              account_id: accountId,
              post_submission_id: null,
              status: 'FAILED',
              error_message: 'Blotato authentication failed (401)',
            });

            continue;
          }

          // F0179: Handle per-platform errors
          console.error(`Blotato post failed for ${platform}:`, errorText);
          results.push({
            platform,
            post_submission_id: null,
            status: 'FAILED',
            error: `Blotato error (${postResponse.status}): ${errorText}`,
          });

          // F1349: Collect for batch insert
          publishResultsToInsert.push({
            publish_job_id: publishJobId,
            platform,
            account_id: accountId,
            post_submission_id: null,
            status: 'FAILED',
            error_message: `Blotato error (${postResponse.status}): ${errorText}`,
          });

          continue;
        }

        const postData = await postResponse.json();
        const postSubmissionId = postData.id || postData.postSubmissionId;

        console.log(`✓ Published to ${platform}: postSubmissionId=${postSubmissionId}`);

        results.push({
          platform,
          post_submission_id: postSubmissionId,
          status: 'SUCCESS',
        });

        // F1349: Collect for batch insert
        publishResultsToInsert.push({
          publish_job_id: publishJobId,
          platform,
          account_id: accountId,
          post_submission_id: postSubmissionId,
          scheduled_for: input.scheduled_for || null,
          status: 'SUCCESS',
        });

      } catch (error) {
        // F0179: Handle per-platform errors (continue processing other platforms)
        console.error(`Error posting to ${platform}:`, error);
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';

        results.push({
          platform,
          post_submission_id: null,
          status: 'FAILED',
          error: errorMessage,
        });

        // F1349: Collect for batch insert
        publishResultsToInsert.push({
          publish_job_id: publishJobId,
          platform,
          account_id: getPlatformAccountId(platform),
          post_submission_id: null,
          status: 'FAILED',
          error_message: errorMessage,
        });
      }
    }

    // F1349: Batch insert all publish_results in one query (avoid N+1)
    if (publishResultsToInsert.length > 0) {
      const { error: resultsError } = await supabaseAdmin
        .from('publish_results')
        .insert(publishResultsToInsert);

      if (resultsError) {
        console.error('Failed to insert publish_results:', resultsError);
      }
    }

    // Update publish_jobs status (initially PUBLISHING, polling will update later)
    const allSuccess = results.every(r => r.status === 'SUCCESS');
    const someSuccess = results.some(r => r.status === 'SUCCESS');

    await supabaseAdmin
      .from('publish_jobs')
      .update({
        status: allSuccess ? 'PUBLISHING' : someSuccess ? 'PARTIAL' : 'FAILED',
        completed_at: allSuccess ? null : new Date().toISOString(), // Only set completed_at if failed
      })
      .eq('id', publishJobId);

    // F0268: Auto-start polling after POST /api/publish
    if (someSuccess) {
      console.log(`Starting background polling for publish job ${publishJobId}`);
      startPollingInBackground(publishJobId);
    }

    // F0178: Publish success response
    return NextResponse.json({
      publish_job_id: publishJobId,
      results: results.map(r => ({
        platform: r.platform,
        post_submission_id: r.post_submission_id,
        status: r.status,
        error: r.error,
      })),
    });

  } catch (error) {
    console.error('Publish error:', error);
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
