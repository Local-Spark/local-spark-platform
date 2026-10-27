# Operação e deploy

F00 é fundação local. Antes de expor a clientes: onboarding/auth completo, app reviews,
políticas e gates das fases seguintes. Nunca usar `.env.example` em produção.

## Ambiente local

F01.5 acrescenta o processo `billing` em Compose/debug. Por padrão ele registra
billing.disabled e não consome jobs no Temporal nem chama Stripe. Login restrito
meu_braco_direito_payments/meu_braco_direito_billing, separado de auth/app/relay. Setup de
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
da sessão/assinatura antes de alterar intent, lease ou estado de falha. Jobs de
cobrança com falha permanecem duráveis e exigem revisão antes de reprocessamento.
A migração `0038_retire_billing_outbox` preserva os eventos financeiros em
`billing_audit` e remove a outbox sem consumidor; não há notificações financeiras
agendadas por ela. Atualizar API e processo `billing` junto da migração, evitando
executáveis antigos que ainda gravam a tabela retirada. O login de migração
precisa de BYPASSRLS; permissões de runtime continuam restritas. Não escrever
eventos financeiros no outbox geral de `business.created`. Nenhuma integração
comercial está ativa apenas por subir o worker.

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
conta, Verify Service e API key, configurar no backend `MEU_BRACO_DIREITO_PHONE_VERIFY_MODE=twilio`,
`MEU_BRACO_DIREITO_TWILIO_VERIFY_SERVICE_SID`, `MEU_BRACO_DIREITO_TWILIO_API_KEY` e
`MEU_BRACO_DIREITO_TWILIO_API_SECRET`. O canal padrão é SMS; `MEU_BRACO_DIREITO_PHONE_VERIFY_CHANNEL`
pode ser `whatsapp` se o serviço estiver habilitado para isso. Reiniciar API após
configurar. O número do perfil deve ser brasileiro válido ou E.164; código vence
em 10 minutos, espera mínima entre envios de 60 segundos e máximo de cinco
tentativas. Nenhum dado de teste local substitui entrega real. No staging, validar
envio/recebimento, número trocado, rate limit e falhas do provedor antes do piloto.
Na tela `/app/phone`, o destino mostra o número com `+55` normalizado antes do
envio. O proprietário pode corrigir o número pelo `PATCH` no recurso de verificação;
isso remove a condição de verificado e invalida o código anterior. A migration
0012 é necessária para a atualização de `business_profiles.phone` pela role runtime.

F02.1 usa `GET/POST /api/v1/webhooks/whatsapp` para desafio e eventos da Meta.
Por padrão `MEU_BRACO_DIREITO_META_WEBHOOK_MODE=disabled`; a rota responde 503. Para
habilitar em ambiente de teste com App/WABA e número próprios, configurar no
backend o modo `cloud`, `META_DATABASE_URL` com login exclusivo `meu_braco_direito_ingest`,
`META_VERIFY_TOKEN`, `META_APP_SECRET`, `META_WABA_ID`, `META_PHONE_NUMBER_ID` e
`META_ENCRYPTION_KEY` Fernet privada, todos sob prefixo `MEU_BRACO_DIREITO_`. Reiniciar
API; `/health/ready` exige migration 0013 e acesso ao banco restrito. A URL de
callback precisa de HTTPS público controlado; não expor um túnel sem assinatura.
O login recebe `meu_braco_direito_meta`, não `meu_braco_direito_app`/auth/billing. No volume
local já existente, criar o login e conceder a role uma vez com
`docker compose exec -T postgres psql -U postgres -d postgres < scripts/ensure_local_meta_login.sql`;
initializer não roda novamente. Não apagar o volume. O banco de testes também precisa do login
`TEST_META_DATABASE_URL` na base `_test`.

