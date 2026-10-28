# BL04.2 — proposta de leitura mínima de efeitos editoriais

Estado: **proposta para revisão; não aplicada**. A revisão automática rejeitou
uma tentativa de alterar a política de acesso e os privilégios desta tabela.
A retirada da autorização editorial continua imediata; este documento não
implementa a espera nem autoriza geração visual real.

## Problema e proposta

Uma chamada editorial pode permanecer em andamento depois da exclusão da sua
proposta, porque o material original possui exclusões em cascata. A tabela
`editorial_ai_usage` registra a chamada e não depende da sobrevivência da
proposta. É necessário verificar se há chamadas `submitted` ou `uncertain` do
mesmo negócio antes de efetivar a retirada, sem expor texto, tokens ou dados de
outros negócios.

Uma migração candidata, sujeita a revisão e testes com as roles reais, criaria
uma política de leitura para a role `meu_braco_direito_app` com as mesmas
condições de tenant e owner ativo usadas nas tabelas editoriais existentes. A
role receberia somente leitura das colunas `tenant_id`, `business_id` e `state`:

```sql
CREATE POLICY owner_usage_status ON editorial_ai_usage
  FOR SELECT TO meu_braco_direito_app
  USING (
    tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid
    AND EXISTS (
      SELECT 1 FROM memberships m
      WHERE m.tenant_id = nullif(current_setting('app.tenant_id', true), '')::uuid
        AND m.actor_id = nullif(current_setting('app.actor_id', true), '')::uuid
        AND m.role = 'owner' AND m.active
    )
  );
GRANT SELECT (tenant_id, business_id, state)
  ON editorial_ai_usage TO meu_braco_direito_app;
```

O serviço consultaria somente a existência de estados abertos para o tenant e
negócio validados. A policy e o grant não dão à API acesso a `proposal_id`,
contagem de tokens, conteúdo ou metadados adicionais; a interface não recebe
registros individuais. A role correlator mantém seus privilégios existentes.
Antes de aplicar, comprovar que as roles não têm heranças que ampliem esse
acesso, que a policy de memberships não cause recursão e que tenant/actor sejam
definidos por transação. A migração de reversão deve revogar apenas o novo grant
e remover apenas a nova policy, sem apagar o histórico.

## Integração necessária, ainda não implementada

- Serializar o pedido de retirada e a admissão da chamada com o mesmo lock curto;
  registrar estado pendente durável e impedir pedidos ainda não iniciados.
- Manter autorização pendente enquanto houver uso submetido ou incerto, inclusive
  se a proposta e a origem forem apagadas; expiração de lease não é conclusão.
- Registrar conclusão conhecida com a role que já executa a chamada. Se a proposta
  desaparecer ou o resultado for desconhecido, manter o estado em verificação até
  haver uma reconciliação segura; não reenviar a chamada automaticamente.
- Aplicar a retirada após a última execução conhecida, com checagem atual da
  membership do solicitante. O caso de proprietários diferentes continua sem
  solução aprovada; não trocar a identidade da sessão para aplicá-lo.
- Tratar a autorização visual, a de materiais WhatsApp e a da TypeSafe como
  autorizações distintas, conforme as decisões do produto.

## Validação obrigatória

Testar migrations e roles reais apenas na base `_test`: owner ativo do mesmo
tenant, viewer, owner de outro tenant, usuário revogado, `app.tenant_id` ausente,
e tentativas de ler colunas não autorizadas. Testar também submissão concorrente
com retirada, cascata durante chamada, expiração, resultado conhecido e incerto,
reconcessão, rollback e isolamento entre negócios. A política de retenção das
fotos e seus cinco caminhos de exclusão têm problema separado e continuam fora
do escopo desta proposta. Nenhum teste deve fazer chamada paga ou usar conteúdo
real de cliente.
