// F0931: Script utilities for word counting and text processing

/**
 * F0931: Estimate word count in a script
 * Counts the number of words by splitting on whitespace
 *
 * @param script The script text
 * @returns Word count
 */
export function estimateScriptWordCount(script: string): number {
  if (!script || script.trim().length === 0) {
    return 0;
  }

  // Split on whitespace and filter out empty strings
  const words = script.trim().split(/\s+/);
  return words.filter((word) => word.length > 0).length;
}

/**
 * Estimate reading time in seconds (assuming 150 words per minute)
 *
 * @param script The script text
 * @returns Reading time in seconds
 */
export function estimateReadingTime(script: string): number {
  const wordCount = estimateScriptWordCount(script);
  const wordsPerMinute = 150;
  const readingTimeMinutes = wordCount / wordsPerMinute;
  return Math.round(readingTimeMinutes * 60);
}
