# BL04.2 — recuperação de alteração órfã: proposta restrita

Proposta de 28/10/2026; status atualizado em **29/10/2026: implementação adiada
pelo proprietário** para evolução de gestão de acesso/suporte. Não bloqueia o
encerramento da fatia simulada validada. **Nenhuma capability, função, migration
ou grant abaixo foi aplicada ou aprovada.** C10 mantém a recuperação exclusiva
de staff como regra de produto. O desenho abaixo é referência futura para a
fronteira de permissões descrita no [desenho de atomicidade](BL04-atomicity-proposal.md).
Até sua entrega, a exceção administrativa permanece bloqueada com a autoria
original; não transferir a pendência ou ampliar permissões para liberá-la.

## Evidência e proteção entregue

A policy `owner_business_visual_pending_changes` da migration 0050 permite
leitura e alteração somente a owner ativo no tenant. Staff sem membership não
consegue consultar nem cancelar a pendência. As policies da migration 0002
também impedem um owner de verificar a conta/membership de outro usuário.
Logo, a sessão owner não prova que o autor de uma pendência continua autorizado;
a sessão staff não tem a capability necessária para resolvê-la.

O teste PostgreSQL `test_orphaned_command_cannot_be_replaced_by_owner_or_mutated_by_staff`
demonstra ambas as fronteiras com o login restrito da aplicação. O código passa
a recusar substituição de falha e descarte de foto pendente por outro autor com
`VISUAL_CHANGE_STAFF_REQUIRED`. A identidade e a alteração original continuam
preservadas. O autor original ainda pode resolver suas próprias falhas enquanto
sua autorização de owner for válida. Isso é uma proteção parcial de C10;
não é uma implementação do suporte de recuperação.

## Capability mínima proposta, ainda não autorizada

Reusar a role de aplicação existente, as tabelas de pendências e auditoria e a
checagem `public.is_platform_staff()`. Não adicionar role, login, tabela,
SELECT/UPDATE geral, leitura de objetos ou troca de `app.actor_id`.

A proposta exige **duas funções estreitas `SECURITY DEFINER`**, com
`search_path=pg_catalog,public`, SQL estático, referências qualificadas,
`REVOKE ALL ... FROM PUBLIC` e `GRANT EXECUTE` somente para a role app existente.
Isso constitui uma capability nova e depende da revisão exigida pelo desenho
atual. Não está implicitamente autorizado pela decisão de produto C10.

Contratos propostos:

```sql
public.admin_visual_pending_changes(p_tenant uuid, p_business uuid, p_limit integer)
-- RETURNS TABLE(operation_id uuid, kind text, state text,
--   requested_at timestamptz, error_code text)

public.admin_cancel_visual_change(p_tenant uuid, p_business uuid,
  p_change uuid, p_recovery uuid)
-- RETURNS text: cancelled, replayed, not_found, author_active,
--   in_flight, upload_recovery_required, operation_conflict
```

Ambas recusam caller sem staff ativo, com `42501`, antes de qualquer consulta
privada. A listagem limita `p_limit` a 1–100 e exige tenant e negócio explícitos.
Só retorna `pending`/`failed` cujo autor perdeu autoridade, pelo predicado:

```sql
NOT EXISTS (
  SELECT 1 FROM public.memberships m
  JOIN public.user_accounts u ON u.id=m.actor_id
  WHERE m.tenant_id=c.tenant_id AND m.actor_id=c.actor_id
    AND m.active AND m.role='owner' AND u.active
)
```

Não retorna payload, resource key, hash, briefing, legenda, telefone, URL ou chave
de storage. Metadados só permitem identificar a operação e seu estado.

O cancelamento é a única ação proposta: nunca aplicar o comando antigo em nome
do staff ou de outro owner. O endpoint recebe `operation_id` de recuperação e
alvo explícito; não recebe identidade do autor nem documentos para substituição.
Rotas propostas: `GET /api/v1/admin/visual-changes` e
`POST /api/v1/admin/visual-changes/{change_id}/cancel`, com autenticação/MFA staff
vigente. A regra de recuperação permanece no serviço e a função só oferece a
capability atômica delimitada; nenhum endpoint é criado nesta entrega.

## Transação e limites propostos

1. Validar staff; adquirir a trava visual existente do negócio, sem mudar a
   identidade da sessão. A integração depende da ordem global de locks da fatia.
2. Bloquear a pendência alvo; verificar escopo e estado. Revalidar a perda de
   autoridade do autor com conta e membership, sem inferir isso do plano vencido.
3. Recusar enquanto houver `visual_consent_runs.state='in_flight'`, inclusive
   operação incerta ou lease vencida. Recuperação de autoria não prova término
   do efeito e não libera reserva financeira nem uma segunda chamada.
4. No primeiro recorte, recusar `photo_create` com
   `upload_recovery_required`. Uma PUT incerta não pode ser convertida em
   exclusão, publicação de foto ou retry só para liberar a fila. A evolução deve
   demonstrar quarentena dos bytes e bloqueio do escritor antigo antes de incluir
   esse caso; nenhuma limpeza física será acionada pelo suporte.
5. Para os demais comandos, mudar apenas `state='cancelled'` e `finished_at`.
   Preservar `actor_id`, payload, hash e operação original. Não executar o comando,
   substituir fontes, modificar prévia ou assumir identidade.
6. Inserir na mesma transação `audit_events` com tenant, ator staff real,
   `operation_id=p_recovery`, ação `visual.change_cancelled_by_staff` e
   `resource_id=p_change`. A unicidade existente `(tenant_id,operation_id,action)`
   protege replay; conferir ator e alvo antes de retornar `replayed`.
   Divergência retorna `operation_conflict`. Não há efeito assíncrono novo.

Essa revisão não resolveria uploads órfãos nem aplicaria outras pendências por
conta própria. Depois do cancelamento, os caminhos owner já existentes revalidam
o restante da fila e todas as admissões permanecem sujeitas aos gates vigentes.

## Validação necessária se a capability for aceita

Provar em PostgreSQL `_test` com login restrito: chamada direta por não staff
recusada; tenant/negócio/operacão divergentes; conta ou membership revogada;
autor ainda ativo; staff revogado; replay e conflito; corrida com admissão e
restauração de acesso; in-flight incerto; `photo_create` recusado; rollback
conjunto da mutação/auditoria; ausência de leitura privada fora dos metadados.
Os testes atuais demonstram a barreira vigente e a proteção contra outro owner;
não comprovam as funções propostas, que ainda não existem.
