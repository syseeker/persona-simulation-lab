import type {TeachingPage} from './types';

/** Each destination owns one explanation; references identify its actual boundary. */
export function inputLibraries(scenario:string):Record<string,TeachingPage> {
  const retail=scenario==='dreamjob';
  return {
    personas:{title:'Nemotron Personas',intro:'Nemotron Personas supplies synthetic background records. In this application it is a dataset, rather than a service that receives a prompt and invents a person. Our reader selects an original row and preserves its identity before any conversation starts.',sections:[
      {paragraphs:[
        'The public Hugging Face Singapore distribution and Singapore NGC Extended have different schemas and terms. HF is profile-only here; NGC Extended includes the original OCEAN fields used for behavioural conditioning. A field describing a synthetic person is context for a test, not proof of a real resident’s behaviour or eligibility.',
        'Loading, filtering, sampling and hashing belong to this repository. That separation lets you replace the storage or selection method without pretending that it is a NeMo model operation. The [[url:https://huggingface.co/datasets/nvidia/Nemotron-Personas-Singapore|HF dataset card]] and [[url:https://catalog.ngc.nvidia.com/orgs/nvidia/teams/nemotron-personas/resources/nemotron-personas-dataset-en_sg|NGC Extended distribution]] define the source boundary; the selected recording determines which one was used.'
      ]}
    ]},
    situation:{title:'Authored situation',intro:'The situation is our experiment specification: what the learner asks about today, what constraints are supplied and what information may be disclosed later. It remains separate from the person’s original profile, so an authored spending limit cannot silently become a demographic fact.',sections:[
      {paragraphs:[retail
        ? 'Retail combines a source-seeded hypothetical overlay with an authored three-turn disclosure protocol. Designer supplies labelled enrichment; the application supplies the experimental sequence. The salary range appears in turn 2, while the total training budget and weekend availability appear in turn 3. Salary never supplies the missing budget.'
        : scenario==='boardgames'
          ? 'The board-games story fixes the goal of learning to play, then asks whether video-game design is equivalent. This deliberate follow-up tests whether the advisor preserves the learner’s original intent when the catalogue lacks a suitable class.'
          : 'Photography supplies beginner photography, Saturday availability and a spending limit under S$50. Those constraints are the developer’s test input. The simulator may phrase the request naturally, but it is not discovering the budget or timetable from the profile.',
        'Keeping the experiment in application code makes its assumptions reviewable. It also limits what this example demonstrates: it tests the specified story, rather than establishing the distribution of needs among Singapore residents.'
      ]}
    ]},
    designer:{title:'NeMo Data Designer',intro:retail
      ? 'Data Designer generates structured hypothetical enrichment from the selected source record. The original record is the seed; the generated fields are a separate overlay. We use its schema-constrained generation pipeline to create test variation without modifying the source person.'
      : 'This preset uses an authored situation and does not run Data Designer. Adding generation would introduce another variable without helping this particular test. The library is used in retail when a source-seeded, explicitly hypothetical overlay is part of the question being tested.',sections:[
      {paragraphs:[
        'A builder describes seed columns, generated columns and their model dependencies. The SDK validates that graph, runs inference for the generated columns and retains generation/profiling artifacts. Our closed schema and lineage validation remain application responsibilities: SDK generation alone cannot establish that a salary is true or that the original row was preserved.',
        'The [[url:https://docs.nvidia.com/nemo/datadesigner/v0.10.0/concepts/architecture-performance|Data Designer 0.10 architecture and execution model]] is the reference for this isolated integration. UserSim’s compatible environment contains a different Designer version; combining their dependency environments would change the tested integration.'
      ]}
    ]},
    usersim:{title:'NeMo UserSim',intro:'UserSim drives the test conversation around an external application. It prepares a simulated learner, generates and checks learner turns, delegates assistant activations to our citizen advisor, then judges replies and decides whether to continue. Here “assistant” means the whole advisor application, including its selected harness and real course tools.',sections:[
      {paragraphs:[
        'The custom learning_advisor probe supplies the subject and story-specific disclosure instructions. UserSim’s inherited engine supplies the conversation machinery; we have not copied that loop into a second simulator. Its user and judge models are separate roles from the advisor’s model, so an assistant activation is not a count of provider calls.',
        'For NGC input, the SDK derives a behavioral_profile from the original traits and background. Its patience value influences frustration handling; verbosity and cooperativeness describe interaction tendencies. The probe’s SDK formatter expresses personality through the OCEAN descriptions and adds tech_literacy and error_proneness cues about technology confidence and communication mistakes, rather than injecting every derived number as another instruction. These are simulation controls, not observed human traits. For HF profile-only input, the application supplies an empty behavioural profile and neutral interaction style instead of inventing OCEAN scores.',
        'The [[url:https://github.com/NVIDIA-NeMo/UserSim/blob/v0.3.0/architecture/overview.md|UserSim 0.3 architecture]] separates person, behaviour, probe and evaluation. The [[url:https://github.com/NVIDIA-NeMo/UserSim/blob/v0.3.0/docs/engine/EXTERNAL_PROBE_RUNTIME.md|external runtime contract]] explains how our host executes activations. The retained path saves a JSON trajectory and native outcomes; it does not invoke the optional post-loop eval/report workflow or produce its report dashboard.',
        retail
          ? 'In the current retail flow, the salary-only turn can receive an application-owned clarification without any Fabric invocation. UserSim still observes a public assistant response and judges that response. There are three public turns, but only the agent-dispatched turns have native Fabric/model/tool evidence.'
          : 'The target keeps one agent runtime across this scenario’s public turns. That conversation continuity is narrower than long-term memory across independent tests, which this example does not establish.'
      ]}
    ]},
    catalogue:{title:'Frozen course catalogue',intro:'The catalogue is the application’s bounded factual source. It stores dated, source-linked course records that the advisor may retrieve through the course tools. Freezing it per run makes a recommendation and its later evaluation refer to the same facts.',sections:[
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
    'persona.source':{title:'Load the original distribution',intro:'Start with an explicit source choice. The application opens installed Arrow/Parquet data through its dataset reader; it does not call a persona-generation endpoint. Source metadata tells the reader which schema and revision to expect before a row can be selected.',sections:[
      {paragraphs:[
        '[[call:persona.source|The dataset loader]] resolves the chosen distribution and checks its installed assets. NGC readiness also requires the original identity and behavioural-field audit. An unavailable or invalid selected installation must produce an unavailable/error state, rather than silently substituting the other distribution.',
        'The [[cap:CAP-PER-01|source selection and lock receipt]] identifies the distribution/revision used for this recording. There is no required native Personas YAML: paths and reader settings belong to our application. Keep this source choice constant when comparing agent behaviour.'
      ]}
    ]},
    'persona.select':{title:'Select and inspect a person',intro:'Selection chooses a particular original row, rather than prompting for a convenient example. Inspect the person before running the test so you can distinguish original background from assumptions added by the learning story.',sections:[
      {paragraphs:[
        '[[call:persona.select|sample_personas]] applies the selected dataset filters, scans eligible IDs and uses reservoir sampling without replacement across that filtered local corpus. It then resolves the selected IDs to full rows. A supplied seed makes that selection process repeatable only while the source and eligibility set also remain the same.',
        'An explicitly chosen ID instead follows the locking path. The [[cap:CAP-PER-01|recorded original-selection evidence]] preserves the selected identity; it should not be interpreted as proof of sampling filters that were never captured. Changing the person is a useful new test, but it changes the input and should receive a separate result.'
      ]}
    ]},
    'persona.lock':{title:'Verify and lock the original',intro:'Locking turns a selected ID into a reproducible test input. The application resolves that ID in the specified distribution, preserves the complete original privately and computes a content hash. Reusing the ID with changed row contents must not count as reusing the same person.',sections:[
      {paragraphs:[
        '[[call:persona.lock|lock_personas]] rejects duplicate or missing IDs, restores the requested order and returns original records plus their hashes. The selected run records distribution, revision and original SHA-256 in [[file:source-lock.json|the source-lock receipt]]. These are application operations; UserSim has not executed.',
        'The guide resolves the selected original against the installed source before showing the person. A missing source is an honest unavailable state. Keeping that constraint prevents a plausible replacement profile from making a broken reproduction appear successful.'
      ]}
    ]},
    'situation.authored':{title:'Supply the learning goal and constraints',intro:retail
      ? 'Define the disclosure experiment before generating any learner wording. The test first asks about the SMU programme, then discloses hypothetical salary concerns, then states an explicit total training budget and study days. These are distinct pieces of information with different release times.'
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
    'situation.bind':{title:'Bind the situation without changing the original',intro:'Binding creates the resolved simulator input from the locked person and selected story. It attaches the current learning task to a derived row, while preserving the original record as its parent. This is preparation for conversation generation, not a generated conversation.',sections:[
      {paragraphs:[
        '[[call:situation.bind|The preparation and binding code]] carries the selected theme, story ID and any explicitly selected overlay into the episode context. For approved Designer scenarios the schema is checked before generated fields can influence the situation. Public Preferences remain a separate typed object.',
        retail
          ? 'Retail’s private overlay informs the simulator; the advisor’s budget/day inputs are accumulated from public messages instead. Compare [[file:situation.json|the prepared story]] with [[file:public-constraints.jsonl|the turn-by-turn public constraints]] to see that preparation and disclosure are different boundaries.'
          : 'The [[file:situation.json|situation receipt]] states which story and constraints were bound. The [[cap:CAP-US-01|resolved simulator input]] remains private because it contains the original and simulator context. The advisor receives the public message, rather than that whole row.'
      ]}
    ]},
    'designer.schema':{title:'Define seed data and closed schemas',intro:retail
      ? 'Before generation, specify exactly what Designer may add. This integration seeds the original profile JSON and its hash, then requests one structured retail_situation column containing permitted brand interests, a fixed experimental salary-band enum and a short learning situation.'
      : 'This scenario does not generate an overlay. The schema mechanism shown here belongs to the optional enrichment integration; the authored situation is sufficient for this preset.',sections:[
      {paragraphs:[
        retail
          ? '[[call:retail.designer.builder|The SDK builder setup]] uses DataDesignerConfigBuilder, an ordered LocalFileSeedSource and LLMStructuredColumnConfig. [[call:designer.schema|The closed retail schema]] becomes its output_format: allowed fields and values are declared before the SDK runs. That constrains shape; it does not make generated circumstances factual.'
          : '[[call:designer.schema|The optional workbench builder]] defines the seeded columns and permitted generated fields. Its output_format constrains shape; it does not make generated circumstances factual. This preset uses its authored situation instead.',
        '[[cap:CAP-DD-01|The saved native builder configuration]] contains the generation definition; its private seed/prompt portions are not published. [[cap:CAP-DD-02|The safe generation-settings summary]] is an application projection, not a substitute runnable builder input. Changing the allowed salary enum changes the experiment, rather than estimating a person’s real income.'
      ]}
    ]},
    'designer.generate':{title:'Generate the requested fields',intro:retail
      ? 'The application launches the isolated Designer 0.10 integration with the locked source seed and closed schema. One generated row is requested. Inference is attributed to the Designer role through the shared gateway, keeping it distinct from the learner and advisor models.'
      : 'No Designer generation is invoked for this preset. When enrichment is selected, the isolated job below is the real SDK path; displaying an authored situation must not be described as generated output.',sections:[
      {paragraphs:[
        '[[call:designer.generate|The generation call]] validates the builder, applies the effective RunConfig and calls DataDesigner.create with a batch-completion callback. [[cap:CAP-DD-03|Run/provider settings]] show execution controls separately from the column graph: concurrency is bounded, correction/restart counts are zero and credentials are omitted from review copies.',
        'Read [[cap:CAP-DD-04|the generated fields and generation receipt]] together with [[cap:CAP-DD-05|the native profiling report]]. A single row has no defined sample standard deviation. Our version-specific compatibility boundary preserves that missing statistic as JSON null so Designer can complete its real report; it changes no generated data and records exactly which statistic was normalized. Other profiling errors stop the job. Earlier failed reports remain unchanged.'
      ]}
    ]},
    'designer.lineage':{title:'Validate and retain lineage',intro:retail
      ? 'A structurally valid SDK row still needs application validation. We verify that it preserves its seed and that generated fields stay inside the permitted experiment. Only then can the overlay be selected as input to the simulator.'
      : 'This preset has no generated overlay to validate. For generated situations, this application boundary verifies seed preservation and experiment rules before accepting an overlay. The authored situation used here follows a separate path.',sections:[
      {paragraphs:[
        '[[call:designer.lineage|The lineage/validation path]] checks the closed output schema and parent identity. In retail, the free-text learning situation may describe skills, but may not smuggle in a person’s name, money, funding or disclosure rules. The salary enum and brand interests remain explicitly hypothetical fields.',
        '[[file:designer-lineage.json|The lineage receipt]] connects the original profile hash, generated overlay and generation configuration. [[file:designer-output.json|The retained overlay]] is stored separately from the original. A validation failure means no accepted overlay; attaching a new label to invalid output would remove the reproducibility this boundary is meant to provide.'
      ]}
    ]},
    'usersim.prepare':{title:'Resolve persona, behaviour and probe',intro:'Preparation builds the actual UserSim episode input. The original supplies who the learner is; behaviour settings influence interaction style; the learning_advisor probe supplies what capability and situation the conversation will exercise. None of these steps has generated the public opening message yet.',sections:[
      {paragraphs:[
        '[[call:usersim.prepare|prepare_rows]] constructs ConversationSimulatorConfig and calls the public construct_episode_preamble API. Important choices are en_SG, the scenario’s turn limit, one query/assistant attempt, disabled context compression, persona grounding and the probe’s profile_only/story_id options. In HF mode the application explicitly supplies neutral/profile-only behaviour instead of inventing OCEAN scores.',
        '[[cap:CAP-US-01|The resolved input]] is the private native preparation record. [[cap:CAP-US-03|The effective role-model settings]] identify the host models; [[file:usersim-setup.json|the companion setup]] is a safe summary. These objects are created in Python, so there is no mandatory UserSim YAML to look for.'
      ]}
    ]},
    'usersim.probe':{title:'Apply the custom learning-advisor hooks',intro:'Our probe customises the learner’s task without reimplementing UserSim’s engine. It is registered as learning_advisor through the public extension API. The same probe class supports the three stories through explicit options and scenario-specific hooks.',sections:[
      {paragraphs:[
        '[[call:usersim.probe|LearningAdvisorProbe.get_user_system_prompt]] combines the synthetic profile, story theme and labelled assumptions with UserSim’s formatting helpers. Follow-up hooks specify the board-games distinction or retail disclosure sequence; gate instructions clarify that those planned follow-ups remain relevant. The inherited engine still performs generation, filtering and judging.',
        'The assistant-system hook returns an empty string because the external advisor owns its own policy and MCP tools. The simulator’s private profile/preamble is not an extra advisor system prompt. [[file:usersim-setup.json|The saved simulator setup]] identifies the probe/options without publishing that private prompt; this custom probe was not a run of an unrelated built-in safety or sovereign-AI probe.'
      ]}
    ]},
    'usersim.loop':{title:'Generate/check a turn and process the reply',intro:'The host drives UserSim one activation at a time. Each activation specifies a role and requested work; the host returns the answer under the same activation ID before asking the engine to advance. A later learner message therefore depends on the actual earlier reply.',sections:[
      {paragraphs:[
        '[[call:usersim.loop|hosted_episode]] creates ProbeEpisodeRuntime.from_resolved_row, awaits advance(), and distinguishes assistant activations from user/judge work. The latter use their host role models. An assistant activation sends only the latest public user message to the external target and returns the content actually delivered to the learner.',
        retail
          ? 'The salary-only activation may be answered by the application’s clarification branch before Fabric/model/tool dispatch. That public response still goes back to UserSim for judging. [[file:application-turns.json|The confirmed application-turn receipt]] explains the absence of a native invocation; it must not be replaced with a fabricated RunResult.'
          : 'The advisor may make several model/tool calls inside one delegated activation. [[file:usersim-activations.jsonl|Activation request/answer records]] show the outer loop, while native agent evidence shows the inner loop. Their counts measure different work.',
        'The application rejects unexpected assistant resampling because replaying a side-effectful target activation is unsafe. Attempt limits are part of the effective configuration; an invalid activation is not silently retried until it looks plausible.'
      ]}
    ]},
    'usersim.finalize':{title:'Stop and save the trajectory',intro:'When no further activation is requested, the host asks UserSim to finalize the episode and always closes the runtime. Finalization preserves the engine’s outcome, counters, warnings and trajectory; it is not a second generation pass that repairs a weak conversation.',sections:[
      {paragraphs:[
        '[[call:usersim.finalize|runtime.finalize]] returns the native result after the engine has reached its limit or stopping condition. The full [[cap:CAP-US-04|native trajectory/result]] stays private; the public conversation and quality-flag projection expose the allowed review material. An early stop or helpfulness failure remains part of that result even if application assertions later pass.',
        'This external-runtime integration saves JSON records. It does not run the UserSim CLI’s optional post-loop evaluation/report stages, and it does not create a trajectory Parquet or report dashboard for those stages. Re-scoring through our application checks or Helix is a different path and must be interpreted under its own criteria.'
      ]}
    ]},
    'catalogue.freeze':{title:'Freeze facts and source links',intro:'A test needs a fixed answerable world. Before the advisor starts, the application copies the course facts into a run-owned snapshot and validates them as Course records. That snapshot is then used by both the tools and the saved-response checks.',sections:[
      {paragraphs:[
        retail
          ? '[[call:catalogue.freeze|The retail freeze path]] merges the base catalogue and separately dated supplement, validates unique course IDs and computes the final content hash. It preserves each listing’s capture date rather than assigning one date to the whole merged dataset.'
          : '[[call:catalogue.freeze|freeze_catalogue]] preserves the selected snapshot and validates its records before use. Reproduction should use these frozen bytes, rather than silently replacing them with today’s provider pages.',
        '[[file:catalogue-snapshot.json|The actual snapshot]] is a factual input file, not a model configuration. Inspect cost ranges, extra costs, weekdays, duration and unknown notes together. A known fee with an unknown timetable does not establish a guaranteed match, and a missing duration cannot support a claim that a course is shorter.'
      ]}
    ]}
  };
}
