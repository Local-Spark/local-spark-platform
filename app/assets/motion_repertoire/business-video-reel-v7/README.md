# Business video reel v7

Handoff unlock + SVG graphics + finish references:

- `dissolve|fade` requires a declared full-bleed plane under the VIDEO (≤500ms).
- Runtime `capabilities-v3` creates `role=graphic` as SVG shapes (rectangle/ellipse/rounded/bar).
- Guard `video-reel-v4` allowlists those SVG trees; unplanned SVG still fails.
- Music: `elevenlabs-music-v1` with the same gates as photo.
- `reference_images` are `finish_reference_only` teaching frames — not render assets.
- Anti-examples (12)/(15)/(16)/(17)/(18)/(19)/(20) in rules and skill-v24.
- Every scene `video_layout` includes `design.version=video-design-v2`
  (see `examples/development-plan.json`). Layout without design is invalid.
- Decode fills beat holes / text→video related / bar width floor structurally;
  the model should still declare contiguous beats and design.

Synthetic examples do not certify aesthetic quality vs the 41 refs / Maestros.
