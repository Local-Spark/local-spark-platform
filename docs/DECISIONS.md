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

### Origem da pesquisa e endereço próprio — 04/11/2026

Ao selecionar endereço em **Origem da pesquisa**, preencher todos os campos
com o cadastro salvo de **Endereço do negócio** e deixá-los somente para leitura.
Se esse cadastro não existir, exigir que o cliente o informe antes de salvar a
origem por endereço. Não oferecer outro endereço editável nessa configuração.
Para referências de outras regiões, manter a indicação manual de @ em
**Perfis que inspiram seu negócio**. A localização atual do dispositivo continua
como alternativa já existente. Essa decisão não altera raios nem ciclos.

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
| C15 | Após o trabalho inicial de skills, desenvolver pesquisa de referências que combine indicações do cliente com descoberta automática de negócios semelhantes em destaque. Usar referências para orientar a criação sem copiar conteúdo ou identidade de terceiros. | Indicação manual e snapshot implementados localmente. A descoberta automática, a relevância e as métricas ainda precisam ser implementadas e avaliadas; uma indicação do cliente não substitui a descoberta. O titular confirmou a possibilidade de armazenar a nota própria e a associação dos perfis do Apify, e escolheu Jev para avaliar candidatos, não como fonte de dados. |
| C16 | O modelo deve criar o texto da peça, a legenda e o convite à ação a partir do pedido e das referências do negócio; não substituir sua resposta por texto fixo ou fallback do código na geração real. | O briefing com skill usa redação natural e validação de fonte/valores; não comprova sentido ou qualidade e exige revisão humana. Baseline disabled é rejeitado em novas propostas. A avaliação real do novo caminho ainda está pendente. |
| C17 | A geração deve reunir pedido, fatos, kit, acervo pertinente, referências externas aceitas quando disponíveis e skill de feed/story em um briefing; solicitar ao modelo a peça final completa, inclusive texto e identidade, e conferir o resultado antes da publicação. O trace deve permitir examinar a entrada e decisões sem expor dados privados em logs. O caminho visual que gera só fundo e aplica layout fixo deve ser descontinuado para novas gerações. | Novo caminho local com skill, referência do kit, peça integral e trace cifrado. Aprovação via API exige conferência humana por SHA; WhatsApp/web ainda não oferecem o checklist. Sem homologação/ensaio real posterior. Indicações manuais não verificadas e snapshot implementados localmente; descoberta e aceite de sugestões continuam pendentes. Histórico preservado não autoriza novo efeito do caminho antigo. Ideia de concorrentes/fontes do kit fica para estudo posterior. |
| C18 | Promoções, ofertas e horários para uma peça vêm do pedido e das revisões pelo WhatsApp, sem cadastro desses fatos na interface. Uma promoção explicitamente pedida por R$ 19,90 vale para aquela criação mesmo que o catálogo registre R$ 25, sem perguntar sobre a diferença nem alterar o catálogo. Desconto percentual exige preço de catálogo válido como base; ausência ou ambiguidade exige esclarecimento, sem inventar valores. Permanece um campo simples para características gerais do negócio. O titular autorizou remover as informações antigas dessa área sem preservar seu histórico. | Formulários de fatos livres e promoções removidos da interface; palavras e características gerais entram no contexto versionado. Fatos livres antigos do contexto não alimentam novas peças; novos snapshots editoriais ignoram promoções legadas, mantendo a política dos snapshots antigos. Registros físicos históricos não foram purgados. O WhatsApp/Jev ainda não extrai e vincula fatos promocionais e revisões nem aplica todas as regras; a mensagem não atualiza o catálogo automaticamente. |

### Pesquisa de referências — decisões adicionais de 30/10

O proprietário escolheu pesquisa somente no raio solicitado, uma por raio em
cada ciclo, com até dez candidatos por raio e sem promessa de 30 negócios únicos.
A decisão de 04/11 abaixo acrescenta a ampliação automática quando o Google retorna zero negócios.
Em 03/11, o titular esclareceu que o cliente verá até dez candidatos elegíveis,
com até três recomendações do Jev destacadas, mostrando critérios e nota quando houver candidatos
suficientes. O cliente pode escolher de uma a três entre os exibidos.
Falha comprovada não consome a tentativa. Em 03/11, o titular esclareceu que a
primeira confirmação de uma a três sugestões inicia um ciclo de seis meses: cada
raio pode ser pesquisado uma vez nesse ciclo, inclusive outros raios após a
confirmação. Os raios voltam a ficar disponíveis ao fim do prazo original; mudar
endereço ou segmento não libera um raio já pesquisado. A seleção pode combinar
negócios de diferentes raios. Trocar entre candidatas encontradas não renova o
prazo e a seleção permanece após seu fim até outra confirmação; o titular confirmou
que referências ainda selecionadas de ciclos anteriores podem ser combinadas com as
encontradas na nova pesquisa. As referências
@ manuais são adicionais e não contam no limite. Durante o ciclo, não repetir
consultas Apify para negócios já encontrados; é permitido consultar o Apify para
negócios novos encontrados em outro raio e repetir uma tentativa que tenha
falhado sem retornar o perfil. Não haverá pesquisa nacional nova.
Negócios sem Instagram devem ser mostrados e o cliente
poderá informar o @. Um @ indicado pelo cliente já é referência escolhida; isso
não confirma que existe, que pertence ao negócio ou que foi acessado. Sugestões
automáticas, quando existirem, continuam sujeitas à escolha do cliente. Se não for
possível consultar um perfil público por falha ou limite, informar a falha e
permitir nova tentativa posterior.

