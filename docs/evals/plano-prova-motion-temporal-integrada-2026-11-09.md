# Prova integrada dos passos 1–3 de motion — 09/11/2026

Estado: tentativa interrompida por saída truncada; nenhuma versão renderizada.
Zero chamadas à OpenAI, inclusive contagem, durante o preparo.

## Comparação concreta

A é a última geração do Café Pausa, avaliada como melhora parcial, ainda abaixo
do acabamento esperado. SHA-256:
`82c11f885ce4879fc6e6b28621d142d9bdd5d2c6987c942f2b63809a2ae6536e`.
B será nova geração com a mesma gravação, kit, briefing, modelo e limites de saída,
acrescentando plano temporal, API `MotionV1` e crítica temporal implementados.
C somente se B apresentar problema maior acionável e houver orçamento.

A/B mede a combinação das mudanças e a variabilidade da geração, não o efeito
isolado da autocrítica. Se houver C, B/C mostra a correção condicional. A anterior
é preservada e comparada pelo titular; não será reenviada ao crítico como uma
versão desta operação. Não se presume equivalência aos Reels externos.
Calibrações são textuais; não enviamos quadros externos de referência nem
importamos suas cores/fontes/assets. O kit continua sendo o do Café Pausa.

Gravação de preparo de café, 11,2 s finais, preservando sequência e áudio.
SHA de origem: `dd3f0265a4b2d94206188f46c094dc0177663e1a529b9ad2e0718a1dfad78a34`.

## Preparo e execução

- Banco dev existente autorizado, sem migração/limpeza. Pedido fictício novo
  `6f9e9e90-cde0-5706-9154-339ec66e9884`, admitido pela API autenticada (202).
- Temporal local `localhost:49805`, já autorizado, com fila própria. Serviços
  existentes não serão parados; encerraremos somente o worker desta rodada.
- Worker atualizado por cópia de `app` sobre a imagem previamente qualificada,
  sem rede ou aquisição de dependências; 14 arquivos/importação conferidos sem
  credenciais. Renderer isolado existente e inalterado, com prefixo `MotionV1`
  incluído pelo adapter e protegido pelo hash do snapshot.
- Pacote inicial: seis quadros da fonte, 1.767.580 bytes. Sem CI, testes SQL ou
  render redundante durante o preparo. O render real ocorrerá no fluxo da prova.
- Resultado esperado: versões/criticas privadas, custo/tempo, estado do pedido,
  coleção e download autenticado conferido por SHA, quando houver versão aceita.
  Falhas preservam material disponível e limitações, sem fabricar aprovação.

[Plano exato](../../.local/evals/reel-integrated-motion-proof-20261109/paid-plan.json)
· [preparo](../../.local/evals/reel-integrated-motion-proof-20261109/preparation.json)
· [worker conferido](../../.local/evals/reel-integrated-motion-proof-20261109/worker-ready.json).

## Orçamento autorizado

`gpt-6.1-sol`, reasoning high, Standard. Até quatro chamadas ao modelo e quatro
contagens: geração/crítica; uma correção e crítica final somente se justificadas.
Limite de saída: 16.000 tokens na geração/correção, 8.000 na crítica.

**US$ 3,40 em novas reservas**, até US$ 0,85 por chamada. O saldo global já retido
no dev é US$ 4,25: teto agregado US$ 7,65, sem liberar/reutilizar reservas antigas
ou confundir estimativa de uso com faturamento. Nova operação/tenant: US$ 3,40.

Envio à OpenAI: briefing/kit fictícios, seis quadros da fonte, até 20 quadros por
versão atual/anterior desta rodada, código, plano temporal e calibrações textuais.
Não enviamos MP4/áudio. A guarda conta o payload exato antes de cada chamada e
interrompe se não couber na reserva. Falha/resultado incerto interrompem, sem
retry automático, outro modelo ou nova tentativa com orçamento antigo.

## Limites de interpretação

Crítica temporal cobre até três eventos e declara omissões. Seu parecer não
certifica toda a fluidez, sincronismo ou áudio. Comparação humana com som continua
decisiva para motion/narrativa, leitura, enquadramento, mensagem e áudio.
Modelo retornar `adequate` não é aceite humano, aprovação comercial ou publicação.
Nada será publicado nem cobrado de cliente. Nenhuma expansão de formato integra
esta prova. Se houver falha ou ganho insuficiente, registrar sem declarar o alvo
criativo atingido.

Autorização registrada: entrevista `call_843eae67486a4ea5a3f22b21f392f154`,
resposta “Autorizar até US$ 3,40 para esta rodada”. Arquivo local de aprovação
vinculado ao SHA-256 do plano proposto, preservado sem alterações.

## Resultado da tentativa autorizada

O pedido terminou `failed/MOTION_AI_RESPONSE_INVALID`, sem render, crítica ou
peça. A resposta preservada revelou `incomplete`, motivo `max_output_tokens`:
9.428 tokens de entrada e 16.000 de saída, dos quais 10.876 de raciocínio. Não
houve retry. Geração: 321,241 s; workflow: 351,02 s. Worker próprio encerrado.

Uma chamada e uma contagem; reserva US$ 0,85. Uso estimado **US$ 0,183570**, apurado
posteriormente dos tokens registrados e tarifas conservadoras configuradas. O
efeito histórico mantém estimativa desconhecida; o diagnóstico separado não
altera o ledger nem declara faturamento conciliado. Global retido: US$ 5,10.
Não há comparação B disponível nem evidência de ganho criativo desta tentativa.

[Relatório da interrupção](../../.local/evals/reel-integrated-motion-proof-20261109/report.html)
· [uso recuperado](../../.local/evals/reel-integrated-motion-proof-20261109/usage-analysis.json).

Correção de implementação: `MOTION_AI_OUTPUT_LIMIT` passa a identificar esse caso
e carregar uso/estimativa para a persistência privada existente. 80 testes
específicos passaram em 6,05 s, Ruff/mypy aprovados, sem ampliar CI. O limite de
16.000 permanece no histórico; nenhuma chamada foi repetida após a correção.

[Retomada executada após autorização](plano-retomada-motion-temporal-2026-11-09.md): geração
com 32.000 tokens, duas chamadas/contagens, sem correção; US$ 1,70 adicionais em
reservas dentro do teto original de US$ 3,40. A retomada foi autorizada e concluiu geração/render/crítica/download.
Comparativo A/B disponível; aceite humano e conclusão sobre ganho criativo pendentes.
