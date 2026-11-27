import type {LessonId} from '../lessonArchitecture';
import type {TeachingPage} from './types';

type Story = 'photography' | 'boardgames' | 'dreamjob';
type Versions = Record<Story, string>;

function selected(scenarioId: string, versions: Versions): string {
  if (!Object.hasOwn(versions, scenarioId)) throw new Error('Unknown teaching scenario');
  return versions[scenarioId as Story];
}

function chapter(title: string, intro: string, scenario: string, mechanism: string[],
  observation: LessonId): TeachingPage {
  return {title, intro, sections: [
    {heading: 'In this scenario', paragraphs: [scenario], observation},
    {heading: 'How it works', paragraphs: mechanism},
  ]};
}

/** User-approved writing reference: keep these bodies and existing lesson titles. */
function photographySimple(stage: LessonId): TeachingPage {
  const pages: Record<LessonId, TeachingPage> = {
    persona: chapter('Choose a test persona',
      'We will test a citizen advisor that helps people find learning opportunities. To begin, we need someone to ask it a question. UserSim will play that person during the test.',
      'This recording uses Caroline, a synthetic profile from the Singapore Extended persona dataset. Her structured name is Min Hoon Lim, and Caroline is her preferred English name. Both names belong to the same profile. She is described as a 24-year-old university student living in Bukit Timah.',
      ['The application keeps a reference to the selected original profile so we can check which person was used. At this point, we have chosen our test participant. The conversation has not started.'], 'persona'),
    situation: chapter('Create a situation',
      'A persona tells us who the simulated learner is. We also need to decide what she wants to do in this test.',
      'For this scenario, we supply a specific task: find a beginner photography class on Saturday for less than S$50. These requirements come from the scenario we authored. They are separate from Caroline’s original profile.',
      ['UserSim will use the profile and this task to write the learner’s message. This lets us test how the advisor handles a clear request while keeping track of which information came from the profile and which information we supplied. This scenario does not use Data Designer to generate additional fields.'], 'situation'),
    build: chapter('Build and connect the agent',
      'The advisor needs instructions, a language model and access to course information. The instructions explain its job. The model decides how to respond, and the course tools let it retrieve facts from the saved catalogue.',
      'Here, Deep Agents manages the conversation between the model and its tools. Fabric provides the application’s interface for configuring, starting and calling that agent. We prepare one runtime and keep it available throughout the test.',
      ['The advisor can search for courses, retrieve course details and compare courses. These tools read catalogue information; they cannot book a class or make a payment. Completing this setup makes the advisor ready to receive Caroline’s question.'], 'build'),
    run: chapter('Run the application',
      'UserSim now writes Caroline’s opening message:',
      '“Hi, I\'m looking for a beginner photography class that meets on Saturdays and costs under S$50. Do you have any recommendations?”',
      ['The application sends this public message to the advisor. The advisor searches the catalogue and returns a recommendation for Photography and Photo Enhancement with AI (AI30) at Toa Payoh West CC.',
        'In the saved catalogue, the class runs on Saturday and has a published fee of S$10. The reply also explains that materials may cost extra and that the learner should confirm the total cost.',
        'This recording contains one learner message and one delivered advisor reply. Producing that reply involved two model requests and one course search.'], 'run'),
    investigate: chapter('Investigate execution',
      'Suppose we want to check where the recommendation came from. We can follow the recorded execution: the model requests a course search, the tool returns catalogue information, and the model uses that result to write its reply.',
      'Relay records activity inside the agent, including the captured model and tool operations. Open the course-search record to inspect the actual arguments and returned facts. This is where we can check whether the recommendation has evidence behind it.',
      ['The application also records model usage for the whole test. That includes generating Caroline’s message and running UserSim’s checks. The advisor’s two model requests have global IDs 3 and 4 because other requests happened first. They are the advisor’s first and second requests, not missing conversation turns.'], 'investigate'),
    evaluate: chapter('Evaluate behaviour',
      'Now we can compare the delivered answer with the requirements of this test.',
      'The lab’s developers wrote nine checks for this scenario. They cover whether an answer was saved, whether the original profile was preserved, whether the request contains the intended constraints, and whether selected course details agree with the saved catalogue and tool evidence.',
      ['All nine checks passed. These checks run as application code and make no additional model requests.',
        'Their coverage is specific. For example, checking a published fee does not establish the total checkout cost, and checking a course link does not confirm available seats or travel distance. UserSim also assessed the reply during the conversation using its own answer-quality judge. That is a separate assessment, which we will identify by name when displaying its result.'], 'evaluate'),
    routing: chapter('Optimize model routing',
      'This recording uses one fixed model for the advisor: Nemotron 3.5 Lightning. Both advisor model requests go through LiteLLM to that configured model.',
      'A fixed route gives us a straightforward starting point: we know which model was asked to produce the answer. Switchyard is not used in this scenario, so there is no automatic model-selection decision to inspect.',
      ['To study a different route later, we would keep the task and course information steady, change the model-selection condition, and compare the resulting answers and resource usage. This recording establishes the fixed-route example.'], 'routing'),
    safeguards: chapter('Configure behavioural safeguards',
      'The advisor receives instructions to use course evidence and explain uncertainty. Its permitted tools are also restricted to the course catalogue. These controls work together: instructions guide the answer, while the tool restrictions limit the operations available to the agent.',
      'Three course tools are available in this scenario. The execution record shows that the advisor used the search tool for this reply. Making a tool available and actually calling it are different events.',
      ['This photography scenario does not use NeMo Guardrails. The board-game scenario introduces that component and shows the checks it performs on messages entering and leaving the application.'], 'safeguards'),
    deploy: chapter('Deploy with controlled access',
      'The advisor ran inside an OpenShell sandbox. That sandbox contained the application, Deep Agents and the course tools. UserSim and the gateway holding the model-provider credentials ran outside it.',
      'The sandbox policy permits the file and network access needed for the task. To check enforcement, the test also deliberately tried to read a file outside the permitted locations and connect to an unlisted network address. Both attempts received a permission-denied result. These were separate boundary tests, not actions requested by Caroline.',
      ['The policy view should show the relevant rules alongside those observed results. The recording also confirms that permitted model and tool work completed and that the sandbox was removed afterward.',
        'This boundary was already active when the conversation ran. We explain it here so you can connect the saved answer with the environment in which it was produced. Photography uses standalone OpenShell; the retail scenario separately demonstrates Helix-managed deployment.'], 'deploy'),
  };
  return pages[stage];
}

