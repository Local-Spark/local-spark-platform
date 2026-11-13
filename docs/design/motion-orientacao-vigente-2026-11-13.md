# Motion: orientação de leitura e ambiguidades documentais — 13/11/2026

Escopo: auditoria dirigida aos documentos de motion, PROJECT, SDD e fase BL04.
Não é uma certificação de ausência de conflitos em toda a documentação do produto.
Não altera contratos serializados, runtime, autorizações ou histórico de execução.

## Como interpretar os documentos

Instruções atuais do titular e AGENTS prevalecem sobre propostas e gates históricos.
O roteiro da próxima melhoria é
[motion-roteiro-melhoria-peca-completa-2026-11-13.md](motion-roteiro-melhoria-peca-completa-2026-11-13.md).
A implementação e a entrega local revisada desta sessão estão registradas em
[motion-execucao-melhoria-2026-11-13.md](motion-execucao-melhoria-2026-11-13.md).
O roteiro não autoriza por si só gastos ou migrações. Os achados abaixo são
o diagnóstico anterior à implementação; não substituem esse registro de execução.
A evidência visual vigente está na
[análise das 41 referências](../evals/analise-41-referencias-motion-2026-11-12.md).

Documentos datados registram o estado daquela entrega. “Atual”, “vigente”,
“próximo passo”, orçamento e aprovação dentro deles têm esse escopo temporal.
Não executar um gate antigo apenas porque uma busca retornou sua frase.
Contratos antigos continuam vinculando seus snapshots: documento mais recente
não autoriza promovê-los ou reescrever seus bytes. Para novos pedidos, conferir
seleção efetiva no builder e payload, não apenas uma constante ou texto de design.

## Achados e interpretação corrigida

| Problema documental | Evidência | Interpretação para a próxima execução |
| --- | --- | --- |
| Vários “próximos passos” incompatíveis | Piso independente manda fechar ASR/parar antes de render; ASR manda migrar 0118; relatórios posteriores registram ASR, migração, código e MP4 | Esses passos pertencem à rodada encerrada visualmente como reprovada. Não repetir migração ou cobrança; consultar estado real antes de agir. |
| Ordens de parada antigas aparentam bloquear trabalho novo | Etapas 2/3 dependem de OK; objeto realista manda parar antes da etapa 4; contrato antigo diz que não há etapa 8 | Gates de rodadas específicas, não proibição permanente. As sete etapas do roteiro de 13/11 são uma organização nova, não renumeração dos contratos anteriores. Autorização de trabalho novo deve vir da sessão atual. |
| “Piso” pode soar como garantia artística | Documento de piso v1 descreve sete critérios; implementação atual inclui v2 com oito; prévia passou estruturalmente e foi reprovada | Rubrica/guard verifica cobertura declarada e integridade, não qualidade mínima comprovada. Qualidade visual exige resultado e avaliação; preservar versões históricas. |
| Histórico de evolução pode ser confundido com geração nova | Contrato de 11/11 exige vínculo com patamar histórico; decisão de 12/11 retira base anterior do modo de nova criação | Evolução explicitamente solicitada e nova peça são percursos diferentes. Não injetar última peça do cliente no modo novo; baseline separada continua útil à avaliação do produto. |
| Zero referências pode parecer proibição de repertório visual | Preparações v4–v9 retiram oito prints e registram zero referências externas | É descrição da seleção daquela rodada. Não proíbe contexto seletivo de mecanismos, com proveniência/política de uso. Não autoriza copiar mídia de terceiros ou misturar baseline de cliente. |
| “Preservar vídeo” pode virar layout fixo | Documentos insistem em fonte, voz e tempo preservados; exemplo usa janela persistente | Integridade temporal/sonora não exige janela sempre visível. Exercitar os modos de visibilidade já permitidos, respeitando a ação relevante e o contrato capturado. |
| “Ação não estática” pode recusar som de ação filmada | Planejamento audiovisual inicial exige ação não estática; correção posterior permite ação interna ao vídeo com layout hold | Aplicar a regra versionada: hold do layout não prova ausência de ação na mídia. Não extrapolar essa exceção para qualquer elemento parado. |
| Revisão “representativa” pode sugerir cobertura suficiente | Etapa 2 mantém três janelas/20 quadros; motion_temporal confirma esses limites | Limite implementado, não meta de qualidade nem regra imutável. Nova política precisa de implementação/testes/orçamento; não assumir que aumentou só porque o roteiro propôs. |
| “Skill integrada” pode sugerir agente visual ativo | Auditoria de planejamento distingue texto/exemplos no builder de ferramentas; adapter não oferece ferramentas ao modelo | Instrução carregada não equivale a executar, observar e corrigir. Demonstrar o ciclo real; não presumir capacidade pelo nome da skill. |
| “Aprovado” mistura tipos de evidência | Documentos centrais acumulam aprovações técnicas, plano aprovado, MP4 entregue e reprovação visual | Sempre identificar objeto e autor do aceite. A prévia de 12/11 foi reprovada visualmente; o MP4 local não concluiu o checkpoint nativo. |
| Configuração e custos aparecem como se fossem atuais | Relatos antigos registram dev 0117, orçamento zero ou tetos autorizados para outras rodadas | Último estado documentado: dev 0118, runtime global desabilitado; US$ 0,774901 estimados e US$ 3,75 reservados sem reconciliação. Não são consulta nova nem saldo disponível; verificar antes de executar. |

## Decisões de manutenção

Adicionados avisos nos documentos com maior risco de interpretação como comando
atual e ponteiros nos três documentos centrais. Mantidos os relatos e contratos
históricos sem apagá-los. CHANGELOG continua histórico, não fila de execução.

A duplicação extensa entre PROJECT, SDD e BL04 continua sendo um risco estrutural:
um resumo vigente único e histórico separado seriam mais sustentáveis. Esta
fatia não reestrutura todo o acervo nem elimina todas as duplicações. Novas
atualizações devem distinguir explicitamente: implementado, apenas proposto,
validado tecnicamente, observado visualmente e aceito pelo titular.

Validação desta fatia documental: referências locais verificadas e git diff
--check. Sem código de produção, testes de runtime, banco, render ou chamada paga.
