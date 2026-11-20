/** Highlight only the saved record's attributable boundary, not an invented span join. */
export type RequestFocus = { nodes: string[]; edges: string[]; notice: string };
export function requestFocus(trace: Record<string, any> | null, request: string): RequestFocus | null {
  if (!trace || !request) return null;
  if (request.startsWith('call:')) {
    const record = trace.usage.records.find((r: any) => `call:${r.call}` === request);
    if (!record) return {nodes:[],edges:[],notice:'This model-call identity is missing from the selected run.'};
    return {
      nodes:['gateway','litellm',...(record.selected_model ? ['providers'] : [])],
      edges:['gateway-litellm',...(record.selected_model ? ['litellm-providers'] : [])],
      notice:`Gateway call ${record.call} · ${record.role} · ${record.status}. Native Relay span correlation is not assumed.`
    };
  }
  if (request.startsWith('tool:')) {
    const record = trace.tools.find((r: any) => `tool:${r.scope_uuid}` === request);
    if (!record) return {nodes:[],edges:[],notice:'This native tool identity is missing from the selected run.'};
    return {nodes:['mcp','relay'],edges:['mcp-relay'],notice:`Native Relay tool ${record.name} · ${record.status} · ${record.scope_uuid}`};
  }
  if (request.startsWith('turn:')) {
    const record = trace.conversation.find((r: any) => r.role === 'user' && `turn:${r.turn}` === request);
    return record ? {nodes:['usersim','fabric','records'],edges:['usersim-fabric','usersim-records'],
      notice:`Saved public turn ${record.turn}. Model and tool records remain separately attributable.`}
      : {nodes:[],edges:[],notice:'This public turn is missing from the selected run.'};
  }
  return {nodes:[],edges:[],notice:'Unsupported saved request identity.'};
}