/** Lessons explain cooperation. Library and operation pages own API tutorials. */
export function lessonPage(scenarioId: string, stageId: LessonId, detailed: boolean): TeachingPage {
  if (scenarioId === 'photography' && !detailed) return photographySimple(stageId);
  switch (stageId) {
    case 'persona': return detailed ? chapter('Choose a test persona',
      'First choose the dataset record that UserSim will use to portray the learner. Our application reads and locks an existing original; it does not ask a model to invent one. Keeping that record unchanged lets you test a different advisor configuration with the same participant.',
      selected(scenarioId, {
        photography: 'The profile below is the original selected for the photography recording. Read its background before deciding what this one test can represent. An interest or age field is context for the simulator; it is not evidence that every similar person wants a photography class.',
        boardgames: 'This recording locks the same original profile used by the other demonstrations: Min Hoon Lim, whose preferred English name is Caroline. The board-game situation is a separate input. We use the profile as background, then test whether the advisor follows the learner’s publicly stated wish to play games.',
        dreamjob: 'Retail also begins with Caroline’s original Singapore Extended profile. The record’s structured name is Min Hoon Lim. Brand and salary hypotheses are added later as separate test inputs, so you can distinguish the original background from the situation we designed.',
      }), [
        'The application reads the chosen distribution, retains the selected original and records its revision and content identity. The guide resolves that identity against the installed source before displaying the person. [[cap:CAP-PER-01|The selection receipt]] identifies the input; it establishes neither population coverage nor unrecorded sampling decisions.',
        'HF profile-only data and NGC Singapore Extended have different fields. Use the distribution named by this recording rather than assuming OCEAN traits exist in both. If that source cannot be matched, an unavailable profile is the correct outcome; sampling a replacement would create a different test.',
      ], 'persona') : chapter('Choose a test persona',
      'We will test the citizen application by giving it a learner to help. UserSim will play that learner using an existing synthetic profile. We begin by choosing the person, before deciding what she should ask.',
      selected(scenarioId, {
        photography: 'Meet the person selected for the photography test below. This person will ask for help with a first class; the request itself comes next. Read the profile as one example of a learner, rather than a description of all Singapore residents.',
        boardgames: 'The selected profile is Caroline, whose structured name is Min Hoon Lim. This recording will ask her to seek help learning to play board games. Keeping the person fixed helps us follow the same learner’s goal across both exchanges.',
        dreamjob: 'The selected profile is Caroline, whose structured name is Min Hoon Lim. We will use that original background for a retail-learning test. Later we add hypothetical salary and brand details separately, so it remains clear which information the dataset supplied.',
      }), [
        'The application keeps a reference to the selected original profile. [[cap:CAP-PER-01|That profile reference]] lets another developer find the same starting point. UserSim has not generated a message yet; this step only chooses the participant for the conversation.',
        'One person makes a useful repeatable example, but cannot establish that the advisor works well for everyone. A later test could deliberately choose a different background while keeping the situation and application unchanged.',
      ], 'persona');

    case 'situation': return detailed ? chapter('Create a situation',
      'Next prepare the task that this learner will attempt. The application combines the locked original with a goal, any constraints and the custom probe settings. UserSim will use those prepared inputs to generate messages when the conversation starts.',
      selected(scenarioId, {
        photography: 'The authored situation supplies beginner photography, Saturday availability and a budget under S$50 before funding. UserSim may phrase that request in the selected person’s voice. It is not asked to discover or invent those constraints, and no separate Designer enrichment job is used.',
        boardgames: 'The authored probe preserves the goal of playing board games across two public turns. The later distinction from designing digital games tests whether the advisor keeps the original intent. There is no Designer overlay to manufacture a more convenient catalogue match.',
        dreamjob: 'Designer generates one separate retail overlay from the original seed. It contains brand interests, a fixed hypothetical salary band and a practical learning task. Our authored protocol determines disclosure: salary becomes public in turn 2; the S$3,000 training budget and weekends become public in turn 3. The salary band does not supply the training budget.',
      }), [
        selected(scenarioId, {
          photography: 'The [[call:situation.authored|scenario preset]] and [[call:usersim.prepare|preparation code]] create the effective person/behaviour/probe inputs. [[cap:CAP-US-01|The resolved UserSim inputs]] are the useful configuration boundary: compare what the simulator received, while keeping that private context out of the advisor request.',
          boardgames: 'The [[call:usersim.probe|custom learning-advisor probe]] supplies the test’s instructions while inheriting the UserSim conversation engine. Its role is to specify this task, rather than reimplement generation, turn checks and stopping. [[file:usersim-setup.json|The saved probe settings]] show the configured test rather than an unrelated built-in safety or sovereign-AI probe.',
          dreamjob: 'The [[cap:CAP-DD-01|Designer seed and closed schema]] request only the permitted derived fields. Generation and application validation are separate boundaries: [[cap:CAP-DD-04|the selected overlay and lineage]] identify what was retained and its original parent. The simulator receives that overlay with disclosure instructions; the advisor receives only later public messages.',
        }),
        'The application chooses the situation and probe options, while UserSim interprets the original behaviour fields. [[cap:CAP-US-02|The preparation record]] shows the resulting configuration. Keeping those inputs separate helps a developer and behavioural scientist vary one part of a test at a time. Here the prescribed follow-ups are authored test rules; optional population-level disclosure and simulation-health diagnostics were not measured.',
      ], 'situation') : chapter('Create a situation',
      'A persona tells us who the simulated learner is. We also need to decide what she wants to do in this test. The situation gives her a task and the information she should share with the advisor.',
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
      'Now connect the advisor’s instructions, chosen harness, model endpoint and course tools. The application builds a typed FabricConfig and uses Fabric to check and start the selected runtime. Once this setup succeeds, the advisor is ready for a public learner message.',
      selected(scenarioId, {
        photography: 'Photography selects the Deep Agents adapter and a fixed model route. The tool surface contains course search, details and comparison. This intentionally small setup lets you review the common Fabric lifecycle without Designer, routing optimization or a managed deployment.',
        boardgames: 'Board games selects Hermes through Fabric. The adapter and Hermes settings differ from photography, but the application still plans, starts and invokes a Fabric runtime. Selecting another harness should not require a second business-logic implementation of the advisor.',
        dreamjob: 'Retail starts a persistent Deep Agents runtime for the baseline and fresh runtimes for comparison conditions. The application also enables its source-based public response boundary. A native model proposal and the application’s delivered answer therefore have separate responsibilities and evidence.',
      }), [
        '[[call:fabric.config|build_config]] constructs the installed SDK’s actual typed configuration. [[cap:CAP-FAB-01|The recorded settings]] express that decision. Fabric planning and Doctor preflight then check resolution and readiness before startup; [[cap:CAP-FAB-03|their reports]] are preparation evidence, not proof of an answered request.',
        'Runtime startup connects the adapter, instructions and MCP tool schemas, while Relay instrumentation attaches to the harness. [[cap:CAP-FAB-04|The lifecycle record]] identifies what started. Model access remains host-side through the gateway and LiteLLM; the application, harness and course tools execute inside OpenShell. Discovering a tool means it is available, not that the agent has called it.',
      ], 'build') : chapter('Build and connect the agent',
      'The advisor needs instructions, a model and course information. The instructions explain its job, and the course tools let it retrieve saved facts. We connect these parts through the selected agent harness, using Fabric to configure and start it.',
      selected(scenarioId, {
        photography: 'For photography we connect Deep Agents to the fixed model and the course catalogue. The advisor can look up a listing and explain unknown costs, but it has no booking or payment tool. Its available actions reflect the job we want it to do.',
        boardgames: 'For board games we connect Hermes to the same kind of course service. Fabric remains the application’s entry point. This shows where a harness choice changes the setup while leaving the citizen-facing purpose and read-only tools understandable.',
        dreamjob: 'For retail learning we connect Deep Agents and the course tools, then add an application rule for presenting verified returned facts. We also prepare separate model-comparison runs. Their outcomes will be reviewed independently instead of being mixed into the baseline conversation.',
      }), [
        'The app builds a configuration, asks Fabric to check it and starts one conversation runtime. [[cap:CAP-FAB-03|The preparation reports]] help distinguish a valid setup from a runtime that actually started. A missing adapter or broken tool connection should be visible here, before interpreting any answer.',
        'We use a shared Fabric interface so the application does not need separate execution code for every harness. The tradeoff is another configuration boundary to understand. The next lesson follows a real public message through that boundary; this one establishes what the advisor is ready to use.',
      ], 'build');

    case 'run': return detailed ? chapter('Run the application',
      'The conversation now begins. UserSim generates and checks the learner’s message, then sends it to our application. When agent execution is needed, Fabric invokes the selected harness, which may make several model and tool calls before returning one public reply.',
      selected(scenarioId, {
        photography: 'The single public request goes from UserSim through the application into a Fabric RunRequest. Deep Agents can query the course MCP server, consume its returned facts and produce a normalized result. The recorded public exchange below is the outcome to interpret, rather than the authored story text.',
        boardgames: 'Two public exchanges use the same Hermes runtime. UserSim generates the follow-up after receiving the first reply, so the advisor must preserve the original playing goal across turns. A successful empty search is legitimate evidence; inventing an attractive substitute would change the task.',
        dreamjob: 'Retail keeps three public turns but uses native agent execution for turns 1 and 3. At turn 2, salary has been disclosed without a training budget or study days. Application code fills a clarification template asking for those constraints. It makes no advisor model or tool call for that reply, which is not a third Fabric result.',
      }), [
        selected(scenarioId, {
          photography: 'The public message enters [[call:fabric.invoke|runtime.invoke]] and its [[cap:CAP-FAB-05|captured request]]. The adapter runs the configured harness and returns [[cap:CAP-FAB-06|a normalized RunResult]]. UserSim then judges the delivered response and finalizes its trajectory; it does not see the advisor’s private internal reasoning.',
          boardgames: 'The common [[call:fabric.invoke|Fabric invocation call]] remains the application boundary even though Hermes owns the internal loop. Compare the selected turn’s [[cap:CAP-FAB-05|request]] with [[cap:CAP-FAB-06|its result]], then read how UserSim continues or stops. Its public-turn limit is separate from the harness’s internal execution bounds.',
          dreamjob: '[[call:retail.response.clarify|The pre-agent clarification branch]] checks public decision constraints first. Native turns retain their original proposals and Fabric identities; [[call:retail.response.render|the application response boundary]] separately formats returned course facts. [[cap:CAP-FAB-07|The delivery decisions]] distinguish the public answer from the model proposal, and output safeguards must permit delivery before it is acknowledged.',
        }),
        '[[cap:CAP-US-04|The UserSim activation and trajectory records]] show what its engine generated and retained. Follow-up context is based on replies actually delivered. In-loop helpfulness/stop judgments belong to that interaction; the later saved-response evaluation asks different questions. A valid answer does not by itself establish that every engine judgment agreed.',
      ], 'run') : chapter('Run the application',
      'UserSim now writes the learner’s message and sends it to the application. The advisor can look up course information before answering. UserSim receives that delivered answer before writing the next message, so the follow-up can react to what was actually said.',
      selected(scenarioId, {
        photography: 'The learner asks for a Saturday photography class within the stated budget. Read the lookup and answer together: the listed price can be known while extra materials remain unconfirmed. The advisor should preserve that distinction when explaining an option.',
        boardgames: 'The learner first asks to play board games, then asks about a different kind of activity. The useful outcome may be an honest no-match. The second answer should help the learner understand the difference instead of quietly replacing their original goal.',
        dreamjob: 'The learner asks about a programme, discloses income, then states a spending limit and weekend availability. After income alone, the application asks for the missing budget and study days without calling the agent again. It resumes the agent only when the learner supplies those constraints.',
      }), [
        selected(scenarioId, {
          photography: 'UserSim plays the learner. The citizen application passes the public request to the advisor and returns its answer. [[cap:CAP-US-04|The recorded conversation]] contains what was actually said, while the tool records show which facts the advisor obtained.',
          boardgames: 'UserSim receives the first reply before generating the next learner message. The advisor keeps its conversation context, so it can relate the follow-up to the original request. [[cap:CAP-US-04|The saved interaction]] lets you inspect that continuity rather than assuming it from the two-turn setting.',
          dreamjob: 'The clarification comes from a template in ordinary application code. No language model writes that reply, so there is no hidden direct model call or missing agent execution. For the other turns, the application presents returned course facts and explicit unknowns; [[cap:CAP-FAB-07|the response record]] keeps that presentation decision visible.',
        }),
      ], 'run');

    case 'investigate': return detailed ? chapter('Investigate execution',
      'Suppose a recommendation surprises you. Select its public turn, find the corresponding Fabric invocation if one ran, and inspect the recorded model/tool work. This lets you compare the request, returned course facts and delivered answer instead of guessing how the answer was produced.',
      selected(scenarioId, {
        photography: 'Follow the actual course request and returned listing behind the photography answer. Compare the public Saturday/budget constraints with the tool arguments, then check which fee and uncertainty fields were available when the reply was produced.',
        boardgames: 'Distinguish a completed search returning no suitable board-game class from a failed or malformed tool response. For the follow-up, inspect whether Hermes made another lookup or reused public context. Either is possible; the selected turn’s native records determine what can be claimed.',
        dreamjob: 'Retail requires two views of the same execution: native proposals and application-delivered replies. Turn 2 has an application clarification receipt rather than a Fabric/model subtree. Its reference to an earlier course is reuse of previously returned facts, not evidence of a new search.',
      }), [
        'Expand the observed agent scope to follow its model and tool children. Relay’s [[cap:CAP-REL-02|saved events]] provide their IDs, parent relationships, timing and status. Then open [[cap:CAP-MCP-03|the matching tool result]] to check its arguments and returned facts. The trace viewer and local Phoenix import present these historical records; they do not recreate missing events or turn run-wide records into a proven per-turn sequence.',
        'Use [[cap:CAP-GW-02|model usage accounting]] for a different question: how much model work did the test require? It includes learner generation and UserSim checks as well as advisor requests. Global call numbers can therefore have gaps when filtered to one role. These call IDs are not automatically Relay span IDs, so an unrecorded relationship must remain unknown.',
      ], 'investigate') : chapter('Investigate execution',
      'Let us check where the answer came from. Start with the learner’s question, then look at the course information returned during that turn. We can compare those facts with the reply to understand why the advisor made its recommendation.',
      selected(scenarioId, {
        photography: 'Look for the course facts behind the photography recommendation. A published class fee can support the quoted amount, while an unknown materials fee explains why the advisor should ask the learner to confirm the full cost.',
        boardgames: 'Look closely at the no-match. A tool that ran successfully and found no suitable class supports an honest explanation. A tool that failed supports only an admission that the lookup failed; those are different reasons for not recommending a course.',
        dreamjob: 'Compare the sourced programme facts with the public answer. On the salary-only turn, the application should ask for a budget and schedule; no fresh model or course lookup is needed. Later advice can use earlier public context without pretending a new lookup occurred.',
      }), [
        'The selected records below connect the reply to the actions we can actually observe. [[cap:CAP-MCP-03|The saved course-tool evidence]] is where you can open the returned facts yourself. If the recording cannot connect an action to this turn, the guide should tell you that rather than attach the whole run to the answer.',
        'Relay records what happened inside the agent execution. A separate application record counts model work for the advisor, simulated learner and judges. Keeping those sources distinct helps diagnose a problem without mistaking the learner’s work for the advisor’s work.',
      ], 'investigate');

    case 'evaluate': return detailed ? chapter('Evaluate behaviour',
      'We can now test the saved answer against the application requirements. For each criterion, the lab computes an observed value from the conversation and evidence, then compares it with an expected value. This checks a defined requirement without generating another conversation.',
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
        'Read the criteria by purpose: functional checks cover turns and intent; grounding checks compare selected facts with the catalogue; privacy/safety checks cover disclosure and particular assurance patterns; runtime checks establish actual execution. Token and latency records are measurements, with no performance pass target defined by these criteria. UserSim’s in-loop answer-quality judge asks whether the reply addresses the request coherently, so its judgment can differ. The optional post-loop UserSim evaluator/report workflow was not run.',
      ], 'evaluate') : chapter('Evaluate behaviour',
      'Now compare the answer with what we wanted the test to achieve. The lab’s developers wrote checks for these requirements. Reading each check helps us understand what a passing score means and which parts of answer quality still need review.',
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
      'To study model routing, keep the task and course facts steady while changing how advisor requests select a model. A fixed alias names one deployment; a routed alias lets Switchyard choose from a candidate group. Compare completed answers and measured resources for the controlled conditions.',
      selected(scenarioId, {
        photography: 'Photography uses a fixed advisor alias. LiteLLM resolves that alias to its configured provider; Switchyard does not choose among candidates. The saved model identity explains the baseline, not an optimization result.',
        boardgames: 'Both Hermes turns use the fixed route. This scenario is intended to examine context and honest no-match behaviour, so changing a routing policy would introduce an unnecessary comparison variable. It is not a controlled Deep Agents-versus-Hermes benchmark either.',
        dreamjob: 'Retail replays the same public inputs with fresh memory for each condition. fixed-candidate keeps MiniMax for the advisor; switchyard chooses within MiniMax/Mistral; capable-access keeps Mistral for the same advisor/harness/tool path. available-fixed and available-switchyard are a separate diagnostic pair over another inventory. Each keeps its own settings, result and usage within the run’s shared call budget.',
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
      'An advisor can send every request to one model, or let a routing policy choose among models. We can compare those approaches using the same learner messages and course information. The question is whether a different choice improves the answer or the resources needed to produce it.',
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
      'Before passing a public message to the advisor, the application checks its selected input rules. Before delivery, it checks the output rules. These behavioural decisions differ from Relay’s execution recording and OpenShell’s access policy, so each needs its own configuration and result.',
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
      'Some requests should continue and others should be stopped. Asking for a class is a normal learning question, even when no class matches. Asking the application to reveal its provider credential is different. Behavioural safeguards apply the rules we chose for those messages.',
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
      'The application also needs a defined place to run and an access policy. OpenShell’s supervisor creates a sandbox for the advisor, selected harness and course tools. The test learner and credentialed model gateway stay outside, communicating only through the intended application connections.',
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
      'Run the advisor with the access its task needs. OpenShell places the application, harness and course tools in a sandbox. UserSim stays outside as the test learner, and a separate gateway holds the model-provider credentials.',
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
