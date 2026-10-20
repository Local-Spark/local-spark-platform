# Contexto vivo do projeto

Atualizado: 20/10/2026. Nome adotado: Local Spark. Repositório principal: `local-spark-platform`.

## Negócio

Pequenos empresários enviam fotos, vídeos, áudio ou ideias pelo WhatsApp. A plataforma
pesquisa, seleciona temas, roteiriza, gera conteúdo, recebe aprovação, publica e mostra
resultados. Pode usar avatar e voz autorizados do próprio dono. Sem material novo,
gera sugestões a partir de fatos e biblioteca autorizados, com orçamento e aprovação.
Aquisição será por vídeos longos de entretenimento no YouTube dos três sócios.
Negócios apresentados podem ser pagantes ou receber acesso patrocinado por seis meses.
R$ 99/mês é hipótese de plano de entrada, sem franquias comerciais fechadas.
200 mil clientes é cenário de escala, não capacidade comprovada nem adoção garantida.

## Decisões aceitas

- Backend em Python; FastAPI, PostgreSQL, Temporal, Redis e S3.
- Multi-tenancy em tabelas compartilhadas/RLS; sem schema por cliente como padrão.
- Instagram primeiro, vários formatos incluindo avatar e híbrido na v0 completa.
- Pesquisa local com raio configurável e fontes permitidas; nenhuma promessa de
  conhecer faturamento/alcance privado de concorrentes.
- Jev/TypeSafe é candidato a decisão semântica após eval PT-BR; não escreve roteiros.
- Aprovação por versão/destino; silêncio não autoriza publicação. Consentimento,
  autorização de gasto e aprovação de postagem são permissões distintas.
- Padrão de organização baseado no `spotlight-api`, sem copiar domínio/dependências.
- Testes unitários, integração real, coverage de linhas/branches de 100% e GitHub Actions.
- Implementação em fases pequenas com SDD geral, SDD por fase e atualização contínua.

## Estado atual

F00 concluída e validada localmente: API, configuração, JWT verificado, tenants/
memberships, RLS, criação/listagem, idempotência, auditoria/outbox, relay com lease/
fencing e workflow inicial Temporal. **62 testes passaram, cobertura 100%** com
linhas e branches; gate 100%. PostgreSQL 17.6 e Temporal em Docker, lint e tipos,
rollback/reaplicação de migration, build e smoke da jornada em containers passaram.
GitHub Actions validado com actionlint; execução remota/deploy ainda não ocorreram.
Validação após a troca de nome: `make ci`, rollback/reaplicação no banco `_test`,
build e smoke HTTP/Temporal passaram. Dados e histórico anteriores foram preservados;
tokens anteriores foram rejeitados e um novo token de demonstração foi emitido.
Suíte ampliada: contratos HTTP de criação/replay, serviço de paginação/idempotência,
readiness sem migration, lease expirado durante RPC e retorno inválido da activity.
Pytest usa `.env.test.example`/`.env.test`, com ambiente do processo prevalecendo;
PostgreSQL/Temporal indisponíveis causam falha, sem pular integração silenciosamente.
F01 é a próxima fase: onboarding público, provedor de identidade e contexto do negócio.
Detalhes em `docs/phases/F00-foundation.md`; v0 comercial continua em implementação.

## Decisões não bloqueantes para F00

Validação comercial da marca; segmento/coorte inicial; limites de cada plano e política de refações;
orçamento de geração proativa; emissor OIDC e onboarding público; cobrança local;
contratos/capacidade dos fornecedores; scopes/app review Meta; retenção final e termos.
Esses itens bloqueiam partes do piloto comercial, não a fundação local.

## Continuidade

Fonte principal passa a ser este repositório. Os documentos de origem copiados para
`docs/design` preservam contexto; docs de implementação e status em `docs/SDD.md`
e `docs/phases` prevalecem sobre nomes de pastas sugeridos em rascunhos anteriores.
O repositório principal já possui remoto Git configurado; esta implementação permanece
em alterações locais. Não houve push, execução remota de CI ou provisionamento AWS.
Configuração usa `LOCAL_SPARK_`, bancos `local_spark_platform`/`local_spark_platform_test`
e roles `local_spark_*`. Credenciais locais foram atualizadas, incluindo a assinatura JWT.
Não há cliente real ou integração paga provisionados.

Desenvolvimento: `.vscode/launch.json` oferece `Local Spark: API (FastAPI)` com
Python da `.venv`, `.env` local e porta 8000. Prelaunch para a API Docker e sobe
dependências para evitar conflito de porta; workers seguem nos containers.
No macOS, pré-tarefas usam o caminho absoluto do Docker Desktop e PATH explícito
para funcionar quando o VS Code é aberto pela interface gráfica.
Versionamento: `.gitignore` exclui credenciais locais, estado de runtime, bancos,
backups, caches e artefatos gerados. Código, testes, migrations SQL, SDDs, lockfile,
workflows CI e os quatro arquivos compartilhados de debug VS Code permanecem versionáveis.
