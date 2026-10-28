# Entrega — repositórios, infraestrutura e gates

Reconciliado em **28/10/2026**. [PROJECT](../PROJECT.md), [SDD](../SDD.md) e
[fases](../phases/README.md) definem estado e ordem vigentes. O plano v0 anterior
continua no snapshot; seus nomes de módulos/rotas/serviços eram propostas.

## Repositórios e organização

`local-spark-platform` contém FastAPI, serviços, adapters, schemas, migrations,
workers/dispatchers e Temporal. Seguir `app/core`, `app/api/v1`, `app/schemas` e
`app/services`; não importar pacotes/credenciais privados do Spotlight nem criar
schema por tenant. `local-spark-web` contém React/TypeScript. Infraestrutura
separada continua uma fronteira prevista, sem presumir repo provisionado/deploy.

API, dispatchers, workers de IO/mídia e cobrança podem escalar separadamente sem
virar microserviço por etapa. Temporal é o coordenador dos mesmos workflows,
sem Celery/RabbitMQ/runner paralelo. Redis é candidato futuro, sem dependência
local ativa. A documentação de operação é [operations](../operations.md) e o
ambiente local é descrito no [README](../../README.md).

## Ambientes e gates

- Desenvolvimento local usa serviços locais e fixtures sintéticas. Testes de DB
  só usam base dedicada terminada em `_test`, com logins runtime restritos;
  não limpar/migrar base de usuário para executar suíte.
- IA paga, API pública/paga, publicação e identidade exigem credenciais e teto
  explicitamente configurados para a execução. CI não chama provedores pagos.
- Staging/AWS, HTTPS, segredos/IAM, storage privado, observabilidade e alertas
  ainda precisam ser provisionados/homologados. Workflow de deploy não é deploy.
- Backup/restauração precisam cobrir PostgreSQL, objetos e execuções Temporal,
  com reconciliação de efeitos externos. Backup SQL isolado não cobre todo o produto.
- Capacidade cresce por medição/coortes; autoscaling sem admissão pode multiplicar
  gasto, 429 e fila. Meta de 200 mil clientes não demonstra escala já atendida.

O backend exige Ruff/formatação, mypy e testes unitários/integração PostgreSQL/
Temporal com 100% linhas/branches, sem excluir módulos produtivos. Web exige
tipos, testes, cobertura integral, build e navegador para jornadas significativas.
Mudança só documental é verificada por coerência, links e diff, sem declarar nova
execução de CI. Não confundir validação histórica com suíte atual.

## Sequência concreta

1. Reconciliar documentação e decisões; implementar a coordenação BL04.2 com
   mocks, fontes/contrato/acesso/fence/budget, recuperação e todos os escritores.
2. Adequar retenção/acesso de prévias: preservar enquanto conta ativa; criação
   admitida termina após vencimento do plano e continua revisável, sem novos
   trabalhos/publicação até renovação. Só staff recupera autor sem acesso, com
   ação auditada; esse caminho ainda precisa existir.
3. Conectar guarda, modo real e workflow visual separado depois de provar os
   gates. BL04.3 mede fidelidade, qualidade e custo por peça aceita com refações.
4. BL05 fecha WhatsApp simulado, ajuste versionado, aprovação/publicação falsas
   e proatividade mínima. Hoje solicitar ajuste ainda não regenera automaticamente.
5. Homologar WhatsApp/Instagram oficiais; fechar franquias/custos F07, staging,
   recuperação/suporte F08 e piloto acompanhado com as receitas aprovadas.
6. BL03.3/imports, BL06/expansão de kits, pesquisa avançada e outros canais seguem
   o [roadmap](delivery-roadmap-2026-10-27.md). Avatar/voz ficam após o piloto.

Esta ordem permite trabalho local enquanto Meta não foi homologada, sem alegar
jornada oficial concluída. Plano inicial contempla foto/story; quantidades dependem
de medição e vídeo exige decisão comercial própria. Retenção após encerramento
da conta será decidida em sua fase, sem descarte automático criado nesta revisão.

## Rollout de mudanças duráveis

Executar migrations aditivas com inventário/backup e versões compatíveis; tratar
claims incertos sem presumir conclusão por lease. Não misturar código antigo que
apaga materiais com 0058 durável. Quarentena/upload têm seu [procedimento](BL04-quarantine-rollout.md).
Workflows ativos precisam replay representativo e versionamento/patching antes
de deploy. Reverter imagem não prova replay compatível; restaurar base antiga
pode perder dados novos e duplicar efeitos externos sem reconciliação.

Versão anterior integral: [snapshot de 28/10/2026](../history/2026-10-28-pre-documentation-reconciliation/design/v0-delivery.md).
