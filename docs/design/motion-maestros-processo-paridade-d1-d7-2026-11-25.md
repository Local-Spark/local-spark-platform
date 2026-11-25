# Paridade de processo Maestros — D1–D7 (especificação)

**Data:** 25/11/2026  
**Estado:** docs completos para estes gaps; **não autoriza** implementação,
schema, chamada paga, pin de QCR em código nem geração Café.  
**Pergunta respondida:** havia informação suficiente no acervo — sim. Este
arquivo fecha o que faltava documentar.

**Dependências já documentadas:**  
[fluxo-completo](motion-maestros-fluxo-completo-extracao-2026-11-25.md) ·
[galeria kit](motion-creative-gallery-kit-envelope-2026-11-25.md) ·
[sequência B](motion-maestros-html-sequencia-pos-programa-a-2026-11-25.md) ·
[Programa A](motion-maestros-html-quality-program-a-2026-11-25.md).

**Pele:** kit/acervo/skills do cliente. Processo: Maestros traduzido ao HTML lab.

---

## D1 — MOTION_DESIGN_SYSTEM subset (barra anti-slop)

**Fonte:** `motion-pipeline/MOTION_DESIGN_SYSTEM.md` (V8).  
**Entrar no lab como:** invariantes + checklist de review/samples — não o
toolkit Remotion/Lottie.

### Invariantes a pinar

1. **Settle, não bounce everywhere** — entrada default = snap/settle
   (MotionV1 curve damped). Bounce/overshoot só como **accent racionado**
   (≤1 por cena; ver dials do `motion_intensity` na galeria).
2. **Complement rule** — texto de motion **não** transcreve a fala/ASR:
   ≤3 palavras compartilhadas com o segmento simultâneo; nunca 4+ consecutivas.
   Preferir label/conclusão/número/marca. Se `subtitle_pack` = kinetic-only e o
   stagger **é** a linha falada, a regra aplica-se a **outras** placas na mesma
   janela (não duplicar a mesma frase em dois lugares).
3. **Abertura (S0)** — nos primeiros ~0–3s: headline/frase do brief
   (`headline_formula`), true ao conteúdo, ≤8 palavras (ou teto do vertical),
   gancho visual &lt;~2s. Sem hard-sell falso.
4. **Teto de palavras na cena** — ≤15 palavras visíveis “de leitura” por
   momento (exclui textura ≤6 chars). Se não couber: revelar por etapas, não
   reduzir fonte abaixo de `typography.min_readable_px`.
5. **Safe margins 9:16** — do `creative_brief.chrome.safe_margins_9_16`
   (defaults galeria: top 264 / bottom 360 / side 96 @ 1080×1920; escalar ao
   profile 720×1280).
6. **Sem emoji** como ícone de conteúdo; graphic = SVG/path pinado ou asset kit.
7. **Library-only spirit** — primitos MotionV1 + layers allowlist; sem CSS
   animation ad hoc que o seek não reproduz.

### Checklist de frames (review / Capricho)

Antes de `adequate`: amostrar abertura, miolo, CTA e bordas de cena.

- [ ] Complement / sem double-subtitle  
- [ ] Settle default; accents ≤ dial  
- [ ] Headline/abertura honra formula + verdades do brief  
- [ ] Safe margins; nada crítico sob UI de plataforma  
- [ ] Tipografia do kit; contraste legível  
- [ ] Progressão: estados distintos (já B2)  
- [ ] Chrome = brief (sem overlay não planejado)

**Fora de D1:** Lottie bank, 40/60 avatar Remotion, HeroCascade Remotion.

---

## D2 — Archetypes + retention spine (vertical Café)

**Fonte:** `NARRATIVE_ARCHETYPES.md` + filtros de tom soft.  
**Não** importar enemy-callout / warning agressivo para cafeteria.

### Retention spine (adaptada a reel ~11–15s)

Nos Maestros (~60s+): plant loop → re-hook ~50% → callback.  
No reel curto do lab:

1. **Plant** (0–~2s): abertura com tensão leve ou convite (gap ou claim calmo).  
2. **Re-hook** (~40–60% da duração): detalhe / crop / frase que renova atenção
   (“mas no meio do dia…” / detalhe do preparo) — **nova** informação visual ou
   verbal, não repetir a abertura.  
