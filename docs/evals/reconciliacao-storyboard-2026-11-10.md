# Registro da galeria recuperado — 10/11/2026

## Resultado

Migração aditiva `0115_motion_storyboard_events` aplicada no dev autorizado, sem
limpeza. Permite ready/decided/approved/reconciled do storyboard no outbox,
preservando os eventos anteriores e a RLS. Não altera a migração 0114 já aplicada.
Downgrade não apaga histórico: é recusado se houver eventos que deixariam de ser
permitidos.

A captura do Café Pausa foi reconciliada pelo serviço, a partir dos recibos e
arquivos já existentes. Três quadros passaram à galeria privada do produto, no
estado **awaiting_approval**, sem geração, render, upload ou chamada paga novos.
O pedido volta a running somente para aguardar a decisão; o workflow de geração
anterior permanece encerrado. Aprovação posterior inicia a continuação Temporal
já existente, com sua identidade própria. Nenhum aceite foi inferido.

Versão: `d027e78c-e7bf-5ea5-b3f6-7b795cbcf80f`.
SHA do conjunto: `e24c2ac4b706955c8d93163f5eee56b69b94306e9576f1fdbf1e5abfe3f5177e`.
[Galeria exportada e aberta para o titular](../../.local/evals/reel-storyboard-composition-20261109/gallery.html).
A avaliação da composição está pendente; movimento e áudio ainda não avaliados.

## Escopo da recuperação

`MotionStoryboardRecovery` é operação explícita de serviço, sem novo endpoint ou
retry automático. Aceita somente a captura inicial sem ilustrações, cujo payload
da galeria tenha sido persistido em upload durável recebido. Recusa geração ou
render incompletos, estado incerto, custo desconhecido/excedido, outra causa de
falha, versões de vídeo existentes ou efeitos de crítica/correção.

Confere titular/RLS, admissão, consentimento, contexto atual e fingerprint. Verifica
a composição contra a geração e o render recebidos, todos os manifestos de upload,
proveniência, caminhos privados e bytes/SHA dos PNGs. Downloads ocorrem fora dos
locks. Antes da gravação, relê contexto, estado e recibos sob lock; mudança concorrente
bloqueia a operação. Estado, galeria, auditoria e outbox são gravados juntos.

A identidade do conjunto é derivada do pedido original; repetição com mesmo hash
não duplica galeria/eventos nem reinicia efeitos. A falha anterior continua no
histórico; a reconciliação registra `motion.storyboard_reconciled` e
`motion.storyboard_ready`. Não emite aprovação nem agenda vídeo automaticamente.

## Validação e pendências

- 44 testes unitários direcionados passaram em 1,94 s.
- Dois testes SQL no banco dedicado `_test` passaram em 4,08 s: criação/aceite
  exato da galeria e recuperação após falha de registro, com isolamento entre
  negócios, idempotência e nenhuma segunda geração/render.
- Ruff, formatação e mypy aprovados. Sem CI completo ou suíte longa.
- Operação real no dev validou e recuperou os três arquivos preservados.

Custos permanecem: estimativa acumulada US$ 0,596631 e reservas US$ 2,55. Não há
nova cobrança nesta reconciliação. Pendências: decisão do titular, render integral,
crítica e avaliação final com som. Ponto 4 ainda não concluído; etapa 5 não iniciada.

Verificação final pela API autenticada: consulta do pedido, metadados do storyboard
e HTML da galeria retornaram HTTP 200, mantendo `awaiting_approval`. Sem chamada
de geração, render ou crítica.

## Aceite e continuação

Titular respondeu: “Aprovar os quadros e montar o vídeo”. Aceite exato da versão/hash
registrado pela API (HTTP 200) e continuação disparada pelo outbox/Temporal.
Reutiliza composição e materiais, sem nova geração. Permitida somente a crítica
prevista no plano, sem correção automática. Resultado do vídeo e avaliação final
com som ainda pendentes; este aceite não substitui a decisão final da peça.

## Atualização após a continuação — 10/11

A decisão pendente acima foi recebida: quadros aprovados, vídeo efetivamente
renderizado. A crítica veio truncada; não houve retry. O pedido foi encerrado com
falha após correção da identidade de eventos (0116), mantendo o MP4. O titular
avaliou melhora parcial, mas aparência infantil e qualidade ainda insuficiente.
Estado e custos atuais: [resultado do vídeo](resultado-video-composicao-2026-11-10.md).
Os valores e estados nas seções anteriores descrevem a recuperação, antes do vídeo.
