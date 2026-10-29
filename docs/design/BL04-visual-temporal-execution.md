# BL04.2 — execução Temporal da prévia visual

Atualizado em **29/10/2026**. **Partes 2/3 conectadas e exercitadas**: `visual_ai`
tem persistência/API próprias e usa dispatcher, workflow, activity e runner
ligados à guarda concreta e ao adapter OpenAI. CI da parte 2 usa HTTP simulado;
a parte 3 concluiu uma imagem real de feed com teto/fontes autorizados, sem
publicação. Validação dirigida aprovada: 94 unitários, lint/types e leitura/hash
com execução desligada; CI completo da parte 2 não repetido.
O caminho `StaticPreviewWorkflow` conserva seus contratos e
IDs históricos. Produto e próxima entrega em [BL04](../phases/BL04-context-and-ai-production.md).

## Percurso conectado

1. A API owner persiste a prévia `visual_ai`, a operação, tenant/negócio/ator,
   proposta, candidata e fingerprint das fontes. A migration 0059 diferencia
   esse modo de `local` e `visual_fake`; não altera grants nem relabela registros.
   Foi validada no `_test` e aplicada ao banco local da aplicação para a parte 3.
2. O dispatcher reclama prévia pendente com fence/lease e inicia
   `VisualGenerationWorkflow` com ID estável `visual-preview/<preview>` e
   `REJECT_DUPLICATE`. O worker exige pools owner e correlator restritos e
   registra a activity visual somente quando a execução está habilitada.
3. `DatabaseVisualGenerationRunner` reconstrói a identidade persistida. A guarda
   admite fontes/owner/aceite/plano em owner; reserva orçamento e executa claim
   única na role correlator. Preparação, leitura de arquivos e chamada ao provider
   acontecem fora de row locks. Não há IO no workflow determinístico.
4. Após a resposta, o acabamento aplica o kit e produz JPEG privado por
   operação/fence/hash. Antes do commit, a guarda renova autorização e revalida
   prazos e identidade. Resposta/tokens não comprovam a fatura; custo desconhecido
   continua reservado mesmo com resultado conhecido e run concluído.
5. Mudanças de contexto/catálogo/kit/fotos/roteiro aguardam runs admitidos e só
   aplicam após conclusão segura. Prévias concluídas e proveniência permanecem
   para revisão, marcadas quando anteriores à mudança. C08 permite concluir e
   revisar criação admitida após vencimento financeiro; novos inícios/publicação
   exigem plano. Revisão histórica não exige execução visual habilitada.

O [protocolo da guarda](BL04-effect-guard.md) detalha ordem de locks, fronteiras
das roles e efeitos incertos. O aceite é único C01; APIs de retirada individual
são compatibilidade legada, sem nova etapa da experiência. Perda de identidade/
membership e direitos continuam impedimentos. C10 foi adiada pelo proprietário;
outro owner não assume a pendência. Retenção pós-encerramento fica para sua fase,
sem exclusão automática agora. Ver [registro](../DECISIONS.md).

## Tempos, duplicatas e incerteza

O adapter HTTP tem timeout de 180 s. A activity visual usa
`schedule_to_start_timeout=1 minuto`, `start_to_close_timeout=10 minutos` e
`maximum_attempts=1`; a lease é de **12 minutos**. Esses limites cobrem a
integração local e ainda precisam de medição operacional em produção.

Uma confirmação de início perdida não devolve `visual_ai` para a fila. Prévia
real já reclamada não é redispatchada; lease vencida marca
`VISUAL_OUTCOME_UNCERTAIN`, conservando a identidade do run e a reserva. Após
claim, timeout/cancelamento/lease vencida não provam que o provedor parou. Nunca
trocar provedor ou repetir a geração para resolver o resultado desconhecido.
Fence vencido impede commit tardio e não apaga custo ocorrido.

A recuperação somente libera run obsoleto/falhado após tornar a prévia terminal
sob lock correlator e comprovar ausência de tentativa/reserva, inclusive não
vinculada. Depois do commit confirmado, owner conclui o run. Confirmação perdida
repete somente essa reconciliação. Uma duplicata viva conserva o run original;
qualquer tentativa/reserva bloqueia a recuperação sem prova adicional. Não há
varredura automática de todos os runs abandonados nesta fatia.

`StaticPreviewWorkflow` conserva lease de três minutos, activity de dois minutos
e IDs `media-preview/<preview>/<attempt>`. A espera da candidata usa o patch
Temporal `visual-preview-wait-v1`: históricos antigos mantêm 60 consultas e
novos usam 156, com intervalo de cinco segundos. Esse patch não autoriza
reexecutar a geração visual.

## Ativação e próxima entrega

O opt-in exige desenvolvimento/teste, modo `openai`,
`VISUAL_AI_EXECUTION_ENABLED=true`, chaves de provedor/criptografia, enforcement
do aceite único e reserva positiva dentro dos tetos mensal por tenant e
agregado. Variáveis usam o prefixo `MEU_BRACO_DIREITO_`; a flag é `false` e a
reserva zero por padrão. Configuração incompleta bloqueia o caminho e não
substitui a imagem por um placeholder local. API usa apenas owner; worker exige
seu pool correlator. Resolução automática de item/fontes depende da configuração
Jev já existente com credencial/teto próprios, sem fallback lexical automático.

A **parte 3** concluiu uma chamada real de imagem para Café do Cedro com foto
CC0/logo e teto total de US$ 1 autorizados, além de duas interpretações Jev.
JPEG privado obtido pela API/S3; run terminado, candidata pendente e publicação
nula. Reserva visual permanece incerta: uso estimado não é fatura. A primeira
tentativa foi barrada pelo wrapper antes do HTTP de imagem e reconciliada com
prova de zero submissões, sem reenvio de efeito incerto. Entrada/canal Meta e
entrega de candidata foram simuladas. [Evidência](../evals/bl042-first-product-image-2026-10-29.md).

A próxima fatia é **BL04.3**, revisão de feed/post/story e custo por peça aceita,
seguida de BL05, WhatsApp como jornada principal e proatividade. Flags persistentes
seguem desligadas; essa autorização não é recorrente. A chamada isolada não
comprova fidelidade comercial, fatura ou margem.

Versão anterior integral: [snapshot de 28/10/2026](../history/2026-10-28-pre-documentation-reconciliation/design/BL04-visual-temporal-execution.md).
