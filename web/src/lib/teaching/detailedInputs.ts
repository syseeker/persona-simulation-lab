import type {TeachingPage} from './types';

/** Each destination owns one explanation; references identify its actual boundary. */
export function inputLibraries(scenario:string):Record<string,TeachingPage> {
  const retail=scenario==='dreamjob';
  return {
    personas:{title:'Nemotron Personas',intro:'To simulate a learner, we first need a description of a person. Nemotron Personas provides those descriptions as a dataset. Our application reads an existing record, selects it for a test and keeps the original unchanged.',sections:[
      {paragraphs:[
        'The three selected demonstrations use Singapore NGC Extended. This distribution includes background descriptions and OCEAN personality fields that UserSim can interpret. The public Hugging Face distribution has a different schema and does not provide those OCEAN fields. When choosing a distribution, decide whether your test needs background alone or also needs these synthetic behaviour controls.',
        'The application implements reading, filtering, sampling and identity checks; these are not calls to a persona-generation model. The [[url:https://huggingface.co/datasets/nvidia/Nemotron-Personas-Singapore|HF dataset card]] and [[url:https://catalog.ngc.nvidia.com/orgs/nvidia/teams/nemotron-personas/resources/nemotron-personas-dataset-en_sg|NGC Extended distribution]] explain the available data. Keeping the chosen record lets you compare advisor changes with the same test participant, although one synthetic participant cannot represent a population.'
      ]}
    ]},
    situation:{title:'Authored situation',intro:'The persona describes the learner. The situation describes what we want that learner to try today. Here the application defines the learning goal, any spending or schedule constraints, and when the learner should reveal them.',sections:[
      {paragraphs:[retail
        ? 'Retail combines a source-seeded hypothetical overlay with an authored three-turn disclosure protocol. Designer supplies labelled enrichment; the application supplies the experimental sequence. The salary range appears in turn 2, while the total training budget and weekend availability appear in turn 3. Salary never supplies the missing budget.'
        : scenario==='boardgames'
          ? 'The board-games story fixes the goal of learning to play, then asks whether video-game design is equivalent. This deliberate follow-up tests whether the advisor preserves the learner’s original intent when the catalogue lacks a suitable class.'
          : 'Photography supplies beginner photography, Saturday availability and a spending limit under S$50. Those constraints are the developer’s test input. The simulator may phrase the request naturally, but it is not discovering the budget or timetable from the profile.',
        'These choices are test-design decisions. A developer and a behavioural scientist could agree on a different goal or disclosure pattern, then express it in the situation and custom probe. Keep that change separate from the advisor configuration so a changed result has an understandable cause. The present guide demonstrates three authored situations; it does not measure how common those needs are among residents.'
      ]}
    ]},
    designer:{title:'NeMo Data Designer',intro:retail
      ? 'Retail adds three hypothetical details to the selected learner: preferred brands, a salary band and a practical learning task. Data Designer generates them in one structured column, using the original profile as a seed. The application saves the result separately so the original profile stays unchanged.'
      : 'This scenario already has the situation it needs, so it does not call Data Designer. Retail uses the library to add hypothetical test details from a selected source profile. Those additions are saved separately from the original person.',sections:[
      {paragraphs:[
        'A builder tells Designer which columns to copy and which to generate. In the retail recording, two seed columns hold the original profile JSON and its hash. Designer produces one retail_situation column containing three fields. The salary field is constrained to the test value 2500–3499 and the brand choices to UNIQLO and Decathlon; neither is an estimate of the person’s actual income or preferences. The generated learning task describes sales analysis, inventory trends and dashboards.',
        'To reproduce this generation, use the isolated integration pinned to Data Designer 0.10.0. The main UserSim 0.3.0 environment instead uses Designer 0.9.7 because UserSim requires a version below 0.10. The helper project’s own 0.1.0 version is not the Designer SDK version. These versions live in separate environments so each integration can keep its tested dependencies.',
        'For new standalone Designer work, Designer 1.0.1 is a newer upstream release to assess with its own documentation in a separate environment. Reproducing this lab still calls for its pinned versions; moving this integration to 1.x requires an explicit compatibility update and verification. The [[url:https://docs.nvidia.com/nemo/datadesigner/v0.10.0/concepts/architecture-performance|0.10 execution model]] describes the version that generated these saved results; the [[url:https://github.com/NVIDIA-NeMo/DataDesigner/releases|official release notes]] describe newer releases.'
      ]}
    ]},
    usersim:{title:'NeMo UserSim',intro:'UserSim plays the learner who tests our citizen advisor. It generates a message, checks that the message fits the test, sends it to the application and reads the reply. It then decides whether the learner should continue. In this integration, the assistant being tested is the whole citizen application.',sections:[
      {paragraphs:[
        'Start experiment design with four separate choices: who participates, how they interact, what task they attempt and how you will judge the result. The persona answers the first question. UserSim interprets its synthetic traits as behaviour controls. Our custom learning_advisor probe supplies the task and any planned follow-ups. Evaluation then examines what happened. The [[url:https://github.com/NVIDIA-NeMo/UserSim/blob/v0.3.0/architecture/overview.md|UserSim 0.3 architecture]] explains these replaceable layers.',
        'For NGC input, the preparation API derives behavioral_profile values such as patience, verbosity, cooperativeness, tech_literacy and error_proneness. Our probe uses the SDK formatting helpers to express the OCEAN descriptions and relevant interaction cues. Patience can influence frustration handling. These settings shape the simulated learner; they are not measured facts about human behaviour. HF profile-only mode supplies an empty behavioural profile and a neutral interaction style because its source has no OCEAN values.',
        'A developer and behavioural scientist can therefore change a task or behaviour assumption without changing the advisor. In this repository the task hooks live in LearningAdvisorProbe, while ConversationSimulatorConfig supplies locale, limits and probe options. Our retail test deliberately specifies when salary, budget and study days are disclosed. That authored sequence is different from demonstrating a statistically representative disclosure pattern.',
        'The word strategy in simulation.py has a different meaning. RunSpec in src/learning_lab/service.py accepts concise or clarification-first and defaults to concise. The CLI’s --paired option supplies both values; run_experiment then loops over each selected persona and each requested strategy. That strategy changes the advisor’s instructions in target.py. It does not change UserSim’s personality. The current three demonstrations instead use JourneyService and one locked person per run.',
        'In that general experiment path, `runs/<run_id>/run.json` stores the requested specification. events.jsonl stores episode_started records containing the new episode ID, persona index, advisor strategy, source, story, source ID, preferences and scenario binding. resolved-inputs.json retains the prepared simulator rows, and each episode directory contains its own usersim-result.json. In the current guide, Journey run and condition records provide the corresponding identities. These are saved records from execution; browsing them does not create another episode.',
        'For a larger behavioural study, define and version the participant selection, task probe, behaviour/disclosure conditions, advisor variant and evaluation rubric before enumerating the cases. For example, keep the same persona and course request while changing only whether the learner states a budget immediately or after a clarification. That compares a learner-side disclosure condition. Keeping those inputs fixed while changing concise to clarification-first instead compares an advisor-side instruction strategy. The general service permits up to ten personas and two advisor strategies; a 100,000-case study would need additional scheduling, concurrency, recovery and cost controls that this repository does not implement.',
        'During the conversation, UserSim asks its judge model whether generated learner messages stay in role and whether each delivered advisor reply addresses the request coherently. Its summary role also supports stopping decisions. These calls test or manage the interaction; they are separate from the advisor model and later saved-response evaluation. The [[url:https://github.com/NVIDIA-NeMo/UserSim/blob/v0.3.0/docs/engine/EXTERNAL_PROBE_RUNTIME.md|external runtime contract]] explains how the application returns each role’s result to the engine.',
        'For the selected recordings, the application saves resolved-inputs.json, usersim-model-config.json, usersim-activations.jsonl and usersim-result.json under the run directory. The result includes the transcript, outcome, judge ratings and counters. This path does not generate the CLI trajectory Parquet, optional post-loop evaluation dataset or report dashboard. D1–D4 and MATTR simulation-health reporting were not run, so those diagnostics cannot be inferred from the conversation.',
        retail
          ? 'In the current retail flow, the salary-only turn can receive an application-owned clarification without any Fabric invocation. UserSim still observes a public assistant response and judges that response. There are three public turns, but only the agent-dispatched turns have native Fabric/model/tool evidence.'
          : 'The target keeps one agent runtime across this scenario’s public turns. That conversation continuity is narrower than long-term memory across independent tests, which this example does not establish.'
      ]}
    ]},
    catalogue:{title:'Frozen course catalogue',intro:'The advisor needs course facts it can look up and cite. Our catalogue stores those facts with their source links and capture dates. Each test keeps a fixed copy so the tools and evaluation read the same information.',sections:[
      {paragraphs:[
        retail
          ? 'Retail combines the base community/skills catalogue with a separately dated SMU programme supplement. Each record keeps its own capture date. The merged file is a test snapshot, not a live scrape or a claim that every intake remains open.'
          : 'The selected snapshot contains the community and learning listings available to this test. Missing courses remain absent even if the model recognises other plausible providers from training.',
        'The Course schema keeps unknown fees, timetable, prerequisites and eligibility explicit. This makes the evidence reproducible but requires the public answer to tell the learner what still needs provider confirmation. A source URL identifies the published listing; it does not certify a personal subsidy or a current place.'
      ]}
    ]}
  };
}

