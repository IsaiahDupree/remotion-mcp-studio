// F0399-F0402 + F0411: Instagram adapter constants and utilities

/**
 * F0411: ConfigurationError for missing environment variables
 */
export class ConfigurationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ConfigurationError';
  }
}

/**
 * F0399: Instagram caption structure: hook + body + hashtags
 * F0408: Instagram caption emoji support - preserves emoji characters
 */
export function getInstagramCaption(hook: string, bodyPoints: string[], hashtags: string[]): string {
  const parts: string[] = [];

  // Hook (F0408: preserves emoji without encoding issues)
  parts.push(hook);

  // Body points
  if (bodyPoints.length > 0) {
    parts.push(bodyPoints.join('\n\n'));
  }

  // F0400: Hashtag count: 20-30 tags
  // Use first 30 hashtags if more provided
  const limitedHashtags = hashtags.slice(0, 30);
  const hashtagString = limitedHashtags.map(tag => `#${tag}`).join(' ');

  if (hashtagString.length > 0) {
    parts.push(hashtagString);
  }

  // F0408: Return string with emoji support (no encoding transformations)
  return parts.join('\n\n');
}

/**
 * F0401: Instagram first_comment for overflow hashtags
 * If there are more than 30 hashtags, create a first_comment with the overflow
 */
export function getInstagramFirstComment(hashtags: string[]): string | null {
  // F0400: If we have more than 30 hashtags, put the overflow in first_comment
  if (hashtags.length > 30) {
    const overflowHashtags = hashtags.slice(30);
    return overflowHashtags.map(tag => `#${tag}`).join(' ');
  }

  return null;
}

/**
 * Complete Instagram publish payload interface
 */
export interface InstagramPublishPayload {
  caption: string;
  account_id: string;           // F0402
  media_url: string;
  media_type: 'IMAGE' | 'VIDEO' | 'CAROUSEL_ALBUM';
  first_comment?: string;       // F0401
  cover_timestamp_ms?: number;  // F0403: Thumbnail timestamp (0 = first frame)
  scheduled_for?: string;       // F0409: ISO 8601 timestamp for scheduled posting
}

/**
 * Build Instagram publish payload
 * F0402: account_id from environment variable
 * F0409: scheduled_for support for scheduled Reel posting
 */
export interface BuildInstagramPayloadParams {
  hook: string;
  bodyPoints: string[];
  hashtags: string[];
  mediaUrl: string;
  mediaType?: 'IMAGE' | 'VIDEO' | 'CAROUSEL_ALBUM';
  scheduledFor?: string;  // F0409: ISO 8601 timestamp for scheduled posting
}

export function buildInstagramPayload(params: BuildInstagramPayloadParams): InstagramPublishPayload {
  // F0402 + F0411: Get account_id from environment
  // F0411: Read IG_BLOTATO_ACCOUNT_ID, throw ConfigurationError if missing
  const accountId = process.env.IG_BLOTATO_ACCOUNT_ID ||
                    process.env.BLOTATO_INSTAGRAM_ACCOUNT_ID ||
                    process.env.BLOTATO_ACCOUNT_INSTAGRAM;

  if (!accountId) {
    throw new ConfigurationError('IG_BLOTATO_ACCOUNT_ID environment variable is required for Instagram publishing');
  }

  // F0399: Build caption with hook + body + hashtags (first 30)
  const caption = getInstagramCaption(params.hook, params.bodyPoints, params.hashtags);

  // F0401: Create first_comment for overflow hashtags
  const firstComment = getInstagramFirstComment(params.hashtags);

  const payload: InstagramPublishPayload = {
    caption,
    account_id: accountId,
    media_url: params.mediaUrl,
    media_type: params.mediaType || 'VIDEO',
    cover_timestamp_ms: 0,  // F0403: Use first frame as thumbnail
  };

  // F0401: Add first_comment if we have overflow hashtags
  if (firstComment) {
    payload.first_comment = firstComment;
  }

  // F0409: Add scheduled_for if provided
  if (params.scheduledFor) {
    payload.scheduled_for = params.scheduledFor;
  }

  return payload;
}
