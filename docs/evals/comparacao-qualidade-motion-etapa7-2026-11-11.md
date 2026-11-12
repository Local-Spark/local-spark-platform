# Etapa 7 — rodada autorizada de qualidade motion

**Análise comparativa posterior:** o titular identificou as duas peças da
comparação de 11/11 (“Anterior” e “Nova — quatro melhorias”) como referências de
que gostou. A perda de sete elementos já estava na direção da etapa 1; os
payloads não incluem composição anterior apesar da base anexada ao pacote.
A espera de 2,52 s descrita abaixo já era de 2,56 s na base fotográfica: não é
causa nova suficiente. O preenchimento da xícara já não existia nessa base aceita.
Diagnóstico causal, diferenças visuais e retificações:
[`diagnostico-regressao-motion-2026-11-11.md`](diagnostico-regressao-motion-2026-11-11.md).

Data: 11/11/2026. Storyboard entregue e reprovado visualmente pelo titular.
Sem autorização para avançar ao MP4. O estado persistido continua
`awaiting_approval`; esta atualização registra o feedback, sem decisão terminal
pela API ou alteração dos recibos da rodada.

## Retorno do titular e diagnóstico posterior

O titular considerou o resultado horrível e descreveu a sequência percebida:
vídeo com “Sinta o cheiro”, saída do vídeo, “Uma pausa”, entrada da xícara e fim.
Essa avaliação reprova a concepção visual, não apenas a sombra ou um quadro da
transição. A avaliação anterior do assistente destacou problemas secundários e
não deu peso suficiente à estrutura genérica da composição.

Confronto com o plano efetivamente recebido:

- A gravação tem recuo de apenas 4% e 18 px; depois desaparece por opacidade
  entre 3,680 e 4,260 s. O gesto real não conduz a uma transformação visual clara.
- “Uma pausa” entra entre 4,120 e 4,500 s; a xícara só começa a surgir em 6,780 s.
  Há aproximadamente 2,52 s entre o fim previsto da gravação visível e o início
  da xícara. Nesse intervalo, o plano oferece título, pequenas mudanças do fundo
  e uma elevação de texto, percebidos como cartela de espera.
- A entrada da xícara combina opacidade, escala 0,94→1 e deslocamento curto;
  segue-se assentamento de 18 px. Isso não materializa, por si só, uma ideia visual
  forte para a fala. A saída e o retorno usam novas dissoluções.

A entrada verificada por hash comprova o envio da direção e das referências,
mas não seu bom aproveitamento. O plano passou nos contratos estruturais com
descrições de coordenação; isso não assegurou uma relação perceptível de causa
e consequência entre gravação, objeto, fundo e texto. A fraqueza já está no
plano, antes do código. Os quadros não comprovam toda a animação, mas são
suficientes para identificar a composição que o titular rejeitou; não exigir
render ou nova crítica paga para reconhecer esse problema.

Revisão necessária: repensar o encadeamento visual antes de outra execução.
Para este caso, uma hipótese é manter o gesto filmado presente durante a
preparação da pausa e transferir o foco à xícara conceitual em uma passagem
contínua, com transformação visível do espaço e consequência na disposição do
texto. Eliminar a longa espera entre a saída da gravação e a entrada do objeto.
Isso é hipótese para revisão, não nova direção aprovada nem regra universal.

A correção delimitada da etapa 6 preserva o plano: não resolve uma mudança dessa
estrutura narrativa. Não consumir o saldo autorizado como permissão implícita
para replanejar, gerar outra imagem ou repetir chamadas. Nenhuma chamada paga,
renderização, mudança de código, banco ou serviço foi feita para este diagnóstico.
Etapa 7 continua aberta, agora com reprovação criativa explícita.

## Autorização e limites

O titular respondeu **Sim** à proposta com reserva máxima **nova de US$ 6,75**,
uma imagem conceitual e até uma correção delimitada com nova crítica. Manteve
somente a gravação original no áudio. A execução deve parar no storyboard:
aprovação do orçamento não é aprovação do storyboard nem permissão para produzir
o MP4 antes dessa decisão. Não há etapa 8 no contrato vigente.

Autorização local em `.local/evals/motion-qualidade-etapa7-20261111/approval.json`,
vinculada ao manifesto da proposta
`518cb8be6a6666ffaf6c5868df7fb606e56e7355db6261b9a00b77c814674e57`.
Mantidos os limites por efeito: US$ 1,25 por chamada de modelo e US$ 0,50 pela
única imagem. Até o storyboard, são duas chamadas de modelo e uma imagem, com
reserva máxima de US$ 3,00. As reservas históricas não foram liberadas/reutilizadas;
o teto da rodada está no pedido e o ledger existente registra cada efeito.

## Admissão e executor

Executor isolado fixado em
`sha256:59c6229282fc8ba5cbf52c84321a260e8e5a94f37e373025ce0ca9ede733e449`.
Verificação sintética 64×64: dois quadros com fingerprints e MP4 de 1.886 bytes;
segunda execução somente de quadro, sem MP4. Não usou conteúdo do cliente.
Recibo: `executor-check.json`. Isso comprova funcionamento técnico, não qualidade
visual, voz ou ausência de regressão na futura peça completa.

Admissão fresca no PostgreSQL e armazenamento existentes confirmou fonte, kit,
áudio autorizado e saída iguais à proposta: 11.200 ms, 720×1280, 30 fps, seis
quadros da fonte e cinco referências. Fonte SHA-256
`dd3f0265a4b2d94206188f46c094dc0177663e1a529b9ad2e0718a1dfad78a34`.
Contratos de geração, direção, revisão, correção e imagem também conferidos.
`admitted-input/` é a projeção anterior ao novo ASR local; recibos executados
devem ser confrontados separadamente. O montador real produziu a entrada.

