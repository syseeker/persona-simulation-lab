export type PersonaSource = 'hf-profile-only' | 'ngc';
export type DatasetMeta = {
  source: PersonaSource; name: string; revision: string; row_count: number; ready: boolean;
  columns: { name: string; type: string }[]; ocean_fields: string[]; reason?: string; source_url: string;
};
export type SourceRecord = {
  source_id: string; source: PersonaSource; source_revision: string; original_profile_sha256: string;
  kind: 'original'; profile: Record<string, unknown>;
};
export type ProfilePage = {
  dataset: DatasetMeta; records: SourceRecord[]; offset: number; limit: number; total: number; has_more: boolean; inference_calls: number;
};
export type ProfileOptions = {
  source: PersonaSource; source_revision: string; geography_field: string; row_count: number;
  fields: Record<string, { value: string; count: number }[]>; inference_calls: number;
};
