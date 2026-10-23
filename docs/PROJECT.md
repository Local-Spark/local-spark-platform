# Contexto vivo do projeto

22/10/2026 — Produto renomeado para **Meu Braço Direito**. Diretórios e remotos
Git permanecem `local-spark-platform`/`local-spark-web`; os pacotes, Compose,
variáveis `MEU_BRACO_DIREITO_`, bancos e roles usam os identificadores novos.
A migração `0015_product_brand` precede a correlação WhatsApp, preserva IDs,
senhas/MFA e permissões, atualiza as duas identidades de demonstração e congela
as chaves Stripe de checkouts anteriores. Contas existentes conservam suas senhas;
as senhas de exemplo abaixo valem para instalações novas. Instruções e exceções
de compatibilidade em [renomeação do produto](product-rename.md).


Atualizado: 23/10/2026. Nome adotado: Meu Braço Direito. Repositório principal: `local-spark-platform`.

23/10/2026 — Primeira fatia do assistente conversacional editorial: simulador local
restrito ao proprietário recebe texto e `operation_id`, reconhece oferta de preço
ou disponibilidade para hoje, pede confirmação e grava fato temporário no contexto
versionado após aceite. Repetições são idempotentes; mensagens incertas vão para
revisão. Migration 0026. Ainda não usa LLM nem responde pelo WhatsApp real;
Meta/WABA restrita continua bloqueando o smoke externo. Ver [F02](phases/F02-whatsapp-ingestion.md).

23/10/2026 — F03.2c, terceira fatia: `GET /api/v1/admin/editorial-usage`
agrega por organização as reservas de tokens do dia UTC, tokens informados pelo
provedor e chamadas pendentes/incertas. Leitura exclusiva de staff e auditada;
alertas de 80% e 100% usam o limite diário atualmente configurado, não valor
histórico. Não há tarifa versionada, portanto custo monetário permanece
desconhecido. Fluxo completo WhatsApp/publicação e feedback continuam pendentes.

23/10/2026 — F03.2c, segunda fatia: eventos editoriais novos são correlacionados
ao ID interno único do pedido, vinculado ao `operation_id` externo, e consultáveis
por staff numa linha do tempo de metadados,
sem prompt ou material. O dispatcher registra a etapa de claim na transação;
duplicatas não criam outro marco. Eventos antigos podem estar incompletos.
Percurso WhatsApp/publicação, custo monetário e alertas além da quota editorial ainda faltam.

23/10/2026 — F03.2b: a geração agora exige pelo menos um fato vigente
confirmado pelo proprietário, inclusive quando há material WhatsApp. Sem isso,
o pedido termina com `EDITORIAL_FACTS_REQUIRED` antes da reserva de tokens ou
da chamada à OpenAI. O eval sintético pula esses casos em modo live. F03.2c
iniciada: `/admin/editorial-operations` projeta apenas estado, IDs, versão de
contexto/modelo, tokens e erro estável, com função restrita a staff e auditoria. Custo
monetário fica explicitamente desconhecido; trace de todas as etapas e leitura
restrita de conteúdo ainda estão pendentes. Ver [F03](phases/F03-editorial-research.md).
Avaliação técnica F03.2b encerrada com decisão **não ativar comercialmente**;
o modelo permanece apenas para testes consentidos. Título e ângulo entregues
são derivados deterministicamente de fato confirmado.

23/10/2026 — F03.2c planejada antes do piloto: contexto confirmado e feedback
por negócio personalizam a geração sem treinar um modelo por cliente; mensagens
WhatsApp seguem retenção F02, e eval com conteúdo real pede finalidade/autorização
específicas. Admin terá visão por operação com etapas, erros, tokens e custos;
acesso eventual ao conteúdo será restrito, justificado e auditado. O console
unificado e o dataset real ainda não foram implementados. Ver [F03](phases/F03-editorial-research.md).

23/10/2026 — F03.2b iniciou avaliação sintética da geração editorial: credencial
OpenAI validada, adapter ajustado para limite/estrutura, cinco casos PT-BR
versionados e runner pago apenas com `--live`. Cinco respostas completas passaram
pelos guardas automáticos, mas revisão identificou sugestão semântica não apoiada
em caso sem fato confirmado. Sem liberação comercial, alteração de consentimentos,
conteúdo real; o worker local já lê o modo OpenAI do `.env`, mas não havia
consentimentos ativos nem pedidos pendentes. Ampliar eval, comparar modelo atual e
homologar fluxo completo ainda são pendências. Ver [F03](phases/F03-editorial-research.md).

23/10/2026 — F03.2a cria sugestões editoriais revisáveis a pedido do dono,
ligadas a uma versão do contexto e opcionalmente a um material WhatsApp. O modo
local funciona sem chave; o modo OpenAI usa consentimento próprio, quota diária,
JSON estruturado e activity Temporal sem repetição de chamada paga. Excluir um
material apaga suas sugestões. A interface `/app/ideas` mostra o estado e separa
hipóteses de fatos. Teste real de provedor, avaliação PT-BR, pesquisa e
planejamento proativo são F03.2b/fatias seguintes. WABA Meta segue restrita.

