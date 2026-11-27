import {readFileSync} from 'node:fs';
import {describe, expect, it} from 'vitest';
import {lessonIds, scenarioIds, simpleBlocks} from '../lessonArchitecture';
import {lessonPage} from './lessons';
import {simplePage} from './concepts';
import type {TeachingPage} from './types';

function text(page: TeachingPage): string {
  return [page.intro, ...page.sections.flatMap(section => section.paragraphs || [])].join('\n');
}

describe('destination-owned teaching content', () => {
  it('authors all 54 audience/scenario lessons with one correctly owned observation', () => {
    for (const scenario of scenarioIds) for (const lesson of lessonIds) {
      const simple = lessonPage(scenario, lesson, false);
      const detailed = lessonPage(scenario, lesson, true);
      expect(simple.title).toBe(detailed.title);
      expect(simple.intro).not.toBe(detailed.intro);
      for (const page of [simple, detailed]) {
        const approvedShortOpening = scenario === 'photography' && page === simple && ['run', 'evaluate'].includes(lesson);
        expect(page.intro.split(' ').length).toBeGreaterThan(approvedShortOpening ? 5 : 20);
        expect(text(page).split(/\s+/).length).toBeGreaterThan(60);
        expect(page.sections.flatMap(section => section.observation ? [section.observation] : [])).toEqual([lesson]);
        expect(page.sections.map(section => section.heading)).not.toContain('Why this matters');
        expect(text(page)).not.toContain('Check your implementation');
        expect(text(page)).not.toContain('Recorded · inspect the matching proof');
      }
    }
  });

  it('preserves every visible conceptual/action heading without inheriting a lesson observation', () => {
    for (const scenario of scenarioIds) for (const block of simpleBlocks(scenario)) {
      const concept = simplePage(scenario, block.id);
      expect(concept.title).toBe(block.title);
      expect(concept.sections.some(section => section.observation)).toBe(false);
      for (const [index, row] of block.rows.entries()) {
        const action = simplePage(scenario, block.id, `${block.id}.${index}`);
        expect(action.title).toBe(row.title);
        expect(action.intro).not.toBe(concept.intro);
        expect(action.sections.some(section => section.observation)).toBe(false);
        for (const paragraph of action.sections.flatMap(section => section.paragraphs || [])) {
          expect(concept.sections.flatMap(section => section.paragraphs || [])).not.toContain(paragraph);
        }
      }
    }
    expect(simplePage('photography', 'advisor').title).toBe('Citizen advisor');
    expect(simplePage('photography', 'advisor', 'advisor.0').title).toBe('Connect the selected agent');
  });

  it('provides conceptual explanations for operational boundaries as well as the seven core blocks', () => {
    for (const scenario of scenarioIds) for (const [block, title, actions] of [
      ['guardrails', 'Behavioural safeguards', 1],
      ['openshell', 'Controlled execution', 3],
      ['platform', 'Managed operations', 2],
    ] as const) {
      expect(simplePage(scenario, block).title).toBe(title);
      for (let index = 0; index < actions; index++) {
        expect(simplePage(scenario, block, `${block}.${index}`).intro.length).toBeGreaterThan(50);
      }
    }
  });

  it('keeps staged disclosure and application-only clarification explicit without inventing success', () => {
    const situation = text(lessonPage('dreamjob', 'situation', true));
    expect(situation).toContain('salary becomes public in turn 2');
    expect(situation).toContain('budget and weekends become public in turn 3');
    const run = text(lessonPage('dreamjob', 'run', true));
    expect(run).toContain('native agent execution for turns 1 and 3');
    expect(run).toContain('not a third Fabric result');
    const routing = text(lessonPage('dreamjob', 'routing', true));
    expect(routing).toContain('MiniMax/Mistral');
    for (const condition of ['fixed-candidate', 'switchyard', 'capable-access', 'available-fixed', 'available-switchyard']) {
      expect(routing).toContain(condition);
    }
    expect(routing).not.toContain('Gemma/GLM failures');
    expect(routing).not.toContain('all conditions passed');
    expect(text(lessonPage('boardgames', 'routing', true))).toContain('not contain a native Switchyard decision');
  });

  it('keeps the approved first-scenario opening and explains the actual request counts', () => {
    expect(lessonPage('photography', 'run', false).intro).toBe('UserSim now writes Caroline’s opening message:');
    expect(text(lessonPage('photography', 'persona', false))).toContain('Caroline is her preferred English name');
    expect(text(lessonPage('photography', 'run', false))).toContain('two model requests and one course search');
    expect(text(lessonPage('photography', 'investigate', false))).toContain('not missing conversation turns');
    expect(text(lessonPage('photography', 'deploy', false))).toContain('separate boundary tests, not actions requested by Caroline');
  });

  it('explains conceptual sequences in connected prose instead of orphan outlines', () => {
    for (const scenario of scenarioIds) for (const block of simpleBlocks(scenario)) {
      for (const action of [undefined, ...block.rows.map((_, index) => `${block.id}.${index}`)]) {
        expect(simplePage(scenario, block.id, action).sections.some(section => section.flow?.length)).toBe(false);
      }
    }
  });

  it('references actual capture requirements and never adds generic architecture links to action pages', () => {
    const registry = JSON.parse(readFileSync(new URL('../../../../src/learning_lab/capture_registry.json', import.meta.url), 'utf8'));
    const requirements = new Set(registry.requirements.map((row: {id: string}) => row.id));
    const pages = scenarioIds.flatMap(scenario => [
      ...lessonIds.flatMap(lesson => [lessonPage(scenario, lesson, false), lessonPage(scenario, lesson, true)]),
      ...simpleBlocks(scenario).flatMap(block => [simplePage(scenario, block.id),
        ...block.rows.map((_, index) => simplePage(scenario, block.id, `${block.id}.${index}`))]),
    ]);
    for (const page of pages) {
      for (const match of text(page).matchAll(/\[\[cap:([^|]+)\|/g)) expect(requirements.has(match[1]), match[1]).toBe(true);
      expect(text(page)).not.toContain('[[url:');
    }
  });

  it('rejects unknown or mismatched destinations instead of using an unrelated fallback', () => {
    expect(() => simplePage('photography', 'advisor', 'fabric.config')).toThrow();
    expect(() => simplePage('photography', 'advisor', 'person.0')).toThrow();
    expect(() => simplePage('photography', 'advisor', 'advisor.20')).toThrow();
    expect(() => simplePage('photography', 'fabric')).toThrow();
    expect(() => lessonPage('toString', 'persona', false)).toThrow();
  });
});
