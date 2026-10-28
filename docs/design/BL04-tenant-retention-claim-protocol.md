# BL04.2 — holds de retenção: proposta histórica superada

Reconciliado em **28/10/2026**. **Registro histórico, sem implementação a executar a partir
deste documento.**

O protótipo de holds e os testes temporários foram removidos. Eles investigavam TTL/exclusão
de materiais associados e exceção de revisão por sete dias. A 0058 passou a preservar todos
os materiais associados, sem exclusão pelo histórico. A decisão posterior também preserva
prévias enquanto a conta estiver ativa; essa parte ainda precisa de implementação. Não criar
holds, grants ou exceções antigas a partir desta proposta.

## Contrato de referência

[Materiais duráveis](BL04-whatsapp-durable-materials.md), [integração
segura](BL04-integration-safety.md) e [decisões de retenção/acesso](../DECISIONS.md).
Limpeza técnica de órfãos/efeitos incertos continua exigindo coordenação, sem presumir o
mecanismo histórico.

## Evidência preservada

O [texto original
integral](../history/2026-10-28-pre-documentation-reconciliation/design/BL04-tenant-retention-claim-protocol.md)
conserva hipóteses, SQL, diagnósticos e rejeições da época. Ele não autoriza alterações de
permissões, migrações, efeitos externos ou gasto. As [decisões vigentes](../DECISIONS.md) e
o [SDD](../SDD.md) prevalecem.
