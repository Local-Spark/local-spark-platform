# F07 — Franquias, assinatura e relatórios

Status: Parcial; contratação mínima antecipada na F01.5. Atualizado em 08/11/2026.
Dependências: F00, F01; integra F03–F06.

## Estado local e decisões correntes

O piloto será por **autoatendimento com cobrança**, conforme entrevista já
respondida. Ainda não há participantes reais definidos. A etapa 7 do
[roteiro de trabalho](../design/execucao-ate-etapa-7-2026-11-07.md) prepara essa
operação; preço/franquias dependem do custo completo por peça aceita, e o
sandbox não comprova contratação comercial pronta. Instagram não é condição
desse piloto de geração, revisão e download.

Checkout/webhook Stripe sandbox, pagamento de teste confirmado, reconciliação
por evento e patrocínio local existem. Billing segue por organização, agora
limitada a um negócio (`0057` aplicada). O aceite único versionado do serviço
em Plano e acesso é pré-requisito do checkout; não confirma pagamento e não
reativa consentimentos antigos. Não há check adicional de modelo, fornecedor ou
transcrição. Ver [registro de decisões](../DECISIONS.md).

Há reservas técnicas de tokens, segundos de áudio, interpretação e imagem,
inclusive teto agregado mensal OpenAI no ledger visual. Isso não completa quota
comercial, tarifa versionada, custo faturado ou margem. Não criar novo agregado
como se `0049` ainda não existisse; integrá-lo à admissão visual na BL04.

C08/C09 estão entregues no recorte local `visual_fake`/`visual_ai`: uma criação
admitida pode concluir e permitir revisão privada após vencimento financeiro;
prévias concluídas, proveniência e tentativas sem resultado resolvido são
preservadas sem limpeza automática por prazo. Novas criações/publicação exigem
plano vigente; bloqueio financeiro explícito e perda de acesso não são simples
vencimento. O renderer legado e a futura integração motion ainda precisam dessa
extensão. Ver [limites da BL04](BL04-context-and-ai-production.md). A assinatura
não se renova por sugestão de IA ou por terminar trabalho já admitido.

## Objetivo

Controlar direito de uso, custo real e continuidade comercial com resultados observáveis.

O [contrato de cadência e evidência](../design/editorial-planning-and-evidence.md)
define que cada plano tenha teto mensal por formato/canal e limite de revisões;
F03 sugere uma cadência dentro da franquia. Valores e volumes finais dependem
do custo por peça aceita medido na BL04. R$ 99/mês e custo total desejado de
até R$ 50/cliente/mês são hipóteses de medição, não preço/franquia aprovados. Exceder o plano exige upgrade
com preço e aceite explícitos; uma sugestão da IA nunca gera cobrança.

## Features e contratos

- Ledger separado de quota comercial e COGS; reserva atômica, consumo e compensação.
- O ledger mínimo é pré-requisito de F03/F04 para primeira operação paga, não
  entrega aguardada até F07. Esta fase amplia planos, franquias, reconciliação,
  custo faturado e margem por tipo de peça/tenant sem confundir preço do plano
  com custo do fornecedor.
- Concessão de seis meses com início/fim e sem renovação paga implícita.
- Assinatura, cobrança, cancelamento, webhook e conciliação do processador escolhido.
- Relatório semanal com dados disponíveis, origem e lacunas; não inventar atribuição de vendas.
- Aprender padrões editoriais apenas com métricas próprias comparáveis e amostra
  suficiente; registrar hipótese, fonte, período e incerteza no contexto versionado.

## Critérios de aceite e testes

- Disputa pelo último crédito, pagamento duplicado/reordenado e custo UNKNOWN.
- Expiração promocional e cancelamento não geram cobrança indevida.
- Relatório reproduzível e sem acesso às conversas comerciais não integradas.

## Limites e decisões pendentes

F01.5 implementa o primeiro adapter Stripe em modo disabled/test/live, jobs/inbox,
reconciliação por evento, patrocínio e interfaces mínimas. Ver [SDD billing](../design/billing.md).
Continuam pendentes: cenários externos restantes e staging, quota comercial/COGS,
preços finais, upgrades, cancelamento/portal self-service, conciliação periódica,
resolução/reprocesso de holds e faturamento/MRR/relatórios. Retry de webhook não
substitui conciliação operacional. Não habilitar cobrança comercial antes dessas
condições. Pix e meios adicionais exigem validação/habilitação no provedor.

- Franquias/preços/refações finais dependem de medição e decisão comercial.
  Stripe é o adapter atual; outros meios/provedores exigem validação própria.
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

A [versão anterior](../history/2026-10-28-pre-documentation-reconciliation/phases/F07-billing-reports.md)
preserva o planejamento original; não tratar o sandbox já exercitado como
pendência integral nem confundir seus dados com faturamento de produção.
