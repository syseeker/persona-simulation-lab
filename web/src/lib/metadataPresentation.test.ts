import{describe,it,expect}from'vitest';
import{artifactGroups,moduleRows}from'./metadataPresentation';
import type{MetadataArtifact,MetadataRow}from'./metadataTypes';
const artifact=(change:Partial<MetadataArtifact>={}):MetadataArtifact=>({id:'file',path:'settings.json',sha256:'a'.repeat(64),kind:'redacted-native-configuration',source_kind:'native-effective-configuration',source_schema:'FabricConfig',privacy:'public',status:'exists',direction:'input',...change});
const row=(condition:string,file:MetadataArtifact):MetadataRow=>({id:'CAP-FAB-01',module:'Fabric',steps:[3],operation:'Configure',scenario_ids:['dreamjob'],filenames:['settings.json'],status:'exists',privacy:'public',condition_id:condition,condition_purpose:condition,execution_status:'completed',artifacts:[file]});
describe('condition-aware metadata presentation',()=>{
  it('groups a module once and byte-identical settings while keeping every condition link',()=>{
    const rows=[row('baseline',artifact({url:'https://example.com/baseline'})),row('fixed-candidate',artifact({url:'https://example.com/fixed'}))];
    expect(moduleRows(rows)).toHaveLength(1);const groups=artifactGroups(rows);expect(groups).toHaveLength(1);
    expect(groups[0].uses.map(u=>u.artifact.url)).toEqual(['https://example.com/baseline','https://example.com/fixed']);
  });
  it('does not group by filename, hash alone, or a different source schema',()=>{
    const rows=[row('baseline',artifact()),row('candidate',artifact({sha256:'b'.repeat(64)})),row('schema',artifact({source_schema:'OtherSchema'})),row('role',artifact({source_kind:'application-input'}))];
    expect(artifactGroups(rows)).toHaveLength(4);
  });
  it('retains each result execution even if its public output bytes match',()=>{
    expect(artifactGroups([row('baseline',artifact({direction:'output'})),row('candidate',artifact({direction:'output'}))])).toHaveLength(2);
  });
  it('never turns opaque private-source records into file links',()=>{
    expect(artifactGroups([row('baseline',artifact({privacy:'private',path:undefined}))])).toHaveLength(0);
  });
});
