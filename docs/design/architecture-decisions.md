# ADRs v0.1 — registro histórico superado

Reconciliado em **28/10/2026**. **Registro histórico, sem implementação a executar a partir
deste documento.**

Os ADRs anteriores registravam opções do bootstrap. Celery/RabbitMQ e runner de workflow
próprio foram substituídos por Temporal. Não operar dois runners para os mesmos processos.
Redis é candidato futuro, sem dependência ativa.

## Contrato de referência

[Arquitetura atual](v0-architecture.md), [consistência](v0-consistency-observability.md) e
[resiliência Temporal](v0-reliability.md).

## Evidência preservada

O [texto original
integral](../history/2026-10-28-pre-documentation-reconciliation/design/architecture-decisions.md)
conserva hipóteses, SQL, diagnósticos e rejeições da época. Ele não autoriza alterações de
permissões, migrações, efeitos externos ou gasto. As [decisões vigentes](../DECISIONS.md) e
o [SDD](../SDD.md) prevalecem.
