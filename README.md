# Meu Braço Direito Platform

Backend Python/FastAPI para pequenos negócios produzirem conteúdo a partir do
WhatsApp. O produto usa PostgreSQL/RLS, Temporal, storage compatível com S3 e
web React separada. Nome de produto: **Meu Braço Direito**; os diretórios/remotos
continuam `local-spark-platform` e `local-spark-web`.

**Estado em 27/10/2026:** identidade, onboarding, billing sandbox, ingestão e
processamento de materiais, contexto/roteiros, kits BL01/BL02, acervo manual
BL03.1/BL03.2 e prévias/revisões funcionam localmente. A publicação do percurso
local é **simulada**. IA visual, importação automática de cardápio BL03.3,
proatividade, Meta/Instagram reais e AWS de produção não estão concluídos. As prévias Pillow/FFmpeg são baseline técnico, não receitas
com qualidade comercial aprovada. Próxima fase: **BL04, acervo e kit na geração**.
Avatar/voz (F05) permanecem planejados para depois do primeiro piloto comercial,
após validar imagens/vídeos com material real, qualidade e custo.
Ver [contexto vigente](docs/PROJECT.md), [SDD](docs/SDD.md) e [fases](docs/phases/README.md).

## Ambiente local

Pré-requisitos: Python 3.13, uv, Docker Desktop; Node 24 para o frontend.
Na pasta do backend, para instalação nova:

```bash
uv sync --frozen
cp -n .env.example .env
docker compose up -d postgres temporal mailpit
uv run --env-file .env alembic upgrade head
uv run --env-file .env python scripts/seed_operator.py
```

`cp -n` preserva `.env` existente. Compare-o com `.env.example` quando aparecerem
variáveis novas; preserve chaves de autenticação/criptografia e dados. O comando
de migration usa o login administrativo configurado em
`MEU_BRACO_DIREITO_MIGRATION_DATABASE_URL`. Atualize até o head antes de iniciar
o código novo; não apague volumes nem recrie o banco para migrar.
A migração `0038` retira `billing_outbox` e preserva eventos faltantes em audit;
jobs/reconciliação continuam. As migrações `0039`/`0040` criam catálogo e fotos
privadas da BL03. Não reescrever migrations já publicadas.

O seed é exclusivo de desenvolvimento local: cria as duas contas demo e prepara
logins restritos necessários, preservando IDs, senhas e MFA existentes. Não
provisiona plano pago ou credenciais de produção. O seed antigo foi retirado;
use somente `scripts/seed_operator.py`.

Para rodar o conjunto local em containers:

```bash
docker compose --profile workers up -d --build
```

O perfil inclui API, worker Temporal, correlator/dispatcher WhatsApp, cobrança,
e-mail e storage, além das dependências. Integrações externas continuam sujeitas
à configuração de cada capacidade. O relay genérico de recibos não inicia
nesse perfil; `legacy-relay` foi mantido apenas para recuperação de históricos,
sem necessidade na rotina nova. Não confundir essa simplificação com remoção
do Temporal ou dos jobs de domínio.

Para desenvolver a API no terminal com workers em containers:

```bash
docker compose stop api
uv run --env-file .env uvicorn app.main:create_app --factory --reload --host 127.0.0.1 --port 8000
```

No VS Code, abra **Meu Braço Direito: API (FastAPI)** e use F5. A tarefa para a
API Docker, libera 8000 e sobe as dependências de debug. O debug usa `.venv`,
`.env` e breakpoints, sem reload; reinicie F5 após mudar código/configuração.
Para testar todas as fatias de mídia/WhatsApp, mantenha também o perfil completo
`workers` ativo. No macOS as tarefas usam o caminho do Docker Desktop para
funcionar com VS Code aberto pelo Dock.

No repositório web:

```bash
cd ../local-spark-web
npm ci
npm run dev
```

O proxy `/api` aponta para `127.0.0.1:8000`. Abra localhost ou 127.0.0.1 na porta
5173. Em development/testing, aliases locais precisam ter a mesma porta/protocolo
de `MEU_BRACO_DIREITO_PUBLIC_WEB_URL`; em staging/produção a origem é exata.
Links de e-mail usam a URL canônica configurada.

| Serviço | Endereço local |
| --- | --- |
| Web | http://localhost:5173 |
| Swagger | http://localhost:8000/docs |
| Temporal UI | http://localhost:8233 |
| Storage S3 (perfil workers) | http://localhost:9000 |
| Mailpit, e-mails capturados | http://localhost:8025 |
| SMTP no host | localhost:11025 |
| PostgreSQL | localhost:55432 |

DBeaver: banco `meu_braco_direito_platform`, schema `public`, usuário `postgres`,
senha **local** `meu-braco-direito-admin-password`. Os processos usam logins
restritos por capacidade, não o administrador. As credenciais de exemplo não
servem para produção. A [renomeação](docs/product-rename.md) documenta a
preservação das instalações antigas.

