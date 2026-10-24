# F02 — WhatsApp e biblioteca de materiais

## Assistente editorial conversacional: simulação local (primeira fatia entregue)

A migration 0026 e os endpoints autenticados `POST /api/v1/organizations/{tenant_id}/businesses/{business_id}/editorial-conversation/simulate` e `POST /api/v1/organizations/{tenant_id}/businesses/{business_id}/editorial-conversation/{decision_id}/decide` permitem ensaiar a conversa pelo Swagger em `development`/`testing`. Apenas o proprietário do negócio pode chamar os endpoints. O simulador reconhece duas frases claras de preço ou horário livre **hoje**, fixa a data pelo fuso do negócio e devolve uma pergunta curta de confirmação. Texto fora dos padrões fica em `needs_review`, sem fato confirmado. Confirmar acrescenta um fato temporário ao contexto editorial versionado na mesma transação; descartar não o acrescenta. `operation_id` é idempotente por tenant/negócio; reutilizá-lo com outro texto gera conflito. A decisão registra intenção, proposta estruturada, hash do texto e auditoria, sem persistir a mensagem integral nessa tabela.

O simulador usa regras determinísticas, sem LLM/Jev, envio de WhatsApp ou publicação. A fatia seguinte conecta a inbox real ao estado de decisão. Respostas por outbox, extração estruturada de texto livre, janela e opt-out Meta ficam em recorte posterior. O smoke externo depende do desbloqueio da WABA; testes no Swagger não exigem conta, chave ou despesa nova.

Validação: `make ci` com 450 testes e 100% de linhas/ramos; migration 0026 aplicada no banco local após backup e testada por downgrade/upgrade no banco `_test`.

## F02.2c4 — Decisões a partir da inbox vinculada (entregue localmente)

O worker de materiais agora registra uma decisão para cada mensagem de texto elegível na mesma transação em que salva o material e marca o evento como processado. Usa o ID do evento como `operation_id`, o proprietário vinculado como ator e o horário da mensagem no fuso do negócio para determinar a data de validade. Reentregas não criam outra decisão nem outra auditoria. A API do proprietário lista decisões por negócio (`GET /editorial-conversation`) e aceita confirmação/descarte (`POST /{decision_id}/decide`) em qualquer ambiente; o endpoint de simulação continua restrito a development/testing. A confirmação versiona o contexto, sem publicar.

A entrada de webhook e a correlação existentes são aproveitadas, mas **não há envio de resposta ao WhatsApp**. A resposta textual fica na decisão para revisão pela API. Esta fatia também não interpreta imagens ou áudio, não usa LLM/Jev e não transforma comandos “Confirmar” recebidos pelo WhatsApp em aceite; essas capacidades, o outbox de envio, opt-out e a homologação Meta ficam no próximo recorte. Migration 0027 concede ao papel restrito do correlator somente inserção de decisões e leitura das colunas de identidade necessárias à idempotência. O serviço exige vínculo, consentimento e plano antes de processar o evento.

Validação: `make ci` com 450 testes e 100% de linhas/ramos; migration 0027 aplicada no banco local após backup e revertida/reaplicada no `_test`.

## F02.2c5 — Respostas editoriais e comandos vinculados (entregue localmente)

Migration 0028 adiciona uma fila de respostas por decisão: destinatário cifrado, ID do evento de origem, prazo conservador de até 23 horas e limitado ao fim do dia da oferta, estado e ID retornado pela Meta. O worker cria a resposta na mesma transação em que conclui o texto. O dispatcher usa a Cloud API oficial `/{phone_number_id}/messages` somente quando `MEU_BRACO_DIREITO_META_REPLY_ENABLED=true`, token, versão e número estão configurados; a chave vem **desativada** por padrão. Antes de enviar, revalida vínculo ativo, consentimento, proprietário, telefone verificado e plano. Respostas vencidas não saem; itens concluídos têm dados do destinatário apagados após 30 dias.

