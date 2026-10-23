# Registro de mudanças

## 2026-10-23 — F02: primeira fatia do assistente editorial conversacional

- Migration 0026 guarda decisões por tenant/negócio e `operation_id`, com RLS e auditoria. O texto original não é persistido nessa tabela.
- Simulador autenticado somente em ambiente local/teste classifica duas entradas claras de preço/agenda de hoje, pede confirmação e permite confirmar ou descartar. Confirmação cria um fato temporário versionado; entradas ambíguas ficam para revisão.
- WhatsApp real, LLM e publicação seguem pendentes; o simulador não envia mensagens externas.
- Validação: `make ci` passou com 450 testes, Ruff, mypy e 100% de linhas/ramos. Migration 0026 aplicada no banco local após backup e revertida/reaplicada no `_test`.

## 2026-10-23 — F03.2c: consumo editorial diário

- Migration 0025 cria projeção SQL restrita a staff para uso editorial do dia UTC,
  por organização, sem liberar leitura direta da tabela do ledger. Endpoint
  auditado devolve tokens reservados, observados, chamadas medidas e incertas.
- Estados de quota usam o limite atual: aviso em 80%, esgotado em 100% e ausência
  de configuração explícita. Custo monetário segue desconhecido até haver tarifa
  versionada; não há alerta automatizado fora do painel.
- Validação: `make ci` com 444 testes, 100% de linhas/ramos, Ruff e mypy;
  teste de integração cobre isolamento de tenant, staff/cliente e agregação.
  Migration 0025 aplicada no `_test` e na base local após backup verificado.

## 2026-10-23 — F03.2c: etapas editoriais correlacionadas

- Auditoria de novos pedidos usa o ID interno único, associado ao `operation_id`
  externo, para não misturar negócios que reutilizem o mesmo ID. Claim do dispatcher
  registra etapa em transação; replay da mesma etapa é deduplicado.
- Migration 0024 cria projeção SQL restrita a staff para ação/data por pedido;
  endpoint auditado não devolve texto, mídia, prompt nem rascunho.
- Histórico legado pode ser parcial. Fluxo WhatsApp/publicação, custos em moeda,
  alertas e avaliação semântica ainda não estão concluídos.
- Validação: `make ci` com 443 testes e 100% de linhas/ramos, Ruff e mypy;
  migration 0024 revertida/reaplicada no `_test` e aplicada no banco local após
  backup em `.local/backups/`.

## 2026-10-23 — F03.2b: abstinência; F03.2c: diagnóstico inicial

- Pedidos editoriais sem fato vigente confirmado terminam com código
  `EDITORIAL_FACTS_REQUIRED` antes da reserva ou chamada paga, mesmo com material.
- Runner sintético registra esses casos como necessidade de confirmação, com zero
  tokens, e conserva os dados do relatório fora do Git.
- Nova rodada live sintética: 3/3 respostas elegíveis válidas, 2/2 casos sem
  fatos bloqueados, 821 tokens de entrada/1.335 de saída. Revisão humana ainda
  encontrou afirmações não fundamentadas; decisão de liberação comercial é
  **não**, até corrigir o contrato e passar por nova avaliação.
- Guarda adicional exige ID de fato citado; título e ângulo expostos são
  reconstituídos de um fato confirmado, enquanto formato/hipóteses/perguntas
  permanecem do modelo para revisão. Testes cobrem a remoção de uma promoção
  inventada do rascunho persistido.
- Migration 0023 cria uma função de projeção de metadados para staff, sem
  liberar leitura cruzada das tabelas editoriais ao papel da API. Endpoint
  `/admin/editorial-operations` audita a consulta e devolve só metadados de até
  100 pedidos por filtro de organização, sem texto, rascunho ou mídia.
- Custo monetário aparece como desconhecido. A linha do tempo completa e a
  leitura excepcional de conteúdo seguem para a continuação da F03.2c.
- Validação: `make ci` com 443 testes e 100% de linhas/ramos; migration 0023
  revertida/reaplicada no banco `_test` e aplicada ao desenvolvimento após
  backup verificado. Eval sintético pago repetido após a guarda, sem dados de
  clientes. A web passou 170 testes/100%, build e Chromium mobile.

## 2026-10-23 — Política planejada de aprendizado e diagnóstico

- F03.2c explicita retenção e personalização por contexto versionado/feedback,
  sem treino automático por cliente ou dataset compartilhado de WhatsApp.
- Visão admin por operação reúne etapas e gastos; leitura de conteúdo fica em
  caminho restrito e auditado. Mudança documental, sem UI/API nova.

## 2026-10-23 — F03.2b: primeiro smoke e avaliação sintética

- Adapter ajustado após o modelo consumir o limite antigo em raciocínio:
  esforço baixo, 1200 tokens de saída e limites no JSON Schema.
