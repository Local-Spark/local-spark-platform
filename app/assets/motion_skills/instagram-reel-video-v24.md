---
name: instagram-reel-video
version: 24
description: Video com handoff editorial, SVG graphic declarado, EDL speech-safe, ElevenLabs como photo.
---

# Reel com vídeo: capacidade e verificação

Norte: desenvolvimento e integração vistos nas 41 referências de propaganda e
Maestros. Soft significa ritmo e intenção suaves, não peça parada. Take contínuo
com textos e crop mínimo não satisfaz o contrato, mesmo rotulado adequate.
Planeje estabelecimento → detalhe/transformação → convite com conteúdo novo.
Transições `cut|dissolve|fade` com `transition_reason` (origem→destino). Soft
≠ parado. Não encha a peça de efeitos só para passar contagens.

Video handoff: motion-video-reel-v4 + motion-video-edit-v5, design video-design-v2. O plano é allowlist: design.layers com shape rectangle|ellipse|rounded|bar e color #RRGGBB ou #RRGGBBAA do kit. Runtime cria cada graphic como SVG com forma preenchida (não DIV vazio); filhos SVG só sob o id declarado. Beats lineares JSON {x,y,opacity} ou {x,y,opacity,scale} (scale>0, default 1). transition cut|dissolve|fade com transition_reason. dissolve/fade = handoff editorial: VIDEO pode ceder opacidade só na borda <=500ms se um plano full-bleed declarado (layer box 0,0,1,1, z_index<10, opacity>=.95) cobre o quadro — nunca fade para preto. EDL: com áudio, duração do segmento = intervalo na fonte (1:1) + speech-safe; silent permite rate 0.75–1.25 (source_span/scene_span). Padding final 1–34ms na última cena permanece. Desenvolvimento editorial: >=2 funções, >=2 assinaturas de composição, e ao menos um de PIP>=800ms, imagem auxiliar sustentada, ou graphic exposto (deslocamento>=24px ou barra/rounded visível >=800ms). Take+texto+crop mínimo continua rejeitado. Mix: elevenlabs-music-v1 (cache + geração com as mesmas gates da photo) + duck; sem compra pelo modelo; sem credencial fica cache/status explícito. Logo kit, texto legível (spans ok), scene-visibility, 60s/50MiB, sem Remotion/TTS/avatar/inventar assets.



## design obrigatório em toda cena (video-design-v2)

Em **cada** cena com `video_layout`, declare `design`. Sem `design` a peça
falha com `MOTION_VIDEO_DESIGN_REQUIRED` — `mode`/`edit`/ids sozinhos não
bastam. Versão fixa: `video-design-v2`. Todo `role=graphic` ou imagem auxiliar
(fora de vídeo/logo/textos do layout) entra em `design.layers` com o mesmo
`element_id`; layers vazias só quando a cena não tem esses elementos.

Esqueleto mínimo (cover, sem layers auxiliares):

```json
"design": {
  "version": "video-design-v2",
  "viewport": {"x": 0, "y": 0, "width": 1, "height": 1},
  "layers": [],
  "transition_reason": "origem → destino desta passagem"
}
```

Com graphic/imagem auxiliar, cada um vira um item em `layers` (`box`,
`z_index` 0..18, `shape` rectangle|ellipse|rounded|bar, `color` do kit).
Beats de cada layer e de cada texto: JSON `{x,y,opacity[,scale]}`, curve linear,
contíguos do `scene.start_ms` ao `scene.end_ms` — use `hold` para preencher
intervalos; sem buracos (ex.: transform em 500–1000 e exit em 6400). Texto:
enter→transform→hold→exit; `related_element_ids` inclui o vídeo da cena; CTA da
última cena com hold ≥1500ms. bar/rounded com `box.width` ≥0.04; imagem auxiliar na frente do vídeo (z>10)
com box ≥0.5×0.5 se for o desenvolvimento por material. mode cover exige
viewport 0,0,1,1; pip declara retângulo menor e fundo full-frame em `layers`.
Confira design + cobertura temporal.

