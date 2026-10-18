// F0062: Perplexity API client initialization

import { env } from './env';
import { distance } from 'fastest-levenshtein';

const PERPLEXITY_BASE_URL = 'https://api.perplexity.ai';

export interface PerplexityQueryOptions {
  model?: string;
  maxTokens?: number;
  temperature?: number;
}

export interface PerplexityMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

export interface PerplexityResponse {
  id: string;
  model: string;
  choices: Array<{
    index: number;
    message: {
      role: string;
      content: string;
    };
    finish_reason: string;
  }>;
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

export interface StatWithSource {
  stat: string;
  source_url: string;
}

export interface QuoteWithAttribution {
  quote: string;
  source_url: string;
}

export interface ResearchResult {
  facts: string[];
  statistics: string[];
  stats: StatWithSource[]; // F0073: Top 3 stats with source URLs
  quotes: string[]; // F0072: Extracted quotes (legacy)
  quotesWithAttribution: QuoteWithAttribution[]; // F0074: Top 2 quotes with attribution
  sources: string[];
  summary: string;
}

// F1151: Query templates for topic expansion
export interface ExpandedQueryTemplates {
  queries: string[];
  templates: string[];
}

// F1157: Raw query results storage
export interface RawQueryResult {
  query: string;
  response: PerplexityResponse;
  extractedStats: StatWithSource[];
  extractedQuotes: QuoteWithAttribution[];
}

class PerplexityClient {
  private apiKey: string | undefined;

  constructor(apiKey?: string) {
    this.apiKey = apiKey;
  }

  /**
   * Checks if Perplexity is configured
   */
  isConfigured(): boolean {
    return !!this.apiKey && !this.apiKey.includes('your_') && !this.apiKey.includes('_here');
  }

  /**
   * Query Perplexity API
   * F0063/F1161: sonar-medium-online model selection for up-to-date web-grounded responses
   * F0065: return_citations flag set to true
   * F0066: max_tokens set to 1000
   * F0067: 20-second timeout on API call
   * F0068: Retry logic with 3 attempts and backoff
   */
  async query(
    messages: PerplexityMessage[],
    options: PerplexityQueryOptions = {}
  ): Promise<PerplexityResponse> {
    if (!this.isConfigured()) {
      throw new Error('PERPLEXITY_API_KEY not configured');
    }

    const model = options.model || 'sonar-medium-online'; // F1161: Use sonar-medium-online by default
    const maxTokens = options.maxTokens || 1000;

    // F0068: Retry with backoff: 1s, 2s, 4s
    const delays = [1000, 2000, 4000];
    let lastError: Error | null = null;

    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        // F0067: 20-second timeout
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 20000);

        const response = await fetch(`${PERPLEXITY_BASE_URL}/chat/completions`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${this.apiKey}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            model,
            messages,
            max_tokens: maxTokens,
            temperature: options.temperature || 0.2,
            return_citations: true,
            return_images: false,
          }),
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const errorText = await response.text();

          // F0088: Handle 429 rate limit - propagate immediately
          if (response.status === 429) {
            throw new Error(`Perplexity API error (429): Rate limit exceeded`);
          }

