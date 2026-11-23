# Decisões vigentes e pendências

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

Titular pediu análise do MP4 recuperado do run `cefe9071…` (S1–S3 ok no
audiovisual; falha só na persistência). Decisão desta mudança: **só docs** —
[motion-ensaio-cafe-aurora-v10-gaps-2026-11-18.md](design/motion-ensaio-cafe-aurora-v10-gaps-2026-11-18.md).
Próxima fatia alvo: T1 variedade/clima, T2 legibilidade tipográfica, T3 limpeza
de acentos residuais; T4 mix opcional. Preservar S1–S3, intent v10, guarda
v2/v3 e o tom soft do briefing. Sem código, chamada paga, A5b ou aceite E2E
nesta mudança. Arquivo recuperado ≠ versão aprovada.

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

Titular pediu análise de `versao-1 (9).mp4` (melhoria subjetiva e métrica vs
v8; distância às refs ainda ~metade). Decisão desta mudança: **só docs** —
[motion-ensaio-cafe-aurora-v9-gaps-2026-11-18.md](design/motion-ensaio-cafe-aurora-v9-gaps-2026-11-18.md).
Próxima fatia alvo: S1 cover no miolo, S2 energia no fecho até end, S3
filtrar/despriorizar assets com marca de terceiros; S4 mix opcional.
Preservar intent v10 / guarda v2 (dissolve/CTA). Sem código, chamada paga,
A5b ou aceite E2E nesta mudança.

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

## 18/11/2026 — pós-ensaio v8: documentar R1–R4, enforcement hard

Titular pediu análise de `versao-1 (8).mp4` (melhoria subjetiva vs refs ainda
distante; análise técnica: regressão vs v7). Decisão desta mudança: **só docs**
—
[motion-ensaio-cafe-aurora-v8-gaps-2026-11-18.md](design/motion-ensaio-cafe-aurora-v8-gaps-2026-11-18.md).
Próxima fatia alvo: R1 cover hard, R2 energia no miolo, R3 logo sem placa hard;
R4 mix opcional. Prompts soft sozinhos falharam; priorizar validação de
layout/HTML. A5b, TTS/avatar, renderer e tarifa Music fora até OK explícito.

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

## 18/11/2026 — pós-ensaio v7: documentar Q1–Q4, não implementar ainda

Titular confirmou melhora em `versao-1 (7).mp4`; pediu diagnóstico e docs para
outro chat. Decisão desta mudança: **só docs** —
[motion-ensaio-cafe-aurora-v7-gaps-2026-11-18.md](design/motion-ensaio-cafe-aurora-v7-gaps-2026-11-18.md).
Próxima fatia alvo: Q1 cover no miolo, Q2 energia contínua, Q3 logo sem placa;
Q4 mix opcional. Crop v5 e gates M3/N2/O2 preservados. A5b, TTS/avatar,
renderer e tarifa Music fora até OK explícito.

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

## 18/11/2026 — pós-ensaio v6: documentar O1–O4, não implementar ainda

Titular confirmou melhora em `versao-1 (6).mp4` sem nível máximo; pediu
diagnóstico e docs para outro chat. Decisão desta mudança: **só docs** —
[motion-ensaio-cafe-aurora-v6-gaps-2026-11-18.md](design/motion-ensaio-cafe-aurora-v6-gaps-2026-11-18.md).
Próxima fatia alvo: O1 cover contínuo, O2 energia perceptível, O3 logo sem
placa; O4 mix opcional. Crop v5 e gates M3/N2 preservados (podem endurecer).
A5b, TTS/avatar, renderer e tarifa Music fora até OK explícito.

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

## 18/11/2026 — pós-ensaio v5: documentar N1–N4, não implementar ainda

Titular confirmou evolução em `versao-1 (5).mp4` sem nível máximo de propaganda;
pediu diagnóstico e docs para outro chat. Decisão desta mudança: **só docs** —
[motion-ensaio-cafe-aurora-v5-gaps-2026-11-18.md](design/motion-ensaio-cafe-aurora-v5-gaps-2026-11-18.md).
Próxima fatia alvo: N1 full-bleed real, N2 energia no miolo, N3 fecho sem creme;
N4 mix opcional. Crop v5 e gates M3 preservados. A5b, TTS/avatar, renderer e
tarifa Music fora até OK explícito.

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

## 17/11/2026 — M1–M3 versionados, gates de declaração e exemplo de anúncio

O pedido atual autoriza implementar o backlog v4. Decisões:

- Nova captura usa intent v4, skill photo v16 e default repertório v8. Não editar
  bytes/hashes de v15/v7 nem o contrato v3: replay conserva sua regra de logo
  declarada, sem receber os gates novos. Seleção explícita continua respeitada.
- Full-bleed/overlay desde o gancho é default forte. Inset precisa de motivo em
  staging.development e scene_direction.composition. Sem campo/schema novo nem
  gate geométrico; instrução de rejeitar default editorial vai ao provedor.
- Logo como âncora: referência 32–44% da largura (mínimo orientado 28%; exemplo
  36%), proporção/contain, contraste e atenção à área transparente do PNG.
  Sem alegar que largura CSS garante tamanho perceptivo da marca.
- `motion_photo_quality` valida apenas intent v4, após vínculo de materiais e
  staging. `MOTION_PHOTO_HOLD_TOO_LONG` para hold contínuo >2500 ms, incluindo
  beats hold adjacentes do mesmo elemento. Transform não é hold; cenas vivas
  e movimentos contínuos podem durar mais. Gaps/estados implícitos fora do fecho
  e renomear um hold como transform não são detectados como congelamento.
- Fecho: `MOTION_PHOTO_CLOSING_WINDOW_INVALID` se handoffEnd não estiver entre
  início da última cena e end (exclusivo); deriva da transição staging de chegada,
  ou fim das entradas/início da cena quando não há transição. Materiais ausentes
  no fecho geram `MOTION_PHOTO_CLOSING_MATERIAL_REQUIRED`; presença em cena anterior
  não basta. Todos os nós foto/logo do fecho precisam cobrir handoffEnd→end com
  transforms e estados distintos, ou `MOTION_PHOTO_CLOSING_MOTION_REQUIRED`.
  KB/scale e visibilidade são instruções, não semântica inferida de texto livre.
- Exemplo v8 mostra markup full-frame, scrim local, logo e wrappers separados;
  não instala helper automaticamente. M4/mix adiado; Music, vídeo, renderer,
  TTS/avatar e A5b não mudam.

Validação: 286 unitários, 10 Node e três integrações `_test`; intent/validador
100% linhas/branches, Ruff/formato local aprovados. `make ci` permanece bloqueado
nas 66 ocorrências de lint anteriores; não declarar cobertura global ou CI verde.
Sem chamada paga ou novo MP4. Aceite E2E depende de ensaio autorizado e revisão
do titular, inclusive enquadramento, tamanho útil da logo e energia percebida.

## 17/11/2026 — pós-ensaio v4: documentar M1–M4, não implementar ainda

Titular confirmou que v4 não retrocede em marca (logo pequena no fecho) mas
permanece distante de propaganda / refs YouTube; pediu diagnóstico e docs para
outro chat. Decisão desta mudança: **só docs** —
[motion-ensaio-cafe-aurora-v4-gaps-2026-11-17.md](design/motion-ensaio-cafe-aurora-v4-gaps-2026-11-17.md).
Próxima fatia alvo: M1 full-bleed, M2 logo âncora, M3 ritmo no plano; M4 mix
opcional. A5b, TTS/avatar, renderer e tarifa Music fora até OK explícito.

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

## 17/11/2026 — pós-ensaio v3: documentar L1–L4, não implementar ainda

Titular confirmou melhora perceptível em `versao-1 (3).mp4`, pediu análise de
gaps (holds parados, logo como texto) e documentação para outro chat.
Decisão desta mudança: **só docs** —
[motion-ensaio-cafe-aurora-v3-gaps-2026-11-17.md](design/motion-ensaio-cafe-aurora-v3-gaps-2026-11-17.md).
Próxima fatia alvo: L1 logo obrigatória, L2 ritmo/fecho, L3 full-bleed; L4 mix
opcional. A5b, TTS/avatar, renderer e tarifa Music fora até OK explícito.

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


## 17/11/2026 — próximo salto visual photo: documentado, não autorizado ainda

Após ensaio com Music ainda visualmente estático, o titular pediu documentar
melhorias (Ken Burns, tipografia cinética, scale/handoff, ritmo, mix) para
iniciar noutro chat. Decisão desta mudança: **só documentação** —
[motion-melhorias-pos-ensaio-cafe-aurora-2026-11-17.md](design/motion-melhorias-pos-ensaio-cafe-aurora-2026-11-17.md).
A5b, TTS/avatar e alteração de tarifa Music continuam fora até OK explícito.
Runtime continua em snapshots locais pinados; repos skills/motion-sources
externos não são lidos ao vivo.

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


## 17/11/2026 — escopo da rodada: A2, sem executar testes agora

Titular confirmou Starter+ e chave ElevenLabs no `.env`, autorizou habilitar
Music e dispensou merge como pré-requisito. Flags locais Music/confirmacão de
direitos habilitadas; tetos e credencial preservados; nenhum gasto autorizado
ou executado nesta rodada. Instrução final: implementar primeiro **somente A2**,
com lab sempre aprovando plano e WhatsApp validando automaticamente. A3–A5,
TTS/Voice e avatar continuam fora desta mudança. Testes devem ser preparados,
com execução adiada pelo pedido expresso de não testar agora. O aceite de
ponta a ponta continua posterior; não declarar A1/A2 artisticamente aceitas.


## 17/11/2026 — trilha de photo reel via ElevenLabs Music (cache interno)

