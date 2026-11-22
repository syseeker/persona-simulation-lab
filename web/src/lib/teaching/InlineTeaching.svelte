<script lang="ts">
  import {sourceId} from '../lessonArchitecture';
  let {text,context,metadata,scenarioId,conditionId='',onmetadata=(_id:string,_condition?:string)=>{}}:{text:string;context:Record<string,any>|null;metadata:Record<string,any>|null;scenarioId:string;conditionId?:string;onmetadata?:(id:string,condition?:string)=>void}=$props();
  const pieces=$derived(text.split(/(\[\[[\s\S]*?\]\])/g).filter(Boolean).map(part=>{
    const match=/^\[\[([^:]+):([^|]+)\|([^\]]+)\]\]$/.exec(part);
    if(!match)return {text:part};
    const [,kind,id,label]=match;
    if(kind==='call'){
      const ref=context?.sources?.[sourceId(id,scenarioId)||id]||context?.sources?.[id];
      return {text:label,url:ref?.url,reason:'Calling code is not available in the committed repository.'};
    }
    if(kind==='file'){
      const comparisonSelected=conditionId&&!(metadata?.conditions||[]).some((c:Record<string,any>)=>c.id===conditionId&&c.purpose==='baseline');
      const candidates=comparisonSelected?(metadata?.rows||[]).filter((r:Record<string,any>)=>r.condition_id===conditionId).flatMap((r:Record<string,any>)=>r.artifacts||[]):context?.artifacts||[];
      const refs=[...new Map(candidates.filter((a:Record<string,any>)=>(a.path===id||a.path?.split('/').at(-1)?.replace(/^[a-f0-9]{24}-/,'').replace(/\.projection\.(jsonl?|yaml)$/,'.$1')===id)&&a.url).map((a:Record<string,any>)=>[a.url,a])).values()] as Record<string,any>[];
      return {text:label,url:refs.length===1?refs[0].url:undefined,reason:refs.length>1?'More than one record matches; no file was guessed.':'This scenario has no published '+id+'.'};
    }
    if(kind==='cap'||kind==='cap-run'){
      const rows=(metadata?.rows||[]).filter((r:Record<string,any>)=>r.id===id);
      const baseline=metadata?.conditions?.find((c:Record<string,any>)=>c.purpose==='baseline');
      // These two registry entries are explicitly run-owned aggregates, never
      // substitutes for a selected condition's native configuration or result.
      const runAggregate=kind==='cap-run'&&['CAP-SW-01','CAP-SW-02'].includes(id);
      const row=kind==='cap-run'&&!runAggregate?null:conditionId&&!runAggregate?rows.find((r:Record<string,any>)=>r.condition_id===conditionId):rows.find((r:Record<string,any>)=>r.condition_id===baseline?.id)||rows.find((r:Record<string,any>)=>r.condition_purpose==='baseline')||(rows.length===1?rows[0]:null);
      const refs=row?.artifacts?.filter((a:Record<string,any>)=>a.url)||[];
      return {text:label,url:refs.length===1?refs[0].url:undefined,metadata:refs.length>1?id:undefined,
        metadataCondition:runAggregate?row?.condition_id:conditionId,
        reason:row?.status==='not-used'?'This component was not used in the selected condition.':row?.privacy==='private'?'The original includes private simulator or runtime data and is not published.':'No matching public capture is available for this scenario.'};
    }
    if(kind==='url'&&/^https:\/\//.test(id))return {text:label,url:id};
    return {text:label,reason:'The reference is unavailable.'};
  }));
</script>

{#each pieces as piece}{#if piece.url}<a href={piece.url} target="_blank" rel="noreferrer">{piece.text} ↗</a>{:else if piece.metadata}<button class="text-button inline-ref" onclick={()=>onmetadata(piece.metadata!,piece.metadataCondition)} title="Open the matching configuration and result files in Metadata">{piece.text} ↗</button>{:else if piece.reason}<span class="unavailable-reference" title={piece.reason}>{piece.text} <small>(unavailable)</small></span>{:else}{piece.text}{/if}{/each}

<style>.inline-ref{display:inline;padding:0;font:inherit;text-align:left;vertical-align:baseline}.unavailable-reference small{font-size:.9em;color:var(--muted)}</style>