Uma tentativa é gravada como `submitting` antes da chamada. `200` com ID vira `accepted` (aceitação da API, **não** entrega no aparelho); HTTP 4xx explícito vira `failed`; 5xx, resposta malformada, queda de rede ou interrupção do processo viram `uncertain`. Estado incerto não é reenviado automaticamente, porque a Cloud API não fornece neste contrato uma chave de idempotência de envio. Mensagens exatamente como `Confirmar` ou `Descartar` atuam quando respondem ao ID de uma pergunta `accepted` do mesmo remetente e negócio; sem citação, só quando existe exatamente uma pergunta pendente aceita nos últimos 30 minutos. Havendo ambiguidade, nenhum fato é confirmado. A confirmação usa a transação idempotente do contexto editorial.

Ainda faltam recibos de entrega/falha do webhook, interface de reconciliação para estado incerto, resposta de confirmação ao proprietário, teste externo após desbloqueio da WABA e orçamento específico para mensagens pagas. Até essas verificações, a chave de envio permanece desligada em local e produção. Nenhuma mensagem real foi enviada nesta entrega.

Validação: `make ci` com 452 testes e 100% de linhas/ramos; migration 0028 aplicada no banco local após backup e testada por downgrade/upgrade no `_test`. Worker e dispatcher reconstruídos com a chave de envio desligada.

## F02.2c6 — Recibos, limite e revisão operacional (entregue localmente)

Migration 0029 registra separadamente o estado da chamada e o resultado de entrega de cada pergunta e confirmação. O correlator lê apenas recibos assinados que já foram persistidos e cifrados na inbox. Faz a correspondência pelo ID de mensagem devolvido pela Meta, deduplica por evento, aceita avanço `sent → failed/delivered → read` e ignora regressões tardias. Um recibo que chega antes do commit do ID fica em quarentena por até dois minutos; sem correspondência depois disso é descartado, sem associar a outro cliente. Só códigos numéricos de erro entram no diagnóstico, nunca texto do WhatsApp ou telefone. O aceite HTTP continua distinto da entrega.

Ao confirmar ou descartar uma proposta, o backend prepara na mesma transação uma resposta curta ao proprietário, apenas se a pergunta original foi aceita e ainda está na janela conservadora. Ela usa o mesmo destinatário cifrado, vínculo/consentimento/plano revalidados, tentativas duráveis e o mesmo tratamento de resultado incerto. Não há repetição automática de envio incerto. A fila considera as duas mensagens no teto de tentativas por organização e dia UTC (`MEU_BRACO_DIREITO_META_DAILY_MESSAGE_LIMIT`); o bloqueio transacional por organização impede duas instâncias de excederem o limite. Sem teto positivo, a chave de envio não pode ser ativada. Esse teto limita tentativas, não é uma estimativa de reais cobrados pela Meta.

`GET /api/v1/admin/whatsapp-replies` lista somente metadados de envios com falha/incerteza ou sem comprovante de entrega após 15 minutos; `POST /api/v1/admin/whatsapp-replies/{id}/review` permite marcar `investigating` ou `closed_no_retry`. O backend exige staff com MFA, usa projeção SQL restrita e audita leitura/revisão e tentativas de envio sem duplicar ações. A revisão não altera o estado de entrega e não dispara retry. A web mostra esses casos em **Administração → Envios WhatsApp**. Sem acesso à WABA liberada, o percurso foi validado com respostas HTTP e webhooks sintéticos assinados; nenhum envio real foi ativado.

Permanecem: smoke externo em baixo volume após verificação da empresa na Meta, custos monetários de mensagens por categoria/tarifa versionada, tratamento explícito de opt-out e classificação de texto livre com avaliação semântica. Até o smoke, `MEU_BRACO_DIREITO_META_REPLY_ENABLED=false`.

Validação: `make ci` com 455 testes e 100% de linhas/ramos; migration 0029 revertida/reaplicada no `_test` e aplicada na base local após backup em `.local/backups/`. Frontend: 179 testes, cobertura integral, build e smoke Chromium de 390 px.

O WhatsApp é a conversa com o proprietário verificado sobre materiais e peças
do **próprio negócio**; não é atendimento aos consumidores dele nem um chat geral.
Cada entrada gera no máximo uma ação editorial: guardar material, propor fato
temporário, responder pergunta sobre o fluxo, pedir uma informação indispensável,
mostrar rascunho para revisão ou encaminhar à equipe. Mensagens de um mesmo envio
são agrupadas antes da resposta; confirmação de recebimento é uma só por grupo,
idempotente, e pode ser omitida quando uma pergunta específica já responde ao dono.

Exemplos de contrato:

