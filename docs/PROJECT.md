# Contexto vivo do projeto

22/10/2026 — Produto renomeado para **Meu Braço Direito**. Diretórios e remotos
Git permanecem `local-spark-platform`/`local-spark-web`; os pacotes, Compose,
variáveis `MEU_BRACO_DIREITO_`, bancos e roles usam os identificadores novos.
A migração `0015_product_brand` precede a correlação WhatsApp, preserva IDs,
senhas/MFA e permissões, atualiza as duas identidades de demonstração e congela
as chaves Stripe de checkouts anteriores. Contas existentes conservam suas senhas;
as senhas de exemplo abaixo valem para instalações novas. Instruções e exceções
de compatibilidade em [renomeação do produto](product-rename.md).


Atualizado: 22/10/2026. Nome adotado: Meu Braço Direito. Repositório principal: `local-spark-platform`.

F02.2b1 foi implementada e validada localmente: um processo restrito correlaciona mensagens
cifradas ao negócio após a prova do canal e grava fila durável, privada e auditada.
Não há IA, download, resposta ou publicação. F02.2b2 fará consumo da fila,
validação de plano/consentimento, mídia e workflow. A migração 0015 foi testada
com rollback/reaplicação num PostgreSQL temporário `_test`; a base local renomeada
está no head 0015. 289 testes passaram com 100% de linhas/ramos; lint, tipos e
Compose passaram. Smoke real Meta e staging ainda pendentes.

Correção CI de F02.2a: o workflow declara `TEST_META_DATABASE_URL` com a porta
5432 do PostgreSQL do Actions e prepara o login restrito Meta. Em `CI`, pytest
exige todas as URLs explicitamente para não herdar a porta local 55432 do
`.env.test.example`. A próxima fatia funcional é F02.2b: correlação de eventos
ao negócio vinculado, retenção, biblioteca de mídia e início dos workflows.
Simulação local do modo CI passou: 278 testes, 100% de linhas/ramos, lint e tipos.
O workflow remoto ainda não foi executado nesta alteração.

F02.2a implementa a prova de posse do canal WhatsApp: dono autenticado com
telefone verificado e plano ativo recebe código único, envia-o pelo WhatsApp
registrado, e confirma após webhook Meta assinado. Há vínculo tenant/negócio,
auditoria e revogação automática ao trocar o telefone. A inbox continua em
quarentena: UI do vínculo, correlação de mensagens, mídia, transcrição e workflow
de conteúdo permanecem nas próximas fatias. Validação local usa webhooks
sintéticos; ainda não existe App/WABA Meta disponível para smoke real.
Migration 0014 aplicada no desenvolvimento local após backup; 278 testes com
100% de linhas/ramos, lint e tipos passaram. Banco `_test` validou rollback/upgrade.

F02 começou pela ingressão segura de WhatsApp (F02.1): desafio e assinatura Meta,
limite de corpo, inbox cifrada/deduplicada com papel PostgreSQL isolado e migração
0013. Sem App/WABA configurados, a rota fica desabilitada. Sem vínculo específico
entre remetente e negócio, eventos ficam em quarentena; ainda não há processamento
de fotos/áudio/texto nem resposta via WhatsApp. F02.2 continua com resolução do
remetente, biblioteca privada e workflow. F02.1 foi validada com 271 testes/100% linhas e ramos, lint,
tipos, migração de teste revertida/reaplicada e migração local após backup. Nenhum
smoke real com a Meta ocorreu.

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
- F02 coleta preferências opcionais sem aumentar o cadastro obrigatório. F03 entrega
  contexto versionado do negócio, com fatos confirmados separados de hipóteses e
  edição pelo dono; aprovar conteúdo não confirma fatos comerciais automaticamente.
- Antes da primeira operação paga, reservar quota/custo de forma atômica (F03 se
  pesquisa paga; F04/F05 para mídia). Adapters de IA por capacidade e fornecedores
  são escolhidos por benchmark, contrato e direitos, sem primário fixado nesta etapa.
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
Configuração usa `MEU_BRACO_DIREITO_`, bancos `meu_braco_direito_platform`/`meu_braco_direito_platform_test`
e roles `meu_braco_direito_*`. Credenciais locais foram atualizadas, incluindo a assinatura JWT.
Não há cliente real ou integração paga provisionados.

Desenvolvimento: `.vscode/launch.json` oferece `Meu Braço Direito: API (FastAPI)` com
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
