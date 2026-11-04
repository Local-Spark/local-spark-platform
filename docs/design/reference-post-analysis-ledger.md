# Ledger da análise de publicações

`DatabasePostAnalysisGuard` vincula o pedido Jev exato à organização, negócio,
titular executor, referência, versão de associação, janela de análise, execução
Apify de origem, piloto e tarifa. Uma identidade opaca por publicação/imagem,
calculada com HMAC, permite recuperar padrões já calculados sem guardar o ID da
publicação, URL, legenda ou imagem. O código de origem permanece só em memória.

A revisão em preparação `0109_reference_post_analysis` usa o mesmo ledger e os
mesmos contadores financeiros existentes. Antes do efeito valida a seleção
canônica da `0108`, o token do coletor e seu run persistido. Reserva custo e cria
identidade, auditoria e outbox na mesma transação. A chamada de rede ocorre após
a transação. Outra organização ou executor não recebe tokens.

Repetir o pedido não concede outra execução; alterar o corpo com a mesma identidade
gera conflito. Resultado incerto conserva a reserva. Resultado bem formado
persiste apenas códigos do vocabulário próprio, modelo e uso de tokens. Sem
recibo monetário, a reserva continua contabilizada e não é registrada como custo
efetivo. O piloto de US$ 5 e limites por fornecedor continuam valendo; atingir
um limite não autoriza descartar imagens silenciosamente nem declarar análise
completa. O coordenador deve informar parcialidade.

O serviço e HMAC passaram em 46 unitários com 100% de linhas e branches. Vinte e
duas integrações SQL passaram em banco descartável com a seleção canônica da
`0108`, incluindo a confirmação pela API e o claim real do coletor. Cobrem replay,
concorrência, limites independentes, isolamento, retirada da seleção, prova do
coletor, saída inválida, âncora da legenda e proteção de downgrade. A migração
ainda não foi aplicada ao banco de desenvolvimento.

A legenda tem uma âncora HMAC única por publicação/janela. Um efeito incerto
continua ocupando essa âncora, mesmo que as imagens disponíveis mudem na retomada.
Leituras privadas expõem apenas estado, presença de legenda e códigos concluídos;
nunca devolvem tokens. O executor pode continuar imagens restantes sem reenviar
a legenda.

`reference_feed_record_terminal_cost` reconcilia o custo Apify informado pelo
run validado. Zero é recibo válido; ausente mantém reserva incerta. Replay igual
é idempotente, divergência falha e inconsistencia mensal faz rollback completo.
O roundtrip vazio passou. A primeira rodada detectou conflito na unicidade da
auditoria ao chegar um recibo depois de custo desconhecido; os dois eventos
agora têm ações distintas, validadas em SQL.
