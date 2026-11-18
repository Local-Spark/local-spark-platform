# Ensaio Café Aurora v3 — gaps e próxima fatia — 17/11/2026

## Ensaio v4 — próximo backlog noutro doc

Após L1–L3, o ensaio `versao-1 (4).mp4` e o backlog M1–M4 estão em
[motion-ensaio-cafe-aurora-v4-gaps-2026-11-17.md](motion-ensaio-cafe-aurora-v4-gaps-2026-11-17.md).
Este documento permanece o diagnóstico v3 + histórico L1–L4.

## Atualização — L1–L3 implementados; aceite audiovisual pendente

Pedido posterior do titular autorizou esta fatia. Novas capturas usam intent
v3, skill photo v15 e repertório default v7; snapshots históricos e vídeo
preservados. Logo disponível entra no inventário/preview e é obrigatória no
plano como imagem. Ritmo/fecho e full-bleed são orientação forte; exemplo
executável anima fotos e logo até o fim. Não há gate A5b nem auto-injeção.
Validação e limitações em PROJECT/SDD/BL04/CHANGELOG/DECISIONS. L4 Music/mix
permanece fora; sem chamada paga, novo MP4 ou aceite E2E nesta implementação.
O diagnóstico e as medições abaixo continuam sendo a evidência anterior.

Estado: **diagnóstico e backlog documentados** a partir de
`/Users/israelsilva/Downloads/versao-1 (3).mp4`. Não autoriza, por si,
implementação, chamada paga, A5b nem alteração de Music/renderer. Destinado a
um próximo chat/modelo.

Referências: baseline e P1–P3 em
[motion-melhorias-pos-ensaio-cafe-aurora-2026-11-17.md](motion-melhorias-pos-ensaio-cafe-aurora-2026-11-17.md);
plano A0–A5a
[motion-plano-reels-15s-foto-2026-11-17.md](motion-plano-reels-15s-foto-2026-11-17.md);
Maestros [WuzMxEKJHkQ](../evals/analise-video-maestros-WuzMxEKJHkQ-2026-11-11.md).

## Evidência do ensaio v3

Arquivo: 15,0 s · 720×1280 · H.264 + AAC stereo · ~484 kbps.
Loudness ~**−31,6 LUFS** (trilha ainda baixa; True Peak ~−16,3 dBTP).

Amostragem a 5 fps (cinza 90×160), vs ensaio anterior `versao-1 (2).mp4`:

| Medida | v2 (anterior) | **v3 (este)** |
| --- | --- | --- |
| Pares quase estáticos (diff &lt; 2) | ~89% | **~76%** |
| Holds longos | ~4,8 s e ~6,6 s | **~2,8 s · ~3,0 s · ~4,0 s (fecho)** |
| Picos (trocas) | ~2,2 s e ~7,8 s | **~5–6 s e ~10–11 s** |
| Fecho 11–15 s | — | **quase morto** (13–15 s mean ≈ 0) |

Leitura humana (titular): **melhorias perceptíveis**; ainda há trechos parados;
**logo não entrou** — marca só como tipografia “Café Aurora”.

### Storyboard observado

1. **0–1 s** — cartão creme tipográfico (“No meio do dia,”), marca texto no canto.
2. **~1–5 s** — foto flat-lay em janela + texto partido; meio **congelado** ~2–4 s.
3. **~5–6 s** — transição.
4. **~6–10 s** — foto lifestyle inset em fundo marrom + caixa “uma pausa.”; meio
   **congelado** ~7–9 s.
5. **~10–11 s** — transição ao fecho.
6. **11–15 s** — cartão creme: título tipográfico + díptico + CTA “Conheça nosso
   cardápio”; **quase estático** (~4 s).

Estética: **editorial/revista** (fotos landscape em janela, painéis sólidos), não
propaganda full-bleed 9:16 com gesto contínuo.

## Causa: logo como texto (código)

Não é falha de anexar o PNG; é **não exigir uso**.

| Fato | Onde |
| --- | --- |
| Kit com logo → `assets/logo.png` no pacote de render | `motion_inputs.py` |
| Logo **fora** de `available_materials`; sem preview no planejamento | `motion_inputs` / `motion_ai` |
| Preview da logo só se o plano declarar `image` + `assets/logo.png` | `motion_materials` / adapter |
| Schema aceita marca como `role=text` (`brand_name`) | `motion_plan` — sem role `logo` |
| Nenhuma validação “se logo existe, plano deve usá-la” | validadores atuais |
| Prompt: “Não invente … ou logotipo” + tipografia forte | `CREATIVE_RULES` / skill / intent |
| `makePhotoReelMotion`: `brand` é nó genérico (texto ou img); exemplo sem `<img src="assets/logo.png">` | `business-reel-v6/examples/photo-reel.js` |
| Lab `automatic_plan` remove revisão humana do plano | amplifica o caminho texto |

## Causa: holds ainda parados