export function inputOperations(scenario:string):Record<string,TeachingPage> {
  const retail=scenario==='dreamjob', board=scenario==='boardgames';
  return {
    'persona.source':{title:'Load the original distribution',intro:'First choose the dataset that contains the profiles you want to test. The application opens its installed Parquet files and reads their schema and revision. This tells the selection code which fields it can use before it reads a person.',sections:[
      {paragraphs:[
        '[[call:persona.source|The dataset loader]] resolves the chosen distribution and checks its installed assets. NGC readiness also requires the original identity and behavioural-field audit. An unavailable or invalid selected installation must produce an unavailable/error state, rather than silently substituting the other distribution.',
        'The [[cap:CAP-PER-01|source selection and lock receipt]] identifies the distribution/revision used for this recording. There is no required native Personas YAML: paths and reader settings belong to our application. Keep this source choice constant when comparing agent behaviour.'
      ]}
    ]},
    'persona.select':{title:'Select and inspect a person',intro:'Now choose one record from that dataset and read the person it describes. This gives you a concrete test participant before you add a learning request or run the advisor.',sections:[
      {paragraphs:[
        '[[call:persona.select|sample_personas]] applies the selected dataset filters, scans eligible IDs and uses reservoir sampling without replacement across that filtered local corpus. It then resolves the selected IDs to full rows. A supplied seed makes that selection process repeatable only while the source and eligibility set also remain the same.',
        'The selected demonstrations instead provide an explicit ID to the locking path. Their [[cap:CAP-PER-01|selection evidence]] records the chosen original, rather than a sampling seed or a complete history of earlier filtering. The same record has structured name Min Hoon Lim and preferred English name Caroline, which explains the name used in its narrative fields. Showing both names makes that relationship clear without changing the source.'
      ]}
    ]},
    'persona.lock':{title:'Verify and lock the original',intro:'After choosing a person, keep the exact record used by the test. The application saves its identity and calculates a content hash. On a later read, the hash lets it check whether the record has changed.',sections:[
      {paragraphs:[
        '[[call:persona.lock|lock_personas]] rejects duplicate or missing IDs, restores the requested order and returns original records plus their hashes. The selected run records distribution, revision and original SHA-256 in [[file:source-lock.json|the source-lock receipt]]. These are application operations; UserSim has not executed.',
        'The guide resolves the selected original against the installed source before showing the person. A missing source is an honest unavailable state. Keeping that constraint prevents a plausible replacement profile from making a broken reproduction appear successful.'
      ]}
    ]},
    'situation.authored':{title:'Supply the learning goal and constraints',intro:retail
      ? 'Before the learner speaks, define what each part of the test should reveal. Retail begins with an SMU programme question, then introduces salary concerns and finally a training budget and study days. The application writes this sequence as test instructions.'
      : board
        ? 'The authored story asks to learn to play board games and later tests a tempting mismatch: video-game design. The goal is to see whether the advisor admits that the available catalogue does not satisfy the original request.'
        : 'The authored photography situation supplies a beginner’s subject, Saturday availability and a budget under S$50. It gives the simulation a concrete task without inferring financial circumstances or availability from a synthetic profile.',sections:[
      {paragraphs:[
        '[[call:situation.authored|The scenario definition]] selects the story, public constraints and turn limit. [[file:situation.json|The saved situation]] shows the application-owned input to the test. It is neither a generated learner utterance nor a native Fabric configuration.',
        retail
          ? 'The salary band is a labelled hypothesis. It cannot populate budget_sgd, and private overlay fields cannot be sent to the advisor merely because they are available to the simulator. The separate public-context parser records constraints only after the learner states them.'
          : 'Keeping these values explicit makes a small variation interpretable: for example, changing only the spending limit tests constraint handling. Rewriting the person, goal and catalogue at the same time would make the cause of a different answer unclear.'
      ]}
    ]},
    'situation.bind':{title:'Bind the situation without changing the original',intro:'Combine the chosen person with the task you want to test. The application puts those inputs in a prepared UserSim row while keeping the original profile unchanged. UserSim will use that row when it generates the conversation.',sections:[
      {paragraphs:[
        '[[call:situation.bind|The preparation and binding code]] carries the selected theme, story ID and any chosen overlay into the episode input. The general experiment service can bind an approved Designer scenario after validating its schema. The current retail Journey instead attaches the selected retail overlay and its authored disclosure protocol. Public Preferences remain a separate object that controls what the advisor’s tools are allowed to assume.',
        retail
          ? 'Retail’s private overlay informs the simulator; the advisor’s budget/day inputs are accumulated from public messages instead. Compare [[file:situation.json|the prepared story]] with [[file:public-constraints.jsonl|the turn-by-turn public constraints]] to see that preparation and disclosure are different boundaries.'
          : 'The [[file:situation.json|situation receipt]] states which story and constraints were bound. The [[cap:CAP-US-01|resolved simulator input]] remains private because it contains the original and simulator context. The advisor receives the public message, rather than that whole row.'
      ]}
    ]},
    'designer.schema':{title:'Define seed data and closed schemas',intro:retail
      ? 'Tell Designer which values to copy and which new field to create. Here the original profile JSON and its hash are seed columns. A single generated retail_situation column will hold brand interests, a salary band and a short practical learning task.'
      : 'This scenario does not generate an overlay. The schema mechanism shown here belongs to the optional enrichment integration; the authored situation is sufficient for this preset.',sections:[
      {paragraphs:[
        retail
          ? '[[call:retail.designer.builder|The SDK builder setup]] uses DataDesignerConfigBuilder, an ordered LocalFileSeedSource and LLMStructuredColumnConfig. [[call:designer.schema|The closed retail schema]] becomes its output_format: allowed fields and values are declared before the SDK runs. That constrains shape; it does not make generated circumstances factual.'
          : '[[call:designer.schema|The optional workbench builder]] defines the seeded columns and permitted generated fields. Its output_format constrains shape; it does not make generated circumstances factual. This preset uses its authored situation instead.',
        'The builder supplies the actual SDK generation definition. [[cap:CAP-DD-01|Its saved configuration]] includes private seed and prompt fields, while [[cap:CAP-DD-02|the public settings summary]] selects the safe parts for review. The salary schema allows only 2500–3499, so that value is a controlled test assumption. Designer is not being asked to predict income.'
      ]}
    ]},
    'designer.generate':{title:'Generate the requested fields',intro:retail
      ? 'The application now launches the separate Designer 0.10.0 process and requests one row. Designer copies the two seed columns and fills the structured retail_situation column. Its model call is recorded under the Designer role so you can distinguish generation work from the conversation.'
      : 'No Designer generation is invoked for this preset. When enrichment is selected, the isolated job below is the real SDK path; displaying an authored situation must not be described as generated output.',sections:[
      {paragraphs:[
        '[[call:designer.generate|The generation call]] validates the builder, applies the effective RunConfig and calls DataDesigner.create with a batch-completion callback. [[cap:CAP-DD-03|Run/provider settings]] show execution controls separately from the column graph: concurrency is bounded, correction/restart counts are zero and credentials are omitted from review copies.',
        'The retail recording’s native batch contains one row and three physical columns: original_profile_json, original_profile_sha256 and retail_situation. The last column has three nested generated fields. [[file:designer-output.json|The selected output]] shows UNIQLO/Decathlon, the fixed salary band and the generated sales/inventory-analysis task. The application saves this as an overlay; it does not append a new person to the source dataset.',
        'Designer also profiles the generated batch. A one-row sample has no defined sample standard deviation, so our narrow 0.10 compatibility boundary represents that statistic as JSON null. [[cap:CAP-DD-05|The native profiling report]] records the result and the normalization. Generated values stay unchanged, and other profiling errors still stop generation.'
      ]}
    ]},
    'designer.lineage':{title:'Validate and retain lineage',intro:retail
      ? 'Before using the generated row, check that it still refers to the chosen original and contains only the permitted additions. The application accepts the overlay only after those checks pass. This gives the later conversation an identifiable, reviewable input.'
      : 'This preset has no generated overlay to validate. For generated situations, this application boundary verifies seed preservation and experiment rules before accepting an overlay. The authored situation used here follows a separate path.',sections:[
      {paragraphs:[
        '[[call:designer.lineage|The lineage/validation path]] checks the closed output schema and parent identity. In retail, the free-text learning situation may describe skills, but may not smuggle in a person’s name, money, funding or disclosure rules. The salary enum and brand interests remain explicitly hypothetical fields.',
        '[[file:designer-lineage.json|The lineage receipt]] connects the original profile hash, generated overlay and generation configuration. [[file:designer-output.json|The retained overlay]] is stored separately from the original. A validation failure means no accepted overlay; attaching a new label to invalid output would remove the reproducibility this boundary is meant to provide.'
      ]}
    ]},
    'usersim.prepare':{title:'Resolve persona, behaviour and probe',intro:'Prepare the information UserSim needs for one conversation. The persona describes the learner, behaviour settings shape how they interact, and the learning_advisor probe describes the task. UserSim combines those choices before generating the opening message.',sections:[
      {paragraphs:[
        '[[call:usersim.prepare|prepare_rows]] constructs ConversationSimulatorConfig and calls the public construct_episode_preamble API. Important choices are en_SG, the scenario’s turn limit, one query/assistant attempt, disabled context compression, persona grounding and the probe’s profile_only/story_id options. In HF mode the application explicitly supplies neutral/profile-only behaviour instead of inventing OCEAN scores.',
        'The returned row is saved in [[cap:CAP-US-01|resolved-inputs.json]] with the original, derived behaviour, theme, configuration and source identity. Because it includes private simulator context, the public [[file:usersim-setup.json|setup summary]] exposes only selected settings. [[cap:CAP-US-03|The role-model configuration]] separately records which models perform learner, judge and summary work. These are Python-built settings saved for inspection; the public summaries are not new runtime input formats.'
      ]}
    ]},
    'usersim.probe':{title:'Apply the custom learning-advisor hooks',intro:'A probe gives the conversation its purpose. Our LearningAdvisorProbe tells the simulated learner what help to seek and which follow-up matters to the test. UserSim supplies the shared turn-processing engine, so the probe only implements the task-specific parts.',sections:[
      {paragraphs:[
        '[[call:usersim.probe|LearningAdvisorProbe.get_user_system_prompt]] combines the synthetic profile, story theme and labelled assumptions with UserSim’s formatting helpers. Follow-up hooks specify the board-games distinction or retail disclosure sequence; gate instructions clarify that those planned follow-ups remain relevant. The inherited engine still performs generation, filtering and judging.',
        'The class lives in src/learning_lab/probe.py and registers as learning_advisor through the usersim.probes entry point in pyproject.toml. Its Python hooks supply the learner task, follow-up and gate instructions. This custom BaseProbe class uses the shared engine; it does not run one of UserSim’s built-in sovereign-AI or safety probes.',
        'The assistant-system hook returns an empty string because the external citizen application owns its advisor instructions and course tools. Its per-turn assistant-quality judge is inherited from UserSim: it asks whether the delivered answer addresses the request coherently. Our probe does not override that generic rubric or load a custom assistant-judge YAML. [[file:usersim-setup.json|The saved setup]] identifies the selected probe/options without exposing private simulator prompts.',
        'To author a new behavioural test, agree on the hypothesis first, then change the relevant probe option or Python hook. A planned follow-up belongs in format_followup_user_instructions; a task-specific interpretation of relevance belongs in format_gate_prompt. If your study needs a different assistant-quality rubric, BaseProbe also exposes format_assistant_judge_prompt for an explicit override. Record that rubric change as part of the experiment, rather than silently treating the inherited generic judge as a domain expert.'
      ]}
    ]},
    'usersim.loop':{title:'Generate/check a turn and process the reply',intro:'UserSim asks the host application to perform one piece of work at a time. That request is called an activation. The host returns a result under the same activation ID, then UserSim decides what should happen next using the conversation so far.',sections:[
      {paragraphs:[
        '[[call:usersim.loop|hosted_episode]] creates ProbeEpisodeRuntime.from_resolved_row and awaits advance(). A user-role activation generates learner text. Judge-role activations check the learner’s role/relevance or rate the delivered reply. Summary-role work supports the engine’s stopping decisions. These use the configured host models; they are separate from the advisor’s model calls.',
        'For an assistant activation, the host sends the latest public learner message to the citizen application. The application then returns the answer actually delivered to the learner. UserSim calls this an assistant activation even when application code can answer without running an agent. It counts one delegated application turn, not each model/tool exchange inside that turn.',
        retail
          ? 'The salary-only activation is answered by a clarification template in application code, before Fabric/model/tool dispatch. No advisor language-model call writes that reply. The public response still goes back to UserSim for judging, which uses its separate judge model. [[file:application-turns.json|The confirmed application-turn receipt]] explains the absence of a native invocation; it must not be replaced with a fabricated RunResult.'
          : 'The advisor may make several model/tool calls inside one delegated activation. [[file:usersim-activations.jsonl|Activation request/answer records]] show the outer loop, while native agent evidence shows the inner loop. Their counts measure different work.',
        'The selected configuration allows one assistant attempt. A negative quality verdict is retained without replacing the answer, which keeps the test from becoming a best-of-many selection. The host also rejects an unexpected request to repeat the external application activation, since that could repeat real tool work. [[cap:CAP-US-04|The saved activation/result records]] let you distinguish these engine decisions from the conversation itself.'
      ]}
    ]},
    'usersim.finalize':{title:'Stop and save the trajectory',intro:'When UserSim reaches the turn limit or a stopping condition, save what happened and close the runtime. The completed trajectory includes the conversation and the engine’s judgments. Saving it preserves weak answers as well as successful ones.',sections:[
      {paragraphs:[
        '[[call:usersim.finalize|runtime.finalize]] returns usersim-result.json with conversation_messages, conversation_metadata, simulation_outcome and simulation_traces. The full [[cap:CAP-US-04|result]] stays private because it also carries the original simulator context. The public quality-flag file selects failed assistant_quality traces; the full metadata retains all success/failure verdicts. The three demos contain zero, one and two such failures respectively. These are per-turn UserSim ratings, not counts of failed application assertions.',
        'This external-runtime integration saves JSON records. It does not run the UserSim CLI’s optional post-loop evaluation/report stages, and it does not create a trajectory Parquet or report dashboard for those stages. Re-scoring through our application checks or Helix is a different path and must be interpreted under its own criteria.'
      ]}
    ]},
    'catalogue.freeze':{title:'Freeze facts and source links',intro:'Keep the course information used by the test before the advisor starts. The application copies and validates those records, then gives the same snapshot to the course tools and later checks. This lets you explain the answer using the facts available at the time.',sections:[
      {paragraphs:[
        retail
          ? '[[call:catalogue.freeze|The retail freeze path]] merges the base catalogue and separately dated supplement, validates unique course IDs and computes the final content hash. It preserves each listing’s capture date rather than assigning one date to the whole merged dataset.'
          : '[[call:catalogue.freeze|freeze_catalogue]] preserves the selected snapshot and validates its records before use. Reproduction should use these frozen bytes, rather than silently replacing them with today’s provider pages.',
        '[[file:catalogue-snapshot.json|The actual snapshot]] is a factual input file, not a model configuration. Inspect cost ranges, extra costs, weekdays, duration and unknown notes together. A known fee with an unknown timetable does not establish a guaranteed match, and a missing duration cannot support a claim that a course is shorter.'
      ]}
    ]}
  };
}
