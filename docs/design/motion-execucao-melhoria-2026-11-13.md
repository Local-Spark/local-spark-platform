# Execução da melhoria de motion — 13/11/2026

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

**Resultado registrado antes da reprovação:** entrega local completa em `cafe-pausa-final.mp4`, fluxo
nativo concluído, comparação e relatório privados na raiz desta rodada.
`make ci`: 6.351 testes, 100% linhas/branches. Seis chamadas, US$ 1,286597
estimados de teto US$ 12,50. Melhora visual observada com limites; aceite do
titular e escuta pendentes. Seções intermediárias abaixo preservam a cronologia
e seus estados; não renovam autorizações ou reabrem gates já encerrados.

Trabalho local autorizado na sessão de 13/11. Após esclarecimento dos custos,
o titular autorizou explicitamente o teto novo de US$ 12,50 para o ciclo completo.
A execução nativa começou após CI aprovado. As continuações implementadas
depois também passaram pelo CI completo: 6.337 testes, 100% linhas/branches.
Este registro acompanha o roteiro de sete etapas, sem substituir o aceite visual.

## Baseline conferida

Árvore Git inicialmente limpa. Conferidos feedback vinculado ao SHA do MP4,
folha temporal da prévia, entrada v9 e contratos de construção/revisão.
A prévia reprovada continua evidência de avaliação, fora da entrada de geração.
Inspeção por quadros, sem escuta perceptiva ou certificação de fluidez integral.

| Defeito observado | Evidência / causa ou hipótese | Mudança e prova esperada |
| --- | --- | --- |
| Gravação e grafismos separados | Conferido na folha: janela superior, desenho lateral e campo inferior. O contrato já permite outra visibilidade; não é limitação de Python. | Qualificar passagem por máscara/oclusão e composição em camadas no renderer; observar mídia e texto compartilhando atenção no MP4 final. |
| PAUSA/campo permanecem entre aproximadamente 4,7–8,4 s sem informação nova | Conferido nos quadros; intenção já presente no plano. Fidelidade não poderia corrigir direção insuficiente. | Planejar contribuição de conteúdo, protagonista e material por momento; crítica deve poder pedir revisão de direção, preservando o plano anterior. |
| Xícara com pouca presença material | Feedback do titular; ativos da rodada eram vídeo, sons e fontes. Ausência de imagem limita algumas direções, mas não explica todo acabamento. | Dependências de material explícitas e validadas antes de código; não substituir silenciosamente material faltante por desenho. |
| Passagens com pouco impacto | Campo cresce/recolhe sem desenvolver outra situação. Ausência de repertório visual no payload é comprovada; causalidade exclusiva é hipótese. | Exemplos originais executáveis, com estados de origem/travessia/destino e proveniência seletiva; verificar aplicação no resultado completo. |
| Inspeção insuficiente | Teto de três eventos/20 imagens e max_corrections=0; prévia privada não passou pela crítica nativa. | Seleção por risco/evento, cobertura e omissões explícitas; crítica/correção com identidades, limites e retorno ao plano. |

## Estado operacional inicial

A primeira consulta Docker encontrou os cinco serviços restritos ativos, com
uptime de segundos. Foram parados imediatamente conforme instrução do titular.
Não se atribui causa ao reinício sem evidência. Nenhum gasto, migração, commit ou
publicação executado. Infraestrutura de teste anterior estava parada; validação
deve usar infraestrutura dedicada, sem limpar ou migrar banco de projeto.

## Implementação

- `business-reel-v5`: exemplos próprios de tipografia como abertura para mídia e
  passagem em profundidade, com código e duas sequências de seis quadros reais.
  Estudo seletivo R10/R12/R17; nenhum pixel dos 41 vídeos é enviado. Renderer
  `e9884862762529bf49086fb579676a7be15a108a5ac1bb88c7c0f44496a6bf51`;
  MP4 sintético `5ead5523a7d7b980906202f2f9ea2aa63518d028e533739b8fc96b466f77c3c2`.
  Prova local de capacidade, **não** peça da cafeteria ou ganho artístico do gerador.
- Novas capturas de qualidade usam staging/repertório v5 por padrão. Capturas
  antigas e escolha explícita v4 conservam contratos e hashes anteriores.