Execução posterior nesta rodada: A1 implementada com flag desativada, cache
privado, ledger e testes sintéticos. Aceite pago/escuta e gates globais de CI
continuam pendentes; ver o registro de execução no topo de PROJECT/SDD/BL04.
A autorização de código não autoriza chamada paga nem ativação.

Titular rejeitou Freesound CC0 como fonte principal de trilha para café/jazz
(qualidade aquém do alvo tipo Cafe Music BGM). Decisão: **ElevenLabs Music**
para gerar trilhas instrumentais; **Freesound CC0 permanece para SFX**.
ElevenLabs Voice/clonagem continua reservada a fatia posterior (narração/voz
do cliente), distinta da trilha.

Modelo de produto (não é seletor para o cliente):
- Cliente **não escolhe** faixas e **não vê** catálogo/stock.
- O sistema seleciona uma faixa já gerada/cacheada que faça sentido ao clima
  do pedido/negócio, ou **gera** quando não houver candidata adequada.
- Faixas geradas são baixadas, armazenadas com identidade/hash e reutilizadas
  no mix sem nova cobrança à API enquanto o mesmo arquivo for reaproveitado.
- Custo de lista ~US$ 0,15/min gerado (API); cobrança por geração, não por
  reprodução no Instagram. Plano pago Starter+ exigido para uso comercial de
  música conforme termos ElevenLabs vigentes.

Enquadramento vs Music Terms: não expor biblioteca de outputs a terceiros para
escolha/download/licenciamento. O cache é operacional interno do produto (o
sistema escolhe/gera). Revisão jurídica/Enterprise permanece se o enquadramento
multi-tenant for questionado; não confundir com Marketplace público.

Estado atualizado: integração A1 implementada; titular confirmou chave e Starter+
e autorizou a flag local. Reserva/tarifa/teto e aceite pago/escuta continuam
pendentes; não declarar integração aceita E2E. Plano:
[motion-plano-reels-15s-foto-2026-11-17.md](design/motion-plano-reels-15s-foto-2026-11-17.md).

## 16/11/2026 — confirmação da base editorial no laboratório

O titular escolheu sugestão pelo modelo a partir da mensagem, seguida de confirmação
explícita do produto/serviço antes da geração. A seleção lexical apenas fornece
candidatos; não substitui interpretação nem aprovação. Planejamento vale também
para vídeos. Retenção de sete dias apaga só trace; peças/anexos e textos da peça
permanecem. Configuração financeira e validação real não foram executadas.

## 16/11/2026 — laboratório administrativo: acesso e seleção implementados

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
528 testes/100% nas quatro métricas. CI integral backend e QA/build web em curso.
Docker iniciado pelo titular; dez consumidores antigos pausados com autorização,
PostgreSQL/Temporal disponíveis. Nenhuma migração de dev, geração paga ou publicação.

Pendentes: persistência, execução produtiva por formato, orçamento separado,
anexos, SSE/trace, retenção/exportação e jornada completa. Não é entrega final.
[Especificação, decisões e evidências](design/admin-production-rehearsal-2026-11-16.md).

## 09/11/2026 — recorte da integração do Reel qualificado localmente

A implementação autorizada preserva HTML/`scene_init` e o caminho de serviços
Python/Temporal. Pedido, render isolado, revisão condicional e versões privadas
compõem a etapa 4; os demais formatos vêm após sua qualificação. A coleção
`content_pieces` registra aceite da versão sem criar postagem e mantém a
proveniência simulada visível. Selecionar uma versão anterior como melhor não
apaga alternativas posteriores; a interface usa “atual” e “alternativa”, sem
confundir seleção com cronologia.

A crítica distingue evidências de fonte, atual e anterior; aprovação/reprovação
de critério exige quadro da versão atual. A reserva precisa cobrir o máximo de
saída configurado, mas ainda não prova teto total com entrada/imagens. Antes
de ativar chamadas integradas, definir esse limite por modelo, credenciais e
orçamento explícito. Os ensaios pagos históricos não renovam autorização.

A [qualificação local](evals/qualificacao-integracao-reel-2026-11-09.md) passou
com quatro replays, prova integrada com modelo/crítico simulados, backend
5.353 testes/100% e web 524/100%. A configuração continua desativada por padrão.
Isso não substitui avaliação criativa do gerador pago nem ativação comercial. [Desenho e limites](design/integracao-reel-2026-11-09.md).

## 09/11/2026 — preferência humana por B e conclusão delimitada da etapa 3

O titular respondeu **“B ficou melhor.”** à entrevista de motion/narrativa do
Giz, `call_3e1d59720b1b4daabd16fcb8cfd27982`, item 0. O
[registro humano](../.local/evals/motion-feedback-review-runs/1c758136-7530-43d8-96b7-39e4b0e44888/human-feedback.json)
vincula a resposta aos hashes de A/B, relatório e summary, sem alterar esses
artefatos ou a crítica. O estado automático `completed_human_pending` permanece
como registro histórico, anterior ao feedback.

A etapa 3 está concluída **no recorte demonstrado**: reparação de legibilidade
1c e refinamento criativo Giz guiado por feedback/referência adicionais, com
preferência humana por B. Não inferir aprovação separada de áudio, todo critério,
todos os formatos ou benefício econômico geral. A evidência não transforma a
revisão em descoberta autônoma de um erro do briefing original.

Prosseguir à **implementação do Reel integrado (4)** e depois dos **demais
formatos (5)**, conforme autorização já recebida. Essas entregas ainda não estão
concluídas. Novas APIs pagas continuam sujeitas ao escopo/orçamento aplicáveis;
esta preferência não autoriza postagem ou renova automaticamente os tetos.

O CI e o QA já foram concluídos. Na entrevista operacional
`call_9cd4f8a76acd4c8c81f68ace7f4918e1`, item 0, o titular respondeu “Sim, posso
manter o Mac acordado”; isso não exige nem autoriza por si só repetir o CI já
concluído. As falhas e resultados anteriores permanecem preservados.

## 08/11/2026 — legibilidade do 1c reconhecida, motion não aprovado

Registro anterior à resposta final do Giz em 09/11. A limitação do 1c permanece;
a pendência humana do Giz abaixo foi encerrada pela decisão vigente acima.

O titular confirmou que B tem títulos e legendas melhores e perguntou se era
story, se deveria ter motion e por que parecia apenas vídeo com texto sobreposto.
O [feedback integral](evals/ensaio-revisao-reel-1c-2026-11-08.md) confirma a melhora
de legibilidade, sem aceite global, aprovação de áudio/motion ou liberação da
integração. Não registrar a peça inteira como aceita nem calcular seu custo
por peça aceita com base nessa confirmação parcial.

O contexto original conferido especifica `reel` com cortes, transições, motion
graphics e legendas. A entrada é ilustrativa/licenciada com voz sintética,
não gravação de cliente. O diagnóstico da retomada é que os pequenos ajustes
de enquadramento/fades não demonstram o acabamento criativo esperado. A crítica
ter classificado movimento como `pass` expõe uma lacuna: presença de animação
não comprova qualidade criativa ou atendimento ao briefing.

Intensa/Dog/Luma continuam as referências de qualidade; o 1c é evidência de
reparação específica e caso de limitação criativa, não padrão a integrar.
O CI foi concluído em 09/11; a avaliação humana da prova criativa continua
anterior às etapas 4/5. Esse feedback
de legibilidade isoladamente não autorizou outro gasto; a escolha e autorização
posteriores de Giz estão registradas abaixo.

A entrevista posterior foi respondida: **“Comprovar melhora do motion primeiro
(recomendado)”**. A etapa 3 exige prova criativa antes da integração. Giz
(operação `15adf19d`, lote `e2bbd3aa`), antes avaliado abaixo de Intensa, é o
candidato em análise. Não foi identificada violação inequívoca do briefing
original: motion/desenho existem, e pedidos de tema/janela contínua são feedback
posterior. A prova deve declarar refinamento com contexto adicional, sem
apresentar esse resultado como descoberta de erro do pedido original.
O [plano do Giz](evals/plano-refinamento-motion-giz-2026-11-08.md) e pacote de
70 arquivos estão concluídos; contexto original, feedback e novas referências
ficam separados. O percurso proposto tem até duas chamadas: refinamento e
avaliação comparativa, sem crítica paga inicial para repetir feedback conhecido.
Protótipo/contrato implementados e replay real qualificado: 336 quadros/tempos
e áudio preservados. Isso prova equivalência técnica do baseline, não ganho
criativo. B foi inspecionada localmente no código e no artefato antes da
comparação paga; isso não é aprovação do titular. HTML livre não garante
invariância geral de fatos/textos por schema; as conferências do caso e a prova
de AAC/PCM/tempos foram preservadas.
O orçamento concreto proposto é US$ 1,25 de admissão para até duas chamadas,
com reservas de US$ 0,75/US$ 0,25 e folga US$ 0,25. Em 09/11, o titular
respondeu “Autorizar até US$ 1,25 para a prova Giz”. `authorization.json` vincula
a decisão ao plano, qualificação e pedido; o plano proposto original permanece
intacto. As duas chamadas foram concluídas, sem retry/incerteza ou reparo manual.
A crítica preferiu v1 e considerou os três requisitos atendidos; áudio ficou
incerto. Estimativa incremental US$ 0,6482575, comprometimento US$ 1,0138475
dentro do teto. [Resultado e comparação](evals/ensaio-refinamento-motion-giz-2026-11-09.md).
QA do relatório aprovado; comparação aberta e entrevista humana enviada com
link explícito. Resposta/aceite pendentes. A avaliação é de refinamento com
feedback/contexto posterior, sem provar autocrítica do
pedido inicial. A decisão humana continua pendente; nenhuma integração foi iniciada. O CI
foi concluído em 09/11 com 5.043 testes aprovados e dois pulados inicialmente,
completados separadamente após ajuste de PATH, cobertura app 100% e verificações
do laboratório aprovadas. Isso não substitui aceite criativo nem qualifica
durabilidade de produção: opções de durabilidade foram desligadas apenas no
PostgreSQL descartável do CI.

