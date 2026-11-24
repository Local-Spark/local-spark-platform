function installVideoSceneVisibilityV1(plan) {
  const original = window.seek;
  const fail = () => { throw new Error('MOTION_VIDEO_SCENE_SCOPE_INVALID'); };
  if (typeof original !== 'function') fail();
  const ids = plan.scenes.flatMap(scene => scene.video_layout.text_element_ids);
  function scope(ms) {
    const scene = [...plan.scenes].reverse().find(scene =>
      scene.start_ms <= ms && (ms < scene.end_ms || ms === plan.duration_ms && scene.end_ms === ms));
    if (!scene) fail();
    const active = new Set(scene.video_layout.text_element_ids);
    const parents = new Set();
    // Resolve on every seek: replacing a node cannot bypass ownership validation.
    const entries = ids.map(id => {
      const matches = document.querySelectorAll(`[id="${id}"]`);
      if (matches.length !== 1) fail();
      const node = matches[0], parent = node.parentElement;
      if (!parent || parent === document.body || parent === document.documentElement ||
          parent.children.length !== 1 ||
          parent.textContent.trim() !== node.textContent.trim() || parents.has(parent)) fail();
      parents.add(parent);
      return {id, parent};
    });
    for (const {id, parent} of entries)
      parent.style.setProperty('display', active.has(id) ? 'block' : 'none', 'important');
  }
  window.seek = async function(ms) {
    scope(ms); // Active text must be measurable by the implementation.
    await original.call(window, ms);
    scope(ms); // Model code cannot leave an inactive scrim visible after its seek.
  };
}