- “Hoje tenho agenda livre às 15h” → detectar disponibilidade, fixar a data pelo
  fuso do negócio e perguntar uma vez: “Quer divulgar um horário livre hoje às
  15h? Responda Confirmar, Ajustar ou Só guardar.” A confirmação cria um fato
  temporário com expiração no fim do dia; não agenda cliente nem publica sozinha.
- “Hoje o X-tudo está 20 reais” → propor preço R$ 20,00 para o produto identificado
  e perguntar se vale apenas hoje e se pode ser divulgado. Se produto, moeda,
  vigência ou contexto estiverem ambíguos, perguntar só o dado que falta. Sem
  confirmação, guardar como material/hypótese; não atualizar preço confirmado.
- Foto/vídeo sem legenda → acusar recebimento uma vez e, quando necessário,
  perguntar “O que você quer destacar nessa imagem?”; não afirmar o que há nela
  antes de uma capacidade visual avaliada. Perguntas sobre o serviço (“o que você
  pode postar hoje?”) usam contexto e estado autorizados, sem conversa aberta.

Pipeline planejada: webhook autenticado → correlação de owner/tenant e grupo →
transcrição opcional → classificação de intenção + extração estruturada com
evidência do trecho → validação determinística (datas, fuso, preço, produto,
consentimento, plano, expiração) → estado `awaiting_confirmation` ou
`material_saved` → resposta curta por template → confirmação explícita → nova
versão do contexto ou pedido de ideia → revisão da peça → publicação só após
aprovação própria. Entrada incerta, fora de escopo ou falha do modelo nunca vira
fato confirmado; resposta segura ou revisão humana. Processar eventos por
ID/conversa com idempotência, ordem e outbox de envio; não repetir mensagem ao
reentregar webhook. Respeitar janela/regras de mensagens da Meta e opt-out.

Primeiro corte: regras para comandos claros e LLM de saída estruturada para
extrair intenção e campos de texto livre. Jev pode ser avaliado em shadow para
decisões fechadas (`material`, `oferta`, `disponibilidade`, `pergunta`, `fora de
escopo`; `responder`, `perguntar`, `guardar`, `revisar`), com limiar de confiança
e fallback. Jev não gera texto nem extrai preço arbitrário; não escolhê-lo como
motor único de conversa antes de eval PT-BR, custo/latência e termos de dados.
Modelo de conversa e limiares permanecem decisões da fase de avaliação. O simulador
devolve uma resposta na API, mas ainda não envia respostas pelo WhatsApp.

Status: Em implementação; F02.1–F02.2c6 entregues localmente, envio real desativado
e smoke Meta pendente por restrição da WABA. As seções abaixo registram o estado
de cada fatia quando foi entregue; pendências históricas podem ter sido resolvidas
por fatias posteriores.
Dependências: F00, F01.

## Objetivo

Receber texto, áudio, fotos e vídeo no número oficial da plataforma e montar solicitações com fatos rastreáveis.

## F02.2c3a — Agrupamento determinístico (entregue localmente)

O correlator atribui `group_id` ao copiar uma mensagem da inbox para a fila. A
identidade usa tenant, negócio, remetente autenticado e uma janela **fixa** de
dez minutos em UTC, calculada a partir do horário recebido pela Meta. Dois
workers concorrentes ou reentregas produzem o mesmo grupo sem consultar ou
travar um grupo mutável. Uma mensagem na virada da janela inicia outro grupo;
este limite é visível na biblioteca e pode ser ajustado em versão futura, com
migração explícita de regra. A migration 0019 preserva materiais antigos como
grupos unitários e grava o grupo no asset antes de a fila vencer. A API só
devolve o identificador ao proprietário autorizado; a web reúne recibos do
mesmo envio e mantém exclusão individual. Não há interpretação de conteúdo.

## F02.2c3b — Transcrição de áudio controlada (entregue localmente)

Converter áudio validado para formato aceito pelo provedor, limitar
duração, reservar franquia/segundos por tenant em ledger antes de cada chamada
paga, chamar `gpt-transcribe` por adapter no worker Temporal e guardar texto
cifrado com estado auditável. Uma tentativa de resultado incerto não será
submetida automaticamente de novo; revogação, retenção e exclusão também devem
abranger a transcrição. Credencial e teto de gasto são obrigatórios para ativar.
Transcrição converte fala em texto; extração de intenção, fatos, promoções e
respostas com LLM/Jev pertencem a uma etapa posterior com confirmação do dono.