## 08/11/2026 — testar correção do Reel histórico com defeito conhecido

Após Dog/Luma receberem críticas v2 `adequate` sem refação, o titular escolheu
em entrevista: **“Testar a correção do Reel antigo com problema conhecido”**.
A escolha mantém a prova antes da integração; não aceita antecipadamente seguir
com ganho não demonstrado. O [plano 1c](evals/plano-revisao-reel-1c-2026-11-08.md)
usa a primeira montagem histórica com tipografia pequena, preservando as dez
normalizações anteriores e distinguindo a variante manual posterior.

A origem tem direção declarativa, não HTML/JS. Sua ponte está implementada,
com qualificação completa aprovada e pacote offline ampliado de 56 para 69
arquivos para incluir custos históricos.
O manifesto anterior permanece preservado. A falha de unidades já foi corrigida no
schema atual; testar reparação desse caso não atribui ao crítico a melhoria do
briefing já realizada nem demonstra benefício criativo geral. Avaliação humana
continua necessária. Depois da qualificação, o titular autorizou em entrevista
própria **US$ 1,25 para até três chamadas e envio à OpenAI**. O registro privado
`authorization.json` vincula decisão, plano, primeiro pedido e qualificação.
A autorização é específica do 1c; não transfere o orçamento de Intensa/Dog/Luma.
A execução paga concluiu três chamadas e gerou v1; a crítica final preferiu v1
pela legibilidade, com estimativa incremental de US$ 0,527685. O [resultado](evals/ensaio-revisao-reel-1c-2026-11-08.md)
é evidência automatizada específica. O feedback posterior acima confirmou a
melhora tipográfica, mas não a qualidade global. A integração continua
condicionada à avaliação criativa e à validação técnica; ganho global e retorno
financeiro geral não foram demonstrados.

## 08/11/2026 — roteiro recuperado, retomada e piloto por autoatendimento

O titular forneceu o texto original dos [sete processos](design/execucao-ate-etapa-7-2026-11-07.md)
e autorizou alinhar a documentação, resolver pendências técnicas e concluir a
prova da etapa 3 antes da integração do Reel (4); depois, implementar os outros
formatos (5). Comparação real e avaliação humana continuam anteriores à
integração. Cada formato exige qualificação própria; não converter limite de
correções em obrigação de gerar nem considerar a última versão a melhor.

A confirmação de 07/11 permanece: etapa 7 é preparar o piloto e a operação
comercial. A entrevista foi respondida: não há participantes reais definidos e
o modelo escolhido é **autoatendimento com cobrança**. Usar os quatro cenários
fictícios documentados para validação inicial; não registrá-los como clientes.
Patrocínio de seis meses não é concedido automaticamente. Preço/franquias
continuam dependentes de medição (P05), e P03 não foi revogado.

WhatsApp oficial é necessário para a jornada real. Publicação no Instagram
fica após geração, revisão e download, sem bloquear esse piloto. A aprovação
da peça é independente de postagem. O backlog após os sete itens é proposta a
priorizar pelos resultados do piloto, sem novo escopo fechado. O trabalho
atual preserva autorização, identidades e reservas do ensaio Intensa/Dog/Luma;
resultado incerto continua sem retry. Outras rodadas pagas precisam de orçamento
específico. Dúvidas serão tratadas em entrevista e os avanços comunicados.

## 06/11/2026 — ciclo de revisão em Python/API

O titular priorizou ensaiar revisão iterativa de Reel em Python/APIs: gerar,
renderizar, inspecionar, corrigir e renderizar, sem servidor Claude Code ou
agentes hospedados. Usar composição inicial histórica comum aos braços,
crítica por versão, até duas correções e julgamento humano, preservando as
versões anteriores. Não presumir que a última seja melhor. Isso substitui a
prioridade exclusiva anterior do clipe pessoal, cuja avaliação ainda está
pendente. Não habilita produção. Para Intensa/Dog/Luma o titular autorizou até
15 chamadas e US$ 6,75 em reservas, com envio de quadros/contexto/código à
OpenAI; áudio técnico conserva mix/trilha, com escuta humana explícita. Outras
rodadas exigem orçamento e materiais autorizados. O
[desenho](design/ciclo-revisao-motion-2026-11-06.md) distingue a decisão do
trabalho ainda não implementado e da integração posterior.

## 06/11/2026 — uma frente: peça musical pessoal

Priorizar o arquivo fornecido pelo titular, mantendo a performance/áudio e
adicionando narrativa visual ligada à letra. Brabo/Higgsfield são frentes
adiadas, não dependências da peça. Consentimento de fixtures não autoriza envio
da voz/quadros pessoais; apresentar plano de três chamadas e orçamento novo.
Modo pessoal separado não altera guardas sintéticas ou habilita produção geral.
[Plano](evals/plano-clipe-musical-pessoal-2026-11-06.md).
Titular autorizou três chamadas e envio do áudio/quadros pessoais e derivados,
apoios licenciados e código local/MIT, até US$ 1,60 adicionais, sem refação
automática. Não inclui Higgsfield, TTS ou geração paga de imagens/vídeos.
Peça entregue com fonte pessoal e apoios licenciados; direção recebeu revisão
escrita para evitar motion restrito às bordas. Composição final executada sem
alteração visual; áudio original preservado. Aceite criativo continua humano.
[Resultado](evals/ensaio-clipe-musical-pessoal-2026-11-06.md).

## 06/11/2026 — step 1 com foco de marca e experiência

Para Dog/Luma, titular confirmou foco de marca/experiência sem preços, com
material ilustrativo e sem afirmar trabalho real dos negócios. Intensa orienta
o nível; direção/kit continuam próprios. Dois clipes individuais Pexels podem
ser usados para edição pontual por inferência conforme revisão fundamentada
do §5/§8/FAQ; não há coleta em escala ou desenvolvimento/treinamento de modelo.
Não é liberação irrestrita nem autorização para reenviar Papel incerto. O novo
[plano](evals/plano-motion-outros-negocios-2026-11-06.md) foi autorizado: duas
chamadas/envio dos pacotes, até US$ 1,50 adicionais, sem refação automática.
Foram entregues os dois Reels, estimativa US$ 0,5906725. Dog teve tradução
estrita de IDs de áudio e render offline, sem modificar o visual ou repetir
geração paga. Resposta/falha originais preservadas. Titular gostou bastante e
declarou que mantiveram o nível da Intensa; duração curta considerada boa.
Mesma música apontada como possível problema: os pacotes só ofereciam uma
trilha obrigatória. Seleção automática entre faixas licenciadas adequadas é
pendência a qualificar. Titular confirmou: IA escolhe conforme negócio e peça,
varia entre pedidos e pode repetir em séries/campanhas com continuidade. Não
exige música inédita em toda peça. Seleção/histórico seguem pendentes de implementação.
[Resultado](evals/ensaio-motion-outros-negocios-2026-11-06.md).

## 06/11/2026 — feedback positivo e sequência de validação

O titular gostou bastante da versão intensa e, após comparar a diversidade,
declarou-a a melhor até agora, sem adoção universal. Autorizou seguir a sequência: linguagens distintas no mesmo
material, outros negócios fictícios, story e carrossel, preparando a integração
posterior. Para Dog em Casa e Estúdio da Luma escolheu vídeos ilustrativos
licenciados; não simular que fotos sejam gravações. Manter origem e limites de
uso explícitos, inclusive antes de enviar material ao provedor.

Conservar o caminho qualificado com versões, inputs/outputs, código efetivamente
executado, custos e avaliação humana. Não reduzir a integração a um contrato que
apague os mecanismos aceitos. [Registro](evals/motion-registro-de-validacao.md).
Após a preparação, o titular autorizou três chamadas e o envio do pacote,
até US$ 2,25 adicionais, sem refação automática. Duas peças concluídas; Papel
incerto sem resposta/custo salvos, sem retry. Cartaz bem avaliado; Giz menos
convincente pela falta de mudanças de tema e transições no formato do vídeo.
Levar o nível da Intensa aos outros negócios, depois story/carrossel;
não repetir Giz/Papel automaticamente. [Resultado](evals/ensaio-motion-diversidade-2026-11-06.md).
Não confundir preparação, qualidade, integração e backup remoto.

## 06/11/2026 — rodada intensa autorizada e entregue

O titular autorizou uma chamada/envio do pacote intenso, até US$ 0,75 adicionais,
sem refação automática. A peça foi entregue com comparação ao v2 mínimo e à
rodada anterior. Não presumir aceite criativo, estilo padrão ou renovação de
verba para outras tentativas. [Resultado](evals/ensaio-motion-intenso-2026-11-06.md).

## 06/11/2026 — explorar intensidade sem transformar preferência em regra

O titular gostou um pouco mais da peça `276486e3` e mantém a preferência pelo
v2. O pedido de uma versão “exagerada”, com motion mais robusta, abre um ensaio
exploratório; não constitui rejeição da peça nem adoção dessa intensidade para
todos os negócios. Mudanças verde/creme, letras invertidas e o ponto compõem o
feedback a considerar. V2 continua piso de qualidade, sem obrigar cópia.
Revisão criativa permanece no resultado final, sem renovação automática de verba.
[Plano da rodada](evals/plano-motion-intenso-2026-11-06.md).

## 06/11/2026 — rodada adicional pela biblioteca autorizada e entregue

O titular autorizou uma chamada e envio do pacote preparado, até US$ 0,75
adicionais, sem refação automática. O ensaio entregou nova peça e comparação
com v2 mínimo/rodada anterior. Isso não autoriza nova geração nem constitui
aceite criativo ou declaração de superioridade.
[Resultado](evals/ensaio-motion-biblioteca-2026-11-06.md).

