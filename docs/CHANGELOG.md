# Registro de mudanças

## 2026-11-11 — contrato da próxima evolução de qualidade de motion

- Consolidado plano em sete etapas, da direção/repertório ao aceite comparativo,
  com entregas, dependências, evidências e limites de autorização.
- Separados aceite técnico, aprovação de prévias e ganho criativo; comparação
  preserva base e declara diferenças, cobertura, custos e intervenções manuais.
- Registradas dependências reais: asset antes do código, áudio original protegido,
  cobertura de transições e isolamento verificável de correções em código monolítico.
- Tracking, OCR, stock, 3D e EDL definidos como evoluções condicionais.
- Validação documental e diff-check; sem produção, CI, banco, gasto ou render.
  Todas as etapas pendentes. Contrato:
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


## 2026-11-11 — construção de motion em duas etapas

- Novas capturas com direção fornecida usam v3: plano e implementação separados,
  preservados em efeitos cifrados com identidades/reservas próprias. Sem retry.
- Plano validado antes da implementação; montagem restaura áudio, direção e
  metadados autoritativos. Recapturas v1/v2 e correções existentes preservadas.
- Serialização mantém ordem do schema; ledger vincula também o hash dos bytes.
- Exportador distingue planejamento/implementação e aceita plano completo validado;
  mesma entrada Café Pausa preparada offline, com 12 imagens idênticas à anterior.
- Banco dev já estava em 0116; nenhuma alteração nele. Defasagem pertence ao banco
  de testes. Banco temporário criado antes da orientação posterior foi removido;
  nenhum novo será criado nesta tarefa. Testes não foram apontados para dev.
- 23 testes de integração passaram; execução mais ampla parou por Temporal local
  indisponível. Sem CI integral, chamada paga, imagem gerada ou novo MP4.
- 473 testes dirigidos aprovados, cobertura de linhas/ramos integral nos seis
  módulos medidos; Mypy em 15 módulos, Ruff e diff-check aprovados.
- Escopo, validação e pendências: `docs/design/motion-construcao-em-etapas-2026-11-11.md`.

## 2026-11-11 — análise do vídeo Maestros WuzMxEKJHkQ

- Referência baixada com áudio português/legendas; leitura integral da transcrição
  automática, inspeção de 114 quadros distribuídos e seis detalhes em resolução integral.
- Relatório por etapa/ferramenta distingue evidência visual, afirmação do autor e
  recomendação; compara executor, ASR, áudio, percepção e revisão do produto.
- Proposta de construção recuperável no Temporal existente, reaproveitamento de
  helpers e qualificação da moldura/fundo/objeto/fala; sem nova feature implementada.
- Fontes técnicas primárias consultadas; caminhos, metadados e hashes verificados.
  Sem alteração executável, CI, chamada paga, asset novo ou MP4 de comparação.
- Relatório: `docs/evals/analise-video-maestros-WuzMxEKJHkQ-2026-11-11.md`.

## 2026-11-11 — diagnóstico das interrupções de geração

**Análise das interrupções concluída, sem chamada paga adicional.** Retornos
reproduzidos offline no parser: corte em scene_init vem marcado pela API; limites
locais de bytes, orçamento e falta de anexos não explicam a falha registrada.
Identificados saída indivisível, ordenação alfabética do schema colocando código
após plano e reasoning=high fixo. A causa raiz do limite reportado continua sem
comprovação: uso abaixo do teto e dos limites públicos do modelo. Compactação de
20,87% não era prova de conclusão. Próximos passos documentados, não implementados.
Relatório: `docs/evals/diagnostico-interrupcao-motion-2026-11-11.md`.


## Atualização — 11/11/2026

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

## 2026-11-10 — contrato de construção compacto v2

**Contrato compacto v2 implementado; nova comparação preparada, sem execução.**
Representação dos beats reduzida em 20,87% no plano completo da resposta anterior,
com igualdade exata dos 63 movimentos após expansão. Contratos antigos preservados;
mesmas validações e formato completo na persistência/crítica/render. 234 testes
dirigidos aprovados; cobertura integral dos dois módulos medidos, Ruff/Mypy OK.
Nenhuma nova chamada paga ou peça gerada. Entrevista de autorização pendente para
uma tentativa adicional: reservas acumuladas máximas US$ 3,95 no teto US$ 4.
A causa da interrupção anterior permanece indeterminada; redução não garante
sucesso. Detalhes: `docs/design/motion-contrato-compacto-2026-11-10.md`.


## 2026-11-10 — recuperação da comparação encerrada sem MP4

**Comparação das quatro melhorias bloqueada na geração; sem novo MP4.** Duas
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


## 2026-11-10 — preparação da comparação visual e ASR real

**Comparação das quatro melhorias executada; sem novo MP4.** Autorização exclusiva
US$ 4; uma composição tentada, sem imagem ou crítica acionadas. O provedor retornou
MOTION_AI_OUTPUT_LIMIT e JSON cortado após 512,66 s de workflow. Estimativa US$
0,34454; reserva US$ 1,40 preservada. Solicitados 64.000 tokens, reportados 25.722
de saída (15.020 de reasoning); a divergência impede atribuir causa definitiva.
ASR local funcionou: 30 palavras, efeito durável com custo zero. Corrigidos bundle
sem vocabulário e incompatibilidade PyAV reutilizando PCM limitado. 43 testes,
cobertura integral do worker, Ruff/Mypy aprovados. Executor sintético passou.
Recuperação autorizada e iniciada com instrução de código compacto; reservas
acumuladas máximas US$ 3,40 dentro do teto US$ 4;
qualidade das quatro melhorias continua por qualificar. Cinco serviços mantidos
parados. Detalhes: `docs/evals/comparacao-quatro-melhorias-2026-11-10.md`.


## 2026-11-10 — etapa visual 4: ASR local e motion ligado à fala

- Backend local opcional faster-whisper, inspirado no Clipador Viral fornecido.
  Tempos/confiança por palavra, modelo local verificado por hash, subprocesso
  offline com limites, claim/resultados privados e reutilização no storyboard.
  Sem nova API paga, tabela ou runner; pacotes opcionais no uv.lock/Dockerfile.
- Speech_timing revisado, speech_result automático não revisado, vínculo por
  speech_cue_id, validação de fonte/onsets/focos e eventos de crítica priorizados.
  Skill v11 preserva as três etapas anteriores; snapshots antigos não ganham ASR.
- 346 testes Python dirigidos e 11 Node passaram; cobertura integral nos sete
  módulos medidos, Ruff/Mypy e uv.lock offline conferidos.
  Configuração ainda desabilitada; sem instalar modelos, inferência real, chamadas
  pagas, render ou Docker. Comparação depende do OK; vídeos longos/cortes futuros.
- Escopo, origem, ativação e validação: `docs/design/motion-fala-alinhada-2026-11-10.md`.

## 2026-11-10 — etapa visual 3: objeto realista em camadas

- Skill v10 com seleção/proveniência de recorte, material e luz coerentes, helper
  makeCutoutObject para objeto/sombra e critérios de crítica. V1–v9 preservadas.
  Mantidos fundo, moldura, runtime, schema e fluxo de imagens existentes.
- Direção e especificação Café Pausa preparadas para uma imagem conceitual
  reutilizada; removido preenchimento incompatível com cerâmica numa imagem única.
  Asset ainda não gerado; captura exige capacidade/orçamento configurados.
- 131 testes Python e 11 Node passaram; cobertura integral no loader medido,
  Ruff/Mypy aprovados. Sem CI global, chamadas pagas, asset novo, MP4 ou Docker.
  Qualificação visual pendente; etapa 4 aguarda OK.
- Detalhes: `docs/design/motion-objeto-realista-2026-11-10.md`.

## 2026-11-10 — etapa visual 2: fundo narrativo

- Skill v9 com fundo em planos do kit, contraste intermediário, repouso e
  integração com vídeo/moldura. Helper executável makeNarrativeBackdrop usa
  movement-v3 existente; sem novo runtime/schema/serviço. V8 preservada por hash.
- Nova direção Café Pausa acrescenta três fundos, preserva os 16 elementos
  anteriores e coordena as passagens. Pacote offline completo montado/verificado.
- 97 testes Python e 9 Node passaram; cobertura integral no loader medido,
  Ruff/Mypy aprovados. Sem CI global, chamadas pagas, novo MP4 ou acionamento
  do Docker. Etapa 3 aguarda OK; prova visual do resultado continua pendente.
- Detalhes: `docs/design/motion-fundo-narrativo-2026-11-10.md`.

## 2026-11-10 — etapa visual 1: tratamento da gravação; Docker local

- Skill v8 com tratamento de moldura/enquadramento e helper executável transmitido
  ao modelo; runtime v3 preserva border-radius CSS quando não há radius na track.
  Estados explícitos, máscaras e runtime histórico v1/v2 preservados.
- 99 testes Python e 30 Node passaram; cobertura integral nos três serviços
  medidos, Ruff/Mypy aprovados. Direção/brief de Café Pausa e pacote offline
  preparados. Sem geração/render pago ou novo MP4; etapa 2 depende de OK.
- Por pedido paralelo, diagnosticados cinco serviços em reinício contínuo e
  dependências paradas. Titular autorizou pará-los e mantê-los parados; nenhum
  volume/contêiner foi removido, outros projetos não foram alterados.
- Documentação: `docs/design/motion-tratamento-gravacao-2026-11-10.md` e
  `docs/evals/diagnostico-docker-2026-11-10.md`.

## 2026-11-10 — confiabilidade da geração/captura e comparação concluída

- Contrato versionado de saída compacta para direção fornecida; restauração da
  direção integral pelo serviço, sem permitir sobrescrita pelo modelo. Capturas
  antigas continuam reproduzíveis; exportador usa o mesmo montador.
- Uso, estimativa e request ID preservados quando a resposta completa é inválida,
  mantendo evidência privada e holds conservadores, sem retry implícito.
- Limpeza de subprocesso interrompe e drena pipes antes de aguardar encerramento;
  regressão real com saída maior que o buffer.
- Prova local concluiu MP4 em 99,35 s após pausa autorizada de cinco serviços em
  reinício contínuo, todos restaurados ao final. Executor, limites e sandbox
  preservados; 336 quadros, 11,2 s, áudio original conferido por sinal.
- Comparação local identifica origem v6 e reparo anterior de dois intervalos do
  plano, sem alterar HTML/JS. Sem geração/critica paga nesta etapa, sem comprovar
  o fundo/moldura/objeto da direção v7 ou sucesso automático de pedido anterior.
- 441 testes dirigidos passaram; cobertura 100% de linhas/ramos nos quatro
  módulos medidos, Ruff e Mypy aprovados. Sem CI global/SQL. Exportação final
  verificada; saída de exemplo 23,21% menor em bytes, direção reconstruída intacta.
- Plano/evidências: `docs/design/motion-confiabilidade-geracao-captura-2026-11-10.md`.

## 2026-11-10 — alternância de gravação e motion; recorte e crítica

- Não concluído novo MP4: captura local integral atingiu limite de 600 s; captura
  em trechos falhou `MOTION_RENDER_BROWSER_TIMEOUT`. Encerrado processo diagnóstico
  pendente, sem contêineres remanescentes. Três quadros parciais organizados em
  `previas-parciais.html`; não são comparação de movimento nem validação final.
  Sem chamadas pagas adicionais. Investigar captura/cancelamento junto ao gate
  de saída completa antes de outra rodada.

- Recuperação v7 incompleta (`MOTION_AI_OUTPUT_LIMIT`), zero render/crítica no
  fluxo. Total estimado US$ 0,572968; reservas retidas US$ 2,15, workers encerrados.
  Preparada comparação local a partir da primeira saída completa v6, reunindo
  dois intervalos do plano sem alterar HTML/JS. Não é sucesso automático ou prova
  da direção posterior de fundo ativo/objeto realista. Gate de geração permanece.
- Primeira geração completa foi rejeitada por dois beats sobrepostos no mesmo
  elemento, antes de render/crítica. Uso estimado local US$ 0,308018; ledger da
  resposta inválida sem estimativa, reserva US$ 1,40 preservada. Titular autorizou
  recuperação com cena completa/v7 dentro do mesmo teto US$ 3; reservas totais
  máximas US$ 2,90. Sem alteração da guarda, imagem paga ou tentativa automática.
- Feedback durante a execução: fundo vivo e vídeo com variação de escala/moldura,
  além de deslocamento. Skill v7 para próximas capturas; v6 da rodada preservada.
  66 testes de contexto/skills/exportação e dois Node passaram. V7 ainda sem prova
  visual paga; não atribuir sua orientação à chamada anteriormente despachada.
- Skill v6, executor v2 e criativo v6/v7 permitem motion em tela inteira com
  retorno da gravação no tempo absoluto. Duração/ordem/áudio preservados;
  sem transcrição inventada, percentual fixo ou cortes de vídeo longo.
- Runtime movement-v2 não cria clip-path em tracks sem clip explícito; v1 intacta,
  renderer/export selecionam bytes por hash. Repertório v1 validado também na v2.
- Crítica v3 liga checks criativos a issues explicitamente e inclui seus quadros
  reais. Mantém guardas, mínimos temporais e suporte à v2. Sem retry automático.
- 393 testes Python dirigidos, cobertura integral em cinco módulos; 47 de
  contexto/skills após dois casos adicionais. 25 Node, Mypy dos dez módulos e
  Ruff aprovados. Dois quadros sintéticos no Chromium confirmam correção do
  recorte sem remover máscaras intencionais. Sem CI global ou SQL.
- Rodada própria autorizada até US$ 3, uma geração/render/crítica, sem imagens
  pagas. Pedido despachado; resultado em `docs/evals/plano-motion-alternancia-2026-11-10.md`.
- Avaliada a evolução para objetos realistas em camadas: 2.5D aproveita assets
  transparentes existentes; geometria 3D requer estudo separado. Sem assets novos.
- Sequência de fechamento documentada: jornada/ajuste do Reel, fala alinhada,
  story em vídeo, carrossel, qualidade por formato e piloto operacional; postagem
  posterior. Proposta não equivale a implementação ou nova autorização de gasto.

## 2026-11-10 — interação entre mensagem e elementos

- Feedback corrigido: menos infantil não significava remover ícones/setas/xícaras.
  Skill v4 e direção em três momentos relacionam tempo, café e pausa a ações.
  Texto editorial é a base temporal; não alegar sincronismo vocal sem transcrição.
- Primeira tentativa incompleta: `MOTION_AI_OUTPUT_LIMIT`, sem render/crítica.
  Teto declarado 64.000 e saída informada 23.118; causa exata não estabelecida.
- Recuperação explicitamente autorizada dentro dos mesmos US$ 3: geração completa
  e render via API/Temporal, mas vídeo cortado por máscaras de wrappers aninhados.
  Crítica apontou o defeito, porém falhou em `MOTION_CREATIVE_CORRECTION_UNGROUNDED`;
  pedido permaneceu `failed/MOTION_AI_RESPONSE_INVALID`. Guarda não relaxada.
- Variante local corrige somente clipping de quatro contêineres e usa o renderer
  existente. MP4 e comparação entregues com identificação de intervenção manual;
  código/saída automática originais preservados. Sem novo modelo ou imagem paga.
- Skill v5 torna explícitos o cuidado com máscaras aninhadas e o vínculo exato de
  IDs entre check criativo e issue. Default apenas de novas capturas; v1–v4 intactas.
  Sem schema, serviço, tabela, runtime ou ASR novo. V5 sem prova de geração real.
- Reservas acumuladas US$ 2,90; uso estimado US$ 0,758614 incluindo falha inicial.
  Custo da crítica inválida calculado localmente a partir do uso; ledger incompleto
  preservado. Worker encerrado e ambiente temporário removido; saldo não autoriza retry.
- 100 testes Python e quatro Node passaram; cobertura dirigida do loader 100%
  de linhas/ramos. Ruff e tipagem direcionada aprovados. Sem CI global/testes SQL.
  MP4 local 720×1280/30 fps/11,2 s; quadros e sinal de áudio conferidos.
- Resultado e limites em `docs/evals/plano-motion-interacao-2026-11-10.md`.
  Confiabilidade automática e aceite criativo continuam pendentes.

## 2026-11-10 — comparação após refatoração concluída

- Teto novo de US$ 5 autorizado pelo titular: uma geração, render e uma crítica,
  sem refações nem imagens pagas. Uso estimado US$ 0,322005; reservas US$ 2,80.
- Pedido via API/outbox/Temporal, worker com código atual e 12 imagens na entrada.
  Uma versão concluída; worker dedicado encerrado e arquivo de ambiente removido.
- MP4 720×1280, 30 fps, 336 quadros/11,2 s. Crítica `adequate`, sem issues, com
  4.110 tokens de saída, sem truncamento. Não houve crítica comparativa do vídeo
  anterior nem aceite criativo humano; áudio incerto para o modelo, que não o ouviu.
- Checagem curta do renderer, hashes, FFprobe, quadros e comparação do sinal de
  áudio aprovados. PNGs da fonte diferem na codificação macOS/Linux, com pixels
  idênticos; contador do produto usou o corpo real, preservado na evidência.
- Comparação A/B e MP4 entregues em `.local/evals/reel-refactor-comparison-20261110/`.
  Plano/resultado: `docs/evals/plano-comparacao-refatoracao-motion-2026-11-10.md`.
  Sem alteração de código de produção, migração, limpeza ou testes longos.

## 2026-11-10 — preparação da comparação após refatoração

- Plano de uma nova candidata Café Pausa contra a última peça avaliada pelo titular,
  com mesma gravação/voz/kit e configuração histórica do modelo; contexto atual,
  direção em dois momentos e uma crítica compacta. Teto novo solicitado em entrevista.
- MP4 anterior, arquivos do manifesto e ZIP conferidos por hash. Verificador estrito
  da pasta exportada acusa somente arquivos extras; originais íntegros e preservados.
- Sem alteração de código, orçamento reaproveitado, chamada paga, render, assets,
  reconstrução de imagem ou testes longos. Execução e avaliação de qualidade pendentes.

## 2026-11-10 — etapa 6: exportação integral para teste externo

- Titular confirmou a direção Café Pausa da etapa 3. Montador de instruções
  extraído sem regra paralela e compartilhado entre captura e exportação offline;
  corpo final produzido por `OpenAIMotionProvider.build_request`.
- ZIP com 39 arquivos: prompt/contexto/JSON/schema, 12 imagens, direção,
  repertório/licenças, vídeo-fonte, fontes e runtimes. Manifesto distingue o que
  entra no modelo do que fica para execução e registra diferenças do teste externo.
- Contexto factual e seis amostras reutilizados da prova registrada, por hash;
  sem consulta/admissão atual no banco. IDs locais novos, ilustrações desabilitadas,
  sem credenciais ou reaproveitamento de orçamento. Transporte offline bloqueia envio.
- 69 testes curtos aprovados; 100% de linhas/ramos no contexto em cobertura dirigida;
  Ruff, tipos e diff aprovados. Pacote/ZIP real verificado. Sem SQL, CI global,
  rede, contagem remota, geração de assets ou render. Aguardar resultado externo.

## 2026-11-10 — etapa 5: crítica alinhada e resposta compacta

- `motion-review-v2` capturado apenas em novos pedidos: alvo compartilhado de
  acabamento, sem confundir integridade com ganho criativo ou copiar identidade.
- Schema compacto limita prosa/problemas e usa IDs de quadros; serviço expande
  para tempo/SHA no parecer durável e mantém validações. Falha criativa acionável
  deve compartilhar evidência com o problema. Sem referências externas como prova.
- Projeção explícita retira código das composições só para a crítica; correção
  mantém o código. Snapshots anteriores preservados; sem nova tabela/executor.
- 214 testes aprovados, 100% de cobertura dirigida no serviço de crítica/schema
  compacto; Ruff, tipos e diff aprovados. Fixture reduziu 76,1% dos bytes da
  resposta, sem inferir economia de tokens/custo ou garantir ausência de truncamento.
- Teto de 8.000 tokens mantido, sem retry, aprovação ou correção por saída parcial.
  Sem API paga, assets, render, banco ou CI global. Aguardar OK para a etapa 6.

## 2026-11-10 — etapa 4: orientações e exemplos de construção

- Nova skill HTML `instagram-reel-v3` com hierarquia, revelação, camadas,
  profundidade, ação, coordenação, leitura e continuidade da gravação/voz.
  Mapa de uso do repertório sem copiar identidade ou impor efeitos/cenas.
- Dois exemplos originais completos no texto enviado ao modelo, usando MotionV1
  existente. Sem novo componente, runtime, serviço, tabela ou renderizador.
- Recaptura HTML resolve ID/hash já registrados; skills v1/v2 e pacote de
  referências preservados. Texto e exemplos integram a mesma contagem de entrada.
- 170 testes Python e quatro Node aprovados; cobertura dirigida dos dois módulos
  de produção alterados em 100% de linhas/ramos. Ruff, tipos e diff aprovados.
  Sem CI global, banco, APIs, geração de assets ou render. Testes de código não
  comprovam acabamento. Etapas 5–6 pendentes; aguardar OK para a etapa 5.

## 2026-11-10 — etapa 3: direção visual antes da construção

- `MotionRequest.scene_direction` opcional reutiliza o contrato existente;
  snapshot v5 e payload identificam direção fornecida, origem/hash e ausência
  de aprovação. Pedidos sem direção conservam v4 e omitem o novo campo.
- Validação compartilhada impede substituição silenciosa na geração/correção
  antes de imagens/render. Plano temporal e código desenvolvem a direção;
  sem novo planejador, tabelas, chamadas ou executor.
- Direção Café Pausa e briefing revisável documentados, ainda sem aceite criativo.
  Preservam gravação, voz e kit; não repetem as imposições do briefing anterior.
- 228 testes dirigidos aprovados; 100% de linhas/ramos do novo módulo na cobertura
  dirigida, Ruff, tipos e diff aprovados. Sem CI global, banco, API, assets ou render.
  Acabamento ainda não demonstrado; aguardar OK para a etapa 4. Etapas 4–6 pendentes.

## 2026-11-10 — etapa 2: repertório e referências no pedido real

- Seleção explícita `business-reel-v1` no pedido existente; três exemplos
  adaptados de Maestro/Finalizador/claude-video e seis quadros de Felipe Borges
  e Lucas Leite com origem, licença/permissão, tempos, hashes e limites.
- Montador, loader, orquestrador e adapter entregam o pacote no mesmo corpo
  contado e limitado. Referências ficam fora dos assets e das evidências da peça.
- Snapshots anteriores preservados; sem novas tabelas, serviços externos ou motor.
- 163 testes Python e dois Node aprovados; cobertura dirigida do novo módulo
  em 100% de linhas/ramos, Ruff, tipos e diff aprovados. Sem CI global, API real, assets novos
  ou render. Etapas 3–6 pendentes; aguardar OK do titular para a etapa 3.

## 2026-11-10 — etapa 1 da refatoração de motion

- Novos pedidos passam a usar a skill `instagram-reel-v2`, o contrato de
  capacidades `html-motion-executor-v1` e a projeção `html-executor-style-v1`
  das fichas, separando orientações visuais do executor anterior.
- Fontes e hashes históricos preservados; a recaptura mantém o formato de
  pedidos anteriores. Kit, fatos, gravação, voz e isolamento continuam protegidos.
- Passaram 95 testes direcionados de contexto, skills, estilos e adaptador;
  Ruff check/format e `git diff --check` aprovados. Sem CI completo. Etapas
  2–6 pendentes; aguardar o OK do titular para a etapa 2.
- Sem chamada paga, geração de assets ou render; a etapa não comprova acabamento.

## 2026-11-10 — plano de refatoração antes do teste externo

- Sequência vigente em seis etapas documentada: contexto, repertório, direção,
  construção, crítica e exportação fiel da entrada. Implementação não iniciada.
- Titular fará o teste manual em modelo de sua escolha após os ajustes; não
  executar nova produção integrada nem gastar com API/asset/render nesta preparação.
- Exportação deve partir do mesmo montador do produto, com prompt integral,
  schema/parâmetros, anexos e manifesto; diferenças do chat externo explicitadas.
- Sem novo executor, migração ou escopo de edição longa. Validação documental
  por diff; testes curtos serão aplicados às futuras mudanças de código.


## 2026-11-10 — adaptação do fluxo de edição ao Reel do negócio

- Conferidos skill de montagem, princípios, guias de etapas e modelos de estado/
  perfil de Lucas Leite; análise dos vídeos permanece visual por amostragem,
  sem alegar escuta ou transcrição integral.
- Mapeadas oito etapas ao fluxo existente, distinguindo capacidade pronta de
  proposta: direção/plano/código ainda saem juntos; aprovação é posterior.
- Proposto reaproveitar kit, acervo, serviços Python e Temporal; referências e
  instruções selecionadas por etapa, prova curta antes de expandir automação.
- Edição de bruto para YouTube fora do escopo. Sem instalação, código, API paga
  ou CI; ver `docs/design/adaptacao-fluxo-edicao-2026-11-10.md`.


## 2026-11-10 — referências visuais e auditoria do contexto efetivo

- Dois vídeos públicos baixados e examinados por amostragem desde o início, com
  sequências detalhadas e comparação com o MP4 Café Pausa; sem escuta integral.
- Escopo reafirmado: motion na postagem do negócio com gravação preservada;
  edição de bruto para YouTube é ideia separada do titular.
- Chamada real usa gpt-6.1-sol/high, sem referências visuais de acabamento;
  três fichas antigas contradizem capacidades do executor HTML atual. Skill
  integrada não equivale a executar o repertório completo dos pacotes locais.
- Diagnóstico e recorte de correção documentados; sem mudar runtime, instalar
  skills, gerar peça paga ou realizar benchmark de modelos nesta análise.

## 2026-11-10 — vídeo concluído, crítica incompleta e feedback criativo

- MP4 da composição aprovada gerado pelo produto; A/B apresentado. Titular viu
  melhora parcial, mas acabamento infantil e aquém do alvo; não há aceite final.
- Crítica truncada em 8.000 tokens, sem repetição paga. Vídeo/recibos preservados;
  pedido encerrado como `MOTION_AI_OUTPUT_LIMIT` após corrigir colisão de evento.
- Falhas da continuação usam identidade própria em audit/outbox, inclusive na
  quarentena. Migração aditiva 0116 aplicada no dev sem limpeza de dados.
- 69 testes unitários e três SQL no `_test` passaram; Ruff aprovado. Sem CI longo.
- Estimativa da prova US$ 0,775244; reservas retidas US$ 3,40; quatro chamadas
  textuais consumidas, nenhuma imagem paga. Etapa 5 não iniciada.
- Nova análise solicitada: dois vídeos de Lucas Leite sobre edição do bruto,
  sem geração paga nem adoção automática de ferramentas externas.


## 2026-11-10 — aceite dos quadros e continuação do vídeo

- Titular aprovou a versão/hash recuperada. Decisão registrada pela API e evento
  despachado pelo Temporal para render e crítica, reutilizando composição/assets.
- Sem nova geração, imagens ou correção automática; crítica dentro do plano já
  autorizado. Avaliação final do vídeo com som ainda pendente; etapa 5 não iniciada.


## 2026-11-10 — galeria reconciliada sem refazer conteúdo

- Migração 0115 permite os eventos de storyboard omitidos na 0114, preservando
  histórico e RLS. Aplicada no dev sem limpeza.
- Serviço explícito recupera captura inicial integralmente recebida, verificando
  titular, contexto, recibos e SHA fora de locks de IO; registro transacional de
  galeria/auditoria/outbox, idempotente, sem aprovação ou retry pago automático.
- Galeria real do Café Pausa recuperada e aberta para avaliação: três quadros,
  nenhuma nova geração/render/upload ou cobrança. Ponto 4 permanece pendente.
- 44 testes unitários (1,94 s) e dois testes SQL no `_test` (4,08 s) aprovados;
  Ruff/format e mypy aprovados. Sem CI completo. Etapa 5 não iniciada.


## 2026-11-09 — pausa solicitada e ponto de retomada preservado

- Reformulação gerou três quadros reais pelo produto, sem edição manual. Registro
  falhou pela ausência dos eventos de storyboard na constraint do outbox.
- Worker dedicado parado; resposta, PNGs e payload cifrado preservados. Nenhuma
  nova chamada, render, migração ou recuperação iniciada após pedido de pausa.
- Retomada em `docs/evals/retomada-composicao-2026-11-09.md`: corrigir eventos,
  reconciliar captura concluída e obter avaliação humana antes do vídeo.
- Estimativa acumulada US$ 0,596631; reservas US$ 2,55. Ponto 4 pendente; etapa 5
  não iniciada.


## 2026-11-09 — reformulação da composição solicitada pelo titular

- Titular gostou dos desenhos de xícara e autorizou reformular antes do vídeo.
  Novo briefing Café Pausa alterna gesto, transformação ilustrada e pausa, com
  hierarquias distintas; kit, fonte integral, áudio e aprovação preservados.
- Orientação do produto passa a exigir avaliação da evolução espacial/narrativa,
  sem confundir adicionar ícones ao mesmo layout com elaboração visual.
- Vinte testes direcionados passaram em 1,09 s; Ruff/format aprovados. Worker
  atualizado; sem mudar runtime, schema, renderer ou reabrir pedidos com falha.
- Nova execução dentro do orçamento original: US$ 1,70 retidos + até US$ 3,70
  restantes = US$ 5,40, sem aumento ou repetição automática. Pendente nova galeria,
  aceite e vídeo/crítica; etapa 5 não iniciada.


## 2026-11-09 — retomada autorizada e quadros locais de composição

- Geração completa pelo produto; render falhou porque o código colocou tracks
  estáticas sem beats. Esclarecida a exigência de 1–12 beats e hold estático na
  instrução da biblioteca, preservando runtime/hashes e a resposta original.
- Cópia local com apenas esse ajuste técnico gerou três PNGs reais no sandbox,
  sem nova chamada paga; galeria apresentada, decisão visual pendente. O pedido
  integrado permanece encerrado com falha, sem aceite fictício ou reabertura SQL.
- Estimativa da retomada US$ 0,180125; total das duas tentativas US$ 0,421603,
  reservas retidas US$ 1,70. Nenhuma imagem, MP4 ou crítica paga nesta retomada.
- Cinco testes direcionados passaram em 0,68 s e Ruff aprovado. Sem CI completo.
  Ponto 4 ainda pendente; etapa 5 não iniciada.


## 2026-11-09 — ponto 4: preparação e início da prova por cenas

- Ativada no dev a migração aditiva 0114, sem limpeza; reconstruídos worker e
  renderer com fontes atuais e dependências locais, sem credenciais no contexto.
- Verificador do executor passa a testar protocolo de quadros quando habilitado;
  verificação real curta aprovou MP4 e PNG separado. Oito testes direcionados
  aprovados em 0,71 s; Ruff/format e mypy aprovados. Sem CI ou suíte de banco.
- Preparado payload real de Café Pausa; titular autorizou US$ 5,40 em novas
  reservas, incluindo até duas ilustrações opcionais. Execução para na galeria
  para aprovação humana antes do vídeo. Plano em
  `docs/evals/plano-prova-storyboard-integrada-2026-11-09.md`.
- Primeira geração interrompida por saída truncada: estimativa US$ 0,241478,
  reserva US$ 0,85 retida; sem imagem/render/crítica ou repetição. Instruções e
  schema esclarecem IDs globais e tempos absolutos; 105 testes passaram em 1,71 s.
  Retomada autorizada explicitamente e iniciada dentro do orçamento original.
- Pendente: resultado dos quadros, aceite exato, vídeo/crítica e comparação humana.
  Não foi iniciada expansão de formatos nem demonstrada equivalência criativa.


## 09/11/2026 — quadros principais com aprovação humana (ponto 3)

- Captura PNG de cada cena da composição real, sem codificar MP4/áudio; renderer
  protocolo 2 mantém isolamento. Momentos declarados validados antes de gerar assets.
- Galeria privada autenticada e decisão por versão/hash; feedback de reprovação
  cifrado. Pausa durável, retomada pelo outbox/Temporal e reaproveitamento da
  composição/ilustrações, sem nova geração ao aprovar ou reentregar eventos.
- Migração 0114 com RLS; API e configuração de ativação explícita. Não aplicada no
  dev. Renderer precisa de nova imagem/digest; flag permanece false por padrão.
- 295 testes Python em 3,70 s e 72 Node em 0,55 s aprovados; mypy/Ruff aprovados.
  Teste SQL acrescentado, não executado; sem CI completo, API paga ou prova visual.
- Ponto 4 aguarda comando. Quadros aprovam composição, não ritmo, áudio ou vídeo
  final. Uma versão de galeria por pedido; reprovação não gera nova tentativa paga.


## 09/11/2026 — geração de ilustrações integrada (conclusão do ponto 2)

- Declaração de até duas ilustrações na mesma composição; serviço gera PNGs com
  fundo transparente antes do render e entrega miniaturas à crítica/correção.
- Reutiliza adaptador de imagens, ledger compartilhado, efeitos duráveis e storage
  privado. Reserva própria dentro do orçamento do Reel; uso registrado e falhas
  interrompem sem repetição. Reserva não equivale a teto garantido da fatura.
- Correção conserva a lista e reutiliza pixels, sem novas cobranças de imagem.
  Kit, acervo, componentes, skills, motion lib e fluxo Temporal preservados.
- Configuração no overlay e exemplo do worker, desabilitada/sem orçamento por padrão.
  Nenhum ambiente ativado ou chamada paga. Ponto 3 aguarda comando.
- 273 testes direcionados aprovados em 3,76 s; Ruff/format e mypy em 12 módulos
  aprovados. Transporte simulado; regressão SQL adicionada, não executada.
  Sem CI completo, banco, migração ou prova visual integrada nesta implementação.


## 09/11/2026 — componentes e acervo no Reel (ponto 2 parcial)

- Catálogo de 16 objetos vetoriais com partes, desenho progressivo, nós e
  conectores; subconjunto Maestro autorizado, proveniência registrada. Cor/fonte
  do kit, desenho original permitido; sem importar o estilo das referências.
- Contrato `reel-creative-v4` vincula seleção ao catálogo e hash do runtime;
  render isolado incorpora bytes verificados. Revalidação preserva o contrato
  histórico em vez de atualizar silenciosamente pedidos em andamento.
- Até quatro fotos ativas/autorizadas do acervo pela API, com verificação de
  versão/bytes, miniaturas no payload contado e originais privados no render.
- Validação: 307 testes Python distintos aprovados nas verificações direcionadas
  (rodada de 5,07 s e reexecução dos casos ajustados de 0,80 s), três testes Node
  em 0,11 s, Ruff e mypy em 12 módulos. Sem comprovação de cobertura global.
- Ponto 2 parcial: falta geração automática de bitmaps sob demanda. Entrevista
  aberta sobre concluí-la agora ou avaliar composição antes; ponto 3 não iniciado.
- Sem chamadas pagas, migração, banco, render integrado, deploy ou CI completo.


## 09/11/2026 — direção criativa por cena implementada (novo ponto 1)

- `reel-creative-v3` exige `scene-direction-v1` na geração e correção: mensagem
  representada visualmente, composição, ação narrativa e elementos concretos.
- Vínculos completos com cenas/elementos/tempos do plano existente; validação de
  origem e atenção antes de render. Sem novos efeitos ou chamadas obrigatórias.
- Direção preservada na composição privada e revisão; contratos anteriores
  continuam compatíveis. Kit, acervo, skills, biblioteca e limites mantidos.
- 201 testes direcionados em 5,18 s, Ruff/format e mypy aprovados. Cobertura
  100% dos três módulos medidos, sem alegar CI global. SQL acrescentado, não rodado.
- Liberação do conteúdo Maestro informada pelo titular registrada. Sem assets
  gerados, API paga, banco, render ou deploy; passo 2 aguarda comando.

## 09/11/2026 — pesquisa das fontes de arte e componentes de motion

- Inspecionados Maestro, Finalizador e claude-video; extrações privadas com SHA.
- Confirmados objetos recortados gerados, componentes desenhados, takes e
  capturas reais; catálogo Finalizador com 70 entradas, ainda não integrado.
- Consultadas fontes oficiais HyperFrames, Lucide, Storyset e Pexels; anotados
  limites de acesso/licença sem instalar ou executar os pacotes pesquisados.
- Diagnóstico ampliado para arte e composição por mensagem; preservados kit,
  acervo e arquitetura. Sem render, chamadas pagas, alterações de runtime ou CI.
- Validação documental: `git diff --check`.

## 09/11/2026 — feedback recebido: alvo criativo não atingido

- Titular reconheceu melhora parcial, mas falta repertório de componentes,
  ilustrações, imagens e ícones relacionados à mensagem. Não há aceite comercial.
- Feedback preservado no A/B; documentos vigentes e resultado atualizados.
- Auditoria identificou input vídeo/fontes/logo, direção centrada na gravação,
  ausência de transcrição e crítica pouco discriminante para esse alvo.
- Próximo recorte proposto no plano de evolução: representação por mensagem,
  materiais/componentes do kit/acervo, cenas e crítica representativa. Ainda não
  implementado; sem API paga, render, runtime ou testes/CI adicionais.
- Validação documental: `git diff --check`.

## 09/11/2026 — retomada concluída; comparação A/B e limites registrados

- Worker/Temporal dev concluíram geração, render, crítica e download autenticado
  real. Uma versão, duas chamadas/contagens, sem correção; worker próprio encerrado.
- 574,11 s; US$ 0,379066 estimado. Com falha anterior: US$ 0,562636 estimado e
  US$ 2,55 reservado, dentro do teto. Sem fatura conciliada ou nova chamada.
- Crítica adequate, mas janelas cobrem três de 40 eventos e omitem sequências
  próximas das transições principais. A/B aberto; avaliação humana pendente.
- Geração consumiu 18.102 tokens (teto 32.000); crítica 7.924/8.000. Defaults
  gerais preservados. Sem CI completo, publicação ou expansão de formatos.

## 09/11/2026 — retomada autorizada da prova temporal

- Titular autorizou duas chamadas/contagens, geração com 32.000 tokens e zero
  correções. US$ 1,70 em reservas, dentro do teto original. Aprovação vinculada
  ao plano; worker próprio no dev/Temporal existente. Resultado pendente.

## 09/11/2026 — prova truncada; diagnóstico corrigido e retomada proposta

- Geração real atingiu 16.000 tokens, sem JSON completo/render/crítica. Sem retry;
  uma chamada/contagem, US$ 0,85 reservado e US$ 0,183570 estimado dos tokens.
- `MOTION_AI_OUTPUT_LIMIT` preserva uso/estimativa no registro privado, sem liquidar
  reserva ou provocar repetição. 80 testes em 6,05 s, Ruff/mypy; sem CI completo.
- Retomada preparada: geração com 32.000 tokens, duas chamadas, sem correção,
  US$ 1,70 dentro do teto anterior. Aprovação pendente; quarto passo incompleto.

## 09/11/2026 — quarto passo: orçamento autorizado e execução iniciada

- Titular autorizou até US$ 3,40 novos, quatro chamadas/quatro contagens,
  uma correção condicional. Aprovação vinculada ao hash do plano concreto.
- Worker próprio/Temporal local/dev; baseline preservado. Resultado e avaliação
  humana pendentes. Sem retry automático, migração ou CI.

## 09/11/2026 — quarto passo preparado, orçamento pendente

- Café Pausa: baseline preservado, pedido fictício novo admitido no dev e worker
  atualizado/conferido sem rede. Temporal/storage existentes reutilizados.
- Plano propõe US$ 3,40 novos, até quatro chamadas e quatro contagens, uma
  correção condicional. Zero chamadas pagas no preparo; sem CI/migração/limpeza.
- Comparação e avaliação humana ainda pendentes; nenhuma qualidade presumida.

## 09/11/2026 — terceiro passo: evidências e crítica temporal

- Capacidade `motion-temporal-v1`: seleção de até três eventos e 20 quadros por
  versão, mantendo o teto anterior. Manifesto privado registra cobertura/omissões.
- Quatro checks temporais exigem sequências reais; correção ligada a issue
  demonstrada e preferência A/B com sequências das duas versões. Incerteza não
  dispara refação. Histórico sem capacidade mantém validação anterior.
- 292 testes direcionados (7,29 s), Ruff/mypy; ajuste contra contorno da incerteza:
  41 testes (0,80 s). Extração real do MP4 sintético: 16 quadros, três eventos
  completos, 12 omitidos. Sem nova geração, render, CI completo, banco ou deploy.
- Quarto passo aguarda comando/orçamento: crítica com IA real e comparação
  integrada. Ganho criativo e equivalência às referências ainda não demonstrados.

## 09/11/2026 — segundo passo: recursos de movimento no executor

- API `MotionV1`: timeline determinística, curvas/Bézier/mola, stagger, máscaras
  e transformações coordenadas. Direção numérica acompanha o kit existente.
- Versão/hash/API no snapshot; disponibilidade conferida antes de geração paga;
  runtime conferido e incluído no pacote de cena pelo adapter. Execução permanece
  no Chromium, sem dependência externa. Pedidos sem capacidade mantêm a cena original.
- 266 testes Python (4,20 s), 8 Node (0,51 s), Ruff/mypy; ajuste final confirmado
  por 30 testes (1,98 s). Recusa de cena vazia com prefixo: 5 testes (1,66 s).
  Render manual sintético de 4 s/120 quadros conferido.
- Sem CI completo, SQL, migração, deploy ou API paga. Terceiro passo aguarda comando;
  crítica temporal e prova integrada criativa continuam pendentes.

## 09/11/2026 — primeiro passo do contrato de movimento implementado

- Novos pedidos `reel-creative-v2` exigem `motion-plan-v1`: cenas/elementos,
  tempos, estados, curvas, relações e propósito na mesma geração/correção.
- Kit, acervo, skill e biblioteca preservados; referências orientam movimento.
  Serviço valida duração/estilo/assets antes do render; plano segue no histórico
  privado e no payload da crítica. Leitura/processamento de v1 preservados.
- 155 testes direcionados passaram em 8,75 s; Ruff/mypy aprovados. Regressão SQL
  adicionada, não executada; sem CI completo, banco, render, API paga ou deploy.
- Passos 2–4 pendentes: recursos de movimento, crítica temporal e prova integrada.
  Plano coerente não comprova execução no HTML nem ganho de qualidade visual.

## 09/11/2026 — escopo de motion e identidade visual esclarecidos

- Referências orientam qualidade do movimento; kit confirmado do negócio continua
  determinando identidade. Exemplos não fornecem paleta, fontes ou marcas à peça.
- Plano detalha contrato temporal, recursos determinísticos, crítica de sequências
  e prova pelo fluxo real; primeira prévia não exige biblioteca completa.
- Mudança documental; sem runtime, testes de CI ou chamadas pagas.

## 09/11/2026 — quatro Shorts e processo de motion consolidados

- Quatro vídeos completos baixados; 266 quadros inspecionados e legendas
  automáticas do tutorial de cinco passos lidas. Relatório e manifesto locais.
- Processo comparado com o código: tempo determinístico, navegador e captura
  quadro a quadro já existem; direção visual, materiais e crítica comparativa
  são as próximas lacunas. Sem pressupor necessidade de Remotion ou 60 fps.
- [Plano concreto de evolução](design/evolucao-qualidade-motion-referencias-2026-11-09.md),
  ainda não implementado; sem runtime, CI, API paga ou novo orçamento.

## 09/11/2026 — referência direta do Instagram analisada

- Reel `Db9axeiOotS` baixado sem login; 106 quadros da duração completa e
  transição amostrada a 0,1 s. Relatório local com vídeo e navegação temporal.
- Priorizados planejamento de estados, hierarquia, revelação e continuidade;
  recursos de recorte/imagens geradas não são pré-requisitos deste exemplo.
- [Evidências e limites](evals/referencia-reel-Db9axeiOotS-2026-11-09.md).
  Sem runtime, CI ou nova API paga.

## 09/11/2026 — análise da referência em vídeo indicada pelo titular

- Vídeo completo baixado e inspecionado desde o início por sequências de quadros;
  relatório local com navegação temporal e limites explícitos de áudio/movimento.
- Registrada a diferença entre cenas gráficas próprias dos exemplos e o foco
  atual em gravação contínua. Restrição de preservação integral e ausência de
  edição/legendas alinhadas identificadas no contrato vigente.
- [Análise e próximo recorte proposto](evals/referencia-motion-youtube-fqaEZqPzKZs-2026-11-09.md).
  Sem mudança de runtime, nova API paga ou CI.

## 09/11/2026 — avaliação humana da nova comparação Café Pausa

- Titular reconheceu pequena melhora em B, mas considerou o resultado muito
  abaixo dos motion graphics e das bibliotecas esperados. Qualidade criativa
  ainda insuficiente; sucesso técnico preservado, sem aceite comercial.
- Registrada divergência com os quatro checks `met`: a crítica avaliou funções
  gráficas com calibração textual, sem referências visuais. Próxima calibração
  precisa de alvo concreto; sem nova API, mudança de runtime ou testes.

## 09/11/2026 — nova comparação integrada: prova técnica concluída

- Café Pausa real completou geração, render, crítica, coleção e download privado
  conferido por SHA; referências cifradas pequenas resolveram a persistência.
- Duas chamadas e duas contagens; US$ 0,266156 estimados, US$ 1,70 em reservas
  novas. Sem correção, retry, migração ou CI; worker próprio encerrado.
- Comparativo A/B entregue; quatro checks criativos atendidos segundo o modelo.
  Avaliação humana de motion/narrativa pendente; não se declara ganho da autocrítica.
- [Resultado, custos e evidências](evals/plano-comparacao-criativa-integrada-2026-11-09.md#resultado-da-execução-autorizada).

## 09/11/2026 — preparo da nova comparação integrada (item 3)

- Nova operação fictícia Café Pausa admitida no dev; mesmos materiais e briefing,
  contrato criativo novo. Worker atualizado construído e nove módulos conferidos
  sem rede; renderer com UTF-8 preservado. Sem migração, limpeza ou CI completo.
- Coleta preparada para referências cifradas, fora de transações SQL; relatório
  separa baseline histórico, geração nova e eventual correção, com quatro checks.
- Plano: até quatro chamadas e quatro contagens, uma correção condicional,
  US$ 3,40 novos. Autorizado em entrevista; execução iniciada. Zero chamadas
  à OpenAI no preparo. Teto agregado US$ 5,95 inclui US$ 2,55 anteriores retidos.
- [Plano e critérios de encerramento](evals/plano-comparacao-criativa-integrada-2026-11-09.md).

## 09/11/2026 — direção e critérios criativos do Reel (item 2)

- Contrato `reel-creative-v1` capturado em novos snapshots/fingerprints, com
  planejamento criativo na geração e calibrações textuais de Intensa/Dog/Luma/Giz B.
  Preserva variedade de estilos e os snapshots históricos das skills.
- Crítica exige quatro verificações criativas vinculadas ao briefing e às
  evidências; desenvolvimento temporal exige dois momentos da versão atual.
  Adequação técnica não encobre requisito criativo falho ou incerto.
- Correção criativa usa limites existentes e exige problema maior acionável;
  dúvida não gera refação. Melhora de acentos é separada de melhora de motion.
- 98 testes direcionados passaram em 1,50 s; Ruff/mypy. Regressão SQL adicionada
  para execução posterior. Sem chamadas pagas, render, migração ou CI completo.
- Item 2 entregue em código; ganho visual e prova integrada aguardam item 3.
  [Contrato e limites](design/integracao-reel-2026-11-09.md).

## 09/11/2026 — correção da persistência de pacotes grandes do Reel

- Pedidos multimodais e quadros cifrados maiores que 64 KiB passam ao storage
  privado existente. SQL conserva referências cifradas pequenas e hashes;
  o payload integral enviado à IA permanece inalterado.
- Upload com identidade durável e auditoria antes do IO; PUT único e leitura de
  conferência. Falha/resultado incerto interrompe sem nova geração. Leitor valida
  escopo, integridade e tamanho, mantendo compatibilidade com registros inline.
- Preparação criptográfica fora das transações de efeitos e versões. Respostas
  continuam inline pelo caminho restrito que preserva evidência após revogação.
- 81 testes direcionados passaram em 1,42 s; Ruff/mypy. Duas regressões SQL
  adicionadas, não executadas. Pacote fictício real salvo: campo SQL de
  42.205.388 para 716 bytes, conteúdo recuperado exatamente, medição sem rede.
- Sem migração/alteração de dev, build, CI completo ou API paga. Pedido anterior
  preservado; item 2 aguarda comando e a prova integrada continua posterior.
- [Contrato e limites](design/integracao-reel-2026-11-09.md).

## 09/11/2026 — ponto 3: prova real interrompida antes da crítica final

- Café Pausa gerado, criticado, corrigido e renderizado novamente pelo produto;
  duas versões preservadas. Três chamadas pagas, US$ 0,412521 estimados,
  US$ 2,55 reservados do teto US$ 3,40; sem fatura conciliada ou retry automático.
- INSERT do pacote da crítica final cancelado pelo PostgreSQL após 10 s;
  nenhuma quarta chamada ao modelo. Pedido falhou, sem peça na coleção.
  Persistência de pacotes grandes, crítica final e download integrado pendentes.
- Defeito de acentos corrigido no renderer com charset UTF-8 explícito;
  71 testes direcionados passaram em 1,17 s. Imagem nova construída e checagem
  real mínima aprovada; comparação paga preserva a imagem original.
- Exportação somente leitura com prazo local maior recuperou os dois vídeos;
  worker próprio encerrado. Sem CI completo, nova migração ou limpeza.
- [Comparativo e pendências](evals/plano-prova-reel-integrada-2026-11-09.md).

## 09/11/2026 — ponto 3: preparo real e prova paga autorizada

- Worker em contêiner construído; checagem sintética real de dois quadros aprovada.
- Banco dev existente utilizado por escolha explícita; migrações 0112/0113
  aplicadas após confirmação específica, sem limpeza/recriação.
- Pedido fictício Café Pausa admitido pela API. Orçamento novo de até US$ 3,40
  autorizado; até quatro chamadas de geração/crítica e quatro contagens.
- Temporal dev falhou antes dos efeitos pagos. Após entrevista, prova direcionada
  à instância local já ativa, preservando banco dev e identidade. Temporal dev
  voltou ao estado parado original; investigação desse serviço permanece fora
  desta fatia. Nenhum CI completo ou repetição automática de chamada paga.
- [Plano e limites](evals/plano-prova-reel-integrada-2026-11-09.md).

## 09/11/2026 — ponto 2: executor no worker em contêiner

- Target `motion-worker` herda o worker de mídia e acrescenta CLI Docker;
  overlay opcional alinha API/relay/worker e compartilha socket somente com o
  worker confiável e pasta temporária no mesmo caminho do host. Sem novo runner.
- Adapter aceita scratch explícito, mantém entrada isolada por tentativa e
  limpeza, rejeita caminhos inválidos e falha antes do Docker se a pasta faltar.
- Comando sintético de dois quadros preparado para verificar o executor real
  antes da próxima prova, sem IA, banco ou geração comercial.
- 130 testes direcionados passaram em 4,49 s; Ruff/formatação/mypy aprovados.
  Compose resolvido validado em modo desativado e fake, sem `.env` real.
  Sem CI completo, build, render real, API paga ou alteração de serviços atuais.
- Implementação/configuração entregue; aplicação e verificação no contêiner
  serão o preparo da prova do ponto 3 após novo comando e orçamento específico.
  [Guia e comandos](../docker/motion-worker/README.md).

## 09/11/2026 — ponto 1: orçamento completo do Reel

- Reutiliza o `VisualCostLedger`: antes de gerar, consulta a contagem de textos,
  instruções, schema e imagens; soma ao teto de saída e bloqueia excesso de reserva.
  Falha de contagem não autoriza geração, reserva financeira nem retry.
- Política versionada para `gpt-6.1-sol` Standard, com piso de tarifa cobrindo
  escrita de cache; bloqueia modelos não qualificados e entrada acima de 272 mil
  tokens. Cálculo preservado no pedido cifrado de cada efeito.
- Consulta `/responses/input_tokens` com identidade derivada da operação;
  sem geração, redirecionamento ou repetição automática. Material adicionalmente
  enviado nessa consulta deverá constar do próximo plano de execução autorizado.
- 100 testes unitários direcionados passaram em 1,62 s; Ruff e mypy aprovados.
  Sem CI completo, SQL, render ou API real, conforme recorte pedido pelo titular.
  O CI integral anterior permanece histórico; teste SQL existente foi adaptado
  à nova interface/tarifa, mas não reexecutado nesta entrega.
- Somente ponto 1 implementado. Executor (2) aguarda novo comando;
  prova integrada com IA (3) continua dependente de orçamento específico.
  [Contrato e fontes](design/integracao-reel-2026-11-09.md).

## 09/11/2026 — qualificação técnica local do Reel concluída

- `make ci` exit 0: 5.353 testes, sem skips, 100% de 18.570 linhas e 5.090
  branches; 363 testes Python motion, 137 Node renderer, lint e tipos aprovados.
  Execução final de 1.235,05 s; 828 fontes estáveis, relógios sem repouso.
- Web: 524 testes/100%, tipos/build/formatação e QA sintético aprovados.
- Quatro replays Linux aprovados; prova integrada real com modelo/crítico fake
  concluída. Acesso privado e reentrega sem repetição demonstrados. Nenhuma
  chamada paga nova ou aprovação humana fabricada.
- Os dez workers autorizados foram restaurados às 16:06:23 UTC; storage próprio
  de teste parado, volume e arquivos preservados. Nenhum banco de projeto limpo.
- [Evidências e limites](evals/qualificacao-integracao-reel-2026-11-09.md).
  Qualificação local não equivale a ativação comercial/gerador pago homologado.
  Etapa 5 planejada, ainda não implementada; demais limites permanecem explícitos.

## 09/11/2026 — replays Linux e suíte web aprovados

- [Desenho da revisão de imagens](design/ciclo-revisao-imagens-2026-11-09.md)
  detalha o reuso do JPEG final antes da entrega, seleção de referências e
  finalização durável. Planejamento da etapa 5, sem implementação ou nova API.
- CI inicial da nova árvore: 4.658 aprovados antes de expectativa antiga de
  tabela falhar. Ajuste restrito ao teste da guarda compartilhada; nova prova
  SQL verifica bloqueio/liberação do aceite durante um Reel, sem gravação parcial.
  Validação dirigida e repetição integral pendentes; sem mudança de produção
  para contornar a falha.
- Quatro replays reais preservaram código/assets, geometria, duração e número
  de quadros. Comparação visual amostral e SSIM de todos os 1.215 quadros
  registrados; métricas não são aceite criativo ou escuta humana.
- Com autorização, dez workers de desenvolvimento foram parados temporariamente
  para liberar CPU; restauração após validação ainda pendente. Nenhuma mudança
  de qualidade ou aumento de timeout para fazer os replays passarem.
- Web: 524 testes, 100% de linhas/branches/funções/instruções; tipos, build e
  Prettier aprovados. Conferência textual de versão alternativa também passou.
- Renderer real preservou estéreo/44,1 kHz e bloqueou imagem externa. Storage
  exclusivo passou em acesso autenticado/assinado e negação anônima. A rede de
  teste ganhou bridge com porta somente em loopback porque Docker Desktop não
  publicou a porta da rede exclusivamente interna; renderer continua sem rede.
- Prova integrada passou em 97,637 s, com API/auth/SQL/RLS/Temporal/render/storage
  reais e modelo/crítico simulados. Reentrega não repetiu efeitos, download por
  hash conferido e acesso anônimo/outro tenant bloqueado. Nenhum aceite fabricado.
- CI integral backend ainda em execução; etapa 5 pendente.
  [Evidências e limites](evals/qualificacao-integracao-reel-2026-11-09.md).

## 09/11/2026 — retomada da qualificação do executor após interrupção

A retomada após a interrupção por limite de uso continua na etapa 4. A correção
faz o executor reconhecer a origem interna fixa dos assets históricos, preservando
HTML e mídia e bloqueando outros endereços. Erro de carregamento já ocorrido é
reportado imediatamente, sem ficar oculto como timeout. Passaram 137 testes Node
com 100% de linhas, branches e funções. A imagem foi reconstruída, mas o replay
completo de Intensa atingiu o limite de tempo e continua em diagnóstico. O CI
integral da nova árvore foi iniciado em banco exclusivo `_test`; sua conclusão
e a prova integrada permanecem pendentes. Nenhuma nova chamada paga.

## 09/11/2026 — integração do Reel em implementação após preferência por Giz B

- Escopo confirmado: concluir a etapa 4 antes dos demais formatos, mantendo o
  caminho HTML/JS aprovado. Titular reforçou evitar trabalho paralelo sem
  relação com a entrega e tratar definições faltantes por entrevista.
- Em implementação: pedidos/contexto privados, efeitos no ledger existente,
  executor HTML isolado, crítica fundamentada e coleção de versões com aceite
  independente de publicação. [Desenho](design/integracao-reel-2026-11-09.md).
- [Matriz de formatos](design/v0-motion-etapa-0-formatos-e-casos.md) atualizada
  com o estado de 09/11, reuso do caminho visual e lacunas de crítica/edição,
  story e ajuste seletivo de carrossel. Histórico de 05/11 preservado; esta
  análise não implementa a etapa 5 nem autoriza novas APIs pagas.
- Implementados pedidos/snapshots cifrados, versões/decisões imutáveis e
  revisão privada independente de publicação. A peça simulada fica identificada
  na API/UI. Migrations 0112/0113 passaram em banco `_test` novo com roles
  restritas; casos dirigidos verificam RLS, repetição/conflito, concorrência,
  hashes, versão exata, importação JPEG real e ausência de postagem.
- Crítica/correção recebem fonte, atual e anterior separadas. Critério
  `pass`/`fail` exige evidência da versão atual. A guarda financeira verifica
  cobertura do máximo de saída antes do efeito; o limite de entrada/imagens
  por modelo ainda é requisito para ativação paga, sem teto total presumido.
- Passaram 19 testes de inputs/fixture/runtime com 100% de linhas/branches e
  132 Node dos dois renderers com 100% de linhas/branches/funções. Regressões
  cobrem sandbox, limites de IO e áudio cujo fim real precede ligeiramente o
  trim planejado, sem alterar áudio ou acrescentar padding. Node usa IO simulado;
  replays reais no contêiner seguem em qualificação.
- [QA da interface](../.local/piece-ui-qa-20261109/result-2026-11-09T14-29-08-411Z/qa.json)
  aprovado em 390/1440 px, com MP4 sintético 720×1280: versões, cinco
  confirmações, download por hash e conflito de versão; sem overflow/erro JS ou
  rede externa. API simulada, fontes de sistema e reprodução mutada; não é
  jornada com backend, aceite de áudio ou qualidade criativa. Alteração textual
  posterior distingue versão atual de alternativa, sem presumir que a versão
  selecionada seja sempre a mais nova; conferência textual dirigida pendente.
- Sem novas APIs pagas ou ativação para clientes. A integração e o CI da nova
  árvore ainda não estão concluídos. O CI registrado abaixo continua evidência
  da árvore anterior; resultados dirigidos não substituem sua nova execução.

## 09/11/2026 — preferência por B registrada; etapa 3 concluída no recorte

- Titular respondeu “B ficou melhor.” na entrevista de motion/narrativa do
  Giz, `call_3e1d59720b1b4daabd16fcb8cfd27982`, item 0. Novo registro privado
  exclusivo/somente leitura `human-feedback.json`, SHA-256
  `cdfabf43a8b4378eddb4cb1cdcde9dee55a31941a3f51bdd834338d3ee47f924`.
  Hashes de A/B, relatório e summary conferidos e vinculados; vídeos, crítica,
  relatório e estado automático histórico não foram alterados.
- Etapa 3 concluída no recorte de legibilidade 1c + refinamento guiado Giz.
  Preferência humana não equivale a aceite isolado de áudio, todo critério,
  todos os formatos, economia geral ou publicação. Custos e autorizações
  históricas continuam separados. [Resultado](evals/ensaio-refinamento-motion-giz-2026-11-09.md).
- Próximo trabalho já autorizado: implementar Reel integrado (4), depois demais
  formatos (5). Integração não está concluída. Estado vigente simplificado nos
  documentos centrais e índices; histórico/evidências preservados.
- Resposta operacional “Sim, posso manter o Mac acordado”, entrevista
  `call_9cd4f8a76acd4c8c81f68ace7f4918e1`, item 0, não demanda repetir o CI já
  concluído. Esta atualização não executou API, render ou suíte novamente.

## 09/11/2026 — CI concluído e testes reais de mídia completados

- `make ci` exit 0: 5.043 testes aprovados e dois pulados por FFmpeg/FFprobe fora
  do PATH. Esses mesmos dois testes reais de MP4 passaram separadamente em
  4,97 s após ajustar só o PATH privado para FFmpeg 9.0/FFprobe 4.4.8; nenhuma
  alteração de teste ou produção. [Resultado final](../.local/ci-20261108/ci-final-result.json).
- Cobertura app 100%: 17.229/17.229 linhas e 4.726/4.726 branches. Passaram
  363 Python motion, três Node áudio e 62 Node renderer, este último com 100%
  de linhas/branches/funções. Ruff/formatação e mypy 272 módulos app mais oito
  scripts aprovados. Os recortes anteriores não se somam a esta suíte.
- 735 arquivos app/migrations e 29 do laboratório iguais aos snapshots.
  69 amostras de relógio sem sinal de repouso; diferença total −0,048 s em
  1.114,6 s. Logs sem credenciais e falhas anteriores preservados como histórico;
  a disponibilidade do Mac não bloqueia mais esta execução concluída.
- `fsync`, `synchronous_commit` e `full_page_writes` desligados somente no
  PostgreSQL descartável do CI. Esta prova não qualifica perda de energia ou
  recuperação do servidor e não muda os requisitos/configuração de produção.
- Pendência técnica de CI encerrada nos documentos vigentes. A etapa 3 aguarda
  a entrevista humana já enviada sobre o Giz; nenhuma integração foi iniciada.

## 09/11/2026 — QA Giz aprovado e entrevista humana enviada

- QA real em 390/1440 px, modos cego/identificado, oito reproduções mutadas
  completas de 11,2 s, sete links por vista com HEAD 200. Sem overflow, erro
  JavaScript/console/HTTP ou rede externa; três leituras locais `ERR_ABORTED`
  registradas separadamente, com todos os players chegando ao fim.
- 248 arquivos conservaram hashes e 12 screenshots foram arquivados. QA SHA-256
  `1d6d7f33acfca8a9d9619eeec451683dd8f875b04655f7507281b00e982747d3`;
  relatório SHA-256 `753721817bfd70de7f8f70e83f19ee9aa1991b35ff7fd2a2668531a2b34c63ec`.
  Tentativa anterior falhou com EPERM antes do navegador e foi preservada;
  seguinte execução local passou com script inalterado. Sem API ou reparo novo.
- Relatório aberto no navegador, vistas inspecionadas e entrevista humana
  enviada com link explícito. Resposta/aceite pendentes; QA mutado não comprova
  escuta, qualidade criativa ou aprovação de integração. [Resultado](evals/ensaio-refinamento-motion-giz-2026-11-09.md).
- CI da aplicação continua em execução, com 587 testes aprovados sem falhas no
  checkpoint, sem aprovação integral presumida.

## 09/11/2026 — refinamento Giz concluído, comparação humana pendente

- [Ensaio real](evals/ensaio-refinamento-motion-giz-2026-11-09.md) terminou
  `completed_human_pending`: duas chamadas HTTP 200, sem retry, incerteza ou
  reparo visual manual. Crítica prefere v1, três requisitos `met`, seis critérios
  `pass`, áudio `uncertain`, zero achados. QA do relatório em execução; titular
  ainda não viu nem aprovou A/B. Não é conclusão automática da etapa 3.
- Amostras mostram verde → creme → verde na área editorial, janela em arco e
  estados intermediários nas transições 2,582–3,182 s e 8,053–8,753 s. Leiteira,
  fio de leite e xícara reconhecíveis; arco recorta um pouco mais a extremidade
  da mão. Quadros não comprovam movimento completo, fluidez ou escuta.
- Inspeções locais de código/artefato registradas; HTML byte a byte igual,
  dois avisos MIT, textos, assets e fontes conferidos. V1 final SHA-256
  `9c2bb1708aea9dfc708ad98c2c44372d7bca5b18c2269d9fd9652910cf26c32e`;
  176 pacotes AAC, tempos e PCM iguais ao baseline, com MP4 bruto preservado.
- Incremental US$ 0,6482575; histórico US$ 0,2203975; subtotal de APIs
  US$ 0,8686550. Comparação excedeu reserva em US$ 0,0138475: comprometimento
  US$ 1,0138475, dentro do teto US$ 1,25. Subtotal medido 483,872 s exclui
  preparo/qualificação/inspeções/intervalos; não é fatura, COGS ou SLA.
- Refinamento com feedback e seis quadros posteriores de Intensa; não prova
  descoberta autônoma de erro do briefing original. Históricos 1c/trio intactos.
- Novo CI da aplicação em execução, com 451 testes aprovados e relógios alinhados
  no checkpoint; ainda sem aprovação integral ou causa geral das falhas anteriores.

## 09/11/2026 — orçamento Giz autorizado e primeiro refinamento iniciado

- Titular respondeu “Autorizar até US$ 1,25 para a prova Giz”, entrevista
  `call_d3ff68b65d724ed392cee307e73bdf9c`, item 0. Registro privado de autorização
  SHA-256 `1705ce1c3078f640846049f797649684319be9a7c287fecaaf7f58307cc008c6`,
  vinculado ao plano, qualificação intacta e pedido inicial; plano proposto
  histórico preservado. Máximo de duas chamadas, sem retry ou transferência
  de orçamento anterior.
- Primeira chamada de refinamento iniciada, ainda sem resultado. A segunda
  depende de inspeção local de código, artefato e áudio; essas verificações
  não são outra aprovação intermediária do titular. Ganho criativo não presumido.
- CI da aplicação não passou: após 785 aprovações, falha em recibo durante
  diferença de cerca de 11 h entre relógios de parede e monotônico; módulo
  isolado passou em dois testes. A nova execução falhou com `Invalid access
  token` após 75 aprovações/56,81 s. Investigação em andamento, sem mudança de
  produção nesta frente e sem causa final atribuída à nova falha.
- Resultados do laboratório e ensaios anteriores preservados; Reel integrado
  e demais formatos continuam dependendo da prova criativa e validação técnica.

## 08/11/2026 — Giz qualificado e orçamento concreto aguardando autorização

- Protótipo e contrato de avaliação por requisitos implementados. Passaram 160
  testes de Giz/contratos/relatório/legado e 66 declarativos (57 mais nove casos
  de bloqueio de caminhos indevidos). Executor/transporte genéricos impedem
  contornar as guardas próprias de Giz/1c. Sidecar real, tempos de referências
  e proveniência bruto/remuxado corrigidos; `make types` inclui oito módulos.
- Replay real qualificado no run `1c758136-7530-43d8-96b7-39e4b0e44888`:
  MP4 bruto byte a byte igual ao original; remux com todos os 336 quadros RGB24,
  tempos e AAC/PCM/tempos preservados. Qualificação SHA-256
  `c899ac2d7f84c6328599a10adb4dc6d4db42218748c7edd1d9df926162517e69`;
  código usado arquivado em 14 arquivos. Baseline reproduzido não prova ganho.
- [Plano Giz](evals/plano-refinamento-motion-giz-2026-11-08.md) propõe até duas
  chamadas/US$ 1,25 de admissão, com reservas US$ 0,75/US$ 0,25 e folga US$ 0,25.
  Pedido inicial: 32 imagens/19.738.876 bytes; comparação prevista: 52 imagens,
  corpo exato só após B, limite 45 MB sem truncar evidências. Mesmo provedor/
  modelo, reasoning high, store=false, sem retry e sem transferir tetos antigos.
- Entrevista de orçamento enviada e pendente; nenhuma nova API paga. Antes da
  comparação, inspeções locais de código/artefato e prova do áudio, sem nova
  aprovação intermediária do titular. HTML livre não prova fatos/textos pelo
  schema. Históricos preservados, sem alterar suas autorizações/artefatos.
- Conferência final do laboratório aprovada: 363 testes Python motion em
  101,60 s, três Node de áudio, lint/formatação e mypy de 272 módulos app mais
  oito scripts. Os 29 arquivos conferidos antes/depois permaneceram idênticos;
  evidência em `.local/ci-20261108/lab-final-checks-result.json`. Recortes de
  testes anteriores não devem ser somados à suíte final.
- CI da aplicação ainda em execução: checkpoint 429/797 integrações sem falhas,
  com 4.248 unitários posteriores pendentes. Sem aprovação integral ou calibração
  criativa presumida.

## 08/11/2026 — plano e pacote de refinamento do Giz preparados

- [Plano específico](evals/plano-refinamento-motion-giz-2026-11-08.md) e pacote
  privado concluídos: 70 arquivos, sendo 68 inventariados (14,44 MB), mais
  manifesto/digest. Manifesto SHA-256
  `486f5a2467b704cb488416fccbd6b72d639aadea5fcbfa3df073d3fff03f7d0d`.
  Contexto original, feedback posterior e referências novas ficam separados.
- Percurso proposto de até duas chamadas: refinamento pelo feedback já conhecido
  e avaliação comparativa. Não repetir o feedback em uma crítica paga inicial.
  Orçamento ainda não finalizado/autorizado; nenhum render ou API novo.
- Protótipo privado em implementação. O novo contrato deverá confrontar mudança
  de tema, transformação da janela e função narrativa, separando presença de
  movimento de atendimento criativo. HTML/JS livre não assegura fatos/textos
  imutáveis por schema; invariância de áudio depende de prova real futura.
  Replay, qualificação e orçamento concreto continuam pendentes.
- O CI da aplicação permanece em execução: checkpoint de 199 testes sem falhas,
  com os quatro de locks aprovados. Esse avanço parcial não é aprovação do CI.

## 08/11/2026 — comprovar melhora do motion antes da integração

- O titular escolheu “Comprovar melhora do motion primeiro (recomendado)”.
  A prova criativa continua sendo condição anterior à integração do Reel;
  a melhora de legibilidade do 1c permanece reconhecida, com alcance limitado.
- Giz (`15adf19d`, lote `e2bbd3aa`), avaliado anteriormente abaixo de Intensa,
  é candidato em análise. A auditoria não encontrou violação inequívoca do
  briefing original: motion/desenho existem; tema e janela contínua vieram
  no feedback posterior. A prova deverá declarar refinamento com contexto
  adicional, sem atribuir a melhoria à descoberta de erro original.
- Preparar plano, pacote e contrato antes da entrevista de orçamento.
  Nenhuma API/renderização nova ou degradação artificial foi executada;
  orçamento novo ainda não autorizado. Resultados e custos anteriores preservados.

## 08/11/2026 — limitações visíveis e significado de adequate no relatório

- O gerador agora apresenta `limitations[]` com escape de HTML e explica
  `adequate` como ausência de outro defeito acionável nas evidências observadas.
  Encerramento automático do ciclo é distinguido de aceite criativo; respostas
  e classificações originais não foram reescritas.
- Passaram 15 testes do relatório, Ruff e mypy. Somente o HTML 1c foi regenerado;
  vídeos, críticas e summary permanecem intactos. Original conservado como
  `report-before-limitations.html`, SHA-256
  `8a93ab0561adf4300df3e559ee3f0a3c6bb230dc10dcc41877e7f06be473bc4e`.
  Novo HTML SHA-256 `d532a425c861e3ffc0766116c7ceb96020e2628739e08689bd2ce439bf3b91ce`.
- Código/testes/manifesto da revisão preservados em
  `report-revisions/2026-11-08-limitations`; snapshot original mantido. Novo QA
  dirigido aprovado em 390/1440 px, modos cego/identificado, limites somente no
  identificado, dois players e sete links; sem overflow, erro JavaScript ou
  rede externa. Ledger/manifesto/summary/MP4s conferidos contra QA anterior,
  críticas contra ledger; HTML e QA anteriores conservados. Sem API ou custo novo.
- A lacuna da rubrica continua: o próximo contrato deve separar movimento
  observado de atendimento criativo ao pedido. Essa alteração ainda não foi
  implementada ou calibrada; a correção de apresentação não a substitui.
- Naquele momento, entrevista de alinhamento enviada e pendente: comprovar melhora real de motion/
  narrativa antes da integração ou integrar o caminho Intensa/Dog/Luma com
  avaliação criativa humana. Candidatos históricos apenas em análise de leitura,
  sem degradação artificial, render ou API. Não há nova rodada autorizada.



## 08/11/2026 — feedback humano confirmou legibilidade e questionou motion

- Titular respondeu: “sim. o B tem os titulos e legendas bem melhor. mas o que é
  isso. seria um story? era para ter motion? porque é só um video gravado pelo
  cliente com legenda e titulo em cima? o que ele deveria ter?”. [Registro integral](evals/ensaio-revisao-reel-1c-2026-11-08.md).
- Melhora de títulos/legendas reconhecida, sem aceite global, aprovação do áudio
  ou de motion. Conferido o contexto original: `reel`, com cortes, transições,
  motion graphics e legendas; vídeo ilustrativo licenciado com voz sintética,
  não material de cliente real.
- A peça histórica tem pequenos ajustes de enquadramento/fades. O ensaio reparou
  legibilidade, mas o `pass` automático em movimento não comprova acabamento
  criativo. Registrada a lacuna de avaliação; Intensa/Dog/Luma continuam como
  referências, e 1c não vira padrão de produto nem libera integração.
- Atualizado o índice de validação com estado vigente e sequência de sete
  processos, preservando resultados históricos e orçamentos separados. CI
  integral continua em execução; nenhuma nova API, verba ou publicação.



## 08/11/2026 — módulo de concorrência aprovado, novo CI integral em execução

- O módulo final de concorrência passou em quatro testes, em 93,61 s, após
  ajuste da preparação e detecção de saída antecipada das tarefas. Timeouts
  do domínio e fases de bloqueio foram preservados.
- Novo CI integral iniciado, ainda sem resultado ou aprovação presumida. O
  snapshot anterior à execução registra 735 arquivos de `app`/`migrations`,
  SHA-256 `b4ecde70bc620ab7f2821e603191f6fc3220a9d7f4091bf8989bfa237417843f`.
  Nesse recorte, só `test_destination_lock_proof.py` mudou desde a tentativa
  anterior desta retomada; código de produção e migrations permanecem intactos.
- A entrevista humana do 1c segue pendente. Não houve novo orçamento ou chamada
  de API nesta validação; custos e resultados dos ensaios permanecem iguais.

## 08/11/2026 — relatório 1c validado e avaliação humana solicitada

- QA final do relatório 1c passou em 390/1440 px, nos modos cego/identificado:
  dois players 720×1280/11,2 s, oito reproduções completas mutadas, sete links,
  zero overflow, erro JavaScript ou rede externa. Hashes dos vídeos preservados.
  `report-qa/qa.json` e 14 PNGs conservam as provas; cancelamentos locais de seek
  foram registrados sem erro de mídia. Reprodução mutada não é escuta humana.
- Link e entrevista enviados ao titular para comparar A/original e B/corrigida:
  avaliar legibilidade e eventual regressão. Resposta pendente; não há aceite
  humano, integração ou conclusão da etapa 3 por causa desse QA.
- Nos três testes de concorrência, espera preparatória unificada em 60 s e
  saída antecipada da tarefa detectada após reproduzir a falha de barreira de
  preparação. Timeouts do negócio e fases de bloqueio mantêm os valores
  originais. Validação dirigida e CI integral ainda pendentes; nenhum teste
  excluído ou aprovação presumida.

## 08/11/2026 — ciclo 1c concluído, preferência automática pela v1

- Run `3a52c376-e8ea-4bea-b997-94ba59c628de` terminou `completed_human_pending`:
  três chamadas HTTP 200, sem retry ou operações incertas. Crítica inicial
  identificou um defeito `major` de legibilidade; correção validada/renderizada;
  crítica final `adequate`, sem achados e com preferência por v1. Seis critérios
  `pass`, áudio `uncertain`; julgamento humano continua pendente.
- V1 SHA-256 `5305dfda85284fd9a762320dc6e8fe6e0c95cbd20acbea3810fab2f030013eca`.
  AAC/PCM/tempos conferem com o baseline. Resultado executado sem ajuste visual
  manual; artefatos e versões conservados. [Comparação e evidências](evals/ensaio-revisao-reel-1c-2026-11-08.md).
- Crítica final: US$ 0,194605 estimados. Ciclo novo: US$ 0,527685, com US$ 1,25
  em reservas; histórico US$ 0,106892; subtotal de APIs US$ 0,634577, sem fatura
  ou COGS completo. Orçamento e custos de Intensa/Dog/Luma permanecem separados,
  incluindo a operação incerta de Intensa.
- Tempos observados: APIs 154,561 s, render/evidências 151,928 s; subtotal
  306,489 s exclui setup, preflight, qualificação, intervalos e trabalho humano.
  Não é duração total da retomada nem SLA de produto.
- Snapshot privado `qualified-code` conserva 11 arquivos (dez ligados à
  qualificação e o gerador do relatório), com manifesto e hashes conferidos.
  Relatório SHA-256 `8a93ab0561adf4300df3e559ee3f0a3c6bb230dc10dcc41877e7f06be473bc4e`.
  Isso não constitui backup remoto/restauração homologada.
- QA final do relatório HTML em andamento; avaliação humana e CI integral
  pendentes. Após reproduzir o timeout, o teste estrutural de concorrência está
  em correção. Esta prova específica de reparação não encerra a etapa 3 nem
  demonstra ganho criativo ou retorno financeiro geral para liberar integração.

## 08/11/2026 — crítico identificou o defeito histórico do 1c

- Crítica real da v0, operação `f48e3377-c84b-474d-92b1-315edc39972e`, retornou
  `needs_correction`: um achado `major` de legibilidade (`i01`) em títulos,
  legendas e convite pequenos, fundamentado em seis quadros do vídeo.
- Estimativa conhecida da crítica: US$ 0,124605. A correção, operação
  `b3205955-fdee-493f-943a-28035efda6f2`, retornou e passou na validação contratual,
  com estimativa de US$ 0,208475; subtotal conhecido do 1c US$ 0,333080.
- A candidata amplia os três títulos para 48 px e as quatro legendas para
  32 px, ajustando caixas/espaçamento e preservando fatos, textos, materiais,
  plano de áudio, cortes e intervalos. Render v1 em execução, ainda sem crítica
  final. Validade contratual não é comprovação do resultado visual. Custo total,
  comparação e julgamento humano continuam pendentes.

## 08/11/2026 — qualificação 1c aprovada e execução paga autorizada

- A segunda qualificação completa do run `3a52c376-e8ea-4bea-b997-94ba59c628de`
  passou: recompilação/render da direção original, 336 quadros RGB24 e tempos
  iguais, AAC/PCM preservados. Remux SHA-256 `7e07d6470d414082e821b58b9da03f00f89d3f02b4a99eb35e08441621422bd4`.
  `qualification.json` tem SHA-256 `21d7f2da63889674eb4b607523be3287a3d1f45459ddb746fa545d7154eabd78`.
  A primeira tentativa local falha e o preflight intermediário foram conservados.
- O titular autorizou em entrevista própria US$ 1,25 para até três chamadas e
  envio à OpenAI. `authorization.json` liga resposta/pergunta, plano, primeiro
  pedido e qualificação. Primeiro pedido coincide com o hash preparado.
- Execução `--execute --budget-usd 1.25` iniciada; está em andamento, sem resultado
  ainda. Não há conclusão da comparação, ganho ou avaliação humana. CI geral
  continua em diagnóstico após o timeout, separado desta qualificação.
  [Plano e limites](evals/plano-revisao-reel-1c-2026-11-08.md).

## 08/11/2026 — preflight real de mídia 1c e segunda qualificação em execução

- Ponte declarativa implementada; passaram 146 testes locais (57 da
  orquestração e 89 da ponte), Ruff e mypy estrito. O pacote privado conserva
  69 arquivos e as dez normalizações históricas; a origem não é HTML/JS.
- A primeira qualificação do run `3a52c376-e8ea-4bea-b997-94ba59c628de` parou
  somente na interpretação dos metadados FFprobe 4.4.8 (`size` textual e
  `pkt_pts`). Artefatos preservados em `qualification-attempt-1-failed`;
  nenhuma API ou cobrança nessa falha local. O leitor foi corrigido com
  validação estrita, sem suprimir a prova de igualdade.
- Preflight real em `media-preflight-ffprobe-4.4.8/result.json` passou sobre
  mídia já renderizada: MP4 arquivado byte a byte igual ao original; remux
  muda o empacotamento/hash, conservando 526 pacotes AAC, PCM/tempos e
  336 quadros RGB24/tempos. [Evidências e limites](evals/plano-revisao-reel-1c-2026-11-08.md).
- Segunda qualificação completa em execução; preflight não equivale a
  qualificação integral ou admissão de efeito pago. Até três chamadas/US$ 1,25
  ainda não enviados para aceite nem autorizados. Etapa 3 continua aberta.
- CI geral parou após 131 testes aprovados, em `TimeoutError` no caso
  `test_destination_lock_timeout_does_not_record_delivery`, após 26 min 48 s.
  Investigação e repetição dirigida do módulo pendentes; sem causa comprovada,
  alteração de timeout ou testes pulados. Aprovação integral continua pendente.

## 08/11/2026 — custo histórico completo das APIs do Reel 1c

- Pacote privado ampliado de 56 para 69 arquivos, com manifesto anterior
  preservado. Auditoria, pedidos/respostas e custo da tentativa 1b rejeitada
  conferidos por hash antes de preparar a nova execução.
- Subtotal histórico estimado de US$ 0,106892: Jev 1b rejeitado, Jev 1c,
  transcrição e direção do Reel. Não inclui outros formatos, trabalho ou
  infraestrutura, nem constitui fatura. O relatório identifica o subtotal das
  APIs registradas para não apresentá-lo como COGS completo. Nenhuma nova API.

## 08/11/2026 — escolha do caso 1c e conferência do relatório

- Titular escolheu em entrevista testar a correção do Reel antigo com defeito
  conhecido. [Plano 1c](evals/plano-revisao-reel-1c-2026-11-08.md) e pacote privado
  de 56 arquivos preservam a montagem inicial com tipografia pequena, dez
  normalizações históricas, contexto, fontes e custos. A direção é declarativa;
  a ponte contratual está em implementação, sem tratar a origem como HTML/JS.
- Até três chamadas/US$ 1,25 propostos, ainda sem autorização financeira. Nenhum
  novo efeito pago além das críticas Dog/Luma. Falha de unidades já corrigida
  na geração atual; o ensaio avalia reparação histórica, não ganho criativo amplo.
- Relatório do run `4338880a-10f2-48a7-96cd-54138f87dbdd` corrigido para caminhos
  longos e regenerado sem mudar vídeos, críticas ou ledger. Navegador a
  390/1440 px, modos cego/identificado: três players, sem overflow, erro JavaScript
  ou rede externa. A validação do relatório não é revisão criativa dos vídeos.
- CI da aplicação em execução após ajustes de infraestrutura local; resultado
  integral ainda pendente. Os 107 testes Python de motion já registrados são
  uma validação dirigida e não substituem esse CI.

## 08/11/2026 — críticas válidas de Dog/Luma, prova comparativa ainda aberta

- Corrigida a tipagem do caminho de continuação independente. O alvo `types`
  inclui os três módulos de revisão; testes de evidência resolvem ferramentas
  por configuração, PATH ou diretório local persistente, e o CI Linux instala
  FFmpeg explicitamente. Binários originais recuperados com hashes conferidos;
  os caminhos temporários históricos apontam para as cópias preservadas.
- Passaram 107 testes Python de motion e o preflight dos três casos. A verificação
  de acesso ao modelo retornou HTTP 200. O CI integral da árvore atual está em
  preparação; os resultados de 06/11 abaixo não são reaproveitados como prova.
- Run `4338880a-10f2-48a7-96cd-54138f87dbdd` concluiu Dog/Luma com contexto criativo
  v2: críticas `adequate`, sem achados acionáveis nem versão corrigida. Intensa
  permaneceu bloqueada pela operação `2b9fa3ad-c4c1-4bd1-8490-daf573fbf339`, sem retry
  ou liberação de reserva. Estado final: `completed_partial_human_pending`.
- Duas novas chamadas, US$ 0,175165 estimados. Revisão acumulada: seis tentativas,
  US$ 0,427215 conhecidos e US$ 1,50 em reservas; custo da tentativa incerta ainda
  desconhecido. O teto de US$ 6,75 não foi esgotado; estimativa não é fatura.
- A etapa 3 permanece aberta: nenhuma comparação original/corrigida, ganho
  demonstrado ou avaliação humana concluída. Caso histórico com defeito está
  em seleção para proposta de novo escopo e orçamento antes de novos efeitos;
  integração do Reel e etapa 5 continuam dependendo da prova. [Resultado](evals/ensaio-ciclo-revisao-motion-2026-11-06.md).

## 08/11/2026 — alinhamento do roteiro e das decisões do piloto

- Roteiro de sete processos alinhado ao texto recuperado pelo titular. Retomada
  autorizada: documentação e pendências técnicas → prova comparativa da etapa 3
  → Reel integrado após avaliação humana → demais formatos da etapa 5.
- Registradas as respostas já dadas: autoatendimento com cobrança e ausência de
  participantes reais definidos. Os quatro cenários fictícios permanecem casos
  de validação, sem assumir recrutamento, preço ou franquia final.
- Corrigida a condição de piloto: WhatsApp oficial pertence à jornada real;
  publicação Instagram permanece posterior. F07/F08/billing distinguem C08/C09
  já entregues no recorte visual da extensão ainda pendente para motion e legado.
- O CI de 06/11 foi identificado como evidência daquela árvore. Tipagem e
  ferramentas de mídia estão em correção na retomada; a continuação independente
  está preparada, sem novo efeito por esta alteração documental. Prova criativa,
  CI da árvore atual, integração e operação comercial permanecem pendentes.
- Validação documental: conferência de links locais e consistência entre roteiro,
  PROJECT, SDD, fase ativa e decisões. Não houve execução de API ou mudança de
  runtime nesta atualização de documentos.

## 07/11/2026 — solicitação de avanço e entrevista

- Titular confirmou etapa 7 como preparar o piloto e operação comercial após a
  frente atual. O [roteiro consolidado](design/execucao-ate-etapa-7-2026-11-07.md)
  é nova decomposição operacional, não citação dos nomes das etapas 5/6 anteriores.
  Naquele momento, a entrevista sobre participantes e modalidade aguardava
  respostas; o registro de 08/11 acima incorpora as respostas recebidas.
- Continuação offline por caso independente preparada e testada, com Intensa
  bloqueada e reservas cumulativas. Integração e CI da nova árvore pendentes;
  sem presumir conclusão da comparação ou início de cobrança, publicação,
  deploy, concessão automática de patrocínio ou liberação comercial.

## 06/11/2026 — continuação interrompida por resultado incerto

- A primeira crítica da continuação parou com `transport_or_recording_failed`,
  sem resposta salva. Operação `2b9fa3ad-c4c1-4bd1-8490-daf573fbf339` e
  reserva preservadas; não houve retry, crítica v2 nem peça derivada.
- No conjunto, quatro chamadas; estimativa conhecida US$ 0,2520500 das três
  críticas anteriores, custo da última desconhecido e reservas US$ 1,00. O teto
  autorizado não foi esgotado, mas não prova o custo nem libera reenvio incerto.
  Comparação real, ganho de qualidade e avaliação humana permanecem pendentes.
  [Relatório parcial](evals/ensaio-ciclo-revisao-motion-2026-11-06.md).
- `make lint types motion-test` passou após os ajustes: Ruff/formatação, mypy
  em 272 módulos, 91 testes Python, três Node de áudio e 62 do renderer. O
  primeiro CI integral foi interrompido após duas falhas de integração; os
  dois casos passaram isoladamente. A segunda execução integral foi interrompida
  após um teste receber 401 em vez de 200; esse teste também passou isoladamente.
  A terceira foi interrompida para reiniciar com parada na primeira falha. A
  seguinte parou após 202 testes em resposta sem `error_code`; o caso passou
  isoladamente. Ao testar o módulo completo, outra prévia encontrou
  `PREVIEW_FACT_EXPIRED` porque a data local era 06/11 e UTC já era 07/11.
  O módulo passou com 41 testes em `TZ=UTC`, alinhando o processo ao ambiente
  CI Linux e às datas UTC; isso não estabelece a causa das falhas anteriores.
  Nova execução integral passou com `TZ=UTC`, `PYTEST_ADDOPTS=--maxfail=1` e
  `caffeinate -di` temporário, sem excluir testes: **5.045 testes Python da
  aplicação**, **100% de linhas e branches** (17.229 statements, 4.726 branches),
  Ruff/formatação e mypy em 272 módulos. Também passaram 91 testes Python de
  motion, três Node de áudio e 62 Node do renderer. PostgreSQL e Temporal eram
  descartáveis, com banco exclusivo `_test` e seis logins runtime restritos;
  `fsync`, `synchronous_commit` e `full_page_writes` foram desativados somente
  nesse banco de teste. O CI não qualifica o resultado criativo nem resolve a
  chamada externa incerta.

## 06/11/2026 — primeira crítica e revisão de contexto

- Três críticas reais retornaram `adequate`, sem correções; estimativa total
  US$ 0,2520500 e reservas US$ 0,75, sem confundir estimativa com fatura.
- Auditoria posterior detectou omissão de direção criativa, feedback, skill
  própria e instruções originais. A rodada demonstra apenas o funcionamento com
  contexto incompleto, sem comprovar qualidade, ausência de falhas ou ganho.
- [Continuação delimitada](evals/plano-ciclo-revisao-motion-2026-11-06.md)
  preparada offline: até nove chamadas/US$ 3,75 adicionais em reservas, dentro da autorização
  original; até uma correção por caso, somente quando justificada. A execução
  posterior interrompida está registrada acima; segue sem decisão humana.

## 06/11/2026 — contrato do ciclo de revisão de Reel preparado

- Registrada a prioridade de Python/API e os [critérios v1](design/ciclo-revisao-motion-2026-11-06.md):
  evidências do render, limites de observação, até duas correções, crítica por
  versão e avaliação humana sem presumir melhora.
- Preparado [plano de comparação](evals/plano-ciclo-revisao-motion-2026-11-06.md)
  com baseline histórico e mesmo ponto de partida; CLI privado implementado.
  Clipe pessoal continua aguardando avaliação; Instagram permanece posterior.
- Reconciliados os resumos e índice com a integração local de referências e o
  escopo confirmado de vídeo, preservando marcos históricos. O titular autorizou
  até US$ 6,75 em reservas e 15 chamadas para Intensa/Dog/Luma, com envio de
  quadros/contexto/código à OpenAI; áudio técnico e escuta humana. O primeiro
  preflight offline detectou erro de cálculo no quadro final de Luma e foi
  interrompido; a correção passou em regressão para duração de 284/30 segundos.
  Não há comparação real,
  chamada paga ou nova homologação nesta preparação.

## 06/11/2026 — clipe pessoal gerado e áudio preservado

- Entregues [MP4 de 46,5s e comparação](evals/ensaio-clipe-musical-pessoal-2026-11-06.md),
  720×1280/30fps, 1.395 quadros, com formas e apoios licenciados de chuva/vitrola.
- Três chamadas autorizadas, estimativa US$ 0,51148, zero retries. Original ASR,
  correções por legendas, direção, revisão escrita e composição preservados.
- HTML/JS executados como recebidos; AAC copiado com payload/PCM/tempos iguais.
  Divergência do cabeçalho AAC foi validada por pacotes reais, sem novo render.
- Decodificação passou; 3 players/26 links em 390/1440 px, sem erro. Ensaios
  locais não qualificam produto/isolamento OS. Avaliação humana pendente;
  sem código de produção, gasto adicional ou repetição do CI integral.

## 06/11/2026 — preparação local do clipe pessoal

- Foco único definido pelo titular: edição do próprio vídeo musical de 46,5s.
  Fonte preservada; AAC, WAV e 12 quadros privados preparados.
- Modo pessoal separado, por consentimento/hash, com controles do browser
  preservados; smoke técnico de 1s/30 quadros e testes negativos passaram.
  Não é peça criativa nem qualificação de produção/isolamento no SO.
- Apoios realistas licenciados preparados; [plano](evals/plano-clipe-musical-pessoal-2026-11-06.md)
  de três chamadas com teto adicional US$ 1,60. Sem envio pessoal/API nova,
  mudança do produto ou execução de CI integral nesta preparação.
- Após preparação, titular autorizou três chamadas/envio pessoal até US$ 1,60.
  ASR recebido na operação `6f4fdd0c-ff03-4dfe-b55c-efc5d396a760`, estimativa
  US$ 0,0047; resposta original e correções semânticas por legenda preservadas
  separadamente. Direção/composição/MP4 ainda pendentes.

## 06/11/2026 — política de variedade musical confirmada

- IA escolhe conforme negócio/peça, varia entre pedidos e pode repetir para
  continuidade de séries/campanhas. Não exige música inédita em toda peça.
- Decisão e resposta da entrevista preservadas; seleção/histórico e validação
  ainda dependem da implementação. Sem mudança de código/peças, nova chamada
  paga ou execução de testes/CI nesta atualização documental.

## 06/11/2026 — feedback positivo do step 1 e limite da seleção musical

- Titular gostou bastante de Dog/Luma e confirmou nível da Intensa nos dois
  casos curtos; apontou a mesma música como possível problema.
- Auditoria confirmou uma única trilha obrigatória e mesmo hash nos dois
  pacotes. Variação de mix não prova seleção musical entre alternativas.
  [Feedback e próxima prova](evals/ensaio-motion-outros-negocios-2026-11-06.md).
- Registrar alternativas licenciadas e escolha contextual/escuta como pendência
  antes da integração; regra de repetição entre pedidos ainda não definida.
- Atualização documental e feedback privado; sem alterar peças/código, iniciar
  novas chamadas pagas ou repetir testes/CI.

## 06/11/2026 — Reels de Dog/Luma disponíveis para avaliação

- Entregues os dois MP4s e comparação com Intensa/Cartaz, com kits próprios,
  inversões de tema e transformação do enquadramento. [Resultado](evals/ensaio-motion-outros-negocios-2026-11-06.md).
- Duas chamadas autorizadas, estimativa US$ 0,5906725. Dog foi recusado pelo
  mixer por IDs de arquivos em vez de aliases; tradução estrita de cinco strings
  e render offline preservaram a resposta paga e toda a animação original.
- HTML/JS recebidos e executados idênticos, sem ajuste visual manual; Luma sem
  adaptação. Decodificação passou; quatro players e 22 links conferidos em
  Chromium com sandbox, 390/1440 px. Áudio medido; sem nova escuta perceptiva.
- Não houve retry pago, mudança de executor/produto ou repetição de CI integral.
  Qualidade humana dos dois novos negócios e etapas seguintes permanecem abertas.

## 06/11/2026 — step 1 preparado para outros negócios

- Titular confirmou marca/experiência sem preços para Dog/Luma. Dois cenários
  congelados com kits/skill/fontes reais, seis quadros do material e quatro da
  Intensa; sem ASR/TTS, intenção manual explicitada. [Plano](evals/plano-motion-outros-negocios-2026-11-06.md).
- Originais preservados; proxies técnicos sem áudio/cortes/crop facilitam render.
  Decisão de direitos pontual registrada, corrigindo cautela anterior excessiva
  sobre Pexels/inferência, sem apagar histórico ou afirmar liberação irrestrita.
- Preflight dos dois casos passou. Duas chamadas/US$ 1,50 adicionais propostos;
  sem envio pago, mudança no executor/produto ou repetição de CI nesta preparação.
- Após preparação, titular autorizou duas chamadas/envio dos pacotes até
  US$ 1,50 adicionais; lote `04e48db9-1313-4a52-a188-7a151a9d0e80` iniciado,
  sem retry automático ou resultado presumido.

## 06/11/2026 — diversidade entregue parcialmente e preferência pela Intensa

- Duas peças novas e comparação com v2/Intensa disponíveis; Papel terminou com
  falha de transporte/gravação, resultado/custo incertos, sem resposta salva ou
  retry. [Resultado](evals/ensaio-motion-diversidade-2026-11-06.md).
- Cartaz e Giz usam funções concretas da biblioteca. Código recebido/executado
  idêntico por hash, sem ajuste manual; MP4s 11,2 s, 720×1280, H.264/AAC.
  Quatro players/26 links conferidos em Chromium com sandbox, 390/1440 px.
- Subtotal conhecido estimado US$ 0,3751375; total desconhecido por Papel,
  com reserva preservada. Três chamadas iniciadas sob teto US$ 2,25, zero retries.
- Titular gostou do Cartaz, menos do Giz por tema/enquadramento; declarou
  Intensa a melhor até agora. Próximo passo são outros negócios, depois
  story/carrossel; voz natural em teste separado. Registro para integração
  atualizado. CI integral não repetido nesta rodada de geração.

## 06/11/2026 — registro criativo e preparação da diversidade

- Registrado feedback positivo da intensa e sequência solicitada: estilos,
  outros negócios, story, carrossel e integração. Criado
  [índice de evidências e transferência](evals/motion-registro-de-validacao.md).
- Preparados cartaz tipográfico, giz e papel com código/fichas MIT, skill própria
  de Reel e mesmos fatos/gravação. [Plano](evals/plano-motion-diversidade-2026-11-06.md).
- Novo CLI/Make para lote com até três cenários, dois trabalhadores, render
  serializado, reserva agregada, preservação de incerto e relatório comparativo.
  Limite de deduplicação entre comandos explicitado; não é runner de produção.
- Preflight e 40 testes Python/três Node offline aprovados; Ruff/mypy do lote
  aprovados. Sem chamada paga ou repetição de CI integral nesta preparação.
- Após preparação, titular autorizou três chamadas/envio do pacote, com teto
  adicional US$ 2,25. Autorização privada vinculada aos três hashes; lote
  `e2bbd3aa-e405-4411-9d56-82752537bc73` iniciado, sem refação automática.
- Titular escolheu vídeos ilustrativos licenciados para os demais negócios;
  inventário privado preserva origem e direitos. Verificar uso no provedor antes
  de enviar. Backup remoto, dependências e integração seguem pendentes.

## 06/11/2026 — exploração intensa de motion concluída

- Após autorização, uma chamada gerou [MP4 intenso e comparação](evals/ensaio-motion-intenso-2026-11-06.md)
  com v2 mínimo e última variante. Estimativa US$ 0,3086025; sem retry ou ajuste
  manual da composição recebida.
- Verificados código/quadros: inversões verde–creme–verde, 42 arcos em ondas,
  letras com movimento de linha, forma protagonista e janela contínua.
- MP4 11,2 s, H.264/AAC; decodificação e links locais passaram. Áudio medido,
  sem escuta perceptiva nova. Qualidade aguarda avaliação final do titular;
  sem alteração do executor/produto ou repetição do CI integral nesta variante.

## 06/11/2026 — feedback da rodada com biblioteca e exploração de intensidade

- Titular gostou um pouco mais da peça `276486e3`, mas ainda prefere o v2;
  registro preserva essa avaliação sem convertê-la em rejeição.
- Pedido de uma versão “exagerada”, com motion mais robusta, e feedback sobre
  verde/creme, letras invertidas e ponto orientam o [próximo ensaio](evals/plano-motion-intenso-2026-11-06.md).
  É exploração criativa, sem estilo universal ou renovação automática de verba.
- Atualização documental; nenhuma chamada, mudança de executor ou execução de
  CI nesta alteração. Histórico das rodadas anteriores preservado.

## 06/11/2026 — nova peça com biblioteca e demonstração em três vídeos

- Após autorização, uma chamada gerou composição com skill própria Reel e
  adaptações concretas de `showreel`, `app-de-motion` e `diagrama-azul-marinho`.
  Código renderizado sem ajuste manual; [MP4 e comparação](evals/ensaio-motion-biblioteca-2026-11-06.md).
- Relatório contém nova peça, v2 mínimo e rodada anterior, com players,
  downloads e trace/custo. Conferidos três arquivos de vídeo e 15 links locais.
- MP4 11,2 s, 720×1280, 30 fps, H.264/AAC; decodificação passou. Estimativa
  conservadora US$ 0,28714, não fatura, sem retry. Aceite criativo pendente.
- 27 testes offline/Ruff/mypy aprovados; CI integral não repetido nesta fatia.

## 06/11/2026 — cenário orientado pela biblioteca, v2 como piso

- Registrado esclarecimento do titular: não copiar o v2; buscar evolução própria
  e entregar comparação HTML como na rodada anterior.
- Preparado cenário com skill própria Reel por versão/hash, código de três
  candidatos selecionados após inspeção local e critérios de movimento. 21
  originais preservados com licenças/manifesto no repositório próprio, sem push.
- Report suporta comparações adicionais com hashes/snapshots, labels e downloads;
  27 testes offline, Ruff/mypy passaram. Make aponta para o novo cenário;
  preflight aprovado. [Plano](evals/plano-motion-biblioteca-2026-11-06.md).
- Após a preparação offline, titular autorizou uma chamada/envio do pacote,
  até US$ 0,75 adicionais. Operação `276486e3-f312-4c5c-aaa6-4975536b9fb3`
  iniciada; resultado pendente, sem refação automática.

## 06/11/2026 — feedback de qualidade do Reel novo

- Titular esclareceu que a peça não é ruim, mas o salto esperado não ocorreu;
  v2 continua preferido por janela horizontal/vertical contínua, suavidade e
  formas/pontos. Feedback preservado sem alterar a saída.
- Auditado uso parcial de biblioteca/skill externa, ausência das skills próprias
  no último request e escolhas explícitas que substituíram mecanismos do v2.
  [Diagnóstico](evals/ensaio-motion-comando-2026-11-06.md). Somente documentação;
  sem geração paga, mudança de código ou nova execução de CI.

## 06/11/2026 — Reel novo concluído após retomada autorizada

- Após reposição de créditos pelo titular, executado retry explícito com nova
  identidade; o 429 anterior e seus registros permaneceram intactos.
- Gerado [Reel novo](evals/ensaio-motion-comando-2026-11-06.md): 11,2 s,
  720×1280, 30 fps, H.264/AAC, com código HTML/JS idêntico ao recebido,
  sem intervenção visual ou correção manual. Composição adapta funções reais
  do motor `cartaz-risografia`; voz, música e dois cliques no mix.
- Custo conservador estimado desta geração US$ 0,3114475; não fatura.
  Decodificação passou; quadros/código conferidos, sem escuta perceptiva nova.
  Aceite criativo e comparação com o v2 continuam com o titular.
- Recuperação do CLI limitada a quota conhecida: 25 testes, Ruff/mypy aprovados;
  CI integral da aplicação não repetido. Resultado não conclui a feature integrada.

## 06/11/2026 — tentativa de gerar o Reel pelo comando único

- Executado o comando pago com a reserva restante de US$ 0,75 da rodada.
  Preflight passou; provedor devolveu 429 `credit_balance_exhausted` em 2,508 s,
  sem conteúdo/uso informado. Nenhum MP4 novo ou retry automático.
- Request, resposta, assets, direitos, identidade e reserva preservados.
  Entrevista de continuação apresentada; sem alteração de chave/modelo ou
  ampliação de orçamento. [Registro](evals/ensaio-motion-comando-2026-11-06.md).

## 06/11/2026 — recuperação explícita de rejeição por saldo

- CLI recebeu `--retry-rejected`, exigindo `--execute` e orçamento explícito
  para uma nova operação. Admite somente 429 de saldo comprovado pelo corpo e
  ledger, sem saída/uso; uso vazio só é aceito junto ao erro específico.
- UUID, reserva e marcador sucessor novos; hashes vinculam a rejeição anterior.
  Nenhum marcador, ledger, reserva ou custo antigo é removido ou reclassificado.
  Estados incertos, rate limit e respostas com uso/saída não são reenviados.
- 25 testes offline, Ruff e mypy strict passaram; nenhuma chamada real nos
  testes. [Recuperação](evals/como-executar-ensaio-motion.md#recuperação-explícita-de-saldo-insuficiente).

## 06/11/2026 — comando único para o ensaio de motion

- Titular escolheu gerar MP4 e avaliar só no final, dispensando cards/frames
  intermediários no ensaio rápido. [Uso](evals/como-executar-ensaio-motion.md).
- CLI local e alvo `make motion-eval` encadeiam cenário fixado, orçamento,
  resposta estruturada, render e comparação, preservando resposta bruta, custo
  e trace. Sem banco/Temporal ou habilitação de formatos no produto.
- Cenário inicial privado reutiliza os inputs fictícios, Jev/transcrição e
  bibliotecas da retomada. Provas offline não representam nova direção paga;
  validação e limitações registradas no guia operacional.
- Validação: 15 testes Python offline, três Node, Ruff e mypy strict passaram.
  A execução completa com resposta local reproduziu o MP4 WAAPI v2 por hash,
  com relatório e sete quadros. Nenhuma API paga ou CI integral nesta fatia;
  testes novos ligados ao alvo existente de CI, sem mudar o fluxo do produto.

## 06/11/2026 — primeira direção concluída; cards para aprovação

- Titular autorizou duas chamadas até US$ 1,50 adicionais e o envio do pacote
  local ao Responses. Duas rejeições anteriores da revisão automática ocorreram
  antes do processo, sem envio ou gasto.
- Chamada 1 retornou HTTP 200/completed em 236,653 s. Estimativa com cache:
  US$ 0,2397635, não fatura; reserva de US$ 0,75 preservada. Resposta bruta salva.
- Cinco cards capturados e vistos, junto a três quadros v2. HTML preservado;
  a primeira captura com diferença de 1 px foi corrigida ampliando o viewport,
  sem alterar a arte, com tentativas registradas. Nenhuma requisição inesperada.
- Aguardando aceite dos cards; segunda chamada não executada e nenhum vídeo
  novo. [Plano e arquivos](evals/plano-retomada-qualidade-motion-2026-11-06.md).

## 06/11/2026 — retomada criativa e fontes próprias selecionadas

- Registrado o [plano de retomada](evals/plano-retomada-qualidade-motion-2026-11-06.md):
  um Reel primeiro, mesma mídia/kit, referência v2 como patamar mínimo e código
  real de três projetos. Escolha automática coerente e intervenções rastreáveis;
  WhatsApp/Instagram fora da prova. Naquela preparação, nova chamada ainda era
  somente proposta, sem autorização.
- Importados 24 originais, em snapshot de 30 arquivos, no repositório local
  `meu-braco-direito-motion-sources`; hashes e verificador offline conferidos,
  avisos MIT e README/Git existentes preservados. Sem commit/push ou verificação
  da privacidade remota; não é espelho completo, backup ou pacote de dependências.
- Executor privado reproduziu o MP4 WAAPI anterior com hash idêntico na mesma
  configuração: prova local da base, sem nova criação ou conclusão do produto.
- CI da clarificação descritiva interrompido a pedido do titular, saída 143,
  sem resultado final. Baseline anterior de 5.044 Python/62 Node preservado;
  nenhuma nova execução de CI nesta atualização documental.

## 06/11/2026 — rejeição criativa e diagnóstico da regressão

- Titular rejeitou Reel/story/carrossel 1c; registrado feedback e mantidos vídeos,
  respostas e ledger. Página de comparação identifica a rejeição.
- Inputs enviados tinham referências vazias e não continham a direção concreta
  do Reel v2. A orientação expressiva anterior perdeu força na migração para
  fichas e contrato técnico. A direção do carrossel já prescrevia textos fixos
  e zooms de 2–3%; perícia comparativa em andamento, sem nova chamada.
- Rascunhos de normalização/admissão permanecem somente em `/private/tmp`, não
  aplicados. CI da correção descritiva foi interrompido a pedido do titular
  (saída 143), sem resultado final ou alegação de qualidade.

## 06/11/2026 — encerramento das chamadas 1c e clareza do contrato

- Após autorização específica, executadas as duas direções restantes. A revisão
  automática permitiu a chamada final com a rejeição do story explicitamente
  informada. Sete chamadas nesta continuação, sem retry; três direções rejeitadas
  localmente, com respostas/uso/reservas preservados.
- Story derivado com sete correções técnicas: MP4 720×1280, 11 s, 330 quadros,
  silencioso; decodificação e quadros verificados. Carrossel de três páginas
  1080×1350 de 6 s montado, com nove correções técnicas rastreadas, sem nova
  chamada; todos decodificados. Página local reúne peças, referência e traces.
- Estimativa global US$ 0,263073 incluindo 1b; reservas US$ 1,55 dentro do teto
  US$ 1,60, sem fatura conferida. Harness privado passou em 88 testes mock.
- Após a última chamada, schema exportado e builder passaram a explicar unidades
  tipográficas, sequência/tempos de keyframes e regras de áudio. Sem alterar
  validadores, versão ou decisões criativas. Ruff dirigido aprovado; CI integral
  interrompido a pedido do titular (saída 143), sem resultado final. Aceite criativo
  e integração de geração/revisão/download pendentes.

## 06/11/2026 — rodada motion 1c e Reel para avaliação

- Executadas cinco chamadas: três Jev e transcrição aceitas; direção Reel
  retornada/rejeitada por invariantes. Resposta, uso e reserva preservados.
- Cópia derivada corrigiu nove interpolações entre estados iguais e um rótulo
  de voz; variante posterior ajustou sete tamanhos de fonte como decisão visual
  explícita do agente. MP4 720×1280/11,2 s H.264/AAC decodificado, com quadros
  inspecionados e limites de fala/legendas registrados; sem refação paga.
- Unidades/invariantes esclarecidos somente nas instruções de dois pedidos
  ainda não enviados, preservando originais, demais campos e orçamento.
  Harness de continuação passou em 71 testes mock; app não mudou.
- Revisão automática bloqueou a chamada de story antes do envio, exigindo
  autorização explícita para retomar após a rejeição. Nova entrevista enviada
  somente para story/carrossel, sem repetir Reel e sem aumentar teto global.
- Estimativa global US$ 0,106955, reserva comprometida US$ 0,55, sem fatura
  conferida. [Peça e relatório](evals/ensaio-motion-v0-rodada-1c-2026-11-06.md).

## 06/11/2026 — retomada e fechamento da validação Jev

- Conferido o CI concluído antes da interrupção: 5.044 testes Python, sem
  pulados, e 62 testes Node, com cobertura de 100%; Ruff e mypy aprovados.
- O mock da comparação foi corrigido sem alterar casos, gabaritos ou custos
  simulados. A execução final passou após a falha já registrada abaixo.
- Continuação criativa 1c preparada com 53 testes simulados, vínculo com a
  reserva anterior e teto global de US$ 1,60. Sem nova chamada ou autorização;
  ainda falta o ensaio real e a integração de geração/revisão/download.
- Alterações existentes e índice Git preservados. Nenhum repositório remoto
  criado; cópia independente das fontes continua pendente de acesso GitHub.
- Plano sincronizado com a base DOM/WAAPI já aprovada; HyperFrames permanece
  como fonte estudada, sem ser dependência obrigatória desse caminho. Encerrados
  somente os dois containers efêmeros do CI após o resultado aprovado.

## 05/11/2026 — Jev: não selecionar item quando não há candidatos

- Titular autorizou rodada1b com sete chamadas/teto US$ 1,60. Primeira Jev
  reconheceu intenção/Reel, mas confiança 0,46 para `offering=none` bloqueou
  lista sem candidatos. Resposta HTTP 200, pedido, ledger e reserva preservados;
  seis chamadas não iniciadas. Estimativa US$ 0,000035, reserva US$ 0,01.
- Adapter omite somente a pergunta de item para lista vazia; limiares originais
  continuam válidos para as perguntas feitas. Não infere catálogo vazio, fatos
  confirmados ou prontidão editorial, nem reclassifica o efeito anterior.
- 55 testes dirigidos com cobertura de 100%, Ruff/mypy aprovados; CI integral
  encontrou um mock antigo que exigia `offering` sem candidatos. Ajustado o mock,
  73 testes do adapter/comparação passaram e o CI integral subsequente terminou
  aprovado nos serviços efêmeros `_test`, conforme fechamento acima. Admissão sem item e nova rodada
  criativa continuam pendentes. [Trace](evals/ensaio-motion-v0-rodada-1b-2026-11-05.md).
- Preparada [continuação 1c](evals/plano-motion-v0-rodada-1c-2026-11-05.md),
  sem autorização: sete novas operações, teto próprio US$ 1,59 e reserva anterior
  US$ 0,01 preservada dentro do teto global US$ 1,60. Cinquenta e três testes locais
  de harness/ponte passaram com mocks, incluindo conferência do ledger anterior
  antes de credenciais/rede e distinção entre áudio do protótipo e compilador
  visual do produto; não houve segunda chamada paga.
- [Desenho da admissão sem item](design/admissao-motion-sem-item-2026-11-05.md)
  registra a próxima fatia de integração, ainda não implementada.

## 05/11/2026 — executor do ensaio e rodada criativa preparada

- Executor privado geral gerou cinco MP4s sintéticos: Reel com mix, story sem
  áudio e três páginas 4:5. Decodificação integral passou; dimensões, duração,
  mudança de frames e bloqueios CSP/rotas registrados. Não prova qualidade criativa
  ou isolamento de produção; a fixture de carrossel tem texto embutido sobreposto.
- Preparada [rodada 1b](evals/plano-motion-v0-rodada-1b-2026-11-05.md), com builder,
  catálogo, wire strict e ponte de render reais. Sete chamadas propostas, reserva
  US$ 1,54/teto operacional US$ 1,60; nenhuma concessão ou chamada paga.
- Harness privado: 33 testes com mocks e sete da ponte; pedido/resposta/hash,
  reserva durável, bloqueio de replay/incerteza e modelo/tier explícitos. Não é
  runner alternativo do produto. Transcrição e revisão da fixture são dependências
  futuras da direção do Reel dentro da rodada autorizada.
- Documentos web sincronizados com carrossel 4:5 e Reel/story 9:16; apenas docs.
  AWS não confirmou arquitetura por token inválido; GitHub continua sem conexão
  e nenhum repositório remoto foi criado. Pacote e backup permanecem pendentes.

## 05/11/2026 — catálogo, contexto de direção e plano de áudio

- CI do segundo bloco concluído: 4.987 testes Python, sem pulados, com 100%
  de linhas/ramos; 62 Node, com 100% de linhas/ramos/funções. Serviços efêmeros
  e dados sintéticos, sem banco do projeto ou chamadas pagas.
- Três fichas próprias versionadas e verificadas por hash, com atribuição às
  fontes MIT preservadas; nenhuma seleção fixa por negócio.
- Builder puro reutiliza contratos de kit/contexto/referências e prepara skill,
  todas as fichas e evidências efetivamente fornecidas. Não chama modelo, anexa
  bytes ou prova alinhamento da transcrição; envelope Responses ainda em preparo.
- Plano técnico de áudio com fontes verificadas, trims, posição, ganho e fades;
  [protótipo isolado](evals/ensaio-composicao-audio-sintetico-2026-11-05.md)
  executou dois sinais sintéticos e conferiu sincronismo PCM,
  AAC e saída silenciosa. Não prova qualidade da fala nem integra produção.
- Testes dirigidos: 52 composição/áudio, 13 catálogo e 23 builder, com 100% de
  linhas/ramos; lint/tipos passaram. CI integral do terceiro bloco concluído:
  5.042 testes Python e 62 Node, sem pulados, com cobertura de 100%. Os dois
  containers efêmeros de teste foram parados após a validação.
- Pendentes: direção por modelo, renderer integrado/empacotado, áudio/legendas
  avaliados, persistência, revisão/download, backup independente e avaliação dos
  três formatos. Nenhuma nova chamada paga ou repositório GitHub criado.
- [Inventário das dependências](design/motion-dependencias-linux-2026-11-05.md)
  distingue avisos dos binários e wrappers e identifica o alvo Docker incompleto;
  não houve download, build ou alteração de deploy nesta revisão.

## 05/11/2026 — contrato v2 e compilador de cenas

- CI do primeiro bloco passou: 4.913 testes, 2 pulados por ausência de binários
  no PATH e 100% de linhas/ramos. Os dois casos sintéticos de vídeo passaram
  com FFmpeg/FFprobe nos testes dirigidos. PostgreSQL `_test` e Temporal efêmeros.
- O titular aprovou avançar com a base WAAPI e escolheu carrossel vertical 4:5.
- Contrato v2 passa a definir geometria/keyframes/tipografia/fades e áudio
  explícito; o tradutor valida snapshots e revalida instâncias alteradas.
  Compilador/runtime próprios usam DOM seguro e perfis separados da direção.
- Fade tem envelope independente da animação, confirmado em prova de pixel
  no Chromium. Áudio mixado, velocidade variável e capacidades ausentes são
  recusados; não há ativação de geração ou promessa de MP4 por essa fatia.
- 148 testes Python dirigidos/100% e 62 Node/100% passaram; contrato entre
  linguagens exercitado para Reel, story e três páginas. `make unit/test/ci`
  incluem cobertura Node; workflow prepara Node 24.18.0 sem dependências npm.
  CI integral concluído conforme registro acima, com binários de mídia explícitos.
- Driver, áudio, fontes/dependências preservadas remotamente, catálogo/seleção,
  integração Temporal e revisão da peça continuam pendentes. Sem chamadas pagas.

## 05/11/2026 — prova local de render e separação da revisão

- Ensaio mecânico WAAPI reproduziu hashes de quadros e MP4 por seek, com executor
  próprio parametrizado. Adaptado depois o Reel v2, preservando material fictício,
  composição e áudio. Corrigido e registrado vídeo congelado na primeira tentativa.
- MP4 final H.264/AAC, 720×1280, 30 fps e 11,200s decodificado sem erro. Revisão
  de seis pares de quadros e comparação técnica de áudio não substituem avaliação
  do titular assistindo/ouvindo. Na entrevista posterior, o titular aprovou
  avançar com essa base técnica para o caso, sem homologar produção. Sem APIs pagas.
- Identificada a falta de aceite durável da peça sem postagem; o fluxo legado
  agenda publicação simulada. Documentado contrato próprio para revisão/coleção.
  Rascunho de UI não foi aplicado; apenas SDDs/changelog da web foram alinhados.
- Preparados plano e insumos privados de rodada futura (teto proposto US$ 1,10,
  nenhuma autorização/gasto), com story sem áudio e seis quadros verificados.
  Catálogo real de estilos e compilador geral ainda impedem submissão/render final.

## 05/11/2026 — primeiras fatias de implementação de motion

- Empacotadas três skills por formato/versão/SHA-256, preservando fonte e índice.
- Adicionado contrato puro de direção: UUIDs, snapshots, cortes, timelines,
  camadas, gráficos, movimento, transições, áudio e legendas opcionais. Reel/story
  exigem gravação e teto de 60s; carrossel valida 3–5 páginas de 5–8s.
- Adapter Jev aceita formatos motion explicitamente elegíveis; capacidades do
  produto permanecem em imagem, sem ativar a jornada incompleta.
- Inspeção e extração local de áudio opcional com limites e hash; duração por
  metadados não prova decodificação/duração de todos os quadros. Sem transcrição.
- Preservados 16 arquivos técnicos originais de `claude-video`, com licenças MIT,
  manifesto e verificador de arquivo/restauração. Sem mídias da galeria,
  execução dos scripts, backup remoto ou dependências empacotadas.
- Entrevista confirmou 50 MiB e pedido de versão menor em excesso de tamanho
  ou duração, sem corte automático.
- Testes dirigidos de skills, contrato, Jev e mídia passaram com cobertura
  integral dos módulos; verificador tem testes e restauração local conferida.
  CI completo em execução em PostgreSQL `_test` e Temporal efêmeros. Sem chamada
  paga, publicação ou alteração no índice Git.

## 05/11/2026 — geração das peças finais antes da postagem

- O titular adiou os itens de verificação e integração de publicação no Instagram
  para fase posterior, substituindo a exigência anterior de postagem nesta entrega.
- Reorganizado o plano em dez fases até geração, prévia, ajustes, aprovação da
  peça e download final; qualidade, segurança, custo e recuperação da geração
  permanecem exigidos. Conta Meta e testes de publicação não bloqueiam a geração.
- Aprovação da peça não autoriza postagem futura; C11 permanece vigente para a
  fase própria de integração. Demais limites de vídeo/carrossel foram preservados.
- Documentos centrais, índice de fases, plano, casos, nota de estudo, docs da web
  e README de skills alinhados. Validação: leitura cruzada, links e whitespace;
  sem alteração adicional de runtime, chamada paga ou publicação. CI de código
  anterior continua pendente.

## 05/11/2026 — entrevistas e alinhamento do escopo de motion

Registro anterior à revisão de prioridades acima. A exigência de publicação para
concluir esta entrega foi substituída; as demais decisões permanecem vigentes.

- Confirmados uma gravação por pedido de edição, até 60 segundos de entrada e
  saída, carrossel de 3–5 páginas com 5–8 segundos por MP4 e estilo escolhido a
  cada pedido, preservando a identidade do kit.
- Ajustar uma página preserva as demais; mudanças nelas exigem confirmação
  prévia, além de nova revisão/aprovação da sequência resultante.
- Publicação integrada no Instagram é obrigatória para concluir a v0 em todos
  os formatos previstos; revisão/download são entregas intermediárias. A
  comprovação de conta, formato e publicação real permanece pendente.
- Esclarecidos retenção já decidida em C04/C09, motor HyperFrames candidato,
  preferência recebida pelo Reel v2 e limites dos registros históricos de gasto
  e ensaios. Registrada autorização de repositório privado para fontes permitidas,
  ainda sem criação. Limites comerciais continuam sujeitos a medição em P05.
- Alinhados os textos das três skills próprias e README do repositório de skills,
  preservando integralmente seu índice Git anterior, e os SDDs/changelog da web.
  Empacotamento das skills e integração do novo contrato continuam pendentes.
- Validação documental por leitura cruzada, links locais e whitespace; nenhuma
  mudança adicional de runtime, chamada paga ou publicação. O CI da fatia de
  código anterior continua pendente.

## 05/11/2026 — início da v0 de conteúdo com motion

- Registrados [formatos, lacunas e quatro casos fictícios](design/v0-motion-etapa-0-formatos-e-casos.md), com Reel v2 como referência específica e limites do ensaio anterior.
- Inventariados os arquivos locais da [claude-video](design/inventario-claude-video-2026-11-05.md), hashes, avisos e dependências. Cópias próprias, direitos por item, backup e empacotamento seguem pendentes; nenhuma fonte externa foi incorporada.
- A proposta integral rejeita padrões específicos de instruções internas para revisar ou aprovar material antes de publicar nos campos públicos; o prompt reforça a separação. A guarda é limitada e não substitui revisão humana.
- Testes dirigidos: 59 passaram; `make unit` passou com 3.955 testes. No `make ci`, Ruff, formatação e mypy passaram; a suíte foi interrompida após 39 testes de integração aprovados em 6min22s por lentidão e não produziu cobertura final. PostgreSQL 17 `_test` e Temporal eram efêmeros; `fsync` foi desativado apenas no PostgreSQL descartável durante a execução. CI completo e cobertura continuam pendentes. Nenhuma chamada paga ou novo ensaio criativo.

## 05/11/2026 — preservação de fontes de motion

- Planejadas cópias próprias, backups verificáveis e empacotamento das fontes e
  dependências permitidas, com teste de operação sem os repositórios originais.
- Nenhum espelho remoto, backup, cópia integral ou integração foi criado nesta
  alteração documental.

## 05/11/2026 — reutilização concreta de fontes de motion

- Detalhada integração de instruções, fichas, composições e scripts permitidos,
  adaptados ao produto e às regras de cada negócio, com versões e atribuições.
- Conferidos os pontos reais do carregador de skills e as licenças publicadas;
  nenhuma integração, cópia de terceiros ou chamada paga foi executada.

## 05/11/2026 — plano da v0 para imagem e motion

- Documentado plano de desenvolvimento para imagens de feed/story, vídeo do
  cliente editado para Reel/story e carrossel com MP4 por página, com escolha
  automática de estilo, limites de evidência e gates de qualidade e integração.
- Registrada proposta de responsabilidades entre skills próprias, catálogo
  interno, dados privados do negócio, fontes externas e HyperFrames candidato.
- Validação documental por inspeção do código e das fontes oficiais; nenhuma
  implementação, chamada paga, migração ou teste de publicação foi executado.

## 05/11/2026 — correção do fluxo de mídia

- Instalada no Codex a skill `claude-video` e aberta sua galeria local de 21 vídeos; 209 arquivos conferidos pelo hash do commit. A checagem de dependências passou com FFmpeg e FFprobe temporários no PATH do processo; detalhes e limites no [estudo](design/estudo-claude-video-2026-11-05.md).
- Titular preferiu o Reel v2 deste ensaio e esclareceu que a escolha do estilo deve ser automática pelo sistema, evitando uma decisão adicional do cliente. Preferência não é aprovação de publicação nem regra geral de estilo.
- [Ensaio de motion com modelos reais](evals/ensaio-motion-referencia-2026-11-05.md) gerou Reel v1/v2 e carrossel com trace, correção de transcrição e ajustes do HTML; reservas US$ 0,78, estimativa ajustada US$ 0,147533 sujeita à fatura. Avaliação visual e auditiva do titular pendente.
- Registrada [proposta do titular](design/biblioteca-estilos-motion-2026-11-05.md) para biblioteca de estilos de motion, sugestão pelo sistema e opção de escolha pelo cliente. Sem implementação nesta alteração.
- O titular esclareceu que não escolhe imagens do acervo; pode enviar imagem e envia vídeo para edição. O acervo não é exigência do vídeo. Áudio do vídeo pode ser extraído para o mesmo transcritor, com integração e sincronização por palavra ainda pendentes.
- Analisada [claude-video](design/estudo-claude-video-2026-11-05.md) e preparados [dois ensaios rápidos](evals/plano-hyperframes-2026-11-05.md), com anexos fictícios e orçamento próprio sujeito à autorização.
- Renderizadas [prévias locais](evals/ensaio-hyperframes-2026-11-05.md) em HyperFrames: Reel e três páginas com áudio; direção pelo agente e Jev simulado, sem chamadas pagas. Aguardam revisão do titular e não comprovam integração, transcrição real ou publicação.

## 04/11/2026 — pesquisa de vídeo e motion

- Pesquisa documental dos repositórios HyperFrames e Howseen, com comparação, direitos, encaixe arquitetural e proposta de ensaios diretos em [estudo](design/estudo-hyperframes-motion-design-2026-11-04.md). Sem instalação, geração ou chamadas pagas; preservadas as alterações anteriores.
- O titular rejeitou as prévias silenciosas e quase estáticas. Novo [ensaio direto](evals/ensaio-motion-valido-2026-11-04.md) produziu vídeo e carrossel com Jev real, direção experimental por modelo, áudio, cortes, transições e legendas. Reservas de US$ 0,32 e uso estimado de US$ 0,019071 dentro do limite autorizado; revisão do titular, áudio e compatibilidade seguem pendentes.
- Dois ensaios diretos e gratuitos produziram uma prévia de vídeo e três páginas de carrossel com MP4 individual; direção pela assistente e Jev simulado. [Relatório](evals/ensaio-video-motion-2026-11-04.md) registra fontes, custos, validação e limitações. Aguardam revisão do titular e não demonstram integração, transcrição ou publicação.
- Registrada direção do titular: edição criativa por IA, com FFmpeg permitido na montagem, e estudo de vídeos e carrosséis animados. O titular escolheu até 60 segundos por vídeo final e testes separados de vídeo gravado e carrossel; entrada e preços seguem por definir; nenhuma ativação de provedores ou chamada paga nesta pesquisa.
- O [estudo](design/estudo-video-motion-2026-11-04.md) compara skills públicas, restrições dos formatos e trabalho de integração. Criadas três skills iniciais no repositório de skills e aprovadas na validação estrutural; elas ainda não geram ou publicam peças no produto.

## 04/11/2026 — procedimento de avaliação criativa rápida

- Registrada orientação do titular para próximos ensaios de qualidade: execução
  direta das etapas e comparação de peças sem preparar banco nem o fluxo completo.
  [Procedimento](design/ensaios-rapidos-qualidade.md) inclui entradas/saídas,
  autorização financeira, identidades duráveis e tratamento de incerteza.
- Testes de banco/integração e CI mantêm base `_test` e roles restritas; um
  ensaio direto não prova integração nem aceite comercial. Alteração documental,
  sem geração ou chamadas pagas nesta atualização.

- Titular preferiu os dois resultados com referências e pediu rastreabilidade dos elementos. [Relatório](evals/bl043-reference-quality-2026-11-04.md) distingue padrões agregados, kit, foto, skills e limites de causalidade; preferência não constitui aceite final.

- Ensaio direto BL04.3 gerou quatro peças com/sem referências e registrou Jev, respostas, tentativas e custos em [relatório](evals/bl043-reference-quality-2026-11-04.md). Reserva US$ 1,52, uso estimado US$ 0,216691; sem publicação ou aceite humano. A primeira resposta editorial com referências foi rejeitada e preservada, seguida de nova tentativa.

- Titular redirecionou a BL04.3 para ensaio direto e rápido das etapas, sem exigir fluxo completo; ver [plano](evals/bl043-reference-quality-2026-11-04.md). A preparação anterior permanece documentada como histórica.

## 04/11/2026 — preparação da avaliação BL04.3

- Inventário inicial do piloto e plano preliminar para comparação editorial/visual com e sem padrões, com critérios de revisão humana, estimativa ilustrativa e limites em [relatório](evals/bl043-reference-quality-2026-11-04.md).
- O controle de padrões requer desenho e prova que preservem snapshot e guardas; conferência individual contra evidências, dimensionamento da guarda dentro do teto de US$ 2 e aceite permanecem pendentes. O titular escolheu dois pares do negócio fictício do piloto, aceitou reservas de US$ 2 com risco de cobrança maior e fará revisão visual pontual do perfil público. Nenhuma chamada paga, geração, alteração de código de produção ou mudança de flags.
- Validação: revisão de instruções, código de integração, histórico e Git dos dois repositórios; 20 testes e seis subcasos de protótipos privados offline passaram. O protótipo não integra o produto; não houve execução de CI para esta preparação.

## 2026-11-04 — Origem por endereço vinculada ao cadastro próprio

- Registrada a decisão de preencher a origem por endereço somente com o cadastro
  salvo de **Endereço do negócio**, em campos somente para leitura, exigindo esse
  cadastro quando ausente. Referências de outras regiões seguem pelo @ manual;
  GPS, raios e ciclos permanecem como existentes.
- Diagnosticado o aviso de busca indisponível: a API retorna a prontidão global
  de descoberta; flags locais persistentes estão desligadas e a configuração
  temporária do piloto não foi carregada no runtime normal. As três credenciais
  estão presentes; não é bloqueio por endereço ou ciclo semestral.
- Web validada com 513 testes e 100% nas quatro métricas, TypeScript, build,
  formatação e três jornadas Chromium em celular/desktop. A primeira execução
  teve um timeout em teste inalterado; a repetição serial passou sem ampliar o
  limite. Conferidos 154 links locais da documentação e whitespace.
- Backend alterado apenas em documentação, sem chamadas pagas, migração ou
  ativação de serviços. O CI anterior do backend permanece em 4.734 testes/100%.

## 2026-11-04 — Retomada BL04.3 documentada para novo chat

- SDD ativo detalha os quatro passos: conferir aprendizados, comparar com/sem
  referências, avaliar com o titular e corrigir/repetir com custo por peça aceita.
- PROJECT, SDD geral, decisões e índice apontam a primeira ação, as entregas,
  evidências anteriores e escolhas do ensaio ainda abertas. O piloto não é
  descrito como geração de uma peça final com referências nem orçamento de imagens.
- Alteração apenas documental; conferidos links locais e whitespace. Não houve
  chamada paga, mudança de código/banco ou nova execução de testes. O último CI
  do código permanece em 4.734 testes e 100% de linhas/ramos.

## 2026-11-04 — Autoria direta e capas de vídeos/Reels

- Aplicada a decisão do titular: publicações do autor selecionado; coautoria ou
  marcação em post de outra conta não habilita a análise.
- Vídeos/Reels usam somente capa e legenda. Carrosséis mistos incluem as capas
  explícitas dos itens de vídeo; nenhuma URL de vídeo é enviada ao downloader ou
  ao Jev. O estado parcial preserva o limite da evidência visual.
- 164 unitários passaram com 100% do adapter; cinco integrações provaram capas,
  legendas, exclusão de coautoria, persistência dos padrões, snapshot e replay
  sem novas chamadas. CI integral aprovado: 4.734 testes, 100% de linhas/ramos,
  Ruff/format e mypy. Sem nova chamada paga ou migração do banco da aplicação.
- A interface explica autoria direta e capa/legenda; dez testes dirigidos/100%
  do componente, TypeScript e Prettier aprovados. Decisões de conteúdo resolvidas.

## 2026-11-04 — Padrões reais no contexto de geração

- No negócio fictício, a referência manual gerou nove padrões editoriais/visuais
  de onze publicações e quarenta imagens; 41 amostras Jev concluídas. A API mostra
  análise parcial e atualização semestral. Snapshot validado inclui os mesmos
  padrões; não houve geração ou publicação de imagem.
- Piloto comprometeu US$ 0,455502 de US$ 5, somando custos Apify e reservas
  Google/Jev. Flags persistentes permanecem desligadas e worker dedicado encerrou.
- Web validada integralmente em 508 testes/100%, TypeScript, build e Chromium.
  Ajuste posterior das mensagens de endereço passou em 13 testes/100% do
  componente, TypeScript e Prettier. CI integral final do backend aprovado:
  4.724 testes, 100% de linhas e ramos, Ruff e mypy. Banco `_test` exclusivo e
  logins restritos removidos pelo runner ao final; banco de desenvolvimento preservado.

## 2026-11-04 — Contabilização Apify após o término

- A coleta aguarda trinta segundos e contadores compatíveis antes de publicar
  custo final; repete apenas GET do run existente. 275 testes/100% no recorte.
- Cinco recibos do piloto foram observados como preliminares. O ajuste de
  30.700 micros foi aplicado pela revisão auditável 0111, sem alterar o teto de
  US$ 5. Validada em 38 integrações, 12 unitários/100%, Ruff, mypy e roundtrip
  vazio; banco local atualizado após backup privado verificado.
- Descoberta real publicou dez candidatos e três destaques; seleção confirmada.
  Feed coletado, mas primeira análise indisponível pelo filtro de autoria/formato.
  Entrevista pendente sobre coautoria e capas/legendas de vídeos.

## 2026-11-04 — Validação real e compatibilidade Google

- Parser ajustado ao ProtoJSON para componentes opcionais de endereço; tipos
  malformados continuam rejeitados. 160 testes/100% nos módulos verificados.
- Ensaio real confirmou 20 candidatos aceitos e três recomendações Jev distintas;
  coleta de perfis e análise ainda em fechamento. Operações anteriores não foram
  reenviadas e suas reservas permanecem dentro do mesmo piloto de US$ 5.
- Banco local atualizado de 0105 para 0110 após backup privado verificado. A
  leitura das referências do negócio informado passou com runtime restrito.
- CI com 4.659 testes aprovados expôs uma fixture antiga do snapshot editorial;
  corrigida junto da prova de bloqueio do renderer legado sem parent. 107 testes
  dirigidos passaram. A rodada seguinte foi interrompida para incorporar o
  contrato real do Google; nova execução integral está em curso.

## 2026-11-04 — Integração da análise e fechamento de referências

- Incorporadas associação e agenda 0108, ledger por amostra 0109 e snapshot
  editorial/visual 0110; o fechamento ainda depende do CI combinado e piloto.
- Guardião Jev: 46 unitários com cobertura integral e 22 integrações com seleção
  canônica, replay, isolamento, reservas, âncora de legenda e recibo Apify.
- Política v2 aplicada ao piloto local sem zerar contadores ou ampliar US$ 5;
  cinco testes financeiros e quatro de endereço aprovados em banco descartável.
- Corrigido teste de privacidade que confundia os dígitos de um endereço com
  UUIDs aleatórios na outbox. A lista exata de campos continua verificada.
- `.env.example` documenta as configurações de referências; flags persistentes
  seguem desligadas. Nenhuma chamada paga nesta etapa de integração.

## 2026-11-04 — Cadastro versionado de endereço próprio

- API autenticada GET/PUT com origem declarada pelo titular, versionamento
  otimista, replay histórico por operação e compartilhamento entre titulares.
- Endereço, histórico, auditoria e outbox permanecem na mesma transação; RLS
  inclui conta e associação ativas. Salvar não consulta fornecedores.
- Validação: cinco testes PostgreSQL com logins restritos, banco exclusivo
  removido ao final e 100% de linhas/ramos nos módulos novos; cinco unitários de
  schema, Ruff e mypy aprovados.
- A fatia ainda não inclui interface conectada, geocodificação ou vínculo à
  admissão/publicação de referências.


## 2026-11-03 — Proteções preparatórias para referências reais

- As revisões 0098 e 0099 foram incorporadas e aplicadas ao banco de
  desenvolvimento após backup privado verificado por leitura. A prontidão com
  role restrita foi confirmada; a API pode precisar ser reiniciada.

- O titular definiu que a decisão de manter uma referência anterior fora dos
  dez será solicitada apenas no início de uma nova rodada após seis meses;
  outra pesquisa por raio na mesma rodada não repete essa pergunta. O contrato
  transacional e a interface dessa decisão ainda estão pendentes.

- A cadeia privada simulada vincula requisições Google e Jev às intenções,
  credenciais e reservas, filtra semelhança antes da pontuação e grava apenas
  lote intermediário sanitizado; falhas e repetição são testadas sem rede real.
  A intenção Google é idempotente e exige busca parental e contexto compatíveis.
- O desempate pela semelhança tem adapter somente simulado e HMAC de pedido
  testados; ainda faltam guarda durável e integração à lista. O titular decidiu
  usar a ordem Google se o Jev não conseguir decidir e autorizou guardar a
  conclusão estruturada de semelhança para recuperação.
- Um adapter e sanitizador simulados pedem ao Jev o grau de semelhança de forma
  explícita e excluem `unknown` antes de calcular a nota, sem interpretar a
  confiança como grau. Foram ligados ao pipeline simulado e à persistência
  privada de evidência; os novos writers seguem sem permissão runtime. A cadeia
  e o snapshot passaram em 15 testes com Nearby/MAC v3 em banco isolado. Dos
  36 testes legados, um falhou de forma intermitente na preparação de custo e
  passou isolado e em sequência de quatro; a causa continua desconhecida.
- O titular determinou que o próprio negócio não apareça nas sugestões e
  autorizou identificá-lo por nome/endereço quando a correspondência for clara,
  pedindo confirmação apenas na dúvida. Um comparador puro e conservador foi
  preparado e passou em 36 testes com cobertura integral; ainda faltam vínculo
  transacional da identidade, confirmação e integração ao fluxo real.
- Uma leitura interna compartilha listas publicadas e escolhas entre titulares
  ativos, preservando seleções antigas. Testes de unidade e PostgreSQL cobriram
  raios ocupados sem publicação, listas vazias, histórico, dados privados,
  outros tenants, viewer e conta ou associação inativa;
  não há rota nem publicação real ativada.
- A base privada também prepara até dez posições finais sem publicá-las. Um
  contrato isolado projeta somente aprendizados de seleções e versões informadas;
  não coleta, verifica procedência, persiste análises ou integra geração.
- Foi preparado em memória o contrato de análise do feed e um downloader de
  imagem limitado a HTTP simulado. A extração multimodal, a autenticação da
  origem, o download real e a proteção de rede ainda não existem. O titular
  decidiu analisar todas as imagens acessíveis dos carrosséis; os contratos e
  adapters simulados não limitam mais imagens por publicação. Os testes dos
  três módulos passaram com cobertura integral de linhas e ramos.
- Ainda faltam conexão da admissão à pesquisa real, recomendação dos três destaques,
  custo Apify, publicação, seleção real, integração à geração e ensaio
  real autorizado. O titular definiu empate pela semelhança e destaques pela
  combinação de semelhança e nota; nenhuma fase completa foi concluída nesta fatia.
- A admissão privada por dispositivo agora possui ciclo próprio separado do
  fake, identidade, auditoria e outbox. Testes isolados cobriram concorrência,
  reapresentação, raios e troca de ciclo; a seleção que inicia o prazo é interna
  e ainda não está disponível. A intenção Google e o pipeline simulado passaram
  junto à nova migration
  em 19 testes, incluindo retenção de raio em estados inconclusivos, com cobertura
  integral de linhas e ramos do serviço; nenhuma chamada real foi feita. A versão
  da chave HMAC é guardada para permitir futura verificação e rotação controlada.
- O cancelamento interno idempotente libera o raio quando não existe nenhuma
  intenção de fornecedor; sua concorrência com a criação da intenção foi testada.
  Ele ainda não tem permissão runtime nem recuperação conectada. Outros estados
  conservam o raio até existir prova de falha conclusiva.
- Foram adaptados mais 13 testes de preservação de prévias históricas. Uma
  execução completa do `make ci` passou por lint, formato e tipos; foi
  interrompida após 324 testes aprovados e 45 falhas de integração, antes de
  completar a suíte. As falhas incluem testes dos fluxos visuais aposentados e
  propostas editoriais; não foi alterado código de produção para contorná-las.
  A cobertura global dessa execução não é válida porque outro teste a utilizou
  simultaneamente; a próxima execução usará arquivo de cobertura exclusivo.
- A suíte de propostas editoriais foi atualizada para usar fatos de catálogo e
  briefings atuais, preservando os testes de revisão, limite e falha incerta;
  seus 14 testes passaram em banco exclusivo. Os testes históricos de prévias
  foram separados do bloqueio de novas renderizações legadas, e mais nove
  variantes de integridade e limpeza passaram no fluxo visual simulado.
- Os arquivos completos de entrega e preservação passaram juntos em 31 testes,
  preservando revisão pelo SHA, bloqueio sem checklist, acesso histórico e
  expiração; nenhuma regra de produção foi alterada nessa adaptação.
- Os módulos de guarda e continuidade visual passaram com 19 testes, incluindo
  relink entre titulares e reserva após reconhecimento de commit perdido. As
  fixtures foram alinhadas à receita integral sem aumentar os timeouts.
- A suíte unitária completa passou com 2.931 testes após atualizar fixtures
  históricas de contexto e manter os testes de privacidade de localização.
- Na web, o comando padrão `npm run test:coverage` passou no repositório
  original com 432 testes e cobertura de 100% em linhas, instruções, funções e
  ramos; o typecheck também passou. A integração real de sugestões segue pendente.
- A contabilidade de feed do Apify e a guarda do efeito Jev para recomendações
  foram exercitadas somente em teste e permanecem sem permissão runtime; faltam
  a associação versionada de perfil, janelas comprovadas e proveniência da
  shortlist. A seleção real interna tem testes
  de ciclo e concorrência, mas não possui publicação confiável nem endpoint.
- O arquivo completo de prévias passou com 40 testes em banco isolado, sem
  skips. As garantias ainda vigentes foram adaptadas ao `visual_fake` e a
  artefatos históricos; o bloqueio de novos vídeos/ajustes locais foi mantido.
- A geocodificação manual tem adapter e reserva preparados para testes simulados,
  sem armazenar resposta ou coordenadas e sem permissão runtime. Ainda faltam
  admissão, confirmação do ponto e integração ao fluxo completo. O titular
  corrigiu a decisão anterior: endereço e coordenadas do próprio negócio devem
  permanecer no cadastro, sem apagamento após a pesquisa. Um sucesso ainda não
  conclui o efeito nem recupera candidatos; a reserva permanece em aberto.
- Foram preparados fences para impedir novos efeitos quando a versão do
  contexto já mudou. A identidade dos recursos da execução Apify tem registro
  privado testado sem acesso runtime para apoiar reconciliação.
- O titular esclareceu que o fluxo esperado do Apify é chamada e resposta,
  sem etapa obrigatória de exclusão no fornecedor. A regra de não guardar as
  publicações vale para nossa base; o adapter experimental de DELETE foi
  removido e nenhuma exclusão no fornecedor será executada pelo fluxo.
- Um carregador privado valida o evento, o contexto vigente e o HMAC antes de
  entregar localização fornecida pelo titular e contexto versionado à activity.
  A cadeia integrada de admissão/carregamento/pipeline passou em 21 testes,
  com 100% de linhas e ramos nos serviços de admissão e carregamento. Ainda não
  está conectada a uma activity ou chamada real.
- Uma regressão conjunta mais ampla das migrations até 0094 passou em 98 testes
  em banco dedicado, incluindo guards, seleção, shortlist, limpeza simulada e
  lote Google de até 20. Não houve chamada HTTP real.
- A revisão 0095 passou em round-trip e 113 testes conjuntos em banco exclusivo.
  Foi aplicada ao banco local após backup privado verificado por leitura integral;
  o backup não foi restaurado. A API anterior pode precisar de reinício.
- As revisões 0096 e 0097 preparam tentativa após prova de não envio e leitura
  compartilhada apenas de resultados publicados. A sequência passou em 43
  testes adicionais no banco exclusivo; foi aplicada ao banco local após novo
  backup cuja leitura integral foi verificada. Os efeitos continuam sem acesso
  runtime, e a nova tentativa por outro titular e após falha remota conclusiva
  ainda dependem de implementação e prova.
- O teto de uma pesquisa também precisará somar reservas de todos os titulares;
  a agregação restrita está em preparação e a claim compartilhada continua
  desativada até que essa garantia seja testada e integrada.
- A [documentação oficial do Google](https://developers.google.com/maps/documentation/places/web-service/place-id)
  informa que Place IDs não possuem tamanho máximo. Os limites atuais nos contratos e índices são técnicos e precisam ser
  revistos antes da ativação para não perder identificadores válidos.

## 2026-11-03 — Parte da suíte de entrega atualizada

- Vinte testes dirigidos de entrega e guardas foram adaptados ao contrato visual vigente:
  esclarecimentos sem geração de prévia, validações de consentimento/canal e
  uma aprovação com `visual_fake` e conferência vinculada ao arquivo. Sem alterar
  código de produção nem afrouxar os gates de revisão.
- Os 20 testes passaram juntos em banco exclusivo `_test`, com logins restritos; Ruff e
  formatação também passaram. O banco temporário foi removido. Outros testes de
  entrega e prévia ainda dependem do fluxo descontinuado; `make ci` completo não
  foi executado nesta fatia.
- Outros oito testes dirigidos de prévias passaram em recortes separados,
  cobrindo privacidade, despacho e retenção com `visual_fake` ou registros
  históricos sintéticos. A suíte completa permanece pendente.

## 2026-11-03 — Origem do perfil e atualização automática

- O titular corrigiu a orientação anterior: perfil retornado pelo Apify deve
  ser usado e analisado automaticamente, sem exigir confirmação do cliente.
  Havendo várias opções, usar a principal indicada ou, se ausente, a primeira
  retornada. A origem permanece Apify, sem alegar verificação independente;
  segue disponível a indicação de outro @ pelo cliente.
- A análise de padrões de até 20 posts do feed deverá ser atualizada
  automaticamente a cada seis meses. As publicações não serão mantidas; somente
  padrões extraídos, com indicação de análise parcial quando aplicável.
- Autorizado guardar temporariamente até 20 Place IDs/notas para recuperação,
  preservando a ordem: Jev filtra semelhança antes de calcular notas. Nenhum
  desses comportamentos foi conectado a provedores reais nesta atualização.

## 2026-11-03 — Preparação simulada de feed Instagram

- Adapter isolado aceita até 20 posts públicos de imagem/carrossel e legendas
  por perfil, mantém conteúdo somente em memória e informa retorno parcial.
  Exige transporte HTTP simulado, build fixo, intenção e guarda; não baixa
  imagens, chama Apify ou integra Temporal. A limpeza dos recursos externos e a
  análise criativa permanecem para as fases seguintes.
- A regra de escolha de perfil permite informar outro @ quando as sugestões não
  servem, mantendo origem do titular e acesso não verificado. Passaram 99 testes
  unitários do adapter e 41 dos contratos/regras, com cobertura isolada de linhas
  e ramos de 100%; Ruff/mypy passaram. Nenhum provedor real foi acionado.

## 2026-11-03 — Semelhança e uso de perfis

- O titular reiterou que não há nota mínima: a lista apresentará os melhores
  negócios pontuáveis disponíveis. Candidatos de semelhança incerta ficam fora.
  Os destaques mostrarão critérios e nota, sem explicação em texto livre.
- Com múltiplos perfis Instagram possíveis, o cliente confirma um antes de
  escolher o negócio, podendo informar outro @ se estiverem incorretos; um único
  perfil não comprovado pode ser sugestão não verificada. O titular deseja
  analisar via Apify até 20 publicações recentes do feed por perfil, incluindo
  imagens e legendas públicas acessíveis. Apenas padrões e aprendizados serão
  guardados; retorno parcial será usado e identificado como parcial.
- Decisões registradas; a análise de publicações e a confirmação de perfis ainda
  não foram implementadas. O titular informou que configurará as credenciais no
  ambiente local; nenhuma credencial foi solicitada na conversa.

## 2026-11-03 — Preparação da descoberta real

- A chamada Places fornece à guarda o método, endpoint, field mask e corpo exato,
  sem credencial; um HMAC vincula requisição, identidade, versão da chave e da
  tarifa, versão de configuração da credencial, valor reservado e ensaio.
- Migrations 0074–0075 preparam busca real e resultados sanitizados, com FK
  composta e RLS: até dez candidatas, até três destaques e opções de Instagram
  não verificadas. Papéis runtime têm apenas leitura, sem writer ou rota.
- Um adapter isolado de semelhança Jev aceita apenas HTTP simulado e devolve
  abstenção quando faltam dados. Não gera explicações nem faz chamadas reais.
- A migration 0076 e a guarda preparam claim durável compartilhando o ledger
  existente, teto cumulativo do ensaio, reserva antes do HTTP e fence do executor.
  Replays não interrompem a tentativa viva, e resultado incerto conserva reserva.
  A 0077 registra resposta vazia de Places com fence, auditoria e outbox e
  reconhece replay sem reenvio; a reserva segue incerta até evidência financeira.
  Só Google está representado nessa guarda; ainda faltam commit sanitizado com
  candidatos, reconciliação, efeitos Apify/Jev e ativação controlada.
- Validação dirigida: 104 testes de Places, vínculo e guarda com HTTP simulado,
  27 unitários de contratos, 63 unitários Jev e quatro integrações de RLS em banco `_test`;
  cobertura isolada de linhas/ramos em 100% nos módulos novos exercitados. As
  migrations desta preparação ainda não foram aplicadas ao banco do projeto;
  CI global segue pendente pela suíte visual legada. A fase de guarda financeira
  real e o armazenamento com prova de efeitos seguem em andamento.

## 2026-11-03 — Notas fictícias por pesquisa

- Cada candidata fake grava a nota integral e as versões da fórmula e fixture na
  conclusão da pesquisa. A leitura usa esse registro e ordena sem arredondar;
  mudanças posteriores na fórmula ou fixture não alteram a nota anterior. Não
  são gravadas estrelas, contagem ou dados reais de provedores. A migração 0073
  recusa candidatas anteriores sem nota comprovada e downgrade que a perderia.
- Passaram 89 testes dirigidos, com cobertura isolada de linhas e ramos de 100%
  nos serviços de descoberta, ciclos, reputação e candidatas e na activity;
  Ruff e mypy passaram.
  A migração foi revertida e reaplicada no `_test` e aplicada ao banco de
  desenvolvimento após backup privado com leitura integral verificada. A API
  iniciada antes da migração precisa de reinício para reconhecer o novo head.
- A migração bloqueia a tabela antes de verificar a presença de resultados, no
  upgrade e no downgrade; testes concorrentes confirmam que não apaga um snapshot
  gravado enquanto aguardava. O cálculo e o arredondamento de apresentação são
  estáveis mesmo se o contexto decimal do chamador mudar.
- A simulação continua desligada por padrão. Lista real, confirmação de
  referência fora dos dez, associação dos perfis e efeito real ainda faltam.
  O CI completo permanece pendente devido aos testes legados descritos abaixo.

## 2026-11-03 — Nova rodada e teto de ensaio

- O titular esclareceu que toda nova pesquisa forma a lista de até dez pela mesma
  regra, usando o retorno daquela rodada do Google; um negócio reencontrado usa
  a nota nova, preservando notas anteriores no histórico. Se uma referência já
  escolhida ficar fora dos dez, o cliente decidirá se deseja mantê-la. A jornada
  real de nova rodada e confirmação ainda não está implementada.
- Autorizado teto total de até US$ 5 para um primeiro teste real controlado,
  somando fornecedores. Limites mensais serão definidos posteriormente. Sem
  chamadas externas ou gastos nesta atualização documental.

## 2026-11-03 — Histórico e confirmação de perfis

- O titular definiu Instagram como única rede inicial; múltiplos perfis sem
  associação confirmada serão apresentados para confirmação pelo cliente. Jev
  considerará semelhança e nota para destacar até três negócios, com explicação.
- Notas anteriores permanecem no histórico de cada pesquisa. Após nova pesquisa,
  candidatos antigos não selecionados poderão voltar à lista se tiverem notas
  altas e estiverem entre os até dez; a composição exata está em esclarecimento
  e ainda não está implementada no fake.
- O titular autorizou testes reais controlados com valores baixos; o teto do
  primeiro teste está em esclarecimento e limites mensais por fornecedor serão
  definidos depois. Nenhuma chamada externa ou alteração de código foi feita
  nesta entrada documental.

## 2026-11-03 — Ciclo simulado de referências entre raios

- A busca fake admite outro raio ainda não usado após a primeira confirmação,
  mantendo o prazo comum de seis meses. A confirmação pode combinar candidatas
  do ciclo atual com referências ainda selecionadas de ciclos anteriores, sem
  duplicar a mesma identidade; outros resultados antigos não são reativados.
  Ao esperar locks, admissão e confirmação usam o relógio atual do banco.
- O titular confirmou guardar somente o Place ID dos dados Google, usar estrelas
  e contagem como entrada transitória e armazenar a nota própria e a associação
  de perfis do Apify. O nome exibido virá do Apify quando disponível; caso
  contrário, será usado o perfil ou outro identificador disponível.
- Os 12 testes dirigidos de ciclo passaram no banco `_test` com logins restritos,
  incluindo concorrência, expiração, busca e seleção em múltiplos raios e
  combinação entre ciclos; o serviço de ciclos teve cobertura isolada de linhas
  e ramos de 100%. Ruff e mypy passaram. O `make ci` completo não passou: testes
  antigos de entrega esperam gerar prévias pelo caminho visual descontinuado;
  a execução foi interrompida após essas falhas. O modo segue fictício e desligado;
  não chama Google, Apify ou Jev, nem implementa persistência dos dados reais.
  Para permitir a coleta de testes com nomes iguais, pytest usa `importlib`; um
  ajuste de formatação preexistente foi corrigido sem alterar a fórmula.

## 2026-11-03 — Ciclo de pesquisa por raio e dados desejados

- O titular esclareceu que a primeira confirmação inicia prazo comum de seis
  meses, com uma pesquisa por raio no ciclo, inclusive outros raios depois da
  confirmação. Mudar endereço ou segmento não libera raio já usado; todos são
  liberados no fim do prazo original. A seleção pode combinar raios, sem renovar
  o prazo, e permanece até nova confirmação.
- Apify pode consultar negócios novos de outro raio durante o ciclo e repetir
  tentativa que falhou sem retornar perfil, mas não repetir consulta bem-sucedida
  aos já encontrados. O titular deseja guardar até dez resultados
  por pesquisa, com Place ID, pontuação e perfis disponíveis, sujeito à validação
  de uso e retenção. A nota continua em calibração.
- Decisões documentadas; o fake ainda bloqueia os demais raios após confirmação
  e precisará ser alterado. Persistência de dados reais e fornecedores reais não
  foram implementados nesta atualização.

## 2026-11-03 — Banco local de desenvolvimento atualizado

- A API de referências retornava erro porque o banco de desenvolvimento estava
  na revisão 0059 e ainda não possuía a tabela criada na 0062. Criado backup
  privado e verificada a leitura integral do arquivo; não foi feito teste de
  restauração. As migrations 0060–0072 foram aplicadas ao banco local para
  sincronizar o esquema com o código em execução.
- A API passou de `not_ready` a `ready`; a tabela de referências existe e o
  banco está na 0072. Um teste de integração da rota passou em banco dedicado
  `_test`, com logins restritos. A sessão real no navegador não foi reproduzida;
  é necessário recarregar a página para confirmar o fluxo do usuário.

## 2026-11-03 — Apresentação das referências e calibração

- O titular esclareceu a jornada futura: exibir até dez candidatos elegíveis e
  destacar até três recomendações explicadas pelo Jev, quando houver candidatos
  suficientes. O cliente escolhe de uma a três entre os exibidos. As indicações
  manuais continuam adicionais. A busca e as recomendações reais seguem pendentes.
- A fórmula de reputação seguirá em teste e calibração; o peso e a escolha final
  continuam abertos. Uso e retenção de dados derivados da fonte exigem validação.
- Atualização documental; sem alteração de código, chamadas externas ou CI.

## 2026-10-31 — Ordenação das sugestões fictícias

- O titular esclareceu que não quer sugestões sem avaliação. A simulação
  descarta candidatos sem média ou contagem positiva e ordena os elegíveis pela
  pontuação experimental completa, antes do arredondamento; poucas avaliações
  não impedem a inclusão. Empates usam o número da fixture como critério técnico.
  Negócios sem Instagram continuam previstos, desde que possam ser pontuados.
- Leituras omitem identidades fake persistidas sem nota na fixture atual, sem
  apagar registros ou seleções. A resposta é recomposta, não um snapshot;
  versionamento segue necessário. Não existe integração ou ranking real aqui.
- Passaram 61 testes unitários e um teste de integração no banco dedicado
  `_test`, com roles restritas; cobertura isolada de linhas e ramos de 100% no
  serviço de fixtures, Ruff e mypy. Sem CI ou chamadas a fornecedores.

## 2026-10-31 — Pontuação com poucas avaliações

- O titular revisou a decisão anterior: negócios com menos de dez avaliações
  podem receber pontuação. Não foi estabelecido corte mínimo de nota 8, e uma
  estrela representa qualidade muito baixa sem exigir valor exatamente zero.
- As duas fórmulas experimentais aceitam de uma avaliação em diante; zero ou
  média ausente não gera nota. Na segunda fórmula o zero para uma estrela é
  consequência da escala atual, não um requisito final. A fixture fake com nove
  avaliações agora recebe nota; o status para dados ausentes é `unavailable`.
  Sua resposta é recomposta em leitura e, portanto, esta mudança altera as
  respostas fictícias anteriores; versionamento histórico continua pendente.
- Foram executados 50 testes unitários dirigidos, um teste de integração no
  banco dedicado `_test` com logins restritos, cobertura isolada de linhas e
  ramos de 100% nos dois serviços, Ruff e mypy. CI e provedores reais
  não foram executados. A ordenação da simulação e a busca real seguem pendentes.

## 2026-10-31 — Pontuação na descoberta fictícia

- O titular escolheu continuar os testes com a segunda fórmula de reputação,
  com peso ainda provisório. A descoberta fake descarta um candidato com
  semelhança predefinida inadequada antes de pontuar e identifica falta de
  informação em candidatos com menos de dez avaliações. A lista permanece na
  ordem da fixture; não é ranking nem análise real pelo Jev.
- O endpoint privado fake recompõe nota apenas das fixtures e a apresenta com
  duas casas; não persiste as notas. Falta versionar cálculo e fixtures para
  garantir histórico imutável. A precisão do cálculo foi estabilizada e 4.010
  combinações fictícias foram verificadas. Fonte real, uso de derivados,
  ordenação e coordenação com os efeitos orçados continuam pendentes.
- Validação dirigida: 64 testes unitários e seis integrações no banco dedicado
  `_test` com papéis restritos; cobertura isolada de linhas e ramos de 100% no
  serviço de candidatos fictícios, Ruff e mypy. Também passaram 48 testes de
  reputação e fixtures após a correção de precisão. Não foram feitas chamadas
  externas nem executado CI.

## 2026-10-31 — Experimentos de reputação e limites de pesquisa

- O titular escolheu testar uma pontuação de reputação de 0 a 10; negócios com
  menos de dez avaliações não recebem nota. A primeira fórmula suavizada pode
  elevar notas baixas. Uma segunda alternativa, ainda provisória, penaliza pouca
  evidência sem aumentar a nota observada. Ambas são funções isoladas com dados
  fictícios, sem ranking real ou integração de fonte. Resultados e limitações em
  [avaliação](evals/reference-reputation-eval-2026-10-31.md).
- O titular escolheu limites por pesquisa, por fornecedor e mensal total, com
  janela em UTC. Uma etapa já admitida pode concluir após revogação; novas
  etapas não devem começar. Valores e ativação requerem configuração explícita.
- Política compartilhada versionada sem versão ativa por padrão, reservas e
  eventos com consumidores Temporal foram exercitados somente com fixtures
  fictícias. Um resultado incerto mantém a reserva; liquidação sem evidência
  verificável é recusada. Hash e operações reais, conciliação com fatura/mês,
  rotação da chave HMAC, provisionamento restrito e integração permanecem
  pendentes. A migration 0071 recusa atualizar ledger 0070 com histórico sem
  migração e reconciliação explícitas. Providers reais continuam desligados.
  A chave fictícia não tem versão: se trocada com operação pendente, o fluxo
  aguarda restaurar a chave anterior e preserva eventual reserva já criada.
- Validação dirigida da fundação fictícia: 35 testes no `_test`, incluindo
  Temporal local, oito testes de workflows e 38 testes de relay/worker;
  cobertura isolada de linhas e ramos de 100% em três módulos novos, Ruff e
  mypy. Migrations de teste não foram aplicadas ao banco do projeto.
- Validação da pontuação: 45 testes direcionados, cobertura isolada de linhas e
  ramos de 100%, Ruff e mypy. O CI não foi executado; sem chamadas externas.

## 2026-10-30 — Contexto e adapters isolados para referências

- Palavras e características gerais do negócio entram no contexto versionado.
  A interface removeu os formulários de fatos livres e promoções; fatos antigos
  do contexto não alimentam novas peças e novos snapshots editoriais ignoram
  promoções legadas do catálogo. Snapshots antigos mantêm sua política; dados
  físicos históricos não foram purgados. O fluxo de ofertas e horários pelo
  WhatsApp e pelas revisões permanece pendente.
- Além da simulação `fake` dos raios e seleção com bloqueio de seis meses,
  há adapters isolados e desativados para Places com tipos principais múltiplos,
  Geocoding, perfis e enriquecimento por Place ID via Apify e mapeamento de tipos
  fornecidos com Jev. Eles não integram a busca real. Guardiões concretos de
  custo, taxonomia e direitos de fonte, associação de perfis e fórmula de
  pontuação permanecem pendentes; não há promessa de ranking ou acesso a posts.
- Validação dirigida: características e palavras, 164 testes unitários e 20
  integrações em banco `_test`; isolamento de promoções legadas, 125 unitários e
  duas integrações `_test`. Interface: 52 testes dirigidos, TypeScript e duas
  jornadas Chromium com serviços simulados. Nos adapters, 66 testes Places,
  39 Geocoding, 73 perfil Apify, 70 Place ID Apify e 58 Jev, com cobertura
  isolada de linhas e ramos em 100%; Ruff e mypy dirigidos. Esses conjuntos
  podem repetir testes. Não foram executados CI ou cobertura global.

## 2026-10-30 — Decisão sobre ofertas no pedido

- Decisão de produto documentada: promoções, ofertas e horários da peça vêm do
  WhatsApp e de revisões, sem cadastro desses fatos na interface. Preço
  explicitamente promocional no pedido vale para a criação, sem confirmação
  de divergência ou atualização automática do catálogo; desconto percentual
  depende de preço de catálogo válido. Fica um campo simples para características
  gerais. O titular autorizou remover informações antigas dessa área sem
  preservar histórico. A implementação dessa jornada está pendente e o uso de
  promoções cadastradas está suspenso como direção de produto; código legado
  ainda existe. Nenhum dado foi removido nesta atualização de documentação.
- Apenas documentação; CI não executado a pedido do titular.

## 2026-10-30 — Prova pontual Nearby por tipos principais

- Uma segunda chamada autorizada repetiu o ponto genérico de Curitiba, raio de
  5 km e ordem `POPULARITY`, buscando até 20 resultados pelos tipos principais
  `cafe`, `coffee_shop`, `bakery` e `pastry_shop`. Vieram 20: 14 com tipo
  principal `bakery`, quatro `coffee_shop` e dois `pastry_shop`; nenhum tinha
  `supermarket` entre os tipos. Na primeira amostra, sete de 20 tinham esse tipo.
  As diferenças de filtro, categorias e momento impedem atribuir causalidade ou
  concluir cobertura. O [registro](evals/google-nearby-order-probe-2026-10-30.md)
  contém apenas dados agregados, sem nomes, endereços, IDs, valores individuais
  ou resposta bruta.
- A nova reserva foi de US$ 0,035 e o total cumulativo passou a US$ 0,280;
  reserva não é fatura. A sonda teve 15 testes HTTP simulados; o CI não foi
  executado, conforme pedido do titular.

## 2026-10-30 — Restrição e compatibilidade do alcance de referências

- O serviço aceita novas escolhas apenas locais de 5, 20 ou 50 km. Preferência
  nacional ou raio legado é preservado quando igual ou omitido; `null` explícito
  remove a preferência. Replays e alterações pendentes admitidas antes da regra
  mantêm compatibilidade. A validação não ativa a descoberta real.
- Validação dirigida: 50 testes, cobertura isolada de linhas e ramos em 100% para
  `editorial_context.py`, Ruff e mypy; banco dedicado `_test`. CI e cobertura
  global não foram executados a pedido do titular.

## 2026-10-30 — Adapter isolado de consulta de perfil

- Preparado adapter Apify desativado para consulta individual de perfil, sem
  integração de produto ou guardião de custos real. Um resultado de perfil não
  encontrado de fonte não comprovada é tratado como inconclusivo; acesso ao
  perfil não comprova vínculo ao negócio nem análise de publicações. A política
  de retenção do dataset remoto permanece pendente.
- Validação dirigida: 73 testes com HTTP simulado, cobertura isolada de linhas
  e ramos em 100%, Ruff e mypy direcionados. Nenhuma chamada externa foi feita
  pelo adapter e o CI não foi executado.

## 2026-10-30 — Ciclo simulado de referências

- Infraestrutura `fake`, desativada por padrão e sem fornecedores externos,
  exercita raios de 5, 20 e 50 km, uma pesquisa por raio/ciclo, confirmação de
  uma a três fixtures, bloqueio por seis meses, troca sem renovar prazo e
  preservação da seleção após vencimento. Contempla compensação de falha
  comprovada e reconciliação de autor revogado. Fixtures são anônimas e não
  comprovam busca, correspondência, deduplicação ou aprovação de perfis reais.
- Adapters Google Places e Geocoding permanecem isolados e desativados, sem
  integração de produto ou guardião de custos real. A pontuação 0–10 não está
  implementada: o titular decidiu que Jev deve primeiro avaliar semelhança e
  eliminar candidatos inadequados, e só então pontuar os restantes. A fórmula e
  os direitos de uso/retenção de dados derivados do Google permanecem abertos.
- A [prova Nearby](evals/google-nearby-order-probe-2026-10-30.md) observou a
  ordem `POPULARITY` em 20 resultados, sem salvar nomes ou respostas brutas.
  Reservas cumulativas Places de US$ 0,245 não representam fatura.
- Validação dirigida: 48 testes funcionais da simulação, com cobertura combinada
  isolada de linhas e ramos de 100% em nove módulos novos; 51 testes simulados do
  adapter Places e 39 do Geocoding. Migrations 0065–0069 aplicadas somente ao
  banco `_test`. CI e cobertura global não foram executados a pedido do titular.

## 2026-10-30 — prova pontual da ordem do Google Nearby

- Uma chamada autorizada buscou até 20 cafés em raio de 5 km de um ponto público
  genérico de Curitiba, usando a ordem `POPULARITY`. Os 20 resultados retornaram;
  sete incluíam `supermarket` nos tipos. A ordem observada não correspondia
  simplesmente à nota ou à quantidade de avaliações. A observação não explica
  o critério do Google nem comprova relevância ou
  cobertura. O [registro da prova](evals/google-nearby-order-probe-2026-10-30.md)
  preserva apenas observações agregadas, sem resultados individuais, nomes,
  endereços, IDs ou resposta bruta.
- Reserva de US$ 0,035 para a chamada; US$ 0,245 cumulativos com as reservas
  anteriores do Places. Não representa a fatura. Sem integração produtiva,
  classificação própria, envio ao Jev ou outras chamadas nessa prova.

## 2026-10-30 — Raios e preparação da descoberta de referências

- A web oferece 5, 20 ou 50 km em opções acessíveis, preservando raios antigos;
  localização do dispositivo é confirmada sem mostrar coordenadas. A opção de
  busca nacional foi retirada; configurações nacionais antigas só são substituídas
  ao salvar um alcance local. O titular definiu uma busca por raio solicitado,
  até dez candidatos por raio e nenhuma tentativa consumida em falha comprovada.
  Confirmar entre uma e três sugestões bloqueia buscas por seis meses, inclusive
  após mudar endereço ou segmento; trocar sugestões não renova o prazo e elas
  permanecem após seu término. @ manuais são adicionais e não contam no limite;
  revalidar perfis e trocar entre candidatos não são novas buscas. Regras de busca,
  sugestões e bloqueio ainda não estão habilitadas na interface.
- O titular propôs pontuação própria de 0 a 10 com nota e número de avaliações,
  sem armazenar esses campos; a fórmula e a permissão de uso ou retenção quando
  derivada do Google continuam pendentes. A pontuação não foi implementada.
- A operação `fake` usa identidade durável, auditoria/outbox e Temporal, com
  fixtures anônimas e sem candidatos reais ou efeito externo. Há adapter Google Geocoding isolado e desativado,
  sem guardião real de custos nem integração; pesquisa e geocodificação reais,
  verificação de perfis e autorização contratual das fontes permanecem pendentes.
- Validação dirigida: 36 testes web, TypeScript e uma jornada Chromium com API
  e GPS simulados; no backend, oito unitários novos e quatro integrações da
  simulação, incluindo Temporal local, 29 unitários de worker/relay, 14 integrações
  legadas e 39 testes simulados do adapter de geocodificação. Cobertura isolada
  de linhas e ramos em 100% nos cinco módulos novos da simulação e no adapter;
  Ruff e mypy dirigidos passaram. Apenas o banco `_test` foi migrado. CI e
  cobertura global não foram executados a pedido do titular.

## 2026-10-30 — decisão sobre avaliação das sugestões

- O titular escolheu que Jev avalie semelhança, nota e quantidade de avaliações
  disponíveis e explique cada uma das até três sugestões, com fonte e uso
  permitidos. Nota de estabelecimento não mede engajamento em rede social.
  Decisão documentada; avaliação automática ainda não foi implementada.

## 2026-10-30 — prova isolada Apify para links sociais

- Uma execução autorizada do actor `capi2/my-actor-1` consultou três sites
  públicos e retornou três respostas HTTP 200. Dois sites retornaram links de
  Instagram; um deles também retornou Facebook, e o terceiro nenhuma rede no
  resultado. Pesquisa separada em guia indicou um perfil para o terceiro negócio,
  cuja associação não está garantida. [Método e resultados](evals/apify-sites-technical-probe-2026-10-30.md).
- A execução informou US$ 0,00005 em eventos, sem leitura/armazenamento adicionais;
  reserva de US$ 0,50 não é fatura. Não foram consultados Places ou Maps nesta
  prova, nem ranking ou perfis sociais. Integração Google/Apify, termos de uso,
  validação de correspondência e consumidor da outbox continuam pendentes.

## 2026-10-30 — referências indicadas e jornada de pesquisa

- Implementados localmente cadastro e remoção de @ indicado pelo titular, com
  observação opcional, isolamento por negócio e snapshot na proposta para
  briefing/trace. A indicação representa escolha explícita, não verifica perfil,
  analisa publicações ou autoriza copiar. A seção de alcance na web usa
  cartões responsivos alinhados ao padrão visual, mantendo as regras existentes.
- Registradas decisões: busca automática inicial, ao mudar segmento ou localização
  e por botão; exibição de negócios sem @ com preenchimento pelo cliente; informar
  falha ou limitação de acesso a perfil público e permitir tentativa posterior.
  Google Places é a fonte a estudar para busca inicial e Apify candidato ao
  enriquecimento; contratos, custos, cobertura e vínculo dos perfis precisam ser
  confirmados. A origem manual ainda exige geocodificação e confirmação.
- Os eventos `reference.created` e `reference.removed` ficam pendentes na outbox,
  sem consumidor; o relay não os entrega. Eles se acumulam e sua destinação deve
  ser resolvida antes da operação continuada da funcionalidade.
- Validação dirigida: 63 testes unitários e 11 de integração backend no banco
  dedicado `_test`, 41 testes web, TypeScript, Prettier e Chromium com API
  simulada. O CI não foi executado a pedido do titular. A prova Apify posterior
  foi isolada e autorizada, conforme o registro acima.

## 2026-10-30 — preferência de alcance para referências

- Contexto versionado e tela de Sobre meu negócio permitem ao proprietário
  configurar pesquisa nacional ou local (raio de 1–50 km), por endereço manual
  ou posição do dispositivo confirmada. Endereço manual exige CEP ou UF e
  cidade, sem fingir que já foi geocodificado. A localização é excluída dos
  prompts de geração. A tela informa que a busca continua indisponível.
- Mantida a compatibilidade de idempotência de contextos antigos e proteção de
  edições não salvas ao abrir Referências. Fontes sociais, Apify, SerpAPI,
  ordenação, limites e pontos a estudar foram registrados sem escolher provedor.
- Validação: 1.657 unitários backend e testes dirigidos adicionais para validação
  de UF, quatro integrações no PostgreSQL `_test`, 35 testes web dirigidos e uma
  jornada Chromium com API simulada. Cobertura isolada do schema e do componente
  novo em 100% de linhas/ramos; CI e cobertura global não executados por
  orientação do titular. Nenhuma consulta paga foi feita nesta fatia.

## 2026-10-30 — prova individual Google Places

- Três buscas repetidas retornaram cinco resultados cada. Links de Instagram
  apareceram no campo de site em três resultados; uma consulta ambígua trouxe
  negócio de outra localidade. Reserva cumulativa US$ 0,210 sob teto US$ 0,50,
  sem fatura confirmada. Resultados brutos não foram salvos em arquivos nem
  enviados ao Jev. Raio, busca nacional e uso em produto continuam não provados.

## 2026-10-30 — prova técnica Google Places

- Três buscas genéricas reais retornaram HTTP 200 e cinco resultados cada, com
  nota e contagem presentes em todos; site presente em 14 de 15. Reserva
  conservadora US$ 0,105 sob teto autorizado de US$ 0,50, sem fatura confirmada.
  Respostas brutas não foram persistidas nem enviadas ao Jev. Sem prova de
  pertinência, cobertura, perfil social ou autorização de uso para produto.
  [Evidência](evals/google-places-technical-probe-2026-10-30.md).

## 2026-10-30 — registro da arquitetura da jornada

- Documentados os processos e repositórios atuais, a coordenação por Temporal,
  os limites da analogia com saga e as partes ainda simuladas da jornada.
  Organização por responsabilidade e visão correlacionada ficam como
  recomendações para discussão, sem decisão de separação ou mudança de código.
- Validação documental: leitura do código e documentos existentes; sem testes,
  CI, chamadas externas ou alterações na execução.

## 2026-10-30 — estudo multissetorial de fontes

- Comparadas capacidades documentadas de Google Places, Foursquare,
  Tripadvisor e dados abertos, com custos consultados e limitações de uso;
  registrada prova proposta em múltiplos nichos. Nenhuma consulta paga,
  credencial, provedor ou capacidade produtiva foi criada.

## 2026-10-30 — estudo de descoberta de referências

- Registradas fontes candidatas para localizar perfis e consultar dados, limites
  documentados da Meta e necessidade de provar campos/permissões com conta de
  teste. Jev pode classificar candidatos recebidos; não é a fonte de descoberta.
  Estudo sem integração, credenciais, chamadas pagas ou seleção de fornecedor.

## 2026-10-30 — qualidade da copy e destino comercial

- Contexto editorial e tela web aceitam canal comercial opcional escolhido pelo
  titular, separado do telefone de identificação. Redação e guarda visual usam
  o contexto versionado, rejeitam canais não confirmados e não presumem clique.
- Ajustado o contrato editorial para texto público/briefing separados e
  verificação de identificadores e direções visuais evidentes. A checagem de
  fatos distingue notação técnica de valores comerciais; ainda não comprova
  semântica nem confere automaticamente a imagem produzida.
- Foram realizados ensaios diretos reais de três peças fictícias; a geração do
  café e da manicure precisou de ajustes manuais no briefing, e a manicure de
  uma segunda chamada editorial. Não comprovam a correção atual. O kit
  fictício independente Ateliê Aurora foi criado para QA isolado; seu uso na
  geração e as referências externas com jornada web permanecem pendentes.
- Validação: 1.630 testes unitários backend, três testes de integração do
  contexto no banco dedicado `_test`, 17 testes da tela web, Ruff, mypy (156
  módulos) e verificação TypeScript. Os dois novos serviços tiveram 100% de
  linhas e branches nos testes dirigidos. CI e cobertura global não executados
  por orientação do titular. Sem novas chamadas pagas.

## 2026-10-30 — geração de peça integral e referências do kit

- Novas propostas de feed/story com briefing selecionam skill versionada, usam
  redação natural e geram conceito, hierarquia, uso de foto, texto, legenda e
  CTA. Provedor editorial desativado rejeita novos pedidos em vez de produzir
  baseline fixo; um fato comercial continua vinculado à autorização.
- `visual_ai` e o simulador `visual_fake` preparam peça integral com pedido,
  briefing, kit, fotos pertinentes, logo autorizada e um exemplo visual do kit
  demo por formato, versão e hash. O modelo devolve a peça completa sem overlay
  fixo. Novos estáticos locais e jobs de receitas anteriores não iniciam efeitos;
  prévias concluídas permanecem revisáveis. Vídeo mantém escopo próprio.
- Migration 0061 fixa a receita e cria traces privados cifrados e protegidos por
  RLS, ligados a tentativa/identidade. Owner consulta requisições preparadas com
  endpoint, parâmetros, skill, versões e referências por hash, sem bytes das
  fotos ou dados privados em logs; o estado preparado não comprova envio incerto.
  A aprovação de peça integral via API requer confirmação humana dos cinco itens
  de qualidade e hash; a publicação simulada revalida a prova. Não há OCR ou
  verificação semântica automática, nem checklist na web/WhatsApp nesta fatia.
- Decisão C18: perguntar antes de continuar em conflito de preço sem instrução
  sobre cadastro; interpretação WhatsApp/Jev e pergunta ficam para depois. A ideia
  de indicações, até três sugestões e opções de fontes para o kit foi registrada
  para estudo, sem afirmar que pesquisa de concorrentes está implementada.
- Foram executados **1.577 testes unitários** e quatro testes integrados finais
  de trace, revisão e geração em banco `_test` exclusivo; também passaram
  baterias dirigidas do briefing e do worker Temporal com provedores simulados.
  Ruff/formatação e mypy (154 módulos) passaram. **CI não executado** por
  orientação do proprietário; cobertura global não verificada.
  Sem chamadas pagas, migração no banco da aplicação ou nova prova comercial.

## 2026-10-29 — comparação visual isolada após correção editorial

- Três chamadas editoriais e seis imagens reais para negócios fictícios,
  com e sem skill visual, em ensaio isolado sem banco, Temporal ou publicação.
  Quatro imagens trazem o preço; as duas de manicure omitem o valor na arte,
  presente apenas na legenda. Café e delivery usam “apresente” como copy de
  público; a guarda lexical passou as respostas, sem garantir qualidade.
- Pares compartilham texto/legenda/CTA; a skill varia apenas a cena visual.
  Um único fato de preço foi pré-selecionado, sem testar seleção do produto.
  [Peças, pedidos e limites](evals/editorial-copy-visual-after-2026-10-29.md).
- Reservas acumuladas US$ 13,065 de teto US$ 15; estimativa desta rodada
  US$ 0,19736825, não fatura. Três testes mock passaram. CI não executado por
  instrução do proprietário; o último CI completo continua o da correção.

## 2026-10-29 — copy editorial gerada pelo modelo

- O provedor editorial real solicita texto da arte, legenda e CTA ao modelo;
  a proposta versionada conserva esses campos e a prévia e a entrega os usam.
  Resposta ausente ou fora das regras não é substituída por copy fixa no caminho
  visual real; o baseline determinístico permanece somente na simulação.
- O catálogo pode fornecer fato próprio para preço regular confirmado e válido,
  vinculado ao item e sua versão. Validade e fontes são revalidadas; a proteção
  lexical é restritiva e não comprova significado. Revisão humana continua
  necessária. Instruir o modelo a incluir preço pedido não garante inclusão;
  interpretação estruturada do pedido permanece pendente.
- Aprovação e publicação simulada revalidam a validade factual; agendamento além
  desse prazo é recusado, preservando o pedido de ajustes. A API da candidata
  expõe a legenda. Testes integrados específicos passaram em banco `_test` para
  expiração antes da aprovação e antes da publicação. `make ci` passou: **1.969
  testes, 100% de linhas e branches**, Ruff/formatação e mypy em 152 módulos.
- A skill continua apenas na direção visual, sem briefing editorial integrado.
  Os testes usam provedores simulados; nova avaliação com modelo real, comparação
  das peças e validação comercial permanecem abertas. Nenhum efeito pago nesta
  alteração.

## 2026-10-29 — três negócios fictícios, seis prévias reais

- Sob teto acumulado conservador de US$ 10, três pedidos fictícios com fotos CC0,
  kit/acervo e preço confirmado geraram seis prévias com e sem skill visual por
  serviços do produto, Temporal, guarda e adapters Jev/OpenAI reais. Não houve
  publicação, webhook Meta, dados de cliente ou alteração do banco da aplicação.
- **Nenhuma das seis peças incluiu o preço solicitado.** O baseline prioriza o
  nome do item e a skill atua apenas no prompt de imagem; CTA também foi genérico.
  A correção editorial e a avaliação do usuário seguem pendentes. A segunda
  prévia foi solicitada internamente; acervo e origem usaram cópias dos mesmos
  bytes. [Peças e evidência](evals/three-business-visual-ab-2026-10-29.md).
- Estimativa pelas nove chamadas **US$ 0,19161307**, não fatura ou custo por
  peça aceita. Holds novos US$ 3,15 e anteriores US$ 6,615 foram preservados;
  total US$ 9,765. Tentativa anterior incerta não foi reenviada.
- `make ci`: **1.920 testes**, 100% linhas e branches; Ruff/formatação e mypy
  152 módulos. Prova de ponta a ponta do executor com transportes mock passou
  em `_test`/Temporal antes dos efeitos. Nenhum commit ou deploy.

## 2026-10-29 — preparação de três cenários e orientação visual

- Integrada orientação visual experimental de skills de feed/story ao percurso
  `visual_ai`, apenas desenvolvimento/teste, desligada por padrão. Migration 0060
  registra ID/hash por prévia, preserva legados e recusa downgrade com dados;
  versão e fontes são revalidadas e vinculadas ao pedido autenticado. Não integra
  briefing/legenda por skill nem seleção automática pelo WhatsApp.
- Três negócios fictícios com kit e foto CC0 foram exercitados em banco novo
  `_test` e Temporal: seis prévias com providers simulados e prova de bytes da
  foto originada de evento de imagem. Evento entra já processado, segunda prévia
  é pedida internamente e acervo contém cópia da mesma foto; não prova webhook
  Meta, escolha automática ou retrieval entre imagens diferentes.
- `make ci` aprovado: **1.920 testes, 100% linhas e branches** (9.459 statements,
  2.612 branches), Ruff/formatação e mypy em 152 módulos. Migration aplicada
  somente a bancos dedicados `_test`; nenhuma geração paga nesta preparação.
  O ensaio real e a revisão das peças ficam pendentes.

## 2026-10-29 — comparação visual com e sem skill

- Autorizado teto independente de US$ 5; duas direções textuais e duas imagens
  concluídas para feed fictício, mesma foto CC0, kit/logo e acabamento. Peças e
  prompts em `.local/evals/visual-skill-ab-20261029/`; sem publicação ou dados
  de cliente. O adapter e overlay do produto foram usados em ensaio isolado,
  não no worker. [Evidência](evals/skills-visual-comparison-2026-10-29.md).
- Estimativa por uso de **US$ 0,04643825** no total; não é fatura ou custo por
  peça aceita. Quatro holds de US$ 1,25 permanecem sem liquidação automática.
  A tentativa textual anterior segue incerta em ledger separado, não reenviada.
- Dry run e 15 testes mock passaram. Ambas as peças mostram prato apesar de
  restrição comum; a imagem com skill parece conter tecido adicional. Revisão
  pelo titular, qualidade/custo comercial e testes pelo produto continuam abertos.
  Sem alteração de código produtivo ou banco da aplicação; `make ci` não repetido.

## 2026-10-29 — ensaio pareado real interrompido

- Autorizado teto total de US$ 5 para oito chamadas de texto com casos fictícios.
  O dry run e 12 testes offline passaram. A primeira tentativa ficou `uncertain`
  e interrompeu o lote; nenhum resultado completo foi obtido e não há comparação.
- Ledger privado conserva reserva de US$ 0,625 e identidade da operação. Custo,
  uso e causa da falha são desconhecidos; a consulta posterior do modelo retornou
  HTTP 200, sem esclarecer a tentativa. Não houve reenvio, imagem ou publicação.
  [Evidência e apuração](evals/skills-paired-attempt-2026-10-29.md).
- A preparação registrou runner e entradas em `.local/evals`; sem mudanças de
  código produtivo ou banco de aplicação. `make ci` não foi repetido. Uma versão
  futura do executor deve preservar diagnóstico seguro antes de outro ensaio.

## 2026-10-29 — avaliação exploratória das skills

- Quatro casos fictícios foram usados em saídas de agentes com e sem skills e
  numa sonda isolada do baseline para três casos. As entradas e contratos diferem;
  não é comparação controlada nem prova de melhora criativa. Os resultados e a
  sonda estão no repositório `meu-braco-direito-skills` em
  `evals/2026-10-29-comparacao-exploratoria/`.
- A skill de story não esclareceu uma escolha ambígua entre serviços; foi
  ajustada e uma repetição independente perguntou qual serviço divulgar. Ambas
  as skills foram verificadas estruturalmente; a observação cobre um caso apenas.
- Pesquisa externa, integração das skills, comparação controlada com modelo e
  revisão comercial permanecem pendentes. Nenhuma chamada paga, imagem, banco ou
  código de produção alterado; `make ci` não foi repetido nesta avaliação.

## 2026-10-29 — primeiras skills editoriais em repositório separado

- Criadas instruções iniciais `instagram-feed` e `instagram-story` no repositório
  `meu-braco-direito-skills`, com quatro casos fictícios e protocolo para comparar
  com o baseline. As skills produzem briefing para revisão, não renderizam ou
  publicam, e não integram automaticamente a API ou o worker.
- Ambas passaram na validação estrutural `quick_validate`; dois exercícios
  independentes com negócio fictício pediram confirmação para serviço ausente e
  preço vencido. Links locais e espaços foram verificados. Não houve comparação
  controlada com baseline, chamada paga, teste de banco ou avaliação comercial.
  A pesquisa de concorrentes e o gate BL04.3 continuam pendentes; `make ci` não
  foi repetido porque não houve mudança de código da plataforma.

## 2026-10-29 — direção para qualidade editorial e referências

- O proprietário priorizou skills de criação de feed e story, com kit, acervo e
  contexto do negócio, antes da pesquisa de referências e da evolução da jornada.
  A pesquisa deverá combinar perfis indicados pelo cliente com descoberta
  automática de negócios semelhantes em destaque; padrões inspiram peças
  originais sem cópia. Jev é hipótese de estudo, não fornecedor escolhido.
- [Plano por fases](design/skills-e-referencias-editoriais.md), decisões, PROJECT,
  SDD e fases registram escopo, avaliação, fronteiras e questões abertas. A
  proposta de um repositório de skills não equivale a criar ou instalar um.
  O gate BL04.3 com titular e custo permanece; chamadas pagas precisam de
  autorização própria. Pesquisa e skills ainda não estão implementadas.
- Validação documental: revisão de consistência, links locais e `git diff --check`; nenhuma
  mudança de produção, chamada paga, migração, teste de banco ou homologação.
  O último CI completo continua sendo o da parte 2 abaixo.

## 2026-10-29 — BL04.2 parte 3: primeira imagem real pelo produto

- Sob autorização explícita de Café do Cedro com foto CC0/logo, teto total de
  **US$ 1** e uma imagem sem publicação, o fluxo do produto concluiu um feed
  `visual_ai` 1024×1280. Jev e OpenAI foram reais; Temporal/worker, guarda,
  claim/ledger e acabamento determinístico do kit/logo produziram JPEG privado,
  obtido pela API autenticada e S3. [Evidência](evals/bl042-first-product-image-2026-10-29.md).
- Uma chamada de imagem `gpt-image-2.5-flare-2026-09-08`, medium, retornou
  2.363 tokens de entrada (2.160 imagem/203 texto) e 378 de saída. Estimativa
  visual: **US$ 0,029635**; duas interpretações Jev somam **US$ 0,000066**;
  total **US$ 0,029701** estimados. Uso não é fatura: a reserva visual de
  **US$ 0,99** permanece `uncertain`, `actual_usd_micros=NULL`, mesmo com run
  terminado e prévia concluída. Não comprova margem ou custo por peça aceita.
- A primeira interpretação não informou formato e o baseline criou story.
  O wrapper de autorização barrou o tamanho antes do delegate HTTP, com zero
  chamadas de imagem demonstradas pela execução única. Conferência do hash
  original/preparo e reprodução dessa barreira sustentaram reconciliação da
  reserva antiga em zero e término explícito do run com efeito resolvido,
  preservando tentativa, marcadores e auditoria. Uma nova origem esclarecida
  como foto/feed e legenda gerou a imagem sob a mesma autorização; não houve
  edição manual de roteiro ou repetição de imagem com resultado desconhecido.
- Prévia `7cda1858-8b68-4350-8734-dc9f4ca115d2` concluída, run `finished`,
  candidata pendente e publicação nula. Hash do JPEG privado:
  `18ee9ae8fe0edcee080fd6d2506b03c18ac4b95fdfa3bef17ba31fe12186e427`.
  Ingresso/prova de canal Meta foram sintéticos e a entrega da candidata foi
  simulada; a execução não comprova WhatsApp completo ou homologação Meta.
- Migration 0059 aplicada ao banco local da aplicação para a execução autorizada.
  Flags persistentes continuam desligadas, sem novos grants ou mudanças no código
  de produção. A autorização é delimitada e não habilita chamadas recorrentes.
  As provas C08/C09 continuam na suíte anterior; uma imagem não revalida todos
  esses cenários. C10 permanece adiada e estados sem prova ficam bloqueados.
- PROJECT, SDD, DECISIONS, fase ativa, índices, README/operação e contratos
  técnicos atualizados. Próxima fatia: **BL04.3**, revisão de feed e conjunto
  post/story com qualidade/custo por peça aceita; depois **BL05**, WhatsApp como
  jornada principal de prévia/ajuste/aprovação e proatividade.
- Validação dirigida aprovada: **94 testes unitários**, `make lint types` e mypy
  em 151 módulos. Com modo `disabled`, flag desligada e limites zero, owner
  consultou a prévia e baixou hash idêntico; acesso anônimo retornou 401.
  Processos temporariamente habilitados encerrados. O `make ci` de **1.914 testes**
  e **100% de linhas/branches** abaixo é o último CI completo, da parte 2 e do
  mesmo código, não repetido nesta execução operacional. Nenhum novo resultado
  de suíte foi inferido da chamada paga.

## 2026-10-29 — BL04.2 parte 2: caminho visual completo conectado

- Persistência/API acrescentam `generation_mode=visual_ai`, distinto de `local`
  e `visual_fake`, com identidade de pedido/fingerprint próprios. A migration
  0059 conserva os registros existentes, exige fingerprint visual e recusa
  downgrade com linhas reais; foi aplicada somente ao banco dedicado `_test`.
  Sem migração do banco da aplicação, novas roles ou grants.
- `DatabaseVisualGenerationRunner` liga pedido, preparo das fontes, guarda
  concreta, reserva por tenant/agregado, claim única, adapter OpenAI, acabamento
  do kit e commit privado por versão/fence/hash. O modo da guarda/claim precisa
  corresponder à prévia persistida; imagem real não é rotulada como simulação.
- Opt-in separado de configuração isolada do adapter:
  `VISUAL_AI_EXECUTION_ENABLED=false` e reserva por tentativa zero por padrão.
  Habilitar exige desenvolvimento/teste, modo OpenAI, chaves de provedor e
  criptografia, aceite único C01 e reserva positiva dentro de ambos os tetos
  mensais. A API usa apenas o pool owner; o worker exige seu pool correlator
  restrito. Configuração incompleta não aciona placeholder local.
- Dispatcher inicia workflow visual com ID estável por prévia, rejeição de
  duplicata e lease de 12 minutos. Activity com prazo de dez minutos, espera de
  agendamento de um minuto e tentativa única. Confirmação perdida ou lease
  vencida não autoriza redispatch do efeito; resultado incerto mantém run/hold.
  Recuperação somente encerra admissão após prova de ausência de tentativa e
  reserva, inclusive não vinculada, e commit terminal da prévia confirmado.
- `StaticPreviewWorkflow` conserva IDs/tempos antigos. A espera da candidata é
  ampliada pelo patch Temporal `visual-preview-wait-v1`, preservando replay.
  A seleção automática de item/fontes exige Jev com credencial/orçamento
  existentes; correspondência lexical não substitui a interpretação.
- C06–C09 e leitores de candidata/consentimento/continuidade/retenção cobrem
  `visual_ai`. Prévias concluídas, versão/hash e proveniência permanecem para
  revisão privada mesmo com execução visual desligada, conservando acesso e
  direitos. Criação admitida conclui após vencimento financeiro; novos inícios
  e publicação exigem plano. Bloqueio explícito, patrocínio revogado e perda de
  identidade continuam impedimentos distintos.
- Web reconhece o modo visual real nos contratos/estados sem tratar simulação
  como geração de IA; laboratório manual continua ferramenta interna DEV.
  PROJECT, SDD, DECISIONS, fase ativa, índices, operação e contratos técnicos
  registram a entrega e deixam a **parte 3** como próxima fatia: primeira chamada
  paga pelo produto, com fontes/credenciais e teto explicitamente autorizados.
- Validação: `make ci` aprovado com **1.914 testes**, **100% de linhas e
  branches** (9.394 statements, 2.582 branches), Ruff/formatação e mypy
  (151 módulos). Web: **375 testes**, **100% nas quatro métricas**, build/formatação
  e **quatro jornadas Chromium** na árvore final (conteúdo local/IA, laboratório e
  aceite). Compose validado sem resolver/imprimir segredos e `git diff --check`
  aprovado nos dois repositórios. Testes novos percorrem API → dispatcher →
  Temporal → runner/guarda → adapter real com transporte HTTP simulado →
  acabamento → revisão privada; PostgreSQL `_test` e Temporal locais,
  fontes/interpretação/storage simulados. Cobrem modo/versão/hash, orçamento,
  continuidade/preservação, resultado incerto e ausência de nova submissão.
  Nenhuma chamada paga nesta entrega. C10, varredura de recuperação e limpeza
  física de PUT incerto continuam evoluções delimitadas, sem desbloqueio por
  inferência nem autorização adicional de gasto.

## 2026-10-29 — BL04.2 parte 1: guarda concreta para a próxima conexão visual

- `DatabaseVisualEffectGuard` e `GuardedVisualSubmissionClaims` implementam
  prova owner de fontes/aceite/run, reserva por tenant/agregado, claim durável
  única com acesso/financeiro revalidados e commit privado por versão/fence/hash.
  Sessões mantêm suas roles e commits separados, sem novos grants ou tabelas.
  O run conserva fontes entre as transações; não há rede sob row lock.
- `admitted_visual_run` envolve o orquestrador inteiro. `effect_resolved` distingue
  efeito terminado de custo conhecido: dinheiro incerto continua reservado.
  Confirmações perdidas de reserva/claim/arquivo conservam prova/hold e objetos
  possivelmente referenciados. Resposta conhecida tardia não vence fence novo
  e encerra a substituta antes de liberar alterações pendentes.
- Edição/revisão de roteiro agora enfileiram comandos, preservando a versão
  atual até o término das criações. Aplicação acontece em nova transação
  proposta → visual após o commit de finish; nunca visual → proposta. Autoria
  é conservada. Alteração de outra fonte já pendente/falhada impede novo comando
  conflitante no laboratório, que conserva formulário para retry.
- Esclarecimento do proprietário: a IA cria roteiro a partir do WhatsApp/contexto;
  o cliente revisa a peça e pede ajustes. Editor manual continua só no laboratório
  DEV. A web mostra espera/falha e consulta aplicação sem antecipar sucesso;
  `pending_change` é opcional nos contratos. Ajuste automático WhatsApp segue BL05.
- `BillingProcessor.save` participa do comercial antes de alterar acesso.
  Revogação de patrocínio já usava `clock_timestamp()` corretamente; regressão
  comprova revogação em transação antiga aplicada após admissão. Usuário/membership
  são revalidados sem criar escritores ou grants de active/papel.
- C05: canal/telefone atuais deixam de compor a identidade da fonte atribuída,
  e a leitura não depende do ator atual do vínculo. Mesmo com relink por outro
  owner válido, a criação original termina e a entrega usa o novo destino.
  Origem exige asset/event do negócio, owner ativo, estado processado e aceite;
  nenhuma mensagem não atribuída ganha origem retroativa.
- `authorize_visual_copy` concentra a validação de fato/texto/CTA antes existente
  no preparo e agora também na guarda. A prova leva o limite factual/proposta/
  preço/promoção para comparação de relógio real na claim/commit após locks,
  evitando iniciar gasto com informação vencida durante espera.
- Rollout: drenar fila/criações com fingerprints antigos antes do novo worker.
  Concluídas preservam revisão pela prova histórica, sem reescrever hashes.
- PROJECT, DECISIONS, SDD geral, fase ativa, índices e
  [protocolo da guarda](design/BL04-effect-guard.md) registram escopo e sequência.
  Mudanças já staged da fatia anterior foram preservadas; nenhum commit/push.
- Próxima entrega delimitada: **parte 2**, modo real explícito na persistência/API
  e conexão dispatcher/worker/runner com percurso simulado; **parte 3**, primeira
  chamada real controlada com fontes, credenciais e teto de gasto explícitos.
  C10, varredura fora do redispatch e limpeza de PUT incerto seguem operacionais,
  mantendo exceções bloqueadas. Nenhum provedor real foi ligado nesta parte 1.
- Validação final: `make ci` aprovado com **1.836 testes**, **100% de linhas e
  branches** (9.284 statements/2.550 branches), Ruff/formatação e mypy (149 módulos),
  PostgreSQL `_test` com logins restritos e Temporal locais. Web: **365 testes**
  com **100% nas quatro métricas** (1.609 statements/2.142 branches/653 funções/
  1.513 linhas), build/formatação e três jornadas Chromium (laboratório pendente,
  conteúdo e aceite). As primeiras execuções web tiveram timeouts em testes
  existentes sob concorrência e passaram sem alterar limites com `--maxWorkers=1`.
  Links locais dos 13 documentos e `git diff --check` conferidos. Caches uv/mypy
  isolados em `/private/tmp`; somente fontes fictícias e providers/storage/HTTP
  simulados, sem chamada paga ou banco da aplicação.

## 2026-10-29 — BL04.2: recuperação sem reserva e provas de concorrência

- O renderer simulado recupera admissão obsoleta/falhada sem tentativa financeira:
  sob locks prévia → ledger tenant, a role correlator comprova ausência de tentativa
  e reserva (inclusive não vinculada), torna a prévia terminal e audita. Só após
  confirmar o commit a role owner conclui o run com o ator/fence originais e aplica
  mudanças elegíveis. Sem tabelas, grants, roles ou efeitos pagos novos.
- Crash e confirmação perdida repetem somente a reconciliação, com prova durável
  e auditoria sem duplicação. Um worker atrasado não reserva nem conclui; uma
  duplicata viva não falha o original. Reserva existente/incerta impede liberação,
  e confirmação perdida da liquidação conserva a admissão bloqueante.
- Reserva e claim usam tempo real em nova instrução após os locks. A reserva
  revalida também após aguardar orçamento; prazo vencido reverte tentativa, reserva
  e agregado. Testes cobrem locks de prévia, ledger tenant e agregado OpenAI.
- Provas integradas de admissão owner → tentativa correlator exercitam a última
  reserva concorrente por tenant/agregado, retenção de custo incerto e ajuste
  tardio sem crédito duplicado. Selecionar a categoria OpenAI no ledger sintético
  não constrói adapter nem chama fornecedor.
- Provas de kit/logo demonstram upload imutável sem alterar a fonte confirmada,
  serialização de draft/confirmação, espera dos runs, bloqueio de novos inícios,
  cancelamento da fila e revisão da prévia com o logo anterior.
- PROJECT, DECISIONS, SDD geral, fase ativa e desenho de atomicidade registram
  escopo e limites. Backend/web estavam limpos ao começar; instruções e SDDs da
  web foram consultados, sem mudança de contrato/API ou arquivos web.
- Permanecem: edição/revisão de roteiro, transições de acesso, recuperação de PUT
  incerto de logo pendente, coordenação global e resultados com reserva/objeto
  incertos. O serviço de recuperação participa do redispatch e de falha conhecida;
  registros fora dessa fila ainda exigem invocação interna explícita, sem varredura
  automática ou ação web/staff. C10 e retenção pós-encerramento seguem adiadas.
- Validação final: `make ci` aprovado com **1.688 testes**, Ruff/formatação e mypy
  (146 módulos); **100% de linhas e branches** (8.989 statements e 2.462 branches),
  sem novas exclusões. PostgreSQL `_test` com logins restritos e Temporal locais,
  fontes fictícias e storage/provedores simulados; nenhum banco da aplicação,
  chamada paga ou homologação externa. Links locais e `git diff --check` aprovados.
  Caches uv/mypy isolados em `/private/tmp` por restrição do ambiente. A web não
  mudou e suas suítes não foram repetidas.

## 2026-10-29 — Recuperação staff C10 adiada

- O proprietário decidiu registrar e implementar futuramente a recuperação de
  pendências de autores sem acesso, na evolução de gestão de acesso/suporte.
  Essa exceção administrativa não bloqueia o encerramento da fatia simulada já
  validada de admissão, continuidade financeira e preservação.
- A regra C10 de recuperação exclusiva de staff e a proteção que impede outro
  owner de assumir/descartar a pendência continuam vigentes. Até a entrega futura,
  a exceção permanece bloqueada; nenhuma função privilegiada, grant, aplicação
  automática ou troca de autoria foi autorizada.
- PROJECT, DECISIONS, SDD, fase ativa, índices e designs registram a prioridade.
  A proposta de suporte fica como referência futura, sem aprovação pendente que
  interrompa a próxima fatia de coordenação. Os demais gates da BL04/provedor real
  permanecem; o adiamento não declara a fase inteira ou a v0 concluída.
- Alteração somente documental, preservando código/testes existentes. Validação:
  links locais, coerência das referências, hashes de código/configuração/testes
  e `git diff --check`. Não repetidas suítes ou chamadas externas: a evidência
  anterior continua `make ci` com 1.642 testes e 100% de linhas e branches.

## 2026-10-28 — BL04.2: admissão e continuidade com provedor simulado

- A admissão `visual_fake` valida proposta, fontes/fingerprint, usuário ativo,
  membership, aceite e plano sob as travas existentes, na ordem proposta → visual
  → comercial. O run e a auditoria são transacionais; a reserva/fence permanece
  em outra transação com a role correlator. Replay ou resultado incerto não
  autorizam segunda execução. Provedor real continua desconectado.
- C08 no recorte visual simulado: vencimento financeiro após admissão permite
  concluir, consultar e entregar a prévia privada. Novas criações e publicação
  continuam bloqueadas. Identidade revogada, bloqueio financeiro e revogação
  explícita de patrocínio não recebem a exceção de vencimento.
- C09: prévias concluídas, proposta, versões do roteiro e snapshots referenciados
  permanecem preservados após os prazos de uso/aprovação. Download privado não
  exige atualizar fatos ou renovar plano; publicação conserva seus gates.
  Entrega de candidata ainda exige versão/estado atuais do roteiro para não
  combinar arte histórica com legenda nova. URLs assinadas continuam temporárias.
- Limpeza conserva tentativas visuais iniciadas e resultados incertos, assim
  como artefatos com chave/hash conhecidos, inclusive leases legadas de purge.
  Drenar workers antigos e conciliar `purging` antes do rollout; não há recuperação
  de bytes já apagados nem política nova de exclusão após encerramento.
- C10 parcial: outro owner não substitui falha nem descarta foto pendente do
  autor original. As roles existentes impedem staff sem membership de recuperar
  a pendência. A [proposta restrita](design/BL04-staff-recovery-review.md), com
  metadados/cancelamento auditado, aguarda aprovação explícita antes de ampliar
  capabilities; nenhuma migration, função privilegiada ou grant foi adicionado.
- Backend e web começaram limpos; instruções/SDDs da web foram consultados.
  A web já usa a listagem e o download privado da API, sem filtro local de plano
  ou prazo; não precisou de alteração neste recorte.
- Validação final: `make ci` passou com 1.642 testes, Ruff/formatação e mypy;
  100% de linhas e branches (8.942 statements e 2.446 branches), sem excluir
  módulos produtivos. PostgreSQL `_test` com logins restritos e Temporal locais;
  efeitos externos simulados, sem banco da aplicação ou provedor pago. Caches
  uv/mypy isolados em `/private/tmp` devido às restrições do ambiente/cache local.
  Links locais da documentação e `git diff --check` também conferidos.
- Permanecem: recuperação staff, coordenação dos demais escritores e da revisão
  por outro owner, continuidade do renderer local legado, prova global de locks
  e recuperação entre commits, guarda/worker visual real e gates BL04.3/BL05.

## 2026-10-28 — Reconciliação de documentação e decisões de continuidade

- PROJECT, SDD, fases, designs, operação e READMEs dos dois repositórios foram
  alinhados ao código e às decisões vigentes. O registro DECISIONS concentra
  produto aceito, implementação pendente e perguntas já respondidas.
- Retiradas das seções normativas as instruções antigas de permissões por
  fornecedor, retenção/exclusão de envios WhatsApp e propostas de grants/holds
  superadas. Jev/retrieval opcional no worker, aceite único, 0057/0058 e os
  limites do fluxo visual simulado são descritos sem tratá-los como homologação.
- O proprietário confirmou C08/C09/C10: concluir criação iniciada se o plano
  vencer e permitir revisão privada, bloqueando novas criações/publicação;
  preservar prévias sem expiração com conta ativa; recuperação de pendência
  cujo autor perdeu acesso exclusivamente por staff, com ação registrada.
  As três regras estão aprovadas e ainda precisam de implementação.
- O prazo de exclusão após encerramento da conta foi adiado para essa fase;
  não implementar exclusão automática nesta etapa. URL assinada, validade de
  fatos, preservação do arquivo e aprovação permanecem conceitos distintos.
- Preservados 52 snapshots backend e quatro frontend, com originais conferidos
  byte a byte e índices de procedência. Changelogs, auditorias e evals datados
  conservam seus registros; a pesquisa de IA/skills antiga aponta ao original.
- Validação documental: 408 links/âncoras locais, integridade dos 56 snapshots,
  coerência das referências e `git diff --check`. Apenas Markdown alterado;
  código, testes, configurações, bancos e serviços não foram modificados.
  Suítes de aplicação não foram repetidas nesta alteração documental.
- Próxima implementação: C08/C09/C10 e coordenação BL04.2 com mocks antes de
  conectar o provedor visual real. Franquias e qualidade/custo seguem BL04.3/F07;
  jornada automática, ajustes e proatividade seguem BL05.

## 2026-10-28 — Aceite único do serviço na contratação

- POST por negócio registra o aceite explícito do aviso versionado, com hash,
  owner, data, auditoria e replay idempotente. A contratação não cria checkout
  sem o aceite atual; assinatura e patrocínio seguem fontes próprias de acesso.
- O contrato substitui permissões individuais de texto, imagem, interpretação
  e transcrição. A web remove os controles de WhatsApp e Informações e
  preferências; contas existentes usam o mesmo check em Plano e acesso.
- Consentimentos antigos não são reescritos ou reativados. Novos pedidos
  editoriais usam uma geração contratual distinta; trabalhos antigos não herdam
  o novo aceite. Mudanças e gerações visuais pendentes impedem o primeiro aceite.
- Desconexão do WhatsApp continua própria do canal; não retira o contrato.
  Configuração de fornecedores, RLS, plano, orçamento e aprovação de publicação
  continuam internos. Nenhuma migration nova ou chamada paga nesta entrega;
  a migration 0058 já existente foi aplicada somente ao banco `_test`, que
  ainda estava na 0057. Validação completa usa PostgreSQL temporário em memória,
  migrations até o head, RLS e logins restritos, além do Temporal local.
- Validação backend: suíte completa com 1.583 testes aprovados; após o relatório
  de cobertura, uma rodada complementar de 24 testes aprovou sete casos novos e
  completou 100% de linhas e branches (8.871 statements e 2.412 branches), sem
  excluir módulos produtivos. Ruff/formatação e mypy passaram. Os dados de dois
  testes visuais antigos foram alinhados ao vínculo com telefone verificado.
- Web: 360 testes, cobertura integral nos quatro critérios, TypeScript, build,
  formatação e três jornadas Chromium com APIs simuladas aprovados. Isolamento
  por negócio, replay, histórico recusado, mudança de vínculo e ausência de
  permissão individual foram exercitados sem chamadas pagas.
- Permanecem: termos comerciais definitivos, integração visual real BL04.2,
  qualidade BL04.3, jornada BL05 e homologação Meta/staging.

## 2026-10-28 — Preservação dos envios e continuidade após troca de número

- A migration 0058 preserva materiais e eventos associados sem expiração,
  rejeitando pedidos ou leases de remoção pendentes até revisão. A limpeza de
  status, mensagens não atribuídas e uploads órfãos permanece separada.
- A API recusa exclusão de materiais WhatsApp de todos os tipos. A edição e
  remoção de fotos desatualizadas do acervo continuam disponíveis.
- O processamento de materiais associados e a entrega simulada continuam
  durante a troca de número e usam o novo vínculo. O envio real de prévias ou
  aprovações não está implementado; aceite único por negócio também é separado.
- Testes direcionados em PostgreSQL descartável, com RLS e roles restritas;
  nenhuma chamada paga ou real à Meta. A migration foi aplicada à base local
  após pausa dos processos, verificação de claims e backup privado; API e
  workers foram reconstruídos e reiniciados.

## 2026-10-28 — Troca de número durante o processamento

- O proprietário definiu que um material já enviado continua sendo processado
  para o mesmo negócio se houver troca de número. Após a troca, a prévia e o
  pedido de aprovação devem ir para o novo número ativo; o cliente não precisa
  esperar a conclusão do processamento para trocar.
- Decisão registrada; o envio para o número ativo e a continuidade após a
  troca ainda não foram implementados e validados no percurso completo.

## 2026-10-28 — Materiais enviados como contexto durável

- O proprietário definiu que o material enviado pelo cliente deve ser
  preservado para contexto e que enviar outra foto é a saída para uma peça de
  que ele não gostou. A expiração automática da foto que motivou a exceção de
  sete dias deixa de ser premissa de produto.
- A interface do histórico já não oferece exclusão de fotos; seu teste passou
  com 29 casos. A API recusa a exclusão de fotos; passaram sete testes
  unitários e quatro testes de integração em PostgreSQL temporário isolado. A
  retenção automática permanece. A [proposta técnica](design/BL04-whatsapp-durable-materials.md)
  descreve o restante da mudança.
- A preservação durável ainda não foi implementada: o código mantém retenção e a
  cópia de fotos do WhatsApp para o acervo é manual. Memória ou skills por
  negócio também não são construídas automaticamente. Nenhuma estrutura ou
  dado foi removido nesta revisão. O proprietário esclareceu que a exclusão de
  fotos permanece no acervo para retirar imagens desatualizadas; no histórico
  do WhatsApp não haverá opção de excluir fotos. O comportamento após o
  encerramento da conta segue para definição.

## 2026-10-28 — Coordenação visual aprovada para desenvolvimento com mocks

- O proprietário aprovou desenvolver e testar a coordenação de geração e
  alterações com travas e ledger existentes, sem criar tabelas nem ampliar
  permissões. A geração real permanece desligada; a retenção de fotos do
  WhatsApp ainda exige uma solução técnica revisada.
- A autorização não substitui a revisão automática nem habilita o POST de
  aceite rejeitado. A revisão automática também rejeitou a extração proposta
  da barreira de geração; nenhuma mudança correspondente foi aplicada.
- Testes diagnósticos na base `_test`, sem rede, reproduziram a inversão entre
  as travas visual e comercial e verificaram que edição de roteiro ou exclusão
  de material WhatsApp podem tornar a prévia indisponível. O primeiro ensaio de
  roteiro usa prévia local sintética, não geração real por IA. As evidências e
  os limites estão no SDD; a correção e a retenção ainda não estão implementadas.

## 2026-10-28 — BL04.2: validação de integração e revisão de bloqueios

- Um teste sintético encadeia briefing, foto, kit, preparo do pedido, reserva e
  adapter de imagem com `httpx.MockTransport`. A resposta, o armazenamento e a
  guarda são simulados; não há rede nem cobrança. Isso valida o encaixe dos
  componentes, não a atomicidade nem a integração ao fluxo do cliente.
- Um teste independente demonstra a visibilidade das evidências de operações
  em andamento com as roles reais e o isolamento entre tenants. Não prova a
  autenticidade completa dos eventos nem autoriza reativar capacidades.
- A revisão automática rejeitou o POST de aceite com reativação de permissões
  legadas por risco de ativação e verificações ainda não comprovadas. O endpoint,
  a tela e os controles existentes permanecem como estavam. A proposta de
  coordenação sem novos grants continua em revisão e não habilita a geração real.
- Validação: ambos os testes direcionados passaram em `_test`, com Ruff; não
  houve chamada paga ou alteração do banco de desenvolvimento.

## 2026-10-28 — Migrations locais até 0057

- Após revisão, o proprietário aprovou aplicar a sequência 0051, 0053, 0054,
  0055, 0056 e 0057 e revisar os controles antigos de IA depois. A base local
  está em `0057_one_business_per_tenant`, com unicidade por organização e
  tabela de aceite; o aceite único ainda não está ligado à jornada.
- Um backup privado posterior à limpeza foi restaurado e migrado em base
  isolada antes da atualização local. Filas, efeitos incertos e Temporal foram
  verificados; API e workers foram pausados e retomados. Foram confirmados
  histórico, RLS e permissões relevantes da tabela de aceite, além de 200 em
  `/health/ready` e `/docs`. A restauração em teste não validou owner/ACLs e o
  backup não inclui objetos ou estado Temporal.

## 2026-10-28 — Limpeza local autorizada de negócios de teste

- O proprietário autorizou remover `Local Spark - validacao local` e `Local
  demo shop`. Os dois registros e suas duas respostas de idempotência foram
  removidos em uma única transação com pré-condições, sem cascata; organização,
  auditorias, eventos processados e patrocínio revogado foram preservados.
- Antes da alteração, foi criado backup privado do PostgreSQL, restaurado em
  base temporária; a limpeza foi validada na cópia. O backup não inclui o
  armazenamento de objetos nem o estado do Temporal. A base permanece em 0050;
  nenhuma migration foi aplicada nesta operação.

## 2026-10-28 — Proteção de um negócio por organização

- Com aprovação do proprietário, a API recusa nova criação com
  `BUSINESS_ALREADY_EXISTS` e serializa pedidos simultâneos por organização;
  replay idempotente e conflito de conteúdo são preservados, sem gravação
  parcial ao recusar a criação. A migration `0057` acrescenta unicidade por
  organização e interrompe antes de mudar o banco se encontrar duplicatas.
- A migration foi aplicada somente à base `_test`; a base de desenvolvimento
  segue em `0050` e contém uma organização com dois negócios. A decisão sobre
  esses registros e a aplicação local das migrations permanece pendente. A
  prontidão exige que a base esteja no head do código.
- Os testes antigos que usavam múltiplos negócios por organização foram
  adaptados para contas distintas, preservando os testes de isolamento. Não
  houve chamada paga nem alteração de assinaturas.
- A violação da restrição por um processo antigo concorrente é convertida para
  o mesmo erro de negócio, com rollback da operação no savepoint. Passaram 23
  testes de integração de cadastro e onboarding, 23 unitários relacionados e
  33 testes de integração adaptados. O CI completo passou com 1.530 testes e
  100% de cobertura, além de Ruff e mypy.

## 2026-10-28 — Uma organização por negócio

- O proprietário definiu uma conta e uma organização para cada negócio. Assim,
  a cobrança já vinculada à organização poderá ser reaproveitada. A proposta
  anterior de adaptar as tabelas de cobrança para vários negócios foi superada.
- A [revisão atual](design/one-business-per-organization.md) apresenta a
  garantia da regra e registra que há uma organização local com dois negócios
  e patrocínio histórico inativo. Nada foi alterado na base; o tratamento dos
  dados existentes e a restrição de unicidade dependem de revisão e aprovação.

## 2026-10-28 — Transição para aceite único: concorrência

- As alterações existentes de autorização de WhatsApp, transcrição e Jev passam
  a compartilhar o bloqueio transacional por negócio já usado pelo aceite. Isso
  evita que uma delas ocorra simultaneamente ao registro do aceite; não muda
  a decisão do cliente nem altera tabelas ou credenciais.
- Validação: quatro cenários de concorrência passaram na base `_test`, sete
  testes unitários relacionados e Ruff passaram. Nenhum provedor foi chamado.
  O POST do aceite e sua integração à web
  continuam pendentes, assim como o tratamento dos registros antigos e a
  cobrança por negócio. A migration 0056 não foi aplicada à base local. A
  proposta de cobrança foi detalhada para revisão, sem executar migrações.

## 2026-10-28 — Decisão: cobrança e aceite por negócio

- O proprietário definiu cobrança e aceite separados por negócio, mesmo quando
  a mesma pessoa possui vários negócios. A implementação ainda cobra por
  organização; nenhuma alteração de banco, cobrança ou integração foi feita.
- A [proposta de revisão](design/review-billing-and-agreement-per-business.md)
  compara o aceite histórico com `0056` e descreve alternativas de cobrança para
  o proprietário decidir antes da implementação. O proprietário aprovou usar
  `0056` e preservar `consents`; a integração ainda está pendente. Os controles
  de IA de Sobre meu negócio deverão sair junto com a jornada de aceite único
  funcional. O proprietário esclareceu que, na jornada comercial inicial,
  o WhatsApp será conectado após contratação e aceite; não se propõe uma fila
  especial para mensagens anteriores ao aceite.

## 2026-10-28 — IA como parte do serviço contratado

- O proprietário corrigiu a jornada: não exigir que o cliente escolha OpenAI,
  TypeSafe, imagem ou transcrição como ativações separadas. A contratação deve
  explicar o uso de IA e registrar uma única versão aplicável do serviço.
- Contas de teste existentes devem conhecer e aceitar os termos atualizados uma
  única vez antes do uso. Os termos anteriores de validação local não são
  convertidos silenciosamente. Preservar registros/tabelas e controles de acesso,
  orçamento, direitos sobre material e aprovação de publicações.
- O proprietário confirmou que a transcrição por IA de áudios enviados também
  integra o serviço, sem confirmação separada. A implementação anterior que
  tentava ativar as capacidades em conjunto foi rejeitada pela revisão automática
  enquanto os gates integrados ainda não estavam validados.
- Os gates por fornecedor permanecem no backend até a substituição funcional;
  essa decisão não torna a geração visual real pronta para clientes.
- Foi preparada a leitura versionada e uma transação interna de aceite por
  negócio, testada em `_test`; o POST e a tela única ainda não estão conectados.
  A confirmação explícita inclui transcrição de áudio. A entrada do WhatsApp
  pode marcar mensagem sem aceite como falha definitiva. A decisão posterior
  determina conectar o canal após contratação e aceite, sem criar fila especial
  para mensagens anteriores; os dados locais existentes seguem em revisão.
  A migration 0056 não foi aplicada à base de desenvolvimento. Documentos
  apresentados seguem como validação local.
- A primeira ativação conjunta foi rejeitada pela revisão automática por falta
  de decisão explícita sobre áudio e gates integrados; o proprietário confirmou
  a inclusão do áudio e a alternativa reduzida foi testada, mas não exposta.
  A retirada de um novo endpoint de desconexão também foi rejeitada; a corrida
  identificada nele foi corrigida e testada com o mesmo lock por negócio.
- Validação: `make ci` passou com 1.513 testes e 100% de cobertura; a web passou
  com 353 testes e 100% de cobertura. Não houve chamada paga de IA nesta rodada.

## 2026-10-28 — Acervo: quarentena e recuperação do negócio

- O autor pode descartar um upload de resultado desconhecido após vencer sua
  reserva e reenviá-lo com nova operação; a chave antiga permanece privada e
  indisponível. PUTs novos usam uma tentativa e prova durável; registros legados
  sem prova não são considerados seguros para retomada ou exclusão.
- A migration 0055 protege a quarentena no banco contra transições de workers
  antigos. Isso não encerra efeitos externos já em andamento nem prova que
  objetos legados excluídos não reapareçam; drenagem e reconciliação são
  obrigatórias. A limpeza física da quarentena e o cancelamento por outro owner
  seguem pendentes. As migrações foram testadas somente na base `_test`.
- Validação da rodada: `make ci` passou com 1.462 testes e 100% de cobertura de
  linhas e branches; a web passou com 336 testes e 100% de cobertura.

## 2026-10-28 — Cancelamento de propostas editoriais após reautorização

- O lock de negócio e uma geração de consentimento impedem reativar propostas
  enfileiradas para OpenAI antes de uma retirada, mesmo após nova concessão.
  Propostas antigas sem prova não são enviadas ao provedor; o histórico não é
  apagado e o processamento local independente continua. A autorização
  Jev/TypeSafe permanece separada da OpenAI.
- A espera da retirada editorial foi retirada da implementação: uma cascata pode
  apagar a proposta que servia como prova do efeito ainda em andamento. A revisão
  automática rejeitou o grant de leitura para a tabela de uso sem revisão de RLS
  e rejeitou também uma reversão combinada de barreiras na prévia; por isso a
  migração 0051 e seus campos de proteção permanecem sem emissor ativo. A retirada
  atual continua imediata, sem prometer espera. A geração real segue bloqueada.
- Implantação mista com workers antigos é insegura: parar tráfego e workers,
  aplicar as migrações e iniciar versões que conheçam o epoch antes do uso.

## 2026-10-28 — BL04.2: execução Temporal de imagem

- Workflow separado com timeout próprio e no máximo uma tentativa, sem alterar
  o histórico de `StaticPreviewWorkflow`. Teste com Temporal real confirma que
  uma falha da activity não repete o efeito. O worker ainda não o registra e
  nenhum provedor foi conectado; a guarda de fontes continua pendente.

## 2026-10-28 — BL04.2: acabamento simulado e ensaio de imagem sintética

- Proprietário definiu que a expiração da retenção de uma foto WhatsApp deve
  aguardar uma geração já iniciada e excluir a origem em seguida; resultado
  incerto permanece em verificação. Prévia concluída continua para revisão após
  excluir a origem. A mesma espera vale para retirar autorização de WhatsApp
  ou de IA de texto durante geração visual. Essas regras ainda não estão implementadas.
- Se a retenção da foto e a própria prévia vencerem durante a geração, o
  proprietário decidiu manter a prévia por sete dias após a conclusão. A regra
  também aguarda implementação.
- A inclusão de foto no acervo reserva a mudança antes do upload e aguarda as
  criações admitidas. Upload com resultado incerto permanece privado e bloqueia
  o negócio; o cliente é orientado a procurar suporte, pois a reconciliação desse
  caso ainda não foi implementada. A proteção de fontes WhatsApp segue pendente.
- Um teste de integração usa Temporal e PostgreSQL reais para percorrer o fluxo
  sintético até a revisão de uma prévia simulada com kit; não chama Meta ou OpenAI.
- Validação final: `make ci` passou com 1.444 testes e cobertura de 100% de
  linhas e branches. Os testes de interface da coleção passaram (28 casos),
  assim como a verificação de tipos do frontend.
- O worker `visual_fake` prepara referências e aplica o acabamento do kit sobre
  uma cena neutra, mantendo marca de simulação. Não gera imagem com IA e não
  habilita o fornecedor real para dados de clientes.
- Uma chamada OpenAI isolada foi autorizada até US$ 1 e executada uma única vez
  com fixture fictícia e foto CC0. O uso estimado foi US$ 0,020615; resultado,
  limites e evidência estão em [evals](evals/bl042-synthetic-brand-finish-2026-10-28.md).
  Isso não é integração real nem prova de fatura ou custo por cliente.

## 2026-10-28 — Número WhatsApp por negócio

- Decisão de produto: a versão inicial terá um número WhatsApp ativo de cliente
  por negócio. Suporte a vários números é uma evolução futura; o compartilhamento
  de histórico e as regras de mensagens serão definidos nessa fase.
- A decisão não restringe contas proprietárias na web nem resolve a limitação
  já identificada para alterações pendentes entre proprietários diferentes.
  Apenas documentação alterada; nenhuma integração real foi homologada.

## 2026-10-28 — Espera para alterações durante criação visual simulada

- A decisão de mudança imediata foi substituída: pedidos de alteração aguardam
  criações já iniciadas; trabalhos na fila são cancelados e novos inícios ficam
  bloqueados. A prévia concluída permanece identificada para revisão.
- O modo simulado cobre parcialmente contexto editorial, catálogo, confirmação de kit e
  alteração/exclusão de fotos do acervo. Fila e falhas são persistidas; a
  interface mostra espera e acompanha o resultado.
- Limitações: outros escritores de fontes, remoção física automática em todos
  os casos, pedidos de outro proprietário e geração real seguem pendentes.
  A revisão automática rejeitou a troca temporária de identidade na sessão por
  risco de vazamento de autorização; não foi aplicada nem contornada.
- A retenção passou a usar a chave de objeto efetivamente registrada na prévia;
  isso corrige a remoção de arquivos sob diretórios de tentativa. Objetos sem
  chave persistida após resultado incerto ainda exigem reconciliação própria.
- Validação: `make ci` passou com 1.363 testes e 100% de cobertura de linhas e
  branches. A migração `0050_visual_pending_changes` foi aplicada à base `_test`
  e ao banco local de desenvolvimento. Nenhuma chamada paga foi realizada.

## 2026-10-28 — BL04.2: decisão de aguardar criações em andamento

- O proprietário substituiu a decisão de alteração imediata: solicitações de
  mudança de kit ou contexto e exclusão/alteração de foto aguardam o término
  das criações já iniciadas. Enquanto pendentes, a fila ainda não iniciada é
  cancelada e novas criações não começam; depois a mudança é aplicada.
- A retirada da autorização mantém a regra de espera e a prévia concluída
  durante essa espera permanece disponível. A prévia concluída antes da mudança
  de fonte também permanece disponível para revisão e deve ser identificada como
  anterior à alteração; publicação segue os direitos e a aprovação aplicáveis.
- Esta entrada registra decisão, não implementação. Os testes anteriores do
  simulador cobrem a regra substituída e ainda precisam ser atualizados.

## 2026-10-27 — BL04.2: orçamento agregado e endurecimento parcial

- Adicionado teto mensal agregado para reservas OpenAI, separado do teto por
  tenant, sem armazenar dados de clientes no agregado. Resultado incerto mantém
  a reserva; chamadas fora deste ledger e diferenças de fatura não estão cobertas.
- O claim também consulta associação e conta ativa. Esta defesa não serializa
  alterações concorrentes e não é a guarda completa exigida para envio real.
- Acabamento experimental produz JPEG compatível com prévias privadas e preserva
  o objeto em caso de commit incerto; um desenho Temporal separado registra os
  gates pendentes. O worker real permanece desligado e não há publicação.
- A disponibilidade visual não é anunciada apenas pela presença de credencial.
- Validação: Ruff, formatação, mypy e testes focados passaram; 68 testes
  mediram 100% de linhas e branches nos três serviços de custo, envio e
  orquestração. A migração `0049` passou por downgrade/upgrade na base `_test`
  e foi aplicada ao banco local de desenvolvimento. Nenhuma chamada paga foi
  feita. O CI completo não foi repetido nesta alteração.

## 2026-10-27 — BL04.2: decisão de alteração imediata de fontes

- Proprietário definiu alteração imediata de kit ou exclusão de foto durante a
  criação, com descarte da prévia antiga. Dois testes concorrentes confirmam
  esse comportamento no fluxo simulado; o envio real ainda não está habilitado.
- Serviço experimental de acabamento prepara cena sem texto e reaplica kit,
  logo e textos verificados; orquestrador isolado com guard injetado foi testado
  com mocks. Ambos permanecem fora do worker até existir guarda efetiva para
  todas as fontes, consentimentos, orçamento e tratamento de falhas.
- Alternativa de travas cooperativas foi prototipada e retirada dos serviços
  existentes: a cobertura integral dos escritores e a recuperação de falhas
  ainda não foram demonstradas. A avaliação está na proposta de atomicidade.
- `make ci` passou com 1.310 testes e cobertura de 100% de linhas e ramos; não
  foram feitas novas chamadas pagas nesta entrega.

## 2026-10-27 — BL04.2: ensaio isolado e componentes experimentais

- Uma chamada real apenas com fixture fictícia e foto CC0 produziu prévia de
  feed; custo estimado US$ 0,026272, sem comprovação de fatura ou custo mensal.
  O [relatório](evals/bl042-guarded-synthetic-feed-2026-10-27.md) registra
  reservas, falhas de fidelidade e o escopo isolado do ensaio.
- Acabamento experimental e executor com CAS do ledger adicionados como peças
  isoladas. Nenhum liga o worker à OpenAI: fonte/consentimento ainda não são
  validados atomicamente com a reserva e o acabamento precisa de avaliação.
- Validação: `make ci` passou com 1.267 testes e 100% de linhas/ramos. Após
  corrigir o fechamento de conexões SQLite no runner do ensaio, seus sete
  testes offline passaram com `ResourceWarning` tratado como erro. Nenhuma
  chamada adicional foi feita.

## 2026-10-27 — Retirada gradual da autorização visual simulada

- Solicitação bloqueia novas admissões, cancela logicamente a fila não iniciada
  e permanece pendente enquanto houver tentativa já admitida. O dispatcher
  marca as entradas canceladas quando as encontra; interrupção ou resultado
  incerto exigem verificação, sem presumir conclusão.
- Prévia cuja tentativa terminou durante a pendência pode ser consultada após a
  retirada, inclusive após nova concessão, mediante validação de identidade,
  hash e demais fontes. Decisão/publicação depois da retirada segue bloqueada.
- Interface informa os estados e atualiza enquanto pendente. Controle integrado
  ao modo fake; envio real à OpenAI e reconciliação automática seguem pendentes.
- CI backend passou com 1.215 testes e 100% de linhas/ramos. Cinco testes
  direcionados de interface e typecheck passaram; migração aditiva `0048` aplicada
  ao banco local, com health e OpenAPI respondendo 200 em nova instância.

## 2026-10-27 — BL04.2: referências e percurso visual simulado

- Preparação do pedido usa fontes validadas, foto WhatsApp e referências do
  acervo, com hash e remoção de metadados, além de paleta, composição e textos
  confirmados. Fontes/nome/logo do kit ainda não são aplicados à peça.
- Jornada fake de desenvolvimento/teste exercita reserva e fence, prévia privada,
  entrega e decisão; imagem e interface indicam simulação. Nenhum provedor real
  foi chamado. A validação de fontes em transação separada impede afirmar que a
  geração real está pronta. Revisão automática rejeitou a migração candidata de
  permissões; proposta e pendências constam no SDD da fase.
- Validação: `make ci` passou com 1.199 testes e 100% de linhas/ramos. No
  frontend, 13 testes e 100% de cobertura focada da tela Conteúdos, typecheck e
  build passaram. Migrações `0046` e `0047` aplicadas ao banco de desenvolvimento
  local; health e OpenAPI retornaram 200 em nova instância da API.

## 2026-10-27 — Avaliação de ferramentas de vídeo, voz e desenvolvimento

- Registrada análise preliminar de HyperFrames, Remotion, VoiceStudio e
  Superpowers, com condições de licença, distinção entre geração e edição e POC
  futura para vídeo. Nenhuma ferramenta foi instalada ou incluída no runtime.

## 2026-10-27 — BL04.2: início dos controles de geração visual

- Consentimento visual independente por negócio, auditado e revogável, com
  interface em Sobre meu negócio; geração real continua em preparação e desligada.
- Ledger oferece reserva na transação do chamador. A integração com intenção
  de envio, fence e provedor ainda precisa ser implementada e validada.
- Captura pontual interna valida owner, consentimento, briefing e kit e calcula
  impressão digital do contexto; ainda não persiste tentativa nem envia mídia.
- Prévias locais usam chave por tentativa para evitar que um worker vencido
  remova o arquivo de uma execução mais nova.
- Nenhuma chamada visual paga foi feita nesta entrega; não há resultado novo ou
  conclusão sobre qualidade e custo por peça aceita.
- Validação: `make ci` do backend passou com 1.147 testes e 100% de linhas e
  ramos. No frontend, 303 testes e cobertura de 100% passaram em execução
  sequencial, após instabilidade em execuções anteriores; typecheck, build e
  jornada Chromium em desktop/celular também passaram. Migração `0045` aplicada
  ao banco local de desenvolvimento; health e OpenAPI responderam 200 em uma
  nova instância da API.

## 2026-10-27 — BL04.1: comparação e recuperação de orçamento

- Jev reconhece pedidos explícitos de divulgação nos critérios sem promover preços e horários isolados a publicações. Teste real do adapter reconheceu o caso anterior; a [comparação Jev/OpenAI](evals/intent-comparison-2026-10-27.md) documenta outros erros e seis respostas OpenAI incompletas no recorte comparável.
- Orçamento recusado antes da submissão gera `budget_blocked`; retomada serializada exige ausência de tentativa no ledger, revalida origem/acesso e usa espera Temporal limitada. Resultado incerto continua sem reenvio; desabilitar o interpretador não faz fallback legado para eventos que já exigem briefing. Migração aditiva 0044.
- Avaliação real apenas com fixtures sintéticas; teto autorizado US$ 1, custo superior conservador estimado US$ 0,0172870085, incluindo uma reserva de chamada incerta. Não é fatura nem custo mensal. O runner é offline por padrão e não repete casos já submetidos entre journals.
- Validação: `make ci` passou com 1.113 testes e 100% de linhas/ramos no backend, incluindo PostgreSQL `_test` e Temporal; Ruff e mypy aprovados. Downgrade e reaplicação da 0044 testados no `_test`. Migração 0044 aplicada ao banco local de desenvolvimento e nova instância respondeu 200 em readiness e OpenAPI; reiniciar a API de debug para carregar o novo head. Sem homologação comercial, Meta ou teste de conversa com memória.

## 2026-10-27 — Proposta de vídeo real e voz opcional

- Registrado [plano de vídeo real e voz](design/video-real-and-voice.md): roteiro sob pedido ou proativo, gravação guiada de mãos, produtos e espaço, original, edição leve ou motion, preview e aprovação por peça.
- Clonagem de voz permanece F05 após piloto; pesquisa técnica autorizada separadamente, avaliando modelo, pesos, licença, consentimento, qualidade e custo. O projeto citado pelo sócio não foi identificado. Vídeo, quantidade e preço ainda não compõem automaticamente o plano inicial.

## 2026-10-27 — BL04.1: candidato Jev no worker local

- Interpretador Jev opcional e pinado, com autorização específica TypeSafe por negócio, reserva diária por tenant, identificador idempotente e tratamento conservador de resultado incerto; sem chamada paga nos testes.
- Ambiguidade registra esclarecimento pelo adaptador simulado. A autorização e as fontes são revalidadas; desabilitar o provedor não substitui consentimento TypeSafe por consentimento OpenAI.
- Roteiro pode usar o nome de item ativo e versionado do acervo como fonte, sem cadastrar fato artificial nem inferir preço; edição exige revalidar a versão da fonte e rejeita alegações comerciais não confirmadas.
- Decisão de produto: oferta inicial de R$ 99 com foto e story; vídeo e limites de quantidade serão definidos depois. Regra estática vale apenas para a primeira oferta e deverá ser substituída por permissões persistidas para novos planos.
- Ensaios Jev autorizados: 29/30 intenções e 6/7 cenários do adapter corresponderam ao gabarito; houve erro em negação e um pedido implícito de divulgação exigiu esclarecimento. Custo estimado total US$ 0,000793884 e reserva conservadora total US$ 0,099456, dentro de US$ 0,10, sem cobrança incerta. As amostras não aprovam produção.
- Migração 0043 aditiva aplicada no banco de testes e no banco de desenvolvimento local; uma instância nova respondeu 200 em readiness e OpenAPI. Reiniciar a sessão de debug após a migração. Produção e staging continuam bloqueados. Faltam eval PT-BR conclusivo, franquias, conversa, geração visual e demais gates descritos na spec BL04.
- Validação local: 843 testes unitários, 124 testes direcionados, integração do roteiro com edição e invalidação, 299 testes da web e build passaram. A execução de `make ci` foi interrompida durante os testes de integração; não há resultado consolidado de cobertura do backend para esta entrega.

## 2026-10-27 — Cenários de QA e avaliação inicial do OpenCode

- Registrados três cenários fictícios e um guia manual com passos disponíveis,
  limitações atuais, testes planejados e pontos de observação. Nenhum negócio,
  imagem, pagamento, publicação ou registro de cliente foi criado nesta mudança.
- OpenCode avaliado pela documentação oficial como candidato para QA e análise;
  sem instalação, integração, decisão comercial ou substituição dos traces do produto.


## 2026-10-27 — BL04.1: integração experimental do briefing

- Material WhatsApp e áudio transcrito podem alimentar resolução privada do
  acervo com intérprete injetado em desenvolvimento/teste; intenção persistida,
  idempotência, autorização, estado incerto e snapshot revalidado. Texto bruto
  não entra no histórico do Temporal; alterações na origem são detectadas.
- Proposta recebe projeção mínima do acervo e expõe resumo owner-only na web.
  Prévia é bloqueada para briefing experimental até revalidação de ponta a ponta;
  remoção de briefing não permite fallback à proposta legada. Negação explícita
  pede esclarecimento, que ainda não é entregue ao cliente.
- Adapter estruturado OpenAI de interpretação testado com mocks, sem integração
  de provider pago. Jev continua candidato em avaliação. Worker normal mantém
  comportamento anterior; não há IA semântica real habilitada nesta entrega.
- A migração 0042 é aditiva; avaliação de acesso, contexto, consentimento,
  orçamento, reconciliação e testes devem preceder habilitação de provider real.
- Validação final: backend `make ci` com 996 testes, Ruff e mypy aprovados
  e 100% de linhas/ramos; web 296 testes com 100% nos quatro critérios,
  typecheck/build e Chromium desktop/móvel. Migrações aditivas 0041/0042
  aplicadas no banco local após validação no `_test`. Uma instância recém-carregada
  respondeu 200 em `/health/ready` e OpenAPI; o processo de debug anterior deve
  ser reiniciado para atualizar o head em cache. Nenhuma chamada paga neste passo.


## 2026-10-27 — Primeiro ensaio Jev com dados fictícios

- Conta e chave configuradas localmente; cinco chamadas de `jev-1.14.0` em
  mensagens sintéticas de desenvolvimento, sem dados de clientes. O modelo
  acertou 5/5; baseline acertou 2 e se absteve em 3. Mediana 179,676 ms;
  2.357 tokens de entrada e custo estimado US$ 0,000098994 no total.
- Amostra pequena e não cega, insuficiente para adoção ou aferir precisão real;
  comparação ampla, novo holdout e integração continuam pendentes. Registro em
  [eval Jev](evals/jev-intent-ptbr-v1.md). Não foram alterados código ou banco.

## 2026-10-27 — Início BL04: bases isoladas, avaliação e ensaio sintético

- Busca owner-scoped de candidatos no acervo, snapshot mínimo e revalidação de
  versões, preço, promoções e fotos; orquestrador interno interpreta fora das
  transações e rejeita seleção inválida. Não há consumidor no fluxo editorial,
  nem resolução automática por modelo real ou persistência de snapshot.
- Adapter de imagem OpenAI isolado, sem retries e com resultado incerto após
  submissão; ledger `0041` reserva limite técnico em micros de USD por tenant,
  com idempotência, lock, RLS e retenção de reservas incertas. Ainda não estão
  integrados a prévias, consentimento visual, Temporal ou plano comercial;
  limite padrão é zero e não habilita chamadas reais de clientes.
- Cópia criativa opcional em desenvolvimento/teste, ligada a um fato e protegida
  pelas verificações existentes; validação lexical não garante veracidade.
  Classificador conservador solicita esclarecimento para negações explícitas.
- Avaliação Jev preparada com 50 casos PT-BR sintéticos e chave opcional
  `TYPESAFE_API_KEY`; nenhuma chamada real ou adoção. O holdout foi contaminado
  durante correção do baseline e será substituído antes de avaliação cega.
- Uma chamada de imagem real com marca fictícia e foto CC0, autorizada até US$ 1,
  estimada em US$ 0,024627, documentada no [eval](evals/bl04-visual-synthetic-story-2026-10-27.md).
  O resultado não garante fidelidade do logo/texto nem qualidade comercial.
- A [spec BL04](phases/BL04-context-and-ai-production.md) e o [desenho de
  integração](design/BL04-integration-safety.md) distinguem as unidades prontas
  da etapa durável de ponta a ponta ainda pendente.
- Validação final: `make ci` com cache isolado do mypy, Ruff e mypy aprovados,
  **930 testes aprovados e 100% de cobertura de linhas/ramos**. A migração 0041
  foi aplicada apenas na base dedicada `_test`; a base de desenvolvimento não
  foi alterada. Houve uma única chamada real de imagem no ensaio sintético.


## 2026-10-27 — Correção local da consulta ao acervo

- A consulta do catálogo falhava com 500 porque o banco de desenvolvimento
  ainda estava na migração `0037_brand_kits`. Após pausar a cobrança, aplicadas
  as migrações `0038`–`0040` previamente aprovadas; `0038` preserva os eventos
  na auditoria financeira antes de retirar a outbox sem consumidor.
- Cobrança reconstruída e reiniciada. Confirmados head `0040`, existência das
  tabelas, API `/health/ready` e leitura do catálogo do negócio informado pelo
  serviço com a role restrita e RLS, sem expor seu conteúdo. A resposta HTTP
  autenticada deve ser verificada novamente na sessão do cliente.

## 2026-10-27 — BL03.1/BL03.2: acervo opcional do negócio

- Produtos, serviços, promoções com validade e fotos privadas dos itens ou do
  espaço em Sobre meu negócio; opcional, progressivo e independente do plano.
  Fichas distinguem rascunho, confirmação e arquivamento. Histórico de versões
  é exposto pela API; interface concentra cadastro/revisão, sem tela de histórico.
- API owner-only com RLS/FKs por tenant/negócio, snapshots imutáveis, CAS,
  idempotência, auditoria transacional e migrações novas 0039/0040. Upload
  PNG/JPEG/WebP até 2 MiB com direitos; miniaturas e URLs privadas temporárias.
  Promoção autorizada de foto WhatsApp copia o objeto para acervo independente.
- Intents/leases, fencing e reconciliação protegem upload e remoção: repetição
  em andamento preserva operação, erros/cancelamento ambíguos aguardam o escritor
  e efeitos tardios são compensados. Remoções pendentes podem ser retomadas por
  owner; varredura global automática permanece F08.
- Proprietário aprovou manual/fotos agora e solicitou importação automática de
  imagens de cardápio/tabela de serviços depois. BL03.3 especifica extração e
  preenchimento de rascunhos com fontes e revisão de ambiguidades; ainda não há
  OCR, retrieval para geração, JEV, Motion ou geração visual integrada.
- [Roadmap até produção e evolução](design/delivery-roadmap-2026-10-27.md)
  registra recomendação de formato, concorrência, custos, Meta, AWS e piloto.
- Validação: `make ci` com **806 testes**, Ruff, mypy e **100% de linhas/ramos**;
  web com **293 testes e 100%** nos quatro critérios, build/typecheck/Prettier e
  jornada desktop/celular com APIs e imagens fictícias. Migrações testadas apenas
  no banco `_test`; desenvolvimento permanece em 0037 e precisa atualizar até
  0040. `.env` local ganhou somente configurações ausentes do object storage;
  bucket local validado com upload/leitura/URL temporária/exclusão de objeto
  sintético. Sem uso de dados reais ou chamadas pagas.

## 2026-10-27 — Auditoria e simplificação aprovadas P1–P15

- Jornada web centrada em **Início**, **WhatsApp** e **Conteúdos**; histórico de
  envios secundário, telefone como etapa do canal e IA autorizada em Sobre meu
  negócio. Organização/negócio ativos compartilhados, sem seletores repetidos.
  Campo semanal retirado preservando o valor histórico. Guia estático removido
  com redirect; editor de ideia/roteiro/render somente no laboratório DEV.
- APIs/tabelas de materiais, propostas, roteiros, versões, decisões, retenção e
  consentimento permanecem: a jornada automática usa esses contratos.
- P9 remove gravação na outbox financeira sem consumidor. Migração nova
  `0038_retire_billing_outbox` copia eventos faltantes para `billing_audit`,
  aborta em conflito de tenant e permite downgrade com RLS/permissões. Jobs,
  Stripe e reconciliação preservados. Aplicada somente à base `_test` nesta
  revisão; atualizar executáveis junto da migração no ambiente de uso.
- Removidos helper `actor_for_subject`, stub `seed_development.py` e declaração
  sem serviço do volume Keycloak. Contas/IDs/MFA e volumes reais preservados.
- P14 retira novos eventos-recibo de criação de negócio/alteração de kit;
  auditoria e idempotência continuam atômicas. Relay sai do startup normal e
  debug, mantendo profile manual, tabelas e handlers para históricos.
- PROJECT/SDD/README consolidados; snapshots integrais com SHA-256 em
  `docs/history/2026-10-27-pre-consolidation`. Avatar/voz do cliente ficam após
  o primeiro piloto comercial (P15), sem eliminar a F05 do produto.
- [Auditoria de produto e IA](audits/product-flow-and-ai-2026-10-27.md) registra
  decisões, evidências, capacidades faltantes e comparação proposta entre
  OpenAI/Claude/chamada direta/harness. Nenhuma troca de modelo ou chamada paga.
  BL03 continua próxima; acervo e IA visual não foram implementados nesta limpeza.
- Validação final: `make ci` passou (Ruff, formatação, mypy e **722 testes**,
  **100% de linhas/ramos**). Web: **257 testes**, **100% nos quatro critérios**,
  build/typecheck, Prettier e quatro jornadas Chromium aprovadas. Migração
  validada com preservação/rollback/RLS em `_test`; base do usuário intocada.

## 2026-10-27 — BL02 API de kit aplicado e snapshot F03

- Catálogo derivado do manifesto `cafe-pausas/v1`, com fotos limpas de origem
  para o editor e gate `public_demo`: seleção local/teste; produção somente
  após status aprovado. API owner-only salva rascunhos, confirma, mostra
  histórico e valida cores, fontes, textos e composição por formato.
- Versões imutáveis usam CAS (`expected_version`), replay exato por
  `operation_id`, RLS por tenant, audit e outbox `brand_kit.changed` entregue
  a workflow/activity idempotente. F03 copia versão e documento confirmado na
  criação da proposta, sem trocar estilo em execução tardia.
- Logo privado com autorização de uso, validação PNG/JPEG/WebP, dimensões,
  limite de corpo HTTP antes de parse, normalização sem EXIF e URL temporária.
  Intent e lease protegem upload concorrente; reconciliação de pendência é
  owner-scoped. Varredura global fica para F08 após desenho de permissão.
- Backend integrado ao editor web BL02. Uma peça visual nova que use o
  kit, revisão de qualidade comercial e homologação da Meta pertencem às
  próximas fases. Migração `0037_brand_kits` aplicada no banco local; relay e
  worker reconstruídos para reconhecer o novo evento. A imagem Docker inclui
  somente o manifesto do kit, com leitura do catálogo verificada sem rede.
- Validação final: `make ci` passou (Ruff, formatação, mypy e **718 testes**, com
  **100% de cobertura de linhas e ramos**); web com 220 testes e 100% de
  cobertura, build e duas jornadas Chromium desktop/mobile aprovadas.

## 2026-10-27 — Roadmap BL reorganizado em torno do primeiro conteúdo personalizado

- A ordem vigente agora é BL01 vitrine piloto local, BL02 escolha e edição
  guiada do kit por negócio e formato, BL03 acervo privado progressivo em
  “Sobre meu negócio”, BL04 recuperação automática e nova peça com gate de
  qualidade/custo, BL05 jornada WhatsApp local/proativa e BL06 expansão de
  nichos e catálogo em objetos/CDN.
- A renumeração substitui BL02 (prova de reaplicação), BL03 (expansão),
  BL04 (escolha) e BL04.5 (acervo) usados nos registros anteriores; esses
  registros permanecem históricos. Escolha/edição, acervo e IA visual no
  pipeline continuam **planejados**, enquanto o kit/vitrine BL01 já existe
  localmente.
- Decisões de produto confirmadas: o acervo fica em seções de “Sobre meu
  negócio” e é opcional/progressivo; o editor de kits permite alterar também
  a composição de feed, story e capa vertical por controles guiados com
  prévias. Áudio/texto livre continuará sem exigir escolha manual de item.
- Validação desta mudança documental: revisão de referências, estados e
  `git diff --check`; testes de código não foram necessários.

## 2026-10-27 — Peças finais no kit e catálogo do negócio

- O kit fictício de cafeteria ganhou três JPEGs 4:5 com texto/CTA no próprio
  arquivo: editorial de produto, oferta ilustrativa e destaque de cardápio.
  Manifesto e validador rastreiam fotos de origem, receitas, hashes e os três
  formatos. O fluxo de promoção mostra entrada e arquivo final distintos.
- BL04.5 especifica produtos/serviços, preço/validade, promoções e fotos do
  item/ambiente com armazenamento privado, revisão do dono e recuperação
  automática e seletiva após texto/áudio livre, sem escolha manual de item no
  pedido. BL03 diferencia biblioteca pública em objeto/CDN do
  bootstrap local atual; não há API de catálogo nem cadastro estruturado ainda.
- Validação: 16 testes do catálogo passaram; lint/tipos e 642 testes da suíte
  completa passaram com 100% de cobertura. Um teste Temporal falhou enquanto
  o serviço local iniciava e passou isoladamente após ficar disponível.
  Avaliação visual por comerciantes e publicação do catálogo em produção
  permanecem pendentes.

## 2026-10-26 — Entradas do kit e fidelidade do negócio

- O manifesto do piloto descreve seis cenários WhatsApp e a origem da mídia de
  cada um. O validador rejeita referências ausentes e evita que demos de foto
  do produto/local troquem a imagem de entrada por outro cenário.
- SDD/BL01–BL02 separam imagem fictícia de vitrine e material real do cliente:
  um local físico não pode parecer outro; prato, porção e embalagem de delivery
  precisam ser fiéis. Texto sem foto usa arte conceitual ou pede material.
- Validação local: `make ci` com 639 testes e 100% de cobertura no app;
  qualidade visual comercial, ensaio consentido e pipeline de edição real
  seguem pendentes.

## 2026-10-26 — BL01 técnica e ensaio inicial BL02

- Catálogo `cafe-pausas/v1` com dez posts fotográficos distintos, dois stories,
  reel silencioso de 8,96 s, receitas editáveis, fontes com licença, hashes e
  proveniência. Validador/exportador bloqueia mídia alterada, direitos incompletos
  e referências quebradas; a vitrine web usa o pacote estático.
- BL02 compara foto CC0 de um segundo negócio fictício em quatro rotas. Três
  chamadas Flare/medium custaram US$ 0,074311 juntas; a referência extra
  aumentou custo neste caso. Texto/preço/CTA exatos foram compostos localmente
  para todas as rotas. [Resultado e limites](evals/brand-kit-transfer-v1.md).
- A vitrine pública `/kits` entra antes do cadastro; acesso real a recursos pagos
  seguirá autorização de API por plano em BL04/BL05, sem travar checkout.
- Validação: validador do catálogo, testes unitários e FFprobe do MP4; `make ci`
  e testes/browser web registrados no changelog da web. Revisão de titular
  consentido, custos operacionais e qualidade comercial ainda pendentes.

## 2026-10-26 — Kits por nicho e cadência vinculada ao plano

- BL03 passa a prever cafeteria, manicure com agenda e personal trainer, cada
  um com peças e gate de qualidade próprios. BL04 detalha edição opcional de
  cor/fonte/logo com três prévias por receita e versão aplicada ao negócio.
- Novo [SDD de planejamento](design/editorial-planning-and-evidence.md): plano
  limita peças por formato/canal, F03 sugere ritmo explicável dentro da franquia,
  cliente aceita/reduz/pausa e upgrade exige preço aceito. Preços/volumes
  dependem da medição BL02, não de uma quantidade presumida.
- Biblioteca publicável própria fica separada de padrões observados em
  concorrentes e resultados agregados autorizados dos clientes. Pesquisa
  automática depende de APIs/permissões reais; TikTok Research API não atende
  uso comercial. Estado: especificação; sem backend de recomendação novo.
- Validação: `git diff --check`; não houve mudança de código backend.

## 2026-10-26 — UI da vitrine antecipada para BL01

- A navegação visual dos kits começa em paralelo à produção do primeiro kit:
  `/app/kits` na web simula Instagram, Facebook e TikTok com mídia fictícia
  estática, pautas e exemplos de WhatsApp/cadência. A tela marca capa de vídeo
  e demais peças como protótipo; não escolhe kit, publica ou consulta rede.
- BL03 passa a completar a vitrine com catálogo e mídias finais de três kits,
  após a prova de reaplicação BL02. Backend ainda não ganhou API ou catálogo.
- Validação: revisão documental e `git diff --check`; testes web no changelog
  do repositório frontend.

## 2026-10-26 — Reordenação para a biblioteca de kits

- Nova [trilha BL01–BL05](phases/BL-brand-library.md): kit mestre com dez posts,
  story e reel + fontes editáveis; prova de reaplicação pelo pipeline real;
  vitrine interna de três kits; escolha versionada; jornada WhatsApp com kit.
- Limite corrigido para **zero ou uma imagem de referência do kit da mesma
  receita/formato** por geração, além da mídia original do cliente quando houver.
  Custo/qualidade são medidos por peça aceita antes de ampliar a vitrine.
- O índice das fases substitui a ordem anterior que melhorava o template
  universal antes de validar uma biblioteca reutilizável. Status: documentação
  e critérios definidos; nenhum kit, UI ou adapter novo entregue nesta mudança.
  Validação: `git diff --check`.

## 2026-10-26 — Kit selecionado como referência da geração

- A receita editável e um manifesto compacto do kit escolhido passam a orientar
  o briefing de produção real. Exemplos visuais são selecionados por formato,
  sem enviar os dez posts da vitrine a toda chamada nem copiar sua marca fictícia.
- Definido eval controlado: sem kit, kit compacto, kit + referência visual e
  composição local, com qualidade, tentativas/tokens e custo por peça aceita.
  Menos erros e custo menor são hipóteses, não resultados comprovados.
- Estado: especificação; nenhuma nova integração ou geração executada.
  Validação: `git diff --check`.

## 2026-10-26 — Correção: showroom reutiliza kits prontos

- Corrigida a hipótese anterior de gerar dez pautas/posts com dados de cada
  visitante. A biblioteca guarda campanhas demonstrativas criadas e revisadas
  uma vez por versão/segmento, com marca fictícia e arquivos estáticos completos.
- Instagram/Facebook/TikTok são **simuladores internos da nossa web**; nenhuma
  conta pessoal é aberta ou lida nessa etapa. Abrir/comparar kits não chama IA;
  custo de criação do catálogo é amortizado. Dados do negócio entram somente na
  personalização/produção posteriores, com gate e custo próprios.
- Estado: somente especificação. Validação: `git diff --check`.

## 2026-10-26 — Showroom do futuro perfil na escolha do kit

- Histórico da hipótese inicial, substituída pela correção acima: foi proposto
  montar pautas e miniaturas por visitante. A experiência de comparação de
  formatos permanece, mas os exemplos agora são ativos reutilizáveis.

## 2026-10-26 — Biblioteca de identidade visual proposta

- Novo [contrato de produto](design/brand-library.md): kit de marca sugerido,
  três direções com prévias comparáveis e escolha/edição/aceite do cliente.
  Separação entre kit do negócio, direção visual e receita de publicação.
- F03/F04/F06 passam a prever kit e receitas versionados, com aprovação da peça
  separada. A escolha de renderer será medida por qualidade, fidelidade e custo
  por peça aceita; composição local com foto real concorre com edição por IA.
- Estado: **somente especificação**. Nenhuma UI, tabela, integração ou peça
  comercial foi criada nesta mudança. Validação: `git diff --check`.

## 2026-10-26 — Eval de contexto completo para uma geração visual

- Fixture sintético de cafeteria com dados atuais de onboarding/editoria e
  campos futuros de marca, catálogo, concorrência, histórico, direitos e orçamento;
  foto CC0 e logo fictício acompanham o caso. Inventário dos campos da web e
  contrato de ferramentas de leitura em
  [eval visual](evals/visual-context-eval-v1.md).
- Runner offline valida fatos/mídia e cria briefing/planilha de revisão; modo
  `--live` limita a uma chamada por execução e mede tokens/custo. Nove testes
  verificam fatos vencidos, arte pronta, ausência de foto, isolamento por tenant,
  instrução externa, consentimento, orçamento e cálculo. Nenhum cliente ou
  banco foi alterado.
- Primeira peça Flare/high custou US$ 0,060232; aparência melhor, texto literal
  e fidelidade comercial reprovados. Scripts/eval são laboratório, não integração
  de geração ao serviço de prévias.
- Comparação exploratória com a mesma entrada: Flare/medium US$ 0,026272
  (13,33 s) e Sunburst/high US$ 0,060232 (32,57 s). Medium pareceu próximo em
  aparência nesta amostra, mas as três peças tiveram problema de texto literal
  e não foram aprovadas para uso comercial.

## 2026-10-26 — Medição direta de uma edição visual e impacto técnico

- Após recarga da API, uma edição de foto CC0 com `gpt-image-2.5-flare`
  retornou imagem em 19,56 s; 1.080 tokens de imagem de entrada, 189 de texto e
  1.510 de imagem de saída correspondem a US$ 0,054885 nas tarifas Standard.
  Arquivo e metadados ficam privados em `.local/evals/`.
- [Ensaio](evals/ai-visual-spike-2026-10-26.md), PROJECT, F04 e
  [plano criativo](design/creative-production-quality.md) agora distinguem custo
  de uma chamada, custo por peça aceita e custo mensal. O plano registra quais
  contratos atuais são reaproveitados e onde a camada criativa precisa mudar.
  Código de produção não foi alterado nesta medição.

## 2026-10-26 — Promessa de constância e iniciativa do produto

- Produto definido pela entrega de conteúdo relevante que busque contatos e
  clientes, com ou sem pedido diário do comerciante. Cliente não opera IA,
  prompts, roteiro ou editor; prévia e aprovação continuam simples no WhatsApp.
- Proatividade mínima de F03 movida para antes do piloto: cadência, pausa,
  biblioteca/fatos vigentes, ausência de novo input, pergunta quando faltar
  contexto e aprovação explícita. Pesquisa extensa de concorrentes permanece
  posterior. Roadmap e plano criativo alinhados; nenhuma automação proativa nova
  foi implementada por esta atualização documental.

## 2026-10-26 — Geração visual por IA como percurso principal

- SDD geral, F04 e plano criativo esclarecem a decisão: contexto, marca, material
  e pedido do cliente viram briefing para modelo visual gerar/editar a peça
  completa. Preservação de arte pronta e acabamento exato continuam disponíveis.
- Estado honesto: integração de IA de imagem/vídeo no produto ainda não existe;
  o ensaio externo não a implementou. Próxima fatia F04.1b integra adapter,
  orçamento, prévia e avaliação; F04.2b/F05 tratam vídeo/avatar com gates próprios.
  Nenhum código de produção foi alterado por esta decisão documental.

## 2026-10-26 — Ensaio visual com IA e custo de referência

- Foto de croissant CC0 gerou conceito de fotografia e post com IA, guardados
  somente em `.local/evals/ai-visual-2026-10-26/`, ao lado do template v4.
  [Registro](evals/ai-visual-spike-2026-10-26.md) separa melhora percebida,
  risco de alterar produto/cenário e custo de referência de medição real.
- Uma chamada à OpenAI Images API com a chave local recebeu 429
  `credit_balance_exhausted`; não houve saída nem `usage`. A ferramenta de
  imagem integrada não informou modelo/custo. Nenhum preço real por peça foi
  inferido. Documentação apenas; código de produção e testes não mudaram.

## 2026-10-26 — Plano de qualidade criativa

- Diagnóstico no código: IA atual propõe texto/roteiro; Pillow e FFmpeg produzem
  layouts e cenas fixas, com falhas observadas de duplicação e destaque do
  produto. Nenhuma peça atual está aprovada para publicação comercial.
- [Plano de produção](design/creative-production-quality.md) define rotas para
  feed, story, carrossel, reel real, motion, geração visual e avatar; gate de
  material autorizado, direção/kit de marca, avaliação em celular e custo por
  peça aceita. F03/F04 passam a comparar edição de imagem por IA com a base
  local antes da expansão; F05 continua opcional com orçamento/consentimento
  próprios. Alteração documental; nenhuma integração visual paga foi chamada.

## 2026-10-26 — Ensaio de editores locais e teto unitário

- [Benchmark privado](evals/open-source-editors-2026-10-26.md): PhotoCraft CLI
  v0.16.0 editou foto/arte; FilmCraft CLI v0.13.0 exportou MP4 H.264 de oito
  segundos. Comparação local com a receita atual está em `.local/evals/`, fora
  do Git. A falha de preenchimento RGBA no PhotoCraft exigiu inspeção visual e
  correção. Nenhuma IA visual, publicação, autorização da proprietária ou custo
  AWS foi testado.
- SDD/PROJECT/F04 registram motores como candidatos opcionais, a necessidade
  de classificar arte pronta e o limite de desenho de R$ 50 de custo mensal
  total por cliente no plano de R$ 99. Franquia e viabilidade comercial dependem
  de medir custo por peça aceita, revisão consentida e staging.

## 2026-10-26 — Candidata automática e aprovação simulada

- Workflow Temporal do material pede roteiro e prévia privada sem marcar o
  roteiro como aceito; sem fato confirmado, registra pedido de esclarecimento.
- Entrega simulada, decisão idempotente e publicação falsa vinculam proprietário,
  candidata, hash, legenda, destino e horário. Sem aceite, nada é publicado;
  contexto alterado e prazo vencido bloqueiam a ação. Resultado incerto do
  dispatcher é retido para revisão, sem segunda publicação automática.
- Cenários adicionais de cafeteria continuam sintéticos. A amostra pública do
  [perfil indicado](evals/priscila-public-reference-2026-10-26.md) foi examinada
  para orientar linguagem e avaliação visual, sem versionar nem modificar mídias
  alheias e sem tratar dados públicos como fatos confirmados do negócio.
  Avaliação humana com autorização e custo staging ainda não ocorreram. Meta
  real, resposta a ambiguidade e ajuste automático pendentes.
- Validação: migrações 0035/0036 em banco `_test`, integração de aprovação/RLS e
  workflow simulado; 618 testes backend com 100% de linhas/ramos, Ruff e mypy
  aprovados. O corpus editorial local passou 12 verificações de segurança, com
  quatro casos que corretamente pedem confirmação; nove artes sintéticas foram
  renderizadas sem chamadas pagas. Cinco vídeos sintéticos também foram
  renderizados com FFmpeg no contêiner, todos aguardando revisão humana. Um
  ensaio privado com duas mídias públicas
  da cafeteria identificou texto duplicado em arte já pronta e pouco destaque
  do produto em frame bruto; [registro visual](evals/priscila-public-reference-2026-10-26.md).

## 2026-10-26 — Sequência orientada por qualidade

- SDD geral, contexto vivo e roadmap alinhados: avaliação factual, criativa,
  visual e de custo por receita precede sua automação/publicação comercial.
  F04.3/F06 continuam testáveis localmente com Meta simulada; a homologação
  externa permanece obrigatória antes de clientes reais.
- O plano da v0 passa a colocar candidata pelo WhatsApp e aprovação/publicação
  simulada antes de avatar e expansão de formatos. Escopo final da v0 preservado.
  Mudança documental; nenhum gate comercial foi aprovado por esta revisão.

## 2026-10-26 — F04.2b: enquadramento integral e avaliação repetível do vídeo

- Vídeo v4 preserva o clipe inteiro em retrato ou paisagem, com fundo desfocado.
  `render_key` versionado mantém prévias v3 imutáveis. Smoke FFmpeg com vídeo
  horizontal sintético confirmou bordas vermelha/azul, H.264 1080×1920 e 7,96 s.
  Em clipe vertical, as faixas superior e inferior da fonte permanecem visíveis
  fora dos painéis de título e CTA.
- Quatro cenários sintéticos PT-BR geram MP4s, folha de contato, hashes e
  medidas de render. Nesta execução local, tempo de parede foi 3,7–10,3 s,
  CPU acumulada 16,9–33,2 s e saída 63–79 KiB. São arquivos simples e custos
  locais; não extrapolar para mídia real, carga concorrente ou custo AWS.
- Avaliador de revisão consentida exige 20 peças, quatro segmentos, cinco fotos
  e cinco clipes, revisão em celular, ≥90% de legibilidade/visibilidade/cortes,
  ≥80% de aceite sem ajuste e zero falha crítica. Nenhum material real foi
  avaliado; gate comercial permanece fechado. Seleção semântica de trechos e
  medição p50/p95/COGS em staging ainda faltam.
- Validação: testes do renderizador e avaliador, benchmark real no worker e
  `make ci` com 589 testes, Ruff/mypy e 100% de linhas e ramos.

## 2026-10-26 — F04.2b: abertura, CTA e dois cortes na prévia de vídeo

- Template de vídeo v3 usa textos do roteiro aceito para abertura e CTA, preserva
  o fato confirmado literalmente e mostra a foto real inteira sobre fundo
  desfocado. Clipes autorizados de pelo menos 4,5 segundos fornecem um trecho
  inicial e um segundo trecho para o CTA; clipes curtos usam CTA de marca.
- Saída permanece privada, vertical, H.264, oito segundos e sem áudio. O hash
  versionado mantém as prévias anteriores imutáveis e exige novo render para a
  receita v3. Não há envio/publicação nesta entrega.
- O proprietário pode revisar o ritmo em até quatro versões privadas: equilíbrio
  2/4/2 s, mais cena 3/3/2 s, mais leitura 1/5/2 s. A API exige última versão,
  mesmo formato, roteiro/contexto vigente, operação idempotente e fonte válida;
  falha pode repetir o mesmo ritmo. A web acompanha e reproduz cada versão.
- Gates pendentes: avaliação com comerciantes consentidos e em celular, custo em
  staging, edição avançada de clipes e eventual fala/legenda alinhadas ao arquivo real.
- Validação: `make ci` com 580 testes e 100% de linhas/ramos; smoke FFmpeg no
  worker com clipe sintético de três cores confirmou cortes distintos no início
  e no CTA, inclusive com ritmo de mais cena, H.264 vertical sem áudio e duração
  7,96 s. Prévia de foto sintética também renderizou. Nenhuma chamada paga ou
  conteúdo de cliente foi usado.

## 2026-10-26 — F04.1b: ajustes visuais e gate de revisão humana

- Foto/story podem gerar até quatro versões privadas ligadas à peça anterior, escolhendo equilíbrio, foto ou texto em destaque. Concorrência, replay idempotente e contexto/roteiro obsoleto são tratados no serviço; vídeo e mudança de fato não passam por esse fluxo.
- A avaliação de peças reais consentidas recebe CSV privado e calcula todos os gates de amostra, segmentos, formatos, legibilidade, aceitação e erro crítico, sem confundir o corpus sintético com homologação.
- A revisão com comerciantes e a medição real de COGS em staging ainda são gates externos antes do piloto. Validação: `make ci` com 571 testes, 100% de linhas e ramos; migração 0034 aplicada ao desenvolvimento após backup e ciclo downgrade/upgrade aprovado no banco `_test`.

## 2026-10-25 — F04.1b: primeira revisão da arte estática

- Template v4 preserva fotos inteiras, mostra fundo desfocado nas faixas vazias,
  aplica contraste conforme a cor da marca e mantém preço/fato em painel opaco.
  O hash da receita muda; arquivos antigos continuam imutáveis.
- Corpus sintético de oito cenários e `scripts/evaluate_static_art.py` geram folha
  de contato, medidas de bytes/latência e formulário de revisão humana local.
  Não houve uso de dados de clientes nem chamada a provedor pago.
- Revisão com comerciantes consentidos, ajuste visual versionado e custo real
  em staging continuam pendentes; esta entrega não libera piloto comercial.
- Validação: `make ci` com 545 testes e 100% de linhas/ramos, Ruff e mypy;
  oito imagens e folha de contato geradas localmente sem dados reais. Worker
  local reconstruído para usar o template v4 nas novas prévias.

## 2026-10-25 — F03.3b: edição versionada do roteiro

- A API grava histórico, hash, autor, contexto, fonte e revisão por versão; edição é idempotente e usa versão esperada. Testes concorrentes confirmam uma única versão vencedora e replay da mesma operação. Fato e proveniência não mudam silenciosamente; padrões explícitos de preço/promoção/garantia sem fato confirmado são recusados.
- Uma edição exige novo aceite. Prévia criada para versão anterior deixa de aparecer e não pode ser reaberta; renderizações em curso revalidam a versão.
- Migration 0033 adiciona histórico e versão de roteiro às prévias. Avaliação PT-BR com material consentido e comparação de modelos seguem pendentes antes de liberar clientes reais.
- O eval sintético v2 contém dez cenários e produz planilha para revisão humana; o modo live mantém limite explícito de chamadas. Execução baseline: 10/10 storyboards válidos estruturalmente, com 3 casos sem fato confirmado corretamente abstidos. Ainda não mede utilidade real.
- Validação: `make ci` com 539 testes, 100% de linhas e ramos, Ruff e mypy; migration 0033 revertida/reaplicada no `_test` e aplicada à base local após backup verificado. Worker local reconstruído. Nenhuma chamada à Meta/OpenAI foi necessária.

## 2026-10-25 — Ordem das próximas entregas após F04.2

- Corrigido o status do índice: já existe prévia privada de vídeo curto, mas edição direta e publicação continuam pendentes.
- Sequência explícita: F03.3b edição/versionamento e avaliação do roteiro; F04.1b qualidade visual da arte; F04.2b narrativa, edição e avaliação do vídeo; F04.3 geração e entrega da candidata pelo WhatsApp. Os gates criativos permanecem obrigatórios antes do piloto.
- Atualização documental; nenhuma capacidade de produto foi ativada. Validação: `git diff --check`.

## 2026-10-25 — F04.2: primeira prévia de vídeo curto

- Roteiro `short_video` aceito gera MP4 H.264 privado, vertical e silencioso de aproximadamente oito segundos, com três cenas e fato confirmado em texto. Usa foto autorizada, o trecho inicial de um clipe autorizado sem áudio, ou apenas a identidade da marca.
- O fluxo reutiliza pedido idempotente, worker Temporal, revalidação de fatos/materiais, link temporário e limpeza da F04.1. A migration 0032 registra tipo de mídia e duração; fonte de vídeo é limitada e inspecionada antes de renderizar.
- Artes e vídeos passam a usar uma fonte PT-BR incluída no worker, com licença preservada; a versão dos dois templates sobe para invalidar prévias antigas que poderiam exibir acentos como quadrados.
- Web reproduz o vídeo no card da ideia. Ainda faltam edição de trechos, fala/legenda alinhadas ao áudio, avaliação com negócios reais, envio pelo WhatsApp e publicação.
- Validação: `make ci` com 535 testes backend e 100% de linhas/ramos; 188 testes web com 100% dos quatro critérios. Render real de foto e clipe no Docker, com H.264 vertical sem áudio; migration 0032 revertida/reaplicada no `_test` e aplicada localmente após backup verificado. Worker local reconstruído.

## 2026-10-25 — Jornada WhatsApp e gates de qualidade especificados

- F04.3 passa a orquestrar geração e envio de prévia no WhatsApp sem exigir a web; F06 registra aprovação explícita da peça final, separada da confirmação de fato da F02. A web continua como alternativa.
- F03.3b detalha edição/versionamento de roteiro e avaliação PT-BR; F04.1b detalha avaliação visual com comerciantes consentidos, ajustes de template e bloqueio de erro factual antes do piloto.
- Alteração somente de SDD; nenhuma API, envio, renderização ou publicação nova foi ativada. Validação documental: referências entre fases e `git diff --check`.

## 2026-10-25 — F04.1: prévia estática privada

- Roteiro aceito gera arte JPEG de foto ou story com template de marca, foto real opcional, fato confirmado e CTA genérico. API do proprietário oferece pedido, estado e link temporário; a interface web mostra a prévia sem publicar.
- Migration 0031 cria registro isolado por tenant, chave de render estável e estados duráveis. Temporal faz claim, retry até três vezes e fencing; o worker verifica hash da foto e revalida entradas após upload. Falhas e mudanças de contexto não criam entrega final duplicada.
- Exclusão/expiração de roteiro ou foto oculta a prévia e agenda remoção do objeto, inclusive upload parcial; a linha só sai após o armazenamento confirmar. O roteiro local `baseline-v1` não exige consentimento para OpenAI.
- Validação: `make ci` aprovado com 501 testes, 100% de linhas e ramos, Ruff e mypy; migration 0031 revertida/reaplicada no banco `_test` e aplicada localmente após backup verificado. Worker e dispatcher locais reconstruídos. Integração externa Meta e avaliação visual com comerciantes continuam pendentes. F04.2 acrescentará vídeo e legenda.

## 2026-10-24 — F03.3: roteiro estruturado e revisão local

- Ideias passam a incluir até três cenas, fala, texto na tela e origem de cada fato/material; afirmações comerciais são montadas de fatos confirmados e vigentes, mesmo quando a ordem vem da IA.
- Proprietário pode aceitar ou pedir ajustes por API, com operação idempotente, bloqueio transacional, auditoria e isolamento por tenant. Aceite não publica.
- Migration 0030 registra decisão e comentário. Faltam edição direta, ciclo automático de revisão, leitura visual e benchmark PT-BR antes de uso comercial.
- Validação: `make ci` passou com 459 testes e 100% de linhas/ramos; inclui revisão concorrente, replay, isolamento e auditoria. Migration 0030 aplicada no `_test` e na base local após backup em `.local/backups/`; worker local atualizado com o código novo. Homologação Meta externa pendente.

## 2026-10-24 — Caminho de entrega consolidado

- Índice das fases atualizado para refletir F02.2c6 e o estado real de F03. Próxima
  entrega definida como F03.3: briefing e roteiro revisável a partir dos materiais,
  com avaliação factual antes de ativação comercial.
- F04 e F06 seguem em adapter fake até homologação externa Meta; avatar F05 é
  opcional para a primeira publicação. Nenhuma capacidade de produção foi ativada
  por esta atualização documental.
- F03.3 exige benchmark PT-BR de qualidade, latência e custo por roteiro aprovado
  antes de substituir o `gpt-5-mini` configurado, agora deprecated; baseline sem IA,
  Luna e Sol são candidatos, sem escolha automática de modelo.

## 2026-10-23 — F02.2c6: recibos e revisão dos envios WhatsApp

- Migration 0029 liga recibos `sent`, `failed`, `delivered` e `read` ao ID Meta sem confundir aceite HTTP com entrega; eventos repetidos ou fora de ordem não regridem estado.
- Decisão do proprietário prepara resposta curta na mesma transação. Pergunta e confirmação compartilham teto diário de tentativas por organização, com bloqueio transacional; resultados incertos não são reenviados.
- API e web administrativas exibem metadados de falhas/incertezas e permitem registrar análise/encerramento sem reenvio. Leitura e revisão exigem staff e auditoria; conteúdo e telefone permanecem fora da projeção.
- Validação local: `make ci` passou com 455 testes e 100% de linhas/ramos; testes cobrem recibos, limite, resposta final, RLS, revisão e auditoria idempotente. Migration 0029 revertida/reaplicada no `_test` e aplicada no banco local após backup em `.local/backups/`. Smoke Meta e custos monetários seguem pendentes; envio real permanece desligado.

## 2026-10-23 — F02.2c5: respostas WhatsApp e confirmação vinculada

- Migration 0028 cria fila durável com destinatário cifrado, prazo de 24 horas e ID Meta. Envio Cloud API fica desativado por padrão e requer chave, token e número configurados.
- Dispatcher revalida vínculo, consentimento, proprietário, telefone e plano; não reenvia tentativas de resultado incerto. `Confirmar`/`Descartar` usam o ID da pergunta ou, sem citação, uma única pergunta aceita nos últimos 30 minutos para o mesmo negócio/remetente. Ambiguidade não altera fatos.
- A aceitação da API ainda não prova entrega; recibos de status, reconciliação, resposta final no canal e smoke Meta seguem pendentes. Nenhuma mensagem real foi enviada.
- Validação: `make ci` com 452 testes, Ruff, mypy e 100% de linhas/ramos. Migration 0028 aplicada no banco local após backup, revertida/reaplicada no `_test`; worker e dispatcher locais reconstruídos com envio desativado.

## 2026-10-23 — F02.2c4: inbox vinculada → decisão editorial

- Migration 0027 dá ao papel restrito do worker a inserção idempotente de decisões de texto, sem abrir acesso ao texto de mensagens para a API.
- O processamento do material grava a proposta na mesma transação; usa o fuso do negócio, o ID do evento e o proprietário do vínculo. A API do dono lista propostas e permite confirmar ou descartar em qualquer ambiente.
- Resposta WhatsApp, comandos de aceite no canal, LLM e publicação continuam pendentes da próxima fatia; smoke externo requer WABA liberada.
- Validação: `make ci` com 450 testes, 100% de linhas/ramos, Ruff e mypy. Migration 0027 aplicada no banco local após backup e revertida/reaplicada no `_test`.

## 2026-10-23 — F02: primeira fatia do assistente editorial conversacional

- Migration 0026 guarda decisões por tenant/negócio e `operation_id`, com RLS e auditoria. O texto original não é persistido nessa tabela.
- Simulador autenticado somente em ambiente local/teste classifica duas entradas claras de preço/agenda de hoje, pede confirmação e permite confirmar ou descartar. Confirmação cria um fato temporário versionado; entradas ambíguas ficam para revisão.
- WhatsApp real, LLM e publicação seguem pendentes; o simulador não envia mensagens externas.
- Validação: `make ci` passou com 450 testes, Ruff, mypy e 100% de linhas/ramos. Migration 0026 aplicada no banco local após backup e revertida/reaplicada no `_test`.

## 2026-10-23 — F03.2c: consumo editorial diário

- Migration 0025 cria projeção SQL restrita a staff para uso editorial do dia UTC,
  por organização, sem liberar leitura direta da tabela do ledger. Endpoint
  auditado devolve tokens reservados, observados, chamadas medidas e incertas.
- Estados de quota usam o limite atual: aviso em 80%, esgotado em 100% e ausência
  de configuração explícita. Custo monetário segue desconhecido até haver tarifa
  versionada; não há alerta automatizado fora do painel.
- Validação: `make ci` com 444 testes, 100% de linhas/ramos, Ruff e mypy;
  teste de integração cobre isolamento de tenant, staff/cliente e agregação.
  Migration 0025 aplicada no `_test` e na base local após backup verificado.

## 2026-10-23 — F03.2c: etapas editoriais correlacionadas

- Auditoria de novos pedidos usa o ID interno único, associado ao `operation_id`
  externo, para não misturar negócios que reutilizem o mesmo ID. Claim do dispatcher
  registra etapa em transação; replay da mesma etapa é deduplicado.
- Migration 0024 cria projeção SQL restrita a staff para ação/data por pedido;
  endpoint auditado não devolve texto, mídia, prompt nem rascunho.
- Histórico legado pode ser parcial. Fluxo WhatsApp/publicação, custos em moeda,
  alertas e avaliação semântica ainda não estão concluídos.
- Validação: `make ci` com 443 testes e 100% de linhas/ramos, Ruff e mypy;
  migration 0024 revertida/reaplicada no `_test` e aplicada no banco local após
  backup em `.local/backups/`.

## 2026-10-23 — F03.2b: abstinência; F03.2c: diagnóstico inicial

- Pedidos editoriais sem fato vigente confirmado terminam com código
  `EDITORIAL_FACTS_REQUIRED` antes da reserva ou chamada paga, mesmo com material.
- Runner sintético registra esses casos como necessidade de confirmação, com zero
  tokens, e conserva os dados do relatório fora do Git.
- Nova rodada live sintética: 3/3 respostas elegíveis válidas, 2/2 casos sem
  fatos bloqueados, 821 tokens de entrada/1.335 de saída. Revisão humana ainda
  encontrou afirmações não fundamentadas; decisão de liberação comercial é
  **não**, até corrigir o contrato e passar por nova avaliação.
- Guarda adicional exige ID de fato citado; título e ângulo expostos são
  reconstituídos de um fato confirmado, enquanto formato/hipóteses/perguntas
  permanecem do modelo para revisão. Testes cobrem a remoção de uma promoção
  inventada do rascunho persistido.
- Migration 0023 cria uma função de projeção de metadados para staff, sem
  liberar leitura cruzada das tabelas editoriais ao papel da API. Endpoint
  `/admin/editorial-operations` audita a consulta e devolve só metadados de até
  100 pedidos por filtro de organização, sem texto, rascunho ou mídia.
- Custo monetário aparece como desconhecido. A linha do tempo completa e a
  leitura excepcional de conteúdo seguem para a continuação da F03.2c.
- Validação: `make ci` com 443 testes e 100% de linhas/ramos; migration 0023
  revertida/reaplicada no banco `_test` e aplicada ao desenvolvimento após
  backup verificado. Eval sintético pago repetido após a guarda, sem dados de
  clientes. A web passou 170 testes/100%, build e Chromium mobile.

## 2026-10-23 — Política planejada de aprendizado e diagnóstico

- F03.2c explicita retenção e personalização por contexto versionado/feedback,
  sem treino automático por cliente ou dataset compartilhado de WhatsApp.
- Visão admin por operação reúne etapas e gastos; leitura de conteúdo fica em
  caminho restrito e auditado. Mudança documental, sem UI/API nova.

## 2026-10-23 — F03.2b: primeiro smoke e avaliação sintética

- Adapter ajustado após o modelo consumir o limite antigo em raciocínio:
  esforço baixo, 1200 tokens de saída e limites no JSON Schema.
- Cinco casos PT-BR sintéticos versionados e runner com `--live` explícito;
  relatório local ignorado pelo Git. Última rodada: 5/5 respostas completas,
  5/5 guardas automáticos, 1.276 tokens de entrada e 1.945 de saída.
- Revisão humana encontrou uma inferência não fundamentada em caso sem fato
  confirmado. Coorte comercial permanece desativada; dados reais não foram usados.
- Worker local lê modo OpenAI, mas a base tinha zero consentimentos ativos,
  pedidos em andamento ou propostas OpenAI persistidas ao fim da avaliação.
- `make ci`: 442 testes, 100% de linhas e ramos, Ruff e mypy aprovados.
- Comparação sintética com `gpt-5.4-mini`: 5/5 respostas completas, 4/5 nos
  guardas; sem troca do modelo local nem escolha de modelo para produção.

## 2026-10-23 — Contrato futuro de conversa editorial no WhatsApp

- F02 define respostas curtas por ação editorial, confirmação explícita para
  preço/horário e limites entre falar com o dono e atender consumidores.
- Jev fica candidato a roteamento fechado após eval; extração de campos livres
  e redação exigem outros componentes. Documentação apenas, sem execução nova.

## 2026-10-23 — F03.2a: sugestões editoriais revisáveis

- Migration 0022 separa consentimento de IA, pedidos idempotentes e ledger de
  tokens reservados por tenant. RLS owner/worker, Temporal com ID determinístico,
  reconciliação de estado incerto e exclusão de sugestões derivadas de material.
- Baseline local por padrão. OpenAI Responses API opcional (`store=false`, JSON
  Schema estrito, saída limitada), com consentimento e quota antes da chamada;
  sem retry pago. Fatos vencidos, plano revogado e material ausente bloqueiam uso.
- A sugestão é um rascunho, sem publicação ou confirmação automática de fatos.
  Teste real do provedor, eval PT-BR e custo monetário aferido ficam pendentes.
- Validação: 442 testes backend com 100% de linhas/ramos, Ruff e mypy;
  migration 0022 revertida/reaplicada no `_test` e aplicada no banco local após
  backup verificado. Web: 167 testes/100% nos quatro critérios, typecheck,
  build, formatação e jornada Chromium. Workers reconstruídos e em execução.
  API local em debug precisa reiniciar para carregar a rota nova.

## 2026-10-23 — F03.1: contexto editorial confirmado

- Migration 0021 cria cabeça e versões imutáveis por tenant/negócio, com RLS
  restrito ao proprietário. API salva com versão esperada e ID de operação,
  rejeita concorrência, oferece histórico e restauração auditada.
- Fatos têm tipo, origem declarada e validade; preço, horário e oferta exigem
  prazo. Preferências ficam separadas de hipóteses. A área do cliente permite
  corrigir e restaurar versões sem publicar ou afirmar conteúdo gerado.
- Sem LLM/Jev, pesquisa externa ou chamadas pagas nesta entrega. F03.2 tratará
  interpretação estruturada, propostas e orçamento após fixar o contexto.
- Validação: 417 testes backend/100% de linhas e ramos, Ruff/mypy, concorrência
  PostgreSQL e rollback/upgrade da 0021 no `_test`. Banco local migrado após
  backup verificado. Web: 158 testes/100% em quatro critérios, build e jornada
  Chromium de edição e restauração.

## 2026-10-23 — F02.2c3b: transcrição de áudio controlada

- Migration 0020 adiciona transcript cifrado ao asset e ledger privado de
  segundos reservados; idempotência por evento e orçamento diário por tenant.
- Worker normaliza áudio a WAV, usa `gpt-transcribe` somente com chave e limite
  explícitos, e não repete chamada paga após submissão. Dispatcher converte
  submissões antigas sem conclusão em estado incerto. API e web mostram texto
  e estados ao proprietário; exclusão do asset remove o transcript.
- Consentimento específico por negócio é exigido para enviar áudio à OpenAI;
  aceite antigo de materiais não basta. O dono ativa/revoga pela API e web.
- Sem credenciais OpenAI configuradas, integração permanece desligada. Smoke
  real Meta/fornecedor e interpretação semântica continuam pendentes.
- Validação: 410 testes backend com 100% de linhas/ramos, Ruff e mypy;
  migration 0020 revertida/reaplicada no `_test` e aplicada localmente após
  backup verificado. Testes cobrem reserva, replay, teto, consentimento,
  conversão, falha incerta e reconciliação. Sem chamada paga real.

## 2026-10-23 — F02.2c3a: materiais de um mesmo envio

- Migration 0019 adiciona identidade estável de grupo à fila e aos assets,
  preservando materiais anteriores como grupos unitários. O correlator usa
  tenant, negócio, remetente e janela fixa de dez minutos; o processamento
  persiste essa identidade e a API a expõe apenas ao proprietário.
- Biblioteca web reúne itens do mesmo envio. Testes cobrem concorrência,
  isolamento entre negócios, virada da janela e persistência até o recibo.
- Validação: 374 testes backend com 100% de linhas/ramos, Ruff e mypy.
  Migration 0019 revertida/reaplicada no `_test`; backup verificado da base local
  antes da atualização para 0019. Integração PostgreSQL passou com logins
  restritos; correlator e worker locais foram reconstruídos e a API respondeu
  200 em `/health/ready`. Nenhum conteúdo Meta real foi processado.
- A transcrição com provedor, reserva de orçamento e ledger forma F02.2c3b.
  Ainda não existe interpretação semântica por LLM/Jev ou harness de agentes;
  WABA real continua restrita.

## 2026-10-22 — F02.2c2: reconciliação de uploads interrompidos

- Cada upload ganha intenção durável, chave S3 única por tentativa e auditoria antes
  de chamar o storage. A finalização do asset remove a intenção no mesmo commit.
- Dispatcher reconcilia intenções vencidas em lotes com lease/fencing, retry e
  auditoria; nunca reivindica uma chave ligada a asset finalizado. A finalização
  trava a intenção e rejeita uma tentativa já reivindicada pela limpeza. Cliente
  S3 agora tem timeouts explícitos. Migration 0018 aditiva com papel restrito.
- Validação: 372 testes backend com 100% de linhas/ramos, Ruff, formatação e mypy;
  sucesso, revogação após upload, corrida com limpeza, falha/retry do storage,
  fencing e isolamento do
  login da API. Migration 0018 revertida/reaplicada no `_test`, aplicada no banco
  local após backup verificado. Worker e dispatcher reconstruídos e em execução.
  Readiness da API local retornou 200. Nenhum evento Meta real ou conteúdo de
  cliente foi usado.
- Pendente: agrupamento/transcrição (F02.2c3), smoke Meta após desbloqueio da
  WABA, staging e inventário periódico do bucket para operação em escala.

## 2026-10-22 — F02.2c1: retenção e exclusão de materiais

- Migração 0017 adiciona prazo de 30 dias aos assets e estado de exclusão com
  lease/fencing e privilégios RLS. API oferece pedido idempotente de exclusão ao
  proprietário; materiais pedidos/vencidos somem da biblioteca e não geram links.
- Dispatcher limpa inbox/fila cifradas vencidas e apaga objetos S3 antes dos
  registros correspondentes. Falha de storage mantém a intenção para retry.
  A web mostra prazo e confirmação de exclusão; links já emitidos duram até 2 min.
- Validação: 367 testes backend com 100% de linhas/ramos; 149 testes web com
  100% nos quatro critérios; uma jornada Chromium de exclusão; Ruff, mypy,
  typecheck, build e formatação aprovados. Migração 0017 revertida/reaplicada no
  `_test`, aplicada localmente após backup. Arquivo sintético removido no
  SeaweedFS e dispatcher atualizado em execução.
- A API iniciada antes da migração pelo depurador VS Code precisa reiniciar com
  F5 para reconhecer o novo head; readiness local fica 503 até esse reinício.
- Reconciliação de upload órfão, agrupamento/transcrição, Meta real e staging
  permanecem pendentes antes de conteúdo real.

## 2026-10-22 — Diagnóstico do sandbox Meta

- App/WABA e número de teste configurados somente no `.env` local; sem segredos
  ou IDs transitórios versionados. Callback HTTPS temporário limitado à rota
  WhatsApp respondeu ao desafio e aceitou POST vazio sintético com HMAC válido;
  requisição sem assinatura recebeu 403 e outras rotas receberam 404.
- Primeiro envio de teste recebeu status `failed` com erro Meta `131031`
  (`Business Account locked`). Inbox local não recebeu subevento real. A Meta
  mostra a WABA de teste como restrita permanentemente e exige verificação da
  empresa antes de iniciar/responder conversas ou adicionar números. Verificação,
  remoção da restrição e confirmação de `subscribed_apps` da WABA estão pendentes;
  mídia e conteúdo de clientes permanecem fora do teste.

## 2026-10-22 — F02.2b2: consumo e biblioteca de materiais

- Migration 0016 adiciona consentimento por negócio, leases/fencing/tentativas
  na fila e recibos privados com RLS. Dispatcher inicia workflow Temporal por
  evento; activity revalida vínculo, proprietário, telefone, consentimento e
  acesso comercial antes e depois de buscar mídia.
- Texto cifrado e originais de foto/áudio/vídeo vão para biblioteca S3 privada;
  Meta download impõe hosts permitidos, limites de tamanho, MIME, checksum e
  inspeção local. API lista recibos e cria URL assinada de dois minutos só para
  proprietário. Revogar consentimento desconecta o canal.
- Compose local usa SeaweedFS 4.39 como storage S3. Migração 0016 validada com
  downgrade/reaplicação no banco `_test`; escrita/leitura/remoção de objeto
  sintético e URL assinada passaram no storage local. Backup da base de
  desenvolvimento salvo antes de aplicar a migration 0016.
- Validação final: 361 testes backend, 100% de linhas/ramos, Ruff, formatação,
  mypy, Compose e build das imagens API/worker passaram. API nova respondeu
  `/health/ready` e expôs três rotas de materiais em contêiner temporário.
- Sem App/WABA e staging, não houve smoke Meta real. Transcrição, resposta,
  geração, retenção/exclusão de assets e produção permanecem pendentes.

## 2026-10-22 — Marca Meu Braço Direito

- Produto renomeado na interface, metadados, logotipo, favicon, e-mails e
  documentação. Pacotes e identificadores técnicos usam `meu-braco-direito`;
  backend configura por `MEU_BRACO_DIREITO_`. Nomes, caminhos e remotos Git preservados.
- Cookies, CSRF, Web Locks e canal de logout atualizados em conjunto, mantendo
  tokens só em memória e as proteções HttpOnly/Origin. Novo login é necessário.
- Migração preserva IDs, senhas/MFA, vínculos, políticas RLS e chaves de idempotência
  de checkouts anteriores. E-mails pendentes recebem a marca nova ao enviar,
  conservando seus links/tokens. Contas de demonstração mantêm IDs estáveis.
- Ambiente local atualizado após backup SQL completo e cópia dos volumes parados;
  originais preservados. PostgreSQL, Temporal e workers usam os nomes novos.
  IDs de usuários/credenciais/negócios/organizações/checkouts comparados ao backup.
  Nenhum workflow ativo ficou na fila antiga; histórico Temporal preservado.
- Testes de navegador ajustados aos seletores e títulos atuais e ao HTML UTF-8
  no retorno externo simulado. Documentação operacional em
  [renomeação do produto](product-rename.md).
- Validação: 136 testes web com 100% de linhas/statements/funções/branches;
  289 testes backend em modo CI com 100% de linhas/branches; tipos, formatação,
  lint, build web e imagens Docker aprovados. Nove jornadas Chromium passaram
  com API/SMTP reais em banco exclusivo `_test`; checkout externo simulado,
  sem pagamento adicional. Screenshots desktop/mobile revisados.
- Migração de uma cópia do banco anterior validou conflito de roles com rollback
  atômico, upgrade, downgrade/reaplicação e preservação de IDs/chaves Stripe.
  Instalação local passou em readiness e título OpenAPI. Nenhuma pendência de
  implementação da marca; reinício do processo F5 continua necessário.
- Reiniciar a API em F5 para reler `.env` e autenticar novamente. Sem publicação,
  commit ou push; configurações de marca em contas externas não foram alteradas.

## 2026-10-22 — F02.2b1: correlação privada de mensagens

- Migration 0015 cria papel/login restrito de correlação e fila cifrada de
  materiais com identidade única, tenant/negócio, retenção e RLS.
- Processo separado associa apenas mensagens posteriores a vínculo ativo;
  descarta comandos e formatos não aceitos, audita e permite concorrência por
  `SKIP LOCKED`. A fila ainda não é consumida por IA ou Temporal.
- Migração 0015 validada com upgrade/downgrade/reaplicação em PostgreSQL
  temporário `_test`; a base local renomeada está em 0015. 289 testes com
  100% de linhas/ramos, Ruff, mypy e configuração Compose passaram. Não houve
  smoke Meta real nem envio de conteúdo ao Temporal.
- Após a migração de marca entrar na cadeia Alembic, uma segunda base temporária
  confirmou upgrade completo desde zero, downgrade até `0015_product_brand`,
  reaplicação da rota e seis testes direcionados. Containers de teste removidos.

## 2026-10-22 — Correção do CI da F02.2a

- GitHub Actions define explicitamente `TEST_META_DATABASE_URL` na porta 5432 do
  serviço PostgreSQL do CI; antes, pytest carregava a URL de exemplo local na
  porta 55432 e falhava na checagem de isolamento do banco `_test`.
- Preparação do banco de teste cria o login restrito `meu_braco_direito_ingest` e concede
  `meu_braco_direito_meta`, necessário aos testes da inbox e do vínculo WhatsApp.
- Pytest exige todas as URLs e o endereço Temporal explícitos sob `CI`, evitando
  que um ambiente remoto use por engano valores do exemplo local.
- Validação local: YAML/URLs do workflow conferidos, setup dos logins executado
  no banco `_test`, guarda de URL ausente exercitada, 278 testes em modo `CI=true`
  com 100% de linhas e ramos, Ruff e mypy aprovados. Execução remota do Actions
  ainda depende de push.

## 2026-10-22 — F02.2a: vínculo comprovado do WhatsApp

- Migration 0014 acrescenta índice cego do remetente à inbox e tabelas de desafio
  e vínculo com RLS por dono/tenant, expiração e unicidade de remetente ativo.
- API cria código único de 15 minutos após verificar dono, telefone e plano; confirma
  somente mensagem assinada do mesmo número. Corridas de confirmação, troca de
  telefone e repetição não vinculam um negócio incorreto; vínculo e revogação
  têm auditoria durável.
- Webhook sintético e testes de falha/concorrência exercitam a prova localmente.
  UI, smoke Meta real, resolução do remetente e mídia/IA continuam pendentes.
- Migration 0014 revertida e reaplicada no banco `_test` e no desenvolvimento
  local, após backup `.local/backups/meu-braco-direito-before-0014-2026-10-22.dump`.
  As tabelas novas estavam vazias antes da reaplicação da política RLS; nenhum
  dado de vínculo foi descartado. 278 testes, 100% de linhas e ramos, Ruff e
  mypy aprovados com comandos equivalentes da `.venv`.

## 2026-10-21 — F02.1: entrada segura do WhatsApp

- Handshake e callback WhatsApp Cloud API com HMAC do corpo bruto, limite de 256 KiB,
  filtro do número/WABA configurados e separação de mensagens/status. Configuração
  ausente desabilita o webhook; nenhum segredo entra em logs/resposta.
- Migration 0013 cria inbox cifrada com dedupe por subevento, RLS e papel isolado.
  Reentregas concorrentes não duplicam registros; login normal não lê a inbox.
  Eventos ficam em quarentena até vínculo comprovado na F02.2.
- Role local criada no cluster existente; banco `_test` validou downgrade/upgrade.
  Backup local `.local/backups/meu-braco-direito-before-0013-2026-10-21.dump` antecedeu
  upgrade aditivo do banco de desenvolvimento. Dados existentes preservados.
- 271 testes backend/100% linhas e ramos; Ruff e mypy passaram. `make ci` não
  executou porque `uv` não está no PATH deste shell; comandos equivalentes da
  `.venv` passaram. Sem teste real Meta, envio, transcrição ou publicação.

## 2026-10-21 — Revisão da análise externa de IA e conhecimento do negócio

- SDD geral, fases F02–F08, PROJECT e interfaces incorporam contexto do negócio
  versionado, separado em fatos confirmados, preferências e hipóteses. Aprovação
  de conteúdo não autentica preço/horário/promoção; dono pode revisar e corrigir.
- Ledger mínimo com reserva atômica é pré-requisito de qualquer operação paga em
  F03/F04, e F07 fica responsável pela evolução comercial/relatórios.
- Geração passa a ter contratos por capacidade, FFmpeg para receitas compatíveis e
  benchmark limitado/consentido. HeyGen, Runway, Kling e Veo são candidatos sujeitos
  a spike, contrato, custo e qualidade; nenhum foi ativado por esta decisão.
- Revisão documental apenas: sem código, migration, teste de execução, acesso a
  credenciais ou mudança de status das fases. ADR em
  `docs/design/business-context-and-generation.md` registra critérios e rejeições.

## 2026-10-21 — Correção do telefone do negócio

- `/app/phone` mostra o destino E.164 do SMS; DDD e número brasileiros recebem
  `+55` automaticamente. Proprietários podem corrigir o telefone depois do
  onboarding. A alteração invalida códigos pendentes e exige nova verificação.
- `PATCH` protegido por owner/RLS e migration 0012 aditiva. Validado com 254
  testes backend, 100% de cobertura e downgrade/upgrade da migration no banco
  `_test`; aplicada também ao banco local sem alterar perfis existentes.

## 2026-10-21 — Conta de operador após revogação

- A consulta de convite agora informa também quando a identidade já foi operadora
  e teve o acesso revogado. A conta sem negócio vê `/staff-access-revoked` após
  login, em vez de entrar automaticamente no onboarding comercial.
- Um novo convite pendente continua sendo apresentado primeiro para permitir a
  reativação por aceite, novo login e MFA. Testes de API e interface cobrem a
  perda do acesso administrativo e o destino após revogação.

## 2026-10-21 — Aceite de convite e e-mails

- Convite válido acessado por outra conta responde
  `INVITATION_EMAIL_MISMATCH`; token expirado, revogado ou já usado mantém
  `INVALID_INVITATION`. A migration 0011 permite consultar apenas o convite
  correspondente ao token apresentado, preservando o isolamento entre contas.
- E-mails transacionais novos usam HTML padronizado e alternativa em texto.
  O worker também reconhece mensagens anteriores pelo assunto e extrai o link
  do corpo, inclusive quando a API em debug ainda está com código antigo.
- `GET /staff/invitations/pending` identifica o convite válido da própria conta
  para separar a entrada de operador do onboarding de negócios.

## 2026-10-21 — Reconciliação e F01.6 local

- Billing agenda consultas canônicas à Stripe para checkouts abertos sem assinatura
  ativa, mesmo se o webhook não chegar. Jobs duráveis têm dedupe por janela de cinco
  minutos, batch limitado e reaproveitam Temporal/lease/fencing. Migration 0008.
- Operadores com MFA convidam por e-mail criptografado, com expiração de 48 horas,
  idempotência, aceite por e-mail verificado e TOTP individual. Revogação cancela
  convite ou encerra sessões de staff; ações são auditadas e RLS impede concessão
  direta por clientes. Migration 0009 e telas `/admin/staff`/`/staff-invite`.
- Verificação de telefone do negócio preparada com Twilio Verify, cooldown, cinco
  tentativas, expiração e checagem `approved` antes de marcar o perfil. A UI
  `/app/phone` mostra indisponibilidade quando não há provedor. Migration 0010.
  Nenhuma entrega real de SMS/WhatsApp ocorreu: conta/credenciais não existem.
  Compose repassa somente as variáveis do provedor à API; o cliente web não recebe
  segredos. Adapter compartilha pool HTTP por processo e o fecha no shutdown.
- Migrações 0009/0010 testadas com downgrade/upgrade em `_test` e aplicadas ao banco
  local após backup; contagens de contas, tenants, negócios, perfis e jobs preservadas.
  Workers billing/auth-mail reconstruídos. API do usuário em F5 requer reinício.
- Readiness compara a revisão do banco com o head Alembic do código, recusando API
  nova sobre schema antigo; scheduler divide candidatos entre workers com
  `SKIP LOCKED` e cobre assinatura anterior vencida.
- Backend: 244 testes/100% linhas/branches, lint/tipos e integração PostgreSQL/Temporal;
  web: 107 testes/100% nos quatro critérios, tipos/build e oito jornadas Chromium,
  inclusive envio/cancelamento de convite ao Mailpit em banco `_test`. Staging AWS
  e envio real de código ficam pendentes; sem deploy, commit ou push.

## 2026-10-21 — Oportunidades de checkout no admin

- Endpoint administrativo paginado lista checkouts atuais abertos ou expirados sem
  acesso ativo, com nome do negócio, e-mail de quem iniciou a contratação e telefone
  informado (indicando se foi verificado). Não retorna link Stripe nem cartão.
- Consulta exige staff/MFA, RLS e auditoria; assinatura/patrocínio ativos não viram
  oportunidade. Índice 0007 para paginação recente, aplicado localmente e testado
  com upgrade/downgrade/upgrade no banco `_test`.
- 219 testes backend com 100% de linhas/branches; mypy aprovado. Sem cobrança nova.
- Smoke somente de leitura na base local confirmou que o negócio informado aparece
  entre as oportunidades abertas. Browser no banco `_test` validou a lista do admin.

## 2026-10-21 — Contrato para novos operadores

- F01.6 explicita convites/revogação auditados de staff, e-mail verificado,
  MFA individual e bootstrap administrativo controlado. Ainda planejado;
  o operador demo permanece restrito ao desenvolvimento local.
- Corrigido no frontend o reuso do campo de senha no passo de MFA, sem mudança
  no backend. Sem alteração de credenciais, cobrança ou dados de clientes.

## 2026-10-21 — Sessão no retorno do checkout

- Reproduzido em Chromium: login em 127.0.0.1 e retorno para localhost geram
  INVALID_SESSION, pois o cookie de refresh é host-only. Pagamento sandbox do
  titular já estava confirmado; nenhuma nova cobrança foi necessária.
- API valida Origin pela allowlist e congela na intenção antes do processamento.
  Migration 0006 adiciona return_origin nullable; legados usam configuração vigente,
  checkouts criados e sua idempotência preservam parâmetros. Produção exige origem
  exata; sem URLs arbitrárias, cookies compartilhados ou token no navegador.
- Testes de origem, replay, worker com configuração alterada, legado e URLs Stripe;
  jornadas browser para restauração após saída/retorno nos dois aliases locais.
- README usa --all-snapshot para a CLI atual. Sem commit/push/deploy.
- Validação: make ci com 218 testes/100% linhas e branches; web com 84 testes/100%,
  tipos/build e sete jornadas Playwright aprovadas. Retorno externo simulado sem
  pagamento; API/SMTP/DB _test reais. Downgrade/reaplicação da 0006 no banco de teste.
- Migration local aplicada preservando contagens de cadastros, sessões e cobrança,
  incluindo a assinatura de teste ativa. Worker billing reconstruído/atualizado;
  API do usuário em F5 precisa reiniciar. Sem nova assinatura ou cobrança.

## 2026-10-20 — F01.5: contratação e acesso

- Stripe escolhido como primeiro adapter para teste/produção, sem alegação de
  liderança de mercado nem cobrança comercial habilitada. ADR/SDD em design/billing.md.
- API de status, intenção de checkout idempotente, webhook assinado com inbox de
  referências, consulta canônica e jobs Temporal. Timers duráveis para expiração,
  lease/fencing, retry limitado e falha rastreável. URLs de pagamento fora do
  histórico Temporal; mensagens sensíveis do SDK não entram em falhas do workflow.
- Migration 0005 com role billing isolada e FORCE RLS. Runtime não confirma
  pagamento; billing não escreve identidade/membership/patrocínio ou auditoria antiga.
- Patrocínio de seis meses com motivo, replay sem extensão e revogação auditada;
  estado pago/teste/patrocinado separado. Auditoria/outbox atômicas, MRR indisponível.
- Cliente /app/billing, admin /admin/billing, busca limitada e contagens reais.
  Checkout indisponível sem keys/Price/valor; callback de sucesso não ativa acesso.
- CI inclui login restrito billing. Compose/debug incluem processo billing,
  inativo para provedores no modo disabled. R$99 continua exemplo de sandbox.
- Downgrade/upgrade da 0005 validado no banco _test; upgrade main preservou
  contagens de contas, organizações, negócios/perfis e memberships. Sem deploy/push.
- Pendentes: conta e credenciais do titular, sandbox real, plano/franquias/termos,
  conciliação periódica/reprocesso, portal/cancelamento, staging/AWS e carga.
- Validação final local: make ci com 206 testes, 100% linhas/branches, lint/tipos;
  frontend 84 testes/100% em quatro critérios, tipos/build/formatação. Cinco
  jornadas Playwright com API/SMTP reais passaram, incluindo uso/revogação de
  patrocínio. Adapter Stripe validado por contratos, não por cobrança em sandbox.
- Imagens API/billing construídas; role billing pronta no Docker e processo
  disabled verificado. Migração local preservou dados existentes. F01.5 permanece
  aberta até validação do provedor e staging; sem commit/push/deploy/cobrança real.
- Rollback completo até base e upgrade head passaram no banco _test, com logins
  restritos reaplicados. Preparo de browser recusou billing apontando para main
  antes de semear/resetar fixtures. Servidores temporários de QA encerrados;
  processos do usuário e o serviço billing local/disabled foram preservados.

## 2026-10-20 — Contexto do negócio e cidade estruturada

- Web amplia atividades com opção livre e permite qualquer cor HEX, além de sugestões.
- API oferece catálogo público IBGE versionado (27 UFs/5.571 municípios), cacheado
  em memória, sem chamadas externas ou acesso a dados de tenant no cadastro.
- Validação conjunta de município/UF/código; migration 0004 aditiva e reversível.
  Perfis legados e hashes de replay mantidos. Código IBGE não equivale a coordenadas.
- Testes de catálogo, incompatibilidade de UF/cidade/código, persistência atômica,
  replay e cores/atividades livres. `make ci`: 131 testes, 100% linhas/branches.
- Downgrade/upgrade da 0004 validado no banco _test. Upgrade local preservou
  contagens de contas, organizações e perfis. API em F5 requer reinício.
- Frontend: 62 testes com cobertura 100% em quatro critérios, formato e build
  aprovados. Quatro jornadas Playwright com API/SMTP reais passaram, incluindo
  novo onboarding desktop/mobile. Build Docker confirmou snapshot de 5.571 cidades
  presente na imagem. Relatórios/sessões de QA locais, sem dados da base principal.
- F01.5/F01.6 e staging continuam pendentes; sem commit, push ou deploy.

## 2026-10-20 — Cadastro local: ORIGIN_REJECTED

- Reproduzido 403 com Origin http://127.0.0.1:5173, endereço anunciado pelo Vite,
  enquanto a API estava configurada com http://localhost:5173.
- Guard de auth aceita ambos os nomes de loopback em development/testing,
  preservando porta/protocolo. Staging/production continuam com origem exata;
  nenhum wildcard/CORS permissivo. Links canônicos e cookies host-only preservados.
- Regressão cobre cadastro/verificação/login/refresh pelo alias, rejeição de
  origem ausente/null, outros hosts, portas e protocolos e isolamento por ambiente.
- Validação: `make ci` aprovado, 117 testes e 100% de linhas/branches; lint e tipos
  aprovados. Reprodução HTTP também confirmou que o proxy Vite preserva Origin.
- Não exige migration. Debug F5 sem reload precisa reiniciar para carregar a correção.

## 2026-10-20 — F01.1–F01.4 implementadas localmente

- Atualizados SDD geral e fases com contratação automática, provisionamento,
  onboarding WhatsApp, admin interno e área do cliente. F01.5 antecipa cobrança mínima.
- Criados SDDs geral/admin/cliente no novo repositório local-spark-web.
- Entregues OIDC/RS256/JWKS com cache/timeout/rotação, identidade por issuer+subject,
  sessão e contexto; HS256 legado limitado a desenvolvimento/testes sem OIDC.
- Migration 0002 adiciona identidade, staff, perfil, consentimentos e registro de
  onboarding; RLS e permissões limitam bootstrap ao primeiro owner e negam hijack.
- Onboarding usa lock transacional por ator, deduplicação, replay e conflito de payload;
  negócio, perfil, consentimentos, auditoria e outbox compartilham transação.
- Admin readonly auditado com métricas reais, busca limitada e paginação; cliente
  não recebe privilégio global. Contas/memberships/staff revogados têm acesso negado.
- Keycloak/Mailpit locais, realm público PKCE e audience da API; seed do operador
  local sem impressão de tokens. Debug passa a iniciar também identidade e e-mail.
- Web independente com SDDs geral/admin/cliente, login, onboarding, áreas distintas e
  estados reais. Documentação de execução atualizada; referência React preservada.
- Evidência: `make ci` passou com **85 testes, 573 statements e 62 branches, 100%**;
  lint/tipos, rollback/reaplicação no banco `_test` e build Docker aprovados.
- Frontend: 31 testes com 100% de cobertura, build e quatro jornadas reais Playwright
  em desktop/mobile. F01 inteira permanece aberta; sem CI remoto/deploy nesta entrega.
- Checkout, verificação WhatsApp, convites e staging permanecem pendentes.

## 2026-10-20 — Cobertura 100% e configuração da suíte completa

- Gate de cobertura elevado de 81% para 100%, incluindo branches e todos os
  módulos de produção existentes, sem novas exclusões.
- Adicionados testes dos contratos HTTP de criação/replay, idempotência e paginação
  no serviço, readiness sem migration, lease perdido durante dispatch e resposta
  inválida da activity no workflow.
- Pytest carrega configuração exclusiva `.env.test.example` e `.env.test` opcional;
  variáveis de ambiente exportadas prevalecem. Integrações PostgreSQL/Temporal
  não são mais puladas por falta de variáveis. Banco continua limitado a `_test`.
- `.env.test.example` versionável; `.env.test` continua ignorado. CI e documentação
  atualizados para o novo gate. Nenhuma regra de produção alterada.
- Evidência: 62 testes passaram; 390 statements e 40 branches cobertos, total 100%.
- `make ci` completo passou sem exportar variáveis `TEST_*` manualmente: lint,
  formatação, tipos e suíte completa. Actionlint validou os workflows atualizados.

## 2026-10-20 — Versionamento e arquivos locais

- Substituído template genérico do `.gitignore` por regras específicas de Python,
  segredos locais, PostgreSQL/Temporal, backups, cobertura e metadados do editor/SO.
- Mantidos versionáveis `.env.example`, `uv.lock`, `.python-version`, CI, testes,
  migrations SQL, documentação e os quatro arquivos compartilhados `.vscode`.
- Nenhum arquivo removido do disco ou do índice; commit/push não executados.
- Validação: `git check-ignore` confirmou 27 caminhos ignorados e 29 caminhos
  versionáveis; nenhum arquivo já rastreado exige remoção do índice. Diff sem erros.

## 2026-10-20 — Correção de Docker nas tarefas VS Code/macOS

- Pré-tarefas do debug usam o executável absoluto do Docker Desktop no bloco `osx`
  e PATH explícito para Compose e credential helpers. Corrige falha de lançamento
  quando o editor não herda `/usr/local/bin` no PATH.
- Validação: ambas as pré-tarefas executadas com PATH herdado restrito a
  `/usr/bin:/bin`; API Docker restaurada e readiness 200 após a verificação.

## 2026-10-20 — Debug VS Code

- Adicionados launch, tasks, seleção de interpreter e extensões recomendadas em
  `.vscode` para depurar a API FastAPI localmente com `.venv` e `.env`.
- Prelaunch sequencial para a API Docker e inicia dependências, liberando porta
  8000 para o debugger. Workers continuam em Docker; debug sem reload.
- Documentados nome do banco, schema e conexão local no DBeaver.
- Validação: quatro JSONs válidos; pré-tarefas executadas; API iniciada com debugpy
  da extensão e argumentos configurados, ready/Swagger/OpenAPI 200. API Docker
  restaurada após smoke. Não foi executada uma sessão interativa no editor.

## 2026-10-20 — Nome e ambiente Meu Braço Direito

- Adotado `local-spark-platform` como repositório principal, preservando seu remoto
  e as alterações locais existentes. Restaurados os arquivos de CI, Docker e
  configuração que não estavam presentes na cópia do repositório.
- Padronizados nome de pacote, Swagger, logs, configuração `MEU_BRACO_DIREITO_`, issuer,
  audience e task queue. Bancos usam `meu_braco_direito_platform` e
  `meu_braco_direito_platform_test`; roles usam `meu_braco_direito_*`.
- Atualizadas senhas locais de administração, runtime e relay, além da chave JWT
  de desenvolvimento. `.env` local criado e ignorado pelo Git; tokens precisam
  ser reemitidos. Nenhuma credencial externa/produção foi alterada.
- Dados PostgreSQL copiados com o serviço parado antes de renomear bancos/roles
  e alterar senhas. Volume anterior mantido. Identidades de demonstração preservadas.
- Histórico Temporal local transferido para volume nomeado persistente. Containers
  anteriores permanecem parados; desenvolvimento passa a usar o novo projeto Compose.
- SDD geral, fase F00, contexto do projeto e instruções locais atualizados.
- Validação: `make ci` passou (54 testes, cobertura 96,05%, lint e tipos);
  migrations revertidas/reaplicadas no banco `_test`; actionlint e build passaram.
  Swagger/health/OpenAPI 200; criação 201, replay 200 e um efeito no workflow.
  Registro anterior e histórico Temporal concluído preservados; JWT antigo rejeitado.

## 2026-10-20 — F00

- Criado repositório local `local-spark-platform`, nome provisório, seguindo convenções
  organizacionais do `spotlight-api`, sem modificar esse projeto ou copiar segredos.
- Implementados API versionada, configuração, JWT verificado, tenants/memberships,
  negócios, RLS, idempotência, auditoria e outbox atômicas.
- Relay com SKIP LOCKED, lease/fencing, timeout RPC e workflow ID estável; activity
  revalida intenção persistida e deduplica o efeito. Temporal real usado nos testes.
- Testes unitários/integração/concorrência, lint, tipos e gate de coverage 81%.
- Containers locais e GitHub Actions de CI/deploy ECS preparados e validados.
- Documentação geral, resumo vivo, nove SDDs de fase e AGENTS.md para continuidade.
- Evidência: 54 testes passando, 96,74% coverage; migration rollback/upgrade,
  actionlint, build Docker e smoke HTTP/outbox/Temporal confirmados.
- Próximo: F01. Pendências comerciais não bloqueiam a fundação, mas devem ser
  resolvidas antes de cobrar, gerar identidades ou publicar para clientes reais.

## 2026-10-20 — Auth própria substitui Keycloak

- Decisão do usuário registrada em `docs/design/native-auth.md` e refletida nos
  SDDs geral/F01/F08, PROJECT, operação e READMEs. OIDC do GitHub/AWS permanece.
- FastAPI implementa cadastro, login, sessão JWT curta/revogável, refresh aleatório
  com hash, cookie HttpOnly, CSRF/Origin, rotação atômica e revogação por reutilização.
- Argon2id com concorrência limitada fora do event loop; verificações de sessão,
  conta ativa e MFA administrativo em cada pedido/renovação. Falhas sanitizadas.
- Staff exige TOTP, segredo criptografado, proteção de replay e recuperação de uso
  único. Reset de senha revoga sessões e preserva MFA; mudança de papel exige prova.
- Verificação/reset com ações de uso único e TTL, outbox criptografada e worker SMTP
  separado com lease/fencing, retry limitado e recuperação de leases expirados.
- Migration 0003 mantém usuários/empresas/vínculos e prepara credenciais sem senha
  para e-mails antigos não ambíguos. Login DB de auth isolado, sem acesso a negócio
  ou concessão de staff; readiness verifica também o banco de autenticação.
- Tokens/credenciais excluídos de parâmetros SQL de diagnóstico e respostas 422.
- Keycloak removido do Compose/debug, container encerrado/removido sem apagar seu
  volume legado. Mailpit permanece local, com SMTP 11025 no host e 1025 no Docker.
- Seed local preserva IDs/senhas/MFA; seed que imprimia JWT sem sessão foi aposentado.
- Frontend usa telas e AuthProvider próprios; bibliotecas OIDC removidas. Cookies
  restauram a sessão após recarga; cache/logout entre abas e tratamento de links
  sucessivos na mesma aba validados por testes.
- Evidência: `make ci` aprovado com 103 testes, **100% linhas/branches** em todos os
  módulos app, sem novas exclusões. Frontend com 59 testes e 100% em quatro critérios.
- Migration downgrade/base/upgrade validado no banco exclusivo _test. O preparo de
  browser recusa main/remoto e não toca dados da aplicação. Build Docker e browser
  registrados após a validação completa. AWS/staging e demais fatias continuam pendentes.
- Validação final: quatro jornadas Playwright reais passaram (staff com MFA/logout,
  cliente/onboarding/recarga/403, registro/verificação/reset/replay e navegação pública).
  Builds web/API/SMTP aprovados. Smoke na imagem Docker confirmou readiness dos
  dois logins DB, login nativo, vínculo antigo preservado, revogação imediata por
  logout e entrega SMTP real no Mailpit. Nenhum provedor de identidade externo usado.

## 2026-11-04 — geocodificação do cadastro e vínculo da identidade

- API GET/POST de geocodificação e confirmação, outbox/Temporal e guard financeiro
  reutilizando origem, piloto, tarifa e limites existentes; nenhum fornecedor pago.
- Coordenadas próprias persistidas, identificação precisa automática, opções
  ambíguas confirmadas pelo titular e retry sem novo HTTP após resposta incerta.
- Admissão exige endereço próprio; nome/versões ficam vinculados por HMAC e são
  revalidados antes da publicação. Pesquisa manual usa a origem salva e inclui
  seu custo no agregado0102; origem de dispositivo segue distinta do cadastro.
- Validação:21 testes aprovados com PostgreSQL `_test`, runtime restrito,
  Temporal local e HTTP simulado; módulos novos com100% de linhas e branches
  (182 statements/26 branches). Downgrade0103→0102 e upgrade vazio aprovados;
  Ruff e mypy10 módulos aprovados. Ensaio externo e descoberta completa continuam
  fora desta fatia. Contrato em `docs/design/business-geocoding.md`.

## 2026-11-04 — integração de referências até 0105

- Publicação privada de resultados e API de leitura/seleção; revisão de ausentes
  restrita ao primeiro resultado do ciclo novo. Publicação: 21 testes, 100% dos
  módulos novos. Dois cenários adicionais de cache/rollback aguardam nova execução.
- Orçamento por pesquisa compartilhado entre titulares: cinco casos SQL aprovados.
- Override manual de Instagram com versão/operação/audit/outbox: 12 testes, 100%.
- Contrato Compass corrigido, run persistido, recuperação por GET e custo terminal
  idempotente: 164 unitários (100% adapter/MAC) e 14 integrações SQL aprovados.
  Nenhuma chamada paga. Metadados oficiais e limites em
  [contratos](evals/reference-provider-contracts-2026-11-04.md).
- Primeira execução integral da retomada: lint/mypy aprovados, 3.993 testes
  aprovados, duas falhas e 99,38% de cobertura. Falhas baseline de identidade do
  login de teste/Temporal e lacunas de cobertura em correção; não registrar como
  `make ci` aprovado. Migrações integradas no código, ainda sem aplicar ao banco local.
- Restam executor real, análise/atualização de perfis, contexto criativo completo,
  validação final e ensaio fictício dentro do teto autorizado.

## 2026-11-04 — transporte de feed e nova regra de vazio

- Feed Instagram possui rede explícita, preço/build/Actor conferidos e custo
  terminal separado; imagens limitadas aos CDNs conhecidos, sem redirects/proxy
  ou retries e sem persistência de conteúdo. Entrada oficial sem skipPinnedPosts,
  MACv2; helper de metadados/custo compartilhado com contatos.
- 357 unitários, 100% linhas/branches em cinco módulos, Ruff/mypy aprovados.
  Nenhum POST pago. A cadeia integrada0105 passou em19 testes SQL adicionais.
- Entrevista definiu Google vazio: ampliar5 → 20 → 50; todos vazios permitem tentar
  novamente sem iniciar seis meses. Regra sendo conectada no executor.

### Configuração do piloto de referências, 04/11

O script `scripts/configure_reference_pilot.py` prepara a política local e o
piloto acumulado de US$ 5, sem zerar consumo ou habilitar fornecedores. Plano
por padrão; aplicação exige banco local/admin separado e preserva configurações
divergentes. 14 unitários e três testes SQL aprovados; execução real ainda pendente. Ver
[operação](design/reference-pilot-operations.md).

## 04/11/2026 — Retomada do baseline de validação

- Corrigida a prova de role para o login runtime do banco isolado, exigindo
  ausência de superuser/bypassRLS. E2E Temporal mantém timeout de 45s.
- Retirados caminhos inacessíveis após C17/C18 em pedidos/render local e
  execução editorial; preservados bloqueios, replay e histórico.
- Acrescentados guards de trace, skill, symlink, vínculo de tentativa, SHA,
  comandos ambíguos e aprovação histórica. 14 integrações dirigidas e 3.555
  testes relacionados aprovados; cobertura parcial de 98,31%, com verificações
  adicionais posteriores. CI integral final ainda pendente.
- [Funções afetadas e limites da evidência](evals/ci-resume-2026-11-04.md).

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

## 2026-11-04 — Revisão da própria loja e expansão de resposta vazia

- Persistência atômica da conclusão própria do matcher com notas e semelhança; confirmação compartilhada auditada e retomada da mesma execução.
- Loja própria excluída do ranking e publicação; Google names/endereço/tipos permanecem transitórios.
- Resposta vazia amplia pelos raios 5/20/50 sem mudar preferências; cache/custos/ciclo revalidados e limite financeiro compartilhado.
- Rodada completamente vazia preserva seleções e permite nova tentativa quando ainda não confirmada; resultado e replay sobrevivem à liberação do ciclo.
- Banco dedicado e restrito validou upgrade/downgrade, revisão compartilhada, exclusão, fallback, orçamento e replay. Feed/agenda e consumo editorial seguem na próxima fatia.

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

Contrato e validação em [integração de referências na geração](design/reference-generation-context.md).
177 testes unitários e 13 casos PostgreSQL passaram nos recortes desta fatia,
incluindo leitura 0108 e geração visual com HTTP simulado. A agenda completa e
o CI integral continuam pendentes; essas provas não demonstram qualidade comercial.

### 2026-11-04 — persistência e agenda de aprendizados (0108)

- Associações canônicas de perfis manuais/sugeridos e sincronização atômica nos
  escritores; janela imediata no aceite/troca e aniversários de seis meses.
- Run de coleta persistido, retomada com o mesmo identificador, bloqueio por
  orçamento/configuração sem encerrar a janela e cancelamento após remoção/troca.
- Padrões próprios comprovados, nome oportunista Apify e estado explícito de
  análise; leitura compartilhada pelos titulares e revalidação para geração.
- Validação: 36 integrações dirigidas, 11 unitários (store 100%, 84 linhas/6 ramos),
  Ruff/mypy e roundtrip vazio 0109→0107→0109. As fatias de execução, snapshot/UI e
  o ensaio real são validados separadamente; CI final ainda deve ser concluído.

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
