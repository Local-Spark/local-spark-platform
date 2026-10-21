# Local Spark Platform

FastAPI/Python da Local Spark, plataforma de conteúdo para pequenos negócios.
F00 e primeiras fatias da F01 funcionam localmente. Geração, redes e cobrança
continuam nas fases seguintes. Autenticação própria substitui o Keycloak.

## Preparar o ambiente

Pré-requisitos: Python 3.13, uv, Docker Desktop. Na pasta do backend:

```bash
uv sync --frozen
cp -n .env.example .env
docker compose up -d postgres temporal mailpit
export LOCAL_SPARK_MIGRATION_DATABASE_URL=postgresql+asyncpg://postgres:local-spark-admin-password@localhost:55432/local_spark_platform
uv run alembic upgrade head
uv run python scripts/seed_operator.py
```

A migration cria tabelas/permissões. O seed prepara o login DB restrito de auth em
volumes existentes e as duas contas locais, preservando IDs, senhas e MFA já
configurados. Não apague volumes para atualizar o ambiente. Exemplos são locais;
produção usa segredos privados e migrações com login dedicado.

Para API no terminal:

```bash
uv run uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000
# Em outro terminal, entrega de e-mails:
uv run python -m app.entrypoints.auth_mail
```

Para rodar API, relay, worker Temporal e worker SMTP em containers:

```bash
docker compose --profile workers up -d --build
```

Para debug, abra **Local Spark: API (FastAPI)** no VS Code/F5. A tarefa para a API
Docker, libera 8000 e inicia postgres, Temporal, workers e Mailpit. No macOS usa
Docker Desktop por caminho absoluto para funcionar com VS Code aberto pelo Dock.
A API usa `.venv/bin/python` e `.env`, sem reload, com breakpoints. Após atualizar
autenticação, reinicie F5 e reconstrua o worker SMTP: `docker compose build auth-mail`.

Web: `../local-spark-web`, Node 24, `npm ci && npm run dev`.
Abra **http://localhost:5173** ou **http://127.0.0.1:5173**. Em desenvolvimento/teste,
a API aceita esses dois nomes de loopback na mesma porta e protocolo da
`LOCAL_SPARK_PUBLIC_WEB_URL`; links de e-mail continuam usando a URL configurada.
Em staging/produção, somente a origem configurada é aceita. Reinicie F5 após mudar
o código/configuração da API, pois o debug não usa reload.
Proxy `/api` vai para `127.0.0.1:8000`; ajuste `.env` da web para outra porta.

| Serviço | Endereço |
| --- | --- |
| Web | http://localhost:5173 |
| Swagger | http://localhost:8000/docs |
| Temporal UI | http://localhost:8233 |
| Mailpit (caixa de e-mails locais) | http://localhost:8025 |
| SMTP Mailpit para processos no host | localhost:11025 |
| PostgreSQL | localhost:55432 |

DBeaver: banco `local_spark_platform`, schema `public`, usuário administrativo
`postgres`, senha **local** `local-spark-admin-password`. API usa
`local_spark_runtime`; relay usa `local_spark_delivery`; autenticação/SMTP usam
`local_spark_identity`. Nenhum login de runtime tem superuser ou BYPASSRLS.

| Conta de desenvolvimento | Senha inicial |
| --- | --- |
| operator@local-spark.local | LocalSpark-Operator-2026! |
| cliente@local-spark.local | LocalSpark-Client-2026! |

O operador configura um autenticador TOTP no primeiro login e guarda os códigos
de recuperação. Depois usa o código do aplicativo ou um código de recuperação.
Cadastro público nunca concede staff. Contas antigas sem senha definem uma por
recuperação de e-mail, preservando UUID e negócios. E-mails locais chegam só ao
Mailpit, sem envio para destinatários externos. Telefone informado não é verificado.

## Cobrança e patrocínio — F01.5

Cliente: http://localhost:5173/app/billing; equipe: http://localhost:5173/admin/billing
(staff/MFA). Patrocínio de seis meses com motivo, revogável e sem renovação paga.
Pagantes live, testes e patrocinados aparecem separados. Stripe é o primeiro
adapter para teste/produção. Padrão `LOCAL_SPARK_BILLING_MODE=disabled`: sem cobrança
e sem consumir tarefas do provedor. Contratos em [SDD billing](docs/design/billing.md).

Para sandbox real, crie sua conta/sandbox Stripe e Price mensal BRL. Acrescente as
variáveis abaixo ao `.env` existente; preserve chaves de auth/criptografia:

```dotenv
LOCAL_SPARK_BILLING_MODE=test
LOCAL_SPARK_STRIPE_SECRET_KEY=sk_test_SUA_CHAVE
LOCAL_SPARK_STRIPE_WEBHOOK_SECRET=whsec_SEU_LISTENER
LOCAL_SPARK_STRIPE_PRICE_ID=price_SEU_PRECO
LOCAL_SPARK_BILLING_MONTHLY_AMOUNT_MINOR=9900
```

