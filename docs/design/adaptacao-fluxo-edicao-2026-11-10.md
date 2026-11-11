# Adaptação do fluxo de Lucas Leite ao produto — 10/11/2026

Status: análise e proposta, não implementação. Complementa a
[auditoria do acabamento](../evals/analise-acabamento-motion-2026-11-10.md).
Não substitui os sete processos gerais do produto nem inicia sua etapa 5.

## Fontes e alcance

Os dois vídeos foram baixados integralmente e inspecionados por amostragem de
quadros, com sequências mais densas nos exemplos. Não houve escuta integral nem
transcrição das aulas; a descrição do procedimento é fundamentada também nos
guias publicados pelo autor, não em uma alegação de assistir/ouvir cada minuto.

A [skill publicada](https://github.com/LeiteZ/fluxo-de-edicao/blob/main/SKILL.md)
monta um fluxo personalizado; não distribui todos os scripts e o perfil exato
usados nas aulas. Ela organiza preparação, cortes, planejamento visual, assets,
construção, câmera e efeitos sonoros. Podemos adaptar o método ao nosso produto;
instalá-la isoladamente não reproduz o resultado mostrado.

## Correspondência com o Reel integrado

| Etapa de origem | Situação no nosso fluxo | Adaptação proposta |
| --- | --- | --- |
| Iniciar | Pedido, kit, fatos, preferências, consentimento e snapshot existem | Organizar o pedido de postagem como briefing, sem perder contexto confirmado |
| Preparar | Inspeção da mídia, seis quadros da fonte e preservação de áudio; esta integração envia `transcript=None` | Para fala que exija sincronismo, obter transcrição alinhada; roteiro orienta, mas não substitui a fala real |
| Cortes | Gravação integral preservada nesta prova | Sem seleção de takes/cortes como requisito atual; projeto de bruto para YouTube está fora do escopo |
| Motion-mapa | `scene_direction` e `motion_plan` existem, produzidos junto com HTML/JS | Decidir representação, camadas, atenção e ação antes da implementação; entregar referência visual pertinente |
| Assets | Componentes, código próprio, fotos autorizadas e ilustrações opcionais existem | Selecionar pelo plano e acabamento; biblioteca não limita a cena nem obriga desenho de contorno |
| Motion-render | Renderer isolado, captura de quadros, aprovação por hash, MP4 e crítica existem | Construir a partir da direção decidida e validar uma cena exigente antes de ampliar |
| Câmera | Transformações e coordenação possíveis; sem etapa editorial dedicada | Coordenar enquadramento e gráficos, respeitando ação/rosto; conservar gravação e kit, sem copiar zooms indiscriminadamente |
| SFX | Áudio da fonte preservado; não há aqui seleção automática de efeitos por evento visual | Evolução separada: eventos, sons licenciados, alinhamento e mixagem com voz preservada; não bloquear prova visual por isso |

Mapa baseado em `motion_context.py`, `motion_inputs.py`, `motion_orchestrator.py`,
`motion_storyboards.py`, `motion_illustrations.py` e nos contratos de direção e
movimento. Capacidade implementada não implica qualidade criativa validada.

## Diferenças que realmente importam

### Planejamento e construção

O [motion-mapa](https://raw.githubusercontent.com/LeiteZ/fluxo-de-edicao/main/guias/etapa-motion-mapa.md)
define a ideia e sua realização visual antes de construir. Hoje a chamada
`generate:0` retorna direção, plano e código juntos; a captura vem depois.
Nossa aprovação dos quadros é real, mas não equivale à decisão anterior de um
plano criativo independente. Essa distinção deve ser explícita na documentação.

Próximo experimento: definir primeiro a direção de uma cena com referências,
validar a composição e só então concluir seu movimento. Uma separação futura de
chamadas deve justificar custo; oito etapas conceituais não significam oito
chamadas de IA. A prova pode começar com direção preparada e revisada nesta
conversa, sem alegar que o produto já automatiza essa etapa.

### Técnica, identidade e repertório

O [perfil do autor](https://raw.githubusercontent.com/LeiteZ/fluxo-de-edicao/main/modelos/perfil.md)
separa preferências do procedimento. No produto: identidade continua no kit;
orientações de construção ficam nas skills; preferências de movimento e
referências têm versão/origem; acervo fornece mídia autorizada. Uma aprovação
de estilo num negócio não vira regra global.

É necessário selecionar e transmitir exemplos úteis das bibliotecas. A chamada
atual não lê as pastas locais por conta própria. Corrigir as fichas antigas
contraditórias e incluir evidências visuais são pendências já comprovadas.

### Memória, revisão e cálculo

Os [princípios publicados](https://raw.githubusercontent.com/LeiteZ/fluxo-de-edicao/main/guias/principios-do-fluxo.md)
separam decisões criativas de cálculos e registram estado, revisões e aprendizados.
Nossa tradução é usar os serviços Python, registros duráveis, versões e Temporal
existentes; não criar um segundo executor ou usar arquivos locais como autoridade
do SaaS. Entrada de cada etapa contém somente o contexto necessário, com origem
verificável. Aprovação de quadros e avaliação final continuam distintas.

Há IDs de cenas/elementos e versões, mas ainda não uma operação completa para
aprovar um plano independente, reconstruir apenas uma cena e invalidar todas as
dependências afetadas. Isso é uma evolução a especificar, não capacidade pronta.
Feedback do titular deve distinguir correção desta peça de preferência reutilizável;
o produto não deve alterar automaticamente o estilo de todos os negócios.

### Som e precisão temporal

O [guia de preparação](https://raw.githubusercontent.com/LeiteZ/fluxo-de-edicao/main/guias/etapa-iniciar-preparar.md)
usa fala alinhada, enquanto o [guia de SFX](https://github.com/LeiteZ/fluxo-de-edicao/blob/main/guias/etapa-sfx.md)
associa efeitos aos eventos visuais e ao nível da voz. Para nós, sincronizar uma
entrada com uma palavra exige sua marca temporal, mesmo preservando a gravação
inteira. Isso não exige cortar o bruto. Som e transcrição entram somente quando
necessários à fatia proposta, com fontes e orçamento definidos.

## Sequência adaptada proposta

Briefing e kit → leitura do material → referências de acabamento → direção visual
por momento → escolha/criação de assets → quadros completos → aprovação → animação
e enquadramento coordenados → som quando aplicável → revisão da peça → entrega.

Na validação atual, manter aprovação humana dos quadros e do vídeo. Não transportar
para o autoatendimento comercial uma entrevista obrigatória a cada uma das oito
etapas do tutorial. Pontos de interação com clientes serão definidos pela jornada
do produto; aqui o titular está validando o processo criativo.

## Próxima implementação recomendada

1. Sanear e versionar o contexto de criação, com capacidades reais do executor,
   instruções das skills selecionadas e referência visual de acabamento.
2. Provar uma cena curta preservando gravação e kit, separando a decisão visual
   da construção; verificar se o repertório foi de fato realizado no render.
3. Depois do ganho demonstrado, especificar a divisão de etapas automatizadas,
   revisão por cena e aprendizado, medindo custo/tempo. Comparar modelos apenas
   com o mesmo pacote de entrada se o resultado ainda não atingir o alvo.

Nenhuma instalação, chamada paga, mudança de código ou teste longo nesta análise.
Documentação vinculada a PROJECT, SDD, BL04 e CHANGELOG; validação documental por
`git diff --check`. Pendências não foram marcadas como implementadas.
