'use strict';
const {test}=require('node:test');
const assert=require('node:assert/strict');
const {buildAudioArgs}=require('./motion_audio.cjs');
const assets=new Map([['voice','/fixtures/voice.wav'],['music','/fixtures/music.ogg'],['click','/fixtures/click.wav']]);
const track=(id,start,end,offset,volume)=>({asset_id:id,trim_start_ms:start,trim_end_ms:end,offset_ms:offset,volume});
const plan={mode:'mix',tracks:[track('voice',0,11180,0,1),track('music',0,11180,0,.08),track('click',0,250,2500,.1),track('click',0,250,7900,.1)]};
test('baseline: four events, independently mapped files and unchanged gains',()=>{
 const a=buildAudioArgs(plan,assets,11180);
 assert.equal(a.inputs.length,16);assert.deepEqual(a.inputs.slice(0,4),['-protocol_whitelist','file,pipe','-i','/fixtures/voice.wav']);
 assert.match(a.filter,/\[1:a\]atrim=start=0:duration=11\.18,asetpts=PTS-STARTPTS,volume=1,adelay=0:all=1\[t0\]/);
 assert.match(a.filter,/\[2:a\].*volume=0\.08/);assert.match(a.filter,/\[3:a\].*volume=0\.1,adelay=2500/);
 assert.match(a.filter,/\[4:a\].*volume=0\.1,adelay=7900/);
 assert.ok(a.filter.endsWith('amix=inputs=4:duration=longest:normalize=0,atrim=duration=11.18[a]'));
 assert.deepEqual(a.mapArgs,['-map','0:v:0','-map','[a]']);
});
test('silent or 16 events',()=>{
 assert.deepEqual(buildAudioArgs({mode:'silent',tracks:[]},assets,1000),{inputs:[],filter:null,mapArgs:['-map','0:v:0','-an']});
 assert.equal(buildAudioArgs({mode:'mix',tracks:Array.from({length:16},()=>track('click',0,100,0,0))},assets,1000).inputs.length,64);
});
test('reject unsupported, malformed and unsafe data without coercion',()=>{
 const bad=[null,{mode:'silent',tracks:[plan.tracks[0]]},{mode:'mix',tracks:[]},{mode:'mix',tracks:Array.from({length:17},()=>plan.tracks[0])},{mode:'mix',tracks:[{...plan.tracks[0],volume:1.1}]},{mode:'mix',tracks:[{...plan.tracks[0],volume:.0000001}]},{mode:'mix',tracks:[{...plan.tracks[0],volume:NaN}]},{mode:'mix',tracks:[{...plan.tracks[0],asset_id:'voice;bad'}]},{mode:'mix',tracks:[{...plan.tracks[0],asset_id:'missing'}]},{mode:'mix',tracks:[{...plan.tracks[0],trim_start_ms:-1}]},{mode:'mix',tracks:[{...plan.tracks[0],trim_start_ms:11180}]},{mode:'mix',tracks:[{...plan.tracks[0],offset_ms:1}]},{mode:'mix',tracks:[{...plan.tracks[0],offset_ms:0.2}]},{mode:'mix',tracks:[{...plan.tracks[0],extra:'filter injection'}]}];
 for(const p of bad)assert.throws(()=>buildAudioArgs(p,assets,11180));
 assert.throws(()=>buildAudioArgs(plan,assets,0));assert.throws(()=>buildAudioArgs(plan,assets,60001));
 assert.throws(()=>buildAudioArgs(plan,new Map([['voice','https://host/a']]),11180));
});
