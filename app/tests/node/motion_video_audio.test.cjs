'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const {buildAudioArgs}=require('../../assets/motion_html_renderer/audio.cjs');
const assets=new Map([['assets/source.mp4','/tmp/source.wav'],['assets/music.mp3','/tmp/music.wav'],['assets/sfx.mp3','/tmp/sfx.wav']]);
function track(role,start=0,end=3000,offset=0){return {asset_id:role==='original'?'assets/source.mp4':role==='music'?'assets/music.mp3':'assets/sfx.mp3',role,trim_start_ms:start,trim_end_ms:end,offset_ms:offset,volume:role==='original'?1:.1,fade_in_ms:0,fade_out_ms:0};}
function plan(){return {version:'motion-audio-v3',mode:'mix',tracks:[track('original',3000,6000),track('original',0,3000,3000),track('music',0,6000)],ducking:{threshold:.02,ratio:6,attack_ms:15,release_ms:250}};}
test('EDL uses source offsets, one original bus and ducks only music',()=>{
 const p=plan(),result=buildAudioArgs(p,assets,6000);
 assert.match(result.filter,/atrim=start=3.000:duration=3.000/);
 assert.match(result.filter,/adelay=3000:all=1/);
 assert.match(result.filter,/\[t0\]\[t1\]amix=inputs=2/);
 assert.match(result.filter,/\[t2\]\[key2\]sidechaincompress/);
 assert.match(result.filter,/\[voice\]\[duck2\]amix/);
 p.tracks[2].fade_in_ms=500;p.tracks[2].fade_out_ms=800;
 p.tracks.push(track('effect',0,200,4000),track('music',0,6000));
 assert.match(buildAudioArgs(p,assets,6000).filter,/afade=t=out:st=5.200:d=0.800/);
 p.ducking=null;assert.doesNotMatch(buildAudioArgs(p,assets,6000).filter,/sidechain/);
 p.tracks=p.tracks.filter(t=>t.role!=='original');assert.doesNotMatch(buildAudioArgs(p,assets,6000).filter,/\[original\]/);
});
test('rejects malformed plans, sources, gains, ordering, fades and duck parameters',()=>{
 const changes=[
  p=>p.extra=1,p=>p.mode='silent',p=>p.tracks=null,p=>p.tracks=[],p=>p.tracks[0].extra=1,
  p=>p.tracks[0].role='other',p=>p.tracks[0].fade_in_ms=.1,p=>p.tracks[0].fade_out_ms=.1,
  p=>p.tracks[0].fade_in_ms=-1,p=>p.tracks[0].fade_out_ms=-1,p=>p.tracks[0].fade_in_ms=4000,
  p=>p.tracks[0].fade_in_ms=1,p=>p.tracks[0].fade_out_ms=1,
  p=>p.tracks[0].asset_id='assets/music.mp3',p=>p.tracks[0].volume=.5,p=>p.tracks[1].offset_ms=2900,
  p=>p.tracks=[p.tracks[2],p.tracks[0]],p=>p.tracks[2].asset_id='assets/source.mp4',
  p=>p.tracks[2].trim_end_ms=7000,p=>p.ducking=undefined,p=>p.ducking.extra=1,
  p=>p.tracks=p.tracks.slice(2),p=>p.tracks=p.tracks.slice(0,2),
  ...['threshold','ratio'].flatMap(k=>[p=>p.ducking[k]=NaN,p=>p.ducking[k]=0,p=>p.ducking[k]=100]),
  ...['attack_ms','release_ms'].flatMap(k=>[p=>p.ducking[k]=.5,p=>p.ducking[k]=0,p=>p.ducking[k]=10000])
 ];
 for(const change of changes){const p=plan();change(p);assert.throws(()=>buildAudioArgs(p,assets,6000),/invalid motion audio plan/);}
});
module.exports={plan,assets};
