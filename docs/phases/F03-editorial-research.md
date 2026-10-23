# F03 — Pesquisa, temas e planejamento proativo

Status: Em implementação; F03.1 entregue localmente em 23/10/2026.
Dependências: F01, F02.

## Objetivo

Pesquisar referências permitidas e produzir ideias/roteiros úteis mesmo sem material novo no dia.

## F03.1 — Contexto confirmado e versionado (entregue localmente)

O proprietário registra até 20 fatos por negócio, com tipo, declaração, origem
informada e validade. Preços, horários e ofertas exigem validade; fatos vencidos
continuam no histórico, mas uma proposta futura não poderá usá-los como atuais.
Preferências de objetivo, tom, frequência semanal e assuntos a evitar ficam em
campo separado. Hipóteses são uma categoria distinta e permanecem vazias nesta
fatia: texto vindo do WhatsApp, transcrição ou pesquisa não vira fato confirmado.

`GET/PUT /api/v1/organizations/{tenant_id}/businesses/{business_id}/editorial-context`
consulta e substitui o snapshot. O PUT exige `expected_version` e `operation_id`;
o banco faz compare-and-swap, registra cada versão imutável e audita no mesmo
commit. Repetir a mesma operação devolve a versão original; mesmo ID com outro
conteúdo e edição baseada em versão antiga retornam 409. Histórico limitado a 20
versões recentes, leitura por versão e restauração explícita estão na mesma API.
A restauração cria nova versão; não apaga o histórico. RLS e autorização de owner
protegem os dois registros por tenant/negócio. A web oferece edição, correção e
restauração, com conflito de versão visível.

Não há chamada paga nem inferência nesta fatia. F03.2 consumirá um snapshot
fixado, separará propostas e fatos e só então integrará um provedor de texto com
consentimento, orçamento e eval. Pesquisa de referências, raio e agendamento
proativo também continuam pendentes. A WABA Meta restrita não bloqueia a edição
manual do contexto, mas impede homologar ingestão real.

Validação local: 417 testes backend com 100% de linhas/ramos, Ruff e mypy;
concorrência, replay, autorização e isolamento em PostgreSQL real. Migration 0021
revertida/reaplicada no `_test` e aplicada ao desenvolvimento após backup
verificado. Web: 158 testes com 100% nos quatro critérios, build, formatação e
jornada Chromium de salvar/restaurar.

## Features e contratos

- Contexto de fatos, objetivo e materiais autorizados; ideias com fontes e validade.
- Raio configurável, candidatos a concorrente/referência e correção pelo comerciante.
- Google Places/Tavily respeitam permissões e retenção; dados privados não viram cache compartilhado.
- Roteiro e plano de cenas estruturados; preferências de frequência, gasto e mensagens.
- DecisionProvider com baseline; Jev em shadow/eval PT-BR antes de ativar.
- `BusinessContext` compacto e versionado por tenant/negócio: fatos confirmados
  com origem/validade, preferências explícitas e padrões hipotéticos separados.
  Snapshot fixado em cada proposta/roteiro; dono pode inspecionar, corrigir e
  restaurar versões. Atualizações concorrentes usam CAS, evento único e auditoria.
- Montar apenas contexto necessário e fontes autorizadas; registrar tokens/custo
  reais e comparar qualidade/custo com baseline antes de alegar economia. Entrada
  externa não é instrução confiável para o agente.
- Implantar reserva atômica de quota/COGS antes de qualquer pesquisa ou chamada de
  modelo paga nesta fase, inclusive propostas proativas sem material do dia.

## Critérios de aceite e testes

- Fontes ausentes/expiradas não viram fatos ou métricas inventadas.
- Sem dados novos, sugestão contextual; silêncio nunca autoriza publicação.
- Teste de orçamento de pesquisa e admissão por coorte, sem cron simultâneo de 200 mil.
- Medição de custo, acerto, abstention e fallback de modelos.
- Aprovação posterior de uma peça não confirma fatos comerciais usados nela;
  preço/promoção/horário vencidos ou não confirmados bloqueiam a sugestão factual.

## Limites e decisões pendentes

- Fonte pública não dá acesso a métricas privadas da concorrência.
- Não compartilhar ou treinar com conteúdo sem direitos compatíveis.

## Integração e manutenção

Dividir as features acima em mudanças revisáveis. Cada mudança atualiza este SDD,
`docs/PROJECT.md` e `docs/CHANGELOG.md`, incluindo evidências de testes e pendências.
Contratos que afetam outras fases devem ser refletidos no SDD geral e nos consumidores.
Não marcar como concluído por possuir mocks ou documentação de uma API ainda não validada.

## Interfaces e transparência

Propostas e referências aparecem no WhatsApp e, quando disponível, na área do
cliente. Admin vê estado operacional e consumo, não segredos. Fonte, data, fatos
e limites de gasto acompanham sugestões. Entrega depende dos SDDs web admin/cliente.
