# BL04 — contexto seletivo e produção visual com IA

Atualizado em **29/10/2026**, com a primeira imagem real pelo produto concluída
na parte 3 e a priorização de skills de geração antes da avaliação BL04.3.
Estado: **em implementação local**, sem aprovação
comercial. Este é o contrato vigente da fase, junto ao [SDD geral](../SDD.md), à
[trilha BL](BL-brand-library.md#bl04--recuperar-contexto-e-produzir-uma-peça-nova)
e ao [registro de decisões](../DECISIONS.md). A versão anterior foi preservada
[integralmente no histórico](../history/2026-10-28-pre-documentation-reconciliation/phases/BL04-context-and-ai-production.md);
pendências datadas de permissões por fornecedor nesse histórico não são novas
etapas da jornada contratada.

## Qualidade de copy e ação — 30/10/2026

Ensaios diretos em negócios fictícios expuseram bloqueios por notação visual,
identificadores vazados na copy e CTAs que pressupunham interação. A fatia
local corrige a distinção de direção/fatos, valida campos públicos e permite
ao titular informar o canal comercial no contexto versionado. A checagem é
conservadora e não valida o conteúdo semântico ou a imagem final: revisão humana
continua obrigatória. O novo caminho precisa de nova avaliação real controlada;
os ensaios anteriores exigiram ajustes manuais e não provam essa correção.

Foi criado um segundo [kit fictício Ateliê Aurora](../evals/kit-atelier-aurora-v1/README.md), como fixture isolada de QA,
sem inclusão no catálogo nem execução pelo produto. Próximos trabalhos: usá-lo
em ensaio e implementar com a web indicação de perfis e recomendações para
aceite do cliente. Fonte, disponibilidade de métricas e custos da descoberta
automática ainda precisam ser demonstrados; não inferir acesso do Jev ao Instagram.

## Resultado esperado

Um pedido livre identifica o que divulgar, recupera somente fontes pertinentes
do mesmo negócio e produz uma prévia privada com o kit aplicado. Falta de fonte,
negação ou ambiguidade pede esclarecimento; material hipotético não vira fato.
Revisão da peça e autorização de publicação são ações distintas. WhatsApp real
e publicação oficial continuam dependentes de homologação Meta.

## Contrato vigente

- **IA integra o serviço.** O cliente aceita uma vez em **Plano e acesso**, antes
  do checkout, o uso para texto, imagem, interpretação/Jev e transcrição. Contas
  existentes usam essa mesma jornada. WhatsApp e Informações e preferências não
  oferecem controles individuais de IA, áudio ou fornecedor. O aceite versionado
  por negócio registra versão/hash, ator, data e auditoria; não ativa pagamento,
  provedor ou publicação. Configuração, acesso, plano, orçamento e direitos das
  fontes permanecem verificações internas.
- **Compatibilidade preservada.** Registros e APIs antigos de consentimento não
  são reativados nem reescritos pelo aceite. Após o aceite único, mutações dessas
  permissões são recusadas com `SERVICE_AGREEMENT_MANAGES_PROCESSING`. Retirada
  individual por fornecedor não é uma nova funcionalidade a entregar. A geração
  contratual dos pedidos impede que o aceite reviva trabalho editorial antigo.
  O aceite inicial aguarda efeitos visuais e alterações legadas pendentes.
- **Fontes privadas e versionadas.** Kit confirmado, fatos vigentes, itens ativos,
  direitos, hashes e proveniência acompanham o briefing. Correspondência lexical
  identifica candidatos; não confirma preço, produto, oferta ou interpretação.
  Nomes com alegações comerciais exigem fato confirmado adicional. Enviar apenas
  fotos pertinentes, com no máximo uma referência do kit quando necessária.
- **WhatsApp preservado; acervo editável.** Envios associados de texto, foto,
  áudio e vídeo permanecem sem prazo automático e sem exclusão pelo histórico;
  migration `0058` aplicada localmente. Fotos desatualizadas do acervo podem ser
  removidas. Preservar envios não implementa memória pesquisável, cadastro de
  produto ou skill automática. Eventos técnicos não atribuídos e uploads órfãos
  continuam sujeitos a limpeza; objetos já apagados não são recuperáveis.
- **Troca de número não interrompe a criação.** Material já associado continua
  no mesmo negócio. Na entrega simulada, a ausência de canal adia o envio; após
  vínculo verificado, o destino é o número ativo novo. A origem histórica não
  fixa o destinatário. Há um número ativo por negócio na versão inicial.
- **Plano vencido e prévias — C08/C09 entregues no recorte local.** A criação
  `visual_fake` ou `visual_ai` admitida tem prova durável para concluir após o vencimento
  financeiro e permitir revisão privada. Novas criações e publicação continuam
  exigindo plano vigente. Bloqueio financeiro explícito, revogação de patrocínio
  e perda de identidade/membership não são vencimento. A exceção de conclusão
  ainda não cobre o renderer local legado. Prévias concluídas e proveniência
  são conservadas sem limpeza automática por prazo; tentativas visuais iniciadas
  sem resultado resolvido também são preservadas. `expires_at` continua sendo
  janela de criação/aprovação. URL assinada curta, validade factual e aprovação
  permanecem conceitos separados da preservação, sem atualização implícita de fatos.
  A revisão de resultados concluídos não depende de manter o modo de execução ativo.
- **Alterações aguardam trabalhos admitidos.** Solicitações de mudança de fonte
  bloqueiam novas admissões e cancelam a fila não iniciada. Trabalhos já admitidos
  terminam antes da aplicação da mudança. A prévia concluída permanece para
  revisão, identificada como anterior à alteração; direitos e publicação seguem
  suas verificações. A cobertura atual dessa coordenação é parcial, abaixo.

## BL04.1 — interpretação e contexto: implementado e limites

O worker pode usar **Jev**, opcionalmente em desenvolvimento/teste, desligado por
padrão. A interpretação usa o aceite único; não pede consentimento TypeSafe
separado. Uma operação durável reserva orçamento por tenant/dia, revalida ator,
origem e snapshot e não repete submissão incerta. Recusa de orçamento anterior
à submissão pode aguardar no workflow em intervalos de uma hora, por até sete
dias, com nova verificação no ledger e revalidação. Estados incertos antigos
não são reclassificados como recusa de orçamento.

A configuração exige `TYPESAFE_API_KEY`,
`MEU_BRACO_DIREITO_INTENT_AI_MODE=jev`, chave de criptografia e teto positivo
`MEU_BRACO_DIREITO_INTENT_AI_DAILY_BUDGET_USD_MICROS`. Configurar não homologa
produção nem autoriza um novo ensaio pago. O teto é conservador por tenant/dia;
a reserva conhecida ainda conserva o máximo reservado após sucesso, sem provar
custo faturado ou capacidade em escala.

O briefing experimental liga intenção, formato, catálogo, kit, fatos e fotos.
O nome do item ativo pode ser fonte factual versionada; preço e oferta não são
inferidos dele. O formato inicial definido para a hipótese de R$ 99 é foto/feed
e story; vídeo e quantidades aguardam decisão comercial. A regra é estática,
ainda sem franquias persistidas por múltiplos planos.

A pergunta local é simulada e genérica. Não há conversa completa, memória de
múltiplas mensagens validada, ferramentas arbitrárias ou pesquisa de concorrentes.
Os caminhos de conversa e conteúdo ainda precisam coordenar uma única resposta
por evento antes do envio real. O [ensaio Jev/OpenAI](../evals/intent-comparison-2026-10-27.md)
identificou erros e saídas incompletas; não é holdout independente nem homologação.

## BL04.2 — prévia simulada: implementado e limites

O modo `fake` captura snapshot privado, lê até uma foto WhatsApp e fotos
pertinentes do item/espaço, confere hashes, normaliza orientação e remove
metadados das cópias. Preserva originais. Usa kit, fato e CTA conferidos;
identidade durável, fence e reserva transacional protegem a tentativa.
O acabamento aplica fontes, nome, tagline, logo autorizado e texto do kit sobre
cena neutra, com marca explícita de **simulação**. Não cria a cena com OpenAI e
não comprova qualidade comercial. O resultado é revalidado no acesso e na revisão.

`MEU_BRACO_DIREITO_VISUAL_AI_MODE=fake` e teto positivo
`MEU_BRACO_DIREITO_VISUAL_AI_MONTHLY_BUDGET_USD_MICROS` habilitam a simulação
somente em desenvolvimento/teste. A reserva fictícia é de um milionésimo de dólar,
liquidada em zero. API/schema preservam esses caminhos; mudar somente a
configuração para `openai` não habilita a execução conectada descrita na parte 2.

Um teste sintético usa Temporal e PostgreSQL reais: material já processado,
contexto/acervo, roteiro, dispatchers, prévia simulada com kit e revisão. Intérprete
e storage são stubs; não chama Meta/OpenAI e não começa no webhook completo.
Os testes iniciais uniam preparo, reserva, adapter e orquestrador com HTTP/guarda
simulados. A parte 1 abaixo acrescenta a guarda concreta com PostgreSQL restrito.

A admissão simulada agora bloqueia a proposta, depois o gate visual e o domínio
comercial, revalidando fontes/fingerprint, usuário ativo, membership, aceite e
plano antes de inserir o run e sua auditoria na mesma transação owner. A revogação
de patrocínio participa do lock comercial existente. A reserva/fence e o ledger
continuam em transação correlator separada, com os tetos já existentes; um run
gravado não autoriza repetição quando a etapa seguinte falha ou fica incerta.
Os testes adicionados exercitam captura real e concorrência PostgreSQL com
catálogo e alteração comercial. Isso não prova serialização de todos os escritores
nem autoriza o provedor real.

### Recuperação sem reserva e concorrência — 29/10/2026

`VisualAdmissionRecovery` cobre uma queda entre a admissão owner e a reserva
correlator usando somente as tabelas, locks e roles existentes:

1. Consulta o run com o ator original e o gate owner, sem transferir sua autoria.
2. Em outra transação, bloqueia a prévia fake e depois o ledger tenant. Exige
   prévia falhada, lease vencida ou fence substituído, sem arquivo/hash concluídos,
   e prova ausência de tentativa e de reserva, inclusive uma reserva não vinculada.
3. Marca a prévia como `failed`/`VISUAL_ADMISSION_ABORTED` e grava auditoria.
   O commit impede reserva e conclusão por um worker atrasado antes de liberar
   qualquer alteração de fonte pendente.
4. Somente após confirmação do commit correlator chama `finish` owner com o
   fence original. Crash/confirmação perdida permite repetir essa reconciliação;
   a auditoria da prova terminal não duplica, e a geração nunca é retomada.

Uma duplicata de execução ainda viva retorna `skipped`, conservando o trabalho
original. Reserva existente ou incerta impede a liberação; uma liquidação sem
confirmação também conserva a admissão. O renderer usa a recuperação ao reencontrar
um run no redispatch e após uma falha conhecida sem reserva. Registros já fora
da fila (prévia vencida, falhada ou tentativas exauridas) exigem invocação interna
explícita do serviço; ainda não existe varredura automática nem ação web/staff.
O autor sem acesso continua bloqueado conforme C10, adiada.

Reserva e claim verificam `clock_timestamp()` após adquirir os locks, em nova
instrução. A reserva verifica novamente após os locks financeiros e reverte
tentativa/reserva/total agregado se os prazos venceram durante a espera. Os testes
usam PostgreSQL restrito e cobrem locks da prévia, do tenant e do agregado, sem
submeter imagem. Tetos concorrentes por tenant e agregado são exercitados com
run owner real → tentativa correlator; custo incerto conserva a reserva e custo
tardio comprovado ajusta apenas a diferença, sem crédito duplicado.

A composição kit/logo também tem prova: upload de outro logo imutável não muda a
fonte pronta; draft e confirmação participam do gate; confirmação espera os runs,
bloqueia novos inícios e cancela a fila anterior. A prévia concluída continua
revisável com o kit/logo anterior. A recuperação de PUT incerto de logo ainda
pendente continua operacional; a parte 1 abaixo coordena edição/revisão de roteiro.

A consulta e o download para revisão preservam concluídas após o prazo da prévia
ou da proposta, sem usar esse acesso como autorização de geração/publicação.
O purge conserva seus objetos e a reconciliação conserva propostas, versões de
roteiro e snapshots referenciados como proveniência. No modo visual, revisão
após vencimento financeiro exige prova do run, fence e resultado concluído,
além de identidade e permissões das fontes. O prazo de aprovação permanece
independente; uma candidata vencida não ganha nova autorização por ser preservada.
Antes do rollout, drenar os workers antigos de limpeza e revisar suas leases.
Registros legados em `purging` com chave e hash conhecidos não são reclamados
pela limpeza nova; conservam estado e bytes para conciliação manual. Não inferir
que um arquivo já apagado foi recuperado. A revisão visual por outro owner ainda
pode depender do ator/vínculo original, e permanece fora deste recorte.

A fila durável de alterações cobre atualização/restauração do
contexto, catálogo, confirmação de kit e criação/alteração/exclusão de fotos do
acervo. Bloqueia novas admissões, espera as iniciadas e preserva a prévia anterior
com indicação visível. Erros previstos mantêm a alteração explícita e o bloqueio.
Edição/revisão de roteiro e writers financeiros são cobertos pela parte 1 abaixo;
logo ready é imutável e novas capacidades de acesso devem seguir o protocolo.
A decisão C10 já definiu recuperação exclusiva
pela equipe da plataforma, com ação registrada/auditada. Esta fatia recusa que
outro owner substitua ou descarte a pendência do autor original. A recuperação
staff foi adiada pelo proprietário em 29/10 para evolução de gestão de acesso e
suporte. Não bloqueia o encerramento da fatia simulada já validada. Até sua entrega,
a pendência excepcional continua bloqueada; nenhuma nova permissão foi aprovada.

Upload do acervo reserva a alteração antes de transferir, sem rede sob row lock.
Após vencer a reserva, o autor pode descartar upload incerto; a chave fica privada
em quarentena e a próxima operação usa outra chave. Retomada exige prova persistida
de PUT de tentativa única. Não há limpeza física automática da quarentena nem
fluxo de suporte para recuperar a pendência se o autor perder acesso. O rollout
requer drenagem e avaliação dos órfãos legados conforme o [procedimento](../design/BL04-quarantine-rollout.md).

## BL04.2 — parte 1: guarda concreta e escritores coordenados

`DatabaseVisualEffectGuard` e `GuardedVisualSubmissionClaims` implementam a prova
owner de fontes/aceite/run, reserva por tenant/agregado, claim única com revalidação
financeira/de identidade e commit privado por versão/fence/hash. As duas roles
continuam com commits separados; run durável conserva as fontes entre eles.
O [protocolo e inventário dos escritores atuais](../design/BL04-effect-guard.md)
documenta a ordem dos locks, o ponto de início durável e as falhas conservadas.
Não foram criados grants, roles ou tabelas para contornar a fronteira.

Edição e revisão de roteiro agora enfileiram comandos e conservam a versão atual
durante a criação. Após o commit de finish, a aplicação adquire proposta → visual
em outra transação; nunca adquire proposta a partir do gate visual. Leituras do
autor retomam aplicação pendente. O editor é ferramenta interna DEV; a IA cria o
roteiro a partir do WhatsApp/contexto, e o cliente revisa a peça. O laboratório
aguarda alteração de outra fonte pendente/falhada, conservando o formulário para
retry. Contratos opcionais `pending_change` e polling não antecipam sucesso.

`BillingProcessor.save` participa do lock comercial antes de mudar acesso.
Revogação de patrocínio usa o relógio real após a espera. Usuário/membership são
revalidados; não há writer runtime ou grant de atualização de active/papel de
cliente. Fontes WhatsApp processadas, transcrição concluída, logo ready e briefing
preparado são imutáveis nos fluxos atuais; mudanças de seleção usam comandos
coordenados. Upload de logo pendente é evolução de órfãos, não fonte selecionável.

Troca de telefone não muda mais o fingerprint de material já atribuído (C05),
e a entrega usa o vínculo novo verificado. Drenar fila/criações com fingerprints
antigos antes do rollout; concluídas antigas mantêm revisão por prova durável.

O orquestrador instala/restaura `admitted_visual_run` e distingue efeito terminado
de custo liquidado. Resposta conhecida permite concluir o run sem liberar custo
incerto. Resposta tardia não vence fence novo; confirmação perdida de claim,
reserva ou commit conserva prova/hold e, quando aplicável, objeto. Nenhum reenvio
automático. Na entrega da parte 1, essa guarda foi exercitada somente com
simulação persistida; a parte 2 acrescenta o modo explícito abaixo.

## BL04.2 — parte 2: caminho completo conectado

O modo persistido/API `visual_ai` identifica geração pelo adapter de imagem,
sem confundir resultados com `local` ou `visual_fake`. A migration 0059 exige
fingerprint para ambos os modos visuais, preserva os registros existentes e
recusa downgrade com prévias `visual_ai`. Não altera grants; foi aplicada
somente ao banco `_test` na parte 2. Para a execução autorizada da parte 3,
também foi aplicada ao banco local da aplicação.

`DatabaseVisualGenerationRunner` liga o pedido ao preparo/normalização de fontes,
guarda concreta, reserva, claim única, adapter OpenAI, acabamento, storage privado
e commit por versão/fence/hash. A API somente enfileira: não faz chamada de imagem
nem precisa receber o pool correlator. O worker usa pools owner e correlator
restritos e registra workflow/activity visual apenas com a execução habilitada.
Os testes usam o adapter real com transporte HTTP simulado, PostgreSQL e Temporal
locais; storage/interpretação externos são simulados. Não houve chamada paga.
Essa é a validação da parte 2; a chamada controlada posterior está registrada abaixo.

A ativação exige desenvolvimento/teste e, com prefixo `MEU_BRACO_DIREITO_`,
`VISUAL_AI_MODE=openai`, `VISUAL_AI_EXECUTION_ENABLED=true`,
`VISUAL_AI_RESERVATION_USD_MICROS>0`, tetos mensal por tenant e agregado pelo
menos iguais à reserva, chaves de provedor/criptografia e enforcement do aceite
único C01. A flag é desligada e a reserva zero por padrão; configuração incompleta
é recusada e não troca a geração por um placeholder local. Seleção automática de
item/fontes exige a interpretação Jev existente, com sua chave/teto próprios;
correspondência lexical de candidatos não vira seleção automática silenciosa.

O fence/reserva são atômicos entre si. Fontes, aceite, plano e run compartilham
a transação owner; a reserva continua em outra transação/role.
Falha entre os commits conserva uma admissão bloqueante, sem reenvio automático.
Essa sequência não é uma transação única; a barreira durável e a claim coordenam
os escritores atuais conforme o desenho. Novas capacidades de acesso precisam
participar do protocolo, sem inferir novos privilégios de banco.

O dispatcher inicia `VisualGenerationWorkflow` com ID estável
`visual-preview/<preview>`, rejeição de duplicata e lease de 12 minutos. A activity
tem até dez minutos, espera de agendamento de um minuto e uma tentativa. Uma
confirmação de início perdida conserva a mesma identidade/fence; prévia real já
reclamada não é redispatchada. Lease vencida marca `VISUAL_OUTCOME_UNCERTAIN`,
conservando run/reserva e sem inferir que o provedor parou. Recuperação só libera
admissão após prova de ausência de tentativa e reserva; não há varredura automática
de todos os runs abandonados. `StaticPreviewWorkflow` conserva IDs/tempos antigos;
o patch `visual-preview-wait-v1` amplia a espera da candidata sem alterar replay
dos históricos anteriores. A revisão privada conserva resultados concluídos e
proveniência de ambos os modos visuais mesmo com execução desligada.

O ledger já possui teto mensal agregado de reservas OpenAI, além do teto por
tenant (`0049`). Valores incertos permanecem reservados. É controle das operações
que passam por esse ledger, não limite da fatura OpenAI nem cobertura de chamadas
externas ao fluxo. A guarda concreta já usa os tetos por tenant e agregado na
reserva; não é uma tabela ainda a criar. Resultado desconhecido exige prova/reconciliação;
lease vencido não demonstra que a chamada terminou. Não repetir nem trocar
provedor automaticamente após possível submissão paga.

O [desenho de atomicidade](../design/BL04-atomicity-proposal.md) registra as
lacunas e a ordem de locks existente; não copiar uma ordem comercial → visual
sem resolver as inversões atuais. Não há rede enquanto se mantém row lock.
Propostas anteriores de grants e retirada de consentimento por modalidade ficam
como histórico técnico, sem tornar novos controles de IA requisito do produto.

## BL04.2 — parte 3: primeira imagem real pelo produto concluída

O proprietário autorizou Café do Cedro com foto CC0 e logo, uma imagem e teto
total de **US$ 1**, sem publicação. A execução concluiu um feed `visual_ai`
1024×1280 com `gpt-image-2.5-flare-2026-09-08`, qualidade medium, Jev real,
guarda/claim/ledger, Temporal/worker e acabamento determinístico do kit/logo.
O JPEG foi obtido pela API autenticada e S3 privado; run `finished`, prévia
`completed`, candidata com decisão pendente e publicação nula. Evidência no
[relatório de 29/10](../evals/bl042-first-product-image-2026-10-29.md).

Foram **uma chamada OpenAI de imagem e duas interpretações Jev**, com estimativa
de uso de **US$ 0,029701** no conjunto. Não é fatura nem custo por peça aceita:
a reserva visual de **US$ 0,99** permanece `uncertain`, com custo efetivo
desconhecido (`actual_usd_micros=NULL`), sem crédito inferido
da resposta. A primeira interpretação retornou formato nulo e o baseline criou
story; o wrapper de autorização recusou esse formato antes de delegar ao HTTP,
com zero chamadas de imagem demonstradas. A reconciliação em zero dessa reserva
antiga e o término explícito do run preservaram tentativa, marcadores e auditoria.
Uma nova origem esclareceu foto/feed e legenda sob a mesma autorização; não
houve edição manual de roteiro, reenvio de imagem incerta ou aprovação/publicação.

A migration 0059 foi aplicada ao banco local para esse percurso. Flags
persistentes continuam desligadas, sem novos grants ou mudanças no código de
produção. Ingresso Meta e prova de canal continuaram sintéticos, com entrega de
candidata simulada: não é prova de WhatsApp completo nem homologação Meta.
Validação dirigida aprovada: 94 unitários e `make lint types` (151 módulos).
Owner listou/baixou o hash idêntico com geração desligada e limites zero;
acesso anônimo retornou 401. Os processos habilitados foram encerrados.
O último CI completo continua o da parte 2, sem repetição nesta execução.
Os testes C08/C09 permanecem a
evidência das suas demais condições; esta única imagem não as demonstra novamente.

## Próxima fatia de desenvolvimento

**Direção de 30/10/2026:** usar pedido, fatos, kit, acervo, skill adequada e
referências externas aceitas quando disponíveis para construir briefing e pedir
ao modelo a peça final completa. Conferir a peça produzida e oferecer trace
privado; não tratar texto no prompt como prova de que preço ou marca aparecem
corretamente. Pesquisa e seleção de concorrentes ainda não estão entregues. A
ideia posterior de sugerir até três referências e orientar seleção de fontes e
formatos do kit está registrada para estudo no
[plano de skills e referências](../design/skills-e-referencias-editoriais.md).
O proprietário adiou a evolução WhatsApp/Jev: quando a mensagem trouxer preço
diferente do catálogo sem dizer se quer alterá-lo, a decisão C18 é perguntar
antes de continuar. Extração do valor e pergunta específica ainda não existem;
priorizar agora a geração da peça, sem alegar que o conflito já é detectado.

A implementação local descontinua novas gerações de fundo/overlay e snapshota
`full_piece_v1` por prévia. Skill editorial, logo autorizada, fotos e um exemplo
do kit demo entram no pedido completo; o provedor devolve a peça inteira. O
trace é cifrado e owner-scoped; a API exige checklist humano por hash antes da
aprovação. Checagem automática da imagem, checklist no WhatsApp/web, múltiplos
fatos temporários, concorrentes e avaliação de qualidade real permanecem abertos.
Suporte real continua limitado a desenvolvimento/teste e desligado por padrão.

**Preparação de três cenários em 29/10:** foi ligada ao percurso visual uma orientação
experimental de skill para feed/story, selecionada por prévia somente em
desenvolvimento/teste e desligada por padrão. A migration 0060 adiciona ID/hash,
protegidos pela identidade do pedido e revalidados no preparo/acabamento. Naquela
etapa não integrava o briefing editorial completo; o caminho automático do
WhatsApp ainda não escolhe skill. O A/B local usou a mesma origem e segunda prévia selecionada
internamente. Três negócios e seis prévias passaram com provedores simulados e
PostgreSQL/Temporal locais; o evento de imagem entra já processado e a foto do
acervo é cópia dos mesmos bytes, sem provar webhook Meta ou retrieval entre fotos
distintas. O ensaio real subsequente gerou seis prévias com Jev e imagem reais:
todos os pares omitiram o preço confirmado solicitado. Naquele ensaio a skill
orientava a imagem e a copy seguia baseline. O contrato editorial real foi
alterado para solicitar ao modelo texto da arte, legenda e CTA, com vínculo a
fato confirmado ou preço válido do catálogo e rejeição sem fallback fixo. O
modo simulado continua separado. A barreira lexical daquele ensaio não verificava
sentido e não substituía revisão humana. O pedido de preço ainda não tem
interpretação estruturada que garanta sua inclusão; teste real do novo caminho
integral segue pendente.
[Evidência](../evals/three-business-visual-ab-2026-10-29.md).
Validação da correção com provedores simulados: `make ci` aprovado com 1.969
testes, 100% de linhas e branches, Ruff/formatação e mypy em 152 módulos.
Ensaio real isolado posterior produziu seis peças: preço em quatro artes, mas
não nas duas de manicure, e copy artificial em café/delivery. A skill permaneceu
restrita à imagem e cada par compartilhou a proposta; o executor não exercitou
seleção factual ou jornada completa. CI não repetido por orientação do titular.
[Evidência](../evals/editorial-copy-visual-after-2026-10-29.md).

1. **Skills para geração:** estudar e especificar as primeiras skills de feed e
   story; compará-las com o baseline em casos fictícios e integrar versões
   aprovadas à geração com kit, contexto e acervo pertinentes. No repositório
   separado `meu-braco-direito-skills`, há instruções iniciais para feed/story,
   quatro casos fictícios e protocolo de comparação. Validação estrutural e dois
   exercícios independentes passaram, sem comparação com baseline ou geração
   paga; a integração ao produto e a qualidade comercial continuam pendentes.
   Uma sonda exploratória posterior confrontou baseline isolado e saídas de
   agentes, com entradas e contratos diferentes. A skill de story não perguntou
   sobre serviços ambíguos; uma alteração dirigida e uma repetição independente
   corrigiram o caso observado. Não é comparação controlada nem prova de ganho.
   Ensaio pareado real de texto sob teto de US$ 5 foi interrompido na primeira
   tentativa incerta, sem saída e sem custo conhecido; ledger e hold preservados.
   A [evidência](../evals/skills-paired-attempt-2026-10-29.md) não autoriza
   reenvio ou avanço automático. Comparação controlada segue pendente.
   Um novo ensaio visual isolado, sob teto próprio de US$ 5, gerou duas peças
   de feed para caso fictício com e sem skill, mesma foto/kit/acabamento; duas
   chamadas textuais orientaram as cenas. Não usa o worker nem comprova ganho,
   aprovação comercial ou custo por peça aceita. [Evidência](../evals/skills-visual-comparison-2026-10-29.md).
2. **Pesquisa e referências externas:** estudar e implementar indicação do
   cliente e descoberta automática de negócios semelhantes em destaque; avaliar
   fontes, permissões, métricas e relevância antes de aplicar padrões à geração.
   Jev é hipótese a avaliar, não provedor escolhido. Referência não autoriza cópia;
   seu estudo pode começar após a comparação simulada das skills, sem esperar
   o fechamento integral do gate comercial BL04.3.
3. **BL04.3:** integrar padrões externos aprovados como referência e avaliar
   post/story pelo produto com titular e fontes autorizadas, incluindo revisão
   do feed já produzido. Medir pertinência, fidelidade, legibilidade, texto
   literal, rejeições, refações e custo por peça aceita. Uma chamada bem-sucedida
   ou um teste fictício não encerra esse gate.
4. **BL05:** WhatsApp como jornada principal de prévia, ajuste, aprovação e
   publicação simulada, incluindo proatividade sem nova mensagem. BL03.3 não
   bloqueia esta sequência. Novas chamadas precisam de autorização de gasto;
   a execução delimitada da parte 3 não habilita uso recorrente.

As fases, hipóteses e gates de skills e referências estão no
[plano editorial](../design/skills-e-referencias-editoriais.md). A escolha de
provedor para pesquisa e a viabilidade das fontes automáticas permanecem abertas;
o cliente indicar um perfil não substitui a descoberta automática pretendida.

C10, recuperação automática fora do redispatch, limpeza física de PUT incerto e
suporte operacional seguem como evoluções próprias, com exceções bloqueadas até
prova segura. Não são novos poderes concedidos nem autorização para duplicar
um efeito. Retenção pós-encerramento continua adiada, sem exclusão automática.

**Adiada em 29/10/2026:** recuperação exclusiva e auditada de staff para autor
sem acesso (C10), na evolução de gestão de acesso/suporte. A proteção que impede
outro owner de assumir ou descartar a pendência permanece entregue. Até a entrega
futura, conservar a exceção bloqueada. A [proposta](../design/BL04-staff-recovery-review.md)
fica como referência, sem aprovação de novas permissões. O adiamento permite
encerrar o recorte simulado validado; os demais gates da BL04/provedor real continuam.

## BL04.3 — qualidade e economia: pendente

As skills de feed/story devem ser estudadas, comparadas e integradas antes deste
gate, respeitando as verificações de fonte, acesso e orçamento existentes. O
trabalho com dados fictícios prepara a avaliação e não comprova aceite comercial.
Gerar ao menos um post e um story novos para um caso com fontes autorizadas;
revisar no celular com titular. Medir identidade, legibilidade, texto literal,
fidelidade de produto/local, rejeições, retrabalho, todas as tentativas e custo
completo por peça aceita. A hipótese econômica é R$ 99/mês e custo total máximo
pretendido de R$ 50 por cliente/mês, incluindo serviços, infraestrutura e suporte;
não foi demonstrada. Vídeo, motion e avatar não integram automaticamente essa oferta.

Um lugar/produto inventado não pode aparecer como fotografia documental do
negócio. Referência visual não comprova fidelidade por si só; texto, preço, CTA
e logo precisam de conferência literal. Cenas conceituais devem ser identificadas.
Os [casos fictícios de QA](../evals/manual-qa-negocios-ficticios.md) preparam
cenários, sem substituir os gates de qualidade e aceite.

## Evidência datada e histórico

- Parte 3, primeira imagem: uma chamada real de imagem, duas Jev e JPEG privado
  pelo fluxo do produto, sem aprovação/publicação e com reserva de custo incerta.
  Meta de entrada/canal e entrega de candidata permaneceram simuladas. Estimativa
  total US$ 0,029701, sem fatura ou gate de qualidade comercial. Validação dirigida
  aprovada: 94 unitários, lint/types (151 módulos) e leitura/hash com geração
  desligada; CI completo da parte 2 não repetido.
  [Evidência](../evals/bl042-first-product-image-2026-10-29.md).
- Parte 2, conexão completa: `make ci` aprovado com **1.914 testes**,
  **100% de linhas e branches** (9.394 statements, 2.582 branches), Ruff/formatação
  e mypy (151 módulos). Web: **375 testes**, **100% nas quatro métricas**,
  build/formatação e **quatro jornadas Chromium** na árvore final. O percurso API →
  dispatcher → Temporal → runner/guarda → adapter com HTTP simulado → acabamento
  → prévia privada exercita modo persistido, fontes, versão/hash, revisão e
  orçamento; complementos cobrem resultado incerto sem nova submissão,
  continuidade/preservação e leitura com execução desligada. A migration 0059 foi
  aplicada somente ao `_test`; sem chamada paga ou novos grants.
- Parte 1, guarda concreta: `make ci` aprovado com **1.829 testes**, **100% de
  linhas e branches** (9.284 statements/2.550 branches), Ruff/formatação e mypy
  (149 módulos), PostgreSQL `_test`/roles restritas e Temporal locais. Prova de
  fontes/roteiro, finanças/acesso, relink por outro owner, validade factual após
  locks, claim única, resposta tardia e commits incertos. Web: 365 testes/100% nas
  quatro métricas, build/formatação e três jornadas Chromium. Sem chamada paga
  ou novos grants; à época, a próxima entrega era modo/API e wiring da parte 2.
- Recuperação sem reserva e concorrência, 29/10: `make ci` aprovado com 1.688
  testes, 100% de linhas e branches (8.989 statements, 2.462 branches), Ruff,
  formatação e mypy. PostgreSQL `_test`/roles restritas e Temporal locais; crash,
  confirmações perdidas, tentativa tardia, RLS/autoria, orçamento concorrente e
  custo tardio, prazos após locks e kit/logo. Nenhuma chamada paga, mudança web
  ou liberação da guarda real. Limites do consumidor de recuperação acima.
- Entrega anterior de admissão/continuidade/preservação: novos testes unitários e
  PostgreSQL para fontes e transição comercial concorrentes, plano vencendo após
  admissão, retenção/proveniência, prazos de aprovação e recusa de outro owner.
  `make ci`: 1.642 testes aprovados, 100% de linhas e branches (8.942 statements,
  2.446 branches), Ruff/formatação e mypy. PostgreSQL `_test` com roles restritas
  e Temporal locais; nenhuma chamada paga ou integração visual real habilitada.

- [Ensaio de feed de 27/10](../evals/bl042-guarded-synthetic-feed-2026-10-27.md):
  uma chamada com dados fictícios/CC0, US$ 0,026272 estimados; alterou logo e
  pontuação. Não usa worker do cliente nem comprova fatura, margem ou fidelidade.
- [Ensaio com acabamento de 28/10](../evals/bl042-synthetic-brand-finish-2026-10-28.md):
  US$ 0,020615 estimados, também isolado. A autorização de até US$ 1 para o ensaio
  fictício é histórica, não franquia comercial nem liberação de novos gastos.
- Aceite único: suíte backend de 1.583 testes e complemento de 24 execuções
  (sete testes novos), com cobertura final agregada de 100% de linhas e branches;
  web com 360 testes/cobertura integral, build e três jornadas Chromium. Serviços
  locais RLS/Temporal e efeitos externos simulados. Ver [CHANGELOG](../CHANGELOG.md).
- As decisões anteriores de descarte imediato de prévias, expiração dos envios
  WhatsApp e controles individuais de IA foram substituídas. As evidências originais,
  datas, contagens e propostas rejeitadas permanecem no snapshot desta fase e nos
  evals/changelogs; não são pendências de produto a reintroduzir.
