# F07 — Franquias, assinatura e relatórios

Status: Planejada. Atualizado em 20/10/2026.
Dependências: F00, F01; integra F03–F06.

## Objetivo

Controlar direito de uso, custo real e continuidade comercial com resultados observáveis.

## Features e contratos

- Ledger separado de quota comercial e COGS; reserva atômica, consumo e compensação.
- Concessão de seis meses com início/fim e sem renovação paga implícita.
- Assinatura, cobrança, cancelamento, webhook e conciliação do processador escolhido.
- Relatório semanal com dados disponíveis, origem e lacunas; não inventar atribuição de vendas.

## Critérios de aceite e testes

- Disputa pelo último crédito, pagamento duplicado/reordenado e custo UNKNOWN.
- Expiração promocional e cancelamento não geram cobrança indevida.
- Relatório reproduzível e sem acesso às conversas comerciais não integradas.

## Limites e decisões pendentes

- Franquias/preços/refações e provedor de cobrança precisam de decisão.
- As tabelas/reservas mínimas entram antes de habilitar gasto real em fases anteriores.

## Integração e manutenção

Dividir as features acima em mudanças revisáveis. Cada mudança atualiza este SDD,
`docs/PROJECT.md` e `docs/CHANGELOG.md`, incluindo evidências de testes e pendências.
Contratos que afetam outras fases devem ser refletidos no SDD geral e nos consumidores.
Não marcar como concluído por possuir mocks ou documentação de uma API ainda não validada.
