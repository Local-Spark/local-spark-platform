---
name: instagram-reel-video
version: 22
description: Video com desenvolvimento editorial, camadas declaradas, EDL speech-safe e mix local.
---

# Reel com vídeo: capacidade e verificação

Norte: desenvolvimento e integração vistos nas 41 referências de propaganda e
Maestros. Soft significa ritmo e intenção suaves, não peça parada. Take contínuo
com textos e crop mínimo não satisfaz o contrato, mesmo rotulado adequate.
Planeje estabelecimento → detalhe/transformação → convite com conteúdo novo.
Uma transição cut pode relacionar escala/plano/função; explique origem e destino.
O repouso tem função de leitura. Não encha a peça de efeitos para atingir contagens.

Video C: motion-video-reel-v2 + motion-video-edit-v3, video_layout.design.version=video-design-v1. O plano é allowlist: declare TODOS os grafismos/imagens em design.layers com element_id, box {x,y,width,height} normalizado, z_index 0..18, shape rectangle/ellipse e color hexadecimal do kit. Cada layer aponta para role graphic ou image e beats lineares com JSON {x,y,opacity} em px. Grafismos puros sem filhos; imagens usam somente assets autorizados. O runtime cria essas layers, aplica beats e visibilidade; não duplique seus nós no HTML. Vídeo único e logo/textos ficam no HTML. design.viewport define retângulo normalizado do vídeo: mode cover exige 0,0,1,1; mode pip revela camada de fundo declarada. Vídeo z-index 10; texto e logo acima (20 ou mais). O runtime executa EDL/crop e viewport; a guarda confere mídia, texto, logo e overlays. Corte com função: design.transition_reason relaciona origem/destino; >=2 funções editoriais, mudança de composição >=800ms, graphic com deslocamento >=48px e presença >=800ms. Take contínuo + texto + crop mínimo falha, mesmo em briefing soft; capacidade não prova qualidade. EDL in/out livres dentro da fonte, sem speed ramp, duração final <= output.duration_ms (teto); pode encurtar sem repetir material; remonte com áudio exige fronteiras com margem 120ms em silêncio medido ou intervalo ASR completo com confiança >=.8; lacunas de transcrição parcial não provam silêncio. Cortes visuais contínuos não cortam áudio. Unsafe: MOTION_VIDEO_SPEECH_CUT_UNSAFE. O servidor monta áudio original na mesma EDL, aplica música autorizada/cache local e duck; SFX apenas biblioteca licenciada. Não comprar/gerar música. Ausência real fica explícita. Texto puro, scrim local estável, logo kit, scene-visibility, limites 60s/50MiB permanecem. Sem Remotion/TTS/avatar. Qualidade das refs 41/Maestros depende de MP4 e revisão humana autorizados.

Para cada cena declare vídeo e logo do kit, textos e layers com IDs únicos.
O runtime cria layers (DIV gráfico ou IMG autorizado), aplica seus beats lineares,
viewport/PIP, crop e seek EDL, inclusive reversos. Não crie esses nós no HTML;
implemente o VIDEO único, logo por cena e textos com scrims exclusivos. Texto e
logo z-index >=20, vídeo 10, layers 0..18. Para revelar fundo use pip e uma layer
full-frame do kit; imagens auxiliares só do inventário. Os beats de layers cobrem
sua cena; estados JSON {x,y,opacity}, posições em px. Ao menos um grafismo tem
movimento visível >=48px durante >=800ms; isto é piso verificável, não nota artística.
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