- Cinco casos PT-BR sintéticos versionados e runner com `--live` explícito;
  relatório local ignorado pelo Git. Última rodada: 5/5 respostas completas,
  5/5 guardas automáticos, 1.276 tokens de entrada e 1.945 de saída.
- Revisão humana encontrou uma inferência não fundamentada em caso sem fato
  confirmado. Coorte comercial permanece desativada; dados reais não foram usados.
- Worker local lê modo OpenAI, mas a base tinha zero consentimentos ativos,
  pedidos em andamento ou propostas OpenAI persistidas ao fim da avaliação.
- `make ci`: 442 testes, 100% de linhas e ramos, Ruff e mypy aprovados.
- Comparação sintética com `gpt-5.4-mini`: 5/5 respostas completas, 4/5 nos
  guardas; sem troca do modelo local nem escolha de modelo para produção.

## 2026-10-23 — Contrato futuro de conversa editorial no WhatsApp

- F02 define respostas curtas por ação editorial, confirmação explícita para
  preço/horário e limites entre falar com o dono e atender consumidores.
- Jev fica candidato a roteamento fechado após eval; extração de campos livres
  e redação exigem outros componentes. Documentação apenas, sem execução nova.

## 2026-10-23 — F03.2a: sugestões editoriais revisáveis

- Migration 0022 separa consentimento de IA, pedidos idempotentes e ledger de
  tokens reservados por tenant. RLS owner/worker, Temporal com ID determinístico,
  reconciliação de estado incerto e exclusão de sugestões derivadas de material.
- Baseline local por padrão. OpenAI Responses API opcional (`store=false`, JSON
  Schema estrito, saída limitada), com consentimento e quota antes da chamada;
  sem retry pago. Fatos vencidos, plano revogado e material ausente bloqueiam uso.
- A sugestão é um rascunho, sem publicação ou confirmação automática de fatos.
  Teste real do provedor, eval PT-BR e custo monetário aferido ficam pendentes.
- Validação: 442 testes backend com 100% de linhas/ramos, Ruff e mypy;
  migration 0022 revertida/reaplicada no `_test` e aplicada no banco local após
  backup verificado. Web: 167 testes/100% nos quatro critérios, typecheck,
  build, formatação e jornada Chromium. Workers reconstruídos e em execução.
  API local em debug precisa reiniciar para carregar a rota nova.

## 2026-10-23 — F03.1: contexto editorial confirmado

- Migration 0021 cria cabeça e versões imutáveis por tenant/negócio, com RLS
  restrito ao proprietário. API salva com versão esperada e ID de operação,
  rejeita concorrência, oferece histórico e restauração auditada.
- Fatos têm tipo, origem declarada e validade; preço, horário e oferta exigem
  prazo. Preferências ficam separadas de hipóteses. A área do cliente permite
  corrigir e restaurar versões sem publicar ou afirmar conteúdo gerado.
- Sem LLM/Jev, pesquisa externa ou chamadas pagas nesta entrega. F03.2 tratará
  interpretação estruturada, propostas e orçamento após fixar o contexto.
- Validação: 417 testes backend/100% de linhas e ramos, Ruff/mypy, concorrência
  PostgreSQL e rollback/upgrade da 0021 no `_test`. Banco local migrado após
  backup verificado. Web: 158 testes/100% em quatro critérios, build e jornada
  Chromium de edição e restauração.

## 2026-10-23 — F02.2c3b: transcrição de áudio controlada

- Migration 0020 adiciona transcript cifrado ao asset e ledger privado de
  segundos reservados; idempotência por evento e orçamento diário por tenant.
- Worker normaliza áudio a WAV, usa `gpt-transcribe` somente com chave e limite
  explícitos, e não repete chamada paga após submissão. Dispatcher converte
  submissões antigas sem conclusão em estado incerto. API e web mostram texto
  e estados ao proprietário; exclusão do asset remove o transcript.
- Consentimento específico por negócio é exigido para enviar áudio à OpenAI;
  aceite antigo de materiais não basta. O dono ativa/revoga pela API e web.
- Sem credenciais OpenAI configuradas, integração permanece desligada. Smoke
  real Meta/fornecedor e interpretação semântica continuam pendentes.
- Validação: 410 testes backend com 100% de linhas/ramos, Ruff e mypy;
  migration 0020 revertida/reaplicada no `_test` e aplicada localmente após
  backup verificado. Testes cobrem reserva, replay, teto, consentimento,
  conversão, falha incerta e reconciliação. Sem chamada paga real.

## 2026-10-23 — F02.2c3a: materiais de um mesmo envio

- Migration 0019 adiciona identidade estável de grupo à fila e aos assets,
  preservando materiais anteriores como grupos unitários. O correlator usa
  tenant, negócio, remetente e janela fixa de dez minutos; o processamento
  persiste essa identidade e a API a expõe apenas ao proprietário.
