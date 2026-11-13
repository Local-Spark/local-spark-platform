# Continuação antes da submissão de código — 12/11/2026

O titular aprovou avançar do plano corrigido para código, com parada antes de
qualquer render. A aprovação exata foi persistida, mas a primeira retomada parou
antes da contagem de tokens ou de claim/reserva/submissão do código. A guarda
privada do ensaio comparava literalmente o texto JSON de metadados; o armazenamento
canônico devolveu chaves em outra ordem, com conteúdo igual. Foi um erro da
conferência preparada pelo assistente, não resposta inválida do modelo.

## Guarda corrigida

Somente textos JSON dos blocos input_text são normalizados para comparar ordem
irrelevante de chaves. Valores, instruções, imagens, listas, parâmetros, plano
exato e ordem do schema de saída continuam vinculados. Contagem e submissão usam
a mesma entrada efetiva, preservada com wire_sha256. A entrada offline anterior
e o diagnóstico do bloqueio ficam arquivados; não se afirma identidade binária
entre ela e o texto reserializado. Nenhuma guarda de custo do produto foi relaxada.

## Por que foi necessária uma continuação explícita

O checkpoint consome a aprovação antes de executar. O erro anterior ao provider
ficou terminal no pedido e no workflow, preservando o evento de falha. Reenviar a
mesma aprovação não executa de novo; não se reverteu manualmente o recibo para
claimed nem se apagou histórico. Novo método interno de owner
MotionCheckpoints.recover_before_submission arma uma continuação auditada,
somente para implementação ainda não iniciada. Não é um endpoint/UX novos nem
uma repetição automática de chamadas pagas.

Precondições transacionais sob gate/RLS:

- Pedido failed e mesmo titular; aprovação original consumida, íntegra, do tipo
  approve e vinculada ao hash do pacote atual.
- Plano sem declarações de imagens geradas, evitando repetir efeitos de imagem.
- Ausência do efeito generate:0 e do seu upload payload:request. Qualquer estado
  desses efeitos recusa a continuação; uncertain e pedido em execução também.
- Admissão, consentimento, orçamento configurado e fingerprint do contexto
  revalidados antes de tornar o pedido ativo outra vez.

A operação de continuação tem identidade própria, payload criptografado/hash,
audit e outbox no mesmo commit. Usa motion.plan_approved já permitido pela 0118,
com event_id novo; não há tabela ou migração. A aprovação e a primeira falha não
são reescritas. A retomada reconhece apenas o recibo de continuação vinculado ao
pedido/evento/hash; consome esse recibo uma vez com identidade própria de auditoria.
O evento original continua idempotente/consumido. Duplicata da continuação não
repete código. Evento sem outbox ou recibo válido é recusado.

Temporal continua dono da execução, pelo workflow/atividade existentes. Não há
IO novo no workflow determinístico, runner concorrente ou rede sob locks SQL.
A etapa retomada reutiliza plano e ASR, compila o som planejado e passa pelas
mesmas guardas/claims/ledger antes da única chamada de código. Não há recuperação
por esse método depois de um claim de código/upload, de geração de imagens ou
de um resultado externo incerto.

## Validação e limites

Testes PostgreSQL no _test existente cobrem recuperação concorrente/idempotente,
recusa de efeitos de código/upload iniciados, pedido uncertain, aprovação ausente/
não consumida/adulterada/rejeitada, origem alterada, imagens declaradas, recibo
adulterado e outbox ausente. Modelo, mídia e renderer são sintéticos nesses testes.
Cobertura agregada do módulo de checkpoints: 100% de linhas/branches, sem omitir
produção. A fixture unitária do orquestrador agora usa o event_id canônico
motion.requested; antes usava UUID arbitrário com begin simulado.

No ensaio real, a aprovação e a primeira falha são preservadas. Foi comprovada
por leitura de efeitos e ledger a ausência de submissão/reserva de código;
a continuação mantém o teto único de US$ 1,25 já autorizado, sem liberar reservas
antigas. Runtime global permanece disabled e renderer recusado pelo processo.
Continuação real concluída com uma submissão de código, sem repetir ASR/plano;
parada em awaiting_render, approval original/falha preservados, zero render.
Resultado e limites: [eval da implementação](../evals/implementacao-motion-plano-aprovado-2026-11-12.md).

CI integral continua pendente nos gates anteriores de cobertura Node e schema
de geocodificação do _test; esta fatia não modifica esses problemas ou autoriza
migração, publicação, storyboard ou render. Validade do código e fidelidade de
metadados não certificam fluidez, qualidade visual ou inteligibilidade da mistura.
