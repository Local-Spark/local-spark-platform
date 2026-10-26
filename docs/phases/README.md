# Fases de implementação

Cada fase é integrada em features menores, com testes e SDD atualizados.
A v0 completa reúne F00–F08; concluir F00 não conclui o produto.

| Fase | Escopo | Status |
| --- | --- | --- |
| [F00](F00-foundation.md) | Fundação executável | Concluída localmente |
| [F01](F01-identity-onboarding.md) | Identidade, onboarding, admin mínimo e base React | Código local; homologação externa/staging pendente |
| [F02](F02-whatsapp-ingestion.md) | WhatsApp e biblioteca de materiais | Recebimento, vínculo, biblioteca, transcrição opcional e respostas limitadas implementados localmente até F02.2c6; Meta real pendente |
| [F03](F03-editorial-research.md) | Pesquisa, temas e planejamento proativo | Contexto, ideia e edição versionada de roteiro locais; benchmark F03.3b, pesquisa e proatividade pendentes |
| [F04](F04-media-recipes.md) | Artes, vídeo e prévia pelo WhatsApp | F04.1 estática e primeira receita F04.2 vídeo locais; F04.1b tem template v4, ajuste visual versionado e avaliador; F04.2b tem narrativa/cortes v3 e revisão de ritmo; revisão real/staging e F04.3 pendentes |
| [F05](F05-avatar-generative-video.md) | Avatar, voz e cenas geradas | Planejada |
| [F06](F06-instagram-publishing.md) | Aprovação, agenda e Instagram | Planejada |
| [F07](F07-billing-reports.md) | Franquias, assinatura e relatórios | Contratação mínima na F01.5; restante pendente |
| [F08](F08-production-scale.md) | Operação, segurança e escala | Planejada |

F01 é integrada com a base web e o admin mínimo; telas essenciais do cliente entram
junto. Área completa acompanha F02–F07. Contratação/ativação mínima antecipa F07
na fatia F01.5; métricas reais entram quando existirem suas fontes.

Decisão transversal de F02–F07: [contexto versionado do negócio, adapters por
capacidade e ledger anterior ao primeiro gasto pago](../design/business-context-and-generation.md).

## Caminho até o primeiro conteúdo publicado

**Estado atual:** F02 recebe e guarda material de texto/foto/áudio/vídeo por webhook
assinado, com vínculo do remetente e consentimento, e F03 sugere uma ideia inicial
sob pedido. Esses componentes passaram em testes locais com eventos e mídias
sintéticos. A WABA restrita impede a homologação de mensagens reais; a geração de
ideias ainda não passou no gate de qualidade comercial. F03.3 gera cenas com
fontes e registra aceite/pedido de ajustes do proprietário; F04.1 renderiza
foto/story privada a partir do roteiro aceito; F04.2 acrescenta a primeira
prévia privada de vídeo curto. F03.3b já permite editar o roteiro; ainda não há
publicação.

**Próximas entregas, sem saltar os gates de qualidade:** F03.3b (editar,
versionar e avaliar roteiros) tem edição técnica local; F04.1b (evoluir e
validar as artes com negócios consentidos) tem template v4 e avaliador; F04.2b
iniciou narrativa, cortes e revisão de ritmo, mas precisa validar qualidade e custo. Em seguida,
F04.3 gerará e entregará candidatas pelo WhatsApp. F04.2 entregou somente a
primeira receita técnica de vídeo; esses gates criativos antecedem o piloto.

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
**F04.3** gera e entrega candidatas
pelo WhatsApp sem exigir cliques na web. **F06** recebe aprovação explícita da
peça por WhatsApp ou web, agenda e simula publicação usando adapter fake com
aceite, atraso,
falha, timeout e recibos; **F03** acrescenta pesquisa e sugestões proativas;
**F05** acrescenta avatar opcional; **F07/F08** completam planos, métricas,
operação e infraestrutura. A integração oficial de WhatsApp e Instagram,
incluindo OAuth, permissões, formatos e smoke em staging, deve ser homologada
antes de atender clientes reais, mas não bloqueia o desenvolvimento local dessas
etapas. Fake prova o comportamento do nosso sistema; não prova a API da Meta.

Confirmar um preço ou horário no WhatsApp apenas confirma o fato usado no
conteúdo. Aprovar a peça final é uma decisão distinta em F06, associada à versão,
legenda, destino e horário. A web é complementar no percurso principal.
