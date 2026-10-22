# F02 — WhatsApp e biblioteca de materiais

Status: Em implementação; F02.1–F02.2c1 entregues localmente.
Dependências: F00, F01.

## Objetivo

Receber texto, áudio, fotos e vídeo no número oficial da plataforma e montar solicitações com fatos rastreáveis.

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

Este recorte cobre assets finalizados. Ainda falta tratar objetos órfãos caso o
upload termine, mas o commit de processamento não ocorra; por isso não usar mídia
real até existir reconciliação de staging/órfãos e smoke Meta. Agrupamento de
mensagens, transcrição, resposta, confirmação de fatos e preferência contextual
permanecem F02.2c2+. O prazo de 30 dias é decisão inicial de produto e deve ser
reavaliado antes do piloto com clientes reais.

Validação local: migração 0017 revertida e reaplicada no banco `_test` e aplicada
na base local após backup; 367 testes backend com 100% de linhas/ramos, Ruff e
mypy aprovados. A web passou 149 testes/100% e uma jornada Chromium de exclusão.
Um objeto sintético foi gravado e removido no SeaweedFS; o dispatcher atualizado
subiu no Compose. Nenhum conteúdo real ou evento Meta foi usado.


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
