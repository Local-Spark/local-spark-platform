# Operação e deploy

Revisado em **28/10/2026** para refletir o código local. Decisões de produto em
[DECISIONS](DECISIONS.md), contratos no [SDD](SDD.md) e estado em
[PROJECT](PROJECT.md). O [texto anterior](history/2026-10-28-pre-documentation-reconciliation/operations.md)
foi preservado; a cronologia de migrations não substitui este procedimento.
Não houve operação em serviços, dados, credenciais ou infraestrutura nesta revisão.

## Ambiente local

Configuração e comandos básicos estão no [README](../README.md). PostgreSQL em
55432, Temporal gRPC 7233/UI 8233, Mailpit HTTP 8025/SMTP 11025 e storage S3 do
perfil `workers` em 9000, ligados ao loopback. Temporal start-dev é apenas local;
seu volume conserva histórico de desenvolvimento, sem comprovar HA/backup de produção.

Inicialização PostgreSQL de instalação nova cria logins restritos e o banco
`meu_braco_direito_platform_test`. Em volume existente, initializer não roda de
novo; não apagar volume para corrigir a instalação. Scripts específicos de
logins Meta/correlator existem em `scripts/ensure_local_*_login.sql`; avaliar
necessidade antes de executá-los no ambiente correto.

API requer o **head Alembic exato**, não apenas a migration que criou uma rota.
`/health/live` não consulta banco; `/health/ready` verifica schema e conexões
habilitadas. Código da 0058 entende `expires_at=NULL` nos materiais; versões
anteriores podem limpar dados ou falhar ao ler esses valores.

## Contratação e acesso

Antes de criar checkout, o owner verificado registra o aceite único por negócio
em Plano e acesso. A API valida versão/hash e ação explícita. O contrato não
configura credencial, orçamento, pagamento ou publicação e não reativa linhas
antigas de consentimento. Não há checklist operacional por fornecedor para o
cliente. A flag `SERVICE_AGREEMENT_REQUIRED` permite compatibilidade local de
migração; produção exige enforcement. A web e a criação de checkout já exigem o
aceite atual mesmo quando a flag local está desligada.

`billing` usa login de pagamentos separado. `BILLING_MODE=disabled` não consome
jobs de provedor nem chama Stripe. Configuração sandbox/live em
[cobrança](design/billing.md). Em sandbox local, o listener é:

```bash
stripe listen --all-snapshot --forward-to http://localhost:8000/api/v1/webhooks/stripe
```

A Stripe pode concluir com listener fechado. Redirect não ativa acesso; billing
reconcilia estado canônico de sessões/assinaturas/faturas. Checkouts abertos são
consultados em ciclo de 30 s, até 25 por ciclo, com dedupe por janela de cinco
minutos. Não repetir compra ou criar nova chave para resolver resultado ambíguo.
Jobs com falha permanecem duráveis até revisão. A migração 0038 já retirou a
outbox financeira sem consumidor, preservando `billing_audit`; `billing_jobs`
permanece. Não redirecionar esses eventos para recibos genéricos de CRUD.

Patrocínio é concessão distinta de receita, com início/fim e revogação próprios.
O comportamento aprovado para plano vencido durante criação (C08) ainda precisa
ser integrado: hoje há revalidações de plano na conclusão e leitura. Não afirmar
que o runtime já conserva o acesso de revisão após vencimento.

## Identidade, convites e telefone

Auth nativa exige segredo de assinatura e chave Fernet privada fora do ambiente
local. Access token permanece em memória na web; refresh HttpOnly e CSRF seguem
cookies host-only. HTTPS usa prefixo `__Host-`, Secure, path `/`, SameSite=Lax.
Web e `/api` devem compartilhar origem; proxy preserva Origin/Cookie/Set-Cookie/
Authorization e não armazena respostas autenticadas em cache.

`auth-mail` entrega confirmação, recuperação e convites via SMTP. Convites de
staff expiram em 48 h; aceite usa a conta com o mesmo e-mail verificado, seguido
de novo login/MFA. Conta convidada sem negócio não passa pelo onboarding
comercial. Revogação encerra acesso/sessões; novo convite pendente tem prioridade
na orientação de recuperação. Diagnóstico usa estado da outbox, sem copiar tokens,
links, ciphertext ou seed de MFA para logs/tickets.