- `motion_staging` valida correspondência entre cenas, protagonista, materiais,
  intervalos e transições. Dependência indisponível bloqueia implementação antes
  de reservar/chamar o modelo. Contribuição, desenvolvimento e permanência são
  intenções para a crítica observar, sem confundi-las com prova de qualidade.
- Builder envia IDs/MIME/hashes dos materiais reais e amostras da fonte. Não
  oferece segmentação automática, tomadas novas, vídeo gerado ou reconstrução 3D.
- `motion-temporal-v4` seleciona intervalos de encenação e todas as passagens que
  couberem, com prioridade temporal distribuída, até 16 eventos/48 imagens por
  versão. São limites de evidência/custo, não quantidade de cenas/cortes/efeitos
  exigida. Omissões e sequências incompletas ficam explícitas; cobertura incompleta
  não pode receber certificado temporal `pass`. Quadros não provam fluidez integral.
- Crítica identifica `repair_kind`: implementação, direção, material ou incerteza.
  Somente defeito local de implementação pode iniciar correção automática. Rejeição
  major/blocking de direção/material persiste a candidata e crítica e termina com
  `MOTION_PLAN_REVISION_REQUIRED`. `MotionPlanRevision` permite uma nova admissão
  idempotente, mantendo a mensagem e anotando observação vinculada ao hash do MP4.
  É continuação explícita por serviço interno, não novo runner ou aprovação automática.
  Efeitos incertos bloqueiam; reservas anteriores não são liberadas; uma segunda
  revisão de plano é recusada. Cada tentativa mantém checkpoints próprios.
- Temporal, serviços, RLS/owner, ledger, auditoria/outbox e cercas de execução
  existentes continuam responsáveis pelos efeitos. Nenhuma migration adicionada.

## Validação e evidência privada

Raiz: `.local/evals/motion-quality-20261113/`.
`mechanisms-v3/` contém MP4 sintético e 12 quadros inspecionados no renderer real;
primeiras duas tentativas locais falharam por configuração de scratch e foram
preservadas. As imagens sintéticas do catálogo são ativos próprios versionados.

189 testes Node passaram com 100% de linhas, funções e branches dos renderers.
32 testes unitários novos passaram; cinco integrações passaram com RLS, checkpoints,
rejeição de direção, orçamento restante e replay idempotente. As integrações usam
provider/renderer de teste, não demonstram qualidade de IA. Regressão inicial de
motion: 1.266 passaram, dois skips. Três módulos novos tiveram 100% linhas/branches
na rodada focada. Os fixtures antigos de rastreio visual foram corrigidos para
o campo `background`; adicionadas verificações de fronteira em áudio, material,
evolução e recuperação já existentes, sem mudar suas regras de produção.
Regressão unitária posterior: 5.349 testes passaram. Artefatos reais anteriores
de plano/composição mantiveram a serialização e os hashes canônicos
(`legacy-compatibility.json`). **CI final aprovado: 6.285 testes, 100% linhas e
branches (22.402 statements / 6.512 branches), lint, tipos e renderer.**
A rodada completa anterior passou 6.243 testes, mas falhou no gate de cobertura
(99,47%). Os gaps foram localizados e receberam testes de fronteira; a rodada
final completa passou. Não foram adicionadas exclusões de produção.
Os testes de fechamento somados à rodada anterior deixaram uma única linha/branch
de proteção da mixagem; o teste dessa última rejeição também passou.

Banco dedicado novo terminado em `_test`, papéis de runtime restritos, schema 0118.
Somente esse banco novo foi migrado. Dev já estava em 0118 e foi apenas lido.
Os cinco containers proibidos permanecem parados. Outros consumidores da mesma
aplicação que reiniciavam foram pausados antes de iniciar PostgreSQL/S3 existentes
para a preparação. Motion permanece globalmente desabilitado.

`preparation-v3/` é a entrada real final desta fatia: captura RLS e leitura dos
materiais pelo produto, builder real com transporte offline, sem admissão. Payload
SHA-256 `50565329d122139b51fae094b8932dc396e70190cef0e4dec109b15a6ed34cf6`.
Mensagem simples preservada, fonte real de 11,176 s / 360×640, 15 amostras;
zero baseline, dois exemplos visuais próprios, dois sons candidatos com relatos
humanos vinculados aos hashes. ASR local novo: 30 palavras, sem revisão humana
atual de texto/tempos. Preflight de admissão conferiu titular, acesso comercial,
consentimento e pendências, apenas em leitura; nenhum pedido ou reserva criado.
Leitura do pedido anterior: estado persistido `running`, checkpoint de render
sem decisão e `rendered=false`, confirmado em `previous-checkpoint-state.json`. Nenhuma imagem gerada ou tomada adicional prometida.

