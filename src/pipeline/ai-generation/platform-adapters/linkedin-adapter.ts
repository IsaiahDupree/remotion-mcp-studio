// F0428-F0433: LinkedIn adapter constants and utilities

/**
 * LinkedIn caption structure: professional tone with hook + body
 * F0428: Professional tone enforcement (validation)
 */
export function getLinkedInCaption(hook: string, bodyPoints: string[], hashtags: string[]): string {
  const parts: string[] = [];

  // Hook
  parts.push(hook);

  // Body points
  if (bodyPoints.length > 0) {
    parts.push(bodyPoints.join('\n\n'));
  }

  // Hashtags (LinkedIn typically uses 3-5 hashtags)
  const linkedInHashtags = hashtags.slice(0, 5);
  const hashtagString = linkedInHashtags.map(tag => `#${tag}`).join(' ');

  if (hashtagString.length > 0) {
    parts.push(hashtagString);
  }

  return parts.join('\n\n');
}

/**
 * F0428: Validate professional tone
 * Simple validation that flags casual language indicators
 */
export function validateProfessionalTone(text: string): { isValid: boolean; issues: string[] } {
  const issues: string[] = [];
  const casualIndicators = [
    /\blol\b/i,
    /\blmao\b/i,
    /\byolo\b/i,
    /\bwanna\b/i,
    /\bgonna\b/i,
    /\bkinda\b/i,
    /\bsorta\b/i,
    /\byeah\b/i,
    /\bnope\b/i,
    /😂/,
    /🔥/,
    /💯/,
  ];

  for (const indicator of casualIndicators) {
    if (indicator.test(text)) {
      issues.push(`Contains casual language: ${indicator.source}`);
    }
  }

  return {
    isValid: issues.length === 0,
    issues,
  };
}

/**
 * Complete LinkedIn publish payload interface
 */
export interface LinkedInPublishPayload {
  caption: string;
  account_id: string;              // F0431
  media_url: string;
  visibility: string;              // F0433
  scheduled_for?: string;          // F0439: ISO 8601 timestamp for scheduled posting
}

/**
 * Build LinkedIn publish payload
 * F0431: account_id from environment variable
 * F0439: scheduled_for support for scheduled posting
 */
export interface BuildLinkedInPayloadParams {
  hook: string;
  bodyPoints: string[];
  hashtags: string[];
  mediaUrl: string;
  visibility?: string;             // F0433: Allow override
  scheduledFor?: string;           // F0439: ISO 8601 timestamp for scheduled posting
}

export function buildLinkedInPayload(params: BuildLinkedInPayloadParams): LinkedInPublishPayload {
  // F0431: Get account_id from environment
  const accountId = process.env.LI_BLOTATO_ACCOUNT_ID || process.env.LINKEDIN_ACCOUNT_ID;
  if (!accountId) {
    throw new Error('LinkedIn account ID not configured (LINKEDIN_ACCOUNT_ID or LI_BLOTATO_ACCOUNT_ID)');
  }

  // F0428: Validate professional tone
  const caption = getLinkedInCaption(params.hook, params.bodyPoints, params.hashtags);
  const validation = validateProfessionalTone(caption);

  if (!validation.isValid) {
    console.warn('LinkedIn caption contains casual language:', validation.issues);
    // Note: In production, this could trigger a Claude rewrite
    // For now, we log a warning but allow it to proceed
  }

  const payload: LinkedInPublishPayload = {
    caption,
    account_id: accountId,
    media_url: params.mediaUrl,
    visibility: params.visibility || 'PUBLIC',  // F0433: Default to PUBLIC
  };

  // F0439: Add scheduled_for if provided
  if (params.scheduledFor) {
    payload.scheduled_for = params.scheduledFor;
  }

  return payload;
}
