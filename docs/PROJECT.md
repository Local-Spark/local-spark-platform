# Contexto vivo do projeto

Atualizado: 21/10/2026. Nome adotado: Local Spark. Repositório principal: `local-spark-platform`.

F01.6 está implementada e validada localmente: reconciliação periódica de checkout
aberto sem depender do listener Stripe, convite/revogação auditados de operadores
com MFA e confirmação de telefone pela API Twilio Verify. A web tem telas de equipe
e telefone. O envio de código fica desativado até configurar conta e credenciais
Twilio; nenhum telefone foi marcado como verificado por teste local. O staging AWS
ainda não existe, portanto a fase não está homologada externamente. Migrations
0008–0010 aplicadas no banco local após backup e teste de rollback/upgrade no `_test`.
Validação: 244 testes backend/100% linhas e branches, 107 web/100% em quatro
critérios, tipos e lint, oito jornadas Chromium com banco `_test`. API em F5 deve
reiniciar para carregar as novas rotas.

Atualização 21/10/2026: sandbox do titular recebeu pagamento de teste, com assinatura
ativa e eventos checkout/subscription/invoice processados. Isso não encerra os
demais critérios de sandbox/staging. Retorno localhost após login em 127.0.0.1
reproduziu INVALID_SESSION por ausência do cookie host-only. Checkout passa a
congelar Origin autorizado na intenção (migration 0006); produção continua exata,
sem redirect arbitrário. Sessões/assinaturas existentes preservadas na migração local.
Validação: 218 testes backend/100%, 84 testes web/100% e sete jornadas browser;
rollback/reaplicação da 0006 no _test, build e atualização do worker billing.
API F5 precisa reiniciar; nenhum pagamento adicional realizado.

F01.5 agora inclui `GET /admin/billing/opportunities` e uma visão no admin para
checkouts abertos/expirados sem acesso ativo. A lista é paginada pelo job mais
recente, separa teste/produção pelo ambiente, mostra contato já cadastrado sem
distribuir a URL Stripe e exige staff/MFA/RLS/auditoria. Fechar a aba não marca
abandono; a expiração vem da reconciliação. Migration 0007 adiciona índice de
ordenação; aplicada localmente e validada com upgrade/downgrade no banco `_test`.

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
- Autenticação própria na FastAPI: Argon2id, sessões revogáveis, cookies/CSRF,
  recuperação por e-mail e MFA de staff. Sem dependência de Keycloak/Cognito.

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
F01.1–F01.4 implementadas localmente: autenticação nativa, onboarding concorrente
idempotente, contexto do negócio, consentimentos e administração com acesso auditado.
React independente em `../local-spark-web`, com entrada/login, cadastro, espaço do
cliente, overview e busca/paginação de organizações. Worker SMTP e Mailpit em Docker.
Suíte atual antes da cobrança: **131 testes backend, 100% linhas/branches**, lint/tipos aprovados;
rollback/reaplicação da nova migration validado no banco exclusivo de teste.
Onboarding ampliado: atividade sugerida ou livre, cor HEX personalizada e UF/código
IBGE/cidade consistentes. Catálogo versionado de 27 UFs e 5.571 municípios, sem
consulta externa no cadastro. Migration 0004 aditiva preserva perfis e hashes de replay
legados; aplicada localmente sem remover usuários, negócios ou organizações.
Frontend: 62 testes/100%, build e quatro jornadas Playwright com API/SMTP reais
aprovados; onboarding desktop/mobile revisado. Build Docker e catálogo na imagem
validados. F5 deve reiniciar para carregar as novas rotas de referência.
F01.5 em implementação. Entregas locais: Stripe Checkout, inbox/webhook autenticado, jobs
Temporal com lease/fencing, confirmação canônica e acesso pago/teste separados de
patrocínio de seis meses. Cliente /app/billing e admin /admin/billing. Cobrança
desabilitada por padrão; credenciais, Price/valor, sandbox real e staging pendentes.
F01.6 tem convites e verificação de telefone implementados localmente; entrega
real de código e homologação AWS/staging dependem das contas externas. Sem deploy.
Contrato e continuidade em docs/design/billing.md; migration 0005 aditiva aplicada
localmente, preservando contas, negócios, organizações e memberships.
Validação da entrega: 206 testes backend/100% linhas e branches; 84 testes web/
100% em quatro critérios; cinco jornadas Playwright com API/SMTP reais, incluindo
concessão/uso/revogação do patrocínio. Stripe foi exercitado por contratos locais,
sem pagamento no provedor. Builds e serviço Docker billing em modo disabled.
Detalhes em `docs/phases/F00-foundation.md`; v0 comercial continua em implementação.

## Decisões não bloqueantes para F00

Validação comercial da marca; segmento/coorte inicial; limites de cada plano e política de refações;
orçamento de geração proativa; operação SMTP e política de autenticação em PRD; cobrança local;
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

## Interfaces e jornada aprovadas

Operadores da plataforma e membros de negócios são permissões distintas. F01.6
implementou convite/revogação de staff por outro staff autenticado com MFA, com
e-mail verificado, trilha auditada e TOTP individual. O seed de operador existente
serve somente para desenvolvimento local; cadastro público não cria staff.

`local-spark-web` é repositório separado inspirado na organização de rogue-skydogg-ui.
F01: backend de identidade, base React, admin de cadastros/onboarding e configuração
essencial do cliente. Área completa cresce junto das integrações. Contratação
automática e concessão patrocinada entram em F01.5; não marcar como implementadas
antes do webhook/provedor real. Perfil em setup não concede plano pago.

Admin usará nossa base de cadastros/assinaturas/consumo e métricas sociais importadas
com autorização. Diferenciar usuários, organizações, negócios, pagantes e patrocinados.
Sem fonte não há métrica; redes não comprovam faturamento. Autenticação própria,
sem dependência de provedor de identidade externo ou deploy nesta entrega.
Cadastro local: localhost e 127.0.0.1 são aliases aceitos apenas em development/
testing, com porta/protocolo idênticos à origem web configurada. Produção/staging
continuam exigindo a origem exata. Debug precisa reiniciar F5 após alterações.
Contrato vigente em `docs/design/native-auth.md`: IDs antigos preservados, credenciais
sem senha recuperadas por e-mail, role auth isolada e MFA obrigatório para staff.