Pedido `43986daf-f509-55b6-b0b4-085782c4b297`, admitido pela API com HTTP 202,
despachado pelo outbox para o workflow Temporal existente com fila exclusiva.
Sem novo serviço, tabela, migração, banco temporário ou teste destrutivo.
Nenhum serviço anteriormente interrompido foi iniciado ou reconfigurado.
O worker dedicado executou somente a fila nova, sem retries de efeito, e encerrou.

## Resultado e limitações

Workflow terminou em `awaiting_storyboard` após 423,35 s. A API retornou a galeria
e os metadados com HTTP 200. Storyboard `awaiting_approval`, versão
`8772e91f-d939-5241-9635-c3b611ade5e5`, conteúdo SHA-256
`078dfaf1ae439559f1a26a1f7eafe1c7c0ee331f3a9b1a345eaca775be4d69f3`.
Nenhuma decisão ou evento `motion.storyboard_approved` foi registrado. O pedido
permanece `running` por convenção do produto enquanto aguarda a decisão; workflow
Temporal está `COMPLETED` e o worker dedicado encerrou. Sem `piece_id` ou MP4 novo
do cliente. Recibos: `workflow-result.json`, `result.json`, `final-checks.json`.

Galeria local: `.local/evals/motion-qualidade-etapa7-20261111/storyboard.html`,
obtida pelo endpoint real, com 18 PNGs verificados. São três quadros principais
e três sequências de cinco quadros: duas passagens e a entrada da xícara. O
manifesto declara 24 de 27 eventos omitidos, nenhuma passagem omitida e nenhuma
cena sem janela. `complete=true` significa presença dos quadros solicitados,
não comprovação da ação integral. A primeira janela termina em 3,800 s, enquanto
o código prevê fade da gravação até 4,260 s; a janela de retorno termina em
8,967 s, antes do fade previsto até 9,340 s. Esses limites de amostragem devem
continuar explícitos na crítica futura.

Inspeção dos 18 quadros: texto legível e hierarquia simples, gravação sem borda
verde/cobre decorativa, xícara fotográfica recortada e retorno ao gesto real.
Ressalvas visuais: sombra difusa pode sugerir flutuação mesmo no repouso em
8,100 s; o retorno contém um quadro somente de fundo em 8,833 s. O impacto dessa
passagem depende da reprodução contínua. Não houve escuta, comparação lado a
lado em movimento, nota criativa ou aprovação humana. A presença de 18 quadros
e o sucesso do executor não demonstram acabamento ou sincronismo.

## Chamadas efetivas, materiais e custos

Planejamento e implementação usaram `gpt-6.1-sol`, reasoning high, limite de
54.000 tokens. Cada entrada foi reconstruída pelos builders reais e comparada
ao `wire_sha256` persistido antes do envio. Arquivos na pasta desta rodada:

| Etapa | Entrada | SHA-256 | Tokens entrada/saída |
| --- | --- | --- | --- |
| Plano | `planning-input.json` | `839b7c298619aa931e57714caa3a7f5bb5be0305949dc50318216a178100d57a` | 35.500 / 8.393 |
| Implementação | `implementation-input.json` | `126239ec96413ca39b87533cef631aef917ccc420d8c9a64bb6b3b6aba4e23b7` | 40.532 / 8.342 |

Pacotes legíveis e ZIPs adjacentes reúnem textos, schemas, anexos e execução,
com nota de reconstrução posterior: não são autorização para repetir chamadas.
Ambos passaram em `motion_external_export --verify`. A transcrição local nova
coincidiu com a proposta; continua automática, não revisada por pessoa. A imagem
autorizada foi gerada uma única vez, validada e armazenada antes da implementação;
o preview verificado foi incluído na segunda entrada. O material representa uma
xícara conceitual, não fotografia documental do produto do negócio.

| Efeito | Reserva US$ | Estimativa pelo recibo US$ |
| --- | ---: | ---: |
| Plano | 1,25 | 0,172680 |
| Imagem | 0,50 | 0,015035 |
| Implementação | 1,25 | 0,184750 |
| Total até o storyboard | **3,00** | **0,372465** |

O ledger preserva as três reservas como `uncertain`, com `actual_usd_micros=null`:
há recibos recebidos, mas não confirmação de fatura. Não liberar nem confundir
estimativa com gasto liquidado. Restam até US$ 3,75 do teto da rodada para crítica,
eventual correção e crítica seguinte, respeitando todas as condições originais.
Não houve crítica paga, correção, imagem extra, retry ou aprovação automática.

## Pendências e validação

O próximo passo depende da decisão explícita sobre este storyboard. MP4, escuta,
crítica, eventual correção e comparação lado a lado continuam pendentes. A etapa
7 permanece aberta e a melhora visual não foi validada. Nenhuma etapa 8 existe
neste contrato; não se iniciou trabalho adicional.

As alterações anteriores do titular permanecem no índice. Esta rodada acrescenta
recibos locais e documentação, sem substituir a implementação das etapas 1–6.
CI integral e cobertura de 100% não foram executados nesta rodada operacional.
Passaram: qualificação sintética do executor, admissão/invariantes, reconstrução
das entradas por hash, verificação dos dois pacotes, checks finais de estado e
`git diff --check`. A consulta final Docker ficou em `container-status-final.json`;
não houve ação de iniciar/reiniciar serviços. Não se alterou código de produção
nesta continuação; scripts e recibos operacionais ficam em `.local`.
