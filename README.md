# Meu Braço Direito Platform

22/10/2026 — Produto renomeado para **Meu Braço Direito**. Diretórios e remotos
Git permanecem `local-spark-platform`/`local-spark-web`; os pacotes, Compose,
variáveis `MEU_BRACO_DIREITO_`, bancos e roles usam os identificadores novos.
A migração `0015_product_brand` precede a correlação WhatsApp, preserva IDs,
senhas/MFA e permissões, atualiza as duas identidades de demonstração e congela
as chaves Stripe de checkouts anteriores. Contas existentes conservam suas senhas;
as senhas de exemplo abaixo valem para instalações novas. Instruções e exceções
de compatibilidade em [renomeação do produto](docs/product-rename.md).


FastAPI/Python da Meu Braço Direito, plataforma de conteúdo para pequenos negócios.
F00 e as fatias locais da F01 funcionam. Checkout de teste e reconciliação estão
implementados; geração/publicação continuam nas fases seguintes. A verificação
de telefone precisa de conta Twilio e staging para homologação. Autenticação
própria substitui o Keycloak.
F02.1 já recebe callbacks WhatsApp assinados em uma inbox criptografada, desativada
por padrão. F02.2a comprova o vínculo do remetente ao negócio; processamento do
material ainda aguarda as próximas fatias de F02.2.
F02.2b1 prepara a correlação de mensagens com login e fila cifrada separados.
Essa fila ainda não inicia IA ou publicação.

## Preparar o ambiente

Pré-requisitos: Python 3.13, uv, Docker Desktop. Na pasta do backend:

