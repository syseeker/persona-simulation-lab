# Singapore Persona Sources and Derived Data

> **Backend/data reference.** Source audits and selection/generation rules below describe retained services and the historical v0.2 workbench. The external guide's Data schema subtab preserves audit metadata; Explore profiles now reads installed original rows through the shared dataset service. Its simulation stories remain illustrative and no generation is connected. UI availability follows the [current plan](../PLAN.md). The [v0.2 snapshot](history/v0.2/INDEX.md) preserves the earlier context.

## Original public HF source

[NVIDIA Nemotron Personas Singapore](https://huggingface.co/datasets/nvidia/Nemotron-Personas-Singapore) is pinned at revision `a3994709410410f834bd949d643d3f2796908969`, under CC BY 4.0. The recorded audit covers both parquet shards, all 148,000 rows, 148,000 distinct IDs and 21 columns. Ages span 18–108 and 48 planning-area values are populated. These are source dataset facts, not a claim about representative coverage of an experiment.

The recorded age counts are 41,200 aged 18–34, 67,191 aged 35–59 and 39,609 aged 60+. Industry is missing in 64,801 records (43.78%). Skills, interests and career goals are present; the two list-named fields are encoded as strings and parsed safely. No OCEAN columns are present. The local audit and shard hashes remain in ignored data files.

v0.1's diagnostic panel has twelve profiles, with four from each age band, and its default simulation selected the first profile per band. **v0.2 selection uses the full available local corpus.** A small panel is still useful as a frozen fixture; it is not the population and age bands are not persona types.

## Explore, sample and lock

The retained services behind the archived v0.2 data workbench read bounded pages from local parquet, supports field search/filters and shows source schema/revision, original values and hashes. Sampling chooses actual source IDs without replacement, saves its seed and reports the eligible corpus. Locking resolves selected IDs in the requested distribution and records exact original rows.

The current guide's read-only Explore profiles view reuses these services with text, age, geography and education filters and a maximum of twenty rows per response. It shows original names where present, the source's actual missing values and grouped row details; HF's absent name/OCEAN columns stay absent. Facet options/counts are computed from projected columns across the selected source, while result counts apply all filters. `planning_area` is HF's physical column and `district` is NGC's. This browser selection inspects a row; it does not lock it into a simulation. Original files remain ignored under the checkout's local `data/` folder or an explicitly configured operator/SDK source.

The frozen input, not a seed alone, guarantees which source rows were used. Follow-up comparisons reuse those resolved rows and the frozen catalogue, with fresh target state. Reopening a saved dataset or simulation makes no inference calls.

Skills/career ambitions and interests support learning scenarios. Occupation/education do not prove prerequisites; planning area does not establish an address or travel tolerance. Budget, availability and delivery preferences come from explicit learner input or separately labelled generated scenarios. Ethnicity, religion and sex are not ranking inputs.

## Singapore NGC Extended

This application supports **Singapore Nemotron Personas Extended (`en_SG`) only**, not a general NGC catalogue. Its source/access/terms are separate from HF and from inference credentials. The retained explorer services report installed assets and requires source IDs plus behavioural columns; it never substitutes public HF profiles for an NGC request.

On **19 November 2026**, the original [NGC Singapore resource](https://catalog.ngc.nvidia.com/orgs/nvidia/teams/nemotron-personas/resources/nemotron-personas-dataset-en_sg), artifact version **0.0.1**, was downloaded through NVIDIA's authenticated resource API. Its single `en_SG.parquet` is **311,355,075 bytes**, with locally measured SHA-256 `357e8c503f1b2d669fadf3048c280bf22da77e4c568d193a951ffda3260e3db0`. This digest identifies the downloaded bytes; it is not an upstream signature. The catalogue's separate “Data Version 1.0” label is not the artifact revision.

The actual file contains **148,000 rows, 148,000 distinct nonempty UUIDs and 44 columns**. The card advertises 36 columns; this integration uses the downloaded file's observed schema. Its geography field is `district` (47 populated values), rather than HF's `planning_area`. Each of the five OCEAN fields has 148,000 valid JSON objects with `t_score`, `label` and `description`: zero missing or malformed values, with observed T-scores from 20 to 80. These are synthetic source attributes, not measured traits of real residents. The installed UserSim 0.3.0 parser supports the JSON-string representation; [verification](verification.md) distinguishes model-free input compatibility from a live conversation.

Original bytes and the aggregate/hash provenance remain ignored under `data/ngc/en_SG/0.0.1/`. The [restricted installer](../scripts/install_ngc_personas.py) downloads only this resource/revision, never overwrites an existing asset, never accepts license terms and never writes credentials:

```bash
# Uses the existing local NGC_CLI_API_KEY; requires this resource's NGC access.
uv run python scripts/install_ngc_personas.py --download

# Verify an existing pinned install without network access or inference.
uv run python scripts/install_ngc_personas.py
```

The installer follows the [official authenticated download mechanism](https://docs.nvidia.com/ngc/latest/ngc-catalog-user-guide.html#downloading-authenticated-access-resources-via-wget-curl): the `/v2/org/nvidia/team/nemotron-personas/resources/…` route with the existing personal/service API key. The guest resource alias can return 403 for the same resource; an actual authenticated 401/403 stops installation. NGC access/permission or license gates require the operator to resolve access in the catalogue; the installer does not bypass them. The source uses the [NVIDIA Dataset License Agreement](https://assets.ngc.nvidia.com/products/api-catalog/legal/Personas-Dataset-NVIDIA-Training-Dataset-License-Agreement-2025-11-26.pdf), separately from HF's CC BY 4.0 terms.

The [shared resolver](../src/learning_lab/ngc_personas.py) first honours the trusted operator's `LAB_NGC_PERSONAS_PATH`, then an existing Data Designer managed `datasets/en_SG.parquet`, then this version-pinned local installation. An explicit missing path fails clearly; it never silently selects another file. Every selected origin must pass the complete original ID/OCEAN value audit before readiness or sampling; columns containing only null or malformed traits are unavailable for simulation. Invalid selected assets never cause fallback to another distribution or local file. Pinned discovery additionally verifies resource/revision, size and SHA-256. Audit caching is invalidated when the actual selected file changes. Source revision remains explicit; an unversioned operator/managed file is not labelled as a pinned release. Browser service requests cannot supply arbitrary filesystem paths or resource names. Explorer selection and [simulation preparation](../src/learning_lab/simulation.py) share the same lock/sample resolution and preserve original rows.

The external guide has **Why NeMo Stack / Integration Map / Q&A / Datasets**. **Data schema** compares the audit-metadata snapshot and field schemas; **Explore profiles** reads bounded original rows through the authorised read-only backend. The actual ignored files are separate from the bundled schema snapshot. Browsing does not connect scenario execution or establish acceptance of the new simulation journeys.

## Data Designer products

- **Source-seeded scenario:** LLM-generated learning goal, explicit hypothetical preferences and opening message, linked to the original profile.
- **Added columns:** closed typed hypothetical values such as last drawn gross monthly salary in SGD or favourite brands. The original row and hash stay unchanged.
- **Additional synthetic profile:** a new generated identity and app-ready fields inspired by source examples, with parent IDs/revision/hashes. It is labelled Designer-generated, not original HF or NGC data.

Text, integer, decimal, boolean, enum and text-list fields are supported, with applicable bounds/choices and protected provenance names. Typed LLM output is independently validated before use. User descriptions/source rows are reference data within trusted templates; the UI cannot execute Python, SQL or arbitrary expressions.

Five-row generation previews are the default. Native configuration, seeds, raw output, validation, model/call accounting and warnings remain local. A learner explicitly chooses whether to use the saved generated data as simulation context. Generated salary/brands do not establish financial history, citizenship, funding eligibility, observed behaviour or demand. Generating preferences is different from sampling source profiles, and neither demonstrates real residents' choices.

## Provenance and limits

Keep raw source records, generated overlays and generated profiles in separate ignored artifacts. Every derived product identifies its parent inputs, original hashes, pipeline/configuration and generated identity. Store exact source/derived records with paired experiments rather than resampling silently.

Profile text can contain invented courses or unsuitable content. Ground recommendations independently in the official catalogue and preserve unsupported/no-match outcomes. Small synthetic simulations and model-scored outputs do not establish population effects, human learning outcomes or entitlement. Review the source license/access terms before redistributing source-derived material; public code does not include raw profiles or transcripts.
