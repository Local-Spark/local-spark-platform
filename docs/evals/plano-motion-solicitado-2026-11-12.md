# Plano audiovisual solicitado — 12/11/2026

Atualização posterior: autorização explícita recebida; backup/migração 0118 e
geração única do plano concluídos, com parada awaiting_plan e revisão entregue.
Resultado atual em [plano audiovisual](plano-audiovisual-motion-2026-11-12.md).
O registro de preparação/espera abaixo é histórico, preservado.

Pedido do titular: gerar somente o plano audiovisual e revisá-lo antes do código.
Autoriza a chamada de plano no teto novo apresentado de US$ 1,25; não aprova
implementação, render ou uma nova tentativa. Plano ainda não gerado.

## Trabalho preparado e verificado

- Formatação dos 13 arquivos apontados pelo Ruff corrigida. Cópias privadas
  anteriores e prova de igualdade das ASTs preservam a lógica existente.
- Lint global, 905 arquivos formatados, Mypy de 334 módulos app e oito scripts
  passaram. Regressão motion/exportadores: 1.646 passaram, dois skipped.
  Integrações motion/audiovisual/checkpoints: 23 passaram no dedicado _test,
  com roles restritas e sem executar as migrações novamente.
- Entrada v7/manifesto/payload conferidos, hash
  `6be0608f467776acfe1efcf97bfe9e88afc94d6ddbaaa40ff1e5dda613c2b158`.
  Guard offline reproduz bytes exatos e rejeita outra operação.
- Preparado processo privado que reutiliza serviços reais de admissão/RLS,
  ASR, ledger, orquestrador/checkpoint e workflow Temporal existentes em fila
  exclusiva. Somente generate:plan:0 permitido; wrapper exclusivo de submissão
  e renderer proibido. Não foi introduzido runner de produção concorrente.
- Limite novo de ledger preparado apenas em memória, sem apagar consumo ou
  reservas anteriores: US$ 1,25 para uma chamada. Capacidade de duas etapas exigida
  pelo runtime permanece intacta, mas não autoriza gastar com código.
- Credencial configurada e Temporal existente saudáveis. Configuração global
  segue disabled, sem novos serviços ou contêineres iniciados. Nenhum segredo
  incluído nos relatórios. Ferramentas pg_dump/pg_restore 18.3 disponíveis para
  backup compatível com PostgreSQL 17.6, antes de eventual migração autorizada.

## Bloqueio de autorização

A instrução original anexada pelo titular exige: “não repita migrações nem migre
dev implicitamente”. Dev confirmado em 0117_motion_recapture_events. Persistir
motion.plan_ready pelo checkpoint real exige a adição da 0118_motion_checkpoint_events.
A pergunta específica foi enviada ao titular e aguarda resposta. Nenhuma
migração, admissão, contagem remota ou geração paga ocorreu nesta rodada.

Migração preparada acrescenta quatro eventos à restrição já existente de outbox,
sem tabela nova ou remoção de dados. Execução exige backup privado/hash/índice
verificado e autorização correspondente; scripts não foram executados. Não contornar
a pausa persistida com uma chamada isolada ou fabricar estado awaiting_plan.

## CI e demais limites

Após remover o bloqueio de formatação, make lint/types passou; make motion-test
mostrou todos os testes Node passando, mas cobertura abaixo do gate: 98,33% linhas,
96,61% branches e 98,63% funções. Backend ampliado sem os dois testes que reaplicam
migrações foi interrompido após 108 aprovados e sete falhas de geocodificação;
uma evidencia policy_id ausente em reference_cost_reservations do _test. Não houve
correção implícita de schema nem exclusão de módulos de produção para cobertura.
Não declarar make ci completo aprovado ou falhas funcionais globais resolvidas.

Preparação privada em `.local/evals/motion-supervised-20261112/plan-only-v1/`,
com instrução do titular, prova de formato/guard, diagnóstico e scripts limitados.
status.json aponta para autorização de plano somente e espera de migração.

Depois da resposta necessária: backup/migração única → admissão real → ASR novo
no workflow → contagem e reserva → uma chamada de plano → checkpoint awaiting_plan
→ revisão por cena de fala/gravação, objeto, fundo, texto, transição e som.
Não aprovar checkpoint, gerar código ou render nesta rodada. Qualidade artística
e inteligibilidade da mistura continuam pendentes de material observado depois.
