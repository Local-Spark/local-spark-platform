# F01 — Identidade, onboarding e interfaces iniciais

Status: Em implementação. Atualizado em 20/10/2026. Dependência: F00.

21/10/2026: pagamento de sandbox confirmado no banco; retorno externo entre aliases
locais reproduziu INVALID_SESSION. Migration 0006 e validação de Origin preservam
o host autorizado da sessão nos retornos success/cancel. Cookies continuam host-only;
staging/produção não aceitam aliases. Demais cenários externos e staging pendentes.
Validação da correção: 218 testes backend/100%, 84 testes web/100%, sete jornadas
Playwright, migration 0006 reversível no _test e aplicada localmente sem perda.

## Objetivo e jornada aceita

O cliente conhece a Meu Braço Direito na landing page, contrata um plano e tem sua
organização provisionada automaticamente após confirmação confiável. Identidade
e posse do canal precisam ser verificadas; informar e-mail/telefone no checkout
não concede propriedade. A configuração diária migra para o WhatsApp na F02.
Páginas web curtas atendem identidade, contexto, OAuth, consentimentos e assinatura.
Uma conta pode participar de várias organizações; organização, usuário, negócio,
assinatura e conta social são entidades distintas. Patrocinados por seis meses são
uma categoria explícita de concessão, sem aparecer como clientes pagantes.

## Fatias e estado

| Fatia | Entrega | Estado |
| --- | --- | --- |
| F01.1 | Auth própria, sessão, provisionamento idempotente, proprietário e perfil | Implementada localmente |
| F01.2 | Base React/TypeScript, login e separação de áreas | Implementada localmente |
| F01.3 | Admin mínimo com organizações, usuários e onboarding reais | Implementada localmente |
| F01.4 | Onboarding inicial do cliente e consentimento de termos/privacidade | Implementada localmente |
| F01.5 | Checkout, webhook e ativação automática; concessão patrocinada | Código local validado; fase aberta até sandbox/staging |
| F01.6 | Convites, revogação, telefone verificado e validação em staging | Código local validado; provedor de envio/staging pendentes |

F01.6 inclui convite de operadores da plataforma, separado dos convites para
equipe de cada negócio. Somente staff ativo com MFA poderá convidar outro operador.
Convite terá e-mail verificado, token de uso único e expiração; concessão e revogação
de staff serão auditadas. Cada operador usará credenciais e TOTP próprios; revogar
staff deverá invalidar acesso administrativo/sessões. Conta demo local é bootstrap
de desenvolvimento, não processo de cadastro para produção. O cadastro público
continua sem capacidade de conceder staff; a primeira conta administrativa de
cada ambiente requer bootstrap operacional controlado.

Convite: `POST /admin/staff/invitations` com Idempotency-Key, listagem em
`GET /admin/staff`, aceite autenticado em `/staff/invitations/accept` e DELETE
para convite/acesso. E-mail usa outbox criptografada e entrega SMTP; aceite exige
conta com e-mail verificado e força novo login/MFA. RLS só permite criar convite
a staff ativo e impede um cliente de fabricar o próprio. Revogação é auditada e
encerra sessões. Web em `/admin/staff` e `/staff-invite`. O aceite distingue
convite inválido de conta autenticada com e-mail diferente do destinatário;
nesse caso, orienta troca de conta e reabertura do link original. Convites,
verificação de e-mail e recuperação de senha usam template HTML único com
alternativa em texto simples; o worker também reconhece payloads antigos desses
três tipos. O endpoint `GET /staff/invitations/pending` permite que a conta
convidada sem negócio veja instruções de aceite, sem ser enviada ao onboarding
comercial. Após aceite e novo login com MFA, a entrada vai ao admin.
Depois da revogação, a identidade permanece válida, mas perde sessões e acesso
administrativo. O estado `revoked` da consulta de convite leva a conta sem negócio
para `/staff-access-revoked`, em vez do onboarding comercial. Um novo convite
pendente tem prioridade e permite recuperar o acesso pelo aceite e novo login/MFA.

