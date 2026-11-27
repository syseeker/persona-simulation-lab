import{describe,it,expect}from'vitest';
import{integrationNodes}from'./integrationLayout';
import{edgesFor,simpleBlocks}from'./lessonArchitecture';
import{routeConnections,routingObstacles,rectanglesOverlap,segmentHitsRect,type RoutingLink,type GeometryNode}from'./orthogonalRouter';

function links(scenario:string,detailed:boolean):RoutingLink[]{
  const membership=new Map(simpleBlocks(scenario).flatMap(b=>b.members.map(id=>[id,b.id]))),grouped=new Map<string,RoutingLink>();
  for(const e of edgesFor(scenario)){const source=detailed?e.source:membership.get(e.source)||e.source,target=detailed?e.target:membership.get(e.target)||e.target;
    if(source===target)continue;const id=`${source}-${target}-${e.kind}`;if(!grouped.has(id))grouped.set(id,{...e,id,source,target});}
  return[...grouped.values()];
}
function verify(nodes:GeometryNode[],connections:RoutingLink[]){
  const routed=routeConnections(nodes,connections),obstacles=routingObstacles(nodes);
  expect(routed.map(r=>r.id).sort()).toEqual(connections.map(r=>r.id).sort());
  for(const edge of routed){
    expect(edge.path).not.toContain('NaN');expect(edge.labelBox,`${edge.id} has a visible label`).toBeDefined();
    for(let i=1;i<edge.points.length;i++){
      const a=edge.points[i-1],b=edge.points[i];expect(a.x===b.x||a.y===b.y,`${edge.id}: orthogonal`).toBe(true);
      for(const obstacle of obstacles)expect(segmentHitsRect(a,b,obstacle),`${edge.id} crosses ${obstacle.id}`).toBe(false);
    }
    if(edge.labelBox)for(const obstacle of obstacles)expect(rectanglesOverlap(edge.labelBox,obstacle),`${edge.id} label covers ${obstacle.id}`).toBe(false);
  }
  for(let i=0;i<routed.length;i++)for(let j=i+1;j<routed.length;j++){
    const a=routed[i],b=routed[j];if(a.labelBox&&b.labelBox)expect(rectanglesOverlap(a.labelBox,b.labelBox),`${a.id}/${b.id} labels overlap`).toBe(false);
    for(const[label,other]of[[a,b],[b,a]])if(label.labelBox)for(let k=1;k<other.points.length;k++)expect(segmentHitsRect(other.points[k-1],other.points[k],label.labelBox),`${other.id} crosses ${label.id} label`).toBe(false);
  }
  return routed;
}
describe('obstacle-aware architecture connections',()=>{
  for(const scenario of['photography','boardgames','dreamjob'])for(const detailed of[false,true]){
    it(`routes every ${scenario} ${detailed?'detailed':'simplified'} path and label outside cards`,()=>verify(integrationNodes(detailed,false),links(scenario,detailed)));
  }
  for(const detailed of[false,true])it(`routes the separate managed caller ${detailed?'detailed':'simplified'} boundary`,()=>verify(integrationNodes(detailed,true),links('dreamjob',detailed)));
  it('reroutes after a group moves, including its children',()=>{
    const nodes=integrationNodes(true,false).map(n=>n.id==='zone-inputs'?{...n,position:{x:n.position.x-120,y:n.position.y+80}}:n);
    verify(nodes,links('dreamjob',true));
  });
  it('reroutes a valid manually moved component and retains its exact position',()=>{
    const nodes=integrationNodes(false,false).map(n=>n.id==='models'?{...n,position:{x:n.position.x+150,y:n.position.y-120}}:n);
    const position={...nodes.find(n=>n.id==='models')!.position};verify(nodes,links('boardgames',false));expect(nodes.find(n=>n.id==='models')!.position).toEqual(position);
  });
  it('is deterministic and keeps reverse directions on separate ports',()=>{
    const nodes=integrationNodes(false,false),connections=links('photography',false),first=routeConnections(nodes,connections);
    expect(routeConnections(nodes,connections)).toEqual(first);
    const request=first.find(e=>e.source==='learner'&&e.target==='advisor')!,reply=first.find(e=>e.source==='advisor'&&e.target==='learner')!;
    expect(request.points[0]).not.toEqual(reply.points.at(-1));
  });
});