## 06/11/2026 — v2 mínimo, sem reprodução da composição

O titular esclareceu: “a ideia não é copiar v2 aprovado. ela é uma versão minima
aceita”. Usar os bons exemplos da biblioteca para uma evolução própria e manter
a demonstração comparativa em HTML da rodada anterior. Isso substitui qualquer
interpretação de preservar o layout/storyboard v2 como base obrigatória; suas
qualidades orientam o piso, sem estilo universal. Revisão humana segue somente
no resultado final. [Plano](evals/plano-motion-biblioteca-2026-11-06.md).

## 06/11/2026 — preferência pelo mecanismo do Reel v2

O titular esclareceu que a peça nova não ficou ruim, mas esperava evolução
maior. Prefere transformação contínua da janela horizontal/vertical, formas
geométricas e pontos nas transições do v2. Isso orienta este benchmark, sem
fixar o mesmo estilo para todos os negócios. Mais fontes e execução fiel
não equivalem a ganho criativo aprovado. O feedback não autoriza nova rodada.
[Evidências](evals/ensaio-motion-comando-2026-11-06.md).

## 06/11/2026 — retomada explícita após reposição de saldo

O titular informou “ja adicionei mais creditos. pode tentar novamente”. A
rejeição 429 anterior permaneceu intacta; a retomada criou nova identidade,
vinculou a evidência de rejeição e usou teto de US$ 0,75 para esta tentativa,
sem retries automáticos. O Reel foi gerado e entregue para avaliação final,
com código recebido preservado e sem ajuste manual. Isso não é aceite criativo
nem renovação automática de orçamento para novas amostras.
[Registro](evals/ensaio-motion-comando-2026-11-06.md).

## 06/11/2026 — comando único e revisão criativa somente no final

O titular escolheu expressamente “Sim, gerar o MP4 e avaliar só no final” para
o ensaio rápido. Essa decisão substitui os portões intermediários de cards e
frames da skill `claude-video` neste modo. Encadear etapas num comando não
significa uma única chamada para qualquer material: a primeira fixture
reaproveita Jev/transcrição e solicita uma composição completa. Orçamento
explícito, resposta bruta, identidade, reserva e ausência de retries permanecem.
Os resultados continuam sujeitos à avaliação criativa humana final.
[Uso](evals/como-executar-ensaio-motion.md).

## 06/11/2026 — orçamento e envio autorizados; cards aguardam aceite

O titular autorizou duas chamadas com teto de **US$ 1,50 adicionais** e,
explicitamente, o envio do pacote local a `api.openai.com/v1/responses`.
Duas rejeições anteriores da revisão automática ocorreram antes de iniciar
o processo, sem envio ou gasto. A primeira chamada concluiu; cinco cards foram
capturados. A segunda continua condicionada ao aceite desses cards e não foi
executada. Não há vídeo novo. [Registro e resultados](evals/plano-retomada-qualidade-motion-2026-11-06.md).

## 06/11/2026 — retomar somente a qualidade criativa

O titular priorizou um ensaio fiel e expressivo antes da integração, com o v2
como patamar mínimo. A sequência proposta começa por um Reel, com a mesma
mídia/kit. Levar a referência
concreta e reutilizar código permitido dos projetos selecionados, preservando
origem e intervenções. A escolha de componentes/estilo continua automática e
coerente com cada pedido; o v2 não vira estilo universal. WhatsApp/Instagram
ficam fora desta prova. Na preparação do [novo plano](evals/plano-retomada-qualidade-motion-2026-11-06.md),
ainda não havia autorização nem execução de nova chamada; a autorização posterior
está registrada acima.

O repositório próprio informado recebeu apenas o snapshot local selecionado,
com licenças MIT preservadas, sem commit/push. A importação não comprova sua
privacidade remota, backup ou direitos de dependências/fontes externas.

## 06/11/2026 — rodada 1c rejeitada; referência v2 permanece

O titular rejeitou a qualidade criativa de todos os formatos 1c: Reel e story
simples demais, carrossel sem movimento perceptível. A preferência pelo Reel v2
anterior permanece; não considerar os derivados 1c aprovados por terem sido
renderizados. Investigar e explicar a regressão antes de promover essa direção
na integração. O feedback não autoriza chamadas pagas adicionais.

## 06/11/2026 — separar derivação técnica de aceitação da direção

As três direções da rodada 1c completaram no provedor, mas foram rejeitadas pelo
contrato local. Correções de montagem ficam em cópias derivadas com cada patch
registrado; não reclassificam o resultado pago, devolvem reservas ou aprovam a
peça. O ajuste de tipografia do Reel é intervenção visual explícita, distinta
das correções técnicas. A versão do contrato e seus validadores permanecem;
esclarecer suas regras no schema/instruções após encerrar a rodada, com testes.
O esclarecimento não constitui correção automática nem prova de confiabilidade
do modelo. Novas chamadas pagas exigem plano e orçamento próprios.

## 06/11/2026 — retomada após rejeição do Reel autorizada

Após o bloqueio da revisão automática, o titular autorizou explicitamente
retomar somente as duas direções ainda não enviadas: story e carrossel.
A autorização permite prosseguir apesar da condição de parada após a rejeição
do Reel, sem repeti-lo e sem refações pagas. Reserva adicional US$ 1,00;
comprometimento planejado global US$ 1,55; teto global mantido em US$ 1,60.
Grant, rejeição e reservas anteriores permanecem preservados, com registro
separado da autorização de retomada.

## 06/11/2026 — continuação motion 1c autorizada

O titular autorizou as sete novas chamadas do [plano 1c](evals/plano-motion-v0-rodada-1c-2026-11-05.md):
três interpretações Jev (incluindo nova interpretação do Reel corrigido), uma
transcrição e três direções. O teto global permanece US$ 1,60; a reserva anterior
de US$ 0,01 é preservada, com limite próprio de US$ 1,59 e reservas planejadas
de US$ 1,54 para a continuação. Sem refação automática. A rodada 1b permanece
encerrada; esta autorização não reclassifica sua resposta nem autoriza postagem.

## 05/11/2026 — rodada motion 1b autorizada

O titular autorizou a [rodada 1b](evals/plano-motion-v0-rodada-1b-2026-11-05.md):
três interpretações Jev, uma transcrição e três direções, com reserva planejada
de US$ 1,54 e teto operacional de US$ 1,60. Sem refação automática. A autorização
é específica dessas sete operações; não autoriza publicação ou novas tentativas.

## 05/11/2026 — proporção do carrossel confirmada

O titular escolheu **4:5 vertical** como padrão inicial de todos os MP4s de uma
sequência de carrossel. Reel e story em vídeo permanecem em **9:16**. Isso não
altera os limites de 3–5 páginas/5–8 segundos nem antecipa homologação de postagem.

## 05/11/2026 — base técnica de Reel com animações nativas aprovada

O titular confirmou que podemos avançar com a base do
[Reel adaptado sem GSAP](evals/ensaio-reel-waapi-2026-11-05.md), após receber
o MP4 e a comparação com o v2. A confirmação vale para esse ensaio: não torna
o estilo universal, não conclui o renderer integrado e não autoriza chamadas
pagas ou publicação. Prosseguir com composição parametrizada, escolha de
direção por pedido e empacotamento/isolamento próprios.

## 05/11/2026 — limite de entrada confirmado na implementação

O titular confirmou o teto de **50 MiB (52.428.800 bytes)** por gravação,
além dos 60 segundos já definidos. Se qualquer limite for excedido, explicar
o limite e pedir uma versão menor; **não cortar automaticamente** a gravação.
Essa decisão fecha a pendência de tamanho e comportamento de excesso registrada
abaixo. Preservação do original e retenção seguem C04/C09.

## 05/11/2026 — geração primeiro; postagem em fase posterior

O titular reviu a exigência de publicação integrada nesta entrega. Primeiro,
concluir a geração das peças finais de imagem, Reel, story em vídeo e carrossel
com motion, incluindo prévia, ajustes, aprovação da peça e download. Só depois
tratar a viabilidade e o fluxo de integração de postagem no Instagram.

Esta decisão substitui o requisito anterior de publicação para concluir a fase
atual de geração. Conta Meta, homologação da API e postagem real não são critérios
de saída dessa fase. A integração de postagem permanece como trabalho futuro,
sem alegar que está entregue. Aprovar a peça final não autoriza publicação:
C11 continua exigindo aprovação específica antes de qualquer postagem futura.
Os demais limites e escolhas da entrevista abaixo permanecem vigentes.

## 05/11/2026 — entrevista de escopo da v0 de conteúdo

- A edição de vídeo recebe inicialmente **uma gravação do cliente por pedido**,
  com **até 60 segundos de material bruto**. O vídeo final também terá no máximo
  60 segundos. O teto de entrada é 50 MiB; excesso pede versão menor sem corte
  automático, conforme confirmação acima. Isso não limita imagens do carrossel.
- **Entrega atual: geração, revisão, ajustes, aprovação da peça e download**
  de imagens feed/story, Reel, story em vídeo e carrossel com motion. A exigência
  anterior de publicação integrada foi substituída pela decisão acima; a
  viabilidade e a integração de postagem ficam para uma fase posterior.
- O carrossel tem **de 3 a 5 páginas, cada MP4 com 5 a 8 segundos**; a IA escolhe
  quantidade e duração nessa faixa conforme o pedido. Validar legibilidade,
  movimento, arquivos finais e custo sem alterar os limites silenciosamente.
- Ao ajustar uma página, **preservar as demais**. Se o ajuste exigir mudanças
  nelas, pedir confirmação antes de aplicar; depois, apresentar a nova versão
  completa para revisão e aprovação da peça. Confirmar o alcance do ajuste ou
  aceitar a peça não aprova publicação futura, que continua sujeita a C11.
