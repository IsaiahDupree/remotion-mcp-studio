// F1166: Script Generation Prompt Template
// Produces a Claude prompt that generates JSON with: hook, body_points (array of 3), cta, estimated_duration_sec

export interface ScriptPromptOptions {
  topic: string;
  platform: 'youtube' | 'instagram' | 'tiktok' | 'linkedin';
  tone: 'professional' | 'casual' | 'educational' | 'entertaining' | 'inspirational';
  targetLength: number; // seconds
  audienceDescription?: string;
  offerCta?: string;
  researchStats?: Array<{ stat: string; source_url: string }>;
  researchQuotes?: Array<{ quote: string; source_url: string }>;
}

export interface ScriptGenerationOutput {
  hook: string;
  body_points: Array<{
    point: string;
    details: string;
    example?: string;
  }>;
  cta: string;
  estimated_duration_sec: number;
}

// F0035: Platform-specific prompt instructions
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

// F0036: Tone-specific prompt modifiers
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

/**
 * Generate a Claude prompt for script generation with platform and tone guidelines.
 * Returns a system prompt and user prompt that produces structured JSON output.
 *
 * F1166: Prompt template that produces JSON with:
 * - hook (string ≤20 words)
 * - body_points (array of 3 objects with point, details, example)
 * - cta (string)
 * - estimated_duration_sec (number)
 */
export function generateScriptPrompt(options: ScriptPromptOptions): {
  systemPrompt: string;
  userPrompt: string;
} {
  const {
    topic,
    platform,
    tone,
    targetLength,
    audienceDescription,
    offerCta,
    researchStats = [],
    researchQuotes = [],
  } = options;

  // F0037: Duration-aware word count target
  const targetWordCount = Math.round(targetLength * 2.5);
  const wordCountInstruction = `Target Word Count: Approximately ${targetWordCount} words (${targetLength} seconds at 2.5 words/sec)`;

  // Build research context if available
  let researchContext = '';
  if (researchStats.length > 0 || researchQuotes.length > 0) {
    researchContext = '\n\n## Research Data (Use these in your script):\n';

    if (researchStats.length > 0) {
      researchContext += '\nStatistics:\n';
      researchStats.forEach((stat, i) => {
        researchContext += `${i + 1}. ${stat.stat} (Source: ${stat.source_url})\n`;
      });
    }

    if (researchQuotes.length > 0) {
      researchContext += '\nQuotes:\n';
      researchQuotes.forEach((quote, i) => {
        researchContext += `${i + 1}. "${quote.quote}" (Source: ${quote.source_url})\n`;
      });
    }
  }

  const audienceContext = audienceDescription
    ? `\n\nTarget Audience: ${audienceDescription}`
    : '';

  const ctaOverride = offerCta
    ? `\n\nCall-to-Action Override: Use this specific CTA: "${offerCta}"`
    : '';

  // F0023: System prompt - expert content strategist persona
  const systemPrompt = `You are an expert content strategist who writes platform-native scripts optimized for maximum engagement. No filler, no fluff.

Platform: ${platformGuidelines[platform]}

Tone: ${toneGuidelines[tone]}

Target Length: ${targetLength} seconds
${wordCountInstruction}${audienceContext}${ctaOverride}

The script must include:
1. HOOK (first 3 seconds): Attention-grabbing opening (≤20 words)
2. BODY (main content): Exactly 3 key points with details and examples
3. CTA (call-to-action): Clear next step for viewer

CRITICAL: You must respond with ONLY valid JSON. No markdown, no code blocks, no explanation. Just raw JSON.

Required JSON structure:
{
  "hook": "Opening line (≤20 words)",
  "body_points": [
    {
      "point": "Main idea of section 1",
      "details": "Supporting explanation",
      "example": "Concrete example or analogy (optional)"
    },
    {
      "point": "Main idea of section 2",
      "details": "Supporting explanation",
      "example": "Concrete example or analogy (optional)"
    },
    {
      "point": "Main idea of section 3",
      "details": "Supporting explanation",
      "example": "Concrete example or analogy (optional)"
    }
  ],
  "cta": "Call-to-action line",
  "estimated_duration_sec": ${targetLength}
}`;

  // F0024: User prompt assembly from validated input
  const userPrompt = `Generate a ${targetLength}-second video script for: ${topic}${researchContext}

Remember:
- Hook must be ≤20 words
- Exactly 3 body points required
- Include concrete examples
- Match the ${tone} tone
- Optimize for ${platform}
- Output ONLY valid JSON (no markdown, no code blocks)`;

  return {
    systemPrompt,
    userPrompt,
  };
}

/**
 * Validate that Claude's response matches the expected schema.
 * Throws an error if validation fails.
 */
export function validateScriptOutput(output: any): ScriptGenerationOutput {
  if (!output || typeof output !== 'object') {
    throw new Error('Invalid script output: not an object');
  }

  if (typeof output.hook !== 'string') {
    throw new Error('Invalid script output: hook must be a string');
  }

  const hookWordCount = output.hook.split(/\s+/).length;
  if (hookWordCount > 20) {
    console.warn(`Hook exceeds 20 words (${hookWordCount} words): "${output.hook}"`);
  }

  if (!Array.isArray(output.body_points)) {
    throw new Error('Invalid script output: body_points must be an array');
  }

  if (output.body_points.length !== 3) {
    throw new Error(`Invalid script output: body_points must have exactly 3 elements, got ${output.body_points.length}`);
  }

  for (let i = 0; i < output.body_points.length; i++) {
    const point = output.body_points[i];
    if (!point || typeof point !== 'object') {
      throw new Error(`Invalid script output: body_points[${i}] is not an object`);
    }
    if (typeof point.point !== 'string' || typeof point.details !== 'string') {
      throw new Error(`Invalid script output: body_points[${i}] missing required fields`);
    }
  }

  if (typeof output.cta !== 'string') {
    throw new Error('Invalid script output: cta must be a string');
  }

  if (typeof output.estimated_duration_sec !== 'number') {
    throw new Error('Invalid script output: estimated_duration_sec must be a number');
  }

  return output as ScriptGenerationOutput;
}
