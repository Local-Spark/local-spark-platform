# F01 — Identidade, onboarding e interfaces iniciais

Status: Em implementação. Atualizado em 20/10/2026. Dependência: F00.

21/10/2026: pagamento de sandbox confirmado no banco; retorno externo entre aliases
locais reproduziu INVALID_SESSION. Migration 0006 e validação de Origin preservam
o host autorizado da sessão nos retornos success/cancel. Cookies continuam host-only;
staging/produção não aceitam aliases. Demais cenários externos e staging pendentes.
Validação da correção: 218 testes backend/100%, 84 testes web/100%, sete jornadas
Playwright, migration 0006 reversível no _test e aplicada localmente sem perda.

## Objetivo e jornada aceita

O cliente conhece a Local Spark na landing page, contrata um plano e tem sua
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
| F01.6 | Convites, revogação, telefone verificado e validação em staging | Planejada |

F01.6 incluirá convite de operadores da plataforma, separado dos convites para
equipe de cada negócio. Somente staff ativo com MFA poderá convidar outro operador.
Convite terá e-mail verificado, token de uso único e expiração; concessão e revogação
de staff serão auditadas. Cada operador usará credenciais e TOTP próprios; revogar
staff deverá invalidar acesso administrativo/sessões. Conta demo local é bootstrap
de desenvolvimento, não processo de cadastro para produção. O cadastro público
continua sem capacidade de conceder staff; a primeira conta administrativa de
cada ambiente requer bootstrap operacional controlado.

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
  atômico do primeiro tenant/membership/business/profile/outbox. Replay do mesmo
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
- Validação local não fecha F01 inteira: checkout real, convites, telefone e staging
  precisam das integrações e validações pendentes.

## Continuidade

Atualizar PROJECT.md, SDD geral, este SDD e CHANGELOG.md em cada feature.

## Fluxo implementado

O diagrama de autenticação vigente está no [SDD auth](../design/native-auth.md).
Depois de autenticar, POST /session retorna contexto; POST /onboarding confirma
identidade/e-mail/consentimento e cria tenant, owner, negócio, perfil, auditoria e
outbox na mesma transação. O relay entrega o evento ao Temporal sem efeito pago.

Validação backend: 206 testes, 100% linhas/branches. Frontend e browser no changelog
web; migration e imagem Docker no changelog backend. Staging e demais fatias da F01
continuam pendentes. A autenticação implementada não comprova capacidade para 200 mil.