- O estilo de motion é escolhido **a cada pedido**, conforme objetivo, material
  e referências, preservando o kit. A v0 guarda snapshots por peça e não fixa uma
  preferência de estilo por negócio com base nas peças aprovadas.
- Preços, franquias e limites comerciais de refação seguem P05, após medição de
  qualidade e custo; não fixar quantidades por inferência.
- O titular autorizou criar um repositório privado próprio no GitHub para as
  fontes adotadas, quando necessário, informando nome e link depois da criação.
  Licenças, atribuições e direitos por material devem ser verificados; nenhum
  repositório de preservação foi criado até este registro.

Essas são decisões de produto a implementar, não capacidades já entregues.
Aplicam-se as regras de retenção C04/C09 e o adiamento de encerramento P03;
não reabrir essas escolhas como se fossem indefinidas.

O titular quer evitar dependência da permanência de repositórios de terceiros. O plano prevê cópias e backups próprios das fontes e dependências permitidas, além do empacotamento do runtime; não afirma que esses backups já existem.

O titular esclareceu que quer **reutilização concreta** dos projetos abertos, além de pesquisa. O plano passa a prever incorporar e adaptar materiais permitidos, com origem, versão e licença; a integração continua pendente.

## 05/11/2026 — plano para a v0 de conteúdo com motion

O titular quer concluir a v0 com imagem de feed/story, vídeo gravado pelo cliente
editado para Reel/story e carrossel com motion. O sistema escolhe e adapta o estilo
sem exigir escolha do cliente. O [plano proposto](design/plano-v0-imagens-video-motion-2026-11-05.md)
detalha a separação entre fontes externas de pesquisa, skills próprias, catálogo
interno, contexto privado e motor candidato, além de fatias e gates. A análise
atual de perfis não mede ritmo, cortes ou áudio; inferência e observação precisam
ser diferenciadas. A entrevista acima definiu uma gravação de até 60 segundos
por pedido. O titular priorizou concluir geração, revisão, ajustes e download,
deixando viabilidade e integração de postagem para a fase seguinte; cotas seguem
pendentes, enquanto 50 MiB e reenvio sem corte foram confirmados acima.

## 05/11/2026 — avaliação de motion com modelos reais

O titular autorizou chamadas pagas e solicitou trace integral de entradas,
prompts, saídas e resultados. O [ensaio](evals/ensaio-motion-referencia-2026-11-05.md)
usou teto operacional de US$ 0,80 em reservas e permanece sujeito à revisão
do titular; essa referência de orçamento não autoriza futuras rodadas.

## 05/11/2026 — proposta de biblioteca de estilos de motion

O titular prefere uma biblioteca interna de estilos escolhidos automaticamente pelo sistema, sem exigir que o cliente escolha. A [proposta](design/biblioteca-estilos-motion-2026-11-05.md) distingue estilo, kit, skill e conteúdo; ainda não determina persistência ou implementação.

## 04/11/2026 — direção para vídeo e motion

Em 05/11/2026 o titular esclareceu que o cliente não seleciona imagens no acervo: pode enviar imagem própria e envia vídeo para edição; o uso do acervo não é pressuposto nesse vídeo.

Os repositórios HyperFrames e Howseen foram estudados como candidatos, não adotados como decisão de produto. O [estudo](design/estudo-hyperframes-motion-design-2026-11-04.md) propõe ensaio direto, além de listar custos, direitos e condições de segurança para eventual integração.

O titular rejeitou as primeiras prévias e pediu repetir pelo procedimento de ensaio rápido, incluindo áudio, cortes, transições, efeitos e legendas dinâmicas. Autorizou até US$ 0,50 em reservas para a nova rodada, aceitando o risco de uma chamada ultrapassar a reserva. Ver [plano](evals/plano-motion-valido-2026-11-04.md); aceite das novas peças permanece pendente.

O [ensaio direto](evals/ensaio-video-motion-2026-11-04.md) preparou uma prévia de vídeo e três páginas animadas para revisão do titular, sem chamadas pagas. Não constitui decisão sobre aprovação visual ou provedor de produção.

O titular esclareceu que deseja decisões criativas de edição e motion por IA; FFmpeg pode ser usado para montar os arquivos. Quer avaliar vídeo de feed/Reel, story em vídeo e carrossel com um MP4 em loop por página, preservando kit, acervo e referências. Escolheu até 60 segundos por vídeo final na primeira versão e testes separados de vídeo gravado e carrossel. A entrevista posterior de 05/11 definiu uma gravação de até 60 segundos de entrada por pedido; tamanho em bytes, custos e planos continuam pendentes. Vídeo gerado e avatar continuam sujeitos a decisões futuras. Ver [estudo](design/estudo-video-motion-2026-11-04.md).

## 04/11/2026 — procedimento para próximos ensaios criativos

O titular pediu que testes de qualidade futuros sejam rápidos e executem as etapas
diretamente, registrando entradas/saídas e peças, sem criar bancos ou montar o
sistema completo apenas para essa avaliação. O [procedimento](design/ensaios-rapidos-qualidade.md)
preserva autorização, custos, identidade e limites. Essa decisão não altera os
requisitos para testar integração, segurança, bancos ou CI.

Ensaio direto BL04.3 realizado em dois pares; o titular preferiu as peças com referências, com revisão completa e aceite final ainda pendentes. Os resultados e a limitação da tentativa editorial estão no [relatório](evals/bl043-reference-quality-2026-11-04.md).

O titular esclareceu que a comparação BL04.3 deve ser direta e rápida: simular mensagem WhatsApp, registrar interpretação Jev e as entradas/saídas editoriais e visuais, sem exigir percurso integral pelo sistema. O teto de US$ 2 em reservas aplicou-se àquela rodada; novas rodadas exigem orçamento próprio, preservando operações incertas anteriores. [Plano](evals/bl043-reference-quality-2026-11-04.md).

## 04/11/2026 — escolhas para preparar a avaliação BL04.3

O titular escolheu o negócio fictício do piloto, um par de feed e um de story, e
um limite novo de US$ 2 em reservas para a rodada inteira incluindo refações;
aceitou o risco de a cobrança do fornecedor ultrapassar as reservas. Autorizou
revisão visual pontual do perfil público, sem arquivar publicações ou repetir
coleta paga, e informou que fará a conferência no navegador. A conferência dos padrões e as guardas do ensaio estão pendentes; orçamento
histórico não é renovado. O [plano](evals/bl043-reference-quality-2026-11-04.md)
registra a estimativa, o limite técnico da reserva e o trabalho restante.

Atualizado em **29/10/2026**, incluindo a primeira imagem paga autorizada pelo
produto (parte 3), o adiamento da recuperação de suporte C10 e a prioridade de
qualidade de conteúdo, skills e pesquisa de referências definida pelo proprietário.
Este registro reúne decisões de produto; implementação e contratos técnicos
ficam no [PROJECT](PROJECT.md), no [SDD](SDD.md) e nos [SDDs de fase](phases/README.md).
Uma decisão aprovada ainda não implementada deve aparecer com esse estado em
todos os consumidores. O texto antigo preservado em histórico não é requisito atual.

## Ordem de leitura e resolução de divergências

1. A decisão explícita mais recente do proprietário prevalece.
2. Este registro define o produto aceito; PROJECT resume o que existe e o que falta.
3. SDD geral e fase ativa definem contratos e critérios da próxima entrega.
4. Designs detalham alternativas e execução, respeitando os documentos acima.
5. Changelogs, evals, auditorias e snapshots são evidências datadas. Um estado
   antigo nesses registros não deve ser copiado como pendência ou regra vigente.

O código comprova o comportamento implementado, mas uma limitação atual não
substitui uma decisão de produto. Quando houver diferença, registrar a lacuna;
não afirmar que documentação, flag ou migration isoladas já a resolveram.

## Conceitos que não devem ser confundidos

- **Conta ativa:** conta não encerrada ou desativada. Pode existir com plano
  vencido; isso não dispensa identidade e membership válidas para consultar dados.
- **Plano ativo:** acesso financeiro vigente por assinatura ou patrocínio. C08
  separa revisão de uma criação admitida das novas criações e da publicação.
- **Arquivo preservado:** bytes e proveniência necessários à revisão. Não
  equivale a uma URL pública permanente, fato atualizado ou publicação aprovada.
- **Aceite de IA:** decisão contratual única. Direitos sobre cada material,
  comprovação de canal e aprovação de uma peça têm finalidades diferentes.

## Decisões confirmadas

### Origem da pesquisa e endereço próprio — 04/11/2026

Ao selecionar endereço em **Origem da pesquisa**, preencher todos os campos
com o cadastro salvo de **Endereço do negócio** e deixá-los somente para leitura.
Se esse cadastro não existir, exigir que o cliente o informe antes de salvar a
origem por endereço. Não oferecer outro endereço editável nessa configuração.
Para referências de outras regiões, manter a indicação manual de @ em
**Perfis que inspiram seu negócio**. A localização atual do dispositivo continua
como alternativa já existente. Essa decisão não altera raios nem ciclos.

### Qualidade, canal comercial e referências — 30/10

O titular pode informar o canal preferido de contato, venda ou agendamento
para orientar as chamadas; esse dado não deve ser inferido do telefone de
identificação. A chamada depende dos canais realmente informados e não presume
que uma imagem tenha um botão ou link funcional. Ausência de canal não autoriza
inventá-lo.

Após as correções de qualidade editorial, usar kit independente para QA e
desenvolver com a web duas entradas complementares de referências: perfis
indicados por @ pelo cliente e sugestões de negócios semelhantes obtidas pelo
sistema, apresentadas para aceite. A capacidade de pesquisa, fontes, métricas
e fornecedor ainda devem ser avaliados; uso de referências não autoriza cópia.

