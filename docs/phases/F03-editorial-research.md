# F03 — Pesquisa, temas e planejamento proativo

Status: Planejada. Atualizado em 20/10/2026.
Dependências: F01, F02.

## Objetivo

Pesquisar referências permitidas e produzir ideias/roteiros úteis mesmo sem material novo no dia.

## Features e contratos

- Contexto de fatos, objetivo e materiais autorizados; ideias com fontes e validade.
- Raio configurável, candidatos a concorrente/referência e correção pelo comerciante.
- Google Places/Tavily respeitam permissões e retenção; dados privados não viram cache compartilhado.
- Roteiro e plano de cenas estruturados; preferências de frequência, gasto e mensagens.
- DecisionProvider com baseline; Jev em shadow/eval PT-BR antes de ativar.

## Critérios de aceite e testes

- Fontes ausentes/expiradas não viram fatos ou métricas inventadas.
- Sem dados novos, sugestão contextual; silêncio nunca autoriza publicação.
- Teste de orçamento de pesquisa e admissão por coorte, sem cron simultâneo de 200 mil.
- Medição de custo, acerto, abstention e fallback de modelos.

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
