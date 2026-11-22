import type {LessonId} from '../lessonArchitecture';
import type {TeachingPage} from './types';

type Story = 'photography' | 'boardgames' | 'dreamjob';
type Versions = Record<Story, string>;

function selected(scenarioId: string, versions: Versions): string {
  if (!Object.hasOwn(versions, scenarioId)) throw new Error('Unknown teaching scenario');
  return versions[scenarioId as Story];
}

function chapter(title: string, intro: string, scenario: string, mechanism: string[],
  observation: LessonId, flow?: string[]): TeachingPage {
  return {title, intro, sections: [
    {heading: 'In this scenario', paragraphs: [scenario], observation},
    {heading: 'How it works', paragraphs: mechanism, ...(flow ? {flow} : {})},
  ]};
}

/** Lessons explain cooperation. Library and operation pages own API tutorials. */
export function lessonPage(scenarioId: string, stageId: LessonId, detailed: boolean): TeachingPage {
  switch (stageId) {
    case 'persona': return detailed ? chapter('Choose a test persona',
      'A reproducible simulation starts with an identifiable input person. In this application, choosing that person is dataset-reading and selection code: it does not call UserSim or ask a model to invent a profile. Keeping the original intact lets you change an agent later without silently changing who tested it.',
      selected(scenarioId, {
        photography: 'The profile below is the original selected for the photography recording. Read its background before deciding what this one test can represent. An interest or age field is context for the simulator; it is not evidence that every similar person wants a photography class.',
        boardgames: 'The board-games recording has its own selected original. Its background gives UserSim a person to portray, while the test will examine whether the advisor preserves that person’s stated wish to play games. A profile trait does not authorize substituting a different learning goal.',
        dreamjob: 'Retail learning begins with an original Singapore profile. Generated brand preferences and salary hypotheses are separate inputs introduced during situation preparation; they must not appear as original dataset attributes here.',
      }), [
        'The application reads the chosen distribution, retains the selected original and records its revision and content identity. The guide resolves that identity against the installed source before displaying the person. [[cap:CAP-PER-01|The selection receipt]] identifies the input; it establishes neither population coverage nor unrecorded sampling decisions.',
        'HF profile-only data and NGC Singapore Extended have different fields. Use the distribution named by this recording rather than assuming OCEAN traits exist in both. If that source cannot be matched, an unavailable profile is the correct outcome; sampling a replacement would create a different test.',
      ], 'persona') : chapter('Choose a test persona',
      'Before testing an advisor, choose a person to test with. A synthetic profile supplies a background, interests and, where available, behaviour traits. It helps the simulated learner speak as someone with particular needs instead of as a generic test prompt.',
      selected(scenarioId, {
        photography: 'Meet the person selected for the photography test below. This person will ask for help with a first class; the request itself comes next. Read the profile as one example of a learner, rather than a description of all Singapore residents.',
        boardgames: 'This person will ask about learning to play board games. Keeping the same person across the conversation helps us see whether the advisor follows their intent when a tempting but different activity is mentioned.',
        dreamjob: 'This person will explore retail-related learning. Their original background is the starting point. The additional salary and brand details used by this test will be introduced separately, so you can tell what the source actually supplied.',
      }), [
        'The app selects an existing synthetic profile and keeps a receipt identifying that exact original. The person shown here is read from that source, rather than written to make the demonstration look convincing. [[cap:CAP-PER-01|The saved selection]] lets another developer use the same starting point.',
        'One person makes a useful repeatable example, but cannot establish that the advisor works well for everyone. A later test could deliberately choose a different background while keeping the situation and application unchanged.',
      ], 'persona');

    case 'situation': return detailed ? chapter('Create a situation',
      'A profile answers who the simulated user is; a situation defines what this test asks them to attempt. Preparation combines the original with scenario-owned goals, disclosure rules and probe settings. UserSim then uses those resolved inputs when its conversation engine runs; preparing them does not generate a completed conversation.',
      selected(scenarioId, {
        photography: 'The authored situation supplies beginner photography, Saturday availability and a budget under S$50 before funding. UserSim may phrase that request in the selected person’s voice. It is not asked to discover or invent those constraints, and no separate Designer enrichment job is used.',
        boardgames: 'The authored probe preserves the goal of playing board games across two public turns. The later distinction from designing digital games tests whether the advisor keeps the original intent. There is no Designer overlay to manufacture a more convenient catalogue match.',
        dreamjob: 'Designer enriches the original with explicitly hypothetical retail interests, brands and a salary band. A separate authored protocol controls disclosure: salary becomes public in turn 2; the S$3,000 training budget and weekends become public in turn 3. Generated salary is never interpreted as spending capacity.',
      }), [
        selected(scenarioId, {
          photography: 'The [[call:situation.authored|scenario preset]] and [[call:usersim.prepare|preparation code]] create the effective person/behaviour/probe inputs. [[cap:CAP-US-01|The resolved UserSim inputs]] are the useful configuration boundary: compare what the simulator received, while keeping that private context out of the advisor request.',
          boardgames: 'The [[call:usersim.probe|custom learning-advisor probe]] supplies the test’s instructions while inheriting the UserSim conversation engine. Its role is to specify this task, rather than reimplement generation, turn checks and stopping. [[file:usersim-setup.json|The saved probe settings]] show the configured test rather than an unrelated built-in safety or sovereign-AI probe.',
          dreamjob: 'The [[cap:CAP-DD-01|Designer seed and closed schema]] request only the permitted derived fields. Generation and application validation are separate boundaries: [[cap:CAP-DD-04|the selected overlay and lineage]] identify what was retained and its original parent. The simulator receives that overlay with disclosure instructions; the advisor receives only later public messages.',
        }),
        'The custom probe, interpreted behaviour and scenario constraints have different owners. Inspect [[cap:CAP-US-02|the effective preparation record]] to distinguish them. Authored disclosure is a deliberate test protocol; it does not prove that the engine’s optional probabilistic disclosure or simulation-health diagnostics were exercised. The actual generated messages belong to Run the application.',
      ], 'situation') : chapter('Create a situation',
      'Knowing someone’s background does not tell us what they need today. A situation gives the selected person a reason to approach the advisor and states the constraints this test should respect. Separating those choices makes it possible to explain why a particular conversation happened.',
      selected(scenarioId, {
        photography: 'We supply a simple task: find beginner photography on Saturday for under S$50 before funding. Those are test instructions, rather than facts discovered in the profile. UserSim will turn them into the learner’s own request when the conversation starts.',
        boardgames: 'We ask the learner to look for a way to play board games, then explore whether video-game design would serve the same purpose. This creates a useful test even when the catalogue has no suitable class: the advisor should acknowledge the gap and preserve the learner’s goal.',
        dreamjob: 'We create a retail-learning situation and add hypothetical details with Data Designer. The learner reveals salary only after the opening exchange, then gives an actual training budget and weekend availability. This lets us test whether the advisor waits for a spending limit instead of guessing one from income.',
      }), [
        selected(scenarioId, {
          photography: 'The app combines the chosen person with this authored situation and prepares UserSim’s instructions. [[cap:CAP-SIT-01|The situation record]] shows the goal we supplied; [[cap:CAP-US-01|the simulator’s prepared inputs]] show how it was given to the conversation engine. No learner has spoken at this preparation stage.',
          boardgames: 'The app gives UserSim the person, the learning goal and the conversation rules. UserSim acts as the learner rather than as the course advisor. [[cap:CAP-SIT-01|The saved situation]] lets you see the test intent before comparing it with the messages generated later.',
          dreamjob: 'Designer proposes extra test details; the app checks and stores the accepted additions separately from the original person. [[cap:CAP-DD-04|The selected hypothetical details]] show that result. UserSim is then instructed when those details may enter the public conversation, so hidden simulator context does not become advance knowledge for the advisor.',
        }),
      ], 'situation');

    case 'build': return detailed ? chapter('Build and connect the agent',
      'The citizen advisor needs instructions, a selected agent harness, a model endpoint and a restricted course-tool interface. Fabric joins those settings behind a common runtime contract. This lesson covers assembling and starting that runtime; sending a learner message is a later operation.',
      selected(scenarioId, {
        photography: 'Photography selects the Deep Agents adapter and a fixed model route. The tool surface contains course search, details and comparison. This intentionally small setup lets you review the common Fabric lifecycle without Designer, routing optimization or a managed deployment.',
        boardgames: 'Board games selects Hermes through Fabric. The adapter and Hermes settings differ from photography, but the application still plans, starts and invokes a Fabric runtime. Selecting another harness should not require a second business-logic implementation of the advisor.',
        dreamjob: 'Retail starts a persistent Deep Agents runtime for the baseline and fresh runtimes for comparison conditions. The application also enables its source-based public response boundary. A native model proposal and the application’s delivered answer therefore have separate responsibilities and evidence.',
      }), [
        '[[call:fabric.config|build_config]] constructs the installed SDK’s actual typed configuration. [[cap:CAP-FAB-01|The recorded settings]] express that decision. Fabric planning and Doctor preflight then check resolution and readiness before startup; [[cap:CAP-FAB-03|their reports]] are preparation evidence, not proof of an answered request.',
        'Runtime startup connects the adapter, instructions and MCP tool schemas, while Relay instrumentation attaches to the harness. [[cap:CAP-FAB-04|The lifecycle record]] identifies what started. Model access remains host-side through the gateway and LiteLLM; the application, harness and course tools execute inside OpenShell. Discovering a tool means it is available, not that the agent has called it.',
      ], 'build') : chapter('Build and connect the agent',
      'Turn the application’s ingredients into an advisor that can run. Instructions describe the job, a model provides language and reasoning, and read-only course tools provide facts. The harness manages the conversation and tool use; Fabric gives the application a consistent way to configure and start it.',
      selected(scenarioId, {
        photography: 'For photography we connect Deep Agents to the fixed model and the course catalogue. The advisor can look up a listing and explain unknown costs, but it has no booking or payment tool. Its available actions reflect the job we want it to do.',
        boardgames: 'For board games we connect Hermes to the same kind of course service. Fabric remains the application’s entry point. This shows where a harness choice changes the setup while leaving the citizen-facing purpose and read-only tools understandable.',
        dreamjob: 'For retail learning we connect Deep Agents and the course tools, then add an application rule for presenting verified returned facts. We also prepare separate model-comparison runs. Their outcomes will be reviewed independently instead of being mixed into the baseline conversation.',
      }), [
        'The app builds a configuration, asks Fabric to check it and starts one conversation runtime. [[cap:CAP-FAB-03|The preparation reports]] help distinguish a valid setup from a runtime that actually started. A missing adapter or broken tool connection should be visible here, before interpreting any answer.',
        'We use a shared Fabric interface so the application does not need separate execution code for every harness. The tradeoff is another configuration boundary to understand. The next lesson follows a real public message through that boundary; this one establishes what the advisor is ready to use.',
      ], 'build');

    case 'run': return detailed ? chapter('Run the application',
      'Execution contains two cooperating loops. UserSim generates a learner turn, checks it and processes the advisor’s response; the selected harness may make several model/tool calls while answering one public turn. A public turn is therefore neither one model call nor necessarily one native agent invocation.',
      selected(scenarioId, {
        photography: 'The single public request goes from UserSim through the application into a Fabric RunRequest. Deep Agents can query the course MCP server, consume its returned facts and produce a normalized result. The recorded public exchange below is the outcome to interpret, rather than the authored story text.',
        boardgames: 'Two public exchanges use the same Hermes runtime. UserSim generates the follow-up after receiving the first reply, so the advisor must preserve the original playing goal across turns. A successful empty search is legitimate evidence; inventing an attractive substitute would change the task.',
        dreamjob: 'Retail keeps three public turns but uses native agent execution for turns 1 and 3. At turn 2, salary has been disclosed without a training budget or study days. The application asks for those missing constraints before another model or tool call; that confirmed clarification is not a third Fabric result.',
      }), [
        selected(scenarioId, {
          photography: 'The public message enters [[call:fabric.invoke|runtime.invoke]] and its [[cap:CAP-FAB-05|captured request]]. The adapter runs the configured harness and returns [[cap:CAP-FAB-06|a normalized RunResult]]. UserSim then judges the delivered response and finalizes its trajectory; it does not see the advisor’s private internal reasoning.',
          boardgames: 'The common [[call:fabric.invoke|Fabric invocation call]] remains the application boundary even though Hermes owns the internal loop. Compare the selected turn’s [[cap:CAP-FAB-05|request]] with [[cap:CAP-FAB-06|its result]], then read how UserSim continues or stops. Its public-turn limit is separate from the harness’s internal execution bounds.',
          dreamjob: '[[call:retail.response.clarify|The pre-agent clarification branch]] checks public decision constraints first. Native turns retain their original proposals and Fabric identities; [[call:retail.response.render|the application response boundary]] separately formats returned course facts. [[cap:CAP-FAB-07|The delivery decisions]] distinguish the public answer from the model proposal, and output safeguards must permit delivery before it is acknowledged.',
        }),
        '[[cap:CAP-US-04|The UserSim activation and trajectory records]] show what its engine generated and retained. Follow-up context is based on replies actually delivered. In-loop helpfulness/stop judgments belong to that interaction; the later saved-response evaluation asks different questions. A valid answer does not by itself establish that every engine judgment agreed.',
      ], 'run') : chapter('Run the application',
      'Now watch the prepared learner talk to the advisor. The learner sends a request; the advisor can look up course facts before replying. Each follow-up reacts to the previous answer, so this is an interaction rather than a script of prewritten successful replies.',
      selected(scenarioId, {
        photography: 'The learner asks for a Saturday photography class within the stated budget. Read the lookup and answer together: the listed price can be known while extra materials remain unconfirmed. The advisor should preserve that distinction when explaining an option.',
        boardgames: 'The learner first asks to play board games, then asks about a different kind of activity. The useful outcome may be an honest no-match. The second answer should help the learner understand the difference instead of quietly replacing their original goal.',
        dreamjob: 'The learner asks about a programme, discloses income, then states a spending limit and weekend availability. After income alone, the application asks for the missing budget and study days without calling the agent again. It resumes the agent only when the learner supplies those constraints.',
      }), [
        selected(scenarioId, {
          photography: 'UserSim plays the learner. The citizen application passes the public request to the advisor and returns its answer. [[cap:CAP-US-04|The recorded conversation]] contains what was actually said, while the tool records show which facts the advisor obtained.',
          boardgames: 'UserSim receives the first reply before generating the next learner message. The advisor keeps its conversation context, so it can relate the follow-up to the original request. [[cap:CAP-US-04|The saved interaction]] lets you inspect that continuity rather than assuming it from the two-turn setting.',
          dreamjob: 'The clarification is ordinary application logic asking a necessary question. It is clearly labelled so you can distinguish it from an agent-generated proposal. For the other turns, the application presents returned course facts and explicit unknowns; [[cap:CAP-FAB-07|the response record]] keeps that presentation decision visible.',
        }),
      ], 'run');

    case 'investigate': return detailed ? chapter('Investigate execution',
      'An execution trace helps explain how a specific answer was produced. Start with the selected public turn, identify any captured Fabric invocation, then inspect the native model/tool scopes associated with it. Preserve missing correlations rather than turning a run-wide export into an invented per-turn sequence.',
      selected(scenarioId, {
        photography: 'Follow the actual course request and returned listing behind the photography answer. Compare the public Saturday/budget constraints with the tool arguments, then check which fee and uncertainty fields were available when the reply was produced.',
        boardgames: 'Distinguish a completed search returning no suitable board-game class from a failed or malformed tool response. For the follow-up, inspect whether Hermes made another lookup or reused public context. Either is possible; the selected turn’s native records determine what can be claimed.',
        dreamjob: 'Retail requires two views of the same execution: native proposals and application-delivered replies. Turn 2 has an application clarification receipt rather than a Fabric/model subtree. Its reference to an earlier course is reuse of previously returned facts, not evidence of a new search.',
      }), [
        'Relay attaches instrumentation to the harness and exports parent-linked scopes. [[cap:CAP-REL-02|The native event export]] supports observed order and ownership; [[cap:CAP-MCP-03|the actual tool records]] carry arguments and domain results. A search result, details object, comparison and domain error need different interpretations.',
        '[[cap:CAP-GW-02|Gateway accounting]] separately records the simulated learner, advisor and judge calls. It is not automatically joined to every Relay scope. These recordings use file output; there is no hidden Phoenix dashboard or collector trace to open. Lifecycle records explain startup/closure, while invocation results explain the selected reply.',
      ], 'investigate') : chapter('Investigate execution',
      'Read an answer as a small evidence trail: what did the learner ask, what information did the advisor obtain, and how did that information support the reply? A count of calls is less useful than understanding the result of the important lookup.',
      selected(scenarioId, {
        photography: 'Look for the course facts behind the photography recommendation. A published class fee can support the quoted amount, while an unknown materials fee explains why the advisor should ask the learner to confirm the full cost.',
        boardgames: 'Look closely at the no-match. A tool that ran successfully and found no suitable class supports an honest explanation. A tool that failed supports only an admission that the lookup failed; those are different reasons for not recommending a course.',
        dreamjob: 'Compare the sourced programme facts with the public answer. On the salary-only turn, the application should ask for a budget and schedule; no fresh model or course lookup is needed. Later advice can use earlier public context without pretending a new lookup occurred.',
      }), [
        'The selected records below connect the reply to the actions we can actually observe. [[cap:CAP-MCP-03|The saved course-tool evidence]] is where you can open the returned facts yourself. If the recording cannot connect an action to this turn, the guide should tell you that rather than attach the whole run to the answer.',
        'Relay records what happened inside the agent execution. A separate application record counts model work for the advisor, simulated learner and judges. Keeping those sources distinct helps diagnose a problem without mistaking the learner’s work for the advisor’s work.',
      ], 'investigate');

    case 'evaluate': return detailed ? chapter('Evaluate behaviour',
      'Evaluation turns a requirement into a criterion with an expected result, observed value and stated coverage. This application evaluates saved public responses against the frozen catalogue and execution evidence. Re-scoring that material does not need to simulate another conversation.',
      selected(scenarioId, {
        photography: 'The application checks supported course identifiers/links, the stated schedule and budget, attributable tool activity and honest cost uncertainty. These are application-authored assertions. This preset does not invoke Helix or UserSim’s optional post-loop evaluator.',
        boardgames: 'The application checks that the no-match is supported and that the follow-up preserves the playing goal. UserSim’s in-loop judge independently rates the interaction. If it flags an unhelpful answer while a no-match assertion passes, both observations should be retained and explained.',
        dreamjob: 'The application derives explicit criterion rows for disclosure, salary versus budget, sourced facts, delivered-response limits and execution continuity. Helix scores those saved rows. Local SDK scoring and the separately submitted durable job have different execution records; neither certifies the entire native model proposal.',
      }), [
        selected(scenarioId, {
          photography: '[[call:checks.evaluate|The photography assertions]] define what a pass means. [[cap:CAP-EVAL-01|The criterion results]] expose those rules’ expected and observed values. A published fee check cannot prove current seats, proximity, personal eligibility or all-in affordability.',
          boardgames: '[[call:checks.boardgames|The board-games assertions]] examine the actual saved reply and native search evidence. [[cap:CAP-EVAL-01|Their results]] should be read alongside any UserSim quality flags. The application’s catalogue-grounding requirement is deliberately different from a broad helpfulness rating.',
          dreamjob: '[[call:retail.criteria|evaluate_retail]] extracts the expected/observed values before [[cap:CAP-HX-01|Helix SDK scoring]]. [[cap:CAP-HX-03|The durable job receipt]] establishes that separate job’s status. A confirmed application-only clarification can sit between two native invocations; evaluation must not invent a third native result to make the continuity check pass.',
        }),
        'UserSim’s reply and stop judges operate during the conversation. Its optional post-loop evaluator/report pipeline is another workflow and is not invoked by this lesson. The evidence shown here is the selected application evaluation, with coverage attached to each criterion rather than inferred from a high total.',
      ], 'evaluate') : chapter('Evaluate behaviour',
      'A finished conversation can still give poor advice. Evaluation asks concrete questions about the delivered answer and compares it with what the learner requested and what the catalogue actually supported. Read those questions before reading the overall score.',
      selected(scenarioId, {
        photography: 'Did the advisor preserve Saturday and the spending limit, name a supported listing and explain what the price did not include? A low listed fee is useful information, but it does not settle an unknown materials cost.',
        boardgames: 'Did the advisor admit that the catalogue had no suitable match and keep the learner’s wish to play games intact? A negative search result can be a correct outcome. Recommending an unrelated activity just to produce an answer would fail the purpose of this test.',
        dreamjob: 'Did income stay private until disclosure, did the advisor wait for a training budget, and did the delivered answer preserve published facts and unknowns? We also distinguish the model’s proposal from the application’s public presentation, so good presentation is not mistaken for proof of model compliance.',
      }), [
        selected(scenarioId, {
          photography: 'The app reads the saved exchange and checks specific requirements. [[cap:CAP-EVAL-01|The saved checks]] explain each result and its limits. They do not ask another model to pronounce the answer universally correct.',
          boardgames: 'The app compares both answers with the intended request and the actual search evidence. [[cap:CAP-EVAL-01|The outcome of each check]] gives a reason you can assess. A separate simulated judge may have a different view of helpfulness; agreement is useful, but disagreement should not be hidden.',
          dreamjob: 'The app defines the questions and supplies their observed values to Helix for scoring. [[cap:CAP-HX-01|The saved evaluation]] shows the result; the separate job shows another way to execute the same defined checks. Using Helix does not make a narrow check broader than the rule we wrote.',
        }),
      ], 'evaluate');

    case 'routing': return detailed ? chapter('Optimize model routing',
      'A model strategy comparison changes how a request selects its provider while keeping the application task understandable. Separate admission limits, proxy dispatch, routing choice and provider completion: each boundary can succeed or fail independently.',
      selected(scenarioId, {
        photography: 'Photography uses a fixed advisor alias. LiteLLM resolves that alias to its configured provider; Switchyard does not choose among candidates. The saved model identity explains the baseline, not an optimization result.',
        boardgames: 'Both Hermes turns use the fixed route. This scenario is intended to examine context and honest no-match behaviour, so changing a routing policy would introduce an unnecessary comparison variable. It is not a controlled Deep Agents-versus-Hermes benchmark either.',
        dreamjob: 'Retail replays the same public inputs through separate fixed-candidate and Switchyard conditions using the MiniMax/Mistral inventory. Each condition has fresh memory and separately recorded usage; all conditions share the run’s call budget. Older Gemma/GLM failures and separate diagnostics remain distinct historical evidence, rather than being renamed as successful comparisons.',
      }), [
        selected(scenarioId, {
          photography: '[[cap:CAP-LLM-01|The loaded proxy settings]] define the fixed alias. [[cap:CAP-GW-02|The call records]] show the actual selected model and any unknown usage. With no alternate condition, no quality, latency or cost improvement can be inferred.',
          boardgames: '[[cap:CAP-LLM-01|The fixed-route configuration]] and [[cap:CAP-GW-02|observed model calls]] let you verify what answered. They do not contain a native Switchyard decision, because this preset intentionally has no routing experiment.',
          dreamjob: '[[cap:CAP-LLM-02|The condition’s loaded candidate configuration]] defines the deployments, while [[cap-run:CAP-SW-02|the comparison record]] retains actual decisions and corresponding outcomes. Switchyard operates within LiteLLM’s routing integration, not as a second conversational agent. A selected deployment still needs a completed response and evaluation.',
        }),
        selected(scenarioId, {
          photography: 'A useful later experiment would change only the model policy and replay the same inputs. Changing the learner, catalogue and model together would make any improvement difficult to attribute.',
          boardgames: 'Keeping the route fixed makes the no-match lesson easier to diagnose. A more powerful model cannot turn an absent catalogue listing into a supported option.',
          dreamjob: 'Compare fixed and routed runs over the same candidate pool before attributing a difference to policy. The fixed Nemotron baseline also changes inventory, so it answers a different question. Read actual selected models, failures, usage and criterion coverage; repeated selection of one candidate is a possible policy result, not proof that routing failed.',
        }),
      ], 'routing') : chapter('Optimize model routing',
      'An advisor can use one fixed model or choose among configured models. A routing experiment asks whether a different selection strategy helps this particular task. To learn from the result, keep the learner’s public inputs and course facts steady.',
      selected(scenarioId, {
        photography: 'This photography example keeps one model route. There is no optimization experiment to report: the purpose is to make the baseline answer and its course evidence easy to understand.',
        boardgames: 'This board-games example also keeps a fixed model. The key problem is missing catalogue coverage, which switching models cannot honestly repair. Keeping the route steady helps isolate the conversation behaviour we are examining.',
        dreamjob: 'Retail has separate runs for a fixed candidate and a model-selection policy using MiniMax and Mistral. They receive the same saved public inputs and start with fresh conversation state. The results below belong to those individual conditions, not to a blended demonstration of whatever happened to work.',
      }), [
        selected(scenarioId, {
          photography: 'The configured alias determines where advisor requests go. [[cap:CAP-GW-02|The saved model calls]] identify what actually answered. Without another comparable condition, there is no evidence that a different model strategy would be better.',
          boardgames: 'The proxy sends the fixed alias to its configured provider. [[cap:CAP-GW-02|The observed calls]] let you confirm that choice. A later routing test would need its own controlled runs and evaluations rather than comparing two different stories.',
          dreamjob: 'Switchyard makes a selection within the model proxy, then the selected provider still has to answer. [[cap-run:CAP-SW-02|The comparison outcomes]] distinguish that choice from a completed conversation. Prefer the strategy supported by the measured answers and available usage, without claiming savings when cost data is missing.',
        }),
      ], 'routing');

    case 'safeguards': return detailed ? chapter('Configure behavioural safeguards',
      'Behavioural safeguards decide whether a public input or proposed output may continue. They have a different job from tracing execution or denying filesystem/network access. Their placement and coverage must be established for the selected condition, rather than inferred from the presence of a policy file.',
      selected(scenarioId, {
        photography: 'Photography uses application instructions, the Fabric execution allowlist and the gateway’s provider-visible tool filter. Native Guardrails is intentionally unused. Those application restrictions should not be presented as native rail decisions.',
        boardgames: 'Native input/output Guardrails runs inside the standalone OpenShell workload. Legitimate board-game messages are separate from the negative credential-request demonstration. An honest catalogue no-match is normal advice, not a safety refusal.',
        dreamjob: 'Retail combines native behavioural checks with a separate application delivery policy for source facts and clarification. Baseline/comparison checks run inside OpenShell; the separate managed condition applies its checks at the host caller boundary. These are different placements, not interchangeable traces.',
      }), [
        selected(scenarioId, {
          photography: '[[cap:CAP-FAB-01|The Fabric settings]] define execution permissions, and [[cap:CAP-GW-01|gateway settings]] bound the advertised model tool surface. Review these restrictions as their own controls; no Guardrails configuration or native allow/reject receipt is expected in this preset.',
          boardgames: '[[cap:CAP-GR-01|The effective rail configuration]] connects YAML, Colang and custom deterministic actions. [[cap:CAP-GR-02|The native decisions]] show the boundary checked, executed action and whether processing continued. A loaded policy without a matching executed decision establishes configuration only.',
          dreamjob: '[[cap:CAP-GR-01|The rail settings]] define the native input/output checks, while [[cap:CAP-GR-02|their decisions]] establish what was checked. [[call:retail.response.clarify|The missing-constraint branch]] and source-based rendering are application logic. A successful delivered-response check does not certify every sentence in the preserved native proposal.',
        }),
        'The connected custom rules cover particular credential and assurance patterns; they are not a general safety classifier. Checks surround execution even though we explain them late in the journey. A useful policy change must name the new behaviour, update the relevant configuration and retain the resulting native decision.',
      ], 'safeguards') : chapter('Configure behavioural safeguards',
      'Decide which interactions the advisor should accept and which it should stop. A learner asking about a course should be able to continue; asking the app to reveal a provider credential should not. This is a behaviour rule, separate from whether a course happens to match.',
      selected(scenarioId, {
        photography: 'The photography advisor is restricted to read-only course tools and application instructions. This small preset does not use native Guardrails. Keeping that omission explicit helps you understand which controls are actually doing the work.',
        boardgames: 'The board-games conversation is a legitimate request, even if no suitable class exists. A separate forbidden credential request demonstrates blocking. Keeping those examples separate prevents a correct no-match from looking like a safety intervention.',
        dreamjob: 'Retail permits ordinary learning questions while checking inputs and delivered replies for the configured forbidden behaviour. The app also has a separate rule for asking missing budget/schedule questions and presenting returned facts; that presentation rule is not the same thing as Guardrails.',
      }), [
        selected(scenarioId, {
          photography: 'The app decides which tools the model sees and which actions can execute. [[cap:CAP-GW-01|The saved access settings]] make that choice inspectable. There is no native Guardrails verdict to inspect for this scenario.',
          boardgames: 'Guardrails runs the configured checks before the relevant message or reply continues. [[cap:CAP-GR-02|The saved decisions]] show the legitimate and negative examples separately. A few matching rules are useful, but do not establish protection against every possible unsafe request.',
          dreamjob: 'The behavioural checker allows or blocks according to the configured rules; the application separately confirms the answer it actually delivers. [[cap:CAP-GR-02|The recorded decisions]] show those checks. The managed demonstration places them outside its sandboxed agent, so review that condition’s boundary rather than assuming every run is arranged identically.',
        }),
      ], 'safeguards');

    case 'deploy': return detailed ? chapter('Deploy with controlled access',
      'Deployment needs an operational boundary as well as a runnable agent. OpenShell’s trusted supervisor creates a sandbox and enforces its policy around the application, selected harness and course tools. The simulator and credentialed model gateway remain outside that workload.',
      selected(scenarioId, {
        photography: 'Photography uses standalone OpenShell for the persistent Deep Agents application. Review the exact sandbox identity, loaded policy, allowed model/tool work and actual denial probes. A policy declaration alone does not establish that the running workload enforced it.',
        boardgames: 'Board games contains the persistent Hermes runtime and read-only course MCP in standalone OpenShell. The two-turn conversation belongs to that owned runtime. Cleanup evidence must refer to its exact resources, rather than deleting any old-looking container on the host.',
        dreamjob: 'Retail has standalone baseline/comparison execution and a separate Helix-managed deployment. Helix registers the reusable package and opens a fresh session with selected public context. It does not resume local private memory or create a fourth turn in the UserSim conversation.',
      }), [
        selected(scenarioId, {
          photography: 'Compare [[cap:CAP-OS-01|the requested operational policy]] with [[cap:CAP-OS-02|the effective policy and probes]]. A permitted course/model exchange and a policy-specific denial establish different parts of the boundary. An unrelated network failure cannot stand in for a demonstrated policy denial.',
          boardgames: '[[cap:CAP-OS-02|The runtime and enforcement receipts]] connect the running policy, sandbox identity, denied operations and cleanup. Native tool execution is permitted through the bounded bridge; host credentials do not become agent tools. The trusted supervisor remains outside the contained workload.',
          dreamjob: '[[cap:CAP-PLAT-04|Registration and deployment records]] establish managed resources, and [[cap:CAP-PLAT-05|session/invocation/cleanup records]] establish their lifecycle. [[cap:CAP-OS-03|The managed enforcement evidence]] belongs to that separate condition. Local Helix scoring is not proof that a managed deployment happened.',
        }),
        'These controls were applied before and during the conversation, despite being explained in the final lesson. Preserve the distinction between intended policy, loaded policy, observed enforcement and owner-confirmed cleanup. Resource absence after cleanup is an execution outcome, not something the inspector should create by closing a panel.',
      ], 'deploy') : chapter('Deploy with controlled access',
      'An advisor should run with only the access needed for its job. The sandbox contains the application, its agent harness and the course tools, while the trusted supervisor manages that boundary. The test learner and the gateway holding provider credentials stay outside it.',
      selected(scenarioId, {
        photography: 'Photography runs in a standalone OpenShell sandbox. It can perform the permitted model and course operations, while the demonstrated denied operations test whether the surrounding access policy is being enforced.',
        boardgames: 'Hermes and the course tools stay inside one standalone sandbox across the board-game conversation. The app can preserve conversation context without granting unrelated host access. Finishing the run also requires cleaning up its own resources.',
        dreamjob: 'Retail additionally demonstrates managed deployment through Helix. That managed example starts a new session using selected public constraints. It is a separate execution, rather than a continuation that secretly carries the original person’s private simulator context.',
      }), [
        selected(scenarioId, {
          photography: 'The app requests an access policy, starts the sandbox and tests permitted and forbidden operations. [[cap:CAP-OS-02|The recorded boundary checks and cleanup]] show the observed result. A connection that simply failed for an unknown reason would not demonstrate protection.',
          boardgames: 'OpenShell applies the operational policy while the advisor runs. [[cap:CAP-OS-02|The loaded policy, denial checks and cleanup]] let you examine what the app could access and whether its workload was removed afterward. These controls limit access; they do not make missing catalogue information appear.',
          dreamjob: 'Helix manages the application package, deployment and session; OpenShell supplies the execution boundary used by that condition. [[cap:CAP-PLAT-05|The managed session record]] and [[cap:CAP-OS-03|its access checks]] show different parts of that process. The standalone conversation keeps its own evidence.',
        }),
        'The boundary was already active during the earlier conversation. We explain it here so you can connect a working answer with the permissions under which it was produced.',
      ], 'deploy');
  }
  throw new Error('Unknown teaching lesson');
}