| ID | Decisão de produto | Implementação local e limite |
| --- | --- | --- |
| C01 | IA para interpretação, texto, imagem e transcrição integra o serviço. Um único aceite explícito por negócio em Plano e acesso, antes do checkout; contas existentes aceitam a versão uma vez. | GET/POST versionado com hash, ator, data e auditoria; web sem permissões por fornecedor. `visual_ai` exige enforcement do aceite; primeira imagem real executada sob autorização delimitada, sem ativar uso recorrente. Credenciais/orçamento/plano continuam internos; registros antigos não são reescritos. |
| C02 | Cada negócio tem conta de cliente e organização próprias, com cobrança e aceite próprios. | Onboarding cria organização/negócio; API e migration 0057 garantem no máximo um negócio por organização. Cobrança continua por organização. Memberships/seleção legadas e staff são preservados. |
| C03 | Um número de cliente WhatsApp ativo por negócio na primeira versão. | Vínculo único local. Múltiplos números e sua experiência ficam para evolução posterior. |
| C04 | Envios WhatsApp associados ao negócio são preservados sem expiração automática e não oferecem exclusão pelo histórico, para texto, imagem, áudio e vídeo. | Migration 0058 e leitores adaptados; API recusa exclusão. Eventos técnicos não atribuídos e uploads órfãos têm limpeza própria. Preservação não cria automaticamente memória pesquisável ou produto confirmado. |
| C05 | Trocar de número não interrompe o processamento de materiais já associados. A futura prévia e aprovação seguem para o número ativo novo. | Processamento e entrega simulada adaptados. Envio real de candidata WhatsApp pendente. Mensagens ainda não associadas não ganham origem retroativa por suposição. |
| C06 | Alterar kit, foto do acervo ou contexto durante uma criação aguarda os processos iniciados; cancela a fila ainda não iniciada e bloqueia novas admissões até aplicar a mudança. | `visual_fake` e `visual_ai` coordenam contexto, catálogo, kit, fotos e edição/revisão de roteiro pela mesma guarda, com writers financeiros e roles existentes. Novos writers de acesso exigem o mesmo protocolo. |
| C07 | A prévia anterior à alteração continua disponível para revisão e deve ser identificada como anterior à mudança. | Provas e campos de revisão estendidos a `visual_ai`. Preservar para revisão não confirma fatos vencidos, direitos ou aprovação de publicação. |
| C08 | Se o plano vencer durante uma criação já iniciada, concluir e permitir revisar a prévia privada; bloquear novas criações e publicação até renovar. | Implementado em `visual_fake` e `visual_ai`: admissão durável com plano vigente e continuidade/revisão após vencimento financeiro. Bloqueio explícito, revogação de patrocínio e perda de identidade/membership continuam distintos. Novos inícios/publicação exigem plano; renderer local legado conserva seu limite de conclusão. Conexão real validada com HTTP simulado, sem gasto novo. |
| C09 | Preservar as prévias geradas sem expiração automática enquanto a conta estiver ativa. | Prévias concluídas saem do purge por prazo; propostas, roteiro e snapshots referenciados são conservados e a revisão histórica usa links privados. Tentativas visuais iniciadas sem resultado resolvido também são preservadas. `expires_at` continua delimitando criação/aprovação, sem apagar a concluída. URL assinada e validade factual mantêm prazos próprios. Sem exclusão automática após encerramento nesta etapa. |
| C10 | Se quem iniciou uma alteração perder acesso, somente a equipe da plataforma pode resolver a pendência, com ação registrada. | Outro owner já não pode substituir nem descartar a pendência do autor original. **Implementação da recuperação staff adiada pelo proprietário em 29/10/2026**, para evolução de gestão de acesso/suporte; não bloqueia o fechamento da fatia simulada validada. Até lá, a pendência excepcional permanece bloqueada. A proposta de novas permissões não foi aprovada; manter autoria, RLS e auditoria existentes. |
| C11 | Publicação exige aprovação explícita da versão, arquivo/hash, legenda, destino e horário aplicáveis. | Revisão/publicação simuladas locais. Escolher kit, confirmar fato, aceitar o serviço ou permanecer em silêncio não aprova publicação. Meta/Instagram reais pendentes. |
| C12 | A oferta inicial implementada admite foto e story. O escopo de desenvolvimento da v0 foi ampliado em 05/11 para vídeo do cliente em Reel/story e carrossel com motion. A entrega atual conclui as peças finais; viabilidade e integração de postagem ficam para fase posterior. Franquias e preço de vídeo seguem P05; avatar/voz sintética ficam após o primeiro piloto comercial. | O código ainda limita os formatos iniciais; isso não reduz o novo escopo da v0 nem habilita os formatos novos. Não há franquia comercial final nem qualidade homologada. R$ 99/mês e teto total de R$ 50/cliente/mês orientam medição. |
| C13 | Provar a primeira peça personalizada antes de ampliar nichos; fechar BL04, depois a jornada/ajuste/proatividade BL05. | BL01/BL02 e BL03.1/BL03.2 locais; BL04 em implementação. BL03.3, BL06, pesquisa ampla, avatar e expansão multicanal têm etapas próprias. |
| C14 | Priorizar a qualidade da geração e estudar skills reutilizáveis para orientar as peças antes de avançar na jornada completa. Começar por feed e story e avaliar o resultado com o contexto e os materiais de cada negócio. | A skill do formato entra no briefing editorial e na peça integral, versionada por ID/hash; validação de qualidade real e seleção completa no WhatsApp ainda pendentes. O gate BL04.3 permanece. |
| C15 | Após o trabalho inicial de skills, desenvolver pesquisa de referências que combine indicações do cliente com descoberta automática de negócios semelhantes em destaque. Usar referências para orientar a criação sem copiar conteúdo ou identidade de terceiros. | Indicação manual e snapshot implementados localmente. A descoberta automática, a relevância e as métricas ainda precisam ser implementadas e avaliadas; uma indicação do cliente não substitui a descoberta. O titular confirmou a possibilidade de armazenar a nota própria e a associação dos perfis do Apify, e escolheu Jev para avaliar candidatos, não como fonte de dados. |
| C16 | O modelo deve criar o texto da peça, a legenda e o convite à ação a partir do pedido e das referências do negócio; não substituir sua resposta por texto fixo ou fallback do código na geração real. | O briefing com skill usa redação natural e validação de fonte/valores; não comprova sentido ou qualidade e exige revisão humana. Baseline disabled é rejeitado em novas propostas. A avaliação real do novo caminho ainda está pendente. |
| C17 | A geração deve reunir pedido, fatos, kit, acervo pertinente, referências externas aceitas quando disponíveis e skill de feed/story em um briefing; solicitar ao modelo a peça final completa, inclusive texto e identidade, e conferir o resultado antes da publicação. O trace deve permitir examinar a entrada e decisões sem expor dados privados em logs. O caminho visual que gera só fundo e aplica layout fixo deve ser descontinuado para novas gerações. | Novo caminho local com skill, referência do kit, peça integral e trace cifrado. Aprovação via API exige conferência humana por SHA; WhatsApp/web ainda não oferecem o checklist. Sem homologação/ensaio real posterior. Indicações manuais não verificadas e snapshot implementados localmente; descoberta e aceite de sugestões continuam pendentes. Histórico preservado não autoriza novo efeito do caminho antigo. Ideia de concorrentes/fontes do kit fica para estudo posterior. |
| C18 | Promoções, ofertas e horários para uma peça vêm do pedido e das revisões pelo WhatsApp, sem cadastro desses fatos na interface. Uma promoção explicitamente pedida por R$ 19,90 vale para aquela criação mesmo que o catálogo registre R$ 25, sem perguntar sobre a diferença nem alterar o catálogo. Desconto percentual exige preço de catálogo válido como base; ausência ou ambiguidade exige esclarecimento, sem inventar valores. Permanece um campo simples para características gerais do negócio. O titular autorizou remover as informações antigas dessa área sem preservar seu histórico. | Formulários de fatos livres e promoções removidos da interface; palavras e características gerais entram no contexto versionado. Fatos livres antigos do contexto não alimentam novas peças; novos snapshots editoriais ignoram promoções legadas, mantendo a política dos snapshots antigos. Registros físicos históricos não foram purgados. O WhatsApp/Jev ainda não extrai e vincula fatos promocionais e revisões nem aplica todas as regras; a mensagem não atualiza o catálogo automaticamente. |

### Pesquisa de referências — decisões adicionais de 30/10

O proprietário escolheu pesquisa somente no raio solicitado, uma por raio em
cada ciclo, com até dez candidatos por raio e sem promessa de 30 negócios únicos.
A decisão de 04/11 abaixo acrescenta a ampliação automática quando o Google retorna zero negócios.
Em 03/11, o titular esclareceu que o cliente verá até dez candidatos elegíveis,
com até três recomendações do Jev destacadas, mostrando critérios e nota quando houver candidatos
suficientes. O cliente pode escolher de uma a três entre os exibidos.
Falha comprovada não consome a tentativa. Em 03/11, o titular esclareceu que a
primeira confirmação de uma a três sugestões inicia um ciclo de seis meses: cada
raio pode ser pesquisado uma vez nesse ciclo, inclusive outros raios após a
confirmação. Os raios voltam a ficar disponíveis ao fim do prazo original; mudar
endereço ou segmento não libera um raio já pesquisado. A seleção pode combinar
negócios de diferentes raios. Trocar entre candidatas encontradas não renova o
prazo e a seleção permanece após seu fim até outra confirmação; o titular confirmou
que referências ainda selecionadas de ciclos anteriores podem ser combinadas com as
encontradas na nova pesquisa. As referências
@ manuais são adicionais e não contam no limite. Durante o ciclo, não repetir
consultas Apify para negócios já encontrados; é permitido consultar o Apify para
negócios novos encontrados em outro raio e repetir uma tentativa que tenha
falhado sem retornar o perfil. Não haverá pesquisa nacional nova.
Negócios sem Instagram devem ser mostrados e o cliente
poderá informar o @. Um @ indicado pelo cliente já é referência escolhida; isso
não confirma que existe, que pertence ao negócio ou que foi acessado. Sugestões
automáticas, quando existirem, continuam sujeitas à escolha do cliente. Se não for
possível consultar um perfil público por falha ou limite, informar a falha e
permitir nova tentativa posterior.