Telefone: `GET/POST /organizations/{tenant}/businesses/{business}/phone-verification`
`PATCH` no mesmo recurso para corrigir o número e `POST .../confirm`, somente
proprietário. Número brasileiro é normalizado para
E.164; envio via Twilio Verify SMS por padrão, canal WhatsApp configurável. Pedido
persistido antes da chamada externa, cooldown de 60 s, expiração de 10 min e no
máximo cinco tentativas. Só a resposta `approved` do provedor permite alterar
`business_profiles.phone_verified`; troca de número/solicitação concorrente não
confirma um desafio antigo. `PHONE_VERIFY_MODE=disabled` é o padrão e mostra
indisponibilidade em `/app/phone`. Sem conta Twilio, não há entrega real de código;
sem ambiente AWS, não há homologação em staging. Verificar número não vincula a
conta WhatsApp: essa conexão/autorização continua na F02.
O `GET` mostra o destino E.164 do SMS, incluindo `+55` adicionado a números
brasileiros digitados com DDD. Corrigir o número exige dono ativo, grava o formato
canônico, limpa a verificação existente e invalida desafios anteriores. Migration
0012 libera apenas a coluna `phone` para atualização sob a política RLS de dono.

As primeiras quatro fatias criam uma organização em setup, sem ativar geração paga.
F01.5 antecipa a parte mínima de cobrança da F07. Nunca marcar pagamento por redirect,
parâmetro do navegador ou simples conclusão de checkout ainda não liquidado. Evento
assinado/reconciliado é deduplicado e provisiona/ativa uma única vez. O usuário pode
criar identidade e rascunho de organização antes de pagar; não recebe franquia paga.
O admin distingue acesso de intenção de compra: checkout aberto sem pagamento
confirmado aparece como oportunidade, com contato cadastrado e prazo; expirado
fica em filtro separado. Fechar o navegador não prova abandono. A lista é paginada,
auditada e restrita a staff/MFA, sem expor URL do Stripe ou cartão.

## Identidade e autorização

Decisão vigente: [SDD/ADR de autenticação própria](../design/native-auth.md), aceita
em 20/10/2026. Substitui Keycloak/OIDC: módulo da FastAPI e telas React próprias.

- Argon2id fora do event loop com concorrência limitada, cadastro e login próprios.
- JWT HS256 curto com issuer/audience/tipo/sub/sid; refresh aleatório com hash no
  banco, cookie HttpOnly, rotação atômica, conflito concorrente e revogação por reuse.
- Sessão/conta verificadas a cada pedido; logout/reset/revogação imediatos.
- Cookie host-only, Secure em HTTPS, SameSite=Lax, CSRF vinculado à sessão e Origin
  explícito. Tokens só em memória; nenhum token no localStorage/sessionStorage.
  Localhost/127.0.0.1 são aliases apenas em development/testing e na mesma porta/
  protocolo; staging/production exigem origem exata. Links de e-mail são canônicos.
- Verificação de e-mail e reset de uso único, com TTL, fragmentos limpos no navegador,
  respostas genéricas e outbox SMTP criptografada com lease/fencing/retry.
- Segundo fator TOTP obrigatório para staff, segredo criptografado e códigos de
  recuperação de uso único; reset de senha não remove MFA.
- Role DB de auth separada, sem acesso a empresas/memberships ou concessão de staff.
- UUIDs e vínculos antigos preservados; credenciais antigas sem senha exigem
  recuperação por e-mail. Inscrição pública não faz merge/associação pelo e-mail.
- Contas desativadas não são reativadas e owner não recebe autorização global.

## Contratos iniciais

F01.5: [SDD detalhado de cobrança](../design/billing.md). Stripe test/live, inbox
durável e Temporal em processo billing separado. Conta/negócio em setup antes do
checkout nesta fatia; propriedade é vinculada ao owner autenticado, não ao pagador.
Plano único mensal BRL configurado; sem keys/Price/valor não há cobrança.
Patrocínio exige staff/MFA e motivo, dura seis meses de calendário e pode ser
revogado. Não renova nem vira pagamento automaticamente. Um benefício inicial por
organização, com replay sem extensão. Ledger/franquias permanecem na F07.
Rotas web: /app/billing e /admin/billing. Pagantes live, testes e patrocinados
contados separadamente; nenhum MRR inventado. Sandbox/staging ainda não validados.

