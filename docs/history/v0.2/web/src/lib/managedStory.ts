import type { ManagedStoryCondition, Run, StoryPreferences } from './types.ts';

export function prepareManagedStory(run: Run, episodeId: string): ManagedStoryCondition {
  if (['queued', 'running'].includes(run.status)) throw new Error('Wait for this saved story to finish before preparing a managed condition.');
  const episode = run.episodes.find(item => item.episode_id === episodeId);
  if (!episode) throw new Error('Choose one saved conversation for the managed condition.');
  const starts = run.events?.filter(event => event.episode_id === episodeId && event.type === 'episode_started') ?? [];
  const started = starts.length === 1 ? starts[0] : undefined;
  const message = run.events?.find(event => event.episode_id === episodeId && event.type === 'message' && event.role === 'user')?.content;
  if (!message?.trim()) throw new Error('This episode has no saved first public learner input. No replacement input was invented.');
  const preferences = started?.preferences ?? null;
  return { condition_id: crypto.randomUUID(), run_id: run.run_id, episode_id: episodeId,
    story_id: run.spec.story_id ?? run.story?.id ?? null, source_id: started?.source_id ?? episode.source_id ?? null,
    source_mode: run.spec.mode, source_strategy: episode.strategy, catalogue_sha256: run.catalogue_sha256 ?? null,
    preferences: preferences ? JSON.parse(JSON.stringify(preferences)) : null, first_learner_input: message,
    harness: run.spec.harness ?? (['direct', 'relay'].includes(run.spec.engine) ? 'deepagents' : null),
    model_route: run.spec.model_route ?? null };
}

export function samePreferences(left: StoryPreferences | null, right: StoryPreferences | null): boolean {
  if (!left || !right) return false;
  const fields: (keyof StoryPreferences)[] = ['goal', 'budget_sgd', 'days', 'planning_area', 'known_skills', 'kind'];
  return fields.every(field => JSON.stringify(left[field] ?? null) === JSON.stringify(right[field] ?? null));
}
