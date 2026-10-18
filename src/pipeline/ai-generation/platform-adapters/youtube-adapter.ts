// F0385: YouTube title format templates
// F0386-F0395: YouTube adapter constants and utilities

import { YouTubeValidationError } from './errors';

// F0388: Default YouTube category (27 = Education)
export const YOUTUBE_DEFAULT_CATEGORY = 27;

// F0389: Made for kids default
export const YOUTUBE_MADE_FOR_KIDS = false;

// F0393: Default privacy status
export const YOUTUBE_DEFAULT_PRIVACY = 'public' as const;

/**
 * F0385: Generate YouTube-optimized title from topic and format template
 * Enforces max 100 character limit
 */
export function getYouTubeTitle(topic: string, format?: 'how-to' | 'things-about' | 'guide'): string {
  let title: string;

  switch (format) {
    case 'how-to':
      // Format: "How to [Topic]"
      title = `How to ${topic}`;
      break;

    case 'things-about':
      // Format: "5 Things About [Topic]"
      title = `5 Things About ${topic}`;
      break;

    case 'guide':
      // Format: "The Ultimate [Topic] Guide"
      title = `The Ultimate ${topic} Guide`;
      break;

    default:
      // Use topic as-is if no format specified
      title = topic;
      break;
  }

  // F0385: Enforce max 100 character limit
  if (title.length > 100) {
    title = title.substring(0, 97) + '...';
  }

  return title;
}

/**
 * F0386: YouTube description 3-paragraph structure
 * F0397: YouTube description CTA customization from user_settings.youtube_cta_text
 * Creates a well-formatted description with hook, body, and CTA
 */
export function getYouTubeDescription(
  hook: string,
  bodyPoints: string[],
  cta?: string,
  customCta?: string  // F0397: Custom CTA from user_settings
): string {
  const paragraphs: string[] = [];

  // Paragraph 1: Hook
  paragraphs.push(hook);

  // Paragraph 2: Body (numbered points)
  if (bodyPoints.length > 0) {
    const bodyText = bodyPoints
      .map((point, index) => `${index + 1}. ${point}`)
      .join('\n');
    paragraphs.push(bodyText);
  }

  // Paragraph 3: CTA
  // F0397: Use customCta from user_settings if provided, fall back to explicit cta or default
  if (customCta) {
    paragraphs.push(customCta);
  } else if (cta) {
    paragraphs.push(cta);
  } else {
    paragraphs.push('👍 Like, Subscribe, and hit the bell for more!');
  }

  return paragraphs.join('\n\n');
}

/**
 * F0387: YouTube tags array from hashtags
 * Extracts tags from a hashtag string, removes # symbols
 */
export function getYouTubeTags(hashtagString: string): string[] {
  // Split by # and filter empty strings
  const tags = hashtagString
    .split('#')
    .map(tag => tag.trim())
    .filter(tag => tag.length > 0);

  return tags;
}

/**
 * F0392: Complete YouTube publish payload interface
 * F0398: Include default_language field
 */
export interface YouTubePublishPayload {
  title: string;
  description: string;
  tags: string[];
  category_id: number;           // F0388
  made_for_kids: boolean;         // F0389
  account_id: string;             // F0390
  privacy_status: 'public' | 'private' | 'unlisted';  // F0393
  thumbnail_url?: string;         // F0391
  schedule_time?: string;         // F0395 (ISO 8601 timestamp)
  default_language?: string;      // F0398 (e.g., 'en', 'es', 'fr')
}

/**
 * F0394: Validate YouTube-specific constraints before building payload
 */
export function validateYouTubePayload(payload: Partial<YouTubePublishPayload>): void {
  // F0394: Title validation
  if (payload.title) {
    if (payload.title.length > 100) {
      throw new YouTubeValidationError(
        'title',
        'max 100 characters',
        `Title exceeds 100 characters (${payload.title.length} chars)`
      );
    }
  }

  // F0394: Description validation
  if (payload.description) {
    if (payload.description.length > 5000) {
      throw new YouTubeValidationError(
        'description',
        'max 5000 characters',
        `Description exceeds 5000 characters (${payload.description.length} chars)`
      );
    }
  }

  // F0394: Tags validation
  if (payload.tags && Array.isArray(payload.tags)) {
    const totalTagsLength = payload.tags.join('').length;
    if (totalTagsLength > 500) {
      throw new YouTubeValidationError(
        'tags',
        'total max 500 characters',
        `Total tags length exceeds 500 characters (${totalTagsLength} chars)`
      );
    }
  }
}

/**
 * F0392: Build complete YouTube publish payload with validation
 * F0390: account_id from environment variable
 * F0398: Include defaultLanguage parameter
 */
export interface BuildYouTubePayloadParams {
  title: string;
  description: string;
  tags?: string[];
  categoryId?: number;
  madeForKids?: boolean;
  privacyStatus?: 'public' | 'private' | 'unlisted';
  thumbnailUrl?: string;
  scheduleTime?: string;
  defaultLanguage?: string;       // F0398: Override default language (defaults to 'en')
}

export function buildYouTubePayload(params: BuildYouTubePayloadParams): YouTubePublishPayload {
  // F0390: Get account_id from environment
  const accountId = process.env.BLOTATO_YOUTUBE_ACCOUNT_ID || process.env.YOUTUBE_ACCOUNT_ID;
  if (!accountId) {
    throw new Error('YouTube account ID not configured (YOUTUBE_ACCOUNT_ID or BLOTATO_YOUTUBE_ACCOUNT_ID)');
  }

  const payload: YouTubePublishPayload = {
    title: params.title,
    description: params.description,
    tags: params.tags || [],
    category_id: params.categoryId || YOUTUBE_DEFAULT_CATEGORY,  // F0388
    made_for_kids: params.madeForKids ?? YOUTUBE_MADE_FOR_KIDS,   // F0389
    account_id: accountId,                                         // F0390
    privacy_status: params.privacyStatus || YOUTUBE_DEFAULT_PRIVACY,  // F0393
    default_language: params.defaultLanguage || 'en',              // F0398: Defaults to 'en'
  };

  // F0391: Optional thumbnail URL
  if (params.thumbnailUrl) {
    payload.thumbnail_url = params.thumbnailUrl;
  }

  // F0395: Optional schedule time
  if (params.scheduleTime) {
    payload.schedule_time = params.scheduleTime;
  }

  // F0394: Validate before returning
  validateYouTubePayload(payload);

  return payload;
}