## Orçamento e continuação

Proposta detalhada privada em `.local/evals/motion-quality-20261113/ORCAMENTO.md`.
Novo teto proposto de US$ 12,50, até dez submissões de US$ 1,25 de reserva cada:
plano+código+crítica, até dois pares correção+crítica e uma revisão de direção
com novo plano+código+crítica. Materiais desta direção: US$ 0 em APIs novas,
restritos à fonte, fontes e sons locais e elementos construídos por código.
Nenhuma autorização antiga é reutilizada. Não há liberação de reservas históricas.
O titular pediu explicação do teto, sem autorizar gastos. Esclarecido que US$ 12,50
é reserva máxima de múltiplas tentativas, não custo normal estimado por peça;
alternativa apresentada: primeira peça com crítica por até US$ 3,75 e avaliação
antes de ampliar. Posteriormente, o titular autorizou o teto completo de US$ 12,50:
“certo. pode seguir entao com o teto de 12.50”. Autorização preservada em
`owner-authorization.json`; configurações aplicadas somente ao processo isolado de execução autorizada.
Custos estimados por tokens continuam diferentes de fatura reconciliada.

Com validação e autorização novas registradas: admitir pela operação preparada, executar em
fila Temporal isolada, inspecionar/decidir hashes exatos dos checkpoints, renderizar
peça completa, receber crítica nativa e aplicar somente correções cobertas pelo
contrato/teto. Voltar ao planejamento quando a direção for o problema. Exportar
MP4 nativo, comparação em momentos concretos e custos/limites; aceite visual final
continua pertencendo ao titular. Não declarar conclusão pelo efeito sintético,
contrato preenchido ou teste aprovado. Sem escuta perceptiva da nova mistura até
haver áudio final e evidência de escuta; medições não a substituem.

## Primeira execução e correção de sobreposição

Uma chamada de planejamento recebida: 43.009 tokens de entrada / 12.037 de saída,
US$ 0,227893 estimados, US$ 1,25 reservados sem reconciliação de fatura. A guarda
`MOTION_STAGING_TRANSITION_INVALID` rejeitou indevidamente uma transição iniciada
na entrada da cena seguinte e atravessando a sobreposição até depois da saída da
anterior. A regra agora aceita esse intervalo; continua recusando intervalos
sem travessia ou cobertura da sobreposição. Nenhum byte do plano foi editado.

`MotionPlanningRecovery` reconcilia somente plano recebido após essa falha local:
owner/RLS, contexto atual, recibos completos, custos conhecidos, hash exato e
reconstrução semântica de toda a entrada, inclusive imagens. Revalida contratos,
faz somente reconciliação de metadados SQL com auditoria/outbox, preserva falha
histórica e reservas e deixa o checkpoint sem decisão. Não chama provider,
render, ASR ou storage write; etapas seguintes continuam no Temporal existente.
38 testes focados passaram, 100% linhas/branches nos dois serviços. CI completo
da correção em andamento; o CI anterior aprovado não é atribuído a esta correção.

CI da correção aprovado: 6.299 testes em 19m18s, 22.483 statements / 6.540
branches, nenhum missing. A reconciliação real concluiu sem submissão adicional;
checkpoint `a3b9ce7018c453c9e33e7cefc925bab66f7707a45781f730671816220611e0b2`,
plano intacto. Revisão do assistente registrada em `plan-review.json`, incluindo
risco de direção ainda limitada por uma tomada e grafismos simples. Hash aprovado
para construção nativa depois do CI; não representa aceite artístico do titular.

## Executor real e retomada de render

