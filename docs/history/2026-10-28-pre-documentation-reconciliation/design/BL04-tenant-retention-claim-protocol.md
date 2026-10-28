# BL04.2 — protocolo proposto para claim e retenção por tenant

Estado: **desenho não implementado**. Uma migração experimental com política
por tenant foi testada no banco `_test` com as roles existentes e depois
removida, junto com o endpoint e testes experimentais desconectados. O banco
de desenvolvimento não foi alterado. Os jobs atuais ainda não usam holds.
A implementação só pode ser ativada depois de todos os caminhos de exclusão
e a admissão seguirem o mesmo protocolo.

## Evidência da cadeia

O ensaio temporário usou `save_events`,
`route_once` e `MaterialProcessor` com mensagem e mídia fictícias: o ID de
inbox é copiado para evento e asset. Essa igualdade é uma regra do código, não
uma FK entre as três tabelas. `editorial_briefings.source_asset_id` e
`editorial_proposals.source_asset_id` têm FK com remoção em cascata para
asset. A prévia registra uma cópia do ID da origem. Não se deve criar FKs
presumindo que inbox, evento e asset sempre coexistem.

No ensaio temporário, testes com dados sintéticos demonstraram que retenção raw e
o cleanup dentro de `route_once` apagam um evento segurado; o raw purge não
espera o lock da admissão. No teste de asset, `SKIP LOCKED` retorna vazio
durante a transação que cria o hold, mas a varredura seguinte reivindica o
asset mesmo após o hold ter sido confirmado. A exclusão do objeto acontece
antes de uma FK impedir o DELETE do asset. Os dois últimos casos foram
reexecutados sem a marcação de falha esperada para confirmar os motivos reais.
Os testes temporários não estão no CI, pois dependiam da migração removida;
suas falhas não são validação de comportamento seguro.

## Claim e conclusão do asset

1. O correlator descobre somente IDs, tenant e negócio de candidatos por suas
   permissões atuais sobre assets. A consulta é limitada e não assume que o
   estado descoberto continuará válido.
2. Para cada negócio, abre transação do próprio correlator, define apenas
   `app.tenant_id` com `set_config(..., true)` e obtém o mesmo advisory lock
   `visual-consent:{tenant}:{business}` usado pela admissão. Não troca
   `app.actor_id` por um proprietário. A policy dos holds permite ao correlator
   apenas SELECT das colunas mínimas do tenant corrente. Verificar a role,
   identidade, correspondência tenant/negócio e o estado sob esse lock.
3. Se houver hold da origem, ou se status/expiração deixaram de justificar a
   remoção, não reivindicar o asset. Caso contrário, gravar owner, fence e
   lease da exclusão na mesma transação. A admissão precisa tomar primeiro o
   mesmo lock, validar existência, tenant, negócio, TTL e ausência de pedido de
   exclusão **e de qualquer owner de exclusão**, mesmo com lease expirada, e
   inserir o hold na mesma transação do run. A lease expirada não prova que
   uma exclusão de storage já parou.
4. Somente após o commit do claim, apagar o objeto. Nunca fazer I/O de rede ou
   storage segurando o lock. O claim mantém a origem inelegível a novas
   admissões até o resultado ser conhecido e a linha ser eliminada.
5. Para finalizar, abrir outra transação do correlator no tenant, obter o lock,
   conferir owner/fence exatos, motivo de exclusão e ausência de holds antes
   de apagar inbox, evento e asset e registrar auditoria. Se o resultado do
   storage ou a confirmação da transação forem desconhecidos, manter estado de
   exclusão; não liberar uma nova geração nem presumir término por timeout.
   Retries devem ser idempotentes com chaves de objeto que não são reutilizadas.

## Outros caminhos obrigatórios antes da ativação

- `purge_expired_raw` deve tratar eventos e inbox sob o mesmo protocolo. Para
  inbox sem negócio identificado, adquirir lock da própria linha e revalidar
  que não há evento nem asset; o roteamento também bloqueia essa linha antes
  de criar o evento. Para registros associados a asset/evento, descobrir o
  negócio e revalidar a relação dentro da transação e do lock por negócio.
- Remover ou substituir o DELETE direto de eventos expirados em `route_once`;
  ele hoje contorna a retenção e não consulta holds.
- A exclusão voluntária de material deve entrar na fila de mudanças sob o
  mesmo lock, sem remover imediatamente a proposta. Não deixar novas
  admissões começarem após um pedido pendente.
- O purge de propostas e o de prévias precisam respeitar o hold de origem e o
  recibo de revisão. O recibo deve ser emitido na transação do `finish` após
  provar run/fence/hash e antes de liberar o hold ou apagar a origem.
- Passar prova interna de run/fence através das leituras do contexto,
  briefing, referências e renderização. A exceção para TTL expirado aplica-se
  apenas ao run admitido; não é autorização de uma nova geração ou publicação.
- A leitura da prévia preservada requer endpoint específico e os
  consentimentos comprovados no run, inclusive o caso de retirada durante a
  criação. O endpoint não deve compartilhar `file_key` usado pela publicação.

Uma falha na consulta do hold, no lock ou na validação de tenant deve abortar
o claim; nunca tratar erro como ausência de hold. Os lotes devem continuar
limitados e evitar que uma origem em espera bloqueie indefinidamente outras.
Antes de usar em escala, medir a quantidade de transações e a contenção por
negócio; a solução precisa respeitar a ordenação dos locks e não manter
conexões/locks durante chamadas externas.

## Testes para habilitação

Com roles reais e ao menos dois tenants, verificar claim concorrente com
admissão em ambas as ordens, hold não commitado, exclusão manual, TTL de
inbox/evento/asset/proposta/prévia, todos os caminhos de retry e o cleanup do
router. Simular uma exclusão de storage lenta que sobrevive ao prazo da lease;
nenhuma admissão deve passar enquanto o efeito externo puder estar em curso.
Verificar crash antes/depois do I/O e do commit, troca de fence, revogação de
owner, logs sem dados sensíveis, revisão por sete dias e impossibilidade de
publicar pelo endpoint de revisão. Recriar as regressões automatizadas antes
de ativar a solução; não habilitar o provedor real antes de elas passarem.