```bash
uv sync --frozen
cp -n .env.example .env
docker compose up -d postgres temporal mailpit
export MEU_BRACO_DIREITO_MIGRATION_DATABASE_URL=postgresql+asyncpg://postgres:meu-braco-direito-admin-password@localhost:55432/meu_braco_direito_platform
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

Para debug, abra **Meu Braço Direito: API (FastAPI)** no VS Code/F5. A tarefa para a API
Docker, libera 8000 e inicia postgres, Temporal, workers e Mailpit. No macOS usa
Docker Desktop por caminho absoluto para funcionar com VS Code aberto pelo Dock.
A API usa `.venv/bin/python` e `.env`, sem reload, com breakpoints. Após atualizar
autenticação, reinicie F5 e reconstrua o worker SMTP: `docker compose build auth-mail`.

Web: `../local-spark-web`, Node 24, `npm ci && npm run dev`.
Abra **http://localhost:5173** ou **http://127.0.0.1:5173**. Em desenvolvimento/teste,
a API aceita esses dois nomes de loopback na mesma porta e protocolo da
`MEU_BRACO_DIREITO_PUBLIC_WEB_URL`; links de e-mail continuam usando a URL configurada.
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

DBeaver: banco `meu_braco_direito_platform`, schema `public`, usuário administrativo
`postgres`, senha **local** `meu-braco-direito-admin-password`. API usa
`meu_braco_direito_runtime`; relay usa `meu_braco_direito_delivery`; autenticação/SMTP usam
`meu_braco_direito_identity`. Nenhum login de runtime tem superuser ou BYPASSRLS.

| Conta de desenvolvimento | Senha inicial |
| --- | --- |
| operator@meu-braco-direito.local | MeuBracoDireito-Operator-2026! |
| cliente@meu-braco-direito.local | MeuBracoDireito-Client-2026! |

O operador configura um autenticador TOTP no primeiro login e guarda os códigos
de recuperação. Depois usa o código do aplicativo ou um código de recuperação.
Cadastro público nunca concede staff. Operadores adicionais são convidados em
`/admin/staff` por outro operador com MFA. Contas antigas sem senha definem uma por
recuperação de e-mail, preservando UUID e negócios. E-mails locais chegam só ao
Mailpit, sem envio para destinatários externos. Telefone informado só se torna
verificado após confirmação pelo provedor configurado.

## WhatsApp — F02.1

`GET/POST /api/v1/webhooks/whatsapp` implementam desafio e recebimento da Meta
Cloud API. Sem configuração real, respondem 503. Mensagens e status autenticados
entram numa inbox isolada e criptografada; ainda não aparecem na área do cliente
nem iniciam geração. O SMS confirmado na F01 não vincula automaticamente uma
conversa do WhatsApp ao negócio. Consulte [F02](docs/phases/F02-whatsapp-ingestion.md)
e [operação](docs/operations.md) antes de configurar App/WABA, número, secrets,
login PostgreSQL dedicado e callback HTTPS. A migration 0014 deve preceder a API.
F02.2a expõe `GET/POST /api/v1/organizations/{tenant_id}/businesses/{business_id}/whatsapp-link`
e `POST .../confirm`: o dono com telefone verificado e plano ativo envia ao número
oficial o código retornado e confirma após o webhook. A interface e o smoke real
Meta ainda faltam; mensagens permanecem em quarentena, sem gerar conteúdo.

## Cobrança e patrocínio — F01.5

Cliente: http://localhost:5173/app/billing; equipe: http://localhost:5173/admin/billing
(staff/MFA). Patrocínio de seis meses com motivo, revogável e sem renovação paga.
Pagantes live, testes e patrocinados aparecem separados. Stripe é o primeiro
adapter para teste/produção. Padrão `MEU_BRACO_DIREITO_BILLING_MODE=disabled`: sem cobrança
e sem consumir tarefas do provedor. Contratos em [SDD billing](docs/design/billing.md).
O admin mostra também checkouts abertos ou expirados sem acesso ativo, com negócio,
prazo e contatos cadastrados. O endpoint paginado é
`GET /api/v1/admin/billing/opportunities?state=open&limit=10` (staff/MFA).

Para sandbox real, crie sua conta/sandbox Stripe e Price mensal BRL. Acrescente as
variáveis abaixo ao `.env` existente; preserve chaves de auth/criptografia:

```dotenv
MEU_BRACO_DIREITO_BILLING_MODE=test
MEU_BRACO_DIREITO_STRIPE_SECRET_KEY=sk_test_SUA_CHAVE
MEU_BRACO_DIREITO_STRIPE_WEBHOOK_SECRET=whsec_SEU_LISTENER
MEU_BRACO_DIREITO_STRIPE_PRICE_ID=price_SEU_PRECO
MEU_BRACO_DIREITO_BILLING_MONTHLY_AMOUNT_MINOR=9900
```

9900 é exemplo R$99 para sandbox, não preço comercial aprovado. Valor e moeda
precisam coincidir com o Price; nenhum preço/cartão vem do nosso formulário.
Login DB billing em `.env.example`. Nunca envie chaves no chat ou versione `.env`.

Com a [Stripe CLI](https://docs.stripe.com/webhooks#local-listener), encaminhe eventos:

```bash
stripe listen --all-snapshot --forward-to http://localhost:8000/api/v1/webhooks/stripe
docker compose --profile workers up -d --build billing
```

Use o signing secret da CLI em WEBHOOK_SECRET e reinicie API F5/serviço billing.
Webhook snapshot/API 2026-02-25.clover, eventos listados no SDD. API e worker precisam
do mesmo PUBLIC_WEB_URL. Checkout retorna ao site, mas só confirmação canônica ativa
acesso. Pagamento sandbox foi confirmado em 21/10; demais cenários e staging pendentes.

Se o listener parar durante um pagamento, não refaça a compra. O billing worker
agora agenda reconciliação canônica de checkouts abertos a cada 30 segundos; a
assinatura muda apenas após consulta confiável à Stripe. Reinicie o worker após
atualizar o código: `docker compose --profile workers up -d --build billing`.

## Telefone e operadores — F01.6

Cliente: `/app/phone`; equipe: `/admin/staff`. O telefone é confirmado via Twilio
Verify; o modo padrão `MEU_BRACO_DIREITO_PHONE_VERIFY_MODE=disabled` não envia código nem
marca número como verificado. Para habilitar, crie um Verify Service/API key e
configure as variáveis comentadas em `.env.example`, preservando seus segredos no
`.env` local. SMS é o canal padrão; WhatsApp exige habilitação no provedor. A
confirmação do telefone não vincula o WhatsApp da F02. Convites de operadores são
entregues pelo worker `auth-mail`, com e-mail verificado, token único e MFA próprio.
O operador convidado não precisa cadastrar negócio: enquanto o convite estiver
pendente, `GET /api/v1/staff/invitations/pending` leva à orientação de aceite.
E-mails transacionais usam HTML com alternativa em texto; o worker também renderiza
payloads antigos da API por assunto/link. Reinicie a API no debug após atualizar
o código e reconstrua `auth-mail` para carregar o template.
Entrega real do código e validação AWS/staging ainda dependem de contas externas.

Retorno do checkout preserva a origem autorizada do navegador que iniciou o pedido.
Em desenvolvimento, localhost/127.0.0.1 funcionam com a mesma porta/protocolo;
produção usa somente PUBLIC_WEB_URL. Migration 0006 é necessária antes de reiniciar
API e billing. Links já criados conservam a origem antiga: se ocorrer logout ao
voltar, entre novamente nesse endereço e consulte o plano, sem pagar outra vez.
Em 21/10, pagamento de sandbox foi confirmado; demais cenários continuam pendentes.

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
export TEST_ADMIN_DATABASE_URL=postgresql+asyncpg://postgres:meu-braco-direito-admin-password@localhost:55432/meu_braco_direito_platform_test
MEU_BRACO_DIREITO_MIGRATION_DATABASE_URL="$TEST_ADMIN_DATABASE_URL" uv run alembic upgrade head
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
