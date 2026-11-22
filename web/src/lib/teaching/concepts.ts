import type {TeachingPage} from './types';

type Story = 'photography' | 'boardgames' | 'dreamjob';

function choose(scenarioId: string, values: Record<Story, string>): string {
  if (!Object.hasOwn(values, scenarioId)) throw new Error('Unknown teaching scenario');
  return values[scenarioId as Story];
}

function page(title: string, intro: string, paragraphs: string[], flow?: string[], rows?: [string, string][]): TeachingPage {
  return {title, intro, sections: [{heading: 'How it works', paragraphs,
    ...(flow ? {flow} : {}), ...(rows ? {rows} : {})}]};
}

/** Conceptual responsibilities and actions have their own prose and identities.
 * Their many-to-many technical bindings are used by the diagram, not as pages.
 */
export function simplePage(scenarioId: string, blockId: string, actionId?: string): TeachingPage {
  const retail = scenarioId === 'dreamjob';
  const boardgames = scenarioId === 'boardgames';
  if (!['photography', 'boardgames', 'dreamjob'].includes(scenarioId)) throw new Error('Unknown teaching scenario');
  if (actionId !== undefined && actionId !== '') {
    if (!actionId.startsWith(blockId + '.')) throw new Error('Action does not belong to this concept');
    return actionPage(scenarioId, blockId, actionId.slice(blockId.length + 1));
  }
  switch (blockId) {
    case 'person': return page('Test person',
      'This is the person-shaped input to the test, not a customer account or a real resident. The profile gives the simulator a consistent background from which to speak. Its value is that you can examine whom you tested with instead of treating one anonymous prompt as representative of everyone.', [
        'Nemotron Personas supplies the original data; application code selects and preserves an original. Those are different responsibilities: the dataset describes a synthetic person, while the app decides which person participates in this test. A saved identity lets you return to the same input after changing the advisor.',
        choose(scenarioId, {
          photography: 'Here the person will participate in the photography story. Keep the person fixed while examining whether a different class request or advisor setup changes the outcome. Choosing the person does not yet send a message to the advisor.',
          boardgames: 'Here the person will take part in a board-game conversation. Their background helps the simulator portray a learner, but the public goal remains something the learner must actually say. The advisor does not receive the whole profile in advance.',
          dreamjob: 'Here the person is the original input to a retail-learning test. Later hypothetical details are held separately, so the original cannot quietly acquire a salary or preference just because an experiment needed one.',
        }),
      ]);
    case 'situation-block': return page('Test situation',
      'A situation turns background into a task we can test. It says what help the learner will seek, what constraints apply and which details they will reveal later. This block owns those test choices; it does not claim the person’s profile already contained the request.', [
        choose(scenarioId, {
          photography: 'The application supplies a deliberately small photography situation. Authored constraints make the test easy to reproduce: the developer knows what a satisfactory answer must respect without asking a generator to choose a convenient budget or date.',
          boardgames: 'The application supplies a playing-related goal and a later comparison with game design. This tests a meaningful failure mode: an advisor can sound helpful while changing the kind of activity the learner wanted.',
          dreamjob: 'The application combines an authored learning goal with a separately stored Designer overlay. Designer adds hypothetical details under a limited schema; the app validates and selects them. Disclosure rules still come from the test protocol, rather than being inferred from the generated salary.',
        }),
        'The prepared situation is handed to the simulated learner, not exposed wholesale to the advisor. This creates a useful information boundary: the learner can possess private context while the advisor must work from what has actually been said.',
      ]);
    case 'learner': return page('Simulated learner',
      'The simulated learner is the test participant who speaks to the advisor and reacts to its replies. UserSim combines the selected person, interpreted behaviour and a task-specific probe. The probe describes this test; the inherited engine handles the conversation around it.', [
        'The learner and advisor are different actors. UserSim generates learner messages and runs its configured checks and judges; the advisor receives the public message and handles course advice. A judge can assess that reply without becoming another citizen-facing participant.',
        choose(scenarioId, {
          photography: 'For this short example, UserSim phrases the supplied photography task and records the exchange. Its persona context shapes the test input; it does not become extra knowledge supplied to the course advisor.',
          boardgames: 'Here UserSim must react to the first answer before asking its intended follow-up. The custom probe preserves the playing goal while the inherited engine still checks that the generated message stays in the learner’s role.',
          dreamjob: 'Here UserSim controls the learner side of staged disclosure. It knows the hypothetical salary before the advisor does, but must reveal it only at the intended public turn. This authored protocol is different from assuming that random incremental disclosure happened.',
        }),
      ], ['Person, behaviour and task', 'Learner message and turn checks', 'Advisor reply', 'Judge, continue or stop']);
    case 'advisor': return page('Citizen advisor',
      'The citizen advisor turns a public learning request into advice. The application decides which information the agent may receive, which course tools it may use and which responses can reach the learner. Fabric connects the selected agent, while the application keeps responsibility for these rules.', [
        `The application owns what the advisor may do and what it delivers. Fabric connects that application to ${boardgames ? 'Hermes' : 'Deep Agents'} through a consistent runtime interface. The harness manages the model/tool loop; the course tools supply published facts. These cooperating parts do not all make the same decision.`,
        retail
          ? 'Retail makes this distinction visible: the app can ask for a missing budget and schedule before invoking the harness. When native execution is needed, it preserves the model’s proposal and separately presents verified returned facts. That is a deliberate application design, not evidence that the model itself always produced compliant prose.'
          : 'The application uses read-only course operations so advice cannot accidentally turn into a booking, purchase or account change. A different app might need those actions, but it would need explicit rules and additional evidence before granting them.',
      ], ['Public request', 'Application decision', 'Selected agent and course tools when needed', 'Delivered advice']);
    case 'courses': return page('Course information',
      'The advisor needs a reliable place to look up course facts. This responsibility combines a read-only tool interface with a frozen catalogue. The tool gives the agent a defined way to ask questions; the catalogue determines what information it can truthfully return.', [
        'MCP is the connection and tool-description protocol, not the course database. Our application implements search, details and comparison over dated listings. The response can contain supported facts, unknown fields, no suitable matches or a structured error; those outcomes mean different things for the advice.',
        choose(scenarioId, {
          photography: 'A photography listing can establish the published class price and day without establishing the cost of materials. Keeping that unknown visible prevents a neat-looking recommendation from overstating what the source supports.',
          boardgames: 'This story is useful precisely because the known listings may not cover the requested activity. An honest empty search tells the advisor about catalogue coverage. It does not justify inventing a class or treating game design as the same activity.',
          dreamjob: 'Retail advice uses both programme facts and explicit public constraints. A published full fee, a personal spending limit and funding eligibility are three separate values. The catalogue can supply the first, the learner states the second, and the app must not invent the third.',
        }),
      ]);
    case 'models': return page('Model access',
      'The advisor and simulated learner need access to language models, but they should not hold provider credentials or make unbounded calls. This block combines the application’s gateway, the model proxy and any selected routing policy. It is an access path, rather than another agent in the conversation.', [
        'The gateway admits and accounts for work under application limits. LiteLLM maps an application-facing model name to a provider deployment. When routing is enabled, Switchyard chooses within the configured candidate group. A successful selection still needs a successful provider response.',
        retail
          ? 'The retail comparisons make those responsibilities visible with a fixed candidate and a MiniMax/Mistral routing policy. Judge the conditions by their actual responses and measured usage. A routing choice on its own says nothing about whether the resulting course advice was suitable.'
          : 'This scenario intentionally fixes the model route. Keeping one variable steady makes its application behaviour easier to study. The recorded provider identity explains what ran; it is not evidence that model optimization was attempted.',
      ], ['Application call limits', 'Model alias and provider connection', retail ? 'Configured model selection' : 'Fixed deployment', 'Response or explicit failure']);
    case 'evidence': return page('Execution records and checks',
      'Understanding an answer needs both a record of what happened and a judgment about whether it met the requirement. This responsibility combines native traces, saved application evidence and the appropriate evaluation. A trace and a score answer different questions.', [
        'Relay observes the agent’s model and tool activity. The app also retains public messages, configuration and model-call accounting, then packages the reviewed evidence for inspection. None of those records causes the answer; they let you examine the execution after it happened.',
        retail
          ? 'For retail, application-defined criteria are scored with Helix and a separate durable evaluation job. The criteria still have the scope of the rules we wrote. Native model proposals, application-delivered answers and the application-only clarification remain distinguishable, so a good score cannot hide which part produced the response.'
          : 'Here the application checks saved replies against the request, course facts and observed actions. UserSim’s own in-conversation judgments are separate observations. A helpful-looking answer can fail grounding, and a well-grounded no-match can still disappoint a helpfulness judge.',
      ], ['Observed events and public output', 'Scenario-owned saved evidence', 'Explicit criteria', 'Result with coverage']);
    case 'guardrails': return page('Behavioural safeguards',
      'These checks decide whether a public request or reply should continue under the application’s behaviour policy. They sit at the message boundaries, rather than replacing the advisor or supplying course facts.', [
        scenarioId === 'photography'
          ? 'Photography does not connect native Guardrails. Its tool restrictions and instructions are application controls, so this map must not imply that a native behavioural check ran.'
          : 'The application loads its selected Guardrails rules and checks the relevant input or output. It records the resulting decision so you can distinguish an allowed learning request from the separate forbidden credential-request demonstration.',
        'A safety refusal is different from “there is no matching course.” The former is a policy decision; the latter is an ordinary information result. The implemented custom patterns have limited coverage, so demonstrating one blocked request is not proof that every unsafe interaction is covered.',
      ]);
    case 'openshell': return page('Controlled execution',
      'The advisor can be useful without receiving general access to the developer’s machine. OpenShell provides the operational boundary: a trusted supervisor creates a sandbox, then limits what the contained application can reach.', [
        'The advisor, selected harness and course tools execute inside. UserSim and the model gateway holding provider credentials stay outside. This split lets the learner test the application without handing the agent the private simulator profile or host credentials.',
        retail
          ? 'Retail has standalone runs and a separate managed session. Each needs its own loaded policy, observed denials and cleanup evidence. The managed example does not inherit proof from a standalone sandbox.'
          : 'A declared policy expresses our intention; a policy-specific denial demonstrates an enforced restriction. Finishing also means confirming removal of the workload owned by this run. An unrelated failed connection or an old container name proves neither.',
      ]);
    case 'platform': return page('Managed operations',
      'Managed operations handle how an application package is registered, deployed and given sessions. They are outside the citizen advisor’s own decision-making. Helix provides this control-plane role in addition to its separate evaluation capability.', [
        retail
          ? 'The retail managed condition deploys a reusable package and opens a fresh session with selected public context. It does not contain the original persona or resume a private local conversation. The advisor still needs its model and course-tool connections inside the chosen execution boundary.'
          : 'This preset uses standalone execution and does not connect Helix managed operations. The block remains visible to explain the wider architecture, without implying that a registration or managed session exists for this scenario.',
        'Registration, deployment, invocation and cleanup are separate lifecycle outcomes. A package can register successfully while deployment or invocation fails; those records must remain distinguishable when deciding whether the managed example worked.',
      ]);
  }
  throw new Error('Unknown conceptual block');
}