Cada callback autenticado é gravado na `whatsapp_inbox` cifrada e deduplicada;
a correlação e o workflow posteriores só operam após vínculo/consentimento.
Reentrega
da Meta recebe 200 após commit sem criar duplicata. Falha de banco retorna erro,
permitindo retry do provedor. Nunca consultar/copiar ciphertext ou payload bruto
para logs/tickets. Ingressão remove linhas expiradas quando chega novo evento;
F02.2b acrescenta correlação e processamento. A
[coleção oficial da Meta](https://www.postman.com/meta/whatsapp-business-platform/overview)
documenta a configuração do webhook e os formatos de mensagens/status.

F02.2a acrescenta a migration 0014. Após backup, aplicá-la antes de iniciar a
API nova. O proprietário com telefone verificado e plano ativo chama `POST` no
recurso `/api/v1/organizations/{tenant_id}/businesses/{business_id}/whatsapp-link`,
envia exatamente a mensagem retornada para o número oficial da plataforma e
chama `POST` no mesmo recurso com sufixo `/confirm`. O `GET` mostra o status.
Sem modo Meta `cloud` e webhook real, o vínculo fica indisponível; simulações
somente no banco `_test`. Trocar o telefone desativa o vínculo. A inbox segue sem
processamento de material. Rotação da chave `META_ENCRYPTION_KEY` requer migrar
e reindexar dados antes de aplicá-la, pois também é chave para HMAC do remetente.

F02.2b1 adiciona a migration 0015 e o processo `whatsapp-correlator`. Após backup,
aplicar a migração; no volume PostgreSQL existente, criar o login restrito uma
vez com `docker compose exec -T postgres psql -U postgres -d postgres <
scripts/ensure_local_correlator_login.sql`. O processo usa
`MEU_BRACO_DIREITO_CORRELATOR_DATABASE_URL` e a mesma
`MEU_BRACO_DIREITO_META_ENCRYPTION_KEY` da API. O processo não precisa das
credenciais de assinatura do app Meta; ele permanece desativado sem URL do login
restrito ou chave de criptografia. A API de webhook exige modo Meta `cloud`.
Sua fila cifrada mantém materiais por até sete dias. Com F02.2b2 ela aciona o
dispatcher/Temporal apenas quando há consentimento e vínculo válido. Não ligar
o processo com conteúdo real antes da política de retenção dos assets e do smoke Meta.

F02.2b2 adiciona migration 0016 e a tela `/app/whatsapp`. Após backup e migração,
subir `docker compose --profile workers up -d --build` para iniciar
`object-storage`, `whatsapp-correlator`, `whatsapp-dispatcher` e o worker Temporal.
O build `media-worker` inclui ffprobe; a imagem padrão da API não inclui esse
binário. Na publicação, criar/deployar as duas imagens separadamente.
O storage local é SeaweedFS/S3 em `localhost:9000`, bucket
`meu-braco-direito-materials`, com credenciais locais do Compose. API em F5 usa
`MATERIAL_STORAGE_ENDPOINT=http://localhost:9000`; containers usam
`http://object-storage:8333`. O endpoint público para URLs assinadas deve ser
alcançável pelo navegador. Staging/produção exigem bucket privado, endpoints
HTTPS e credenciais restritas. Nunca usar as credenciais locais fora do Compose.

Além das chaves F02.1, configurar `META_PUBLIC_PHONE` com o número oficial em E.164,
`META_ACCESS_TOKEN` de usuário de sistema com permissão de mídia,
`META_GRAPH_VERSION`, `MATERIAL_STORAGE_BUCKET`,
`MATERIAL_STORAGE_ACCESS_KEY` e `MATERIAL_STORAGE_SECRET_KEY`. Reiniciar API e
workers após mudar `.env`; as variáveis com prefixo completo estão em
`.env.example`. Confirmar no app Meta que callbacks de mensagens chegam pelo
endpoint público HTTPS. Na web, dono com plano e SMS válido autoriza materiais,
gera código, envia pelo WhatsApp cadastrado e confirma; então envia ideia, foto,
áudio e vídeo. O recibo deve aparecer em `/app/whatsapp`; a URL assinada vence
em dois minutos. Sem App/WABA/HTTPS públicos ainda não é possível homologar a
integração. O teste local usa somente mensagens e arquivos sintéticos.

Não há transcrição, resposta automática, geração, publicação nem exclusão de
assets nesta fatia. Antes de dados reais, definir retenção/apagamento, monitorar
falhas dos workflows e revisar permissões do bucket. O revogamento impede novos
downloads pela API, mas uma URL assinada previamente pode durar até dois minutos.

`docker compose up -d postgres temporal mailpit`; migração separada com conexão administrativa.
O SQL de inicialização cria logins locais sem bypass e banco `meu_braco_direito_platform_test`. As roles
de acesso são concedidas sem propriedade das tabelas. Se volume já existe, initializer
não roda novamente; não apagar volumes para corrigir migrações de usuário.

PostgreSQL em 55432; Temporal gRPC 7233 e UI 8233, todos ligados ao loopback.
Temporal start-dev é exclusivamente desenvolvimento/CI, não topologia de produção.
Seu SQLite fica no volume nomeado `meu-braco-direito-platform_meu-braco-direito-temporal`,
preservando o histórico ao recriar o container de desenvolvimento.
Isso não representa persistência/HA de produção nem substitui Temporal Cloud.
API só sobe após migration; health live não acessa DB, ready exige exatamente o
head Alembic do código em execução. Durante deploy, migração deve preceder a
versão nova da API.

## Runtime

API: `uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --no-access-log`.
Worker: `python -m app.entrypoints.worker`. O relay legado
`python -m app.entrypoints.relay` é manual, exclusivo para recibos históricos;
não integra mais a inicialização automática `workers` ou o debug. Quando
necessário, iniciar explicitamente `docker compose up -d relay` (profile
`legacy-relay`). Novos CRUDs de negócio/kit não geram esses recibos.
API/worker usam runtime login; o relay manual tem URL específica e só acessa outbox. Owner
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

Auth própria: definir `MEU_BRACO_DIREITO_AUTH_DATABASE_URL` com login restrito distinto
(`meu_braco_direito_auth`), chave de assinatura aleatória e `MEU_BRACO_DIREITO_AUTH_ENCRYPTION_KEY`
Fernet privada. Staging/PRD exigem `PUBLIC_WEB_URL` HTTPS, SMTP com STARTTLS/autenticação
e TLS Temporal. Prefixar as variáveis de aplicação com `MEU_BRACO_DIREITO_`.
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
