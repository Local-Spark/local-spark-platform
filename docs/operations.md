# Operação e deploy

F00 é fundação local. Antes de expor a clientes: onboarding/auth completo, app reviews,
políticas e gates das fases seguintes. Nunca usar `.env.example` em produção.

## Ambiente local

F01.5 acrescenta o processo `billing` em Compose/debug. Por padrão ele registra
billing.disabled e não consome jobs no Temporal nem chama Stripe. Login restrito
local_spark_payments/local_spark_billing, separado de auth/app/relay. Setup de
sandbox, flags live e contratos em [SDD billing](design/billing.md) e README.
Durante compras na sandbox local, mantenha o listener em execução:

```bash
stripe listen --all-snapshot --forward-to http://localhost:8000/api/v1/webhooks/stripe
```

A Stripe pode concluir o pagamento mesmo que esse listener esteja fechado. A volta
ao site não ativa o plano por si só. O processo billing agenda reconciliação
canônica de checkouts abertos a cada 30 segundos (até 25 por ciclo, com dedupe por
janela de cinco minutos), além do timer de expiração. Depois que o worker consulta
a sessão/assinatura/fatura na Stripe, o acesso pode ser ativado sem o webhook
perdido. Não repetir a compra; confirmar o estado pelo endpoint de assinatura.
Reiniciar o listener não retransmite automaticamente eventos perdidos.
Nunca reprocessar um checkout ambíguo com uma nova chave: consultar estado canônico
da sessão/assinatura antes de alterar intent, lease ou estado de falha. Billing jobs
failed e billing_outbox pending são duráveis; reprocesso e consumo de notificações
dependem das próximas fatias. Não escrever mensagens incompatíveis no outbox
business.created. Nenhuma integração comercial está ativa apenas por subir o worker.

F01.6: convites de staff saem pelo worker `auth-mail` para o e-mail convidado e
expiram em 48 horas. O operador acessa `/staff-invite`, usa conta com e-mail
verificado e faz novo login para configurar TOTP. O painel `/admin/staff` exige
staff/MFA. Revogação encerra sessões. Inspecionar `auth_mail.state=failed` se o
convite não chegar; não copiar token/ciphertext para logs ou tickets.
O aceite exige login com o mesmo e-mail que recebeu o convite. A API distingue
`INVITATION_EMAIL_MISMATCH` de convite inválido/expirado, e a interface orienta
trocar de conta e reabrir o link original. E-mails de confirmação, recuperação e
convite usam HTML padronizado com alternativa em texto. O worker reconhece também
payloads antigos desses três assuntos, desde que tenham link HTTP(S) no corpo.
Atualizar o worker `auth-mail` para aplicar o template. A migration 0011 é
necessária para a distinção de e-mail sob RLS; reiniciar a API depois da migration.
`GET /staff/invitations/pending` só consulta convite da identidade autenticada;
conta convidada sem negócio vai à orientação de aceite, nunca ao onboarding comercial.
Esse endpoint também retorna `revoked` para uma conta que já foi operadora. Se o
acesso foi revogado e não há convite novo, a web mostra `/staff-access-revoked`.
Um novo convite pendente prevalece sobre a revogação anterior; o aceite reativa
staff somente após login com o mesmo e-mail e novo login/MFA.

Verificação de telefone usa Twilio Verify e fica desativada por padrão. Após criar
conta, Verify Service e API key, configurar no backend `LOCAL_SPARK_PHONE_VERIFY_MODE=twilio`,
`LOCAL_SPARK_TWILIO_VERIFY_SERVICE_SID`, `LOCAL_SPARK_TWILIO_API_KEY` e
`LOCAL_SPARK_TWILIO_API_SECRET`. O canal padrão é SMS; `LOCAL_SPARK_PHONE_VERIFY_CHANNEL`
pode ser `whatsapp` se o serviço estiver habilitado para isso. Reiniciar API após
configurar. O número do perfil deve ser brasileiro válido ou E.164; código vence
em 10 minutos, espera mínima entre envios de 60 segundos e máximo de cinco
tentativas. Nenhum dado de teste local substitui entrega real. No staging, validar
envio/recebimento, número trocado, rate limit e falhas do provedor antes do piloto.

`docker compose up -d postgres temporal mailpit`; migração separada com conexão administrativa.
O SQL de inicialização cria logins locais sem bypass e banco `local_spark_platform_test`. As roles
de acesso são concedidas sem propriedade das tabelas. Se volume já existe, initializer
não roda novamente; não apagar volumes para corrigir migrações de usuário.