function actionPage(scenarioId: string, block: string, index: string): TeachingPage {
  const retail = scenarioId === 'dreamjob';
  switch (`${block}.${index}`) {
    case 'person.0': return page('Inspect a synthetic person',
      'Read the chosen person before treating their simulated conversation as a useful test. Background and interests help you decide what this example might reveal; they do not establish a real person’s needs or eligibility.', [
        'The app looks up the original identified by the recording and reads it from the installed distribution. [[call:persona.select|The selection code]] is the application operation to inspect. A retained chosen record shows whom we tested; it may not retain every filter or sampling decision that led to that choice.',
        'Keep demographic context and behaviour traits separate when reading the fields. HF profile-only data does not provide the same OCEAN fields as NGC Extended. Missing source data should make this inspection unavailable, rather than cause the app to invent a replacement.',
      ]);
    case 'person.1': return page('Keep the same original',
      'Preserve the selected person so a later change to the advisor does not quietly become a test with someone else. A repeatable input is especially useful when debugging an unexpected answer.', [
        '[[call:persona.lock|The locking operation]] records the source distribution, revision and a fingerprint of the original contents. [[cap:CAP-PER-01|The saved receipt]] lets the app detect a changed row instead of matching only a familiar name.',
        'This action preserves identity; it does not freeze the learner’s replies. Their wording can still depend on the situation, behaviour configuration and previous advisor answers. Generated additions stay separate so they cannot overwrite the original person.',
      ], ['Selected original', 'Identity and content receipt', 'Same original for later comparisons']);
    case 'situation-block.0': return page('Supply the goal and constraints',
      'Choose what you want this test to ask of the advisor. A useful situation gives the learner an understandable goal and enough explicit constraints to recognize a suitable answer.', [
        choose(scenarioId, {
          photography: 'We supply the photography subject, Saturday availability and the spending limit. [[cap:CAP-SIT-01|The authored situation]] is the decision record. These inputs define the test; UserSim later chooses the learner’s wording.',
          boardgames: 'We supply a wish to play board games and an intended follow-up about game design. [[cap:CAP-SIT-01|The authored situation]] preserves that distinction so the test cannot pass merely by offering any game-related activity.',
          dreamjob: 'We supply the retail-learning task and specify when private details may be disclosed. [[cap:CAP-SIT-01|The authored protocol]] keeps the later public training budget separate from the hypothetical salary generated for the simulator.',
        }),
        'The choice belongs to the developer of the test. Keeping it explicit helps you decide whether a failure came from the advisor misunderstanding the request or from the test never providing a necessary constraint.',
      ]);
    case 'situation-block.1': return retail ? page('Add hypothetical details',
      'Add variation without pretending the original dataset supplied it. In retail learning, generated brand preferences and a salary band are labelled hypotheses used to make the test situation richer.', [
        'Data Designer receives an original seed and a limited schema describing the permitted extra fields. The app checks the generated result and stores the selected overlay separately. [[cap:CAP-DD-04|The retained additions and lineage]] show what was accepted and which original it came from.',
        'The overlay belongs to the simulator’s private test context. It is not a statement of real salary, employer endorsement or funding eligibility. The app keeps the authored disclosure protocol in charge of when a hypothetical detail becomes public.',
      ], ['Original seed and permitted fields', 'Generated candidate', 'Validated separate overlay']) : page('Keep source and situation separate',
      'Attach a request to the person without rewriting their biography. This distinction makes the test easier to reason about: the profile is background, while the situation says what the learner wants today.', [
        '[[call:situation.bind|The preparation code]] combines those inputs for UserSim while preserving their different roles. The original can be reused with another request, and the same request can be tried with another original.',
        'No separate Designer enrichment is needed for this preset. Adding generation just to fill a pipeline would introduce another uncertain input without helping explain the intended task.',
      ]);
    case 'learner.0': return page('Prepare the test conversation',
      'Give the simulated learner the instructions needed to act as this person on this task. Preparation decides the starting context and behaviour; it does not manufacture the entire conversation in advance.', [
        '[[call:usersim.prepare|The UserSim preparation code]] resolves the person, behaviour settings and custom learning-advisor probe. [[cap:CAP-US-01|The prepared inputs]] let you distinguish original background from scenario instructions and derived behaviour. Those inputs are for the simulator, rather than a hidden extra briefing for the advisor.',
        retail
          ? 'The probe also specifies staged disclosure. That authored rule takes responsibility for when salary, budget and availability become public. It should not be presented as proof that a probabilistic incremental-disclosure feature happened to choose the same sequence.'
          : 'The custom probe gives this task its goal while inheriting the conversation engine. You do not need to author a new turn-processing loop merely to change the learning request.',
      ]);
    case 'learner.1': return page('Generate messages and react',
      'Let the learner take a turn, hear the advisor and decide what to say next. This is where preparation becomes an interaction: a follow-up is generated in the context of a received answer.', [
        '[[call:usersim.loop|The inherited conversation runtime]] generates and checks a learner message, sends the public text to the target application, then processes the response and its judge/stop decisions. [[cap:CAP-US-04|The activation and trajectory records]] distinguish the messages actually produced from the intentions in the probe.',
        choose(scenarioId, {
          photography: 'This story ends after its short photography exchange. A saved public reply and a saved judge decision are different outputs; neither should be invented to fill an incomplete pair.',
          boardgames: 'The next message must still express the learner’s intended comparison with game design. A generation rejected for role or language problems is a simulator event, not a second successful public conversation.',
          dreamjob: 'The learner hears the application’s confirmed clarification at turn 2 before stating budget and study days. That reply can advance UserSim even though the application did not invoke Fabric or another advisor model call for the clarification.',
        }),
      ], ['Generate learner text', 'Check the turn', 'Receive public advisor output', 'Judge and continue or finish']);
    case 'advisor.0': return page('Connect the selected agent',
      'Make the chosen harness ready to answer through the application. Connecting it means supplying instructions, a model connection and the approved course-tool interface, then checking that the runtime can start.', [
        `The app uses [[call:fabric.config|one configuration builder]] to connect ${scenarioId === 'boardgames' ? 'Hermes' : 'Deep Agents'}. Fabric provides the common startup interface while the selected adapter handles the harness-specific setup. This is why a harness choice can change settings without duplicating the course-advisor application.`,
        '[[cap:CAP-FAB-03|The plan and preflight reports]] show whether those connections are understood; [[cap:CAP-FAB-04|startup evidence]] shows what became ready. Neither means a learner request has already run. Separate readiness from answer quality when diagnosing the setup.',
      ], ['Instructions, model connection and tools', 'Configuration and readiness checks', 'Persistent selected runtime']);
    case 'advisor.1': return page('Use tools and return a reply',
      'Handle the learner’s public request with the information available at that moment. The advisor should retrieve facts when needed and produce advice that stays within those facts, rather than treating fluent prose as proof of a course listing.', [
        retail
          ? 'The app first checks whether an options discussion is missing budget or study days. [[call:retail.response.clarify|It asks a clarification directly]] when those decisions are missing. Otherwise the selected harness can call the model and course tools, after which the app presents returned facts and keeps the native proposal separately.'
          : '[[call:fabric.invoke|The application invocation]] passes the public message into the selected harness. The harness can ask its model, call approved course tools and continue with the returned information before it finishes. One public reply can therefore involve more than one internal operation.',
        '[[cap:CAP-FAB-06|The native response record]] shows what the agent returned when it was invoked. Compare that boundary with the delivered public answer; if the application also transforms or checks the response, that responsibility must remain visible.',
      ]);
    case 'courses.0': return page('Look up matching courses',
      'Turn the learner’s stated needs into a question the catalogue can answer. A course search is useful when its inputs reflect the public request and its result is interpreted honestly.', [
        '[[call:mcp.search|The read-only search tool]] combines the requested topic with permitted public constraints. The matching code reads known listings; it does not ask a model to invent suitable offerings. [[cap:CAP-MCP-03|The actual tool evidence]] shows both the arguments and what came back.',
        choose(scenarioId, {
          photography: 'Check how the search treats the stated day and budget while preserving unknown extra costs. A listing that looks inexpensive is not automatically a confirmed all-in fit.',
          boardgames: 'An empty match list is meaningful when the search completed successfully. It tells the advisor the catalogue has no supported option for this request; a lookup error would instead mean the search could not be established.',
          dreamjob: 'The tool budget comes from an explicit public spending limit, never from monthly salary. Before budget and days are stated, those fields remain unknown instead of being filled with convenient assumptions.',
        }),
      ]);
    case 'courses.1': return page('Keep the facts and source links',
      'Preserve the information the advisor actually had. A dated snapshot lets you explain an answer and evaluate it later without quietly switching to today’s version of a provider page.', [
        'The app freezes source-linked course records for the run. [[cap:CAP-MCP-03|Returned native course facts]] can then be compared with [[file:catalogue-snapshot.json|that run’s catalogue snapshot]]. A course identifier helps connect the response to a specific listing, while the source link tells you where the published information came from.',
        'A snapshot preserves evidence rather than guaranteeing that a place, timetable or fee is still available. Unknown fields should remain unknown. If current advice needs a fresher source, that should become an explicit data update and a new test.',
      ]);
    case 'models.0': return page('Limit and account for calls',
      'Put a boundary around model work before a conversation starts. The application needs to know how much work it permits and which requests came from the advisor, simulated learner or judges.', [
        '[[call:models.admit|The gateway admission code]] enforces the configured workload budget, and [[cap:CAP-GW-01|its effective settings]] show the actual limits. Requests that cannot be admitted fail explicitly instead of silently running outside the declared budget.',
        '[[cap:CAP-GW-02|The call accounting]] records attempts, role, status and available usage. Bounded recovery from HTTP 429 can create another attempt; it does not make invalid content eligible for automatic retry. A missing usage figure remains unknown rather than becoming zero.',
      ]);
    case 'models.1': return retail ? page('Choose a model strategy',
      'Decide how the proxy should select a model without changing the citizen-facing application request. A fixed candidate provides a baseline for comparing a policy that chooses within the same inventory.', [
        'Retail compares MiniMax/Mistral conditions with separate runtime state. [[cap:CAP-LLM-02|The loaded candidate settings]] define the available deployments. Switchyard’s policy chooses within that group; it does not answer the learner itself.',
        '[[cap-run:CAP-SW-02|The actual decisions and outcomes]] show whether a selection led to a completed and evaluated answer. Compare conditions that held inputs, catalogue, harness and limits steady. A different inventory or unfinished run cannot establish a policy improvement.',
      ], ['Same public task', 'Fixed candidate or routing policy', 'Selected provider response', 'Comparable evaluation']) : page('Use the fixed model route',
      'Choose one configured model path for this example. Keeping the route fixed makes the advisor’s task behaviour easier to examine before adding a model-selection experiment.', [
        'The application requests an alias, and LiteLLM resolves it to its configured deployment. [[cap:CAP-LLM-01|The loaded proxy settings]] express that choice. The alias is a connection name, not another conversational participant.',
        '[[cap:CAP-GW-02|The observed provider identity]] lets you see what actually answered. Switchyard does not make a candidate decision here, so this example offers no evidence of routing optimization or model-policy savings.',
      ]);
    case 'evidence.0': return page('Follow what actually happened',
      'Follow an observed action back to its input and result. This helps explain an answer more reliably than the advisor’s own claim that it performed a search.', [
        'Relay records agent, model and tool scopes with their captured parent relationships. [[cap:CAP-REL-02|The native event export]] lets the app show that tree without guessing missing parents. The separate gateway record counts model work but is not automatically a parent-linked trace of the agent.',
        retail
          ? 'For the application-only clarification, expect an application delivery decision and no new agent subtree. Previously retrieved course facts can be reused without a fresh search. An absent native event is correct for that branch, rather than a trace failure that needs filling.'
          : 'Use the selected turn’s attributable events when available. If the recording provides only a run-wide export, interpret it at that wider scope rather than pretending every recorded action belongs to the reply currently selected.',
      ]);
    case 'evidence.1': return page('Check the saved advice',
      'Compare the delivered answer with a specific requirement. A useful check tells you what was expected, what was observed and why that difference matters for the learner.', [
        retail
          ? 'The application derives explicit criterion values from the conversation, catalogue and execution evidence. [[cap:CAP-HX-01|Helix scores those saved values]]; it does not broaden the coverage of the rules we authored or certify the preserved model prose.'
          : 'The application runs deterministic assertions over the saved conversation and its available evidence. [[cap:CAP-EVAL-01|The criterion results]] let you inspect the reason for a pass or failure rather than trust the total alone.',
        'A source-link check can verify that a cited listing belongs to the snapshot without proving every sentence in the answer. Reading the coverage helps you choose the next useful test instead of treating a perfect fraction as universal correctness.',
      ]);
    case 'guardrails.0': return page('Load policy, check and return a decision',
      'Apply the selected behaviour rule to the message boundary being examined. The result should tell the application whether to continue or return its configured blocked response.', [
        scenarioId === 'photography'
          ? 'Native Guardrails is not connected for photography, so no policy execution is claimed. The advisor’s application instructions and course-only tool permissions are separate controls.'
          : '[[cap:CAP-GR-01|The effective rules]] define the configured behaviour. [[cap:CAP-GR-02|The native check decisions]] establish which boundary and action ran. Keep the legitimate learning conversation separate from the negative credential-disclosure probe.',
        'Pattern-based checks can demonstrate a concrete boundary, but a passed check is only as broad as its rule. A normal catalogue no-match should continue as advice rather than be relabelled as a policy refusal.',
      ]);
    case 'openshell.0': return page('Create the sandbox with policy',
      'Start a contained place for the advisor to run and tell it what access is allowed. This step establishes the operational boundary before the conversation begins.', [
        '[[cap:CAP-OS-01|The requested policy]] expresses the intended permissions. The trusted OpenShell supervisor creates the workload under that policy; it does not become part of the untrusted agent process.',
        '[[cap:CAP-OS-02|The runtime identity and loaded policy]] show what was actually created. Keep those separate from a reusable source policy, because declaring permissions is different from verifying the running configuration.',
      ]);
    case 'openshell.1': return page('Execute the advisor and course tools inside',
      'Keep the application and its tools within the access boundary while the learner talks to it. A sandbox that only wrapped startup would not explain the permissions of the later agent and tool work.', [
        'The app uses [[call:openshell.execute|the native execution bridge]] to keep the persistent harness and course service inside. Model requests cross the bounded host bridge, where the credentialed gateway remains outside the workload.',
        'The learner’s private simulator context is not copied into an agent image. Only public requests and the permitted course-tool configuration cross the application boundary. That gives the containment decision a concrete information-flow meaning.',
      ]);
    case 'openshell.2': return page('Verify allowed/denied operations and cleanup',
      'Test whether the declared access boundary did its job, then remove the resources this run owns. Useful enforcement evidence needs a known permitted action and a known forbidden action.', [
        '[[cap:CAP-OS-02|The probe and cleanup receipts]] distinguish policy-specific denial from ordinary connection failure. A successful model/tool exchange demonstrates permitted work; a denied filesystem or network operation demonstrates a different restriction.',
        'Cleanup must identify this run’s workload and confirm its absence. Do not delete unrelated or uncertain resources merely because their names look old. Reviewing this evidence should never itself terminate a workload.',
      ]);
    case 'platform.0': return page('Register and deploy the application',
      'Make a reusable application package available to managed operations. Registration describes the application; deployment asks the platform to run that registered package in a selected environment.', [
        retail
          ? '[[cap:CAP-PLAT-02|The submitted agent definition]] carries the public package configuration. [[cap:CAP-PLAT-04|The registration and deployment receipts]] identify the resulting resources. The package does not embed the private original persona or its hypothetical overlay.'
          : 'This preset does not register or deploy through Helix. Its standalone OpenShell execution has a different lifecycle and cannot serve as proof of a managed deployment.',
        'A registered package is not yet a successful session. Inspect each boundary’s outcome before interpreting the later managed answer.',
      ]);
    case 'platform.1': return page('Open a session, invoke and clean up',
      'Give the managed deployment a fresh conversation, send the selected public request and close the owned resources afterward. A session is an execution context, rather than a copy of the local simulator’s private state.', [
        retail
          ? '[[cap:CAP-PLAT-05|The managed lifecycle records]] show the public invocation and its result separately from session/deployment cleanup. This condition starts new memory; it does not resume the baseline conversation or append another UserSim public turn.'
          : 'There is no managed session for this preset. Opening the map does not create one, and standalone conversation records must not be relabelled as platform session evidence.',
        'A complete result includes what happened to the owned session and deployment, even when invocation failed. Preserving that lifecycle makes the demonstration usable for diagnosing a real managed application.',
      ]);
  }
  throw new Error('Unknown conceptual action');
}
