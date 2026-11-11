# F06 — Aprovação, agenda e Instagram

Status: Fatia local em andamento; integração oficial posterior ao piloto de geração.
Atualizado em 08/11/2026.
Dependências: F01 e F04, incluindo a entrega da prévia por WhatsApp em F04.3.
F05 é necessária somente para peças com avatar.

## Contrato corrente e limites da entrega

O [roteiro vigente](../design/execucao-ate-etapa-7-2026-11-07.md) prioriza geração,
revisão, aprovação da peça e download. Postagem Instagram é posterior e não
bloqueia o piloto por autoatendimento com cobrança; a aprovação da peça não
serve como autorização implícita para publicar.

O [aceite único do serviço](../DECISIONS.md) substitui permissões de IA por
fornecedor, sem substituir aprovação de publicação. Envios WhatsApp associados
já são preservados. C08/C09 estão implementadas no recorte `visual_fake`/`visual_ai`:
conclusão e revisão privada após vencimento financeiro de trabalho admitido,
com conservação das prévias/proveniência; novas criações/publicação exigem plano
vigente. Bloqueio financeiro explícito e perda de acesso são situações distintas.
A extensão ao renderer legado e motion permanece pendente. Validade factual,
prazo da decisão e URL assinada curta continuam separados da preservação.

Material associado continua em processamento durante troca de número; a entrega
simulada usa o novo número ativo verificado após vínculo. O envio real de prévia/
aprovação ainda não está conectado. Conteúdos (`/app/content`) oferece revisão
complementar; controles de render manuais ficam no laboratório DEV.

## Objetivo

Publicar versões efetivamente aprovadas em contas profissionais elegíveis, com rastreabilidade por destino.

Evidência da fatia entregue em 26/10/2026: a migração 0036 e o serviço local guardam candidata entregue,
identidade vinculada, decisão idempotente, hash da arte, legenda, destino
Instagram e horário. A API do proprietário e os comandos recebidos no fluxo
WhatsApp podem aprovar ou registrar pedido de ajustes de uma candidata única;
sem decisão a fila de publicação fica vazia. O dispatcher Temporal publica
somente um recibo `fake-instagram/<id>` em development/testing/staging e nunca
chama Meta. Mudança/expiração de contexto, roteiro, fonte ou prévia bloqueia a
decisão ou o envio; lease vencido vira `unknown`, sem retry cego. A web de
desenvolvimento mostra o simulador e o estado. A publicação falsa é proibida em
production. Pedido de ajustes ainda não cria nova versão; comandos ambíguos
são ignorados sem publicação e precisam uma resposta de orientação. Cancelamento,
recibo/erro Meta, reconciliação real e expurgo do conteúdo/telefone cifrado das
entregas conforme política aplicável permanecem pendentes para o futuro piloto
com publicação. Não presumir prazo de exclusão enquanto P03 estiver adiado.

## Features e contratos

- Adapter fake de Instagram para exercitar aprovação, agendamento, erro, timeout,
  callback duplicado e resultado incerto sem conta Meta; o adapter oficial entra
  após essas regras estarem testadas. Publicação real exige OAuth e smoke externo.
- OAuth, scopes e capability discovery por conta; não pedir senha do Instagram.
- Aprovação vincula ator, versão, hashes, legenda, conta, janela e direitos de uso;
  o contrato do serviço não aprova a peça.
- Fluxo principal: enviar prévia, legenda, destino e horário proposto pelo
  WhatsApp; receber "Aprovar" ou "Pedir ajustes" do proprietário vinculado.
  A área web oferece a mesma decisão como alternativa, sem ser passo obrigatório.
  A resposta deve apontar para uma única peça/versão ainda válida; se estiver
  ambígua, vencida, alterada ou com recibo de entrega inconclusivo, pedir nova
  confirmação e não publicar. "Confirmar" um fato na F02 é outra ação.
- A aprovação final é durável, idempotente e auditada; exige versão/hash da arte
  e legenda, destino, janela e identidade autorizada. Nova edição ou render,
  mudança de fato, destino ou horário invalida a aprovação anterior. Publicar
  somente depois da aprovação explícita, plano/direitos/contrato válidos e revalidação
  imediatamente anterior ao envio. Silêncio nunca equivale a aceite.
- Imagem/carrossel/Reel/Story elegível, processamento de container e confirmação.
- Agendamento, cancelamento concorrente, reauth e reconciliação de publicação UNKNOWN.
- Aprovação/rejeição e correções explícitas podem propor nova versão do contexto do
  negócio. Preferência explícita pode ser aplicada após confirmação; aprovação da
  peça sozinha vira sinal de estilo/hipótese, não prova de preço, horário ou venda.

## Critérios de aceite e testes

- Smoke real por formato elegível e app review para usuários externos.
- Revisão não herda aprovação; cancelamento/expiração antes do envio respeitados.
- Timeout após possível publicação não cria segunda postagem automaticamente.
- Testes locais cobrem aprovação por webhook WhatsApp assinado e envio fake,
  respostas duplicadas/concorrentes/ambíguas, pedido de ajuste, expiração e
  bloqueio de publicação sem aceite; smoke Meta real é gate separado.

## Limites e decisões pendentes

- TikTok/Facebook/Shorts são expansão posterior.
- Não prometer remoção/rollback de post se API não suportar.

## Integração e manutenção

Dividir as features acima em mudanças revisáveis. Cada mudança atualiza este SDD,
`docs/PROJECT.md` e `docs/CHANGELOG.md`, incluindo evidências de testes e pendências.
Contratos que afetam outras fases devem ser refletidos no SDD geral e nos consumidores.
Não marcar como concluído por possuir mocks ou documentação de uma API ainda não validada.

## Painéis e base de métricas

Conexão OAuth e revisão da versão/destino usam páginas do cliente. Publicações
registram IDs externos e origem; iniciar coleta periódica de insights autorizados
com snapshots, período e última sincronização conforme políticas da plataforma.
Admin acompanha operação. F07 agrega e apresenta evolução; indisponível não vira zero.

O [snapshot anterior](../history/2026-10-28-pre-documentation-reconciliation/phases/F06-instagram-publishing.md)
preserva o contrato da primeira entrega simulada; a [BL04 ativa](BL04-context-and-ai-production.md)
detalha coordenação de fontes e gates antes de integrar efeitos reais.