- Biblioteca web reúne itens do mesmo envio. Testes cobrem concorrência,
  isolamento entre negócios, virada da janela e persistência até o recibo.
- Validação: 374 testes backend com 100% de linhas/ramos, Ruff e mypy.
  Migration 0019 revertida/reaplicada no `_test`; backup verificado da base local
  antes da atualização para 0019. Integração PostgreSQL passou com logins
  restritos; correlator e worker locais foram reconstruídos e a API respondeu
  200 em `/health/ready`. Nenhum conteúdo Meta real foi processado.
- A transcrição com provedor, reserva de orçamento e ledger forma F02.2c3b.
  Ainda não existe interpretação semântica por LLM/Jev ou harness de agentes;
  WABA real continua restrita.

## 2026-10-22 — F02.2c2: reconciliação de uploads interrompidos

- Cada upload ganha intenção durável, chave S3 única por tentativa e auditoria antes
  de chamar o storage. A finalização do asset remove a intenção no mesmo commit.
- Dispatcher reconcilia intenções vencidas em lotes com lease/fencing, retry e
  auditoria; nunca reivindica uma chave ligada a asset finalizado. A finalização
  trava a intenção e rejeita uma tentativa já reivindicada pela limpeza. Cliente
  S3 agora tem timeouts explícitos. Migration 0018 aditiva com papel restrito.
- Validação: 372 testes backend com 100% de linhas/ramos, Ruff, formatação e mypy;
  sucesso, revogação após upload, corrida com limpeza, falha/retry do storage,
  fencing e isolamento do
  login da API. Migration 0018 revertida/reaplicada no `_test`, aplicada no banco
  local após backup verificado. Worker e dispatcher reconstruídos e em execução.
  Readiness da API local retornou 200. Nenhum evento Meta real ou conteúdo de
  cliente foi usado.
- Pendente: agrupamento/transcrição (F02.2c3), smoke Meta após desbloqueio da
  WABA, staging e inventário periódico do bucket para operação em escala.

## 2026-10-22 — F02.2c1: retenção e exclusão de materiais

- Migração 0017 adiciona prazo de 30 dias aos assets e estado de exclusão com
  lease/fencing e privilégios RLS. API oferece pedido idempotente de exclusão ao
  proprietário; materiais pedidos/vencidos somem da biblioteca e não geram links.
- Dispatcher limpa inbox/fila cifradas vencidas e apaga objetos S3 antes dos
  registros correspondentes. Falha de storage mantém a intenção para retry.
  A web mostra prazo e confirmação de exclusão; links já emitidos duram até 2 min.
- Validação: 367 testes backend com 100% de linhas/ramos; 149 testes web com
  100% nos quatro critérios; uma jornada Chromium de exclusão; Ruff, mypy,
  typecheck, build e formatação aprovados. Migração 0017 revertida/reaplicada no
  `_test`, aplicada localmente após backup. Arquivo sintético removido no
  SeaweedFS e dispatcher atualizado em execução.
- A API iniciada antes da migração pelo depurador VS Code precisa reiniciar com
  F5 para reconhecer o novo head; readiness local fica 503 até esse reinício.
- Reconciliação de upload órfão, agrupamento/transcrição, Meta real e staging
  permanecem pendentes antes de conteúdo real.

## 2026-10-22 — Diagnóstico do sandbox Meta

- App/WABA e número de teste configurados somente no `.env` local; sem segredos
  ou IDs transitórios versionados. Callback HTTPS temporário limitado à rota
  WhatsApp respondeu ao desafio e aceitou POST vazio sintético com HMAC válido;
  requisição sem assinatura recebeu 403 e outras rotas receberam 404.
- Primeiro envio de teste recebeu status `failed` com erro Meta `131031`
  (`Business Account locked`). Inbox local não recebeu subevento real. A Meta
  mostra a WABA de teste como restrita permanentemente e exige verificação da
  empresa antes de iniciar/responder conversas ou adicionar números. Verificação,
  remoção da restrição e confirmação de `subscribed_apps` da WABA estão pendentes;
  mídia e conteúdo de clientes permanecem fora do teste.

## 2026-10-22 — F02.2b2: consumo e biblioteca de materiais

- Migration 0016 adiciona consentimento por negócio, leases/fencing/tentativas
  na fila e recibos privados com RLS. Dispatcher inicia workflow Temporal por
  evento; activity revalida vínculo, proprietário, telefone, consentimento e
  acesso comercial antes e depois de buscar mídia.
- Texto cifrado e originais de foto/áudio/vídeo vão para biblioteca S3 privada;
  Meta download impõe hosts permitidos, limites de tamanho, MIME, checksum e
  inspeção local. API lista recibos e cria URL assinada de dois minutos só para
  proprietário. Revogar consentimento desconecta o canal.
