# Fases de implementação

Produto: cliente manda ideia/mídia **ou não manda nada novo**; a plataforma
planeja, cria com IA visual, pede aprovação pelo WhatsApp e acompanha sinais de
interesse comercial. A proatividade mínima de F03 é pré-requisito do primeiro
piloto/lançamento, enquanto pesquisa ampla de concorrentes continua expansão.

O [plano de qualidade criativa](../design/creative-production-quality.md) detalha
o próximo marco de F03.3b/F04.1b/F04.2b: inspecionar material, criar briefing e
kit de marca, testar edição de imagem por IA contra edição local e fazer vídeo
com fonte real, corte relevante e áudio/legenda. As peças atuais são baseline
técnico; nenhuma passou no gate comercial. Avatar F05 continua separado e
depende de custo/consentimento próprios.

A [biblioteca de identidade e formatos](../design/brand-library.md) cria kits
demonstrativos **uma vez pela equipe**; F03 recomenda/registra a escolha e F04
testa a produção posterior com material real. O showroom da nossa web serve dez
posts de exemplo, stories e reels por kit em simuladores de canais, com marca
fictícia e conversas exemplares de WhatsApp/cadência. Nenhum arquivo é gerado
por IA visual quando o visitante apenas navega. Canais não conectados seguem
como simulações rotuladas; selecionar kit não autoriza publicar.

Cada fase é integrada em features menores, com testes e SDD atualizados.
A v0 completa reúne F00–F08; concluir F00 não conclui o produto.

| Fase | Escopo | Status |
| --- | --- | --- |
| [BL01–BL05](BL-brand-library.md) | Kit mestre, prova de reaplicação, vitrine, escolha e jornada com kit | UI exploratória BL01 entregue; kit final e demais etapas pendentes |
| [F00](F00-foundation.md) | Fundação executável | Concluída localmente |
| [F01](F01-identity-onboarding.md) | Identidade, onboarding, admin mínimo e base React | Código local; homologação externa/staging pendente |
| [F02](F02-whatsapp-ingestion.md) | WhatsApp e biblioteca de materiais | Recebimento, vínculo, biblioteca, transcrição opcional e respostas limitadas implementados localmente até F02.2c6; Meta real pendente |
| [F03](F03-editorial-research.md) | Pesquisa, temas e planejamento proativo | Contexto, ideia e edição versionada de roteiro locais; benchmark F03.3b, pesquisa e proatividade pendentes |
| [F04](F04-media-recipes.md) | Artes, vídeo e prévia pelo WhatsApp | Render estático/vídeo local e avaliação sintética; F04.3 cria candidata e caixa WhatsApp simulada; envio Meta, revisão real e custo staging pendentes |
| [F05](F05-avatar-generative-video.md) | Avatar, voz e cenas geradas | Planejada |
| [F06](F06-instagram-publishing.md) | Aprovação, agenda e Instagram | Aprovação e publicação falsa locais em andamento; ajustes automáticos, Instagram real e homologação pendentes |
| [F07](F07-billing-reports.md) | Franquias, assinatura e relatórios | Contratação mínima na F01.5; restante pendente |
| [F08](F08-production-scale.md) | Operação, segurança e escala | Planejada |

F01 é integrada com a base web e o admin mínimo; telas essenciais do cliente entram
junto. Área completa acompanha F02–F07. Contratação/ativação mínima antecipa F07
na fatia F01.5; métricas reais entram quando existirem suas fontes.

Decisão transversal de F02–F07: [contexto versionado do negócio, adapters por
capacidade e ledger anterior ao primeiro gasto pago](../design/business-context-and-generation.md).

## Qualidade por etapa e dependência da Meta

**Ordem vigente em 26/10/2026:** a
[trilha BL01–BL05](BL-brand-library.md) vem antes de ampliar receitas antigas.
Esta decisão do produto substitui a restrição anterior de não criar kits antes
de uma peça aprovada pelo proprietário. O limite novo é mais preciso: construir
**um kit mestre junto com sua UI exploratória**, provar sua reaplicação numa nova
peça, então ampliar a vitrine. A qualidade comercial da produção real continua
gate antes do piloto.

