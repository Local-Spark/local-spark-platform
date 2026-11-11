# Fases de implementação

**Prioridade visual atual — etapa 4, 10/11/2026:** transcrição local automática
por palavra e ligação ao motion implementadas/testadas. Dependências/modelo
aguardam provisionamento para a prova; sem nova peça. Comparação só após OK.
[Escopo e limites](../design/motion-fala-alinhada-2026-11-10.md).

**Histórico — etapa visual 3, 10/11/2026:** objeto realista em camadas
implementado na skill v10 e testado com o fluxo de imagens existente. Direção e
especificação preparadas; sem asset gerado ou novo MP4. Etapa 4 aguarda OK.
[Escopo e limites](../design/motion-objeto-realista-2026-11-10.md).

**Histórico — etapa visual 2, 10/11/2026:** fundo narrativo implementado
na skill v9 com exemplo executável e pacote offline. Etapa 3 aguarda OK; sem
novo MP4 ou prova visual automática. [Detalhes](../design/motion-fundo-narrativo-2026-11-10.md).

**Histórico — etapa visual 1, 10/11/2026:** etapa 1 (tratamento da gravação)
implementada em skill/runtime e testada; sem novo MP4. Etapa 2 (fundo vivo)
aguarda OK do titular. [Escopo e limites](../design/motion-tratamento-gravacao-2026-11-10.md).

**Atualização da etapa 1 — 10/11/2026:** geração compacta, metadados de falha e
limpeza de captura implementados; comparação MP4 local concluída. Qualificação
paga do contrato novo e causa dos reinícios do ambiente ainda pendentes.
[Resultado e limites](../design/motion-confiabilidade-geracao-captura-2026-11-10.md).

**Prioridade de fechamento, 10/11/2026:** os ajustes de alternância, recorte e crítica estão implementados, mas as duas
gerações da prova falharam antes do render. Fechar saída completa/validável e
recuperação limitada antes de liberar a jornada; comparação local não encerra esse gate. A sequência proposta
posterior está em [fechamento do produto de geração](../design/fechamento-produto-geracao-2026-11-10.md):
jornada do Reel com ajuste e nova versão, fala alinhada, story em vídeo, carrossel,
qualidade por formato e operação. Aceite da peça/download não publicam; postagem
continua posterior. Seções anteriores abaixo são históricas onde divergirem.

## Roteiro vigente — atualizado em 09/11/2026

A [etapa 3 foi concluída no recorte demonstrado](../design/execucao-ate-etapa-7-2026-11-07.md):
legibilidade do [1c](../evals/ensaio-revisao-reel-1c-2026-11-08.md) reconhecida e
preferência humana **“B ficou melhor.”** no [Giz](../evals/ensaio-refinamento-motion-giz-2026-11-09.md).
O Giz é refinamento com feedback/referência adicionais; não prova autocrítica
do pedido original ou ganho universal. Áudio e cada critério não receberam
aprovação humana isolada. Custos são estimativas de APIs, sem COGS completo.

A [fatia local do Reel (4)](../evals/qualificacao-integracao-reel-2026-11-09.md)
está implementada e tecnicamente qualificada: quatro replays Linux, prova
integrada com modelo/crítico simulados, backend 5.353 testes/100% e web 524/100%.
Os dez workers foram restaurados. Isso não conclui ativação comercial ou
homologação do gerador pago; configuração continua desativada por padrão e
restrita a materiais sintéticos. Limites de entrada/imagens, deploy e contrato
para clientes reais permanecem pendentes. Nenhuma nova chamada paga.

A próxima fatia autorizada é **demais formatos (5)**, ainda não implementada.
O [desenho de imagens](../design/ciclo-revisao-imagens-2026-11-09.md) e a
[matriz](../design/v0-motion-etapa-0-formatos-e-casos.md) registram o trabalho.
A sequência segue WhatsApp (6) e piloto/comercial (7). Intensa/Dog/Luma continuam
referências; operação paga incerta não é repetida e 1c não vira padrão criativo.

