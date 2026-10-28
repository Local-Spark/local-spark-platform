# BL04.2 — proposta de execução durável da prévia visual

Estado: **em implementação**, sem workflow real conectado ao dispatcher nem
chamadas pagas autorizadas por este documento. `VisualGenerationWorkflow` e sua
activity agora têm contrato isolado, prazo próprio e uma única tentativa; teste
com Temporal real verifica que uma falha não repete o efeito. O runner completo
e a guarda ainda não estão conectados ou registrados no worker. Não modifica o
workflow existente `StaticPreviewWorkflow`; execuções já iniciadas mantêm seus
comandos Temporal e continuam usando o caminho local/simulado.

## Caminho proposto

1. A API persiste uma prévia privada e uma identidade imutável de operação,
   com tenant, negócio, proprietário, proposta, versão do kit, fontes e formato.
   O worker despacha um workflow separado, por exemplo
   `VisualGenerationWorkflow`, com identificador estável para a prévia. A
   existência do workflow não autoriza envio ao fornecedor.
2. O dispatcher registra um fence e um prazo de lease. Uma nova activity
   carrega o registro, prepara fontes e executa a guarda completa: autorizações,
   isolamento, versões, prazo das fontes, plano, orçamento e claim durável de
   envio. O protocolo da guarda precisa fechar a lacuna entre as roles antes
   de esta etapa ser conectada; snapshot ou rechecagem isolada não bastam.
3. Apenas após a autorização confirmada, a activity chama o adaptador uma vez,
   sem retry automático. Nenhuma transação ou lock de banco fica aberto durante
   leitura de arquivos, envio ao provedor ou escrita de objeto. Saída é privada.
4. Solicitações de alteração de kit, foto ou contexto e de retirada visual
   aguardam a conclusão das criações já iniciadas; cancelam a fila ainda não
   iniciada e bloqueiam novas criações. Após resposta conhecida, finalizar a
   tentativa conforme o consentimento original e então efetivar a solicitação
   pendente. O commit precisa verificar fence, direitos e condições aplicáveis.
   A prévia concluída durante retirada continua disponível. A prévia concluída
   antes de alteração de uma fonte também permanece disponível para revisão,
   identificada como anterior à mudança; publicação exige direitos e aprovação.
   Somente após commit confirmado a prévia é legível. A espera de alteração de
   fontes ainda não foi implementada.
5. Em caso de cancelamento, timeout, queda ou confirmação de commit perdida,
   conservar o estado durável e a reserva apropriados; não repetir a geração
   nem presumir que o objeto é órfão. A reconciliação precisa distinguir uma
   falha comprovadamente anterior à submissão do resultado desconhecido.

## Limites temporais propostos

- O adaptador atual usa timeout HTTP de 180 s por operação; ele não garante,
  sozinho, limite de tempo total. Usar também um prazo total explícito, por
  exemplo 195 s, e considerar cancelamento após início da submissão incerto.
- Workflow novo: `start_to_close_timeout` inicial de 10 minutos para cobrir
  preparação, envio e acabamento; `schedule_to_start_timeout` de 1 minuto e
  `RetryPolicy(maximum_attempts=1)`. Esses valores são orçamento de engenharia,
  não garantias de capacidade; ajustar depois de medir tempos reais.
- Lease inicial de 12 minutos para incluir a espera permitida da fila, a
  activity e margem de reconciliação. Tempos máximos de acesso aos objetos e ao
  banco também precisam ser limitados; não depender de IO potencialmente
  infinito. A activity deve conferir lease e fence na admissão e no commit.
- Em fila congestionada, timeout de agendamento pode ocorrer sem a activity ter
  começado. Uma nova tentativa só pode ser criada ao comprovar no banco que
  nenhum claim de submissão foi feito; em outros casos manter incerto. Expirar
  lease ou receber timeout Temporal não comprova que a IA deixou de processar.
- Ao vencer lease após um claim, o reconciliador não pode redistribuir nem
  gastar novamente. Deve sinalizar o estado para recuperação auditável. Antes
  do claim, o redispatch pode ocorrer com novo fence somente se provar a ausência
  de efeito. Os casos de atraso na fila e de corrida entre reconciliador e
  activity exigem teste de integração com Temporal/PostgreSQL.

O dispatcher atual usa lease de 3 minutos, enquanto `StaticPreviewWorkflow`
permite apenas 2 minutos de activity; reutilizar esse caminho para a chamada
visual de 180 s seria incorreto. A proposta não deve ampliar esses prazos no
workflow histórico sem estratégia de versão e compatibilidade de replay.

## Formato e critérios para ativação

O acabamento experimental gera PNG; o orquestrador isolado o converte para JPEG
qualidade 95, sem subsampling, calcula hash dos bytes entregues e não copia
metadados EXIF/ICC. Um gradiente sintético verificou perda média inferior a dois
níveis por canal e remoção de metadados; não mede qualidade de fotografias,
logo ou texto reais. Isso requer avaliação visual BL04.3. A conversão não
conecta o orquestrador ao worker nem confirma fidelidade comercial.

Antes de ativar: guarda ponta a ponta revisada; schema e API para o modo real;
worker novo registrado; orçamento por tenant e global; recuperação de resultado
incerto e de consentimento pendente; testes de races, cancelamento, crash,
lease e replay; conteúdo e custos reais verificados. A conta Meta não é
necessária para ensaios locais com provedor simulado.
