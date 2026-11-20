/**
 * Metadata-only audit snapshot, 19 November 2026.
 * Field names, Arrow types and nullability were read from local Parquet footers.
 * The recorded OCEAN content audit is separate from this schema inspection.
 * No source rows, profile identifiers, credentials or persona values are bundled.
 */
import { compareFields } from './fieldGroups.ts';
export type DatasetId = 'hf' | 'ngc';
export type FieldScope = 'shared' | 'hf-only' | 'ngc-only';
export type DatasetField = { name: string; type: string; nullable: boolean };
export type DatasetSnapshot = {
  id: DatasetId;
  title: string;
  subtitle: string;
  versionLabel: string;
  version: string;
  rows: number;
  columns: number;
  oceanColumns: number;
  sourceUrl: string;
  bytes?: number;
  originalSha256?: string;
  fields: DatasetField[];
};
export const auditDate = '19 November 2026';
export const oceanFieldNames = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism'] as const;

export const hfFields: DatasetField[] = [
  {
    "name": "uuid",
    "type": "string",
    "nullable": true
  },
  {
    "name": "professional_persona",
    "type": "string",
    "nullable": true
  },
  {
    "name": "sports_persona",
    "type": "string",
    "nullable": true
  },
  {
    "name": "arts_persona",
    "type": "string",
    "nullable": true
  },
  {
    "name": "travel_persona",
    "type": "string",
    "nullable": true
  },
  {
    "name": "culinary_persona",
    "type": "string",
    "nullable": true
  },
  {
    "name": "persona",
    "type": "string",
    "nullable": true
  },
  {
    "name": "cultural_background",
    "type": "string",
    "nullable": true
  },
  {
    "name": "skills_and_expertise",
    "type": "string",
    "nullable": true
  },
  {
    "name": "skills_and_expertise_list",
    "type": "string",
    "nullable": true
  },
  {
    "name": "hobbies_and_interests",
    "type": "string",
    "nullable": true
  },
  {
    "name": "hobbies_and_interests_list",
    "type": "string",
    "nullable": true
  },
  {
    "name": "career_goals_and_ambitions",
    "type": "string",
    "nullable": true
  },
  {
    "name": "sex",
    "type": "string",
    "nullable": true
  },
  {
    "name": "age",
    "type": "int64",
    "nullable": true
  },
  {
    "name": "marital_status",
    "type": "string",
    "nullable": true
  },
  {
    "name": "education_level",
    "type": "string",
    "nullable": true
  },
  {
    "name": "occupation",
    "type": "string",
    "nullable": true
  },
  {
    "name": "industry",
    "type": "string",
    "nullable": true
  },
  {
    "name": "planning_area",
    "type": "string",
    "nullable": true
  },
  {
    "name": "country",
    "type": "string",
    "nullable": true
  }
];