- Compose local usa SeaweedFS 4.39 como storage S3. Migração 0016 validada com
  downgrade/reaplicação no banco `_test`; escrita/leitura/remoção de objeto
  sintético e URL assinada passaram no storage local. Backup da base de
  desenvolvimento salvo antes de aplicar a migration 0016.
- Validação final: 361 testes backend, 100% de linhas/ramos, Ruff, formatação,
  mypy, Compose e build das imagens API/worker passaram. API nova respondeu
  `/health/ready` e expôs três rotas de materiais em contêiner temporário.
- Sem App/WABA e staging, não houve smoke Meta real. Transcrição, resposta,
  geração, retenção/exclusão de assets e produção permanecem pendentes.

## 2026-10-22 — Marca Meu Braço Direito

- Produto renomeado na interface, metadados, logotipo, favicon, e-mails e
  documentação. Pacotes e identificadores técnicos usam `meu-braco-direito`;
  backend configura por `MEU_BRACO_DIREITO_`. Nomes, caminhos e remotos Git preservados.
- Cookies, CSRF, Web Locks e canal de logout atualizados em conjunto, mantendo
  tokens só em memória e as proteções HttpOnly/Origin. Novo login é necessário.
- Migração preserva IDs, senhas/MFA, vínculos, políticas RLS e chaves de idempotência
  de checkouts anteriores. E-mails pendentes recebem a marca nova ao enviar,
  conservando seus links/tokens. Contas de demonstração mantêm IDs estáveis.
- Ambiente local atualizado após backup SQL completo e cópia dos volumes parados;
  originais preservados. PostgreSQL, Temporal e workers usam os nomes novos.
  IDs de usuários/credenciais/negócios/organizações/checkouts comparados ao backup.
  Nenhum workflow ativo ficou na fila antiga; histórico Temporal preservado.
- Testes de navegador ajustados aos seletores e títulos atuais e ao HTML UTF-8
  no retorno externo simulado. Documentação operacional em
  [renomeação do produto](product-rename.md).
- Validação: 126 testes web com 100% de linhas/statements/funções/branches;
  289 testes backend em modo CI com 100% de linhas/branches; tipos, formatação,
  lint, build web e imagens Docker aprovados. Nove jornadas Chromium passaram
  com API/SMTP reais em banco exclusivo `_test`; checkout externo simulado,
  sem pagamento adicional. Screenshots desktop/mobile revisados.
- Migração de uma cópia do banco anterior validou conflito de roles com rollback
  atômico, upgrade, downgrade/reaplicação e preservação de IDs/chaves Stripe.
  Instalação local passou em readiness e título OpenAPI. Nenhuma pendência de
  implementação da marca; reinício do processo F5 continua necessário.
- Reiniciar a API em F5 para reler `.env` e autenticar novamente. Sem publicação,
  commit ou push; configurações de marca em contas externas não foram alteradas.

## 2026-10-22 — F02.2b1: correlação privada de mensagens

- Migration 0015 cria papel/login restrito de correlação e fila cifrada de
  materiais com identidade única, tenant/negócio, retenção e RLS.
- Processo separado associa apenas mensagens posteriores a vínculo ativo;
  descarta comandos e formatos não aceitos, audita e permite concorrência por
  `SKIP LOCKED`. A fila ainda não é consumida por IA ou Temporal.
- Migração 0015 validada com upgrade/downgrade/reaplicação em PostgreSQL
  temporário `_test`; a base local renomeada está em 0015. 289 testes com
  100% de linhas/ramos, Ruff, mypy e configuração Compose passaram. Não houve
  smoke Meta real nem envio de conteúdo ao Temporal.
- Após a migração de marca entrar na cadeia Alembic, uma segunda base temporária
  confirmou upgrade completo desde zero, downgrade até `0015_product_brand`,
  reaplicação da rota e seis testes direcionados. Containers de teste removidos.

## 2026-10-22 — Correção do CI da F02.2a

- GitHub Actions define explicitamente `TEST_META_DATABASE_URL` na porta 5432 do
  serviço PostgreSQL do CI; antes, pytest carregava a URL de exemplo local na
  porta 55432 e falhava na checagem de isolamento do banco `_test`.
- Preparação do banco de teste cria o login restrito `meu_braco_direito_ingest` e concede
  `meu_braco_direito_meta`, necessário aos testes da inbox e do vínculo WhatsApp.
- Pytest exige todas as URLs e o endereço Temporal explícitos sob `CI`, evitando
  que um ambiente remoto use por engano valores do exemplo local.
- Validação local: YAML/URLs do workflow conferidos, setup dos logins executado
  no banco `_test`, guarda de URL ausente exercitada, 278 testes em modo `CI=true`
  com 100% de linhas e ramos, Ruff e mypy aprovados. Execução remota do Actions
  ainda depende de push.

