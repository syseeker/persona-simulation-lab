import {componentById,operationById,simpleBlocks,preset} from '../lessonArchitecture';

/** Conceptual actions are destinations of their own. Their many-to-many
 * operation relationship is used only to focus the architecture. */
export function conceptOperations(scenario:string,block:string,action=''):string[]{
  const p=preset(scenario);
  const actions:Record<string,string[][]>={
    person:[['persona.source','persona.select'],['persona.lock']],
    'situation-block':[['situation.authored','situation.bind'],p.designer?['designer.schema','designer.generate','designer.lineage']:['situation.bind']],
    learner:[['usersim.prepare','usersim.probe'],['usersim.loop','usersim.finalize']],
    advisor:[['fabric.config','fabric.plan','fabric.start','harness.context','mcp.connect','models.alias','relay.configure'],['fabric.invoke','harness.loop','mcp.search','fabric.result']],
    courses:[['mcp.search','mcp.details','mcp.compare'],['catalogue.freeze']],
    models:[['models.admit','models.request'],p.routing==='switchyard'?['routing.policy','routing.decision','models.alias']:['models.alias']],
    evidence:[['relay.configure','relay.scopes','relay.tools','records.read'],p.helix?['checks.evaluate','helix.evaluate','helix.job']:['checks.evaluate']],
  };
  if(actions[block]){
    const index=action.startsWith(block+'.')?Number(action.slice(block.length+1)):-1;
    return index>=0&&Number.isInteger(index)?actions[block][index]||[]:[...new Set(actions[block].flat())];
  }
  const operations=componentById[block]?.operations||[];
  const index=action.startsWith(block+'.')?Number(action.slice(block.length+1)):-1;
  return index>=0&&Number.isInteger(index)?[operations[index]?.id].filter(Boolean):operations.map(o=>o.id);
}
export function validConcept(scenario:string,id:string){return simpleBlocks(scenario).some(b=>b.id===id)||['guardrails','openshell','platform'].includes(id);}
export function validSelection(scenario:string,detailed:boolean,block:string,action=''){
  if(detailed)return !!componentById[block]&&(!action||operationById[action]?.component===block);
  if(!validConcept(scenario,block))return false;
  if(!action)return true;
  if(!action.startsWith(block+'.')||!/^(?:0|[1-9]\d*)$/.test(action.slice(block.length+1)))return false;
  return conceptOperations(scenario,block,action).length>0;
}

type RecordedContext = {state?:string;scenario_id?:string;run_id?:string;context?:Record<string,any>};

/** A persisted comparison belongs to one recording, not just a scenario name. */
export function recordedRoutingCondition(scenario:string,context:RecordedContext|null,id:string,runId?:string):boolean {
  if(scenario!=='dreamjob'||context?.state!=='recorded'||context.scenario_id!==scenario||!context.run_id||!id
    ||(runId!==undefined&&runId!==context.run_id))return false;
  const conditions=context.context?.['routing-comparison.json']?.conditions;
  return Array.isArray(conditions)&&conditions.some(condition=>condition.condition_id===id);
}

/** Inspect the managed boundary only when this recording actually contains it. */
export function recordedManagedSelection(scenario:string,stage:string,component:string|null,context:RecordedContext|null):boolean {
  if(scenario!=='dreamjob'||context?.state!=='recorded'||context.scenario_id!==scenario||!context.run_id)return false;
  const managed=context.context?.['platform-condition.json'];
  return typeof managed?.condition_id==='string'&&managed.condition_id.length>0
    &&(component==='platform'||stage==='deploy');
}
