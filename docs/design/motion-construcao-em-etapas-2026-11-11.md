# Construção de motion em duas etapas

Data: 11/11/2026. Escopo autorizado: resolver a fragilidade que impediu a última
peça. As melhorias extraídas do vídeo Maestros ficam para um próximo plano.

## Problema e limite do diagnóstico

As três respostas anteriores chegaram com `status=incomplete`, motivo
`max_output_tokens` e `scene_init` interrompido. Plano, HTML e JavaScript eram
uma única saída indivisível. A API reportou menos tokens usados que o teto
solicitado; a causa raiz dessa divergência continua sem comprovação. Não atribuir
a falha a modelo incapaz, Docker, falta de referências ou orçamento esgotado.

A mudança elimina o acoplamento entre plano e código na mesma completion. Isso
é uma correção estrutural verificável localmente, não prova de conclusão real pela
API. Nenhuma string parcial das respostas antigas é completada ou executada.

## Contrato implementado

Novas capturas com direção fornecida usam `provided-direction-output-v3`.
Recapturas preservam v1/v2; pedidos sem direção fornecida mantêm seu fluxo anterior.
A direção visual já separada continua sendo entrada autoritativa.

1. **Planejamento:** uma chamada devolve `concept`, `source_usage`, `audio`,
   `illustrations` e `motion_plan` compacto. O servidor expande os beats, restaura
   a direção e preserva um `MotionConstructionPlan` completo, sem código executável.
2. **Validação intermediária:** duração, assets, direção, elementos, tempos da
   fala, áudio original, declarações de imagem e momentos de storyboard passam
   pelas validações existentes antes da segunda chamada.
3. **Implementação:** outra chamada recebe o plano completo e seu SHA-256 e
   devolve somente `plan_sha256`, `html` e `scene_init`. Campos extras ou hash
   divergente são rejeitados. O servidor monta a composição usando os metadados
   preservados, sem pedir que o modelo os repita.
4. **Fluxo posterior:** imagens, storyboard/render e crítica seguem os controles
   atuais. A igualdade dos metadados não comprova que o código executa cada
   movimento: sandbox, render e crítica continuam necessários.

As correções criativas posteriores à crítica ainda usam uma resposta completa
compacta v2; esta fatia divide a geração inicial que bloqueou a comparação. Não
há looping, troca automática de modelo ou novas tentativas implícitas.

## Persistência, orçamento e compatibilidade

`construct_motion` usa o `MotionEffects` existente. Plano e implementação têm IDs
duráveis distintos: `uuid5(operation, "generate:plan:0")` e
`uuid5(operation, "generate:0")`, ambos com kind `generate`. Cada envio conserva
claim, payload privado, reserva compartilhada, resposta cifrada e custo. Não
há rede sob locks, tabela nova ou runner adicional; Temporal continua responsável
pela execução.

Antes de planejar, exige capacidade para três reservas de modelo: plano,
implementação e crítica. Após o plano, verifica novamente implementação, crítica
e imagens declaradas. Os tetos individuais e a contagem exata de entrada continuam
no preflight. Dividir chamadas não autoriza aumentar o orçamento do pedido.

Se a implementação falhar, o recibo completo do plano permanece salvo. O pedido
para; não há reinício automático de operação falha ou incerta. Esta fatia não cria
um endpoint de retomada paga. Um novo envio exige autorização própria; a persistência
é a base para uma retomada explícita futura, não autorização para realizá-la.
A reconciliação existente de storyboard já recebido reconhece o par de recibos
e exige igualdade com o plano, sem efetuar geração/render novamente.

`request_bytes` preserva a ordem do schema, enquanto `digest/canonical` continua
ordenando dados para identificação. A reserva inclui `wire_sha256` para também
vincular a ordem efetivamente enviada. Preflight e envio conferem os mesmos bytes.
A documentação oficial confirma que a ordem das propriedades influencia a ordem
da saída; isso não prova que a ordenação tenha causado o limite anterior.
[Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs).

## Exportação e preparação da comparação

O exportador usa o mesmo builder do adapter e identifica `plan`, `implementation`
ou `complete` no manifesto. Schema e prompt legível preservam a ordem do payload.
Para a segunda etapa, `--plan-output caminho/plano.json` valida um JSON completo
de planejamento, confere áudio/assets/direção e exporta a implementação. Não
completa JSON truncado, não faz chamadas nem executa a resposta externa.

Entrada local preparada para a mesma comparação:
`.local/evals/motion-staged-construction-20261111/planning-input/` e ZIP adjacente.
Inclui `PROMPT-INTEGRAL.md`, JSON, schema, contexto, bibliotecas, fonte e 12 imagens.
Igualdade binária das 12 imagens com a tentativa anterior conferida. Preservados
gravação, kit, direção, imagem conceitual declarada e fala automática não revisada.
O pacote é uma proposta offline; valores de políticas anteriores não são uma
nova autorização de gasto. `input-check.json` registra zero chamadas e zero render.

