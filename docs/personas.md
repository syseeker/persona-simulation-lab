# Singapore Personas Review

## Contents

- [Source And Audit](#source-and-audit)
- [Application Mapping](#application-mapping)
- [HF And NGC Modes](#hf-and-ngc-modes)
- [Limits](#limits)

## Source And Audit

Source: [NVIDIA Nemotron Personas Singapore](https://huggingface.co/datasets/nvidia/Nemotron-Personas-Singapore), public HF revision `a3994709410410f834bd949d643d3f2796908969`, CC BY 4.0. The dataset was inspected before the catalogue was created.

The reproducible audit covers both parquet shards and all **148,000** rows. It found 148,000 distinct IDs, 21 columns including the ID, ages 18 through 108 and 48 populated planning-area values. There are 41,200 records aged 18–34, 67,191 aged 35–59 and 39,609 aged 60 and above.

Skills, interests and career goals are present in every record. Industry is null in 64,801 records, or 43.78%. The two list-named columns are stored as strings; every record parsed as a list using safe literal parsing. No OCEAN columns are present. Full local counts and shard hashes are in ignored `data/persona-audit.json`.

The review panel covers three age bands with four profiles each. It is a deterministic diagnostic sample, not a population-weighted panel. Generated descriptions still need case-level review for consistency and suitability.

## Application Mapping

- Skills and career goals support workplace learning scenarios such as spreadsheets, analytics, project management and operations.
- Interests and hobby descriptions support photography, baking, calligraphy and movement classes.
- Education and occupation provide context; they do not establish course prerequisites.
- Planning area is a broad location preference. It does not establish an address, travel distance or acceptable commute.
- Budget, availability and delivery preferences must come from explicit learner input or labelled scenario hypotheses.
- Ethnicity, religion and sex are not course-ranking inputs.

Course names inside generated aspirations are unverified. The catalogue uses independently checked official listings.

## HF And NGC Modes

**HF profile-only:** use the audited public record for identity and interests, with no OCEAN prompt conditioning. UserSim's loop defaults remain operational settings. The app labels this source in manifests and the interface.

**NGC Extended:** use UserSim's official `en_SG` materialization path and its additional behavioural fields. It requires a separate NGC account/key and locally installed assets. NGC setup was not verified in this environment: the installed CLI needed organization configuration, and the attempted direct resource API access was rejected. The app never substitutes public records silently for an NGC request.

NGC datasets have separate terms. Keep raw records and source-derived conversations local and review the current dataset terms before use. An NVIDIA inference key does not establish dataset access.

## Limits

These are synthetic profiles, not observations of named people or validated predictors of learning demand. The source describes census grounding alongside data and modeling limitations. Course recommendations and model-judged conversations do not demonstrate representativeness or real human outcomes.
