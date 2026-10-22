# Meu Braço Direito — renomeação do produto

Decisão de 22/10/2026: **Meu Braço Direito** é a marca do produto. Somente nomes
e caminhos dos repositórios Git permanecem iguais. Os identificadores novos são:

| Uso | Identificador |
| --- | --- |
| Prefixo de configuração Python | `MEU_BRACO_DIREITO_` |
| Pacotes | `meu-braco-direito-platform`, `meu-braco-direito-web` |
| Projeto Compose | `meu-braco-direito-platform` |
| Bancos local e de testes | `meu_braco_direito_platform`, `meu_braco_direito_platform_test` |
| Roles e logins | `meu_braco_direito_*` |
| JWT issuer / audience | `meu-braco-direito-local` / `meu-braco-direito-api` |
| Fila Temporal padrão | `meu-braco-direito-foundation` |
| Cookies | `meu-braco-direito-refresh`, `meu-braco-direito-csrf` |
| Domínio fictício local | `meu-braco-direito.local` |

Os cookies conservam HttpOnly/Secure/host-only, prefixo `__Host-` em HTTPS e as
proteções Origin/CSRF. A mudança exige novo login. Não compartilhar tokens ou
transferir credenciais entre cookies antigos e novos.

## Atualização de uma instalação existente

1. Parar API/workers locais e criar backup do PostgreSQL e dos volumes antes de
   qualquer alteração. Não usar `down -v`, apagar bancos ou rodar fixtures de testes
   no banco da aplicação. Encerrar gravações antes da cópia física de volumes.
2. Migrar as chaves do `.env` para `MEU_BRACO_DIREITO_`. Conservar exatamente as
   chaves de criptografia, credenciais reais de provedores e demais segredos. Não
   substituir uma chave criptográfica por um exemplo para trocar o nome do produto.
3. Executar Alembic com `MEU_BRACO_DIREITO_MIGRATION_DATABASE_URL` ainda apontando
   para o banco existente. `0015_product_brand` renomeia roles sem recriá-las,
   preservando OIDs, memberships, grants e políticas RLS. A migração precede a
   `0015_whatsapp_message_routing` que já estava em desenvolvimento. Se existem
   roles com os dois nomes, a migração aborta atomicamente; revisar o conflito sem
   excluir roles e perder permissões.
4. Conectado ao banco administrativo `postgres`, sem conexões abertas nos bancos
   afetados, renomear `local_spark_platform` e `local_spark_platform_test` para os
   respectivos nomes novos. Atualizar URLs no `.env` e credenciais dos logins locais
   em conjunto. As senhas reais de usuários e o MFA não devem ser alterados.
5. Copiar os volumes PostgreSQL e Temporal parados para os nomes usados pelo novo
   Compose. Conservar os volumes originais e o backup SQL para recuperação. Subir
   dependências e reconstruir workers com a configuração nova. Reiniciar o F5 da
   API para reler `.env`; processos já carregados não mudam de configuração sozinhos.
6. Conferir IDs/contagens, status de assinatura, RLS, `/health/ready`, login/MFA,
   refresh/logout e e-mails antes de retomar o uso. Validar testes em banco `_test`
   separado. Se houver workflows ainda ativos na fila antiga, manter um worker
   de drenagem nessa fila até terminarem; não recriar workflows com novos IDs.

A atualização local desta entrega fez backup SQL completo e conservou os volumes
originais. Os backups ficam em `.local/rebrand-before/`, ignorado pelo Git. A
cópia nova usa os nomes do produto e conserva o histórico Temporal.

## Compatibilidade e histórico

- IDs de usuários, negócios, tenants, sessões, eventos e assinaturas não mudam.
  As duas contas fictícias locais recebem o novo domínio; outros e-mails privados
  não são reescritos. IDs das contas de demonstração são constantes preservadas.
- Cada checkout anterior conserva o prefixo de idempotência enviado à Stripe na
  coluna `provider_key_prefix`. Novos checkouts recebem o prefixo da marca atual.
  Repetir uma intenção não cria outra cobrança por causa da renomeação.
- Downgrade da marca mantém nomes operacionais e chaves congeladas. Reaplicação
  é idempotente; rollback de schema não descarta essas identidades externas.
- E-mails cifrados pendentes são apresentados com a marca atual no momento do
  envio, conservando links/tokens e sem recifrar conteúdo ou mudar destinatários.
- Referências antigas só são intencionais nos caminhos Git, na migração/testes
  de compatibilidade, em identificadores externos já usados e nos backups.
  Não reescrever payloads/auditoria ou histórico Temporal por razões cosméticas.
- `Sparkles` é o nome de um ícone genérico da biblioteca Lucide, usado para ações
  de criação; não é texto da marca. Logotipo e favicon usam o símbolo de parceria.
- Domínio/remetente público, identidade da conta Stripe e nomes exibidos por
  serviços externos dependem de configuração nas respectivas contas. Este código
  não registra domínio, muda conta externa nem efetua publicação.
