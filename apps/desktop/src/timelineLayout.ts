import type { TimelineDoc } from './types';

export function resizeTimeline(timeline: TimelineDoc, width: number, height: number): TimelineDoc {
  const sx = width / timeline.width, sy = height / timeline.height;
  return { ...timeline, width, height, clips: timeline.clips.map(clip => {
    if (!clip.transform) return clip;
    const transform = { ...clip.transform };
    for (const key of ['x', 'y', 'width', 'height'] as const) {
      const value = transform[key];
      if (value === undefined) continue;
      const scaled = value * (key === 'x' || key === 'width' ? sx : sy);
      transform[key] = key === 'width' || key === 'height'
        ? Math.max(2, Math.min(3840, Math.round(scaled / 2) * 2))
        : Math.max(-3840, Math.min(3840, Math.round(scaled)));
    }
    return { ...clip, transform };
  }) };
}
