# Pausa solicitada pelo titular — 09/11/2026

O titular pediu parar e retomar amanhã. Nenhuma nova execução autorizada por esta
nota. Não iniciar geração, render ou crítica durante a pausa.

## Ponto exato

A reformulação gerou uma composição válida e três PNGs reais pelo worker/renderer
do produto, sem ajustes manuais no código. Nenhuma ilustração paga foi solicitada.
A peça alterna gravação central, desenho protagonista e fechamento com outra
hierarquia. Movimento/áudio ainda não foram avaliados; titular ainda não aprovou
estes novos quadros. Não há MP4 dessa composição nem conclusão do ponto 4/etapa 5.

O registro final falhou depois do render e dos uploads recebidos. Confirmado por
leitura do banco: a constraint `outbox_events_event_type_check` não permite
`motion.storyboard_ready`. A migração 0114 criou a tabela, mas não incluiu os eventos
`motion.storyboard_ready`, `motion.storyboard_decided`, `motion.storyboard_approved`.
A transação de registro da galeria foi revertida e o pedido ficou `failed` com
`MOTION_EXECUTION_FAILED`. O worker dedicado foi parado pelo finally do executor.
Não foi aplicada correção de schema ou recuperação do pedido nesta rodada.

## Evidências preservadas

Pasta `.local/evals/reel-storyboard-composition-20261109/`:

- `recovered-gallery.html`: galeria local dos PNGs realmente gerados pelo produto;
  não equivale a uma galeria persistida/aprovada. `scene-1.png` a `scene-3.png`.
- `preserved-board-payload.json`: composição, contexto, manifestos dos quadros e
  fingerprint recuperados do upload cifrado já recebido. Conteúdo privado.
- `composition.json`, `provider-response-0.json`, `generated-response-0.json`:
  resposta completa e uso; não precisam ser gerados novamente.
- `cost-status.json`, `paid-plan.json`, `approval.json`, `request.json`:
  estado/custos/plano e identidades. Não expor `.env`, `worker.env` ou credenciais.
- `run_proof.py`: tentativa encerrada; NÃO executar `execute` novamente.
- `approve_and_render.py`: preparação da continuação normal, ainda não executada;
  requer galeria persistida e aceite explícito exato. Não usar enquanto o pedido
  estiver failed; não criar `human-board-approval.json` sem resposta do titular.

## Próxima ação, após o comando do titular

1. Corrigir a lacuna de eventos com migração aditiva revisável; preservar validações,
   RLS e eventos anteriores. Não editar silenciosamente a migração já aplicada.
2. Preparar uma reconciliação controlada da captura concluída, validando os efeitos,
   hashes, contexto, titular e ausência de MP4/chamadas adicionais. Não reabrir o
   pedido por SQL improvisado nem refazer geração/upload já recebido. Registrar
   recuperação/auditoria/outbox de forma transacional e respeitar autorizações.
3. Apresentar os três quadros novos ao titular e aguardar sua avaliação antes do
   vídeo. O aceite anterior foi para reformular, não para aprovar esta nova versão.
4. Só depois continuar vídeo/crítica pelo Temporal, dentro do plano e orçamento;
   sem correção automática. Nenhuma etapa 5 antes de novo comando.

Manter foco na prova; testes dirigidos e curtos, sem CI completo prolongado.

## Custos e validação

Nova geração: 12.323 tokens de entrada, 14.422 de saída, estimativa US$ 0,175028;
reserva US$ 0,85 retida. Três tentativas somam estimativa **US$ 0,596631** e reservas
**US$ 2,55**. Nenhuma imagem/crítica paga. Teto original US$ 5,40 não ampliado.
Valores estimados não são fatura; não liberar reservas desconhecidas.

Última mudança de produto: orientação de composição em `motion_creative.py`;
20 testes direcionados passaram em 1,09 s, Ruff/format aprovados. O worker inclui
essa orientação e a instrução de hold estático de `motion_movement.py`. Runtime e
renderer não foram alterados. Nenhuma migração posterior à 0114 criada/aplicada.

## Retomada em 10/11/2026

Titular autorizou retomar. Migração e reconciliação concluídas, sem refazer a peça;
galeria real aguarda aprovação humana. Consulte o estado atual em
[reconciliação de 10/11](reconciliacao-storyboard-2026-11-10.md). As pendências
acima registram o estado da pausa; não devem motivar nova geração ou nova migração.
