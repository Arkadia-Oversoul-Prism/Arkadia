/**
 * SSE frame extraction for the Engineering Lab event transport.
 *
 * Frames are separated by a blank line. Per the SSE specification that
 * separator is a real line feed (0x0A), not the two literal characters
 * backslash + "n". The server-side emitter in api/lab_routes.py must therefore
 * terminate frames with LF bytes; a doubled backslash there emits 0x5C 0x6E and
 * no frame is ever recognised.
 *
 * Kept as a pure function so the exact code the operator surface runs can be
 * exercised against captured wire bytes in tests.
 */
export type SseFrame = { event: string | null; data: string };

export function drainSse(buffer: string): { frames: SseFrame[]; rest: string } {
  const chunks = buffer.split('\n\n');
  const rest = chunks.pop() ?? '';
  const frames: SseFrame[] = [];
  for (const chunk of chunks) {
    const lines = chunk.split('\n');
    const dataLine = lines.find((x) => x.startsWith('data: '));
    if (!dataLine) continue;
    const eventLine = lines.find((x) => x.startsWith('event: '));
    frames.push({
      event: eventLine ? eventLine.slice(7).trim() : null,
      data: dataLine.slice(6),
    });
  }
  return { frames, rest };
}
