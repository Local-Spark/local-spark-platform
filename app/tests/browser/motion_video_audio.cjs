// Real FFmpeg with synthetic PCM only. No MP4, provider or customer asset.
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),{execFileSync}=require('node:child_process');
const {buildAudioArgs}=require('../../assets/motion_html_renderer/audio.cjs');
test('FFmpeg preserves EDL waveform and attenuates music under source audio',()=>{
 const dir=fs.mkdtempSync(path.join(os.tmpdir(),'video-audio-c-')),ffmpeg=process.env.FFMPEG_PATH||'ffmpeg';
 try{
  const source=path.join(dir,'source.wav'),music=path.join(dir,'music.wav');
  for(const [file,expr] of [[source,'if(lt(t,3),0.25*sin(2*PI*440*t),0.25*sin(2*PI*880*t))'],[music,'0.2*sin(2*PI*110*t)']])
   execFileSync(ffmpeg,['-hide_banner','-loglevel','error','-f','lavfi','-i',`aevalsrc=${expr.replaceAll(',','\\,')}:s=16000:d=6`,'-c:a','pcm_s16le',file]);
  const original=(start,offset)=>({asset_id:'assets/source.mp4',role:'original',trim_start_ms:start,trim_end_ms:start+3000,offset_ms:offset,volume:1,fade_in_ms:0,fade_out_ms:0});
  const plan={version:'motion-audio-v3',mode:'mix',tracks:[original(3000,0),original(0,3000)],ducking:null};
  const assets=new Map([['assets/source.mp4',source],['assets/music.mp3',music]]);
  function render(p){const a=buildAudioArgs(p,assets,6000);const b=execFileSync(ffmpeg,['-hide_banner','-loglevel','error','-f','lavfi','-i','color=s=16x16:d=6',...a.inputs,'-filter_complex',a.filter,'-map','[a]','-ac','1','-ar','16000','-f','f32le','pipe:1']);return new Float32Array(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength));}
  const voice=render(plan);assert.equal(voice.length,96000);
  const peak=Math.max(...voice.subarray(16000,32000));assert.ok(peak>.249&&peak<.251);
  const crossings=(start,end)=>{let n=0;for(let i=start+1;i<end;i++)if(voice[i]>=0&&voice[i-1]<0)n++;return n;};
  assert.ok(Math.abs(crossings(16000,32000)-880)<=1);assert.ok(Math.abs(crossings(64000,80000)-440)<=1);
  plan.tracks.push({asset_id:'assets/music.mp3',role:'music',trim_start_ms:0,trim_end_ms:6000,offset_ms:0,volume:.18,fade_in_ms:100,fade_out_ms:200});
  const plain=render(plan);plan.ducking={threshold:.02,ratio:6,attack_ms:15,release_ms:250};const duck=render(plan);
  const energy=a=>{let v=0;for(let i=16000;i<80000;i++)v+=(a[i]-voice[i])**2;return v/64000;};
  assert.ok(energy(duck)<energy(plain)*.4);assert.ok(Math.max(...duck.subarray(16000,32000))<1);
 }finally{fs.rmSync(dir,{recursive:true,force:true});}
});
