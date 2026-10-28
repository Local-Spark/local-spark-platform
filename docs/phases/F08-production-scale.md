# F08 — Operação, segurança e escala

Status: Operação de produção planejada; Compose/CI e workflow de deploy locais.
Atualizado em 28/10/2026.
Dependências: Integra F00–F07; práticas começam na F00.

AWS/staging, recuperação, observabilidade operacional e capacidade ainda não
foram provisionados/homologados. Deploy preparado não comprova operação. Ver
[decisões](../DECISIONS.md) e [BL04 ativa](BL04-context-and-ai-production.md).

## Objetivo

Comprovar capacidade e recuperação dentro dos limites reais de infraestrutura e fornecedores.

## Features e contratos

- Console operacional, retry seguro, pausas, auditoria e ações por escopo.
- Circuit breakers, rate limiting, bulkheads e fairness medidos por tarefa/provedor.
- AWS/IaC, OIDC no CI/CD, secret refs e deploy versionado com workers compatíveis.
- Restore coordenado, políticas de retenção e perfis de carga por coorte.
  Envios WhatsApp associados já são preservados (`0058` aplicada). Prévia sem TTL
  enquanto a conta está ativa é decisão aprovada ainda por implementar. Política
  de encerramento/exportação/exclusão da conta será definida na fase própria;
  não introduzir limpeza automática por encerramento nesta etapa.
- Recuperação de alteração pendente cujo autor perdeu acesso será exclusiva da
  equipe da plataforma, com ação registrada/auditada; fluxo ainda não entregue.
  Outro owner não assume a pendência e staff não recebe acesso irrestrito à mídia.
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
