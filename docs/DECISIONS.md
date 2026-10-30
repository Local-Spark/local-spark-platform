# Decisões vigentes e pendências

Atualizado em **29/10/2026**, incluindo a primeira imagem paga autorizada pelo
produto (parte 3), o adiamento da recuperação de suporte C10 e a prioridade de
qualidade de conteúdo, skills e pesquisa de referências definida pelo proprietário.
Este registro reúne decisões de produto; implementação e contratos técnicos
ficam no [PROJECT](PROJECT.md), no [SDD](SDD.md) e nos [SDDs de fase](phases/README.md).
Uma decisão aprovada ainda não implementada deve aparecer com esse estado em
todos os consumidores. O texto antigo preservado em histórico não é requisito atual.

## Ordem de leitura e resolução de divergências

1. A decisão explícita mais recente do proprietário prevalece.
2. Este registro define o produto aceito; PROJECT resume o que existe e o que falta.
3. SDD geral e fase ativa definem contratos e critérios da próxima entrega.
4. Designs detalham alternativas e execução, respeitando os documentos acima.
5. Changelogs, evals, auditorias e snapshots são evidências datadas. Um estado
   antigo nesses registros não deve ser copiado como pendência ou regra vigente.

O código comprova o comportamento implementado, mas uma limitação atual não
substitui uma decisão de produto. Quando houver diferença, registrar a lacuna;
não afirmar que documentação, flag ou migration isoladas já a resolveram.

## Conceitos que não devem ser confundidos

- **Conta ativa:** conta não encerrada ou desativada. Pode existir com plano
  vencido; isso não dispensa identidade e membership válidas para consultar dados.
- **Plano ativo:** acesso financeiro vigente por assinatura ou patrocínio. C08
  separa revisão de uma criação admitida das novas criações e da publicação.
- **Arquivo preservado:** bytes e proveniência necessários à revisão. Não
  equivale a uma URL pública permanente, fato atualizado ou publicação aprovada.
- **Aceite de IA:** decisão contratual única. Direitos sobre cada material,
  comprovação de canal e aprovação de uma peça têm finalidades diferentes.

## Decisões confirmadas

### Qualidade, canal comercial e referências — 30/10

O titular pode informar o canal preferido de contato, venda ou agendamento
para orientar as chamadas; esse dado não deve ser inferido do telefone de
identificação. A chamada depende dos canais realmente informados e não presume
que uma imagem tenha um botão ou link funcional. Ausência de canal não autoriza
inventá-lo.

Após as correções de qualidade editorial, usar kit independente para QA e
desenvolver com a web duas entradas complementares de referências: perfis
indicados por @ pelo cliente e sugestões de negócios semelhantes obtidas pelo
sistema, apresentadas para aceite. A capacidade de pesquisa, fontes, métricas
e fornecedor ainda devem ser avaliados; uso de referências não autoriza cópia.