Plano e código foram gerados pelo produto: custo estimado acumulado US$ 0,405106
(duas reservas de US$ 1,25). Checkpoint de código aprovado pelo assistente e
21 quadros nativos inspecionados. Conjunto ainda visualmente contido; autorização
de render não representa aprovação artística. A primeira tentativa completa
falhou com `MOTION_RENDER_EXECUTION_FAILED`, antes de MP4 persistido ou crítica paga.
A imagem antiga continha runner/audio diferentes dos arquivos atuais e não
implementava fingerprints/áudio v2. A prova sintética anterior sem áudio não
qualificava esse caminho completo: limitação operacional agora explícita.

Imagem local atual construída sem novas dependências, por exportação do filesystem
da base existente e cópia dos arquivos atuais já testados. Tentativas de build
por referência da base travaram e foram canceladas, sem resultado reutilizado.
Nova imagem `sha256:fbdc637cfc6c64034f7328dc096c586464030628c23c743a6316e77a90bd6e79`.
Prova sintética completa com áudio v2, 120 fingerprints e medições decodificadas:
MP4 `d943070968fd50a2ab4679b7fc4fed8ba47aed8f480338c493217301cc91d56d`,
em `.local/evals/motion-quality-20261113/renderer-audio-proof/`. Não é peça do cliente.

`MotionRenderRecovery` permite uma continuação explícita após falha local de render:
owner/RLS/contexto/board exato, nenhum efeito pago ou upload incerto, custo
conhecido e nenhuma versão persistida. Marca o recibo antigo como falha local
recebida, sem inventar saída, registra imagem substituta e evento auditado, e usa
novo namespace para render/upload. Plano/código/custos/decisões e snapshot inicial
permanecem intactos; o override de executor é explícito no efeito de recuperação.
O workflow Temporal existente restaura a entrada e prossegue para produção/crítica.
Uma nova falha não autoriza outra repetição. Não há migração ou habilitação global.
18 testes focados passaram com 100% linhas/branches; lint/tipos passaram.
CI completo dessa continuação em andamento; CI anterior aprovado não cobre esta alteração.

A retomada local já produziu a versão 0 nativa, sem nova chamada paga. MP4 em
`.local/evals/motion-quality-20261113/native-evidence/initial/version-0.mp4`,
11,2 s, 336 quadros, 720×1280/30 fps, H.264 e AAC mono 22.050 Hz, áudio 11,176 s.
Decodificação independente integral passou. Diagnósticos: -15,3 LUFS / pico
amostral -3,6 dBFS; sem escuta perceptiva ou aprovação da mistura.
18 amostras nativas do MP4 mais 30 quadros adicionais das duas transições foram
inspecionados, além dos 21 quadros prévios. A passagem barras→colchetes→vídeo
funciona nos estados observados; conjunto permanece visualmente contido, com
pouco desenvolvimento entre 4,5–6,5 s e retorno por fade. Melhora limitada frente
à prévia; não demonstra ainda o patamar visual solicitado. Comparação privada
em `comparacao.html`, apontamentos em `comparison-notes-initial.json`.
O worker Temporal está aguardando CI antes de qualquer nova chamada paga de
crítica; o render local corre em paralelo, dentro do trabalho local autorizado.

## Suspensão do host e continuação da crítica recebida

O CI da retomada interrompeu em fixture de autenticação de outro módulo (401);
o caso passou isoladamente sem alterar autenticação. Logs de energia do macOS
confirmaram várias suspensões no período. São compatíveis com expiração de JWT,
mas o motivo interno do 401 não foi preservado para prova causal. O workflow
Temporal excedeu prazo enquanto o guard privado aguardava CI; nenhuma chamada
de crítica foi submetida. MP4/recibos recebidos permaneceram persistidos.

Adicionado `MotionReviewRecovery`: continuação explícita de uma única versão 0
recebida, após falha local e antes de qualquer claim/submissão de revisão. Verifica
owner/RLS, contexto, orçamento, todos os efeitos fechados, hash do MP4, bytes,
composição, imagens e executor. Restaura a entrada/board e entrega a candidata
recebida à crítica no workflow Temporal, sem repetir planejamento/código/render.
As correções posteriores continuam com os limites e namespace originais. Uma
nova falha não autoriza repetição automática da crítica. 63 testes focados
passaram, serviço com 100% linhas/branches; lint/tipos passaram. CI final em
andamento. A nova execução só começa após CI; comandos usam inibição temporária
de suspensão enquanto ativos, sem alterar configurações permanentes de energia.

