# Registro de mudanças

## 2026-10-20 — Cobertura 100% e configuração da suíte completa

- Gate de cobertura elevado de 81% para 100%, incluindo branches e todos os
  módulos de produção existentes, sem novas exclusões.
- Adicionados testes dos contratos HTTP de criação/replay, idempotência e paginação
  no serviço, readiness sem migration, lease perdido durante dispatch e resposta
  inválida da activity no workflow.
- Pytest carrega configuração exclusiva `.env.test.example` e `.env.test` opcional;
  variáveis de ambiente exportadas prevalecem. Integrações PostgreSQL/Temporal
  não são mais puladas por falta de variáveis. Banco continua limitado a `_test`.
- `.env.test.example` versionável; `.env.test` continua ignorado. CI e documentação
  atualizados para o novo gate. Nenhuma regra de produção alterada.
- Evidência: 62 testes passaram; 390 statements e 40 branches cobertos, total 100%.
- `make ci` completo passou sem exportar variáveis `TEST_*` manualmente: lint,
  formatação, tipos e suíte completa. Actionlint validou os workflows atualizados.

## 2026-10-20 — Versionamento e arquivos locais

- Substituído template genérico do `.gitignore` por regras específicas de Python,
  segredos locais, PostgreSQL/Temporal, backups, cobertura e metadados do editor/SO.
- Mantidos versionáveis `.env.example`, `uv.lock`, `.python-version`, CI, testes,
  migrations SQL, documentação e os quatro arquivos compartilhados `.vscode`.
- Nenhum arquivo removido do disco ou do índice; commit/push não executados.
- Validação: `git check-ignore` confirmou 27 caminhos ignorados e 29 caminhos
  versionáveis; nenhum arquivo já rastreado exige remoção do índice. Diff sem erros.

## 2026-10-20 — Correção de Docker nas tarefas VS Code/macOS

- Pré-tarefas do debug usam o executável absoluto do Docker Desktop no bloco `osx`
  e PATH explícito para Compose e credential helpers. Corrige falha de lançamento
  quando o editor não herda `/usr/local/bin` no PATH.
- Validação: ambas as pré-tarefas executadas com PATH herdado restrito a
  `/usr/bin:/bin`; API Docker restaurada e readiness 200 após a verificação.

## 2026-10-20 — Debug VS Code

- Adicionados launch, tasks, seleção de interpreter e extensões recomendadas em
  `.vscode` para depurar a API FastAPI localmente com `.venv` e `.env`.
- Prelaunch sequencial para a API Docker e inicia dependências, liberando porta
  8000 para o debugger. Workers continuam em Docker; debug sem reload.
- Documentados nome do banco, schema e conexão local no DBeaver.
- Validação: quatro JSONs válidos; pré-tarefas executadas; API iniciada com debugpy
  da extensão e argumentos configurados, ready/Swagger/OpenAPI 200. API Docker
  restaurada após smoke. Não foi executada uma sessão interativa no editor.

## 2026-10-20 — Nome e ambiente Local Spark

- Adotado `local-spark-platform` como repositório principal, preservando seu remoto
  e as alterações locais existentes. Restaurados os arquivos de CI, Docker e
  configuração que não estavam presentes na cópia do repositório.
- Padronizados nome de pacote, Swagger, logs, configuração `LOCAL_SPARK_`, issuer,
  audience e task queue. Bancos usam `local_spark_platform` e
  `local_spark_platform_test`; roles usam `local_spark_*`.
- Atualizadas senhas locais de administração, runtime e relay, além da chave JWT
  de desenvolvimento. `.env` local criado e ignorado pelo Git; tokens precisam
  ser reemitidos. Nenhuma credencial externa/produção foi alterada.
- Dados PostgreSQL copiados com o serviço parado antes de renomear bancos/roles
  e alterar senhas. Volume anterior mantido. Identidades de demonstração preservadas.
- Histórico Temporal local transferido para volume nomeado persistente. Containers
  anteriores permanecem parados; desenvolvimento passa a usar o novo projeto Compose.
- SDD geral, fase F00, contexto do projeto e instruções locais atualizados.
- Validação: `make ci` passou (54 testes, cobertura 96,05%, lint e tipos);
  migrations revertidas/reaplicadas no banco `_test`; actionlint e build passaram.
  Swagger/health/OpenAPI 200; criação 201, replay 200 e um efeito no workflow.
  Registro anterior e histórico Temporal concluído preservados; JWT antigo rejeitado.

## 2026-10-20 — F00

- Criado repositório local `local-spark-platform`, nome provisório, seguindo convenções
  organizacionais do `spotlight-api`, sem modificar esse projeto ou copiar segredos.
- Implementados API versionada, configuração, JWT verificado, tenants/memberships,
  negócios, RLS, idempotência, auditoria e outbox atômicas.
- Relay com SKIP LOCKED, lease/fencing, timeout RPC e workflow ID estável; activity
  revalida intenção persistida e deduplica o efeito. Temporal real usado nos testes.
- Testes unitários/integração/concorrência, lint, tipos e gate de coverage 81%.
- Containers locais e GitHub Actions de CI/deploy ECS preparados e validados.
- Documentação geral, resumo vivo, nove SDDs de fase e AGENTS.md para continuidade.
- Evidência: 54 testes passando, 96,74% coverage; migration rollback/upgrade,
  actionlint, build Docker e smoke HTTP/outbox/Temporal confirmados.
- Próximo: F01. Pendências comerciais não bloqueiam a fundação, mas devem ser
  resolvidas antes de cobrar, gerar identidades ou publicar para clientes reais.