O percurso completo só tem valor se a peça final for útil para o comerciante.
Cada receita habilitada para clientes precisa passar por avaliação factual,
criativa e visual com negócios consentidos, revisão em celular, taxa de aceite e
custo por peça medido; testes sintéticos e funcionamento técnico não substituem
esse gate. Concluir primeiro as pendências de F03.3b/F04.1b/F04.2b para as
receitas escolhidas, corrigindo os resultados encontrados, antes de liberar a
automação de F04.3 e a publicação de F06 no piloto. Não é necessário concluir
todos os formatos da v0 ou F05 para avaliar foto/story ou um vídeo que já tenha
passado pelo seu próprio gate. Qualidade por etapa não significa prometer que
cada fornecedor ou template é definitivo: comparar com um baseline e reavaliar
quando a receita, modelo ou público mudar.

A conta Meta restrita não bloqueia implementação e testes locais. F04.3/F06
usam adapters falsos e contratos de eventos que exercitam duplicação, entrega
incerta, rejeição, expiração e publicação assíncrona. A homologação real de
WhatsApp e Instagram é um gate separado antes de operar com clientes reais;
ela pode exigir ajustes de permissões, formatos, mídia, janelas de mensagem e
estados externos, não apenas trocar a URL do adapter.

### Próximo marco demonstrável

Entregar **BL01 + BL02** para uma cafeteria fictícia: um kit com dez posts,
story, reel e receitas editáveis que pareçam publicáveis; em seguida gerar pelo
pipeline do produto uma **nova** foto/story no mesmo estilo, usando fonte e fato
distintos dos exemplos. Comparar sem kit, manifesto, manifesto + no máximo uma
referência de imagem do mesmo formato e composição local. Mostrar arte ampliada
no celular, fatos/identidade corretos, versões, tentativas e custo por peça
aceita. O material sintético valida engenharia; comerciante com material
consentido valida qualidade comercial. A UI inicial já permite ver o kit no app,
mas a interface de três kits só amplia após
essa prova, para que a vitrine não prometa uma qualidade que o motor não repete.

## Sequência executiva até a v0 completa

Esta é a ordem de produto. BL01–BL05 é uma trilha transversal às F00–F08,
detalhada no [SDD da biblioteca](BL-brand-library.md). Cada linha precisa gerar
evidência visível; só testes de infraestrutura não a encerram.

| Ordem | Entrega | Evidência de conclusão |
| --- | --- | --- |
| 1 | BL01: UI exploratória em paralelo a um kit mestre completo, versionado e com fontes editáveis | Navegação dos três canais já existe; conclusão exige dez posts, story, reel e direitos revisados, com cada mídia final aberta em tamanho real no celular. |
| 2 | BL02: reaplicar o kit pelo pipeline real e comparar rotas | Nova peça preserva identidade/fatos; no máximo uma referência visual do kit; medir aceite, tentativas e custo por aceita. |
| 3 | BL03: três kits e vitrine web ligada ao catálogo | Cliente navega três kits com mídias finais nos três canais, sem conta conectada ou chamada de IA por visita. |
| 4 | BL04: escolha versionada e ajustes por negócio | Proprietário seleciona/edita kit; API isola tenant e versiona; escolha não aprova post. |
| 5 | BL05 + F03.3b/F04.1b/F04.2b: conteúdo real com kit e qualidade | Roteiro, arte e vídeo refletem o kit escolhido; dono aprova ou rejeita em celular; gates factuais/visuais e COGS fechados por receita. |
| 6 | F03 mínimo proativo: sugestão quando não houver mensagem nova | Cadência/pausa por negócio, fato e acervo vigentes, tema não repetido, custo limitado; pede material quando necessário e não publica por silêncio. |
| 7 | F04.3/F06 locais: candidata, ajuste e aprovação pelo WhatsApp simulado | Entrada recebida ou planejada usa mesma orquestração; decisão vincula versão, legenda, destino e horário; falhas/duplicação têm testes. |
| 8 | F02/F06 reais + F07/F08 mínimos: homologar Meta, gasto, segurança e staging | WhatsApp recebe/envia mídia e candidata; conta profissional publica formato aprovado; quota/COGS, backup, deploy e suporte básico funcionam. |
| 9 | Piloto controlado com negócios consentidos | Jornada iniciada pelo cliente e jornada sem novo input, ambas sem operação manual oculta; medir qualidade, aceite, retrabalho, custo, falhas e contatos observáveis. |
| 10 | Primeiro lançamento comercial: completar o plano inicial e a operação necessária | F07 conclui franquia, cobrança/cancelamento e relatório honesto; F08 comprova recuperação e capacidade para a coorte declarada. |
| 11 | Expandir formatos, segmentos, concorrência e F05 avatar | Cada nova receita passa pelos gates de fatos, qualidade, direitos e custo; pesquisa tem fontes verificáveis e avatar exige consentimento específico. |
| 12 | F07/F08 completos e v0 completa | Relatórios e console operacionais, carga/restore e margens medidos; todas as receitas prometidas pela v0 aprovadas e homologadas nos formatos elegíveis. |

