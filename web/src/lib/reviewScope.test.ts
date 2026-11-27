import {describe,it,expect} from 'vitest';
import {resolveReviewScope,routingExecuted,conditionInfo} from './reviewScope';
const context={run_id:'retail-run',trace:{run:{condition_id:'baseline-id'}},context:{
  'routing-comparison.json':{conditions:[{condition_id:'fixed-id',label:'fixed-candidate'},{condition_id:'routed-id',label:'switchyard'}]},
  'platform-condition.json':{condition_id:'managed-id'}
}};
describe('review evidence condition identity',()=>{
  it('keeps deployment standalone until the managed condition is selected',()=>{
    expect(resolveReviewScope('dreamjob',context,'deploy',null,'','standalone',0)).toMatchObject({conditionId:'baseline-id',purpose:'baseline',deployment:'standalone',publicTurn:1});
    expect(resolveReviewScope('dreamjob',context,'deploy',null,'','managed',0)).toMatchObject({conditionId:'managed-id',purpose:'managed'});
  });
  it('inspects platform links in the managed condition and never substitutes a routing condition',()=>{
    expect(resolveReviewScope('dreamjob',context,'build','platform','fixed-id','standalone',0).conditionId).toBe('managed-id');
  });
  it('preserves an explicit comparison for execution inspection and only marks routed work as routed',()=>{
    const fixed=resolveReviewScope('dreamjob',context,'investigate',null,'fixed-id','standalone',1);
    expect(fixed.conditionId).toBe('fixed-id');expect(routingExecuted(fixed)).toBe(false);
    expect(routingExecuted(resolveReviewScope('dreamjob',context,'routing',null,'routed-id','standalone',0))).toBe(true);
  });
  it('rejects foreign comparison IDs and supplies plain-language purposes',()=>{
    expect(resolveReviewScope('dreamjob',context,'routing',null,'foreign-id','standalone',0).conditionId).toBe('baseline-id');
    expect(conditionInfo('available-switchyard').description).toContain('different pool');
  });
});
