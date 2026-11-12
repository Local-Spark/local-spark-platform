'use strict';
// Synthetic signals only. No customer media, network, video render or persistent assets.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const {buildAudioArgs, parseAudioMetrics} = require('../../assets/motion_html_renderer/audio.cjs');

const base = (asset_id, role, start, end, offset, volume, fadeIn=0, fadeOut=0) =>
  ({asset_id, role, trim_start_ms:start, trim_end_ms:end, offset_ms:offset, volume,
    fade_in_ms:fadeIn, fade_out_ms:fadeOut});
const source = base('assets/source.mp4','original',0,3000,0,1);
const music = base('assets/music.wav','music',0,2500,200,0.5,250,250);
const effect = base('assets/effect.wav','effect',0,120,600,0.2,10,10);
const ducking = {threshold:0.02, ratio:8, attack_ms:10, release_ms:80};
const plan = {version:'motion-audio-v2',mode:'mix',tracks:[source,music,effect],ducking};

test('v2 uses fades and sidechain only on music while retaining an unmodified original branch', () => {
  const assets = new Map([['assets/source.mp4','/fixtures/source.wav'],['assets/music.wav','/fixtures/music.wav'],
    ['assets/effect.wav','/fixtures/effect.wav']]);
  const audio = buildAudioArgs(plan,assets,3000);
  assert.match(audio.filter,/\[1:a\]atrim=start=0:duration=3,asetpts=PTS-STARTPTS,volume=1,adelay=0:all=1\[t0\]/);
  assert.match(audio.filter,/afade=t=in:st=0:d=0\.25,afade=t=out:st=2\.25:d=0\.25,adelay=200/);
  assert.match(audio.filter,/\[t0\]asplit=2\[voice\]\[key0\]/);
  assert.match(audio.filter,/\[t1\]\[key0\]sidechaincompress=.*\[duck0\]/);
  assert.match(audio.filter,/\[voice\]\[duck0\]\[t2\]amix=/);
  const invalid = [
    {...plan,tracks:[{...source,volume:0.9},music]},
    {...plan,tracks:[source,{...music,asset_id:'assets/source.mp4'}]},
    {...plan,tracks:[source,source,music]},
    {...plan,tracks:[music,effect]},
    {...plan,tracks:[source,{...music,fade_in_ms:2000,fade_out_ms:1000}]},
    {...plan,ducking:{...ducking,threshold:NaN}},
    {...plan,ducking:{...ducking,ratio:21}},
  ];
  for (const bad of invalid) assert.throws(()=>buildAudioArgs(bad,assets,3000));
});

function wav(samples, rate) {
  const data = Buffer.alloc(44+samples.length*2);
  data.write('RIFF',0); data.writeUInt32LE(data.length-8,4); data.write('WAVEfmt ',8);
  data.writeUInt32LE(16,16); data.writeUInt16LE(1,20); data.writeUInt16LE(1,22);
  data.writeUInt32LE(rate,24); data.writeUInt32LE(rate*2,28); data.writeUInt16LE(2,32);
  data.writeUInt16LE(16,34); data.write('data',36); data.writeUInt32LE(samples.length*2,40);
  samples.forEach((value,i)=>data.writeInt16LE(Math.round(Math.max(-1,Math.min(1,value))*32767),44+i*2));
  return data;
}
function projection(samples, rate, hz, start, end) {
  let result=0, count=0;
  for (let i=Math.round(start*rate);i<Math.round(end*rate);i++) {
    result += samples.readFloatLE(i*4)*Math.sin(2*Math.PI*hz*i/rate); count++;
  }
  return 2*result/count;
}

test('synthetic audio verifies fades, offsets, ducking, original contribution and sample peak', () => {
  const local = path.resolve(__dirname,'../../../.local/tools/motion-lab/bin/ffmpeg');
  const executable = process.env.MOTION_TEST_FFMPEG || (fs.existsSync(local) ? local : 'ffmpeg');
  const probe=spawnSync(executable,['-version'],{stdio:'ignore'});
  if (probe.error || probe.status!==0) throw new Error('FFmpeg is required for the synthetic audio test');
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'motion-audio-synthetic-'));
  try {
    const rate=48000, count=rate*3;
    const samples=(fn)=>Array.from({length:count},(_,i)=>fn(i/rate));
    const voice=samples(t=>t>=1&&t<2?0.18*Math.sin(2*Math.PI*1000*t):0);
    const bed=samples(t=>0.2*Math.sin(2*Math.PI*200*t));
    const click=samples(t=>t<0.12?0.15*Math.sin(2*Math.PI*2000*t):0);
    const paths=['source.wav','music.wav','effect.wav'].map(name=>path.join(dir,name));
    [voice,bed,click].forEach((values,i)=>fs.writeFileSync(paths[i],wav(values,rate)));
    const assets=new Map([['assets/source.mp4',paths[0]],['assets/music.wav',paths[1]],['assets/effect.wav',paths[2]]]);
    const render = value => {
      const mix=buildAudioArgs(value,assets,3000);
      const args=['-nostdin','-hide_banner','-v','error','-f','lavfi','-i','anullsrc=r=48000:cl=mono',
        ...mix.inputs,'-filter_complex',mix.filter,'-map','[a]','-vn','-ar','48000','-ac','1','-f','f32le','pipe:1'];
      const result=spawnSync(executable,args,{maxBuffer:rate*3*4+65536,timeout:15000});
      assert.equal(result.status,0,result.stderr.toString());
      assert.equal(result.stdout.length,rate*3*4);
      return result.stdout;
    };
    const mixed=render(plan), unducked=render({...plan,ducking:null});
    assert.ok(Math.abs(projection(mixed,rate,200,0.02,0.18))<0.001);
    assert.ok(projection(mixed,rate,200,0.23,0.30) < projection(mixed,rate,200,0.7,0.9)*0.5);
    assert.ok(projection(mixed,rate,200,1.3,1.7) < projection(unducked,rate,200,1.3,1.7)*0.6);
    assert.ok(Math.abs(projection(mixed,rate,1000,1.3,1.7)-0.18)<0.003);
    assert.ok(projection(mixed,rate,2000,0.62,0.70)>0.02);
    assert.ok(Math.abs(projection(mixed,rate,2000,0.8,0.9))<0.002);
    let peak=0;for(let i=0;i<count;i++)peak=Math.max(peak,Math.abs(mixed.readFloatLE(i*4)));
    assert.ok(peak>0 && peak<1);
    const measured=spawnSync(executable,['-nostdin','-hide_banner','-v','info','-f','f32le','-ar','48000',
      '-ac','1','-i','pipe:0','-af','ebur128=peak=sample','-f','null','-'],
      {input:mixed,maxBuffer:2*1024*1024,timeout:15000});
    assert.equal(measured.status,0);
    const stats=parseAudioMetrics(measured.stderr.toString());
    assert.ok(Number.isFinite(stats.integrated_lufs));
    assert.ok(stats.sample_peak_dbfs<0);
    assert.equal(stats.peak_kind,'sample');
  } finally { fs.rmSync(dir,{recursive:true,force:true}); }
});