23/10/2026 — F03.1 iniciou o contexto editorial por negócio. O dono confirma
fatos com origem e validade, informa preferências e pode corrigir/restaurar
versões. A API usa CAS e operação idempotente, guarda histórico imutável e audita
o commit sob RLS. A web oferece a edição. Nenhuma extração automática, LLM/Jev,
pesquisa paga, sugestão ou publicação foi ativada. F03.2 usará snapshots
versionados para separar hipóteses de fatos antes de gerar propostas.
Validação local: 417 testes backend/100% de linhas e ramos, migration 0021
revertida/reaplicada no `_test`, backup e upgrade local. Web: 158 testes/100%,
build e fluxo Chromium de salvar/restaurar.

23/10/2026 — F02.2c3a agrupa mensagens do mesmo remetente e negócio em
janelas fixas de dez minutos, com `group_id` estável desde a correlação até o
asset e a biblioteca web. Migration 0019 preserva itens antigos como grupos
unitários. Nenhuma LLM, Jev ou harness interpreta mensagens nesta entrega:
Temporal orquestra material, mas não infere conteúdo. F02.2c3b adicionou transcrição
com orçamento e ledger; sem credencial, a feature segue desativada. Meta real
continua bloqueada pela WABA de teste.
Validação local: 374 testes backend e 100% de linhas/ramos, Ruff/mypy;
migration 0019 revertida/reaplicada no `_test` e aplicada à base de
desenvolvimento após backup. A UI passou 150 testes com 100% nos quatro
critérios e fluxo Chromium do WhatsApp.

23/10/2026 — F02.2c3b adiciona transcrição de áudio no worker Temporal,
desativada por padrão. Migration 0020 guarda texto cifrado e ledger de segundos
reservados por evento/tenant; chamadas pagas são únicas por evento e resultados
incertos não são reenviados. A biblioteca mostra o texto e o estado verdadeiro.
Ativação exige chave OpenAI, chave Meta e limite diário explícito. Ainda não há
interpretação de intenção por LLM/Jev, resposta automática ou smoke Meta real.
O proprietário também precisa aceitar separadamente o envio de áudio ao
provedor; revogar o recebimento geral apaga esse aceite.
Validação: 410 testes backend/100% de linhas e ramos, Ruff/mypy; migration
0020 reversível no `_test`, base local atualizada após backup. Web: 151 testes,
100% nos quatro critérios, build e jornada Chromium aprovados.

F02.2c2 entregou localmente o registro durável de cada tentativa de upload antes
do S3 e a reconciliação de arquivos sem commit, com chaves exclusivas, retry,
lease/fencing e auditoria. A migration 0018 protege as intenções por papel; a
API não as lê. Agrupamento e transcrição entram em F02.2c3. Mídia real ainda
depende do desbloqueio da WABA e de smoke/staging.
Validação: 372 testes backend com 100% de linhas/ramos, Ruff/mypy, rollback e
reaplicação da 0018 no `_test`, backup e migração da base local; worker e
dispatcher atualizados no Docker. Readiness da API local respondeu 200 após a
migração; se o depurador mantiver código antigo, reiniciar com F5.

F02.2c1 entregou localmente retenção e exclusão da biblioteca: materiais preparados vencem
em 30 dias, o dono pode pedir exclusão antecipada e um worker remove objetos com
retry/lease/fencing antes de apagar registros. Inbox/fila vencem em sete dias com
limpeza periódica. A reconciliação de uploads entrou em F02.2c2;
agrupamento/transcrição, Meta real e staging seguem pendentes. Não operar conteúdo
real até esses bloqueios serem tratados.
Validação: 367 testes backend/100% linhas e ramos, 149 web/100% nos quatro
critérios, Chromium da exclusão, rollback/reaplicação da 0017 no `_test` e
remoção de arquivo sintético no SeaweedFS. Migração 0017 aplicada localmente
após backup; dispatcher atualizado está em execução.
A API que já estava aberta pelo depurador VS Code conserva o head antigo em
memória e responde readiness 503 até ser reiniciada com F5; o processo do
depurador foi preservado para o desenvolvedor reiniciá-lo.

Smoke Meta de 22/10: o app e a WABA de teste foram criados, e o callback HTTPS
temporário respondeu ao desafio e aceitou um POST sintético assinado. O primeiro
envio pelo número de teste falhou na Meta com `131031` (`Business Account locked`);
nenhum subevento real entrou na inbox local. A Qualidade da Conta da Meta mostra
restrição permanente da WABA de teste e exige verificar a empresa antes de iniciar
ou responder conversas; após a análise, confirmar a remoção da restrição e a
assinatura do app na WABA. Não operar conteúdo real.

F02.2b1 foi implementada e validada localmente: um processo restrito correlaciona mensagens
cifradas ao negócio após a prova do canal e grava fila durável, privada e auditada.
F02.2b2 agora consome essa fila pelo Temporal, revalida autorização/consentimento,
guarda texto e mídia em biblioteca privada e oferece conexão/recibos na área do
cliente. O storage local usa SeaweedFS/S3; migration 0016 adiciona consentimento,
leases, fencing e assets. Transcrição, resposta, agrupamento, reconciliação de
uploads órfãos e smoke com a Meta eram pendentes nessa fatia; F02.2c2 cobre
uploads órfãos, e os demais itens ainda impedem conteúdo real.
A migração 0015 foi testada
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
