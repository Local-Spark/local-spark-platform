# Meu Braço Direito — contexto vigente

## Próxima retomada — BL04.3, 04/11/2026

Continuar a avaliação de qualidade das peças com kit, acervo, skills e referências.
A feature de referências está implementada e validada localmente; a nova rodada
de peças com seus aprendizados ainda não foi executada. O
[SDD ativo detalha os quatro passos](phases/BL04-context-and-ai-production.md#quatro-passos-da-avaliação):
conferir aprendizados, comparar com/sem referências, avaliar com o titular e
corrigir/repetir medindo custo por peça aceita. Começar pelo inventário e plano
do ensaio. Casos, quantidade e orçamento devem ser preparados para entrevista;
não reutilizar automaticamente tetos históricos nem refazer a descoberta.
O ponto de retomada inclui evidências anteriores, limites e instruções para o
próximo chat, sem depender da conversa. Preservar as alterações Git existentes.

## Referências — estado da integração em 04/11/2026

No ajuste de interface confirmado pelo titular, a origem por endereço mostra
os campos de **Endereço do negócio** somente para leitura. Sem cadastro salvo,
é necessário preenchê-lo antes de salvar essa origem; alterar o cadastro atualiza
os campos exibidos, mas não salva preferências de pesquisa automaticamente.
Referências de outras regiões continuam podendo ser informadas por @ em
**Perfis que inspiram seu negócio**. A origem pelo dispositivo permanece disponível.

O aviso de busca indisponível reflete `discovery_available=false`, calculado pela
prontidão operacional da API. Na configuração local consultada, as credenciais
Google, Apify e Jev estão presentes, mas as flags de execução estão desligadas e
a configuração complementar do piloto não está carregada. O ensaio anterior usou
processos temporários configurados para esse fim. Esse aviso não representa
ausência de endereço nem bloqueio semestral; a alteração de interface não ativa
serviços pagos. A avaliação BL04.3 continua sendo a próxima etapa de qualidade.

A árvore local reúne descoberta Google com custos, classificação Jev, contatos
Instagram pelo Apify, seleção compartilhada, interface de pesquisa, análise de
publicações e uso dos padrões na criação editorial/visual. As revisões 0108–0110
acrescentam associação versionada, agenda semestral a partir do aceite, ledger
por amostra e snapshot imutável da proposta. A análise guarda padrões próprios;
publicações e imagens permanecem em memória. Eventos aguardam configuração
quando a execução está desligada.

O CI combinado passou em 4.734 testes com 100% de linhas e ramos, Ruff e mypy.
O piloto fictício autorizado de US$ 5 foi executado e comprometeu US$ 0,455502,
incluindo reservas Google/Jev ainda não liquidadas. Isso não equivale a avaliar
a qualidade comercial de peças geradas. O banco da aplicação foi atualizado de
0105 para 0111 após backups privados verificados; a API aberta antes dessas
migrações precisa de reinício. Este estado substitui as pendências de
implementação de referências nos registros datados abaixo.

O ensaio real encontrou um parser excessivamente restrito para componentes
opcionais de endereço do Google. A [correção do contrato](design/google-places-address-components.md)
passou em 160 testes com cobertura integral dos três módulos verificados. No
novo caso fictício, os 20 resultados foram aceitos e o Jev salvou três destaques
distintos. Os dez contatos foram publicados e uma referência foi confirmada.
A primeira análise real terminou indisponível pelo filtro inicial de autoria/formato.
Depois do ensaio, o titular confirmou autoria direta apenas e autorizou capa e
legenda de vídeos/Reels. O filtro foi atualizado, incluindo capas de itens de
vídeo em carrosséis, com estado parcial explícito e sem download do vídeo.
A alteração passou em 164 unitários/100% do adapter, cinco integrações e no CI
integral acima. A interface explica autoria direta e capa/legenda; dez testes
dirigidos/100% do componente, TypeScript e Prettier passaram. O ensaio também
expôs recibos Apify preliminares: a espera por contabilização está implementada,
e a revisão auditável 0111 foi aplicada e reconciliou os onze recibos sem alterar
o teto. A interface passou em 508 testes com cobertura integral, TypeScript,
build e navegação em Chromium. Uma referência manual pública no negócio
fictício foi analisada: 11 publicações, 40 imagens e nove padrões disponíveis
no contexto de geração, com resultado parcial explícito. As decisões de conteúdo
foram resolvidas; fórmula em calibração e orçamento mensal comercial
foram adiados pelo titular. Flags persistentes seguem desligadas. Ver o
[relatório do piloto](evals/reference-feature-pilot-2026-11-04.md) e
[consolidação de custos](design/apify-cost-settlement.md).

Atualizado em **30/10/2026**, após a decisão de gerar a peça integralmente com
briefing, skill e referências pertinentes, e descontinuar o acabamento antigo.
O repositório separado de skills agora tem versões iniciais de briefing para feed
e story e casos fictícios; um ensaio exploratório comparou saídas de agentes com
uma sonda isolada do baseline, sem controle suficiente para demonstrar ganho.
A aplicação seleciona a skill versionada em briefings de feed/story e a usa na
direção da peça integral em desenvolvimento/teste. O efeito visual pago segue
desligado por padrão; homologação e avaliação real do novo caminho estão
pendentes. Decisões de produto e pendências ficam em
[DECISIONS](DECISIONS.md); contratos no [SDD](SDD.md); sequência no
[índice de fases](phases/README.md) e na [trilha BL](phases/BL-brand-library.md).
As versões anteriores foram [preservadas integralmente](history/2026-10-28-pre-documentation-reconciliation/index.md).
Uma entrega local não equivale a uma capacidade comercial homologada.

Em 03/11 o banco de desenvolvimento foi atualizado da revisão 0059 à 0072,
após backup privado com leitura integral verificada, para acompanhar o código
local. Em seguida, a revisão 0073 foi aplicada após outro backup verificado por
leitura. Posteriormente, o banco foi atualizado à revisão 0099 após novo backup
privado com leitura integral verificada; a API iniciada antes dela precisa de
reinício para reconhecer a revisão. Nenhum backup foi restaurado em teste.

Em 30/10, após ensaios diretos com três negócios fictícios, a fatia local
passou a distinguir números de direção de arte de alegações, verificar artefatos
internos na copy e usar um canal comercial opcional confirmado pelo titular.
Esse destino é configurado em Sobre meu negócio e versionado com o contexto;
não se presume que o telefone de identificação seja um canal comercial. A
validação é limitada e a peça continua sujeita a revisão humana.

O cliente pode registrar palavras que descrevem seu negócio e características
gerais no contexto versionado. A interface removeu os formulários de fatos
livres e promoções; fatos antigos do contexto não alimentam novas peças e novos
snapshots editoriais ignoram promoções legadas do catálogo. Snapshots antigos
mantêm sua política e registros físicos históricos não foram purgados. O fluxo
de ofertas e horários pelo WhatsApp e pelas revisões continua pendente.

Os ensaios usaram personalizações diferentes do mesmo kit demonstrativo. O kit
[fictício Ateliê Aurora](evals/kit-atelier-aurora-v1/README.md) foi criado como
fixture independente de QA, com manifesto e exemplos próprios; ainda não integra
o catálogo ou o executor de geração.
A indicação manual, descoberta automática e seleção das sugestões estão
implementadas localmente. A indicação sozinha não comprova análise do perfil;
apenas resultados derivados persistidos alimentam os padrões usados na criação.

A pesquisa pretendida é somente por raio local, a partir de endereço manual ou
posição confirmada do dispositivo; não há nova busca para todo o Brasil. A web
oferece raios de 5, 20 e 50 km; valores anteriores de 1–50 km e preferências
nacionais antigas são preservados até substituição explícita. A posição é
apresentada sem latitude/longitude e exige confirmação. A preferência é versionada
com o contexto e não é enviada aos modelos editorial ou visual nesta fatia.
O serviço também restringe novas escolhas a esses três raios locais. Preferência
legada igual ou omitida é preservada; `null` explícito a remove. Replays e
alterações pendentes já admitidas mantêm a compatibilidade anterior.

A busca começa no raio pedido, uma por raio por ciclo, com até dez candidatos,
sem garantia de 30 negócios únicos; falha comprovada não consome a tentativa.
Em 04/11 foi definida a exceção de resultado Google vazio: ampliar de 5 para
20 e depois 50 km; todos vazios permitem tentar novamente sem iniciar seis meses. Em 03/11, o titular esclareceu que até dez candidatos serão
exibidos, com até três recomendações do Jev destacadas com critérios e nota; o cliente
poderá escolher de uma a três entre os exibidos, combinando raios. A primeira
confirmação inicia um prazo de seis meses; cada raio pode ser pesquisado uma vez
no ciclo, inclusive depois da confirmação, e todos voltam a ficar disponíveis no
fim do prazo original. Mudar endereço ou segmento não libera raio já pesquisado;
trocar referências não renova o prazo e a seleção permanece até outra confirmação;
referências ainda selecionadas de ciclos anteriores podem ser combinadas com as novas.
Cada nova pesquisa formará novamente até dez resultados a partir dos negócios
retornados pelo Google, com nota mais recente e três destaques do Jev. A nota de
cada pesquisa permanece no histórico. Se uma referência escolhida ficar fora dos
dez, o cliente decidirá se a mantém; o fake ainda não implementa essa jornada.
@ manuais são adicionais. O titular quer guardar os até dez negócios apresentados
por pesquisa, com Place ID, nota própria e perfis disponíveis. O titular confirmou
que apenas o Place ID será guardado dentre os dados Google; estrelas e contagem
servem de entrada transitória para a nota própria, que poderá ser armazenada junto
à associação dos perfis do Apify. O nome exibido virá do Apify quando disponível;
caso contrário, mostrar o perfil ou outro identificador disponível. O Apify pode
consultar negócios novos de outro raio, mas não repetir
consulta bem-sucedida aos já encontrados durante o ciclo; uma tentativa que
falhou sem retornar o perfil pode ser refeita.
Na primeira versão, são considerados perfis de Instagram; um único perfil
retornado pelo Apify será usado e analisado automaticamente, sem confirmação do
cliente. Com vários perfis, usar o principal indicado ou, se não houver, o primeiro
retornado; se estiverem incorretos, o cliente poderá informar outro @. O titular deseja
analisar via Apify até 20 publicações recentes do feed por perfil, incluindo
imagens e legendas públicas acessíveis, guardar apenas padrões extraídos e
informar quando a análise for parcial, atualizando automaticamente os padrões a
cada seis meses. Jev deverá destacar até três negócios considerando
semelhança e nota, com critérios e nota exibidos; semelhança incerta não entra nas
sugestões. Não há nota mínima de corte.
A infraestrutura privada `fake`, desligada por padrão, usa fixtures anônimas e
Temporal e permite pesquisar raios ainda não usados após a confirmação, no prazo
original. Ela exercita seleção entre raios, compensação de falha comprovada e
reconciliação de autor revogado. Ela não consulta fontes externas nem apresenta candidatos
reais. Busca real, verificação de perfis, aceite de candidatas reais e uso dessas
referências no produto continuam pendentes. Os adapters Google Places com tipos
principais múltiplos, Geocoding, consulta de perfil e enriquecimento por Place ID
via Apify, e mapeamento de tipos com Jev estão isolados e desativados, sem
guardião de custos integrado a efeitos reais; a origem manual exige localização
confiável, com confirmação apenas se houver dúvida. O resultado de perfil não
encontrado sem fonte comprovada é inconclusivo. O perfil retornado pelo Apify
será utilizado conforme a regra aprovada, após vincular a resposta à consulta
autorizada; a análise de publicações ainda não está conectada. O titular não
exige uma etapa de exclusão dos dados retidos pelo fornecedor.
Em desenvolvimento, uma base privada separada para buscas e resultados reais
foi preparada com RLS e somente leitura, sem writer nem rota. A requisição Places
já entrega seus parâmetros exatos à futura guarda, e existe adapter de
semelhança Jev restrito a HTTP simulado; nenhum deles liga fornecedores reais.
O ledger comum, limite cumulativo do ensaio e fence do executor foram exercitados
para Google com HTTP simulado. Commit sanitizado de resultado, Apify/Jev no mesmo
teto e reconciliação continuam em implementação antes da integração externa.
Um adapter de feed Instagram aceita apenas HTTP simulado e prepara até 20 posts
de imagem/carrossel, com legenda em memória e estado de análise parcial. Não
baixa imagens nem grava publicações na plataforma.
O titular escolheu testar pontuação de reputação de 0 a 10, combinando nota e
quantidade, sem armazenar os campos originais. A regra anterior de não pontuar
com menos de dez avaliações foi revogada: a partir de uma avaliação pode haver
nota; sem média ou avaliações disponíveis, não há pontuação e o negócio não é
incluído nas sugestões. Duas fórmulas foram exercitadas apenas com dados
fictícios. O titular escolheu continuar testando a segunda, que penaliza pouca
evidência sem elevar a média; seu peso continua provisório. O titular confirmou
em 03/11 que a fórmula seguirá em teste e calibração. A descoberta fake
aplica o filtro de semelhança definido na fixture e salva a pontuação integral
e as versões da fórmula e da fixture por pesquisa; leituras posteriores usam o
snapshot e o ordenam sem arredondar. Não há ranking real ou avaliação real pelo Jev. Ver
[avaliação](evals/reference-reputation-eval-2026-10-31.md).
Jev deverá primeiro eliminar candidatos inadequados na busca real; a nota própria
e a associação dos perfis ainda não são persistidas para negócios reais.
Uma política financeira compartilhada e versionada e o tratamento de efeitos
fictícios por outbox/Temporal foram testados isoladamente: limites por pesquisa,
fornecedor e mês em UTC, sem política ativa por padrão. Retornos incertos
mantêm reserva, sem liquidar por valor informado sem evidência. Integração de
efeitos reais, identidade/hash reais, conciliação da fatura e rotação de chave
permanecem pendentes; essa fundação não autoriza chamadas externas. A chave
HMAC fictícia ainda não tem versão: trocá-la com trabalho pendente interrompe
o processamento até restaurar a chave anterior, mantendo qualquer reserva.
Uma [prova pontual do Google Nearby](evals/google-nearby-order-probe-2026-10-30.md)
observou que a ordem `POPULARITY` não corresponde simplesmente a ordenar por
nota e contagem na amostra. A reserva cumulativa das consultas Places foi de
US$ 0,280, não a fatura; o registro não salvou nomes ou respostas brutas.

## Produto

Pequenos negócios enviam texto, foto, áudio ou vídeo pelo WhatsApp. A plataforma
usa os fatos confirmados, o kit e os materiais do próprio negócio para preparar
conteúdo, pedir aprovação específica, publicar nos canais habilitados e mostrar
resultados observáveis. Também deverá propor conteúdo sem envio novo, dentro de
uma cadência aceita e da franquia; essa proatividade ainda não está implementada.
O cliente não precisa escrever prompt ou operar um editor.

A web complementa identidade, contratação, canal, contexto, acervo, kits e revisão.
A vitrine pública usa exemplos fictícios já produzidos; uma visita não chama IA
nem conecta contas sociais. A escolha do kit não aprova publicação.

Uma conta de cliente e uma organização por negócio, com cobrança e aceite
próprios. O runtime garante no máximo um negócio por organização; memberships e
seleção legadas são preservadas. Staff é independente de cadastro de negócio.
Um número WhatsApp de cliente ativo por negócio na primeira versão.

## Decisões atuais sobre IA, materiais e prévias

- **Aceite único entregue localmente (C01):** em Plano e acesso, antes do
  checkout, o cliente concorda uma vez com IA para interpretação, texto, imagem
  e transcrição. Contas existentes recebem o mesmo passo. Não há permissões por
  fornecedor em WhatsApp ou Informações e preferências. Credenciais, plano,
  orçamento e versões são controles internos. Aceitar não confirma pagamento.
- **Envios WhatsApp preservados (C04/C05):** materiais associados ficam sem
  expiração automática; histórico e API não oferecem sua exclusão. A troca de
  número não interrompe material já associado; a entrega simulada usa o novo
  vínculo. Envio real de candidata ainda falta. Eventos técnicos não atribuídos
  e uploads órfãos têm limpeza separada.
- **Acervo:** fotos desatualizadas de item/espaço podem ser removidas. A cópia
  explícita de uma foto do WhatsApp cria outro objeto; preservar o envio não
  cria uma ficha de produto, fato confirmado, memória pesquisável ou skill.
- **Mudanças durante criação (C06/C07):** aguardar processos iniciados, cancelar
  a fila que não começou e impedir novos inícios até aplicar a mudança de kit,
  foto ou contexto. A prévia anterior continua para revisão, identificada como
  anterior à alteração. Os caminhos `visual_fake` e `visual_ai` compartilham
  essa coordenação dos escritores atuais.
- **Continuidade e preservação (C08/C09):** a criação `visual_fake` ou `visual_ai` já admitida
  tem prova durável para concluir após o vencimento financeiro e permitir revisão
  privada. Bloqueio financeiro explícito e revogação de patrocínio continuam
  distintos do vencimento. Novas criações e publicação exigem plano vigente.
  Prévias concluídas e sua proveniência saem da limpeza automática por prazo;
  tentativas visuais iniciadas sem resultado resolvido também são conservadas.
- **Autor sem acesso (C10), implementação de suporte adiada em 29/10:** outro
  owner não pode substituir nem descartar sua alteração pendente. Essa proteção
  permanece; a recuperação staff fica para evolução de gestão de acesso/suporte.
  A exceção continua bloqueada e não impede fechar a fatia simulada validada.

A admissão visual verifica proposta, fontes, usuário/membership, aceite e plano
sob locks na ordem proposta → visual → comercial, antes de gravar o run. A reserva
financeira continua em outra transação/role: falha ou confirmação perdida mantém
o run bloqueante e não libera repetição. A recuperação local pode encerrar uma
tentativa obsoleta/falhada somente após tornar a prévia terminal e comprovar,
sob locks correlator, ausência de tentativa e de reserva, inclusive não vinculada.
O commit confirmado precede a conclusão owner; confirmação perdida permite repetir
somente a reconciliação. Uma duplicata viva não derruba a criação original.
`DatabaseVisualEffectGuard` agora reúne admissão, fontes, reserva, claim única e
commit privado com prova owner e revalidação correlator. Roteiro aguarda runs em
transação separada proposta → visual; writers financeiros participam do comercial.
Troca de telefone não muda a identidade de fonte já atribuída. O protocolo dos
escritores atuais está no [desenho da guarda](design/BL04-effect-guard.md).
O modo persistido `visual_ai` agora liga essa guarda ao adapter OpenAI por um
runner e workflow próprios; os testes usam transporte HTTP simulado. A ativação
continua desligada por padrão. A parte 3 executou uma chamada real de imagem com
Jev, guarda, kit/logo e prévia privada, sob autorização delimitada; ver
[evidência](evals/bl042-first-product-image-2026-10-29.md).
C08 cobre `visual_fake` e `visual_ai`; o
renderer local legado ainda não recebe a mesma exceção de conclusão. `expires_at`
continua delimitando criação/aprovação, sem apagar uma prévia concluída. URL
assinada, validade factual e prazo de aprovação permanecem separados da preservação.
Revisão histórica não depende de manter a execução visual habilitada.

O prazo de exclusão após encerramento da conta foi explicitamente adiado para
essa fase; não implementar exclusão automática nesta etapa (P03). Vencimento do
plano não equivale a encerrar conta nem a perder membership.

## Estado implementado e limites

| Área | Existe localmente | Falta demonstrar ou entregar |
| --- | --- | --- |
| Fundação e identidade | FastAPI, PostgreSQL/RLS, auth própria, sessões, recuperação, e-mail HTML, onboarding, MFA/convites de staff | Homologação de operação e segurança em staging/produção. |
| Contratação | Stripe sandbox, webhook/jobs/reconciliação, patrocínio e aceite único versionado por negócio | Contratos comerciais definitivos, franquias e cenários externos restantes. Cadastro e retorno de checkout não ativam plano. |
| WhatsApp | Inbox assinada/cifrada, vínculo, correlação, processamento, transcrição configurável e preservação de materiais | Meta oficial, envio real de candidata e conversa completa ainda não homologados. |
| Contexto e texto | Fatos/preferências versionados, propostas/roteiros, adapter editorial, reservas/tokens e projeção administrativa restrita | Qualidade comercial, conversa com memória, pesquisa ampla e skills executáveis. |
| Skills de geração | Briefing com skill de feed/story selecionada e versionada e direção para peça integral em desenvolvimento/teste. | Descoberta de referências externas, avaliação real, tratamento de múltiplos fatos e homologação permanecem pendentes. |
| BL01/BL02 | Vitrine fictícia de cafeteria, escolha/edição de kit e logo privado; kit/logo aplicados à primeira imagem real controlada | Kit `public_demo` não tem liberação comercial; fidelidade precisa de revisão. |
| BL03.1/BL03.2 | Catálogo/fotos privadas e uso seletivo de fontes na primeira imagem real controlada | Importação de cardápio é BL03.3 futura; qualidade/fidelidade do contexto aplicado ainda requer avaliação. |
| BL04 | Caminho `visual_ai`, Jev, guarda e adapter exercitados com uma imagem real de feed e prévia privada preservada | BL04.3: revisão de post/story, fidelidade e custo por peça aceita. Uma chamada não comprova qualidade, fatura ou margem. |

A implementação de referências tem uma cadeia privada Google/Jev apenas com
provedores simulados, reservas e recuperação idempotente, além de contratos
preparatórios para resultados e aprendizados. Ainda faltam admissão da pesquisa
real, recomendação dos três destaques, Apify, publicação, análise e integração à
geração; nenhuma fase completa de referência real foi entregue nesta fatia.
A admissão por dispositivo e o carregamento privado da versão autorizada foram
testados, mas ainda não estão ligados a uma execução real.
O titular confirmou a combinação de semelhança e nota nos três destaques, o
desempate por semelhança na décima posição, os raios 5/20/50, a busca manual
após o prazo, a exclusão do próprio negócio e o compartilhamento entre titulares. A análise deverá considerar
todas as imagens acessíveis de carrosséis e aprender tom, temas, formatos e
elementos visuais; essas capacidades ainda não estão integradas ao produto.
Se o Jev não resolver o empate, prevalecerá a ordem Google; sua conclusão
estruturada de semelhança poderá ser armazenada para recuperação. Um perfil
recém-escolhido será analisado após confirmação e atualizado a cada seis meses.
O endereço e as coordenadas do próprio negócio permanecem no cadastro. A comparação
para excluí-lo possui testes isolados, mas não está integrada à busca real.
| F04/F06 | Prévias técnicas estáticas/vídeo, candidata, revisão e publicação simulada com versão/hash | Ajuste não regenera automaticamente; candidata WhatsApp e Instagram reais pendentes. |
| F08 | Compose, CI e workflow manual de deploy preparados | AWS/staging, recuperação coordenada, observabilidade operacional e capacidade não homologadas. |

Os ensaios em [evals](evals/) são evidências datadas, não features ou aceites
comerciais. As imagens reais de IA de 27/10 e 28/10 foram geradas em ensaios
isolados, fora do worker do cliente. Não comprovam fidelidade, margem ou custo
mensal. Consultar perfil público não concede direitos sobre o material observado.
A [execução de 29/10](evals/bl042-first-product-image-2026-10-29.md) percorreu o
worker do produto e exportou o JPEG pela API autenticada e S3 privado. Meta de
entrada/prova de canal foram sintéticas e a entrega da candidata permaneceu
simulada; isso ainda não comprova conversa WhatsApp completa ou homologação.

## Jornada web vigente

| Área | Finalidade |
| --- | --- |
| Início | Resumo e orientações com estados reais do negócio. |
| Plano e acesso | Aceite único do serviço, assinatura, patrocínio e situação financeira. |
| WhatsApp | Telefone/SMS, vínculo e histórico preservado de envios como consulta secundária. |
| Sobre meu negócio | Informações e preferências, Produtos e serviços e Meu espaço. |
| Conteúdos | Acompanhar propostas/prévias e decisões disponíveis; simulações identificadas. |
| Kits visuais | Explorar, escolher e editar a direção visual. |

Organização/negócio ativos são compartilhados em memória; a autorização é
verificada na API/RLS. `/app/content` é a rota vigente; `/app/ideas` redireciona
para ela e `/app/guide` para Início. `/app/phone` é utilitária do WhatsApp.
`/app/editorial-lab` mantém os controles técnicos só no build DEV. O valor
histórico `posts_per_week` é preservado, sem campo manual de frequência.

## Próxima entrega e sequência

Em 30/10/2026 o proprietário direcionou a geração a construir um briefing com
pedido, fatos, kit, acervo pertinente, skill do formato e referências externas
aceitas quando existirem; pedir ao modelo a peça completa, conferir o resultado
e disponibilizar trace privado. A indicação manual e seu snapshot foram
implementados localmente, assim como descoberta e aceite de sugestões automáticas.
O proprietário decidiu descontinuar novas
gerações pelo acabamento antigo de fundo e layout fixo; registros anteriores
podem ser preservados sem gerar novas peças por esse caminho. A ideia posterior
de usar padrões/fontes das referências como sugestões editáveis para o kit
está registrada no [plano de referências](design/skills-e-referencias-editoriais.md).
O proprietário definiu que promoções, ofertas e horários para uma peça vêm do
pedido e de suas revisões no WhatsApp, sem cadastro desses fatos na interface.
Por exemplo, o pedido promocional de R$ 19,90 vale para a peça mesmo com preço
de catálogo de R$ 25; não se pergunta sobre a diferença nem se altera o catálogo.
Desconto percentual depende de preço de catálogo válido; dados ausentes ou
ambíguos pedem esclarecimento. Um campo simples de características gerais do
negócio permanece. O titular autorizou remover as informações antigas dessa
área sem preservar histórico. A mudança ainda não foi implementada: o fluxo
WhatsApp/Jev não extrai e vincula esses fatos integralmente. O código anterior
de promoções de catálogo continua para compatibilidade histórica; novos
snapshots editoriais as ignoram.

O novo caminho local de feed/story reúne briefing com skill, pedido, contexto,
kit, fotos pertinentes e logo; a referência visual demo do kit é enviada
separadamente. O modelo produz a peça inteira, sem overlay fixo. O trace fica
cifrado e acessível ao proprietário; aprovação por API requer conferência humana
dos itens e hash da imagem. O checklist ainda não existe no WhatsApp/web. O uso
real segue restrito a desenvolvimento/teste, desligado por padrão, sem prova de
qualidade comercial. Os ensaios diretos pagos de 30/10 ocorreram fora do worker
e antes das correções atuais. Previews antigas
concluídas ficam acessíveis; jobs antigos não são reexecutados.

Em 29/10, três negócios fictícios foram exercitados pelo fluxo local com Jev e
geração de imagem reais, produzindo seis prévias A/B. Todas omitiram o preço
confirmado solicitado; naquele ensaio a skill atuava só na imagem. A geração
integral posterior recebe texto natural com verificações de valores e origem,
sem fallback fixo. Essas verificações não provam verdade semântica. Ainda não há
interpretação estruturada que garanta que um pedido de preço seja obedecido;
o prompt solicita seu uso, mas a resposta pode omiti-lo. A validação com
seleção factual do produto e a avaliação do efeito editorial da skill
continuam pendentes.
[Evidência](evals/three-business-visual-ab-2026-10-29.md).

Um ensaio isolado de 29/10 gerou seis imagens com modelo editorial real: quatro
exibem preço; nas duas de manicure ele aparece só na legenda. Café e delivery
receberam copy artificial com “apresente”. Cada par compartilhou a copy; a skill
atuou só na imagem. O teste não percorreu seleção factual ou jornada completa e
não comprova qualidade comercial. [Resultado](evals/editorial-copy-visual-after-2026-10-29.md).

O primeiro ensaio autorizado de texto foi interrompido com resultado incerto;
custo desconhecido e hold mantido. Um segundo ensaio, visual e independente,
concluiu duas peças fictícias com e sem skill para revisão, sem comprovar ganho
geral ou execução pelo produto. [Evidência visual](evals/skills-visual-comparison-2026-10-29.md)
e [tentativa anterior](evals/skills-paired-attempt-2026-10-29.md).

No repositório `meu-braco-direito-skills`, as duas skills iniciais orientam
briefings de feed/story, sem gerar arquivo ou publicar. A validação estrutural e
dois exercícios independentes com dados fictícios passaram; não houve comparação
controlada com baseline, geração paga ou avaliação comercial. Um ensaio posterior
identificou ambiguidade não esclarecida em story; a instrução foi ajustada e uma
repetição independente fez a pergunta. Não prova qualidade geral. Seus casos e
protocolo preparam a próxima avaliação.

1. **Skills e geração:** estudar e estruturar skills para feed e story; comparar
   geração com e sem elas em casos fictícios e provedores simulados, integrando
   versões aprovadas ao produto. Kit, acervo e fatos do negócio são suas fontes.
2. **Referências externas:** permitir indicação de perfis pelo cliente e pesquisar
   automaticamente negócios semelhantes em destaque; avaliar fontes, métricas e
   uso de padrões sem copiar. Places é a fonte escolhida para estudar a busca
   inicial e Apify é previsto para enriquecimento de perfis; custos, cobertura e
   vinculação técnica ainda precisam ser verificados. Jev deve avaliar
   semelhança e eliminar candidatos inadequados antes da pontuação de reputação
   dos restantes, além de destacar até três recomendações entre os até dez
   candidatos exibidos, mostrando critérios e nota; não é fonte de dados nem acesso direto ao
   Instagram. Avaliações do estabelecimento não medem engajamento social.
3. **BL04.3:** revisar o feed produzido e completar post/story pelo produto com
   titular e fontes consentidas; medir fidelidade, texto, legibilidade, rejeições
   e custo por peça aceita, incluindo refações. Novas chamadas exigem autorização
   própria; a autorização delimitada de US$ 1 não ativa uso recorrente.
4. **BL05:** fechar WhatsApp como jornada principal de mensagem → prévia → ajuste
   → aprovação → publicação simulada, incluindo iniciativa sem mensagem e pausa.
5. **Piloto:** homologar Meta/Instagram, aplicar franquias F07 e operar staging,
   observabilidade e recuperação F08. A Meta pendente não impede testes locais.
6. **Expansão:** BL03.3 importa cardápio como rascunho; BL06 amplia kits/nichos e
   catálogo/CDN. Avatar/voz e multicanal seguem fases próprias.

A [proposta por fases](design/skills-e-referencias-editoriais.md) detalha os
gates, a pesquisa automática e as decisões ainda abertas. A atualização
documental não autoriza gasto nem comprova os trabalhos ainda pendentes.

Foto e story são os formatos iniciais; vídeo e suas franquias/preço permanecem
para definição posterior. R$ 99/mês e teto total de R$ 50/cliente/mês orientam
medição, sem margem comprovada. Avatar/voz sintética ficam após o primeiro
piloto. HyperFrames/Remotion e outros estudos são candidatos, não integrações.
A aquisição por vídeos longos dos três sócios segue estratégia comercial; a
meta de 200 mil clientes orienta capacidade gradual, sem comprovação atual.

`visual_ai` exige `VISUAL_AI_MODE=openai`, `VISUAL_AI_EXECUTION_ENABLED=true`,
reserva positiva por tentativa, tetos mensal por tenant e agregado suficientes,
chaves de provedor/criptografia e enforcement do aceite único C01. Os nomes de
variáveis usam o prefixo `MEU_BRACO_DIREITO_`; o padrão é flag desligada e reserva
zero. A API usa apenas o pool owner; o worker exige seu pool correlator restrito.
O dispatcher usa ID estável por prévia e lease de 12 minutos, sem redispatch do
efeito visual incerto. A resolução automática do item exige a configuração Jev
existente, com credencial/orçamento próprios; correspondência lexical não a substitui.

## Arquitetura, validação e continuidade

Backend Python modular, FastAPI, PostgreSQL compartilhado/RLS, Temporal e S3;
React em `local-spark-web`. API, dispatchers e workers escalam separadamente.
Redis não é dependência ativa; não adicionar outro runner para os processos de
Temporal. Sem rede sob row lock e sem IO em workflows determinísticos.

A [análise da jornada WhatsApp e orquestração](design/arquitetura-jornada-whatsapp.md)
documenta processos, workflows e limites atuais, diferencia o percurso de uma
saga clássica e registra recomendações para discussão, sem decisão de separar
serviços ou repositórios.

Negócios/kits usam auditoria transacional; relay, tabelas e handlers antigos
ficam só para compatibilidade, sem novos recibos de CRUD. Auth é própria;
access token em memória e refresh HttpOnly. Staff/MFA não equivale a owner.
Os modelos atuais são configuração, não escolha comercial definitiva. Contexto
versionado não treina automaticamente modelos e tokens não são COGS monetário.

Evidência anterior de aplicação: 1.583 testes backend e complemento de 24 testes
com sete casos novos; cobertura final de 100% de linhas/branches. Web: 360 testes,
100% nos quatro critérios, build e três jornadas Chromium. Evidências datadas
no [CHANGELOG](CHANGELOG.md). A parte 1 passou em `make ci`: **1.829 testes**,
**100% de linhas e branches** (9.284 statements e 2.550 branches), Ruff/formatação
e mypy (149 módulos). PostgreSQL `_test` restrito e Temporal locais cobrem admissão,
continuidade, preservação, autoria, recuperação entre commits e confirmações
perdidas, tentativa tardia, orçamento concorrente e fontes kit/logo. Não houve chamada
paga, novos grants ou homologação externa. A guarda concreta também cobre roteiro,
relink por outro owner, acesso financeiro e prazo factual após locks. Web:
**365 testes e 100% nos quatro critérios**, build/formatação e três jornadas
Chromium (laboratório pendente, conteúdo e aceite).

A parte 2 acrescenta testes da API até `VisualGenerationWorkflow`, runner,
adapter real com transporte HTTP simulado, acabamento e revisão privada, com
PostgreSQL/Temporal locais. `make ci` aprovado: **1.914 testes**, **100% de
linhas e branches** (9.394 statements, 2.582 branches), Ruff/formatação e mypy
(151 módulos). Web: **375 testes**, **100% nas quatro métricas**, build/formatação
e **quatro jornadas Chromium** na árvore final (conteúdo local/IA, laboratório e
aceite). As contagens anteriores são evidências da parte 1. A migration 0059 foi
aplicada somente ao `_test`, sem migrar o banco da aplicação, chamar fornecedor
pago ou alterar grants naquela entrega.

A parte 3 concluiu uma imagem real de feed com `gpt-image-2.5-flare-2026-09-08`,
Jev real e acabamento determinístico do kit/logo, preservando candidata pendente
e publicação nula. Estimativa por uso: **US$ 0,029701**, incluindo duas
interpretações Jev; não é fatura. A reserva visual de **US$ 0,99** continua
`uncertain`, com custo efetivo desconhecido, e o run terminou. A primeira entrada
resultou em story e o wrapper bloqueou antes do HTTP de imagem; prova de zero
submissões permitiu reconciliar a reserva antiga em zero, preservando tentativa
e auditoria. Uma nova origem esclarecida gerou o feed sob a mesma autorização;
não houve edição manual de roteiro nem aprovação/publicação. A migration 0059
agora também foi aplicada ao banco local da aplicação para essa execução.
Flags persistentes seguem desligadas, sem novos grants ou código de produção.
`make lint types` aprovado (151 módulos) e **94 testes unitários dirigidos**
aprovados; código de produção inalterado. O `make ci` acima é da parte 2 e não
foi repetido nesta execução operacional. Com geração `disabled`, flag desligada
e limites zero, owner listou/baixou o mesmo hash; acesso anônimo retornou 401.
Os processos temporariamente habilitados foram encerrados. Uma imagem isolada
não substitui as provas C08/C09 da suíte ou a revisão humana de BL04.3.

Diretórios/remotos continuam `local-spark-platform` e `local-spark-web`, com marca
Meu Braço Direito, prefixo `MEU_BRACO_DIREITO_` e bancos renomeados conforme
[registro](product-rename.md). Operação em [operations](operations.md).
Atualizar PROJECT, SDD, fase e CHANGELOG em cada entrega; decisões novas entram
em [DECISIONS](DECISIONS.md), sem recolocar perguntas já respondidas na fila.

## Atualização de 04/11 — endereço próprio

O cadastro próprio de endereço possui API autenticada GET/PUT, versões imutáveis,
conflito otimista, replay de operação, RLS e audit/outbox. Nenhuma origem de pesquisa
é promovida automaticamente a endereço da loja. Geocodificação, ponto permanente
comprovado, interface e vínculo à descoberta continuam pendentes. Ver
[contrato](design/business-address.md).

## 04/11/2026 — Vocabulário de atividade para a busca

A classificação pré-Google agora dispõe de taxonomia versionada da Table A
(478 tipos), adapter Jev com uma chamada identificada e guard antes da rede.
A escolha considera o ramo informado, sem fallback `restaurant`, e retorna
abstenção quando necessário. O [design](design/google-place-type-mapping.md)
descreve limites, fontes e validação. Execução durável e contabilização são
conectadas na fatia 0106; os testes locais não demonstram busca real concluída.

## Atualização de04/11 — localização própria integrada

A [geocodificação do endereço próprio](design/business-geocoding.md) conecta API,
outbox, Temporal e adapter com orçamento, sem chamada paga. Correspondência
precisa resolve automaticamente; ambiguidade aceita escolha explícita do ponto.
Pesquisa manual reutiliza a localização e inclui seu custo no limite da busca.
A admissão vincula nome/endereço atuais por HMAC e a publicação revalida a identidade;
origem GPS permanece separada. A orquestração dos demais fornecedores e o ensaio
real continuam pendentes desta fatia.

## Integração de referências em 04/11 — resultados e custos

A API permite consultar resultados reais publicados, confirmar de uma a três
referências e corrigir o Instagram associado. A revisão de escolhas ausentes
fica vinculada ao primeiro resultado da nova rodada após seis meses. A troca
de raio no mesmo ciclo não solicita essa revisão. O publicador interno usa
somente IDs, notas próprias e perfis já obtidos; ainda depende do executor real.

O teto por pesquisa agora soma o consumo de todos os titulares ativos do negócio.
O run Apify pode ser recuperado por GET sem repetir a coleta, e o custo informado
pelo run terminal atualiza a reserva de forma idempotente. Contrato Compass
corrigido para os campos oficiais; nenhum POST pago foi realizado. As migrações
0101–0105 estão integradas no código; o banco local ainda precisa de atualização.
A suíte completa da retomada encontrou duas falhas e cobertura de 99,38%; a
correção e nova validação integral continuam pendentes.

## Coleta de publicações — adapter integrado em 04/11

Instagram feed e download de imagens possuem opt-in de rede, guardas, limites e
contrato oficial. Foram retirados campos de entrada não suportados pelo coletor.
Os dados de publicações ficam somente em memória; os padrões derivados serão
persistidos pela análise ainda em implementação. A guarda financeira e os custos
terminais usam a mesma semântica do coletor de contatos. 357 testes unitários
passaram com cobertura integral dos cinco módulos; nenhuma coleta paga realizada.

### Configuração do piloto de referências, 04/11

O script `scripts/configure_reference_pilot.py` prepara a política local e o
piloto acumulado de US$ 5, sem zerar consumo ou habilitar fornecedores. Plano
por padrão; aplicação exige banco local/admin separado e preserva configurações
divergentes. 14 unitários e três testes SQL aprovados; execução real ainda pendente. Ver
[operação](design/reference-pilot-operations.md).

## Retomada da validação — 04/11/2026

A revisão do CI removeu trechos inacessíveis de criação local e execução
editorial sem skill após C17/C18, preservando replay e consulta histórica,
rejeições duráveis e controles de acesso/custo. Os testes deixam de fabricar
sucesso do caminho descontinuado. Foram aprovados 3.555 testes relacionados;
a cobertura do recorte foi 98,31%, com guards adicionais posteriores. O CI
integral final continua pendente. [Evidência](evals/ci-resume-2026-11-04.md).

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

### Retomada — identidade própria e resposta vazia (0107)

A descoberta agora persiste a conclusão própria de identidade na mesma transação das notas e da semelhança. Uma correspondência clara exclui a loja; ambiguidade oferece apenas Place IDs ao titular e retoma a mesma execução após sua decisão. Titulares ativos compartilham essa decisão sem compartilhar tokens de fornecedores.

Google sem resultados amplia automaticamente 5 → 20 → 50 km, sem mudar a preferência salva nem consultar novamente um raio ocupado. A família compartilha o teto financeiro e reutiliza o cache. Uma rodada inteiramente vazia e ainda não confirmada permite tentar novamente, preservando escolhas anteriores; um ciclo já confirmado continua respeitando seu prazo. Ainda faltam a integração completa de análise/agenda de publicações, consumo dos aprendizados e ensaio externo configurado.

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

Contrato e validação em [integração de referências na geração](design/reference-generation-context.md).
177 testes unitários e 13 casos PostgreSQL passaram nos recortes desta fatia,
incluindo leitura 0108 e geração visual com HTTP simulado. A agenda completa e
o CI integral continuam pendentes; essas provas não demonstram qualidade comercial.

### Aprendizados das referências — persistência e agenda, 04/11

A fatia 0108 liga referências manuais e sugeridas escolhidas a associações
versionadas e janelas duráveis de análise. Aceite e troca de perfil agendam a
primeira análise; atualizações posteriores derivam do aceite a cada seis meses.
O banco guarda padrões próprios comprovados, metadados e, quando disponível na
resposta já obtida, o nome do perfil Apify. Não guarda publicações ou imagens.
O leitor de status é somente leitura, e a captura para geração permite revalidar
seleção e associação antes de efeitos pagos. Execução Temporal, snapshot e UI são
integrados nas fatias adjacentes; o ensaio real e CI final continuam necessários.
Veja [persistência e agenda](design/reference-learning-storage.md).

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
