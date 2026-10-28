# Revisão das migrations locais de 0050 a 0057

Estado em 28/10/2026: após revisão e aprovação do proprietário, a base de
desenvolvimento foi atualizada de `0050` para `0057`, sem organizações com mais
de um negócio. A sequência aplicada foi 0051 → 0053 → 0054 → 0055 → 0056 →
0057; não há 0052.

| Migration | Efeito | Relação com a decisão de produto |
| --- | --- | --- |
| 0051 | Acrescenta campos para retirada e registro de consentimento editorial. O código atual os consulta; não aciona IA por si. | Ligada aos controles antigos de fornecedor; candidata a simplificação, que exige rever seus consumidores. |
| 0053 | Acrescenta prova de upload para fotos do acervo; registros antigos começam sem essa prova. | Proteção da integridade do material, independente de o cliente escolher fornecedor de IA. |
| 0054 | Acrescenta geração do consentimento editorial e seu snapshot nas propostas. Propostas antigas pendentes podem deixar de ser executáveis sem nova prova. | Ligada ao controle antigo de texto; deve ser revisada ao consolidar o aceite, sem retirar as proteções de trabalhos em andamento por suposição. |
| 0055 | Acrescenta quarentena para fotos e bloqueia a migração caso haja exclusão incerta; pode marcar itens legados de quarentena. | Proteção de integridade do acervo, independente de controles de fornecedor. |
| 0056 | Cria a tabela de aceite por negócio e suas permissões. | Estrutura aprovada para reaproveitamento; não ativa a jornada nem conecta a interface por si só. |
| 0057 | Impõe no máximo um negócio por organização, falhando se houver duplicatas. | Restrição aprovada. Não garante que toda organização tenha um negócio nem resolve sozinha acesso por conta. |

Consultas locais imediatamente antes da atualização identificaram zero fotos e
propostas editoriais, exclusões incertas e candidatas à quarentena; havia um
consentimento editorial. Não havia jobs pendentes, efeitos externos incertos ou
workflows ativos nas filas verificadas. As migrations não fazem chamadas a
fornecedores, mas serviços em execução podem processar trabalho independentemente.

O código atual consulta as colunas das versões intermediárias. Pular ou apenas
marcar versões como aplicadas não cria as estruturas e pode quebrar a aplicação.
O proprietário escolheu aplicar a sequência existente no ambiente local e
revisar os mecanismos antigos depois. A aplicação não representa aprovação para
manter controles individuais na jornada final e não conclui o aceite único.

Na aplicação, um novo backup privado posterior à limpeza foi criado, restaurado
em base isolada e submetido às migrations antes da base local. API e workers
foram pausados temporariamente após checagens e retomados ao final. Versão,
unicidade, isolamento da tabela de aceite, histórico, `/health/ready` e `/docs`
foram verificados. A restauração isolada não validou ACLs nem proprietários; as
permissões efetivas relevantes da tabela de aceite foram verificadas na base
local. O backup não inclui mídia de objetos ou estado do Temporal; restaurar a
base inteira pode reverter mudanças posteriores. Limpeza e migração foram
operações separadas.
