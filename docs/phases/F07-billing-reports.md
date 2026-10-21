# F07 — Franquias, assinatura e relatórios

Status: Parcial; contratação mínima antecipada na F01.5. Atualizado em 20/10/2026.
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

F01.5 implementa o primeiro adapter Stripe em modo disabled/test/live, jobs/inbox,
reconciliação por evento, patrocínio e interfaces mínimas. Ver [SDD billing](../design/billing.md).
Continuam pendentes: validação real da conta em sandbox/staging, ledger/franquias,
preços finais, upgrades, cancelamento/portal self-service, conciliação periódica,
resolução/reprocesso de holds e faturamento/MRR/relatórios. Retry de webhook não
substitui conciliação operacional. Não habilitar cobrança comercial antes dessas
condições. Pix e meios adicionais exigem validação/habilitação no provedor.

- Franquias/preços/refações e provedor de cobrança precisam de decisão.
- As tabelas/reservas mínimas entram antes de habilitar gasto real em fases anteriores.

## Integração e manutenção

Dividir as features acima em mudanças revisáveis. Cada mudança atualiza este SDD,
`docs/PROJECT.md` e `docs/CHANGELOG.md`, incluindo evidências de testes e pendências.
Contratos que afetam outras fases devem ser refletidos no SDD geral e nos consumidores.
Não marcar como concluído por possuir mocks ou documentação de uma API ainda não validada.

## Replanejamento: contratação inicial e analytics

F01.5 antecipa checkout, webhook assinado/reconciliado, ativação idempotente e
concessão patrocinada por seis meses. Criar identidade/organização em setup não
ativa geração paga. Patrocinados e trials não contam como pagantes. Esta fase
completa upgrades, inadimplência, cancelamento, franquias e relatórios.

Admin interno usa dados próprios de cadastro/cobrança/consumo e dados sociais
coletados na F06. Distinguir usuários, organizações, negócios e assinaturas; MRR
separado de recebimento e custos estimados. Cliente vê apenas seu contexto e
recebe resumo semanal pelo WhatsApp. Métricas sociais não comprovam vendas;
faturamento exige integração ou informação declarada com origem e período.
