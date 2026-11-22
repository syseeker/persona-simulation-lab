import {componentById,componentTitle,operationById,scenarioIds} from '../lessonArchitecture';
import type {TeachingPage} from './types';
import {inputLibraries,inputOperations} from './detailedInputs';
import {runtimeLibraries,runtimeOperations} from './detailedRuntime';
import {controlLibraries,controlOperations} from './detailedControls';

/** Technical pages are authored independently from conceptual blocks and lessons. */
export function detailedPage(scenarioId:string,componentId:string,operationId?:string):TeachingPage {
  if (!scenarioIds.some(id=>id===scenarioId) || !Object.hasOwn(componentById,componentId)
      || (operationId && operationById[operationId]?.component!==componentId)) {
    return {title:'Explanation unavailable',intro:'This selection has no matching technical explanation. Return to the current lesson to choose a component or operation.',sections:[]};
  }
  const pages=operationId
    ? {...inputOperations(scenarioId),...runtimeOperations(scenarioId),...controlOperations(scenarioId)}
    : {...inputLibraries(scenarioId),...runtimeLibraries(scenarioId),...controlLibraries(scenarioId)};
  const page=pages[operationId || componentId];
  if (!page) {
    return {title:'Explanation unavailable',intro:'This technical destination has not been authored. No other component’s explanation is substituted.',sections:[]};
  }
  return {...page,title:operationId?operationById[operationId].title:componentTitle(componentId,scenarioId)};
}
