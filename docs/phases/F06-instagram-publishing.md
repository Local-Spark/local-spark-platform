# F06 — Aprovação, agenda e Instagram

Status: Planejada. Atualizado em 25/10/2026.
Dependências: F01 e F04, incluindo a entrega da prévia por WhatsApp em F04.3.
F05 é necessária somente para peças com avatar.

## Objetivo

Publicar versões efetivamente aprovadas em contas profissionais elegíveis, com rastreabilidade por destino.

## Features e contratos

- Adapter fake de Instagram para exercitar aprovação, agendamento, erro, timeout,
  callback duplicado e resultado incerto sem conta Meta; o adapter oficial entra
  após essas regras estarem testadas. Publicação real exige OAuth e smoke externo.
- OAuth, scopes e capability discovery por conta; não pedir senha do Instagram.
- Aprovação vincula ator, versão, hashes, legenda, conta, janela e consentimento.
- Fluxo principal: enviar prévia, legenda, destino e horário proposto pelo
  WhatsApp; receber "Aprovar" ou "Pedir ajustes" do proprietário vinculado.
  A área web oferece a mesma decisão como alternativa, sem ser passo obrigatório.
  A resposta deve apontar para uma única peça/versão ainda válida; se estiver
  ambígua, vencida, alterada ou com recibo de entrega inconclusivo, pedir nova
  confirmação e não publicar. "Confirmar" um fato na F02 é outra ação.
- A aprovação final é durável, idempotente e auditada; exige versão/hash da arte
  e legenda, destino, janela e identidade autorizada. Nova edição ou render,
  mudança de fato, destino ou horário invalida a aprovação anterior. Publicar
  somente depois da aprovação explícita, plano/consentimento válidos e revalidação
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
