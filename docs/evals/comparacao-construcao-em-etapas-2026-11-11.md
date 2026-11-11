# Café Pausa — prova da construção em duas etapas

Nova rodada autorizada pelo titular em 11/11/2026: teto exclusivo US$ 3, um
planejamento, uma implementação, uma imagem conceitual de xícara, renderização e
uma crítica. Sem tentativas extras, publicação ou reutilização de orçamentos.
Reservas máximas US$ 2,75 (modelo: 3 × 0,75; imagem: 0,50).

## Entrada e execução

Mesma gravação SHA-256
dd3f0265a4b2d94206188f46c094dc0177663e1a529b9ad2e0718a1dfad78a34,
voz, kit Café Pausa, direção e repertório. Seis quadros da gravação e seis imagens
de referência; transcrição local automática não revisada com 30 palavras. Mantidos
tratamento/moldura da gravação, fundo narrativo, alternância com motion pleno,
xícara conceitual fotográfica em camadas 2.5D e ações ligadas à fala. Não há objeto
3D, foto documental do produto ou tracking implementado nesta rodada.

Modelo gpt-6.1-sol, reasoning high e teto de saída 54.000 para cada etapa de
construção, conforme configuração anterior. Crítica limitada a 8.000 tokens.
O preflight contabiliza a entrada de cada chamada e exige teto dentro da reserva.
Contrato provided-direction-output-v3 separa plano e implementação com vínculo por
hash, validação intermediária e recibos duráveis. Sem remontar respostas parciais.

Pasta `.local/evals/motion-staged-construction-20261111/`. Entrada real em
`input-package/` e ZIP adjacente; `planning-input/` é a preparação offline anterior.
Autorização específica em `approval.json`, vinculada ao SHA-256 de `paid-plan.json`.
Nunca compartilhar `private.json` ou recibos privados sem revisão.

Pedido `81eaf22e-d32b-5c67-b2d7-5593059e7a7d` admitido pela API com resposta 202 e
despachado pelo outbox no Temporal, com fila e worker exclusivos. Banco de
desenvolvimento existente, sem banco temporário ou limpeza. Cinco serviços em
falha continuam parados. Executor isolado passou no quadro sintético 64×64 antes
da geração; isso verifica funcionamento técnico, não acabamento da peça.

## Comparação visual prevista

Referência anterior:
`.local/evals/motion-reliability-20261110/comparacao-alternancia.mp4`.
Inspeção dos quadros 1 s, 5,5 s e 10 s confirma fundo papel uniforme, gravação sem
moldura visível e xícara desenhada. A alternância com motion pleno já existia.
Avaliar a nova saída pelos pixels e movimento, sem inferir qualidade do texto do
plano. Preservação de áudio também será conferida no arquivo efetivo.

## Resultado

Workflow encerrado após 314,67 s, sem versão de vídeo. O planejamento retornou
`status=completed`, JSON completo de 22.005 caracteres, com 3 cenas, 18 elementos,
36 beats (28 com vínculo a cue da fala) e uma imagem declarada. Passou nas validações
intermediárias e foi preservado antes da segunda chamada. Contagem: 35.392 tokens
de entrada e 13.744 de saída, incluindo 7.384 de reasoning; teto 54.000.

Implementação passou no preflight: 43.448 tokens de entrada, limite 54.000 de
saída, máximo calculado US$ 0,648620 dentro da reserva de US$ 0,75. O provedor
recusou o envio com `type=insufficient_quota` e `code=credit_balance_exhausted`,
informando ausência de créditos. O produto registrou `MOTION_AI_HTTP_FAILED`.
O corpo de erro tem 262 bytes e não traz usage. Não se trata do JSON truncado das
rodadas anteriores, nem de bloqueio pelo teto local desta rodada. O saldo da conta
não foi consultado independentemente: esta é a evidência recebida do provedor.

Nenhuma imagem foi gerada, nenhum render da peça realizado e nenhuma crítica
acionada. Não houve nova tentativa. O plano completo foi preservado, mas ainda
não há prova de conclusão da implementação nem comparação de qualidade.