9900 é exemplo R$99 para sandbox, não preço comercial aprovado. Valor e moeda
precisam coincidir com o Price; nenhum preço/cartão vem do nosso formulário.
Login DB billing em `.env.example`. Nunca envie chaves no chat ou versione `.env`.

Com a [Stripe CLI](https://docs.stripe.com/webhooks#local-listener), encaminhe eventos:

```bash
stripe listen --forward-to http://localhost:8000/api/v1/webhooks/stripe
docker compose --profile workers up -d --build billing
```

Use o signing secret da CLI em WEBHOOK_SECRET e reinicie API F5/serviço billing.
Webhook snapshot/API 2026-02-25.clover, eventos listados no SDD. API e worker precisam
do mesmo PUBLIC_WEB_URL. Checkout retorna ao site, mas só confirmação canônica ativa
acesso. Credenciais do titular e sandbox real ainda não foram fornecidos/validados.

Produção: mesmo adapter, BILLING_MODE=live, sk_live_/secret/Price próprios,
BILLING_LIVE_ENABLED=true, HTTPS e roles/segredos na AWS. Antes, validar
sandbox/staging, plano/franquias/termos, cancelamento e conciliação operacional.
Compose/credenciais do repositório continuam locais; não houve deploy/cobrança real.

## Contratos

Onboarding inclui atividade livre, cor HEX e cidade/UF/código IBGE. Catálogos públicos
em GET `/api/v1/reference/states` e `/api/v1/reference/cities/{UF}`; nomes/IDs vêm do
[IBGE](https://servicodados.ibge.gov.br/api/docs/localidades), snapshot de 20/10/2026
com 27 UFs e 5.571 municípios. Atualização manual: `uv run python scripts/update_localities.py`;
revisar diff e testes antes de liberar. Nenhuma chamada externa acontece no cadastro.
Migration 0004 é aditiva; perfis antigos continuam com códigos nulos e replay válido.

Auth: POST `/api/v1/auth/register`, `/login`, `/mfa/verify`, `/refresh`, `/logout`,
`/verification-request`, `/verify-email`, `/password-reset-request`, `/reset-password`.
POSTs exigem Origin configurado; refresh/logout exigem cookie + `X-CSRF-Token`.
Swagger pode consumir endpoints de domínio com Bearer; o fluxo de login utiliza
as telas da web ou cliente HTTP que informe Origin corretamente.

Access JWT em memória, refresh em cookie HttpOnly e sessão revogável no banco;
Argon2id, CSRF, limites por IP/conta, MFA de staff e ações de uso único. Detalhes no
[SDD de auth](docs/design/native-auth.md). O seed legado que imprimia tokens foi aposentado.

POST `/api/v1/session` sincroniza perfil autenticado; GET `/api/v1/me` retorna
contexto. POST `/api/v1/onboarding` exige e-mail verificado e consentimentos;
cria tenant, owner, negócio, perfil, auditoria e outbox atomicamente. Replay devolve
os mesmos recursos; payload diferente retorna 409. Nenhum plano pago é ativado.
GET `/api/v1/admin/overview` e `/admin/organizations` exigem staff e auditam leituras.
POST/GET `/api/v1/businesses` validam Bearer, X-Tenant-ID e membership; criação
exige Idempotency-Key. Tokens antigos sem sessão são rejeitados.

## Qualidade

```bash
export TEST_ADMIN_DATABASE_URL=postgresql+asyncpg://postgres:local-spark-admin-password@localhost:55432/local_spark_platform_test
LOCAL_SPARK_MIGRATION_DATABASE_URL="$TEST_ADMIN_DATABASE_URL" uv run alembic upgrade head
uv run python scripts/prepare_local_tests.py
make ci
```

Pytest usa `.env.test.example`, `.env.test` opcional e `TEST_*` do processo com
precedência. Não utiliza o banco da aplicação como fallback. PostgreSQL/Temporal
indisponíveis causam falha, sem skips. O harness só limpa banco com sufixo `_test`.
Unitários/integração real: 103 testes, gate 100% de linhas/branches em todos os
módulos de produção, sem exclusões para elevar cobertura. `make unit` roda a fatia
unitária; a cobertura completa inclui integração. Browser isolado é documentado
no [README web](../local-spark-web/README.md).

## CI e produção

GitHub Actions faz lint, tipos, testes, coverage, rollback/reaplicação e build.
Deploy manual ECS usa OIDC do GitHub para AWS, ECR e commit com CI verde. Esse OIDC
é independente da autenticação dos usuários. AWS/IaC, serviços, SMTP real, chaves,
observabilidade e staging ainda precisam ser provisionados/configurados; não houve
push, CI remoto ou deploy nesta entrega. Ver [operação](docs/operations.md).

## Documentação viva

[Contexto](docs/PROJECT.md), [SDD geral](docs/SDD.md), [fases](docs/phases/README.md),
[autenticação própria](docs/design/native-auth.md), [regras de continuidade](AGENTS.md).