3. **Payoff + soft close** (terço final): benefício/CTA; callback opcional à
   imagem/frase inicial (sem CTA gritado).

Falta de plant ou de mudança no miolo → `direction` (alinha anti-(21) / B1).

### Registry de archetypes (Café) — ACTIVE

| `hook_archetype` | when_to_use | `headline_formula` típica | Curva |
| --- | --- | --- | --- |
| `soft-pause` | Pausa / acolhimento (default) | `calm-claim` / `soft-invite` | convite → clima → detalhe → CTA |
| `warm-ritual` | Preparo / ritual do café | `soft-invite` | ação → detalhe sensorial → re-hook → CTA |
| `soft-curiosity` | Um “segredo” leve do lugar | `curiosity-gap` | gap → pista → revelação suave → close |
| `small-list` | 2–3 motivos / passos | `number-promise` (só promo) | N → 1 → re-hook → 2/3 → CTA |

**Candidate / fora do Café:** `warning_fomo`, `direct_call_out`, `shock_myth_bust`.

Anti-repetição: não repetir o mesmo `hook_archetype` em dois runs seguidos do
mesmo business se houver alternativa ACTIVE (freshness dials da galeria).

---

## D3 — add-music layers (som com função)

**Fonte:** `add-music/SKILL.md` + mixer lab já pinado.

### Camadas (defaults; robustez = não hard-fail)

| Layer | Comportamento lab |
| --- | --- |
| **Music bed** | Faixa cujo tag/mood = `creative_brief.music_mood`; volume baixo; fade in/out; **duck** sob fala/overlay |
| **Hook riser** (opcional pin) | SFX crescendo no fim da frase de abertura; duck sob voz; se asset/ASR ausente → skip logado |
| **Drop** | Música entra/só sobe logo após pico do riser (ou t≈fim do hook se sem riser) |
| **Transition clicks** (opcional pin) | Click curto em cortes de edit_plan / bordas de cena; 1º mais alto; demais sutis; se sem pin → skip |
| **Action SFX** | CC0 pour/cup (já) só se plan declarar acento na ação |

### Regras

- Honrar `music_mood` do brief (análogo QCR-076).  
- Narration/source audio preservada; nunca substituir por TTS.  
- Sem riser/click pinados com licença → fase ainda completa com bed+duck+SFX ação.  
- Após re-render de vídeo, re-mix áudio (ordem estável no pipeline).

---

## D4 — QCR subset pinado (determinístico)

**Fonte:** `qc-pipeline/QCR_INDEX.md` (amostra).  
**Não** portar `active-rules.md` inteiro nem Gemini QC nesta fatia.

### Regras a traduzir para gates/review lab (IDs locais sugeridos)

| Origem | Regra no lab |
| --- | --- |
| QCR-004 | Texto motion alinhado (center contract quando plan diz center) |
| QCR-005 | Número/count-up hold ≥300ms |
| QCR-011 / 015 / 020 / 077 | Complement rule (D1); títulos curtos ≠ duplicate phantom |
| QCR-001 / 008 | Safe margins / clearance se houver burn |
| QCR-002 / 017 / 026 | Se subtitle burn: max palavras/linha, merge curtos |
| QCR-032b | Stock: seleção determinística por id estável |
| QCR-033 / 036 / 038 / 052… | Stock: queries que evitam rostos/pessoas indesejadas (§7b) |
| QCR-076 | Music match `music_mood` |
| QCR-079 / 080 | Seções graphic-only sem texto baked quando pack/brief pedem; match linha + variar mecanismo |
| QCR-109 spirit | Sem flash de camada / gap de timeline (já guards; reforçar) |

Cada regra pinada = teste unitário + código de falha estável.  
Novas fricções de produção → nova regra pinada (D7), não prompt solto.

**Fora:** QCR de HeyGen, ManyChat, Remotion Root.tsx, BRAND_FIX Claude-specific.

---

## D5 — Edit plan verify

**Fonte:** `EDIT_STYLES.md` + SECTION grammar (traduzida).

### Artefato

`edit_plan` (no motion plan ou slot irmão): lista ordenada de beats

