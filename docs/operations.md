# Operação e deploy

F00 é fundação local. Antes de expor a clientes: onboarding/auth completo, app reviews,
políticas e gates das fases seguintes. Nunca usar `.env.example` em produção.

## Ambiente local

`docker compose up -d postgres temporal`; migração separada com conexão administrativa.
O SQL de inicialização cria logins locais sem bypass e banco `local_spark_platform_test`. As roles
de acesso são concedidas sem propriedade das tabelas. Se volume já existe, initializer
não roda novamente; não apagar volumes para corrigir migrações de usuário.

PostgreSQL em 55432; Temporal gRPC 7233 e UI 8233, todos ligados ao loopback.
Temporal start-dev é exclusivamente desenvolvimento/CI, não topologia de produção.
Seu SQLite fica no volume nomeado `local-spark-platform_local-spark-temporal`,
preservando o histórico ao recriar o container de desenvolvimento.
Isso não representa persistência/HA de produção nem substitui Temporal Cloud.
API só sobe após migration; health live não acessa DB, ready valida DB migrado.

## Runtime

API: `uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --no-access-log`.
Worker: `python -m app.entrypoints.worker`. Relay: `python -m app.entrypoints.relay`.
API/worker usam runtime login; relay tem URL específica e só acessa outbox. Owner
credencial serve apenas a migrações/provisionamento, nunca é variável de runtime.

Outbox fica `failed` após falhas repetidas conhecidas de entrega e precisa intervenção.
Lease perdido é reivindicável; fencing impede confirmação tardia. Temporal rejeita
workflow ID repetido inclusive depois de concluído dentro da retenção/contrato; o
consumer no banco também deduplica o evento, independentemente dessa retenção.
Expiração do histórico não deve ser usada para repetir operação paga: fases futuras
mantêm tombstones e operação externa persistente.

## GitHub Actions / AWS

Configurar environments `staging` e `production` com permissões e revisores conforme
política do time, OIDC restrito a repo/environment, sem chaves AWS permanentes.
Variáveis: AWS_REGION, AWS_ROLE_ARN, ECR_REPOSITORY, ECS_CLUSTER, ECS_SERVICE,
ECS_TASK_FAMILY e ECS_CONTAINER_NAME. Infra cria task definition com secret refs e
IAM mínimos. TLS Temporal é obrigatório fora de desenvolvimento.

`Deploy ECS` é manual, somente main e mesmo SHA de CI verde. Publica tag de commit
em ECR e atualiza serviço ECS existente. Antes do deploy, aplicar migrações compatíveis
por tarefa separada com role de migração e confirmar `database_ready`. Não executar
DDL com login runtime. Workflow não provisiona conta/infra nem garante rollback de
schema; expand/contract e estratégia de workers ativos fazem parte da F08.

O remoto Git já está configurado. Variáveis, roles e recursos AWS ainda precisam
ser configurados; o pipeline não foi executado remotamente. Não foi feita nenhuma
alteração na AWS/GitHub.