export const ngcFields: DatasetField[] = [
  {
    "name": "uuid",
    "type": "string",
    "nullable": true
  },
  {
    "name": "first_name",
    "type": "string",
    "nullable": true
  },
  {
    "name": "middle_name",
    "type": "string",
    "nullable": true
  },
  {
    "name": "last_name",
    "type": "string",
    "nullable": true
  },
  {
    "name": "sex",
    "type": "string",
    "nullable": true
  },
  {
    "name": "street_number",
    "type": "null",
    "nullable": true
  },
  {
    "name": "street_name",
    "type": "null",
    "nullable": true
  },
  {
    "name": "unit",
    "type": "null",
    "nullable": true
  },
  {
    "name": "city",
    "type": "null",
    "nullable": true
  },
  {
    "name": "region",
    "type": "null",
    "nullable": true
  },
  {
    "name": "district",
    "type": "string",
    "nullable": true
  },
  {
    "name": "postcode",
    "type": "string",
    "nullable": true
  },
  {
    "name": "country",
    "type": "string",
    "nullable": true
  },
  {
    "name": "age",
    "type": "int64",
    "nullable": true
  },
  {
    "name": "marital_status",
    "type": "string",
    "nullable": true
  },
  {
    "name": "education_level",
    "type": "string",
    "nullable": true
  },
  {
    "name": "bachelors_field",
    "type": "null",
    "nullable": true
  },
  {
    "name": "occupation",
    "type": "string",
    "nullable": true
  },
  {
    "name": "preferred_english_name",
    "type": "string",
    "nullable": true
  },
  {
    "name": "ethnic_background",
    "type": "string",
    "nullable": true
  },
  {
    "name": "religion",
    "type": "string",
    "nullable": true
  },
  {
    "name": "industry",
    "type": "string",
    "nullable": true
  },
  {
    "name": "openness",
    "type": "string",
    "nullable": true
  },
  {
    "name": "conscientiousness",
    "type": "string",
    "nullable": true
  },
  {
    "name": "extraversion",
    "type": "string",
    "nullable": true
  },
  {
    "name": "agreeableness",
    "type": "string",
    "nullable": true
  },
  {
    "name": "neuroticism",
    "type": "string",
    "nullable": true
  },
  {
    "name": "cultural_background",
    "type": "string",
    "nullable": true
  },
  {
    "name": "religious_background",
    "type": "string",
    "nullable": true
  },
  {
    "name": "skills_and_expertise",
    "type": "string",
    "nullable": true
  },
  {
    "name": "skills_and_expertise_list",
    "type": "string",
    "nullable": true
  },
  {
    "name": "career_goals_and_ambitions",
    "type": "string",
    "nullable": true
  },
  {
    "name": "hobbies_and_interests",
    "type": "string",
    "nullable": true
  },
  {
    "name": "hobbies_and_interests_list",
    "type": "string",
    "nullable": true
  },
  {
    "name": "professional_persona",
    "type": "string",
    "nullable": true
  },
  {
    "name": "religious_persona",
    "type": "string",
    "nullable": true
  },
  {
    "name": "finance_persona",
    "type": "string",
    "nullable": true
  },
  {
    "name": "healthcare_persona",
    "type": "string",
    "nullable": true
  },
  {
    "name": "sports_persona",
    "type": "string",
    "nullable": true
  },
  {
    "name": "arts_persona",
    "type": "string",
    "nullable": true
  },
  {
    "name": "travel_persona",
    "type": "string",
    "nullable": true
  },
  {
    "name": "culinary_persona",
    "type": "string",
    "nullable": true
  },
  {
    "name": "persona",
    "type": "string",
    "nullable": true
  },
  {
    "name": "detailed_persona",
    "type": "string",
    "nullable": true
  }
];

export const datasetSnapshots: DatasetSnapshot[] = [
  {
    id: 'hf',
    title: 'Public Hugging Face',
    subtitle: 'Nemotron Personas · Singapore',
    versionLabel: 'Pinned revision',
    version: 'a3994709410410f834bd949d643d3f2796908969',
    rows: 148000,
    columns: 21,
    oceanColumns: 0,
    sourceUrl: 'https://huggingface.co/datasets/nvidia/Nemotron-Personas-Singapore/viewer',
    fields: hfFields
  },
  {
    id: 'ngc',
    title: 'NGC Extended',
    subtitle: 'Nemotron Personas · Singapore · en_SG',
    versionLabel: 'Asset version',
    version: '0.0.1',
    rows: 148000,
    columns: 44,
    oceanColumns: 5,
    sourceUrl: 'https://catalog.ngc.nvidia.com/orgs/nvidia/teams/nemotron-personas/resources/nemotron-personas-dataset-en_sg',
    bytes: 311355075,
    originalSha256: '357e8c503f1b2d669fadf3048c280bf22da77e4c568d193a951ffda3260e3db0',
    fields: ngcFields
  }
];

const hfByName = new Map(hfFields.map(field => [field.name, field]));
const ngcByName = new Map(ngcFields.map(field => [field.name, field]));
export const schemaComparison = [...new Set([...hfByName.keys(), ...ngcByName.keys()])].sort(compareFields).map(name => {
  const hf = hfByName.get(name);
  const ngc = ngcByName.get(name);
  const scope: FieldScope = hf && ngc ? 'shared' : hf ? 'hf-only' : 'ngc-only';
  return { name, hf, ngc, scope, ocean: oceanFieldNames.some(field => field === name) };
});
export const schemaCounts = {
  all: schemaComparison.length,
  shared: schemaComparison.filter(field => field.scope === 'shared').length,
  hfOnly: schemaComparison.filter(field => field.scope === 'hf-only').length,
  ngcOnly: schemaComparison.filter(field => field.scope === 'ngc-only').length
};

/** Recorded content-validation results supplied by the 19 November local audit. */
export const oceanAudit = {
  fields: oceanFieldNames,
  rowsCheckedPerField: 148000,
  validObjectsPerField: 148000,
  storedType: 'string',
  objectKeys: ['description', 'label', 't_score'],
  observedScoreMinimum: 20,
  observedScoreMaximum: 80
} as const;