| ID | Decisão de produto | Implementação local e limite |
| --- | --- | --- |
| C01 | IA para interpretação, texto, imagem e transcrição integra o serviço. Um único aceite explícito por negócio em Plano e acesso, antes do checkout; contas existentes aceitam a versão uma vez. | GET/POST versionado com hash, ator, data e auditoria; web sem permissões por fornecedor. `visual_ai` exige enforcement do aceite; primeira imagem real executada sob autorização delimitada, sem ativar uso recorrente. Credenciais/orçamento/plano continuam internos; registros antigos não são reescritos. |
| C02 | Cada negócio tem conta de cliente e organização próprias, com cobrança e aceite próprios. | Onboarding cria organização/negócio; API e migration 0057 garantem no máximo um negócio por organização. Cobrança continua por organização. Memberships/seleção legadas e staff são preservados. |
| C03 | Um número de cliente WhatsApp ativo por negócio na primeira versão. | Vínculo único local. Múltiplos números e sua experiência ficam para evolução posterior. |
| C04 | Envios WhatsApp associados ao negócio são preservados sem expiração automática e não oferecem exclusão pelo histórico, para texto, imagem, áudio e vídeo. | Migration 0058 e leitores adaptados; API recusa exclusão. Eventos técnicos não atribuídos e uploads órfãos têm limpeza própria. Preservação não cria automaticamente memória pesquisável ou produto confirmado. |
| C05 | Trocar de número não interrompe o processamento de materiais já associados. A futura prévia e aprovação seguem para o número ativo novo. | Processamento e entrega simulada adaptados. Envio real de candidata WhatsApp pendente. Mensagens ainda não associadas não ganham origem retroativa por suposição. |
| C06 | Alterar kit, foto do acervo ou contexto durante uma criação aguarda os processos iniciados; cancela a fila ainda não iniciada e bloqueia novas admissões até aplicar a mudança. | `visual_fake` e `visual_ai` coordenam contexto, catálogo, kit, fotos e edição/revisão de roteiro pela mesma guarda, com writers financeiros e roles existentes. Novos writers de acesso exigem o mesmo protocolo. |
| C07 | A prévia anterior à alteração continua disponível para revisão e deve ser identificada como anterior à mudança. | Provas e campos de revisão estendidos a `visual_ai`. Preservar para revisão não confirma fatos vencidos, direitos ou aprovação de publicação. |
| C08 | Se o plano vencer durante uma criação já iniciada, concluir e permitir revisar a prévia privada; bloquear novas criações e publicação até renovar. | Implementado em `visual_fake` e `visual_ai`: admissão durável com plano vigente e continuidade/revisão após vencimento financeiro. Bloqueio explícito, revogação de patrocínio e perda de identidade/membership continuam distintos. Novos inícios/publicação exigem plano; renderer local legado conserva seu limite de conclusão. Conexão real validada com HTTP simulado, sem gasto novo. |
| C09 | Preservar as prévias geradas sem expiração automática enquanto a conta estiver ativa. | Prévias concluídas saem do purge por prazo; propostas, roteiro e snapshots referenciados são conservados e a revisão histórica usa links privados. Tentativas visuais iniciadas sem resultado resolvido também são preservadas. `expires_at` continua delimitando criação/aprovação, sem apagar a concluída. URL assinada e validade factual mantêm prazos próprios. Sem exclusão automática após encerramento nesta etapa. |
| C10 | Se quem iniciou uma alteração perder acesso, somente a equipe da plataforma pode resolver a pendência, com ação registrada. | Outro owner já não pode substituir nem descartar a pendência do autor original. **Implementação da recuperação staff adiada pelo proprietário em 29/10/2026**, para evolução de gestão de acesso/suporte; não bloqueia o fechamento da fatia simulada validada. Até lá, a pendência excepcional permanece bloqueada. A proposta de novas permissões não foi aprovada; manter autoria, RLS e auditoria existentes. |
| C11 | Publicação exige aprovação explícita da versão, arquivo/hash, legenda, destino e horário aplicáveis. | Revisão/publicação simuladas locais. Escolher kit, confirmar fato, aceitar o serviço ou permanecer em silêncio não aprova publicação. Meta/Instagram reais pendentes. |
| C12 | Foto e story são os formatos da oferta inicial. Vídeo e suas franquias/preço serão definidos depois; avatar/voz sintética ficam após o primeiro piloto comercial. | Regra inicial de formatos no código; não há franquia comercial final nem qualidade homologada. R$ 99/mês e teto total de R$ 50/cliente/mês orientam medição. |
| C13 | Provar a primeira peça personalizada antes de ampliar nichos; fechar BL04, depois a jornada/ajuste/proatividade BL05. | BL01/BL02 e BL03.1/BL03.2 locais; BL04 em implementação. BL03.3, BL06, pesquisa ampla, avatar e expansão multicanal têm etapas próprias. |
| C14 | Priorizar a qualidade da geração e estudar skills reutilizáveis para orientar as peças antes de avançar na jornada completa. Começar por feed e story e avaliar o resultado com o contexto e os materiais de cada negócio. | A skill do formato entra no briefing editorial e na peça integral, versionada por ID/hash; validação de qualidade real e seleção completa no WhatsApp ainda pendentes. O gate BL04.3 permanece. |
| C15 | Após o trabalho inicial de skills, desenvolver pesquisa de referências que combine indicações do cliente com descoberta automática de negócios semelhantes em destaque. Usar referências para orientar a criação sem copiar conteúdo ou identidade de terceiros. | Direção aprovada, não implementada. A descoberta automática deve ser estudada e validada quanto a fontes, permissões, relevância e métricas disponíveis; uma indicação do cliente não substitui a descoberta. Jev é uma hipótese a avaliar, não provedor escolhido. |
| C16 | O modelo deve criar o texto da peça, a legenda e o convite à ação a partir do pedido e das referências do negócio; não substituir sua resposta por texto fixo ou fallback do código na geração real. | O briefing com skill usa redação natural e validação de fonte/valores; não comprova sentido ou qualidade e exige revisão humana. Baseline disabled é rejeitado em novas propostas. A avaliação real do novo caminho ainda está pendente. |
| C17 | A geração deve reunir pedido, fatos, kit, acervo pertinente, referências externas aceitas quando disponíveis e skill de feed/story em um briefing; solicitar ao modelo a peça final completa, inclusive texto e identidade, e conferir o resultado antes da publicação. O trace deve permitir examinar a entrada e decisões sem expor dados privados em logs. O caminho visual que gera só fundo e aplica layout fixo deve ser descontinuado para novas gerações. | Novo caminho local com skill, referência do kit, peça integral e trace cifrado. Aprovação via API exige conferência humana por SHA; WhatsApp/web ainda não oferecem o checklist. Sem homologação/ensaio real posterior. Pesquisa e aceite de referências externas não existem. Histórico preservado não autoriza novo efeito do caminho antigo. Ideia de concorrentes/fontes do kit fica para estudo posterior. |
| C18 | Quando uma mensagem pedir peça com preço diferente do catálogo e não esclarecer se deseja atualizar o cadastro, perguntar ao cliente antes de continuar. Não substituir silenciosamente o valor pedido pelo preço antigo. | Decisão de 30/10/2026 para evolução posterior do WhatsApp/Jev. A identificação estruturada do preço, detecção de conflito e pergunta específica ainda não estão implementadas; a geração da peça é a prioridade desta fatia. |

