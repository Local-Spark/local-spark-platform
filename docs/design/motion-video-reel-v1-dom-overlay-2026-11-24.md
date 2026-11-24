# Video-reel v1 — correção de orientação para execução DOM

## 24/11/2026 — acompanhamento v19

A falha seguinte por BR dentro dos textos e o diagnóstico seguro do renderer
estão em [texto puro e erros específicos](motion-video-reel-v1-text-nodes-2026-11-24.md).
V19 preserva o scrim e a guarda; o histórico abaixo descreve v18.

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

## Evidência e limites

Run: `c516f97b-79ae-5a08-a7a1-a7d8612b581a`, criado 24/11/2026 às 09:56:04
(São Paulo), encerrado às 10:01:54. Snapshot: skill v17, repertoire v2,
proposed-video-output-v1, quality-v2, staging-v1 e motion-video-reel-v1.
Custo já registrado: 1.702.688 micros de USD. Não houve novo gasto no diagnóstico.

O trace contém plano, composição e pedido de render, sem resposta de render.
A inspeção e a simulação local identificam violações concretas no código, mas
não recuperam stderr original descartado pelo limite de diagnóstico do runner.
Na simulação: 0ms passa; 33,333ms gera
MOTION_VIDEO_READABLE_ACTION_OVERLAY_REQUIRED; 650/1650/7300/7900ms geram
MOTION_VIDEO_UNPLANNED_OVERLAY. Os assets reais foram substituídos por mídia
sintética; não é render de aceitação nem comparação audiovisual do cliente.

## Decisão

Corrigir orientação antes de gastar em outra captura. v18 inclui instruções para
plan e implementation, mais exemplo executável testado. Repertório v2, skills
v14–v17 e guarda não são regravados; não há normalização silenciosa do plano
recebido nem relaxamento de validação. O exemplo preserva fronteiras enter/exit,
transform próprio por texto e CTA com hold ≥1500ms das versões anteriores.