## Contas e navegação

| Conta demo de instalação nova | Senha inicial local |
| --- | --- |
| operator@meu-braco-direito.local | MeuBracoDireito-Operator-2026! |
| cliente@meu-braco-direito.local | MeuBracoDireito-Client-2026! |

Contas já existentes conservam suas senhas. O operador configura TOTP no primeiro
login e guarda os códigos de recuperação. Cadastro público não concede staff;
novos operadores são convidados em `/admin/staff` por outro operador com MFA.
Operador convidado não precisa cadastrar negócio. E-mail de verificação,
recuperação e convite chega ao Mailpit no ambiente local, em HTML com alternativa
texto. Atualize API e container `auth-mail` para carregar mudanças de template.

Menus do cliente: Início, WhatsApp, Sobre meu negócio, Conteúdos, Kits visuais e
Plano e acesso. A seleção de organização/negócio é compartilhada. Telefone e
vínculo são configurados por WhatsApp. O uso de IA tem um único aceite em
Plano e acesso antes da contratação; não há permissões por fornecedor em
WhatsApp ou Sobre meu negócio. Conteúdos acompanha/revisa as peças disponíveis, sem obrigar sequência
manual de ideia/roteiro/render. A geração manual fica em `/app/editorial-lab`,
somente DEV. `/app/ideas` redireciona para `/app/content`; `/app/guide` para Início.

A vitrine `/kits` é pública, com mídia fictícia reutilizada; `/app/kits` permite
escolha/edição guiada por negócio. O kit piloto continua `public_demo`, para
uso local/teste, sem liberação comercial. Selecionar ou confirmar kit não gera
nova imagem, não ativa plano e não publica.

## Configurar integrações opcionais

Os nomes e valores de exemplo estão em `.env.example`. Não versione `.env` nem
envie chaves por chat. API e workers precisam receber a mesma configuração
pertinente; reinicie o debug e reconstrua os serviços alterados. Em produção,
usar segredos e logins próprios, sem padrões locais.

**WhatsApp oficial.** `GET/POST /api/v1/webhooks/whatsapp` fazem desafio e inbox
assinada/criptografada. Sem configuração, a capacidade fica indisponível.
Configure App/WABA, número, secrets, token Graph, versão da API, callback HTTPS
e storage conforme [F02](docs/phases/F02-whatsapp-ingestion.md) e
[operação](docs/operations.md). O dono precisa de telefone verificado, acesso
ativo, aceite do serviço e vínculo do remetente; confirmar SMS não vincula a
conversa. Envios associados de texto, imagem, áudio e vídeo são preservados sem
expiração automática e sem exclusão pelo histórico/API (migration 0058). O
histórico fica como consulta secundária em WhatsApp; fotos desatualizadas do
acervo continuam removíveis. A homologação real da Meta ainda está pendente; ensaios locais usam
fixtures/mocks. Recebimento implementado não implica envio/publicação completos.

**Telefone.** Twilio Verify é usado para confirmar posse do número, com SMS como
canal padrão. `MEU_BRACO_DIREITO_PHONE_VERIFY_MODE=disabled` não envia código nem
marca telefone como verificado. Habilite o modo/provedor e as variáveis Twilio
comentadas em `.env.example`. O SMS vai para o telefone do negócio; corrigir o
número pela configuração WhatsApp antes de solicitar novo código. Validação por
ambiente/staging continua necessária.

**IA.** OpenAI tem adapters de texto editorial e transcrição opcionais,
aceite único do serviço por negócio e limites internos configurados; os modos
são desabilitados por padrão. O default editorial é `gpt-5-mini`, configurável; a transcrição referencia
`gpt-transcribe`. O worker pode usar Jev para interpretação experimental do
acervo em desenvolvimento/teste, sob o mesmo aceite único e orçamento explícito.
Ainda não há IA visual integrada, skills executáveis por cliente ou pesquisa
automática de concorrentes no produto.
Os ensaios visuais em [evals](docs/evals/) são separados. Ter uma chave/saldo não
habilita automaticamente toda a jornada nem comprova qualidade/custo comercial.

**Stripe.** Use uma conta/sandbox e Price mensal em BRL. Acrescente ao `.env`
existente os dados do ambiente de teste:

```dotenv
MEU_BRACO_DIREITO_BILLING_MODE=test
MEU_BRACO_DIREITO_STRIPE_SECRET_KEY=sk_test_SUA_CHAVE
MEU_BRACO_DIREITO_STRIPE_WEBHOOK_SECRET=whsec_SEU_LISTENER
MEU_BRACO_DIREITO_STRIPE_PRICE_ID=price_SEU_PRECO
MEU_BRACO_DIREITO_BILLING_MONTHLY_AMOUNT_MINOR=9900
```

