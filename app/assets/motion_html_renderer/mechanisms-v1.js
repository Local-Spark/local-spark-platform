/* Browser-only stage for structural floor v3. No clock, network or CSS animation. */
(() => {
  'use strict';
  const scales = { macro: 1.45, medium: 1.05, card: 1.18 };
  const origins = { macro: '50% 62%', medium: '50% 50%', card: '50% 42%' };

  function beats() {
    const node = document.getElementById('structural-beats');
    if (!node) return [];
    const parsed = JSON.parse(node.textContent || '[]');
    return Array.isArray(parsed) ? parsed : [];
  }

  function beatAt(ms, items) {
    let current = items[0] || null;
    for (let i = 0; i < items.length; i++) {
      if (items[i].start_ms <= ms) current = items[i];
    }
    return current;
  }

  function progress(ms, beat) {
    if (!beat || beat.end_ms <= beat.start_ms) return 1;
    return Math.max(0, Math.min(1, (ms - beat.start_ms) / (beat.end_ms - beat.start_ms)));
  }

  function seekMedia(id, ms) {
    const node = document.getElementById(id);
    if (!node || node.readyState < 1) return Promise.resolve();
    const target = ms / 1000;
    if (Math.abs(node.currentTime - target) <= 0.04) return Promise.resolve();
    return new Promise((resolve) => {
      const done = () => {
        node.removeEventListener('seeked', done);
        resolve();
      };
      node.addEventListener('seeked', done);
      node.currentTime = target;
    });
  }

  function paint(ms) {
    const items = beats();
    const beat = beatAt(ms, items);
    const t = progress(ms, beat);
    const media = document.getElementById('media');
    const glyph = document.getElementById('glyph');
    const word = document.getElementById('word');
    const plate = document.getElementById('plate');
    const plateText = document.getElementById('plate-text');
    if (!media || !beat) return;
    const scale = scales[beat.scale] || scales.medium;
    media.style.transformOrigin = origins[beat.scale] || origins.medium;
    media.style.transform = 'scale(' + scale + ')';
    media.style.clipPath = 'none';
    glyph.style.opacity = '0';
    word.textContent = beat.text || '';
    plate.style.height = '0px';
    plateText.textContent = '';
    const rect = beat.rect || [0.32, 0.42, 0.36, 0.28];
    const cx = (rect[0] + rect[2] / 2) * 100;
    const cy = (rect[1] + rect[3] / 2) * 100;
    if (beat.mechanism === 'mask_open_from_point') {
      media.style.clipPath = 'circle(' + (8 + t * 140) + '% at ' + cx + '% ' + cy + '%)';
    } else if (beat.mechanism === 'ellipse_to_glyph') {
      media.style.clipPath = 'ellipse(' + (rect[2] * 50) + '% ' + (rect[3] * 50) + '% at ' + cx + '% ' + cy + '%)';
      media.style.opacity = String(1 - t);
      glyph.style.opacity = String(t);
      glyph.style.clipPath = 'circle(' + (18 + t * 80) + '% at ' + cx + '% ' + cy + '%)';
    } else if (beat.mechanism === 'axis_type_in') {
      word.style.transform = 'translateY(' + ((1 - t) * 160) + 'px)';
      word.style.opacity = String(t);
    } else if (beat.mechanism === 'plate_cta') {
      plate.style.height = (t * 280) + 'px';
      plateText.textContent = beat.text || '';
      word.textContent = '';
    }
  }

  window.MechanismsV1 = {
    seek(ms) {
      paint(ms);
      return Promise.all([seekMedia('media', ms), seekMedia('glyph-media', ms)]);
    },
  };
})();
