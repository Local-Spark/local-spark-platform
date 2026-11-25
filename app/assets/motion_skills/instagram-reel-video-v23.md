---
name: instagram-reel-video
version: 23
description: Video com qualidade desengessada — dissolve/fade, layers ricos, EDL speech-safe e mix biblioteca.
---

# Reel com vídeo: capacidade e verificação

Norte: desenvolvimento e integração vistos nas 41 referências de propaganda e
Maestros. Soft significa ritmo e intenção suaves, não peça parada. Take contínuo
com textos e crop mínimo não satisfaz o contrato, mesmo rotulado adequate.
Planeje estabelecimento → detalhe/transformação → convite com conteúdo novo.
Transições `cut|dissolve|fade` com `transition_reason` (origem→destino). Soft
≠ parado. Não encha a peça de efeitos só para passar contagens.

Video qualidade: motion-video-reel-v3 + motion-video-edit-v4, design video-design-v2. O plano é allowlist: design.layers com shape rectangle|ellipse|rounded|bar e color #RRGGBB ou #RRGGBBAA do kit. Beats lineares JSON {x,y,opacity} ou {x,y,opacity,scale} (scale>0, default 1). transition cut|dissolve|fade com transition_reason; dissolve/fade suavizam opacidade nas bordas da cena. EDL: com áudio, duração do segmento = intervalo na fonte (1:1) + speech-safe; silent permite rate 0.75–1.25 (source_span/scene_span). Padding final 1–34ms na última cena permanece. Desenvolvimento editorial: >=2 funções, >=2 assinaturas de composição, e ao menos um de PIP>=800ms, imagem auxiliar sustentada, ou graphic exposto (deslocamento>=24px ou barra/rounded visível >=800ms). Take+texto+crop mínimo continua rejeitado. Mix: biblioteca/cache + duck; sem compra/geração paga sem credencial. Logo kit, texto legível (spans ok), scene-visibility, 60s/50MiB, sem Remotion/TTS/avatar/inventar assets.

Para cada cena declare vídeo e logo do kit, textos e layers com IDs únicos.
O runtime cria layers (DIV gráfico ou IMG autorizado), aplica seus beats lineares,
viewport/PIP, crop e seek EDL, inclusive reversos. Não crie esses nós no HTML;
implemente o VIDEO único, logo por cena e textos com scrims exclusivos. Texto e
logo z-index >=20, vídeo 10, layers 0..18. Para revelar fundo use pip e uma layer
full-frame do kit; imagens auxiliares só do inventário. Os beats de layers cobrem
sua cena; estados JSON {x,y,opacity[,scale]}, posições em px. Grafismo exposto
com deslocamento >=24px ou barra/rounded sustentada >=800ms; piso verificável,
não nota artística.
Mode cover exige viewport 0,0,1,1; pip declara retângulo menor e fundo full-frame.
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

Biblioteca/cache já autorizado: trilha com duck sob fala; SFX CC0 só com ação e
purpose declarados. Sem faixa elegível registre indisponibilidade real. Não comprar
nem gerar música. Não alegar escuta, qualidade E2E ou porcentagem pelas medições.
Revisão adequada exige evidência temporal de desenvolvimento/camada/motion;
falta de evidência é uncertain, anti-padrão é not_met. Adequate não é aceite humano.

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
