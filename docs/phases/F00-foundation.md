# F00 — Fundação executável

Status: Concluída localmente. Atualizado em 27/10/2026 (P14).
Dependências: Nenhuma.

## Objetivo

API, configuração, autenticação verificada, tenancy/RLS, idempotência e auditoria
transacional. Temporal permanece para os processos assíncronos do produto.

## Features e contratos

- POST/GET /api/v1/businesses com JWT, membership e tenant autorizado.
- Mesmo comando concorrente produz um negócio, uma resposta idempotente e auditoria;
  payload diferente com mesma chave gera conflito.
- A transação de CRUD inclui negócio, registro idempotente e auditoria, sem IO
  externo. P14 encerra a emissão de recibos `business.created` e
  `brand_kit.changed`, que não executavam uma ação assíncrona do produto.
- Relay, tabelas e handlers de recibos antigos permanecem para compatibilidade,
  com SKIP LOCKED, lease, fencing, intenção durável e deduplicação. O relay é
  manual, no profile `legacy-relay`, e sai das dependências de debug e do profile
  automático `workers`. Pode ser iniciado explicitamente com
  `docker compose up -d relay` para tratar dados legados.
- Workflows de materiais, IA, mídia, cobrança e publicação mantêm suas identidades
  duráveis, filas e workers Temporal; não dependem desses recibos de CRUD.

## Critérios de aceite e testes

- Unitários de configuração, autenticação, validação e logs sem segredos.
- Integração PostgreSQL com login runtime real: RLS, rollback, reuso de conexão, concorrência e FK composta.
- Compatibilidade Temporal real: fixtures explícitas de recibos antigos comprovam
  execução, retry de activity e entrega repetida sem novo efeito.
- Lint, tipos, cobertura 100% de linhas/branches, migration downgrade/upgrade e build Docker.

## Limites históricos desta fatia

Onboarding/login públicos, MFA e recuperação de conta estavam fora da F00 e
foram implementados localmente na F01. WhatsApp, IA paga, mídia e publicação
têm entregas próprias nas fases seguintes. Homologação das integrações reais,
provisionamento AWS e capacidade comprovada para 200 mil clientes continuam
gates de produção; não são garantias trazidas pela fundação.

## Evidências históricas de validação da fundação

Os recibos/relay mencionados nesta seção registram a implementação anterior à
P14. A regra vigente acima conserva seus históricos e leitores, sem emitir
novos recibos nas mutações síncronas de negócio ou kit.

- 54 testes passaram, incluindo integração com PostgreSQL 17.6 e serviço Temporal
  real em Docker. Cobertura de linhas/branches: **96,74%**, gate mínimo 81%.
- `ruff check`, `ruff format --check` e `mypy` passaram. `actionlint 1.7.7` validou
  os dois workflows; `docker compose config --quiet` validou a composição.
- Migração Alembic aplicada, revertida e reaplicada no banco exclusivo `_test`.
- Imagem multi-stage construída; runtime sem root; API/worker/relay iniciados.
- `/health/live`, `/health/ready` e OpenAPI responderam 200 no container.
- Smoke no banco local de demonstração: criação 201, repetição idempotente 200,
  listagem com um negócio e auditoria da activity após relay/Temporal.
- Serviços Docker locais permanecem disponíveis. PostgreSQL de teste temporário
  fora do Docker foi encerrado após a validação inicial.
- Um aviso de depreciação do TestClient/httpx é emitido pela dependência Starlette;
  não afeta os testes e não foi suprimido nem usado para reduzir cobertura.
- Repositório principal `local-spark-platform` com remoto Git já configurado.
  Implementação permanece em alterações locais; não houve push, CI remoto ou deploy AWS.

## Identidade Meu Braço Direito

- Prefixo de configuração `MEU_BRACO_DIREITO_`; Swagger `Meu Braço Direito API`.
- Bancos `meu_braco_direito_platform`/`meu_braco_direito_platform_test`, roles `meu_braco_direito_*`;
  login administrativo de desenvolvimento continua `postgres`.
- Senhas e assinatura JWT locais atualizadas; reemitir tokens de demonstração.
- Compose `meu-braco-direito-platform`, volumes próprios para PostgreSQL e Temporal.
  Migração local preserva registros, permissões RLS e identidades de demonstração.
- CI, lockfile, documentação e scripts usam os novos identificadores.
- Revalidação: 54 testes, cobertura 96,05%, lint/tipos, actionlint, rollback/upgrade
  e build passaram. Smoke HTTP/Temporal confirmou criação 201, replay 200 e um
  efeito; dados/histórico anteriores preservados e token anterior rejeitado.

## Atualização de mudanças

Validação de cobertura atual: 62 testes passaram, 390 statements e 40 branches
cobertos, sem linhas/branches faltantes. Gate elevado a 100%, sem novas exclusões.
Casos adicionados cobrem contratos de criação/replay, idempotência e paginação do
serviço, readiness sem migration, perda de lease durante RPC e retorno inválido
da activity. Configuração exclusiva de testes carregada automaticamente; ausência
de PostgreSQL/Temporal não pula a integração.

Debug da API disponível em `.vscode/launch.json` (F5), com pré-tarefas Docker e
extensões recomendadas. A execução usa `.env`/`.venv` e porta 8000 sem reload.
Instruções de conexão ao DBeaver e retomada da API Docker estão no README.
Validado por execução das pré-tarefas e smoke com debugpy/Uvicorn: ready, Swagger
e OpenAPI 200. Sessão interativa/breakpoints no VS Code ficam para uso no editor.
Correção macOS: comandos Docker absolutos nas pré-tarefas e PATH explícito para
plugins/helpers; evita falha de resolução do executável ao abrir o editor pela GUI.
Ambas as tarefas passaram com PATH herdado restrito a `/usr/bin:/bin`; API Docker
restaurada e readiness 200 após a validação.
`.gitignore` específico da plataforma mantém código, testes, SQL, lockfile, CI,
SDDs e debug compartilhado; exclui credenciais, bancos, backups, caches e saídas locais.

Dividir as features acima em mudanças revisáveis. Cada mudança atualiza este SDD,
`docs/PROJECT.md` e `docs/CHANGELOG.md`, incluindo evidências de testes e pendências.
Contratos que afetam outras fases devem ser refletidos no SDD geral e nos consumidores.
Não marcar como concluído por possuir mocks ou documentação de uma API ainda não validada.
