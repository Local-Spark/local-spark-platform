# Local Spark Platform

Backend Python da Local Spark para conteúdo de pequenos negócios;
primeira entrega: **F00 — fundação**, não uma pipeline de geração/publicação já pronta.

Usa o padrão organizacional de `spotlight-api`: `app/core`, `app/api/v1`,
`app/schemas`, `app/services`, migrações Alembic, Python 3.13 e uv. O isolamento é
por tabelas compartilhadas/RLS; execução durável é Temporal, sem Celery/RabbitMQ.
Não há dependência dos pacotes privados, contas ou segredos do Spotlight.

## Desenvolvimento

Para subir todos os serviços em Docker, na primeira execução:

```bash
docker compose up -d postgres temporal
docker compose run --rm --build \
  -e LOCAL_SPARK_MIGRATION_DATABASE_URL=postgresql+asyncpg://postgres:local-spark-admin-password@postgres:5432/local_spark_platform \
  api alembic upgrade head
docker compose --profile workers up -d --build
```

Nas próximas execuções: `docker compose --profile workers up -d --build`.
Swagger em http://localhost:8000/docs; Temporal UI em http://localhost:8233.
PostgreSQL: localhost:55432, banco `local_spark_platform`, usuário administrativo
`postgres`, senha local `local-spark-admin-password`. API e workers usam logins
restritos distintos. Dados locais persistem em volumes nomeados do projeto.

Para executar Python fora dos containers com recarga automática:

```bash
uv sync --frozen
docker compose up -d postgres temporal
export LOCAL_SPARK_MIGRATION_DATABASE_URL=postgresql+asyncpg://postgres:local-spark-admin-password@localhost:55432/local_spark_platform
uv run alembic upgrade head
# Copiar apenas se ainda não existir um .env local:
cp -n .env.example .env
uv run uvicorn app.main:create_app --factory --reload
```

Compose cria logins locais sem privilégios administrativos; Alembic cria as roles
de acesso e RLS. A role runtime não é dona das tabelas e não possui BYPASSRLS.
Migração é comando separado, não startup de cada réplica. O banco/volume local é
exclusivo deste projeto. Nunca usar as credenciais locais em staging/produção.

Para processar a outbox, em outros terminais:

```bash
uv run python -m app.entrypoints.worker
uv run python -m app.entrypoints.relay
```

## Debug no VS Code

Abrir a pasta `local-spark-platform`, instalar as extensões recomendadas Python e
Python Debugger e escolher **Local Spark: API (FastAPI)** em Run and Debug (F5).
Usa `.venv/bin/python`, carrega `.env` e inicia a factory com Uvicorn em
http://127.0.0.1:8000; Swagger em http://127.0.0.1:8000/docs.

A tarefa anterior ao debug para a API Docker para liberar a porta 8000 e sobe
PostgreSQL, Temporal, worker e relay. Docker Desktop deve estar aberto; `.venv`,
`.env` e migrations precisam estar preparados conforme Desenvolvimento. A API
roda localmente sem reload, com breakpoints; workers continuam nos containers.
Ao encerrar F5, dependências permanecem ativas. Para voltar à API Docker:
`docker compose up -d api`.

No macOS, as pré-tarefas usam `/Applications/Docker.app/Contents/Resources/bin/docker`
e incluem esse diretório no PATH. Isso permite abrir o VS Code pelo Dock/Finder
sem depender da configuração de PATH do terminal. Docker Desktop deve estar em
`/Applications/Docker.app`; outro local exige ajustar o bloco `osx` em `tasks.json`.

No DBeaver, criar conexão PostgreSQL: host `localhost`, porta `55432`, banco
`local_spark_platform`, usuário `postgres`, senha local `local-spark-admin-password`.
As tabelas ficam no schema `public`. `local_spark_platform_test` é exclusivo dos testes.

## Contratos da API

`POST /api/v1/businesses` exige Bearer JWT válido, `X-Tenant-ID`, membership de escrita
e `Idempotency-Key`. O tenant não é confiado só pelo header. A criação persiste
negócio, idempotência, auditoria e outbox atomicamente; o workflow registra o evento.
`GET /api/v1/businesses` tem cursor UUID e limite de 100. Não ordena por cronologia.

F00 verifica tokens HS256 já emitidos por um emissor confiável configurado; não há
cadastro/login público, recuperação de senha, MFA ou emissão pública de tokens.
Integração OIDC e onboarding público são parte da F01. Não expor F00 como SaaS pronto.

Para experimentar endpoints protegidos localmente, `uv run python scripts/seed_development.py`
cria uma organização/usuário de demonstração e imprime token de uma hora. Requer
`.env` e `LOCAL_SPARK_MIGRATION_DATABASE_URL` para o mesmo banco em loopback. O script
recusa produção e não cria endpoint de autenticação. Tratar o token como credencial
local temporária; não versionar sua saída.

## Qualidade

```bash
make lint
make types
make unit
# Preparação inicial do banco exclusivo de testes, após subir postgres e temporal:
export TEST_ADMIN_DATABASE_URL=postgresql+asyncpg://postgres:local-spark-admin-password@localhost:55432/local_spark_platform_test
LOCAL_SPARK_MIGRATION_DATABASE_URL="$TEST_ADMIN_DATABASE_URL" uv run alembic upgrade head
uv run python scripts/prepare_local_tests.py
make ci
```

Após essa preparação, `make test` ou `uv run python -m pytest --cov=app` executam
a suíte completa. O pytest carrega os exemplos locais de `.env.test.example`,
depois os ajustes opcionais de `.env.test`; variáveis `TEST_*` exportadas têm
precedência, inclusive no CI. `.env.test` fica fora do Git. Não usa o banco da
configuração da aplicação como fallback. PostgreSQL e Temporal precisam estar
disponíveis: a integração falha quando indisponível, sem skips silenciosos.

O harness recusa limpar banco sem `_test` no nome. Integração usa PostgreSQL real,
incluindo RLS com login sem bypass, concorrência e rollback. Configurar credenciais
e migrações do banco de teste conforme `scripts/prepare_local_tests.py`.
Coverage de linhas/branches usa todos os módulos `app`, excluindo apenas testes;
gate **100%**, com **62 testes passando**. Não exclui serviços para alcançar a meta.
`make unit` executa apenas unitários; a cobertura completa inclui testes de integração.

## CI/CD

GitHub Actions executa lint, tipos, testes unitários/integrados/workflow e coverage;
build do container é verificado no CI. Relatórios são artefatos do job. O remoto Git
já está configurado; a implementação e os workflows ainda não foram enviados/executados.

O deploy manual usa OIDC, ECR e ECS, depende de CI verde para o mesmo commit e de
environment protegido. Exige recursos/roles/variáveis AWS configurados; a F00 não
provisiona AWS nem executa migrações de produção automaticamente. Ver `docs/operations.md`.

## Documentação viva

- [Resumo de negócio, decisões e andamento](docs/PROJECT.md).
- [SDD geral](docs/SDD.md).
- [Fases e critérios de integração](docs/phases/README.md).
- [F00: escopo, execução e resultados](docs/phases/F00-foundation.md).
- [Especificações detalhadas de arquitetura](docs/design/README.md).
- [Regras para continuidade por agentes](AGENTS.md).
