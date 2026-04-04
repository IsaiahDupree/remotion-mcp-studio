// F0154: GET /api/voiceover/:voiceoverId endpoint
// Retrieves a single voiceover job by ID

import { NextRequest, NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabase';
import { extractUserId } from '@/lib/auth';

export async function GET(
  request: NextRequest,
  { params }: { params: { voiceoverId: string } }
) {
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
    const { voiceoverId } = params;

    // Validate UUID format
    const uuidRegex = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
    if (!uuidRegex.test(voiceoverId)) {
      return NextResponse.json(
        {
          error: 'Invalid voiceover ID format',
          code: 'INVALID_ID',
          request_id: crypto.randomUUID(),
        },
        { status: 400 }
      );
    }

    // Query voiceover_jobs table
    const { data: voiceover, error: dbError } = await supabaseAdmin
      .from('content_voiceover_jobs')
      .select('*')
      .eq('id', voiceoverId)
      .single();

    if (dbError || !voiceover) {
      return NextResponse.json(
        {
          error: 'Voiceover job not found',
          code: 'NOT_FOUND',
          request_id: crypto.randomUUID(),
        },
        { status: 404 }
      );
    }

    // F0154: Owner-only access authorization
    if (voiceover.user_id !== userId) {
      return NextResponse.json(
        {
          error: 'Forbidden: You do not have access to this voiceover job',
          code: 'FORBIDDEN',
          request_id: crypto.randomUUID(),
        },
        { status: 403 }
      );
    }

    return NextResponse.json({
      success: true,
      voiceover,
    });

  } catch (error) {
    console.error('Voiceover retrieval error:', error);
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