## Validação

Os testes dirigidos cobrem duas completions, ordem no preflight/envio, montagem
imutável, contratos históricos, orçamento insuficiente, plano inválido, perda de
resposta, falha de armazenamento, ausência de retry, exportação e reconciliação.
473 testes dirigidos passaram em 10,99 s. Cobertura de linhas e ramos de 100%
nos seis módulos medidos: adapter motion_ai, schema motion_generation, serviços
motion_generation, motion_construction, motion_effects e motion_storyboard_recovery.
Mypy passou nos 15 módulos de produção verificados; Ruff e diff-check aprovados.

Foram executados 23 testes de integração com sucesso, incluindo dois novos testes
com PostgreSQL restrito que verificam o recibo do plano comprometido antes da
implementação e sua preservação quando o código falha. A execução mais ampla
parou num teste do Temporal por conexão recusada em 127.0.0.1:7233. Não equivale a
CI integral aprovado ou prova do workflow real com o provedor.

## Bancos e orientação do titular

O banco dedicado de testes existente está na revisão `0076_reference_provider_guard`
e tem divergência com a migration 0075 (`is_primary` ausente). A tentativa de
upgrade transacional desse banco falhou antes de criar as tabelas de motion.
Não foi corrigido por alteração manual de schema.

Um banco temporário vazio foi criado antes da nova orientação do titular. Suas
migrações completas passaram e nele rodaram os testes descritos acima. Quando o
titular pediu para não usar banco temporário, a execução já estava terminando;
ao tentar interrompê-la, não havia processo ativo. O banco criado foi removido
pelo finally. Nenhum outro banco temporário será criado para esta tarefa.

O titular autorizou atualizar desenvolvimento caso necessário. A consulta mostrou
que `meu_braco_direito_platform` já está na revisão atual
`0116_motion_failure_identity`, com `motion_requests`, `motion_effects`,
`motion_storyboards` e a coluna de referências presentes. Nenhuma migração era
pendente; dev não foi modificado nem usado pelos testes que limpam dados.

## Prova real e pendência — 11/11/2026

Titular autorizou nova rodada exclusiva até US$ 3, com reservas máximas US$ 2,75:
planejamento, implementação, uma imagem e crítica, sem tentativas extras. Pedido
81eaf22e-d32b-5c67-b2d7-5593059e7a7d executado pela API/Temporal no dev existente.

O planejamento retornou JSON completo, passou nas validações e ficou preservado:
3 cenas, 18 elementos, 36 beats, uma imagem declarada. A implementação passou no
preflight de custo e recebeu recusa do provedor: insufficient_quota /
credit_balance_exhausted. Não houve nova saída truncada, imagem, render da peça
ou crítica. O teste comprova a primeira etapa e a preservação do plano diante da
falha seguinte, mas não a conclusão do código nem o acabamento visual.

Estimativa conhecida US$ 0,22592; reservas US$ 1,50 mantidas. A recusa não trouxe
usage, portanto não atribuir custo zero comprovado nem confundir reserva com
fatura. Worker exclusivo encerrou; cinco serviços mantidos parados. Nenhuma
repetição automática. Regularizar os créditos da credencial configurada antes de
considerar nova execução; esta autorização excluía tentativas adicionais.

Entrada da implementação exportada offline pelo mesmo builder, com SHA-256 dos
bytes igual ao recibo da chamada recusada, plano validado e 12 imagens. Pacote em
`.local/evals/motion-staged-construction-20261111/implementation-input/` e ZIP
adjacente. A imagem de xícara está apenas declarada, ainda não gerada. O pacote
não é MP4 nem endpoint de retomada automática. Relatório completo em
`docs/evals/comparacao-construcao-em-etapas-2026-11-11.md`.


## Prova completa após reposição de créditos

O titular confirmou reposição e pediu nova tentativa. Pedido
f9a58258-0c49-576f-ac3f-d9cf315495ab executou o fluxo completo sem refações:
planejamento e implementação completos, imagem, render e crítica adequada.
Resultado de 11,2 s disponível em
`.local/evals/motion-staged-retry-20261111/v0.mp4`, com comparação HTML ao lado.
Estimativa US$ 0,737973, reservas US$ 2,75 no teto desta tentativa US$ 3; recibos e
reservas da tentativa recusada preservados separadamente. Isso qualifica a
conclusão real do contrato v3 nesta peça, sem provar a causa das falhas históricas
nem generalizar acabamento comercial. Sobreposições nas transições e cobertura
temporal restrita da crítica ficam registradas para avaliação, sem refação paga.
Detalhes em `docs/evals/comparacao-construcao-em-etapas-2026-11-11.md`.
