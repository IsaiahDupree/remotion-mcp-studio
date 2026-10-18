// F0413-F0420: TikTok adapter constants and utilities

/**
 * F0422: Hashtag reach tier list for sorting
 * Higher tier = higher estimated reach
 */
const HASHTAG_REACH_TIERS: Record<string, number> = {
  // Tier 1 (100M+ views)
  fyp: 1,
  foryou: 1,
  foryoupage: 1,
  viral: 1,
  trending: 1,

  // Tier 2 (10M-100M views)
  ai: 2,
  aiart: 2,
  contentcreation: 2,
  contentcreator: 2,
  marketing: 2,
  digitalmarketing: 2,
  socialmedia: 2,

  // Tier 3 (1M-10M views)
  saas: 3,
  tech: 3,
  startup: 3,
  entrepreneur: 3,
  business: 3,
  productivity: 3,
  automation: 3,

  // Tier 4 (100K-1M views)
  aitools: 4,
  nocode: 4,
  lowcode: 4,
  edtech: 4,

  // Tier 5 (<100K views) - niche/specific
  // All unlisted hashtags default to tier 5
};

/**
 * F0422: Get hashtag reach tier
 * @param hashtag - Hashtag without the # symbol
 * @returns Tier number (lower = higher reach)
 */
function getHashtagReachTier(hashtag: string): number {
  const normalized = hashtag.toLowerCase().replace(/[^a-z0-9]/g, '');
  return HASHTAG_REACH_TIERS[normalized] ?? 5; // Default to tier 5 (lowest reach)
}

/**
 * F0413: TikTok caption structure: hook + 3 hashtags
 * Max 2200 characters for caption
 */
export function getTikTokCaption(hook: string, hashtags: string[]): string {
  // F0413: Use first 3 hashtags inline with hook
  const topHashtags = hashtags.slice(0, 3);
  const hashtagString = topHashtags.map(tag => `#${tag}`).join(' ');

  const caption = `${hook} ${hashtagString}`.trim();

  // Ensure caption doesn't exceed 2200 chars
  if (caption.length > 2200) {
    return caption.substring(0, 2200);
  }

  return caption;
}

/**
 * F0413: TikTok first_comment for remaining hashtags
 * F0422: Sort remaining hashtags by estimated reach before placing in first_comment
 * If there are more than 3 hashtags, create a first_comment with the overflow
 */
export function getTikTokFirstComment(hashtags: string[]): string | null {
  if (hashtags.length > 3) {
    const overflowHashtags = hashtags.slice(3);

    // F0422: Sort by reach tier (lower tier number = higher reach)
    const sortedHashtags = [...overflowHashtags].sort((a, b) => {
      return getHashtagReachTier(a) - getHashtagReachTier(b);
    });

    return sortedHashtags.map(tag => `#${tag}`).join(' ');
  }

  return null;
}

/**
 * Complete TikTok publish payload interface
 */
export interface TikTokPublishPayload {
  caption: string;
  account_id: string;              // F0414
  media_url: string;
  first_comment?: string;          // F0413
  privacy_level: string;           // F0415
  duet_disabled: boolean;          // F0416
  stitch_disabled: boolean;        // F0417
  sound?: string;                  // F0420
  scheduled_for?: string;          // F0423: ISO 8601 timestamp for scheduled posting
  content_disclosure?: {           // F0426: Content disclosure settings
    your_brand: boolean;
    branded_content: boolean;
  };
}

/**
 * Build TikTok publish payload
 * F0414: account_id from environment variable
 * F0423: scheduled_for support for scheduled posting
 */
export interface BuildTikTokPayloadParams {
  hook: string;
  hashtags: string[];
  mediaUrl: string;
  voiceoverUrl?: string;           // F0420: original audio from voiceover
  scheduledFor?: string;           // F0423: ISO 8601 timestamp for scheduled posting
}

export function buildTikTokPayload(params: BuildTikTokPayloadParams): TikTokPublishPayload {
  // F0414: Get account_id from environment
  const accountId = process.env.BLOTATO_TIKTOK_ACCOUNT_ID || process.env.TIKTOK_ACCOUNT_ID;
  if (!accountId) {
    throw new Error('TikTok account ID not configured (TIKTOK_ACCOUNT_ID or BLOTATO_TIKTOK_ACCOUNT_ID)');
  }

  // F0413: Build caption with hook + 3 hashtags
  const caption = getTikTokCaption(params.hook, params.hashtags);

  // F0413: Create first_comment for overflow hashtags
  const firstComment = getTikTokFirstComment(params.hashtags);

  const payload: TikTokPublishPayload = {
    caption,
    account_id: accountId,
    media_url: params.mediaUrl,
    privacy_level: 'PUBLIC_TO_EVERYONE',  // F0415
    duet_disabled: false,                 // F0416
    stitch_disabled: false,               // F0417
    // F0426: Content disclosure settings (defaults to false for both)
    content_disclosure: {
      your_brand: false,
      branded_content: false,
    },
  };

  // F0413: Add first_comment if we have overflow hashtags
  if (firstComment) {
    payload.first_comment = firstComment;
  }

  // F0420: Add original audio from voiceover if provided
  if (params.voiceoverUrl) {
    payload.sound = params.voiceoverUrl;
  }

  // F0423: Add scheduled_for if provided
  if (params.scheduledFor) {
    payload.scheduled_for = params.scheduledFor;
  }

  return payload;
}
