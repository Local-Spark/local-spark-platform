# F08 — Operação, segurança e escala

Status: Planejada. Atualizado em 20/10/2026.
Dependências: Integra F00–F07; práticas começam na F00.

## Objetivo

Comprovar capacidade e recuperação dentro dos limites reais de infraestrutura e fornecedores.

## Features e contratos

- Console operacional, retry seguro, pausas, auditoria e ações por escopo.
- Circuit breakers, rate limiting, bulkheads e fairness medidos por tarefa/provedor.
- AWS/IaC, OIDC no CI/CD, secret refs e deploy versionado com workers compatíveis.
- Restore coordenado, retenção, exportação/exclusão e perfis de carga por coorte.
- Testar montagem do contexto versionado e fairness dos pools de mídia por coorte,
  incluindo custo por peça/tenant e limites contratados dos fornecedores.

## Critérios de aceite e testes

- Carga, crash tests, replay com histórico representativo e migração de workflows ativos.
- SLO por etapa, quota externa, custo e limite comprovados em relatório.
- Meta de 200 mil clientes só orienta cenários de carga; demonstrar capacidade,
  margem e recuperação por etapas antes de afirmá-la comercialmente.
- Restore não repete publicação/gasto e não reintroduz dados excluídos.

## Limites e decisões pendentes

- 200 mil clientes é objetivo de dimensionamento, não garantia por documentação.
- Kubernetes/sharding/extrair serviço só após evidência de necessidade.

## Integração e manutenção

Dividir as features acima em mudanças revisáveis. Cada mudança atualiza este SDD,
`docs/PROJECT.md` e `docs/CHANGELOG.md`, incluindo evidências de testes e pendências.
Contratos que afetam outras fases devem ser refletidos no SDD geral e nos consumidores.
Não marcar como concluído por possuir mocks ou documentação de uma API ainda não validada.

## Operação das interfaces

local-spark-web serve entrada pública, admin e cliente com permissões distintas.
Validar isolamento no backend, revogação, cookies HttpOnly/CSRF e tokens em memória conforme
contrato de autenticação própria, headers, origem compartilhada, acessibilidade e testes de jornada
em staging. Métricas agregadas/caches/replicas evoluem por medição; não fazer
consultas pesadas em cada abertura de painel nem atribuir capacidade sem carga real.
