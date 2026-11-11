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
  events?: { type: string; role?: string; content?: string; episode_id?: string; strategy?: string; persona_index?: number }[] };
export type RunTrace = {
  version: number; run_id: string; episode_id: string; mode: string; status: string; error?: string;
  source_notice: string; source: { distribution?: string; dataset?: string; revision?: string };
  profile: Record<string, unknown>;
  scenario: { theme?: { description?: string } | string; strategy?: string; overlay?: unknown; probe?: string };
  snapshot: { available: boolean; sha256?: string; integrity_matches?: boolean };
  turns: { number: number; user: string; assistant: string | null;
    tools: { name: string; arguments: unknown; result: unknown }[];
    course_references: { id: string; course: (Course & Record<string, unknown>) | null; seen_in_tool_result: boolean }[] }[];
  notices: string[];
};
