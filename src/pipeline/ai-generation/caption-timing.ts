/**
 * Caption Timing Utilities
 *
 * F1001: Word-Level Timing Distribution Algorithm
 * F1002: Natural Pause Point Detection at Sentence-Ending Punctuation
 * F1004: chunkWordsToCaptionPages Function with maxWordsPerPage=6
 * F1014: CaptionPage Type Definition
 * F1021: Multi-Page Caption Sequencing Logic
 * F1024: Remaining Time Proportional Distribution
 */

import { TranscriptWord } from './ai-types';

// F1014: CaptionPage Type Definition
export interface CaptionPage {
  words: TranscriptWord[];
  startTime: number;
  endTime: number;
  text: string;
}

// F1002: Natural pause point detection at sentence-ending punctuation
function isSentenceEnding(word: string): boolean {
  return /[.!?]$/.test(word.trim());
}

// F1002: Check if word has comma (pause point)
function hasCommaPause(word: string): boolean {
  return /,$/.test(word.trim());
}

/**
 * F1001: Word-Level Timing Distribution Algorithm
 * F1002: Natural Pause Point Detection
 * F1186: Proportional Remaining Time Distribution
 *
 * Distributes timing across words with natural pauses:
 * - 300ms silence after sentence-ending punctuation (. ! ?)
 * - 150ms pause after commas
 * - Remaining time distributed proportionally to words without punctuation
 */
export function distributeWordTiming(
  words: string[],
  totalDurationSec: number,
  wordsPerSecond: number = 2.5
): TranscriptWord[] {
  const transcriptWords: TranscriptWord[] = [];
  let currentTime = 0;

  // Calculate base duration per word
  const baseDurationPerWord = 1 / wordsPerSecond;

  // F1186: Track total pauses separately
  let totalWordsDurationMs = 0;
  let silencePaddingTotal = 0;
  let pausePaddingTotal = 0;

  // First pass: calculate base timings and track pauses
  const wordTimings: { word: string; baseDuration: number; silencePause: number; commaPause: number }[] = [];

  for (const word of words) {
    const baseDuration = baseDurationPerWord * 1000; // Convert to ms
    let silencePause = 0;
    let commaPause = 0;

    totalWordsDurationMs += baseDuration;

    // F1184: Add silence padding for sentence endings
    if (isSentenceEnding(word)) {
      silencePause = 300; // 300ms
      silencePaddingTotal += silencePause;
    }
    // F1185: Add pause padding for commas
    else if (hasCommaPause(word)) {
      commaPause = 150; // 150ms
      pausePaddingTotal += commaPause;
    }

    wordTimings.push({ word: word.trim(), baseDuration, silencePause, commaPause });
  }

  // F1186: Compute remaining time to distribute
  const targetDurationMs = totalDurationSec * 1000;
  const remaining_ms = targetDurationMs - totalWordsDurationMs - silencePaddingTotal - pausePaddingTotal;

  // Count words without punctuation (they get the remaining time)
  const wordsWithoutPunctuation = wordTimings.filter(wt => wt.silencePause === 0 && wt.commaPause === 0);
  const extraTimePerWord = wordsWithoutPunctuation.length > 0 ? remaining_ms / wordsWithoutPunctuation.length : 0;

  // Second pass: apply timings with distributed remainder
  currentTime = 0;
  for (const wt of wordTimings) {
    const startMs = currentTime;
    const startInSeconds = startMs / 1000;

    // Add base word duration
    currentTime += wt.baseDuration;

    // F1186: Add proportional extra time to words without punctuation
    if (wt.silencePause === 0 && wt.commaPause === 0 && extraTimePerWord > 0) {
      currentTime += extraTimePerWord;
    }

    // Add pause times
    currentTime += wt.silencePause + wt.commaPause;

    // F1187: Compute endMs for each word
    const endMs = currentTime;
    const endInSeconds = endMs / 1000;

    transcriptWords.push({
      word: wt.word,
      startInSeconds,
      endInSeconds, // F1187
      startMs, // F1187
      endMs, // F1187
    });
  }

  return transcriptWords;
}

/**
 * F1004: chunkWordsToCaptionPages Function with maxWordsPerPage=6
 * F1021: Multi-Page Caption Sequencing Logic
 *
 * Chunks transcript words into caption pages with max 6 words per page.
 * Tries to break at sentence boundaries when possible.
 */
export function chunkWordsToCaptionPages(
  transcriptWords: TranscriptWord[],
  maxWordsPerPage: number = 6,
  totalDurationSec: number
): CaptionPage[] {
  const pages: CaptionPage[] = [];
  let currentChunk: TranscriptWord[] = [];

  for (let i = 0; i < transcriptWords.length; i++) {
    const word = transcriptWords[i];
    currentChunk.push(word);

    // Check if we should create a new page
    const shouldBreak =
      currentChunk.length >= maxWordsPerPage ||
      (isSentenceEnding(word.word) && currentChunk.length >= 3) ||
      i === transcriptWords.length - 1;

    if (shouldBreak) {
      const startTime = currentChunk[0].startInSeconds;
      const endTime =
        i < transcriptWords.length - 1
          ? transcriptWords[i + 1].startInSeconds
          : totalDurationSec;

      pages.push({
        words: [...currentChunk],
        startTime,
        endTime,
        text: currentChunk.map(w => w.word).join(' '),
      });

      currentChunk = [];
    }
  }

  return pages;
}

/**
 * Get the active word index at a given frame
 * Used for F1006: Karaoke Pop Mode Active Word Highlight
 */
export function getActiveWordIndex(
  words: TranscriptWord[],
  currentTimeInSeconds: number
): number {
  for (let i = words.length - 1; i >= 0; i--) {
    if (currentTimeInSeconds >= words[i].startInSeconds) {
      return i;
    }
  }
  return -1;
}

/**
 * Get the active caption page at a given frame
 */
export function getActiveCaptionPage(
  pages: CaptionPage[],
  currentTimeInSeconds: number
): CaptionPage | null {
  for (const page of pages) {
    if (
      currentTimeInSeconds >= page.startTime &&
      currentTimeInSeconds < page.endTime
    ) {
      return page;
    }
  }
  return null;
}

/**
 * F1181: word_count Derivation from script_text.split
 */
export function calculateWordCount(scriptText: string): number {
  return scriptText
    .split(/\s+/)
    .filter(word => word.trim().length > 0).length;
}

/**
 * F1183: Total Words Duration Formula
 * Duration = (word_count / words_per_second) + pause_time
 */
export function calculateTotalDuration(
  scriptText: string,
  wordsPerSecond: number = 2.5
): number {
  const words = scriptText.split(/\s+/).filter(w => w.trim().length > 0);
  const wordCount = words.length;

  // Base duration from word count
  let duration = wordCount / wordsPerSecond;

  // Add pause times
  words.forEach(word => {
    if (/[.!?]$/.test(word.trim())) {
      duration += 0.3; // Sentence ending pause
    } else if (/,$/.test(word.trim())) {
      duration += 0.15; // Comma pause
    }
  });

  return duration;
}