## 2026-10-22 — F02.2a: vínculo comprovado do WhatsApp

- Migration 0014 acrescenta índice cego do remetente à inbox e tabelas de desafio
  e vínculo com RLS por dono/tenant, expiração e unicidade de remetente ativo.
- API cria código único de 15 minutos após verificar dono, telefone e plano; confirma
  somente mensagem assinada do mesmo número. Corridas de confirmação, troca de
  telefone e repetição não vinculam um negócio incorreto; vínculo e revogação
  têm auditoria durável.
- Webhook sintético e testes de falha/concorrência exercitam a prova localmente.
  UI, smoke Meta real, resolução do remetente e mídia/IA continuam pendentes.
- Migration 0014 revertida e reaplicada no banco `_test` e no desenvolvimento
  local, após backup `.local/backups/meu-braco-direito-before-0014-2026-10-22.dump`.
  As tabelas novas estavam vazias antes da reaplicação da política RLS; nenhum
  dado de vínculo foi descartado. 278 testes, 100% de linhas e ramos, Ruff e
  mypy aprovados com comandos equivalentes da `.venv`.

## 2026-10-21 — F02.1: entrada segura do WhatsApp

- Handshake e callback WhatsApp Cloud API com HMAC do corpo bruto, limite de 256 KiB,
  filtro do número/WABA configurados e separação de mensagens/status. Configuração
  ausente desabilita o webhook; nenhum segredo entra em logs/resposta.
- Migration 0013 cria inbox cifrada com dedupe por subevento, RLS e papel isolado.
  Reentregas concorrentes não duplicam registros; login normal não lê a inbox.
  Eventos ficam em quarentena até vínculo comprovado na F02.2.
- Role local criada no cluster existente; banco `_test` validou downgrade/upgrade.
  Backup local `.local/backups/meu-braco-direito-before-0013-2026-10-21.dump` antecedeu
  upgrade aditivo do banco de desenvolvimento. Dados existentes preservados.
- 271 testes backend/100% linhas e ramos; Ruff e mypy passaram. `make ci` não
  executou porque `uv` não está no PATH deste shell; comandos equivalentes da
  `.venv` passaram. Sem teste real Meta, envio, transcrição ou publicação.

## 2026-10-21 — Revisão da análise externa de IA e conhecimento do negócio

- SDD geral, fases F02–F08, PROJECT e interfaces incorporam contexto do negócio
  versionado, separado em fatos confirmados, preferências e hipóteses. Aprovação
  de conteúdo não autentica preço/horário/promoção; dono pode revisar e corrigir.
- Ledger mínimo com reserva atômica é pré-requisito de qualquer operação paga em
  F03/F04, e F07 fica responsável pela evolução comercial/relatórios.
- Geração passa a ter contratos por capacidade, FFmpeg para receitas compatíveis e
  benchmark limitado/consentido. HeyGen, Runway, Kling e Veo são candidatos sujeitos
  a spike, contrato, custo e qualidade; nenhum foi ativado por esta decisão.
- Revisão documental apenas: sem código, migration, teste de execução, acesso a
  credenciais ou mudança de status das fases. ADR em
  `docs/design/business-context-and-generation.md` registra critérios e rejeições.

## 2026-10-21 — Correção do telefone do negócio

- `/app/phone` mostra o destino E.164 do SMS; DDD e número brasileiros recebem
  `+55` automaticamente. Proprietários podem corrigir o telefone depois do
  onboarding. A alteração invalida códigos pendentes e exige nova verificação.
- `PATCH` protegido por owner/RLS e migration 0012 aditiva. Validado com 254
  testes backend, 100% de cobertura e downgrade/upgrade da migration no banco
  `_test`; aplicada também ao banco local sem alterar perfis existentes.

## 2026-10-21 — Conta de operador após revogação

- A consulta de convite agora informa também quando a identidade já foi operadora
  e teve o acesso revogado. A conta sem negócio vê `/staff-access-revoked` após
  login, em vez de entrar automaticamente no onboarding comercial.
- Um novo convite pendente continua sendo apresentado primeiro para permitir a
  reativação por aceite, novo login e MFA. Testes de API e interface cobrem a
  perda do acesso administrativo e o destino após revogação.

## 2026-10-21 — Aceite de convite e e-mails

- Convite válido acessado por outra conta responde
  `INVITATION_EMAIL_MISMATCH`; token expirado, revogado ou já usado mantém
  `INVALID_INVITATION`. A migration 0011 permite consultar apenas o convite
  correspondente ao token apresentado, preservando o isolamento entre contas.
- E-mails transacionais novos usam HTML padronizado e alternativa em texto.
  O worker também reconhece mensagens anteriores pelo assunto e extrai o link
  do corpo, inclusive quando a API em debug ainda está com código antigo.