Em cada rodada, inclusive após seis meses, a lista de até dez será formada pela
mesma regra a partir dos negócios retornados na nova pesquisa Google; não há
mistura automática com resultados antigos ausentes da nova resposta. Um negócio
reencontrado usa a nota mais recente na nova lista, preservando a nota de cada
pesquisa no histórico. Quando uma referência já escolhida ficar fora dos dez,
o cliente decidirá se deseja mantê-la somente no início de uma nova rodada após
os seis meses. Consultar outro raio na mesma rodada não repete a pergunta. O fake
ainda não implementa essa jornada de confirmação nem uma lista real de dez.

O serviço de contexto aceita novas escolhas somente locais de 5, 20 ou 50 km.
Configurações nacionais e raios antigos permanecem quando iguais ou omitidos;
`null` explícito os remove. Replays e alterações pendentes já admitidas mantêm
compatibilidade. Essa validação não ativa a descoberta real.

Para sugestões automáticas, o proprietário escolheu que Jev avalie semelhança
com o negócio e elimine candidatos inadequados antes de pontuar os restantes,
apresentando critérios e nota para cada destaque. Isso depende de fonte e uso
permitidos e ainda não está implementado. Avaliações de estabelecimentos não
medem engajamento social.
O titular autorizou guardar temporariamente até vinte Place IDs e notas para
recuperar uma pesquisa; notas só são calculadas após o filtro de semelhança. A
lista apresentada continua limitada a dez e entradas Google como estrelas,
contagem e nome não são guardadas.
O titular quer guardar os até dez negócios apresentados por pesquisa, incluindo
Place ID, pontuação própria e perfis disponíveis, para permitir trocas sem nova
consulta. Em 03/11, o titular confirmou que, dos dados Google, somente o Place ID
será guardado; estrelas e quantidade são entradas para o cálculo, não campos
persistidos. Confirmou também o armazenamento da nota própria e da associação
de perfis obtidos pelo Apify e informou já ter verificado essa possibilidade.
O nome apresentado virá do Apify quando disponível; na ausência, mostrar o
perfil ou outro identificador disponível sem guardar o nome oriundo do Google.
Nesta primeira versão, perfis descobertos são somente do Instagram. O titular
esclareceu que um único perfil retornado pelo Apify deve ser usado como perfil do
negócio e analisado automaticamente, sem exigir confirmação do cliente; a origem
continua atribuída ao Apify e não representa verificação independente. Havendo
vários perfis, usar o principal indicado pelo Apify ou, se não houver indicação,
o primeiro retornado, preservando a ordem da fonte. Se as sugestões estiverem incorretas,
o cliente pode informar outro @ manualmente. O titular deseja analisar
até 20 publicações recentes do feed por perfil escolhido via Apify, incluindo
imagens e legendas públicas acessíveis quando disponíveis. Guardar somente
padrões e aprendizados extraídos, sem cópias dos posts; usar o material acessível
quando o retorno for parcial e informar que a análise foi parcial. A atualização
dos padrões é automática a cada seis meses.
Para destacar até três negócios, Jev considerará semelhança e nota. Serão exibidos
os critérios avaliados e a nota, sem frase explicativa livre; candidatos cuja
semelhança o Jev não consiga avaliar ficam fora das sugestões.
Em 03/11, o titular decidiu que o Jev combina semelhança e nota para os três
destaques e desempata por semelhança quando houver empate na décima posição.
Confirmou os raios 5, 20 e 50 km; quando os seis meses terminarem, o cliente
escolherá quando pesquisar novamente. Negócios sem estrelas ou avaliações ficam
fora da lista até haver dados suficientes para a nota. Titulares ativos da mesma
organização compartilham pesquisas e escolhas do negócio. O próprio negócio do
cliente deve ser excluído das sugestões; o titular autorizou identificá-lo
automaticamente por nome e endereço quando houver correspondência clara e pedir
confirmação apenas se houver dúvida.
O titular esclareceu que o endereço e as coordenadas do próprio negócio devem
permanecer no cadastro; a orientação anterior de apagá-las após a pesquisa foi
revista. Na análise do Instagram, escolheu aprender
tom, temas, formatos e elementos visuais gerais, considerando todas as imagens
acessíveis de cada carrossel. A primeira análise de um perfil recém-escolhido
ocorre após a confirmação e sua atualização é a cada seis meses. A conclusão
estruturada de semelhança do Jev pode ser guardada para recuperar uma falha sem
consultar Google novamente. Se o Jev não resolver um empate, prevalece a ordem
da resposta Google. O titular autorizou testar Jev ou outro modelo de visão
econômico, escolhendo conforme qualidade e custo.
O titular esclareceu que deseja usar o Apify pelo fluxo de chamada e resposta,
sem etapa obrigatória de exclusão nos servidores do fornecedor. Nossa plataforma
manterá os perfis associados e aprendizados autorizados, sem persistir as
publicações coletadas.
Escolheu testar uma pontuação própria de 0 a 10 com nota e quantidade, sem
armazenar os campos originais; a decisão anterior que impedia pontuar negócios
com menos de dez avaliações foi revista. Eles também podem receber pontuação;
sem média ou avaliações disponíveis, a implementação atual não calcula nota e
omite o negócio, conforme confirmação do titular. A expectativa de que a maior parte dos resultados tenha notas altas
não institui filtro mínimo de 8. Negócio sem Instagram, mas com dados para ser
pontuado, continua elegível para o cliente indicar o perfil.
Nos exemplos, qualidade deve pesar e mais avaliações devem aumentar a
confiança: 1 estrela indica qualidade muito baixa, sem exigir zero exato, e 4,8 com milhares deve superar
5,0 com 11 avaliações. O titular escolheu continuar os testes com a segunda
fórmula; a descoberta fake usa apenas semelhança predefinida e dados fictícios,
ordenados pela pontuação experimental sem arredondar. Em 03/11, o titular confirmou
que deseja continuar testando e calibrando a fórmula antes de defini-la. O peso,
a escolha final da fórmula continuam abertos.

O limite de gastos escolhido combina teto por pesquisa, teto mensal total e
tetos por fornecedor, com mês em UTC. A etapa já admitida pode concluir após
revogação do acesso; novas etapas não devem ser admitidas. Os valores precisam
ser configurados internamente antes de ativar fornecedores. Uma fundação local
de política versionada e efeitos fictícios foi testada sem conexão externa;
conciliação com evidência e integração de efeitos reais continuam pendentes.
O titular autorizou um primeiro teste real controlado de até US$ 5 no total,
somando fornecedores, e indicou que os limites mensais por fornecedor serão
definidos após a recorrência do produto. Não confundir
essa intenção com uma política financeira ativa ou autorização para conteúdo de
clientes nos testes de fundação.

Google Places é o caminho a estudar para descobrir negócios e Apify uma opção a
avaliar para enriquecer perfis; uma prova isolada de sites foi autorizada e
executada. A prova limitada do Places não comprova cobertura, correspondência de
perfil, engajamento ou custos. O titular confirmou a possibilidade de guardar os
campos descritos acima; limites financeiros precisam ser configurados antes de
uso real no produto. Geocodificação e confirmação
do ponto manual permanecem pendentes. Google Geocoding foi escolhido para estudar
a resolução; seu adapter está desativado, sem guardião de custo ou integração.
A indicação manual e seu snapshot no briefing/trace foram implementados
localmente. A infraestrutura simulada, desligada por padrão, exercita as regras
de raios, confirmação, bloqueio, troca e preservação com fixtures anônimas e
Temporal; a descoberta e o aceite de candidatos reais não existem. Os adapters
Places multitype, Geocoding, perfil e Place ID via Apify, e mapeamento de tipos
com Jev estão isolados e desativados; autorizações, guardiões reais de custo e
integração continuam pendentes. Um retorno de perfil não encontrado de fonte
não comprovada não é prova de inexistência. A associação real e a retenção dos
datasets externos ainda requerem tratamento técnico.

## Perguntas resolvidas nesta revisão

| Referência da pergunta | Resolução |
| --- | --- |
| P01 — plano vencido durante criação | Respondida pelo proprietário; C08 aplicada nos caminhos `visual_fake` e `visual_ai`, com os limites descritos acima. |
| P02 — prazo das prévias | Respondida pelo proprietário; C09 aplicada às prévias concluídas e sua proveniência. |
| P04 — autor sem acesso com alteração pendente | Regra C10 confirmada; implementação de suporte adiada em 29/10/2026. |

Não reapresentar essas perguntas como dúvida de produto. Restam os limites de
implementação e validação descritos acima; isso não autoriza remover verificações de
identidade, direitos, assinatura, orçamento ou versão sem uma solução equivalente.

## Priorização de C10 — 29/10/2026

O proprietário decidiu registrar e implementar futuramente a recuperação de
pendências de autores sem acesso. Essa exceção administrativa não é necessária
para encerrar a fatia atual de admissão, continuidade financeira e preservação
com provedor simulado, já validada. A regra de recuperação exclusiva de staff
continua aceita; sua implementação sai da próxima fatia obrigatória.

