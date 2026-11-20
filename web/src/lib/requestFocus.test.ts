import { describe, expect, it } from 'vitest';
import { requestFocus } from './requestFocus';
const trace = {usage:{records:[{call:3,role:'assistant',status:'completed',selected_model:'fixture-model'}]},
  tools:[{name:'search_courses',scope_uuid:'native-fixture',status:'completed'}],conversation:[{role:'user',turn:1}]};
describe('saved request attribution',()=>{
  it('does not fabricate a Relay join for a gateway call',()=>{
    const focus=requestFocus(trace,'call:3')!;
    expect(focus.nodes).toEqual(['gateway','litellm','providers']);
    expect(focus.nodes).not.toContain('relay');
    expect(focus.notice).toContain('correlation is not assumed');
  });
  it('requires the actual native tool identity',()=>{
    expect(requestFocus(trace,'tool:native-fixture')!.edges).toEqual(['mcp-relay']);
    expect(requestFocus(trace,'tool:another-run')!.nodes).toEqual([]);
  });
  it('retains an explicit missing selection instead of choosing another request',()=>{
    expect(requestFocus(trace,'call:42')!.notice).toContain('missing');
    expect(requestFocus(trace,'turn:2')!.nodes).toEqual([]);
    expect(requestFocus(trace,'turn:1')!.nodes).toContain('usersim');
    expect(requestFocus(null,'call:3')).toBeNull();
    expect(requestFocus(trace,'')).toBeNull();
  });
});
