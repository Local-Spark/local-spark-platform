# F02 — WhatsApp, recebimento e histórico de envios

Atualizado em **28/10/2026**. Estado: implementação local com entrada, vínculo,
processamento, transcrição e respostas delimitadas; envio real desativado e smoke
Meta pendente. Dependências: F00/F01. Este documento descreve o contrato vigente;
a [versão anterior integral](../history/2026-10-28-pre-documentation-reconciliation/phases/F02-whatsapp-ingestion.md)
preserva entregas F02.1–F02.2c6, migrations, contagens e premissas substituídas.
Ver [SDD geral](../SDD.md), [decisões](../DECISIONS.md) e [BL04](BL04-context-and-ai-production.md).

## Jornada e contrato de produto

WhatsApp é o percurso diário do proprietário para o **próprio negócio**, não
atendimento aos consumidores dele nem chat geral. O menu **WhatsApp** prioriza
situação do canal, telefone/SMS e vínculo. O histórico de envios é consulta
secundária; pedir conteúdo não exige escolher material nessa lista.

Cada negócio pode ter **um número de cliente ativo**, distinto do número oficial
do Meu Braço Direito. Vários números e suas regras de acesso/histórico são uma
evolução futura. O limite do canal não limita contas proprietárias na web.
Verificar posse do telefone não é vincular uma mensagem à organização; o vínculo
exige a prova própria. Header de tenant ou telefone digitado não concede acesso.

IA integra o serviço: o aceite único em **Plano e acesso** cobre processamento,
texto, imagem, interpretação e transcrição. Não há check separado de áudio no
WhatsApp ou de fornecedor em Informações e preferências. Registros legados
permanecem para compatibilidade; após o aceite único, sua mutação é recusada com
`SERVICE_AGREEMENT_MANAGES_PROCESSING`. Configuração, plano, direitos, limites e
orçamento são gates internos independentes do aceite.

Trocar o número não exige aguardar a criação. Material já associado permanece no
mesmo negócio e continua sendo processado. A entrega simulada aguarda canal ausente
e passa a usar o número ativo verificado novo; origem histórica e destino são
conceitos distintos. Envio real de prévia/pedido de aprovação ainda não existe.

## Material preservado e acervo separado

**Implementado localmente:** texto, foto, áudio, vídeo e seus eventos associados
não expiram automaticamente e não podem ser excluídos pela UI/API do histórico.
A migration `0058_whatsapp_durable_materials` foi aplicada ao desenvolvimento após
pausa e backup. Inbox associada permanece para deduplicação. Eventos técnicos não
atribuídos/status e uploads órfãos ainda têm limpeza técnica; essa regra não
promete retenção de mídia que nunca chegou a ser associada. Objetos já apagados
não podem ser restaurados pela migration.

Preservar material não implementa memória pesquisável, resumo, skill automática
ou cadastro de produtos. O acervo BL03 continua separado, privado e opcional em
**Sobre meu negócio**. Copiar foto WhatsApp ao acervo exige ação explícita e
direitos, cria chave própria e preserva proveniência; fotos desatualizadas do
acervo podem ser removidas sem oferecer exclusão do envio WhatsApp.

**Decisão posterior, ainda não implementada:** prévias geradas também devem ser
preservadas sem expiração automática enquanto a conta estiver ativa. `0058` cobre
somente envios WhatsApp; prazos e limpeza de propostas/prévias ainda existem.
A definição da retenção após encerrar conta foi adiada à fase de encerramento,
sem implementar exclusão automática nesta etapa; ver [registro](../DECISIONS.md).

## Entrada e correlação implementadas

- `GET /api/v1/webhooks/whatsapp` valida modo e verify token; `POST` valida
  assinatura nos bytes originais, limites, envelope e WABA/phone number ID.
  Subeventos têm identidade estável; só há 200 após commit. Inbox cifrada e role
  de ingestão não são leitura comum da API. Modo desabilitado responde 503.
- Vínculo owner-only em `/whatsapp-link` exige telefone verificado, acesso e
  configuração Meta. Código de uso único, SHA-256 persistido, TTL de 15 minutos,
  cooldown de 60 segundos e confirmação por mensagem assinada do mesmo número.
  Troca de telefone invalida desafios e desativa vínculo anterior em transação.
- Correlator isolado associa remetente por índice cego e vínculo válido, copia
  ciphertext para evento durável e audita com idempotência. Quarentena não cria
  negócio nem concede autorização. Mensagens anteriores ao vínculo não são
  automaticamente promovidas a fontes do negócio.
