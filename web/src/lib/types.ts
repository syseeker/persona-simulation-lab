export type Course = {
  id: string; title: string; provider: string; kind: string; summary: string; source_url: string;
  price_min_sgd: number | null; price_max_sgd: number | null; extra_cost_sgd: number | null;
  schedule_note: string; captured_on: string; funding_note: string; tags: string[];
};
export type Status = { nim_key_present: boolean; ngc_key_present: boolean; model: string; catalogue_count: number; snapshot_date: string; personas_audited: boolean };
export type Run = { run_id: string; status: string; started_at: string; calls: number; error?: string; source_notice: string;
  evaluation?: { summary: Record<string, { criteria: number; passed: number }> };
  spec: { mode: string; engine: string; source: string; personas: number; strategies: string[] };
  models?: Record<string, string>;
  episodes: { episode_id: string; status: string; strategy: string; error?: string;
    outcome?: { n_assistant_inline_failures?: number } }[];
  events?: { type: string; role?: string; content?: string; episode_id?: string; strategy?: string }[] };
