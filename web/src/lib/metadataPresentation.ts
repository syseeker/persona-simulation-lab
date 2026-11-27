import type{MetadataArtifact,MetadataRow}from'./metadataTypes';

export type ArtifactUse={artifact:MetadataArtifact;conditionId:string|null;purpose:string|null};
export type ArtifactGroup={key:string;uses:ArtifactUse[]};
/** A repeated filename is not proof of shared content. Only byte-identical
 * publications with the same representation and original schema are grouped. */
export function artifactGroups(rows:MetadataRow[]):ArtifactGroup[]{
  const groups=new Map<string,ArtifactGroup>();
  for(const row of rows)for(const artifact of row.artifacts){
    if(artifact.privacy==='private')continue;
    const sharedSettings=artifact.direction==='input'||(!artifact.direction&&artifact.source_kind==='native-effective-configuration');
    const key=[artifact.sha256,artifact.kind,artifact.source_kind||'',artifact.source_schema||'',sharedSettings?'shared':row.condition_id||''].join(':');
    const group=groups.get(key)||{key,uses:[]};
    if(!group.uses.some(use=>use.conditionId===row.condition_id&&use.artifact.path===artifact.path))group.uses.push({artifact,conditionId:row.condition_id,purpose:row.condition_purpose});
    groups.set(key,group);
  }
  return[...groups.values()];
}
export function moduleRows(rows:MetadataRow[]):{id:string;rows:MetadataRow[]}[]{
  const groups=new Map<string,MetadataRow[]>();for(const row of rows)groups.set(row.id,[...(groups.get(row.id)||[]),row]);
  return[...groups].map(([id,rows])=>({id,rows}));
}
