# Revisão: cobrança e aceite por negócio

Estado: **reutilização do aceite aprovada; proposta de cobrança multinegócio
superada pela decisão posterior de uma organização por negócio**. Ver o
[desenho atualizado](one-business-per-organization.md). O texto abaixo
preserva a análise anterior como histórico, não como plano a implementar.

Em 28/10/2026, o proprietário definiu que negócios diferentes terão cobranças
e aceites diferentes, mesmo que pertençam à mesma pessoa. Cada negócio deve
conhecer as condições do serviço de IA uma vez, sem escolhas separadas de
fornecedor ou modalidade. A transcrição de áudio integra o serviço.

## Aceite: comparação das estruturas existentes

| Estrutura | O que registra | Limite para a decisão atual |
| --- | --- | --- |
| `consents` | Organização, usuário, finalidade, versão e data do onboarding | Não identifica o negócio. Os textos `2026-10` eram de validação local e não apresentam a nova oferta de IA. |
| `service_agreement_acceptances` (`0056`) | Organização, negócio, usuário, versão, hash do aviso e data | Foi criada sem revisão prévia do proprietário; está apenas na base `_test`. O POST e a tela ainda não estão conectados. |

**Decisão aprovada pelo proprietário:** reaproveitar a tabela `0056` para o
novo aceite por negócio e manter `consents` e seus registros históricos, sem
criar outra tabela de aceite. A integração ainda não foi habilitada. Essa
decisão não aprova uma alteração na estrutura da cobrança.

Retirar os controles separados de IA da tela **Sobre meu negócio** faz parte da
jornada aprovada. A remoção deve acompanhar o caminho de aceite funcional, para
que não se esconda o único modo atualmente existente de habilitar as funções.
Transcrição de áudio também pertence à jornada única. A conexão do WhatsApp e a
aprovação da publicação continuam como ações do cliente.

O proprietário esclareceu que ainda não há clientes em produção: o negócio
contrata o serviço, aceita as condições e só então conecta o WhatsApp. Não há
demanda para criar uma fila especial para mensagens anteriores ao aceite.
Contas e vínculos já existentes nos testes locais precisam ser tratados na
transição, sem presumir que já aceitaram os termos novos. O POST de aceite
permanece indisponível e os controles existentes ainda não foram removidos.

## Cobrança: situação atual

Hoje `billing_accounts` tem uma conta por organização e ambiente;
`billing_sponsorships` permite um patrocínio por organização. Checkout, jobs,
reconciliação, APIs e tela de plano trabalham com organização. Assim, uma
assinatura ou patrocínio pode liberar vários negócios da mesma organização.
Esse comportamento não atende à decisão do proprietário.

A consulta administrativa de oportunidades também escolhe um perfil da
organização para mostrar o contato, sem associá-lo necessariamente ao negócio
que iniciou o checkout. Essa projeção precisará acompanhar a correção.

## Alternativas para revisão posterior

1. **Manter vários negócios na organização e associar a cobrança ao negócio.**
   Adaptar conta de cobrança, checkout, patrocínio, eventos/reconciliação,
   validações de acesso, API e telas para identificar o negócio. Reaproveitar
   a conta Stripe e o Price de sandbox já existentes. É a alternativa sugerida
   para preservar o modelo de organização e vários negócios.
2. **Usar uma organização por negócio.** Reaproveitaria a cobrança atual por
   organização, mas exigiria rever navegação e migração dos dados de negócios
   que hoje compartilham uma organização.

Nenhuma alternativa foi aprovada ou implementada ainda. Para a primeira, ainda
é necessário revisar como identificar assinaturas, clientes, reembolsos e
disputas na Stripe; a restrição atual de `customer_id` e as consultas de eventos
usam a organização. Não presumir associação de uma assinatura antiga a um
negócio quando a organização tiver mais de um. A regra de transição dos dados
existentes precisa ser apresentada separadamente antes da migração.

### Desenho concreto da alternativa 1, para aprovação

- Manter a organização com vários negócios e identificar o negócio nas contas
  de cobrança, checkouts, pedidos de checkout, patrocínios e auditoria. Cada
  referência deve apontar para um negócio da própria organização. Eventos de
  webhook podem chegar sem negócio e serão associados pelo checkout ou pela
  assinatura existente, antes de produzir alterações.
- Substituir a chave atual da conta, limitada a uma por organização e ambiente,
  por uma identificação que permita uma conta por negócio e ambiente, mantendo
  uma forma separada de preservar contas históricas ainda não associadas a um
  negócio. Alterar também a unicidade do patrocínio para ser por negócio.
- Checkout, consulta de acesso, reconciliação, cancelamento, painel e
  oportunidades devem receber e verificar organização **e** negócio; o
  processamento e seus locks passam a ser por conta do negócio. O retorno do
  checkout identifica o negócio para exibir o estado correto.
- Preservar deduplicação por evento e unicidade da assinatura Stripe; usar
  uma identidade de cliente Stripe por negócio para que reembolsos e disputas,
  hoje localizados pelo cliente Stripe, sejam atribuídos corretamente. Manter
  a conta Stripe e o preço já configurados; não criar outra cobrança de teste.
- O histórico não será apagado. Nenhuma assinatura ou patrocínio antigo será
  atribuído arbitrariamente. A regra de associação dos registros existentes,
  inclusive organizações com apenas um negócio, será apresentada e decidida
  separadamente antes da migração.

Essa proposta exige uma migração de banco e revisão dos acessos RLS. Sua
descrição não constitui aprovação para executá-la. A forma exata de chaves e
índices será validada antes da implementação; a estrutura existente de aceite
`0056` e o histórico de `consents` permanecem.

## Resultado da alternativa anterior, preservado como histórico

Para uma organização com negócios A e B: contratar A ativa somente A; B segue
sem acesso até ter assinatura ou patrocínio próprio e seu próprio aceite. Uma
alteração ou cancelamento de A não modifica B. Repetir checkout, webhooks e
aceites não duplica cobrança. O painel identifica corretamente cada negócio.
Testar com sandbox e dados sintéticos; preservar históricos e nenhuma cobrança
real. Essa correção não completa a geração real de imagens da BL04.2.
