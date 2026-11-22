import {readFileSync} from 'node:fs';
import {describe,expect,it} from 'vitest';
import {components,componentTitle,operationById,scenarioIds,sourceId} from '../lessonArchitecture';
import type {TeachingPage} from './types';
import {detailedPage} from './libraries';

function prose(page:TeachingPage):string[] {
  return [page.intro,...page.sections.flatMap(section=>section.paragraphs||[])];
}

const registry=JSON.parse(readFileSync(new URL('../../../../src/learning_lab/capture_registry.json',import.meta.url),'utf8'));
const requirements=new Set(registry.requirements.map((row:{id:string})=>row.id));
const sourceRegistry=readFileSync(new URL('../../../../src/learning_lab/guide_sources.py',import.meta.url),'utf8')
  .split('OPERATIONS = {')[1].split('\n}\n')[0];
const sourceIds=new Set([...sourceRegistry.matchAll(/'([^']+)': \('/g)].map(match=>match[1]));

describe('Detailed library and operation teaching destinations',()=>{
  it('authors all 180 destinations with the exact clicked identity',()=>{
    expect(components).toHaveLength(18);
    expect(components.flatMap(component=>component.operations)).toHaveLength(42);
    let destinations=0;
    for(const scenario of scenarioIds) for(const component of components){
      const library=detailedPage(scenario,component.id);
      expect(library.title).toBe(componentTitle(component.id,scenario));
      for(const operation of [undefined,...component.operations]){
        const page=operation?detailedPage(scenario,component.id,operation.id):library;
        expect(page.title).not.toBe('Explanation unavailable');
        if(operation)expect(page.title).toBe(operation.title);
        expect(page.intro.split(/\s+/).length).toBeGreaterThan(20);
        expect(page.sections.flatMap(section=>section.paragraphs||[]).length).toBeGreaterThanOrEqual(2);
        expect(page.sections.some(section=>section.observation)).toBe(false);
        destinations++;
      }
    }
    expect(destinations).toBe(180);
  });

  it('binds purposeful references to existing CAP requirements and scenario-resolved call sites',()=>{
    for(const scenario of scenarioIds)for(const component of components){
      for(const operation of [undefined,...component.operations]){
        const page=detailedPage(scenario,component.id,operation?.id);
        for(const line of prose(page))for(const match of line.matchAll(/\[\[(call|cap):([^|]+)\|([^\]]+)\]\]/g)){
          const [,kind,id,label]=match;
          expect(label.length).toBeGreaterThan(3);
          if(kind==='cap')expect(requirements.has(id),id).toBe(true);
          else {
            expect(sourceIds.has(id),id).toBe(true);
            const resolved=sourceId(id,scenario)||id;
            expect(sourceIds.has(resolved),`${scenario}: ${resolved}`).toBe(true);
          }
        }
      }
    }
  });

  it('keeps architecture at library homes and gives operations different substantive content',()=>{
    for(const scenario of scenarioIds)for(const component of components){
      const library=detailedPage(scenario,component.id);
      const libraryProse=prose(library);
      const intros=new Set<string>();
      for(const operation of component.operations){
        const page=detailedPage(scenario,component.id,operation.id);
        expect(page.intro).not.toBe(library.intro);
        expect(intros.has(page.intro),operation.id).toBe(false);
        intros.add(page.intro);
        for(const line of prose(page)){
          expect(libraryProse,operation.id).not.toContain(line);
          expect(line).not.toContain('[[url:');
          expect(line).not.toMatch(/Why this matters|Check your implementation|Recorded[. ·]+inspect|source hash matches/i);
        }
      }
    }
  });

  it('separates native configuration assembly, resolution, startup, invocation and result handling',()=>{
    const config=prose(detailedPage('dreamjob','fabric','fabric.config')).join('\n');
    expect(config).toContain('nested classes');
    expect(config).toContain('not a sequence of processing stages');
    expect(config).toContain('Neither public file is loaded as runtime input');
    expect(config).toContain('RuntimeConfig');
    expect(config).not.toContain('runtime.invoke');
    expect(config).not.toContain('runtime_started');
    expect(prose(detailedPage('boardgames','fabric','fabric.plan')).join('\n')).toContain('Fabric.doctor');
    expect(prose(detailedPage('boardgames','fabric','fabric.start')).join('\n')).toContain('Fabric.start_runtime');
    expect(prose(detailedPage('boardgames','fabric','fabric.invoke')).join('\n')).toContain('runtime.invoke(request=request)');
    expect(prose(detailedPage('dreamjob','fabric','fabric.result')).join('\n')).toContain('retail.response.confirm');
  });

  it('explains each preset’s effective timeout without confusing request, agent and public-turn limits',()=>{
    for(const [scenario,turns] of [['photography','one public learner turn'],['boardgames','two public learner turns']]){
      const config=prose(detailedPage(scenario,'fabric','fabric.config')).join('\n');
      expect(config).toContain('keeps RuntimeConfig.timeout_seconds=120');
      expect(config).not.toContain('timeout_seconds=600');
      expect(config).toContain(turns);
      expect(config).toContain('RuntimeConfig.max_turns=24');
    }
    const config=prose(detailedPage('dreamjob','fabric','fabric.config')).join('\n');
    expect(config).toContain('initially sets RuntimeConfig.timeout_seconds=120');
    expect(config).toContain('raises it to 600 before planning and startup');
    expect(config).toContain('effective captured configuration contains timeout_seconds=600');
    expect(config).toContain('three public learner turns');
    const request=prose(detailedPage('dreamjob','gateway','models.request')).join('\n');
    expect(request).toContain('300-second total request deadline');
    expect(request).toContain('Retry-After can extend a delay');
    expect(request).toContain('50-second request deadline with application recovery disabled');
  });

  it('preserves native/application and outcome/coverage distinctions at their relevant boundaries',()=>{
    const text=(scenario:string,component:string,operation:string)=>prose(detailedPage(scenario,component,operation)).join('\n');
    expect(text('dreamjob','fabric','fabric.invoke')).toContain('no native request/result');
    expect(text('dreamjob','usersim','usersim.loop')).toContain('fabricated RunResult');
    expect(text('photography','usersim','usersim.finalize')).toContain('does not create a trajectory Parquet');
    expect(text('photography','mcp','mcp.details')).toContain('does not wrap that record in a matches list');
    expect(text('boardgames','mcp','mcp.search')).toContain('error_kind=invalid_input');
    expect(text('dreamjob','gateway','models.request')).toContain('HTTP 429');
    expect(text('dreamjob','gateway','models.request')).toContain('Each retry consumes another admitted attempt');
    expect(text('dreamjob','routing','routing.decision')).toContain('capable-access');
    expect(text('dreamjob','helix','helix.evaluate')).toContain('not general correctness');
  });

  it('never maps an invalid technical selection onto an unrelated component',()=>{
    expect(detailedPage('photography','fabric','persona.lock').title).toBe('Explanation unavailable');
    expect(detailedPage('photography','nonexistent').title).toBe('Explanation unavailable');
    expect(detailedPage('photography','toString').title).toBe('Explanation unavailable');
    expect(detailedPage('not-a-scenario','fabric').title).toBe('Explanation unavailable');
    expect(detailedPage('photography','fabric','not-an-operation').title).toBe('Explanation unavailable');
    expect(operationById['fabric.config'].title).toBe('Build the typed FabricConfig');
  });
});
