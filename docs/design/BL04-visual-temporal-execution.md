# BL04.2 — execução Temporal da prévia visual

Atualizado em **28/10/2026**. **Contrato isolado implementado/testado:**
`VisualGenerationWorkflow` e sua activity usam prazo próprio e uma tentativa.
**Integração pendente:** workflow não registrado no worker, dispatcher/runner
não o iniciam e a guarda real não foi implementada. Isso não libera chamadas pagas.
O caminho existente `StaticPreviewWorkflow` permanece local/simulado; alterar o
novo fluxo não autoriza quebrar replay de execuções antigas.

## Percurso a conectar depois da guarda

1. Persistir prévia, identidade imutável de operação, tenant/negócio/owner,
   proposta, fontes, kit e formato. Schema/API do modo real precisam de contrato
   específico; hoje existem `local` e `visual_fake`.
2. Dispatcher reclama fence/lease e inicia workflow estável para a prévia.
   Activity prepara fontes e executa a guarda completa de contrato único, owner,
   acesso, direitos, versões, orçamento e claim durável de submissão.
3. Confirmar admissão/reserva antes da chamada única. Leituras/escritas de
   arquivos e rede ficam fora de transações e locks. Não executar IO no workflow.
4. Persistir resultado por operação/fence/hash e liquidar custo conhecido ou
   manter incerto. Aplicar mudanças pendentes quando todos os trabalhos admitidos
   tiverem conclusão conhecida. O modo simulado já cobre parte de contexto,
   catálogo, kit e fotos do acervo; ainda falta cobrir todos os escritores no real.
5. Preservar prévia privada para revisão, marcando criação anterior à mudança.
   Vencimento do plano após admissão permite terminar/revisar e bloqueia novas
   criações e publicação até renovação. Prévias devem deixar de expirar enquanto
   conta ativa; retenção/acesso atuais ainda exigem essa implementação coordenada.

O aceite é único; retirada individual por fornecedor/modalidade é compatibilidade
legada, sem etapa nova na experiência. Owner revogado não recebe acesso por causa
da preservação. Somente staff poderá resolver pendência do autor sem acesso, com
registro/auditoria e acesso restrito; outro owner não assume a operação. Esse fluxo
ainda precisa de implementação. Retenção após encerramento fica para sua fase,
sem exclusão automática agora. Ver [registro](../DECISIONS.md).

## Tempos do contrato isolado e integração restante

O adapter HTTP usa timeout de 180 s. O desenho isolado usa activity de até dez
minutos, espera de agendamento de um minuto e `maximum_attempts=1`; lease de doze
minutos é proposta para cobrir fila, execução e margem. Esses valores precisam
ser ligados e medidos como conjunto, incluindo limites de banco/storage e prazo
total da operação HTTP. Não são garantia operacional de produção.

O dispatcher atual de prévia usa lease de três minutos e o workflow estático
permite dois minutos de activity. Reutilizá-los sem mudança coordenada para uma
chamada visual de 180 s seria incorreto. Não ampliar tempos do workflow histórico
sem versão/patching e teste de replay.

Timeout de agendamento pode ocorrer antes do início da activity. Redispatch só
é seguro quando o estado durável comprovar ausência de claim de submissão.
Após claim, cancelamento, timeout ou lease vencida não provam que o fornecedor
parou: preservar estado/reserva e recuperar sem repetir geração. Fence vencido
impede commit da peça, sem apagar um custo ocorrido ou comprovar custo zero.
A recuperação ainda precisa ser demonstrada entre PostgreSQL, Temporal e storage.

## Saída e gate de ativação

O acabamento experimental produz PNG e o orquestrador isolado entrega JPEG
qualidade 95 sem subsampling/EXIF/ICC, com hash dos bytes finais. Um gradiente
sintético validou apenas perda técnica de conversão e remoção de metadados;
não prova qualidade de foto, logo ou texto. O acabamento do modo fake está ligado;
o provedor real continua isolado.

Antes de registrar o novo worker/dispatcher: implementar e testar
[coordenação transacional](BL04-atomicity-proposal.md), orçamento por tenant e
agregado, resultado incerto, fonte mutável, mudança comercial, crash, lease/fence,
replay, retenção e acesso das prévias. Usar provedores falsos no `_test` e
Temporal local. Homologação de qualidade/custo é BL04.3, distinta desses testes.

Versão anterior integral: [snapshot de 28/10/2026](../history/2026-10-28-pre-documentation-reconciliation/design/BL04-visual-temporal-execution.md).