- `GET /staff/invitations/pending` identifica o convite válido da própria conta
  para separar a entrada de operador do onboarding de negócios.

## 2026-10-21 — Reconciliação e F01.6 local

- Billing agenda consultas canônicas à Stripe para checkouts abertos sem assinatura
  ativa, mesmo se o webhook não chegar. Jobs duráveis têm dedupe por janela de cinco
  minutos, batch limitado e reaproveitam Temporal/lease/fencing. Migration 0008.
- Operadores com MFA convidam por e-mail criptografado, com expiração de 48 horas,
  idempotência, aceite por e-mail verificado e TOTP individual. Revogação cancela
  convite ou encerra sessões de staff; ações são auditadas e RLS impede concessão
  direta por clientes. Migration 0009 e telas `/admin/staff`/`/staff-invite`.
- Verificação de telefone do negócio preparada com Twilio Verify, cooldown, cinco
  tentativas, expiração e checagem `approved` antes de marcar o perfil. A UI
  `/app/phone` mostra indisponibilidade quando não há provedor. Migration 0010.
  Nenhuma entrega real de SMS/WhatsApp ocorreu: conta/credenciais não existem.
  Compose repassa somente as variáveis do provedor à API; o cliente web não recebe
  segredos. Adapter compartilha pool HTTP por processo e o fecha no shutdown.
- Migrações 0009/0010 testadas com downgrade/upgrade em `_test` e aplicadas ao banco
  local após backup; contagens de contas, tenants, negócios, perfis e jobs preservadas.
  Workers billing/auth-mail reconstruídos. API do usuário em F5 requer reinício.
- Readiness compara a revisão do banco com o head Alembic do código, recusando API
  nova sobre schema antigo; scheduler divide candidatos entre workers com
  `SKIP LOCKED` e cobre assinatura anterior vencida.
- Backend: 244 testes/100% linhas/branches, lint/tipos e integração PostgreSQL/Temporal;
  web: 107 testes/100% nos quatro critérios, tipos/build e oito jornadas Chromium,
  inclusive envio/cancelamento de convite ao Mailpit em banco `_test`. Staging AWS
  e envio real de código ficam pendentes; sem deploy, commit ou push.

## 2026-10-21 — Oportunidades de checkout no admin

- Endpoint administrativo paginado lista checkouts atuais abertos ou expirados sem
  acesso ativo, com nome do negócio, e-mail de quem iniciou a contratação e telefone
  informado (indicando se foi verificado). Não retorna link Stripe nem cartão.
- Consulta exige staff/MFA, RLS e auditoria; assinatura/patrocínio ativos não viram
  oportunidade. Índice 0007 para paginação recente, aplicado localmente e testado
  com upgrade/downgrade/upgrade no banco `_test`.
- 219 testes backend com 100% de linhas/branches; mypy aprovado. Sem cobrança nova.
- Smoke somente de leitura na base local confirmou que o negócio informado aparece
  entre as oportunidades abertas. Browser no banco `_test` validou a lista do admin.

## 2026-10-21 — Contrato para novos operadores

- F01.6 explicita convites/revogação auditados de staff, e-mail verificado,
  MFA individual e bootstrap administrativo controlado. Ainda planejado;
  o operador demo permanece restrito ao desenvolvimento local.
- Corrigido no frontend o reuso do campo de senha no passo de MFA, sem mudança
  no backend. Sem alteração de credenciais, cobrança ou dados de clientes.

## 2026-10-21 — Sessão no retorno do checkout

- Reproduzido em Chromium: login em 127.0.0.1 e retorno para localhost geram
  INVALID_SESSION, pois o cookie de refresh é host-only. Pagamento sandbox do
  titular já estava confirmado; nenhuma nova cobrança foi necessária.
- API valida Origin pela allowlist e congela na intenção antes do processamento.
  Migration 0006 adiciona return_origin nullable; legados usam configuração vigente,
  checkouts criados e sua idempotência preservam parâmetros. Produção exige origem
  exata; sem URLs arbitrárias, cookies compartilhados ou token no navegador.
- Testes de origem, replay, worker com configuração alterada, legado e URLs Stripe;
  jornadas browser para restauração após saída/retorno nos dois aliases locais.
- README usa --all-snapshot para a CLI atual. Sem commit/push/deploy.
- Validação: make ci com 218 testes/100% linhas e branches; web com 84 testes/100%,
  tipos/build e sete jornadas Playwright aprovadas. Retorno externo simulado sem
  pagamento; API/SMTP/DB _test reais. Downgrade/reaplicação da 0006 no banco de teste.
- Migration local aplicada preservando contagens de cadastros, sessões e cobrança,
  incluindo a assinatura de teste ativa. Worker billing reconstruído/atualizado;
  API do usuário em F5 precisa reiniciar. Sem nova assinatura ou cobrança.

## 2026-10-20 — F01.5: contratação e acesso

