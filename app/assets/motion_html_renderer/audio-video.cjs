'use strict';
// V3: original intervals are server-validated against the pinned EDL. Only music is ducked.
function buildVideoAudio(plan, assets, durationMs, buildLegacy) {
  const invalid=()=>{throw new Error('invalid motion audio plan');};
  if(!plan||Object.keys(plan).sort().join(',')!=='ducking,mode,tracks,version'||plan.mode!=='mix'||
     !Array.isArray(plan.tracks)||!plan.tracks.length) invalid();
  const raw=[], originals=[], music=[], filters=[], labels=[];
  const seconds=ms=>(ms/1000).toFixed(3);
  let end=0;
  for(const [i,t] of plan.tracks.entries()) {
    if(Object.keys(t).sort().join(',')!=='asset_id,fade_in_ms,fade_out_ms,offset_ms,role,trim_end_ms,trim_start_ms,volume'||
      !['original','music','effect'].includes(t.role)||
      !Number.isSafeInteger(t.fade_in_ms)||!Number.isSafeInteger(t.fade_out_ms)||t.fade_in_ms<0||t.fade_out_ms<0||
      t.fade_in_ms+t.fade_out_ms>t.trim_end_ms-t.trim_start_ms) invalid();
    if(t.role==='original') {
      if(i!==originals.length||t.asset_id!=='assets/source.mp4'||t.volume!==1||t.fade_in_ms||t.fade_out_ms||t.offset_ms!==end) invalid();
      originals.push(i);end=t.offset_ms+t.trim_end_ms-t.trim_start_ms;
    } else if(t.asset_id==='assets/source.mp4') invalid();
    if(t.role==='music') music.push(i);
    raw.push({asset_id:t.asset_id,offset_ms:t.offset_ms,trim_start_ms:t.trim_start_ms,trim_end_ms:t.trim_end_ms,volume:t.volume});
  }
  const checked=buildLegacy({mode:'mix',tracks:raw},assets,durationMs);
  for(const [i,t] of plan.tracks.entries()) {
    const duration=t.trim_end_ms-t.trim_start_ms;
    const fades=(t.fade_in_ms?`,afade=t=in:st=0:d=${seconds(t.fade_in_ms)}`:'')+
      (t.fade_out_ms?`,afade=t=out:st=${seconds(duration-t.fade_out_ms)}:d=${seconds(t.fade_out_ms)}`:'');
    filters.push(`[${i+1}:a]atrim=start=${seconds(t.trim_start_ms)}:duration=${seconds(duration)},asetpts=PTS-STARTPTS,volume=${t.volume.toFixed(6)}${fades},adelay=${t.offset_ms}:all=1[t${i}]`);
    if(t.role!=='original') labels.push(`t${i}`);
  }
  if(originals.length) {
    filters.push(originals.map(i=>`[t${i}]`).join('')+`amix=inputs=${originals.length}:duration=longest:normalize=0,apad,atrim=duration=${seconds(durationMs)}[original]`);
    labels.unshift('original');
  }
  if(plan.ducking!==null) {
    const d=plan.ducking;
    if(!d||Object.keys(d).sort().join(',')!=='attack_ms,ratio,release_ms,threshold'||!originals.length||!music.length||
      !Number.isFinite(d.threshold)||d.threshold<.00097563||d.threshold>1||!Number.isFinite(d.ratio)||d.ratio<1||d.ratio>20||
      !Number.isSafeInteger(d.attack_ms)||d.attack_ms<1||d.attack_ms>2000||
      !Number.isSafeInteger(d.release_ms)||d.release_ms<5||d.release_ms>9000) invalid();
    filters.push(`[original]asplit=${music.length+1}[voice]`+music.map(i=>`[key${i}]`).join(''));labels[0]='voice';
    for(const i of music) {
      filters.push(`[t${i}][key${i}]sidechaincompress=threshold=${d.threshold.toFixed(8)}:ratio=${d.ratio.toFixed(6)}:attack=${d.attack_ms}:release=${d.release_ms}[duck${i}]`);
      labels[labels.indexOf(`t${i}`)]=`duck${i}`;
    }
  }
  filters.push(labels.map(l=>`[${l}]`).join('')+`amix=inputs=${labels.length}:duration=longest:normalize=0,atrim=duration=${seconds(durationMs)}[a]`);
  return {inputs:checked.inputs,filter:filters.join(';'),mapArgs:['-map','0:v:0','-map','[a]']};
}
module.exports={buildVideoAudio};