```json
{
  "beats": [
    {
      "t0_ms": 0,
      "t1_ms": 2500,
      "edit_style": "opening",
      "format": "M01",
      "hook_role": "plant"
    }
  ]
}
```

`edit_style` ∈ registry lab (tradução):  
`opening | source_full | phrase | source_caption | hero | split | full_gfx | evidence | flow | stat`  
(mapear aos §1–§6 Maestros; sem avatar HeyGen — `source_*` = gravação cliente).

### Verify pré-render (determinístico)

1. Cobertura contínua `[0, duration)` sem gaps (gap-free).  
2. Beat 0 = `opening` (ou equivalente).  
3. Heurística de variedade: em janela de 4 beats, preferir ≥3 styles distintos;
   **não** hard-fail se QC humano ok (distance-4 desproven no canary Maestros) —
   warning + preferência de profundidade de animação.  
4. `format` ∈ M01–M05 allowlist; M02 só se máscara B5 disponível.  
5. Pacing: duração média alinhada a `creative_brief.pacing` (±tolerância).  
6. Spine D2: existe plant + mudança miolo + close.

Falha → não render / `MOTION_EDIT_PLAN_INVALID` (nome a fixar no código).

---

## D6 — Scene-record schema (consumível)

**Fonte:** Finalizador `scene-record.md`.  
**Mínimo por insert/cena no lab** (JSON no plan ou trace):

```json
{
  "scene_id": "s1",
  "revision": 1,
  "source": {
    "phrase": "…",
    "in_ms": 0,
    "out_ms": 3200,
    "anchors": [{ "kind": "word", "text": "pausa", "t_ms": 800, "confidence": "estimated" }]
  },
  "concept": {
    "gain": "mostrar o ritual",
    "format": "M01",
    "operation": "transform",
    "entry": "cut",
    "exit": "cut",
    "protected_region": null,
    "states": [
      { "id": "a", "delta_from_prev": null },
      { "id": "b", "delta_from_prev": "crop_in" }
    ],
    "text": [{ "string": "No meio do dia,", "hold_s": 1.2 }]
  },
  "assets": [{ "id": "source", "kind": "video", "role": "plate" }],
  "checks": {
    "progression": "not_checked",
    "readable": "not_checked",
    "occupancy": "not_checked",
    "audio": "not_applicable"
  }
}
```

Regras: `null` ≠ sucesso; `not_checked` até sample/review; aprovação Veredito ≠
preencher checks estruturais. Validador de schema ≠ juízo estético.

---

## D7 — Self-improve + learning (sem mudar o kit)

**Fontes:** QCR-014 spirit + Finalizador `agent-learning-review`.

### Loop de produto

1. Fricção: falha de gate, review `direction`, ou Veredito **R** com motivo.  
2. Classificar: processo (gate/skill/repertoire teaching) vs preferência visual
   do **kit** (não generalizar cor/logo do cliente para outros negócios).  
3. Proposta de lição: texto + escopo (`skill` | `repertoire` | `qcr-local` |
   `gallery-identity`) + evidência (run_id, t_ms).  
4. Aplicar **só** com autorização (ou fila de calibração); registrar proveniência.  
5. Nunca promover rejeição estética de um cliente a regra global de marca.

Calibração é **on-demand** (não etapa de todo render). Produção usa só o que
já está pinado/ACEITO.

---

## Ordem docs→código (atualizada)

1. Galeria brief enforce ([gallery](motion-creative-gallery-kit-envelope-2026-11-25.md))  
2. D1 checklist + complement no review  
3. D2 archetypes no brief resolve  
4. D5 edit_plan + D6 scene-record fields  
5. B1 loop direção  
6. B2 progressão/formatos  
7. D3 som layers + B3 EDL  
8. D4 QCR subset + B4 samples  
9. D7 learning process  
10. B5 máscara · §7b stock  

---

## Critério de fechamento deste doc

D1–D7 estão **especificados** o bastante para implementar sem adivinhar.
Secundários (ASS burn completo, image-gen, Arsenal M4, Gemini QC, photo-reel)
continuam opcionais e listados no fluxo-completo §9 secundário — **não**
bloqueiam paridade de edição do reel vídeo com kit.