PostgreSQL em 55432; Temporal gRPC 7233 e UI 8233, todos ligados ao loopback.
Temporal start-dev é exclusivamente desenvolvimento/CI, não topologia de produção.
Seu SQLite fica no volume nomeado `local-spark-platform_local-spark-temporal`,
preservando o histórico ao recriar o container de desenvolvimento.
Isso não representa persistência/HA de produção nem substitui Temporal Cloud.
API só sobe após migration; health live não acessa DB, ready exige exatamente o
head Alembic do código em execução. Durante deploy, migração deve preceder a
versão nova da API.

## Runtime

API: `uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --no-access-log`.
Worker: `python -m app.entrypoints.worker`. Relay: `python -m app.entrypoints.relay`.
API/worker usam runtime login; relay tem URL específica e só acessa outbox. Owner
credencial serve apenas a migrações/provisionamento, nunca é variável de runtime.

Outbox fica `failed` após falhas repetidas conhecidas de entrega e precisa intervenção.
Lease perdido é reivindicável; fencing impede confirmação tardia. Temporal rejeita
workflow ID repetido inclusive depois de concluído dentro da retenção/contrato; o
consumer no banco também deduplica o evento, independentemente dessa retenção.
Expiração do histórico não deve ser usada para repetir operação paga: fases futuras
mantêm tombstones e operação externa persistente.

## GitHub Actions / AWS

Configurar environments `staging` e `production` com permissões e revisores conforme
política do time, OIDC restrito a repo/environment, sem chaves AWS permanentes.
Variáveis: AWS_REGION, AWS_ROLE_ARN, ECR_REPOSITORY, ECS_CLUSTER, ECS_SERVICE,
ECS_TASK_FAMILY e ECS_CONTAINER_NAME. Infra cria task definition com secret refs e
IAM mínimos. TLS Temporal é obrigatório fora de desenvolvimento.

Auth própria: definir `LOCAL_SPARK_AUTH_DATABASE_URL` com login restrito distinto
(`local_spark_auth`), chave de assinatura aleatória e `LOCAL_SPARK_AUTH_ENCRYPTION_KEY`
Fernet privada. Staging/PRD exigem `PUBLIC_WEB_URL` HTTPS, SMTP com STARTTLS/autenticação
e TLS Temporal. Prefixar as variáveis de aplicação com `LOCAL_SPARK_`.
O worker `python -m app.entrypoints.auth_mail` usa apenas o login de auth, sem
privilégio sobre empresas. Mailpit e exemplos de chave/senha são exclusivamente locais.
Secrets Manager guarda assinatura, chave Fernet, senha SMTP e credenciais Twilio;
não versionar valores reais.

Cookies têm prefixo __Host- em HTTPS, path /, Secure e SameSite=Lax; refresh é
HttpOnly, CSRF é legível pelo browser e vinculado ao registro da sessão. `/api` e
web devem compartilhar origem. Proxy deve preservar Origin e encaminhar Cookie/
Set-Cookie e Authorization; desabilitar cache para `/api/*`. Não cachear respostas
com sessão no CloudFront. Configure o IP real somente com proxies conhecidos;
limites por IP não devem confiar em X-Forwarded-For arbitrário da internet.

Workers SMTP fazem claim com lease/fencing e retries; falhas terminais ficam em
`auth_mail.state=failed`, exigindo diagnóstico/reenvio controlado. Não imprimir
ciphertext de MFA/outbox, tokens, links, senhas ou códigos em diagnósticos.
Verificação/reset podem gerar e-mails repetidos, mas a ação só é consumida uma vez.
Chave Fernet não pode ser simplesmente substituída: recriptografar MFA/outbox e
validar antes da rotação. Atualização da chave JWT invalida access tokens antigos;
refresh válido emite token novo. MFA perdido exige código de recuperação ou
procedimento administrativo com comprovação e auditoria, sem bypass público.

Migration 0003 preserva atores, tenants e memberships e cria credenciais sem senha
para e-mails antigos não ambíguos; o usuário define senha via recuperação. E-mail
ambíguo exige conciliação manual sem merge automático. Seed só altera as duas
contas locais conhecidas, e nunca sobrescreve senha/MFA já configurados.
Nenhum deploy/recurso AWS foi criado nesta entrega. A topologia e IaC continuam
pendentes e o primeiro destino deve ser staging, antes de piloto com clientes.

`Deploy ECS` é manual, somente main e mesmo SHA de CI verde. Publica tag de commit
em ECR e atualiza serviço ECS existente. Antes do deploy, aplicar migrações compatíveis
por tarefa separada com role de migração e confirmar `database_ready`. Não executar
DDL com login runtime. Workflow não provisiona conta/infra nem garante rollback de
schema; expand/contract e estratégia de workers ativos fazem parte da F08.

O remoto Git já está configurado. Variáveis, roles e recursos AWS ainda precisam
ser configurados; o pipeline não foi executado remotamente. Não foi feita nenhuma
alteração na AWS/GitHub.
