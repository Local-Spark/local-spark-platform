# BL04 — contexto seletivo e produção visual com IA

## 25/11/2026 — UNPLANNED_OVERLAY chrome

Normalize HTML transparente; regenerar Café.

## 25/11/2026 — renderer image (audio-v3 + audio-video.cjs)

Pin `19836aed…` com `audio-video.cjs`. Códigos `MOTION_RENDER_*` sobem.
Reiniciar lab.

## 24/11/2026 — continuidade + schema + EDITORIAL OR

Wire exige `design`; decode continua beats; unlocked aceita PIP|imagem|graphic.
Reiniciar lab e regenerar Café.

## 24/11/2026 — quality lock completo

Video: ElevenLabs + handoff + SVG + finish refs (repertoire-v7 / skill-v24).
Photo: skill-v23 / repertoire-v13 (progressão perceptual). Reiniciar
`make creation-lab` antes da peça nova.

## 24/11/2026 — desengessar qualidade (video+photo)

Novas capturas: video edit-v4/reel-v3/skill-v23; photo polish-v8/skill-v22.
Inventário e limites mantidos:
[desengessar](../design/motion-qualidade-desengessar-2026-11-24.md).
Sem MP4 E2E nesta fatia.

## 24/11/2026 — video-reel C: capacidade declarada e verificação

Implementado em código para novas capturas: `motion-video-reel-v2`,
`motion-video-edit-v3`, `video-design-v1`, `instagram-reel-video-v22`,
`business-video-reel-v5`, geração `proposed-video-output-v3` e mixer
`motion-audio-v3`. A/B mantêm seus contratos e bytes; ausência de pin não
promove replay. Esta mudança trata exclusivamente de vídeo; alterações
paralelas de photo-polish no workspace são preservadas, fora deste recorte.

O plano declara grafismos, imagens auxiliares e viewport/PIP. Runtime próprio
executa essas camadas, crop e relógio da EDL; guarda V2 verifica execução e
recusa pintura não declarada. Cover continua quando escolhido, além de logo do
kit, texto puro legível/scrim e scene-visibility. Desenvolvimento exige mudança
sustentada de composição e grafismo realmente exposto, não escondido atrás da
fonte. Review `adequate` recusa o anti-padrão take+texto+crop mínimo.

Remonte com áudio admite cortes com margem de 120ms em silêncio medido ou
intervalos ASR confiáveis; risco retorna `MOTION_VIDEO_SPEECH_CUT_UNSAFE`.
Saída pode encurtar: vídeo, áudio original, música e restauração do checkpoint
usam a mesma duração/EDL. Mix usa seleção autorizada ou cache do mesmo negócio,
com reserva zero, duck somente na música e SFX CC0 já existentes. Cache vazio
registra indisponibilidade; este caminho nunca chama o provedor de música.

Temporal, identidades duráveis, audit/outbox, RLS e HTML/Chromium/FFmpeg
permanecem. Sem chamada paga, compra, captura do Café, deploy ou reload.
Testes técnicos não constituem E2E nem nota perceptual. MP4 autorizado e revisão
do titular vs 41 refs/Maestros continuam pendentes. Detalhes e validação no
replanejamento de qualidade de 24/11.

Validação: 179 testes Python do recorte (100% linhas/branches em cinco serviços),
299 Node (100% linhas/branches/funções nos oito módulos medidos), 12 integrações
PostgreSQL `_test`, quatro provas Chromium sintéticas e uma prova FFmpeg de áudio
passaram. Ruff/formato do recorte e mypy de 11 módulos passaram. Trinta assets
históricos A/B conferidos byte a byte, intactos. `make ci` segue bloqueado por
66 lints preexistentes; 20 falhas unitárias antigas de feedback/áudio foram
reproduzidas em HEAD isolado. Regressão ampla final: 1867 passaram e somente essas
20 falharam (mesmo conjunto de HEAD). CI/cobertura globais e aceite audiovisual pendentes.

## 24/11/2026 — photo-reel: polish-v7 allowlist de grafismo declarado

Reel estático (fotos) separado do video-reel. Novas capturas:
`motion-photo-polish-v7` + `photo-polish-v5.js` + `instagram-reel-photo-v21`.
`role=graphic` declarado é allowlist; residual sem plano continua DECORATION.
Cover/crop/legibilidade/Music e replay v1–v6 intactos. Sem MP4 E2E nesta fatia.

## 24/11/2026 — video-reel: replano por qualidade (fim das proibições-teto)

Titular: norte = máxima qualidade alinhada às ~41 refs + Maestros. Proibições
de grafismo (vídeo UNPLANNED / photo `DECORATION_FORBIDDEN`+T3), remonte com
áudio e VR6 “unavailable” foram atalho de gate — remover. Plano = allowlist;
congelamento Café reaberto para capacitar decoração declarada (sem afrouxar
cover/crop/legibilidade). Doc/prompt:
[motion-video-reel-qualidade-replanejamento-2026-11-24.md](../design/motion-video-reel-qualidade-replanejamento-2026-11-24.md).
Sem implementação nesta entrada documental.

## 24/11/2026 — Fatia C autorizada após rejeição do MP4 Fatia B

Titular rejeitou `versao-1 (16).mp4`
(`b1c3a153364e4129061fe705520a9c49531814664f8c6147cfa707be73e3607a`),
run `8ab63903…` (v21/edit-v2/v4): take contínuo + textos/scrim + crop mínimo;
sem camadas, grafismo, transição forte nem trilha/SFX. Review `adequate` ≠
aceite. Síntese vs propaganda **~30–40%** — **não** perto de 70%.

Fatia A+B permanecem. Autorizada **Fatia C** (camadas/saída da fita, grafismo
declarado, transição com função, motion perceptível, mix VR6 com biblioteca
existente). Escopo e prompt:
[motion-video-reel-v1-slice-c.md](../design/motion-video-reel-v1-slice-c.md).
Sem implementação, chamada paga ou novo MP4 nesta mudança documental.

## 24/11/2026 — correção do padding final da EDL (v2)

Run `e5cbf795-c5a7-5506-a275-e184fa7470d3` falhou com
`MOTION_VIDEO_EDL_INVALID`: saída 11200ms, fonte medida 11176ms; cena final
6780–11200ms com in/out 6780–11176ms. A diferença de 24ms é arredondamento
para frame de saída, não corte de fala. O runtime já limitava o seek ao fim
real da fonte, mas o gate do plano v1 exigia durações exatamente iguais.

Novas capturas usam `motion-video-edit-v2`, `instagram-reel-video-v21` e
`business-video-reel-v4`. Somente a última cena pode terminar 1–34ms antes
na fonte, com source_out_ms exatamente igual a source.duration_ms medido pelo
servidor. Sem tolerância em cenas internas, fonte sem duração, fim inventado,
speed ramp ou alteração do áudio. V1/v20/v3 e guarda JS mantêm bytes/pins;
replay v1 continua com o gate original. VR1–VR3, scrim, texto puro, visibilidade
e photo polish permanecem intactos. VR6 continua indisponível.

Validação sintética: 154 testes, 100% linhas/branches nos cinco serviços
medidos (277 statements/122 branches), sem exclusões. Casos de 1/24/34ms,
fonte silenciosa/com áudio, replay v1 e rejeições de cortes internos/fins
não verificados/35ms cobertos. Ruff e mypy do recorte passaram. Mais 32 testes
de wiring/staging e 12
integrações em PostgreSQL dedicado `_test` passaram, com roles restritas e
fornecedores simulados. `make ci` segue nos 66 lints preexistentes. Todos os
193 assets presentes no índice antes desta correção continuam byte a byte iguais.
Revalidação somente em memória do plano capturado: v1 rejeita, v2 passa os
gates de vídeo A+B; isso não é aceite audiovisual.
Run e snapshots do cliente não foram alterados; sem chamada paga, reenvio,
render ou novo MP4. Aceite audiovisual permanece pendente. Worker local
reiniciado com zero runs
ativos: PID 97278 → 3169, carregando v2/v21/v4. Imagem do renderer mantida,
pois a guarda JS não mudou. Pollers workflow/activity do PID 3169 confirmados.
Nenhum snapshot antigo foi promovido.

## 24/11/2026 — lab: Fatia B aplicada (worker + renderer)

Pins B já no disco. Aplicação local: worker creation-lab reiniciado
(PID 97278, skill `instagram-reel-video-v20`, `motion-video-edit-v1`) e
imagem do renderer derivada só com `runner.cjs` atualizado →
`sha256:1e2ecee84e9df1e3b27faf0994dc036782eec67f0bff751301ac7c5d5cf30077`
(inclui `MOTION_VIDEO_EDIT_NOT_EXECUTED`). Imagem `b4d0352f…` preservada.
Fila vazia. Sem chamada paga nem MP4 nesta aplicação; aceite E2E pendente.

## 24/11/2026 — Fatia B: EDL e crop declarados, VR6 indisponível

Implementada extensão pinada `motion-video-edit-v1`, skill
`instagram-reel-video-v20` e repertório `business-video-reel-v3` para novas
capturas. O contrato/guarda VR1–VR3 e scene-visibility-v1 permanecem intactos;
replay sem extensão B não recebe EDL nem regras novas. Photo-reel Café e bytes
polish photo v1–v6 continuam congelados.

B exige pelo menos duas cenas contíguas com funções editoriais distintas,
in/out explícitos na fonte, intenção de crop e corte perceptível entre cenas.
Cada segmento tem pan/scale linear declarado; play-through com só troca de
texto falha. A guarda confere tempo real da fonte e matriz de crop em todo seek,
inclusive reverso, além da guarda A de cover, logo, texto puro e scrim estável.
Não libera grafismos ou assets extras. Storyboard e render compartilham a
mesma montagem; hash do código executado permanece na identidade durável.

Escopo conservador de fala: com áudio original, EDL usa intervalos contíguos
da fonte e cortes de reenquadramento; não elimina palavras nem remixa a faixa.
Sem áudio, permite remonte temporal. Duração final igual à original nesta
versão. Trims/remonte temporal com fala e duração reduzida são trabalho futuro,
não promessa desta entrega. VR6 tem estado capturado
`unavailable / edl_music_mix_not_qualified`: sem música/SFX novos ou provedor.
O mixer existente preserva uma única faixa original e não foi estendido nesta
fatia; biblioteca existente não equivale a mix qualificado para EDL.

Validação: 591 testes aprovados e duas falhas de áudio preexistentes,
reproduzidas em checkout isolado de HEAD; 100% linhas/branches nos oito módulos
Python medidos (696 statements/302 branches), sem exclusões novas. 295 testes
Node aprovados, 100% linhas/branches/funções nos seis módulos medidos. Dez
integrações em PostgreSQL dedicado `_test`, roles restritas e fornecedores
simulados passaram. Três provas Chromium sintéticas passaram (B, A e
scene-visibility), sem MP4. Ruff/formato do recorte e mypy de sete módulos
passaram. `make ci` continua bloqueado nos mesmos 66 lints preexistentes;
CI integral/cobertura global permanecem pendentes.

Pins e limites detalhados em `docs/design/motion-video-reel-v1-slice-b.md`.
Sem chamada paga, captura do cliente, deploy/reload ou novo MP4. Não há aceite
E2E: depende de execução posteriormente autorizada e revisão do titular.

## 24/11/2026 — Fatia B autorizada após rejeição criativa do MP4 Fatia A

Titular rejeitou `versao-1 (15).mp4`
(`f446d636d8ad24388c00603478f34153698ed195dc0ad2aa81962cda008550e9`),
run `86990c48…`: Fatia A passou nos gates (cover, logo, tipografia, v19,
scene-visibility) e a review automática marcou `adequate`, mas a peça é só
gravação integral + textos com scrim — sem EDL, motion no vídeo, grafismos
planejados, acervo de apoio ou trilha. Gate ≠ qualidade.

Fatia A permanece; não desfazer VR1–VR3. Autorizada a **Fatia B** (VR4–VR5;
VR6 só com biblioteca de áudio já existente ou estado explícito de
indisponível). Escopo, critérios e prompt em
[motion-video-reel-v1-slice-b.md](../design/motion-video-reel-v1-slice-b.md).
Photo-reel Café continua congelado. Sem implementação, chamada paga ou novo
MP4 nesta mudança documental.

## 24/11/2026 — runtime de visibilidade por cena, além da orientação

Implementado `motion-video-scene-visibility-v1`, com código/hash pinados no
snapshot de novas capturas vídeo. O executor aplica display:block no scrim da
cena ativa e display:none nos demais, antes e depois do seek do modelo. Assim,
o texto ativo é mensurável e o código gerado não deixa scrims de outras cenas
sobrepostos. O runtime resolve todos os text_element_ids e exige pais exclusivos;
DOM ausente/duplicado, pais compartilhados ou conteúdo extra falham com
MOTION_VIDEO_SCENE_SCOPE_INVALID. Não oculta nós desconhecidos nem modifica
beats, opacidade, fonte, posição, vídeo, logo ou o plano.

Storyboard e render usam o mesmo serviço de montagem: implementação → escopo
de cena → guarda vídeo v1 intacta. O hash do scene_init executado continua na
identidade durável do efeito. Contrato ausente preserva bytes de execução antigos;
previous não ganha o runtime retroativamente. Photo não recebe esse contrato.
Skill v19 e repertório v2 permanecem pinados sem mudança de bytes. Não é mais
uma tentativa de resolver esta falha apenas por prompt.

Validação: 451 testes Python, 291 Node e oito integrações em PostgreSQL `_test`
com roles restritas/fornecedores simulados. 100% linhas/branches nos seis módulos
Python medidos (551 statements/238 branches), incluindo o novo serviço; 100%
linhas/branches/funções no novo JS e nos quatro módulos Node do renderer. O
Makefile inclui o runtime novo na cobertura, sem exclusões. Chromium reproduz
o problema em duas cenas, cobre 337 instantes e seeks reversos/fronteiras,
e mantém rejeições de BR, grafismo desconhecido e pai não exclusivo. Prova local
adicional com o código capturado do run `3e690872…`, mídia sintética e runtime
pinado: 345 seeks passaram, sem MP4. Isso não é aceite audiovisual.

Ruff/formato do recorte passaram. Mypy aponta somente a chamada preexistente sem
tipo a feedback_context em motion_context; CI integral/cobertura global seguem
pendentes. make ci continua bloqueado nos 66 lints preexistentes.
Imagem local derivada do digest anterior foi construída copiando só runner.cjs,
sem credenciais, conteúdo do cliente, novas dependências ou download de base.
Hash interno e código específico de scope foram verificados em contêiner sem
rede. Aplicada no lab após verificar zero runs queued/running: pin local atualizado
para sha256:b4d0352f0403cfe5f1d2e4e387136f78afadf137a7e1dac19f8cfa92c498344b;
worker dedicado reiniciado (PID 68650), com pollers workflow/activity confirmados.
Imagem anterior preservada; nenhum run submetido ou repetido.
Sem chamada paga, reenvio do run, alteração de snapshots ou Fatia B/VR4–VR6.

## 24/11/2026 — video-reel v19: texto puro e diagnóstico seguro do renderer

Run `360588a6…` com v18/v2 passou por plano/implementação e falhou no render.
Simulação local com mídia sintética isolou `<br>` em cena2-convite/cena2-cta:
a guarda exige children.length=0 e recusa os textos no primeiro frame visível.
Substituir apenas os BR em memória eliminou a rejeição nos instantes examinados;
nenhuma alteração foi feita no run. Fundo de leitura e ausência de hastes já
estavam corretos nesta candidata.

Nova skill pinada `instagram-reel-video-v19` exige textContent sem elementos
filhos (incluindo BR/SPAN), com quebra natural ou nova linha real + pre-line
quando houver múltiplas linhas. Mantém medições de texto/scrim, VR1–VR3 e CTA.
Replay v16/v17/v18 permanece com seus pins. Repertório v2 e guarda DOM intactos.
O runner agora traduz somente seis códigos exatos da guarda vídeo recebidos do
Playwright para o protocolo de erro, e o adapter aceita os mesmos códigos.
Prefixo conhecido de page.evaluate é tratado; stacks/conteúdo não são emitidos.
Erros desconhecidos continuam MOTION_RENDER_EXECUTION_FAILED; photo não ganha
novos códigos ou regras. Isso diagnostica a recusa, não aprova a composição.

Validação: 405 unitários Python, 286 Node e oito integrações locais em PostgreSQL
`_test` com roles restritas/fornecedores simulados. 100% linhas/branches nos cinco
módulos Python medidos (adapter HTML, skills, repertoire, video_reel e
video_requests: 522 statements/228 branches); 100% linhas/branches/funções nos
quatro módulos Node medidos, incluindo runner. Sem exclusões novas. Chromium
executa exemplo v19 com texto puro multilinha, todos os frames/seeks reversos,
e recusa BR/SPAN; o erro real atravessa o mapeamento seguro. Duas falhas de áudio
na seleção ampliada foram reproduzidas no índice anterior isolado; não mascaradas.
Ruff/formato e mypy do recorte passaram; make ci segue bloqueado nos 66 lints
preexistentes. CI integral/cobertura global continuam pendentes.

Dos 184 arquivos históricos comparados, só runner.cjs mudou, para diagnóstico;
183 assets/validador permanecem intactos, inclusive skills antigas, repertório,
guarda e polish photo. Sem chamada paga, MP4, reload ou alteração de snapshots.
Aplicação operacional requer worker com v19 e imagem do renderer reconstruída
com o novo runner, usando seu digest explícito; não foi feito deploy. Imagem
antiga mantém o diagnóstico genérico. Sem Fatia B/VR4–VR6 ou aceite E2E.

## 24/11/2026 — video-reel v18: fundo de leitura e overlays compatíveis com DOM

Run `c516f97b…` com v17/v2 passou pelo plano e implementação, mas terminou em
MOTION_RENDER_EXECUTION_FAILED, sem versão MP4 registrada. Diagnóstico local em
Chrome com mídia sintética reproduziu fundo de leitura alpha≈0,04 aos 33ms
(mínimo 0,75) e hastes rejeitadas como UNPLANNED_OVERLAY aos 650ms. O fundo
multiplicava seu alpha pelo fade do texto; declarar role=graphic não autoriza
esse overlay na guarda vigente. O código genérico não identifica por si só
qual foi a primeira falha no ambiente original.

Nova skill pinada `instagram-reel-video-v18` orienta planejar apenas gravação,
logo e textos com seus scrims, sem hastes/grafismos decorativos. A implementação
mantém alpha do scrim em .75–.8 enquanto texto opacity>0 e opacity=1 no pai;
fade só no próprio texto. Exemplo JS pinado na skill posiciona o fundo por
left/top absolutos, preserva translate/opacity do texto e não acumula deslocamento
em seeks reversos. Quando o texto é exatamente invisível, o fundo pode ser
transparente. Não remover do HTML, às escondidas, elementos de um plano aprovado.

Validação: 201 unitários, 100% de linhas/branches nos serviços motion_skills,
motion_repertoire, motion_video_reel e motion_video_requests (178 statements,
78 branches), sem exclusões. Teste Chromium executa o JS extraído da skill em
todos os 91 instantes de frame e seeks reversos; rejeita scrim com fade, fade no
pai e haste declarada no plano. Sem vídeo de cliente, MP4 ou provedor no teste.
183 arquivos históricos de assets/validador comparados: bytes intactos, incluindo
polish photo, repertório v2 e guarda DOM. Replay v16/v17 preservado.
Oito integrações passaram em PostgreSQL dedicado `_test`, roles restritas e
fornecedores simulados. Ruff/formato do recorte e mypy de motion_skills passaram.
`make ci` continua bloqueado nos 66 lints preexistentes;
CI integral e cobertura global 100% permanecem pendentes.

Sem alteração de validate_video_reel/DOM, contratos, runner ou código do run.
Sem VR4–VR6/Fatia B, chamada paga, reload ou novo MP4. Novas capturas precisam
carregar o código atualizado; snapshots antigos não são promovidos. Aceite E2E
continua dependendo de execução autorizada e revisão do titular. O diagnóstico
genérico do renderer permanece; propagação segura de códigos é trabalho separado.

## 24/11/2026 — video-reel v17: transform próprio em cada texto

Run `028a10c5…` confirmou v16/v2 e wiring automático ativos, mas os dois textos
da cena final usaram enter → hold → exit, sem transform. Deslocamentos de
entrada/saída e das hastes não substituem essa fase no próprio texto.
Nova skill pinada `instagram-reel-video-v17` explicita a obrigação para cada
text_element_id, inclusive título/CTA finais, e inclui beats JSON canônicos
com enter → transform → hold → exit. Transform linear/visível desloca ≥4px;
CTA preserva hold ≥1500ms. Exemplo e plano de duas cenas passam pelo gate real.

Validação: 199 unitários e oito integrações em PostgreSQL dedicado `_test`,
roles restritas/fornecedores simulados; 100% linhas/branches nos serviços
motion_skills, motion_repertoire, motion_video_reel e motion_video_requests
(178 statements/78 branches), sem exclusões. Regressão recusa falta de transform
em cada texto isolado e nos dois juntos, mesmo com grafismo animado e enter/exit
com deslocamento. Payload real transmite a orientação; replay v16/v2 preservado.
182 arquivos históricos de assets/validador conferidos byte a byte: intactos.
Ruff do recorte passou; `make ci` permanece bloqueado nos 66 lints preexistentes.
CI integral e cobertura global 100% continuam pendentes.

Sem alteração do gate/DOM, repertório v2, contratos de captura ou photo polish.
Sem VR4–VR6, nova chamada paga, alteração do run, reload ou MP4. A nova skill
vale para novas capturas com código atualizado; replay não promove v16 para v17.
Aceite audiovisual depende de execução autorizada e revisão do titular.

## 23/11/2026 — video-reel: orientação por cena e captura automática do lab

Implementado `instagram-reel-video-v16` com SHA fixo: cada cena declara VIDEO
`assets/source.mp4` e IMG `assets/logo.png`, IDs locais em video_layout e
staging; não herda nós da cena anterior. Briefing soft pode usar uma cena
contínua. Multi-cena repete nós, preservando tempo absoluto/áudio da gravação.
VR3 mantém enter/exit nas fronteiras, sem hold fantasma e CTA visível ≥1500ms.
A orientação adicional de uso do repertório fica na skill v16: os bytes/pins
já capturados de `business-video-reel-v2` permanecem intactos para replay.

LabMotionRequests prepara novos pedidos com vídeo para planejamento automático;
`proposed-video-output-v1` deriva do contrato produtivo da Fatia A, com validação
automática antes da implementação, sem alegar aprovação humana ou inserir
checkpoints. Captura quality-v2, staging-v1 e `business-video-reel-v2`. Evidência
usa o frame inicial (0ms), já amostrado pelo preparador, sem inventar observações
sobre o vídeo. `previous` não é promovido: v15 sem repertório, v15/v2 e v14/v1
mantêm os snapshots. Photo e seus contratos/polish v1–v6 permanecem intactos.

Validação: 192 unitários do recorte e oito integrações locais em PostgreSQL
`_test`, roles restritas e fornecedores simulados. 100% de linhas/branches em
motion_skills, motion_repertoire, motion_video_reel e motion_video_requests
(178 statements/78 branches); motion_generation também atingiu 100% na suíte
ampliada. Todas as linhas/ramificações alteradas em schema/capture/wiring foram
exercitadas, sem exclusões. Isso não significa 100% dos módulos legados inteiros:
a medição ampliada com lab/context/schema ficou em 85,79%. Suíte ampliada:
1746 aprovados e 20 falhas, idênticas às reproduzidas no índice anterior isolado
(1737 aprovados). `make ci` bloqueado nos mesmos 66 lints preexistentes;
CI integral/cobertura global continuam pendentes. Ruff/formato do recorte passam.
181 arquivos históricos (assets e validador vídeo) comparados: bytes intactos.

Sem afrouxar validate_video_reel, DOM ou LAYOUT_REQUIRED; sem VR4–VR6/Fatia B,
chamada paga, reload ou novo MP4. Aceite E2E continua pendente de captura
explicitamente autorizada e revisão do titular.

## 23/11/2026 — video-reel: LAYOUT_REQUIRED multi-cena + repertório lab (só docs)

Run `da6dd899…` (skill v15) falhou: cenas 2+ sem video/logo nos `elements`;
`repertoire=None` no snapshot lab (staging não arma sem `propose_direction`).
Correção pendente: orientação por cena + wiring lab → v2. Sem afrouxar gate.
Ver [layout-per-scene](../design/motion-video-reel-v1-layout-per-scene-2026-11-23.md).

## 23/11/2026 — reforço de orientação VR3, sem alteração do gate

Novas capturas usam `instagram-reel-video-v15` e, no staging padrão, o
`business-video-reel-v2` (revisão do v1). Pins de skill, manifesto e conteúdo
foram adicionados; v14/v1 permanecem carregáveis para replay. Repertório
explicitamente selecionado continua respeitado. As regras transmitidas exigem
que cada texto cubra a cena: primeiro beat enter em scene.start_ms, último
exit em scene.end_ms, continuidade, nenhum hold opacity=0 e invisibilidade
somente via enter/exit. CTA final com hold estável visível ≥1500ms entre ambos.
Exemplo canônico pinado no repertório é validado pelo gate existente.

`VIDEO_REEL_CONTRACT`, validate_video_reel e DOM guard permanecem intactos;
não há mudança nos bytes/replay photo polish v1–v6. Testes sintéticos reproduzem
a topologia de pausa/tempo/cta do run `853327f8…`, isolada e conjuntamente,
sem usar conteúdo do cliente nem alegar seus tempos intermediários exatos.
Validação: 118 unitários aprovados; 100% de linhas e branches nos serviços
motion_skills, motion_repertoire e motion_video_reel (174 statements/78 branches),
sem exclusões novas. Três integrações aprovadas em PostgreSQL dedicado `_test`,
roles restritas e fornecedores simulados. Ruff/formato do recorte e mypy desses
três serviços passaram (cache temporário limpo). Os 175 assets existentes,
contrato, validador e DOM guard foram comparados com o índice inicial: bytes
intactos. A suíte adicional contexto/photo teve 52 aprovados e 18 falhas;
as mesmas 18 falhas foram reproduzidas em checkout isolado do índice anterior.
`make ci` executado, bloqueado nos 66 lints preexistentes. CI integral e
cobertura global 100% continuam pendentes; não houve correções fora do escopo.

Sem VR4–VR6/Fatia B, chamada paga, captura, reload, MP4 ou aceite E2E.
Próximo passo depende de autorização para nova captura e revisão do titular.

## 23/11/2026 — video-reel: gate cinético recusou generate (só docs)

Run `853327f8…` com Fatia A ativa (`instagram-reel-video-v14` +
`motion-video-reel-v1`) falhou em `MOTION_VIDEO_KINETIC_TEXT_REQUIRED`: cover e
logo ok; textos com hold opacity-0 nas pontas. Sem afrouxar o gate; correção
pendente via skill/repertório. Ver
[kinetic-text-gate](../design/motion-video-reel-v1-kinetic-text-gate-2026-11-23.md).

## 23/11/2026 — web lab: prévia pós-review sem parecer falha de sistema

No `local-spark-web`, copy do creation-lab deixa claro que
`artifact.recorded` é prévia técnica e que `MOTION_MANDATORY_REVIEW_FAILED`
mantém a versão para download sem seleção automática. Estados `failed` passam
a “Sem conclusão automática”; sem mudança de API, Temporal ou seleção.

## 23/11/2026 — video-reel Fatia A implementada: VR1–VR3; aceite pendente

Novas capturas vídeo usam contrato `motion-video-reel-v1`, skill
`instagram-reel-video-v14` e repertório staged `business-video-reel-v1`.
Plano e DOM exigem gravação full-bleed cover 9:16, logo autorizado discreto,
tipografia cinética legível sobre a ação e CTA estável ≥1500ms. Cartaz/janela,
label fixo hero e rodapé de slide são recusados. O briefing de pausa aconchegante
permanece soft. Storyboard e render usam a mesma guarda pinada e identidade de
efeito existente; snapshots antigos e polish photo v1–v6 não mudam.

Validação: 34 testes do contrato, serviço novo com 100% linhas/branches; Chromium
com material sintético e seeks completos/reversos; 284 Node; três integrações
PostgreSQL dedicado `_test` com roles restritas e fornecedores simulados. Ruff
do recorte e mypy do serviço novo passaram. `make ci` bloqueado nos 66 lints
preexistentes; os quatro erros mypy de context/AI e as 20 falhas existentes de
fixtures/diagnóstico continuam pendentes. Comparação em HEAD isolado confirmou
as falhas existentes; a suíte motion terminou com 1725 aprovados e essas 20 falhas.
140 arquivos históricos de assets foram comparados byte a byte com HEAD.
Não houve exclusões para elevar cobertura.

Sem VR4–VR6, música nova, TTS/avatar/Remotion, chamada paga, novo MP4 do cliente,
reload ou aceite E2E. Temporal e tetos 60s/50MiB/uma gravação preservados.
Aguardar autorização para **uma captura** e revisão humana; Fatia B somente
mediante novo pedido. Detalhes: [contrato da Fatia A](../design/motion-video-reel-v1-slice-a.md).

## 23/11/2026 — ensaio video-reel v1 rejeitado: gaps VR1–VR6 (só docs)

Titular rejeitou `versao-1 (13).mp4` (hash `04973908…`, ~11,2 s): cartaz creme,
nome “Café Aurora” fixo, vídeo inset, frase/CTA no rodapé, narração sem música
nem transições/motion — longe das ~41 refs de propaganda e do briefing soft.
Entrada `dd3f0265…`; run `0a24112c…` (review failed pós-MP4). Photo-reel Café
permanece congelado. Backlog VR1–VR6 (cover full-bleed, marca kit, tipo sobre
ação, EDL, motion suave, mix) e prompt em
[motion-ensaio-cafe-aurora-video-reel-v1-gaps-2026-11-23.md](../design/motion-ensaio-cafe-aurora-video-reel-v1-gaps-2026-11-23.md).
Só documentação; sem código, chamada paga ou novo MP4.

## 23/11/2026 — revisão photo: evidência de leitura do CTA, temporal-v5

Diagnóstico read-only sob RLS do run `f939401c…`: MP4 `35d26da0…`
registrado (2.054.826 bytes), mas review `insufficient_evidence`, sem issues.
A revisão só observou CTA em 13767/14967ms (1200ms), marcou reading_time
uncertain e não selecionou candidato; daí `MOTION_MANDATORY_REVIEW_FAILED`.
Isso não comprova CTA curto nem falha do render. Run/MP4 não foram alterados.

Novas capturas photo com staging usam `motion-temporal-v5`: evento reading
vinculado ao CTA final, amostras antes/na entrada, primeiro frame a partir
dela, meio e último frame real. O manifesto mantém limite 48 frames/16 eventos,
lista omissões e exige cobertura para checks pass. Informa janela planejada,
mínimo 1500ms e fim da exposição do último frame; orientação distingue esses
dados da evidência visual e não exige frame inexistente em 15000ms.
Plano não aprova pixels; evidência insuficiente continua uncertain.
Storyboard e revisão usam a mesma seleção. Capturas vídeo e replays temporais
v1–v4 permanecem intactos; comparação local confirmou tempos/manifestos
históricos idênticos. Polish-v6 e demais gates não foram modificados.

Validação: 430 unitários passaram, incluindo entrada do CTA em limite de
frame e fora dele, janela mínima, ausência de amostra bloqueando pass, replay
v4 e uso dos mesmos índices no storyboard. `motion_temporal.py`: 100% de
linhas (142 statements) e branches (66), sem exclusões. Ruff/formato do recorte
passaram; mypy dos três serviços temporais passou. Mypy dos cinco módulos
reporta quatro erros em trechos não alterados de motion_context/motion_ai.
`make ci` continua bloqueado pelos 66 lints preexistentes; cobertura global
100%/CI integral pendentes. Nove integrações de captura/staging passaram
com PostgreSQL dedicado _test, roles restritas e fornecedores simulados.

Correção de evidência, sem reabrir qualidade/polish do Café congelado.
Sem fornecedores pagos, render novo, reload de worker, reenvio do run ou aceite E2E. A nova
política vale para novas capturas; não recupera automaticamente o run
histórico. Reavaliação produtiva paga e recuperação explícita continuam fora
desta execução. `run.failed` ainda usa o código genérico existente.


## 23/11/2026 — photo-reel Café congelado; próximo = Reel vídeo do cliente

Titular aceitou congelar o loop de qualidade do **reel com fotos** no Café
Aurora após `versao-1 (12).mp4` (hash `35d26da0…`) com polish-v6: **cover
full-bleed ok** (Stories do `(11)` corrigido); **energia ainda fraca** (~86%
quase-estático / holds ~2 s no pipeline local), abaixo de `cefe9071` no olho.
Tipografia/copy/fecho ok; mix −31,5 intacto. Estimativa ~60–65% propaganda /
~70–75% briefing soft. Go de parar = cover + sem regressão tipográfica, não
80% nem = cefe em movimento. **Sem V2**, sem nova rodada de polish, sem mudar
briefing. Próximo ensaio de formato: Reel com **vídeo enviado pelo cliente**
(testes de criação). Depois: 4 cenários nos outros 2 negócios; só então story
vídeo + carrosséis. Teto/energia/U4 adiados. Detalhe em
[motion-ensaio-cafe-aurora-v13-freeze-2026-11-23.md](../design/motion-ensaio-cafe-aurora-v13-freeze-2026-11-23.md).
Só documentação nesta mudança.

## 23/11/2026 — última rodada Café V1 implementada: polish-v6

Autorização do titular para V1 cover+energia, preservando o briefing de pausa
aconchegante. Novas capturas usam `motion-photo-polish-v6` e a guarda pinada
`photo-polish-v4.js`. Replays v1–v5 conservam regras, admissão e bytes do
executor; cinco hashes históricos são conferidos em regressão. Timing-v1,
finish-v1, readability-v1, intent v10, crop v5 e demais gates permanecem.

V6 fecha a exceção S1: todas as cenas exigem cover, inclusive gancho e último
frame; não há contain_blur nem exceção por foto paisagem. DOM verifica IMG
primária carregada, object-fit, geometria full-bleed e ancestrais, inclusive
na entrada do destino durante overlap. U2 passa a exigir transforms N2
lineares sem lacunas em toda a cena, com estados iguais entre beats; só a
dissolução de saída validada até o fim da cena dispensa seu movimento.
O destino já deve estar cover e em movimento. Texto energético não substitui
foto; O2/Q2 continuam independentes. Plano inviável exige outro material ou
revisão, sem relaxar crop/S3. Ambiente somente quando elegível no inventário.

Orientação favorece conversão por cover imediato, ritmo suave, leitura e
convite CTA, sem reescrever pedido, inventar oferta/urgência ou hard-sell.
U1 e Music preservados; sem U4, TTS/avatar ou renderer novo.

Validação local: 278 unitários photo, 94 testes Node, oito testes Chromium
e três integrações PostgreSQL dedicado `_test` com roles restritas passaram.
Chromium v6 cobre 451 seeks a 30fps, fronteiras/reversos/overlap e rejeições
de contain, janela horizontal, recorte/blur ancestral, foto oculta/duplicada,
hold, execução só nos endpoints e cancelamento por ancestral; imagens
sintéticas e rede interceptada. Serviço polish: 100% linhas (108 statements)
e branches (64), sem exclusões; Ruff/formato e mypy do recorte aprovados.
`make ci` executado com cache temporário, bloqueado nos 66 lints preexistentes.
CI integral/cobertura global 100% continuam pendentes. Provas DOM não medem
qualidade perceptual nem substituem comparação audiovisual com cefe.

Sem chamada paga, novo MP4, reload de worker ou aceite E2E. Ainda falta
ensaio audiovisual autorizado e revisão do titular: go = pelo menos
`cefe9071` no olho em cover + movimento, não 80% propaganda. V2 estreito
somente se o titular pedir; depois congelar Café. Não iniciar outra rodada
automaticamente. Alterações documentais preexistentes foram preservadas.


## 23/11/2026 — pós-ensaio v12: documentar V1 cover+energia, não implementar ainda

Titular rejeitou o caminho de mudar o briefing só para subir propaganda.
Ensaio `versao-1 (11).mp4` (hash `456928a6…`) fechou o render com polish-v5,
melhorou tipografia vs v11 (sem blob) e copy de pausa, mas regrediu o gancho
para Stories/letterbox e manteve holds (~84% quase-estático no pipeline
local). Estimativa ~55–60% vs propaganda / ~65–70% vs briefing soft; referência
positiva continua `cefe9071`. Quase 1 semana de rodadas: no máximo **uma**
fatia V1 (cover full-bleed + energia suave no miolo); V2 estreito só se V1
falhar no aceite; depois congelar Café e abrir outros conteúdos/negócios.
U4/mix e reescrita do pedido ficam fora. Detalhe e prompt em
[motion-ensaio-cafe-aurora-v12-gaps-2026-11-23.md](../design/motion-ensaio-cafe-aurora-v12-gaps-2026-11-23.md).
Só documentação nesta mudança; sem código, chamada paga ou novo MP4.

## 23/11/2026 — corrigir timing de handoff e endpoint: polish-v5

Run `8d3e45a9-9814-5d9d-87ae-221bf3a12911` usou v4 e falhou no render.
Replay local com fingerprint canônico idêntico reproduziu
`MOTION_PHOTO_VISIBLE_REQUIRED` em 5033,33ms: transition 4900–5200 começava
antes do destino (5000), portanto não autorizava fade. Ajustando só essa
janela em memória, apareceu `MOTION_PHOTO_TYPOGRAPHY_NOT_EXECUTED` em 13400ms:
wrapper da tagline usava janela exclusiva no fim, ocultando o endpoint do exit.

Correção produtiva para novas capturas: `motion-photo-polish-v5` mantém v4 e
acrescenta gate de exit da foto primária: transition deve coincidir com o beat,
ter duração >0/≤500ms e estar inteiramente na interseção das cenas. Plano
inválido é recusado antes de implementação/render, sem correção silenciosa.
`photo-timing-v1.js`, pinado por hash e instalado antes do scene_init, fornece
`PhotoTimingV1.textVisible` (fim inclusivo), `photoVisible` (fim exclusivo,
exceto fim do reel) e `outgoingOpacity` absoluto/clampado. Orientação ao gerador
exige seu uso nos wrappers, separa preparação narrativa de overlap e inclui
exemplos 5000–5200 e 13200–13400. Não força visibilidade nem relaxa guardas;
implementações que ignorem as regras continuam sujeitas a rejeição.

Contratos e bytes de replay v1–v4 preservados; comparação do executor v4
com a versão staged confirmou igualdade byte a byte. Sem alteração de
finish-v1, intent v10, crop, guardas DOM, Music, TTS/avatar ou renderer.

Validação: 263 unitários photo, 94 Node, sete Chromium e três integrações
PostgreSQL `_test` com roles restritas passaram. Serviço polish: 100% linhas
(91 statements) e branches (52); Ruff/mypy do recorte aprovados. Cópia local
corrigida do run passou pelos 451 seeks a 30fps e seeks reversos/de fronteira,
com previews/fontes locais e rede interceptada. Isso comprova a execução DOM
nessa cópia, não qualidade audiovisual nem recuperação produtiva do run.
`make ci` continua bloqueado pelos 66 lints preexistentes; CI/cobertura global
permanecem pendentes. Sem chamada paga, novo MP4 ou aceite E2E.

Worker dedicado recarregado após confirmar zero runs queued/running. Novo
PID 83474 confirmado como poller de workflow e atividade; run original relido
continua failed com o mesmo código, sem reenviar efeitos.

## 23/11/2026 — U1–U3 implementados: polish-v4, revisão audiovisual pendente

Autorização posterior ao diagnóstico v11: novas capturas usam
`motion-photo-polish-v4`, com `photo-polish-v3.js` pinado por hash. Contratos,
regras e arquivos DOM de polish v1–v3 permanecem intactos e selecionados no
replay. Preservados intent v10, crop v5, M3/N2/O2/Q2/R1–R3/S1–S3/T1–T3,
finish-v1, readability-v1 e guardas v2/v3. Alterações documentais preexistentes
preservadas; esta entrada sucede o diagnóstico, não apaga seu histórico.

U1 limita sombra a uma preta opaca, blur 2–4px e offsets absolutos ≤2px,
mesmo com outro fundo válido. Rejeita radial/gradientes, glow empilhado,
box-shadow/filtro e scrim arredondado. Fundo preto local: alpha ≤0,8,
≤16px além do retângulo do texto por lado, largura <95% e altura <40% do frame.
Sem sombra, T2 ainda exige alpha ≥0,75 no texto/ancestral. Irmão exato
`<texto>-scrim` pode ser mais suave, mas não substitui T2/CTA. Orientação:
região escura → scrim local suave → sombra discreta; família/pesos coerentes.
Não mede contraste de pixels nem garante estética; texto permanece visível
no beat inteiro e CTA conserva ≥1500ms, sem faixa full-width.

U2 acrescenta continuidade da foto primária em cada cena: união ≥80%,
lacunas ≤500ms inclusive bordas, transforms lineares N2 (scale ≥0,01/s ou
pan ≥0,5%/s). Texto relacionado não substitui essa continuidade; O2/Q2
continuam exigidos à parte. DOM confere interpolação absoluta desses beats
nos seeks, inclusive miolo/reverso/final, e rejeita transform ancestral que
cancele movimento. Não mede diff de frames/A5b nem injeta animação. Se o crop
não permitir, o plano precisa de outro material/revisão, sem acelerar à força.
U3 reforça orientação de progressão ambiente/detalhes e mantém os gates T1:
≥min(3,elegíveis) primárias e ambiente elegível por ≥1500ms exclusivos;
sem inventar fotos ou relaxar S3/crop. Classificações seguem declarações
sobre previews, não nova visão/OCR.

Validação: 258 unitários photo, 94 testes Node, seis testes Chromium
(quatro históricos + dois U1/U2 com HTML sintético/rede interceptada) e três
integrações PostgreSQL dedicado `_test`/roles restritas passaram. Serviço
polish com 100% de linhas/branches; Ruff/formato e mypy do recorte aprovados.
`make ci` executado e bloqueado pelos 66 lints preexistentes: CI integral e
cobertura global 100% permanecem pendentes, sem exclusões de produção.

Sem chamadas pagas, novo MP4, reload de worker, alteração de Music/U4,
TTS/avatar ou renderer. Referência positiva continua `cefe9071`; não há
aceite E2E nem recuperação estética comprovada. Próximo ensaio exige nova
autorização e revisão audiovisual do titular.

## 23/11/2026 — pós-ensaio v11: documentar U1–U4, não implementar ainda

Titular pediu análise de `versao-1 (10).mp4` e julgou a peça fraca/pior que
`Cafe-Aurora-render-recuperado-cefe9071.mp4`. Decisão desta mudança: **só docs**
—
[motion-ensaio-cafe-aurora-v11-gaps-2026-11-23.md](../design/motion-ensaio-cafe-aurora-v11-gaps-2026-11-23.md).
Regressão confirmada: ~70% quase-estático (v10 0%); scrim radial/glow preto
passando T2/`polish-v3` mas antiestético; tipografia inconsistente; loop de
closes. Estimativa ~50–55% vs propaganda / ~55–60% vs briefing (v10 ~60–65 /
~70–75). Próxima fatia alvo: U1 legibilidade sem blob, U2 energia contínua de
volta, U3 variedade/ambiente; U4 mix opcional. Melhorias do gerador photo, não
template Aurora. Sem implementação, chamada paga, A5b, Music ou renderer.

## 23/11/2026 — render: scrim local confundido com decoração, polish-v3

Run `0af57d58-b917-59a0-8b0a-c1de66841022` passou pelo planejamento e falhou
no render com `MOTION_RENDER_EXECUTION_FAILED`. Evidências lidas sob escopo do
titular/RLS; executor reconstruído confere com `executed_scene_init_sha256` do
recibo. Replay de seeks em Chromium, com previews/fontes locais e rede
interceptada, reproduziu `MOTION_PHOTO_DECORATION_FORBIDDEN` em 33,33 ms: um
scrim radial preto local, irmão do texto, era classificado como folha decorativa
sem vínculo. O renderer retorna código genérico para essa exceção DOM; não foi
falha de fila, revisão de inventário ou energia do plano.

Novas capturas usam `motion-photo-polish-v3` e `photo-polish-v2.js`, pinado por
hash. Scrim irmão só é admitido com id exato `<id-do-texto>-scrim` associado a
texto declarado e visível, contendo seu retângulo, largura <95% e altura <40%
do frame, vazio/sem filhos, bordas, outlines, pseudo-elementos, sombra, filtro
ou máscara. Pintura limitada a preto sólido/translúcido ou gradiente radial
elíptico preto; considera a serialização Chromium que omite `ellipse` padrão.
Cor, geometria ou nome inválido continuam rejeitados. Scrim irmão não substitui
a proteção T2 do texto/sombra nem a guarda CTA v3. Isso admite suporte local de
leitura, não libera acentos residuais. V1/V2 e guarda anterior permanecem com os
mesmos bytes; replay escolhe o hash/arquivo da versão persistida.

Segundo achado: com a correção aplicada somente em memória, replay passa pelos
scrims e chega a `MOTION_PHOTO_TYPOGRAPHY_NOT_EXECUTED` em 10200 ms. O wrapper do
texto de fecho está com `clip-path: inset(0px 0px 100%)`, escondendo o texto no
início do beat. É violação de finish-v1, que permanece intacto. V3 explicita ao
gerador a visibilidade integral durante enter/exit, incluindo endpoints, sem
máscara/revelação e sem saída de CTA na janela de leitura. **O run salvo ainda
não é renderizável sob todos os gates**; não houve edição automática de HTML,
relaxamento de finish-v1, reexecução produtiva ou recuperação declarada.

Validação: 250 unitários photo, 94 testes Node photo e três integrações
PostgreSQL `_test` com roles restritas passaram. Serviço polish: 100% de linhas
e branches (57 statements/26 branches), sem exclusões. Quatro testes Chromium
passaram, incluindo aceitação de scrims locais e rejeição de nome falso, cor,
faixa, borda, máscara, pseudo-elemento e texto desprotegido, mais regressões de
legibilidade/finish/guardas antigas. Ruff/formato e mypy do recorte passaram.
`make ci` segue bloqueado nos 66 lints preexistentes; CI e cobertura global
permanecem pendentes.

Worker dedicado recarregado após confirmar zero runs queued/running; novo
PID 16391 confirmado como poller de workflow e atividade. Run relido preserva
failed e o código original, sem reenviar efeitos.
Documentos e alterações staged anteriores preservados. Sem chamada paga, novo
MP4, Music/mix, TTS/avatar ou troca de renderer. Sem aceite E2E; nova geração e
revisão audiovisual continuam dependendo de autorização do titular.

## 19/11/2026 — plano rejeitado por energia; orientação numérica polish-v2

Run `5a2a1152-cba8-503b-ba9b-ed5e1ac92b2a` falhou com
`MOTION_PHOTO_ENERGY_REQUIRED` na admissão do plano, antes de implementação/render.
Leitura restrita e replay local com o contexto preparado exato reproduziram a
rejeição: as cenas têm cobertura O2/Q2 de 3550/5000 ms (71%), 3850/5500 ms
(70%) e 3800/4900 ms (77,6%), abaixo de 80%. Lacunas globais chegam a 800 ms,
acima de 500 ms. As fotos têm zoom lento demais para O2; enter/exit dos textos
não contam como transforms energéticos. O mínimo S2 do fecho não substitui O2.
É rejeição válida, diferente do falso positivo da trilha no inventário T1.

Novas capturas recebem `motion-photo-polish-v2`: preserva T1–T3 e acrescenta
orientação para calcular união por cena/global, fases elegíveis, amplitude e
velocidade no mesmo eixo e um exemplo numérico de texto relacionado com 90%
de cobertura em 5 s. A exceção do CTA é explícita: leitura ≥1500 ms e sem saída
até end. Não acelera fotos nem modifica beats automaticamente; crop v5 e tom
aconchegante continuam prevalecendo. Sem reintroduzir gráficos residuais.
`polish-v1` permanece aceito com suas regras exatas; a seleção das instruções
agora usa a versão pinada no snapshot. Novas regras não entram em replay v1.
Gates M3/N2/O2/Q2/R1–R3/S1–S3, intent v10, finish-v1, readability-v1 e bytes/hashes
DOM não mudaram. A mudança melhora a orientação, não garante obediência do modelo
nem torna válido o plano rejeitado. Não há retry automático ou nova chamada paga.

Validação: 249 unitários photo passaram; serviço polish com 100% linhas/branches
(53 statements/26 branches). Regressões sintéticas mantêm rejeitadas as três
agendas deficientes, verificam o exemplo de 90% sem acelerar a foto e o envio
das instruções v2 ao planejador, preservando v1. Três integrações PostgreSQL
`_test` passaram, incluindo pin v2 em lab/WhatsApp. Ruff/formato e mypy do recorte
passaram. `make ci` continua nos 66 lints preexistentes; CI integral/cobertura
global continuam pendentes, sem exclusões produtivas.

Após a interrupção, Docker e dependências locais foram restaurados. Confirmados
zero runs queued/running antes de iniciar o worker atualizado. Processo PID 77326
confirmado como poller de workflow e atividade; o run relido mantém estado failed
e o código original. Nenhum pedido foi reenviado.
Run, snapshot e custos preservados. Sem novo MP4, Music/mix ou aceite E2E.
Próximo ensaio pago continua dependendo de pedido autorizado pelo titular.

## 19/11/2026 — T1: trilha photo-music não é fotografia

Run `badce3e3-1ecc-50eb-bb79-544da8260bfc` falhou com
`MOTION_PHOTO_INVENTORY_REVIEW_REQUIRED` após gerar o plano. Leitura restrita
mostrou quatro fotos e quatro revisões completas; o inventário também continha
`assets/photo-music.mp3`. O gate T1 contava o prefixo `photo-` sem distinguir
fotografia de trilha e cobrava indevidamente uma quinta revisão.

Corrigida a classificação no serviço: entram no inventário T1 apenas os caminhos
`assets/photo-*.png`, formato normalizado pelo preparo fotográfico. Music/mix,
contratos pinados, guardas DOM, S1–S3 e demais gates permanecem inalterados.
Revisão de fotografia faltante continua bloqueada mesmo com trilha presente.
Não há revisão inventada, novo snapshot, retry ou alteração do run falho.

Validação: 244 unitários photo passaram, incluindo regressões com 1/2/3 fotos
mais trilha e admissão integrada do plano; serviço com 100% linhas/branches.
Três integrações PostgreSQL `_test` com roles restritas passaram. Replay local
do plano salvo com o contexto preparado exato passou em todos os gates de plano,
sem rede, render ou persistência. Ruff/formato e mypy do recorte passaram.
`make ci` permanece bloqueado nos 66 lints preexistentes; cobertura global e CI
integral continuam pendentes, sem exclusões produtivas.

Worker dedicado recarregado após confirmar zero runs queued/running. Novo
processo confirmado como poller de workflow e atividade; run relido continua
failed com o código original.
Sem nova chamada paga, MP4 ou aceite E2E. A validação local do plano não prova
qualidade audiovisual; próximo ensaio depende de pedido autorizado pelo titular.

## 18/11/2026 — T1–T3 pós-v10: variedade, leitura e limpeza gráfica

Implementação autorizada pelo titular: novas capturas photo recebem
`motion-photo-polish-v1`, com regras e hash da guarda suplementar pinados.
Preservados os bytes de intent v10, guardas v2/v3, readability-v1, finish-v1,
crop v5, skill v20 e repertório v12; todos os gates anteriores continuam.
Replay sem o novo contrato não ganha regras nem executor novo. O campo opcional
`staging.photo_material_reviews` é omitido quando ausente, preservando a
serialização histórica. Alterações documentais já staged foram preservadas.

T1 revisa **todo** o inventário fotográfico, incluindo materiais não usados:
assunto (`environment/detail/people/other`), identidade, viabilidade de crop e
evidência textual não vazia. Só `clean` + `crop_safe` é elegível. Plano e
composição exigem ≥min(3, elegíveis) fotos primárias distintas, cada uma com
≥1500 ms fora de overlaps; ambiente elegível exige um desses beats. Inventário
insuficiente usa os elegíveis sem inventar imagens; zero elegíveis pede revisão.
Inspeção faltante/duplicada/estranha, seleção inelegível e loop de dois closes
quando há terceiro material elegível são rejeitados. S3/crop v5 prevalecem;
a classificação é declaração do planejador sobre previews, não visão/OCR novo.

T2 verifica todas as frases visíveis e seus descendentes em cada seek: texto
claro ≥24px, sombra(s) preta(s) opaca(s), pelo menos uma com blur ≥2px e offsets
≤4px, ou scrim preto local alpha ≥0,75 que contenha o texto. Reposicionamento
sozinho não constitui evidência DOM suficiente. É uma decisão conservadora de
admissão, não medição de contraste dos pixels. Full-width permanece proibido
por finish-v1; CTA conserva janela ≥1500 ms e readability-v1/v3 integralmente.
T3 restringe esta fatia a fotos/logo/tipografia e scrim CSS: rejeita `graphic`
no plano, bordas/outlines, pseudo-elementos decorativos, SVG/canvas/HR e nós
visíveis sem relação com texto/imagens declarados. Não é classificador estético
nem prova contra oclusão arbitrária; revisão audiovisual continua necessária.

Validação: 240 unitários photo passaram; serviço novo com 100% de linhas e
branches (52 statements/26 branches), sem exclusões produtivas. Três testes
Chromium passaram (23 cenários T2/T3 + 13 regressões anteriores; rede
interceptada, HTML sintético, seeks reversos/finais); 94 testes Node photo com
v3 passaram. Três integrações PostgreSQL no banco dedicado `_test`, com roles
restritas, passaram incluindo captura lab/WhatsApp com o novo pin. Ruff/formato
do recorte e mypy dos cinco módulos de validação/schema passaram. `make ci`
continua bloqueado nos 66 lints preexistentes. A ampliação para testes de
contexto encontrou 18 falhas; as mesmas 18 foram reproduzidas em cópia isolada
de HEAD, sem T1–T3 (19 casos de contexto passaram). CI integral e cobertura
global 100% permanecem pendentes; não há alegação de aprovação global.

Sem chamada paga, A5b, novo MP4, reload de worker, alteração de vídeo,
Music/mix (T4 não autorizado), TTS/avatar ou renderer. Persistência pós-upload,
run failed, objeto recuperado e snapshots históricos intactos. Preservado o
briefing aconchegante/suave de pausa no dia, sem hard-sell. Pendente novo pedido
explicitamente autorizado e revisão do MP4 pelo titular; **sem aceite E2E**.

## 18/11/2026 — pós-ensaio v10: documentar T1–T4, não implementar ainda

Titular pediu análise do MP4 recuperado
`Cafe-Aurora-render-recuperado-cefe9071.mp4` (hash do upload do run
`cefe9071…`; S1–S3 + readability-v1 no snapshot). Decisão desta mudança:
**só docs** —
[motion-ensaio-cafe-aurora-v10-gaps-2026-11-18.md](../design/motion-ensaio-cafe-aurora-v10-gaps-2026-11-18.md).
Evolução clara vs v9 (~60–65% vs propaganda; ~70–75% vs briefing soft): cover
full-bleed, 0% quase-estático, logo/CTA limpos. Gaps: pouca variedade (~2
fotos), contraste tipográfico em madeira clara, acentos gráficos residuais,
mix −31,5 LUFS. Próxima fatia alvo: T1 clima/variedade, T2 legibilidade, T3
limpeza gráfica; T4 mix opcional. Sem implementação, chamada paga, A5b,
Music ou renderer nesta mudança. O run failed e o arquivo recuperado não são
aceite E2E.

## 18/11/2026 — falha pós-upload: timeout ao gravar evidências

Run `cefe9071-7fc5-553a-9de4-709fb802101e` terminou com
`MOTION_EXECUTION_FAILED`. Snapshot contém S1–S3 e readability-v1. Render e
upload têm recibos concluídos; nenhum efeito de revisão foi iniciado. Logs do
PostgreSQL registram `statement timeout` no INSERT de `creation_lab_trace` às
19:45:04 UTC, após o upload, e timeouts de lock de leitores durante a escrita.
O prazo geral de 10 s era insuficiente para a persistência volumosa de evidências.
Não foi outra rejeição das guardas photo nem falha de geração do MP4.

`LabMotionOrchestrator.persist_render` agora prepara/cifra os três envelopes
antes de adquirir o lock. Somente os INSERTs de evidências já limitadas pelo
fluxo recebem `SET LOCAL statement_timeout = '60s'`; antes de emitir o evento,
restaura 10 s. Lock timeout continua 3 s. Versão, traces e evento permanecem
na mesma transação com autorização/RLS e fence; sem IO de rede sob lock.
Cancelamento SQLSTATE 57014 nessa escrita vira código estável
`CREATION_LAB_RENDER_EVIDENCE_TIMEOUT`, sem mensagem SQL ou dados privados.
Outros erros continuam propagados. Não há retry automático ou descarte de frames.

Validação: 268 unitários dirigidos passaram. Três integrações PostgreSQL `_test`
passaram, incluindo operação sintética de 10,1 s sob o prazo específico, retorno
ao prazo geral, evento/frames preservados, fence vencida sem registros parciais,
isolamento de outro ator e concorrência de leitores/escritores. Ruff/formato do
recorte passaram. `make ci` segue bloqueado nos 66 lints preexistentes; mypy do
adapter mantém cinco erros preexistentes nas funções prepare/checkpoints/storyboards.
Cobertura dirigida do adapter: 48% total; o método alterado persist_render teve
todas as linhas e branches exercitadas. Cobertura global 100% continua pendente;
não houve exclusões produtivas.

O MP4 já enviado foi recuperado somente por leitura do armazenamento local:
2.258.806 bytes, hash conferido com o recibo persistido. Cópia privada temporária
em `/tmp/execution-failure-diagnostic/render-preservado.mp4`. Isso não registra
uma versão, não executa a revisão automática nem aprova a peça. Run, snapshot,
ledger e objeto remoto permanecem intactos. Sem chamada paga, reset, novo render,
Music/mix ou mudança de gates. Recuperação produtiva/revisão continua pendente;
não reenviar a geração só para recuperar o arquivo já existente. Sem aceite E2E.
Worker dedicado recarregado após reconfirmar zero runs ativos; pollers de workflow
e atividade verificados. Run relido continua failed com o código original.

## 18/11/2026 — falso bloqueio do CTA com duas sombras pretas

Run `9db92f5c-9ded-5d55-9ea9-b1b01b8ce329`, criado às 15h50 de São Paulo,
falhou com `MOTION_RENDER_EXECUTION_FAILED`. Leitura restrita/read-only e replay
local da composição salva reproduziram `MOTION_PHOTO_CTA_READABILITY_REQUIRED`
em ~12567 ms. O hash do executor reconstruído confere com o efeito persistido.
CTA visível, branco, 34 px e dentro do frame; CSS computado tinha duas sombras
pretas opacas (`0 2px 6px`, `0 1px 1px`). A regex de v2 aceitava só uma sombra:
falso bloqueio estrutural, não comprovação de falta de legibilidade nos pixels.

O snapshot desse run tem intent v10/guarda v2, **sem o suplemento S1–S3**:
a captura ainda foi feita com código anterior. Run, snapshot, custos e efeitos
falhos ficam preservados; não houve retry, reset ou nova chamada paga.

Correção para novas capturas: `motion-photo-readability-v1` seleciona guarda DOM
v3 por hash. V3 aceita uma lista de sombras, todas pretas opacas e pelo menos
uma com blur ≥2px; rejeita ausência, sombra clara/translúcida ou só blur <2px.
Demais bytes lógicos de v2 permanecem: dissolve aprovada, inset zero, CTA desde
cta_read_start com ≥1500 ms, layout, energia e marca. V1/v2 continuam imutáveis;
replay sem a política nova não muda. S1–S3 continuam capturados separadamente,
com intent v10, skill v20 e repertório v12 preservados. Sem renderer novo.

Validação: 275 unitários dirigidos, 94 testes Node photo com guarda v3, duas
integrações Chromium (13 cenários sintéticos) e três integrações PostgreSQL
`_test` passaram. Serviço de seleção novo com 100% linhas/branches; Ruff e mypy
dirigidos passaram. Replay da composição salva com v3 passou em todos os seeks
amostrados a 30 fps, usando previews/fontes locais com rede interceptada; não é
novo MP4 nem reexecução produtiva. `make ci` continua nos 66 lints preexistentes.

Worker dedicado recarregado após reconfirmar zero runs queued/running;
novo processo confirmado como poller das filas de workflow e atividade. O run
falho foi relido e mantém estado/código originais. S1–S3 e a política de leitura
nova estão carregados para futuras capturas; nenhuma execução foi iniciada.

Sem alteração de Music/mix, identidade, TTS/avatar ou orçamento. Pendente novo
pedido autorizado e revisão do MP4 pelo titular; sem aceite E2E.

## 18/11/2026 — S1–S3 pós-v9: suplemento pinado para novas capturas

Implementado por autorização posterior ao diagnóstico. Novas capturas photo
adicionam `motion-photo-finish-v1`, com regras e hash do suplemento DOM pinados.
Intent v10, guarda v2, skill v20 e repertório v12 continuam com os mesmos bytes;
snapshots sem o suplemento não recebem upgrade no replay. Campos de inspeção
nulos são omitidos na serialização histórica. Alterações documentais já staged
foram preservadas.

S1 mantém cover exclusivo ≥2/3 e no máximo uma exceção estruturada/1/3 das
cenas; agora contain+blur dura **no máximo 2000 ms**, inclusive no miolo.
Esse teto é uma decisão conservadora para impedir o beat Stories de ~4 s do v9,
não uma medição estética. Crop v5 prevalece: selecionar outra foto/revisar plano
quando inviável. O suplemento rejeita suporte pintado de texto com largura
≥95% do viewport e altura <90%, no elemento ou ancestrais; scrim local permitido.

S2 mantém M3/N2/O2/Q2/R1–R3 e exige em cada beat de foto/logo após handoffEnd
velocidade mínima de scale 0,01/s ou pan 0,5 pp/s, linear, até end. Pelo menos
um texto do fecho tem entrada/saída numérica linear com amplitude/velocidade O2;
o suplemento confere transform interpolado, visibilidade e ancestrais por seek.
Saída do CTA após handoff é rejeitada; leitura ≥1500 ms, dissolve aprovada,
cta_read_start e inset zero continuam sob a guarda v2 intacta. O suplemento é
instalado antes dela e não injeta animação. Hash do executor composto continua
vinculado ao efeito existente, incluindo storyboard/correção.

S3 exige `staging.photo_identity_reviews` para todas as fotos selecionadas
quando o inventário contém logo do kit. Asset duplicado/estranho, inspeção
faltante/vazia, `third_party` ou `uncertain` bloqueiam o plano; só `clean` segue.
Escolhida rejeição conservadora em vez de crop de marca sem prova geométrica.
Planejador observa os previews existentes, prefere materiais limpos e pede
revisão se insuficientes. Não há OCR/classificador novo nem remoção de marca.
Instrução explícita impede adicionar “Imagens ilustrativas.” por padrão ao CTA;
texto solicitado pelo titular continua autorizado.

Validação local: 273 unitários do recorte passaram; serviço novo com **100% de
linhas e branches** (52 statements/28 branches). 87 testes Node photo passaram
com guarda v2; duas integrações Chromium cobrem 12 cenários sintéticos, sem
rede externa. Três integrações PostgreSQL no banco dedicado `_test` com roles
restritas passaram, incluindo captura compartilhada lab/WhatsApp. `make ci`
executado e bloqueado nos **66 erros de lint preexistentes**; não há alegação
de CI integral/cobertura global 100%. Sem exclusões produtivas. Ruff/formato dos
arquivos Python alterados passaram; mypy dos cinco módulos de validação/schema
passou. `motion_context.py` conserva erro preexistente de `feedback_context`
sem tipagem. Suíte ampliada de motion: 1.622 passaram e 20 falharam; os mesmos
20 casos falharam numa cópia isolada de HEAD (context/feedback e áudio), sem as
mudanças S1–S3. Essas pendências gerais não foram corrigidas nesta fatia.

Limites: inspeção de terceiros é declaração vinculada ao plano, não prova nos
pixels; a guarda não inspeciona oclusão arbitrária por irmãos/pseudo-elementos
nem mede energia perceptiva/contraste. Sem A5b, chamadas pagas, novo MP4,
recarga de worker, alteração de vídeo, Music/mix, TTS/avatar ou renderer novo.
S4 segue fora do escopo. Pendente novo ensaio explicitamente autorizado,
MP4 e revisão audiovisual do titular; **sem aceite E2E**.

## 18/11/2026 — pós-ensaio v9: documentar S1–S4, não implementar ainda

Titular pediu análise de `versao-1 (9).mp4` (evolução clara vs v8; ainda longe
das refs “incríveis”). Decisão desta mudança: **só docs** —
[motion-ensaio-cafe-aurora-v9-gaps-2026-11-18.md](../design/motion-ensaio-cafe-aurora-v9-gaps-2026-11-18.md).
Estimativa ~**55%** vs propaganda das refs (v8 ~35–40%). Cover no gancho/3º
beat e logo transparente ok; miolo ainda Stories; fecho ~3 s estático; materiais
com Belize/Mackbear/watermark; mix −31,5 LUFS. Próxima fatia alvo: S1 cover no
miolo, S2 energia no fecho até end, S3 identidade dos assets; S4 mix opcional.
Sem implementação, chamada paga, A5b, Music ou renderer nesta mudança.

## 18/11/2026 — correção versionada de transições e leitura na guarda DOM

Pedido `3c142412-2331-5166-92ae-cca0724b94a6` encerrou com
`MOTION_RENDER_EXECUTION_FAILED`. Replay local da composição salva em Chromium,
com previews/fontes autorizados, isolou `MOTION_PHOTO_VISIBLE_REQUIRED` em
~3233 ms: a guarda v1 cobrava opacity ≥95% da foto de saída durante dissolução
3200–3600 aprovada, embora a foto de destino já estivesse totalmente visível.
Outro falso bloqueio ocorria em 11100 ms: CTA tinha entrada aprovada
12100–12500, mas era cobrado no fim do handoff; inset zero também era tratado
como recorte. São erros da guarda, não ausência da nova logo transparente.

Novas capturas usam intent v10/guarda DOM v2 pinada. V9/v1 mantêm bytes e
execução originais; skill v20/repertório v12 permanecem pinados. A exceção de
saída só é compilada de staging aprovado, integralmente no overlap e ≤500 ms.
Somente a foto de origem pode perder opacidade: destino precisa estar visível
≥95% e cumprir os gates normais de layout/movimento. Fora da janela, fades
continuam rejeitados; máscara real, janela, energia ausente e placa continuam
bloqueados. M3/fotos/logo até end preservados.

CTA é conferido do maior entre handoffEnd e fim da entrada aprovada até end;
o plano exige ≥1500 ms de leitura contínua. Só inset literalmente zero é
considerado máscara aberta. Não houve correção automática da composição,
replanejamento, nova chamada paga, troca de renderer ou mudança de Music.
O snapshot e o estado falho do pedido foram preservados.

Validação: 409 unitários, 77 testes Node photo e 56 casos rodados com guarda v2,
três integrações PostgreSQL `_test` e sete cenários sintéticos em Chromium
passaram. Recorte intent/quality/energy/hard: 100% linhas/branches. Todos os
seeks da composição salva passaram na comparação local com v2; isso não é
novo MP4, execução produtiva nem aceite audiovisual. Ruff/formato passaram;
mypy dos quatro serviços passou. Adapter mantém erro de tipagem preexistente
na inferência de `frames`. `make ci` segue bloqueado nos 66 lints preexistentes.
Worker dedicado recarregado após confirmar ausência de pedidos ativos.
Pendente nova captura autorizada com intent v10 e revisão audiovisual do titular.

## 18/11/2026 — logo sintética Aurora transparente e execução nova

Correção de procedência: a logo do Café Aurora foi criada pela própria
plataforma como fixture sintética; não dependia de arquivo novo do titular.
Localizado `scripts/fixtures/demo-businesses/cafe-aurora.svg`, o retângulo de
fundo foi removido numa variante `cafe-aurora-transparent-v1.svg`, preservando
literalmente todos os demais elementos. PNG rasterizado localmente em Chromium,
sem geração por IA; arquivos originais mantidos. Inspeção visual e validação
estrutural/alpha passaram: 1000×400, alpha 0–255, 384.612 pixels transparentes.

Pelos serviços de marca, upload e confirmação com autorização/RLS/auditoria:
logo `1b45cfc7-576a-5852-abbc-79d622ff9e35`, kit confirmado v4. Apenas a
referência à logo mudou; demais escolhas do kit preservadas. O PNG normalizado
recuperado do armazenamento também conserva transparência. Não houve alteração
de gate, credenciais, Music ou renderer.

Nova execução autorizada `3c142412-2331-5166-92ae-cca0724b94a6`, com briefing
anterior e orçamento de US$ 3. Snapshot novo
`fedf00b4-99da-578c-bf44-aa1fc2a9bc3f` confirmou intent v9 e a nova logo;
nenhum snapshot/estado do pedido falho foi reutilizado ou reescrito. Validação
operacional: `running`, catálogo/preparação recebidos e planejamento submetido.
MP4 ainda pendente; não há aceite E2E. Sem mudança de código de produção nesta
intervenção; verificações de artefatos e serviços, sem repetir CI da fatia R1–R3.

## 18/11/2026 — pedido recuperado bloqueado por logo com fundo incorporado

O pedido `ddf87bad-38a7-509e-a7a9-803560351d72` saiu da fila, mas encerrou
`failed` com `MOTION_STAGING_REQUIRES_PLAN_REVISION`. O planejamento registrou
em `staging.unavailable_materials` que `assets/logo.png` contém placa creme
incorporada e necessita de versão autorizada compatível com overlay transparente.

Conferência local do preview exato enviado ao modelo (512×205): retângulo creme
visível, canal alpha integralmente 255. O loader preserva RGBA ao redimensionar;
a placa não foi acrescentada pelo HTML desta execução. O bloqueio ocorreu antes
da implementação, conforme R3 e `require_staging_materials`; não foi falha do
renderer nem nova paralisação da fila.

Nenhum gate relaxado, identidade editada, retry pago ou estado histórico alterado
neste diagnóstico. Pendente fornecer/cadastrar logo transparente autorizada e
então preparar nova execução; não reaproveitar silenciosamente snapshot antigo.
Sem mudança de código ou testes adicionais; evidência por leitura do trace e
inspeção do anexo. Nenhum MP4 novo ou aceite E2E.

## 18/11/2026 — recuperação autorizada da fila do laboratório

Pedido `ddf87bad-38a7-509e-a7a9-803560351d72`: outbox entregue,
atividade recebida pelo worker antigo, mas banco ainda em `queued`, sem efeitos
registrados. Causa interna da paralisação não confirmada. Titular autorizou
recuperar a execução com possíveis chamadas pagas dentro do orçamento existente.

Após reconfirmar ausência de efeitos e de outros pedidos queued/running do
operador, o worker dedicado foi substituído e o mesmo workflow Temporal foi
resetado ao primeiro workflow-task concluído. Identidade do pedido, histórico,
outbox e orçamento preservados; nenhuma edição direta do estado do run.
Nova execução Temporal: `0f033008-9fbf-48ca-931c-a81aee948402`.

Validação operacional: às 14:03 de São Paulo, o banco confirmou `running`,
`catalog=received` e `preparation=claimed`. Pedido saiu da fila; geração ainda
em andamento. Sem mudança de código ou migração nesta intervenção; testes da
fatia R1–R3 não foram repetidos. Não comprova MP4 concluído nem aceite E2E.

## 18/11/2026 — photo R1–R3: enforcement de plano e DOM

Implementado por autorização posterior ao diagnóstico v8. Novas capturas usam
intent/regras photo v9, skill `instagram-reel-photo-v20` e repertório default
`business-reel-v12`, com hashes pinados. Snapshots v1–v8 mantêm contratos,
bytes e execução; campos novos ausentes não entram na serialização histórica.

R1: `photo_layout` obrigatório por cena fotográfica, com foto primária vinculada
a um elemento real. `contain_blur` exige asset, região essencial, alternativas
rejeitadas e movimento seguro; no máximo uma cena e 1/3 das cenas fotográficas.
Cover deve ocupar ≥2/3 da duração total, pela união exclusiva dos intervalos,
descontando sobreposição com exceção. Campo ausente, exceção vazia, Stories
como default ou tentativa de inflar duração por sobreposição bloqueiam o plano.
Crop v5 prevalece: se os materiais não comportam o contrato, revisar o plano.

R2: Q2/O2 permanecem (≥80% por cena, gaps ≤500 ms e magnitude/velocidade).
Helper v12 por cena/beat usa estados aprovados e pan em porcentagem do viewport,
com seek absoluto/reversível. Guarda de DOM versionada envolve o seek existente
no serviço, antes de enviar ao renderer atual; não anima nem corrige crop.
Em cada seek verifica candidato energético visível e matriz CSS interpolada,
rejeitando no-op, ocultação e transforms de ancestrais que possam cancelar motion.
Não basta citar/instanciar helper: o estado executado precisa corresponder ao plano.

R3: `photo_closing` vincula marca e CTA da última cena; só aceita
`transparent_overlay`. Fotos/logo do fecho exigem estados numéricos distintos e
curva linear até end, além de M3. No DOM, fotos cover precisam preencher o frame
9:16 sem janela/clipping; logos são img do PNG autorizado, sem fundo, borda,
padding, sombra ou pseudo-elemento em si/ancestrais. CTA dentro do frame,
visível, fonte ≥24px em 720px, branco com sombra preta local. Contrato deliberadamente
restrito; HTML que não permite comprovar essas condições é rejeitado.

A mesma guarda atende render inicial, correções e storyboard. Hash do executor
composto integra a identidade do efeito; falha interrompe antes de upload/aceite.
O renderer mantém seu erro genérico de execução para exceções JS, sem imprimir
HTML/conteúdo. Sem renderer novo, alteração de vídeo, Music/mix, TTS/avatar ou
A5b. R4 adiado para manter a fatia focada. Alterações documentais previamente
preparadas pelo titular foram preservadas.

Validação: 401 unitários, 65 testes Node photo, três integrações PostgreSQL
no banco dedicado `_test` com logins restritos e uma integração Chromium real
(sete cenários sintéticos, sem rede externa) passaram. Cobertura de linhas e
branches 100% no recorte intent/quality/energy/hard; Ruff e formato dos 18
arquivos Python alterados passaram. `make ci` executado com cache local:
bloqueado nas mesmas 66 ocorrências de lint preexistentes. Mypy dirigido
(12 arquivos) encontrou apenas o erro preexistente de chamada não tipada a
`feedback_context` em motion_context.py. CI integral e cobertura global 100%
continuam pendentes; sem exclusões ou relaxamento de gates.

Limites: são verificações de plano/DOM, não medição perceptiva de energia,
contraste nos pixels, oclusão arbitrária por irmãos ou transparência embutida
no PNG. Placa incorporada ao asset exige revisão do plano, sem editar identidade.
Pendente novo MP4 em ensaio autorizado e revisão audiovisual do titular; sem
chamada paga, novo MP4 ou aceite E2E nesta implementação.

## 18/11/2026 — ensaio v8 Café Aurora: gaps R1–R4 (só docs)

Ensaio `versao-1 (8).mp4`: regressão vs v7 — Stories (janela+blur) o tempo
todo, ~89% quase estático, holds ~4 s, logo em placa creme, mix −31,6 LUFS.
Estimativa ~35–40% vs propaganda incrível das refs. Q1/Q3 soft falharam de
novo. Backlog R1–R4 (enforcement hard de cover/logo) com prompt em
[motion-ensaio-cafe-aurora-v8-gaps-2026-11-18.md](../design/motion-ensaio-cafe-aurora-v8-gaps-2026-11-18.md).
Sem implementação, chamada paga, A5b ou aceite E2E nesta mudança.

## 18/11/2026 — photo Q1–Q3: cover por cena e energia densa

Implementado por autorização posterior ao diagnóstico v7. Novas capturas usam
intent/regras photo v8, skill `instagram-reel-photo-v19` e repertório default
`business-reel-v11`, com hashes pinados. Q1 reforça cover 9:16 em TODAS as
cenas fotográficas; seleção deve priorizar fotos enquadráveis. Contain+blur é
exceção rara, documentada por cena com asset, região essencial, alternativas e
margem; várias exceções exigem rever seleção/composição. Crop v5 prevalece.
Sem campo estruturado de layout, Q1 é instrução e exemplo, não gate geométrico.

Q2 mantém velocidade/amplitude O2, reduz lacunas globais para ≤500 ms e exige
união de intervalos energéticos ≥80% de CADA cena fotográfica, sem contar
sobreposição duas vezes. Energia de outra cena não compensa cena parada.
Overlays text/graphic relacionados na mesma cena continuam disponíveis para
crop restrito. M3 e suas exigências de fecho continuam; N2/O2 históricos não
mudam. O gate verifica declarações, não execução ou visibilidade nos pixels.

O exemplo v11 acrescenta `makePhotoSceneMotion` para cada cena, inclusive miolo:
cover e transform linear durante a leitura, estados/tempos vindos do plano,
seek absoluto/reversível. `preparePhotoBrandOverlay` prepara marca/wrapper
transparentes e contraste do CTA. Q3 proíbe placa/card também em ancestrais e
pseudo-elementos; scrim local pertence à foto. PNG com placa incorporada pede
revisão do plano, não alteração da identidade. CTA separado da saída; fotos e
logo continuam em movimento até end. Helpers exigem adaptação/instanciação em
scene_init e chamada em seek; não são auto-injetados nem gates DOM/pixels.

Preservados snapshots anteriores, seleção explícita, vídeo, Music/mix e renderer,
além das alterações documentais já preparadas pelo titular. Q4 adiado para
manter a fatia focada; sem TTS/avatar, A5b ou chamada paga.

Validação: 273 unitários, 21 testes Node dos exemplos photo e três integrações
PostgreSQL dedicadas `_test`, com logins restritos, passaram. Intent/quality/energy
com 100% de linhas e branches no recorte. Ruff/lint e formato dos arquivos
alterados passaram. `make ci` executado e bloqueado nas 66 ocorrências de lint
preexistentes. Mypy dirigido encontrou o erro preexistente de chamada não tipada
a `feedback_context` em motion_context.py; CI integral e cobertura global 100%
não estabelecidos, sem exclusões ou gates relaxados.

Pendente: novo MP4 em ensaio autorizado e revisão audiovisual do titular para
comprovar cover no miolo, movimento perceptível, logo sem placa e CTA legível.
Não há aceite E2E nem comprovação perceptiva nesta implementação.

## 18/11/2026 — ensaio v7 Café Aurora: gaps Q1–Q4 (só docs)

Ensaio `versao-1 (7).mp4`: melhorou (energia ~2× vs v6; cover no gancho; sem
holds de 6+ s), mas miolo volta a janela+blur, logo em placa creme, mix
−31,6 LUFS. Diagnóstico e backlog Q1–Q4 com prompt em
[motion-ensaio-cafe-aurora-v7-gaps-2026-11-18.md](../design/motion-ensaio-cafe-aurora-v7-gaps-2026-11-18.md).
Sem implementação, chamada paga, A5b ou aceite E2E nesta mudança.

## 18/11/2026 — photo O1–O3: continuidade e magnitude declarada

Implementado por autorização posterior ao diagnóstico v6. Novas capturas usam
intent/regras photo v7, skill `instagram-reel-photo-v18` e repertório default
`business-reel-v10`, com hashes pinados. O1 exige cover 9:16 em cada cena,
inclusive miolo/fecho; contain+blur só por inviabilidade de crop documentada
por cena (região essencial, alternativas e margem). Exceção não se propaga às
outras cenas. Crop v5 continua prevalecendo sobre bleed/energia.

O2 endurece apenas v7: transform linear precisa, no mesmo eixo, de velocidade
de scale ≥0,02/s **e** amplitude ≥0,04, ou pan ≥1 ponto percentual/s **e**
amplitude ≥2 pontos percentuais. Mantém união global, lacunas ≤2500 ms,
overlays text/graphic relacionados na mesma cena e gates M3. Pulsos abaixo
da amplitude não contam; snapshots v6 mantêm os mínimos anteriores. O exemplo
v10 amplia KB, conserva seek absoluto/reversível e mantém CTA separado do
wrapper que sai. Exige adaptação ao crop/plano, instanciação em scene_init e
chamada em seek; não é auto-injetado.

O3 reforça PNG overlay sobre foto, wrapper transparente sem placa/card creme,
CTA com contraste local durante todo percurso e movimento de foto/logo até
end. Não existe campo estruturado de layout no schema atual: O1/O3 são regras
de planejamento/implementação e exemplo, não gates geométricos/DOM/pixels.
O2 mede declarações, não visibilidade ou energia percebida no MP4.

Preservados snapshots históricos, vídeo, Music/mix, renderer e alterações
documentais já preparadas pelo titular. O4 adiado para manter esta fatia
focada; sem TTS/avatar, A5b ou chamada paga.

Validação: 229 unitários, 16 testes Node de exemplos photo e três integrações
PostgreSQL dedicadas `_test` com logins restritos passaram. Intent/quality/energy
com 100% de linhas e branches no recorte. Ruff dos arquivos alterados passou.
`make ci` executado: bloqueado nas 66 ocorrências de lint preexistentes; CI
integral e cobertura global 100% não estabelecidos. Sem exclusões ou gates
relaxados. Pendente: novo MP4 autorizado e revisão audiovisual do titular;
esta implementação não declara aceite E2E nem melhoria perceptiva comprovada.

## 18/11/2026 — ensaio v6 Café Aurora: gaps O1–O4 (só docs)

Ensaio `versao-1 (6).mp4`: melhorou (cover 9:16 na abertura; holds de 6+ s
sumiram), mas miolo regressa a janela+blur, ~88% quase estático entre trocas,
logo em placa creme no fecho, mix −31,6 LUFS. Diagnóstico e backlog O1–O4 com
prompt em
[motion-ensaio-cafe-aurora-v6-gaps-2026-11-18.md](../design/motion-ensaio-cafe-aurora-v6-gaps-2026-11-18.md).
Sem implementação, chamada paga, A5b ou aceite E2E nesta mudança.

## 18/11/2026 — photo N1–N3: cover real, energia declarada e marca sem placa

Implementação autorizada após o ensaio v5. Novas capturas usam intent/regras
photo v6, skill `instagram-reel-photo-v17` e default `business-reel-v9`, com
hashes pinados. Cover 9:16 é o default desde o gancho; janela landscape com
barras blur não é default permitido. Contain sobre fundo fotográfico exige
inviabilidade de crop e justificativa da região essencial, alternativas e margem
em composition/development. Protagonista continua precedendo bleed e movimento.
Logo PNG âncora e CTA são overlays sobre foto, com scrim local, sem placa creme;
micro-movimento até end. N1/N3 são instruções de plano/implementação e exemplo,
não gates geométricos ou inspeção de pixels.

N2 acrescenta gate somente ao intent v6: estados numéricos canônicos
`scale=1.04 x_pct=0 y_pct=0`, curva linear, velocidade média declarada de scale
≥0,01/s OU pan em um eixo ≥0,5 ponto percentual/s. Une intervalos energéticos
no plano inteiro; lacunas >2500 ms geram `MOTION_PHOTO_ENERGY_REQUIRED`, inclusive
começo/fim e fronteiras entre cenas. Prosa diferente, estados iguais, microdrift,
gaps ou fragmentação de beats/cenas não reiniciam a janela. Fotos com crop
restrito podem coordenar overlays text/graphic via related_element_ids na mesma
cena; logo isolada não substitui energia fotográfica. Isso mede declarações,
não execução/visibilidade: não é A5b nem garantia de movimento no MP4.

Gates M3 mantidos para v4/v5/v6, inclusive movimento de todas as fotos/logo no
fecho. O exemplo v9 reforça KB no miolo e mantém seek absoluto/reversível;
exige adaptação ao crop/plano, instanciação em scene_init e chamada em seek.
Intent v1–v5, skill v16 e repertório v8 mantêm bytes/semântica e replay; seleção
explícita continua respeitada. Vídeo, Music/mix e renderer preservados. N4 adiado
para manter a fatia focada. Sem TTS/avatar, chamada paga ou alteração de run antiga.

Validação: 217 unitários, 13 testes Node e três integrações PostgreSQL dedicadas
`_test` com runtime restrito; intent/quality/energy com 100% de linhas e branches
no recorte. Ruff dos arquivos alterados passou. `make ci` executado e bloqueado
nas mesmas 66 ocorrências de lint preexistentes; CI integral e cobertura global
100% não estabelecidos. Sem exclusões ou relaxamento de gates.
Pendente: novo MP4 em ensaio autorizado e revisão audiovisual do titular.
Não há aceite E2E nem comprovação de melhora perceptiva nesta mudança.

## 18/11/2026 — ensaio v5 Café Aurora: gaps N1–N4 (só docs)

Ensaio `versao-1 (5).mp4`: evoluiu (protagonista intacto, logo âncora, fora do
creme puro), mas layout Stories (janela landscape + blur), ~89% quase estático,
hold ~6,6 s no miolo, placa creme no fecho, mix −31,6 LUFS. Diagnóstico e
backlog N1–N4 com prompt em
[motion-ensaio-cafe-aurora-v5-gaps-2026-11-18.md](../design/motion-ensaio-cafe-aurora-v5-gaps-2026-11-18.md).
Sem implementação, chamada paga, A5b ou aceite E2E nesta mudança.

## 18/11/2026 — viabilidade de crop antes da implementação photo

Run `a0a010f8-6ae0-5baf-9d74-514e1d23d8da` falhou com
`MOTION_PLAN_REVISION_REQUIRED`: o implementador declarou que cover 9:16,
foco 22%/50% e scale 1.04→1.112 cortariam xícara/pires, contrariando o plano.
Isso é diagnóstico do modelo, não inspeção independente dos pixels.

Correção: novas capturas usam intent/regras photo v5. Preservação do protagonista
precede full-bleed; planejamento deve avaliar proporção, região essencial e
margem durante todo zoom/pan. Object-position não recupera área perdida por cover.
Reduzir movimento, escolher outra foto autorizada ou justificar foto principal
em contain sobre fundo fotográfico full-frame; sem voltar ao cartão creme.
A orientação precede exemplos numéricos genéricos; não fixa crop da foto real
sem inspeção e não autoriza o implementador a modificar um plano aprovado.
Skill v16/repertório v8 e snapshots v4 permanecem intactos. Gates M1–M3 mantidos
para v4/v5; vídeo, Music/mix e renderer inalterados. Sem gate geométrico/A5b.

109 unitários e três integrações PostgreSQL `_test` passaram; intent/validador
com 100% linhas/branches no recorte. Ruff passou. `make ci` segue bloqueado
nas 66 ocorrências de lint preexistentes. Execução falha não foi reescrita nem
retomada. Sem chamada paga, novo MP4 ou aceite E2E; próxima geração requer
nova captura e revisão visual para comprovar o enquadramento.

## 17/11/2026 — photo M1–M3: anúncio full-bleed, marca âncora e ritmo validado

Pedido do titular implementado em novas capturas: `motion-photo-intent-v4`,
`instagram-reel-photo-v16`, regras photo v4 e default `business-reel-v8`, com
hashes pinados. Full-bleed 9:16 desde o gancho, overlays com contraste local e
foco protegido substituem o cartão creme como default. Inset exige justificativa
na direção. Logo de referência a 32–44% da largura, mínimo orientado 28%
(~202 px em 720); exemplo a 36%, contain/proporção e compensação de padding
pelo preview. Nome tipográfico subordinado à marca.

Gate do plano v4 rejeita `phase=hold` contínuo >2500 ms, somando holds
consecutivos do mesmo elemento. O fecho exige fotos e, quando disponível,
logo PNG na última cena. `handoffEnd` vem da transição staging que chega ao
fecho; sem transição, do fim das entradas da última cena (ou início da cena).
Exige `handoffEnd < duration_ms` e beats `transform` com estados distintos,
sem gaps até end, em todas as fotos/logo do fecho. Cenas e fechos com
desenvolvimento podem durar mais que um hold. Sem janela fixa 11–15 s.

Composição, escala/contraste e tipo de movimento são instruções + exemplo;
não há inspeção geométrica, A5b ou prova de pixels. O gate verifica declarações,
não impede um modelo de descrever movimento sem executá-lo. Helpers exigem
adaptação, instanciação em scene_init e chamada em seek; não são auto-injetados.
Snapshots históricos (inclusive intent v3, skill v15 e repertório v7) mantêm
bytes/semântica; seleção explícita permanece respeitada. Vídeo segue v13/v5.
Music/mix preservados: M4 adiado para manter esta fatia focada em M1–M3.

Validação: 286 unitários; 10 testes Node (v6/v7/v8, tempos variáveis e seek
reverso); três integrações PostgreSQL lab/WhatsApp no banco dedicado `_test`,
com runtime restrito. Intent e novo validador photo: 100% de linhas/branches
no recorte. Ruff/formato dos arquivos Python alterados passaram. `make ci`
executado: bloqueado nas 66 ocorrências de lint preexistentes; cobertura global
100% e CI integral não estabelecidos, sem exclusões ou gates relaxados.
Sem chamada paga, novo MP4 ou aceite E2E. Pendente: ensaio autorizado e revisão
audiovisual do titular; TTS/avatar e renderer fora desta fatia.

## 17/11/2026 — ensaio v4 Café Aurora: gaps M1–M4 (só docs)

Ensaio `versao-1 (4).mp4`: logo PNG pequena no fecho (L1 parcial); energia de
movimento pior que v3 (~82% quase estático vs ~76%); template editorial creme
com fotos em janela; fecho ~4 s morto; mix −31,6 LUFS. Diagnóstico e backlog
M1–M4 (full-bleed, logo âncora, ritmo no plano, mix) com prompt em
[motion-ensaio-cafe-aurora-v4-gaps-2026-11-17.md](../design/motion-ensaio-cafe-aurora-v4-gaps-2026-11-17.md).
Sem implementação, chamada paga, A5b ou aceite E2E nesta mudança.

## 17/11/2026 — photo L1–L3: logo, ritmo do fecho e foto dominante

Implementação autorizada pelo titular após o diagnóstico v3. Novas capturas
photo de produção usam `motion-photo-intent-v3`, `instagram-reel-photo-v15`
e repertório default com staging `business-reel-v7`, com hashes pinados.
Quando `assets/logo.png` existe no pacote, o plano deve conter elemento
`role=image` com esse asset; ausência ou substituição por texto resulta em
`MOTION_PHOTO_LOGO_REQUIRED`, antes de implementar. O inventário de planejamento
inclui `brand_logo` e seu preview, além das até quatro fotografias. A logo não
conta como foto para a relação `photo_dominant` do staging.

Contrato/skill/regras orientam holds de leitura ≤ ~2–2,5 s, full-bleed 9:16
com cover/foco protegido, overlays legíveis e inset somente com intenção
justificada. No fecho/handoff, pelos tempos do plano, fotos/díptico mantêm KB e a logo mantém
micro-movimento de escala. O exemplo v7 mostra `<img src="assets/logo.png">`,
recebe `closingPhotos` fora do wrapper que sai e anima ambos até o fim.
Refinamento solicitado: removida a janela fixa do intent/skill/regras do
repertório. Com logo no pacote, o contrato exige que o HTML do fecho renderize
`<img src="assets/logo.png">` visível; só declarar no plano não basta.
Hashes da fatia L1–L3 em desenvolvimento atualizados; versões históricas intactas.
A exigência de HTML é instrução de implementação, não novo gate de inspeção DOM.
Validação do refinamento: 81 testes focados passaram, incluindo payload de
planejamento/implementação e integridade dos hashes; intent com 100% de
linhas/branches. Ruff/formatação passaram; make ci repetido segue com 66
ocorrências de lint. Sem chamada paga, novo MP4 ou aceite E2E.
Exige adaptação, instanciação em scene_init e chamada em seek absoluto;
não é auto-injetado nem um storyboard fixo. Ritmo/composição são orientação
forte, não gates A5b nem prova de visibilidade no MP4.

Intent v1/v2, regras v1/v2, skill v14 e repertório v6 continuam íntegros para
replay; snapshots capturados não são migrados. Vídeo conserva skill v13 e
default v5; seleção explícita de repertório permanece respeitada. Nenhuma
mudança de Music/mix, renderer, TTS/avatar ou chamada paga.

Validação desta fatia: 254 testes unitários passaram (contratos, plano,
loader, payload do provedor, staging, skills/repertório e replay); intent com
100% de linhas/branches no recorte. Cinco testes Node passaram, incluindo
fecho 11–15 s e seek reverso determinístico. Três integrações PostgreSQL
lab/WhatsApp passaram no banco dedicado `_test`, com roles restritas.
Ruff/check de formato dos 11 arquivos Python alterados e diff-check passaram.
`make ci` executado com cache local permitido parou nas mesmas 66 ocorrências
de lint já documentadas; CI global e cobertura global 100% não estabelecidos.
Mypy global também falhou (183 erros em 31 arquivos); não é declarado verde.
Nenhuma exclusão de módulos ou relaxamento de gates. Pendente: novo MP4 de
ensaio autorizado e revisão visual/escuta do titular. Sem aceite E2E.

## 17/11/2026 — ensaio v3 Café Aurora: gaps e backlog L1–L4 (só docs)

Ensaio `versao-1 (3).mp4`: melhora vs v2 (~89%→~76% quase estático), mas meios
ainda congelam e o fecho 11–15 s fica quase morto. Marca só tipográfica — logo
PNG anexável e não obrigatória no plano. Diagnóstico, causa (logo/holds/ritmo/
bleed/mix) e backlog L1–L4 com prompt para outro chat em
[motion-ensaio-cafe-aurora-v3-gaps-2026-11-17.md](../design/motion-ensaio-cafe-aurora-v3-gaps-2026-11-17.md).
Sem implementação, chamada paga, A5b ou aceite E2E nesta mudança.

## 17/11/2026 — eliminar conflito de instruções photo antes do ensaio

Revisão confirmou que o scaffolding P1–P3 ainda enviava permissões antigas:
“sem exigir movimento contínuo”, “sem exigir zoom ou scale” e “movimento suave
quando pedido”. Novas capturas usam `motion-staging-photo-v2` e
`PHOTO_MOTION_RULES_V2`, inclusive na política do executor, com Ken Burns contínuo
nos holds. Schema do provedor e validação reconhecem photo v2; photo v1 mantém
texto, semântica e replay originais. Vídeo conserva o staging genérico v1.
Não reescrever snapshots já capturados para corrigir o prompt: o ensaio deve
partir de nova captura. Skill photo v14, intent v2 e repertório v6 permanecem.

Validação: 110 testes no recorte AI/photo/staging passaram, com 100% de linhas
e branches em staging/intent; três integrações lab/WhatsApp passaram no banco
exclusivo `_test`. Regressões verificam o payload completo de planejamento e
implementação sem as três frases, regras no modo silencioso sem staging,
schema photo v1/v2 versus vídeo e preservação de snapshots históricos. Ruff
passou; `make ci` segue bloqueado pelas 66 ocorrências de lint preexistentes.
Cobertura global não estabelecida. O recorte inicial photo/staging teve 86
passes (sobrepõe o recorte de 110; não somar as contagens).

Esta é correção da consistência do prompt, não garantia de acabamento visual.
Helper continua exigindo adaptação/chamada pelo modelo. Sem chamada paga,
novo MP4, aceite E2E, A5b ou alteração de Music/renderer. Próxima evidência:
MP4 de ensaio autorizado e escuta/visual do titular.


## 17/11/2026 — photo P1–P3: holds vivos, texto temporal e handoff

Implementada a direção photo versionada `motion-photo-intent-v2`: Ken Burns
contínuo durante leitura, entrada/saída tipográfica com deslocamento e stagger,
saída antes da passagem e scale na entrega à marca. A orientação de evitar
~2 s sem mudança perceptível não é gate A5b. Tempos, materiais e hash do plano
continuam preservados; o intent de implementação usa a versão capturada.

Novas capturas photo usam `instagram-reel-photo-v14` (derivada localmente da
v13) e, com staging/default, `business-reel-v6` (extensão local da v5), ambos
pinados por SHA-256. O exemplo `makePhotoReelMotion` deve ser adaptado/instanciado
em scene_init e chamado em seek absoluto: pan/scale contínuo, texto temporal e
handoff usam wrappers separados. Não há auto-injeção de helpers. v13/v5 e
intent v1 permanecem íntegros para snapshots históricos; vídeo mantém v13/v5.
Repertório explicitamente escolhido continua respeitado. Nenhuma leitura dos
repos externos, chamada paga, troca de renderer, tarifa/credencial ou mix Music.

Validação: 135 unitários focados passaram; intent com 100% de linhas/branches.
Quatro testes Node provaram mudança nos holds, stagger/saída, escala, limites e
seek reverso determinístico. Três integrações PostgreSQL passaram no banco
exclusivo `_test`, incluindo snapshots de lab/WhatsApp com roles restritas.
Mais 83 testes de adapters passaram. Ruff/check de formato dos arquivos alterados
passaram. `make ci` parou no lint global (66 ocorrências).
A ampliação para contexto teve 18 falhas nas fixtures de feedback, reproduzidas
com os módulos de produção de HEAD em cópia isolada (18 falhas/19 passes);
o recorte ampliado atual teve 154 passes/18 falhas. Mypy sem cache apontou
cinco erros em trechos não alterados de context/inputs/AI, também presentes
na cópia de HEAD. Cobertura global 100% não
foi estabelecida. Não excluir módulos nem relaxar gates para declarar CI verde.

Pendente: novo MP4 e escuta/visual do titular para aceite E2E. Testes de estado
não comprovam acabamento comercial nem ausência perceptiva de congelamento.
P4/P5, A5b, TTS/Voice e avatar permanecem fora desta fatia.


## 17/11/2026 — backlog motion pós-ensaio Café Aurora (só docs)

Ensaio `versao-1 (2).mp4`: trilha AAC presente; ~89% dos pares amostrados quase
estáticos; holds longos (~4,8 s e ~6,6 s). Diagnóstico: caminho A1–A5a e método
Maestros ok; acabamento visual ainda editorial/estático. Backlog P1–P5
(Ken Burns contínuo, tipografia cinética, scale no handoff, ritmo, mix) e
prompt para outro chat em
[motion-melhorias-pos-ensaio-cafe-aurora-2026-11-17.md](../design/motion-melhorias-pos-ensaio-cafe-aurora-2026-11-17.md).

Skills/repertório: runtime usa snapshots pinados (`instagram-reel-v13`,
`business-reel-v5` quando staging); repos `meu-braco-direito-skills` e
`meu-braco-direito-motion-sources` **não** entram ao vivo. Sem implementação,
A5b, chamada paga ou aceite E2E nesta mudança.

## 17/11/2026 — lab SSE como fonte de atualização e worker recarregado

Frontend remove polling permanente de run/checkpoints/results. SSE invalida
projeções por tipo de evento, agrupadas em 200 ms; parciais e heartbeat não
consultam snapshots. Conexão/reconexão reconcilia snapshots; fallback de 15 s
somente desconectado e não terminal. Checkpoints só fazem fallback quando há
decisão pendente. Revogação/expiração de sessão interrompe acompanhamento.

Diagnóstico do run fb4c0836-6636-58e4-8533-1233d76cf441: snapshot persistido
com review_checkpoints/storyboard=true e automatic_plan=false. API iniciada
15h46, mas worker desde 15h08 ainda carregava código anterior à mudança de
15h43. Worker recarregado (PID 54401) após verificar zero runs queued/running
do lab. Snapshot pausado não alterado, sem aprovação fictícia, retomada ou
chamada paga. Novo reel usa construção automática e aprovação final mantida.

Validação frontend: sete testes focados passaram, incluindo componentes reais
sem polling por 30 s conectados, fallback/reconexão e isolamento por run.
Três testes de descoberta em CreationLabPage.test.tsx falharam na execução mais
ampla; suíte global não está verde. Aceite manual na UI permanece pendente.


## 17/11/2026 — lab: construção automática, aprovação somente da peça pronta

Por solicitação explícita do titular, esta decisão substitui Q5b/A2: novos reels
do lab não exigem aprovação intermediária de plano, render ou storyboard. Fotos
usam planned_photo_request(human_review=False), como WhatsApp: planejamento e
validação automáticos antes de implementar. Vídeos seguem o caminho produtivo
automático, inclusive em drafts antigos ainda não iniciados. Não são emitidos
eventos fictícios de aprovação. Aprovação final approve-piece, RLS, Music,
reservas, revisão e integridade permanecem; nenhuma geração paga nesta mudança.

Frontend remove a galeria de frames e seus downloads. Checkpoints legados e
perguntas de outros formatos permanecem compatíveis. Runs já iniciados conservam
snapshot/contrato original: não foram migrados, retomados ou cobrados. Para usar
o novo comportamento, reiniciar API/worker e iniciar um novo reel. Frames
internos de revisão automática continuam necessários e não são aprovação humana.

Validação: 15 testes unitários (planejamento photo e snapshots de vídeo) e três
de integração photo lab/WhatsApp passaram no banco dedicado _test. TypeScript
do frontend e Ruff da fatia passaram. Make ci bloqueado no lint global com 66
ocorrências. Aceite UI/MP4 e cobertura global permanecem pendentes.


## 17/11/2026 — leituras concorrentes do storyboard no lab

Correção da contenção nas consultas de frames, checkpoints e resultados: essas
leituras usam advisory lock compartilhado por run; mutações mantêm o lock
exclusivo padrão. A decodificação dos payloads ocorre após encerrar a transação,
sem manter lock/conexão durante essa etapa. RLS, autorização/auditoria e a
rechecagem de expiração/bytes antes de liberar o frame permanecem vigentes.

O relato do run `1095bbe0-ffc8-5242-8e5f-9ca0ec3ad36d` contém DBAPIError em
leituras simultâneas, mas não SQLSTATE; portanto a atribuição dos 500 à contenção
é hipótese sustentada pelo caminho exclusivo encontrado, não traceback conclusivo.
Não houve regeneração, mudança de orçamento ou chamada paga. Reiniciar a API
e reabrir o mesmo run para confirmar a correção na UI; aceite E2E segue pendente.

Validação: cinco testes unitários de frame (sucesso, expiração, ausência, índice
e bytes alterados); regressão PostgreSQL dedicada verifica leitores simultâneos,
escritores exclusivos, auditoria e revogação RLS. Ruff dos arquivos alterados
passa. Make ci segue bloqueado no lint global (66 ocorrências); cobertura global
100% e aceite UI não foram estabelecidos nesta rodada.


## 17/11/2026 — implementação photo: logo não consome limite de fotos

Após aprovação do plano, o run `f9c135c7-c258-502a-8361-4fc5f2f5ccff` falhou
com `MOTION_AI_ASSET_PREVIEW_INVALID` antes do envio da implementação ao modelo.
O checkpoint continha quatro previews de fotos; o plano usava duas dessas fotos
e o logo. O resolvedor preserva previews disponíveis e acrescenta o logo previsto,
produzindo cinco. O adapter aplicava o limite de quatro sem separar identidade
visual de fotografias da coleção.

Correção: permitir um preview adicional somente com ID `assets/logo.png`.
Mantido limite de quatro materiais e até dois previews de ilustrações quando
habilitadas, mais um logo. Preservadas verificações de asset PNG autorizado,
hash do preview e unicidade. Não descartar fotos, alterar plano ou desativar a
validação para passar. O schema, o plano aprovado, Music e orçamento não mudam.

Validação: 124 testes locais passaram, incluindo preparação real do manifesto
seguida do builder com quatro fotos + logo, além de preview extra, duplicata,
logo não autorizado e hash inválido. Ruff passou; `make ci` continua bloqueado
por 70 ocorrências no lint global. Worker do lab atualizado após conferir que
não havia geração ativa/pendente. Sem geração paga nesta investigação.
O run falho foi preservado; o fluxo atual do lab não retoma checkpoint consumido
de run failed por novo clique de aprovação. Aceite UI/MP4 permanece pendente.


## 17/11/2026 — correção do launcher após reinício não resolver o conflito

Correção do diagnóstico operacional anterior: o titular reiniciou a API, mas o
novo processo ainda recebeu do ambiente de debug os mesmos renderer/tarifa
antigos. Portanto, simplesmente reiniciar não era suficiente. Nenhuma mudança
no cadastro ou plano explica este conflito. A validação completa
`LabMotionRequests.current` do run `f9c135c7-c258-502a-8361-4fc5f2f5ccff` passou
com o `.env` vigente, sob escopo RLS e rollback, sem enviar decisão.

A configuração VS Code `Meu Braço Direito: API (FastAPI)` agora usa
`app.entrypoints.api_debug`, que exige o `.env` local e carrega seus valores com
precedência sobre exports herdados antes de iniciar Uvicorn/importar Settings.
Isso se limita ao launcher explícito de desenvolvimento: precedência de ambiente
na API de produção/worker e proteção de fingerprint permanecem inalteradas.
Não gravar o novo contexto sobre o antigo nem afrouxar aprovação para contornar
incompatibilidades reais. Titular deve parar/iniciar pela configuração corrigida
e aprovar o mesmo plano. Sem novo run, nova aprovação automática ou gasto.

Validação: três testes passaram, cobertura de linhas/ramos de 100% no launcher,
incluindo ambiente herdado antigo, arquivo ausente e entrada como módulo.
Ruff/format passaram. O teste de contexto real não alterou o run. CI global
continua com pendências anteriores de lint; aceite UI/E2E segue pendente.
A mensagem genérica de cadastro duplicado no frontend continua inadequada para
este 409 e não deve ser interpretada como evidência de negócio duplicado.


## 17/11/2026 — aprovação bloqueada por ambiente antigo da API

O checkpoint photo permaneceu `awaiting_approval` após dois cliques com
`MOTION_CONTEXT_CHANGED`. Verificação sob RLS confirmou fingerprint íntegro e
recaptura idêntica com o `.env` vigente: nenhuma divergência no plano/material.
A comparação allowlisted do processo API na porta 8000 identificou dois overrides
antigos em memória: renderer `sha256:e9884862762529bf49086fb579676a7be15a108a5ac1bb88c7c0f44496a6bf51`
e tarifa de entrada IA `2000000` micros/milhão. Plano e `.env` atual usam renderer
`sha256:33f0703c51d90bf69f30c359e8eb71fa68a98b10b568265966c3c8d5025c080a`
e tarifa `2500000`, já configurada antes desta investigação.

A proteção de contexto está correta: não remover a conferência nem reescrever
fingerprint/checkpoint para contorná-la. Necessário parar/iniciar o backend pelo
launcher do titular, que carrega `.env`; refresh do navegador não atualiza o
ambiente do processo. Depois, aprovar o mesmo plano, sem recriar a geração.
O processo de backend do titular não foi encerrado pelo agente. Worker do lab já
usa configuração vigente. Sem alteração de tarifas, aprovação programática,
retry pago ou edição do run nesta investigação. Não houve mudança de código;
validação foi comparação de contexto e ambiente, somente leitura.

A mensagem de cadastro duplicado vem do fallback HTTP 409 do frontend e não
representa este caso; não há evidência de negócio duplicado. Aceite E2E permanece
pendente até o titular reiniciar o backend e continuar a aprovação.


## 17/11/2026 — correção de cobertura do plano photo no schema do provedor

Ensaio posterior superou a etapa Music (`music_v2_5`, efeito recebido) e falhou
no plano com `MOTION_QUALITY_COVERAGE_INVALID`. Inspeção local do trace confirmou:
os oito requisitos esperados estavam presentes, com disposition e referências
válidas, mas o modelo adicionou `brief_alignment`, `motion_role` e
`narrative_progression`. Esses são checks de revisão, não requisitos adicionais
de `audiovisual.functions`. O schema genérico anterior aceitava IDs livres e até
24 entradas, embora o validador exigisse exatamente o conjunto do contrato.

O schema enviado ao provedor agora deriva os IDs permitidos de
`quality_contract.requirements`, fixa disposition em `satisfy_requirement` e
limita min/max de entradas ao total exigido. `planning_input.quality_coverage`
explicita uma entrada por ID e separa checks de revisão. Modelos/schemas Pydantic
compartilhados e snapshots anteriores não são mutados; sem quality_contract,
a projeção histórica permanece livre. Unicidade e referências continuam
verificadas no servidor. Não apagar extras de respostas existentes nem relaxar
a validação; isso é integridade de contrato, não gate estético A5b.

Validação: 90 testes focados passaram (schema/provider real com transporte fake,
qualidade, geração e regressões A2/A3/A5a). Regressão sintética reproduz os três
IDs extras; testes mantêm rejeição de duplicatas/referências inválidas e garantem
que o schema compartilhado não muda. Ruff/format dos arquivos alterados passaram;
`make ci` continua bloqueado por 70 ocorrências no lint global. Sem retry pago,
reset do run, edição do plano armazenado ou mudança de orçamento/cache/ledger.
Worker do lab atualizado após verificar ausência de geração ativa/pendente.
Aceite UI/MP4 e escuta humana continuam pendentes; novo ensaio é iniciado pelo titular.


## 17/11/2026 — falha Music no ensaio: diagnóstico seguro de HTTP

O ensaio do titular chegou à geração `music_v2_5` e terminou `run.uncertain`
com `MOTION_MUSIC_PROVIDER_FAILED`; reserva Music de US$ 0,10 permanece incerta.
O adapter anterior descartou status/corpo HTTP, impedindo determinar a causa
retrospectivamente. Não houve retry, geração diagnóstica, reset de run/cache ou
liberação de reserva. Não presumir cobrança nem ausência de cobrança.

Consulta gratuita `GET /v1/user/subscription` retornou HTTP 401 com categoria
`missing_permissions`: falta permissão para essa consulta. Isso não comprova
falta de permissão Music; titular deve verificar a permissão de geração na chave.
Contrato de compose revisado na documentação oficial; causa original permanece
não confirmada, sem atribuí-la a formato/modelo/plano por inferência.

Adapter agora conserva códigos estáveis `MOTION_MUSIC_HTTP_<status>` e sufixos
somente de categorias em allowlist (permissão/chave/quota/formato etc.). Leitura
de erro limitada a 16 KiB; texto livre, headers e secrets não são persistidos
nem exibidos. O código seguro percorre o tratamento de erro existente até o
trace. Falhas de transporte continuam incertas; nenhuma repetição automática.
A correção melhora o diagnóstico de respostas futuras, não recupera a resposta
perdida nem resolve a causa do provedor por si só.

Validação: 47 testes locais passaram, cobertura de linhas/ramos de 100% no
adapter; ruff/format passaram. Sem gasto nesta investigação. Orçamentos, cache,
ledger e estado do run preservados. CI global mantém pendências anteriores.


## 17/11/2026 — preparação operacional para aceite A1–A5a

Titular autorizou rebuild local/digest e, em confirmação explícita, Music:
reserva `100000` micros (US$ 0,10), tarifa `150000` micros/min (US$ 0,15/min),
teto mensal `1000000` micros (US$ 1). Valores aplicados somente no `.env`;
orçamentos OpenAI preservados. Flag Music/direitos já autorizadas permanecem on.
Nenhuma chamada paga foi feita nesta preparação; gasto começa com ensaio do titular.

Migração **somente 0133_motion_music** aplicada ao banco local do lab, antes em
0132; tabela presente com RLS e FORCE RLS. Sem limpeza, dados de teste ou migração
para outras revisões nesse banco. Renderer reconstruído com contexto isolado,
dependências locais e build sem rede; `.env` usa `sha256:33f0703c51d90bf69f30c359e8eb71fa68a98b10b568265966c3c8d5025c080a`.

Novas gerações e ledger usam `music_v2_5`; cache existente continua reutilizável.
Fontes verificadas: [modelo vigente](https://elevenlabs.io/docs/overview/capabilities/music)
e [preço API](https://elevenlabs.io/pricing/api). O preço é referência de configuração,
não reconciliação de fatura. Testes locais do adapter/serviço: 37 passaram;
Ruff/format dos arquivos alterados passaram. CI global continua com pendência
anterior de lint; não declarar verde nesta rodada operacional.

Verificação local concluída: a imagem nova produziu MP4 sintético de 2s,
20 frames de evidência decodificados e `music_integrity` com áudio de 2000ms,
além de pico não vazio. Artefatos locais em `.local/reel-acceptance-20261117/`.
Isso valida integração técnica, não qualidade artística ou escuta de ElevenLabs.
Worker dedicado do lab reiniciado com virtualenv/código/configuração novos e
poller de atividades confirmado no Temporal. Nenhum pedido de geração foi enviado;
os eventos pendentes encontrados eram `creation_lab.piece_approved`, fora do
conjunto consumido pelo worker do lab. Backend/frontend ficam para o titular iniciar.

Checklist do titular: iniciar backend/front após esta atualização e criar **novo**
ensaio Café Aurora (não retomar snapshot antigo). Usar fotos autorizadas e 15s.
Conferir/aprovar plano no lab: fotos/relações, leitura, handoffs, SFX justificado
ou omissão explícita. No MP4 ouvir trilha/fades, conferir leitura/progressão e
adequação dos efeitos; inspecionar `music_integrity`, `audio_measurements` e
`photo_metrics` no diagnóstico. Depois repetir calmo/energético/poucas fotos.
Cache pode evitar nova geração Music; não presumir três cobranças. Aprovação
humana ainda pendente; A5b/TTS/avatar fora do escopo e sem limiares estéticos.


## 17/11/2026 — A5a: SFX opcionais no planejamento photo compartilhado

Novos photo reels montados por `planned_photo_request` (lab e WhatsApp) passam
`sound_library_id=public-cc0-v1` ao caminho audiovisual autorizado. O loader
carrega os dois arquivos locais com hashes fixados: `coffee-pour` e `cup-contact`.
Nenhum download, catálogo de trilha ou escolha de faixa pelo cliente foi criado.
Photo reel sem esse planejamento/seleção não carrega a biblioteca. Pedidos de
silêncio reconhecidos pela política existente A1 (inclusive sem música/trilha)
ficam sem SFX; pedidos históricos sem biblioteca não são promovidos implicitamente.

Cada candidato exige seleção justificada em `audiovisual.sounds` ou omissão
explícita com motivo em `omitted_sounds`. Seleção exige hash autorizado, ação,
elemento/beat não estático e intervalo compatíveis; não é obrigatório usar efeitos.
As regras capturadas esclarecem que servir/contato são representações editoriais
planejadas, nunca prova de ação/som ocorrido dentro da fotografia. Ausência de
justificativa ou de ação exige omissão, não invenção de movimento na foto.

O mix existente adiciona `role=effect` e conserva a faixa ElevenLabs `role=music`
integralmente. SFX não substituem Music nem preenchem a duração para disfarçar
sua indisponibilidade. Com Music off/sem reserva, efeitos pontuais justificados
continuam opcionais; omitir ambos mantém silêncio. A1–A4, aprovação humana do
lab, validação automática WA, orçamento sem auto-upgrade, staging photo, intent,
diagnósticos informativos e `MOTION_RENDER_MUSIC_INVALID` permanecem preservados.

Validação: 174 testes unitários focados passaram, incluindo A1–A4 e A5a,
com 100% de cobertura de linhas/ramos em `motion_photos` e `motion_sound_library`.
Ruff/format dos seis arquivos Python alterados e mypy dos dois serviços acima
passaram. A primeira execução detectou um import em escopo incorreto, corrigido
antes da repetição. Seis testes de integração PostgreSQL `_test` passaram
(photo lab/WhatsApp, cache/ledger Music e decode sintético, sem API externa). `make ci` continua bloqueado no lint global
(70 ocorrências fora desta fatia); não há CI global verde nem aceite E2E.

Não houve rebuild, chamada paga, download, mudança de tarifa/reserva/`.env` ou
migração operacional. Aceite E2E/escuta continua pendente. Próxima rodada exige
autorização operacional para rebuild do renderer, configurar reserva/tarifa/teto
Music, verificar migração 0133/modelo Music vigente e ensaiar UI/MP4 com escuta.
A5b só após amostra e calibração humana; TTS/Voice/avatar fora desta mudança.


## 17/11/2026 — A4: diagnóstico informativo e integridade da música no MP4

Photo reels persistem `motion-photo-diagnostics-v1` em `diagnostics.photo_metrics`,
no recibo durável do render e na versão criptografada, disponível no diagnóstico
do lab. Diferença média normalizada de pixels RGB (amostras reduzidas a 64×64)
e percentual de pares quase estáticos (< 0,01) são **descritivos**, nunca gates.
Os tempos amostrados acompanham os valores: percentual de pares não significa
percentual da duração nem prova de movimento contínuo. Variedade de transições
conta descrições distintas do plano, não efeitos observados. Força narrativa
registra quantidade de momentos declarados e fica **sem score**, dependente de
calibração humana. Sem pares suficientes, medidas visuais são nulas.

Essas métricas ficam fora da entrada de revisão/correção automática, impedindo
que sejam convertidas em requisito de aprovação. Holds, peças calmas e frames
idênticos continuam permitidos. Não há A5b, SFX, TTS/Voice ou avatar nesta fatia.

Integridade: o renderer mantém validação/decode de MP4, codec, resolução, fps,
duração e contagem de frames. Com trilha autorizada de papel `music`, exige uma
stream de áudio cobrindo o término planejado (tolerância técnica de 25 ms) e pico
não vazio medido no áudio decodificado. O serviço exige esse comprovante antes
do upload; falha estável `MOTION_RENDER_MUSIC_INVALID`. Não há mínimo estético de
volume: sinal baixo válido passa. A medida é do mix, não prova de atribuição de
cada fonte. Material, contratos e orçamento continuam nos validadores existentes.
Silêncio autorizado por A1 off/sem reserva continua válido.

**Operação:** é necessário reconstruir/usar a imagem do renderer com esta mudança
antes do ensaio com Music; imagens anteriores sem comprovante de integridade da
trilha serão recusadas pelo serviço. Nenhuma imagem foi publicada/reconfigurada,
nenhuma chamada paga, migração do lab ou alteração de `.env`/tarifa/reserva ocorreu.
Persistem: reserva/tarifa/teto Music, verificar migração 0133 no lab, verificar
`music_v2_5` antes da primeira geração paga e obter teto explícito. A1–A4 não
estão aceitos E2E: falta ensaio UI/MP4, avaliação visual e escuta humana.

Validação: 127 testes unitários focados passaram (A1–A4, orquestração e correções),
com 100% de linhas/ramos no novo serviço de diagnóstico. Os 190 testes Node do
renderer passaram com 100% de linhas/ramos/funções, incluindo sinais sintéticos
FFmpeg e regressões de MP4 inválido, áudio ausente/vazio/curto. Seis integrações
PostgreSQL `_test` passaram (cache/ledger Music e photo lab/WhatsApp). Ruff/format
dos arquivos Python alterados e mypy do novo serviço passaram. `make ci` continua
bloqueado no lint global: 70 ocorrências fora dos arquivos desta fatia; não há
CI global verde nem afirmação de cobertura global de 100%.


## 17/11/2026 — A3: implementação visual e tipografia pela intenção

Novos planos photo capturam `motion-photo-intent-v1` no serviço compartilhado.
O contrato orienta planejamento, implementação e revisão/correção por progressão
perceptível, hierarquia/contraste/quebras de texto e tempo de leitura, além de
handoffs justificados por origem, travessia e destino. Holds podem sustentar
leitura ou contemplação; não há obrigação de scale, zoom, MotionV1, efeitos,
quantidade de cortes ou CTA. Sem novos gates estéticos ou métricas A4.

Na implementação, `photo_implementation_intent` projeta os tempos, beats de texto,
direção, desenvolvimento e transições do plano validado, vinculado ao seu hash.
A projeção não replaneja nem altera áudio. O contrato fica no snapshot; replay
anterior sem A3 não ganha regras novas. Lab mantém checkpoint humano e WhatsApp
validação automática de A2; trilha/cache A1 permanecem intactos.

Validação local: 13 testes unitários A2 passaram. A suíte focada A2/A3/staging
passou com 42 testes e cobertura de linhas/ramos de 100% no novo serviço A3.
A integração A2 revelou fixture sem chave de criptografia; adicionada chave
sintética efêmera, sem credencial real. Repetição: 3 testes de integração passaram
no PostgreSQL dedicado `_test` (isolamento das fotos e origens lab/WhatsApp).
Ruff dos arquivos alterados passou. `make ci` parou no lint global (70 ocorrências);
o gate global continua pendente e não equivale à cobertura localizada.

Sem chamada paga, alteração de tarifa/reserva, migração do banco do lab ou
mudança no `.env`. A1/A2/A3 não estão aceitos E2E: faltam ensaio UI com plano e
MP4, progressão/leitura verificadas e escuta humana. Music segue dependente da
configuração de reserva/tarifa/teto e autorização explícita de gasto; migração
0133 operacional e escolha do modelo Music vigente continuam pendentes de
verificação na rodada própria. A4/A5, TTS/Voice e avatar fora desta mudança.


## 17/11/2026 — A2: planejamento photo compartilhado; testes adiados pelo titular

Escopo final desta rodada: **somente A2**, conforme a última instrução do
titular. A3–A5, TTS/Voice, avatar e gates estéticos não foram implementados.
O titular dispensou merge como pré-requisito, confirmou plano ElevenLabs
Starter+ e chave local e autorizou Music no `.env`. Foram habilitadas somente
as flags de execução Music e confirmação de direitos; credencial, tarifas e
orçamentos preservados. Sem reload de worker, migração operacional, chamada
paga ou teste de ponta a ponta. A ativação local da flag não comprova que os
outros requisitos de execução estejam configurados.

Novos photo reels do fluxo compartilhado por lab/WhatsApp usam preparação
vinculada às fotografias autorizadas, plano audiovisual separado do código e
contratos versionados `proposed-photo-output-v1`, `motion-photo-quality-v1` e
`motion-staging-photo-v1`. `photo_dominant` exige fotografia autorizada como
protagonista; `integrated` exige uma fotografia autorizada no conjunto visual.
`graphic` continua disponível para cenas gráficas, sem classificar toda foto
como grafismo. Não se aceita `recording_dominant` no contrato photo nem se
inventa vídeo, voz ou transcrição. Schema enviado ao modelo fixa versão e
relações válidas do contrato; snapshots antigos conservam seus contratos.

A origem do pedido, não o modo da UI, define a aprovação: lab sempre captura
checkpoint humano de plano (inclusive modo “automatic”); WhatsApp usa
`automatic_plan` e implementa após os validadores compartilhados, sem emitir
`motion.plan_approved`. O plano continua imutável na implementação. Esta
mudança cobre novos pedidos de fotos; não reescreve tentativas históricas.

Admissão photo exige capacidade para plan + implement + review e os pares
correct/review configurados: `(3 + 2*max_corrections) * reserva`. Antes de
implementar, revalida o saldo para implementação/revisões/correções e imagens
declaradas. Insuficiência produz `MOTION_CONSTRUCTION_BUDGET_REQUIRED`; nenhum
teto é ampliado. A seleção/cache/mix de ElevenLabs Music permanece em A1.
Não foi habilitada biblioteca Freesound para novos pedidos nesta fatia.

Validação desta rodada: revisão de código, Ruff e formatação dos arquivos
alterados; `git diff --check`. Adicionados testes unitários de semântica,
schema, orçamento e roteamento lab/WhatsApp, mais integração do assembler
compartilhado com anexos privados/RLS. **Testes não executados**, por instrução
expressa do titular; não há resultado novo de cobertura, CI ou aceite de A2.
Pendentes: executar os testes da fatia/CI e ensaio de ponta a ponta posterior,
com teto explícito antes de qualquer chamada paga; avaliar plano e MP4 pela
UI. Os resultados antigos de A1 abaixo são evidências históricas separadas.

## 17/11/2026 — A1 implementada: Music privado, execução desativada

Autorização desta rodada: implementar somente A1. Adapter ElevenLabs Music
(`music_v1`, instrumental, MP3, uma tentativa, resposta limitada a 1 MiB),
seleção determinística de mood por pedido/fatos confirmados e cache interno
criptografado em PostgreSQL. Cache por negócio + mood + duração, com hash e
vínculo à operação; sem catálogo ou escolha/download de faixa pelo cliente.
Freesound continua reservado ao caminho existente de SFX. A2–A5, TTS e avatar
não fazem parte desta mudança.

O serviço compartilhado prepara a trilha e a reutiliza nas retomadas de plano,
storyboard e recuperação. Mix `motion-audio-v2`: volume 0,18, fade-in 500 ms,
fade-out 800 ms; preserva música quando o caminho existente acrescenta SFX.
Gera pelo menos 15s e cobre a duração do reel (até 60s); não inventa vídeo-fonte.
Novos snapshots usam política `elevenlabs-music-v1`; os antigos conservam o
caminho de biblioteca capturado.

Flag `elevenlabs_music_execution_enabled=false`, chave SecretStr, confirmação
explícita de direitos comerciais, tarifa e reserva/teto mensal inicialmente
zero. O teto Music é por tenant/mês UTC, compartilhado entre lab e produção;
os limites de pedido e o ledger administrativo/comercial continuam aplicáveis.
Reservas são duráveis antes da API; valor estimado não é tratado como fatura.
Falha incerta mantém hold e impede repetição automática. Cache/mês usam RLS,
login restrito, auditoria/outbox e transações curtas sem rede sob locks.
Pedido de silêncio ou configuração/orçamento indisponível mantém silêncio com
status interno; áudio selecionado vazio, alterado ou curto falha explicitamente.

Migração `0133_motion_music` aplicada somente ao banco dedicado `_test`.
Nenhuma leitura/exposição de chave real, chamada paga, download Freesound,
ativação de flag, reload de worker ou migração do banco do projeto.

Validação: 40 testes A1 aprovados com provider fake, HTTP simulado, cache/RLS,
concorrência do teto mensal, ledger real e MP4 sintético de 15s produzido pelo
mixer de produção. Áudio final decodificado com duração, energia não nula,
fades e ausência de clipping verificados. Módulos novos com 100% linhas/branches.
O CI global permanece bloqueado: `make ci` para em 74 erros de lint; mypy
aponta 183 erros em 31 arquivos. Suíte ampliada de motion: 1.395 passaram e
19 falharam; as mesmas 19 falhas foram reproduzidas carregando o código de
`motion_context.py` do HEAD (sem substituir arquivos do workspace). Os oito
testes Node do mixer passaram. Não declarar cobertura global de 100% nem
mudança pronta para merge.

Pendente: resolver gates globais; migração operacional planejada; confirmar com
o titular chave local, plano Starter+/direitos e teto antes de qualquer ensaio
pago. Escuta/aceite de trilha real ElevenLabs e avaliação criativa do MP4 ainda
não realizados. A prova sintética verifica integração, não qualidade musical.
Contrato HTTP consultado: https://elevenlabs.io/docs/api-reference/music/compose
(não confirma preço, assinatura ou autorização de geração).

## 17/11/2026 — trilha photo reel: ElevenLabs Music (decisão)

Titular rejeitou Freesound CC0 para jazz/café e escolheu **ElevenLabs Music**
para trilhas: o sistema escolhe no cache interno ou gera; o cliente não vê nem
escolhe faixas. SFX continuam em Freesound CC0. Voice/clonagem ElevenLabs
permanece fatia posterior. Decisão em `docs/DECISIONS.md`; plano A1 atualizado
em [motion-plano-reels-15s-foto-2026-11-17.md](../design/motion-plano-reels-15s-foto-2026-11-17.md).
Integração/código e chamada paga ainda não autorizadas neste registro — falta
conta, plano comercial e API key local. Credenciais nunca vão para git, imagem
ou logs.

## 17/11/2026 — plano documentado: reels 15s de fotos (A0–A5 + TTS)

Após análise do MP4 `versao-1` (silêncio, holds, dois cortes), do pipeline photo
reel e revisão cruzada do plano, o titular validou decisões em entrevista e
pediu apenas o registro documental — sem executar A0 operacional, sem código
novo, sem download de música e sem chamada paga neste ato.

Plano vigente:
[motion-plano-reels-15s-foto-2026-11-17.md](../design/motion-plano-reels-15s-foto-2026-11-17.md).
A0 = checklist manual (sem script). Silêncio se pedido ou sem faixa elegível.
Lab com checkpoint de plano; WhatsApp com validação automática do plano.
Narração TTS para photo reel é fatia extra (N), com provedor/orçamento ainda
abertos. Variedade musical continua pendência. Primeira prova OpenAI autorizável
depois: teto ≤ US$ 5 com OK explícito na hora. Candidatos Freesound CC0 devem
ser apresentados antes de pinagem (A1). Escopo de produto: regras no serviço
compartilhado; laboratório como avaliação.

## 17/11/2026 — schema de geração respeita habilitação de staging

Tentativa af31c6b3-b273-5871-a2f5-64e0cab96944 falhou com
MOTION_STAGING_UNEXPECTED. Trace autenticado mostrou contexto sem staging_contract,
schema permitindo MotionStaging ou null e composição recebida com staging preenchido.
O problema era a divergência entre o schema enviado e o contrato aceito pelo serviço,
não indisponibilidade do renderer nem preparação de arquivos.

Adapter compartilhado agora restringe o campo staging a null quando o contrato não
está habilitado. Mantém schema de staging completo quando habilitado e preserva o
validador de serviço, sem apagar dados da resposta nem liberar contratos ausentes.
Restrição vale para geração e correção; modelos Pydantic reutilizáveis não são
mutados. Orçamentos, efeitos e respostas históricas preservados.

Validação: 102 testes direcionados de adapter, staging e geração passaram, com novas
regressões de geração/correção sem staging e schema habilitado preservado. Ruff e
formatação passaram nos três arquivos alterados. make ci, com cache gravável, parou
no lint preexistente do repositório (76 erros na execução, um E501 local corrigido
sem mudar o texto). Mypy apontou três erros no trecho de streaming não modificado.
CI completo/cobertura 100% e integração PostgreSQL não comprovados nesta intervenção.

Zero execuções queued/running antes do reload; worker PID 30614 confirmado no Temporal.
Sem nova geração paga ou reescrita da tentativa encerrada. Pendente: validação
completa pela UI e resolução dos gates globais; os testes dirigidos não comprovam
qualidade visual nem sucesso de todas as etapas posteriores.

## 17/11/2026 — renderer local atualizado para o contrato de fingerprints

Tentativa 6a8fbec3-5825-5695-8435-cb00af95e687 falhou com
MOTION_RENDER_INVALID_OUTPUT. Trace de render confirmou fingerprint_frames=true.
A imagem configurada continha runner antigo sem frame_fingerprints e sem
instrumentação audio_measurements, incompatível com o adapter atual. Não se
relaxaram as validações de saída ou isolamento.

Construída imagem local com os arquivos atuais de app/assets/motion_html_renderer
sobre a base instalada, usando contexto temporário contendo somente esses arquivos.
Digest validado e configurado no .env local:
sha256:d95f88a43e845795a3f9146b71794db5d29731ec40e356d934e57743507dbcf4.
Sem mudança de código ou orçamento. Zero pedidos queued/running antes da troca;
worker dedicado recarregado e PID 27418 confirmado nas duas filas do Temporal.

Validação: mesma peça sintética silenciosa de 64x64, três quadros, com fingerprints,
falhou com MOTION_RENDER_INVALID_OUTPUT na imagem anterior e passou na nova,
com MP4 de 2.184 bytes e três fingerprints. Os 122 testes existentes do adapter
passaram. Sem chamada paga, migração ou CI integral nesta intervenção; teste real
usou somente conteúdo sintético. A tentativa encerrada não foi reescrita nem
repetida. Pendente: geração completa e avaliação visual pela UI. A compatibilidade
da imagem não era coberta pela verificação anterior de mera disponibilidade.

## 17/11/2026 — tarifa de entrada de motion alinhada à política interna

Tentativa ac4178c1-8634-5811-bdd8-f913e054bf6d falhou com
MOTION_COST_TARIFF_UNDERESTIMATED. A configuração local usava 2.000.000 micros USD
por milhão de tokens de entrada, abaixo do mínimo conservador de 2.500.000 exigido
por validate_tariff (política sol-standard-2026-11-09). Ajustado somente esse
parâmetro no .env ignorado pelo Git. Trata-se de alinhamento à política existente,
não de nova verificação da tabela comercial do provedor. Tarifa de saída, reserva
de US$ 0,85 e orçamento de requisição de US$ 3,70 preservados.

Confirmados zero pedidos queued/running antes da intervenção. Worker dedicado
recarregado; PID 22405 registrado como poller de workflow e atividade no Temporal.
Validados readiness administrativo, tarifa e custo máximo de saída dentro da reserva.
56 testes existentes de motion_budget/motion_effects passaram, incluindo bloqueio
de tarifa inadequada antes da contagem/submissão. Sem alteração de código, CI
integral ou nova geração paga. A tentativa encerrada não foi repetida.

Pendente: nova tentativa pela UI. A admissão de custo total ainda depende da contagem
real de tokens do payload; readiness e tarifa válidos não comprovam geração completa
nem qualidade visual. Verificação operacional anterior não cobria validate_tariff.

## 17/11/2026 — configuração local de motion restabelecida

Após autorização explícita do usuário, adicionadas ao .env local ignorado pelo Git
as opções motion_execution_enabled=true e motion_ai_mode=openai e a conexão
correlator_database_url do login restrito já configurado no worker Docker, adaptada
ao endereço local do PostgreSQL. As três opções estavam ausentes do .env; os valores
desativados vinham dos padrões. Credenciais não foram exibidas nem versionadas.
Orçamentos e tarifas existentes preservados.

Leitura administrativa confirmou zero pedidos queued/running antes do reinício.
Conexão do correlator validada com rolsuper=false e rolbypassrls=false. Encerrado
somente o worker dedicado anterior e iniciado make creation-lab: PID 20119 confirmado
como poller de workflow e atividade. motion_execution_ready(administrative=True)
retornou true e a imagem configurada do renderer está disponível no Docker local.

Sem alteração de código, migração, testes/CI ou geração paga nesta intervenção.
O pedido encerrado ec9ceb40-d0db-52b2-bc14-2e3f3e352ef3 não foi reaberto nem duplicado.
Pendente: nova tentativa pela UI para validar geração completa e qualidade visual.
A inicialização do worker dedicado continua manual via make creation-lab após
reiniciar a máquina; não foi instalado supervisor de processos.

## 17/11/2026 — fila do laboratório sem worker e bloqueio de motion

Diagnóstico operacional do pedido ec9ceb40-d0db-52b2-bc14-2e3f3e352ef3:
estado queued e zero pollers de workflow/atividade na fila exclusiva do laboratório,
embora os contêineres principais estivessem ativos. Iniciado make creation-lab em
processo independente (launcher PID 15923); Temporal confirmou um poller de cada
tipo. O pedido existente saiu da fila e terminou failed com
MOTION_EXECUTION_NOT_CONFIGURED; não foi criado pedido duplicado.

Configuração local lida pelo worker: motion_execution_enabled=false,
motion_ai_mode=disabled e correlator_database_url ausente. Credencial de provedor,
renderer e limites de custo presentes não bastam para habilitar esse fluxo.
Flags de execução paga e credenciais não foram alteradas nesta intervenção.
O worker dedicado precisa ser iniciado separadamente dos contêineres; sua ausência
foi confirmada, mas a causa de encerramento do processo anterior não foi apurada.

Validação operacional por leitura com ator administrativo configurado/RLS e consulta
ao Temporal. Sem alterações de código, migração ou execução de testes/CI. Pendente:
restabelecer a configuração explícita de motion e então solicitar nova tentativa;
o pedido encerrado não foi reescrito ou repetido automaticamente. A qualidade do
reel com fotos continua sem validação por esta intervenção.

## 16/11/2026 — reel por mensagem sem vídeo de entrada

O fluxo produtivo compartilhado por WhatsApp e laboratório aceita pedido de reel
sem vídeo: usa fotos autorizadas do acervo e prioriza imagens anexadas, dentro do
limite existente de quatro fotos. Somente a ausência de fotos disponíveis solicita
um anexo ao cliente. Não é criado um vídeo-fonte fictício. Consentimento, RLS,
contexto/kit confirmado, orçamento por execução, efeitos duráveis, renderer isolado,
revisão e aprovação continuam nos serviços existentes. Feed/story e a preservação
de áudio/duração do vídeo enviado seguem pelos caminhos anteriores.

Decisão de duração: 15 segundos como padrão de produto para reel de fotos, não como
regra universal de mercado. Duração explícita em segundos inteiros é aceita entre
5 e 60; valores conflitantes ou fora do intervalo pedem esclarecimento. O contrato
separa source_asset_id de photo_duration_ms e não admite alinhamento de fala nem
reedição vinculada a vídeo no modo de fotos. O endpoint legado de qualificação
continua exigindo vídeo; o recurso novo pertence à entrada comum por mensagem.

Áudio: usar trilha licenciada disponível, conforme escolha do titular. A seleção
aceita apenas faixa do manifesto local verificado, marcada como música padrão para
reels de fotos, CC0 e suficientemente longa; preserva hash, mistura autorizada e
fades. A biblioteca atual contém apenas efeitos sonoros, logo o resultado atual é
silencioso e registra music_status no contexto/trace. Não se substitui música por
efeito, não se baixa faixa automaticamente e não há chamada paga adicional.

Validação: regressões unitárias adicionadas para duração, separação foto/vídeo,
loader sem leitura de vídeo, ausência de fotos e seleção de música; integração
adicionada para consulta com source nulo e isolamento RLS dos anexos entre ensaios.
Suítes não executadas por instrução do usuário; não houve geração paga. Conferência
estática de sintaxe, formatação, Ruff (sem E501 preexistente nos serviços) e diff.
Worker dedicado recarregado após leitura confirmar zero execuções queued/running;
novo PID 34505 confirmado como poller de atividades do Temporal. Nenhum ensaio
foi retomado automaticamente. Qualidade visual/movimento e percurso
completo permanecem para validação manual pela UI. Curadoria de uma trilha musical
real permanece pendente, sem bloquear a geração silenciosa autorizada.

## 16/11/2026 — worker antigo confirmado e recarregado

As tentativas ed81a554-8eeb-53bb-8cef-a2cf1093ed29 e
fc214884-9d46-5fac-b61f-659c1252e105 continuavam enviando pergunta de formato sem
confirmed_format. Inspeção de processos confirmou API reiniciada às 17h49, porém
worker dedicado iniciado às 16h25, anterior às correções das 17h47. A preparação
local correta não comprovava o código carregado por esse processo persistente.

Leitura autenticada confirmou ausência de execuções queued/running. Encerrado apenas
o worker dedicado antigo e iniciado make creation-lab às 17h51. Novo processo
confirmado como poller da fila de atividades Temporal. Sem alteração adicional de
regra, geração paga ou execução de testes. Ensaios pausados não foram reescritos ou
retomados; continuação manual permanece pendente. Reiniciar apenas a API no VS Code
não recarrega esse worker: mudanças de geração exigem reiniciar também o processo
make creation-lab. Conferir poller ativo antes de repetir ensaios após mudanças.

## 16/11/2026 — formato explícito em conversa reutilizada como pedido novo

Diagnóstico do ensaio e42276d6-1571-51f8-b428-c97de1fe4744: parent_run_id ausente,
texto com pergunta anterior e resposta “Pro feed mesmo” copiados. A correção anterior
cobria apenas continuações vinculadas e não era acionada nesse novo pedido. Não se
atribui o problema a reinício faltante; o escopo da correção era insuficiente.

Agora um pedido raiz com bloco final completo no formato de conversa da UI pode
fornecer resposta inequívoca de formato. Isso não confere proveniência de sistema
ao texto nem autoriza operações: continua sendo conteúdo do solicitante. Resposta
ambígua, negativa, com instruções adicionais ou sem pergunta conhecida mantém a
interpretação normal. Último bloco prevalece; continuações vinculadas ainda usam
a evidência persistida. Sem alteração de orçamento, aprovação ou publicação.

Conferência local da preparação com a mensagem real do ensaio: formato photo e
pergunta format ausente do payload. Nenhuma chamada de provedor ou geração. Ruff,
formatação, sintaxe e diff conferidos; regressões adicionadas, suíte não executada.
Validação completa pela UI pendente. Ensaio pausado não foi reescrito/reiniciado.
API e worker sem reload precisam carregar o código atualizado.

## 16/11/2026 — formato confirmado na resposta de continuação

Ensaio d060263b-c287-55fb-849b-5cbd9e2bb7d8 voltou a pedir detalhes após “Pro feed
mesmo”. Trace bruto mostrou abstenção de formato (unspecified, confiança 0,39);
validação local também encontrava reel nas opções da pergunta anterior concatenada.

Coordenador comum lê a evidência persistida da continuação, separando a pergunta do
sistema da resposta efetiva. Respostas curtas inequívocas a uma única pergunta conhecida
de formato confirmam photo/story/reel. Jev deixa de perguntar formato nesse caso,
recebe confirmed_format e continua avaliando intenção e catálogo. Guarda contra vídeo
não trata alternativas citadas pelo sistema como solicitação do usuário quando há
confirmação explícita. Sem confirmação, proteções anteriores permanecem. Respostas
negadas, ambíguas ou a perguntas diferentes não recebem esse tratamento.

Sem migração, chamada paga extra ou reinício automático da tentativa pausada. Mesmo
caminho para WhatsApp e laboratório. Ruff aprovado em adapter/helper/regressões;
sintaxe e diff conferidos. message_creation mantém E501 preexistentes. Regressões
adicionadas, não executadas conforme orientação. Validação manual pendente; reiniciar
API/worker sem reload antes da continuação. Botão extra de início no laboratório
permanece uma diferença de UI já identificada, não alterada nesta correção.

## 16/11/2026 — pergunta redundante sobre foto já selecionada

Ensaio 7ef01225-dc4c-5cce-b8f4-683498a2dbd7 aguardava envio/escolha de space_photo,
embora o contexto já contivesse a foto de ambiente autorizada. Entrada editorial
agora explicita selected_for_generation e que o arquivo vai ao gerador na etapa
seguinte; modelo não deve pedir reenvio/seleção nem expor nomes técnicos.
Serviço compartilhado resolve perguntas inteiras reconhecidas de envio/escolha da
foto de ambiente somente quando essa referência está selecionada e autorizada.
Perguntas mistas, factuais, de direitos ou materiais ausentes são preservadas.

Resposta original permanece no trace e resolução fica em editorial_questions,
com justificativa e perguntas restantes. Proposta continua passando por validação
factual normal antes da geração. Não há classificador extra, chamada paga adicional,
alteração do prompt visual, composição ou seleção da foto. API/worker sem reload
precisam reiniciar. Ensaio já pausado não foi reescrito nem retomado automaticamente.

Ruff aprovado nos novos serviços, adapter, materiais e regressões; sintaxe/diff
conferidos. Regressões adicionadas, não executadas conforme orientação vigente.
Sem geração ou testes de integração. Validação manual do fluxo permanece pendente.

## 16/11/2026 — proporção da foto na direção visual

Trace do ensaio b496fb2a-dc47-5a9f-a26b-afa6a6e35cc5 confirmou falso positivo em
creative_brief.photo_use: “evitar adicionar elementos gráficos que cubram mais que
20% da foto”. A regra já aceitava a mesma proporção “da imagem”. Foto e fotografia
agora são reconhecidas como dimensões visuais equivalentes somente no briefing
privado. Não autoriza percentuais em texto público nem descontos na direção visual.

Correção no validador produtivo compartilhado; sem mudança de seleção de fotos,
prompt ou kit. Ruff, formatação e diff conferidos. Regressões de cobertura visual,
texto público e desconto adicionadas, não executadas conforme orientação vigente.
Sem nova geração ou alteração do ensaio encerrado. Reiniciar API/worker sem reload;
validação manual da próxima geração permanece pendente.

## 16/11/2026 — seleção conservadora da foto de espaço pelo pedido

Implementado seletor compartilhado por feed/story via mensagem produtiva e laboratório.
Reconhece indicação visual explícita de fachada, balcão, sala/salão ou ambiente/espaço
usando somente space_kind cadastrado. Não interpreta fotos por título e não chama IA.
Sem categoria inequívoca, com negação ou múltiplas categorias, preserva a ordenação
anterior (environment, room, counter, id). Categoria pedida sem foto elegível também
mantém a seleção habitual. Fotos continuam restritas ao negócio, prontas, ativas,
autorizadas e fora de exclusão. Foto anexada mantém precedência no contexto inicial.

Trace de contexto inclui space_photo_selection: categoria pedida, referência e motivo.
Seleção explícita de espaço também prevalece quando o catálogo fornece uma referência
genérica; foto de produto e limites de referências permanecem iguais. Fonte entra no
fingerprint e continua sendo revalidada por versão/hash/direitos. Contextos antigos
sem o novo metadado não falham apenas pela adição do campo. Mudança limitada a peças
estáticas; sem alteração de prompt, kit, modelo, composição, custos ou aleatoriedade.

Validação: revisão estática, sintaxe Python e diff; Ruff aprovado no novo serviço e
regressões adicionadas. creation_lab_images conserva avisos E501 preexistentes fora
dos trechos alterados. Regressões de pedidos explícitos, genéricos, ambíguos e negados
adicionadas, não executadas. Sem testes/build/navegador ou geração paga por orientação.
Validação visual manual pendente. Reiniciar API/worker sem reload antes de nova criação.

## 16/11/2026 — contagem de linhas no briefing do story

Ensaio 21de1a71-4dea-511f-8300-48ff7d464b1d falhou por números 1 e 2 em
creative_brief.hierarchy: “legível em 1–2 linhas”. Evidência privada confirmou
falso positivo tipográfico; formato já era story. Reconhecimento compartilhado
passa a aceitar contagem/faixa de linhas explicitamente ligada a texto ou
legibilidade em orientação privada. Números soltos, quantidades comerciais e
números no texto público continuam sujeitos à comprovação factual.

Alteração em editorial_design_notation, usada pelo fluxo produtivo e laboratório.
Sem alteração do ensaio encerrado, repetição automática, geração paga ou migração.
Ruff/formatação e diff conferidos; sem testes ou navegador conforme orientação.
É necessário recarregar os processos de API/worker antes do próximo ensaio.
Validação manual de nova geração permanece a cargo do usuário.

## 16/11/2026 — custos por tentativa e total do laboratório

Histórico exibe estimativa conhecida por tentativa, quantidade de chamadas sem custo
apurado, reserva dessas chamadas e total comprometido. Orçamento mostra os mesmos
agregados para todo o laboratório/ator, não apenas os cinquenta itens do histórico.
Sumários usam efeitos duráveis, sem ler traces e sem duplicar reservas como despesas.
Ausência de estimativa não vira custo zero: há aviso de parcialidade e reserva separada.
Comprometido mantém a regra conservadora existente; não se liberam reservas nesta fatia.

Leitura autenticada local: estimativa conhecida US$ 0,023722, reservas sem apuração
US$ 2,05 em três chamadas e comprometido US$ 2,474192. Duas imagens recebidas não têm
estimativa persistida; não há confirmação de fatura. Custo final exato permanece
indisponível até apuração do provedor. Sem migração ou chamada paga. Ruff, Prettier e
diff conferidos; sem testes/build/navegador conforme orientação. Validação visual
manual pendente; reiniciar API local sem reload para carregar os campos.

## 16/11/2026 — mensagem original junto da peça em Conteúdos

Cards das peças aprovadas do laboratório e das peças produtivas passam a mostrar
“Mensagem original”. APIs leem a instrução cifrada da execução inicial do mesmo
negócio/origem, preservando o pedido inicial após continuações. Sem vínculo ou texto
disponível, UI informa ausência; não reconstrói a fala a partir do briefing.
Acesso administrativo exclusivo do laboratório e autorização/RLS do produto mantidos.
Sem migração ou geração. Validação: Ruff, Prettier, diff e leitura autenticada das
peças existentes do Café Aurora. Sem testes, build ou navegador conforme orientação.
Conferência visual e jornada produtiva manual pendentes. Backend local sem reload
precisa de reinício pelo operador para disponibilizar os campos novos.

## 16/11/2026 — contraste do botão Ver peça gerada

A regra button-small sobrescrevia o fundo primário sem alterar o texto branco.
O fundo claro agora se aplica somente aos botões pequenos não primários, preservando
fundo roxo e texto branco antes do hover. Alteração compartilhada de CSS, sem mudança
de comportamento. Prettier e diff conferidos; sem testes, build ou navegador conforme
orientação vigente. Conferência visual manual pendente.

## 16/11/2026 — aprovação ausente não significa pendente

Consulta autenticada confirmou aprovação persistida do último ensaio do Café Aurora.
API local em debug estava sem reload e precisa de reinício pelo operador para carregar
o novo campo do histórico. UI passa a distinguir campo ausente de approved=false:
mostra “aprovação não consultada”, evitando pendência falsa em resposta antiga.
Prettier e diff conferidos; sem testes ou navegador. API do operador não reiniciada.

## 16/11/2026 — status no histórico de ensaios

“Seus ensaios” identifica rascunho não iniciado, fila, andamento, espera de resposta,
peça pronta aguardando aprovação, aprovação explícita, erro, resultado incerto e
cancelamento. Aprovação é consultada por tentativa e ator autorizado, sem inferi-la
da conclusão da geração. Lista mantém ordem cronológica, com texto, ícone e cor.
Status recebido pela execução atualiza o cache do histórico; aprovação invalida a
lista. Sem novo polling, migração ou mudança nas regras de criação/publicação.

Validação estática: Ruff, Prettier e diff. Testes e navegador não executados conforme
orientação vigente; conferência manual das situações na UI permanece pendente.

## 16/11/2026 — espaçamento e feedback visível nas peças de teste

Prévia e aprovação recebem separação visual entre legenda, chamada, download e
aceite; Conteúdos exibe cards com padding e data de aprovação. O aviso de revisão
pendente deixa de aparecer após aceite explícito, sem alterar o parecer original.
Feedback privado ganha seção identificada no laboratório e na peça aprovada em
Conteúdos. A listagem administrativa retorna aprovação e comentários da versão,
com o mesmo controle exclusivo de acesso e sem incluir esses dados nas preferências
reais. Salvar avaliação invalida a listagem de testes aprovados na UI.

Validação: leitura autenticada na base local confirmou uma peça aprovada e um
feedback persistido, também retornado pela listagem atualizada. Ruff, sintaxe Python,
Prettier e diff estáticos conferidos. Sem testes, build, typecheck, navegador ou
nova geração, conforme orientação vigente. Conferência visual manual pendente.
Sem migração ou alteração de dados existentes.

## 16/11/2026 — feedback como referência criativa e aprovação privada de testes

Entrevista concluída: comentários livres do cliente devem ser interpretados como
referências flexíveis, não regras fixas. Aceite de teste exige botão explícito;
feedback do laboratório permanece separado das referências reais.

Implementados serviços/API/UI para feedback opcional após aprovação de versão real,
histórico em Preferências de conteúdo, retirada de comentários do contexto e uso
dos doze mais recentes nos próximos pedidos editoriais/motion. Briefing da versão
é disponibilizado quando existente; ausência de contexto não autoriza inferências.
A resposta ao convite WhatsApp tem correlação própria e não inicia ajuste/geração.
Transporte permanece simulado; feedback por mensagem aceita somente texto nesta
fatia. Não houve fine-tuning nem classificação paga adicional.

Aprovar peça de teste registra versão/hash e exibe sua prévia em Conteúdos marcada
Teste, apenas para o administrador autorizado. Sem cópia para tabelas publicáveis,
sem alteração de preferências do cliente e sem aceite automático de peças antigas.
Migração aditiva 0132 aplicada à base local habitual. Leituras autenticadas dos três
negócios e da peça existente confirmadas; worker dedicado recarregado sem execução
ativa. Sem testes, build, typecheck, browser ou geração paga, conforme orientação.
Regressões unitárias adicionadas, não executadas. Jornada manual e provas de RLS/
concorrência permanecem pendentes. Detalhes e limites em
`docs/design/piece-feedback-and-lab-approval.md`.

## 16/11/2026 — preparação de feedback pós-aprovação e testes em Conteúdos

Usuário autorizou duas frentes: feedback ao final de peças aprovadas e exibição
das peças aprovadas de laboratório em Conteúdos com identificação de teste.
Mapeamento e decisões pendentes em docs/design/piece-feedback-and-lab-approval.md.
Entrevista enviada sobre confirmação das preferências, aceite explícito do teste
e eventual aplicação administrativa de preferências vindas de teste. Respostas
não presumidas; implementação dependente aguarda definição.

Aprovação atual é por versão em Conteúdos, separada de publicação. Respostas
WhatsApp hoje encaminham ajustes, exigindo correlação distinta para feedback.
Transporte permanece simulado. Flags selected/simulated existentes não comprovam
aprovação de teste nem isolamento administrativo. Sem alterações de runtime ou
dados, migração, testes ou chamadas pagas nesta preparação.

## 16/11/2026 — prévia visível ao concluir a criação

O ensaio b555466c-c497-5d66-89ed-2683dbbb3aa2 concluiu e persistiu uma versão
PNG selecionada. Leitura pelo serviço autenticado confirmou a listagem e o arquivo
(1.710.257 bytes). A UI mantinha a seleção de prévias vazia e mostrava solicitação
de ajuste antes da imagem, tornando a entrega difícil de encontrar.

A prévia da tentativa atual abre automaticamente uma vez ao disponibilizar a versão,
priorizando a selecionada pelo produto. Depois disso, escolhas manuais são mantidas.
A imagem/vídeo e download vêm antes do formulário de ajuste. O evento de conclusão
oferece “Ver peça gerada”, que leva à seção e pausa a rolagem automática para não
retirar o operador da peça quando o arquivo carregar. Seleção para avaliação recebe
a versão atual como padrão. Comparação de até duas versões continua disponível.

Validação: leitura autenticada de resultado e arquivo existente, revisão estática,
Prettier e diff. Sem testes automatizados, build, typecheck ou navegador, por
orientação vigente. Sem nova geração, custo de IA, mudança produtiva ou reinício
do worker. Recarregar a UI e abrir o ensaio concluído; avaliação visual permanece
pendente. Não é necessário gerar novamente para acessar esta peça.

## 16/11/2026 — margem de segurança e evidência da rejeição numérica

O ensaio `9e6d6c02-277c-5f3d-adfd-df6b4290febb` foi rejeitado por “mínimo 10% de
espaço livre nas bordas” em creative_brief.photo_use. Era instrução de margem,
não número comercial. O reconhecimento anterior de dimensões não cobria espaço
livre/negativo/de respiro ou margem expressa após o percentual. Essas construções
passam a ser reconhecidas somente na direção privada, com as mesmas restrições
de percentual; os números do texto público não recebem essa exceção.

Rejeições editoriais no fluxo comum agora gravam uma evidência privada
editorial_validation antes do encerramento. Para número não confirmado, registra
campo, números residuais e trecho original (limitado a 700 caracteres por campo),
usando a mesma normalização da guarda. Identidade durável deriva do run; evidência
usa a criptografia, autorização e retenção existentes, sem conteúdo nos logs.
O evento trace.recorded dá acesso pelo botão de dados da etapa na UI existente.
Sem nova chamada de IA, retry ou alteração do histórico anterior.

Validação: leitura do trace, revisão, Ruff, sintaxe Python e diff; regressões
adicionadas para margens e diagnóstico por campo, não executadas por orientação
vigente. Sem suíte, build, typecheck ou geração paga. Worker recarregado após
confirmar ausência de execução ativa/na fila. A confirmação funcional permanece
pendente; o reconhecimento é lexical e ainda pode ter limitações de linguagem.
Sem migração ou alteração das reservas anteriores.

## 16/11/2026 — medidas de layout na pré-validação editorial

O ensaio `10690259-4350-55b7-8b79-dbe7c40a162c` recebeu os novos rótulos sem
códigos e voltou a falhar por `20–25% da altura` em creative_brief.photo_use.
Isso especifica a faixa de texto, não um valor comercial. A guarda de números
continuava estreita para medidas legítimas de composição.

O reconhecimento de direção privada passa a tratar famílias de medidas: intervalos
com hífen/travessão ou “a”, proporções percentuais explicitamente associadas a
dimensões visuais, propriedades de layout, pixels, pontos tipográficos, rem e
canvas com dimensões em pixels. Percentuais visuais são limitados a 0–100 por
extremo. Percentual isolado, desconto, quantidade de produtos, preço, prazo e
número desconhecido continuam sujeitos à evidência factual. A exceção nunca se
aplica ao texto público. A regra permanece lexical, sem promessa de compreensão
semântica completa ou eliminação de todos os falsos positivos.

Validação: leitura do trace, revisão estática, Ruff, sintaxe e diff. Regressões
adicionadas para proporção com intervalo, tipografia, dimensões, descontos,
quantidades, prazos e ausência de exceção no texto público; não executadas por
orientação vigente. Sem suíte, build, typecheck ou geração paga. Worker dedicado
recarregado após confirmar ausência de execução ativa/na fila. Nova geração e
conferência visual permanecem pendentes na UI. Histórico e reservas preservados;
sem migração, alteração de dados comerciais ou repetição automática de chamada.

## 16/11/2026 — referências de materiais sem códigos no briefing

O trace do ensaio `90f3d486-8da6-54cb-ad76-cdffa49d2fcf` mostra feed, acervo e
resposta editorial sem perguntas, mas a direção cita `Ambiente ilustrativo de
referência 2` sem o sufixo de proveniência. A guarda só reconhecia o título
completo e rejeitou o número 2. A correção anterior ficou incompleta; não havia
preço, desconto ou quantidade comercial nesse trecho.

Novos briefings usam rótulos de materiais por papel, sem nomes técnicos ou códigos
numéricos, preservando a declaração de imagem ilustrativa. Os títulos originais,
proveniência, IDs e hashes permanecem no snapshot privado, e a geração continua
usando os mesmos arquivos verificados. Ausência da declaração de ilustração não
comprova autenticidade da foto. O reconhecimento de títulos de snapshots antigos
aceita o nome exato anterior ao separador de proveniência, com limites de palavra:
referência 2 não autoriza referência 25, 3 ou o número isolado. Textos públicos
mantêm a checagem integral; não foi relaxada a validação de dados comerciais.

Validação: inspeção do trace, revisão estática, Ruff, sintaxe Python e diff.
Regressões acrescentadas para abreviação autorizada, identificadores diferentes
e preservação do caráter ilustrativo; não executadas conforme pedido vigente.
Sem testes, build, typecheck ou geração paga. Worker dedicado recarregado após
conferir ausência de execuções running/queued. A validação funcional continua
pendente de nova tentativa pela UI. Sem migração ou alteração do ensaio anterior.

## 16/11/2026 — rolagem acompanhando a execução

A UI acompanha automaticamente o final da execução quando chegam eventos, texto,
perguntas ou resultados, incluindo mudanças de altura após carregar imagens.
O rascunho ainda não iniciado não desloca a página automaticamente. Subir para
ler, abrir detalhes/trace ou focar um campo pausa o acompanhamento. Voltar ao final
rolando para baixo ou usar “Acompanhar atualizações” retoma. Trocar de tentativa
reinicia o comportamento. A rolagem é imediata, sem animações concorrentes durante
streaming, e não transfere o foco de teclado para os novos eventos.

Implementação somente no front, usando MutationObserver/ResizeObserver e um frame
agendado por atualização, com limpeza ao desmontar. Não há polling, endpoint novo,
mudança de orçamento ou reinício de worker. Validado por revisão, Prettier e diff;
sem testes automatizados, build, typecheck ou browser conforme orientação vigente.
Conferência de rolagem e pausa no navegador permanece com o administrador.

## 16/11/2026 — diagnóstico da rejeição editorial e números de direção visual

O ensaio `8fdec608-ab96-5723-a6f9-7f0451d49f48` já usou photo/feed, logo e foto
de ambiente, sem perguntas editoriais. A resposta completa foi recebida; a geração
da imagem não iniciou. A guarda lexical rejeitou números do título da foto
(`referência 2`, `Pexels 31777028`) e `85% opacidade` na direção privada. A legenda
também continha `hoje`, expressão temporal sem respaldo no único fato citado.

A pré-validação distingue títulos exatos dos materiais autorizados fornecidos pelo
servidor e notação de opacidade entre 0 e 100% na direção privada. Essas exceções
não autorizam números no texto público, nem preços, descontos ou datas. Mantém
restrições de temas, fontes e canais. O prompt orienta convites sem data quando
não houver evidência temporal, sem transformar essa escolha criativa em pergunta,
e exige frases completas dentro dos limites dos campos. Não houve corte/reparo
automático nem aceitação retroativa da resposta anterior.

A guarda passa a devolver causa estável: formato, referência factual, conteúdo
incompleto, texto interno exposto, tema evitado, CTA não confirmado, número ou
alegação sem confirmação. O fluxo comum persiste esse código no estado final e a
UI o explica. O wrapper booleano permanece para chamadas existentes. O ensaio
histórico mantém EDITORIAL_RESULT_UNCERTAIN; não há reescrita do trace ou ledger.
A guarda continua lexical e não prova verdade semântica nem qualidade comercial.

Validação: leitura do trace local, revisão estática, Ruff/Prettier, sintaxe e diff.
Regressões adicionadas para títulos autorizados, opacidade e ausência de autorização
para números/alegações públicas; não executadas conforme orientação vigente.
Sem suíte, build, typecheck, browser ou chamadas pagas. Worker dedicado recarregado
após conferir ausência de execuções running/queued. Nova geração pela UI e avaliação
visual permanecem com o administrador. Sem migração e sem retry automático.

## 16/11/2026 — acompanhamento contínuo e recarga do worker local

Acompanhamento administrativo passa a mostrar ícones por evento e indicador animado
somente no último evento de processamento enquanto o estado é running. Fila, espera
por resposta, interrupção e registro têm indicações distintas; animação respeita
preferência de movimento reduzido. O trace abre dentro do evento clicado, com botão
expandir/recolher, sem levar o operador ao final da página. Perguntas e revisões
ficam na sequência do histórico, e resultados/ajustes vêm depois. Checkpoint SSE
invalida imediatamente status e perguntas existentes, sem novo temporizador.

A tentativa `92145155-255f-57e9-8ed6-e175e91a670c` ainda foi executada pelo worker
antigo: trace confirma formato story, apenas logo e ausência de available_materials
e das instruções novas. O processo anterior estava ativo desde 15h11; foi encerrado
após leitura confirmar ausência de execuções running/queued. Worker dedicado foi
reiniciado com o código atual, sem disparar geração. Ensaios anteriores não foram
reescritos nem retomados automaticamente; a próxima validação exige novo ensaio.

Orientação editorial compartilhada reforça que não se pede asset ID/UUID ao cliente,
nem reconfirmação do destino já cadastrado pelo titular. O processamento conserva
as verificações reais de autorização de material; dados cadastrados não autorizam
publicação automática. Escolhas criativas opcionais não devem bloquear a peça.

Validação: inspeção do trace persistido e processo local, revisão de alterações,
Prettier, Ruff, sintaxe Python e diff. Sem testes automatizados, build, typecheck,
validação de navegador ou chamadas pagas, conforme orientação vigente. Qualidade
da próxima resposta e da UI continua pendente de validação manual pelo administrador.
Sem migração ou mudança de autorização/orçamento. O laboratório permanece exclusivo
do administrador; as orientações de criação valem para a entrada comum do produto.

## 16/11/2026 — feed institucional, acervo e perguntas essenciais

Diagnóstico da execução local `297abe95-bf8c-5c24-8727-fdb2170df894`: a mensagem
pedia explicitamente post pro feed, mas a interpretação retornou formato nulo.
O fallback de texto assumiu story. Sem produto selecionado, o contexto continha
somente o logo; a seleção de fotos dependia do catálogo. O editorial perguntou
por foto, escolha opcional de item e restrições hipotéticas de composição.

No serviço comum de mensagens (WhatsApp e laboratório), uma solicitação textual
inequívoca de post/foto/imagem para feed recupera uma abstenção do interpretador.
Negação e menção concorrente a vídeo/story/reel/carrossel não usam essa recuperação.
Texto sem formato resolvido pede esclarecimento em vez de assumir story. Formatos
positivamente classificados continuam sujeitos às validações existentes.

O snapshot visual passa a capturar uma foto de ambiente autorizada, ativa e pronta,
sem exclusão em andamento, quando não há foto anexada e existe espaço no limite.
Seleção determinística prioriza environment, room e counter; não é ranking visual
por IA. ID, versão, hash e título integram o snapshot e sua revalidação. Pedidos
institucionais conservam essa fonte mesmo sem item de catálogo. O editorial recebe
os papéis/títulos dos materiais disponíveis também nessa situação, sem URLs internas.
A geração recebe a imagem e verifica o hash. O prompt exige perguntas apenas para
lacunas factuais essenciais, aplica logo/layout do kit e delega posicionamento ao
briefing; não exige escolher produto para um convite institucional. Isso não afirma
que o modelo jamais fará uma pergunta inadequada; qualidade continua sujeita à revisão.

Leitura da base e do armazenamento confirmou os três logos existentes vinculados
aos kits, prontos/autorizados e com hash íntegro. Cada negócio possui oito fotos
ativas/prontas, duas de ambiente. Não foi necessário criar ou substituir logos.
Fotos demonstrativas continuam sendo ilustrativas, conforme cadastro.

Validação: consulta local de diagnóstico, leitura dos três arquivos de logo,
revisão de código, Ruff, sintaxe e diff. Regressões unitárias adicionadas para feed,
ambiguidade, ausência de formato e preservação das fontes sem catálogo. Sem executar
testes, build, typecheck ou geração paga por orientação do usuário. Não há migração
nem reescrita do ensaio anterior. Reiniciar o worker para carregar os serviços e
iniciar novo ensaio pela UI; validação funcional permanece com o administrador.

## 16/11/2026 — encerramento das consultas após a execução

Consultas de status/resultados param nos estados completed, failed, uncertain e
cancelled. Há uma atualização final de resultados, checkpoints, anexos, histórico
e orçamento para não perder dados confirmados na transação de encerramento.
Checkpoints param junto do status; histórico/orçamento deixam de ter temporizador.
Anexos usam uma chave compartilhada entre componentes e só são consultados
periodicamente enquanto há upload aguardando confirmação. Erros de consulta
não mantêm intervalos indefinidos; ações explícitas conservam atualização/refetch.

SSE drena o replay antes de emitir stream.finished e encerrar, incluindo a corrida
em que o estado final é confirmado entre a leitura de eventos e a de status. O
cliente fecha o leitor, não reconecta após o fim e não reabre a conexão apenas
porque o token foi renovado. Reabrir uma execução faz uma nova leitura finita.
Foco/reconexão não reativam as consultas do ensaio concluído. O temporizador de
acesso foi removido; conferência de acesso na entrada/foco e autorização em cada
requisição continuam vigentes. Consulta de trace/download e feedback continuam
acionados pelo usuário; retenção de trace continua independente do SSE.

Validação: revisão de temporizadores, callbacks e fechamento do stream; formatação,
sintaxe e diff. Adicionado teste de regressão do encerramento SSE para os quatro
estados finais, não executado. Sem suíte, build, typecheck ou geração paga, conforme
orientação vigente. Validação na aba Network do navegador permanece manual.
Sem migração e sem mudança no worker ou no processamento da peça.


## 16/11/2026 — acompanhamento explicado e limite da resposta editorial

O primeiro ensaio de feed parou antes da geração da imagem: o trace persistido
mostra resposta editorial `incomplete`, motivo `max_output_tokens`, com saída de
1.200 tokens (512 de raciocínio) e JSON interrompido. Não foi falha de geração de
imagem. O erro genérico escondia a causa.

Pedidos editoriais de peça completa passam a permitir 4.096 tokens; pedidos
legados simples conservam 1.200. A estimativa anterior à chamada usa o limite do
próprio payload. Para o pedido observado, o limite calculado de 11.091 USD micros
cabe na reserva configurada de 50.000, sem mudar teto ou configuração de custo.
Resposta truncada com uso informado é registrada como retorno recebido, porém
não aceito, e encerra a execução com `EDITORIAL_OUTPUT_LIMIT_EXCEEDED`. Não há
retry automático nem uso de JSON parcial. Reservas permanecem conservadas.

A UI explica ação, retorno e próximo passo em cada estágio, destaca a situação
atual e guarda códigos nos detalhes técnicos. Resposta registrada não significa
validada. Reserva acumulada não é apresentada como fatura confirmada. Para falha
histórica genérica, GET pode apresentar diagnóstico específico derivado do trace
não expirado; estado, efeitos e custos históricos não são reescritos.

Validação: leitura de metadados/uso do trace existente, cálculo local do limite,
revisão e formatação/sintaxe. Teste de regressão adicionado, não executado. Sem
suíte, build, typecheck ou novas chamadas pagas, mantendo a orientação do usuário.
O novo limite precisa de confirmação funcional em uma nova tentativa autorizada
pela UI; não garante sozinho qualidade editorial ou visual. Sem migração.


## 16/11/2026 — entrada comum de criação para laboratório e WhatsApp

Novas mensagens dos dois canais usam `MessageCreation` e o mesmo workflow Temporal
para interpretar intenção/catálogo/formato, pedir informações, gerar feed/story ou
encaminhar reel ao orquestrador produtivo. A UI nova remove formato/modo e aprovações
criativas exclusivas. Respostas/ajustes compartilham composição e saldo restante;
anexos podem ser substituídos antes do início, com histórico preservado.

Migrações aditivas 0130/0131 aplicadas somente à base local habitual. Origem imutável,
RLS por execução/proprietário e dependência exclusiva na API mantêm o laboratório
privado. Produto reserva atomicamente no ledger comercial, com permissões por execução
e estimativas de exposição separadas de faturas, e mantém plano/consentimento; laboratório
usa seu teto administrativo. Peças produtivas entram na revisão existente; perguntas
e resultados têm recibos locais explicitamente simulados. Sem envio externo ou
publicação. Trace mantém sete dias; arquivos e custos permanecem.

Rascunhos anteriores devem ser copiados como novo pedido. Workflows anteriores e
continuações produtivas antigas preservam o caminho legado via patches Temporal.
O teto informado na UI é único por peça: transcrição, interpretação, imagem e vídeo
consomem o mesmo saldo. A reserva de áudio é calculada internamente pela duração
e tarifa documentada, sem configuração de um orçamento adicional. Documentado em `docs/design/shared-message-creation-flow.md`.

Validação: revisão, sintaxe, lint de símbolos, formatação, migração local e carga do
worker dedicado. Testes de encaminhamento/isolamento adicionados, mas **não
executados**, seguindo a instrução do usuário. Sem build/typecheck, CI ou geração
paga; qualidade visual e equivalência funcional ainda dependem do aceite manual.
Limites semanais por formato e melhorias de motion ficam para a próxima etapa.


## 16/11/2026 — unificação de mensagens autorizada, em andamento

O usuário exige o mesmo processamento para produto e laboratório e autorizou
integrar reels à entrada produtiva junto de feed/story. Extraída a coordenação de
`ContentCandidateActivities` para `ContentCreationService`, mantendo atividades,
contratos e comportamento atual; publicação permanece no adaptador de saída.

Esta é uma preparação estrutural, não a conclusão da feature: a entrada produtiva
ainda está limitada a feed/story e o laboratório ainda possui o caminho de imagens
separado. Faltam entrada normalizada, ligação de reels, coordenador comum, persistência
privada/financeira, retomadas e UI sem decisões criativas exclusivas. Decisões de
privacidade, orçamento administrativo e não publicação continuam vigentes.

Revisão de código e formatação somente; sem testes, geração paga, migração ou
reinício de serviços. Não afirmar equivalência integral enquanto houver esses
caminhos concorrentes. Evidências e critérios em [fluxo único](../design/shared-message-creation-flow.md).


## 16/11/2026 — retirada da seleção manual de fotos do laboratório

Por decisão do usuário, o ensaio não possui mais uma escolha manual de fotos do
acervo. Removidos seletor da UI, contrato/endpoint de seleção e cópia de escolhas
para continuações. O contexto retorna informações do negócio, sem listar fotos
para escolher. Anexos da mensagem continuam privados e disponíveis.

Posts/stories vinculados a um item recuperam as referências de produto/ambiente
do `selected_catalog_snapshot` produtivo, depois da confirmação do catálogo, com
revalidação de versão/hash antes dos efeitos. Sem item associado não se escolhe
um produto arbitrário: permanecem os anexos e a marca. Reels usam a seleção padrão
do `MotionContext` produtivo (até quatro fotos elegíveis, ordenadas por id), com
leitura administrativa sem row-lock de escrita; não é ranking semântico. Anexos
explícitos têm prioridade dentro do limite. Não foram adicionadas regras de
seleção visual por IA.

Registros antigos de seleção permanecem apenas para histórico/exportação; novas
execuções e continuações não os consomem. Ensaios de imagem anteriores com escolhas
fixadas podem exigir nova tentativa por mudança de contexto, em vez de alterar
silenciosamente uma execução já iniciada. Nenhuma migração ou alteração no acervo.

Validação: revisão dos caminhos de captura, catálogo, retomada e geração, formatação
e conferência do diff. Não executados testes automatizados, build, typecheck ou
gerações pagas, conforme instrução vigente. Reiniciar API e worker do laboratório
para carregar o backend atualizado. Esta decisão substitui as descrições anteriores
de seleção manual do acervo.


## 16/11/2026 — base local com três negócios demonstrativos

Limpeza da base local habitual autorizada sem backup: preservada a conta admin
com senha/MFA/sessões e substituídos dez negócios antigos por Café Aurora, Ateliê
Lia Nails e Vértice Seminovos. Há quatro contas, três organizações e um único
administrador. Cada cenário tem seis itens, uma promoção, oito fotos ilustrativas,
contexto, endereço, marca própria no kit-base existente, aceite de IA e cortesia.
Quatro perfis de referência foram indicados; não houve análise paga de feeds.

O admin tem vínculo explícito de proprietário nas três organizações e alterna no
seletor existente em **Ver meu espaço → Organização**. Catálogo/acervo/referências
ficam em **Sobre meu negócio**; marca em **Kits visuais**. Nenhuma visão detalhada
foi adicionada ao laboratório, e clientes continuam sem acesso a ele. Fixtures
`.test` não receberam senha nem e-mails: o acesso solicitado é pela conta admin.

Carga pelos serviços com RLS/auditoria/outbox, retomável por identidade de operação;
reset protegido por ambiente, base loopback e revisão de schema. Leituras de sessão,
laboratório e serviços confirmaram seleção e dados dos três cenários. Sem suíte de
testes, build, typecheck ou geração paga, conforme pedido. Worker exclusivo do
laboratório reiniciado; consumidores gerais permaneceram parados.

Limitações documentadas: um kit-base com três personalizações, acervo de fotos
(vídeo para reels ainda é anexo do pedido), referências sem aprendizagem executada,
atributos de veículos em texto livre e integrações externas não conectadas. Origem
das fotos registrada no manifesto; preços/endereços/estoque fictícios. Infraestrutura
de objetos não foi apagada indiscriminadamente. Ver [cadastros, navegação, evidências
e manutenção](../demo-businesses.md).


## 16/11/2026 — respostas, ajustes e teto pela UI

Esta entrada substitui as limitações de continuidade e orçamento das entradas
anteriores. O teto obrigatório é informado na UI por ensaio. Ajustes e respostas
usam o saldo do teto original, sem renová-lo. O teto global é opcional: zero em
`creation_lab_budget_usd_micros` significa ausência desse limite adicional, e não
execução desabilitada. A habilitação técnica independente é
`creation_lab_execution_enabled`, falsa por padrão. A identidade administrativa
exclusiva, consentimentos, reservas antes de efeitos e o limite por ensaio continuam
obrigatórios. Não altera planos, saldos ou quotas comerciais.

- Perguntas de intenção/editorial suspendem a criação e aparecem na UI; aprovar
  um checkpoint com perguntas é recusado. Responder prepara uma continuação no
  mesmo histórico, conservando pedido original, anexos e seleção do acervo.
- “Preparar ajuste” existe na revisão e na peça concluída. Cada tentativa tem
  identidade própria, referência à anterior e ao ensaio raiz; não reaproveita a
  identidade de uma chamada paga. Há uma única continuação por tentativa, no
  máximo dez tentativas e 4 mil caracteres para o pedido composto. Uma chamada
  não resolvida impede continuação. O operador revisa e inicia a nova tentativa
  pela UI; enviar feedback isolado continua sem autorizar geração.
- Peças de tentativas do mesmo ensaio podem ser comparadas na UI. Downloads e
  feedback usam a tentativa proprietária. Cada tentativa conserva seu trace,
  custos e pacote exportável; só o trace expira sete dias depois do seu término.
- Catálogo deixa de ser obrigatório para imagens. Sem correspondência, um pedido
  de criação identificado pode usar fatos vigentes e marca confirmada, com regras
  factuais/CTA compartilhadas. Não cria um item fictício nem transforma texto do
  modelo em fato. O laboratório apresenta essa base para confirmação; informações
  essenciais pendentes viram perguntas. No produto, o briefing institucional é
  recapturado antes de efeitos e respeita a validade dos fatos.
- A jornada produtiva WhatsApp passa a vincular respostas a uma pergunta citada e
  `Pedir ajustes: ...` com observação à entrega anterior. O material recebido
  continua sendo a identidade durável do workflow; ligação, autorização e auditoria
  são persistidas. Pedido composto e proveniência são compartilhados pelas etapas
  de briefing, editorial e geração visual. Uma mensagem nova sem referência não
  é presumida como resposta. O comando sem observação registra a decisão existente,
  sem inventar um ajuste. A entrega de candidatas continua simulada: isto não
  conclui a integração externa do WhatsApp nem a publicação real.

Migrações aditivas 0128 e 0129 aplicadas somente ao banco local de desenvolvimento.
O runtime `app.entrypoints.creation_lab` usa Temporal e o relay existente filtrado
para eventos do laboratório, em fila exclusiva. `make creation-lab` inicia esse
serviço persistente; os pedidos são feitos pela UI. Configuração local preparada
com credenciais existentes e imagem do renderizador já instalada. Worker exclusivo
iniciado após leitura confirmar zero execuções/etapas aprovadas pendentes; nenhum
consumidor antigo foi reiniciado por esta alteração. Flags produtivas não são
habilitadas pelo adaptador administrativo.

Revisão de código e formatação Ruff/Prettier realizadas. **Não executados testes,
CI, typecheck, build, QA em browser ou geração paga**, conforme pedido do titular.
A validação ponta a ponta será feita por ele pela UI. Não há alegação de qualidade
estética validada. Limites semanais por formato e melhorias dos motions permanecem
na etapa posterior combinada.

## 16/11/2026 — integração da execução privada do laboratório

Implementada a ligação da UI às etapas produtivas: início idempotente, fila via
outbox/Temporal, confirmação de catálogo, checkpoints, cancelamento, peças privadas,
comparação/feedback e pacote de execução. Migrações aditivas 0125–0127 aplicadas
somente ao banco local de desenvolvimento. Esta entrada substitui o estado de
integração pendente das entradas anteriores, sem declarar validação operacional.

Decisão confirmada nesta continuação: para posts/stories, o modelo sugere o produto
ou serviço a partir da mensagem e o administrador confirma antes da geração.
O fluxo reutiliza candidatos/snapshot de catálogo, Jev, provedor editorial, regras
factuais/CTA, skills, prompt de peça completa e provedor visual do produto. Não
seleciona automaticamente um item por coincidência textual. Ambiguidade/dúvidas
interrompem a tentativa com trace disponível; revisão do pedido inicia outro ensaio.
No acompanhado há revisão editorial adicional; no automático ela avança após as
validações. A confirmação do catálogo continua obrigatória nos dois modos.

Reels reutilizam MotionOrchestrator e as etapas de preparação, planejamento,
implementação, storyboard, render, crítica e correção. Adaptadores mudam admissão,
fontes privadas, financiamento e persistência; preservam o bloqueio de alterações
visuais pendentes. Não personificam o proprietário nem
escrevem peças/quota do cliente. Checkpoints obrigatórios do produto permanecem
obrigatórios, inclusive no modo automático. Entrada: um vídeo MP4 e até quatro
imagens complementares PNG/JPEG somadas à seleção do acervo. Imagens privadas são
normalizadas pelo preparador compartilhado, com proveniência de upload; nomes de
arquivos não se tornam fatos comerciais. Áudio separado/múltiplos vídeos não são
inferidos como direção de edição e geram impedimento explícito.

Trace guarda entradas/saídas disponíveis e deltas reais dos adapters Responses de
motion/editorial. SSE reconecta por cursor; expiração normal de token permite
renovação sem repetir geração. Jev e Images apresentam espera/resposta terminal,
sem digitação simulada. Parciais não autorizam uso do resultado. Frames de storyboard
ficam no trace cifrado, evitando objetos de diagnóstico órfãos no armazenamento.
O trace é apagado sete dias após término; peças, anexos, textos/legendas, feedback,
auditoria e compromissos de custo permanecem. ZIP inclui o disponível no cursor,
com expiração explícita, sem credenciais; limites de tamanho recusam em vez de
truncar silenciosamente. Consulta/download revalidam acesso e integridade.

Claims, tokens de execução e identidade da etapa impedem repetir efeitos pagos e
impedem uma falha atrasada de finalizar uma etapa mais nova. Cancelar impede novas
etapas; chamadas já submetidas podem terminar/custar e mantêm reserva quando o
resultado é incerto. Compromissos administrativos são separados da franquia do
cliente; estimativa não é fatura confirmada. Teto global padrão zero, sem reset
semanal implícito. Tarifas/reserva editoriais novas também começam em zero.

Validação realizada: leitura/revisão do código, formatação Ruff/Prettier e aplicação
das migrações locais. Por orientação do titular, **não** foram executados testes,
CI, typecheck, build, QA em browser ou geração paga. Não há evidência de sucesso
ponta a ponta nem de melhoria estética. Ativação depende de configuração explícita
de fornecedores, orçamento/tarifas, armazenamento/renderizador e worker/relay
atualizados; consumidores anteriormente pausados não foram reiniciados. Limites
semanais por formato e melhorias de qualidade dos motions continuam para a etapa
seguinte, conforme decisão do titular.

## 16/11/2026 — execução administrativa ainda em integração

Infraestrutura adicionada para compromisso de orçamento, efeitos privados,
trace cifrado e versões/feedback (migrações 0123/0124). Retenção confirmada:
apagar somente o trace sete dias após término; anexos, peças, auditoria e custos
permanecem. Há workflow Temporal de limpeza; consumidores locais seguem pausados.
Teto administrativo padrão zero, sem autorização implícita de geração paga.

Etapas produtivas de motion estão sendo preparadas para reutilização com leitura
e persistência privadas. Corrigida e formatada a extração dos leitores de materiais.
Ainda faltam admissão administrativa ligada à geração, retomada das aprovações e
jornada completa de imagens/vídeos pela UI. O adaptador de motion recusa execução
até essa ligação existir. Exportação atual é de rascunho, não da execução completa.
O laboratório ainda não valida o meio inteiro do fluxo produtivo. Sem testes,
build ou geração paga nesta continuação, conforme orientação do titular.

## 16/11/2026 — organização da UI e seleção privada do acervo

Laboratório reorganizado com seletor de negócios em cards, busca com campo visível,
cabeçalho compacto após seleção, histórico lateral e editor de pedido. CSS local
reutiliza cores/componentes existentes e prevê layout móvel, foco por teclado e
estados vazios/erro. Novo rascunho e reutilização explícita de pedido geram outra
identidade de operação; a reutilização não copia anexos nem seleção de fotos.

Seleção de até quatro fotos confirmadas do acervo agora é persistida somente no
laboratório, com versão/hash/título cifrados, autorização exclusiva/RLS, identidade
idempotente e evento SSE transacional. Migração aditiva 0122 aplicada ao banco local.
Não modifica o acervo. Material selecionado deve ser revalidado antes de geração.
ZIP captura mensagem, eventos, uploads e seleção em uma mesma leitura SQL; inclui
referências do acervo, não seus arquivos. Recusa exportação acima de 10 mil eventos
em vez de truncar silenciosamente. Sem testes/build/typecheck/QA visual nesta etapa,
conforme orientação do titular. Revisão do código e formatação apenas.

Permanecem pendentes execução produtiva, aprovações, orçamento administrativo
efetivo, trace do modelo e retenção/limpeza de sete dias. Redesign não habilita
geração nem comprova qualidade de motion.

**Consulta do contexto implementada nesta continuação:** o rascunho permite
consultar kit confirmado, fatos vigentes, aceite de IA e até 50 fotos autorizadas
do acervo. Migração aditiva 0121 aplicada localmente. Políticas SELECT validam o
negócio e o ator do ensaio sob FORCE RLS; escopo é definido pelo serviço somente
na transação, nunca por header. Não concede escrita nem personifica proprietário.
A consulta reutiliza as projeções de contexto/kit e a regra de consentimento do
produto; não é snapshot de geração, seleção de mídia nem autorização para gerar.
Sem testes/build nesta etapa. Permanecem as pendências de execução abaixo.

**Continuação — anexos e exportação de rascunhos:** upload privado com direitos
confirmados, limites por arquivo/ensaio, claim durável anterior ao armazenamento
e estados `uploading/ready/uncertain`. Reenvio da mesma operação não repete PUT.
Downloads autenticados revalidam acesso depois do armazenamento e verificam hash;
pacote ZIP de rascunho contém mensagem, eventos e anexos confirmados até o cursor,
sem simular trace de modelo. Migração aditiva 0120 aplicada somente ao banco local
de desenvolvimento; armazenamento local iniciado, consumidores continuam pausados.
Sem testes, build ou chamadas de geração nesta continuação, por orientação do titular.
A execução produtiva, orçamento efetivo, aprovações, seleção de acervo, trace de
modelo e expiração de sete dias continuam pendentes: não é a entrega completa.

Planejamento deve anteceder imagens **e vídeos**. Laboratório é a área exclusiva;
acompanhado/automático são modos internos. Limites semanais separados por formato
ficam documentados para a próxima etapa, sem bloquear a conclusão do laboratório.

## 16/11/2026 — laboratório administrativo: acesso e seleção implementados

**Continuação vigente, ainda incompleta:** rascunhos privados cifrados,
histórico e eventos SSE autenticados implementados; migração aditiva 0119
aplicada ao banco local de desenvolvimento, sem remover dados comerciais.
Salvar rascunho não gera nem reserva saldo. A pedido do titular, não corrigir
nem executar testes nesta etapa. O CI anterior foi interrompido por coluna
`policy_id` ausente no banco de teste antigo; validações abaixo são da fatia
anterior de acesso/seleção, não da árvore atual. Restam geração por formato,
anexos, orçamento efetivo, trace do modelo, retenção/download e UI completa.

Requisitos confirmados: todos os formatos já desenvolvidos, modos automático e
acompanhado, ensaios separados, orçamento administrativo sem franquia do cliente,
SSE com deltas quando disponíveis, trace por sete dias e download. Apenas o perfil
admin do titular pode escolher negócios; clientes e outros admins não acessam.
Testes podem ocorrer sem plano comercial ativo, preservando aceite de IA/material;
anexos novos ficam privados no laboratório. Primeiro entregar a jornada, depois
gerar uma peça e melhorar motion a partir do resultado.

Implementados no backend a autorização por identidade configurada e staff ativo,
busca auditada/paginada e endpoints de descoberta. Front tem entrada exclusiva,
rota administrativa e seleção real de negócios; geração ainda não disponível.
Conta conferida e promovida a staff mediante autorização explícita, com auditoria;
configuração individual somente no ambiente local. MFA existente preservado.

Validação: sete testes unitários/HTTP e uma integração PostgreSQL passaram;
módulos novos com 100% linhas/branches, lint e mypy aprovados. Web: tipos e
528 testes/100% nas quatro métricas. QA Chromium em 390/1440 px e build passaram para a fatia anterior; CI backend não concluído.
Docker iniciado pelo titular; dez consumidores antigos pausados com autorização,
PostgreSQL/Temporal disponíveis. Na fatia inicial não houve migração; 0119/0120 foram aplicadas depois. Sem geração paga ou publicação.

Pendentes: persistência, execução produtiva por formato, orçamento separado,
anexos, SSE/trace, retenção/exportação e jornada completa. Não é entrega final.
[Especificação, decisões e evidências](../design/admin-production-rehearsal-2026-11-16.md).

**Estado vigente após o feedback do titular — 13/11/2026: entrega REPROVADA.**
O titular rejeitou o MP4 final desta rodada e apontou repetição visual, perda de
frases e de encenação com café/xícara, e distância das 41 referências. O objetivo
de qualidade não foi alcançado. O parecer automático `adequate` e os avanços
pontuais descritos abaixo não demonstram melhoria artística aceita. A conclusão
técnica do fluxo permanece válida, separada da reprovação visual.

Após interromper a rodada, o titular solicitou os 336 quadros (exportados com
manifesto e ZIP em `.local/evals/motion-quality-20261113/`) e depois pediu estudo
próximo de uma referência, admitindo cópia como exercício. Esse pedido permite
trabalho local; não renova orçamento pago. Uma reconstrução manual deve ser
identificada como estudo e não como prova de melhoria do gerador. A avaliação do
texto externo sobre motion por código confirmou que essa arquitetura já existe
no produto; trocar renderer, por si só, não tem ganho visual demonstrado.

Atualização documental: sem código de produção, render ou chamada paga novos;
`git diff --check` é a validação desta atualização. O CI registrado abaixo é da
implementação anterior. Permanecem a reconstrução comparativa e a demonstração
de qualidade no processo do produto; não há nova peça aprovada.

**Registro da entrega anterior ao feedback (histórico):**

**Motion — entrega local de 13/11/2026.**
Peça revisada completa gerada pelo produto e concluída no fluxo nativo, com
Temporal, checkpoints, render e crítica persistidos. MP4 H.264/AAC, 11,2 s,
720×1280 a 30 fps; decodificação integral independente aprovada. Entrega privada:
`.local/evals/motion-quality-20261113/cafe-pausa-final.mp4`, comparação em
`comparacao.html` e avaliação/custos em `RELATORIO-FINAL.md` no mesmo diretório.
Hash da entrega: `834fefbcabe842b4e254666ccebb8ee1ee76dc1a7df8b74d69f7b2524e2b9992`.

Avaliação visual amostrada do assistente: ganho na presença do preparo, imagem
participando das letras em 3,57–3,70 s e transformação de Pausa em Café Pausa
entre 8,44–9,44 s. CTA maior e estado final mais longo que na primeira candidata
desta rodada. Limites: uma tomada, composição sóbria, integração tipográfica
breve; sem afirmar equivalência geral às 41 referências. Sem escuta perceptiva
do assistente; **aceite visual/sonoro do titular pendente**. Parecer nativo
`adequate` não substitui esse aceite: a primeira candidata também foi considerada
adequada pelo modelo e recebeu revisão de direção pela observação do assistente.

Implementados repertório executável v5, encenação consumida na construção e
inspeção, inventário de materiais reais, amostragem por risco, correção delimitada
e retorno ao plano por crítica nativa ou observação explícita do operador,
vinculada ao MP4/quadros. A mensagem simples é mantida, sem baseline obrigatório
de cliente ou meta de cenas. Plano e código finais foram gerados pelo modelo,
sem edição manual da composição. A revisão ocorreu no serviço do produto;
a rodada demonstra melhoria supervisionada, não garantia autônoma de acabamento.

Continuações explícitas preservam planos/MP4 recebidos e histórico de falhas,
sem replay pago. Orçamento menor do pedido é conservado perante o padrão do
worker; recuperação de admissão só ocorre após recusa sem efeitos. Auditoria,
outbox, RLS, idempotência e execução por Temporal mantidos. Executor local
qualificado com áudio v2/fingerprints; sem migração de dev, publicação, commit,
habilitação global ou alteração em spotlight-api. Cinco serviços restritos parados.

**Validação vigente:** `make ci` passou com 6.351 testes Python e 100%
linhas/branches (22.728 statements, 6.602 branches), lint, tipos, 391 testes de
avaliação e 189 testes Node. Manifesto do código conferido; nenhum gate desse
comando pendente. Seis chamadas pagas: **US$ 1,286597 estimados**, US$ 7,50 em
reservas internas, teto autorizado US$ 12,50; materiais novos pagos US$ 0.
Nenhum efeito pago sem estimativa; fatura não reconciliada.

Pendências: aceite do titular, escuta da mistura e calibração da crítica automática,
que foi permissiva na primeira candidata. Motion global permanece desabilitado.
Decisões, validações e histórico no [registro da execução](../design/motion-execucao-melhoria-2026-11-13.md).

**Histórico documental anterior à implementação desta sessão:**

**Leitura das instruções de motion — 13/11/2026.**
A auditoria documental identificou gates históricos, versões, custos e estados
operacionais descritos como “atuais” em registros antigos. Para a próxima rodada,
consultar `docs/design/motion-orientacao-vigente-2026-11-13.md` e o roteiro de 13/11.
Relatos abaixo permanecem históricos no escopo de cada entrega; não renovam
orçamento, não repetem migração e não substituem instruções atuais do titular.
Correção somente documental; capacidades propostas ainda não implementadas.

**Roteiro técnico até uma nova peça completa — 13/11/2026.**
Análise convertida em sete etapas com entregáveis e critérios de avanço:
baseline, mecanismos executados, planejamento/material, ciclo de revisão,
validação/orçamento, geração completa e avaliação do resultado. Roteiro em
`docs/design/motion-roteiro-melhoria-peca-completa-2026-11-13.md`.
Estado: proposto, ainda não implementado. Esta alteração é documental;
nenhuma nova chamada paga, migração, render ou mudança de produção. A próxima
execução deve entregar MP4 pelo processo melhorado, distinguindo prova técnica,
melhora visual e aceite do titular. Orçamento novo exige autorização explícita.

**Prévia reprovada visualmente; 41 referências analisadas — 12/11/2026.**
Titular considera a peça abaixo do mínimo em cenas/conteúdo/transições/impacto;
áudio é avanço pontual, sem aprovação global da mistura. Não é falta de exemplos
nem escolha obrigatória de um estilo. Analisados 16 links e 26 Shorts do canal
PropagandaIA (um em comum): 41 vídeos, 542,586 s, 2.166 amostras em toda a duração,
87 amostras adicionais de quatro passagens e notas individuais/galeria privada.
Sem escuta perceptiva ou auditoria de ferramentas dos autores. Diagnóstico:
conteúdo/material, encenação e inspeção executada são insuficientes na rodada;
fidelidade ao plano e cobertura declarada não garantiram elaboração visual.
Capacidade de imagem disponível no produto estava desabilitada; vídeo gerado/3D
não podem ser presumidos. Parte importante das referências é motion por código.
Mudança proposta: material/direção factíveis, construção por partes, revisão da
peça completa e aceite calibrado; sem impor 100 quadros ou quantidade de cenas.
Nenhum código de produção, chamada paga, render novo, migração ou serviço
iniciado nesta análise. Estudo e 41 fichas:
`docs/evals/analise-41-referencias-motion-2026-11-12.md`.
Relatos anteriores de avanço técnico não representam aceite visual do titular.

**Prévia audiovisual completa entregue — 12/11/2026.** Titular autorizou gerar
a peça. MP4 local de 11,2 s, 720 × 1280 a 30 fps, H.264/AAC, 336 quadros,
voz + servir conforme plano, sem outra chamada paga. Código exato conferido no
checkpoint/owner/RLS e materiais restaurados pelo serviço existente; execução
Temporal de tentativa única com renderer isolado, sem alterar código de produção.
Quadros decodificados mostram xícara → U de PAUSA, campo móvel e convite; avaliação
de fluidez/integração tipográfica/escuta ainda cabe à reprodução da peça.
Prévia supervisionada privada, sem fabricar aprovação artística, publicação ou
conclusão nativa: checkpoint nativo render autoriza storyboard e produção posterior
exige revisão paga; pedido nativo permanece no checkpoint, sem alterar decisões.
Workflow da prévia COMPLETED, MP4/35 evidências privados em render-preview-v1.
Saída validada/decodificada, -15,3 LUFS e pico amostral -3,6 dBFS; métricas não
substituem escuta. Global disabled/execução false, cinco serviços exited, nenhum
banco migrado; custo pago acumulado estimado continua US$ 0,774901. CI global
mantém os gates anteriores. Resultado e limites:
`docs/evals/previa-motion-completa-2026-11-12.md`.
Registros anteriores de ausência de render descrevem o estado antes desta autorização.

**Código do plano aprovado gerado e revisado — 12/11/2026.** Titular autorizou
avançar para implementação com parada antes do render. Aprovação exata persistida;
uma chamada de código pelo fluxo real, composição recebida e awaiting_render.
Metadados idênticos ao plano, um vídeo contínuo e áudio original + servir previsto.
Sintaxe/bundle sem execução passaram; fórmulas da trajetória em arco evitam a
janela do vídeo em 10.001 amostras por passagem. Sem prévia/escuta ou certificação
artística. Guarda privada inicial confundiu ordem de chaves JSON; falhou antes
de claim/contagem/reserva/submissão. Corrigida e criada continuação interna
explícita, auditada/idempotente, somente sem efeito de código/upload iniciado;
aprovação e falha preservadas. Sem retry pago, endpoint ou migração novos.
1.657 testes motion (dois skipped), casos PostgreSQL de checkpoints e 40 unitários
do orquestrador passaram; checkpoints 100% linhas/branches. Ruff/formato/Mypy e
diff --check aprovados; CI global ainda pendente nos gates anteriores.
Código US$ 0,332548 estimados, reserva US$ 1,25 uncertain mantida; três chamadas
da sequência somam US$ 0,774901 estimados, sem fatura conciliada. Workflow
COMPLETED, pedido running/token liberado, checkpoint de render sem decisão.
Nenhum render/quadro/asset de IA, migração ou serviço iniciado; global disabled,
cinco serviços restritos exited. Escopo, revisão, custos e pendências:
`docs/evals/implementacao-motion-plano-aprovado-2026-11-12.md`.
Registros de awaiting_plan/código não autorizado abaixo são históricos.

**Correção validada em novo plano — 12/11/2026.** Após autorização de uma
chamada substituta até US$ 1,25, encerrada a rodada anterior pelo checkpoint com
feedback e histórico preservados. Correções: piso v2 exige desenvolvimento visual
no pedido simples; entrada separa escuta por fase; guard permite ação dentro do
vídeo-fonte com layout em hold, sem liberar outro vídeo/grafismo parado. Entrada
final v9 (v8 superada antes de envio), ASR novo e fluxo real até awaiting_plan.
Novo plano transforma xícara no U de PAUSA e apoio em campo de leitura; propõe
servir em 1.900–3.680 ms ligado ao vídeo parado e omite contato sem ação observada.
Validadores e compilação de soundtrack em memória passaram; raw e plano iguais.
Pontos anteriores tratados na proposta escrita; metamorfose, proteção da fonte,
leitura e som/mistura ainda exigem execução/prévia/escuta. Sem aprovação artística
ou decisão de implementar. Estimativa desta chamada US$ 0,228198, reserva US$ 1,25
uncertain mantida; duas chamadas somam US$ 0,442353 estimados, sem fatura.
1.657 testes motion (dois skipped), 24 integrações e 100 dirigidos passaram;
qualidade/catálogo com 100% de linhas/branches, lint/formato/Mypy aprovados.
CI global continua pendente. Nenhuma nova migração, código, asset de IA, render
ou serviço iniciado; global disabled e cinco serviços restritos exited. Resultado:
`docs/evals/plano-audiovisual-corrigido-2026-11-12.md`.
Os estados anteriores de entrada v8/espera de orçamento/ausência de plano são históricos.

**Correção da preparação do planejamento — 12/11/2026.** Pedido posterior
mandou encontrar o problema e ajustar. Identificadas lacunas verificáveis:
desenvolvimento visual aparecia em orientações condicionais, mas não como critério
próprio do piso; escuta humana e pendência da mistura não eram sintetizadas por
fase na entrada. Perfil novo motion-production-quality-v2 exige oitavo critério
visual_development no pedido simples e explicita a escolha composicional;
planning_input agrupa disponibilidade/relato humano/hash/revisão futura de som,
sem exigir efeitos ou apagar limitações. Snapshots v1 preservados na recaptura;
plano/checkpoint original intactos, payload anterior reproduzido byte a byte.
Pacote v8 montado com ASR local novo e conferido, sem nova geração paga/admissão/
render. 1.652 testes motion (dois skipped), 23 integrações e 26 dirigidos passaram;
100% linhas/branches em motion_quality, lint/formato e Mypy 334 + oito scripts
aprovados. CI global segue pendente. A correção da entrada não demonstra melhora
artística; novo plano precisa ser gerado/revisado. Chamada anterior consumida;
nova proposta de uma chamada até US$ 1,25 ainda não autorizada. Detalhes:
`docs/design/motion-correcao-planejamento-2026-11-12.md`.
Estados de sete critérios e preparação v7 abaixo descrevem o histórico.

**Plano audiovisual recebido e revisado — 12/11/2026.** Titular autorizou
explicitamente somente a migração 0118 e uma chamada de plano até US$ 1,25.
Backup privado verificado; dev 0117 → 0118, sem tabela nova ou dados removidos.
Admissão/owner/RLS → Temporal/ASR novo → contagem/reserva → plano → checkpoint
real awaiting_plan. Payload exato v7, 15 quadros da fonte/zero de peça anterior;
nenhum código, asset de IA, render ou aprovação automática. Workflow completado;
pedido running com execution_token liberado, aguardando decisão. Retorno/entrada/
raw e custo preservados. Estimativa US$ 0,214155 (39.898 tokens entrada/11.441 saída),
sem fatura; reserva US$ 1,25 uncertain mantida no ledger. Direção propõe três
momentos tipográficos com vídeo contínuo e omite ambos os efeitos. Validadores
passaram; revisão do assistente recomenda desenvolver composição além de títulos/
barras/reposicionamento e melhorar motivo da omissão de servir café; omissão de
contato tem base na fonte. Não é reprovação de vídeo ainda não renderizado nem
exigência de usar som. Plano original/checkpoint não foram alterados ou aprovados.
Configuração paga só no processo já encerrado; global disabled, cinco serviços
restritos exited. CI integral permanece pendente. Resultado, revisão e limites:
`docs/evals/plano-audiovisual-motion-2026-11-12.md`.
Os estados anteriores de espera de autorização/ausência de plano são históricos.

**Plano solicitado, execução preparada — 12/11/2026.** Titular autorizou
somente gerar/revisar plano, até US$ 1,25 da proposta nova; código/render seguem
sem autorização. Corrigida formatação dos 13 arquivos com AST idêntico, sem
alterar lógica. Lint, formato de 905 arquivos e Mypy (334 módulos app + oito
scripts) passaram; 1.646 testes motion (dois skipped) e 23 integrações de motion/
checkpoints passaram. CI integral continua pendente: cobertura Node abaixo de
100%; backend ampliado interrompido após 108 aprovados/sete falhas de geocodificação,
incluindo policy_id ausente no _test. Sem corrigir schema implicitamente.
Execução privada preparada com admissão/RLS, ledger/Temporal e limite de uma
chamada, payload v7 exato, sem aprovação automática ou renderer. Dev confirmado
0117: aplicar 0118 para persistir checkpoint depende da autorização específica
solicitada, conforme restrição original contra migração implícita. Credenciais
presentes/Temporal saudável; backup compatível preparado, ainda não executado.
Sem migração, admissão ou chamada paga nesta rodada; plano ainda não existe.
Registro: `docs/evals/plano-motion-solicitado-2026-11-12.md`.
Os estados anteriores de 13 arquivos pendentes de formato foram superados.

**ASR real, escuta e novo teto — 12/11/2026.** Fechada preparação sonora
para planejar: ASR local novo pelo mesmo serviço do runtime, medições limitadas
no loader, escuta do titular vinculada aos hashes da fonte/candidatos no builder.
Transcrição não revisada; uma palavra abaixo do limiar não pode virar âncora sem
revisão. Eventos/mistura ainda dependem do plano e prévia autorizada. Entrada v7
com 15 quadros da fonte/zero de peça anterior foi conferida, sem admissão, modelo
pago ou render. Teto novo proposto US$ 2,50 para plano/código, código só após
aprovação específica e parada em awaiting_render. Não autorizado/aplicado.
1.646 testes motion/exportadores (dois skipped), quatro integrações, Ruff/Mypy 334
aprovados; 100% em análise/catálogo. CI global ainda bloqueado por 13 arquivos
preexistentes de formato. Dev 0117 preservado; sem migração ou serviços iniciados.
Próximo: revisão da entrada/orçamento, fechamento de CI/configuração; qualquer
migração dev exige autorização separada. Detalhes:
`docs/design/motion-asr-avaliacao-sonora-orcamento-2026-11-12.md`.
Registros anteriores descrevem preparações superadas; qualidade artística aberta.

**Correção do piso de qualidade — 12/11/2026.** Titular rejeitou usar a última
peça como contexto obrigatório para gerar outra. Piso agora pertence ao produto;
ensaios antigos ficam na avaliação separada. Novo perfil propagado/validado no
plano, com builder recusando base/composição/material recuperado de render antigo.
Pacote v5 real sem histórico e sem injeção de ASR: 15 quadros da fonte, zero da
base; falta de ASR bloqueia chamada paga. 1.605 testes motion/exportadores (dois
skipped), 67 dirigidos e quatro integrações passaram; grupos sobrepostos. Novo
módulo com 100% de linhas/branches, Mypy 333/Ruff aprovados; CI global continua
pendente por 14 arquivos preexistentes de formato. Sem gasto/render/migração.
Próximo: fechar ASR e escuta/seleção, CI e entrada efetiva; orçamento novo; plano
→ revisão específica → código → parar antes do render. Sem qualidade artística
ou v0 completa declarada. Detalhes:
`docs/design/motion-piso-qualidade-independente-2026-11-12.md`.

**Continuação de qualidade motion — 12/11/2026.** Nova entrada acompanhada pode
propor direção audiovisual a partir da mensagem simples/contexto, sem direção
herdada fixa. Piso funcional, seleção sonora local por ação e repertório v4 sem
os oito prints integrados aos contratos/builder. Mantidos snapshots, exemplos,
executor, mixer e fidelidade exata após aprovação do plano. Pacote real privado:
`.local/evals/motion-supervised-20261112/preparation-v4/`; zero chamadas pagas,
pedidos admitidos ou renders. A interpretação da mensagem e qualidade da próxima
peça ainda não foram observadas. 1.584 testes motion/exportadores, 47 dirigidos
finais e 55 integrações passaram; teste Temporal passou após usar porta da CI já
ativa. Sem somar grupos sobrepostos. Mypy/Ruff aprovados, 100% de linhas/branches
em dois módulos novos; CI integral segue bloqueado pela formatação preexistente.
Dev 0117/runtime disabled e cinco serviços parados; `_test` 0118 sem nova migração.
Próximo: revisar pacote/orçamento/configuração, gerar plano autorizado, revisar por
cena e aprovar especificamente antes do código; parar em `awaiting_render`.
Detalhes e limitações: `docs/design/motion-planejamento-audiovisual-revisavel-2026-11-12.md`.
Registros anteriores abaixo são históricos; evolução artística permanece aberta.

**Revisão da seleção visual — 12/11/2026.** Titular examinou os prints e
questionou sua contribuição. Decidido retirar os oito da próxima rodada, sem
apagar histórico, demais evidências, skills ou exemplos úteis. Não contabilizar
anexos recebidos como melhoria criativa. Documentados arquivos/instantes,
cinco enviados versus três somente preparados, critérios de curadoria e uso
parcial dos repositórios de origem em
`docs/evals/ensaio-acompanhado-motion-2026-11-12.md`. Só documentação nesta fatia;
seleção revisada no produto e qualidade resultante ainda não implementadas/validadas.

**Primeira fronteira do ensaio acompanhado — 12/11/2026.** Pacote montado pelo
produto, não enviado, revelou direção herdada restritiva e nenhuma seleção de
SFX. Titular corrigiu entrada técnica e uso da referência como molde; escolheu
biblioteca pública com licença comercial verificada. Entrada revisada separa
mensagem do cliente, controles do produto e piso funcional. Inventário confirma
orientações sonoras existentes no estudo Maestros/skills, sem integração de
obtenção/seleção. Plano/código ainda não gerados; não se concluiu `awaiting_render`.
Registro, provas e pendências: `docs/evals/ensaio-acompanhado-motion-2026-11-12.md`.
Sem alteração de produção/banco; cinco serviços parados e orçamento antigo intacto.

**Fases 1–3 da preparação acompanhada — 12/11/2026.** Implementação mantém
capacidades anteriores e adiciona origem das decisões, evidência conferida no
builder, repertório opcional v3 e pausas duráveis após plano/código. API do titular
expõe payload/retorno armazenados e manifesto, com aprovação vinculada ao hash.
Retomada pelo Temporal existente; nenhuma chamada ao renderer antes de aprovar
`render`, que libera só storyboard. 65 testes dirigidos passaram com cobertura
100% nos quatro módulos novos; 1.533 motion/exportadores (dois skipped), seis
integrações de regressão e Mypy 330 módulos aprovados. CI global continua pendente
na formatação preexistente. Migração 0118 somente no `_test` autorizado; dev e
serviços preservados. Sem chamada paga ou peça nova. Escopo técnico e qualidade
ainda não validada: `docs/design/motion-preparacao-e-revisao-fases-1-3-2026-11-12.md`.
Chat/trace OpenCode levantado pelo titular: proposta separada, sem integração
executada, em `docs/design/opencode-e-inspecao-do-produto-2026-11-12.md`.

**Fluxo efetivamente executado — 12/11/2026.** Auditoria ampliada a pedido do
titular: brief manual/API direta, chamadas e retornos reais, normalização pelo
servidor e caminho de avaliação MP4. Diferenciar do percurso completo de cliente
e da revisão/correção que não rodou. Evidências extraídas localmente; sem nova
chamada, render ou mudança de runtime. Ver
`docs/evals/auditoria-fluxo-motion-2026-11-12.md`.

**Prioridade: auditoria por etapa — 12/11/2026.** Conferência inicial compara
pedido/snapshot/payload da rodada anterior e reproduz entrada com builder real
offline. Mantidos skill/kit/repertório/base; limitações de amostragem, escuta,
seleção e direção registradas. Pausa antes da implementação ainda precisa ser
habilitada para nova execução acompanhada. Sem geração/gasto nesta entrega.
`docs/evals/auditoria-fluxo-motion-2026-11-12.md`.

**Feedback sobre direção — 12/11/2026.** Não universalizar exemplos nem congelar
soluções artísticas de uma rodada. Estudo temporal de ação completa em cerca de
4–5 s e aplicação numa janela da peça são propostas; movimento/escuta e conexão
com o conjunto ainda precisam de avaliação. Sem nova etapa, código, geração ou
gasto. Atualização, evidência das restrições na direção e pendências em
`docs/evals/revisao-acabamento-cinematografico-motion-2026-11-11.md`.

**Feedback favorável e próximo acabamento — 11/11/2026.** Titular gostou do MP4
atual e o considera melhor que o último, mas distante do impacto da referência.
Preservar esta versão/hash como referência de continuidade; sem aceite final nem
aprovação fictícia no banco. Auditoria confirma 18 elementos, zero eventos sonoros
extras e referências Maestros de trajetória (80/84/88 s), não os trechos de
luz/câmera. Próximo foco proposto: preparação/revelação em ambiente coerente; A/B
sonoro separado. Distinguir incremento localizado de conclusão global do contrato
(o seletor atual exige ganho nas quatro dimensões); manter não regressão.
Revisão recorrente por rodada definida, ainda não automatizada. Somente análise
e documentação, sem nova geração/gasto/runtime. Evidências e prioridades:
`docs/evals/revisao-acabamento-cinematografico-motion-2026-11-11.md`.

**R5 — MP4 de avaliação autorizado e entregue, 11/11/2026.** Titular pediu o vídeo
após ver os quadros. Mesmo plano/código/material/áudio, renderizados no executor e
Temporal existentes: 720 × 1280, 30 fps, 11,2 s, áudio original; decodificação
verificada. Sem chamada paga adicional, edição do código gerado ou publicação.
Pedido original continua falho; não se fabricou aprovação persistida nem se
relaxou a recaptura. MP4 local para avaliação: `.local/evals/motion-recovery-run-20261111/nova-peca-avaliacao.mp4`.
Cinco serviços parados; qualidade criativa, persistência e CI ainda pendentes.
Evidências: `docs/evals/execucao-recuperacao-motion-2026-11-11.md`.

**R5 — geração recebida, entrega bloqueada, 11/11/2026.** Plano e implementação
concluídos; persistência do storyboard falhou por colisão de identidades dos quadros
globais v3. Bug corrigido, teste adicionado; migração 0117 permite dois eventos de
recaptura, sem novas tabelas. Recuperação por Temporal, sem provider, parou por
diferença de pixels. Diagnóstico guardou 20 quadros: 19 hashes iguais, diferença
em 2.800 ms ainda não localizada. Pedido `failed`, sem storyboard aprovado ou MP4.
US$ 2,50 reservados; estimativa US$ 0,568106, sem fatura. Não repetir chamadas nem
relaxar o controle. Prévia e evidências em
`docs/evals/execucao-recuperacao-motion-2026-11-11.md`. Qualidade visual não aprovada.

**Recuperação R5 — nova rodada autorizada, 11/11/2026.** Titular autorizou gerar
com teto novo da proposta US$ 6,25, sem imagens novas, somente áudio original,
até uma correção delimitada e aprovação do storyboard antes do MP4. Admissão
real e executor sintético conferidos; 77 testes dirigidos passaram. CI integral
permanece pendente; rodada operacional não equivale a merge/aceite visual.
Execução/evidências: `docs/evals/execucao-recuperacao-motion-2026-11-11.md`.

**Recuperação R1–R5 — entrega técnica, 11/11/2026.** Pedido posterior autorizou
implementar as cinco fatias. R1–R4: base histórica vinculada ao contexto real,
imagem original reutilizável, matriz de preservação, direção revista, cobertura
temporal v3 e seleção comparativa que bloqueia regressão/empate/incerteza.
R5: pacote real preparado e verificado; execução pendente, sem qualidade visual
nova validada. Etapas 1–6 preservadas; etapa 7 aberta. Nenhuma chamada paga,
asset novo, render, tabela ou serviço criado. Reserva nova proposta US$ 6,25,
não autorizada; storyboard continua anterior ao MP4. 1.114 testes passaram,
dois skipped; Mypy em 325 módulos. CI parou na formatação preexistente; cobertura
integral e integração `_test` pendentes. Evidências e limites:
`docs/evals/recuperacao-motion-r1-r5-2026-11-11.md`.
Os registros abaixo descrevem estados anteriores, superados por esta entrega.

**Recuperação da etapa 7 planejada — 11/11/2026.** Cinco fatias R1–R5 preservam
implementações das etapas 1–6 e o aprendizado das referências. Entregas e aceites
separam contexto, direção, cobertura, seleção e resultado visual. Base principal:
“Nova — quatro melhorias”; versão desenhada como referência complementar de ação.
Nenhuma fatia iniciada nesta entrega de planejamento. Sem nova peça, chamada,
banco ou serviço; execução paga/render depende de autorização nova. Plano:
`docs/design/plano-recuperacao-e-evolucao-motion-2026-11-11.md`.

**Restrição do titular para recuperação — 11/11/2026.** Manter capacidades
implementadas a partir das referências/YouTube e evoluir a qualidade com comparação
evidenciada. Não restaurar arquitetura antiga nem desativar as etapas 1–6. Bases
indicadas são referências de resultado. Aplicação efetiva da rubrica comparativa
como condição de conclusão/seleção permanece pendente; requisitos registrados nas
Regras transversais do contrato. Sem código, geração, render, banco ou serviços.

**Etapa 7 — causa da regressão, 11/11/2026.** As referências corretas são as duas
peças da comparação “Anterior / Nova — quatro melhorias” de 11/11, indicadas pelo
titular. Sete elementos e suas funções de ligação saíram na direção da etapa 1;
nenhum vínculo com a composição anterior entrou no payload efetivo. Controles
de integridade mantiveram o plano reduzido. A espera de 2,52 s já era de 2,56 s
na base; a perda é de ações e continuidade, incluindo xícara removida no retorno.
Evidências locais, contraprova com validadores e pendências registradas em
`docs/evals/diagnostico-regressao-motion-2026-11-11.md`. Sem código de produção,
geração, render, banco ou serviços alterados. Etapa 7 permanece aberta.

**Etapa 7 — reprovação visual do titular, 11/11/2026.** Storyboard não atendeu:
vídeo, frase e xícara percebidos como blocos separados. Inspeção do plano confirma
longa espera e ações pequenas, apesar das descrições de coordenação. Revisar
concepção antes de outra execução; não tentar resolver com MP4 ou crítica paga.
Sem gasto adicional, mudança de código ou estado terminal na API. Etapa 7 aberta.
Evidências: `docs/evals/comparacao-qualidade-motion-etapa7-2026-11-11.md`.

**Etapa 7 de qualidade motion — storyboard entregue, 11/11/2026.** Plano, uma
imagem e implementação executados pelo produto; entradas conferidas por hash e
ASR novo igual à proposta. Fonte/kit/voz preservados; áudio somente original.
Galeria real com 18 quadros aguarda decisão do titular antes do MP4. Reserva
US$ 3,00 do teto novo US$ 6,75; estimativa US$ 0,372465 sem fatura confirmada.
Sombra difusa e quadro vazio no retorno registrados; fluidez/áudio não avaliados.
Worker dedicado encerrado; sem crítica paga, correção ou aceite criativo. Etapa 7
aberta; nenhuma etapa 8 definida. Evidências:
`docs/evals/comparacao-qualidade-motion-etapa7-2026-11-11.md`.

**Etapa 7 de qualidade motion — preparação, 11/11/2026.** Pacote da comparação
montado pelo produto, com igualdade de fonte/kit/voz/perfil e diferenças declaradas.
Proposta de uma xícara conceitual fotográfica; titular escolheu somente áudio
original. Até cinco chamadas de modelo, uma imagem e uma correção condicional:
reserva nova proposta US$ 6,75, sem autorização ou execução. Executor reconstruído;
qualificação e produção pendentes. 24 testes dirigidos, Ruff e Mypy aprovados;
sem prova visual. Etapa 7 aberta; nenhuma etapa 8 definida. Detalhes:
`docs/design/motion-etapa-7-preparacao-comparacao-2026-11-11.md`.

**Etapa 6 de qualidade motion — 11/11/2026.** Crítica e payload reais carregam
escopo por cena/elementos, evidência, intervalo e margens. Correção sem replanejar;
render completo registra hashes de todos os quadros antes do H.264. Regressões
externas, ambiente diferente e evidência incompleta rejeitam a candidata. Plano,
assets e áudio preservados; operação e teto existentes. Fixture local aprovada,
sem comprovação do MP4 final ou qualidade artística. Imagem, CI e comparação real
pendentes; etapa 7 requer OK. Sem gastos, serviços iniciados ou banco. Detalhes:
`docs/design/motion-etapa-6-correcao-delimitada-2026-11-11.md`.

**Etapa 5 de qualidade motion — 11/11/2026.** Complementos selecionados e
atestados pelo titular usam acervo e vínculos existentes; ramo original protegido,
fades, ducking exclusivo da música e medição implementados. Testes sintéticos
locais aprovados; sem peça, escuta ou A/B. Falta material adequado autorizado e
reconstruir/fixar a imagem do executor antes do uso. Etapas 6–7 pendentes; etapa 6
requer OK. Detalhes: `docs/design/motion-etapa-5-som-e-voz-2026-11-11.md`.

**Etapa 4 de qualidade motion — 11/11/2026.** Skill HTML v13 acrescenta exemplo
opcional de preparação, objeto apoiado, repouso e retorno coordenado de gravação,
fundo e texto usando movement-v3. Snapshots anteriores, executor e bancos não foram
alterados. Montador real exportou entrada de plano v4 com fonte, kit, áudio,
transcrição e referências preservados, sem chamada ou render. 14 testes Node,
133 Python dirigidos, Ruff e Mypy do loader aprovados; sem CI integral. Isso não
comprova acabamento visual ou sincronia. Etapas 5–7 pendentes; etapa 5 requer OK.
Detalhes: `docs/design/motion-etapa-4-espaco-coreografia-2026-11-11.md`.

**Etapa 3 de qualidade motion — 11/11/2026.** Novas capturas com direção usam
v4: plano validado → materiais resolvidos → previews verificados → implementação;
v1–v3 históricas preservadas. Imagens ausentes interrompem a implementação;
pedido de revisão de plano preserva recibo e não gera nova chamada automática.
Exportação e adapters locais comprovam o vínculo, sem gasto ou render. Não há
prova visual nem retomada parcial automática; imagem anterior não foi encontrada
em `.local`. Etapas 4–7 pendentes; etapa 4 requer OK. Verificações e limites:
`docs/design/motion-etapa-3-assets-antes-do-codigo-2026-11-11.md`.

**Etapa 2 de qualidade motion — 11/11/2026.** Política temporal v2 distribui
janelas entre passagens e ação, respeitando o teto de 20 quadros e declarando
omissões; v1 histórica preservada. Storyboard apresenta sequências estáticas e
continua sendo portão após código, antes do MP4. Ao retomar, confere materiais,
direção e runtimes vinculados; quadros não comprovam movimento contínuo nem som.
Caso Café Pausa reproduz seleção de duas passagens e entrada da xícara, com
46 de 49 eventos omitidos; sem nova captura ou crítica. Testes dirigidos, Ruff
e Mypy aprovados; sem CI integral. Sem gasto, banco, geração ou render. Qualidade
visual e etapas 3–7 pendentes; etapa 3 requer OK do titular. Evidências e limites:
`docs/design/motion-etapa-2-revisao-representativa-2026-11-11.md`.

**Etapa 1 da evolução de qualidade motion — 11/11/2026.** Entrega técnica de
direção verificável e repertório aplicado: direção e brief revisados para Café
Pausa, matriz de problemas com instantes, regiões relevantes identificadas por
revisão humana e fichas selecionadas; sem impor borda ou efeito por palavra.
Novas capturas usam skill v12; o repertório opcional `business-reel-v2` incorpora
amostras e fichas rastreáveis, preservando versões históricas. Exportação offline
pelo montador do produto em `.local/exports/motion-qualidade-etapa1-final-20261111/`;
fonte, kit, áudio e transcrição iguais à base; seis quadros da fonte e cinco
imagens de referência. Restaurados, por autorização do titular, os contratos
removidos no commit posterior `4adb596` para manter o fluxo existente. Não há
peça nova nem qualidade visual aprovada.
Testes dirigidos: 96 Python, 62 de skill/contexto e 7 Node (grupos sobrepostos,
sem soma); Ruff e Mypy em quatro módulos aprovados. CI integral não executado. Verificação dos cinco contêineres
bloqueada pelo socket; não se afirma seu estado atual. Sem gastos, geração de
assets ou renderização. Etapas 2–7 permanecem pendentes, e a próxima depende de
OK do titular. Evidências e proposta:
`docs/design/motion-etapa-1-direcao-verificavel-2026-11-11.md`.

**Próximo trabalho planejado — 11/11/2026.** Contrato de sete etapas consolida
os seis gaps e o inventário de capacidades do vídeo Maestros. Começar por direção
verificável/repertório e seguir aceites técnicos separados da validação criativa.
Comparação exige orçamento novo e entrada preparada pelo produto; não reutilizar
tetos anteriores. Recorte/tracking/OCR/stock/3D e EDL não bloqueiam esta entrega.
Planejamento apenas; nenhuma etapa implementada nesta alteração. Referência:
`docs/design/contrato-evolucao-qualidade-motion-2026-11-11.md`.

**Reanálise de qualidade após feedback do titular — 11/11/2026.** A comparação
executou corretamente, mas a moldura foi considerada estranha e a xícara sem a
expressividade esperada. Seis frentes detalhadas: direção por sentido da fala,
integração da gravação, fundo, presença do objeto, som e revisão por cena.
Auditoria confirmou direção excessivamente prescritiva em moldura, código antes
dos pixels da imagem, storyboard desligado na rodada e seleção de três eventos
de fala concentrados no mesmo momento (46 de 49 eventos omitidos). A referência
Maestros foi reexaminada com transcrição e quatro sequências adicionais; não foi
incorporada automaticamente à entrada da peça. Prioridade proposta: direção e
repertório aplicáveis, cobertura da revisão, construção com asset visto, som e
refinamento delimitado; percepção/3D somente conforme necessidade. Nenhuma nova
implementação, geração, gasto, migração ou CI nesta análise. Plano e evidências:
`docs/design/motion-qualidade-direcao-e-gaps-2026-11-11.md`.


**Comparação concluída após reposição de créditos — 11/11/2026.** Novo pedido
pelo fluxo API/Temporal gerou plano e código completos, uma xícara conceitual
fotográfica, MP4 de 11,2 s (720×1280/30 fps) e crítica adequada. Mesma fonte/voz/kit
e 12 imagens, sem refações. Moldura, alternância e mudança dos planos de fundo
observadas; transições próximas de 4 s e 8,8 s ainda merecem refinamento. Crítica
limitada a amostras, sem escuta; nenhum aceite humano ou publicação.
Estimativa desta tentativa US$ 0,737973; reservas US$ 2,75 no teto US$ 3.
Pedido/reservas anteriores preservados separadamente. Worker exclusivo encerrado;
cinco serviços seguem parados. MP4 e comparação em
`.local/evals/motion-staged-retry-20261111/`. Relatório:
`docs/evals/comparacao-construcao-em-etapas-2026-11-11.md`.


**Prova real v3: plano completo; implementação bloqueada por créditos da API.**
Nova rodada de US$ 3 executada pela API/Temporal no banco de desenvolvimento
existente. Planejamento validado e preservado (3 cenas, 36 beats); segunda chamada
recusada pelo provedor com `insufficient_quota/credit_balance_exhausted`.
Não foi outra saída truncada. Nenhuma imagem, crítica ou nova peça produzida;
conclusão da implementação e acabamento continuam pendentes. Estimativa conhecida
US$ 0,22592, reservas US$ 1,50 mantidas; rejeição sem usage/custo conhecido.
Sem repetição ou reutilização de orçamento. Worker exclusivo encerrado; cinco
serviços seguem parados. Entrada exata da implementação exportada e verificada
por hash, sem chamadas adicionais. Evidências e próximo desbloqueio:
`docs/evals/comparacao-construcao-em-etapas-2026-11-11.md`.


## Atualização — 11/11/2026

**Correção estrutural da geração implementada, sem comparação paga.** Contrato
v3 para novas direções fornecidas: planejamento sem código e implementação sem
repetir plano, com validação intermediária e vínculo por hash. Dois recibos/reservas
duráveis, sem retry automático, preservando contratos anteriores. Corrigida ordem
do schema e exportação das duas etapas. Pacote offline conserva as 12 imagens da
última tentativa. Causa raiz do limite do provedor ainda não comprovada; novo MP4
e qualidade pendentes. Dev conferido em 0116, sem migração necessária. As melhorias
do vídeo Maestros ficam para depois da comparação, conforme orientação do titular.
Detalhes: `docs/design/motion-construcao-em-etapas-2026-11-11.md`.
473 testes dirigidos passaram, cobertura integral nos seis módulos medidos e
Mypy/Ruff OK. 23 testes de integração passaram; execução mais ampla interrompida
por Temporal local indisponível. Não houve CI integral ou chamada real ao modelo.

**Estudo da referência WuzMxEKJHkQ entregue.** Download 1080p, legendas automáticas,
114 quadros distribuídos e seis detalhes analisados. Mapeadas ferramentas,
composição, profundidade, alinhamento, percepção espacial, som e revisão ao fluxo
atual. Um pedido humano não demonstra uma única completion. Recomendada recuperação
por artefato antes de outra comparação; preservar as quatro melhorias visuais e
qualificá-las no resultado. Estudo não implementa recorte, tracking, 3D ou cortes
longos. Sem código alterado, chamadas pagas, render ou CI; validação documental.
Sem nova tentativa autorizada. Relatório:
`docs/evals/analise-video-maestros-WuzMxEKJHkQ-2026-11-11.md`.

**Análise das interrupções concluída, sem chamada paga adicional.** Retornos
reproduzidos offline no parser: corte em scene_init vem marcado pela API; limites
locais de bytes, orçamento e falta de anexos não explicam a falha registrada.
Identificados saída indivisível, ordenação alfabética do schema colocando código
após plano e reasoning=high fixo. A causa raiz do limite reportado continua sem
comprovação: uso abaixo do teto e dos limites públicos do modelo. Compactação de
20,87% não era prova de conclusão. Próximos passos documentados, não implementados.
Relatório: `docs/evals/diagnostico-interrupcao-motion-2026-11-11.md`.

**Tentativa com contrato compacto concluída sem MP4.** O provedor voltou a retornar
MOTION_AI_OUTPUT_LIMIT, com JSON cortado em scene_init, após 562,74 s. Contrato v2
foi efetivamente enviado, mas a compactação não resolveu o bloqueio. Contagem:
35.340 tokens de entrada, 27.924 de saída (18.425 de reasoning); teto solicitado
e retornado 54.000. A causa do limite permanece indeterminada. Três tentativas
encerradas: estimativa acumulada US$ 0,998378, reservas US$ 2,80 mantidas. Nenhuma
imagem, crítica ou nova peça gerada. Sem novas tentativas autorizadas. Worker
exclusivo encerrado e cinco serviços seguem parados. Próxima geração exige uma
solução verificada para a saída incompleta; não repetir apenas ajustes de prompt.
Evidências: `docs/evals/comparacao-quatro-melhorias-2026-11-10.md`.

## Estado vigente — 10/11/2026

**Histórico — contrato compacto v2 preparado em 10/11/2026.**
Representação dos beats reduzida em 20,87% no plano completo da resposta anterior,
com igualdade exata dos 63 movimentos após expansão. Contratos antigos preservados;
mesmas validações e formato completo na persistência/crítica/render. 234 testes
dirigidos aprovados; cobertura integral dos dois módulos medidos, Ruff/Mypy OK.
Nenhuma nova chamada paga ou peça gerada. Entrevista de autorização pendente para
uma tentativa adicional: reservas acumuladas máximas US$ 3,95 no teto US$ 4.
A causa da interrupção anterior permanece indeterminada; redução não garante
sucesso. Detalhes: `docs/design/motion-contrato-compacto-2026-11-10.md`.

**Histórico — duas tentativas da comparação bloqueadas; sem novo MP4.** Duas
composições tentadas, incluindo a recuperação explicitamente autorizada dentro
do teto acumulado US$ 4. Ambas retornaram MOTION_AI_OUTPUT_LIMIT e JSON cortado
em scene_init. Recuperação: 364,07 s, 35.075 tokens de entrada e 19.856 de saída
(8.804 de reasoning), apesar de max_output_tokens=64.000 solicitado e retornado.
Não atribuir causa definitiva ao modelo nem confundir com falha de renderização.
Estimativa acumulada US$ 0,630788; reservas US$ 2,15 mantidas. Nenhuma imagem,
crítica ou MP4 produzido; não há terceira tentativa autorizada. ASR local funcionou
nas duas operações e registrou 30 palavras com custo zero. Qualidade visual ainda
não qualificada. Cinco serviços continuam parados; worker exclusivo encerrado.
Antes de outro gasto, investigar a saída interrompida e reduzir a repetição entre
plano e código sem perder as quatro melhorias. Detalhes e evidências:
`docs/evals/comparacao-quatro-melhorias-2026-11-10.md`.

**Histórico da entrega — etapa visual 4 implementada antes da comparação.**
Backend local faster-whisper baseado na abordagem do Clipador Viral dos Maestros
da IA: tempos por palavra, confiança e origem não revisada, com possibilidade de
entrada humana revisada. Execução no fluxo Temporal existente, claim durável e
reutilização em correção/storyboard. Skill v11, validação de fonte/onsets/focos e
amostragem dos eventos ligados. Mantidas moldura, fundo, objeto e alternância.
Configuração desabilitada por padrão; dependências/modelo ainda não instalados no
worker e nenhuma inferência real executada. Sem chamadas pagas, asset novo, MP4
ou Docker. 346 testes Python e 11 Node aprovados; cobertura integral nos sete
módulos medidos. Precisão/qualidade dependem da comparação.
Aguardar OK do titular para iniciar essa comparação, com escopo/orçamento próprios.
Vídeos brutos longos e cortes continuam futuros. Detalhes em
`docs/design/motion-fala-alinhada-2026-11-10.md`.

**Histórico — etapa visual 3: objeto realista em camadas.**
Novas capturas usam skill v10: seleção de imagem autorizada ou conceitual gerada,
material/luz coerentes e helper executável de recorte com sombra coordenada.
Moldura, fundo narrativo e alternância preservados; snapshots v1–v9 intactos.
Direção Café Pausa e especificação de uma única imagem preparadas; substituem
preenchimento do desenho por chegada/assentamento. Dependem de asset e capacidade
configurada; nenhuma imagem ou novo MP4 foi gerado. 131 testes Python e 11 Node
passaram, cobertura integral no loader medido e Ruff/Mypy aprovados. Sem chamadas
pagas ou Docker. Etapa 4 (fala alinhada) aguarda OK; qualificação visual pendente.
Detalhes: `docs/design/motion-objeto-realista-2026-11-10.md`.

**Histórico — etapa visual 2: fundo narrativo.**
Novas capturas usam skill v9, preservando moldura/escala da etapa 1 e movement-v3.
Incluído exemplo executável de base opaca, campo de cor e detalhe com movimentos
coordenados, repouso e contraste planejado. Café Pausa recebe três elementos de
fundo; os 16 elementos anteriores permanecem intactos. Capturas antigas conservam
suas skills. 97 testes Python e 9 Node passaram; cobertura integral no loader
medido, Ruff/Mypy aprovados. Pacote offline montado/verificado, sem geração paga,
asset novo ou MP4 nesta fatia. Acabamento visual permanece por qualificar.
Etapa 3 (objeto realista) aguarda OK. Detalhes em
`docs/design/motion-fundo-narrativo-2026-11-10.md`.

**Histórico — etapa visual 1: tratamento da gravação.**
Novas capturas usam skill v8 e movement-v3: orientação e exemplo executável de
moldura, entrada/assentamento, aproximação uniforme e saída coordenada. Corrigido
reset implícito do arredondamento CSS; radius explícito mantém controle. V1/v2 e
skills anteriores preservados por hash, inclusive recapturas e repertório v2.
99 testes Python e 30 Node passaram; cobertura 100% nos três serviços medidos,
Ruff e Mypy aprovados. Sem CI global, geração paga, asset novo ou MP4 nesta fatia.
Pacote offline preparado pelo montador; acabamento visual ainda não qualificado.
Etapa 2 (fundo vivo) aguarda OK do titular. Detalhes em
`docs/design/motion-tratamento-gravacao-2026-11-10.md`.

**Docker — pedido paralelo de diagnóstico atendido.** Cinco serviços em ciclo de
reinício consumiam mais de quatro núcleos na amostra inicial. Foram parados com
autorização explícita para mantê-los parados, sem restaurar ao final. Nenhum dado,
volume ou contêiner foi removido. Nove contêineres ativos na leitura posterior,
aproximadamente 492 MiB; limite da VM de ~3,83 GiB não é uso por contêiner.
Detalhes/limites em `docs/evals/diagnostico-docker-2026-11-10.md`.

**Histórico — etapa 1 de confiabilidade; comparação local concluída.**
Novas capturas com direção fornecida usam `provided-direction-output-v1`: o
modelo não repete scene_direction; o servidor a restaura integralmente antes
das validações/persistência. Snapshots antigos e direção proposta pelo modelo
preservados. Respostas inválidas agora conservam uso/custo estimado/request ID;
encerramento do subprocesso drena pipes após interrupção, evitando espera com
buffer cheio. Sem retry pago implícito ou relaxamento das validações.

O MP4 local da composição completa v6 foi concluído em 99,35 s: 11,2 s,
720×1280/30 fps, 336 quadros e áudio original, correlação de sinal 0,99998847.
A pausa temporária de cinco serviços com mais de 1.300 reinícios cada foi
explicitamente autorizada; os cinco foram restaurados após a captura. O teste
curto caiu de 75,90 para 26,38 s; limites e sandbox não foram ampliados.
Causa dos reinícios permanece fora desta fatia e pode voltar a afetar o ambiente.

Comparação: `.local/evals/motion-reliability-20261110/comparacao.html` e
`comparacao-alternancia.mp4` na mesma pasta. HTML/JS gerados preservados; apenas
os dois ajustes descritivos anteriores do plano. Não é nova geração v7 nem
qualificação automática: os pedidos anteriores continuam failed. Fundo ativo,
moldura e asset realista ainda precisam da prova específica. Zero novas chamadas
pagas; nenhuma reutilização de orçamento. Contrato compacto validado offline;
qualificação por modelo requer rodada própria autorizada.

Validação final: 441 testes Python dirigidos passaram (38,64 s), com 100% de
linhas/ramos nos quatro módulos medidos: adapters motion_ai/motion_html_renderer,
schema e serviço motion_generation. Ruff e Mypy de seis módulos aprovados;
exportação final verificada, links e JavaScript da comparação conferidos.
Sem CI global, testes SQL ou migração. A saída de exemplo cai de 39.029 para
29.970 bytes (23,21%); reconstrução offline preserva direção validada, HTML e JS.

Detalhes, evidências e pacote externo novo em
`docs/design/motion-confiabilidade-geracao-captura-2026-11-10.md`.

**Histórico anterior — alternância, fundo e confiabilidade; comparação então pendente.**
O titular pediu alternância entre gravação e motion e correção dos defeitos de
recorte/crítica; depois acrescentou fundo ativo, variação de moldura/escala do
vídeo e objetos mais realistas. Novas capturas usam skill v7, executor v2,
criativo v6/v7, movimento v2 e crítica v3. Snapshots antigos permanecem intactos.

Movement-v2 não cria máscara em tracks sem clip explícito. A crítica v3 liga
checks aos problemas por índices e inclui os quadros reais desses problemas,
sem relaxar mínimos de evidência ou inventar suporte. Passaram 393 testes Python
com cobertura integral nos cinco módulos avaliados; 66 testes de contexto/skills/
exportação após o feedback v7; 25 Node, Ruff e Mypy dos dez módulos. A prova
sintética no Chromium confirmou o conserto do recorte com máscaras preservadas.
Sem CI global ou SQL nesta fatia.

A rodada de até US$ 3 teve duas gerações autorizadas: primeira completa mas com
plano inválido (v6), recuperação incompleta (v7). Zero renders/críticas pelo fluxo,
pedidos failed e workers encerrados. Uso estimado total US$ 0,572968, incluindo
cálculo local da primeira resposta cujo ledger ficou sem estimativa; reservas
retidas US$ 2,15. Nenhuma imagem paga, retry adicional ou uso do saldo autorizado.

Não foi concluído novo MP4 para comparação. A variante local da primeira resposta
completa reuniu apenas dois intervalos descritivos do plano, HTML/JS intactos.
A captura integral excedeu 600 s; a tentativa local em trechos falhou por timeout
do navegador. Restaram três quadros estáticos, sem validação de movimento/áudio.
Processo diagnóstico encerrado; nenhum renderer remanescente. A resposta parcial
v7 não foi executada. Ver `previas-parciais.html` na pasta local do ensaio.
Asset realista em camadas (2.5D) é viável com os recursos de imagem existentes;
geometria 3D giratória ainda exige outra integração. Qualificação visual pendente.

Próximo gate: saída completa/validável, captura confiável, recuperação limitada e uso/custo de erros
preservados, antes de liberar a jornada do Reel. Depois: pedido/ajuste/aprovação/
download, fala alinhada, story em vídeo, carrossel e operação. Postagem é posterior.
Detalhes em `docs/design/motion-alternancia-e-confiabilidade-2026-11-10.md`,
`docs/evals/plano-motion-alternancia-2026-11-10.md` e
`docs/design/fechamento-produto-geracao-2026-11-10.md`.

**Histórico — interação entre mensagem e elementos, comparação entregue.** O titular pediu
setas, ícones e objetos com acabamento adulto e ações ligadas às frases. A direção
anterior restringia esses recursos indevidamente. A skill v4 e a nova direção
Café Pausa orientaram tempo→percurso, café→preenchimento, pausa→repouso/convite.
A coreografia usa texto editorial; não há transcrição alinhada nem sincronismo
vocal comprovado. Fonte, áudio, kit e versões históricas foram preservados.

A primeira geração veio incompleta. A recuperação explicitamente autorizada
renderizou, mas contêineres aninhados recortaram o vídeo; a crítica apontou o
defeito e falhou na vinculação exata das evidências. O pedido permaneceu `failed`.
Foi entregue uma variante com correção CSS local apenas desses recortes, pelo
mesmo renderer isolado, sem novas chamadas pagas ou aprovação automática.
Novas capturas usam skill v5, que acrescenta orientações sobre esses dois problemas;
recapturas conservam seus hashes. A v5 ainda não foi qualificada em geração real.

Teto acumulado US$ 3 respeitado: reservas US$ 2,90; estimativa pelo uso retornado
US$ 0,758614, distinta de fatura. O ledger da crítica inválida ficou sem estimativa;
o total inclui cálculo local explicitamente separado. Worker encerrado, ambiente
temporário removido. Passaram 100 testes Python e quatro Node; cobertura dirigida
do loader 100% de linhas/ramos, sem CI global. MP4 local: 11,2 s, 720×1280/30 fps.
Amostras visuais e sinal de áudio conferidos; acabamento depende do titular.
Ver `docs/design/motion-interacao-mensagem-2026-11-10.md` e
`docs/evals/plano-motion-interacao-2026-11-10.md`. Pendentes: confiabilidade do fluxo
automático, qualidade da v5 em prova futura e sincronismo com fala real. Nenhuma
nova chamada ou uso do saldo está autorizado.

**Comparação após a refatoração concluída.** Sob teto novo de US$ 5, o fluxo
API/Temporal gerou e renderizou uma candidata Café Pausa e concluiu uma crítica,
sem refações nem imagens pagas. Uso total estimado US$ 0,322005; reservas US$ 2,80,
distintas de fatura. MP4 720×1280/30 fps, 11,2 s; parecer `adequate` sem truncamento
nesta rodada, sem comparação automática com a peça anterior ou aceite humano.
Worker dedicado encerrado. Comparação A/B, custos, validação e limites em
`docs/evals/plano-comparacao-refatoracao-motion-2026-11-10.md`.
Aguardar avaliação do titular; saldo restante não autoriza novos efeitos.

**Decisão mais recente — etapa 6 concluída; pacote externo entregue.**
O titular confirmou a proposta Café Pausa em entrevista. O exportador usa o mesmo
montador de instruções/contexto do produto e `build_request`, com dados factuais
e amostras verificados da prova registrada. Nenhum prompt paralelo de construção.
ZIP com 39 arquivos em `.local/exports/motion-cafe-pausa-20261110.zip`: prompt
integral, JSON/schema/parâmetros, 12 imagens, contexto, direção, repertório/licenças,
fonte MP4, fontes e runtimes. Manifesto separa entrada do modelo de execução.
Uso e caminhos em `docs/evals/pacote-externo-motion-2026-11-10.md`.

Sem credenciais, consulta ao banco, despacho Temporal, contagem remota, API paga,
novos assets ou render. IDs locais novos e ilustrações desabilitadas nesta entrada;
nenhuma autorização anterior de orçamento reutilizada. Dados factuais e amostras
são históricos, não uma recaptura/admissão operacional atual. O chat externo pode
alterar papéis, schema ou leitura; vídeo/runtimes extras são variações documentadas.

Passaram 69 testes curtos com insumos sintéticos: igualdade do payload, anexos,
hashes, ZIP, ausência de dados privados de teste, bloqueio de rede e compatibilidade
do montador. Contexto com 100% de linhas/ramos na cobertura dirigida; Ruff, tipos
e diff aprovados. Pacote real e ZIP verificados, sem CI global ou teste SQL.
As seis etapas de preparação estão concluídas; aguardar o resultado externo.
Acabamento, movimento e áudio continuam sem nova prova, sem autorização de produção.

**Histórico — etapa 5 implementada e validada localmente.**
Novos snapshots incluem `motion-review-v2`, com o mesmo alvo de acabamento na
geração, crítica e correção. Integridade técnica, legibilidade e preservação do
kit são distintas de desenvolvimento visual; evidências da peça permanecem
separadas das referências. Falha criativa acionável deve compartilhar quadro
atual com o problema correspondente; ausência de evidência não autoriza refação.

A resposta compacta usa IDs de quadros, convertidos ao parecer durável com tempo
e SHA antes das validações. Prosa/problemas são limitados, mantendo os checks.
Somente a entrada da crítica omite HTML/JavaScript das composições; a correção
recebe código completo. Snapshots anteriores conservam o contrato anterior.
Sem novo serviço, tabela, executor ou aumento de orçamento/teto: crítica permanece
limitada a 8.000 tokens ou ao limite configurado menor, sem retry automático.

Passaram 214 testes dirigidos; cobertura de linhas/ramos em 100% no serviço de
crítica e no schema compacto. Ruff, tipos dos quatro módulos e diff aprovados.
Na fixture sintética, 76,1% menos bytes de resposta para o mesmo parecer; não é
medição de tokens/custo nem garantia contra truncamento. Sem CI global, banco,
API real, geração de assets ou render. Detalhes e limites em
`docs/design/critica-motion-2026-11-10.md`. Acabamento continua sem prova visual.
O OK para a etapa 6 foi dado na solicitação seguinte.

**Histórico — etapa 4 implementada e validada localmente.**
Novos pedidos HTML usam a skill `instagram-reel-v3`, com orientações concretas de
hierarquia tipográfica, máscaras, planos em profundidade, ação com resultado,
contraste de movimento, leitura e continuidade. Dois exemplos completos usam
MotionV1 existente: passagem entre focos com gravação contínua e entrada escalonada
com tempos finais disponíveis para o plano. Não são cenas impostas nem APIs novas.
A direção fornecida orienta a implementação; identidade, gravação e voz permanecem.

O texto e os exemplos chegam por `authorized_context.skill`, no mesmo corpo
contado/limitado. O mapa de uso orienta a adaptação do repertório da etapa 2 sem
copiar identidade. Recapturas HTML carregam o ID/hash original da skill; v1/v2,
pacote de referências, renderer e runtimes permanecem intactos. Sem novo serviço,
componente, tabela, motor ou geração de mídia. Caminhos e uso em
`app/assets/motion_skills/README.md`.

Passaram 170 testes Python e quatro testes Node direcionados. Os dois módulos
de produção alterados atingiram 100% de linhas/ramos na cobertura dirigida.
Ruff, tipos e diff aprovados; sem CI global, banco, API real ou render.
Os testes JavaScript executam os exemplos da própria skill com DOM substituído;
validam continuidade de estado e busca temporal, não qualidade visual. A proposta
Café Pausa continua sem aceite criativo. O OK para a etapa 5 foi dado na
solicitação seguinte. Exportação integral permanece na etapa 6.

**Histórico — etapa 3 implementada e validada localmente.**
O pedido aceita `scene_direction` opcional com o schema existente. Quando fornecida,
a direção fica no snapshot antes da construção, sob `reel-creative-v5`, e orienta
plano e código. O payload distingue direção fornecida de proposta pelo modelo,
identifica origem/hash e não infere aprovação humana. O serviço rejeita troca da
direção na geração/correção antes de imagens ou render; tempos e curvas continuam
no único `motion_plan`. Sem direção fornecida, mantém o fluxo existente em v4.

Proposta revisável Café Pausa: “abrir espaço para uma pausa”, com gravação contínua,
planos e tipografia em dois momentos específicos da prova. Não exige jarra/xícara
desenhadas; usa o kit e preserva a voz. A proposta ainda não foi aprovada pelo titular.
Contrato, uso e briefing substituto em `docs/design/direcao-visual-motion-2026-11-10.md`;
entrada em `docs/evals/direcao-cafe-pausa-2026-11-10.json`. Sem planejador automático,
nova chamada, tabela ou alteração do executor. Aprovação de quadros continua separada.

Passaram 228 testes Python direcionados; novo módulo com 100% de linhas/ramos na
cobertura dirigida. Ruff, tipos dos seis módulos de produção e diff aprovados.
Sem CI global, banco, API real, geração de assets ou render. Igualdade da direção
não comprova fidelidade visual do HTML nem acabamento. O OK para a etapa 4 foi
dado na solicitação seguinte. Exportação integral fica na etapa 6.

**Histórico — etapa 2 implementada e validada localmente.**
O pedido pode selecionar explicitamente `repertoire_id=business-reel-v1`.
O mesmo montador do produto captura três exemplos completos adaptados de
Maestro, Finalizador e claude-video, com fontes/licenças/hashes, e entrega seis
quadros de Felipe Borges e Lucas Leite ao modelo. Referências têm rótulo, tempo
aproximado, sequência, uso permitido e limitações; ficam fora dos assets de render.
Não há estilo imposto globalmente, novas tabelas ou novo executor. Pedidos sem
seleção e snapshots históricos conservam seu conteúdo.

Os anexos seguem para geração, revisão e correção e integram o mesmo corpo da
contagem/tetos de entrada existentes. Limites locais de texto/imagens e hashes
falham antes de envio quando há ausência, alteração ou associação incorreta.
Pacote: `app/assets/motion_repertoire/README.md`. Passaram 163 testes Python
focados e dois testes Node sem mídia renderizada; novo módulo com 100% de
cobertura de linhas/ramos na verificação dirigida. Ruff, tipos dos sete módulos
alterados e `git diff --check` aprovados; sem CI global.
Nenhuma API real, geração de assets ou render. Acabamento visual ainda não provado.
O OK para a etapa 3 foi dado na solicitação seguinte.

**Histórico — etapa 1 da refatoração implementada e validada localmente.**
O titular pediu documentar a execução em etapas: (1) contrato/contexto sem
contradições; (2) repertório e referências efetivamente enviados; (3) direção
visual distinta da construção; (4) orientações e exemplos de construção/movimento;
(5) crítica alinhada ao alvo e aos limites; (6) exportação do payload completo.
Plano: `docs/design/refatoracao-contexto-motion-2026-11-10.md`.
Novos pedidos usam a skill `instagram-reel-v2`, o contrato
`html-motion-executor-v1` e a projeção `html-executor-style-v1` das fichas;
arquivos e hashes históricos permanecem intactos, assim como a recaptura de
pedidos anteriores. Passaram 95 testes direcionados de contexto, skills, estilos
e adaptador; Ruff check/format e `git diff --check` aprovados, sem CI completo.
O OK para a etapa 2 foi dado na solicitação seguinte. Ao final da sequência, entregar
prompt, anexos e manifesto para teste manual em ChatGPT, Grok ou outro modelo.
Parar antes de chamadas pagas, geração de assets ou render da peça. Não preparar
um prompt paralelo como se fosse a entrada exata do produto. Aguardar resultado
externo para decidir prova integrada. Infraestrutura existente e kit preservados.

**10/11 — vídeo renderizado; melhora parcial, qualidade desejada não atingida.**
Após a recuperação dos quadros (migração 0115), o titular aprovou a versão exata.
A API registrou o aceite e o Temporal montou o MP4 reutilizando composição e
materiais. Comparativo: `.local/evals/reel-storyboard-composition-20261109/comparison.html`.
O titular reconheceu mais elementos visuais, mas considerou o desenho infantil e
o resultado ainda distante do acabamento profissional das referências. Esse
feedback não é aprovação criativa final. Pediu analisar dois novos vídeos como
referência de acabamento. Esclareceu que edição de bruto para YouTube é outra
ideia, fora do escopo atual: manter a gravação do cliente e explorar muito mais
a composição/movimento ao redor dela na postagem do negócio. Cortes do bruto
não são pré-requisito para esta melhoria.

A única crítica prevista veio truncada no limite de 8.000 tokens, sem parecer
válido. Pedido encerrado como `failed/MOTION_AI_OUTPUT_LIMIT`, MP4 e recibos
preservados. Corrigida a identidade de falha da continuação para não colidir com
a falha anterior em audit/outbox; migração aditiva 0116 aplicada no dev, sem
limpeza. Nenhuma repetição de IA, render ou correção automática nessa recuperação.

Acumulado da prova: quatro chamadas textuais, estimativa US$ 0,775244 e reservas
US$ 3,40 retidas; nenhuma imagem gerada paga. Estimativa não equivale à fatura.
Qualquer nova chamada exige plano/autorização próprios; não reutilizar o saldo
como autorização automática. 69 testes unitários direcionados (1,55 s) e três
testes SQL em banco `_test` (7,52 s) passaram, com Ruff aprovado. Sem CI completo.
Ponto 4 não qualificado; etapa 5 não iniciada. Resultado detalhado em
`docs/evals/resultado-video-composicao-2026-11-10.md`.

**Análise posterior das referências:** download e inspeção dos dois vídeos de Lucas
Leite concluídos por amostragem visual. Auditoria da chamada confirmou seis quadros
da fonte, nenhuma referência visual de acabamento, skill resumida e três fichas
antigas com restrições incompatíveis com o executor HTML. Modelo `gpt-6.1-sol`,
esforço alto, geração completa; não há benchmark que atribua a causa ao modelo.
A direção da prova também induziu os desenhos de jarra/xícara. Corrigir contexto
e testar uma cena exigente é o próximo recorte proposto, ainda não implementado.
Detalhes: `docs/evals/analise-acabamento-motion-2026-11-10.md`. Nenhuma nova chamada paga.


**Adaptação do fluxo de Lucas Leite:** mapeamento das oito etapas e dos guias
publicados concluído em `docs/design/adaptacao-fluxo-edicao-2026-11-10.md`.
Base técnica existente reaproveitável; falta separar decisão visual de construção,
transmitir referências e instruções coerentes e demonstrar acabamento numa cena.
Hoje direção/plano/código são gerados juntos, antes da aprovação dos quadros.
O documento é proposta, não integração concluída. Sem nova API paga ou mudança
no executor; cortes de bruto para YouTube continuam fora do escopo.

**Histórico — reformulação da composição autorizada, antes do vídeo.**
O titular gostou das xícaras desenhadas e autorizou reformular a composição.
Isso não aprova a galeria anterior para animação. A nova direção alterna gesto
real, transformação ilustrada e convite à pausa, com foco, escala e organização
distintos; preserva desenhos figurativos, kit, fonte integral, áudio e aprovação
humana dos quadros. Esse roteiro é específico da prova Café Pausa.

Orientação geral de geração/crítica ajustada para avaliar evolução da composição,
sem impor variedade arbitrária: acrescentar desenhos a um layout repetido não
demonstra elaboração por si só. Repetição com função narrativa continua válida.
Vinte testes direcionados passaram em 1,09 s; Ruff/format aprovados. Worker
reconstruído; renderer, runtime, hashes históricos e banco não foram alterados.

Novo payload preparado para o produto, dentro da autorização original: até
US$ 3,70 restantes + US$ 1,70 retidos = US$ 5,40. Duas chamadas textuais/contagens,
até duas ilustrações opcionais, sem correção automática; parar nos quadros.
Plano: `docs/evals/plano-reformulacao-composicao-2026-11-09.md`.
Pendente: nova galeria real, aceite humano e vídeo/crítica. Etapa 5 não iniciada.

**Histórico da retomada anterior — três quadros após correção técnica local.**
Retomada autorizada executou uma geração completa, validada pelo contrato. O modelo
criou três cenas com desenhos SVG próprios; não solicitou ilustrações pagas.
O render integrado falhou (`MOTION_RENDER_EXECUTION_FAILED`): elementos estáticos
receberam tracks com `beats:[]`, mas a biblioteca exige ao menos um intervalo.

Diagnóstico local preservou o original e acrescentou somente holds idênticos ao
estado inicial dessas tracks. O mesmo renderer isolado capturou três PNGs reais,
sem nova IA, MP4 ou alteração/reabertura do pedido encerrado. Galeria aberta para
o titular: `.local/evals/reel-storyboard-resume-20261109/diagnostic-gallery.html`.
É uma captura após correção técnica, **não** uma galeria aprovada/persistida pelo
fluxo integrado. O titular depois solicitou reformular essa direção antes do vídeo. Movimento/áudio não
foram avaliados; a composição ainda repete vídeo à esquerda e desenho à direita.

Instruções da biblioteca agora explicitam 1–12 beats por track e hold para elementos
estáticos. Runtime e hashes dos snapshots permanecem intactos; não adicionamos
recuperação automática ou nova geração. Cinco testes direcionados passaram em
0,68 s, Ruff aprovado; captura real passou pelo sandbox/protocolo 2. Sem CI completo.

Uso estimado da retomada: US$ 0,180125; somado à tentativa truncada, US$ 0,421603.
Reservas das duas tentativas: US$ 1,70 retidos para conciliação. Nenhuma imagem ou
crítica paga, nenhuma correção paga. Os limites autorizados não foram ampliados.
Plano/resultado: `docs/evals/plano-retomada-storyboard-integrada-2026-11-09.md`.
Pendente: decisão visual, tratamento da falha na integração e vídeo/crítica final.
Nenhuma equivalência às referências demonstrada; nenhuma etapa 5 iniciada.

**Histórico da conclusão do ponto 3 — quadros completos por cena e aprovação antes do MP4.**
Pedidos com `storyboard=true`, quando a capacidade estiver explicitamente habilitada,
produzem um PNG completo por cena com a composição e os assets reais da geração.
O modelo indica o momento representativo; o renderer captura somente esses momentos,
sem codificar vídeo/áudio. Não são todos os frames nem evidência de ritmo/mixagem.

Galeria HTML e metadados privados ficam disponíveis pela API autenticada. O aceite
vincula versão e hash do conjunto; reprovação registra feedback e encerra o pedido,
sem tentar outra chamada paga. A aprovação emite outbox e retoma pelo Temporal,
reutilizando composição e ilustrações, revalidando fontes, consentimento e orçamento.
Reentregas são bloqueadas por identidade durável. A revisão/aprovação final da peça
continua distinta da aprovação inicial de composição.

Validação: 295 testes Python direcionados em 3,70 s e 72 testes Node em 0,55 s;
mypy e Ruff aprovados. IO de banco/browser/provedor substituído nos testes locais;
regressão SQL de isolamento/aceite/reentrega adicionada, não executada. Sem CI
completo, chamadas pagas, reconstrução Docker, migração aplicada ou prova criativa.

**Pendências registradas ao concluir o ponto 3 (resolvidas na preparação do ponto 4):** aplicar `0114_motion_storyboards`, reconstruir
renderer com protocolo 2 e configurar seu novo digest; habilitar
`motion_storyboard_enabled` (default false) e enviar `storyboard=true`.
Pedidos antigos continuam no fluxo anterior. Naquela conclusão, o ponto 4 aguardava comando: prova real
com IA, apresentação dos quadros para o titular e avaliação do vídeo após aceite.
Não há uma nova peça real produzida nesta implementação nem orçamento reutilizado.

**Histórico do ponto 2 — componentes, acervo e ilustrações sob demanda.**
O fluxo do Reel reúne 16 componentes vetoriais, desenho original por código,
até quatro fotos autorizadas do acervo e até duas ilustrações geradas quando
necessárias. A mesma geração textual declara a arte e seus caminhos; o serviço
cria os PNGs antes do render, e a crítica recebe os pixels gerados. Kits, skills,
biblioteca de movimento, Temporal e histórico privado continuam preservados.

Ilustrações têm identidade por pedido/asset, reserva própria no ledger compartilhado,
registro de uso/proveniência e upload privado verificado. Correções reutilizam os
mesmos arquivos e não podem alterar a lista para disparar novas imagens. Despacho
repetido, falha incerta, custo desconhecido/excedido e falta de orçamento interrompem.
A reserva é limite de admissão local, não teto de faturamento imposto pela Images API.

Ativação explícita desabilitada por padrão: `motion_illustrations_enabled=false`,
reserva e orçamento de imagens zero. O orçamento de imagens é parte do orçamento
total do Reel; precisa deixar espaço para geração e crítica. Sem novas permissões,
migração ou chamadas pagas. Modelos e contratos históricos preservados; não há
ativação retroativa para pedidos capturados sem essa capacidade.

**Na conclusão do ponto 2, o próximo ponto era:** quadros principais com a arte
pronta antes do vídeo (ponto 3, implementado conforme registro acima). Prova visual com IA real e aceite criativo continuam posteriores;
esta implementação não demonstra que o acabamento já atingiu as referências.
Validação: 273 testes direcionados aprovados em 3,76 s, Ruff/format e mypy
em 12 módulos aprovados. Pixels sintéticos e transporte simulado; sem CI completo,
banco ou render integrado. Regressão SQL adicionada para o `_test`, não executada.

**Histórico do ponto 1 — direção criativa por cena.**
Novos pedidos capturam `reel-creative-v3` e exigem `scene-direction-v1`: base no
briefing, representação visual, composição, ação narrativa, ordem de atenção e
aparência/construção de cada elemento. A direção se vincula às cenas/elementos
do `motion_plan-v1`, que conserva os tempos, estados, relações e transições.
Geração/correção usam a mesma chamada; não há geração de assets nesta fatia.
O serviço recusa vínculos incompletos/inválidos antes de reservar render. Direção
acompanha composição privada, crítica e correções; v1/v2 históricos permanecem
compatíveis. Kits, acervo, skills, motion lib, orçamento e Temporal preservados.

201 testes direcionados em 5,18 s; Ruff/format e mypy aprovados. Cobertura de
100% nos três módulos medidos de direção/plano/contrato, não CI da aplicação.
Regressão SQL acrescentada, não executada. Sem banco, API paga, render ou deploy.
À época, criação/seleção de elementos aguardava comando; estado atual acima. Quadros principais,
crítica aprimorada e comprovação visual continuam posteriores. Implementar o
contrato não comprova que o modelo atingirá o acabamento desejado.
[Escopo, decisões e validação](../design/evolucao-qualidade-motion-referencias-2026-11-09.md).

**Pesquisa de composição concluída:** Maestro contém geração de objetos
recortados, busca de takes e captura de páginas; Finalizador contém 70 cenas em
código; claude-video já prevê arte por cena antes da animação. Fontes externas
oficiais confirmam catálogo de componentes e mídia. Na pesquisa, esses recursos ainda não estavam
integrados ao Reel; adaptação parcial registrada acima; a pesquisa não demonstra qualidade nem autoriza gastos.
O titular posteriormente confirmou liberação do conteúdo Maestro para nosso uso;
a observação anterior sobre o ZIP não bloqueia o escopo autorizado.
[Inventário, fontes e próximo recorte](../evals/pesquisa-elementos-motion-2026-11-09.md).

**Quarto passo: fluxo técnico concluído; melhora parcial, alvo criativo não atingido.** A retomada
Café Pausa terminou `completed` pelo worker/Temporal dev, com uma versão real,
crítica e download autenticado conferido por SHA. Comparativo A/B aberto para o
titular; não houve correção. Duas chamadas/contagens, 574,11 s, US$ 0,379066 estimado.
Com a tentativa truncada anterior: US$ 0,562636 estimado e US$ 2,55 reservado,
dentro do teto original de US$ 3,40. Reservas não são fatura/uso conciliado.

Modelo retornou `adequate`, quatro checks criativos `met` e temporais `pass`.
Entretanto, as três janelas cobriram entrada de palavra, ponto gráfico e hold de
CTA; **37 de 40 eventos omitidos**, incluindo as principais transições sem sequência
próxima completa. Isso valida o fluxo técnico, não o acabamento esperado ou a
eficácia do crítico nesse alvo. Geração usou 18.102 tokens com override de 32.000;
defaults gerais de 16.000 não foram alterados. Crítica: 7.924 de 8.000 tokens.
Worker próprio encerrado; sem CI completo, migração, publicação ou expansão de
formato. Avaliação humana recebida: melhorou, mas ainda muito longe; faltam
componentes figurativos, imagens e ícones relacionados à mensagem. Não há aceite
criativo/comercial nem confirmação específica de áudio ou ausência de regressões.
A auditoria encontrou entrada restrita a vídeo/fontes/logo, direção centrada em
tipografia/enquadramento e ausência de transcrição. MotionV1 oferece movimento,
mas não constrói por si só esse repertório visual. Próximo recorte proposto:
planejamento visual por mensagem, materiais/componentes associados ao kit e
crítica das cenas principais. A direção foi implementada posteriormente, conforme
registro acima; demais pontos pendentes e nenhum novo gasto.
[Plano concreto](../evals/plano-prova-motion-temporal-integrada-2026-11-09.md).
[Plano de retomada](../evals/plano-retomada-motion-temporal-2026-11-09.md).

**Terceiro passo da evolução de motion implementado — crítica temporal.**
Novos snapshots incluem `motion-temporal-v1`: até três eventos distribuídos pela
peça, cinco quadros de contexto e até cinco por evento, mantendo **no máximo 20
quadros por versão**. Tempos do plano orientam a extração; somente quadros reais
decodificados do MP4 fundamentam a crítica. O manifesto privado registra IDs,
tempos, hashes, cobertura, bordas e eventos omitidos. Nenhuma chamada adicional
é obrigatória; texto e imagens continuam na contagem/reserva existente.

`MotionReview` passa a exigir, nessa capacidade, continuidade, sobreposição,
tempo de leitura e coordenação. Um parecer conclusivo requer sequência completa
com pelo menos três tempos citados, incluindo seus extremos. Correção temporal
precisa apontar issue acionável compatível e localizada nessa evidência; incerteza
não autoriza refação. Preferência pela versão nova requer sequências das duas
versões. Histórico sem capacidade temporal conserva o comportamento anterior.
Kit e referências continuam separados; calibrações externas são textuais, sem
alegar comparação visual com vídeos não enviados.

Validação: **292 testes direcionados em 7,29 s**, Ruff e mypy aprovados; proteção
adicional contra issue genérica de motion contornando incerteza confirmada em
41 testes (0,80 s). Extração do MP4 sintético anterior: 16 quadros, três eventos
completos e 12 omitidos explicitamente; sequências inspecionadas. Sem IA paga,
novo render, CI completo, teste SQL, migração ou deploy. Isso valida implementação
e vínculo das evidências, não acerto do julgamento da IA ou ganho criativo.
**Quarto passo com execução técnica concluída e qualidade criativa insuficiente**, conforme
avaliação humana acima. Não expandimos formatos nesta fatia.

**Segundo passo da evolução de motion implementado — execução reutilizável.**
`MotionV1` oferece timeline com estados numéricos, curvas cúbicas/Bézier/mola,
entradas escalonadas, máscaras e transformações coordenadas, calculadas por
`seek(ms)` sem relógio ou playhead acumulado. A API, versão e SHA-256 entram no
contrato capturado; o serviço verifica disponibilidade antes da geração paga.
O adapter inclui os bytes conferidos no início de `scene.js`, pelo canal isolado
já existente. Assim, a imagem do renderer não precisa incorporar uma nova
biblioteca; o worker precisa receber o código atualizado. Pedidos históricos
sem essa capacidade conservam os bytes originais da cena. Kit, acervo, skills,
estilos, áudio, versões e limites de orçamento permanecem no fluxo existente.

Validação: **266 testes Python em 4,20 s**, 8 testes Node em 0,51 s, Ruff e mypy
aprovados; após um ajuste de compatibilidade, 30 testes afetados em 1,98 s.
Reprodução sintética local de **4 s / 120 quadros / 360×640 / 30 fps**, com
Chromium, CSP/roteamento e FFmpeg reais; quadros extraídos do MP4 inspecionados.
A demonstração foi escrita manualmente, sem áudio ou geração por IA: comprova
execução dos recursos, não ganho criativo. Não houve CI completo, teste SQL,
migração, build/deploy, API paga ou nova prova Linux/Temporal naquela fatia. O
terceiro passo foi implementado posteriormente, conforme registro acima. A prova
integrada continua necessária para demonstrar qualidade do produto.

**Primeiro passo da evolução de motion implementado — contrato de movimento.**
Novos pedidos usam `reel-creative-v2` e exigem `motion-plan-v1` na mesma chamada
que produz/corrige HTML: cenas e elementos identificados, tempos absolutos,
estados, trajetória/curva, relações e propósito. Kit, acervo autorizado, skill e
biblioteca de motions continuam no contexto; referências orientam acabamento do
movimento, preservando a identidade do negócio. O plano acompanha as versões
cifradas e a crítica existente. Antes de reservar o efeito de render, o serviço
confere duração, estilo selecionado e assets autorizados; o schema rejeita
lacunas de cenas, eventos fora de intervalo e relações inválidas. Sobreposição
entre cenas é permitida para transições; entre beats do mesmo elemento, não.
Históricos sem plano e `reel-creative-v1` continuam legíveis e processáveis.

Validação desta fatia: **155 testes direcionados passaram em 8,75 s**, Ruff e
mypy aprovados. Regressão SQL adicionada para falha sem plano e reentrega sem
repetir geração; não executada nesta rodada. Sem CI completo, banco, render,
API paga ou deploy naquela fatia. A conformidade do plano **não comprova execução
visual** do HTML. O segundo passo foi implementado posteriormente, conforme
registro acima; a crítica temporal também está implementada. A prova integrada
(quarto passo) foi executada; o alvo criativo continua não atingido. Detalhes no plano de evolução de qualidade de motion.

**A fatia local de integração do Reel está implementada e tecnicamente
qualificada.** Pedido/contexto privado, efeitos duráveis, Temporal, renderer
HTML isolado, crítica/correção condicionais e versões imutáveis estão ligados.
A coleção permite revisão, cinco confirmações por arquivo e download privado;
a aprovação não cria postagem. A versão mais nova não é automaticamente a melhor.

O [CI da base anterior à proteção completa de orçamento](../../.local/ci-motion-integration-20261109/run-20261109T154537Z/result.json) passou: **5.353 testes, 100% de 18.570 linhas e 5.090 branches**,
sem skips. Passaram também 363 testes Python do laboratório, 137 Node dos
renderers, lint/formatação e tipos. Web: 524 testes/100% nas quatro métricas,
tipos, build, formatação e QA de interface em 390/1440 px. O código daquela execução permaneceu
estável durante o CI; os bancos eram exclusivos `_test`, com roles restritas.

Os quatro replays Linux preservaram código/assets: Intensa 67,3 s, Dog 75,2 s,
Luma 73,3 s e Giz B 107,2 s. A prova do pedido ao download passou em 97,6 s
com API/auth, SQL/RLS, relay, Temporal, renderer e storage reais; **modelo e
crítico simulados**. Reentrega não repetiu efeitos; acesso de outro tenant e
anônimo foi bloqueado. Não houve aprovação humana fabricada nem chamada paga.
[Comparações, resultados e limites](../evals/qualificacao-integracao-reel-2026-11-09.md).

Os dez workers parados com autorização foram restaurados. O storage descartável
da prova foi parado, preservando dados e arquivos. A primeira execução do CI
falhou numa expectativa antiga de tabela; o teste foi alinhado à guarda que
inclui Reels. Novas provas SQL cobrem bloqueio durante execução e repetição de
aprovação antiga após surgir outra versão, sem duplicar efeitos ou aprová-la.

**Isso não encerra a ativação comercial da etapa 4 nem a v0.** A configuração
continua desativada por padrão e restrita a negócios/materiais sintéticos.
A validação completa do orçamento (ponto 1) foi implementada: contagem da
entrada multimodal antes da geração, soma com a saída máxima e bloqueio
quando exceder a reserva compartilhada. A contagem inclui instruções, schema
e quadros de origem/versões, sem gerar conteúdo. Política qualificada para
`gpt-6.1-sol` Standard: tarifa conservadora cobre escrita de cache; entrada
acima de 272 mil tokens e modelos/tarifas não qualificados são bloqueados.
Cálculo e versão da política ficam no registro cifrado da operação.
Validação desta mudança: **100 testes unitários direcionados em 1,62 s**,
Ruff e mypy aprovados; sem CI completo, SQL, render ou chamada externa. O CI
acima documenta a base anterior, não uma nova execução desta mudança.
**Ponto 2 implementado após autorização:** target `motion-worker` com cliente
Docker, overlay opcional com configuração consistente de API/relay/worker e
pasta temporária compartilhada no mesmo caminho. O renderer recebe somente a
entrada da própria tentativa; socket/credenciais permanecem fora dele. Há um
comando de verificação sintética de dois quadros para executar antes da prova.
**130 testes direcionados passaram em 4,49 s**, Ruff/mypy e Compose resolvido
aprovados (desativado e fixture fake, sem carregar o `.env` real). Na entrega
do ponto 2 não houve build/render real; eles foram executados no ponto 3 abaixo.
**Primeira rodada do ponto 3 — histórico da falha:** a prova Café Pausa com IA real
produziu duas versões de 11,2 s pelo worker do produto, Temporal local autorizado
e banco dev existente (migrações 0112/0113 aplicadas com autorização, sem limpeza).
A crítica detectou acentos corrompidos; a correção preservou o JavaScript e
corrigiu o texto observado nos quadros. Foram três chamadas ao modelo e quatro
contagens (a última inferida pelo avanço até o claim); uso estimado conhecido
**US$ 0,412521**, reservas **US$ 2,55**, teto autorizado US$ 3,40. Fatura não conciliada.
O PostgreSQL cancelou o INSERT do pacote da crítica final em `motion_effects`
por ultrapassar o prazo de 10 s. A quarta chamada ao modelo não foi enviada.
Pedido `failed`, duas versões preservadas, sem peça liberada na coleção:
crítica final e download ficaram pendentes naquela rodada, concluídos em nova
operação no item 3 abaixo.
Não houve retry pago, aceite humano ou publicação. Worker próprio encerrado.

O defeito de UTF-8 foi corrigido no runner, com 71 testes direcionados (1,17 s)
e verificação real mínima da imagem nova; a prova paga preservou o digest antigo.
**Correção de persistência implementada após a rodada:** pedidos multimodais e
quadros cifrados acima de 64 KiB passam ao armazenamento privado existente;
SQL mantém referência cifrada pequena, hashes e identidade de operação.
Upload é registrado antes do IO, conferido por tamanho/hash e nunca repetido
automaticamente; falha interrompe antes da chamada paga. Serialização/cifra saíram
das transações desses registros. Leitura recupera registros inline antigos e
referências novas, validando tenant/negócio/pedido antes de buscar o objeto.
No pacote salvo do Café Pausa, o campo SQL caiu de **42.205.388 para 716 bytes**,
com conteúdo recuperado exatamente (medição offline, 1,417 s). **81 testes
unitários direcionados passaram em 1,42 s**, Ruff/mypy aprovados. Acrescentadas
duas regressões SQL para o CI futuro; não executadas nesta fatia.
Não houve migração, alteração do dev, build/deploy, CI completo ou API paga.
O pedido antigo continua falho; a nova prova integrada está registrada abaixo.
Não foi aumentado o timeout global nem removida a trava de custos.
A exportação somente leitura usou prazo local de 60 s para recuperar as evidências.
Temporal dev voltou ao estado parado original, com histórico preservado; seu
problema permanece separado. Sem CI completo nesta rodada.
[Vídeos, resultado, custos e limites](../evals/plano-prova-reel-integrada-2026-11-09.md).
**Item 2 anterior — direção e critérios criativos:** esta entrega introduziu
`reel-creative-v1` (novos pedidos agora usam v2, conforme atualização acima) no contexto cifrado e no fingerprint. Geração/correção recebem
orientação para planejar tempos, estados visuais e função das transformações no
`concept`, com calibrações textuais de Intensa, Dog, Luma e Giz B. Nenhuma mídia
desses ensaios foi incorporada ou enviada; estilo/intensidade não são universais.
A crítica exige quatro avaliações: atendimento ao briefing, progressão narrativa,
função do movimento e desenvolvimento visual. Cada uma liga pedido, observação
e quadros; as três temporais exigem dois tempos distintos da versão atual.
`adequate` não admite requisito criativo falho/incerto; lacuna criativa acionável
usa a correção condicional existente. Incerteza sem defeito concreto não dispara
refação. Acentos corrigidos não são ganho de motion. Leitura histórica preservada.
**98 testes direcionados passaram em 1,50 s**, Ruff/mypy aprovados. Acrescentada
regressão SQL de bloqueio de crítica apenas técnica, para execução futura.
Sem render, API paga, migração, build/deploy ou CI completo. Esses testes provam
as regras de validação, não a qualidade criativa do julgamento do modelo.
Itens 1 e 2 implementados; **item 3: prova técnica real concluída; melhora criativa
parcial, abaixo do nível esperado pelo titular**. Nova operação Café Pausa terminou `completed`, com
geração, render, crítica, coleção privada e download autenticado conferido por
SHA-256. Duas chamadas ao modelo e duas contagens; estimativa **US$ 0,266156**,
reservas novas **US$ 1,70**. Com US$ 2,55 anteriores, permanecem US$ 4,25 retidos
sob teto agregado autorizado de US$ 5,95; fatura ainda não conciliada.
A crítica marcou os quatro requisitos criativos `met` e não pediu correção:
há uma única versão nova. O A/B compara a peça histórica com a nova geração;
não demonstra ganho de correção automática. Payloads grandes usaram referências
SQL cifradas de 716 bytes, sem aumentar o timeout. Workflow em 667,63 s, incluindo
310,30 s de render; essa medição isolada não define tempo comercial de entrega.
Worker próprio encerrado. Sem migração, limpeza, retry pago ou CI completo.
[Plano da nova rodada](../evals/plano-comparacao-criativa-integrada-2026-11-09.md).
Avaliação humana recebida: B ficou um pouco melhor, mas continua muito aquém dos
motion graphics e exemplos das bibliotecas esperados. O nível criativo pretendido
não foi atingido; não há aprovação de qualidade comercial. Áudio e outras possíveis
regressões não foram avaliados explicitamente na resposta. Os quatro checks `met`
do modelo não equivalem ao patamar criativo desejado. A rodada usou calibrações
textuais, sem comparar visualmente com as referências. Próxima necessidade:
definir uma referência concreta e calibrar geração/crítica contra seu acabamento,
preservando diversidade; escopo e orçamento de nova execução ainda não definidos.

Referência concreta recebida: vídeo de Felipe Borges, analisado visualmente desde
o início por sequências de quadros. [Análise e trechos](../evals/referencia-motion-youtube-fqaEZqPzKZs-2026-11-09.md).
Os exemplos usam cenas gráficas, interfaces, diagramas e composição em camadas.
A referência esclarece o alvo, mas não conclui a qualidade do produto. Próximo
recorte proposto: enriquecer o planejamento de cenas e calibrar a crítica visual;
cortes e áudio alinhado exigem ampliação explícita da integração. Sem nova API paga.

O [Reel específico enviado depois](../evals/referencia-reel-Db9axeiOotS-2026-11-09.md) foi baixado e
inspecionado por sequências de quadros. Ele prioriza hierarquia, revelação
progressiva, estados e alternância de composição. Recorte de pessoa e imagens
geradas não são pré-requisitos dessa próxima prova. Eventos ligados à fala
exigem alinhamento; em peças sem fala, usar tempos do roteiro. Sem nova geração.

Quatro Shorts adicionais foram analisados, incluindo legendas do tutorial de
cinco passos. [Plano consolidado de evolução](../design/evolucao-qualidade-motion-referencias-2026-11-09.md).
Cálculo determinístico e render quadro a quadro já existem. A próxima evolução
proposta concentra direção visual/quadros-chave, comportamento dos elementos,
materiais próprios e crítica comparativa. Sem migração de executor ou exigência
automática de 60 fps. Nenhuma nova geração paga ou mudança de runtime.
Esclarecimento do titular: as referências orientam qualidade do movimento; kit
visual, fontes, cores e logo continuam sendo os do negócio. A sequência proposta
é contrato de movimento → recursos determinísticos → crítica temporal → prova
integrada; primeira prévia possível após as duas primeiras fatias, sem biblioteca
completa. Criticar movimento não exige parecer visualmente com a marca da referência.




Contrato para clientes reais e aceite criativo desta peça permanecem pendentes.
Esta fatia usa a gravação inteira e seu áudio reencodado; não acrescenta
transcrição, legendas alinhadas ou seleção de música. Quadros não comprovam
movimento integral ou escuta.
[Contrato da integração](../design/integracao-reel-2026-11-09.md).

**Etapa 3 concluída no recorte demonstrado:** legibilidade do 1c e preferência
humana por Giz B (“B ficou melhor.”). Giz é refinamento com feedback/referência
adicionais; não prova ganho universal de autocrítica ou economia. Artefatos,
feedback e custos históricos permanecem separados no [registro](../evals/motion-registro-de-validacao.md).

**Etapa 5 ainda não implementada.** O escopo autorizado anteriormente inclui
o ciclo de imagem feed/story, seguido de story em vídeo e carrossel animado.
A sequência vigente termina primeiro os três pontos do Reel, um por comando. O
[desenho de imagens](../design/ciclo-revisao-imagens-2026-11-09.md) prevê inspeção do JPEG final antes da entrega,
correção condicional e preservação de versões; planejamento não é entrega.
A [matriz](../design/v0-motion-etapa-0-formatos-e-casos.md) registra o reuso e as lacunas por formato.

WhatsApp (6) e piloto/operação comercial (7) continuam posteriores. Piloto de
autoatendimento com cobrança, ainda sem participantes reais; usar os quatro
casos fictícios. Preço/franquias dependem de custo por peça aceita. Publicação
automática no Instagram permanece posterior. Dúvidas de produto serão tratadas
em entrevista; manter o foco nas fatias autorizadas.

## Histórico da retomada — 08–09/11/2026, antes da preferência humana por Giz

Os registros abaixo preservam a sequência de preparo, execução e validação.
Pendências de avaliação humana descritas nessa sequência eram o estado de cada
momento; a conclusão vigente e os próximos trabalhos são os do bloco acima.

O titular confirmou o texto do [roteiro de sete etapas](../design/execucao-ate-etapa-7-2026-11-07.md).
A prioridade é alinhar documentos, corrigir a checagem de tipos e restaurar as
ferramentas locais de mídia, concluir a prova comparativa (3), integrar o Reel
após comparação e revisão humana (4) e avançar aos outros formatos (5). As
etapas de jornada (6) e preparação do piloto/comercial (7) permanecem no roteiro.
Entrevistas tratarão definições faltantes; preparar ou testar não encerra os gates.

A entrevista já definiu autoatendimento com cobrança, sem participantes reais
escolhidos. Os exemplos de cafeteria, loja física Ponto do Dog, delivery Dog em
Casa e manicure Estúdio da Luma orientam validação sintética. Valores de plano,
franquias e limites comerciais dependem da medição. Instagram permanece depois
da geração/revisão/download; WhatsApp oficial é necessário para a jornada real.

A continuação independente `4338880a-10f2-48a7-96cd-54138f87dbdd` terminou em
`completed_partial_human_pending`: Dog/Luma receberam críticas v2 `adequate`,
sem achados ou correções; Intensa e sua reserva incerta continuam bloqueadas.
Duas novas chamadas somam US$ 0,175165 estimados. Acumulado de Intensa/Dog/Luma: seis
tentativas, US$ 0,427215 conhecidos, custo da tentativa anterior incerta ainda
desconhecido e US$ 1,50 em reservas. O teto de US$ 6,75 não foi esgotado.
[Resultado e relatório](../evals/ensaio-ciclo-revisao-motion-2026-11-06.md).

A tipagem foi corrigida e as ferramentas locais de mídia recuperadas com
hashes conferidos. Passaram 107 testes Python de motion e o preflight dos três
casos. O relatório foi corrigido para caminhos longos e validado a 390/1440 px,
nos modos cego/identificado, com três players e sem overflow, erro JavaScript
ou rede externa; vídeos/críticas/ledger intactos. Após reproduzir o timeout e
ajustar a preparação dos testes de concorrência, o módulo passou em quatro
testes (93,61 s). As falhas posteriores de CI são históricas; a execução final
de 09/11 passou, conforme abaixo. No
recorte `app`/`migrations`, apenas `test_destination_lock_proof.py` mudou desde
a tentativa anterior desta retomada; produção e migrations intactas. O CI de
06/11 registra a árvore daquela execução.
A comparação real do 1c abaixo teve a legibilidade reconhecida pelo titular,
sem aprovação criativa global. Etapa 3, ganho geral e integração permanecem abertos.

Em entrevista, o titular escolheu testar a correção do [Reel histórico 1c](../evals/plano-revisao-reel-1c-2026-11-08.md)
com defeito conhecido. O pacote offline de 69 arquivos foi concluído e preserva
dez normalizações históricas. A ponte declarativa foi implementada; passaram
146 testes locais (57 da orquestração e 89 da ponte), Ruff e mypy estrito.
Não transforma a origem em resposta HTML/JS. A primeira qualificação do run
`3a52c376-e8ea-4bea-b997-94ba59c628de` falhou no parsing de metadados FFprobe 4.4.8;
a tentativa foi preservada e não houve API. Após correção estrita, o preflight
real confirmou MP4 arquivado idêntico ao original e remux preservando 526 pacotes
AAC, PCM e tempos, mais 336 quadros RGB24 e tempos. A segunda qualificação
completa passou depois, recompilando/renderizando a direção original e
confirmando quadros, tempos e áudio. A prova e seu hash foram preservados.

O titular autorizou em entrevista até três chamadas/US$ 1,25 e o envio à OpenAI.
O registro `authorization.json` vincula decisão, plano, primeiro pedido e
qualificação. A execução paga do 1c foi concluída; resultado, custos e comparação
estão abaixo; o titular confirmou legibilidade, sem aprovação global. A falha de
unidade tipográfica já foi corrigida na geração atual; esta prova limitada não
demonstra por si só ganho criativo geral ou economia da revisão em todos os
pedidos. Prova e julgamento humano (3) precedem integração do Reel (4) e demais
formatos (5); qualificação técnica não equivale a ganho criativo ou integração.

O [ensaio 1c concluído](../evals/ensaio-revisao-reel-1c-2026-11-08.md) produziu
original e v1 comparáveis. A crítica inicial encontrou uma falha `major` de
legibilidade; a correção ampliou títulos/legendas e foi renderizada sem ajuste
manual. A crítica final retornou `adequate`, sem achados, e preferiu v1; seis
critérios passaram e áudio ficou `uncertain`. AAC/PCM/tempos foram preservados.
O executor registra `completed_human_pending`. Depois, o titular confirmou:
“o B tem os titulos e legendas bem melhor”, mas questionou se era story e por
que faltava motion. A melhora de legibilidade foi reconhecida; não há aceite
global, de áudio ou de motion. O pedido original era `reel` com cortes,
transições, motion e legendas; a entrada era ilustrativa/licenciada com voz
sintética, não gravação de cliente real.

O 1c tem pequenos ajustes de enquadramento/fades. A prova reparou tipografia,
mas não qualificou acabamento criativo: presença de animação não comprova
adequação ao briefing. Intensa/Dog/Luma continuam as referências; 1c não vira
padrão. O relatório inicial passou em 390/1440 px, dois modos e oito reproduções
mutadas; isso comprova apresentação, não escuta humana ou qualidade criativa.

A apresentação foi corrigida depois: agora exibe `limitations[]` com escape de
HTML, explica `adequate` como ausência de outro defeito acionável nas evidências
e distingue parada automática de aceite criativo. Passaram 15 testes do
relatório, Ruff e mypy. Somente o HTML foi regenerado, preservando original,
código e hashes; vídeos, críticas e summary permanecem intactos. O QA dirigido
do novo HTML passou em 390/1440 px nos dois modos, com limites visíveis apenas
no identificado, dois players, sete links e nenhum overflow, erro JavaScript
ou rede externa. O QA anterior foi conservado. Sem API ou custo adicional.

Separar movimento observado de atendimento criativo pertence ao próximo
contrato de avaliação do Giz, agora implementado e testado, com calibração
criativa ainda pendente. A correção de apresentação do relatório 1c não
reclassifica as críticas históricas nem qualifica a criatividade por si só.

O titular respondeu **“Comprovar melhora do motion primeiro (recomendado)”**.
A etapa 3 exige prova criativa antes da integração. O candidato em análise é
Giz (`15adf19d`, lote `e2bbd3aa`), anteriormente avaliado abaixo de Intensa.
A auditoria não encontrou violação inequívoca do briefing original: motion e
desenho existem; pedidos de tema e janela contínua vieram no feedback posterior.
A próxima prova será de refinamento guiado por feedback/contexto adicional
declarado, sem atribuí-lo à descoberta de um erro do pedido inicial. O
[plano do Giz](../evals/plano-refinamento-motion-giz-2026-11-08.md) e o pacote privado
foram concluídos: 70 arquivos (68 inventariados mais manifesto/digest), com
contexto original separado do feedback e das referências novas. O percurso
proposto tem até duas chamadas: refinamento pelo feedback conhecido e avaliação
comparativa; não repete esse feedback em uma crítica paga inicial.

O protótipo privado e o contrato estão implementados: confrontam
`theme_change`, `window_transformation` e `narrative_role`, separando movimento
observado de atendimento criativo. Passaram 160 testes de Giz/contratos/relatório/
legado e 66 declarativos; os caminhos genéricos não podem contornar as guardas
próprias de Giz/1c. `make types` passou a cobrir oito módulos do laboratório.

O replay real do run `1c758136-7530-43d8-96b7-39e4b0e44888` passou: MP4 bruto
byte a byte igual ao original e remux com 336 quadros RGB24/tempos e AAC/PCM/
tempos iguais. Código qualificado preservado em 14 arquivos. A equivalência do
baseline não demonstra ganho criativo. Depois, B passou nas inspeções locais de
código/artefato e preservação de 176 pacotes AAC, tempos e PCM. HTML, dois avisos
MIT, textos, assets e fontes foram conferidos; não houve reparo visual manual.
HTML/JS livre não garante invariância geral de fatos/textos por schema.

O teto de até duas chamadas/US$ 1,25 foi autorizado em **09/11/2026**, com
registro vinculado ao plano, qualificação e pedido. O ensaio Giz concluiu as
duas chamadas HTTP 200, sem retry ou operação incerta, e terminou
`completed_human_pending`. A crítica preferiu v1: três requisitos `met`, seis
critérios `pass`, áudio `uncertain` e nenhum achado. As amostras mostram mudança
verde → creme → verde e janela em arco com estados intermediários, preservando
a linguagem Giz. Isso ainda não é aceite humano de motion ou narrativa.

O [resultado Giz](../evals/ensaio-refinamento-motion-giz-2026-11-09.md) registra
US$ 0,6482575 estimados incrementais e US$ 0,8686550 de subtotal de APIs com o
histórico. Comprometimento US$ 1,0138475, dentro de US$ 1,25; a comparação
excedeu sua reserva em US$ 0,0138475. Subtotal medido de 483,872 s exclui preparo,
qualificação, inspeções e intervalos. Não são fatura, COGS ou custo por peça aceita.
QA do relatório aprovado em 390/1440 px e dois modos, com oito reproduções
mutadas completas, links válidos e 248 arquivos preservados. Comparação aberta
no navegador e entrevista humana enviada com link; resposta/aceite pendentes.
O ganho avaliado é refinamento com feedback e referência posteriores, sem atribuí-lo à
autocrítica do briefing original ou generalizar benefício da revisão.

A [validação técnica de 09/11](../../.local/ci-20261108/ci-final-result.json)
foi concluída: `make ci` terminou com exit 0, 5.043 testes aprovados e dois
inicialmente pulados por FFmpeg/FFprobe ausentes do PATH. Esses mesmos dois
testes reais de MP4 passaram separadamente em 4,97 s após corrigir somente o
PATH privado, sem alterar testes ou produção. Cobertura da aplicação: 100% das
17.229 linhas e dos 4.726 branches. Passaram também 363 testes Python motion,
três Node de áudio, 62 Node do renderer (100% linhas/branches/funções),
Ruff/formatação e mypy de 272 módulos app mais oito scripts.

Os 735 arquivos app/migrations e 29 do laboratório permaneceram iguais aos
snapshots. As 69 amostras de relógio não indicaram repouso, com diferença total
de −0,048 s em 1.114,6 s. As falhas anteriores de recibo/token e seus logs estão
preservados como histórico, sem credenciais; não são o estado da execução final.
O PostgreSQL descartável do CI usou `fsync`, `synchronous_commit` e
`full_page_writes` desligados: esta prova não qualifica perda de energia ou
recuperação do servidor e não altera requisitos de produção. A entrevista
humana da comparação Giz continua pendente; nenhuma integração foi iniciada.

No ensaio 1c, três chamadas HTTP 200, sem retry ou incerteza: **US$ 0,527685 estimados novos**,
US$ 1,25 reservados. Subtotal histórico de APIs US$ 0,106892; subtotal com revisão
US$ 0,634577, sem fatura ou COGS completo. Chamadas somaram 154,561 s; render e
evidências, 151,928 s; subtotal medido 306,489 s exclui setup/preflight/intervalos.
A prova e o feedback sustentam reparação desse defeito histórico, não ganho
criativo ou retorno financeiro geral. O CI foi concluído; a avaliação humana
da prova criativa precede integração do Reel (4) e demais formatos (5). A etapa 3
não recebeu aprovação global; a autorização posterior de Giz não altera esses
resultados ou o aceite limitado do 1c.

## Histórico: início do ciclo de revisão de Reel — 06/11/2026

O titular priorizou o ensaio em Python/API de gerar, renderizar, inspecionar,
corrigir e renderizar novamente. O braço revisado parte da mesma composição
histórica do baseline; são até duas correções, crítica por versão e escolha
humana explícita. [Desenho](../design/ciclo-revisao-motion-2026-11-06.md) e
[plano](../evals/plano-ciclo-revisao-motion-2026-11-06.md) descrevem o
protótipo privado implementado, sem comparação concluída. O titular autorizou até US$ 6,75
em reservas, até 15 chamadas e envio de quadros/contexto/código à OpenAI para
Intensa/Dog/Luma; áudio técnico mantém a mixagem e exige escuta humana. O clipe pessoal
continua aguardando avaliação. Skills e componentes permitidos são fontes de
estudo; não se prevê servidor Claude Code ou agentes hospedados. A comparação
precede integração em produto; postagem segue fase posterior à geração.
Blocos datados seguintes descrevem decisões e estados de seus momentos.

Primeira execução real: três críticas `adequate`, sem correções, estimativa
US$ 0,2520500 e reservas US$ 0,75. A auditoria constatou que o contexto criativo
do crítico estava incompleto; isso prova execução, não qualidade ou ganho. A
[continuação](../evals/plano-ciclo-revisao-motion-2026-11-06.md) com contexto
corrigido parou na primeira crítica com resultado incerto, sem resposta ou
refações. Total: quatro chamadas, US$ 0,2520500 conhecidos de estimativa,
custo da última desconhecido e US$ 1,00 em reservas. Sem retry; A/B pendente.
[Resultado parcial e limites](../evals/ensaio-ciclo-revisao-motion-2026-11-06.md).
`make ci` aprovado na árvore de 06/11: 5.045 testes da aplicação, cobertura
100% de linhas e branches; 91 testes Python de motion, três Node de áudio e 62
Node do renderer, Ruff e mypy. PostgreSQL `_test` e Temporal descartáveis,
`TZ=UTC`; [detalhes](../CHANGELOG.md). Não encerra comparação criativa.

## Histórico: caso pessoal musical como foco único — 06/11/2026

Titular solicitou editar sua gravação de 46,5s com formas/realismo ligados à letra.
Preparação local concluída, fonte intacta, 12 quadros e áudio separados; teste
técnico de modo pessoal explícito passou. Sem envio real ou gasto novo até
autorização específica. [Plano de três chamadas](../evals/plano-clipe-musical-pessoal-2026-11-06.md),
reserva adicional US$ 1,60. Posteriormente titular autorizou verba e envio pessoal;
ASR recebido, estimativa US$ 0,0047, com conferência parcial pelas legendas
incorporadas e originais preservados. MP4 de 46,5s e comparação entregues;
estimativa total US$ 0,51148, sem retry ou ajuste visual manual. Áudio original
identificado por payload/PCM/tempos; qualidade humana pendente.
[Resultado](../evals/ensaio-clipe-musical-pessoal-2026-11-06.md).
Demais frentes ficam adiadas durante esta peça.

## Preparação do step 1: Dog/Luma — 06/11/2026

Titular solicitou executar outros negócios e confirmou marca/experiência sem
preço. Cenários incluem gravações ilustrativas, kit/skill/fontes concretos e
metas de contraste e transformação do vídeo, no mesmo renderer qualificado.
Revisão dos termos Pexels não identificou vedação concreta à inferência pontual;
ausência de autorização IA específica foi antes tratada com cautela excessiva.
Proveniência, limites e registros anteriores preservados. [Plano](../evals/plano-motion-outros-negocios-2026-11-06.md).
Preflight passou; titular autorizou as duas chamadas/envio dos pacotes, até
US$ 1,50 adicionais. Dois MP4s/comparação entregues, estimativa US$ 0,5906725,
sem retry pago. Dog traduziu IDs de áudio e renderizou offline, sem alteração
visual; falha original preservada. [Resultado](../evals/ensaio-motion-outros-negocios-2026-11-06.md).
Titular gostou bastante e confirmou o nível da Intensa nos dois casos curtos;
mesma música foi apontada como possível problema. Geração/avaliação criativa
deste step concluídas, com diversidade musical pendente: só havia uma trilha
obrigatória. Próximos testes devem oferecer alternativas licenciadas adequadas,
sem inferir validação de story/carrossel, durações longas ou integração.
Titular confirmou variedade musical com escolha automática por negócio/peça e
repetição permitida para continuidade de série/campanha. Seleção entre opções
e registro do contexto ainda são pendências; decisão não gera nova peça/gasto.

## Validar outras linguagens antes da integração — 06/11/2026

Reel intenso recebeu feedback positivo: “muito legal. melhorou bastante.”
Próxima sequência solicitada: diversidade no mesmo material, outros negócios
fictícios, story, carrossel e transferência do caminho qualificado ao produto.
Vozes mais naturais serão comparação separada com orçamento próprio. Instagram
permanece posterior; intensidade exploratória não vira regra universal.
[Registro e pendências](../evals/motion-registro-de-validacao.md).

Preparados três estilos com fichas e código MIT concretos; CLI de lote gera
comparação de cinco vídeos sem banco/WhatsApp. Preflight e 40 testes Python/três
Node passaram; CI integral não repetido. Após preparação, titular autorizou as
três chamadas/envio do pacote, até US$ 2,25 adicionais: duas peças concluídas e
Papel incerto sem resposta/custo salvos, sem retry. Intensa preferida; Cartaz
bem avaliado; Giz menos convincente por tema/enquadramento. Próximo passo:
outros negócios, depois story/carrossel. [Resultado](../evals/ensaio-motion-diversidade-2026-11-06.md).
Para Dog em Casa/Luma o titular escolheu
vídeos ilustrativos licenciados; verificação de direitos de envio a provedor
continua anterior à rodada desses negócios. A feature segue incompleta.

## Intensidade exploratória entregue — 06/11/2026

Disponíveis [versão intensa e comparação](../evals/ensaio-motion-intenso-2026-11-06.md).
Uma chamada autorizada, estimativa US$ 0,3086025; código executado como recebido,
inversões de tema e mecanismos adicionais conferidos por código/quadros.
Ganho criativo e intensidade preferida aguardam o titular; não é padrão universal
nem conclusão de integração, demais formatos ou publicação.

## Próxima prova criativa: versão “exagerada” — 06/11/2026

O titular gostou um pouco mais da rodada `276486e3`, ainda preferindo o v2,
e pediu motion mais robusta. O [plano de intensidade](../evals/plano-motion-intenso-2026-11-06.md)
explora esse pedido e o feedback sobre verde/creme, letras invertidas e ponto.
Não é rejeição da peça nem decisão de aplicar a mesma linguagem a todo negócio.
O aceite será sobre o resultado final; orçamento anterior não se renova e a
integração da feature continua fora desta prova criativa.

## Comparação da nova peça com o piso — 06/11/2026

Disponíveis o [MP4 e relatório comparativo](../evals/ensaio-motion-biblioteca-2026-11-06.md),
com a skill própria e adaptações reais de três fontes da biblioteca. Uma chamada,
estimativa US$ 0,28714; código executado sem ajuste manual. A revisão criativa
final e a integração do produto permanecem pendentes; não houve ampliação
automática do orçamento ou geração dos demais formatos.

## Evolução autoral acima do piso — 06/11/2026

V2 é mínimo aceito, não template, por esclarecimento do titular. O próximo
[ensaio preparado](../evals/plano-motion-biblioteca-2026-11-06.md) inclui skill
própria de Reel, código selecionado da biblioteca e relatório com três vídeos.
Escolha de linguagem permanece automática. 27 testes offline do CLI passaram;
o titular autorizou uma chamada/envio do pacote, até US$ 0,75 adicionais, e a
geração foi iniciada. Resultado e avaliação criativa permanecem pendentes.

## Ganho criativo esperado ainda não demonstrado — 06/11/2026

A peça nova não foi considerada ruim, mas o titular mantém o v2 como preferido:
janela horizontal/vertical contínua, formas e pontos, transições suaves.
O diagnóstico identificou escolha de direção e uso parcial das fontes/skill,
sem as skills próprias por formato no último CLI. Preservar essa preferência
antes de variar mecanismos. [Registro](../evals/ensaio-motion-comando-2026-11-06.md).
Sem chamada paga ou alteração no renderer nesta análise.

## Peça nova disponível para avaliação final — 06/11/2026

O comando concluiu a geração após reposição de saldo/retry autorizado: Reel
11,2 s com vídeo/áudio, sem alterar HTML/JS recebidos. Há componentes reais de
motion adaptados do motor `cartaz-risografia`. [Peça e trace](../evals/ensaio-motion-comando-2026-11-06.md).
Gasto desta geração estimado em US$ 0,3114475, não fatura. A validação técnica
não encerra o aceite criativo, os demais formatos ou a integração do produto.

## Comando pago sem saída por saldo esgotado — 06/11/2026

A tentativa de Reel novo recebeu HTTP 429 `credit_balance_exhausted`, sem
composição ou uso informado. Resposta/reserva preservadas; nenhum MP4 novo ou
retry. Qualidade criativa e nova geração permanecem pendentes.
[Evidências e continuação](../evals/ensaio-motion-comando-2026-11-06.md).

## Ensaio rápido sem portões intermediários — 06/11/2026

O titular escolheu revisão somente do MP4 final. O [comando local](../evals/como-executar-ensaio-motion.md)
concentra preflight, geração, render e comparação, com orçamento explícito e
sem refação automática. O cenário inicial permanece fictício, com fontes/kit
congelados e Jev/transcrição reaproveitados de forma identificada. Provas offline
do comando não equivalem a nova geração ou aceite criativo. A integração e os
critérios completos de saída da v0 continuam abertos.

## Histórico: ensaio criativo fiel — 06/11/2026

Executar a [retomada de qualidade](../evals/plano-retomada-qualidade-motion-2026-11-06.md)
com um Reel primeiro, mesma mídia/kit e v2 como patamar mínimo. Usar referência
concreta e componentes reais selecionados dos três projetos preservados, com
direção automática coerente. Registrar bruto e intervenções antes de avaliar a
peça; só depois ampliar a prova para story/carrossel. Integrações WhatsApp/Instagram
ficam fora deste ensaio. O titular autorizou duas chamadas até US$ 1,50 adicionais
e o envio do pacote local. A primeira concluiu; cinco cards estão capturados e
aguardam aceite. A segunda chamada depende desse aceite; nenhum vídeo novo foi
gerado. Custo e traces estão no plano da retomada.
As demais fatias e critérios de saída da v0 continuam pendentes.

## Reprovação criativa da rodada 1c — 06/11/2026

Reel/story/carrossel foram rejeitados pelo titular por simplicidade e falta de
motion perceptível. A referência continua sendo o Reel v2 anterior; a direção
concreta dele não foi levada aos novos inputs. Priorizar o diagnóstico do caminho
criativo e da fidelidade do executor. Os rascunhos seguintes de integração não
foram aplicados; o CI da clareza do contrato foi interrompido a pedido do titular,
sem resultado final, e continua independente da avaliação de qualidade.

## Rodada 1c encerrada; revisão das peças em andamento — 06/11/2026

Os três formatos foram reconhecidos pelo Jev e a transcrição do Reel corresponde
às palavras da fixture. A direção do Reel exigiu correções locais de contrato
e depois ajuste explícito de legibilidade; o MP4 resultante está pronto para
avaliação, sem aceite criativo presumido. [Arquivos e trace](../evals/ensaio-motion-v0-rodada-1c-2026-11-06.md).
O titular autorizou explicitamente a retomada de story/carrossel após o bloqueio
da revisão automática causado pela rejeição do Reel. As sete operações foram
executadas sem retry pago; as três direções foram rejeitadas localmente e têm
derivados separados para montagem. Estimativa global US$ 0,263073, reservas
US$ 1,55 no teto US$ 1,60. Não há nova chamada autorizada nessa rodada.
O app ficou preservado durante os efeitos. Depois, descrições de unidades,
keyframes e áudio foram incorporadas ao contrato/builder, sem afrouxar validação.
O CI dessa fatia foi interrompido a pedido do titular (saída 143), sem resultado
final; o baseline aprovado de 5.044 Python/62 Node é da fatia anterior.
A jornada e os critérios completos de saída
continuam pendentes.

## Correção após primeiro efeito da rodada 1b — 05/11/2026

A interpretação real reconheceu Reel, mas o limiar de seleção de item bloqueou
uma entrada sem candidatos. A rodada foi interrompida após uma chamada, com
reserva preservada, sem transcrição/direção. [Evidência e custo](../evals/ensaio-motion-v0-rodada-1b-2026-11-05.md).
O adapter agora omite a pergunta de item somente nessa ausência estrutural;
55 testes dirigidos/100% passaram. Na retomada de 06/11/2026, conferido CI
integral aprovado: 5.044 testes Python e 62 Node, sem pulados e com cobertura
de 100%. A admissão
de conteúdo sem item, com origem/material/fatos verificados, segue pendente.
Nenhuma nova chamada está autorizada como refação automática.

## Terceiro bloco: contexto, fichas e plano de áudio — 05/11/2026

Concluídos os módulos puros de catálogo próprio, entrada para direção e plano
de áudio. O catálogo fornece as três fichas verificadas; a escolha automática
por modelo continua pendente. O builder preserva proveniência e separa
observações de hipóteses, sem ler mídia, enviar rede ou autorizar acesso.
O plano de áudio mantém trims/ganhos/fades e evidência de fala, sem alegar
fidelidade semântica. Protótipos locais executaram cena e mixagem sintéticas,
com inspeção de frames e amostras PCM; não são renderer de produção nem ensaio
criativo. O terceiro CI integral passou: 5.042 testes Python e 62 Node, sem
pulados e com cobertura de 100%. Não houve novas chamadas pagas.

A preparação da [rodada 1b](../evals/plano-motion-v0-rodada-1b-2026-11-05.md)
usou os contratos e fichas reais, com sete operações propostas. O executor
privado gerou cinco MP4s sintéticos antes da autorização. A chamada real e a
interrupção posterior estão registradas no início deste documento. Mocks e
provas sintéticas não substituem os efeitos reais; a jornada de produto continua
pendente.

## Segundo bloco: compilador parametrizado — 05/11/2026

O primeiro CI fechou com 4.913 testes aprovados, 2 casos dependentes de binários
pulados e 100% de linhas/ramos; os casos reais de mídia passaram no recorte
dirigido. Depois, contrato v2 e serviço de composição foram conectados ao
compilador próprio. Testes dirigidos: 148 Python/100% e 62 Node/100% de linhas,
ramos e funções. A prova entre linguagens compila Reel, story e três páginas.
O titular confirmou carrossel 4:5 e aprovou avançar com a base WAAPI do ensaio.
CI integral do segundo bloco passou com FFmpeg/FFprobe no PATH: 4.987 testes
Python sem pulados e 62 Node, com cobertura integral de linhas/ramos e funções
Node.
Ainda faltam driver/áudio, seleção automática de estilos, verificação de arquivos
e snapshots no negócio, persistência/Temporal e revisão sem postagem. Nenhum
fluxo foi habilitado nem houve chamada paga por esse código.

## Implementação em andamento — 05/11/2026

Primeiras fatias: snapshots das três skills com loader isolado, contrato puro
de direção, elegibilidade explícita no adapter Jev e inspeção/extração de áudio
local. Contrato valida gravação, páginas/duração, cortes na fonte, timeline,
camadas, motion/transições e áudio/legendas opcionais; não comprova fidelidade
semântica dos cortes, alinhamento de fala ou direitos. A inspeção usa metadados,
limita bytes/tempo/saída e não recorta automaticamente gravação excedente.
A amostra original de `claude-video` tem licenças, origem, hashes e verificador
de arquivo/restauração. Dependências e backup independente ainda pendentes.
O CI do primeiro bloco passou, conforme registro acima. Formatos de motion
ainda não estão habilitados na jornada e não houve chamada paga.

O [Reel adaptado com WAAPI](../evals/ensaio-reel-waapi-2026-11-05.md) preserva
a direção geral do v2 e passou nas verificações técnicas; o titular confirmou
avançar com a base técnica desse caso. Não é compilador ou renderer integrado. A revisão final
precisa de [aceite independente de postagem](../design/revisao-peca-sem-postagem-2026-11-05.md),
pois a operação legada agenda publicação simulada. Nenhum código web foi alterado.

## Escopo confirmado por entrevista — 05/11/2026

A edição recebe uma gravação do cliente por pedido, com até 60 segundos de
material bruto e até 60 segundos no vídeo final. A prioridade revisada é concluir
geração, prévia, ajustes, aprovação da peça e download de imagens feed/story,
Reel, story em vídeo e carrossel com motion. Viabilidade e integração de postagem
no Instagram foram adiadas para a fase seguinte; conta Meta e publicação real
não bloqueiam a conclusão da geração. C11 segue vigente para a postagem futura.
Carrossel tem 3–5 páginas, com 5–8 segundos por MP4. Ajustar uma página preserva
as demais; mudanças nelas exigem confirmação prévia e a nova sequência requer
aprovação própria. O estilo é escolhido a cada pedido conforme objetivo, material
e referências, preservando o kit; guardar snapshots por peça, sem preferência
fixa por negócio. Integração e homologação seguem pendentes. O titular confirmou
50 MiB por gravação; excesso de tamanho ou duração pede uma versão menor,
sem cortar automaticamente. Os limites comerciais
seguem medição em P05. Retenção já segue C04/C09, com P03 adiada.

## Primeira fatia da v0 de conteúdo — 05/11/2026

A [matriz de formatos e casos](../design/v0-motion-etapa-0-formatos-e-casos.md)
consolida o ponto de partida para os ensaios; o
[inventário](../design/inventario-claude-video-2026-11-05.md) identifica fontes
e direitos ainda a conferir, sem declarar preservação ou integração. A guarda
de copy recusa padrões específicos da instrução de revisão vazada no ensaio
BL04.3, rejeitando a proposta sem corrigir o texto automaticamente.
No fluxo integral, a tentativa segue `uncertain` e não produz documento público.
Esse controle é limitado; avaliação criativa, novos ensaios e edição audiovisual
integrada permanecem pendentes. Não houve chamada paga nesta fatia.
O CI inicialmente interrompido foi concluído nos blocos registrados acima;
condições do banco efêmero constam no [changelog](../CHANGELOG.md).

A futura integração deve preservar fontes externas e dependências sob controle próprio e provar o runtime sem acesso ao GitHub original; detalhes e estado no [plano](../design/plano-v0-imagens-video-motion-2026-11-05.md#cópias-próprias-e-independência-dos-repositórios-externos).

O plano inclui reaproveitar instruções, fichas, projetos e scripts externos permitidos na integração, em vez de restringi-los a estudo; ver [etapas concretas](../design/plano-v0-imagens-video-motion-2026-11-05.md#integração-concreta-da-claude-video). Amostra e fichas próprias estão disponíveis conforme os blocos acima; a jornada e o empacotamento ainda não estão integrados.

## Plano para concluir a v0 com motion — 05/11/2026

O [plano de integração](../design/plano-v0-imagens-video-motion-2026-11-05.md)
organiza conclusão de imagem, ensaios rápidos, contratos, análise de mídia,
seleção automática de estilo, render seguro, Reel, story, carrossel e jornada
integrada. Não altera o estado das entregas existentes: as novas capacidades e
seus critérios de qualidade da geração permanecem pendentes; postagem fica para
a fase posterior definida pelo titular.

## Ensaio de motion com modelos reais — 05/11/2026

O [ensaio direto](../evals/ensaio-motion-referencia-2026-11-05.md) produziu carrossel e duas direções de Reel, com inputs, prompts, respostas e custos disponíveis; não comprova integração. O Jev não reconheceu os formatos, houve erro de transcrição e o HTML da refação necessitou ajustes. O titular preferiu o Reel v2; avaliação completa de som/movimento e aprovação de publicação permanecem pendentes.

## Proposta de estilos de motion — 05/11/2026

O titular sugeriu uma biblioteca própria de estilos de motion com escolha automática pelo sistema, sem exigir escolha do cliente. Ver [proposta](../design/biblioteca-estilos-motion-2026-11-05.md); integração e avaliação estão pendentes.

A skill externa `claude-video` foi instalada no Codex e sua galeria aberta localmente para estudo, conforme [registro](../design/estudo-claude-video-2026-11-05.md); não é integração do produto.

## Pesquisa adicional de vídeo e motion, 04/11/2026

Em 05/11/2026 o titular esclareceu que o cliente não escolhe imagens do acervo; pode enviar uma imagem e envia o vídeo para edição. Não exigir acervo na edição de vídeo. Áudio pode ser extraído para transcrição, com integração e sincronização ainda pendentes.

Ver [estudo da skill claude-video](../design/estudo-claude-video-2026-11-05.md) e [plano dos ensaios](../evals/plano-hyperframes-2026-11-05.md).

As [prévias locais HyperFrames](../evals/ensaio-hyperframes-2026-11-05.md) foram geradas sem chamadas pagas, com direção do agente e Jev simulado; ainda não comprovam integração, transcrição real ou publicação.

Pesquisa documental dos repositórios indicados resultou em [proposta de ensaio e integração](../design/estudo-hyperframes-motion-design-2026-11-04.md): testar direção audiovisual criada por agente e HyperFrames local; separar a experiência de qualidade da futura integração ao produto. Nenhuma nova chamada paga ou render foi realizado nesta pesquisa.

As primeiras prévias foram rejeitadas por falta de motion, áudio e edição. O [novo ensaio](../evals/ensaio-motion-valido-2026-11-04.md) produziu as peças com rastreabilidade e orçamento próprio; a direção audiovisual é experimental e não demonstra integração do produto. Revisão do titular pendente.

Um vídeo e três páginas animadas foram montados como ensaio local gratuito de direção criativa, sem Jev real ou referências; ainda aguardam avaliação do titular. O [relatório](../evals/ensaio-video-motion-2026-11-04.md) registra fontes, limitações e verificações. Não houve integração de produto ou teste de publicação.

O titular quer estudar skills de terceiros e preparar skills próprias para vídeo gravado no feed/Reel, story em vídeo e carrossel com um MP4 em loop por página. A IA decide a edição criativa e FFmpeg pode executar a montagem. O titular escolheu até 60 segundos por vídeo final e testar vídeo e carrossel separadamente; orçamento e integração seguem em avaliação; as três skills iniciais foram criadas, mas ainda não estão integradas ou avaliadas com peças reais. Detalhes em [estudo](../design/estudo-video-motion-2026-11-04.md).

## Ensaios de qualidade — procedimento vigente

Avaliações criativas futuras usam o [procedimento direto e rápido](../design/ensaios-rapidos-qualidade.md)
solicitado pelo titular: inputs/outputs de mensagem, Jev, editorial e visual;
comparação e revisão das peças, sem criar banco nem montar o produto completo para
esse objetivo. Identidade, orçamento, retenção de resultados incertos e fontes
autorizadas permanecem obrigatórios. O ensaio não comprova integração; testes
de banco, integração e CI seguem exigindo base `_test` exclusiva e roles restritas.
Os preparativos mais antigos abaixo são histórico, não pré-requisito do ensaio.

Os dois pares de feed/story foram gerados no ensaio direto com/sem referências; [relatório e artefatos](../evals/bl043-reference-quality-2026-11-04.md#resultado-do-ensaio-direto--04112026). Uma resposta editorial foi rejeitada e reconciliada; uma nova tentativa com orientação adicional limita a comparação do feed. Revisão humana e correções permanecem pendentes.

O titular esclareceu que a avaliação comparativa deve seguir um ensaio direto e rápido, semelhante aos anteriores, sem executar o sistema completo. A variável continua sendo a inclusão dos padrões nas etapas editorial e visual, com identidades e orçamento duráveis; conferir [plano atualizado](../evals/bl043-reference-quality-2026-11-04.md). Essa evidência não comprova integração de produto.

## BL04.3 — preparação iniciada em 04/11/2026

Registro histórico anterior ao ensaio executado; não reabrir a preparação como
pré-requisito atual nem reutilizar seu orçamento em outra rodada.

O [relatório preliminar](../evals/bl043-reference-quality-2026-11-04.md) inventaria os estados disponíveis, propõe dois pares e explicita fontes, critérios, custos ilustrativos e limites. As duas associações v1 e os nove padrões foram lidos pelo serviço restrito; a verificação individual contra evidências permanece pendente. O produto ainda não oferece controle seguro para retirar apenas padrões: preparar e testar a intervenção sem enfraquecer snapshot ou revalidação antes de qualquer efeito. O titular escolheu dois pares do negócio do piloto, limite de US$ 2 em reservas incluindo refações, aceitando risco de cobrança maior; fará a revisão visual pontual; nenhuma geração, revisão de peças ou refação ocorreu.

## Ajuste da origem de pesquisa — 04/11/2026

A web usa o endereço próprio salvo como única fonte dos campos da origem por
endereço, todos somente para leitura. Sem cadastro, apresenta a orientação para
preencher **Endereço do negócio** e impede salvar essa origem. Mudanças no
cadastro atualizam a exibição e o próximo envio explícito das preferências, sem
salvamento ou consulta automáticos. GPS confirmado, raios e ciclos são preservados.
Indicações de outras regiões seguem pelo @ manual em **Perfis que inspiram seu
negócio**, conforme decisão do titular; não se acrescenta outro endereço de busca.

Critérios de validação: campos não editáveis; cadastro obrigatório para origem por
endereço; valores persistidos prevalecem sobre uma origem antiga; atualização do
cadastro refletida sem salvar automaticamente; GPS e indicação manual preservados.
Testes e validação da interface são registrados no changelog da web.

A mensagem de busca indisponível é controlada por `discovery_available`, vindo da
prontidão operacional da API. As flags locais persistentes de descoberta,
geocodificação e análise seguem desligadas. Credenciais presentes não substituem
a configuração de execução/custos usada temporariamente no piloto. Esse estado
é independente do endereço e do prazo semestral. Este ajuste não ativa chamadas
pagas; o próximo trabalho de qualidade continua sendo BL04.3.

## Referências — gate de fechamento em 04/11/2026

As fatias de descoberta, seleção, análise e projeção na geração estão integradas
localmente. A 0109 foi validada contra a seleção real da 0108 em 22 integrações
PostgreSQL, além de 46 unitários com cobertura integral do guardião. A política
v2 do piloto redistribui os limites por fornecedor dentro dos mesmos US$ 5,
preservando o consumo. A interface passou em 508 testes/100%, TypeScript, build
e navegação em Chromium. O banco local está em 0111 após backups verificados.
O CI conjunto passou: 4.734 testes, 100% de linhas/ramos, Ruff e mypy.
A análise de referência manual do ensaio gerou nove
padrões a partir de onze publicações e quarenta imagens, com estado parcial e
snapshot de geração conferidos. A fórmula de reputação
continua experimental, conforme decisão do titular.

No piloto real, o Google expôs campos opcionais que o parser rejeitava. A
[correção](../design/google-places-address-components.md) foi validada em 160
testes e na nova resposta real de 20 candidatos, com três destaques Jev salvos.
As tentativas anteriores conservaram suas reservas. O banco local foi atualizado
até 0111 após backups verificados; análise e CI concluídos no escopo atual.

A descoberta real publicou dez candidatos com três destaques; o aceite iniciou
o ciclo. O primeiro feed foi coletado com sucesso, mas não gerou padrões pelo
filtro inicial de autoria/formato. O titular resolveu a entrevista: somente
autoria direta, incluindo capa/legenda de vídeos e Reels. O adapter foi atualizado
e passou em 164 unitários/100% e cinco integrações, incluindo ausência de acesso
ao arquivo de vídeo e padrões no snapshot. O CI integral também passou.
O piloto expôs contabilização preliminar do Apify: espera de trinta segundos
validada em 275 testes/100%; revisão auditável de recibos 0111 validada em 38
integrações e 12 unitários/100%. Os onze recibos foram reconciliados no mesmo
piloto de US$ 5, preservando reservas e histórico. O total comprometido após a
análise manual é US$ 0,455502, incluindo holds ainda não liquidados de Google/Jev.
Decisões de conteúdo resolvidas; [evidências](../evals/reference-feature-pilot-2026-11-04.md).

Atualizado em **29/10/2026**, com a primeira imagem real pelo produto concluída
na parte 3 e a priorização de skills de geração antes da avaliação BL04.3.
Estado: **em implementação local**, sem aprovação
comercial. Este é o contrato vigente da fase, junto ao [SDD geral](../SDD.md), à
[trilha BL](BL-brand-library.md#bl04--recuperar-contexto-e-produzir-uma-peça-nova)
e ao [registro de decisões](../DECISIONS.md). A versão anterior foi preservada
[integralmente no histórico](../history/2026-10-28-pre-documentation-reconciliation/phases/BL04-context-and-ai-production.md);
pendências datadas de permissões por fornecedor nesse histórico não são novas
etapas da jornada contratada.

A [análise da jornada WhatsApp e orquestração](../design/arquitetura-jornada-whatsapp.md)
registra o encadeamento atual, as fronteiras entre estados de domínio e Temporal,
as partes simuladas e pontos para discussão futura sobre organização; não altera
o escopo desta fase nem decide uma extração de serviços ou repositórios.

## Qualidade de copy e ação — 30/10/2026

Ensaios diretos em negócios fictícios expuseram bloqueios por notação visual,
identificadores vazados na copy e CTAs que pressupunham interação. A fatia
local corrige a distinção de direção/fatos, valida campos públicos e permite
ao titular informar o canal comercial no contexto versionado. A checagem é
conservadora e não valida o conteúdo semântico ou a imagem final: revisão humana
continua obrigatória. O novo caminho precisa de nova avaliação real controlada;
os ensaios anteriores exigiram ajustes manuais e não provam essa correção.

Foi criado um segundo [kit fictício Ateliê Aurora](../evals/kit-atelier-aurora-v1/README.md), como fixture isolada de QA,
sem inclusão no catálogo nem execução pelo produto. Próximos trabalhos: usá-lo
em ensaio e implementar recomendações para aceite do cliente. Fonte,
disponibilidade de métricas e custos da descoberta
automática ainda precisam ser demonstrados; não inferir acesso do Jev ao Instagram.

Foi entregue a configuração inicial do alcance de referências: a web oferece
raios locais de 5, 20 e 50 km, endereço manual ou ponto confirmado do dispositivo;
raios anteriores de 1–50 km são preservados. Preferências nacionais anteriores
ficam visíveis até substituição explícita, sem nova opção nacional. A origem
manual ainda aguarda geocodificação/confirmação; não há busca automática real
de concorrentes nesta fatia. A preferência permanece no contexto versionado e é
omitida dos prompts editorial e visual. A indicação manual, o snapshot para
briefing/trace e a revisão visual da tela foram implementados localmente; o perfil
indicado não é verificado nem analisado automaticamente.
No serviço, novas alterações só aceitam os três raios locais. Valores legados
iguais ou omitidos são preservados, `null` explícito os remove, e replay e
alterações pendentes já admitidas mantêm compatibilidade.

Palavras do negócio e características gerais foram adicionadas ao contexto
versionado. A interface removeu os formulários de fatos livres e promoções;
fatos legados do contexto não alimentam novas peças e novos snapshots editoriais
ignoram promoções antigas do catálogo. Snapshots antigos mantêm sua política e
registros físicos históricos não foram purgados. O fluxo WhatsApp/Jev de ofertas,
horários, revisões e cálculo de descontos ainda não foi entregue.

## Resultado esperado

Um pedido livre identifica o que divulgar, recupera somente fontes pertinentes
do mesmo negócio e produz uma prévia privada com o kit aplicado. Falta de fonte,
negação ou ambiguidade pede esclarecimento; material hipotético não vira fato.
Revisão da peça e autorização de publicação são ações distintas. WhatsApp real
e publicação oficial continuam dependentes de homologação Meta.

## Contrato vigente

- **IA integra o serviço.** O cliente aceita uma vez em **Plano e acesso**, antes
  do checkout, o uso para texto, imagem, interpretação/Jev e transcrição. Contas
  existentes usam essa mesma jornada. WhatsApp e Informações e preferências não
  oferecem controles individuais de IA, áudio ou fornecedor. O aceite versionado
  por negócio registra versão/hash, ator, data e auditoria; não ativa pagamento,
  provedor ou publicação. Configuração, acesso, plano, orçamento e direitos das
  fontes permanecem verificações internas.
- **Compatibilidade preservada.** Registros e APIs antigos de consentimento não
  são reativados nem reescritos pelo aceite. Após o aceite único, mutações dessas
  permissões são recusadas com `SERVICE_AGREEMENT_MANAGES_PROCESSING`. Retirada
  individual por fornecedor não é uma nova funcionalidade a entregar. A geração
  contratual dos pedidos impede que o aceite reviva trabalho editorial antigo.
  O aceite inicial aguarda efeitos visuais e alterações legadas pendentes.
- **Fontes privadas e versionadas.** Kit confirmado, fatos vigentes, itens ativos,
  direitos, hashes e proveniência acompanham o briefing. Correspondência lexical
  identifica candidatos; não confirma preço, produto, oferta ou interpretação.
  Nomes com alegações comerciais exigem fato confirmado adicional. Enviar apenas
  fotos pertinentes, com no máximo uma referência do kit quando necessária.
- **WhatsApp preservado; acervo editável.** Envios associados de texto, foto,
  áudio e vídeo permanecem sem prazo automático e sem exclusão pelo histórico;
  migration `0058` aplicada localmente. Fotos desatualizadas do acervo podem ser
  removidas. Preservar envios não implementa memória pesquisável, cadastro de
  produto ou skill automática. Eventos técnicos não atribuídos e uploads órfãos
  continuam sujeitos a limpeza; objetos já apagados não são recuperáveis.
- **Troca de número não interrompe a criação.** Material já associado continua
  no mesmo negócio. Na entrega simulada, a ausência de canal adia o envio; após
  vínculo verificado, o destino é o número ativo novo. A origem histórica não
  fixa o destinatário. Há um número ativo por negócio na versão inicial.
- **Plano vencido e prévias — C08/C09 entregues no recorte local.** A criação
  `visual_fake` ou `visual_ai` admitida tem prova durável para concluir após o vencimento
  financeiro e permitir revisão privada. Novas criações e publicação continuam
  exigindo plano vigente. Bloqueio financeiro explícito, revogação de patrocínio
  e perda de identidade/membership não são vencimento. A exceção de conclusão
  ainda não cobre o renderer local legado. Prévias concluídas e proveniência
  são conservadas sem limpeza automática por prazo; tentativas visuais iniciadas
  sem resultado resolvido também são preservadas. `expires_at` continua sendo
  janela de criação/aprovação. URL assinada curta, validade factual e aprovação
  permanecem conceitos separados da preservação, sem atualização implícita de fatos.
  A revisão de resultados concluídos não depende de manter o modo de execução ativo.
- **Alterações aguardam trabalhos admitidos.** Solicitações de mudança de fonte
  bloqueiam novas admissões e cancelam a fila não iniciada. Trabalhos já admitidos
  terminam antes da aplicação da mudança. A prévia concluída permanece para
  revisão, identificada como anterior à alteração; direitos e publicação seguem
  suas verificações. A cobertura atual dessa coordenação é parcial, abaixo.

## BL04.1 — interpretação e contexto: implementado e limites

O worker pode usar **Jev**, opcionalmente em desenvolvimento/teste, desligado por
padrão. A interpretação usa o aceite único; não pede consentimento TypeSafe
separado. Uma operação durável reserva orçamento por tenant/dia, revalida ator,
origem e snapshot e não repete submissão incerta. Recusa de orçamento anterior
à submissão pode aguardar no workflow em intervalos de uma hora, por até sete
dias, com nova verificação no ledger e revalidação. Estados incertos antigos
não são reclassificados como recusa de orçamento.

A configuração exige `TYPESAFE_API_KEY`,
`MEU_BRACO_DIREITO_INTENT_AI_MODE=jev`, chave de criptografia e teto positivo
`MEU_BRACO_DIREITO_INTENT_AI_DAILY_BUDGET_USD_MICROS`. Configurar não homologa
produção nem autoriza um novo ensaio pago. O teto é conservador por tenant/dia;
a reserva conhecida ainda conserva o máximo reservado após sucesso, sem provar
custo faturado ou capacidade em escala.

O briefing experimental liga intenção, formato, catálogo, kit, fatos e fotos.
O nome do item ativo pode ser fonte factual versionada; preço e oferta não são
inferidos dele. O formato inicial definido para a hipótese de R$ 99 é foto/feed
e story; vídeo e quantidades aguardam decisão comercial. A regra é estática,
ainda sem franquias persistidas por múltiplos planos.

A pergunta local é simulada e genérica. Não há conversa completa, memória de
múltiplas mensagens validada, ferramentas arbitrárias ou pesquisa de concorrentes.
Os caminhos de conversa e conteúdo ainda precisam coordenar uma única resposta
por evento antes do envio real. O [ensaio Jev/OpenAI](../evals/intent-comparison-2026-10-27.md)
identificou erros e saídas incompletas; não é holdout independente nem homologação.

## BL04.2 — prévia simulada: implementado e limites

O modo `fake` captura snapshot privado, lê até uma foto WhatsApp e fotos
pertinentes do item/espaço, confere hashes, normaliza orientação e remove
metadados das cópias. Preserva originais. Usa kit, fato e CTA conferidos;
identidade durável, fence e reserva transacional protegem a tentativa.
O acabamento aplica fontes, nome, tagline, logo autorizado e texto do kit sobre
cena neutra, com marca explícita de **simulação**. Não cria a cena com OpenAI e
não comprova qualidade comercial. O resultado é revalidado no acesso e na revisão.

`MEU_BRACO_DIREITO_VISUAL_AI_MODE=fake` e teto positivo
`MEU_BRACO_DIREITO_VISUAL_AI_MONTHLY_BUDGET_USD_MICROS` habilitam a simulação
somente em desenvolvimento/teste. A reserva fictícia é de um milionésimo de dólar,
liquidada em zero. API/schema preservam esses caminhos; mudar somente a
configuração para `openai` não habilita a execução conectada descrita na parte 2.

Um teste sintético usa Temporal e PostgreSQL reais: material já processado,
contexto/acervo, roteiro, dispatchers, prévia simulada com kit e revisão. Intérprete
e storage são stubs; não chama Meta/OpenAI e não começa no webhook completo.
Os testes iniciais uniam preparo, reserva, adapter e orquestrador com HTTP/guarda
simulados. A parte 1 abaixo acrescenta a guarda concreta com PostgreSQL restrito.

A admissão simulada agora bloqueia a proposta, depois o gate visual e o domínio
comercial, revalidando fontes/fingerprint, usuário ativo, membership, aceite e
plano antes de inserir o run e sua auditoria na mesma transação owner. A revogação
de patrocínio participa do lock comercial existente. A reserva/fence e o ledger
continuam em transação correlator separada, com os tetos já existentes; um run
gravado não autoriza repetição quando a etapa seguinte falha ou fica incerta.
Os testes adicionados exercitam captura real e concorrência PostgreSQL com
catálogo e alteração comercial. Isso não prova serialização de todos os escritores
nem autoriza o provedor real.

### Recuperação sem reserva e concorrência — 29/10/2026

`VisualAdmissionRecovery` cobre uma queda entre a admissão owner e a reserva
correlator usando somente as tabelas, locks e roles existentes:

1. Consulta o run com o ator original e o gate owner, sem transferir sua autoria.
2. Em outra transação, bloqueia a prévia fake e depois o ledger tenant. Exige
   prévia falhada, lease vencida ou fence substituído, sem arquivo/hash concluídos,
   e prova ausência de tentativa e de reserva, inclusive uma reserva não vinculada.
3. Marca a prévia como `failed`/`VISUAL_ADMISSION_ABORTED` e grava auditoria.
   O commit impede reserva e conclusão por um worker atrasado antes de liberar
   qualquer alteração de fonte pendente.
4. Somente após confirmação do commit correlator chama `finish` owner com o
   fence original. Crash/confirmação perdida permite repetir essa reconciliação;
   a auditoria da prova terminal não duplica, e a geração nunca é retomada.

Uma duplicata de execução ainda viva retorna `skipped`, conservando o trabalho
original. Reserva existente ou incerta impede a liberação; uma liquidação sem
confirmação também conserva a admissão. O renderer usa a recuperação ao reencontrar
um run no redispatch e após uma falha conhecida sem reserva. Registros já fora
da fila (prévia vencida, falhada ou tentativas exauridas) exigem invocação interna
explícita do serviço; ainda não existe varredura automática nem ação web/staff.
O autor sem acesso continua bloqueado conforme C10, adiada.

Reserva e claim verificam `clock_timestamp()` após adquirir os locks, em nova
instrução. A reserva verifica novamente após os locks financeiros e reverte
tentativa/reserva/total agregado se os prazos venceram durante a espera. Os testes
usam PostgreSQL restrito e cobrem locks da prévia, do tenant e do agregado, sem
submeter imagem. Tetos concorrentes por tenant e agregado são exercitados com
run owner real → tentativa correlator; custo incerto conserva a reserva e custo
tardio comprovado ajusta apenas a diferença, sem crédito duplicado.

A composição kit/logo também tem prova: upload de outro logo imutável não muda a
fonte pronta; draft e confirmação participam do gate; confirmação espera os runs,
bloqueia novos inícios e cancela a fila anterior. A prévia concluída continua
revisável com o kit/logo anterior. A recuperação de PUT incerto de logo ainda
pendente continua operacional; a parte 1 abaixo coordena edição/revisão de roteiro.

A consulta e o download para revisão preservam concluídas após o prazo da prévia
ou da proposta, sem usar esse acesso como autorização de geração/publicação.
O purge conserva seus objetos e a reconciliação conserva propostas, versões de
roteiro e snapshots referenciados como proveniência. No modo visual, revisão
após vencimento financeiro exige prova do run, fence e resultado concluído,
além de identidade e permissões das fontes. O prazo de aprovação permanece
independente; uma candidata vencida não ganha nova autorização por ser preservada.
Antes do rollout, drenar os workers antigos de limpeza e revisar suas leases.
Registros legados em `purging` com chave e hash conhecidos não são reclamados
pela limpeza nova; conservam estado e bytes para conciliação manual. Não inferir
que um arquivo já apagado foi recuperado. A revisão visual por outro owner ainda
pode depender do ator/vínculo original, e permanece fora deste recorte.

A fila durável de alterações cobre atualização/restauração do
contexto, catálogo, confirmação de kit e criação/alteração/exclusão de fotos do
acervo. Bloqueia novas admissões, espera as iniciadas e preserva a prévia anterior
com indicação visível. Erros previstos mantêm a alteração explícita e o bloqueio.
Edição/revisão de roteiro e writers financeiros são cobertos pela parte 1 abaixo;
logo ready é imutável e novas capacidades de acesso devem seguir o protocolo.
A decisão C10 já definiu recuperação exclusiva
pela equipe da plataforma, com ação registrada/auditada. Esta fatia recusa que
outro owner substitua ou descarte a pendência do autor original. A recuperação
staff foi adiada pelo proprietário em 29/10 para evolução de gestão de acesso e
suporte. Não bloqueia o encerramento da fatia simulada já validada. Até sua entrega,
a pendência excepcional continua bloqueada; nenhuma nova permissão foi aprovada.

Upload do acervo reserva a alteração antes de transferir, sem rede sob row lock.
Após vencer a reserva, o autor pode descartar upload incerto; a chave fica privada
em quarentena e a próxima operação usa outra chave. Retomada exige prova persistida
de PUT de tentativa única. Não há limpeza física automática da quarentena nem
fluxo de suporte para recuperar a pendência se o autor perder acesso. O rollout
requer drenagem e avaliação dos órfãos legados conforme o [procedimento](../design/BL04-quarantine-rollout.md).

## BL04.2 — parte 1: guarda concreta e escritores coordenados

`DatabaseVisualEffectGuard` e `GuardedVisualSubmissionClaims` implementam a prova
owner de fontes/aceite/run, reserva por tenant/agregado, claim única com revalidação
financeira/de identidade e commit privado por versão/fence/hash. As duas roles
continuam com commits separados; run durável conserva as fontes entre eles.
O [protocolo e inventário dos escritores atuais](../design/BL04-effect-guard.md)
documenta a ordem dos locks, o ponto de início durável e as falhas conservadas.
Não foram criados grants, roles ou tabelas para contornar a fronteira.

Edição e revisão de roteiro agora enfileiram comandos e conservam a versão atual
durante a criação. Após o commit de finish, a aplicação adquire proposta → visual
em outra transação; nunca adquire proposta a partir do gate visual. Leituras do
autor retomam aplicação pendente. O editor é ferramenta interna DEV; a IA cria o
roteiro a partir do WhatsApp/contexto, e o cliente revisa a peça. O laboratório
aguarda alteração de outra fonte pendente/falhada, conservando o formulário para
retry. Contratos opcionais `pending_change` e polling não antecipam sucesso.

`BillingProcessor.save` participa do lock comercial antes de mudar acesso.
Revogação de patrocínio usa o relógio real após a espera. Usuário/membership são
revalidados; não há writer runtime ou grant de atualização de active/papel de
cliente. Fontes WhatsApp processadas, transcrição concluída, logo ready e briefing
preparado são imutáveis nos fluxos atuais; mudanças de seleção usam comandos
coordenados. Upload de logo pendente é evolução de órfãos, não fonte selecionável.

Troca de telefone não muda mais o fingerprint de material já atribuído (C05),
e a entrega usa o vínculo novo verificado. Drenar fila/criações com fingerprints
antigos antes do rollout; concluídas antigas mantêm revisão por prova durável.

O orquestrador instala/restaura `admitted_visual_run` e distingue efeito terminado
de custo liquidado. Resposta conhecida permite concluir o run sem liberar custo
incerto. Resposta tardia não vence fence novo; confirmação perdida de claim,
reserva ou commit conserva prova/hold e, quando aplicável, objeto. Nenhum reenvio
automático. Na entrega da parte 1, essa guarda foi exercitada somente com
simulação persistida; a parte 2 acrescenta o modo explícito abaixo.

## BL04.2 — parte 2: caminho completo conectado

O modo persistido/API `visual_ai` identifica geração pelo adapter de imagem,
sem confundir resultados com `local` ou `visual_fake`. A migration 0059 exige
fingerprint para ambos os modos visuais, preserva os registros existentes e
recusa downgrade com prévias `visual_ai`. Não altera grants; foi aplicada
somente ao banco `_test` na parte 2. Para a execução autorizada da parte 3,
também foi aplicada ao banco local da aplicação.

`DatabaseVisualGenerationRunner` liga o pedido ao preparo/normalização de fontes,
guarda concreta, reserva, claim única, adapter OpenAI, acabamento, storage privado
e commit por versão/fence/hash. A API somente enfileira: não faz chamada de imagem
nem precisa receber o pool correlator. O worker usa pools owner e correlator
restritos e registra workflow/activity visual apenas com a execução habilitada.
Os testes usam o adapter real com transporte HTTP simulado, PostgreSQL e Temporal
locais; storage/interpretação externos são simulados. Não houve chamada paga.
Essa é a validação da parte 2; a chamada controlada posterior está registrada abaixo.

A ativação exige desenvolvimento/teste e, com prefixo `MEU_BRACO_DIREITO_`,
`VISUAL_AI_MODE=openai`, `VISUAL_AI_EXECUTION_ENABLED=true`,
`VISUAL_AI_RESERVATION_USD_MICROS>0`, tetos mensal por tenant e agregado pelo
menos iguais à reserva, chaves de provedor/criptografia e enforcement do aceite
único C01. A flag é desligada e a reserva zero por padrão; configuração incompleta
é recusada e não troca a geração por um placeholder local. Seleção automática de
item/fontes exige a interpretação Jev existente, com sua chave/teto próprios;
correspondência lexical de candidatos não vira seleção automática silenciosa.

O fence/reserva são atômicos entre si. Fontes, aceite, plano e run compartilham
a transação owner; a reserva continua em outra transação/role.
Falha entre os commits conserva uma admissão bloqueante, sem reenvio automático.
Essa sequência não é uma transação única; a barreira durável e a claim coordenam
os escritores atuais conforme o desenho. Novas capacidades de acesso precisam
participar do protocolo, sem inferir novos privilégios de banco.

O dispatcher inicia `VisualGenerationWorkflow` com ID estável
`visual-preview/<preview>`, rejeição de duplicata e lease de 12 minutos. A activity
tem até dez minutos, espera de agendamento de um minuto e uma tentativa. Uma
confirmação de início perdida conserva a mesma identidade/fence; prévia real já
reclamada não é redispatchada. Lease vencida marca `VISUAL_OUTCOME_UNCERTAIN`,
conservando run/reserva e sem inferir que o provedor parou. Recuperação só libera
admissão após prova de ausência de tentativa e reserva; não há varredura automática
de todos os runs abandonados. `StaticPreviewWorkflow` conserva IDs/tempos antigos;
o patch `visual-preview-wait-v1` amplia a espera da candidata sem alterar replay
dos históricos anteriores. A revisão privada conserva resultados concluídos e
proveniência de ambos os modos visuais mesmo com execução desligada.

O ledger já possui teto mensal agregado de reservas OpenAI, além do teto por
tenant (`0049`). Valores incertos permanecem reservados. É controle das operações
que passam por esse ledger, não limite da fatura OpenAI nem cobertura de chamadas
externas ao fluxo. A guarda concreta já usa os tetos por tenant e agregado na
reserva; não é uma tabela ainda a criar. Resultado desconhecido exige prova/reconciliação;
lease vencido não demonstra que a chamada terminou. Não repetir nem trocar
provedor automaticamente após possível submissão paga.

O [desenho de atomicidade](../design/BL04-atomicity-proposal.md) registra as
lacunas e a ordem de locks existente; não copiar uma ordem comercial → visual
sem resolver as inversões atuais. Não há rede enquanto se mantém row lock.
Propostas anteriores de grants e retirada de consentimento por modalidade ficam
como histórico técnico, sem tornar novos controles de IA requisito do produto.

## BL04.2 — parte 3: primeira imagem real pelo produto concluída

O proprietário autorizou Café do Cedro com foto CC0 e logo, uma imagem e teto
total de **US$ 1**, sem publicação. A execução concluiu um feed `visual_ai`
1024×1280 com `gpt-image-2.5-flare-2026-09-08`, qualidade medium, Jev real,
guarda/claim/ledger, Temporal/worker e acabamento determinístico do kit/logo.
O JPEG foi obtido pela API autenticada e S3 privado; run `finished`, prévia
`completed`, candidata com decisão pendente e publicação nula. Evidência no
[relatório de 29/10](../evals/bl042-first-product-image-2026-10-29.md).

Foram **uma chamada OpenAI de imagem e duas interpretações Jev**, com estimativa
de uso de **US$ 0,029701** no conjunto. Não é fatura nem custo por peça aceita:
a reserva visual de **US$ 0,99** permanece `uncertain`, com custo efetivo
desconhecido (`actual_usd_micros=NULL`), sem crédito inferido
da resposta. A primeira interpretação retornou formato nulo e o baseline criou
story; o wrapper de autorização recusou esse formato antes de delegar ao HTTP,
com zero chamadas de imagem demonstradas. A reconciliação em zero dessa reserva
antiga e o término explícito do run preservaram tentativa, marcadores e auditoria.
Uma nova origem esclareceu foto/feed e legenda sob a mesma autorização; não
houve edição manual de roteiro, reenvio de imagem incerta ou aprovação/publicação.

A migration 0059 foi aplicada ao banco local para esse percurso. Flags
persistentes continuam desligadas, sem novos grants ou mudanças no código de
produção. Ingresso Meta e prova de canal continuaram sintéticos, com entrega de
candidata simulada: não é prova de WhatsApp completo nem homologação Meta.
Validação dirigida aprovada: 94 unitários e `make lint types` (151 módulos).
Owner listou/baixou o hash idêntico com geração desligada e limites zero;
acesso anônimo retornou 401. Os processos habilitados foram encerrados.
O último CI completo continua o da parte 2, sem repetição nesta execução.
Os testes C08/C09 permanecem a
evidência das suas demais condições; esta única imagem não as demonstra novamente.

## Próxima fatia de desenvolvimento

Esta seção registra o plano de 30/10 e as pendências então observadas; a frente
ativa é o ciclo de revisão de Reel no início do documento. A integração de
referências avançou até 0111, conforme o gate de 04/11 acima.

O banco de desenvolvimento foi atualizado da revisão 0059 à 0099 em 03/11,
após backups privados com leitura integral verificada. A API iniciada antes da
0099 precisa de reinício para reconhecer a nova revisão e confirmar prontidão.

**Direção de 30/10/2026:** usar pedido, fatos, kit, acervo, skill adequada e
referências externas aceitas quando disponíveis para construir briefing e pedir
ao modelo a peça final completa. Conferir a peça produzida e oferecer trace
privado; não tratar texto no prompt como prova de que preço ou marca aparecem
corretamente. À época, a indicação manual estava implementada localmente e a
pesquisa e aceite de sugestões ainda não estavam entregues; a integração local
e o piloto posteriores estão registrados no gate de referências acima. A
ideia posterior de orientar seleção de fontes e
formatos do kit está registrada para estudo no
[plano de skills e referências](../design/skills-e-referencias-editoriais.md).
Conforme C18, uma oferta explicitamente promocional informada no WhatsApp é
fato para aquela criação e suas revisões. Exemplo: R$ 19,90 no pedido com preço
de catálogo R$ 25 não exige confirmar a diferença nem altera o catálogo. Para
um desconto percentual é necessário preço válido de catálogo; informação
ausente ou ambígua exige esclarecimento. Promoções, ofertas e horários não terão
cadastro na interface; o campo simples de características gerais permanece.
O titular autorizou remover informações antigas dessa área sem preservar
histórico. Essa jornada ainda não está implementada: o WhatsApp/Jev não extrai
e vincula integralmente os fatos, e o código de promoções do catálogo permanece
legado; novos snapshots editoriais ignoram essas promoções. Não presumir que a
peça atual já aplica a regra.

A implementação local descontinua novas gerações de fundo/overlay e snapshota
`full_piece_v1` por prévia. Skill editorial, logo autorizada, fotos e um exemplo
do kit demo entram no pedido completo; o provedor devolve a peça inteira. O
trace é cifrado e owner-scoped; a API exige checklist humano por hash antes da
aprovação. Checagem automática da imagem, checklist no WhatsApp/web, múltiplos
fatos temporários, análise dos concorrentes e avaliação de qualidade real permanecem abertos.

A busca começa no raio solicitado, uma vez por raio por ciclo, com até dez
candidatos por raio, sem prometer 30 negócios únicos; falha comprovada não
consome tentativa. Pela decisão de 04/11, Google vazio amplia automaticamente
de 5 para 20 e depois 50 km. Se todos vierem vazios, permitir nova tentativa
sem iniciar seis meses; os limites financeiros continuam valendo para a sequência. O cliente verá até dez candidatos elegíveis, com até três
recomendações do Jev destacadas com critérios e nota quando houver candidatos suficientes,
e escolherá de uma a três entre os exibidos, podendo combinar raios. A primeira
confirmação inicia um prazo comum de seis meses; cada raio pode ser pesquisado
uma vez no ciclo, mesmo após confirmação em outro raio. Todos ficam disponíveis
ao fim do prazo original; mudar endereço ou segmento não libera raio já pesquisado.
Trocas não renovam o prazo e a seleção permanece até outra confirmação; as
referências ainda selecionadas de ciclos anteriores podem ser combinadas com as novas. @ manuais
são adicionais. O Apify não deve repetir consultas bem-sucedidas a negócios já
encontrados durante o ciclo, mas pode consultar negócios novos de outro raio e
repetir tentativa que falhou sem retornar o perfil. O titular quer
guardar até dez negócios apresentados por pesquisa, com Place ID, nota própria
e perfis disponíveis. Confirmou que apenas Place ID será persistido dos dados
Google, usando estrelas e contagem somente como entrada para a nota; confirmou
também que a nota própria e a associação dos perfis do Apify podem ser guardadas.
Até vinte Place IDs/notas podem ser guardados temporariamente para recuperação,
com filtro de semelhança antes do cálculo; a lista exibida continua até dez.
O nome exibido virá do Apify quando houver; na ausência, mostrar o perfil ou
outro identificador disponível, sem persistir o nome fornecido pelo Google.
O titular esclareceu que cada rodada forma até dez candidatos pela mesma regra a
partir da nova resposta Google. Negócio reencontrado usa a nota mais recente na
nova lista, com notas de pesquisas anteriores preservadas no histórico. Se uma
referência escolhida ficar fora dos dez, o cliente decidirá se a mantém; essa
jornada ainda não existe no fake. Nesta primeira versão só serão considerados perfis do Instagram;
um único perfil retornado pelo Apify será usado automaticamente, sem exigir
confirmação. Com várias opções, usar o principal indicado ou, se não houver, o
primeiro retornado; o cliente pode informar outro @ se estiverem incorretas. O titular deseja
analisar via Apify até 20 publicações recentes do feed por perfil, incluindo imagens
e legendas públicas acessíveis quando disponíveis. Somente padrões extraídos serão
guardados, sem cópias de posts; acesso parcial será utilizado e identificado como
tal, e os padrões serão atualizados automaticamente a cada seis meses. Jev destacará até três negócios considerando
semelhança e nota; a interface mostrará critérios e nota, sem frase livre. Candidatos
com semelhança incerta ficam fora; não há nota mínima de corte.
A pesquisa nacional não será oferecida. Negócios sem @ devem ser
exibidos e o cliente poderá informar o perfil. O @ informado já é uma referência
escolhida, mas não se deve afirmar que foi verificado. Falha ou limite de acesso
a perfil público deve ser informado e permitir nova tentativa posteriormente.
Essas capacidades automáticas ainda não existem no produto real. Os eventos transacionais de
criação e remoção de referências ficam pendentes na outbox, sem consumidor;
seu acúmulo deve ser resolvido antes da operação continuada. Places é a fonte da
busca inicial e Apify é previsto para enriquecimento; custos, acesso,
correspondência e cobertura ainda precisam de integração. A infraestrutura fake, desligada
por padrão, exercita via Temporal os raios 5/20/50, a confirmação de uma a três
fixtures anônimas, pesquisa de raios ainda não usados durante os seis meses,
troca sem renovação, preservação da
seleção, compensação de falhas e reconciliação de autor revogado. Isso não cria
nem valida candidatos reais. Os adapters Google Places multitype e Geocoding estão
isolados/desativados e ainda não integrados ao produto;
geocodificação real e confirmação do ponto manual continuam necessárias para
raio; avaliações não medem engajamento. Um adapter de consulta de perfil via
Apify também foi preparado isoladamente e permanece desativado, sem integração
ou guardião real. A indicação de perfil não encontrado, com fonte não comprovada,
é inconclusiva; o adapter não comprova associação ou análise dos posts. A
plataforma conserva apenas padrões derivados; não há etapa obrigatória de
exclusão dos armazenamentos internos do Apify, conforme decisão do titular. Adapters isolados e
desativados para enriquecimento via Place ID no Apify e para mapeamento de tipos
fornecidos com Jev não comprovam titularidade, oficialidade da taxonomia ou
qualidade semântica; precisam de guardiões concretos e integração. Ver
[simulação](../design/reference-discovery-simulation.md).
Durante a implementação das fases seguintes, foram preparados o vínculo exato
do pedido Places e da credencial à intenção e à reserva, o teto compartilhado
do ensaio, e uma cadeia Google → Jev → filtro e gravação privada exercitada
somente com HTTP simulado. A reserva do Jev e o lote filtrado têm identidade
durável, RLS e proteção contra reenvio; até dez posições finais têm armazenamento
privado sem publicação. Há também contrato puro para projetar aprendizados, sem
coleta nem conexão à geração. A admissão da pesquisa real, a recomendação de três,
o Apify, publicação e conciliação permanecem
pendentes; estas preparações não habilitam provedores nem concluem uma fase real.
A leitura interna das listas publicadas e seleções foi testada com dois titulares,
RLS e histórico; ainda não está disponível no produto.
A admissão privada por localização de dispositivo e os ciclos reais separados
do fake foram preparados e testados sem despacho. Uma função interna ainda sem
grant libera o raio se nenhuma intenção de fornecedor existir; outros estados
conservam o raio até comprovação adequada. A seleção real que inicia os seis
meses continua sem acesso ao produto.
O titular confirmou raios 5/20/50 e início manual da próxima busca quando o
prazo terminar. Referências anteriores fora dos dez exigem decisão apenas no
início de nova rodada, sem repetir a pergunta para outro raio do mesmo ciclo.
O próprio negócio será excluído das sugestões, identificado por
nome e endereço quando houver correspondência clara e com confirmação apenas na
dúvida. Um comparador conservador foi testado isoladamente; vínculo e integração
ainda faltam. Empates na décima posição serão resolvidos pelo Jev por
semelhança; os três destaques combinarão semelhança e nota. Os titulares ativos
compartilharão as referências. Endereço e coordenadas do próprio negócio devem
permanecer no cadastro. O aprendizado abrangerá
tom, temas, formatos e elementos visuais, considerando todas as imagens
acessíveis dos carrosséis; perfil novo é analisado após confirmação e atualizado
a cada seis meses.
Essas regras ainda não estão integralmente implementadas.
O desempate possui adapter simulado, ainda sem orçamento, prova das candidatas
e publicação. Na abstenção, usar a ordem da resposta Google; a conclusão de
semelhança do Jev poderá ser guardada para recuperação sem nova pesquisa.
Um carregador restrito de contexto confere identidade, evento e versão vigente
e retorna somente dados necessários em memória; falta conectá-lo à activity.
Um adapter separado prepara coleta de até 20 publicações de imagem/carrossel do
feed por perfil usando HTTP simulado. Imagens e legendas retornam apenas em memória;
análise e conexão com efeitos pagos permanecem pendentes. O titular optou pelo
fluxo de chamada/resposta sem etapa obrigatória de exclusão no fornecedor; a
plataforma não persistirá as publicações coletadas.
O titular escolheu testar pontuação de 0 a 10 baseada em nota e quantidade,
sem armazenar os campos originais. A restrição anterior de não pontuar menos de
dez avaliações foi revista: pode-se calcular a partir de uma avaliação; sem
média ou avaliações disponíveis, o código atual não pontua nem inclui o
candidato, conforme confirmação do titular.
O titular confirmou em 03/11 que continuará testando e calibrando a
segunda fórmula; ela penaliza pouca evidência sem elevar a média e tem peso
provisório. A descoberta fake
aplica semelhança predefinida na fixture e grava a nota integral e as versões
da fórmula e fixture por pesquisa antes da leitura ordenada. Isso não implementa
avaliação real pelo Jev nem ordenação de candidatos reais.
Ver [avaliação](../evals/reference-reputation-eval-2026-10-31.md).
A fórmula final ainda não foi definida e a nota própria ainda não foi integrada
à descoberta real. Jev deverá eliminar candidatos inadequados antes de
pontuar os restantes. O titular escolheu limite financeiro por pesquisa, por
fornecedor e mensal total em UTC; valores e ativação continuam explícitos.
Política compartilhada, reservas e consumidores de efeitos fictícios foram
testados isoladamente, com retenção de resultado incerto e sem política ativa
por padrão. Isso não integra providers reais nem comprova conciliação de fatura;
parâmetros e identidade reais, chave HMAC versionada e provisionamento restrito
continuam pendentes. Trocar a chave fictícia com operação pendente interrompe o
processamento até restaurar a chave anterior, sem liberar uma reserva existente.
Na [prova pontual Nearby](../evals/google-nearby-order-probe-2026-10-30.md),
`POPULARITY` não correspondeu simplesmente a ordenar pela contagem quando a nota
era igual. As reservas Places somam US$ 0,280, sem comprovar fatura; o registro
da prova não salvou nomes ou respostas brutas.
Suporte real continua limitado a desenvolvimento/teste e desligado por padrão.

**Preparação de três cenários em 29/10:** foi ligada ao percurso visual uma orientação
experimental de skill para feed/story, selecionada por prévia somente em
desenvolvimento/teste e desligada por padrão. A migration 0060 adiciona ID/hash,
protegidos pela identidade do pedido e revalidados no preparo/acabamento. Naquela
etapa não integrava o briefing editorial completo; o caminho automático do
WhatsApp ainda não escolhe skill. O A/B local usou a mesma origem e segunda prévia selecionada
internamente. Três negócios e seis prévias passaram com provedores simulados e
PostgreSQL/Temporal locais; o evento de imagem entra já processado e a foto do
acervo é cópia dos mesmos bytes, sem provar webhook Meta ou retrieval entre fotos
distintas. O ensaio real subsequente gerou seis prévias com Jev e imagem reais:
todos os pares omitiram o preço confirmado solicitado. Naquele ensaio a skill
orientava a imagem e a copy seguia baseline. O contrato editorial real foi
alterado para solicitar ao modelo texto da arte, legenda e CTA, com vínculo a
fato confirmado ou preço válido do catálogo e rejeição sem fallback fixo. O
modo simulado continua separado. A barreira lexical daquele ensaio não verificava
sentido e não substituía revisão humana. O pedido de preço ainda não tem
interpretação estruturada que garanta sua inclusão; teste real do novo caminho
integral segue pendente.
[Evidência](../evals/three-business-visual-ab-2026-10-29.md).
Validação da correção com provedores simulados: `make ci` aprovado com 1.969
testes, 100% de linhas e branches, Ruff/formatação e mypy em 152 módulos.
Ensaio real isolado posterior produziu seis peças: preço em quatro artes, mas
não nas duas de manicure, e copy artificial em café/delivery. A skill permaneceu
restrita à imagem e cada par compartilhou a proposta; o executor não exercitou
seleção factual ou jornada completa. CI não repetido por orientação do titular.
[Evidência](../evals/editorial-copy-visual-after-2026-10-29.md).

1. **Skills para geração:** estudar e especificar as primeiras skills de feed e
   story; compará-las com o baseline em casos fictícios e integrar versões
   aprovadas à geração com kit, contexto e acervo pertinentes. No repositório
   separado `meu-braco-direito-skills`, há instruções iniciais para feed/story,
   quatro casos fictícios e protocolo de comparação. Validação estrutural e dois
   exercícios independentes passaram, sem comparação com baseline ou geração
   paga; a integração ao produto e a qualidade comercial continuam pendentes.
   Uma sonda exploratória posterior confrontou baseline isolado e saídas de
   agentes, com entradas e contratos diferentes. A skill de story não perguntou
   sobre serviços ambíguos; uma alteração dirigida e uma repetição independente
   corrigiram o caso observado. Não é comparação controlada nem prova de ganho.
   Ensaio pareado real de texto sob teto de US$ 5 foi interrompido na primeira
   tentativa incerta, sem saída e sem custo conhecido; ledger e hold preservados.
   A [evidência](../evals/skills-paired-attempt-2026-10-29.md) não autoriza
   reenvio ou avanço automático. Comparação controlada segue pendente.
   Um novo ensaio visual isolado, sob teto próprio de US$ 5, gerou duas peças
   de feed para caso fictício com e sem skill, mesma foto/kit/acabamento; duas
   chamadas textuais orientaram as cenas. Não usa o worker nem comprova ganho,
   aprovação comercial ou custo por peça aceita. [Evidência](../evals/skills-visual-comparison-2026-10-29.md).
2. **Pesquisa e referências externas:** completar a descoberta automática de
   negócios semelhantes em destaque além da indicação manual já implementada; avaliar
   fontes, permissões, métricas e relevância antes de aplicar padrões à geração.
   Jev deve avaliar semelhança e eliminar candidatos inadequados antes de aplicar
   a pontuação aos restantes e explicar até três recomendações destacadas entre
   os até dez candidatos exibidos, com fonte e uso permitidos;
   isso ainda não está implementado e não mede engajamento social. Referência não autoriza cópia;
   seu estudo pode começar após a comparação simulada das skills, sem esperar
   o fechamento integral do gate comercial BL04.3.
3. **BL04.3:** integrar padrões externos aprovados como referência e avaliar
   post/story pelo produto com titular e fontes autorizadas, incluindo revisão
   do feed já produzido. Medir pertinência, fidelidade, legibilidade, texto
   literal, rejeições, refações e custo por peça aceita. Uma chamada bem-sucedida
   ou um teste fictício não encerra esse gate.
4. **BL05:** WhatsApp como jornada principal de prévia, ajuste, aprovação e
   publicação simulada, incluindo proatividade sem nova mensagem. BL03.3 não
   bloqueia esta sequência. Novas chamadas precisam de autorização de gasto;
   a execução delimitada da parte 3 não habilita uso recorrente.

As fases, hipóteses e gates de skills e referências estão no
[plano editorial](../design/skills-e-referencias-editoriais.md). A escolha de
viabilidade e os termos das fontes automáticas permanecem abertos;
o cliente indicar um perfil não substitui a descoberta automática pretendida.

C10, recuperação automática fora do redispatch, limpeza física de PUT incerto e
suporte operacional seguem como evoluções próprias, com exceções bloqueadas até
prova segura. Não são novos poderes concedidos nem autorização para duplicar
um efeito. Retenção pós-encerramento continua adiada, sem exclusão automática.

**Adiada em 29/10/2026:** recuperação exclusiva e auditada de staff para autor
sem acesso (C10), na evolução de gestão de acesso/suporte. A proteção que impede
outro owner de assumir ou descartar a pendência permanece entregue. Até a entrega
futura, conservar a exceção bloqueada. A [proposta](../design/BL04-staff-recovery-review.md)
fica como referência, sem aprovação de novas permissões. O adiamento permite
encerrar o recorte simulado validado; os demais gates da BL04/provedor real continuam.

## BL04.3 — qualidade e economia: pendente

### Ponto de retomada histórico — 04/11/2026

O gate de qualidade de feed/story permanece pendente. A frente ativa atual é o
ciclo de revisão de Reel acima; a rodada exploratória mencionada foi executada
posteriormente, com limites e revisão pendente no relatório da BL04.3.

**Próximo trabalho: preparar a avaliação BL04.3 em quatro passos abaixo.** A
implementação local das referências está concluída até 0111, com 4.734 testes e
100% de linhas/ramos. As skills iniciais de feed/story já estão integradas. O
piloto de referências comprovou descoberta, escolha, análise e padrões no
snapshot, mas não gerou nem avaliou uma peça final usando esses aprendizados.
A nova rodada comparativa de qualidade ainda não foi executada.

O contexto a avaliar reúne pedido, informações do negócio, acervo, kit, skill e
aprendizados das referências. Referências orientam a criação; fatos, produto,
local, preço, logo e identidade continuam vindo das fontes do próprio negócio.
Testes de software aprovados não demonstram ganho criativo ou aceite comercial.

### Quatro passos da avaliação

1. **Conferir os aprendizados extraídos.** Inventariar as referências escolhidas,
   versões de associação, padrões, datas e cobertura da análise. Conferir se os
   padrões de tom, temas, formatos e elementos visuais descrevem as evidências
   acessíveis. Registrar concordâncias, erros e pontos não verificáveis. Não
   inventar conteúdo para um perfil indisponível nem arquivar suas publicações.
   Saída: quadro de revisão dos aprendizados aptos a entrar no ensaio.
2. **Gerar uma comparação controlada com e sem aprendizados.** Preparar casos
   de feed e story com o mesmo pedido, contexto, acervo, kit, versão da skill,
   modelos e configurações nos dois braços. A variável do par é a inclusão dos
   aprendizados, tanto no editorial quanto no visual. Usar fixtures autorizadas
   e as guardas do produto, sem enfraquecer snapshots ou revalidação de fontes.
   Registrar inputs versionados, operações, peças e custos de cada tentativa.
   Uma única amostra por braço é exploratória e não comprova ganho geral.
   Saída: pares comparáveis de arte e texto, com limites do ensaio explícitos.
3. **Avaliar as peças lado a lado com o titular.** Revisar no celular identidade,
   fidelidade ao produto/local, clareza e literalidade do texto, preços, CTA,
   logo, legibilidade, composição, originalidade e utilidade para o pedido.
   Registrar preferência, aprovação, rejeição ou necessidade de ajuste, com
   motivos. Avaliação automática pode auxiliar, mas não substituir esse aceite.
   Saída: revisão humana por peça e comparação documentada dos dois braços.
4. **Corrigir os problemas medidos e repetir.** Ajustar briefing, seleção de
   contexto ou instruções conforme os erros observados, em fatias revisáveis.
   Reexecutar os casos afetados com versões rastreáveis, preservando tentativas
   anteriores e registrando rejeições, refações, latência e custo completo por
   peça aceita. Distinguir reserva, estimativa e custo informado; nunca reenviar
   uma operação incerta como se fosse uma tentativa nova. Saída: correções
   validadas e relatório que explicite ganho, regressões e limites encontrados.

### Orientação histórica para a retomada de 04/11

Ler as instruções dos dois repositórios e inspecionar Git/código, preservando as
alterações existentes, inclusive as já staged. Começar pelo inventário dos casos,
aprendizados e executores de avaliação disponíveis; preparar o quadro do passo 1
e um plano revisável do passo 2 antes de qualquer chamada paga. Não reimplementar
a feature de referências nem retomar pendências de seus marcos históricos.

O plano deve informar casos, fontes/kit, formatos, quantidade de pares/tentativas,
modelos/configurações, critérios de aceite e estimativa de gasto. Apresentar as
escolhas de produto ainda abertas em entrevista, como solicitado pelo titular.
Conferir autorização e orçamento aplicáveis antes de executar: os US$ 5 do piloto
Google/Apify/Jev não autorizam esta nova rodada de geração de imagens. Tetos dos
ensaios antigos não devem ser renovados ou reaproveitados automaticamente.
Preparação local e documentação podem avançar enquanto essas escolhas são resolvidas.

Reutilizar aprendizados persistidos quando adequados, sem reiniciar ciclos,
reescrever resultados históricos ou refazer Google/Apify apenas para QA. No piloto,
a referência sugerida ficou indisponível e a manual tem nove padrões com análise
parcial; essa distinção deve continuar explícita. Flags persistentes permanecem
desligadas. O banco local está em 0111; testes de banco continuam exclusivamente
em bases novas `_test` com roles restritas, sem limpar o banco da aplicação.

Consultar antes de preparar o ensaio:

- [Piloto de referências e seus limites](../evals/reference-feature-pilot-2026-11-04.md).
- [Comparação editorial/visual anterior](../evals/editorial-copy-visual-after-2026-10-29.md):
  texto artificial, CTA e preços exigiram atenção; os pares compartilhavam a
  proposta editorial e variavam apenas o visual, limitando a conclusão.
- [Tentativa pareada interrompida](../evals/skills-paired-attempt-2026-10-29.md):
  conservar a operação incerta e sua reserva; não reenviar para iniciar a nova rodada.
- [Kit de QA Ateliê Aurora](../evals/kit-atelier-aurora-v1/README.md): existe como
  fixture independente, mas ainda não está no catálogo/executor; não presumir
  essa integração nem usá-lo como se já estivesse disponível no produto.

Registrar o plano e os resultados em um relatório datado em `docs/evals/`, com
links aos artefatos privados autorizados, sem credenciais ou publicações das
referências. Avançar automaticamente entre os quatro passos dentro do escopo e
orçamento autorizados, avisando ao concluir cada passo. Dúvidas de produto devem
ser feitas em entrevista. BL05 continua posterior à avaliação BL04.3.

### Critérios de fechamento preservados

O trabalho com dados fictícios prepara a avaliação e não comprova aceite comercial.
Gerar ao menos um post e um story novos para um caso com fontes autorizadas;
revisar no celular com titular. Medir identidade, legibilidade, texto literal,
fidelidade de produto/local, rejeições, retrabalho, todas as tentativas e custo
completo por peça aceita. A hipótese econômica é R$ 99/mês e custo total máximo
pretendido de R$ 50 por cliente/mês, incluindo serviços, infraestrutura e suporte;
não foi demonstrada. Vídeo, motion e avatar não integram automaticamente essa oferta.

Um lugar/produto inventado não pode aparecer como fotografia documental do
negócio. Referência visual não comprova fidelidade por si só; texto, preço, CTA
e logo precisam de conferência literal. Cenas conceituais devem ser identificadas.
Os [casos fictícios de QA](../evals/manual-qa-negocios-ficticios.md) preparam
cenários, sem substituir os gates de qualidade e aceite.

## Evidência datada e histórico

- Parte 3, primeira imagem: uma chamada real de imagem, duas Jev e JPEG privado
  pelo fluxo do produto, sem aprovação/publicação e com reserva de custo incerta.
  Meta de entrada/canal e entrega de candidata permaneceram simuladas. Estimativa
  total US$ 0,029701, sem fatura ou gate de qualidade comercial. Validação dirigida
  aprovada: 94 unitários, lint/types (151 módulos) e leitura/hash com geração
  desligada; CI completo da parte 2 não repetido.
  [Evidência](../evals/bl042-first-product-image-2026-10-29.md).
- Parte 2, conexão completa: `make ci` aprovado com **1.914 testes**,
  **100% de linhas e branches** (9.394 statements, 2.582 branches), Ruff/formatação
  e mypy (151 módulos). Web: **375 testes**, **100% nas quatro métricas**,
  build/formatação e **quatro jornadas Chromium** na árvore final. O percurso API →
  dispatcher → Temporal → runner/guarda → adapter com HTTP simulado → acabamento
  → prévia privada exercita modo persistido, fontes, versão/hash, revisão e
  orçamento; complementos cobrem resultado incerto sem nova submissão,
  continuidade/preservação e leitura com execução desligada. A migration 0059 foi
  aplicada somente ao `_test`; sem chamada paga ou novos grants.
- Parte 1, guarda concreta: `make ci` aprovado com **1.829 testes**, **100% de
  linhas e branches** (9.284 statements/2.550 branches), Ruff/formatação e mypy
  (149 módulos), PostgreSQL `_test`/roles restritas e Temporal locais. Prova de
  fontes/roteiro, finanças/acesso, relink por outro owner, validade factual após
  locks, claim única, resposta tardia e commits incertos. Web: 365 testes/100% nas
  quatro métricas, build/formatação e três jornadas Chromium. Sem chamada paga
  ou novos grants; à época, a próxima entrega era modo/API e wiring da parte 2.
- Recuperação sem reserva e concorrência, 29/10: `make ci` aprovado com 1.688
  testes, 100% de linhas e branches (8.989 statements, 2.462 branches), Ruff,
  formatação e mypy. PostgreSQL `_test`/roles restritas e Temporal locais; crash,
  confirmações perdidas, tentativa tardia, RLS/autoria, orçamento concorrente e
  custo tardio, prazos após locks e kit/logo. Nenhuma chamada paga, mudança web
  ou liberação da guarda real. Limites do consumidor de recuperação acima.
- Entrega anterior de admissão/continuidade/preservação: novos testes unitários e
  PostgreSQL para fontes e transição comercial concorrentes, plano vencendo após
  admissão, retenção/proveniência, prazos de aprovação e recusa de outro owner.
  `make ci`: 1.642 testes aprovados, 100% de linhas e branches (8.942 statements,
  2.446 branches), Ruff/formatação e mypy. PostgreSQL `_test` com roles restritas
  e Temporal locais; nenhuma chamada paga ou integração visual real habilitada.

- [Ensaio de feed de 27/10](../evals/bl042-guarded-synthetic-feed-2026-10-27.md):
  uma chamada com dados fictícios/CC0, US$ 0,026272 estimados; alterou logo e
  pontuação. Não usa worker do cliente nem comprova fatura, margem ou fidelidade.
- [Ensaio com acabamento de 28/10](../evals/bl042-synthetic-brand-finish-2026-10-28.md):
  US$ 0,020615 estimados, também isolado. A autorização de até US$ 1 para o ensaio
  fictício é histórica, não franquia comercial nem liberação de novos gastos.
- Aceite único: suíte backend de 1.583 testes e complemento de 24 execuções
  (sete testes novos), com cobertura final agregada de 100% de linhas e branches;
  web com 360 testes/cobertura integral, build e três jornadas Chromium. Serviços
  locais RLS/Temporal e efeitos externos simulados. Ver [CHANGELOG](../CHANGELOG.md).
- As decisões anteriores de descarte imediato de prévias, expiração dos envios
  WhatsApp e controles individuais de IA foram substituídas. As evidências originais,
  datas, contagens e propostas rejeitadas permanecem no snapshot desta fase e nos
  evals/changelogs; não são pendências de produto a reintroduzir.

## Cadastro de endereço próprio — 04/11

A API autenticada de endereço próprio conserva versões e exige controle de
concorrência e identidade de operação. Ela estabelece a origem declarada pelo
titular, sem copiar GPS ou origem de pesquisa. Geocodificação, persistência do ponto
comprovado e vínculo à identidade da busca permanecem pendentes; nenhuma chamada
externa foi habilitada. Ver [contrato](../design/business-address.md).

## 04/11/2026 — Classificação prévia de atividade

Taxonomia Google Table A versionada e adapter Jev pré-Google implementados
com uma requisição, código de tipo fechado e retorno de uso. O vocabulário
contém 478 códigos e foi conferido em fonte oficial; não usa `restaurant`
como padrão. Incerteza de categorias não escolhidas não impede um match válido.
Validação local: 66 testes unitários, 100% linhas/ramos dos dois módulos, Ruff
e tipagem estrita; sem efeitos pagos. Integração do guard e execução 0106 e
ensaio semântico real permanecem gates da descoberta completa.

### Fatia0103 — endereço, geocodificação e identidade própria

A API de endereço passou a ter início, consulta e confirmação de geocodificação,
com relay/Temporal e orçamento persistido. O ponto preciso é aceito automaticamente;
resultados ambíguos aguardam o titular. O endereço próprio e suas coordenadas
continuam no cadastro, e a origem manual de busca pode reutilizá-los com o custo
incluído na mesma pesquisa. O cadastro próprio é obrigatório na admissão real;
nome/endereço têm vínculo HMAC e são revalidados no carregamento, nos claims da
busca e na publicação. A validação usa serviços locais e transportes HTTP falsos,
sem gastar o teto autorizado. Ver [contrato](../design/business-geocoding.md).
A descoberta completa ainda precisa chamar o loader de identidade e tratar o
comparador, a ambiguidade, perfis e aprendizado; não declarar a feature concluída
por causa desta integração de endereço.

## Retomada 04/11 — integração até 0105

Resultados reais e seleção têm rotas autenticadas; publicação privada preserva
IDs/notas e exige revisão de escolhas ausentes só no início da nova rodada.
Correção manual de perfil possui versão, replay e auditoria. Endereço/geocodificação
e identidade própria foram conectados pela 0103. A execução completa Google →
Jev → Apify → publicação ainda está em integração, não concluída.

O custo por pesquisa agrega titulares; run Apify persistido permite consultar a
mesma coleta e reconciliar seu custo terminal sem novo POST. Adapter Compass
usa contrato oficial, build explícita e limite por execução. Os testes dirigidos
passaram; a suíte integral inicial terminou com 3.993 aprovados, duas falhas e
99,38% de cobertura, em correção. Falta validar a árvore final, conectar análise
de publicações/atualização semestral e aprendizados à criação, e executar o ensaio
fictício autorizado de até US$ 5 quando as credenciais locais estiverem disponíveis.

### Transporte real de feed, 04/11

Adapter Instagram e downloader de imagens preparados para o executor, com
network opt-in e controles de custo/identidade/limites. 357 unitários passaram
com 100% dos cinco módulos, Ruff e mypy aprovados. Publicações continuam apenas
em memória. Persistência de aprendizados, agenda Temporal semestral e uso na
criação ainda estão em implementação. Google vazio terá ampliação automática
5 → 20 → 50; ausência nos três permite nova tentativa sem iniciar seis meses, conforme
entrevista. A integração completa dessa ampliação permanece pendente.

### Configuração do piloto de referências, 04/11

O script `scripts/configure_reference_pilot.py` prepara a política local e o
piloto acumulado de US$ 5, sem zerar consumo ou habilitar fornecedores. Plano
por padrão; aplicação exige banco local/admin separado e preserva configurações
divergentes. 14 unitários e três testes SQL aprovados; execução real ainda pendente. Ver
[operação](../design/reference-pilot-operations.md).

## Revisão do baseline — 04/11/2026

A [retomada do CI](../evals/ci-resume-2026-11-04.md) identificou código morto
após C17/C18. Criação local permanece recusada, com auditoria/fence do job
legado e leitura privada histórica preservados. Geração editorial mantém o
percurso obrigatório de catálogo/skill e trace, sem alternativa sem skill
inacessível. Prova de role aceita o login restrito efetivamente configurado;
Temporal conserva timeout de 45s e diagnóstico apenas de estados/códigos.
3.555 testes relacionados passaram; o gate integral de 100% segue pendente.

### Banco local e leitura de referências, 04/11

Banco de desenvolvimento atualizado de 0099 para 0105 após backup privado
`.local/backups/pre-reference-20261104-111303-372421.dump`, com índice do arquivo
validado pelo pg_restore da mesma versão. A leitura de referências do negócio
informado passou usando runtime restrito e autorização de titular ativo. Isso
valida o serviço/banco; a sessão autenticada do navegador ainda não foi repetida.
O banco da aplicação não foi usado como banco de testes.

### Análise estruturada de publicações, 04/11

O adapter Jev aceita legenda e/ou imagem em memória e devolve apenas códigos
de um vocabulário próprio. A agregação gera até nove padrões gerais de tom, temas,
formatos e elementos visuais, sem conteúdo das publicações. 65 testes passaram
com 100% de linhas e branches nos dois módulos novos; Ruff e mypy aprovados.
Persistência, agenda de seis meses e uso no gerador permanecem em integração.
O teto local acumulado de US$ 5 foi configurado; flags persistentes continuam
desligadas e não houve chamadas pagas nesta retomada.

### Fatia 0107 — identidade própria e busca vazia

Implementados: conclusão de identidade atômica com a evidência sanitizada; revisão compartilhada por titulares; exclusão antes do ranking/publicação; ampliação automática de respostas Google vazias; orçamento agregado por família; cache entre raios; resultado vazio terminal e retry sem iniciar ciclo não confirmado; histórico preservado. Estado canônico de família inclui a busca atual, sem inferência da UI.

Validação local usa PostgreSQL exclusivo `_test`, logins restritos e fornecedores simulados. Upgrade/downgrade vazio foi exercitado. Testes cobrem confirmação por segundo titular, rejeição de viewer/revogado, rollback atômico, exclusão antes do ranking, cadeia 5/20/50, limite financeiro da cadeia e replay depois de liberar o head. A entrega final continua condicionada à integração Temporal completa, análise de publicações/agenda e CI integral; esta fatia não demonstra chamada paga real.

Validação concluída da fatia: oito integrações e 45 unitários aprovados; 100% de cobertura em 149 linhas/30 ramos dos cinco módulos, mypy e Ruff. Roundtrip vazio 0107 → 0106 → 0107 aprovado. Cache compartilhado mantém dados históricos sem expor tokens.

### Execução integrada da descoberta, 04/11

0106+0107 conectam admissão, Temporal, Google, Jev, Apify e publicação sob o
ledger existente. A API recebe operação e carrega contexto/raio do servidor;
retomada comprovada do Apify não repete Google/Jev. A tela usa o estado canônico
da família de raios. Flags persistentes continuam desligadas. A validação dirigida
passou em 57 testes, incluindo 17 integrações, com cobertura integral dos módulos
novos de execução; adapters e wiring passaram nos recortes próprios. CI integral
e ensaio pago permanecem pendentes. Veja docs/design/reference-discovery-execution.md.


### Referências escolhidas na geração — fatia 0110

Novas propostas capturam a seleção canônica e os aprendizados da versão exata
do perfil em `reference_generation_snapshot`, separado do histórico manual.
Briefing editorial e peça visual usam a mesma cópia imutável. Ausência de análise
e cobertura parcial permanecem explícitas; notas internas e semelhança orientam
a seleção e não autorizam afirmações comerciais. Posts, legendas e imagens de
terceiros não são armazenados nem enviados como referências visuais.

Retirada ou troca de perfil bloqueia novo efeito que utilizaria a associação
antiga; uma alteração durante o efeito impede aceitar o resultado editorial.
A revalidação não substitui a cópia histórica. Prévias concluídas e traces
continuam acessíveis pelas regras existentes. Propostas legadas com coluna
nula conservam o fingerprint e o significado de suas indicações manuais.
Não há truncamento silencioso a32 referências; o limite de tamanho do pedido
editorial continua sendo conferido antes da reserva.

Contrato e validação em [integração de referências na geração](../design/reference-generation-context.md).
177 testes unitários e 13 casos PostgreSQL passaram nos recortes desta fatia,
incluindo leitura 0108 e geração visual com HTTP simulado. Naquele recorte, a
agenda completa e o CI integral ainda estavam pendentes; essas provas não
demonstravam qualidade comercial. O CI vigente foi concluído em 09/11, conforme
o estado atual no início deste documento.

### 0108 — seleção, persistência e atualização dos aprendizados

A análise passa a ter associação de perfil, janela e evento duráveis derivados
da seleção real. Perfis manuais e sugeridos escolhidos usam a mesma autoridade;
correções de candidatos não selecionados não coletam publicações. Remover ou
trocar o perfil invalida a janela anterior antes de outro efeito. A agenda
semestral deriva do aceite, e resultados mantêm somente padrões próprios
comprovados, nome oportunista Apify e metadados. Captura/revalidação para geração
e leitura de status não confundem perfil escolhido com análise concluída.
As provas locais usam PostgreSQL isolado, roles restritas e fornecedores simulados.
Integração do executor, snapshot editorial/visual e tela vem nas fatias adjacentes;
ensaio real controlado e qualidade comercial continuam gates próprios.

### Aprendizados das referências na API e na jornada, 04/11

O GET autenticado `reference-learnings` entrega somente os estados, datas e
padrões persistidos para as referências escolhidas e sua associação vigente.
Titulares ativos compartilham essa leitura; viewer, outro tenant e sessão ausente
são rejeitados. A consulta não inicia efeitos nem altera a agenda. Quando o feed
já obtido forneceu um nome válido, a tela o apresenta junto ao @; na ausência,
continua usando o perfil. Não há nova chamada para obter nome.

O painel distingue espera, execução, indisponibilidade, análise concluída/parcial
e atualização programada. Seleção, correção do @ e referências próprias
invalidam a leitura. Não afirma sucesso enquanto os padrões não estão salvos.
16 testes unitários passaram com 100% de linhas/branches dos três módulos de
leitura; dois testes HTTP/PostgreSQL passaram com runtime restrito e provaram
isolamento e ausência de novas reservas, resultados, eventos ou auditorias no
GET. Mypy e Ruff passaram. A web passou em 100 testes focados/100% das quatro
métricas e em Chromium 390/1440px com fixtures locais. CI integral combinado e
ensaio externo controlado continuam como gates da entrega completa.