- Stripe escolhido como primeiro adapter para teste/produção, sem alegação de
  liderança de mercado nem cobrança comercial habilitada. ADR/SDD em design/billing.md.
- API de status, intenção de checkout idempotente, webhook assinado com inbox de
  referências, consulta canônica e jobs Temporal. Timers duráveis para expiração,
  lease/fencing, retry limitado e falha rastreável. URLs de pagamento fora do
  histórico Temporal; mensagens sensíveis do SDK não entram em falhas do workflow.
- Migration 0005 com role billing isolada e FORCE RLS. Runtime não confirma
  pagamento; billing não escreve identidade/membership/patrocínio ou auditoria antiga.
- Patrocínio de seis meses com motivo, replay sem extensão e revogação auditada;
  estado pago/teste/patrocinado separado. Auditoria/outbox atômicas, MRR indisponível.
- Cliente /app/billing, admin /admin/billing, busca limitada e contagens reais.
  Checkout indisponível sem keys/Price/valor; callback de sucesso não ativa acesso.
- CI inclui login restrito billing. Compose/debug incluem processo billing,
  inativo para provedores no modo disabled. R$99 continua exemplo de sandbox.
- Downgrade/upgrade da 0005 validado no banco _test; upgrade main preservou
  contagens de contas, organizações, negócios/perfis e memberships. Sem deploy/push.
- Pendentes: conta e credenciais do titular, sandbox real, plano/franquias/termos,
  conciliação periódica/reprocesso, portal/cancelamento, staging/AWS e carga.
- Validação final local: make ci com 206 testes, 100% linhas/branches, lint/tipos;
  frontend 84 testes/100% em quatro critérios, tipos/build/formatação. Cinco
  jornadas Playwright com API/SMTP reais passaram, incluindo uso/revogação de
  patrocínio. Adapter Stripe validado por contratos, não por cobrança em sandbox.
- Imagens API/billing construídas; role billing pronta no Docker e processo
  disabled verificado. Migração local preservou dados existentes. F01.5 permanece
  aberta até validação do provedor e staging; sem commit/push/deploy/cobrança real.
- Rollback completo até base e upgrade head passaram no banco _test, com logins
  restritos reaplicados. Preparo de browser recusou billing apontando para main
  antes de semear/resetar fixtures. Servidores temporários de QA encerrados;
  processos do usuário e o serviço billing local/disabled foram preservados.

## 2026-10-20 — Contexto do negócio e cidade estruturada

- Web amplia atividades com opção livre e permite qualquer cor HEX, além de sugestões.
- API oferece catálogo público IBGE versionado (27 UFs/5.571 municípios), cacheado
  em memória, sem chamadas externas ou acesso a dados de tenant no cadastro.
- Validação conjunta de município/UF/código; migration 0004 aditiva e reversível.
  Perfis legados e hashes de replay mantidos. Código IBGE não equivale a coordenadas.
- Testes de catálogo, incompatibilidade de UF/cidade/código, persistência atômica,
  replay e cores/atividades livres. `make ci`: 131 testes, 100% linhas/branches.
- Downgrade/upgrade da 0004 validado no banco _test. Upgrade local preservou
  contagens de contas, organizações e perfis. API em F5 requer reinício.
- Frontend: 62 testes com cobertura 100% em quatro critérios, formato e build
  aprovados. Quatro jornadas Playwright com API/SMTP reais passaram, incluindo
  novo onboarding desktop/mobile. Build Docker confirmou snapshot de 5.571 cidades
  presente na imagem. Relatórios/sessões de QA locais, sem dados da base principal.
- F01.5/F01.6 e staging continuam pendentes; sem commit, push ou deploy.

## 2026-10-20 — Cadastro local: ORIGIN_REJECTED

- Reproduzido 403 com Origin http://127.0.0.1:5173, endereço anunciado pelo Vite,
  enquanto a API estava configurada com http://localhost:5173.
- Guard de auth aceita ambos os nomes de loopback em development/testing,
  preservando porta/protocolo. Staging/production continuam com origem exata;
  nenhum wildcard/CORS permissivo. Links canônicos e cookies host-only preservados.
- Regressão cobre cadastro/verificação/login/refresh pelo alias, rejeição de
  origem ausente/null, outros hosts, portas e protocolos e isolamento por ambiente.
- Validação: `make ci` aprovado, 117 testes e 100% de linhas/branches; lint e tipos
  aprovados. Reprodução HTTP também confirmou que o proxy Vite preserva Origin.
- Não exige migration. Debug F5 sem reload precisa reiniciar para carregar a correção.

## 2026-10-20 — F01.1–F01.4 implementadas localmente

- Atualizados SDD geral e fases com contratação automática, provisionamento,
  onboarding WhatsApp, admin interno e área do cliente. F01.5 antecipa cobrança mínima.