A regularização da conta Meta pode ocorrer em paralelo às ordens 1–7. Ela só é
dependência da homologação externa nas ordens 8–9. Pesquisa de fornecedores também pode ocorrer em paralelo
quando uma receita falhar no gate; integrar um fornecedor exige benchmark de
qualidade/custo, não apenas disponibilidade da API. A meta de 200 mil clientes
orienta testes graduais de capacidade em F08 e não bloqueia a primeira coorte.

## Caminho até o primeiro conteúdo publicado

**Estado atual:** F02 recebe e guarda material de texto/foto/áudio/vídeo por webhook
assinado, com vínculo do remetente e consentimento, e F03 sugere uma ideia inicial
sob pedido. Esses componentes passaram em testes locais com eventos e mídias
sintéticos. A WABA restrita impede a homologação de mensagens reais; a geração de
ideias ainda não passou no gate de qualidade comercial. F03.3 gera cenas com
fontes e registra aceite/pedido de ajustes do proprietário; F04.1 renderiza
foto/story privada a partir do roteiro aceito; F04.2 acrescenta a primeira
prévia privada de vídeo curto. F03.3b já permite editar o roteiro. A F04.3
registra candidata e entrega falsas e a F06 permite aprovação e publicação
falsas locais; não há envio nem publicação real.

**Próximas entregas, sem saltar os gates de qualidade:** concluir kit/mídias de
BL01 na UI já criada e BL02 antes de ampliar a vitrine ou automatizar a produção
visual. F03.3b já tem
edição técnica; F04.1b tem template v4 e avaliador; F04.2b tem benchmark
sintético, mas nenhuma receita visual passou em qualidade/custo reais. Esses
componentes são reaproveitados para produzir uma nova peça orientada pelo kit,
comparando IA e composição local. BL03/BL04 então expõem três kits e guardam a
escolha. F04.3/F06 locais exercitam candidatas e publicação falsa; envio oficial
e ajustes automáticos continuam pendentes. Os gates criativos antecedem o
piloto.

**F03.3 local: material → roteiro revisável.** Usa
o mesmo pipeline F02 com webhook assinado e servidor de mídia falsos nos testes,
sem criar um caminho de negócio paralelo. Para texto, áudio transcrito e foto com
legenda, montar briefing e roteiro estruturado com cenas, texto, material de origem,
fatos confirmados e validade. Foto sem descrição exige interpretação visual
avaliada e consentida ou uma pergunta ao dono; não inventar produto/preço.
Guarda versão do contexto e apresenta revisão no cliente. Comparar a saída da IA com
baseline e casos PT-BR ainda é gate pendente para ativação comercial.
Os testes não exigem credenciais Meta reais ou gasto externo obrigatório.

**F04.1 local** renderiza prévia de arte estática a partir do roteiro
aceito, com fonte, template, arquivo privado e retry idempotente. **F03.3b**
permite editar/versionar roteiro e mede sua qualidade comercial; **F04.1b** mede
e melhora a qualidade visual das artes antes do piloto. **F04.2** acrescenta
vídeo curto silencioso com foto ou trecho de clipe autorizado e textos de cena
temporizados; cortes múltiplos e legenda alinhada à fala permanecem pendentes.
**F04.3** deverá enviar candidatas pelo WhatsApp sem exigir cliques na web;
atualmente só registra a entrega falsa. **F06** recebe aprovação explícita da
peça por comando WhatsApp processado ou web, agenda e simula publicação local.
Ainda faltam envio real, recibos externos, resposta a ambiguidade, ajustes e
cancelamento. **F03** acrescenta pesquisa e sugestões proativas;
**F05** acrescenta avatar opcional; **F07/F08** completam planos, métricas,
operação e infraestrutura. A integração oficial de WhatsApp e Instagram,
incluindo OAuth, permissões, formatos e smoke em staging, deve ser homologada
antes de atender clientes reais, mas não bloqueia o desenvolvimento local dessas
etapas. Fake prova o comportamento do nosso sistema; não prova a API da Meta.

Confirmar um preço ou horário no WhatsApp apenas confirma o fato usado no
conteúdo. Aprovar a peça final é uma decisão distinta em F06, associada à versão,
legenda, destino e horário. A web é complementar no percurso principal.
