# BL04 — contexto seletivo e produção visual com IA

## Ajuste da origem de pesquisa — 04/11/2026

A web usa o endereço próprio salvo como única fonte dos campos da origem por
endereço, todos somente para leitura. Sem cadastro, apresenta a orientação para
preencher **Endereço do negócio** e impede salvar essa origem. Mudanças no
cadastro atualizam a exibição e o próximo envio explícito das preferências, sem
salvamento ou consulta automáticos. GPS confirmado, raios e ciclos são preservados.
Indicações de outras regiões seguem pelo @ manual em **Perfis que inspiram seu
negócio**, conforme decisão do titular; não se acrescenta outro endereço de busca.

Critérios de validação: campos não editáveis; cadastro obrigatório para origem por
endereço; valores persistidos prevalecem sobre uma origem antiga; atualização do
cadastro refletida sem salvar automaticamente; GPS e indicação manual preservados.
Testes e validação da interface são registrados no changelog da web.

A mensagem de busca indisponível é controlada por `discovery_available`, vindo da
prontidão operacional da API. As flags locais persistentes de descoberta,
geocodificação e análise seguem desligadas. Credenciais presentes não substituem
a configuração de execução/custos usada temporariamente no piloto. Esse estado
é independente do endereço e do prazo semestral. Este ajuste não ativa chamadas
pagas; o próximo trabalho de qualidade continua sendo BL04.3.

## Referências — gate de fechamento em 04/11/2026

As fatias de descoberta, seleção, análise e projeção na geração estão integradas
localmente. A 0109 foi validada contra a seleção real da 0108 em 22 integrações
PostgreSQL, além de 46 unitários com cobertura integral do guardião. A política
v2 do piloto redistribui os limites por fornecedor dentro dos mesmos US$ 5,
preservando o consumo. A interface passou em 508 testes/100%, TypeScript, build
e navegação em Chromium. O banco local está em 0111 após backups verificados.
O CI conjunto passou: 4.734 testes, 100% de linhas/ramos, Ruff e mypy.
A análise de referência manual do ensaio gerou nove
padrões a partir de onze publicações e quarenta imagens, com estado parcial e
snapshot de geração conferidos. A fórmula de reputação
continua experimental, conforme decisão do titular.

No piloto real, o Google expôs campos opcionais que o parser rejeitava. A
[correção](../design/google-places-address-components.md) foi validada em 160
testes e na nova resposta real de 20 candidatos, com três destaques Jev salvos.
As tentativas anteriores conservaram suas reservas. O banco local foi atualizado
até 0111 após backups verificados; análise e CI concluídos no escopo atual.

A descoberta real publicou dez candidatos com três destaques; o aceite iniciou
o ciclo. O primeiro feed foi coletado com sucesso, mas não gerou padrões pelo
filtro inicial de autoria/formato. O titular resolveu a entrevista: somente
autoria direta, incluindo capa/legenda de vídeos e Reels. O adapter foi atualizado
e passou em 164 unitários/100% e cinco integrações, incluindo ausência de acesso
ao arquivo de vídeo e padrões no snapshot. O CI integral também passou.
O piloto expôs contabilização preliminar do Apify: espera de trinta segundos
validada em 275 testes/100%; revisão auditável de recibos 0111 validada em 38
integrações e 12 unitários/100%. Os onze recibos foram reconciliados no mesmo
piloto de US$ 5, preservando reservas e histórico. O total comprometido após a
análise manual é US$ 0,455502, incluindo holds ainda não liquidados de Google/Jev.
Decisões de conteúdo resolvidas; [evidências](../evals/reference-feature-pilot-2026-11-04.md).

