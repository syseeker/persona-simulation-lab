import {describe,it,expect} from 'vitest';
import {components,componentById,operationById,lessonFor,lessonIds,scenarioIds,simpleBlocks,edgesFor,componentUsed,sourceId,hostCallerPosition} from './lessonArchitecture';

describe('one architecture across all scenario lessons',()=>{
  it('gives all 27 combinations an explained operation path and verification contract',()=>{
    let count=0;
    for(const scenario of scenarioIds)for(const id of lessonIds){
      const lesson=lessonFor(scenario,id);count++;
      for(const field of ['why','input','action','output','design'] as const)expect(lesson[field].length).toBeGreaterThan(20);
      expect(lesson.checks.length).toBeGreaterThan(0);expect(lesson.operations.length).toBeGreaterThan(0);
      for(const key of lesson.operations){const op=operationById[key];expect(op,key).toBeDefined();expect(op.proof.length).toBeGreaterThan(0);expect(op.config.length).toBeGreaterThan(10);}
    }
    expect(count).toBe(27);
  });
  it('keeps seven core responsibilities distinct from the nine lesson numbers',()=>{
    for(const scenario of scenarioIds){
      const blocks=simpleBlocks(scenario);expect(blocks).toHaveLength(7);
      expect(blocks.map(b=>b.title)).toEqual(['Test person','Test situation','Simulated learner','Citizen advisor','Course information','Model access','Execution records and checks']);
      for(const block of blocks){expect(block.title).not.toMatch(/^\d/);for(const row of block.rows)expect(operationById[row.operation]).toBeDefined();}
      for(const c of components.filter(c=>!['guardrails','openshell','platform'].includes(c.id)))expect(blocks.flatMap(b=>b.members)).toContain(c.id);
    }
  });
  it('separates selecting a profile, preparing UserSim and executing its loop',()=>{
    for(const scenario of scenarioIds){
      expect(lessonFor(scenario,'persona').operations.every(id=>operationById[id].component==='personas')).toBe(true);
      expect(lessonFor(scenario,'situation').operations).toContain('usersim.prepare');
      expect(lessonFor(scenario,'situation').operations).not.toContain('usersim.loop');
      expect(lessonFor(scenario,'run').operations).toContain('usersim.loop');
    }
  });
  it('shows the progressive integrations without borrowing another scenario’s execution',()=>{
    expect(componentUsed('designer','photography')).toBe(false);expect(componentUsed('routing','photography')).toBe(false);
    expect(componentUsed('guardrails','photography')).toBe(false);expect(componentUsed('helix','photography')).toBe(false);
    expect(componentUsed('designer','boardgames')).toBe(false);expect(componentUsed('guardrails','boardgames')).toBe(true);
    expect(componentUsed('designer','dreamjob')).toBe(true);expect(componentUsed('platform','dreamjob')).toBe(true);
    expect(lessonFor('photography','routing').operations).not.toContain('routing.decision');
    expect(lessonFor('dreamjob','routing').operations).toContain('routing.decision');
    expect(sourceId('harness.context','boardgames')).toBe('harness.context');
    expect(sourceId('fabric.invoke','boardgames')).toBe(sourceId('fabric.invoke','photography'));
  });
  it('connects existing components, attaches Relay to the harness and places safeguards on public boundaries',()=>{
    for(const scenario of scenarioIds)for(const edge of edgesFor(scenario)){
      expect(componentById[edge.source],edge.source).toBeDefined();expect(componentById[edge.target],edge.target).toBeDefined();
      for(const id of edge.operations)expect(operationById[id],id).toBeDefined();
    }
    expect(edgesFor('photography').find(e=>e.id==='harness-relay')?.kind).toBe('telemetry');
    expect(edgesFor('boardgames').some(e=>e.id==='learner-advisor')).toBe(false);
    expect(edgesFor('boardgames').some(e=>e.id==='guard-advisor')).toBe(true);
  });
  it('traces both public-message directions through native safeguards in each guarded preset',()=>{
    for(const scenario of ['boardgames','dreamjob']){
      const edges=edgesFor(scenario);
      for(const [source,target] of [['usersim','guardrails'],['guardrails','fabric'],['fabric','guardrails'],['guardrails','usersim']]){
        const edge=edges.find(e=>e.source===source&&e.target===target);
        expect(edge,`${scenario}: ${source} → ${target}`).toBeDefined();
        expect(edge?.operations).toContain('guardrails.check');
      }
      expect(edges.some(e=>e.source==='usersim'&&e.target==='fabric')).toBe(false);
      expect(edges.some(e=>e.source==='fabric'&&e.target==='usersim')).toBe(false);
    }
    const photography=edgesFor('photography');
    expect(photography.find(e=>e.id==='learner-advisor')).toMatchObject({source:'usersim',target:'fabric'});
    expect(photography.find(e=>e.id==='advisor-learner')).toMatchObject({source:'fabric',target:'usersim'});
    expect(photography.some(e=>e.source==='guardrails'||e.target==='guardrails')).toBe(false);
  });
  it('restores a host caller outside a moved sandbox while retaining valid custom positions',()=>{
    const sandbox={x:900,y:200,width:552,height:920};
    const overlapping={x:1000,y:250,width:552,height:166};
    const restored=hostCallerPosition(overlapping,sandbox);
    expect(restored).toEqual({x:900,y:6});
    expect(restored.y+overlapping.height).toBeLessThan(sandbox.y);
    const outside={x:200,y:250,width:552,height:166};
    expect(hostCallerPosition(outside,sandbox)).toEqual({x:200,y:250});
    const touching={x:900,y:34,width:552,height:166};
    expect(hostCallerPosition(touching,sandbox)).toEqual({x:900,y:34});
  });
});
