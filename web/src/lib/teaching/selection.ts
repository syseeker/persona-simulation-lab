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