- Dispatcher usa lease, fencing e workflow Temporal com ID por mensagem.
  A activity revalida negócio, owner, autoridade de processamento, plano e fonte;
  para material já associado, o processamento não depende de manter o canal
  antigo ativo durante uma troca de número.
- Foto/áudio/vídeo são baixados com token da plataforma, hosts permitidos, sem
  redirects, limites de bytes, MIME/hash e inspeção Pillow/ffprobe. S3 privado,
  checksum e URL curta somente após autorização. Texto e transcript ficam cifrados.
  IO nunca mantém row lock aberto. Upload com chave exclusiva e intent durável
  permite reconciliar órfãos sem remover o asset finalizado.
- Agrupamento determinístico por negócio/remetente e janela fixa de dez minutos
  UTC evita grupos duplicados entre workers. A janela não prova compreensão do
  conjunto nem memória de conversa.

## Transcrição implementada

O worker Temporal normaliza áudio em WAV mono 16 kHz com FFmpeg e chama o adapter
configurado (`gpt-transcribe` no código atual) fora da transação. Áudio acima de
180 segundos é rejeitado antes da reserva. Credencial e teto diário positivo são
necessários; o aceite único cobre a finalidade, sem consentimento individual.

O ledger reserva segundos por tenant/dia antes da chamada. ID do evento e estados
`submitted`, `completed`, `uncertain`, `rejected`, `budget_exceeded` mantêm prova.
Submissão incerta não gera nova chamada paga automática; reserva não é devolvida
por simples timeout. Transcrição é texto observado, não confirmação de preço,
agenda, oferta ou intenção. A interpretação experimental opcional Jev e a busca
seletiva do acervo já existem no worker de desenvolvimento/teste da BL04.

## Conversa delimitada e respostas implementadas

O simulador owner-only em desenvolvimento/teste reconhece padrões claros de
preço/horário **hoje**, fixa data no fuso do negócio e propõe confirmação curta.
Texto desconhecido vai a revisão. O worker também cria decisão idempotente para
texto elegível da inbox vinculada. Confirmar versiona contexto e fato temporário;
descartar não confirma. A tabela de decisão guarda hash/proposta e auditoria,
sem duplicar a mensagem integral.

Há fila durável para perguntas e confirmações com destinatário cifrado, tentativa
antes do submit e prazo conservador de até 23 horas/fim da oferta. O dispatcher
pode usar a Cloud API apenas com configuração explícita e limite positivo por
organização/dia; `MEU_BRACO_DIREITO_META_REPLY_ENABLED=false` permanece o padrão.
HTTP aceito não comprova entrega; 5xx, queda e resposta ambígua viram `uncertain`,
sem retry automático. Recibos assinados deduplicados distinguem `sent`,
`delivered`, `read` e falha; dados de destinatário da fila têm retenção técnica
própria, distinta da preservação do material recebido.

`Confirmar`/`Descartar` exigem resposta vinculada a uma pergunta do mesmo remetente
ou uma única pergunta recente inequívoca. Confirmação factual nunca aprova peça.
Staff com MFA pode revisar metadados de falha/incerteza por projeção restrita e
auditada; não há reenvio por essa revisão. Essa capacidade delimitada não é um
assistente geral nem o envio real de candidatas da F04/F06.

## Restante e validação

Faltam homologação do App/WABA e percurso oficial, opt-out, tarifas monetárias,
resposta orientadora para ambiguidades, recuperação segura de envios incertos,
conversa avaliada com fontes e coordenação de uma única resposta por evento.
A restrição WABA foi observada no smoke histórico; seu estado real deve ser
reverificado antes de retomar a integração. Simulação não confirma liberação Meta.

Testes devem cobrir assinatura, replay/reordenação, callback antes da correlação,
RLS/roles restritas, grupos concorrentes, mídia inválida, órfãos, troca de número,
transcrição e orçamento incerto, confirmação factual e isolamento entre negócios.
Banco exclusivo `_test`, conteúdo sintético, Temporal local e mocks externos.
As evidências datadas de 271–455 testes e testes de navegador das primeiras fatias
estão no snapshot; os gates correntes agregados estão no [CHANGELOG](../CHANGELOG.md).
Atualizar fase, PROJECT, SDD e CHANGELOG em cada entrega; smoke Meta é gate
separado da comprovação local.
