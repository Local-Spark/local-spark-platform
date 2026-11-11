# Diagnóstico local do Docker — 10/11/2026

Durante a etapa visual 1, o titular relatou lentidão e mais de 4 GB atribuídos ao
Docker. Auditoria somente de estado, métricas e classes de erro; logs brutos,
variáveis de ambiente e credenciais não foram exibidos nem anexados.

## Evidências

- 51 contêineres existentes; 16 ativos e 35 não ativos na primeira leitura.
- VM Docker configurada com 8 CPUs e 4.109.803.520 bytes de memória (~3,83 GiB).
  Esse valor é limite/capacidade, não leitura de uso atual de cada contêiner.
- Host com 8 GiB; `memory_pressure -Q` informou 32% livres. A leitura RSS pontual
  da VM não representa sozinha seu footprint completo; não atribuir todo o valor
  visto pelo titular a processos dos contêineres ou certificar ausência de pressão.
- Cinco serviços em ciclo de reinício com política on-failure. Na primeira amostra,
  somavam ~435% de CPU (mais de quatro núcleos), apesar de RAM relativamente pequena.
  As contagens já tinham crescido dezenas de vezes desde a restauração anterior.
- Quatro pertencem à stack antiga `local-spark-platform`: worker, billing, relay
  e auth-mail. Seus PostgreSQL/Temporal/mailpit estavam parados; dependências e
  classes de erro mostraram falhas de resolução de nome/conexão.
- O relay de `meu-braco-direito-platform` também registrou ConnectError e resolução
  de nome; não foi feita correção de configuração ou inicialização de dependências.
- Kafka/Zookeeper pertencem a `spotlight-infra`/`spotlight-api`; não são um novo
  runner do projeto. Não foram alterados por esta tarefa.
- Restam contêineres de CI PostgreSQL/Temporal e serviços da stack atual. Não foi
  presumido que estão sem uso; nenhuma parada desses serviços foi autorizada.
- Muitos contêineres parados são ensaios anteriores de motion e projetos antigos.
  Não consomem CPU/RAM de processo em execução; removê-los libera sobretudo disco.
  Exit 137 sozinho não prova OOM. Não atribuir os erros do renderer ao modelo.

## Ação autorizada

O titular autorizou **parar e manter parados**, sem restaurar ao final:

- `local-spark-platform-worker-1`
- `local-spark-platform-billing-1`
- `local-spark-platform-relay-1`
- `local-spark-platform-auth-mail-1`
- `meu-braco-direito-platform-relay-1`

`docker stop --timeout 10` concluiu para os cinco. Nenhum contêiner, imagem, volume,
banco ou cache foi removido. Políticas de restart e compose não foram modificadas.
Não reiniciar esses serviços automaticamente ao terminar a etapa de motion.

Na amostra posterior havia nove contêineres ativos, somando aproximadamente
492 MiB e ~22% de CPU. Kafka/Zookeeper já não apareciam ativos nessa amostra;
nenhum comando desta tarefa os parou. Os números são amostras, não benchmark ou
prova de que todos os ganhos de memória vieram da parada dos cinco serviços.

A consulta read-only `docker system df` ficou demorada e foi interrompida;
nenhuma limpeza foi executada. Não usar prune global ou redução do limite da VM
como correção presumida. Antes de reativar a stack antiga ou o relay, corrigir
sua configuração/dependências. Avaliar desligamento adicional de CI/stack atual
somente após confirmar que não são necessários a outra atividade do titular.
