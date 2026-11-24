function installVideoEditV1(plan) {
  const original = window.seek;
  const fail = () => { throw new Error('MOTION_VIDEO_EDIT_NOT_EXECUTED'); };
  window.seek = async function(ms) {
    if (!Number.isFinite(ms) || ms < 0 || ms > plan.duration_ms) fail();
    await original.call(window, ms);
    const scene = [...plan.scenes].reverse().find(s => s.start_ms <= ms);
    const edit = scene.video_layout.edit;
    const nodes = document.querySelectorAll(`[id="${scene.video_layout.video_element_id}"]`);
    if (nodes.length !== 1) fail();
    const video = nodes[0], style = getComputedStyle(video);
    const p = (ms - scene.start_ms) / (scene.end_ms - scene.start_ms);
    const value = k => edit.crop_from[k] + (edit.crop_to[k] - edit.crop_from[k]) * p;
    const m = new DOMMatrixReadOnly(style.transform), rect = video.getBoundingClientRect();
    const expected = Math.min(video.duration * 1000 - 1, edit.source_out_ms - 1, edit.source_in_ms + ms - scene.start_ms) / 1000;
    if (video.seeking || !Number.isFinite(video.currentTime) || Math.abs(video.currentTime - expected) > .002 ||
        !Number.isFinite(video.duration) || video.duration * 1000 + 34 < edit.source_out_ms ||
        !m.is2D || Math.abs(m.a - value('scale')) > .0001 || Math.abs(m.d - m.a) > .0001 ||
        Math.abs(m.b) > .0001 || Math.abs(m.c) > .0001 ||
        Math.abs(m.e - value('x') * innerWidth) > .01 || Math.abs(m.f - value('y') * innerHeight) > .01 ||
        style.position !== 'absolute' || parseFloat(style.left) !== 0 || parseFloat(style.top) !== 0 ||
        Math.abs(parseFloat(style.width) - innerWidth) > .01 || Math.abs(parseFloat(style.height) - innerHeight) > .01 ||
        Math.abs(rect.left - innerWidth * ((1-value('scale'))/2 + value('x'))) > .02 ||
        Math.abs(rect.top - innerHeight * ((1-value('scale'))/2 + value('y'))) > .02 ||
        Math.abs(rect.width - innerWidth * value('scale')) > .02 || Math.abs(rect.height - innerHeight * value('scale')) > .02 ||
        style.objectPosition !== '50% 50%' || style.transformOrigin !== `${innerWidth / 2}px ${innerHeight / 2}px`) fail();
    // Ancestors must not cancel the declared crop or alter the effective movement.
    for (let parent = video.parentElement; parent; parent = parent.parentElement) {
      if (getComputedStyle(parent).transform !== 'none') fail();
    }
  };
}
