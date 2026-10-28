# BL04 — contexto seletivo e produção visual com IA

Estado: **em implementação local**, sem aprovação comercial. Complementa a [trilha BL](BL-brand-library.md#bl04--recuperar-contexto-e-produzir-uma-peça-nova), o [SDD geral](../SDD.md) e os contratos transversais F03/F04.

**Correção de produto:** IA integra a contratação. Os botões atuais separados
por fornecedor ou modalidade serão substituídos por uma jornada contratual única,
apresentada também uma vez às contas já existentes. A descrição abaixo dos
controles por fornecedor registra o funcionamento atual, não o objetivo da
jornada; consultar [decisão e transição](../design/ai-as-core-service.md).
O aceite único e sua integração à web substituem os controles individuais;
registros anteriores são mantidos, sem reativação silenciosa. A geração visual
real continua desligada e pendente da coordenação BL04.2.

**Decisão de produto sobre troca de número:** o processamento de um material
já enviado continua para o mesmo negócio, mesmo que o cliente troque de número
enquanto aguarda. Após a troca, a prévia e o pedido de aprovação devem seguir
para o número ativo novo. Não exigir que o cliente espere a conclusão para
trocar. Para materiais já associados, o processamento continua mesmo sem canal
ativo e a entrega simulada aguarda o novo vínculo; essa validação local não
constitui envio real de prévia ou aprovação pelo WhatsApp.

## Aceite único do serviço — 28/10/2026

O cliente concorda uma vez em **Plano e acesso**, antes da contratação, com o
uso de IA para texto, imagem, interpretação e transcrição. WhatsApp não oferece
ativação separada de áudio, e Informações e preferências não oferece permissões
por fornecedor. A web encaminha quem ainda não aceitou para essa mesma página.
O POST por negócio grava versão/hash, ator, data e auditoria; não ativa plano,
provedores ou publicação. Aceite inicial aguarda mudanças e efeitos visuais
pendentes. Consentimentos legados permanecem como histórico e compatibilidade;
o novo contrato é autoridade para novos trabalhos, sem reescrever recusas.
Uma geração contratual distinta impede executar pedidos editoriais antigos como
se tivessem sido criados após o aceite. As descrições de toggles por fornecedor
abaixo registram a implementação anterior e não a jornada vigente.

Validação desta fatia: suíte backend de 1.583 testes aprovada e complemento de
24 testes (sete novos casos) com cobertura final de 100% de linhas e branches;
web com 360 testes/cobertura integral, build e três jornadas Chromium. RLS e
Temporal foram exercitados em serviços locais; sem chamadas pagas. A geração
visual real e os gates de qualidade BL04.3 continuam pendentes.

## Objetivo

A partir de um pedido livre e de informações autorizadas do negócio, identificar o que o cliente pretende divulgar, selecionar somente as fontes pertinentes e produzir uma prévia privada com identidade visual e IA. A revisão e eventual publicação permanecem ações distintas. O WhatsApp real depende de homologação Meta; os testes usam entradas sintéticas e mocks.

## Entregas e gates

### Andamento da BL04.1

O worker pode usar o **Jev como primeiro candidato** em desenvolvimento/teste,
desligado por padrão. O proprietário autoriza separadamente o envio de texto e
nomes de candidatos à TypeSafe. Uma operação durável reserva orçamento por tenant
antes da chamada; o acesso, origem e snapshot são revalidados, e uma resposta
incerta não é repetida automaticamente. Recusa de orçamento antes da submissão
tem estado próprio: a retomada usa verificação no ledger e operação atômica; o
workflow aguarda em intervalos de uma hora, por até sete dias, revalidando a
origem e o acesso. Estados `uncertain` antigos não são reclassificados. Um esclarecimento fica registrado no
adaptador local simulado, sem afirmar envio real pelo WhatsApp. A configuração
requer `TYPESAFE_API_KEY`, `MEU_BRACO_DIREITO_INTENT_AI_MODE=jev`, chave de
criptografia e orçamento diário positivo `MEU_BRACO_DIREITO_INTENT_AI_DAILY_BUDGET_USD_MICROS`.
Esse teto é por tenant/dia, em milionésimos de dólar; é conservador, não uma
fatura nem um limite global para outras APIs. A chamada real exige autorização de
gasto específica e uma avaliação PT-BR mais ampla antes de liberar produção.

Para a oferta inicial de **R$ 99/mês**, o proprietário definiu foto e story como
formatos iniciais; vídeo será definido depois. O interpretador consulta essa regra
única após a verificação do acesso e pede esclarecimento se o formato pedido for
indisponível. A regra estática descreve somente a oferta inicial e precisa ser
substituída por permissões persistidas quando houver múltiplos planos. Não define
quantidade de peças nem autoriza gerar ou publicar.

Permanecem limites relevantes da BL04.1: a interpretação de formato é experimental,
sem franquias de quantidade implementadas; preço e agenda não são confirmados pela IA.
O nome do item ativo e versionado pode servir de fonte factual do roteiro, com
identificador vinculado à versão do acervo e nova validação na edição. Nomes que
contenham alegações comerciais exigem outro fato confirmado; preços e ofertas não
são inferidos do nome. A pergunta simulada é genérica e não mantém uma conversa completa.
Prévia real com este briefing permanece bloqueada; há apenas o modo simulado da
BL04.2. Kit é congelado na proposta; as referências fotográficas ainda não são
enviadas a um gerador visual. Portanto
não afirmar que o fluxo completo ou a qualidade comercial estão concluídos.

### Andamento da BL04.2

O proprietário pode conceder, quando o modo visual estiver configurado, e
retirar em Sobre meu negócio uma autorização específica para o envio futuro de
contexto visual e fotos autorizadas à OpenAI; a API permite retirada mesmo com
o modo desligado.
É independente do consentimento de texto; a tela informa que a criação de
imagens ainda está em preparação. O serviço registra as mudanças por negócio e
mantém isolamento entre organizações. O modo visual continua desligado por
padrão e restrito a desenvolvimento/teste.

Há uma jornada simulada em desenvolvimento/teste: captura o contexto, lê até
uma foto enviada pelo WhatsApp e fotos pertinentes do item e do espaço, confere
hashes, normaliza orientação e remove metadados das cópias; preserva o original.
O pedido usa o kit, fato e CTA conferidos. Uma tentativa com fence e reserva
transacional produz um arquivo explicitamente marcado como simulação, privado e
sujeito a revisão. Isso **não é uma imagem criada pela OpenAI** e não comprova
qualidade. A partir de 28/10, a simulação usa o acabamento experimental para
aplicar fontes, nome, tagline, logo autorizado e texto do kit sobre uma cena
neutra, com faixa de simulação; não chama IA para criar a cena. O resultado é
revalidado antes do acesso e da decisão.

Um teste sintético executa o percurso local com Temporal e PostgreSQL reais:
material processado, contexto e acervo, roteiro baseline, dispatchers, prévia
simulada com kit e decisão de revisão. Interpretador e armazenamento são stubs,
e Meta/OpenAI não são chamados. O teste começa com o material já processado;
ele não homologa o webhook WhatsApp nem a geração de imagem real.

Um teste complementar combina o preparo de fontes, kit, reserva e adapter de
imagem com uma resposta HTTP simulada e guarda simulada. Ele verifica o encaixe
entre os componentes sem rede ou cobrança; não implementa a guarda real, não
liga o dispatcher e não prova segurança de concorrência ou qualidade visual.

Para testes técnicos, `MEU_BRACO_DIREITO_VISUAL_AI_MODE=fake` e um teto mensal
positivo `MEU_BRACO_DIREITO_VISUAL_AI_MONTHLY_BUDGET_USD_MICROS` habilitam a
simulação apenas em desenvolvimento/teste. A reserva fictícia é de um
milionésimo de dólar e liquidada em zero; não aciona a OpenAI. A interface
identifica o arquivo como simulação e ele não deve ser publicado. A seleção
manual de modo é feita pela API; no worker, o modo fake é escolhido para proposta
com briefing quando configurado. O padrão permanece desligado. Não alterar para
`openai` para tentar usar essa rota: o fluxo real continua bloqueado.

A intenção e a reserva são atômicas com o fence, mas a verificação das fontes e
do consentimento ainda ocorre em outra transação, sob outra role. Não habilitar
chamadas reais enquanto essa lacuna persistir. A [proposta para atomicidade](../design/BL04-atomicity-proposal.md)
registra uma alternativa para revisão: uma tentativa de migração de permissões
foi rejeitada pela revisão automática do ambiente. Faltam ainda teto global do
ensaio de US$ 1, tratamento completo de respostas incertas, integração real com
provedor, validação de qualidade e custo. O fluxo de foto sem legenda ou produto
identificado continua dependente de um briefing BL04.1 válido. O acabamento do
kit está ligado somente ao modo simulado, não ao percurso do provedor real.

Decisão do proprietário em 28/10/2026, substituindo a regra de 27/10: ao
solicitar alteração ou exclusão de foto, alteração de kit ou mudança de contexto
durante uma criação, o cliente aguarda o término dos processos já iniciados.
Registrar a alteração pendente, cancelar os trabalhos na fila que ainda não
começaram e não iniciar novas criações até aplicar a mudança. Após a conclusão
das criações em andamento, efetivar a solicitação e comunicar o resultado ao
cliente. Sem processo em andamento, a mudança pode ser aplicada sem espera.
Por decisão do proprietário, a prévia concluída antes da alteração permanece
disponível para revisão e deve ser identificada como criada antes da mudança;
sua publicação continua sujeita aos direitos e ao fluxo de aprovação aplicáveis.
A retirada de autorização conserva a decisão específica de manter disponível a
prévia que terminou durante a espera. O novo comportamento para fontes ainda precisa ser
implementado e testado em concorrência; não está concluído no modo simulado.

**Progresso local em 28/10:** no modo simulado, atualizações/restauração do
contexto editorial, alterações do catálogo de produtos/serviços, confirmação do kit e atualização/exclusão de fotos do
acervo podem aguardar criações admitidas. A fila é durável, bloqueia novas
admissões e conserva a prévia elegível para revisão com indicação de que é
anterior à alteração. Erros previstos ficam explícitos e continuam bloqueando
novas criações até o proprietário corrigir a solicitação. Retirada de
autorização pendente preserva `accepted=true` até a efetiva retirada; o campo
`state` distingue essa espera e impede novos inícios.

O upload de fotos do acervo reserva a alteração antes do envio, fora do lock
durante a transferência. O proprietário autor pode descartar um upload incerto
após vencer a reserva: a chave é isolada, o negócio é desbloqueado e um novo
envio usa outra operação. A retomada exige prova persistida de PUT com tentativa
única; registros legados sem prova ficam em quarentena. A limpeza física da
quarentena ainda não foi implementada e a interface orienta procurar a equipe.
Se o autor perder acesso, outro proprietário ainda não pode cancelar. O rollout
exige drenagem e reconciliação dos efeitos legados, conforme o [procedimento](../design/BL04-quarantine-rollout.md).

Este é um recorte, não a regra completa nem a conclusão da BL04.2: material
WhatsApp e outros escritores de fontes ainda não usam a fila; a limpeza física de foto depende do reconciliador
existente. Se o pedido é de outro proprietário que não o da última geração,
ele pode ficar em erro e não ser aplicado automaticamente. O provedor real
permanece desconectado, e a disponibilidade da prévia preservada continua sujeita
às permissões e à existência do material original aplicáveis.
O tratamento de exclusão de material WhatsApp e da prévia sem origem tem uma
[proposta específica](../design/BL04-whatsapp-deletion-review-proposal.md), ainda
não implementada.
**Decisão posterior do proprietário:** materiais enviados devem ser preservados
para formar contexto do negócio; ele não deseja oferecer exclusão de uma foto
recebida como solução para uma peça ruim. Isso substitui a premissa de expirar
automaticamente a foto que originou a exceção anterior de sete dias. O código
agora preserva materiais já associados sem prazo e a API recusa exclusão de
qualquer tipo pelo histórico. O uso como memória pesquisável permanece pendente;
a remoção de fotos desatualizadas do acervo continua disponível.
A [proposta de preservação](../design/BL04-whatsapp-durable-materials.md)
detalha as dependências. A retenção geral das prévias não foi
definida. As demais regras aprovadas para mudanças durante criações continuam
aplicáveis enquanto seus respectivos recursos existirem.

**Retirada de IA textual — não concluída:** o comportamento atual ainda revoga
imediatamente; não existe espera segura para a criação visual ou chamada
textual já iniciada. Uma tentativa de usar apenas o estado da proposta foi
retirada porque exclusões em cascata poderiam apagar a prova antes do retorno
do provedor. A revisão automática rejeitou conceder leitura da prova de uso ao
app sem revisão de privilégios e RLS. Há campos e barreiras da migração 0051
sem fluxo produtor, preservados enquanto a reversão de uma barreira de revisão
não foi aprovada; eles não implementam espera nem devem habilitar o provedor.
Se uma base experimental contiver uma pendência criada por versões de teste,
o campo residual pode continuar bloqueando prévias mesmo após nova autorização;
é necessário tratar essa situação antes de atualizar a base de desenvolvimento.
Uma [proposta de leitura mínima da prova de uso](../design/BL04-editorial-usage-access-proposal.md)
detalha o grant, a policy e os testes que ainda dependem de revisão; não foi aplicada.

Como recorte independente, propostas editoriais enfileiradas para OpenAI levam
uma geração de consentimento: retirada e reautorização não revivem pedidos
antigos, e as propostas anteriores à migração sem essa prova não são enviadas à
OpenAI. O processamento local independente não é cancelado por essa regra. Jev/TypeSafe
mantém autorização separada da OpenAI. O rollout exige parar tráfego e workers
antigos, aplicar as migrações e iniciar apenas versões que conheçam a barreira
de geração; implantação mista não garante o cancelamento. A retirada WhatsApp,
retenção da origem e revisão após exclusão também permanecem pendentes.

Um [ensaio isolado de feed](../evals/bl042-guarded-synthetic-feed-2026-10-27.md)
gerou uma imagem real da OpenAI usando exclusivamente dados fictícios e foto
CC0; uma chamada custou US$ 0,026272 estimados. Não utiliza o fluxo de cliente,
não comprova fatura nem margem, e a IA alterou logo e pontuação. Um acabamento
experimental pode aplicar nome, logo original e textos validados a uma cena
sem texto; não está integrado nem aprovado. O executor de provedor também está
isolado: um CAS no ledger impede reenvio, sem liberar o envio real de fontes.
Continuam obrigatórios coordenação das fontes, custos e revalidação completa.

Os testes concorrentes do fluxo simulado exercitam a regra atual de espera e
preservação para os tipos cobertos acima. O acabamento experimental possui serviço que
revalida kit, logo, direitos e texto antes/depois, e um orquestrador com guarda
injetado exercita envio, revalidação, descarte e armazenamento com mocks. O
acabamento está ligado ao worker simulado; o orquestrador real segue isolado e
nenhum deles constitui guarda real aprovado. A revalidação do
acabamento relê referências e precisa de medição antes de operar em escala.

Em 28/10, um [novo ensaio sintético isolado](../evals/bl042-synthetic-brand-finish-2026-10-28.md)
usou uma chamada OpenAI autorizada, seguida do acabamento experimental. Custo
estimado por uso: US$ 0,020615; o ledger mantém o novo teto de US$ 1 reservado.
O ensaio não usa o worker de clientes nem comprova qualidade ou margem.

Em 27/10, foi adicionado ao ledger um teto mensal agregado para reservas do
provedor `openai`, separado do teto por tenant e desativado por padrão. A
migração `0049` mantém somente totais mensais agregados e o teste concorrente
verifica a disputa entre tenants; valores incertos continuam reservados. O teto
depende de estimativas e abrange somente chamadas que usem este ledger: não é
limite de fatura da OpenAI, nem cobre áudio, texto ou chamadas de ensaio externas.
Configurar uma chave ou orçamento não ativa o worker, e a API não anuncia o
provedor como disponível enquanto o percurso não estiver integrado.

O acabamento experimental agora converte o resultado em JPEG privado compatível
com o contrato atual, mas ainda não é uma peça avaliada comercialmente. Há um
[desenho de execução Temporal](../design/BL04-visual-temporal-execution.md) para
timeout, lease e recuperação. O workflow separado e sua activity já têm uma
tentativa e prazos próprios, testados com Temporal real; não estão ligados ao
dispatcher, ao runner ou ao worker, e não liberam chamadas pagas.
O claim passou a verificar que a conta e associação owner permanecem ativas;
essa checagem adicional não serializa revogações concorrentes.

### Retirada de autorização visual — decisão do produto

Quando o cliente solicitar a retirada, impedir imediatamente novas admissões
para geração; os trabalhos que ainda aguardam na fila devem ser cancelados. As
gerações que já começaram a usar as fotos podem terminar e a interface deve
informar que a retirada está pendente até seu encerramento. Sem uma tentativa
em andamento, retirar imediatamente. O estado pendente deve ser durável e
isolado por negócio, inclusive após reinício do worker. Resultado desconhecido
por falha não comprova conclusão: bloquear novos inícios e indicar que o pedido
está em verificação. A prévia de uma geração já iniciada que terminar durante a
pendência continuará visível para revisão do cliente após a retirada; isso não
autoriza uma nova geração nem equivale à aprovação ou publicação.

Em 28/10, o proprietário confirmou a mesma espera para retirada da autorização
de processamento de materiais WhatsApp ou de IA de texto durante uma geração
visual já iniciada. Esses dois novos casos ainda não estão implementados.

O fluxo **simulado** implementa esse controle com admissão e pedido serializados
por negócio, sem manter transação aberta durante o processamento. Trabalhos não
admitidos são ocultados imediatamente e o dispatcher os marca como falhos quando
os encontra. Somente a prévia comprovadamente concluída durante a pendência pode
ser consultada depois da retirada, inclusive após nova concessão; as demais
fontes continuam sujeitas à revalidação. A decisão de publicação após a retirada
continua bloqueada. Processos em estado incerto não são encerrados por timeout:
exigem verificação e não possuem reconciliação automática nesta entrega.

Essa implementação não autoriza contornar os limites de acesso existentes e
**não está conectada ao provedor real**. Não comprova exclusão de dados no
fornecedor. URLs privadas já emitidas mantêm sua validade limitada prevista;
o gate não revoga retroativamente um link já entregue.


1. **BL04.1 — Interpretação e contexto:** interpretar intenção e formato dentro das opções efetivamente disponíveis; localizar candidatos no acervo do mesmo negócio com produtos/aliases ativos e validade no fuso do negócio. Correspondência lexical é só candidato: negação, ambiguidade ou ausência de fonte não autorizam escolher produto automaticamente. Fotografias precisam de direito válido; dados de outro tenant, item arquivado e preços vencidos não podem compor o briefing. Kit confirmado, fatos, itens e mídias devem ter versões e proveniência verificáveis. Revalidar direitos e fontes antes do efeito e ao liberar o resultado, aplicando a espera decidida para solicitações de alteração e retirada.
2. **BL04.2 — Imagem e custo:** integrar um provedor de imagem ao caminho real da prévia, com consentimento aplicável, referências mínimas e saída privada; registrar operação, versão de modelo/briefing, fontes e uso. Uma referência de kit no máximo, quando necessária; fotos reais pertinentes do negócio são referências separadas. Se a promessa for retratar local/produto reais, não apresentar um ambiente inventado como fotografia documental. Texto/preço/CTA exigem conferência literal; resultado generativo não comprova fidelidade por si só. Falta de fonte deve gerar pergunta ou conceito identificado, não fato inventado.
3. **BL04.3 — Qualidade e economia:** avaliar post e story novos em celular com titular e materiais consentidos. Registrar rejeições, retrabalho, todas as tentativas e custo por peça aceita; avaliar separadamente legibilidade, identidade, fidelidade e texto. Ensaios fictícios e comparação entre modelos medem viabilidade técnica, mas não substituem aceite do titular nem comprovam margem.

## Fornecedores e controle de risco

A opção de imagem é um adapter por capacidade, comparado com receitas aplicáveis usando qualidade e custo por peça aceita; não prometer que todas as peças serão boas por trocar de modelo. A hipótese é R$ 99 de mensalidade e **custo total máximo pretendido de R$ 50/mês**, incluindo serviços externos, infraestrutura, retentativas e suporte. O valor não foi validado. Vídeo, animação e avatar têm gates próprios e não são automaticamente entregues pela integração de imagem.

Antes de qualquer geração paga para cliente, reservar o limite de gasto por operação e tenant de forma atômica, registrar o intento durável, executar fora da transação, liquidar uso conhecido e tratar como **resultado incerto** qualquer timeout após possível submissão. Não repetir nem trocar provedor automaticamente quando houver risco de cobrança duplicada. Validade do direito, acesso e referências deve ser verificada também após a chamada. Auditoria/telemetria não expõem segredos, imagens ou prompts privados por padrão.

Para a avaliação inicial, o usuário autorizou até **US$ 1 no total para chamadas de imagem com dados fictícios**. Esse teto é para o ensaio, não é franquia comercial e não autoriza dados de clientes nem gastos ilimitados. Testes automatizados usam mocks e não fazem chamadas pagas. O custo informado pelo provedor deve ser distinguido de estimativas e da fatura final.

## Avaliação do Jev

Jev é o primeiro candidato para classificação curta, necessidade de esclarecimento e sugestão de formato; não é gerador de imagem e não decide permissões, consentimento, fatos ou limite de gasto. Um corpus PT-BR sintético com gabarito e casos de ambiguidade/negação compara baseline e modelos, taxa de acerto, abstenções, latência e custo. A [comparação Jev/OpenAI](../evals/intent-comparison-2026-10-27.md) aponta erros em ambos e saídas incompletas da OpenAI; não é holdout independente nem teste da memória do WhatsApp. O ensaio é offline por padrão, sem dados de clientes. A amostra não aprova uso comercial.

**Pendências da validação:** o runtime consulta nomes/aliases por correspondência
lexical e processa eventos isolados; não há memória de conversa validada. Os caminhos
de conversa e de conteúdo precisam coordenar uma única resposta por evento antes
do envio real. Circuit breaker/rate limit de provedor e capacidade em escala ainda
não foram homologados. A reserva de custo conhecida mantém o máximo diário, mesmo
após sucesso; avaliar liquidação segura para não limitar o throughput indevidamente.

## O que não encerra a fase

Um helper de busca, eval isolado ou renderer técnico não significa fluxo integrado. São necessários conexão das fontes ao processo durável, geração de imagem com orçamento e consentimentos, verificação das alterações durante o processamento, prévia utilizável e os gates acima. A importação assistida de cardápio continua BL03.3 posterior. BL05 integra conversa, ajuste, aprovação e publicação simuladas sem depender da Meta.

## Casos de QA planejados

Loja física de cachorro-quente, delivery e manicure com espaço próprio têm cenários
e roteiro de testes manuais em [guia de QA](../evals/manual-qa-negocios-ficticios.md).
Preparação de dados/imagens é distinta de completar o fluxo BL04/BL05.