## CI final das continuações e retomada da crítica

`make ci` terminou com exit 0: 6.337 testes Python em 1.275,77 s, 22.688
statements e 6.592 branches, todos cobertos; lint, tipos, 391 testes de avaliação
e 189 testes Node também passaram. Log privado `ci-final-received-review.log`,
recibo `validation.json`, hashes do código em `tested-code-manifest.json`.
Nenhuma exclusão de produção adicionada. Crítica nativa retomada somente após
esse resultado, usando o MP4 recebido, sem refazer plano, código ou render.
Isso comprova validação técnica; avaliação visual e aceite continuam separados.

## Divergência entre crítica nativa e avaliação do assistente

A continuação de crítica concluiu o pedido nativo e selecionou a versão 0. O
modelo retornou `adequate`, quatro checks criativos `met` e nenhum problema.
Essa avaliação está preservada, não representa aceite do titular. Custo do ciclo
até aqui: três chamadas, US$ 0,612391 estimados, US$ 3,75 reservados.

O assistente observa desenvolvimento ainda limitado em 4,5–6,5 s (campo verde,
colchetes e frase pequena, preparo oculto) e 10,667–11,167 s (vídeo, marca e CTA
em áreas separadas). Não declara o patamar solicitado alcançado. O serviço
`MotionPlanRevision` agora também aceita `MotionDirectionObservation` explícita
para pedido concluído e última crítica adequada, com hash do MP4 e dois a oito
quadros distintos previamente vinculados à crítica atual. Essa quantidade limita
evidência, não conteúdo/cenas. Observação é do operador, não do modelo/cliente;
não altera crítica, peça selecionada ou estado do pedido anterior.

A nova admissão mantém a mensagem simples, adiciona observação com proveniência
e conserva a única identidade de continuação. Admission/RLS/auditoria/outbox e
Temporal existentes executam o restante; teto desconta todas as reservas anteriores.
Não adiciona endpoint, runner, migração ou arte manual. Quadros atuais são vínculo
de avaliação, não baseline obrigatório de cliente. Feedback real privado em
`operator-direction-observation.json`, quatro quadros, sem enviar os 41 vídeos.

25 testes focados passaram com 100% linhas/branches do serviço/schema; lint,
formatação e tipos passaram. CI completo `ci-operator-revision` em andamento;
nenhuma chamada paga adicional antes de concluir o gate.

CI completo da observação do operador encerrado com exit 0: **6.344 testes,
100% linhas/branches (22.711 statements, 6.598 branches)**, 1.316,37 s.
Lint, tipos, 391 testes de avaliação e 189 testes Node passaram. Manifesto do
código conferido antes da chamada. A preparação em leitura confirmou US$ 8,75
de reservas restantes. Replanejamento nativo iniciado após o gate; pedido e
parecer da primeira candidata permanecem intactos.

## Orçamento por pedido e recusa anterior a efeitos

A primeira admissão da revisão falhou com `MOTION_CONTEXT_CHANGED`, antes de
admitir execução, criar efeitos ou chamar o modelo. O serviço de revisão reduziu
o teto capturado para US$ 8,75, mas o worker comparou com seu padrão de US$ 12,50.
A integração anterior testava a criação idempotente, sem executar o filho; essa
lacuna foi corrigida por teste que executa o pedido revisado até o checkpoint.

`MotionRequestService.current` agora conserva o teto menor imutável gravado no
pedido/snapshot ao comparar o contexto. Divergência entre esses dois valores,
teto configurado abaixo do teto do pedido ou outras mudanças continuam bloqueando.
Não aumenta orçamento existente nem relaxa fonte, modelo, executor ou acesso.

`recover_admission` admite explicitamente uma nova identidade derivada da
recusada somente com estado failed/CONTEXT_CHANGED, sem admitted_at, peça,
efeitos ou versões. Confere contexto/acesso/owner/RLS novamente, mantém teto
e conteúdo, usa admissão/auditoria/outbox normais. Pedido falho e evento não são
reescritos. Não é retry de efeito externo; o pedido anterior nunca iniciou um.
Repetir a mesma recuperação retorna a mesma identidade.

