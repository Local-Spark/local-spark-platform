# Cobrança multinegócio — análise histórica substituída

Reconciliado em **28/10/2026**. **Registro histórico, sem implementação a executar a partir
deste documento.**

A alternativa de adicionar negócio às estruturas de cobrança foi substituída pela decisão de
um negócio por organização (0057). A cobrança continua por tenant, sem uma assinatura
compartilhada entre vários negócios. O aceite por negócio reaproveita a tabela 0056 e já
possui POST e interface integrados, preservando consentimentos antigos sem reativá-los.

## Contrato de referência

[Uma organização por negócio](one-business-per-organization.md), [cobrança
atual](billing.md) e [aceite único](ai-as-core-service.md). Não executar a migração
financeira multinegócio da análise anterior.

## Evidência preservada

O [texto original
integral](../history/2026-10-28-pre-documentation-reconciliation/design/review-billing-and-agreement-per-business.md)
conserva hipóteses, SQL, diagnósticos e rejeições da época. Ele não autoriza alterações de
permissões, migrações, efeitos externos ou gasto. As [decisões vigentes](../DECISIONS.md) e
o [SDD](../SDD.md) prevalecem.
