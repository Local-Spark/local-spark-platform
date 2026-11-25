# Galeria criativa do produto — envelope completo (kit = STYLE_GALLERY)

**Data:** 25/11/2026  
**Estado:** especificação de produto; **não autoriza** mudança de schema, pin de
kit, chamada paga nem implementação.  
**Norte:** `STYLE_GALLERY.md` + `choose-creative-direction` (maestro-video) +
kit/acervo/skills já existentes.  
**Pele:** sempre do **negócio** (palette/fonts/logo do kit). Não copiar
marble/gold/Cormorant/`PremiumFrame` visual.

**Objetivo:** a peça resolve **um** `creative_brief` obrigatório com o mesmo
tipo de envelope que a galeria premium —  
`motion_intensity` → dials, chrome, headline + pacing, music mood, subtitle
pack — consumido por generate / render / review / áudio.

---

## 1. Papéis

| Artefato | Função |
| --- | --- |
| **Kit** (`brand-kit-v*`) | Identidade e materiais: cores, fontes, logo, fotos, direitos |
| **Gallery registry** (novo, versionado no repo ou no kit) | Identities ACTIVE: envelope de motion/edição por vertical |
| **`creative_brief`** (por run) | Resolução obrigatória: um `identity_id` + campos congelados |
| **Skill / repertoire** | Teaching + anti-exemplos; **não** substituem o brief |
| **Gates / review** | Falham se o plano/HTML/áudio **driftar** do brief |

Default: identity do kit do negócio. Fallback: identity “reduced” do mesmo kit
(ex. sem stock/image-gen) — análogo a hand-drawn fallback, **não** outro look
de marca.

---

## 2. Schema do `creative_brief` (obrigatório no pipeline)

Emitido na prepare (etapa tipo 2.5), persistido no trace do run, lido por
todas as fases seguintes. Validar antes de generate; se inválido → fallback
seguro do registry + warning (nunca bloquear com brief vazio).

```json
{
  "run_id": "<uuid>",
  "identity_id": "cafe-pausas-calm-v1",
  "kit_id": "cafe-pausas",
  "kit_version": 1,
  "palette": {
    "roles": {
      "bg": "#F5F0E7",
      "ink": "#244739",
      "accent": "#BB7A48",
      "scrim": "rgba(36,71,57,0.55)"
    },
    "source": "kit.palette"
  },
  "typography": {
    "display": "DejaVu Serif",
    "body": "DejaVu Sans",
    "label": "DejaVu Sans",
    "min_readable_px": 28,
    "source": "kit.fonts"
  },
  "chrome": {
    "mode": "none",
    "rule_color": null,
    "corner": "0",
    "safe_margins_9_16": { "top": 264, "bottom": 360, "side": 96 }
  },
  "motion_intensity": "low",
  "motion_dials": {
    "enter_ms": 280,
    "settle_overshoot": 0.02,
    "stagger_step_ms": 40,
    "parallax_layers": 1,
    "accents_per_scene": 0,
    "max_blur_scenes": 0
  },
  "headline_formula": "calm-claim",
  "pacing": "slow-balanced",
  "hook_archetype": "soft-pause",
  "subtitle_pack": "kit-clean",
  "music_mood": "warm-ambient",
  "broll_policy": "kit-first",
  "stock_complement": "gated",
  "rationale": "Identity calm do kit Café; intensity low; pacing lento.",
  "resolved_at": "<iso>",
  "registry_sha256": "<pin>"
}
```

Campos **enum** (registry); cores/fontes **só** do kit (ou derivação
documentada). Improviso de hex/font fora do kit = drift.

---

## 3. `motion_intensity` → dials (MotionV1 / HTML)

Espelha a tabela low/med/high do STYLE_GALLERY §2, mapeada ao que o lab
controla (sem Remotion springs). Valores abaixo são **proposta inicial** a
calibrar com testes; pinar na implementação.

| Dial | `low` | `med` | `high` |
| --- | --- | --- | --- |
| Enter / exit típico | 280–360 ms | 200–280 ms | 140–200 ms |
| Overshoot / bounce | ~0 | leve (1 accent) | 1 accent + 1 extra permitido |
| `MotionV1.stagger` step | 48–64 ms | 32–48 ms | 24–36 ms |
| Parallax / drift camadas | 0–1 | 1–2 | 2–3 |
| Accents “pop” por cena | 0–1 (quase 0) | 1 | 1+ |
| Holds de leitura | mais longos | médios | curtos (ainda ≥0,4s/palavra) |

**Invariantes (todo intensity):** snap/settle como default; bounce **racionado**;
sem wobble contínuo; safe margins 9:16; complement rule se houver subtítulo.

Café / tom soft: default registry **`low`** ou `med`; `high` só identity
promo ACTIVE.

---

## 4. Moldura / chrome de peça

Não é `PremiumFrame` dourado. Contrato:

| `chrome.mode` | Comportamento |
| --- | --- |
| `none` | Full-bleed kit; sem filete (default Café) |
| `soft-rule` | Filete 1px cor `rule_color` do kit (accent ou ink @ α) |
| `card` | Conteúdo em cartão com padding; fundo layer do kit — **não** creme lavagem sem layer |
| `split-band` | Faixa superior/inferior para M04 (janela + canvas) |

Review/DOM: chrome declarado ≠ unplanned overlay; modo `none` + fundo só via
`design.layers` (já normalize chrome transparente).

---

## 5. Headline formula + pacing

### `headline_formula` (registry do vertical)

| Id | Uso | Tom Café |
| --- | --- | --- |
| `calm-claim` | Afirmação curta acolhedora | **Default** |
| `soft-invite` | Convite à pausa / visita | Ok |
| `curiosity-gap` | Gancho leve | Ok se não clickbait agressivo |
| `number-promise` | “3 motivos…” | Só identity promo |
| `warning` / `enemy-callout` | — | **Fora** do vertical café |

Abertura: frase ≤8 palavras (ou ≤15 tokens visíveis na cena), true ao brief;
entra cedo (hook &lt;~2s). Complement: não espelhar narração palavra a palavra.

### `pacing`

| Id | Alvo de troca de tela | Notas |
| --- | --- | --- |
| `slow-balanced` | ~2,5–3,5 s | Default Café |
| `balanced` | ~2–2,5 s | Heurística Maestros |
| `rapid-fire` | ~1,5–2 s | Só promo ACTIVE |

Pacing informa edit_plan / duração de beats; não estica fala do cliente.

### `hook_archetype`

Subset filtrado de `NARRATIVE_ARCHETYPES` ao vertical (ex. `soft-pause`,
`warm-invite`). Anti-repetição entre runs do mesmo negócio (dial freshness).

---

## 6. Music mood + subtitle pack

### `music_mood`

Enum no registry + matching na biblioteca ElevenLabs/cache (nome ou tag):

| Mood | Quando |
| --- | --- |
| `warm-ambient` | Default Café |
| `light-friendly` | Mais energia ainda soft |
| `elegant-quiet` | Noite / fechamento |
| `tense` / `epic` | Fora do café (outros verticais) |

Pipeline áudio **obriga** mood do brief (QCR-076 analog). Duck sob fala; SFX
só em acento. Riser/click: opcional pin CC0/licença — se não pinado, skip
logado (como add-music robusto).

### `subtitle_pack`

| Pack | Comportamento |
| --- | --- |
| `kit-clean` | Sem burn se stagger/kinetic já é o texto; se burn: MarginV seguro, max chars, accent da palette do kit |
| `kit-kinetic-only` | Só MotionV1 stagger; suppress burn |
| `off` | Sem subtítulo |

Accent do pack ∈ cores do kit. Pack não inventa fonte fora do kit.

---

## 7. Pipeline obriga o brief

1. **Emit:** após context/kit snapshot; antes do generate de composição.
2. **Validate:** `identity_id` ACTIVE; enums resolvem; palette/typo do kit;
   intensity dials da tabela pinada.
3. **Persist:** trace slot `creative_brief` (e hash); resume reutiliza, não
   re-deriva à toa.
4. **Consume:**
   - plan/HTML → intensity, chrome, pacing, headline, typography
   - áudio → music_mood (+ SFX policy)
   - legendas → subtitle_pack
   - stock §7b → `broll_policy` / `stock_complement`
5. **Enforce:** decode/validate/review comparam plano a brief; drift →
   `direction` ou código de brief (`MOTION_CREATIVE_BRIEF_DRIFT` a nomear).
6. **Freshness:** variar dials/archetype/formula **dentro** do mesmo
   `identity_id`; não trocar a marca do cliente “por variedade”.

---

## 8. Registry exemplo (Café) — não implementar ainda

```text
identity_id: cafe-pausas-calm-v1
  status: ACTIVE (default)
  motion_intensity: low
  chrome.mode: none
  headline_formula: calm-claim
  pacing: slow-balanced
  music_mood: warm-ambient
  subtitle_pack: kit-kinetic-only
  hook_archetype: soft-pause

identity_id: cafe-pausas-promo-v1
  status: candidate → ACTIVE só após aceite humano
  motion_intensity: med
  chrome.mode: soft-rule
  headline_formula: soft-invite | curiosity-gap
  pacing: balanced
  music_mood: light-friendly
```

Skill/repertoire apontam para estes ids; hashes no pin como hoje.

---

## 9. Relação

- Inventário fluxo: [fluxo-completo](motion-maestros-fluxo-completo-extracao-2026-11-25.md) §8b.
- Sequência B: B0/docs desta galeria **antes** de B2.
- Programa A: piso anti-colagem; este doc é envelope criativo.