Telefone usa Twilio Verify quando configurado; padrão `disabled`. Serviço/SID e
API key/secret ficam no backend. SMS é o canal padrão; WhatsApp só se habilitado
no provedor. Código: 10 min, cooldown 60 s e até cinco tentativas. A tela mostra
E.164; corrigir telefone invalida código e verificação anteriores e desativa o
vínculo até nova prova. SMS confirmado não equivale a vínculo WhatsApp.

Rotação da chave JWT invalida access tokens antigos; refresh válido pode emitir
novos. Rotação Fernet exige recriptografia e validação dos dados que a usam.
Reset de senha não remove MFA. MFA perdido usa recuperação individual ou suporte
com comprovação e auditoria; não há bypass público.

## WhatsApp, processamento e armazenamento

Configurar no backend, sob prefixo `MEU_BRACO_DIREITO_`: modo Meta `cloud`,
`META_DATABASE_URL`, App/WABA/número, verify token, app secret, Graph token/versão,
`META_ENCRYPTION_KEY`, número público oficial e storage privado. Segredos ficam
fora de git/imagens/logs. Callback HTTPS é validado por assinatura; não expor
endpoint sem essa proteção. A API de webhook usa login de ingestão isolado.

Callbacks são cifrados/deduplicados na inbox e recebem 200 após commit. Falha de
persistência permite retry do provedor. Correlator associa origem ao negócio;
nenhum worker deve inventar associação histórica após troca de número. Um envio
já associado conserva o negócio e continua processando, mesmo durante troca ou
indisponibilidade do vínculo. Entrega simulada espera o vínculo novo verificado.

O owner precisa de acesso, aceite do serviço, telefone verificado e prova de
vínculo. Na web, gerar código/mensagem, enviar pelo número cadastrado ao oficial
e confirmar quando a API reconhecer a prova. Desconectar encerra o canal, não o
contrato de IA nem o histórico. Meta real/candidata/publicação seguem sem
homologação; não habilitar envios reais apenas para testar uma tela.

`whatsapp-correlator` e `whatsapp-dispatcher` usam logins/roles restritos, Temporal
e a mesma chave pertinente à origem. O perfil `workers` sobe também storage e
worker de mídia. A imagem `media-worker` contém ffprobe/FFmpeg; a API não precisa
dos binários. API e worker têm imagens/deploys separados.

Storage local: SeaweedFS/S3, bucket `meu-braco-direito-materials`. F5 usa endpoint
`http://localhost:9000`; containers usam `http://object-storage:8333`. URL assinada
deve ser alcançável pelo navegador e tem validade curta, normalmente até dois
minutos. Staging/produção exigem bucket privado, HTTPS e credenciais mínimas.
Permissão sobre o arquivo e expiração da URL são verificações distintas.

### Retenção vigente e mudanças ainda pendentes

- Materiais WhatsApp associados e eventos correspondentes são preservados sem
  expiração automática pela 0058; não há exclusão pelo histórico/API. A inbox
  preserva mensagens associadas para deduplicação. Status técnicos, registros
  não atribuídos e uploads órfãos continuam com limpeza própria.
- Acervo de fotos permite remoção de imagens desatualizadas, com retry e
  reconciliação próprios; uma cópia do WhatsApp é independente da origem.
- Prévias devem ser preservadas sem TTL com conta ativa (C09), mas o código
  ainda usa `expires_at`, propostas e limpeza. Adaptar leitura, proveniência e
  retenção como um conjunto; não desativar jobs ou editar prazos manualmente
  como se isso entregasse o contrato.
- Ao encerrar conta, prazo de exclusão fica pendente da fase específica (P03).
  O proprietário decidiu não implementar essa exclusão automática nesta etapa.
- Quarentena de upload incerto não equivale a exclusão física comprovada.
  Recuperação exclusiva de staff para autor sem acesso foi aprovada (C10), mas
  o fluxo restrito/auditado ainda não existe. Não assumir a identidade do autor
  nem conceder leitura irrestrita aos operadores para contornar a pendência.

