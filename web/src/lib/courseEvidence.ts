export function returnedFacts(tool:Record<string,any>,detailed=false):string {
    let value=tool.result??tool.output;
    if(typeof value==='string'){try{value=JSON.parse(value);}catch{return 'The result is not a decoded course record; inspect the native tool result.';}}
    if(value?.error)return `The tool returned a domain error: ${value.error}. This is not a successful empty search.`;
    const notes=(items:unknown)=>Array.isArray(items)?items.filter((item:unknown)=>typeof item==='string').join('; '):'';
    const course=(c:Record<string,any>)=>`${c.title||c.id} · ${c.price_max_sgd===null||c.price_max_sgd===undefined?'full fee unknown':`published fee up to S$${c.price_max_sgd}`} · ${c.venue||'venue not specified'}${c.cost_note?`. Cost details: ${c.cost_note}`:''}${notes(c.constraint_notes)?`. Constraint notes: ${notes(c.constraint_notes)}`:''}`;
    if(Array.isArray(value?.matches)){
      const matches=value.matches.length?value.matches.map((m:Record<string,any>)=>`${course(m.course)}${notes(m.confirm)?`. Still to confirm: ${notes(m.confirm)}`:''}${detailed&&notes(m.matched_terms)?`. Search terms matched: ${notes(m.matched_terms)}`:''}`).join('\n\n'):'The search completed successfully and found no matching catalogue entry.';
      const exclusions=Array.isArray(value.excluded)&&value.excluded.length?(detailed?` Other excluded listings: ${value.excluded.map((row:Record<string,any>)=>`${row.id}: ${row.reason}`).join('; ')}.`:` ${value.excluded.length} other listings were excluded by the search constraints.`):'';
      return matches+exclusions;
    }
    if(Array.isArray(value))return value.map(row=>{let c=row?.text??row;if(typeof c==='string'){try{c=JSON.parse(c);}catch{return 'Unparsed comparison item';}}return course(c);}).join('; ');
    if(value?.id)return course(value);
    return 'No recognizable course result was retained; inspect the linked native record.';
  }