Implementação: migration 0020 grava transcript cifrado no asset e ledger de
segundos reservados por evento. A unidade de orçamento é tenant/dia UTC; a
reserva usa advisory lock transacional por tenant e não é devolvida em resultado
incerto. Áudio acima de 180 s é rejeitado antes da reserva. O worker normaliza
com FFmpeg para WAV mono 16 kHz, com protocolos `file,pipe` apenas; a chamada ao
provedor ocorre fora da transação com ID estável do evento. Estados expostos:
`submitted`, `completed`, `uncertain`, `rejected`, `budget_exceeded`. Queda após
submissão não aciona retry pago; o dispatcher marca reservas `submitted` com
mais de cinco minutos como `uncertain`. Exclusão do asset apaga o transcript; o
ledger mantém apenas IDs, segundos e estado para custos e auditoria. Sem chave
OpenAI e teto diário configurados, a transcrição fica desativada. Credenciais,
limites, smoke real e orçamento comercial devem ser aprovados antes de ativar.
O dono deve autorizar separadamente o envio do áudio à OpenAI no endpoint
`/whatsapp-materials/audio-consent`; aceite anterior dos materiais não basta.
Revogar o consentimento geral também remove esta autorização. A activity
revalida antes e após a chamada; falhas transitórias anteriores à reserva podem
ser repetidas, mas a submissão paga não é refeita.

## Features e contratos

- Handshake/assinatura Meta, inbox, subeventos, recibos e deduplicação por adapter.
- Download autorizado, inspeção de mídia, biblioteca S3 privada e agrupamento de mensagens.
- Extrair áudio, transcrever e identificar ambiguidades de preço/data; perguntar o necessário.
- Anexos são dados não confiáveis; impor limites, proteção SSRF e inspeção em
  worker de mídia. Endurecer o sandbox do contêiner antes de conteúdo real.
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
`whatsapp_inbox`, com RLS/role `meu_braco_direito_meta` e login isolado. Runtime normal
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

### F02.2b1 — Correlação durável de mensagens (entregue localmente)

Um processo separado, com login `meu_braco_direito_router` e papel
`meu_braco_direito_correlator`, lê apenas a inbox cifrada, os vínculos ativos e
sua própria fila de materiais. Mensagens recebidas **depois** do vínculo são
associadas ao tenant/negócio por índice cego do remetente. `FOR UPDATE SKIP LOCKED`
divide lotes entre instâncias; a transação copia o ciphertext para
`whatsapp_material_events`, muda o estado da inbox e grava auditoria com o ID do
evento. A chave única do evento impede duplicação. A fila mantém o payload cifrado
até o prazo original de sete dias e o processo remove cópias vencidas. Comandos
de vínculo e formatos não suportados são descartados; mensagens anteriores ao
vínculo, sem remetente reconhecido ou de vínculos revogados permanecem em
quarentena até expirar. O papel da API e o papel de ingestão não leem a nova fila.

A fila está pendente para consumo posterior; esta fatia **não** inicia IA, Temporal,
download de mídia, resposta ao usuário ou publicação. F02.2b2 deve validar plano,
consentimento e vínculo novamente antes de qualquer efeito externo; fará download
seguro, inspeção e biblioteca S3 privada, com relay/workflow e expiração explícita.
Não operar esse processo com conteúdo real antes da próxima fatia e do smoke Meta.
Aceite local: duas organizações isoladas, concorrência de dois correlators,
reentrega sem duplicar, comando/formatos descartados, fila cifrada inacessível
pelos papéis da API e ingestão, limpeza de item vencido. Migration 0015 validada
com upgrade/downgrade/reaplicação em PostgreSQL temporário `_test`, inclusive
após `0015_product_brand` na cadeia de renomeação. A suíte local
passou com 289 testes e 100% de linhas/ramos, Ruff, mypy e Compose válidos.
Nenhum evento Meta real foi usado.

O CI declara URL Meta no PostgreSQL de teste na porta 5432 e cria o login
`meu_braco_direito_ingest` com o papel restrito `meu_braco_direito_meta`. O exemplo local usa
55432. Todos os endpoints de teste devem apontar para o mesmo banco `_test`;
sob `CI`, pytest falha cedo se faltar uma URL explícita.