- POST /api/v1/auth/register, /login, /mfa/verify, /refresh e /logout.
- POST /api/v1/auth/verification-request, /verify-email, /password-reset-request e /reset-password.
- POST /api/v1/session: sincroniza identidade validada e retorna contexto do usuário.
- GET /api/v1/me: retorna organizações acessíveis e permissão administrativa.
- POST /api/v1/onboarding: contexto confirmado, termos/privacidade e provisionamento
  atômico do primeiro tenant/membership/business/profile/auditoria. Replay do mesmo
  cadastro retorna os mesmos recursos; payload diferente gera 409.
- GET /api/v1/admin/overview: contagens reais e série de cadastros, sem receita estimada.
- GET /api/v1/admin/organizations: lista paginada e busca limitada, acesso de staff.
- GET /api/v1/admin/billing/opportunities: checkouts abertos/expirados sem acesso
  ativo, com paginação e modo test/live do ambiente.
- Telefone informado é não verificado até a integração de verificação; consentimento
  de termos não autoriza voz/avatar nem publicação.

## Interfaces e design

Onboarding: 32 sugestões de atividade e opção Outro com descrição livre; cor principal
por 12 sugestões, seletor livre ou HEX validado. Estado + busca de cidade com
sugestões IBGE; nova seleção de estado limpa cidade. A web bloqueia conclusão sem
cidade válida, enquanto a API verifica UF/código/nome. Catálogo local versionado,
sem depender do IBGE durante cadastro. Loading, falha e retry preservam o formulário.
Migration 0004 adiciona campos opcionais a perfis antigos, sem adivinhar UF nem
alterar hashes de replay legados. Não inclui edição posterior do perfil ou geocoding.

Repositório separado local-spark-web, React/TypeScript/Vite/Router, organização
inspirada em rogue-skydogg-ui sem copiar seu domínio ou alterar seus arquivos.
Mesmo repositório para admin e cliente; rotas/permissões distintas. Design claro,
fundo off-white, texto escuro, acentos índigo e verde, espaços generosos, tipografia
forte, ícones consistentes e detalhes geométricos discretos. Futurista com legibilidade.
Admin acompanha pessoas/negócios; cliente acompanha configuração. Painel completo,
revisão de conteúdo, assinatura e analytics entram com seus respectivos backends.
Ver SDDs em local-spark-web/docs/{SDD,admin-SDD,client-SDD}.md.

## Testes e critérios

- Cadastro/login, JWT inválido, sessão revogada/expirada, CSRF/Origin, MFA e recuperação.
- Rotação concorrente/reuse, ações de uso único, rollback e isolamento da role auth.
- Replay concorrente do onboarding, conflito, rollback e contexto de duas organizações.
- Owner não vira admin; staff revogado negado; consultas administrativas auditadas.
- Fonte de cada indicador explícita; dados ausentes não viram zero ou sucesso inventado.
- Backend mantém 100% linhas/branches; frontend com testes de jornadas/estados e build.
- Validação local não fecha F01 inteira: entrega real do código, cenários restantes
  da Stripe e staging precisam das integrações e validações externas pendentes.

## Continuidade

Atualizar PROJECT.md, SDD geral, este SDD e CHANGELOG.md em cada feature.

## Fluxo implementado

O diagrama de autenticação vigente está no [SDD auth](../design/native-auth.md).
Depois de autenticar, POST /session retorna contexto; POST /onboarding confirma
identidade/e-mail/consentimento e cria tenant, owner, negócio, perfil e auditoria
na mesma transação. P14 (27/10/2026) retira o evento-recibo que apenas repetia a
auditoria; não há workflow novo de CRUD sem ação de negócio. E-mails, cobrança e
demais efeitos assíncronos mantêm suas intenções/filas próprias.

Validação atual: 244 testes backend, 100% linhas/branches; 107 testes web, 100%
nos quatro critérios; oito jornadas Chromium com banco `_test`. Migrations 0008–0010
reversíveis no teste e aplicadas localmente. Staging e envio real de telefone seguem
pendentes. A autenticação implementada não comprova capacidade para 200 mil.