50 testes focados passaram, incluindo recuperação executada uma vez, recusa de
efeitos iniciados, contexto alterado, teto reduzido e divergência de orçamento.
A cobertura focada inclui módulos legados e é parcial (96%); não substitui CI.
Tipos/lint passaram. Contexto real da revisão foi validado em leitura, teto
US$ 8,75 e zero efeitos confirmados. CI completo `ci-admission-budget` em curso.
Custo inalterado: US$ 0,612391 estimados, US$ 3,75 reservados.

CI final do orçamento/admissão aprovado: **6.351 testes, 100% linhas/branches**,
22.728 statements e 6.602 branches, exit 0 em 1.510,19 s. Lint, tipos,
391 avaliações e 189 testes Node passaram. Manifesto do código conferido antes
da recuperação nativa. A recuperação foi iniciada somente após esse gate;
nenhuma chamada paga na admissão recusada anterior.

## Entrega revisada e avaliação final

Pedido `9491c575-7254-5d20-a88b-628449aa1bc3` e peça
`e44d8c6c-4dd5-5077-be6e-5b3ac96a940b`: `completed` nativo. A admissão
recusada permanece failed, sem efeitos, e a primeira candidata permanece
completed com seu parecer intacto. A prévia local de 12/11 continua separada.

A observação do operador foi conferida no payload real da revisão (43.514 tokens
de entrada, 17 imagens: amostras da fonte e exemplos próprios). Plano revisado
recebido, código e storyboard revisados por hash, composição não editada pelo
assistente. Render e crítica concluídos pelo workflow existente; não houve
correção local de código, pois a crítica não registrou defeito acionável.

MP4 final: 11,2 s, 720×1280, 30 fps, H.264/AAC, 336 quadros e 2.104.629 bytes.
SHA `834fefbcabe842b4e254666ccebb8ee1ee76dc1a7df8b74d69f7b2524e2b9992`.
Cópia de entrega idêntica ao objeto nativo; ffprobe e decodificação integral
independente passaram. Renderer: 336 fingerprints, sandbox/seccomp e zero
solicitações negadas. Voz integral; efeito de servir proposto entre 1,90–3,42 s.
Saída −15,3 LUFS, pico amostral −3,6 dBFS. Sem certificação perceptiva de áudio.

Assistente inspecionou 21 quadros de storyboard e, depois, 18 quadros nativos
decodificados, 36 consecutivos na passagem tipográfica e 27 amostras no fecho.
Ganho observado: preparo maior e presente no trecho central; gravação dentro
dos glifos de PAUSA em 3,57–3,70 s; abertura circular; a palavra Pausa libera
espaço para Café em 8,44–9,44 s. CTA de 40 px e estado final de cerca de 1,4 s,
contra 28 px/0,66 s da primeira candidata desta rodada. Identidade, acentos e
margens conservados nas amostras. Comparação interativa permite confrontar
instantes com a prévia reprovada; comparação intermediária também preservada.

Limites: uma única tomada, composição editorial sóbria, integração tipográfica
concentrada numa passagem breve. Texto e imagem continuam em regiões distintas
em boa parte da peça. Não se afirma equivalência geral às 41 referências,
fluidez integral, ausência de flashes ou melhora perceptiva da mistura. Crítica
nativa final `adequate`, quatro checks criativos `met`, sem issues; não é aceite
do titular nem prova comparativa contra a prévia antiga. A permissividade do
primeiro parecer permanece uma lacuna de calibração. A rodada comprova melhoria
supervisionada pelo processo do produto, sem garantir o mesmo resultado autônomo.

Custos novos: plano/código/crítica inicial US$ 0,612391; revisão completa
US$ 0,674206; **total estimado US$ 1,286597**, seis submissões, US$ 7,50
reservados sob teto de US$ 12,50. Materiais pagos novos: zero. Reservas não são
fatura; não houve reconciliação de cobrança, nem efeito pago sem estimativa.
Os dois pares de correção não foram consumidos.

Entregas privadas: `cafe-pausa-final.mp4`, `comparacao.html`,
`comparacao-inicial.html`, `RELATORIO-FINAL.md`, `delivery-receipt.json`,
`revision-input-proof.json`, checkpoints/criticas e quadros em `native-evidence/`.
Pendências: aceite visual/sonoro do titular, escuta da mistura, calibração da
crítica e avaliação em outras peças/materiais. Sem habilitação global, publicação,
commit ou migração de dev.