Para cada cena declare vídeo e logo do kit, textos e layers com IDs únicos.
O runtime cria layers (SVG gráfico com forma do plano, ou IMG autorizado), aplica seus beats lineares,
viewport/PIP, crop e seek EDL, inclusive reversos. Não crie esses nós no HTML;
implemente o VIDEO único, logo por cena e textos com scrims exclusivos. Texto e
logo z-index >=20, vídeo 10, layers 0..18. Para revelar fundo use pip e uma layer
full-frame do kit; imagens auxiliares só do inventário. Os beats de layers cobrem
sua cena; estados JSON {x,y,opacity[,scale]}, posições em px. Grafismo exposto
com deslocamento >=24px ou barra/rounded sustentada >=800ms; piso verificável,
não nota artística.
Chrome do documento: `html`/`body`/`main` com `background:transparent` e
`overflow:visible` — sem canvas creme (#FFF8EC etc.) e sem `overflow:hidden` no
shell (ancestrais do texto precisam overflow visível). Fundo de cena é layer
declarada (runtime SVG), não pintura do body. Scrim só no pai exclusivo do texto.
Pintura no chrome → `MOTION_VIDEO_UNPLANNED_OVERLAY`.
Mudar apenas nomes de função não muda a composição.

Cada texto mantém enter → transform → hold → exit, estados lineares {x,y,opacity}
contíguos, enter no início da cena e exit no fim. Enter 0→1, exit →0,
transform desloca >=4px. CTA final tem hold estável >=1500ms. Texto puro branco,
fonte >=28px no canvas720; scrim preto alpha .75–.8 constante, padding <=16px,
largura <90%, altura <25%, texto entre 12–78% da altura, margens horizontais 4%.
Scrims sem transform/overflow/blur/sombra, cada texto com pai exclusivo. Logo IMG
assets/logo.png, <=25% largura e <=12% altura, discreto; sem fabricar identidade.

ASR é estimado: não invente palavras/tempos. Remonte em silêncio medido ou lacuna
segura entre utterances, margem 120ms. Cues de fala são da fonte; para beats use
scene.start_ms + cue.start_ms - source_in_ms. Corte visual sem descontinuidade
da fonte não exige silêncio. O servidor verifica corte e monta áudio; o campo
audio continua exatamente authorized_audio, nunca reescrito pelo modelo.

Servidor aplica trilha elevenlabs-music-v1 (cache/geração gated como photo) com
duck sob fala; SFX CC0 só com ação e purpose declarados. Sem faixa elegível o
status fica explícito. Não comprar nem gerar música no modelo. Não alegar escuta,
qualidade E2E ou porcentagem pelas medições. Revisão adequada exige evidência
temporal de desenvolvimento/camada/motion; falta de evidência é uncertain,
anti-padrão é not_met. Adequate não é aceite humano.

## Texto puro: nenhum elemento filho, inclusive quebras de linha

Cada nó identificado em video_layout.text_element_ids deve conter somente texto:
node.children.length === 0. Não insira <br>, <span>, <strong>, <em>, ícones ou
qualquer outro elemento dentro dele, nem use innerHTML para formatar a frase.
Use textContent. <br> é elemento filho e será rejeitado mesmo sem decoração.
O pai direto continua sendo o scrim; o próprio nó de texto recebe transform/opacity.

Para várias linhas no MESMO texto, use caracteres de nova linha em textContent
com CSS white-space:pre-line, ou quebra natural com white-space:normal e largura
adequada. Não confunda a string literal barra+n com uma nova linha real. Se usar
videoTextWithScrim, aplique whiteSpace='pre-line' após a chamada em CADA seek,
pois o exemplo configura nowrap. A alternativa é texto curto em uma única linha.
Não divida em spans internos nem crie IDs extras fora do plano para contornar a regra.

Meça a frase inteira com as fontes carregadas, incluindo todas as linhas. Preserve
fonte mínima, altura do scrim <25%, largura <90%, margens e texto entre 12–78% da
altura do quadro; max-width com nowrap não garante que os glifos caibam. O CTA
continua com transform próprio e hold visível >=1500ms. Antes de entregar a
implementação, confira children.length===0 em TODOS os textos de TODAS as cenas,
inclusive os que começam invisíveis; a falha aparece no primeiro frame visível.


Alternativa à redução PIP: imagem autorizada em layer 11..18 passa à frente da gravação como segundo plano visual (>=800ms). Grafismo pode ficar acima dela; mantenha logo/textos >=20. Não obrigue PIP se o desenvolvimento por material real fizer mais sentido.

## Anti-exemplos (rejeitar)

(12) Take contínuo + texto + crop mínimo rotulado adequate.
(15) dissolve/fade que só apaga o VIDEO sem plano full-bleed por baixo.
(16) Grafismo declarado mas escondido atrás da gravação o tempo todo.
(17) `video_layout` com mode/edit/ids (e até elements graphic/image) **sem**
`design` — ou `design.version` diferente de `video-design-v2`.
(18) Beats de texto/layer com buraco temporal (não contíguos start→end da cena).
(19) Texto sem `related` ao vídeo da cena, ou CTA final sem hold ≥1500ms.
(20) bar/rounded com width <0.04, ou imagem auxiliar z>10 com box <0.5×0.5
quando ela deveria sustentar o desenvolvimento.