Se a exceção ocorrer antes dessa entrega futura, conservar a pendência bloqueada,
sem aplicação automática, troca de autoria ou ampliação de permissões. A proposta
[de suporte restrito](design/BL04-staff-recovery-review.md) fica preservada como
referência futura, sem aprovação de funções privilegiadas ou grants. O adiamento
não encerra a BL04 nem libera o provedor real, que mantém os demais gates técnicos.

## Pendências delimitadas

| ID | Tema | Tratamento e momento |
| --- | --- | --- |
| P03 | Prazo de exclusão dos envios e prévias após encerramento da conta. | O proprietário decidiu **deixar pendente da fase de encerramento** e não implementar exclusão automática nesta etapa. Não escolher prazo ou prometer retenção pós-encerramento. Não bloqueia a BL04 para conta ativa. |
| P05 | Franquias, revisões, preço/volume de vídeo, cadência e custo comercial. | Definir com qualidade e custo por peça aceita medidos em BL04.3/F07; não fixar números por inferência ou com base em uma chamada isolada. |
| P06 | Recuperação da organização legada sem negócio. | Lacuna de implementação/UX: definir percurso que preserve organização, auditoria e histórico financeiro, sem loop entre onboarding e seleção. Não autoriza excluir ou atribuir dados automaticamente. |

Contratos comerciais definitivos, homologação Meta, staging e recuperação
operacional são entregas de prontidão, não prova já obtida nem motivo para
pedir outra autorização individual de IA ao cliente.

## Próxima entrega após a primeira imagem da parte 3

O modo `visual_ai` já conecta API, dispatcher, workflow/worker, runner e adapter
à guarda concreta, usando o aceite único C01. O percurso usa HTTP simulado nos
testes com PostgreSQL e Temporal locais; validação final da parte 2 aprovada.
Na parte 3, o proprietário autorizou Café do Cedro com foto CC0/logo, teto total
de US$ 1 e uma imagem, sem publicação. Uma chamada de imagem real concluiu a
prévia privada; duas interpretações Jev integraram a mesma autorização. Estimativa
total de uso: US$ 0,029701, sem comprovação de fatura ou margem. A reserva visual
incerta permanece no ledger, e a candidata aguarda decisão. A flag persistente
continua desligada; a autorização é delimitada, sem novo orçamento recorrente.
Registro em [evidência da parte 3](evals/bl042-first-product-image-2026-10-29.md).

A próxima preparação é estudar e desenvolver skills de **feed e story**, com
avaliação comparativa inicial da geração. Depois do trabalho inicial com skills,
pesquisar referências tanto indicadas quanto descobertas automaticamente e avaliar
seu uso na geração; a pesquisa não depende do fechamento do gate comercial.
**BL04.3** continua exigindo revisão do feed e post/story com titular, medindo
qualidade e custo por peça aceita, antes da liberação. BL05 fecha a jornada WhatsApp
de prévia/ajuste/aprovação e proatividade. As fases propostas e seus gates estão em
[skills e referências editoriais](design/skills-e-referencias-editoriais.md).
Novas chamadas exigem autorização apropriada às fontes e ao teto; a existência de
saldo estimado não concede gasto.

Um único repositório com uma pasta por skill é uma **recomendação** para estudo,
não decisão sobre criação, visibilidade, licença ou distribuição. Instalar uma
skill em um agente não a integra automaticamente à API do produto. O titular já
confirmou o armazenamento autorizado de Place ID, nota própria e associação de
perfis; não é necessária nova validação dessa decisão. Integração técnica,
critérios pendentes, cobertura e custos continuam a ser avaliados nas fases.

A admissão revalida proposta/fontes/aceite/plano antes do run durável; reserva e
fence continuam em outra transação/role. A recuperação exige prova de ausência
de tentativa/reserva e encerramento da prévia antes de liberar o run original,
com replay somente da reconciliação. `visual_ai` usa tentativa única e ID Temporal
estável; confirmação perdida ou resultado incerto não autoriza redispatch ou
troca automática de provedor. Prévias concluídas ficam revisáveis com a execução
desligada, conservando identidade, acesso, fontes e prova durável. C10 continua
adiada. A migration 0059 foi aplicada ao banco local da aplicação para a execução
da parte 3, sem novos grants ou código de produção. Meta de entrada/canal foi
sintética, entrega da candidata simulada e publicação nula; não afirmar WhatsApp
completo ou homologação. Validação dirigida aprovada: 94 unitários, lint/types
(151 módulos), sem mudança de código. Consulta/download owner funcionaram com
execução desligada e limites zero; o último CI completo é o da parte 2.

## Esclarecimento de jornada — 29/10/2026

O proprietário reafirmou que a IA cria o roteiro a partir da mensagem WhatsApp e
do contexto do negócio. O cliente revisa a prévia e pede ajustes; o editor manual
existente é ferramenta interna do laboratório DEV, não uma etapa da jornada do
cliente. A coordenação dessa ferramenta integra a proteção de fontes da parte 1.
Quando outra alteração já aguarda aplicação, o laboratório conserva o formulário
e pede retry depois; não cria um segundo comando conflitante. Isso é tratamento
técnico interno, sem nova decisão de produto, editor obrigatório ou entrega do
ajuste automático WhatsApp, que permanece BL05.

## 04/11/2026 — ausência de resultados e ampliação do raio

Se o Google retornar zero negócios no raio de 5 km, tentar automaticamente
20 km; se continuar vazio, tentar 50 km. Inícios em 20/50 km só ampliam para os
raios maiores ainda disponíveis. Se as três buscas terminarem sem resultados,
mostrar a ausência e permitir nova tentativa, sem iniciar o ciclo de seis meses.
Não confundir esse caso com uma nota mínima: não existe nota de corte. A mesma
ação continua sujeita aos limites financeiros, incluindo seus raios sucessores.
Implementação integrada em 0107 e coberta pelo CI final de 4.724 testes/100%.
O comportamento vazio foi validado com fixtures; o ensaio real retornou negócios.

### 2026-11-04 — Loja própria e ampliação quando Google retorna vazio

- Manter exclusão automática da própria loja quando nome/endereço correspondem claramente; perguntar apenas na ambiguidade. Guardar somente Place IDs e conclusão própria para recuperação, junto das notas e julgamentos autorizados.
- Na resposta realmente vazia do Google, ampliar 5 → 20 → 50 km automaticamente, respeitando cache, ocupação do raio, ciclo e um mesmo teto de custo. Iniciar em 20 ou 50 amplia somente para raios maiores da lista aprovada. A preferência do cliente não é alterada.
- Se os raios disponíveis terminarem vazios, informar ausência. Uma rodada não confirmada pode ser tentada novamente sem iniciar seis meses; ciclo já confirmado não é liberado por resultado vazio de outro raio.
- Rodada inteiramente vazia conserva escolhas anteriores. A pergunta de retenção só será exigida quando houver uma lista nova utilizável para confirmar.
- Revisão da loja pode ser confirmada por qualquer titular ativo. A autoria da decisão é auditada, mas a execução mantém o ator original e seus bloqueios de revogação.

### 04/11 — aplicação das decisões de análise aceitas

- A versão de associação da referência é positiva desde o perfil original Apify;
  ela muda quando o perfil escolhido muda ou é novamente selecionado após remoção.
- A próxima análise usa aceite + N períodos de seis meses em UTC, preservando a
  âncora original após o ajuste de dias de fevereiro. Atraso não gera coletas de
  compensação para todos os períodos passados.
- Falta de orçamento/configuração conserva a janela para retomada. Um resultado
  indisponível permanece explícito mesmo quando a próxima atualização está agendada.
- O nome do perfil vindo da resposta Apify já necessária pode ser conservado junto
  da análise, inclusive quando nenhuma publicação pôde ser analisada. Não se faz
  nova chamada apenas para obter o nome. Padrões não incluem conteúdo publicado.

Estas são aplicações técnicas das respostas já aceitas sobre perfis, retenção,
aceite e atualização; não alteram o ciclo de busca Google.

### 04/11 — autoria direta e capas de vídeos no feed

O ensaio encontrou carrosséis em coautoria explícita e Reels no perfil escolhido.
O filtro inicial considerava fotos/carrosséis de autoria direta; por isso a
primeira análise real terminou indisponível. O titular respondeu à entrevista:

- Usar somente publicações de autoria direta. A presença em coautores ou pessoas
  marcadas não substitui a autoria informada pelo Apify.
- Para vídeos e Reels, analisar a capa e a legenda disponíveis, sem analisar o
  vídeo em si. Em carrosséis, a imagem de capa de um item de vídeo também pode ser
  usada; o arquivo de vídeo não é baixado.

O adapter aplica o mesmo vínculo de perfil a fotos, carrosséis e vídeos. A análise
de capas conserva estado parcial porque não inclui o conteúdo audiovisual.
Publicações e mídia continuam apenas em memória; persistem os padrões derivados.
Resultados já concluídos e seus prazos não são reescritos pela mudança de filtro.

### 04/11 — retomada documentada da avaliação BL04.3

O titular solicitou que os quatro passos discutidos para BL04.3 e o ponto de
retomada fossem registrados nos SDDs, para continuar em outro chat: conferir
aprendizados, comparar com/sem referências, avaliar peças com o titular e
corrigir/repetir medindo qualidade e custo. O
[SDD ativo](phases/BL04-context-and-ai-production.md#quatro-passos-da-avaliação)
detalha entregas, primeira ação e evidências anteriores.

Esse registro não escolhe corpus, quantidade de tentativas, modelos novos nem
teto de gasto do ensaio. Preparar um plano concreto e consultar o titular em
entrevista sobre escolhas ainda abertas, preservando autorizações aplicáveis.
Não repetir as decisões já respondidas da feature de referências. Nenhuma peça
nova, chamada paga ou avaliação humana foi executada nesta atualização documental.

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

