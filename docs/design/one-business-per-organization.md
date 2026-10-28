# Uma organização por negócio

Atualizado em **28/10/2026**. Decisão aceita e **implementada localmente**:
cada negócio tem conta/organização, assinatura ou patrocínio e aceite próprios.
Negócios distintos, inclusive franquias, não compartilham a cobrança dentro de
um mesmo tenant. Ver [decisões](../DECISIONS.md) e [cobrança](billing.md).

## Estado atual e invariantes

- O onboarding cria organização e negócio juntos em uma transação. A API recusa
  um segundo negócio; a constraint de unicidade em `businesses.tenant_id` da
  `0057_one_business_per_tenant` assegura a regra inclusive em concorrência.
- Repetição com mesma chave/payload conserva a resposta idempotente, sem criar
  outro negócio. A migration recusa duplicatas existentes sem limpá-las sozinha.
- Cobrança, checkout, Stripe e patrocínio continuam por organização. Não implementar
  a proposta anterior de adicionar `business_id` às tabelas financeiras.
- `service_agreement_acceptances` da 0056 é reaproveitada para o aceite por negócio;
  GET/POST e Plano e acesso estão integrados. O contrato não ativa pagamento,
  credenciais, orçamento, provedores ou publicação.
- Conta staff/operador não exige negócio. A regra não limita quantos proprietários
  web podem existir nem resolve recuperação de pendências de outro autor.
- Um número WhatsApp ativo por negócio é uma limitação independente.

A 0057 foi aplicada ao banco local após aprovação; o estado local avançou depois
para 0058 de materiais duráveis. Não tratar o nome deste desenho como versão
corrente do schema. A validação da fatia registrou 1.530 testes backend e 100%
linhas/branches; é evidência daquela entrega, não contagem atual da suíte.

## Dados locais e evidência histórica

A organização local de demonstração tinha dois registros de negócios de teste.
O proprietário autorizou removê-los, preservando organização, patrocínio histórico
inativo, auditorias e eventos entregues/processados. Houve backup PostgreSQL e
restauração em base isolada; ele não inclui mídia de objetos ou Temporal.
A limpeza dos registros e a aplicação das migrations foram operações distintas,
autorizadas naquele ambiente, sem conceder autorização permanente para repetir.

A [revisão 0050–0057](local-migrations-0050-0057-review.md) e o snapshot anterior
conservam o inventário detalhado. Não criar/cancelar assinatura ou associar dados
financeiros históricos automaticamente para preencher organização sem negócio.

## Trabalho restante

Definir recuperação da organização existente sem negócio, evitando redirecionamento
entre seleção e onboarding e preservando seu histórico. Esse caso é diferente de
permitir outro negócio num tenant já ocupado. Permanecem pendentes homologação
comercial da cobrança e recuperação restrita por staff quando o autor da mudança
perde acesso; outro owner não assume essa pendência. A unicidade e o aceite único
não implementam esse fluxo de suporte.

Para novas alterações validar replay, concorrência, RLS entre contas, acesso por
assinatura/patrocínio independente e staff sem negócio. Usar base `_test`, sem
limpar a base de desenvolvimento ou chamar serviços pagos.

Versão anterior integral: [snapshot de 28/10/2026](../history/2026-10-28-pre-documentation-reconciliation/design/one-business-per-organization.md).
