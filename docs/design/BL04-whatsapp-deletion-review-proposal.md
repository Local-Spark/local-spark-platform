# BL04.2 — exclusão de foto WhatsApp: proposta histórica superada

Reconciliado em **28/10/2026**. **Registro histórico, sem implementação a executar a partir
deste documento.**

A proposta pressupunha exclusão voluntária/expiração de foto recebida e revisão excepcional
por sete dias. O produto agora preserva texto, foto, áudio e vídeo associados, e a API
recusa exclusão pelo histórico. A 0058 implementou essa preservação; fotos desatualizadas do
acervo continuam removíveis. Não implementar a tabela de holds/recibos ou a janela de sete
dias deste desenho.

## Contrato de referência

[Preservação WhatsApp](BL04-whatsapp-durable-materials.md), [coordenação de
mudanças](BL04-atomicity-proposal.md) e [decisões atuais](../DECISIONS.md). Prévias devem
permanecer sem expiração automática enquanto a conta estiver ativa; o runtime ainda precisa
acompanhar essa decisão.

## Evidência preservada

O [texto original
integral](../history/2026-10-28-pre-documentation-reconciliation/design/BL04-whatsapp-deletion-review-proposal.md)
conserva hipóteses, SQL, diagnósticos e rejeições da época. Ele não autoriza alterações de
permissões, migrações, efeitos externos ou gasto. As [decisões vigentes](../DECISIONS.md) e
o [SDD](../SDD.md) prevalecem.
