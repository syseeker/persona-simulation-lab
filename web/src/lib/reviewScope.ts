export type ReviewScope = {
  scenarioId:string; runId:string|null; conditionId:string|null;
  purpose:string; publicTurn:number; deployment:'standalone'|'managed';
};
export const conditionDescriptions:Record<string,{label:string;description:string}>={
  baseline:{label:'Original fixed-model run',description:'The recorded UserSim conversation using the scenario’s fixed model.'},
  'fixed-candidate':{label:'MiniMax fixed',description:'Use MiniMax for every advisor model request. Compare this with automatic MiniMax/Mistral selection.'},
  switchyard:{label:'Automatic choice: MiniMax or Mistral',description:'Let Switchyard choose between MiniMax and Mistral for the same saved conversation.'},
  'capable-access':{label:'Mistral access check',description:'Use Mistral for the same advisor, harness and course-tool path to check that the second candidate can actually answer.'},
  'available-fixed':{label:'Nano fixed diagnostic',description:'Repeat with Nemotron Nano from a separate model inventory. Compare with the automatic Nemotron diagnostic.'},
  'available-switchyard':{label:'Automatic Nemotron diagnostic',description:'Let Switchyard choose between Nano and Lightning. This uses a different pool from the MiniMax/Mistral comparison.'},
  managed:{label:'Helix-managed session',description:'A fresh public request in a session deployed and cleaned up through Helix and its OpenShell executor.'},
};
export function conditionInfo(purpose:string){return conditionDescriptions[purpose]||{label:purpose.replaceAll('-',' '),description:'A separately recorded execution condition.'};}
export function resolveReviewScope(scenarioId:string,context:Record<string,any>|null,stage:string,
  component:string|null,conditionId:string,deployment:'standalone'|'managed',turnIndex:number):ReviewScope{
  const extra=context?.context||{},managed=extra['platform-condition.json'];
  let id=context?.trace?.run?.condition_id||null,purpose='baseline';
  if(scenarioId==='dreamjob'&&(component==='platform'||(stage==='deploy'&&deployment==='managed'))&&managed?.condition_id){id=managed.condition_id;purpose='managed';}
  else if(stage==='routing'||stage==='investigate'){
    const candidate=extra['routing-comparison.json']?.conditions?.find((c:Record<string,any>)=>c.condition_id===conditionId);
    if(candidate){id=candidate.condition_id;purpose=candidate.label;}
  }
  return {scenarioId,runId:context?.run_id||null,conditionId:id,purpose,publicTurn:turnIndex+1,deployment:purpose==='managed'?'managed':'standalone'};
}
export function routingExecuted(scope:ReviewScope){return ['switchyard','available-switchyard'].includes(scope.purpose);}
