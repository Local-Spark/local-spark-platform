# Resultado da composição aprovada — 10/11/2026

## Resultado e avaliação humana

O titular aprovou os quadros da versão `d027e78c-e7bf-5ea5-b3f6-7b795cbcf80f`,
hash `e24c2ac4b706955c8d93163f5eee56b69b94306e9576f1fdbf1e5abfe3f5177e`.
Aceite registrado pela API e continuação executada via Temporal. Vídeo montado
com a composição e materiais existentes, sem regeneração da peça.

[Comparativo A/B](../../.local/evals/reel-storyboard-composition-20261109/comparison.html):
A é o resultado anterior; B é a composição aprovada, animada.
MP4 B: 1.065.175 bytes, SHA256
`a52bf391ffd3d6a8b5d1c7970073f9903e19f7839958ed0fae84d276acb4c57f`.

Feedback recebido: mais elementos visuais e melhora parcial, mas xícara desenhada
com aparência infantil; acabamento ainda muito distante do desejado. **Não é
aprovação criativa final, nem demonstra equivalência às referências.** O titular
solicitou analisar dois vídeos de Lucas Leite sobre edição do material bruto.

## Crítica e encerramento técnico

A única crítica prevista recebeu 39.445 tokens de entrada e atingiu 8.000 tokens
de saída, retornando `MOTION_AI_OUTPUT_LIMIT`. Não há parecer válido. Sem retry,
correção automática ou aumento de limite. O MP4 ficou preservado.

O encerramento inicialmente colidiu com o evento da falha anterior à recuperação
do storyboard. Correção: falha da continuação deriva sua identidade do evento de
aprovação, preservando o vínculo do pedido no payload. Audit/outbox e fallback
para quarentena usam essa identidade. Migração aditiva `0116_motion_failure_identity`
aplicada no dev sem limpeza; histórico anterior preservado. Serviço corrigido
registrou `failed/MOTION_AI_OUTPUT_LIMIT`, sem provider ou render novos.

O worker dedicado foi parado. Uma futura execução deve usar imagem reconstruída
com essa correção; não reiniciar a imagem antiga para outra prova.

## Custos e validação

| Tentativa | Estimativa de uso (US$) | Reserva retida (US$) |
| --- | ---: | ---: |
| Geração truncada | 0,241478 | 0,85 |
| Geração com tracks estáticas inválidas | 0,180125 | 0,85 |
| Geração da composição reformulada | 0,175028 | 0,85 |
| Crítica truncada do vídeo | 0,178613 | 0,85 |
| Total | 0,775244 | 3,40 |

Estimativa não é fatura. Reservas ficam retidas para conciliação. Nenhuma imagem
paga foi gerada. As quatro chamadas textuais previstas foram consumidas; eventual
nova chamada exige plano explícito, sem tratar saldo como autorização automática.

69 testes unitários direcionados passaram em 1,55 s; três testes SQL em banco
exclusivo `_test` passaram em 7,52 s, incluindo falha da continuação normal e em
quarentena sem colisão/duplicação. Ruff aprovado. Sem CI completo ou suíte longa.

## Continuidade

Analisar as novas referências para direção de arte e movimento ao redor da
gravação preservada. O titular esclareceu que o projeto de edição de bruto para
YouTube é separado e não foi solicitado; não propor cortes como requisito desta
melhoria. Preservar kit, acervo, skills e biblioteca. Nenhuma
nova geração autorizada por este feedback; etapa 5 não iniciada. Ponto 4 permanece
sem qualificação criativa e sem crítica automática válida.
