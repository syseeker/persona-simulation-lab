# Singapore Persona Sources and Derived Data

## Original public HF source

[NVIDIA Nemotron Personas Singapore](https://huggingface.co/datasets/nvidia/Nemotron-Personas-Singapore) is pinned at revision `a3994709410410f834bd949d643d3f2796908969`, under CC BY 4.0. The recorded audit covers both parquet shards, all 148,000 rows, 148,000 distinct IDs and 21 columns. Ages span 18–108 and 48 planning-area values are populated. These are source dataset facts, not a claim about representative coverage of an experiment.

The recorded age counts are 41,200 aged 18–34, 67,191 aged 35–59 and 39,609 aged 60+. Industry is missing in 64,801 records (43.78%). Skills, interests and career goals are present; the two list-named fields are encoded as strings and parsed safely. No OCEAN columns are present. The local audit and shard hashes remain in ignored data files.

v0.1's diagnostic panel has twelve profiles, with four from each age band, and its default simulation selected the first profile per band. **v0.2 selection uses the full available local corpus.** A small panel is still useful as a frozen fixture; it is not the population and age bands are not persona types.

## Explore, sample and lock

The UI data workbench reads bounded pages from local parquet, supports field search/filters and shows source schema/revision, original values and hashes. Sampling chooses actual source IDs without replacement, saves its seed and reports the eligible corpus. Locking resolves selected IDs in the requested distribution and records exact original rows.

The frozen input, not a seed alone, guarantees which source rows were used. Follow-up comparisons reuse those resolved rows and the frozen catalogue, with fresh target state. Reopening a saved dataset or simulation makes no inference calls.

Skills/career ambitions and interests support learning scenarios. Occupation/education do not prove prerequisites; planning area does not establish an address or travel tolerance. Budget, availability and delivery preferences come from explicit learner input or separately labelled generated scenarios. Ethnicity, religion and sex are not ranking inputs.

## Singapore NGC Extended

This application supports **Singapore Nemotron Personas Extended (`en_SG`) only**, not a general NGC catalogue. Its source/access/terms are separate from HF and from inference credentials. The local explorer reports installed assets and requires source IDs plus behavioural columns; it never substitutes public HF profiles for an NGC request.

The trusted operator may configure the local Extended parquet path through `LAB_NGC_PERSONAS_PATH`; otherwise the documented managed-assets directory is used. UI requests cannot provide arbitrary paths/resources. Source revision is reported explicitly; an unversioned local file is not described as a pinned upstream release. Dataset access and OCEAN conditioning remain unverified until an actual compatible source is available and exercised. Read [verification](verification.md).

## Data Designer products

- **Source-seeded scenario:** LLM-generated learning goal, explicit hypothetical preferences and opening message, linked to the original profile.
- **Added columns:** closed typed hypothetical values such as last drawn gross monthly salary in SGD or favourite brands. The original row and hash stay unchanged.
- **Additional synthetic profile:** a new generated identity and app-ready fields inspired by source examples, with parent IDs/revision/hashes. It is labelled Designer-generated, not original HF or NGC data.

Text, integer, decimal, boolean, enum and text-list fields are supported, with applicable bounds/choices and protected provenance names. Typed LLM output is independently validated before use. User descriptions/source rows are reference data within trusted templates; the UI cannot execute Python, SQL or arbitrary expressions.

Five-row generation previews are the default. Native configuration, seeds, raw output, validation, model/call accounting and warnings remain local. A learner explicitly chooses whether to use the saved generated data as simulation context. Generated salary/brands do not establish financial history, citizenship, funding eligibility, observed behaviour or demand. Generating preferences is different from sampling source profiles, and neither demonstrates real residents' choices.

## Provenance and limits

Keep raw source records, generated overlays and generated profiles in separate ignored artifacts. Every derived product identifies its parent inputs, original hashes, pipeline/configuration and generated identity. Store exact source/derived records with paired experiments rather than resampling silently.

Profile text can contain invented courses or unsuitable content. Ground recommendations independently in the official catalogue and preserve unsupported/no-match outcomes. Small synthetic simulations and model-scored outputs do not establish population effects, human learning outcomes or entitlement. Review the source license/access terms before redistributing source-derived material; public code does not include raw profiles or transcripts.