Estimativa conhecida do planejamento: **US$ 0,22592**. Rejeição da implementação
sem usage/custo conhecido; total estimado incompleto. Duas reservas de US$ 0,75
mantidas, somando **US$ 1,50**; nenhuma liberação manual ou orçamento anterior
reutilizado. Reservas não são fatura. Worker exclusivo encerrado e os cinco
serviços previamente parados continuam parados.

## Evidências e próximo desbloqueio

Na pasta da rodada: `result.json`, `workflow-result.json`, `receipt-summary.json`,
`failure-analysis.json`, `planning-output.json`, além dos recibos privados cifrados
no produto e cópias locais com permissão restrita. Não executar saídas incompletas.

O pacote `implementation-input/` e `implementation-input.zip` foi montado offline
pelo exportador existente a partir do recibo real, plano completo e assets
conferidos por hash. `implementation-export-check.json` comprova igualdade dos
bytes reconstruídos com o `wire_sha256` enviado:
`4d090d333dfc9a7644a6d5270c139a1a12b43e7e53df05cbaff7797b0cdcb6fc`.
Conserva 12 imagens e inclui prompt integral, contexto, plano, bibliotecas,
fontes, gravação e contrato da implementação. A imagem de xícara ainda é uma
solicitação futura; o pacote não contém uma imagem gerada nem um vídeo pronto.
A exportação não consumiu chamadas, créditos ou renderização.

Regularizar os créditos disponíveis para a credencial de API configurada antes
de qualquer nova execução. A autorização desta rodada excluiu tentativas extras;
não repetir automaticamente após regularizar o saldo. A recuperação paga por
etapa não tem endpoint implementado nesta fatia. As melhorias da referência
Maestros permanecem para depois da comparação, conforme orientação do titular.

Verificações desta rodada: executor sintético, admissão API, workflow real,
validação do plano, preflights de custo e exportação idêntica por hash. Sem
alterações de produção neste acompanhamento, sem repetição de CI ou dos 473
testes dirigidos já registrados na implementação. Não há declaração de CI
integral aprovado.

## Nova tentativa após reposição de créditos

Titular confirmou que estava sem créditos, informou reposição e solicitou tentar
novamente. Comunicada execução completa pelo fluxo existente, com teto desta nova
tentativa US$ 3 e reservas máximas US$ 2,75. Não há reutilização de autorização
antiga sem novo pedido; tampouco liberação das reservas anteriores. A retomada
parcial do plano não é implementada por scripts ou alterações manuais do banco.

Pasta `.local/evals/motion-staged-retry-20261111/`. Gravação, briefing, direção e
12 imagens idênticos à tentativa anterior; executor sintético verificado. Banco
de desenvolvimento existente e fila Temporal exclusiva. Pedido
`f9a58258-0c49-576f-ac3f-d9cf315495ab` admitido pela API (202) e despachado.
Uma tentativa por etapa, sem refações. Workflow concluído em 879,56 s (14 min 40 s).


## Resultado da nova tentativa

Pedido concluído (`completed`) com peça
`c5839138-a362-5667-819f-01f0247dc912` e uma versão. Planejamento e implementação
retornaram `status=completed`, JSON válido e preservação do plano por hash.
Planejamento: 35.395 tokens de entrada / 12.827 de saída (6.545 reasoning).
Implementação: 43.440 / 19.700 (13.215 reasoning), 19.215 caracteres completos;
HTML 8.377 e scene_init 10.724 caracteres. Ambos com teto de saída 54.000.
A conclusão do código foi efetivamente verificada nesta tentativa, não apenas
inferida de uma redução do prompt. A causa raiz das interrupções históricas não
é demonstrada por esse sucesso.

Uma imagem de xícara foi gerada e integrada. Render: H.264, 720×1280, 30 fps,
336 quadros, 11,2 s; faixa AAC de 11,176009 s. MP4 SHA-256:
`187b611018d2b24c27edb99f07a4a21aecd5599e7333a64ad1b227147df0c451`.
Correlação do áudio mono 16 kHz sem deslocamento: 0,9999884744, comparando os
178.817 samples comuns. A fonte decodificada tem 178.827 samples, diferença de
10 samples (0,625 ms) compatível com a medição/recodificação, sem alegação de
igualdade binária. Isso é evidência de preservação do sinal, não escuta humana
nem garantia perceptiva de sincronismo.

### Comparação e observações visuais

