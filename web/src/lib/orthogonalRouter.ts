export type Point={x:number;y:number};
export type Rect=Point&{width:number;height:number;id?:string};
export type GeometryNode={id:string;type?:string;position:Point;width?:number;height?:number;parentId?:string};
export type RoutingLink={id:string;source:string;target:string;label?:string;kind?:string};
export type Side='left'|'right'|'top'|'bottom';
export type RoutedLink=RoutingLink&{points:Point[];path:string;sourceSide:Side;targetSide:Side;labelBox?:Rect;labelLines:string[]};
const CLEARANCE=9,STUB=15;
const same=(a:Point,b:Point)=>a.x===b.x&&a.y===b.y;
const inflate=(r:Rect,by:number):Rect=>({...r,x:r.x-by,y:r.y-by,width:r.width+by*2,height:r.height+by*2});
export const rectanglesOverlap=(a:Rect,b:Rect,gap=0)=>a.x<b.x+b.width+gap&&a.x+a.width+gap>b.x&&a.y<b.y+b.height+gap&&a.y+a.height+gap>b.y;
const inside=(p:Point,r:Rect)=>p.x>r.x&&p.x<r.x+r.width&&p.y>r.y&&p.y<r.y+r.height;
export function segmentHitsRect(a:Point,b:Point,r:Rect):boolean{
  if(a.x===b.x)return a.x>r.x&&a.x<r.x+r.width&&Math.max(a.y,b.y)>r.y&&Math.min(a.y,b.y)<r.y+r.height;
  if(a.y===b.y)return a.y>r.y&&a.y<r.y+r.height&&Math.max(a.x,b.x)>r.x&&Math.min(a.x,b.x)<r.x+r.width;
  return true;
}
export function absoluteRectangles(nodes:GeometryNode[]):Rect[]{
  const byId=new Map(nodes.map(n=>[n.id,n]));
  return nodes.map(node=>{let{x,y}=node.position;let parent=node.parentId;const seen=new Set([node.id]);
    while(parent&&!seen.has(parent)){seen.add(parent);const n=byId.get(parent);if(!n)break;x+=n.position.x;y+=n.position.y;parent=n.parentId;}
    return{id:node.id,x,y,width:node.width||0,height:node.height||0};});
}
export function routingObstacles(nodes:GeometryNode[]):Rect[]{
  const rects=absoluteRectangles(nodes);return rects.map((r,i)=>nodes[i].type==='zone'?{...r,height:40}:r);
}
const length=(a:Point,b:Point)=>Math.abs(a.x-b.x)+Math.abs(a.y-b.y);
function simplify(points:Point[]):Point[]{
  const result:Point[]=[];for(const p of points){if(result.length&&same(result.at(-1)!,p))continue;
    while(result.length>1){const a=result.at(-2)!,b=result.at(-1)!;if((a.x===b.x&&b.x===p.x)||(a.y===b.y&&b.y===p.y))result.pop();else break;}result.push(p);}return result;
}
const path=(points:Point[])=>points.map((p,i)=>`${i?'L':'M'}${p.x},${p.y}`).join(' ');
const center=(r:Rect):Point=>({x:r.x+r.width/2,y:r.y+r.height/2});
function sides(a:Rect,b:Rect):[Side,Side]{
  const ac=center(a),bc=center(b),dx=bc.x-ac.x,dy=bc.y-ac.y;
  if(Math.abs(dx)<Math.min(a.width,b.width)*.6)return dy>=0?['bottom','top']:['top','bottom'];
  if(Math.abs(dy)<Math.min(a.height,b.height)*.6)return dx>=0?['right','left']:['left','right'];
  return Math.abs(dx)>Math.abs(dy)*.7?(dx>=0?['right','left']:['left','right']):(dy>=0?['bottom','top']:['top','bottom']);
}
function port(r:Rect,side:Side,index:number,count:number):Point{
  const horizontal=side==='top'||side==='bottom',span=horizontal?r.width:r.height;
  const offset=span/2+(index-(count-1)/2)*Math.min(18,(span-48)/Math.max(1,count-1));
  return horizontal?{x:r.x+offset,y:r.y+(side==='bottom'?r.height:0)}:{x:r.x+(side==='right'?r.width:0),y:r.y+offset};
}
function stub(p:Point,side:Side):Point{return{x:p.x+(side==='right'?STUB:side==='left'?-STUB:0),y:p.y+(side==='bottom'?STUB:side==='top'?-STUB:0)};}
class Heap{
  values:{key:number;cost:number}[]=[];
  push(value:{key:number;cost:number}){let i=this.values.push(value)-1;while(i){const p=(i-1)>>1;if(this.values[p].cost<=value.cost)break;this.values[i]=this.values[p];i=p;}this.values[i]=value;}
  pop(){const first=this.values[0],last=this.values.pop()!;if(this.values.length){let i=0;while(i*2+1<this.values.length){let c=i*2+1;if(c+1<this.values.length&&this.values[c+1].cost<this.values[c].cost)c++;if(this.values[c].cost>=last.cost)break;this.values[i]=this.values[c];i=c;}this.values[i]=last;}return first;}
}
type Segment={a:Point;b:Point};
function segmentPenalty(a:Point,b:Point,previous:Segment[]):number{
  let cost=0;for(const s of previous){const h=a.y===b.y,sh=s.a.y===s.b.y;
    if(h===sh){const distance=h?Math.abs(a.y-s.a.y):Math.abs(a.x-s.a.x);if(distance>=7)continue;
      const overlap=h?Math.min(Math.max(a.x,b.x),Math.max(s.a.x,s.b.x))-Math.max(Math.min(a.x,b.x),Math.min(s.a.x,s.b.x)):
        Math.min(Math.max(a.y,b.y),Math.max(s.a.y,s.b.y))-Math.max(Math.min(a.y,b.y),Math.min(s.a.y,s.b.y));
      if(overlap>0)cost+=overlap*(distance<1?12:2)+32;
    }else{const v=h?s:{a,b},line=h?{a,b}:s;
      if(v.a.x>Math.min(line.a.x,line.b.x)&&v.a.x<Math.max(line.a.x,line.b.x)&&line.a.y>Math.min(v.a.y,v.b.y)&&line.a.y<Math.max(v.a.y,v.b.y))cost+=42;}
  }return cost;
}
/** Rectilinear visibility-grid A*: edges are tested against every inflated card
 * and group title. Existing paths incur overlap/crossing costs, not fake joins. */
