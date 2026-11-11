# Plano do primeiro ciclo de revisão de Reel

Estado em 08/11/2026: **protótipo implementado; críticas v2 de Dog/Luma concluídas sem correções; prova comparativa e avaliação humana desse trio pendentes**. Plano original de 06/11/2026. O objetivo é testar se uma crítica fundamentada
no arquivo renderizado e correções limitadas melhoram um Reel em comparação
com sua própria versão inicial. O [contrato e critérios v1](../design/ciclo-revisao-motion-2026-11-06.md)
são a referência do ensaio. A primeira execução gerou três críticas reais e
terminou sem correções; auditoria posterior detectou contexto criativo incompleto,
conforme registro abaixo. O titular autorizou esta rodada específica, conforme abaixo.

## Continuação independente — resultado de 08/11

Run `4338880a-10f2-48a7-96cd-54138f87dbdd` terminou em
`completed_partial_human_pending`. Somente Dog/Luma eram elegíveis: receberam
críticas com contexto criativo v2, ambas `adequate`, sem achados acionáveis ou
correções. Intensa e sua operação incerta anterior ficaram bloqueadas, sem
retry. Pedidos, respostas, versões e ledger foram preservados.

O plano independente permitia até seis novas chamadas — crítica inicial,
correção somente se justificada e crítica final por caso — com teto planejado
de US$ 3,50 em reservas acumuladas. Foram usadas duas chamadas, US$ 0,1751650
estimados e US$ 0,50 reservados. Acumulado de toda a revisão: seis tentativas,
US$ 0,4272150 conhecidos e US$ 1,50 em reservas. Custo da operação incerta
`2b9fa3ad-c4c1-4bd1-8490-daf573fbf339` ainda desconhecido. O orçamento original
de até 15 chamadas/US$ 6,75 permanece como limite, não meta ou fatura.

O [resultado e relatório](ensaio-ciclo-revisao-motion-2026-11-06.md) não demonstram
A/B, correção de defeito ou ganho. A etapa 3 continua aberta e a integração não
está liberada por esse resultado. O titular escolheu em entrevista testar a
correção do [Reel histórico 1c com defeito conhecido](plano-revisao-reel-1c-2026-11-08.md).
O pacote offline preserva 69 arquivos e dez normalizações históricas; a ponte
para o contrato declarativo está implementada e qualificada. O titular autorizou
em entrevista própria até três chamadas/US$ 1,25 e envio à OpenAI; a execução
paga do 1c concluiu três respostas, v1 e crítica final favorável, ainda com
melhora de legibilidade reconhecida pelo titular e motion questionado, sem
aceite global. O [resultado separado](ensaio-revisao-reel-1c-2026-11-08.md)
registra US$ 0,527685 estimados novos; não altera os custos ou a incerteza do trio.
A falha de unidades já foi corrigida na geração atual, e esta reparação específica
não prova ganho criativo ou retorno financeiro geral. Não alterar casos ou fabricar defeitos para forçar
uma correção; críticas sem falha relevante preservam o original.

## Histórico: primeira execução e continuação delimitada

As três críticas reais retornaram `adequate`, sem solicitar correções. Custo
estimado observado **US$ 0,2520500**, não fatura; reservas **US$ 0,75**.
A auditoria posterior identificou que o contexto do crítico omitiu
`creative_direction_proposal`, `user_feedback`, `own_skill` e instruções
criativas originais. Portanto, esse resultado verifica o funcionamento do
ciclo apenas com entrada incompleta: não comprova que as peças não precisem de
ajuste nem ganho ou qualidade do crítico. Preservar pedidos, respostas, decisões,
reservas e artefatos originais sem os reclassificar.

A continuação explícita corrigiu a preparação do contexto e manteve a ligação à
primeira execução: `c1c45556-adab-4694-8495-1fcd327b9624` é o primeiro run,
e `87acffe2-12ef-488d-921e-8f1745691d1f` é a continuação preparada offline.
Dentro da autorização original de até 15 chamadas/US$ 6,75, o novo
limite operacional é **até nove chamadas e US$ 3,75 em reservas adicionais**:
para cada caso, até uma nova crítica, uma correção quando justificada e sua
crítica final. Isso soma, no máximo, **12 chamadas e US$ 4,50 em reservas**
nas duas etapas. O teto é limite, não meta; falhas incertas não autorizam retry.
A continuação foi iniciada e parou na primeira crítica de Intensa: operação
`2b9fa3ad-c4c1-4bd1-8490-daf573fbf339` terminou `uncertain` com
`transport_or_recording_failed`, sem `response.body`. Não houve crítica v2
disponível ou peça derivada. O acumulado é **quatro chamadas**, estimativa
conhecida **US$ 0,2520500** das três anteriores, custo da quarta desconhecido
e **US$ 1,00 em reservas** naquele ponto. O saldo da autorização original não
demonstra custo efetivo nem autoriza reenvio após resultado incerto. Essa
execução parou sem retry; a continuação independente posterior está registrada
acima. Comparação A/B, ganho e avaliação humana seguem pendentes.

## Caso e comparação