Em cada rodada, inclusive após seis meses, a lista de até dez será formada pela
mesma regra a partir dos negócios retornados na nova pesquisa Google; não há
mistura automática com resultados antigos ausentes da nova resposta. Um negócio
reencontrado usa a nota mais recente na nova lista, preservando a nota de cada
pesquisa no histórico. Quando uma referência já escolhida ficar fora dos dez,
o cliente decidirá se deseja mantê-la somente no início de uma nova rodada após
os seis meses. Consultar outro raio na mesma rodada não repete a pergunta. O fake
ainda não implementa essa jornada de confirmação nem uma lista real de dez.

O serviço de contexto aceita novas escolhas somente locais de 5, 20 ou 50 km.
Configurações nacionais e raios antigos permanecem quando iguais ou omitidos;
`null` explícito os remove. Replays e alterações pendentes já admitidas mantêm
compatibilidade. Essa validação não ativa a descoberta real.

Para sugestões automáticas, o proprietário escolheu que Jev avalie semelhança
com o negócio e elimine candidatos inadequados antes de pontuar os restantes,
apresentando critérios e nota para cada destaque. Isso depende de fonte e uso
permitidos e ainda não está implementado. Avaliações de estabelecimentos não
medem engajamento social.
O titular autorizou guardar temporariamente até vinte Place IDs e notas para
recuperar uma pesquisa; notas só são calculadas após o filtro de semelhança. A
lista apresentada continua limitada a dez e entradas Google como estrelas,
contagem e nome não são guardadas.
O titular quer guardar os até dez negócios apresentados por pesquisa, incluindo
Place ID, pontuação própria e perfis disponíveis, para permitir trocas sem nova
consulta. Em 03/11, o titular confirmou que, dos dados Google, somente o Place ID
será guardado; estrelas e quantidade são entradas para o cálculo, não campos
persistidos. Confirmou também o armazenamento da nota própria e da associação
de perfis obtidos pelo Apify e informou já ter verificado essa possibilidade.
O nome apresentado virá do Apify quando disponível; na ausência, mostrar o
perfil ou outro identificador disponível sem guardar o nome oriundo do Google.
Nesta primeira versão, perfis descobertos são somente do Instagram. O titular
esclareceu que um único perfil retornado pelo Apify deve ser usado como perfil do
negócio e analisado automaticamente, sem exigir confirmação do cliente; a origem
continua atribuída ao Apify e não representa verificação independente. Havendo
vários perfis, usar o principal indicado pelo Apify ou, se não houver indicação,
o primeiro retornado, preservando a ordem da fonte. Se as sugestões estiverem incorretas,
o cliente pode informar outro @ manualmente. O titular deseja analisar
até 20 publicações recentes do feed por perfil escolhido via Apify, incluindo
imagens e legendas públicas acessíveis quando disponíveis. Guardar somente
padrões e aprendizados extraídos, sem cópias dos posts; usar o material acessível
quando o retorno for parcial e informar que a análise foi parcial. A atualização
dos padrões é automática a cada seis meses.
Para destacar até três negócios, Jev considerará semelhança e nota. Serão exibidos
os critérios avaliados e a nota, sem frase explicativa livre; candidatos cuja
semelhança o Jev não consiga avaliar ficam fora das sugestões.
Em 03/11, o titular decidiu que o Jev combina semelhança e nota para os três
destaques e desempata por semelhança quando houver empate na décima posição.
Confirmou os raios 5, 20 e 50 km; quando os seis meses terminarem, o cliente
escolherá quando pesquisar novamente. Negócios sem estrelas ou avaliações ficam
fora da lista até haver dados suficientes para a nota. Titulares ativos da mesma
organização compartilham pesquisas e escolhas do negócio. O próprio negócio do
cliente deve ser excluído das sugestões; o titular autorizou identificá-lo
automaticamente por nome e endereço quando houver correspondência clara e pedir
confirmação apenas se houver dúvida.
O titular esclareceu que o endereço e as coordenadas do próprio negócio devem
permanecer no cadastro; a orientação anterior de apagá-las após a pesquisa foi
revista. Na análise do Instagram, escolheu aprender
tom, temas, formatos e elementos visuais gerais, considerando todas as imagens
acessíveis de cada carrossel. A primeira análise de um perfil recém-escolhido
ocorre após a confirmação e sua atualização é a cada seis meses. A conclusão
estruturada de semelhança do Jev pode ser guardada para recuperar uma falha sem
consultar Google novamente. Se o Jev não resolver um empate, prevalece a ordem
da resposta Google. O titular autorizou testar Jev ou outro modelo de visão
econômico, escolhendo conforme qualidade e custo.
O titular esclareceu que deseja usar o Apify pelo fluxo de chamada e resposta,
sem etapa obrigatória de exclusão nos servidores do fornecedor. Nossa plataforma
manterá os perfis associados e aprendizados autorizados, sem persistir as
publicações coletadas.
Escolheu testar uma pontuação própria de 0 a 10 com nota e quantidade, sem
armazenar os campos originais; a decisão anterior que impedia pontuar negócios
com menos de dez avaliações foi revista. Eles também podem receber pontuação;
sem média ou avaliações disponíveis, a implementação atual não calcula nota e
omite o negócio, conforme confirmação do titular. A expectativa de que a maior parte dos resultados tenha notas altas
não institui filtro mínimo de 8. Negócio sem Instagram, mas com dados para ser
pontuado, continua elegível para o cliente indicar o perfil.
Nos exemplos, qualidade deve pesar e mais avaliações devem aumentar a
confiança: 1 estrela indica qualidade muito baixa, sem exigir zero exato, e 4,8 com milhares deve superar
5,0 com 11 avaliações. O titular escolheu continuar os testes com a segunda
fórmula; a descoberta fake usa apenas semelhança predefinida e dados fictícios,
ordenados pela pontuação experimental sem arredondar. Em 03/11, o titular confirmou
que deseja continuar testando e calibrando a fórmula antes de defini-la. O peso,
a escolha final da fórmula continuam abertos.