Piloto: autoatendimento com cobrança, sem participantes reais definidos. Os
quatro casos fictícios orientam validação; preço/franquias dependem de medição.
WhatsApp oficial integra a jornada real. Instagram automático fica posterior
ao piloto de geração, revisão e download. As demais numerações abaixo conservam
seu contexto histórico.

## Histórico da frente de revisão — 06/11/2026

O próximo ensaio é o [ciclo de revisão de Reel](../evals/plano-ciclo-revisao-motion-2026-11-06.md),
em Python/API, com crítica por evidência, até duas correções e avaliação humana
comparativa. O protótipo privado existe, sem comparação concluída; a rodada Intensa/Dog/Luma tem autorização
de até US$ 6,75 em reservas e 15 chamadas, conforme o plano. O clipe
pessoal já entregue aguarda avaliação. Story/carrossel, integração por Temporal e
jornada de WhatsApp seguem após qualificar o caminho; postagem é fase posterior.
O gate BL04.3 de feed/story continua aberto. As ordens datadas abaixo são
históricas onde indicarem outra próxima frente.
[Resultado parcial](../evals/ensaio-ciclo-revisao-motion-2026-11-06.md):
crítica v2 incerta, sem refação ou avaliação comparativa concluída.

## Prioridade de conteúdo e motion — 05/11/2026

O titular priorizou concluir as peças finais antes de tratar a integração de
postagem. A sequência corrente está no [plano da v0 de geração](../design/plano-v0-imagens-video-motion-2026-11-05.md):
fechar a base/CI, preservar e empacotar fontes, ensaios rápidos, contratos e
roteiro, mídia/transcrição, seleção automática e Reel, story, carrossel, revisão
e ajustes/download, qualidade e operação da geração. A viabilidade Meta e a
integração de postagem F06 ficam para depois; não bloqueiam esta entrega.
Aprovação da peça final não autoriza publicação futura. Os marcos anteriores
abaixo descrevem a evolução do projeto, não substituem essa ordem de trabalho.

## Atualização de referências — 04/11/2026

A descoberta Google, classificação Jev, perfis Apify, seleção, ciclo semestral,
análise e snapshot para criação estão integrados localmente até a revisão 0111.
O [piloto](../evals/reference-feature-pilot-2026-11-04.md) comprovou lista de dez,
três destaques e padrões de referência manual no contexto de geração. A decisão
final inclui apenas autoria direta e usa capa/legenda de vídeos/Reels; o CI
posterior à extensão passou em 4.734 testes/100%. Os detalhes atuais estão no
[PROJECT](../PROJECT.md) e na [BL04](BL04-context-and-ai-production.md).