### F02.2b2 — Consumo e biblioteca privada (entregue localmente)

O proprietário autoriza separadamente o recebimento de materiais na nova tela
`/app/whatsapp`; revogar o consentimento desativa o vínculo imediatamente. A
conexão exige telefone confirmado, acesso comercial ativo e envio da mensagem
`VINCULAR <código>` pelo mesmo número para o WhatsApp oficial. A tela mostra o
estado verdadeiro da conexão e uma biblioteca de ideias e arquivos recebidos.

O dispatcher reivindica itens da fila cifrada com `SKIP LOCKED`, lease de 60 s,
contador de tentativas e fencing token. Inicia um workflow Temporal com ID
determinístico por mensagem; duplicação de start é aceita como replay. Uma
activity revalida proprietário, vínculo, remetente, telefone confirmado,
consentimento prévio e assinatura/patrocínio ativo antes do download e antes do
commit. Falhas transitórias recebem retry do Temporal; as definitivas deixam
recibo de erro e auditoria. Reentregas não duplicam o asset.

Texto é cifrado na biblioteca. Foto, áudio e vídeo são buscados na Graph API com
Bearer token da plataforma, sem redirects, URL Meta permitida, limite de bytes,
MIME/sha256 e inspeção por Pillow ou ffprobe. O original vai para bucket S3
privado por tenant/negócio/evento, com checksum; o dono acessa somente via URL
assinada de dois minutos, após autorização RLS. O ambiente local usa SeaweedFS
4.39, compatível com S3; staging/produção deverão usar bucket e credenciais
dedicadas, com endpoint HTTPS. Respostas Meta reais podem exigir ajuste da lista
de hosts permitidos após o smoke oficial.

O webhook/vínculo ficam inativos sem modo Meta `cloud`; dispatcher e activity de
mídia ficam inativos sem login de correlação ou chave de criptografia. Sem token
Graph, o download de mídia falha com recibo explícito. Ainda **não** há resposta
automática no WhatsApp, transcrição,
extração de fala, agrupamento de mensagens, confirmação de fatos ambíguos,
geração nem publicação. Essas partes formam F02.2c/F03 e dependem de orçamento,
reconciliação de uploads órfãos e consentimentos separados. A fila cifrada
vence em sete dias; F02.2c1 define retenção e exclusão dos assets, mas o fluxo
de mídia real permanece bloqueado até resolver os demais pontos. URLs já assinadas podem continuar
válidas por até dois minutos após a revogação.

Aceite local: migração 0016 com rollback/reaplicação no banco `_test`, testes de
consentimento, isolamento, rechecagem de plano, retries, URLs e mídia malformada,
S3 local com arquivo sintético. Smoke Meta e staging seguem pendentes: o
App/WABA sandbox foi provisionado em 22/10, mas o primeiro envio retornou
`failed`/`131031` (`Business Account locked`). O callback público temporário
passou no desafio e em POST sintético assinado; nenhum evento Meta real foi
gravado na inbox. A Qualidade da Conta da Meta mostra restrição permanente da
WABA de teste e solicita verificação da empresa antes de iniciar/responder
conversas ou adicionar números. Concluir a verificação e confirmar a remoção da
restrição; então checar a inscrição do app na WABA, além do campo `messages`,
antes de repetir o teste. O staging não foi criado.

## Integração e manutenção

### F02.2c1 — Retenção e exclusão da biblioteca (entregue localmente)

Materiais preparados vencem 30 dias após a criação do asset; os existentes recebem
prazo a partir de sua data original. A inbox e a fila cifrada continuam com prazo
de sete dias e agora têm limpeza periódica independente de novos webhooks. O dono
pode pedir a exclusão antecipada de um material preparado por `DELETE
/api/v1/organizations/{tenant_id}/businesses/{business_id}/whatsapp-materials/{event_id}`.
A operação registra auditoria em transação, é idempotente enquanto a linha existe,
oculta o recibo imediatamente e bloqueia novos links. O worker reivindica lotes
limitados de itens vencidos ou pedidos com lease e fencing, remove o objeto S3 fora da transação e só
depois apaga asset, evento e inbox, com auditoria. Falha de storage mantém o registro
para retry. Link assinado antes da exclusão pode funcionar até seu vencimento de
dois minutos; isso deve ser explicado ao usuário. A web apresenta prazo e ação de
exclusão com confirmação. Migração 0017 aplica RLS e privilégios restritos.