Abrir `.local/evals/motion-staged-retry-20261111/comparacao.html` no navegador;
os controles reproduzem a versão anterior e a nova, com seleção de áudio.
`v0.mp4` abre diretamente no player. `LEIA-ME.txt` contém instruções de uso.
Nenhuma credencial é necessária para assistir. Recibos privados não devem ser
compartilhados junto do vídeo sem revisão.

Nos quadros inspecionados, a gravação tem moldura arredondada clara/cobre, campo
verde e mudança de escala no retorno. O fundo passa a motion pleno verde com área
papel e depois retorna a uma margem lateral. A xícara tem aparência fotográfica,
com sombra e reutilização menor no encerramento; continua sendo imagem conceitual
em camadas 2.5D, sem geometria 3D ou documentação do produto do cliente.

Extraídos nove quadros adicionais do MP4, sem rerender, para conferir passagem
à cena gráfica, chegada da xícara e retorno. Há pontos a refinar: em aproximadamente
3,967 s, a sobreposição do texto Uma pausa. e da moldura deixa um recorte retangular
papel visível; em 8,767 s, o filete cobre cruza a gravação e a xícara a sobrepõe
parcialmente durante a transição. O estado central em 5,6 s tem bastante espaço
vazio antes da xícara; ritmo ainda contido. São observações de acabamento, não
correções aplicadas silenciosamente. Evidências em `transitions/` e
`manual-inspection.json`. Não houve segunda versão.

A comparação anterior não isola uma única mudança: textos e direção já haviam
sido adaptados à fala durante as quatro melhorias. A mesma fonte e kit permitem
avaliação visual, mas não um experimento controlado de ganho por componente.

### Crítica e limites

Crítica automática `adequate`, sem issues; preferência A/B `undetermined`, pois
ela recebeu somente a nova versão e a fonte. Não afirmar que o modelo confirmou
superioridade contra a anterior. Cobertura temporal: três de 49 eventos,
concentrados em Sinta; demais estados aparecem em amostras esparsas. A própria
crítica registra ausência de escuta e limites para trajetórias, fluidez, timing
e ausência de flashes. Os quadros extras desta inspeção não foram enviados para
uma segunda crítica paga. Aumentar a representatividade das amostras é uma
pendência de qualidade para a próxima discussão, sem nova implementação agora.

### Custos e encerramento

| Etapa | Estimativa US$ | Reserva US$ |
| --- | ---: | ---: |
| Planejamento | 0,216758 | 0,75 |
| Implementação | 0,305600 | 0,75 |
| Imagem | 0,015050 | 0,50 |
| Crítica | 0,200565 | 0,75 |
| Total desta tentativa | 0,737973 | 2,75 |

Teto desta tentativa US$ 3. Estimativas seguem a política de custo configurada,
não uma fatura. A rodada anterior permanece com estimativa conhecida US$ 0,225920
e reservas US$ 1,50, sem uso informado para sua rejeição por crédito. Entre as
duas, estimativa conhecida US$ 0,963893 e reservas US$ 4,25, em autorizações de
tentativas separadas; não houve liberação manual para fazer a conta caber.

Worker exclusivo e monitor encerrados; cinco serviços em falha mantidos parados.
Sem publicação, aceite criativo humano, chamadas extras ou refações. Banco de
desenvolvimento existente, sem migração/limpeza ou banco temporário nesta execução.
Verificações: admissão/Temporal reais, preflights, JSON e hash do plano, renderer,
armazenamento por hash, MP4/áudio, quadros e crítica. Não houve mudança de produção
nem nova bateria de testes/CI nesta tentativa. Próximo passo: avaliação visual
do titular antes de priorizar as melhorias da referência Maestros.


## Feedback do titular e encaminhamento

Após assistir, o titular percebeu mais trabalho, mas manteve avaliação abaixo do
acabamento desejado: bordas sem sentido na composição, xícara realista agradável
porém sem expressividade/impacto. O verdict automático não é aprovação criativa.
Reanálise da referência e das seis frentes propostas em
`docs/design/motion-qualidade-direcao-e-gaps-2026-11-11.md`, incluindo direção,
asset recebido depois do código e cobertura temporal insuficiente. Nenhuma nova
peça ou correção foi realizada em resposta a esse feedback; próxima fatia proposta
é direção/repertório e revisão representativa.