9900 é exemplo de R$ 99 no sandbox; precisa corresponder ao Price, moeda e
intervalo. Os dados de cartão são coletados pelo checkout Stripe. O valor não é
franquia ou preço comercial aprovado. Com a Stripe CLI autenticada:

```bash
stripe listen --all-snapshot --forward-to http://localhost:8000/api/v1/webhooks/stripe
```

Use o signing secret do listener no `.env`, reinicie a API e atualize o worker:

```bash
docker compose --profile workers up -d --build billing
```

Só confirmação canônica ativa acesso; fechar a aba ou voltar do checkout não
prova pagamento. O worker reconcilia checkouts abertos periodicamente, inclusive
quando o webhook não chegou. Se o listener parar, consulte/aguarde reconciliação
antes de pagar novamente. Pagantes live, testes e patrocínios são separados no
cliente/admin; o painel também mostra oportunidades de checkout sem acesso ativo.
Contrato de webhook/eventos/cancelamento em [billing](docs/design/billing.md).

Produção usa o mesmo adapter com `BILLING_MODE=live`, chaves/Price próprios,
`BILLING_LIVE_ENABLED=true`, HTTPS e gates operacionais. Não há cobrança comercial
ou deploy AWS demonstrados por esta entrega.

## Próxima implementação aprovada

A BL04.2 precisa concluir a coordenação e ligar o provedor visual real. As
novas decisões são: concluir criação já iniciada e permitir revisão se o plano
vencer (bloqueando novas criações/publicação); preservar prévias sem expiração
com conta ativa; recuperação de pendência com autor sem acesso somente por
staff, com ação registrada. **Ainda não estão implementadas.** O código segue
usando prazos de propostas/prévias e verificações de plano; a 0058 trata apenas
materiais WhatsApp. URL assinada e validade de fatos/decisões continuam próprias.
A exclusão após encerramento da conta foi adiada para a fase específica, sem
implementar exclusão automática nesta etapa. Detalhes em
[DECISIONS](docs/DECISIONS.md) e no [SDD BL04](docs/phases/BL04-context-and-ai-production.md).

## Contratos e testes

Auth nativa expõe `/api/v1/auth/*`; login/ações exigem Origin e refresh/logout
exigem cookie mais `X-CSRF-Token`. Swagger pode testar domínio com Bearer;
ações de identidade precisam informar os headers corretos. Onboarding cria
identidade/organização/owner/negócio e auditoria transacional de forma idempotente,
sem assinatura paga. Header tenant sozinho não concede acesso. Contratos completos
estão no [SDD](docs/SDD.md), em [auth](docs/design/native-auth.md) e no Swagger.

Para preparar o banco **exclusivo de teste** e executar o gate backend:

```bash
export TEST_ADMIN_DATABASE_URL=postgresql+asyncpg://postgres:meu-braco-direito-admin-password@localhost:55432/meu_braco_direito_platform_test
MEU_BRACO_DIREITO_MIGRATION_DATABASE_URL="$TEST_ADMIN_DATABASE_URL" uv run alembic upgrade head
uv run python scripts/prepare_local_tests.py
make ci
```

O banco `_test` é criado pelo bootstrap local de instalação nova; em volumes
existentes, prepare-o conforme [operações](docs/operations.md). Nunca use ou
limpe o banco da aplicação para testes. O harness recusa nomes sem sufixo `_test`.
`TEST_*` do processo prevalece sobre `.env.test` e `.env.test.example`;
PostgreSQL/Temporal indisponíveis causam falha, sem skips silenciosos.

`make ci` executa Ruff/formatação, mypy, unitários e integração, com cobertura
obrigatória de **100% de linhas e branches** sem exclusões artificiais. `make unit`
roda a fatia unitária. Validações e contagens datadas ficam no
[CHANGELOG](docs/CHANGELOG.md); testes/build/browser da web estão no
[README web](../local-spark-web/README.md). Não há chamada paga obrigatória na
suíte padrão. Revalidar integração externa exige conta, orçamento e cenário próprios.

## CI, produção e documentação

GitHub Actions contém CI e deploy manual ECS/ECR com OIDC. Isso não provisiona
AWS, SMTP real, secrets, backup/restore, observabilidade ou staging. Essas são
condições ainda abertas antes do piloto real. OIDC do CI/AWS é independente da
autenticação dos usuários. Não considerar a base local uma v0 comercial pronta.

Produto aceito e dúvidas delimitadas: [DECISIONS](docs/DECISIONS.md).
Fontes vigentes: [PROJECT](docs/PROJECT.md), [SDD](docs/SDD.md),
[fases](docs/phases/README.md), [trilha BL](docs/phases/BL-brand-library.md),
[operações](docs/operations.md) e [AGENTS](AGENTS.md).
Registros anteriores estão no [histórico integral](docs/history/2026-10-27-pre-consolidation/index.md);
designs de fase, contratos e evals continuam acessíveis. Em cada entrega, atualizar
o resumo vigente e registrar histórico no changelog, sem sobrepor cronologias.
