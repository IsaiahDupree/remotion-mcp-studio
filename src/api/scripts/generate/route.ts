// F0214: API route timeout protection
export const maxDuration = 60; // 60 seconds for Claude API calls

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import Anthropic from '@anthropic-ai/sdk';
import { env } from '@/lib/env';
import { supabaseAdmin } from '@/lib/supabase';
import { extractUserId } from '@/lib/auth';
import { logAuditEvent } from '@/lib/audit';
import { checkRateLimit } from '@/lib/rate-limit';
import { sanitizeInput } from '@/lib/sanitize';

// F0002: Zod schema - topic field validation
// F0003: Zod schema - platform enum validation
// F0004: Zod schema - tone enum validation
// F0005: Zod schema - targetLength field validation
// F0006: Zod schema - optional audience_description field
// F0007: Zod schema - optional offer_cta field
// F0079: Zod schema - optional research_id field for stat injection
const scriptGenerationSchema = z.object({
  topic: z.string().min(5, 'Topic must be at least 5 characters').max(500, 'Topic must not exceed 500 characters'),
  platform: z.enum(['youtube', 'instagram', 'tiktok', 'linkedin'], {
    errorMap: () => ({ message: 'Platform must be one of: youtube, instagram, tiktok, linkedin' })
  }),
  tone: z.enum(['professional', 'casual', 'educational', 'entertaining', 'inspirational'], {
    errorMap: () => ({ message: 'Tone must be one of: professional, casual, educational, entertaining, inspirational' })
  }),
  targetLength: z.number().int().min(15, 'Target length must be at least 15 seconds').max(180, 'Target length must not exceed 180 seconds'),
  audienceDescription: z.string().optional(),
  offerCta: z.string().optional(),
  researchId: z.string().uuid().optional(),
});

type ScriptGenerationInput = z.infer<typeof scriptGenerationSchema>;