Atualizado em **29/10/2026**, com a primeira imagem real pelo produto concluída
na parte 3 e a priorização de skills de geração antes da avaliação BL04.3.
Estado: **em implementação local**, sem aprovação
comercial. Este é o contrato vigente da fase, junto ao [SDD geral](../SDD.md), à
[trilha BL](BL-brand-library.md#bl04--recuperar-contexto-e-produzir-uma-peça-nova)
e ao [registro de decisões](../DECISIONS.md). A versão anterior foi preservada
[integralmente no histórico](../history/2026-10-28-pre-documentation-reconciliation/phases/BL04-context-and-ai-production.md);
pendências datadas de permissões por fornecedor nesse histórico não são novas
etapas da jornada contratada.

A [análise da jornada WhatsApp e orquestração](../design/arquitetura-jornada-whatsapp.md)
registra o encadeamento atual, as fronteiras entre estados de domínio e Temporal,
as partes simuladas e pontos para discussão futura sobre organização; não altera
o escopo desta fase nem decide uma extração de serviços ou repositórios.

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
em ensaio e implementar recomendações para aceite do cliente. Fonte,
disponibilidade de métricas e custos da descoberta
automática ainda precisam ser demonstrados; não inferir acesso do Jev ao Instagram.

Foi entregue a configuração inicial do alcance de referências: a web oferece
raios locais de 5, 20 e 50 km, endereço manual ou ponto confirmado do dispositivo;
raios anteriores de 1–50 km são preservados. Preferências nacionais anteriores
ficam visíveis até substituição explícita, sem nova opção nacional. A origem
manual ainda aguarda geocodificação/confirmação; não há busca automática real
de concorrentes nesta fatia. A preferência permanece no contexto versionado e é
omitida dos prompts editorial e visual. A indicação manual, o snapshot para
briefing/trace e a revisão visual da tela foram implementados localmente; o perfil
indicado não é verificado nem analisado automaticamente.
No serviço, novas alterações só aceitam os três raios locais. Valores legados
iguais ou omitidos são preservados, `null` explícito os remove, e replay e
alterações pendentes já admitidas mantêm compatibilidade.

Palavras do negócio e características gerais foram adicionadas ao contexto
versionado. A interface removeu os formulários de fatos livres e promoções;
fatos legados do contexto não alimentam novas peças e novos snapshots editoriais
ignoram promoções antigas do catálogo. Snapshots antigos mantêm sua política e
registros físicos históricos não foram purgados. O fluxo WhatsApp/Jev de ofertas,
horários, revisões e cálculo de descontos ainda não foi entregue.

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

O banco de desenvolvimento foi atualizado da revisão 0059 à 0099 em 03/11,
após backups privados com leitura integral verificada. A API iniciada antes da
0099 precisa de reinício para reconhecer a nova revisão e confirmar prontidão.

**Direção de 30/10/2026:** usar pedido, fatos, kit, acervo, skill adequada e
referências externas aceitas quando disponíveis para construir briefing e pedir
ao modelo a peça final completa. Conferir a peça produzida e oferecer trace
privado; não tratar texto no prompt como prova de que preço ou marca aparecem
corretamente. A indicação manual foi implementada localmente; pesquisa e aceite de
sugestões de concorrentes ainda não estão entregues. A
ideia posterior de orientar seleção de fontes e
formatos do kit está registrada para estudo no
[plano de skills e referências](../design/skills-e-referencias-editoriais.md).
Conforme C18, uma oferta explicitamente promocional informada no WhatsApp é
fato para aquela criação e suas revisões. Exemplo: R$ 19,90 no pedido com preço
de catálogo R$ 25 não exige confirmar a diferença nem altera o catálogo. Para
um desconto percentual é necessário preço válido de catálogo; informação
ausente ou ambígua exige esclarecimento. Promoções, ofertas e horários não terão
cadastro na interface; o campo simples de características gerais permanece.
O titular autorizou remover informações antigas dessa área sem preservar
histórico. Essa jornada ainda não está implementada: o WhatsApp/Jev não extrai
e vincula integralmente os fatos, e o código de promoções do catálogo permanece
legado; novos snapshots editoriais ignoram essas promoções. Não presumir que a
peça atual já aplica a regra.

A implementação local descontinua novas gerações de fundo/overlay e snapshota
`full_piece_v1` por prévia. Skill editorial, logo autorizada, fotos e um exemplo
do kit demo entram no pedido completo; o provedor devolve a peça inteira. O
trace é cifrado e owner-scoped; a API exige checklist humano por hash antes da
aprovação. Checagem automática da imagem, checklist no WhatsApp/web, múltiplos
fatos temporários, análise dos concorrentes e avaliação de qualidade real permanecem abertos.

A busca começa no raio solicitado, uma vez por raio por ciclo, com até dez
candidatos por raio, sem prometer 30 negócios únicos; falha comprovada não
consome tentativa. Pela decisão de 04/11, Google vazio amplia automaticamente
de 5 para 20 e depois 50 km. Se todos vierem vazios, permitir nova tentativa
sem iniciar seis meses; os limites financeiros continuam valendo para a sequência. O cliente verá até dez candidatos elegíveis, com até três
recomendações do Jev destacadas com critérios e nota quando houver candidatos suficientes,
e escolherá de uma a três entre os exibidos, podendo combinar raios. A primeira
confirmação inicia um prazo comum de seis meses; cada raio pode ser pesquisado
uma vez no ciclo, mesmo após confirmação em outro raio. Todos ficam disponíveis
ao fim do prazo original; mudar endereço ou segmento não libera raio já pesquisado.
Trocas não renovam o prazo e a seleção permanece até outra confirmação; as
referências ainda selecionadas de ciclos anteriores podem ser combinadas com as novas. @ manuais
são adicionais. O Apify não deve repetir consultas bem-sucedidas a negócios já
encontrados durante o ciclo, mas pode consultar negócios novos de outro raio e
repetir tentativa que falhou sem retornar o perfil. O titular quer
guardar até dez negócios apresentados por pesquisa, com Place ID, nota própria
e perfis disponíveis. Confirmou que apenas Place ID será persistido dos dados
Google, usando estrelas e contagem somente como entrada para a nota; confirmou
também que a nota própria e a associação dos perfis do Apify podem ser guardadas.
Até vinte Place IDs/notas podem ser guardados temporariamente para recuperação,
com filtro de semelhança antes do cálculo; a lista exibida continua até dez.
O nome exibido virá do Apify quando houver; na ausência, mostrar o perfil ou
outro identificador disponível, sem persistir o nome fornecido pelo Google.
O titular esclareceu que cada rodada forma até dez candidatos pela mesma regra a
partir da nova resposta Google. Negócio reencontrado usa a nota mais recente na
nova lista, com notas de pesquisas anteriores preservadas no histórico. Se uma
referência escolhida ficar fora dos dez, o cliente decidirá se a mantém; essa
jornada ainda não existe no fake. Nesta primeira versão só serão considerados perfis do Instagram;
um único perfil retornado pelo Apify será usado automaticamente, sem exigir
confirmação. Com várias opções, usar o principal indicado ou, se não houver, o
primeiro retornado; o cliente pode informar outro @ se estiverem incorretas. O titular deseja
analisar via Apify até 20 publicações recentes do feed por perfil, incluindo imagens
e legendas públicas acessíveis quando disponíveis. Somente padrões extraídos serão
guardados, sem cópias de posts; acesso parcial será utilizado e identificado como
tal, e os padrões serão atualizados automaticamente a cada seis meses. Jev destacará até três negócios considerando
semelhança e nota; a interface mostrará critérios e nota, sem frase livre. Candidatos
com semelhança incerta ficam fora; não há nota mínima de corte.
A pesquisa nacional não será oferecida. Negócios sem @ devem ser
exibidos e o cliente poderá informar o perfil. O @ informado já é uma referência
escolhida, mas não se deve afirmar que foi verificado. Falha ou limite de acesso
a perfil público deve ser informado e permitir nova tentativa posteriormente.
Essas capacidades automáticas ainda não existem no produto real. Os eventos transacionais de
criação e remoção de referências ficam pendentes na outbox, sem consumidor;
seu acúmulo deve ser resolvido antes da operação continuada. Places é a fonte da
busca inicial e Apify é previsto para enriquecimento; custos, acesso,
correspondência e cobertura ainda precisam de integração. A infraestrutura fake, desligada
por padrão, exercita via Temporal os raios 5/20/50, a confirmação de uma a três
fixtures anônimas, pesquisa de raios ainda não usados durante os seis meses,
troca sem renovação, preservação da
seleção, compensação de falhas e reconciliação de autor revogado. Isso não cria
nem valida candidatos reais. Os adapters Google Places multitype e Geocoding estão
isolados/desativados e ainda não integrados ao produto;
geocodificação real e confirmação do ponto manual continuam necessárias para
raio; avaliações não medem engajamento. Um adapter de consulta de perfil via
Apify também foi preparado isoladamente e permanece desativado, sem integração
ou guardião real. A indicação de perfil não encontrado, com fonte não comprovada,
é inconclusiva; o adapter não comprova associação ou análise dos posts. A
plataforma conserva apenas padrões derivados; não há etapa obrigatória de
exclusão dos armazenamentos internos do Apify, conforme decisão do titular. Adapters isolados e
desativados para enriquecimento via Place ID no Apify e para mapeamento de tipos
fornecidos com Jev não comprovam titularidade, oficialidade da taxonomia ou
qualidade semântica; precisam de guardiões concretos e integração. Ver
[simulação](../design/reference-discovery-simulation.md).
Durante a implementação das fases seguintes, foram preparados o vínculo exato
do pedido Places e da credencial à intenção e à reserva, o teto compartilhado
do ensaio, e uma cadeia Google → Jev → filtro e gravação privada exercitada
somente com HTTP simulado. A reserva do Jev e o lote filtrado têm identidade
durável, RLS e proteção contra reenvio; até dez posições finais têm armazenamento
privado sem publicação. Há também contrato puro para projetar aprendizados, sem
coleta nem conexão à geração. A admissão da pesquisa real, a recomendação de três,
o Apify, publicação e conciliação permanecem
pendentes; estas preparações não habilitam provedores nem concluem uma fase real.
A leitura interna das listas publicadas e seleções foi testada com dois titulares,
RLS e histórico; ainda não está disponível no produto.
A admissão privada por localização de dispositivo e os ciclos reais separados
do fake foram preparados e testados sem despacho. Uma função interna ainda sem
grant libera o raio se nenhuma intenção de fornecedor existir; outros estados
conservam o raio até comprovação adequada. A seleção real que inicia os seis
meses continua sem acesso ao produto.
O titular confirmou raios 5/20/50 e início manual da próxima busca quando o
prazo terminar. Referências anteriores fora dos dez exigem decisão apenas no
início de nova rodada, sem repetir a pergunta para outro raio do mesmo ciclo.
O próprio negócio será excluído das sugestões, identificado por
nome e endereço quando houver correspondência clara e com confirmação apenas na
dúvida. Um comparador conservador foi testado isoladamente; vínculo e integração
ainda faltam. Empates na décima posição serão resolvidos pelo Jev por
semelhança; os três destaques combinarão semelhança e nota. Os titulares ativos
compartilharão as referências. Endereço e coordenadas do próprio negócio devem
permanecer no cadastro. O aprendizado abrangerá
tom, temas, formatos e elementos visuais, considerando todas as imagens
acessíveis dos carrosséis; perfil novo é analisado após confirmação e atualizado
a cada seis meses.
Essas regras ainda não estão integralmente implementadas.
O desempate possui adapter simulado, ainda sem orçamento, prova das candidatas
e publicação. Na abstenção, usar a ordem da resposta Google; a conclusão de
semelhança do Jev poderá ser guardada para recuperação sem nova pesquisa.
Um carregador restrito de contexto confere identidade, evento e versão vigente
e retorna somente dados necessários em memória; falta conectá-lo à activity.
Um adapter separado prepara coleta de até 20 publicações de imagem/carrossel do
feed por perfil usando HTTP simulado. Imagens e legendas retornam apenas em memória;
análise e conexão com efeitos pagos permanecem pendentes. O titular optou pelo
fluxo de chamada/resposta sem etapa obrigatória de exclusão no fornecedor; a
plataforma não persistirá as publicações coletadas.
O titular escolheu testar pontuação de 0 a 10 baseada em nota e quantidade,
sem armazenar os campos originais. A restrição anterior de não pontuar menos de
dez avaliações foi revista: pode-se calcular a partir de uma avaliação; sem
média ou avaliações disponíveis, o código atual não pontua nem inclui o
candidato, conforme confirmação do titular.
O titular confirmou em 03/11 que continuará testando e calibrando a
segunda fórmula; ela penaliza pouca evidência sem elevar a média e tem peso
provisório. A descoberta fake
aplica semelhança predefinida na fixture e grava a nota integral e as versões
da fórmula e fixture por pesquisa antes da leitura ordenada. Isso não implementa
avaliação real pelo Jev nem ordenação de candidatos reais.
Ver [avaliação](../evals/reference-reputation-eval-2026-10-31.md).
A fórmula final ainda não foi definida e a nota própria ainda não foi integrada
à descoberta real. Jev deverá eliminar candidatos inadequados antes de
pontuar os restantes. O titular escolheu limite financeiro por pesquisa, por
fornecedor e mensal total em UTC; valores e ativação continuam explícitos.
Política compartilhada, reservas e consumidores de efeitos fictícios foram
testados isoladamente, com retenção de resultado incerto e sem política ativa
por padrão. Isso não integra providers reais nem comprova conciliação de fatura;
parâmetros e identidade reais, chave HMAC versionada e provisionamento restrito
continuam pendentes. Trocar a chave fictícia com operação pendente interrompe o
processamento até restaurar a chave anterior, sem liberar uma reserva existente.
Na [prova pontual Nearby](../evals/google-nearby-order-probe-2026-10-30.md),
`POPULARITY` não correspondeu simplesmente a ordenar pela contagem quando a nota
era igual. As reservas Places somam US$ 0,280, sem comprovar fatura; o registro
da prova não salvou nomes ou respostas brutas.
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
2. **Pesquisa e referências externas:** completar a descoberta automática de
   negócios semelhantes em destaque além da indicação manual já implementada; avaliar
   fontes, permissões, métricas e relevância antes de aplicar padrões à geração.
   Jev deve avaliar semelhança e eliminar candidatos inadequados antes de aplicar
   a pontuação aos restantes e explicar até três recomendações destacadas entre
   os até dez candidatos exibidos, com fonte e uso permitidos;
   isso ainda não está implementado e não mede engajamento social. Referência não autoriza cópia;
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
viabilidade e os termos das fontes automáticas permanecem abertos;
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

### Ponto de retomada — 04/11/2026

**Próximo trabalho: preparar a avaliação BL04.3 em quatro passos abaixo.** A
implementação local das referências está concluída até 0111, com 4.734 testes e
100% de linhas/ramos. As skills iniciais de feed/story já estão integradas. O
piloto de referências comprovou descoberta, escolha, análise e padrões no
snapshot, mas não gerou nem avaliou uma peça final usando esses aprendizados.
A nova rodada comparativa de qualidade ainda não foi executada.

O contexto a avaliar reúne pedido, informações do negócio, acervo, kit, skill e
aprendizados das referências. Referências orientam a criação; fatos, produto,
local, preço, logo e identidade continuam vindo das fontes do próprio negócio.
Testes de software aprovados não demonstram ganho criativo ou aceite comercial.

### Quatro passos da avaliação

1. **Conferir os aprendizados extraídos.** Inventariar as referências escolhidas,
   versões de associação, padrões, datas e cobertura da análise. Conferir se os
   padrões de tom, temas, formatos e elementos visuais descrevem as evidências
   acessíveis. Registrar concordâncias, erros e pontos não verificáveis. Não
   inventar conteúdo para um perfil indisponível nem arquivar suas publicações.
   Saída: quadro de revisão dos aprendizados aptos a entrar no ensaio.
2. **Gerar uma comparação controlada com e sem aprendizados.** Preparar casos
   de feed e story com o mesmo pedido, contexto, acervo, kit, versão da skill,
   modelos e configurações nos dois braços. A variável do par é a inclusão dos
   aprendizados, tanto no editorial quanto no visual. Usar fixtures autorizadas
   e as guardas do produto, sem enfraquecer snapshots ou revalidação de fontes.
   Registrar inputs versionados, operações, peças e custos de cada tentativa.
   Uma única amostra por braço é exploratória e não comprova ganho geral.
   Saída: pares comparáveis de arte e texto, com limites do ensaio explícitos.
3. **Avaliar as peças lado a lado com o titular.** Revisar no celular identidade,
   fidelidade ao produto/local, clareza e literalidade do texto, preços, CTA,
   logo, legibilidade, composição, originalidade e utilidade para o pedido.
   Registrar preferência, aprovação, rejeição ou necessidade de ajuste, com
   motivos. Avaliação automática pode auxiliar, mas não substituir esse aceite.
   Saída: revisão humana por peça e comparação documentada dos dois braços.
4. **Corrigir os problemas medidos e repetir.** Ajustar briefing, seleção de
   contexto ou instruções conforme os erros observados, em fatias revisáveis.
   Reexecutar os casos afetados com versões rastreáveis, preservando tentativas
   anteriores e registrando rejeições, refações, latência e custo completo por
   peça aceita. Distinguir reserva, estimativa e custo informado; nunca reenviar
   uma operação incerta como se fosse uma tentativa nova. Saída: correções
   validadas e relatório que explicite ganho, regressões e limites encontrados.

### Primeiro trabalho do próximo chat

Ler as instruções dos dois repositórios e inspecionar Git/código, preservando as
alterações existentes, inclusive as já staged. Começar pelo inventário dos casos,
aprendizados e executores de avaliação disponíveis; preparar o quadro do passo 1
e um plano revisável do passo 2 antes de qualquer chamada paga. Não reimplementar
a feature de referências nem retomar pendências de seus marcos históricos.

O plano deve informar casos, fontes/kit, formatos, quantidade de pares/tentativas,
modelos/configurações, critérios de aceite e estimativa de gasto. Apresentar as
escolhas de produto ainda abertas em entrevista, como solicitado pelo titular.
Conferir autorização e orçamento aplicáveis antes de executar: os US$ 5 do piloto
Google/Apify/Jev não autorizam esta nova rodada de geração de imagens. Tetos dos
ensaios antigos não devem ser renovados ou reaproveitados automaticamente.
Preparação local e documentação podem avançar enquanto essas escolhas são resolvidas.

Reutilizar aprendizados persistidos quando adequados, sem reiniciar ciclos,
reescrever resultados históricos ou refazer Google/Apify apenas para QA. No piloto,
a referência sugerida ficou indisponível e a manual tem nove padrões com análise
parcial; essa distinção deve continuar explícita. Flags persistentes permanecem
desligadas. O banco local está em 0111; testes de banco continuam exclusivamente
em bases novas `_test` com roles restritas, sem limpar o banco da aplicação.

Consultar antes de preparar o ensaio:

- [Piloto de referências e seus limites](../evals/reference-feature-pilot-2026-11-04.md).
- [Comparação editorial/visual anterior](../evals/editorial-copy-visual-after-2026-10-29.md):
  texto artificial, CTA e preços exigiram atenção; os pares compartilhavam a
  proposta editorial e variavam apenas o visual, limitando a conclusão.
- [Tentativa pareada interrompida](../evals/skills-paired-attempt-2026-10-29.md):
  conservar a operação incerta e sua reserva; não reenviar para iniciar a nova rodada.
- [Kit de QA Ateliê Aurora](../evals/kit-atelier-aurora-v1/README.md): existe como
  fixture independente, mas ainda não está no catálogo/executor; não presumir
  essa integração nem usá-lo como se já estivesse disponível no produto.

Registrar o plano e os resultados em um relatório datado em `docs/evals/`, com
links aos artefatos privados autorizados, sem credenciais ou publicações das
referências. Avançar automaticamente entre os quatro passos dentro do escopo e
orçamento autorizados, avisando ao concluir cada passo. Dúvidas de produto devem
ser feitas em entrevista. BL05 continua posterior à avaliação BL04.3.

### Critérios de fechamento preservados

O trabalho com dados fictícios prepara a avaliação e não comprova aceite comercial.
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

## Cadastro de endereço próprio — 04/11

A API autenticada de endereço próprio conserva versões e exige controle de
concorrência e identidade de operação. Ela estabelece a origem declarada pelo
titular, sem copiar GPS ou origem de pesquisa. Geocodificação, persistência do ponto
comprovado e vínculo à identidade da busca permanecem pendentes; nenhuma chamada
externa foi habilitada. Ver [contrato](../design/business-address.md).

## 04/11/2026 — Classificação prévia de atividade

Taxonomia Google Table A versionada e adapter Jev pré-Google implementados
com uma requisição, código de tipo fechado e retorno de uso. O vocabulário
contém 478 códigos e foi conferido em fonte oficial; não usa `restaurant`
como padrão. Incerteza de categorias não escolhidas não impede um match válido.
Validação local: 66 testes unitários, 100% linhas/ramos dos dois módulos, Ruff
e tipagem estrita; sem efeitos pagos. Integração do guard e execução 0106 e
ensaio semântico real permanecem gates da descoberta completa.

### Fatia0103 — endereço, geocodificação e identidade própria

A API de endereço passou a ter início, consulta e confirmação de geocodificação,
com relay/Temporal e orçamento persistido. O ponto preciso é aceito automaticamente;
resultados ambíguos aguardam o titular. O endereço próprio e suas coordenadas
continuam no cadastro, e a origem manual de busca pode reutilizá-los com o custo
incluído na mesma pesquisa. O cadastro próprio é obrigatório na admissão real;
nome/endereço têm vínculo HMAC e são revalidados no carregamento, nos claims da
busca e na publicação. A validação usa serviços locais e transportes HTTP falsos,
sem gastar o teto autorizado. Ver [contrato](../design/business-geocoding.md).
A descoberta completa ainda precisa chamar o loader de identidade e tratar o
comparador, a ambiguidade, perfis e aprendizado; não declarar a feature concluída
por causa desta integração de endereço.

## Retomada 04/11 — integração até 0105

Resultados reais e seleção têm rotas autenticadas; publicação privada preserva
IDs/notas e exige revisão de escolhas ausentes só no início da nova rodada.
Correção manual de perfil possui versão, replay e auditoria. Endereço/geocodificação
e identidade própria foram conectados pela 0103. A execução completa Google →
Jev → Apify → publicação ainda está em integração, não concluída.

O custo por pesquisa agrega titulares; run Apify persistido permite consultar a
mesma coleta e reconciliar seu custo terminal sem novo POST. Adapter Compass
usa contrato oficial, build explícita e limite por execução. Os testes dirigidos
passaram; a suíte integral inicial terminou com 3.993 aprovados, duas falhas e
99,38% de cobertura, em correção. Falta validar a árvore final, conectar análise
de publicações/atualização semestral e aprendizados à criação, e executar o ensaio
fictício autorizado de até US$ 5 quando as credenciais locais estiverem disponíveis.

### Transporte real de feed, 04/11

Adapter Instagram e downloader de imagens preparados para o executor, com
network opt-in e controles de custo/identidade/limites. 357 unitários passaram
com 100% dos cinco módulos, Ruff e mypy aprovados. Publicações continuam apenas
em memória. Persistência de aprendizados, agenda Temporal semestral e uso na
criação ainda estão em implementação. Google vazio terá ampliação automática
5 → 20 → 50; ausência nos três permite nova tentativa sem iniciar seis meses, conforme
entrevista. A integração completa dessa ampliação permanece pendente.

### Configuração do piloto de referências, 04/11

O script `scripts/configure_reference_pilot.py` prepara a política local e o
piloto acumulado de US$ 5, sem zerar consumo ou habilitar fornecedores. Plano
por padrão; aplicação exige banco local/admin separado e preserva configurações
divergentes. 14 unitários e três testes SQL aprovados; execução real ainda pendente. Ver
[operação](../design/reference-pilot-operations.md).

## Revisão do baseline — 04/11/2026

A [retomada do CI](../evals/ci-resume-2026-11-04.md) identificou código morto
após C17/C18. Criação local permanece recusada, com auditoria/fence do job
legado e leitura privada histórica preservados. Geração editorial mantém o
percurso obrigatório de catálogo/skill e trace, sem alternativa sem skill
inacessível. Prova de role aceita o login restrito efetivamente configurado;
Temporal conserva timeout de 45s e diagnóstico apenas de estados/códigos.
3.555 testes relacionados passaram; o gate integral de 100% segue pendente.

### Banco local e leitura de referências, 04/11

Banco de desenvolvimento atualizado de 0099 para 0105 após backup privado
`.local/backups/pre-reference-20261104-111303-372421.dump`, com índice do arquivo
validado pelo pg_restore da mesma versão. A leitura de referências do negócio
informado passou usando runtime restrito e autorização de titular ativo. Isso
valida o serviço/banco; a sessão autenticada do navegador ainda não foi repetida.
O banco da aplicação não foi usado como banco de testes.

### Análise estruturada de publicações, 04/11

O adapter Jev aceita legenda e/ou imagem em memória e devolve apenas códigos
de um vocabulário próprio. A agregação gera até nove padrões gerais de tom, temas,
formatos e elementos visuais, sem conteúdo das publicações. 65 testes passaram
com 100% de linhas e branches nos dois módulos novos; Ruff e mypy aprovados.
Persistência, agenda de seis meses e uso no gerador permanecem em integração.
O teto local acumulado de US$ 5 foi configurado; flags persistentes continuam
desligadas e não houve chamadas pagas nesta retomada.

### Fatia 0107 — identidade própria e busca vazia

Implementados: conclusão de identidade atômica com a evidência sanitizada; revisão compartilhada por titulares; exclusão antes do ranking/publicação; ampliação automática de respostas Google vazias; orçamento agregado por família; cache entre raios; resultado vazio terminal e retry sem iniciar ciclo não confirmado; histórico preservado. Estado canônico de família inclui a busca atual, sem inferência da UI.

Validação local usa PostgreSQL exclusivo `_test`, logins restritos e fornecedores simulados. Upgrade/downgrade vazio foi exercitado. Testes cobrem confirmação por segundo titular, rejeição de viewer/revogado, rollback atômico, exclusão antes do ranking, cadeia 5/20/50, limite financeiro da cadeia e replay depois de liberar o head. A entrega final continua condicionada à integração Temporal completa, análise de publicações/agenda e CI integral; esta fatia não demonstra chamada paga real.

Validação concluída da fatia: oito integrações e 45 unitários aprovados; 100% de cobertura em 149 linhas/30 ramos dos cinco módulos, mypy e Ruff. Roundtrip vazio 0107 → 0106 → 0107 aprovado. Cache compartilhado mantém dados históricos sem expor tokens.

### Execução integrada da descoberta, 04/11

0106+0107 conectam admissão, Temporal, Google, Jev, Apify e publicação sob o
ledger existente. A API recebe operação e carrega contexto/raio do servidor;
retomada comprovada do Apify não repete Google/Jev. A tela usa o estado canônico
da família de raios. Flags persistentes continuam desligadas. A validação dirigida
passou em 57 testes, incluindo 17 integrações, com cobertura integral dos módulos
novos de execução; adapters e wiring passaram nos recortes próprios. CI integral
e ensaio pago permanecem pendentes. Veja docs/design/reference-discovery-execution.md.


### Referências escolhidas na geração — fatia 0110

Novas propostas capturam a seleção canônica e os aprendizados da versão exata
do perfil em `reference_generation_snapshot`, separado do histórico manual.
Briefing editorial e peça visual usam a mesma cópia imutável. Ausência de análise
e cobertura parcial permanecem explícitas; notas internas e semelhança orientam
a seleção e não autorizam afirmações comerciais. Posts, legendas e imagens de
terceiros não são armazenados nem enviados como referências visuais.

Retirada ou troca de perfil bloqueia novo efeito que utilizaria a associação
antiga; uma alteração durante o efeito impede aceitar o resultado editorial.
A revalidação não substitui a cópia histórica. Prévias concluídas e traces
continuam acessíveis pelas regras existentes. Propostas legadas com coluna
nula conservam o fingerprint e o significado de suas indicações manuais.
Não há truncamento silencioso a32 referências; o limite de tamanho do pedido
editorial continua sendo conferido antes da reserva.

Contrato e validação em [integração de referências na geração](../design/reference-generation-context.md).
177 testes unitários e 13 casos PostgreSQL passaram nos recortes desta fatia,
incluindo leitura 0108 e geração visual com HTTP simulado. A agenda completa e
o CI integral continuam pendentes; essas provas não demonstram qualidade comercial.

### 0108 — seleção, persistência e atualização dos aprendizados

A análise passa a ter associação de perfil, janela e evento duráveis derivados
da seleção real. Perfis manuais e sugeridos escolhidos usam a mesma autoridade;
correções de candidatos não selecionados não coletam publicações. Remover ou
trocar o perfil invalida a janela anterior antes de outro efeito. A agenda
semestral deriva do aceite, e resultados mantêm somente padrões próprios
comprovados, nome oportunista Apify e metadados. Captura/revalidação para geração
e leitura de status não confundem perfil escolhido com análise concluída.
As provas locais usam PostgreSQL isolado, roles restritas e fornecedores simulados.
Integração do executor, snapshot editorial/visual e tela vem nas fatias adjacentes;
ensaio real controlado e qualidade comercial continuam gates próprios.

### Aprendizados das referências na API e na jornada, 04/11

O GET autenticado `reference-learnings` entrega somente os estados, datas e
padrões persistidos para as referências escolhidas e sua associação vigente.
Titulares ativos compartilham essa leitura; viewer, outro tenant e sessão ausente
são rejeitados. A consulta não inicia efeitos nem altera a agenda. Quando o feed
já obtido forneceu um nome válido, a tela o apresenta junto ao @; na ausência,
continua usando o perfil. Não há nova chamada para obter nome.

O painel distingue espera, execução, indisponibilidade, análise concluída/parcial
e atualização programada. Seleção, correção do @ e referências próprias
invalidam a leitura. Não afirma sucesso enquanto os padrões não estão salvos.
16 testes unitários passaram com 100% de linhas/branches dos três módulos de
leitura; dois testes HTTP/PostgreSQL passaram com runtime restrito e provaram
isolamento e ausência de novas reservas, resultados, eventos ou auditorias no
GET. Mypy e Ruff passaram. A web passou em 100 testes focados/100% das quatro
métricas e em Chromium 390/1440px com fixtures locais. CI integral combinado e
ensaio externo controlado continuam como gates da entrega completa.