O limite de gastos escolhido combina teto por pesquisa, teto mensal total e
tetos por fornecedor, com mês em UTC. A etapa já admitida pode concluir após
revogação do acesso; novas etapas não devem ser admitidas. Os valores precisam
ser configurados internamente antes de ativar fornecedores. Uma fundação local
de política versionada e efeitos fictícios foi testada sem conexão externa;
conciliação com evidência e integração de efeitos reais continuam pendentes.
O titular autorizou um primeiro teste real controlado de até US$ 5 no total,
somando fornecedores, e indicou que os limites mensais por fornecedor serão
definidos após a recorrência do produto. Não confundir
essa intenção com uma política financeira ativa ou autorização para conteúdo de
clientes nos testes de fundação.

Google Places é o caminho a estudar para descobrir negócios e Apify uma opção a
avaliar para enriquecer perfis; uma prova isolada de sites foi autorizada e
executada. A prova limitada do Places não comprova cobertura, correspondência de
perfil, engajamento ou custos. O titular confirmou a possibilidade de guardar os
campos descritos acima; limites financeiros precisam ser configurados antes de
uso real no produto. Geocodificação e confirmação
do ponto manual permanecem pendentes. Google Geocoding foi escolhido para estudar
a resolução; seu adapter está desativado, sem guardião de custo ou integração.
A indicação manual e seu snapshot no briefing/trace foram implementados
localmente. A infraestrutura simulada, desligada por padrão, exercita as regras
de raios, confirmação, bloqueio, troca e preservação com fixtures anônimas e
Temporal; a descoberta e o aceite de candidatos reais não existem. Os adapters
Places multitype, Geocoding, perfil e Place ID via Apify, e mapeamento de tipos
com Jev estão isolados e desativados; autorizações, guardiões reais de custo e
integração continuam pendentes. Um retorno de perfil não encontrado de fonte
não comprovada não é prova de inexistência. A associação real e a retenção dos
datasets externos ainda requerem tratamento técnico.

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
skill em um agente não a integra automaticamente à API do produto. O titular já
confirmou o armazenamento autorizado de Place ID, nota própria e associação de
perfis; não é necessária nova validação dessa decisão. Integração técnica,
critérios pendentes, cobertura e custos continuam a ser avaliados nas fases.

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

## 04/11/2026 — ausência de resultados e ampliação do raio