// F0001: POST /api/scripts/generate endpoint registration
export async function POST(request: NextRequest) {
  try {
    // F0009: Bearer token authentication
    // F0012: User ID extraction from bearer token
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

    // F0467: Rate limiting check (60 requests per minute per user)
    const rateLimitResult = await checkRateLimit(userId, 60);

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
            'X-RateLimit-Limit': '60',
            'X-RateLimit-Remaining': '0',
            'X-RateLimit-Reset': rateLimitResult.resetAt?.toISOString() || '',
            'Retry-After': retryAfterSeconds.toString(), // F0467: Standard HTTP Retry-After header in seconds
          },
        }
      );
    }

    const body = await request.json();

    // Validate request body
    const validationResult = scriptGenerationSchema.safeParse(body);

    // F0020: Error response envelope standardization
    if (!validationResult.success) {
      return NextResponse.json(
        {
          error: 'Validation failed',
          code: 'VALIDATION_ERROR',
          request_id: crypto.randomUUID(),
          details: validationResult.error.flatten()
        },
        { status: 422 }
      );
    }

    const input: ScriptGenerationInput = validationResult.data;

    // F0016: Input sanitization - strip HTML from topic
    const sanitizedTopic = sanitizeInput(input.topic);
    const sanitizedAudienceDescription = input.audienceDescription
      ? sanitizeInput(input.audienceDescription)
      : undefined;
    const sanitizedOfferCta = input.offerCta ? sanitizeInput(input.offerCta) : undefined;

    // F0013: Request audit log insert
    await logAuditEvent({
      event: 'script_generate_request',
      user_id: userId,
      metadata: {
        topic: sanitizedTopic,
        platform: input.platform,
        tone: input.tone,
        target_duration_sec: input.targetLength,
      },
    });

    // F0081: Research completion gates script generation
    // F0079: Fetch research findings if researchId provided, or automatically run research
    let researchStats: Array<{ stat: string; source_url: string }> = [];
    let researchQuotes: Array<{ quote: string; source_url: string }> = []; // F0080: Quote injection
    let researchId: string | null = input.researchId || null;

    // If no researchId provided, automatically trigger research expansion
    if (!researchId) {
      try {
        // Import perplexityClient
        const { perplexityClient } = await import('@/lib/perplexity');

        if (perplexityClient.isConfigured()) {
          // Check cache first (24h TTL)
          const cacheExpiry = new Date();
          cacheExpiry.setHours(cacheExpiry.getHours() - 24);

          const { data: cachedResearch } = await supabaseAdmin
            .from('research_findings')
            .select('id, stats, quotes_with_attribution')
            .eq('topic', sanitizedTopic)
            .gte('created_at', cacheExpiry.toISOString())
            .order('created_at', { ascending: false })
            .limit(1)
            .maybeSingle();

          if (cachedResearch) {
            researchId = cachedResearch.id;
            researchStats = cachedResearch.stats || [];
            researchQuotes = cachedResearch.quotes_with_attribution || [];
          } else {
            // Perform new research (F0085: pass userId for cost logging)
            const researchResult = await perplexityClient.researchTopic(sanitizedTopic, userId);

            // Save to database
            const { data: savedResearch } = await supabaseAdmin
              .from('research_findings')
              .insert({
                topic: sanitizedTopic,
                platform: input.platform,
                facts: researchResult.facts,
                statistics: researchResult.statistics,
                stats: researchResult.stats,
                quotes: researchResult.quotes,
                quotes_with_attribution: researchResult.quotesWithAttribution, // F0074
                sources: researchResult.sources,
                summary: researchResult.summary,
              })
              .select('id, stats, quotes_with_attribution')
              .single();

            if (savedResearch) {
              researchId = savedResearch.id;
              researchStats = savedResearch.stats || [];
              researchQuotes = savedResearch.quotes_with_attribution || [];
            }
          }
        }
      } catch (researchError) {
        // Log but don't fail - research is optional
        console.warn('Research expansion failed, continuing without stats:', researchError);
      }
    } else {
      // Fetch existing research
      const { data: research, error: researchError } = await supabaseAdmin
        .from('research_findings')
        .select('stats, quotes_with_attribution')
        .eq('id', researchId)
        .single();

      if (!researchError && research?.stats) {
        researchStats = research.stats;
        researchQuotes = research.quotes_with_attribution || [];
      }
    }

    // F0010: Claude API integration for script generation
    const apiKey = process.env.ANTHROPIC_API_KEY;

    if (!apiKey || apiKey === 'your_anthropic_api_key_here') {
      return NextResponse.json(
        {
          error: 'ANTHROPIC_API_KEY not configured',
          code: 'CONFIG_ERROR',
          request_id: crypto.randomUUID(),
        },
        { status: 500 }
      );
    }

    const anthropic = new Anthropic({
      apiKey: apiKey,
    });

    // F0035: Platform-specific prompt instructions injection
    const platformGuidelines = {
      youtube: `YouTube Shorts Guidelines:
- Structure: Hook (0-3s) → Problem (4-10s) → Solution chapters (11-50s) → CTA (last 10s)
- Chapters: Use 3-5 distinct "chapters" or segments that could be timestamped
- Pacing: Slower than TikTok, allow breathing room between points
- Hook: Question or bold statement that promises value
- CTA: "Subscribe for more" or link to longer content`,
      instagram: `Instagram Reels Guidelines:
- Pacing: FAST - change visuals every 2-3 seconds
- Hook: Immediate visual pattern interrupt (text overlay, quick cuts)
- Format: Vertical 9:16, assume no sound (captions mandatory)
- Trend awareness: Reference current Reels trends/memes if relevant
- CTA: "Save this" or "Share with a friend who needs this"`,
      tiktok: `TikTok Guidelines:
- Hook: Trending sound or viral hook format ("POV:", "Wait for it...", "Here's why...")
- Pacing: MAXIMUM speed - 2-3 words per second, rapid-fire delivery
- Trend hooks: Use current TikTok phraseology and formats
- Authenticity: Raw, unpolished feel > high production value
- CTA: "Follow for Part 2" or participatory challenge`,
      linkedin: `LinkedIn Video Guidelines:
- Tone: Professional, authoritative, value-first (no fluff)
- Structure: Clear problem statement → data/insight → actionable takeaway
- Hook: Lead with ROI, stats, or industry pain point
- Credibility: Reference experience, case studies, or concrete results
- CTA: "Comment your thoughts" or "DM me for the framework"`,
    };

    // F0036: Tone-specific prompt modifier injection
    const toneGuidelines = {
      professional: `Professional Tone:
- Formal language, industry-specific terminology
- Authoritative voice with data-backed statements
- Avoid casual contractions or slang
- Maintain credibility through precise language`,
      casual: `Casual Tone:
- Conversational language with contractions ("you're", "let's", "it's")
- Relatable examples from everyday life
- Friendly, approachable voice (like talking to a friend)
- Use simple analogies and avoid jargon`,
      educational: `Educational Tone:
- CITE SOURCES: Reference studies, experts, or data points
- EXPLAIN SIMPLY: Break complex concepts into digestible steps
- Use "First...", "Second...", "Finally..." structure
- Define any technical terms before using them
- Teach, don't preach - patient and clear explanations`,
      entertaining: `Entertaining Tone:
- HUMOR: Use wit, wordplay, or unexpected comparisons
- ENERGY: Dynamic pacing, exclamations, enthusiasm
- Storytelling elements: mini-narratives or scenarios
- Pop culture references where relevant
- Keep it light and engaging throughout`,
      inspirational: `Inspirational Tone:
- TRANSFORMATION NARRATIVE: Before → After journey
- Motivational language: "You can", "Imagine if", "What if"
- Success stories or triumph-over-adversity examples
- Aspirational future state painting
- Empowerment focus: viewer as the hero`,
    };

    // F0054: Prompt token budget enforcement - truncate audience_description if needed
    let audienceDescriptionForPrompt = sanitizedAudienceDescription || '';
    let truncatedAudience = false;

    // Estimate token count (rough: 1 token ≈ 4 characters)
    const estimateTokens = (text: string) => Math.ceil(text.length / 4);

    const ctaOverride = sanitizedOfferCta
      ? `\nCall-to-Action Override: Use this specific CTA: "${sanitizedOfferCta}"`
      : '';

    // F0037: Duration-aware word count target in prompt
    const targetWordCount = Math.round(input.targetLength * 2.5);
    const wordCountInstruction = `\nTarget Word Count: Write approximately ${targetWordCount} words (${input.targetLength} seconds at 2.5 words/sec)`;

    // Build prompt components for token estimation
    const platformText = `Platform: ${platformGuidelines[input.platform]}`;
    const toneText = `Tone: ${toneGuidelines[input.tone]}`;
    const fixedPromptParts = [
      platformText,
      toneText,
      `Target Length: ${input.targetLength} seconds`,
      wordCountInstruction,
      ctaOverride,
      'You are an expert content strategist...',
      `Generate a video script for: ${sanitizedTopic}`,
    ].join('\n');

    const fixedPromptTokens = estimateTokens(fixedPromptParts);
    const audienceTokens = estimateTokens(audienceDescriptionForPrompt);
    const totalEstimatedTokens = fixedPromptTokens + audienceTokens;

    // If exceeds 6000 token budget, truncate audience description
    const TOKEN_BUDGET = 6000;
    if (totalEstimatedTokens > TOKEN_BUDGET && audienceDescriptionForPrompt) {
      const excessTokens = totalEstimatedTokens - TOKEN_BUDGET;
      const maxAudienceChars = Math.max(0, audienceDescriptionForPrompt.length - (excessTokens * 4));
      const originalLength = audienceDescriptionForPrompt.length;

      if (maxAudienceChars < audienceDescriptionForPrompt.length) {
        audienceDescriptionForPrompt = audienceDescriptionForPrompt.slice(0, maxAudienceChars) + '...';
        truncatedAudience = true;

        console.warn('[Token Budget] Truncated audience_description', {
          originalLength,
          truncatedLength: audienceDescriptionForPrompt.length,
          estimatedTotalTokens: totalEstimatedTokens,
          tokenBudget: TOKEN_BUDGET,
        });
      }
    }

    const audienceContext = audienceDescriptionForPrompt
      ? `\nTarget Audience: ${audienceDescriptionForPrompt}`
      : '';

    // F0023: System prompt - expert content strategist persona
    // F0024: User prompt assembly from validated input
    // F0025: JSON mode - structured output requirement
    const systemPrompt = `You are an expert content strategist who writes platform-native scripts optimized for maximum engagement. No filler, no fluff.

Platform: ${platformGuidelines[input.platform]}
Tone: ${toneGuidelines[input.tone]}
Target Length: ${input.targetLength} seconds${wordCountInstruction}${audienceContext}${ctaOverride}

The script must include:
1. HOOK (first 3 seconds): Attention-grabbing opening
2. BODY (main content): 3 key points with examples
3. CTA (call-to-action): Clear next step for viewer

CRITICAL: You must respond with ONLY valid JSON. No markdown, no code blocks, no explanation. Just raw JSON.

Required JSON structure:
{
  "hook": "Opening line",
  "body_points": [
    {
      "point": "Main idea of section 1",
      "supporting_detail": "Evidence, example, or elaboration",
      "transition": "Bridge to next point"
    },
    {
      "point": "Main idea of section 2",
      "supporting_detail": "Evidence, example, or elaboration",
      "transition": "Bridge to next point"
    },
    {
      "point": "Main idea of section 3",
      "supporting_detail": "Evidence, example, or elaboration",
      "transition": "Bridge to CTA"
    }
  ],
  "cta": "Closing call-to-action",
  "estimatedDuration": seconds,
  "visualSuggestions": ["Visual cue 1", "Visual cue 2", "Visual cue 3"]
}`;

    // F0059: Retry on parse failure - attempt generation up to 2 times
    let scriptData;
    let parseAttempts = 0;
    const maxParseAttempts = 2;

    while (parseAttempts < maxParseAttempts) {
      parseAttempts++;
      const isRetryAttempt = parseAttempts > 1;

      // Append retry instruction if this is a retry
      const retryInstruction = isRetryAttempt
        ? '\n\nIMPORTANT: Previous response had invalid structure. Ensure all required fields are present: hook, body_points (array of exactly 3 objects, each with point, supporting_detail, and transition), cta, estimatedDuration, visualSuggestions.'
        : '';

      // F0079: Stat injection into prompt when research is available
      let statInjection = '';
      if (researchStats.length > 0) {
        const statLines = researchStats
          .map(s => `- ${s.stat} (Source: ${s.source_url})`)
          .join('\n');
        statInjection = `\n\nUse these verified facts in your script:\n${statLines}\n`;
      }

      // F0080: Quote injection into Claude script prompt
      let quoteInjection = '';
      if (researchQuotes.length > 0) {
        const quoteLines = researchQuotes
          .map(q => `- "${q.quote}" (Source: ${q.source_url})`)
          .join('\n');
        quoteInjection = `\n\nConsider incorporating these quotes for credibility:\n${quoteLines}\n`;
      }

      // F0022: Claude model selection: claude-sonnet-4-6
      // F0026: max_tokens set to 2000 for script generation
      // F0028: 30-second timeout on Anthropic API call
      // F0029: Retry on Anthropic overload errors with exponential backoff

      const delays = [1000, 2000, 4000]; // Backoff delays
      let message;
      let lastError: Error | null = null;

      // F0055: Track latency for cost monitoring
      let apiStartTime: number;
      let apiEndTime: number;

      for (let attempt = 0; attempt < 3; attempt++) {
        try {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 30000);

          // F0055: Record start time
          apiStartTime = Date.now();

          // Create a promise that races between the API call and timeout
          message = await Promise.race([
            anthropic.messages.create({
              model: 'claude-sonnet-4-6',
              max_tokens: 2000,
              temperature: 0.8, // F0027: Set to 0.8 for creative script output
              messages: [
                {
                  role: 'user',
                  content: `Generate a video script for: ${sanitizedTopic}${statInjection}${quoteInjection}${retryInstruction}`
                }
              ],
              system: systemPrompt,
            }),
            new Promise<never>((_, reject) => {
              controller.signal.addEventListener('abort', () => {
                reject(new Error('Anthropic API timeout (30 seconds exceeded)'));
              });
            })
          ]);

          // F0055: Record end time
          apiEndTime = Date.now();

          clearTimeout(timeoutId);
          break; // Success, exit retry loop

        } catch (error) {
          lastError = error as Error;

          // Check if it's an overload error (429 or 529)
          const isOverloadError = error instanceof Error && (
            error.message.includes('overload') ||
            error.message.includes('429') ||
            error.message.includes('529')
          );

          // Retry on overload errors if we have attempts left
          if (isOverloadError && attempt < 2) {
            console.warn(`Anthropic API overload (attempt ${attempt + 1}/3), retrying...`);
            await new Promise(resolve => setTimeout(resolve, delays[attempt]));
            continue;
          }

          // Don't retry on other errors
          if (!isOverloadError) {
            throw error;
          }

          // If we've exhausted retries, throw
          if (attempt === 2) {
            throw new Error('Anthropic API overloaded after 3 attempts');
          }
        }
      }

      if (!message) {
        throw lastError || new Error('Failed to generate script');
      }

      const contentBlock = message.content[0];
      if (contentBlock.type !== 'text') {
        throw new Error('Unexpected response format from Claude');
      }

      // Parse Claude's JSON response
      try {
        // Extract JSON from potential markdown code blocks
        const text = contentBlock.text;
        const jsonMatch = text.match(/```json\n([\s\S]*?)\n```/) || text.match(/\{[\s\S]*\}/);
        const jsonText = jsonMatch ? (jsonMatch[1] || jsonMatch[0]) : text;
        scriptData = JSON.parse(jsonText);

        // Validate required fields
        if (!scriptData.hook || !scriptData.cta) {
          throw new Error('Missing required fields (hook or cta) in parsed output');
        }

        // F0043: body_points must be exactly 3 objects
        if (!Array.isArray(scriptData.body_points) || scriptData.body_points.length !== 3) {
          throw new Error('body_points must be an array of exactly 3 objects');
        }

        // F0044, F0045, F0046: Validate each body_point has required fields
        for (let i = 0; i < scriptData.body_points.length; i++) {
          const bp = scriptData.body_points[i];
          // F0044: point field validation
          if (!bp.point || typeof bp.point !== 'string' || bp.point.trim() === '') {
            throw new Error(`body_points[${i}].point is missing or empty`);
          }
          // F0045: supporting_detail field validation
          if (!bp.supporting_detail || typeof bp.supporting_detail !== 'string' || bp.supporting_detail.trim() === '') {
            throw new Error(`body_points[${i}].supporting_detail is missing or empty`);
          }
          // F0046: transition field validation
          if (!bp.transition || typeof bp.transition !== 'string' || bp.transition.trim() === '') {
            throw new Error(`body_points[${i}].transition is missing or empty`);
          }
        }

        // Success! Break out of parse retry loop
        break;

      } catch (parseError) {
        console.warn(`Parse attempt ${parseAttempts} failed:`, parseError);

        // If this is the last attempt, use fallback
        if (parseAttempts === maxParseAttempts) {
          const lines = contentBlock.text.split('\n').filter(Boolean);
          scriptData = {
            hook: lines[0] || 'Check this out!',
            body_points: [
              {
                point: lines[1] || 'First key point',
                supporting_detail: lines[2] || 'Supporting detail for first point',
                transition: 'Moving to the next important aspect...'
              },
              {
                point: lines[3] || 'Second key point',
                supporting_detail: lines[4] || 'Supporting detail for second point',
                transition: 'And finally...'
              },
              {
                point: lines[5] || 'Third key point',
                supporting_detail: lines[6] || 'Supporting detail for third point',
                transition: 'So here\'s what to do next...'
              }
            ],
            cta: 'Like and follow for more!',
            estimatedDuration: input.targetLength,
            visualSuggestions: ['Dynamic text overlay', 'B-roll footage', 'Creator on camera'],
          };
          break;
        }

        // Otherwise, retry with instruction
        continue;
      }
    }

    // F0487: Save generated script to Supabase
    // F0050: script_text field - full assembled script
    const bodyText = scriptData.body_points.map((bp: any) =>
      `${bp.point}\n${bp.supporting_detail}\n${bp.transition}`
    ).join('\n\n');

    const scriptText = [
      scriptData.hook,
      bodyText,
      scriptData.cta
    ].join('\n\n');

    // F0051: word_count field computed from script_text
    const wordCount = scriptText
      .split(/\s+/)
      .filter(Boolean)
      .length;

    // F0052: Flesch-Kincaid readability score calculation
    const sentences = scriptText.split(/[.!?]+/).filter(Boolean).length;
    const syllables = wordCount * 1.5; // Rough approximation: 1.5 syllables per word
    const readabilityScore = Math.round(
      206.835 - 1.015 * (wordCount / Math.max(sentences, 1)) - 84.6 * (syllables / Math.max(wordCount, 1))
    );

    // F1018: Generate transcript_words for Remotion rendering
    const { distributeWordTiming } = await import('@/lib/caption-timing');
    const wordsArray = scriptText.split(/\s+/).filter(Boolean);
    const targetDurationSec = scriptData.estimatedDuration || input.targetLength;
    const transcriptWords = distributeWordTiming(wordsArray, targetDurationSec, 2.5);

    const { data: savedScript, error: dbError } = await supabaseAdmin
      .from('content_scripts')
      .insert({
        user_id: userId, // F0012: user_id from JWT
        hook: scriptData.hook, // F0041: hook field
        body_points: scriptData.body_points, // F0043-F0046: array of 3 objects with point, supporting_detail, transition
        cta: scriptData.cta, // F0047: cta field
        estimated_duration_sec: scriptData.estimatedDuration || input.targetLength,
        script_text: scriptText,
        word_count: wordCount,
        readability_score: readabilityScore,
        transcript_words: transcriptWords, // F1018: Store word-level timing for Remotion
        platform: input.platform,
        tone: input.tone,
        topic: sanitizedTopic, // F0016: sanitized topic
        status: 'DRAFT',
        regeneration_attempts: 0,
      })
      .select()
      .single();

    if (dbError) {
      console.error('Database error saving script:', dbError);
      return NextResponse.json(
        {
          error: 'Failed to save script to database',
          code: 'DB_ERROR',
          request_id: crypto.randomUUID(),
        },
        { status: 500 }
      );
    }

    // F0090: Link research finding to script via script_id
    if (researchId && savedScript?.id) {
      await supabaseAdmin
        .from('research_findings')
        .update({ script_id: savedScript.id })
        .eq('id', researchId)
        .then(({ error }) => {
          if (error) {
            console.error('Failed to link research to script:', error);
          }
        });
    }

    // F0055: Log latency and usage to script_costs table
    // F0030: Input token count logging for cost tracking
    if (message && apiStartTime! && apiEndTime!) {
      const latencyMs = apiEndTime! - apiStartTime!;
      const usage = (message as any).usage;
      const inputTokens = usage?.input_tokens || 0;
      const outputTokens = usage?.output_tokens || 0;
      const totalTokens = inputTokens + outputTokens;

      // Estimate cost based on Claude Sonnet 4.6 pricing
      // $3 per 1M input tokens, $15 per 1M output tokens
      const estimatedCostUsd = (inputTokens / 1_000_000) * 3 + (outputTokens / 1_000_000) * 15;

      const costRequestId = crypto.randomUUID();

      await supabaseAdmin
        .from('script_costs')
        .insert({
          user_id: userId,
          script_id: savedScript.id,
          request_id: costRequestId,
          model: 'claude-sonnet-4-6',
          input_tokens: inputTokens,
          output_tokens: outputTokens,
          total_tokens: totalTokens,
          latency_ms: latencyMs,
          estimated_cost_usd: estimatedCostUsd,
        })
        .then(({ error }) => {
          if (error) {
            console.error('Failed to log script costs:', error);
          }
        });
    }

    // F0082: Research findings returned in script generate response
    const researchFindings = researchStats.length > 0 || researchQuotes.length > 0
      ? {
          stats: researchStats,
          quotes: researchQuotes,
          research_id: researchId,
        }
      : undefined;

    // F0243: Log success metric (fire and forget)
    supabaseAdmin
      .from('script_generation_metrics')
      .insert({
        user_id: userId,
        status: 'success',
        created_at: new Date().toISOString(),
      })
      .then(({ error }) => {
        if (error) console.error('Failed to log success metric:', error);
      });

    // F0053: Full response envelope with all required fields
    return NextResponse.json({
      script_id: savedScript.id,
      hook: scriptData.hook,
      hook_type: scriptData.hook_type || 'question', // Default hook type
      body_points: scriptData.body_points, // F0043-F0046: array of 3 objects
      cta: scriptData.cta,
      cta_type: scriptData.cta_type || 'engagement', // Default CTA type
      script_text: scriptText,
      word_count: wordCount,
      estimated_duration_sec: scriptData.estimatedDuration || input.targetLength,
      readability_score: readabilityScore,
      research_findings: researchFindings,
      request_id: crypto.randomUUID(),
    });

  } catch (error) {
    console.error('Script generation error:', error);

    // F0243: Log failure metric (fire and forget)
    const userId = (await extractUserId(request)).user_id;
    if (userId) {
      supabaseAdmin
        .from('script_generation_metrics')
        .insert({
          user_id: userId,
          status: 'failure',
          error_message: error instanceof Error ? error.message : 'Unknown error',
          created_at: new Date().toISOString(),
        })
        .then(({ error: insertError }) => {
          if (insertError) console.error('Failed to log failure metric:', insertError);
        });
    }

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