## IA e falhas externas

Texto, transcrição, interpretação e imagem usam o mesmo aceite contratual;
adapters, modos, chaves e tetos são configuração interna por capacidade.
Padrões são desligados e limites zero; configuração por si só não homologa uma
capacidade. Jev é opcional no worker de desenvolvimento/teste. A prévia visual
do produto é `visual_fake`; workflow/orquestrador real permanecem desconectados.

Não repetir efeito pago após timeout, perda de lease ou confirmação perdida.
Registrar operação, fence, estado conhecido/incerto e reserva; reconciliação
precisa provar o que ocorreu. Rede, storage e render ficam fora de row locks;
workflows determinísticos não fazem IO. A futura coordenação BL04.2 usará o
contrato atual e C08/C09/C10, sem reintroduzir permissões por fornecedor.

## Runtime e credenciais por capacidade

| Processo/contexto | Login local de exemplo | Role de acesso |
| --- | --- | --- |
| API/domínio e sessões de owner no worker | `meu_braco_direito_runtime` | `meu_braco_direito_app` |
| Identidade e SMTP | `meu_braco_direito_identity` | `meu_braco_direito_auth` |
| Billing | `meu_braco_direito_payments` | `meu_braco_direito_billing` |
| Ingressão Meta | `meu_braco_direito_ingest` | `meu_braco_direito_meta` |
| Correlação/efeitos de material | `meu_braco_direito_router` | `meu_braco_direito_correlator` |
| Relay manual legado | `meu_braco_direito_delivery` | `meu_braco_direito_relay` |

Nomes/segredos de produção são próprios. Logins runtime não são donos das tabelas
nem recebem superuser/BYPASSRLS. `Database.transaction` configura tenant/ator
localmente à transação; workers usam escopo e papéis do efeito. Credencial
administrativa serve a migração/provisionamento, não a execução da aplicação.

API: `uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --no-access-log`.
Worker: `python -m app.entrypoints.worker`. Relay manual:
`python -m app.entrypoints.relay`, profile `legacy-relay`, apenas compatibilidade;
fora do startup comum. Tabelas e handlers históricos ainda não foram removidos.

## Migrações, testes e recuperação

Antes de atualizar ambiente com dados: conferir head, inventário de pendências,
claims e efeitos incertos; planejar pausa/drenagem e backup verificável. Aplicar
migração e código compatíveis em todos os processos envolvidos. Não executar
versões mistas que possam apagar materiais duráveis ou ignorar barreiras.
A 0058 recusa claims/pedidos de exclusão não resolvidos e não recupera objetos
já apagados. A 0055/quarentena também exige avaliação de efeitos legados.

Backup só de PostgreSQL não inclui objetos, estado Temporal, ACLs ou propriedade
validada. Restore deve considerar banco, mídia, execução e ledger para não
repetir gasto/publicação nem perder dados posteriores. F08 ainda precisa
comprovar recuperação coordenada em staging.

Testes usam banco dedicado terminado em `_test`, nunca o banco da aplicação,
com migrations no head e logins restritos. `TEST_*` do processo prevalece sobre
arquivos de exemplo/local de teste. Não executar suítes Python e navegador que
limpam o mesmo `_test` ao mesmo tempo. Integração indisponível falha.
Comandos no README; provas datadas no [CHANGELOG](CHANGELOG.md).

## GitHub Actions / AWS

CI e deploy manual por OIDC/ECR/ECS existem no repositório; não provisionam AWS.
Staging precede piloto. Environments, IAM mínimos, secrets, SMTP TLS, HTTPS,
Temporal TLS e tarefas de migração próprias ainda precisam de configuração e
homologação. Não usar credenciais locais ou `.env.example` em produção.

Deploy exige SHA de CI aprovado e recursos existentes. Migração não é executada
com login runtime. Estratégia de workers ativos, expansão/contração de schema,
backup/restore, alertas e observabilidade fazem parte da F08. Logs usam eventos
estáveis e campos permitidos; conteúdo privado, prompts e credenciais não vão
para stdout, imagens ou relatórios.