Na sequência registrada em 04/11, a próxima fatia era BL04.3: avaliar
post/story com kit, acervo e referências pelo produto, medindo fidelidade e custo
por peça aceita. O piloto de descoberta/análise não substitui essa avaliação.
Os [quatro passos e o ponto de retomada](BL04-context-and-ai-production.md#bl043--qualidade-e-economia-pendente)
estão detalhados no SDD ativo. Começar pelo inventário dos aprendizados e pelo
plano comparativo, antes de executar a nova rodada paga.
BL05 continua sendo a etapa posterior de jornada WhatsApp e proatividade.

Atualizado em **29/10/2026**. Este índice distingue **o que existe no ambiente
local**, **a próxima fase** e os gates para piloto/produção. A v0 completa
continua distribuída entre F00–F08; a trilha [BL](BL-brand-library.md) define
a ordem de produto para aplicar um kit visual e o acervo do negócio a uma
peça nova.

## Estado atual

- F00/F01: fundação, identidade, onboarding, cobrança sandbox, área do cliente
  e admin mínimo locais. Homologação externa e staging continuam pendentes.
- F02: webhook, vínculo do remetente, recibos de texto/foto/áudio/vídeo,
  histórico preservado de envios associados e respostas limitadas locais.
  A restrição Meta observada no smoke impede afirmar homologação real.
- F03: fatos/preferências, ideia e roteiro versionado com edição local.
  Pesquisa ampla, qualidade comercial e sugestão proativa ainda pendem.
- F04/F06: prévias estáticas/vídeo locais e candidata/aprovação/publicação
  **simuladas**. F03 congela kit; BL04 recupera acervo no worker experimental e
  aplica kit à simulação. `visual_ai` já liga o fluxo ao adapter real, com
  validação por HTTP simulado e uma imagem real de feed concluída na parte 3,
  sob fontes/teto autorizados e sem publicação. Meta/canal continuaram sintéticos.
- BL01: um kit fictício de cafeteria e simuladores públicos/cliente locais.
  Ver a vitrine não é escolher ou editar o kit.
- BL02: seleção e edição guiada do kit na área autenticada, logo privado,
  prévias ampliáveis, rascunho/confirmado e histórico por negócio locais.
- BL03.1/BL03.2: catálogo manual e fotos privadas de item/espaço locais;
  BL03.3 importação de cardápio posterior.
- Contratação: um negócio por organização (`0057` aplicada), cobrança por
  organização e aceite único de IA antes do checkout. Sem check individual
  de transcrição, modelo ou fornecedor no WhatsApp/Sobre meu negócio.

## Marco de 29/10 e decisões então pendentes

A fase ativa é [BL04](BL04-context-and-ai-production.md). A parte 1 entrega a
guarda concreta de fontes, aceite, acesso, reserva/claim e resultado privado,
incluindo roteiro/cobrança e troca de telefone, com roles existentes e mocks.
A **parte 2** conecta `visual_ai` na persistência/API ao dispatcher, workflow,
worker, runner e adapter, com transporte HTTP simulado nos testes de PostgreSQL/
Temporal. A validação final da parte 2 foi aprovada. A **parte 3** concluiu uma
imagem real de feed para Café do Cedro, com Jev real, teto total autorizado de
US$ 1 e sem aprovação/publicação. Estimativa total US$ 0,029701; reserva visual
incerta, sem fatura. A execução continua desligada por padrão e a autorização
não é recorrente. [Evidência](../evals/bl042-first-product-image-2026-10-29.md).
A próxima fatia prioriza **skills de geração para feed e story**: estudo,
especificação e comparação simulada com o baseline, seguidos de integração
versionada ao produto. Depois, pesquisar referências indicadas pelo cliente e
descobertas automaticamente pela plataforma, avaliar fontes e aplicar padrões
pertinentes à geração sem copiar. A pesquisa não precisa esperar o fechamento
integral do gate comercial **BL04.3**, que continua exigindo avaliação de
post/story pelo titular e custo por peça aceita. Depois BL05 fecha WhatsApp como
jornada principal e proatividade. Detalhes e dependências no
[plano de skills e referências](../design/skills-e-referencias-editoriais.md).
Parte 3 foi validada com 94 unitários, lint/types e leitura/hash com geração
desligada; o último CI completo permanece o da parte 2.

A admissão `visual_fake` e `visual_ai` revalida fontes, aceite e plano sob locks; depois de
admitida, a criação conclui e permite revisão privada após vencimento financeiro.
Novas criações/publicação esperam renovação. Concluídas e proveniência são
preservadas sem limpeza por prazo e revisáveis com execução desligada; a janela
de aprovação continua independente. Tentativa real usa ID Temporal estável e
lease de 12 minutos; resultado incerto não dispara outro efeito.
O renderer local legado ainda tem limites próprios. Escritores atuais têm o
[protocolo documentado](../design/BL04-effect-guard.md); futuras capacidades de
acesso precisam participar dele antes de serem adicionadas.
Outro owner não assume pendência do autor original. A implementação da recuperação
staff C10 foi adiada pelo proprietário em 29/10, para evolução de gestão de acesso
e suporte; não bloqueia o fechamento do recorte simulado. A exceção permanece
bloqueada até a entrega futura. Retenção após encerramento
fica para essa fase, sem nova exclusão automática agora. Detalhes e lacunas em
[decisões](../DECISIONS.md).

## Próximas entregas em ordem

| Ordem | Fase | Entrega demonstrável | Estado |
| --- | --- | --- | --- |
| 1 | [BL01](BL-brand-library.md#bl01--kit-piloto-e-vitrine-local) | Kit piloto de cafeteria, dez posts, stories, reel e vitrine. | Técnica local pronta; revisão comercial/direitos pendente. |
| 2 | [BL02](BL-brand-library.md#bl02--escolher-e-editar-o-kit-piloto-para-um-negócio) | Dono seleciona o kit e ajusta cores, fontes, logo, textos e composição guiada de feed/story/capa vertical; vê e confirma prévias versionadas. | Implementada localmente; gate comercial do kit segue pendente. |
| 3 | [BL03](BL-brand-library.md#bl03--acervo-progressivo-em-sobre-meu-negócio) | Dentro de “Sobre meu negócio”, cadastrar opcionalmente produtos/serviços e fotos reais do espaço; dado privado, confirmado e versionado. | **BL03.1/BL03.2 implementadas localmente; BL03.3 posterior.** |
| 4 | [BL04](BL04-context-and-ai-production.md#próxima-fatia-de-desenvolvimento) | Skills de feed/story e geração com kit/acervo. | Versões iniciais integradas; avaliação de ganho e qualidade comercial pendente. |
| 5 | [F03 — referências externas](../design/skills-e-referencias-editoriais.md) | Cliente indica perfis e plataforma descobre semelhantes; padrões próprios alimentam a criação. | Implementada localmente com Google, Apify e Jev; piloto executado e CI final aprovado, incluindo capas de vídeos. |
| 6 | [BL04.3](BL04-context-and-ai-production.md#bl043--qualidade-e-economia-pendente) | Avaliar post/story pelo produto, com fontes autorizadas e titular; medir pertinência, fidelidade, aceite e custo completo. | Gate comercial pendente; ensaio sintético isolado não o encerra. |
| 7 | [BL05](BL-brand-library.md#bl05--jornada-completa-local-ajuste-e-proatividade-mínima) | WhatsApp simulado e proposta sem mensagem percorrem prévia, ajuste, aprovação e publicação falsa com as mesmas regras. | Contratos F02/F04/F06 parciais já existem; integração pendente. |
| 8 | [BL06](BL-brand-library.md#bl06--ampliar-a-biblioteca-e-servir-o-catálogo-em-escala) | Kits de manicure e personal, catálogo público versionado em objetos/CDN e revisões por nicho. | Planejada após prova de reaplicação. |

BL02 e BL03 podem avançar com a Meta restrita. BL04 testa localmente com
mocks e, para fechar qualidade comercial, precisa de avaliação de titular
com material consentido. BL05 exercita integração e falhas locais; uso real
depende da homologação F02; F06 é necessária para a publicação posterior.
A expansão BL06 não precisa atrasar o primeiro
piloto de cafeteria, mas não deve anteceder uma peça personalizada aprovada.

O [roadmap de 27/10 até produção e expansão](../design/delivery-roadmap-2026-10-27.md)
preserva a ordem histórica de homologação, custo/franquia, AWS e piloto. O
roteiro de sete processos acima define a ordem atual e adia a postagem Instagram;
importação de cardápio, novos nichos, avatar e multicanal têm fases próprias.
BL03 atual entrega cadastro manual/fotos; [BL03.3](BL03-business-collection.md#bl033--importação-automática-de-fotos-de-cardápio-planejada)
extrairá dados de fotos de cardápio/tabela de serviços e preencherá o acervo
automaticamente como rascunho para conferência. Não bloqueia a primeira peça.

## Fases transversais até produção

| Fase | Escopo | Estado/gate |
| --- | --- | --- |
| [F00](F00-foundation.md) | Fundação, Postgres/RLS, Temporal e observabilidade base | Concluída localmente. |
| [F01](F01-identity-onboarding.md) | Identidade, onboarding, admin e cobrança mínima | Código local; staging/homologação externa pendentes. |
| [F02](F02-whatsapp-ingestion.md) | WhatsApp, materiais e confirmação | Local/mock; Meta real pendente. |
| [F03](F03-editorial-research.md) | Contexto, pauta, roteiro, cadência proativa e pesquisa | Contexto e pesquisa de referências locais integrados; proatividade e homologação comercial permanecem em fases próprias. |
| [F04](F04-media-recipes.md) | Receita visual, IA de imagem/vídeo, prévia e ajuste | Renderer local é baseline técnico; BL04 fecha primeira receita aprovada. |
| [F05](F05-avatar-generative-video.md) | Avatar, voz e cenas geradas | Avatar do cliente após o primeiro piloto comercial (P15), com consentimento, qualidade e orçamento próprios. |
| [F06](F06-instagram-publishing.md) | Aprovação, agenda, publicação e métricas Instagram | Fluxo falso local; Meta/Instagram reais pendentes. |
| [F07](F07-billing-reports.md) | Franquias, assinatura e relatórios honestos | Cobrança mínima F01.5 local; limite por formato e custo real antes do piloto pago. |
| [F08](F08-production-scale.md) | Deploy, segurança, suporte, recuperação e escala | Staging, backup/restore, capacidade e operação ainda pendentes. |

**Antes de um piloto real com postagem:** completar BL02–BL05 para as receitas
prometidas; fechar qualidade e custo por peça aceita com um negócio consentido;
homologar WhatsApp e Instagram oficiais; aplicar franquia/orçamento F07 e
operar staging F08 com logs, alertas e recuperação. A entrega atual de geração,
revisão e download não exige integração de postagem ou homologação Instagram.
Aprovação de peça é
distinta de confirmação de preço ou escolha do kit. Não prometer frequência,
venda, alcance ou canal não comprovados.

**Depois do piloto:** BL06 amplia nichos; F05 acrescenta avatar somente se
qualidade, consentimento e margem sustentarem o formato. Pesquisa de referências
de concorrentes foi antecipada para a sequência acima, com fontes permitidas e
evidência de ganho. A meta de 200 mil clientes orienta capacidade gradual F08,
não bloqueia a primeira coorte.

## Documentos de decisão

- [Biblioteca e kits](../design/brand-library.md): amostras públicas, kit
  aplicado e acervo privado separados.
- [Contexto e geração](../design/business-context-and-generation.md):
  snapshots, adapters, ledger e dados confirmados.
- [Qualidade criativa](../design/creative-production-quality.md): gates
  por receita e comparação IA/composição.
- [Skills e referências editoriais](../design/skills-e-referencias-editoriais.md):
  fases de geração, pesquisa de concorrentes e avaliação.
- [Cadência e planos](../design/editorial-planning-and-evidence.md):
  franquia do plano, recomendação explicável e evidência.
- [Decisões vigentes e abertas](../DECISIONS.md): aceite, retenção, acesso,
  recuperação de pendências e escolhas ainda dependentes de evidência.
- [SDD geral](../SDD.md) e [contexto vivo](../PROJECT.md):
  contratos e decisões correntes.

**Numeração histórica:** entradas até 26/10 chamavam a prova de reaplicação
de BL02, a expansão de BL03, a escolha de BL04 e o acervo de BL04.5.
A [trilha BL vigente](BL-brand-library.md#numeração-substituída) renumerou
esses marcos para seguir a dependência real. Changelogs antigos permanecem
registros do momento em que foram escritos.

As [versões anteriores à reconciliação](../history/2026-10-28-pre-documentation-reconciliation/)
preservam evidências históricas; a síntese vigente acima não transforma antigas
permissões por fornecedor ou exclusão de envios em trabalho a retomar.
