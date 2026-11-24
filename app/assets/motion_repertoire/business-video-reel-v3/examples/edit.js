async function videoEditSeek(video, scene, ms, width, height) {
  const edit=scene.video_layout.edit;
  const p=(ms-scene.start_ms)/(scene.end_ms-scene.start_ms);
  const value=k=>edit.crop_from[k]+(edit.crop_to[k]-edit.crop_from[k])*p;
  video.id=scene.video_layout.video_element_id;
  Object.assign(video.style,{position:'absolute',left:'0px',top:'0px',width:width+'px',height:height+'px',
    objectFit:'cover',objectPosition:'50% 50%',transformOrigin:'50% 50%',
    transform:`translate(${value('x')*width}px,${value('y')*height}px) scale(${value('scale')})`});
  const time=Math.min(video.duration*1000-1,edit.source_out_ms-1,edit.source_in_ms+ms-scene.start_ms)/1000;
  if(Math.abs(video.currentTime-time)>.0001) {
    await new Promise((resolve,reject)=>{
      const cleanup=()=>{video.removeEventListener('seeked',done);video.removeEventListener('error',error);};
      const done=()=>{cleanup();resolve();},error=()=>{cleanup();reject(new Error('MOTION_VIDEO_EDIT_NOT_EXECUTED'));};
      video.addEventListener('seeked',done,{once:true});video.addEventListener('error',error,{once:true});
      video.currentTime=time;
    });
  }
}
