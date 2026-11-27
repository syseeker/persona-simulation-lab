import type {Node} from '@xyflow/svelte';

const card=(id:string,x:number,y:number,width:number,height:number,parentId?:string):Node=>({
  id,type:'component',position:{x,y},width,height,style:`width:${width}px;height:${height}px`,parentId,
  ...(parentId?{extent:'parent' as const}:{}),dragHandle:'.node-drag-handle',deletable:false,connectable:false,zIndex:2,data:{}
});
const zone=(id:string,title:string,x:number,y:number,width:number,height:number,kind:string,caption=''):Node=>({
  id,type:'zone',position:{x,y},width,height,style:`width:${width}px;height:${height}px`,
  dragHandle:'.zone-drag-handle',selectable:false,deletable:false,connectable:false,zIndex:0,
  data:{title,caption,kind,overlay:kind==='deployment'}
});

/** Saved positions remain authoritative. These defaults reserve space between
 * cards for connections, rather than using card interiors as routing lanes. */
export function integrationNodes(detailed:boolean,managed:boolean):Node[]{
  if(!detailed)return[
    zone('zone-sandbox','OpenShell · sandboxed advisor and course tools',620,-32,344,700,'deployment','Host simulator and model gateway stay outside'),
    ...(managed?[zone('zone-caller','Host caller · managed session',620,-232,344,172,'runtime','Checks stay outside OpenShell')]:[]),
    card('person',0,0,250,177),card('situation-block',0,248,250,177),card('learner',310,106,250,194),
    card('advisor',32,214,280,190,'zone-sandbox'),card('courses',32,460,280,188,'zone-sandbox'),
    card('guardrails',32,managed?52:64,280,108,managed?'zone-caller':'zone-sandbox'),card('models',1036,174,280,200),
    card('evidence',310,490,250,202),card('openshell',620,742,344,150),card('platform',1036,490,280,202)
  ];
  return[
    zone('zone-inputs','Test inputs and simulated learner',0,0,304,1194,'data'),
    zone('zone-sandbox','OpenShell · sandboxed workload',372,0,604,1076,'deployment','Advisor + selected harness + course tools'),
    ...(managed?[zone('zone-caller','Host caller · managed session',372,-222,604,194,'runtime','Input/output checks outside OpenShell')]:[]),
    zone('zone-models','Host-side model access',1044,0,304,832,'models','Credentials remain here'),
    zone('zone-evidence','Execution evidence and evaluation',1416,0,334,938,'evidence'),
    card('personas',24,68,256,210,'zone-inputs'),card('situation',24,332,256,166,'zone-inputs'),
    card('designer',24,552,256,220,'zone-inputs'),card('usersim',24,850,256,290,'zone-inputs'),
    card('guardrails',32,managed?52:68,540,120,managed?'zone-caller':'zone-sandbox'),card('fabric',32,258,540,264,'zone-sandbox'),
    card('harness',32,608,250,205,'zone-sandbox'),card('mcp',322,608,250,205,'zone-sandbox'),
    card('catalogue',32,898,540,145,'zone-sandbox'),
    card('gateway',24,68,256,206,'zone-models'),card('litellm',24,348,256,160,'zone-models'),
    card('routing',24,582,256,210,'zone-models'),
    card('relay',24,68,286,224,'zone-evidence'),card('records',24,366,286,140,'zone-evidence'),
    card('checks',24,580,286,140,'zone-evidence'),card('helix',24,794,286,120,'zone-evidence'),
    card('openshell',1044,900,304,294),card('platform',1416,1012,334,200)
  ];
}