function route(start:Point,end:Point,obstacles:Rect[],previous:Segment[]):Point[]|null{
  if(obstacles.some(r=>inside(start,r)||inside(end,r)))return null;
  const xs=new Set([start.x,end.x]),ys=new Set([start.y,end.y]);
  for(const r of obstacles){xs.add(r.x);xs.add(r.x+r.width);ys.add(r.y);ys.add(r.y+r.height);}
  for(const s of previous){if(s.a.x===s.b.x){xs.add(s.a.x-8);xs.add(s.a.x+8);}else{ys.add(s.a.y-8);ys.add(s.a.y+8);}}
  const all=[start,end,...obstacles.flatMap(r=>[{x:r.x,y:r.y},{x:r.x+r.width,y:r.y+r.height}])];
  xs.add(Math.min(...all.map(p=>p.x))-36);xs.add(Math.max(...all.map(p=>p.x))+36);
  ys.add(Math.min(...all.map(p=>p.y))-36);ys.add(Math.max(...all.map(p=>p.y))+36);
  const xx=[...xs].sort((a,b)=>a-b),yy=[...ys].sort((a,b)=>a-b),w=xx.length,h=yy.length;
  const point=(i:number):Point=>({x:xx[i%w],y:yy[Math.floor(i/w)]});
  const source=yy.indexOf(start.y)*w+xx.indexOf(start.x),target=yy.indexOf(end.y)*w+xx.indexOf(end.x);
  const distances=new Map<number,number>(),parent=new Map<number,number>(),heap=new Heap(),blocked=new Map<number,boolean>();
  const valid=(i:number)=>{if(!blocked.has(i))blocked.set(i,!obstacles.some(r=>inside(point(i),r)));return blocked.get(i)!;};
  for(const orientation of[0,1]){const key=source*2+orientation;distances.set(key,0);heap.push({key,cost:length(start,end)});}
  let found=-1;
  while(heap.values.length){const state=heap.pop(),index=Math.floor(state.key/2),orientation=state.key%2,a=point(index),g=distances.get(state.key)!;
    if(state.cost>g+length(a,end)+.01)continue;if(index===target){found=state.key;break;}
    const col=index%w,row=Math.floor(index/w);
    for(const[next,d]of[[col?index-1:-1,0],[col+1<w?index+1:-1,0],[row?index-w:-1,1],[row+1<h?index+w:-1,1]]){
      if(next<0||!valid(next))continue;const b=point(next);if(obstacles.some(r=>segmentHitsRect(a,b,r)))continue;
      const key=next*2+d,cost=g+length(a,b)+(orientation===d?0:24)+segmentPenalty(a,b,previous);
      if(cost<(distances.get(key)??Infinity)){distances.set(key,cost);parent.set(key,state.key);heap.push({key,cost:cost+length(b,end)});}
    }
  }
  if(found<0)return null;const result:Point[]=[];let key:number|undefined=found;while(key!==undefined){result.push(point(Math.floor(key/2)));key=parent.get(key);}return simplify(result.reverse());
}
function labelLines(text:string):string[]{
  const words=text.split(/\s+/),lines:string[]=[];let line='';for(const word of words){if(line&&`${line} ${word}`.length>28){lines.push(line);line=word;}else line+=(line?' ':'')+word;}if(line)lines.push(line);return lines;
}
function labelAlong(points:Point[],lines:string[],obstacles:Rect[],placed:Rect[],previous:Segment[]):Rect|undefined{
  if(!lines.length)return;const width=Math.max(...lines.map(l=>l.length))*5.7+14,height=lines.length*12+8;
  const candidates:{box:Rect;score:number}[]=[];
  for(let i=1;i<points.length;i++){const a=points[i-1],b=points[i],horizontal=a.y===b.y;
    if(length(a,b)<(horizontal?width+12:height+14))continue;
    for(const ratio of[.5,.32,.68]){const p={x:a.x+(b.x-a.x)*ratio,y:a.y+(b.y-a.y)*ratio};
      for(const sign of[-1,1]){const box={x:p.x-width/2+(horizontal?0:sign*(width/2+7)),y:p.y-height/2+(horizontal?sign*(height/2+5):0),width,height};
        if(obstacles.some(r=>rectanglesOverlap(box,r,3))||placed.some(r=>rectanglesOverlap(box,r,7))||previous.some(s=>segmentHitsRect(s.a,s.b,inflate(box,3))))continue;
        // A label may sit beside its own segment, but not cover another bend.
        if(points.some((q,j)=>j>0&&j!==i&&segmentHitsRect(points[j-1],q,inflate(box,2))))continue;
        candidates.push({box,score:Math.abs(ratio-.5)*30+(horizontal?0:20)-Math.min(length(a,b),450)/20});}
    }
  }return candidates.sort((a,b)=>a.score-b.score)[0]?.box;
}
export function routeConnections(nodes:GeometryNode[],links:RoutingLink[]):RoutedLink[]{
  const rectangles=absoluteRectangles(nodes),byId=new Map(rectangles.map(r=>[r.id!,r]));
  const cardObstacles=routingObstacles(nodes),baseObstacles=cardObstacles.map(r=>inflate(r,CLEARANCE));
  const ports=new Map<string,{edge:string;end:'source'|'target';other:Point}[]>(),sideById=new Map<string,[Side,Side]>();
  const usable=links.filter(e=>byId.has(e.source)&&byId.has(e.target));
  for(const e of usable){const a=byId.get(e.source)!,b=byId.get(e.target)!,ss=sides(a,b);sideById.set(e.id,ss);
    for(const[end,id,side,other]of[['source',e.source,ss[0],center(b)],['target',e.target,ss[1],center(a)]]as const){const key=`${id}:${side}`;ports.set(key,[...(ports.get(key)||[]),{edge:e.id,end,other}]);}}
  for(const[key,list]of ports){const side=key.split(':').at(-1);list.sort((a,b)=>(side==='left'||side==='right'?a.other.y-b.other.y:a.other.x-b.other.x)||a.edge.localeCompare(b.edge));}
  // Labels must not strand an endpoint belonging to a later connection.
  const terminalLanes:Rect[]=[];
  for(const[key,list]of ports){const split=key.lastIndexOf(':'),rect=byId.get(key.slice(0,split))!,side=key.slice(split+1) as Side;
    list.forEach((_,index)=>{const a=port(rect,side,index,list.length),b=stub(a,side);terminalLanes.push({x:Math.min(a.x,b.x)-5,y:Math.min(a.y,b.y)-5,width:Math.abs(a.x-b.x)+10,height:Math.abs(a.y-b.y)+10});});}
  const previous:Segment[]=[],placed:Rect[]=[],result:RoutedLink[]=[];
  const sorted=[...usable].sort((a,b)=>{const priority=(e:RoutingLink)=>e.kind==='telemetry'?3:e.kind==='control'?2:e.kind==='request'?1:0;return priority(a)-priority(b)||length(center(byId.get(a.source)!),center(byId.get(a.target)!))-length(center(byId.get(b.source)!),center(byId.get(b.target)!))||a.id.localeCompare(b.id);});
  for(const e of sorted){const source=byId.get(e.source)!,target=byId.get(e.target)!,[sourceSide,targetSide]=sideById.get(e.id)!;
    const endpoint=(id:string,side:Side,end:'source'|'target')=>{const list=ports.get(`${id}:${side}`)!;return port(byId.get(id)!,side,list.findIndex(v=>v.edge===e.id&&v.end===end),list.length);};
    const a=endpoint(e.source,sourceSide,'source'),b=endpoint(e.target,targetSide,'target'),s=stub(a,sourceSide),t=stub(b,targetSide);
    const obstacles=[...baseObstacles,...placed.map(r=>inflate(r,6))];
    let middle=route(s,t,obstacles,previous),points=middle?simplify([a,...middle,b]):[],lines=labelLines(e.label||''),labelBox=labelAlong(points,lines,[...cardObstacles,...terminalLanes],placed,previous);
    if(lines.length&&!labelBox){
      // A crowded manual layout may lack a long enough free segment. Reserve a
      // labelled outer lane and route to it; never put text behind a card.
      const width=Math.max(...lines.map(l=>l.length))*5.7+14,height=lines.length*12+8;
      const minX=Math.min(...rectangles.map(r=>r.x)),maxX=Math.max(...rectangles.map(r=>r.x+r.width));
      const minY=Math.min(...rectangles.map(r=>r.y)),maxY=Math.max(...rectangles.map(r=>r.y+r.height));
      outer:for(let lane=0;lane<12;lane++)for(const top of[true,false]){
        const y=(top?minY-42:maxY+42)+(top?-1:1)*lane*(height+20),x=(center(source).x+center(target).x)/2;
        const left={x:Math.max(minX-20,Math.min(x-width/2-14,maxX-width-10)),y},right={x:Math.max(minX-20,Math.min(x-width/2-14,maxX-width-10))+width+28,y};
        const box={x:left.x+14,y:y-height-5,width,height};
        if([...cardObstacles,...terminalLanes].some(r=>rectanglesOverlap(box,r,3))||placed.some(r=>rectanglesOverlap(box,r,8))||previous.some(seg=>segmentHitsRect(seg.a,seg.b,inflate(box,3))))continue;
        const reserved=[...obstacles,inflate(box,3)],first=route(s,left,reserved,previous),last=route(right,t,reserved,previous);
        if(!first||!last||reserved.some(r=>segmentHitsRect(left,right,r)))continue;
        points=simplify([a,...first,right,...last.slice(1),b]);labelBox=box;break outer;
      }
    }
    // Overlapping user-dragged cards have no truthful unobstructed connection.
    // The graph rejects those drops; this state is retained for static callers.
    if(!points.length)continue;
    if(labelBox)placed.push(labelBox);
    for(let i=1;i<points.length;i++)previous.push({a:points[i-1],b:points[i]});
    result.push({...e,points,path:path(points),sourceSide,targetSide,labelBox,labelLines:labelBox?lines:[]});
  }return result;
}
