# F02 — WhatsApp e biblioteca de materiais

Status: Em implementação; F02.1 entregue localmente em 21/10/2026; F02.2a entregue localmente em 22/10/2026.
Dependências: F00, F01.

## Objetivo

Receber texto, áudio, fotos e vídeo no número oficial da plataforma e montar solicitações com fatos rastreáveis.

## Features e contratos

- Handshake/assinatura Meta, inbox, subeventos, recibos e deduplicação por adapter.
- Download autorizado, inspeção de mídia, biblioteca S3 privada e agrupamento de mensagens.
- Extrair áudio, transcrever e identificar ambiguidades de preço/data; perguntar o necessário.
- Anexos são dados não confiáveis; limites, SSRF e sandbox de mídia implementados.
- Capturar de modo opcional tom, produtos/serviços, ofertas, restrições e frequência
  informados pelo dono, com ator, mensagem-fonte, data e consentimento. Guardar como
  propostas de contexto; transcrição ou inferência ambígua pede confirmação e não
  valida preço, horário ou promoção. Não aumentar o formulário obrigatório da F01.

## Critérios de aceite e testes

- Webhook duplicado/parcial/reordenado, callback antes da correlação, arquivo inválido e expiração de URL.
- Agrupamento concorrente e contexto de duas empresas sem mistura.
- Mensagem bruta e instrução embutida não alteram preferências/fatos confirmados sem
  identidade, confirmação e operação idempotente.
- Smoke com WhatsApp oficial e material consentido.

## Limites e decisões pendentes

- App/WABA, número e templates precisam de configuração e validação.
- A caixa de entrada do produto não equivale às conversas de vendas do cliente.

## F02.1 — Webhook autenticado e inbox isolada (entregue localmente)

`GET /api/v1/webhooks/whatsapp` devolve o desafio apenas com modo `subscribe` e
verify token correto. `POST` limita o corpo a 256 KiB durante a leitura, valida
`X-Hub-Signature-256` sobre os bytes originais com o App Secret, exige envelope
WhatsApp e filtra WABA/phone number ID configurados. Separa mensagens recebidas e
transições de status; chave estável por subevento deduplica reentregas concorrentes.
Só retorna 200 depois do commit. Eventos ficam cifrados com chave exclusiva em
`whatsapp_inbox`, com RLS/role `local_spark_meta` e login isolado. Runtime normal
não possui leitura. Eventos não reconhecidos são ignorados sem criar negócio ou
tratar texto externo como comando. Registros vencem em sete dias; ingressão nova
remove os vencidos, e limpeza periódica fica para F02.2. Configuração desabilitada
responde 503, sem simular uma conexão Meta.

F02.1 não criou vínculo de remetente WhatsApp ao tenant: o SMS de F01 comprova
posse do número cadastrado, mas não autoriza associar qualquer mensagem recebida
na caixa central a esse negócio. Portanto os eventos permanecem em quarentena e
**não** iniciam Temporal, download, transcrição, resposta nem publicação. F02.2a
implementa prova de vínculo; resolução segura de tenant/negócio, retenção
periódica, material no S3 privado e outbox/workflow continuam pendentes. Status
de mensagens de saída sem correlação também aguarda. Smoke real exige Meta.

Aceite local: desafio válido/inválido, assinatura ausente/incorreta, payload parcial,
subeventos ignorados, reentrega concorrente, criptografia, separação de roles,
readiness e rollback/upgrade de migration 0013 no banco `_test`. 271 testes,
100% de linhas/ramos, Ruff e mypy aprovados. Nenhum evento real da Meta foi testado.

## F02.2a — Prova de vínculo do canal (entregue localmente)

O proprietário autenticado inicia pelo `POST /api/v1/organizations/{tenant_id}/businesses/{business_id}/whatsapp-link`.
Exige telefone do negócio verificado por F01, acesso ativo por assinatura ou
patrocínio e configuração Meta `cloud`. O serviço retorna uma mensagem
`VINCULAR <código>` para envio pelo número verificado ao número da plataforma.
O código aleatório de uso único vence em 15 minutos, apenas seu SHA-256 fica no
banco e um novo pedido espera 60 segundos. `POST .../confirm` busca a mensagem
na inbox cifrada e assinada, do mesmo remetente e posterior à emissão do código;
uma transação marca o desafio como usado, cria o vínculo e audita. `GET` informa
`enabled`, `pending` e `linked`. Repetir confirmação já concluída é idempotente.
Um índice HMAC permite localizar a mensagem sem número em claro na inbox.
O HMAC usa a chave de criptografia da inbox; rotação dessa chave requer plano
conjunto de recifragem/reindexação antes de trocar a configuração.
Alterar o telefone do perfil cancela o desafio e desativa o vínculo na mesma
transação, com auditoria do proprietário que revogou o canal. Índice único impede
um remetente ativo em dois negócios. Operadores,
outros tenants e contas sem plano não iniciam vínculo. Mensagens continuam em
quarentena até a próxima fatia de resolução e processamento; esse endpoint não
responde via WhatsApp. A interface para executar o vínculo ainda precisa ser feita.
Sem credenciais Meta reais, a prova foi exercitada apenas por webhooks sintéticos
assinados no banco `_test`; não afirmar conexão com a Meta em produção.

Próxima fatia F02.2b: resolver remetente para tenant/negócio ativo com papel
restrito, associar eventos com identidade durável e outbox, agendar limpeza da
retenção, baixar e validar mídia na biblioteca privada, iniciar workflow de
extração/transcrição. O vínculo por si só não aciona IA ou publicação.

O CI declara URL Meta no PostgreSQL de teste na porta 5432 e cria o login
`local_spark_ingest` com o papel restrito `local_spark_meta`. O exemplo local usa
55432. Todos os endpoints de teste devem apontar para o mesmo banco `_test`;
sob `CI`, pytest falha cedo se faltar uma URL explícita.

## Integração e manutenção


Dividir as features acima em mudanças revisáveis. Cada mudança atualiza este SDD,
`docs/PROJECT.md` e `docs/CHANGELOG.md`, incluindo evidências de testes e pendências.
Contratos que afetam outras fases devem ser refletidos no SDD geral e nos consumidores.
Não marcar como concluído por possuir mocks ou documentação de uma API ainda não validada.

## Integração com onboarding e interfaces

A identidade é iniciada na web; a posse do WhatsApp é verificada nesta fase, antes
de associar mensagens à contratação/organização. Telefone digitado no checkout ou
perfil não é verificação. Onboarding conversacional complementa o perfil inicial,
sem exigir uso diário do painel. Consentimentos são específicos por finalidade.