Se o Google retornar zero negócios no raio de 5 km, tentar automaticamente
20 km; se continuar vazio, tentar 50 km. Inícios em 20/50 km só ampliam para os
raios maiores ainda disponíveis. Se as três buscas terminarem sem resultados,
mostrar a ausência e permitir nova tentativa, sem iniciar o ciclo de seis meses.
Não confundir esse caso com uma nota mínima: não existe nota de corte. A mesma
ação continua sujeita aos limites financeiros, incluindo seus raios sucessores.
Implementação integrada em 0107 e coberta pelo CI final de 4.724 testes/100%.
O comportamento vazio foi validado com fixtures; o ensaio real retornou negócios.

### 2026-11-04 — Loja própria e ampliação quando Google retorna vazio

- Manter exclusão automática da própria loja quando nome/endereço correspondem claramente; perguntar apenas na ambiguidade. Guardar somente Place IDs e conclusão própria para recuperação, junto das notas e julgamentos autorizados.
- Na resposta realmente vazia do Google, ampliar 5 → 20 → 50 km automaticamente, respeitando cache, ocupação do raio, ciclo e um mesmo teto de custo. Iniciar em 20 ou 50 amplia somente para raios maiores da lista aprovada. A preferência do cliente não é alterada.
- Se os raios disponíveis terminarem vazios, informar ausência. Uma rodada não confirmada pode ser tentada novamente sem iniciar seis meses; ciclo já confirmado não é liberado por resultado vazio de outro raio.
- Rodada inteiramente vazia conserva escolhas anteriores. A pergunta de retenção só será exigida quando houver uma lista nova utilizável para confirmar.
- Revisão da loja pode ser confirmada por qualquer titular ativo. A autoria da decisão é auditada, mas a execução mantém o ator original e seus bloqueios de revogação.

### 04/11 — aplicação das decisões de análise aceitas

- A versão de associação da referência é positiva desde o perfil original Apify;
  ela muda quando o perfil escolhido muda ou é novamente selecionado após remoção.
- A próxima análise usa aceite + N períodos de seis meses em UTC, preservando a
  âncora original após o ajuste de dias de fevereiro. Atraso não gera coletas de
  compensação para todos os períodos passados.
- Falta de orçamento/configuração conserva a janela para retomada. Um resultado
  indisponível permanece explícito mesmo quando a próxima atualização está agendada.
- O nome do perfil vindo da resposta Apify já necessária pode ser conservado junto
  da análise, inclusive quando nenhuma publicação pôde ser analisada. Não se faz
  nova chamada apenas para obter o nome. Padrões não incluem conteúdo publicado.

Estas são aplicações técnicas das respostas já aceitas sobre perfis, retenção,
aceite e atualização; não alteram o ciclo de busca Google.

### 04/11 — autoria direta e capas de vídeos no feed

O ensaio encontrou carrosséis em coautoria explícita e Reels no perfil escolhido.
O filtro inicial considerava fotos/carrosséis de autoria direta; por isso a
primeira análise real terminou indisponível. O titular respondeu à entrevista:

- Usar somente publicações de autoria direta. A presença em coautores ou pessoas
  marcadas não substitui a autoria informada pelo Apify.
- Para vídeos e Reels, analisar a capa e a legenda disponíveis, sem analisar o
  vídeo em si. Em carrosséis, a imagem de capa de um item de vídeo também pode ser
  usada; o arquivo de vídeo não é baixado.

O adapter aplica o mesmo vínculo de perfil a fotos, carrosséis e vídeos. A análise
de capas conserva estado parcial porque não inclui o conteúdo audiovisual.
Publicações e mídia continuam apenas em memória; persistem os padrões derivados.
Resultados já concluídos e seus prazos não são reescritos pela mudança de filtro.

### 04/11 — retomada documentada da avaliação BL04.3

O titular solicitou que os quatro passos discutidos para BL04.3 e o ponto de
retomada fossem registrados nos SDDs, para continuar em outro chat: conferir
aprendizados, comparar com/sem referências, avaliar peças com o titular e
corrigir/repetir medindo qualidade e custo. O
[SDD ativo](phases/BL04-context-and-ai-production.md#quatro-passos-da-avaliação)
detalha entregas, primeira ação e evidências anteriores.

Esse registro não escolhe corpus, quantidade de tentativas, modelos novos nem
teto de gasto do ensaio. Preparar um plano concreto e consultar o titular em
entrevista sobre escolhas ainda abertas, preservando autorizações aplicáveis.
Não repetir as decisões já respondidas da feature de referências. Nenhuma peça
nova, chamada paga ou avaliação humana foi executada nesta atualização documental.
