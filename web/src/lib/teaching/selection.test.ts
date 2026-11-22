import {describe, expect, it} from 'vitest';
import {components, scenarioIds, simpleBlocks} from '../lessonArchitecture';
import {conceptOperations, validConcept, validSelection} from './selection';

describe('semantic teaching selections', () => {
  it('keeps conceptual identities independent from their several technical members', () => {
    expect(validConcept('photography', 'advisor')).toBe(true);
    expect(validConcept('photography', 'fabric')).toBe(false);
    expect(conceptOperations('photography', 'advisor', 'advisor.0')).toEqual(expect.arrayContaining([
      'fabric.config', 'fabric.plan', 'fabric.start', 'harness.context', 'mcp.connect', 'models.alias', 'relay.configure',
    ]));
    expect(conceptOperations('dreamjob', 'evidence', 'evidence.1')).toEqual(expect.arrayContaining([
      'checks.evaluate', 'helix.evaluate', 'helix.job',
    ]));
  });

  it('accepts every graph action but rejects foreign, technical and malformed action IDs', () => {
    for (const scenario of scenarioIds) {
      for (const block of simpleBlocks(scenario)) {
        expect(validSelection(scenario, false, block.id)).toBe(true);
        for (const index of block.rows.keys()) expect(validSelection(scenario, false, block.id, `${block.id}.${index}`)).toBe(true);
      }
      for (const component of components.filter(candidate => ['guardrails', 'openshell', 'platform'].includes(candidate.id))) {
        expect(validSelection(scenario, false, component.id)).toBe(true);
        for (const index of component.operations.keys()) expect(validSelection(scenario, false, component.id, `${component.id}.${index}`)).toBe(true);
        expect(validSelection(scenario, false, component.id, `${component.id}.${component.operations.length}`)).toBe(false);
      }
      for (const invalid of ['fabric.config', 'person.0', 'advisor.-1', 'advisor.0.5', 'advisor.99', 'advisor.NaN', 'advisor.']) {
        expect(validSelection(scenario, false, 'advisor', invalid), invalid).toBe(false);
      }
      expect(validSelection(scenario, true, 'fabric', 'advisor.0')).toBe(false);
    }
  });

  it('accepts library operations only under their actual library', () => {
    for (const scenario of scenarioIds) for (const component of components) {
      expect(validSelection(scenario, true, component.id)).toBe(true);
      for (const operation of component.operations) {
        expect(validSelection(scenario, true, component.id, operation.id)).toBe(true);
        const other = components.find(candidate => candidate.id !== component.id)!;
        expect(validSelection(scenario, true, other.id, operation.id)).toBe(false);
      }
    }
  });
});
