# Implementação do plano aprovado, antes do render — 12/11/2026

Após o titular autorizar avançar, a aprovação do plano corrigido foi persistida
pelo checkpoint real. Uma chamada de código, limitada a US$ 1,25, produziu HTML e
scene_init. O fluxo parou em awaiting_render: nenhum browser, animação, quadro,
storyboard ou vídeo executado; nenhuma aprovação de render registrada.

## Continuação e fidelidade

Plano aprovado: checkpoint
`68877906f2ae87dcf2d01026b0bff84f97763229df8a4976ebd44addeffe8354`,
construction_plan_hash
`f0c88460e79ae6a3bd640bcf8a43d4d9a3c1ea867b308260036bd9f253401d1c`.
Metadados da composição são exatamente iguais aos do plano, e HTML/JavaScript
persistidos são iguais ao retorno bruto. Materiais e áudio são os autorizados.
Não se anexou peça anterior como exemplo nem se geraram assets de IA.

Admissão/owner/RLS, audit/outbox, Temporal e ledger existentes foram usados.
Workflow final COMPLETED, pedido running com execution_token liberado, esperando
a decisão do novo checkpoint. Efeitos do pedido: um ASR, um plano, um código e
zero render. ASR e plano foram reutilizados, sem refazer etapas pagas.
Checkpoint pendente de render:
`3478bc260526fe60e5e91cdbaa4e508090fdf85e857d1dc6971d94de5f58bc41`.

A primeira retomada falhou antes de contar/reservar/submeter código: erro da
guarda privada do assistente ao comparar literalmente JSON com chaves reordenadas
pelo armazenamento canônico. Diagnóstico preservado; a guarda agora normaliza
somente essa ordem irrelevante, mantendo valores, listas, imagens, parâmetros,
schema e plano vinculados. A entrada efetiva foi vinculada tanto à contagem como
à única submissão, wire_sha256
`43d2e941f99077c8e8986cae9ae586a1068f929f1a476c9cae58d2e14874a4d1`.
Não se afirma identidade binária com a preparação offline anterior.

Como a aprovação original já fora consumida, implementada continuação interna
explícita, idempotente e auditada, restrita à ausência de qualquer claim de código
ou upload correspondente. Aprovação original e falha ficam no histórico. Não há
retry automático, endpoint novo, migração ou mudança de runner. Condições e
recusas: [decisão técnica](../design/motion-checkpoint-pre-submission-recovery-2026-11-12.md).

## Resultado da revisão estática

- Schema e validação nativa da composição passaram. Preparação do bundle e
  injeção das bibliotecas locais passaram sem invocar o renderer. JavaScript
  original e bundle passaram em node --check, sem executar o código.
- Dezessete IDs planejados presentes, sem duplicatas; um vídeo local, sem áudio
  de browser ou script inline. Mesmo nó de vídeo é reutilizado nas três cenas,
  com seek pelo tempo absoluto fornecido e espera por seeked. Continuidade real
  ainda depende da execução posterior.
- Xícara e U usam paths com comandos compatíveis para interpolação; asa/abertura
  recuam e apoio vira campo. Alinhamento visual, reconhecimento e legibilidade
  não foram certificados por análise do código.
- Implementação escolheu deslocamento em arco para expansão/recolhimento.
  Verificação independente das fórmulas, em 10.001 valores de progresso para
  cada passagem, não encontra interseção do campo/xícara com a janela do vídeo;
  caixa da xícara permanece no canvas. Isso trata o risco da interpolação direta
  apontado no plano. É evidência geométrica estática, sem pixels observados.
- Soundtrack mantém áudio original autorizado, sem ganho/corte novo, e apenas o
  servir aprovado no plano: offset 1.900 ms, trecho 290–2.070 ms, ganho 0,75,
  fades 60/140 ms. Nenhuma mistura foi produzida ou ouvida nesta etapa.

Revisão privada e evidências:
`.local/evals/motion-supervised-20261112/implementation-v1/REVISAO-DO-CODIGO.md`,
`code-verification.json`, `observed-execution-summary.json`, código/retorno bruto
e entradas. Conteúdo da fonte permanece fora do Git.

## Validação, custo e pendências

Regressão: 1.657 testes motion/exportadores aprovados, dois skipped. Casos
PostgreSQL de checkpoints/continuação passaram no _test existente; cobertura
agregada de motion_checkpoints: 184 statements/60 branches, 100%. Concorrência,
duplicatas, ausência de outbox, payload adulterado, contexto alterado e início
prévio do efeito são cobertos. Quarenta unitários do orquestrador passaram.
Ruff lint/formato (905 arquivos), Mypy 334 módulos app + oito scripts e diff
--check passaram. Grupos de testes se sobrepõem; não somar os totais.
CI global ainda não qualificado: cobertura Node abaixo de 100% e falhas anteriores
de geocodificação/schema no _test, sem correção/migração implícita nesta etapa.

Única chamada de código: 45.771 tokens de entrada e 21.812 de saída; estimativa
US$ 0,332548, teto calculado US$ 0,654428, dentro dos US$ 1,25 autorizados.
Reserva continua uncertain/actual nulo, sem fatura conciliada ou liberação de
sobra. Três chamadas nesta sequência, incluindo os dois planos anteriores,
somam US$ 0,774901 estimados e US$ 3,75 reservados. A primeira falha desta etapa
foi anterior à submissão e não acrescentou chamada paga de código.

Runtime global disabled/execução false, cinco serviços restritos exited e dev
0118; nenhuma nova migração ou inicialização de serviço. Próximo gate é a decisão
sobre o pacote de render exato. Prévia posterior deve conferir metamorfose,
fluidez, legibilidade do U/CTA, detalhe útil da gravação, sincronismo e escuta da
mistura. Aprovação de código/revisão estática não certifica qualidade artística.
