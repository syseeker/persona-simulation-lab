export type CaptureAvailability = 'exists' | 'missing' | 'not-used' | 'unavailable';
export type CapturePrivacy = 'public' | 'private' | 'projection' | 'unknown';

export interface MetadataArtifact {
  id: string;
  path?: string;
  url?: string | null;
  kind: string;
  source_kind?: string | null;
  privacy: Exclude<CapturePrivacy, 'unknown'>;
  status: CaptureAvailability;
  sha256: string;
  link_status?: 'committed' | 'not-committed';
}

export interface MetadataCondition {
  id: string;
  purpose: string;
  execution_status: string;
}

export interface MetadataRow {
  id: string;
  module: string;
  steps: number[];
  operation: string;
  scenario_ids: string[];
  filenames: string[];
  status: CaptureAvailability;
  privacy: CapturePrivacy;
  condition_id: string | null;
  condition_purpose: string | null;
  execution_status: string;
  artifacts: MetadataArtifact[];
}

export interface GuideMetadata {
  schema: 'citizen-guide-metadata/v1';
  scenario_id: string;
  run_id: string | null;
  available: boolean;
  notice?: string;
  inference_calls_for_inspection: 0;
  rows: MetadataRow[];
  conditions: MetadataCondition[];
}