- Criados SDDs geral/admin/cliente no novo repositório local-spark-web.
- Entregues OIDC/RS256/JWKS com cache/timeout/rotação, identidade por issuer+subject,
  sessão e contexto; HS256 legado limitado a desenvolvimento/testes sem OIDC.
- Migration 0002 adiciona identidade, staff, perfil, consentimentos e registro de
  onboarding; RLS e permissões limitam bootstrap ao primeiro owner e negam hijack.
- Onboarding usa lock transacional por ator, deduplicação, replay e conflito de payload;
  negócio, perfil, consentimentos, auditoria e outbox compartilham transação.
- Admin readonly auditado com métricas reais, busca limitada e paginação; cliente
  não recebe privilégio global. Contas/memberships/staff revogados têm acesso negado.
- Keycloak/Mailpit locais, realm público PKCE e audience da API; seed do operador
  local sem impressão de tokens. Debug passa a iniciar também identidade e e-mail.
- Web independente com SDDs geral/admin/cliente, login, onboarding, áreas distintas e
  estados reais. Documentação de execução atualizada; referência React preservada.
- Evidência: `make ci` passou com **85 testes, 573 statements e 62 branches, 100%**;
  lint/tipos, rollback/reaplicação no banco `_test` e build Docker aprovados.
- Frontend: 31 testes com 100% de cobertura, build e quatro jornadas reais Playwright
  em desktop/mobile. F01 inteira permanece aberta; sem CI remoto/deploy nesta entrega.
- Checkout, verificação WhatsApp, convites e staging permanecem pendentes.

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

## 2026-10-20 — Nome e ambiente Meu Braço Direito

- Adotado `local-spark-platform` como repositório principal, preservando seu remoto
  e as alterações locais existentes. Restaurados os arquivos de CI, Docker e
  configuração que não estavam presentes na cópia do repositório.
- Padronizados nome de pacote, Swagger, logs, configuração `MEU_BRACO_DIREITO_`, issuer,
  audience e task queue. Bancos usam `meu_braco_direito_platform` e
  `meu_braco_direito_platform_test`; roles usam `meu_braco_direito_*`.
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

## 2026-10-20 — Auth própria substitui Keycloak

- Decisão do usuário registrada em `docs/design/native-auth.md` e refletida nos
  SDDs geral/F01/F08, PROJECT, operação e READMEs. OIDC do GitHub/AWS permanece.
- FastAPI implementa cadastro, login, sessão JWT curta/revogável, refresh aleatório
  com hash, cookie HttpOnly, CSRF/Origin, rotação atômica e revogação por reutilização.
- Argon2id com concorrência limitada fora do event loop; verificações de sessão,
  conta ativa e MFA administrativo em cada pedido/renovação. Falhas sanitizadas.
- Staff exige TOTP, segredo criptografado, proteção de replay e recuperação de uso
  único. Reset de senha revoga sessões e preserva MFA; mudança de papel exige prova.
- Verificação/reset com ações de uso único e TTL, outbox criptografada e worker SMTP
  separado com lease/fencing, retry limitado e recuperação de leases expirados.
- Migration 0003 mantém usuários/empresas/vínculos e prepara credenciais sem senha
  para e-mails antigos não ambíguos. Login DB de auth isolado, sem acesso a negócio
  ou concessão de staff; readiness verifica também o banco de autenticação.
- Tokens/credenciais excluídos de parâmetros SQL de diagnóstico e respostas 422.
- Keycloak removido do Compose/debug, container encerrado/removido sem apagar seu
  volume legado. Mailpit permanece local, com SMTP 11025 no host e 1025 no Docker.
- Seed local preserva IDs/senhas/MFA; seed que imprimia JWT sem sessão foi aposentado.
- Frontend usa telas e AuthProvider próprios; bibliotecas OIDC removidas. Cookies
  restauram a sessão após recarga; cache/logout entre abas e tratamento de links
  sucessivos na mesma aba validados por testes.
- Evidência: `make ci` aprovado com 103 testes, **100% linhas/branches** em todos os
  módulos app, sem novas exclusões. Frontend com 59 testes e 100% em quatro critérios.
- Migration downgrade/base/upgrade validado no banco exclusivo _test. O preparo de
  browser recusa main/remoto e não toca dados da aplicação. Build Docker e browser
  registrados após a validação completa. AWS/staging e demais fatias continuam pendentes.
- Validação final: quatro jornadas Playwright reais passaram (staff com MFA/logout,
  cliente/onboarding/recarga/403, registro/verificação/reset/replay e navegação pública).
  Builds web/API/SMTP aprovados. Smoke na imagem Docker confirmou readiness dos
  dois logins DB, login nativo, vínculo antigo preservado, revogação imediata por
  logout e entrega SMTP real no Mailpit. Nenhum provedor de identidade externo usado.