## Perguntas resolvidas nesta revisão

| Referência da pergunta | Resolução |
| --- | --- |
| P01 — plano vencido durante criação | Respondida pelo proprietário; C08 aplicada nos caminhos `visual_fake` e `visual_ai`, com os limites descritos acima. |
| P02 — prazo das prévias | Respondida pelo proprietário; C09 aplicada às prévias concluídas e sua proveniência. |
| P04 — autor sem acesso com alteração pendente | Regra C10 confirmada; implementação de suporte adiada em 29/10/2026. |

Não reapresentar essas perguntas como dúvida de produto. Restam os limites de
implementação e validação descritos acima; isso não autoriza remover verificações de
identidade, direitos, assinatura, orçamento ou versão sem uma solução equivalente.

## Priorização de C10 — 29/10/2026

O proprietário decidiu registrar e implementar futuramente a recuperação de
pendências de autores sem acesso. Essa exceção administrativa não é necessária
para encerrar a fatia atual de admissão, continuidade financeira e preservação
com provedor simulado, já validada. A regra de recuperação exclusiva de staff
continua aceita; sua implementação sai da próxima fatia obrigatória.

Se a exceção ocorrer antes dessa entrega futura, conservar a pendência bloqueada,
sem aplicação automática, troca de autoria ou ampliação de permissões. A proposta
[de suporte restrito](design/BL04-staff-recovery-review.md) fica preservada como
referência futura, sem aprovação de funções privilegiadas ou grants. O adiamento
não encerra a BL04 nem libera o provedor real, que mantém os demais gates técnicos.

## Pendências delimitadas

| ID | Tema | Tratamento e momento |
| --- | --- | --- |
| P03 | Prazo de exclusão dos envios e prévias após encerramento da conta. | O proprietário decidiu **deixar pendente da fase de encerramento** e não implementar exclusão automática nesta etapa. Não escolher prazo ou prometer retenção pós-encerramento. Não bloqueia a BL04 para conta ativa. |
| P05 | Franquias, revisões, preço/volume de vídeo, cadência e custo comercial. | Definir com qualidade e custo por peça aceita medidos em BL04.3/F07; não fixar números por inferência ou com base em uma chamada isolada. |
| P06 | Recuperação da organização legada sem negócio. | Lacuna de implementação/UX: definir percurso que preserve organização, auditoria e histórico financeiro, sem loop entre onboarding e seleção. Não autoriza excluir ou atribuir dados automaticamente. |