Este recorte cobre assets finalizados. A F02.2c2 abaixo trata objetos órfãos caso
o upload termine, mas o commit de processamento não ocorra. Ainda não usar mídia
real antes do smoke Meta e staging. Agrupamento de
mensagens, transcrição, resposta, confirmação de fatos e preferência contextual
permanecem F02.2c3+. O prazo de 30 dias é decisão inicial de produto e deve ser
reavaliado antes do piloto com clientes reais.

Validação local: migração 0017 revertida e reaplicada no banco `_test` e aplicada
na base local após backup; 367 testes backend com 100% de linhas/ramos, Ruff e
mypy aprovados. A web passou 149 testes/100% e uma jornada Chromium de exclusão.
Um objeto sintético foi gravado e removido no SeaweedFS; o dispatcher atualizado
subiu no Compose. Nenhum conteúdo real ou evento Meta foi usado.

### F02.2c2 — Reconciliação de uploads interrompidos (entregue localmente)

Cada tentativa de mídia usa uma chave S3 exclusiva e grava antes do `put` uma
intenção durável `whatsapp_upload_intents`, com tenant, negócio, evento e auditoria.
O download da Meta e a inspeção ocorrem antes da intenção; falha nessa etapa não
cria objeto. O commit que finaliza o asset remove a intenção na mesma transação.
Se o upload falhar, a autorização mudar, o processo cair ou o commit falhar, a
intenção permanece para reconciliação, sem expor o arquivo ao cliente.

O dispatcher reivindica intenções com mais de 20 minutos em lotes limitados,
lease de 60 segundos e fencing; apaga o objeto fora da transação, confirma a
remoção da intenção e audita. Falhas de storage preservam a intenção para retry.
Uma chave já referenciada por asset finalizado não é reivindicada. O prazo de
20 minutos excede o limite de 12 minutos do workflow e os timeouts/retries
limitados do cliente S3. A finalização trava a intenção e recusa anexar uma
tentativa já reivindicada pela limpeza, evitando referência para objeto apagado.
Chaves por tentativa evitam que retries concorrentes sobrescrevam o asset vencedor.
O papel da API não lê a tabela de intenções.

Esta fatia fecha o caminho normal de objetos órfãos causados por upload sem commit.
Homologação de mídia real ainda depende de smoke Meta após remover a restrição da
WABA e de staging. Antes da operação em escala, adicionar inventário periódico do
bucket como defesa contra anomalias externas ao banco e revisar limites por
fornecedor. Agrupamento de mensagens, transcrição de áudio com orçamento/consentimento,
resposta e confirmação de fatos formam F02.2c3. Não tratar o recibo como conteúdo
pronto para publicar.

Validação local: 372 testes backend/100% de linhas e ramos, Ruff e mypy; falha
após upload, corrida entre finalização e limpeza, retries, fencing, privacidade
do papel da API e rollback/reaplicação
da migration 0018 no `_test`. Base local migrada após backup verificado; worker e
dispatcher atualizados no Docker. Nenhum evento Meta real foi usado.


Dividir as features acima em mudanças revisáveis. Cada mudança atualiza este SDD,
`docs/PROJECT.md` e `docs/CHANGELOG.md`, incluindo evidências de testes e pendências.
Contratos que afetam outras fases devem ser refletidos no SDD geral e nos consumidores.
Não marcar como concluído por possuir mocks ou documentação de uma API ainda não validada.

## Integração com onboarding e interfaces

A identidade é iniciada na web; a posse do WhatsApp é verificada nesta fase, antes
de associar mensagens à contratação/organização. Telefone digitado no checkout ou
perfil não é verificação. Onboarding conversacional complementa o perfil inicial,
sem exigir uso diário do painel. Consentimentos são específicos por finalidade.

22/10/2026: renomeação para Meu Braço Direito aplica `MEU_BRACO_DIREITO_` e
roles `meu_braco_direito_*` também ao correlator em desenvolvimento. A migration
`0015_product_brand` fica entre 0014 e `0015_whatsapp_message_routing`; a
renomeação preserva dados e permissões. Escopo funcional da F02 não é ampliado.
