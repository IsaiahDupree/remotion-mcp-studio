/**
 * F0483: GET /api/scripts/:id — retrieve script
 *
 * Returns a single content_script by ID.
 */

import { NextRequest, NextResponse } from 'next/server';
import { extractUserId } from '@/lib/auth';
import { supabaseAdmin } from '@/lib/supabase';

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  // F0009: Bearer token authentication
  const authResult = await extractUserId(request);

  if (!authResult.success) {
    return NextResponse.json(
      { error: authResult.error || 'Unauthorized' },
      { status: 401 }
    );
  }

  const userId = authResult.user_id!;
  const scriptId = params.id;

  try {
    // Fetch script with user verification
    const { data: script, error } = await supabaseAdmin
      .from('content_scripts')
      .select(`
        id,
        hook,
        body_points,
        cta,
        script_text,
        estimated_duration_sec,
        created_at,
        updated_at,
        platform,
        tone,
        topic,
        user_id,
        research_id,
        status
      `)
      .eq('id', scriptId)
      .single();

    if (error || !script) {
      return NextResponse.json(
        { error: 'Script not found' },
        { status: 404 }
      );
    }

    // Verify ownership
    if (script.user_id !== userId) {
      return NextResponse.json(
        { error: 'Not authorized to access this script' },
        { status: 403 }
      );
    }

    return NextResponse.json({
      script: {
        id: script.id,
        hook: script.hook,
        body_points: script.body_points,
        cta: script.cta,
        script_text: script.script_text,
        estimated_duration_sec: script.estimated_duration_sec,
        created_at: script.created_at,
        updated_at: script.updated_at,
        platform: script.platform,
        tone: script.tone,
        topic: script.topic,
        research_id: script.research_id,
        status: script.status,
      },
    }, { status: 200 });

  } catch (error) {
    console.error('GET /api/scripts/[id] error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