Contratos comerciais definitivos, homologação Meta, staging e recuperação
operacional são entregas de prontidão, não prova já obtida nem motivo para
pedir outra autorização individual de IA ao cliente.

## Próxima entrega após a primeira imagem da parte 3

O modo `visual_ai` já conecta API, dispatcher, workflow/worker, runner e adapter
à guarda concreta, usando o aceite único C01. O percurso usa HTTP simulado nos
testes com PostgreSQL e Temporal locais; validação final da parte 2 aprovada.
Na parte 3, o proprietário autorizou Café do Cedro com foto CC0/logo, teto total
de US$ 1 e uma imagem, sem publicação. Uma chamada de imagem real concluiu a
prévia privada; duas interpretações Jev integraram a mesma autorização. Estimativa
total de uso: US$ 0,029701, sem comprovação de fatura ou margem. A reserva visual
incerta permanece no ledger, e a candidata aguarda decisão. A flag persistente
continua desligada; a autorização é delimitada, sem novo orçamento recorrente.
Registro em [evidência da parte 3](evals/bl042-first-product-image-2026-10-29.md).

A próxima preparação é estudar e desenvolver skills de **feed e story**, com
avaliação comparativa inicial da geração. Depois do trabalho inicial com skills,
pesquisar referências tanto indicadas quanto descobertas automaticamente e avaliar
seu uso na geração; a pesquisa não depende do fechamento do gate comercial.
**BL04.3** continua exigindo revisão do feed e post/story com titular, medindo
qualidade e custo por peça aceita, antes da liberação. BL05 fecha a jornada WhatsApp
de prévia/ajuste/aprovação e proatividade. As fases propostas e seus gates estão em
[skills e referências editoriais](design/skills-e-referencias-editoriais.md).
Novas chamadas exigem autorização apropriada às fontes e ao teto; a existência de
saldo estimado não concede gasto.

Um único repositório com uma pasta por skill é uma **recomendação** para estudo,
não decisão sobre criação, visibilidade, licença ou distribuição. Instalar uma
skill em um agente não a integra automaticamente à API do produto. Fornecedor de
pesquisa, acesso aos dados, critérios de destaque e similaridade, interação do
cliente com sugestões e custos permanecem a definir e validar em suas fases.

A admissão revalida proposta/fontes/aceite/plano antes do run durável; reserva e
fence continuam em outra transação/role. A recuperação exige prova de ausência
de tentativa/reserva e encerramento da prévia antes de liberar o run original,
com replay somente da reconciliação. `visual_ai` usa tentativa única e ID Temporal
estável; confirmação perdida ou resultado incerto não autoriza redispatch ou
troca automática de provedor. Prévias concluídas ficam revisáveis com a execução
desligada, conservando identidade, acesso, fontes e prova durável. C10 continua
adiada. A migration 0059 foi aplicada ao banco local da aplicação para a execução
da parte 3, sem novos grants ou código de produção. Meta de entrada/canal foi
sintética, entrega da candidata simulada e publicação nula; não afirmar WhatsApp
completo ou homologação. Validação dirigida aprovada: 94 unitários, lint/types
(151 módulos), sem mudança de código. Consulta/download owner funcionaram com
execução desligada e limites zero; o último CI completo é o da parte 2.

## Esclarecimento de jornada — 29/10/2026

O proprietário reafirmou que a IA cria o roteiro a partir da mensagem WhatsApp e
do contexto do negócio. O cliente revisa a prévia e pede ajustes; o editor manual
existente é ferramenta interna do laboratório DEV, não uma etapa da jornada do
cliente. A coordenação dessa ferramenta integra a proteção de fontes da parte 1.
Quando outra alteração já aguarda aplicação, o laboratório conserva o formulário
e pede retry depois; não cria um segundo comando conflitante. Isso é tratamento
técnico interno, sem nova decisão de produto, editor obrigatório ou entrega do
ajuste automático WhatsApp, que permanece BL05.