- Usar três composições históricas sintéticas com MP4, assets, resposta, cenário
  e configuração verificáveis por hash: Intensa
  `b14bc09d-4131-4018-b666-1f9d0fff8651`, Dog e Luma do
  [lote original](ensaio-motion-outros-negocios-2026-11-06.md). Para Dog,
  preservar a tradução documentada de IDs de áudio e a resposta original; o
  render offline é a versão efetivamente apresentada. Verificar linhagem,
  integridade, direitos e disponibilidade das ferramentas no preflight. O MP4
  real, resposta, código, trace e hashes originais são preservados; o preflight
  não re-renderiza v0 e não comprova reprodução bit a bit. Ausência de evidência
  interrompe o caso, sem fabricar equivalência ou substituir caso sem nova definição.
- **A:** preservar o MP4 e composição inicial histórica. **B:** partir da mesma
  composição, insumos e configuração, revisar e renderizar os derivados.
  Assim a variável investigada é o processo de crítica e correção; há
  não determinismo e uma única peça não estabelece efeito geral.
- A trilha original permanece igual na comparação principal para não misturar
  variáveis. Seleção entre faixas licenciadas permanece uma prova separada antes
  da integração. Não confundir preservação de uma trilha com validação da escolha.
- O pacote deve incluir critérios `motion-review-v1`, fatos e materiais, quadros
  e tempos da versão correspondente, medições e o que o crítico recebeu. O
  áudio será verificado tecnicamente; não será enviado para crítica perceptiva.
  Escuta humana é explícita e necessária para a avaliação de som. Anotar trechos
  não observados; não inferir qualidade auditiva por medições.

## Execução prevista

1. O CLI privado `scripts/evals/motion_review_eval.py` prepara snapshots e
   evidências offline, com entrada e rubrica versionadas, persistência por
   operação e relatório. Reaproveita o executor de ensaio e não integra o produto.
2. Inspecionar A e produzir crítica com achados rastreáveis. O contrato geral
   permite até duas correções; a continuação desta rodada foi limitada a uma
   por caso, identificada e orçada antes da chamada; renderizar e
   criticar cada resultado, inclusive o último. Só corrigir uma falha concreta,
   relevante, sustentada por evidência e corrigível; parar diante de crítica
   incerta, preferência apenas estética, falha ou evidência insuficiente. A
   segunda correção exige preferência fundamentada do crítico pela primeira e
   falha relevante e corrigível restante; sem essa evidência, parar. A preferência
   automática é provisória e não substitui a escolha humana final.
3. Conservar os MP4s, pedidos/respostas, código, evidências, custos e tempos de
   cada etapa; montar comparação A e derivados para o titular. Não sobrescrever
   a fonte, escolher a última como melhor ou usar falha técnica como nota criativa.
4. Avaliação humana explícita no celular, preferencialmente sem identificar as
   versões durante o julgamento: preferência e motivos por critério, aceitação,
   rejeição e problemas não verificáveis. Pode haver empate ou regressão.
   Informar custo total conhecido e desconhecido, tempo, número de chamadas,
   renderizações e intervenções; estimativa não é fatura.

O titular autorizou enviar quadros, contexto e código à OpenAI para os três
casos, até **15 chamadas e US$ 6,75 em reservas**: por caso, até três críticas
de US$ 0,25 e duas correções de US$ 0,75, total de US$ 2,25 por caso. Não há
obrigação de usar todas as chamadas: o teto não é meta. Medir se o ganho
observado justifica custo e tempo adicionais. Achados recorrentes podem orientar
melhorias no briefing inicial, mas esse braço não terá resultado sem ensaio
próprio. Antes de cada efeito, registrar operação,
modelo/configuração, pacote e reserva dentro do teto; exigir credenciais
explicitamente configuradas. Tetos antigos não se renovam. Cada tentativa tem
identidade e reserva antes da rede;
timeout ou resposta perdida conserva estado e reserva sem retry automático.
Reserva limita a admissão, não garante teto da cobrança do fornecedor.

## Comandos

Preparar os três casos offline, sem chamada de API:

```sh
make motion-review-eval
```

O comando abaixo registra como a continuação foi iniciada. O run está parado
com efeito incerto e **não deve ser reenviado**:

```sh
make motion-review-eval EXECUTE=1 REVIEW_BUDGET_USD=6.75 REVIEW_RUN=.local/evals/motion-review-runs/87acffe2-12ef-488d-921e-8f1745691d1f
```

A continuação independente `4338880a-10f2-48a7-96cd-54138f87dbdd` também já foi
iniciada e encerrada parcialmente: não reenviar esse run para tentar obter
correções. Seu relatório é a saída dessa execução, não um pedido pendente.

O orçamento de US$ 6,75 foi o valor efetivamente usado no comando, conforme
`started.json`; o plano adicional previa máximo acumulado de US$ 4,50 em
reservas, incluindo as reservas de US$ 0,75 da primeira execução. O executor
conserva operações e bloqueia repetição de execução já iniciada ou
incerta. Os artefatos e
relatório ficam privados em `.local/evals/motion-review-runs/`.

## Saída e limites

Saída esperada: critérios versionados, protótipo testado offline, comparação
real A/B rastreável e julgamento humano registrado. Não há promessa antecipada
de melhora, integração, qualidade comercial ou publicação. Ensaios usam fontes
permitidas e não conteúdo de cliente. O confinamento atual de Chromium não prova
isolamento de SO; qualquer ampliação para material real depende de qualificação
própria. Testes de banco, se houver futuramente, usam banco dedicado `_test` e
roles restritas. CI e validação da implementação serão registrados conforme sua
execução, sem reaproveitar resultados históricos como prova da nova fatia.