          // Retry on 5xx errors
          if (response.status >= 500 && attempt < 2) {
            console.warn(`Perplexity API 5xx error (attempt ${attempt + 1}/3):`, errorText);
            await new Promise(resolve => setTimeout(resolve, delays[attempt]));
            continue;
          }
          console.error(`Perplexity API error with model ${model}:`, errorText);
          throw new Error(`Perplexity API error (${response.status}): ${errorText}`);
        }

        return response.json();

      } catch (error) {
        lastError = error as Error;

        // Handle abort timeout
        if (error instanceof Error && error.name === 'AbortError') {
          throw new Error('Perplexity API timeout (20 seconds exceeded)');
        }

        // Retry on network errors
        if (attempt < 2) {
          console.warn(`Perplexity API network error (attempt ${attempt + 1}/3):`, error);
          await new Promise(resolve => setTimeout(resolve, delays[attempt]));
          continue;
        }

        throw error;
      }
    }

    throw lastError || new Error('Perplexity API failed after 3 attempts');
  }

  /**
   * Research a topic and extract facts, statistics, and sources
   * F0064: Perplexity query construction with topic and year range
   * F0085: Log Perplexity API costs to research_costs table
   */
  async researchTopic(topic: string, userId?: string): Promise<ResearchResult> {
    if (!this.isConfigured()) {
      throw new Error('PERPLEXITY_API_KEY not configured');
    }

    // F0064: Sanitize topic - strip HTML and truncate to 300 chars
    const sanitizedTopic = topic
      .replace(/<[^>]*>/g, '') // Remove HTML tags
      .replace(/&[^;]+;/g, '') // Remove HTML entities
      .trim()
      .substring(0, 300);

    // F0064: Build query with topic and year range
    const query = `${sanitizedTopic} statistics facts data 2024 2025`;

    const response = await this.query([
      {
        role: 'system',
        content: 'You are a research assistant. Extract key facts, statistics, and credible sources about the given topic. Focus on recent, verifiable information.',
      },
      {
        role: 'user',
        content: `Research this topic and provide:
1. 5-10 key facts
2. 3-5 relevant statistics with sources
3. 3-5 credible source URLs
4. A 2-3 sentence summary

Topic: ${query}

Format your response as JSON:
{
  "facts": ["fact 1", "fact 2", ...],
  "statistics": ["stat 1 (source)", "stat 2 (source)", ...],
  "sources": ["https://...", "https://...", ...],
  "summary": "Summary text..."
}`,
      },
    ]);

    // F0085: Log Perplexity API cost
    if (userId && response.usage) {
      try {
        const { supabaseAdmin } = await import('./supabase');
        const { topicHash: generateTopicHash } = await import('./utils/hash');

        // F0934: Create topic hash for deduplication (case-insensitive)
        const topicHashValue = generateTopicHash(sanitizedTopic);

        // Perplexity pricing: ~$1 per 1M tokens (estimate)
        const totalTokens = response.usage.total_tokens;
        const estimatedCost = (totalTokens / 1_000_000) * 1;

        await supabaseAdmin
          .from('research_costs')
          .insert({
            user_id: userId,
            topic: sanitizedTopic,
            topic_hash: topicHashValue,
            model: response.model || 'sonar-medium-online', // F1161
            tokens_used: totalTokens,
            estimated_cost_usd: estimatedCost,
          });
      } catch (error) {
        console.error('Failed to log research costs:', error);
        // Don't throw - cost logging is non-critical
      }
    }

    // F0070: Extract answer text from Perplexity response
    const content = response.choices[0]?.message?.content;
    if (!content) {
      console.warn('No content returned from Perplexity');
      return {
        facts: [],
        statistics: [],
        stats: [],
        quotes: [],
        quotesWithAttribution: [],
        sources: [],
        summary: '',
      };
    }

    // F0069: Extract citations array from Perplexity response
    const citations = (response as any).citations || [];
    if (citations.length > 0) {
      console.log(`Perplexity returned ${citations.length} citations`);
    }

    // F0072: Quote extraction - regex for quoted text patterns
    const quoteRegex = /"([^"]{10,200})"|"([^"]{10,200})"|"([^"]{10,200})"/g;
    const quoteMatches: string[] = [];
    let quoteMatch;
    while ((quoteMatch = quoteRegex.exec(content)) !== null) {
      const quote = quoteMatch[1] || quoteMatch[2] || quoteMatch[3];
      if (quote && quote.trim().length >= 10) {
        quoteMatches.push(quote.trim());
      }
    }

    // F0074: Top 2 quotes selection with attribution (source URL)
    const quotesWithAttribution: QuoteWithAttribution[] = [];
    const topQuotes = quoteMatches
      .sort((a, b) => b.length - a.length) // Prefer longer, more substantive quotes
      .slice(0, 2); // Top 2 quotes

    for (const quote of topQuotes) {
      quotesWithAttribution.push({
        quote,
        source_url: citations[0] || '', // Associate with first citation (best available)
      });
    }

    // F0071: Stat extraction - regex for numbers and percentages
    const statRegex = /(?:\b\w+\s+){0,5}(\d+(?:\.\d+)?%?)(?:\s+\w+){0,5}/g;
    const statMatches = content.match(statRegex) || [];
    const extractedStats = statMatches
      .slice(0, 10)
      .map(match => match.trim())
      .filter(stat => stat.length > 5); // Filter out very short matches

    // F0073: Top 3 stats selection with source URL association
    // F0075: Stat deduplication by text similarity using Levenshtein distance
    const statsWithSources: StatWithSource[] = [];
    const sortedStats = extractedStats.sort((a, b) => b.length - a.length); // Prefer longer, more specific stats

    for (const stat of sortedStats) {
      // F0075: Check if this stat is too similar to any already-selected stat
      const isDuplicate = statsWithSources.some(existing => {
        const maxLen = Math.max(stat.length, existing.stat.length);
        if (maxLen === 0) return false;

        const lev = distance(stat.toLowerCase(), existing.stat.toLowerCase());
        const similarity = 1 - (lev / maxLen);

        // Discard if >80% similar
        return similarity > 0.8;
      });

      if (!isDuplicate) {
        statsWithSources.push({
          stat,
          source_url: citations[0] || '',
        });

        // Stop after collecting 3 unique stats
        if (statsWithSources.length >= 3) {
          break;
        }
      }
    }

    // Extract JSON from potential markdown code blocks
    const jsonMatch = content.match(/```json\n([\s\S]*?)\n```/) || content.match(/\{[\s\S]*\}/);
    const jsonText = jsonMatch ? (jsonMatch[1] || jsonMatch[0]) : content;

    try {
      const parsed = JSON.parse(jsonText);

      // Merge extracted citations into sources
      const sources = Array.from(new Set([
        ...(parsed.sources || []),
        ...citations
      ])).slice(0, 10); // Limit to 10 sources

      return {
        facts: parsed.facts || [],
        statistics: parsed.statistics || extractedStats,
        stats: statsWithSources,
        quotes: quoteMatches.slice(0, 5), // Top 5 quotes (legacy)
        quotesWithAttribution, // F0074: Top 2 with attribution
        sources,
        summary: parsed.summary || content.substring(0, 500),
      };
    } catch (error) {
      // Fallback: use extracted data
      return {
        facts: [],
        statistics: extractedStats,
        stats: statsWithSources,
        quotes: quoteMatches.slice(0, 5),
        quotesWithAttribution, // F0074: Top 2 with attribution
        sources: citations.slice(0, 10),
        summary: content.substring(0, 500),
      };
    }
  }

  /**
   * F1151: Generate 3 expanded query templates from a topic
   */
  generateExpandedQueries(topic: string): ExpandedQueryTemplates {
    const sanitizedTopic = topic
      .replace(/<[^>]*>/g, '')
      .replace(/&[^;]+;/g, '')
      .trim()
      .substring(0, 300);

    // F1151: Three query templates
    const templates = [
      `${sanitizedTopic} statistics data 2025`,
      `${sanitizedTopic} research findings expert insights`,
      `${sanitizedTopic} industry trends case studies`,
    ];

    return {
      queries: templates,
      templates: [
        'statistics',
        'research_and_insights',
        'trends_and_cases',
      ],
    };
  }

  /**
   * F1152: Run 3 expanded queries in parallel
   * F1157: Store raw query results
   */
  async researchTopicExpanded(topic: string, userId?: string): Promise<{
    result: ResearchResult;
    rawQueries: RawQueryResult[];
  }> {
    if (!this.isConfigured()) {
      throw new Error('PERPLEXITY_API_KEY not configured');
    }

    // F1151: Generate expanded queries
    const { queries } = this.generateExpandedQueries(topic);

    // F1152: Run queries in parallel
    const queryPromises = queries.map(query =>
      this.query([
        {
          role: 'system',
          content: 'You are a research assistant. Extract key facts, statistics, and credible sources. Focus on recent, verifiable information.',
        },
        {
          role: 'user',
          content: `Research this topic and provide:
1. 5-10 key facts
2. 3-5 relevant statistics with sources
3. 3-5 credible source URLs
4. A 2-3 sentence summary

Topic: ${query}

Format your response as JSON:
{
  "facts": ["fact 1", "fact 2", ...],
  "statistics": ["stat 1 (source)", "stat 2 (source)", ...],
  "sources": ["https://...", "https://...", ...],
  "summary": "Summary text..."
}`,
        },
      ]).catch(err => {
        console.warn(`Query failed: ${query}`, err);
        return null;
      })
    );

    const responses = await Promise.all(queryPromises);
    const validResponses = responses.filter((r): r is PerplexityResponse => r !== null);

    // F1153-1156: Merge and deduplicate results
    const rawQueries: RawQueryResult[] = [];
    const allStats: StatWithSource[] = [];
    const allQuotes: QuoteWithAttribution[] = [];
    const allFacts: string[] = [];
    const allSources: Set<string> = new Set();

    for (let i = 0; i < validResponses.length; i++) {
      const response = validResponses[i];
      const query = queries[i];
      const content = response.choices[0]?.message?.content || '';
      const citations = (response as any).citations || [];

      // Extract stats, quotes, facts from each response
      const statRegex = /(?:\b\w+\s+){0,5}(\d+(?:\.\d+)?%?)(?:\s+\w+){0,5}/g;
      const stats = (content.match(statRegex) || [])
        .slice(0, 5)
        .map(s => ({ stat: s.trim(), source_url: citations[0] || '' }));

      allStats.push(...stats);

      const quoteRegex = /"([^"]{10,200})"/g;
      let quoteMatch;
      while ((quoteMatch = quoteRegex.exec(content)) !== null) {
        const quote = quoteMatch[1];
        if (quote && quote.trim().length >= 10) {
          allQuotes.push({ quote: quote.trim(), source_url: citations[0] || '' });
        }
      }

      citations.forEach(c => allSources.add(c));

      // F1157: Store raw query result
      rawQueries.push({
        query,
        response,
        extractedStats: stats,
        extractedQuotes: allQuotes.slice(-2), // Last 2 quotes from this query
      });
    }

    // F1153: Deduplicate stats by numeric value similarity
    const deduplicatedStats = this.deduplicatedStats(allStats);

    // F1154: Deduplicate quotes by text similarity >0.8
    const deduplicatedQuotes = this.deduplicateQuotes(allQuotes);

    // F1155: Rank stats by specificity
    const rankedStats = this.rankStatsBySpecificity(deduplicatedStats).slice(0, 3);

    // F1156: Rank quotes by authority
    const rankedQuotes = this.rankQuotesByAuthority(deduplicatedQuotes).slice(0, 2);

    // Merge facts from first response
    const firstContent = validResponses[0]?.choices[0]?.message?.content || '';
    const facts = this.extractFacts(firstContent).slice(0, 5);

    const result: ResearchResult = {
      facts,
      statistics: rankedStats.map(s => s.stat),
      stats: rankedStats,
      quotes: rankedQuotes.map(q => q.quote),
      quotesWithAttribution: rankedQuotes,
      sources: Array.from(allSources).slice(0, 10),
      summary: validResponses.length > 0
        ? `Research compiled from ${validResponses.length} queries`
        : '',
    };

    return { result, rawQueries };
  }

  /**
   * F1153: Deduplicate stats by numeric value similarity
   */
  private deduplicatedStats(stats: StatWithSource[]): StatWithSource[] {
    return stats.filter((stat, index, arr) => {
      // Check if this stat is similar to any previous stat
      const numMatch = stat.stat.match(/\d+(?:\.\d+)?/);
      if (!numMatch) return true;

      const currentNum = parseFloat(numMatch[0]);

      return !arr.slice(0, index).some(prev => {
        const prevMatch = prev.stat.match(/\d+(?:\.\d+)?/);
        if (!prevMatch) return false;

        const prevNum = parseFloat(prevMatch[0]);
        const diff = Math.abs(currentNum - prevNum);
        const tolerance = Math.max(currentNum, prevNum) * 0.1; // 10% tolerance

        return diff < tolerance;
      });
    });
  }

  /**
   * F1154: Deduplicate quotes by text similarity >0.8
   */
  private deduplicateQuotes(quotes: QuoteWithAttribution[]): QuoteWithAttribution[] {
    return quotes.filter((quote, index, arr) => {
      return !arr.slice(0, index).some(prev => {
        const maxLen = Math.max(quote.quote.length, prev.quote.length);
        if (maxLen === 0) return false;

        const lev = distance(quote.quote.toLowerCase(), prev.quote.toLowerCase());
        const similarity = 1 - (lev / maxLen);

        return similarity > 0.8;
      });
    });
  }

  /**
   * F1155: Rank stats by specificity (exact numbers over ranges)
   */
  private rankStatsBySpecificity(stats: StatWithSource[]): StatWithSource[] {
    return stats.sort((a, b) => {
      const aIsExact = /^\d+%?$/.test(a.stat.trim());
      const bIsExact = /^\d+%?$/.test(b.stat.trim());

      if (aIsExact && !bIsExact) return -1;
      if (!aIsExact && bIsExact) return 1;
      return 0;
    });
  }

  /**
   * F1156: Rank quotes by authority (prefer named experts)
   */
  private rankQuotesByAuthority(quotes: QuoteWithAttribution[]): QuoteWithAttribution[] {
    const scoreQuote = (quote: string): number => {
      const hasNamedIndividual = /(?:Mr\.|Ms\.|Dr\.|Prof\.|[A-Z][a-z]+ [A-Z][a-z]+)/g.test(quote);
      const hasTitle = /(CEO|founder|expert|researcher|professor|author)/i.test(quote);

      let score = 0;
      if (hasNamedIndividual && hasTitle) score = 3; // Named expert with title/affiliation
      else if (hasNamedIndividual) score = 2; // Named individual without clear affiliation
      else if (hasTitle) score = 1; // Title/affiliation without named individual
      else score = 0; // Generic quote

      return score;
    };

    return quotes.sort((a, b) => scoreQuote(b.quote) - scoreQuote(a.quote));
  }

  /**
   * Helper to extract facts from response
   */
  private extractFacts(content: string): string[] {
    const lines = content.split('\n');
    const facts: string[] = [];

    for (const line of lines) {
      const trimmed = line.trim();
      if (trimmed.length > 20 && !trimmed.startsWith('{') && !trimmed.startsWith('[')) {
        facts.push(trimmed);
        if (facts.length >= 5) break;
      }
    }

    return facts;
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: 'healthy' | 'unhealthy'; error?: string }> {
    if (!this.isConfigured()) {
      return { status: 'unhealthy', error: 'PERPLEXITY_API_KEY not configured' };
    }

    try {
      await this.query([
        { role: 'user', content: 'Hello' }
      ], { maxTokens: 10 });
      return { status: 'healthy' };
    } catch (error) {
      return {
        status: 'unhealthy',
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }
}

// Export singleton instance
export const perplexityClient = new PerplexityClient(env.perplexityApiKey);