1. P1–P3 + staging photo v2 **alinharam o prompt**; helper **não** é auto-injetado.
2. Movimento medido concentra-se nas **trocas**; meios e fecho ainda congelam.
3. P4 (ritmo / holds curtos) e composição full-bleed **não** foram implementados.
4. Cartão final ~4 s sem micro-movimento viola a orientação ~2 s (ainda não é gate).
5. P5 (mix) não feito — loudness igual ao ensaio anterior.

## Gaps vs propaganda / Maestros

| Referência | v3 | Gap de produto |
| --- | --- | --- |
| Gesto contínuo que explica a ideia | Picos nas trocas; meios frios | Holds longos ainda legais; KB fraco/ausente no miolo |
| Marca como âncora visual | Tipografia “Café Aurora” | Sem obrigação de `assets/logo.png` |
| Full-bleed / profundidade | Janelas inset + faixas | Sem contrato de bleed/overlay |
| Ritmo em 15 s | 3 atos + fecho morto | P4 pendente |
| Mix presente | −31,6 LUFS | P5 pendente |
| Helper executado | Só orientação | Sem auto-injeção; sem A5b |

Método (código → timeline → Chromium/FFmpeg → etapas) permanece o caminho certo.
Acabamento ainda abaixo do alvo de anúncio.

## Backlog priorizado (próxima implementação)

### L1 — Logo obrigatória quando disponível (maior gap de marca)

- Se `assets/logo.png` estiver no pacote: plano **deve** declarar ≥1 elemento
  `role=image` + `asset_id=assets/logo.png` (cena de marca/handoff/fecho).
- Expor logo em inventário/`available_materials` (ex.: `brand_logo`) e **preview
  no planejamento**, não só pós-declaração.
- Intent/skill/regras photo: quando logo existe, a marca visual é esse asset;
  `brand_name` tipográfico não substitui o logotipo (pode coexistir como copy).
- Atualizar exemplo `makePhotoReelMotion` / docs do repertório com
  `<img src="assets/logo.png">` no nó `brand`.
- Snapshots históricos sem essa regra: não migrar; nova captura.

### L2 — P4 ritmo + vida no fecho

- Orientação forte: holds de leitura ≤ ~2–2,5 s; nenhum fecho ≥ ~2 s sem mudança
  perceptível (ainda **não** A5b automático).
- Cartão final: KB no díptico/fotos + scale/assentamento da **logo** (não só texto).
- Storyboard alvo em 15 s: gancho → acento → 2º material vivo → handoff → marca/CTA
  com micro-movimento (sem alongar hold contemplativo).

### L3 — Composição photo “anúncio”

- Preferir foto dominante full-bleed 9:16 (cover + foco protegido) em vez de
  janela landscape com faixas mortas; inset só quando a intenção justificar.
- Tipografia/ overlay sobre a foto com contraste, sem voltar ao cartaz estático.

### L4 — P5 mix (opcional nesta fatia ou imediato seguinte)

- Subir presença da trilha alguns dB (instrumental de fundo); fades ok.
- Sem mudar tarifa/credencial Music sem OK explícito.

### Fora desta onda

- A5b com limiares automáticos.
- TTS/Voice, avatar, troca de renderer.
- Auto-injeção cega de helpers sem chamada explícita em `scene_init`/`seek`
  (preferir validação de plano + exemplo + regras; auto-inject só se o titular
  autorizar fatia separada).

## Prompt sugerido para o próximo chat

```
Leia AGENTS.md, o topo de docs/PROJECT.md, docs/SDD.md,
docs/phases/BL04-context-and-ai-production.md e
docs/design/motion-ensaio-cafe-aurora-v3-gaps-2026-11-17.md
(contexto P1–P3 em motion-melhorias-pos-ensaio-cafe-aurora-2026-11-17.md).

Implemente a próxima fatia de qualidade photo reel (L1–L3 do doc v3):
1) Logo obrigatória quando assets/logo.png existe (validação de plano +
   inventário/preview no plan + intent/skill/regras + exemplo com <img>)
2) P4 ritmo: holds curtos; fecho 11–15s com micro-movimento (KB + logo)
3) Composição full-bleed / foto dominante 9:16 (orientação forte no contrato)

Preservar snapshots históricos e caminho de vídeo. Sem A5b, TTS/avatar,
troca de renderer, alteração de Music sem meu OK.

Evidência: versao-1 (3).mp4 — melhorou vs v2 (~76% quase estático) mas meios
congelados, fecho ~4s morto, marca só tipográfica.

Testes + PROJECT/SDD/BL04/CHANGELOG/DECISIONS na mesma mudança.
Não declare aceite E2E sem novo MP4 e minha revisão. Não rode chamada paga
sem eu autorizar.
```

## Aceite da próxima fatia

- Novo MP4: logo PNG visível no handoff/fecho (quando o kit tem logo).
- Fecho sem “cartão morto” de vários segundos; holds de miolo perceptivelmente vivos.
- Menos estética de janela editorial; foto dominante cobrindo o quadro.
- Trilha preservada (mix L4 se incluído).
- Sem gate A5b automático; sem upgrade silencioso de snapshots antigos.
