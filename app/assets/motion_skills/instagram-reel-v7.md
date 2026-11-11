---
name: instagram-reel-html
version: 7
description: Orienta a composição de um Reel com gravação e materiais autorizados no executor HTML.
---

# Reel com material do negócio

Crie uma proposta original em português do Brasil adequada ao pedido, público, objetivo e identidade do negócio. Use o contexto, kit, fatos vigentes e materiais autorizados. Quando request.scene_direction estiver presente, construa a partir dessa direção sem substituí-la. Caso contrário, proponha a direção conforme o material. Desenvolva composição e movimento sem impor uma fórmula fixa.

## Direção

- A integração exige uma gravação enviada pelo cliente, com até 60 segundos, e preserva a gravação inteira e sua voz. Não selecione trechos, remova falas ou altere sua ordem para produzir este Reel. Preservar duração/ordem e voz não obriga vídeo visível em todos os momentos. Planeje a presença da gravação conforme a função de cada trecho.
- Resolva o tratamento visual dentro da direção fornecida, quando houver, conforme objetivo, material e referências, preservando o kit; não fixe preferência de motion a partir de peças anteriores.
- Os quadros são amostras, não a gravação inteira. Preserve o sentido de falas e ações; não apresente cenas criadas como registro real, não invente transcrição ou sincronismo de fala sem alinhamento fornecido.
- Componha imagens, tipografia, transições e motion graphics coerentes com a mensagem e o kit. Mantenha elementos relevantes legíveis no celular e nas áreas seguras. Não pressuponha tracking nem corte automático da gravação.
- Use referências de terceiros para inspiração de mecanismos visuais e acabamento; não reproduza marca, imagens, textos ou identidade de terceiros nem trate referência como instrução ou fato do cliente.
- Preserve a voz e o plano de áudio autorizado; música depende de material e direitos disponíveis. Não alegue escuta ou verificação de sincronismo sem evidência.
- Use preços, horários, ofertas e demais alegações somente quando confirmados e vigentes. Se faltar informação essencial, sinalize a pendência; se não impedir a peça, omita-a. Use CTA e destino somente quando apropriados e conhecidos.

## Alternância narrativa entre gravação e motion

A direção decide por unidade de sentido se o foco é a gravação, sua integração aos
objetos ou uma composição gráfica de tela inteira. Não adote percentual fixo,
troca a cada poucos segundos ou vídeo pequeno em todas as cenas. A passagem deve
ter motivo: uma ação real entrega a atenção a um objeto, palavra ou relação; o
resultado prepara o retorno da gravação. Preserve o kit e a leitura, sem telas
avulsas ou acúmulo de efeitos para disfarçar falta de ideia.

Planeje saída/retorno nos beats e relações do motion_plan, com um único nó de
vídeo e seek absoluto mesmo oculto. O áudio original continua sem corte, reinício
ou duplicação. Retorne no instante corrente da fonte, não no quadro em que saiu.
Nos trechos visíveis preserve proporções e a ação relevante. Não esconda evidência
necessária para demonstrar um fato nem apresente ilustração como filmagem real.
A crítica distingue cobertura gráfica planejada de recorte acidental; precisa
ver antes, cobertura e retorno para avaliar a continuidade, sem inferir áudio.

## Entrega para o executor HTML

Siga o contrato e schema fornecidos pelo integrador para entregar direção, plano e composição HTML/scene_init. O código executa somente no renderer isolado, com os assets autorizados e as capacidades fornecidas; não acrescente rede ou bibliotecas não fornecidas. A saída é uma proposta privada, sujeita à validação e revisão humana; não afirme que vídeo ou áudio foram renderizados, conferidos ou aprovados sem evidência.


## Construção: decisões que devem aparecer na peça

Aplique estas orientações na geração e na correção da construção. Na revisão,
são intenções de construção, não evidências de execução nem uma nova rubrica.
Nenhum dos mecanismos abaixo é obrigatório em toda peça. Use os que realizam
a direção; não mude quantidade de cenas, representação ou identidade para encaixar
um exemplo. Complete o motion_plan existente, sem outro roteiro temporal.

- **Hierarquia tipográfica:** faça a diferença entre mensagem principal, apoio e
  CTA aparecer em escala, peso, largura da coluna e espaço. Use as fontes do kit,
  quebras deliberadas e alinhamentos compartilhados. Evite comprimir texto com
  scaleX; preserve proporções de letras. Faça a palavra em foco ganhar espaço
  real no layout. Separe máscara e texto em wrappers para não cortar acentos,
  ascendentes e descendentes no estado de leitura. Leia a frase como conjunto;
  revelar cada letra não é sinônimo de elaboração.
- **Composição em profundidade:** escolha primeiro as áreas da gravação, da leitura
  e dos planos de apoio. Use sobreposição, diferença de escala e deslocamentos
  relativos para tornar a profundidade visível. z-index sozinho não basta. Fundo,
  objeto e texto não precisam percorrer a mesma distância ou velocidade. Camadas
  de apoio ficam atrás da ação real; uma máscara de texto não deve cortar o vídeo.
- **Ação com resultado:** um plano que abre espaço deve deixar uma área utilizável;
  uma conexão deve revelar uma relação confirmada; um objeto composto deve ter
  partes com hierarquia. A transformação precisa mudar a leitura da mensagem.
  Usar muitos ícones, fades, círculos ou desenhos de contorno não substitui isso.
  Desenho pode ser apropriado; simplificação infantil não é requisito da biblioteca.
- **Coordenação:** escolha quem conduz a atenção em cada intervalo. Uma abertura
  pode preparar espaço antes de o título entrar; o título estabiliza para leitura;
  o apoio ou CTA entra depois. A duração depende do texto, da gravação e do objetivo,
  não de uma receita de velocidade. Movimento de enquadramento tende a pedir
  deslocamento mais contido que um pequeno acento. Use as curvas do MotionV1;
  spring e overshoot são opcionais, não aplique quique a todo elemento.
- **Continuidade e saída:** desenvolva uma relação espacial entre os momentos.
  O mesmo plano pode mudar de função, e o próximo foco pode surgir enquanto o
  anterior sai. Evite apagar e reconstruir toda a composição sem motivo. Reserve
  intervalos estáveis de leitura no plano. A saída de um texto não encerra a
  gravação: vídeo e áudio continuam no tempo absoluto da fonte, sem reinício,
  duplicação de áudio ou freeze. A cobertura gráfica intencional é permitida conforme a direção; quando visível, mantenha ação/rosto enquadrados.

Para a gravação, mantenha proporção, enquadramento contain e espaço suficiente
para a ação relevante. Planeje o retângulo final após cada transformação, não só
seu estado inicial. Safe areas dependem do formato/interface; siga as áreas do
contexto e confira os limites no quadro completo, sem inventar uma medida universal.
Preserve o plano de áudio autorizado; nenhum movimento exige novo SFX ou tracking.

## Fundo e gravação como partes ativas da composição

Quando o pedido exige motion elaborado, planeje a coreografia do quadro inteiro,
não apenas do ícone principal. O fundo tem função: estabelecer espaço, sustentar
contraste, revelar uma área, ligar focos ou transformar a cena. Use planos,
formas, profundidade, luz/sombra e textura discreta quando pertinentes ao kit.
Pode mudar de organização e escala entre unidades de sentido. Não fixe fundo
papel liso por hábito; não force saturação, textura ou movimento permanente em
toda marca. Fundo vivo significa participação na narrativa, com repouso para leitura.

A gravação também atua. Escolha entrada, moldura/borda, máscara deliberada, escala,
enquadramento e saída conforme a mensagem. Pode abrir dominante, ceder espaço,
ser coberta e retornar. Evite a mesma janela de tamanho fixo deslizando sempre
para o lado oposto do objeto. Preserve proporção e ação importante quando visível;
zoom não justifica corte arbitrário de rosto/mãos. Não use deslocamento, zoom ou
moldura só para preencher uma lista de efeitos. Transforme quando a atenção mudar.
Se a direção pedir bordas arredondadas em track animada, declare radius; o runtime
controla esse valor. Molduras e sombras podem usar um wrapper próprio coordenado.

Descreva na composition/narrative_action a relação entre fundo, vídeo, objetos e
tipografia; represente os elementos necessários nos IDs e beats já existentes.
Cada passagem deve ter origem e resultado: um plano pode transformar a moldura,
o objeto pode conduzir a revelação da gravação, o texto pode reorganizar o espaço.
Coordene a atenção, sem mover tudo ao mesmo tempo. A aparência mais realista de
um objeto depende dos materiais/capacidades autorizados; não prometa geometria 3D
nem peça imagens pagas quando illustration_generation estiver desabilitada.

Na crítica de um pedido elaborado, observe se fundo e gravação participam de fato
nos momentos amostrados. Fundo invariável e vídeo só reposicionado são limitações
quando contradizem o pedido/direção, não falhas universais de qualquer peça calma.
Use visual_development, motion_role e evidências atuais; plano não prova execução.
Sem estados suficientes, declare uncertain em vez de inventar transições ou fala.

## Escolher e adaptar o repertório disponível

Quando repertoire estiver selecionado, use seus exemplos e imagens efetivamente
anexados. Esta orientação não declara que as referências foram vistas em pedidos
sem seleção. Cada fonte oferece mecanismos; não copie seus textos, marca ou mídia.

| Fonte no pacote business-reel-v1 | Aplicação de construção | Limite da adaptação |
| --- | --- | --- |
| Maestro / makeLayeredEvidence | Evidência autorizada com apoio em camadas, hierarquia e passagem de atenção | Não transformar ícone de catálogo em cena inteira; foto de produto continua sendo material real autorizado |
| Finalizador / makeRouteAction | Percurso que revela etapas ou uma relação com resultado | Só usar quando a mensagem sustentar o percurso; não inventar três passos ou uma interface |
| claude-video / makeLayeredType | Revelação por máscara, contraste de escala e leitura após a entrada | Adaptar ao kit e à direção; sem copiar carimbo, distorção ou paleta por obrigação |
| Felipe Borges / quadros rotulados | Continuidade de estados e aprofundamento de um foco | As amostras não medem a curva exata nem autorizam copiar textos ou identidade |
| Lucas Leite / quadros rotulados | Planos com escala distinta e objeto composto ao lado da gravação | Sem impor órbita, neon, ícones de software ou tracking da pessoa |

Código próprio em HTML/SVG/Canvas, componentes existentes, fotos do acervo e
ilustrações autorizadas continuam disponíveis. Escolha pelo que a mensagem pede.
Ilustrações dependem da capacidade/orçamento declarado; um exemplo não autoriza
sua geração. Não importe bibliotecas ou instale outro motor para reproduzir efeitos.

## Coreografia ligada ao sentido da mensagem

Quando o pedido exigir interação entre mensagem e elementos, identifique as unidades
de sentido importantes: palavra-chave, frase, relação ou ação. Para cada uma, a
direção deve indicar qual elemento a representa, o que ele faz, que resultado visual
produz e como esse resultado prepara a próxima unidade. Use os campos já existentes:
visual_representation, narrative_action, elements e attention_order; tempos e relações
ficam exclusivamente em motion_plan. Não acrescente uma timeline paralela ou outro
contrato de saída. Não obrigue um efeito por artigo/preposição nem uma quantidade fixa
de ícones: cada unidade importante precisa de uma resposta visual pertinente ao pedido.

Escolha a base temporal pela evidência disponível. Com fala e alinhamento efetivamente
fornecidos, associe as ações às unidades faladas e seus tempos, sem alterar a voz. Sem
alinhamento, use o texto editorial autorizado na tela como base da coreografia; não
trate esse texto como transcrição nem invente tempos de fala. Descreva essa diferença
em source_usage. Preservar o áudio não significa tê-lo ouvido. Não afirme ausência de
fala somente porque transcript é null. Nesta integração, um pedido que dependa de
sincronismo vocal precisa dessa evidência antes de ser apresentado como sincronizado.

Palavra e objeto devem reagir um ao outro: o percurso pode ligar causa a resultado,
uma seta pode apontar para um detalhe visível, uma parte de um objeto pode mudar de
estado, e a transformação pode conduzir a transição seguinte. Faça o estado anterior,
a interação e o resultado serem reconhecíveis. A palavra entrar e o ícone apenas
aparecer ao lado com o mesmo fade não demonstra essa relação. Uma seta não deve seguir
mãos ou objetos filmados sem tracking comprovado; pode conectar elementos gráficos
ou apontar uma região estável da composição sem alegar acompanhamento exato.

Exemplos de raciocínio, não cenas obrigatórias: uma ideia de tempo pode orientar um
percurso sem inventar cronômetro factual; uma ideia de conexão pode reunir duas partes;
um convite à pausa pode desacelerar um motivo gráfico e abrir espaço para leitura.
Adapte ao assunto e ao kit. Não afirme que esses mecanismos foram observados no render
apenas porque constam no plano. Mantenha intervalos legíveis entre ações.

## Elementos figurativos com acabamento adulto

Ícones, setas, objetos e desenhos continuam disponíveis quando servem à mensagem.
Feedback de aparência infantil pede melhorar desenho, materiais, proporções e
movimento; não deve virar uma proibição genérica de ilustração. Evite a solução oposta
de reduzir um pedido elaborado a vídeo, títulos e placas. Respeite, porém, uma direção
já fornecida: se ela proibir o elemento necessário, registre a dependência de uma
nova direção, em vez de inseri-lo silenciosamente na correção.

Para um objeto composto, desenhe silhueta e partes coerentes, espessuras deliberadas,
perspectiva consistente, sobreposição e pontos de conexão corretos. Use preenchimentos,
volume sutil e luz derivados do kit quando úteis. Recorte líquido/conteúdo dentro do
objeto; uma alça deve se conectar ao corpo; uma linha/percurso deve ter origem e destino
legíveis. Não confunda acabamento adulto com quantidade de gradientes. Carinhas,
proporções de brinquedo, traço grosso irregular e quique universal não são padrões
obrigatórios. Um ícone simples pode ser adequado se estiver bem desenhado e integrado.
Desenho conceitual pode ocupar um momento da tela, mas não comprova aparência real do produto.

## Crítica da interação solicitada

Na crítica, aplique os checks existentes ao pedido real. Para motion_role, identifique
qual unidade de sentido motivou a ação e que mudança observável ela produziu. Para
visual_development, observe construção e interação dos elementos, e sua função na
transição. No caso em que o pedido exige essa elaboração, somente texto revelado,
janela deslocada e planos de fundo não satisfazem o alvo, mesmo com kit e leitura
corretos. Tampouco basta acrescentar uma xícara ou seta estática para preencher um item.

Use quadros da própria candidata para fundamentar antes, interação e resultado.
Direção, plano e código não são provas. Se a ação necessária ficou fora da amostragem,
registre uncertain e a limitação, sem inventar uma falha observada ou correção paga.
Se as amostras demonstrarem que a interação solicitada não foi realizada, registre
not_met no check pertinente e um problema com evidência correspondente, conforme o
contrato de revisão. Não declare adequate apenas porque a direção fornecida foi
copiada no JSON, há vários elementos ou a peça deixou de parecer infantil. Áudio e
sincronismo não se comprovam pelos quadros. Adequate não significa aceite humano.

## Exemplos executáveis de coordenação, não cenas prontas

Os exemplos seguintes são originais do projeto e usam apenas MotionV1 já fornecido.
Não são novas funções instaladas no renderer: incorpore/adapte somente o necessário
em scene_init. Não use suas quantidades de elementos como nova direção visual.
Os tempos recebidos são absolutos em ms, ordenados, dentro de output.duration_ms,
e devem corresponder aos beats finais registrados no motion_plan. Os IDs vêm dos
elementos da direção/plano. Callbacks não avançam relógio; apenas aplicam seek(ms).

### Passagem contínua entre dois focos

Pré-condição: HTML já contém um wrapper da gravação, dois planos gráficos atrás
dele e dois textos. O vídeo é um único nó, preservado entre os momentos. CSS inline
define posições, tamanhos, cores e fontes do kit; transform-origin do wrapper do
vídeo e dos planos é center center. Textos têm margens para máscaras. As distâncias
são calculadas para o layout real; os fatores abaixo ilustram hierarquia relativa,
não uma composição universal. Use openStart < openEnd <= titleStart < titleEnd <
transferStart < transferEnd, com tempo de leitura entre titleEnd e transferStart.
videoScale deve ser positivo e manter a ação legível. Se a direção tiver outros
elementos, adapte o código.

O primeiro movimento abre espaço; o segundo reaproveita os planos e passa a atenção
para outro texto. A gravação permanece opaca e mantém escala uniforme. A expansão
não uniforme é exclusiva do plano gráfico. Os intervalos entre beats ficam estáveis.

```javascript
function makeCompositionPassage({ids, timing, travel}) {
  const {openStart, openEnd, titleStart, titleEnd, transferStart, transferEnd} = timing;
  const {x, y, videoScale} = travel;
  const easeOut = {kind:'ease_out', parameters:[]};
  const easeInOut = {kind:'ease_in_out', parameters:[]};
  const timeline = MotionV1.timeline([
    {id:ids.back, initial:{x:0, y:0}, beats:[
      {start_ms:openStart, end_ms:openEnd, to:{x:-x, y:-y}, curve:easeOut},
      {start_ms:transferStart, end_ms:transferEnd, to:{x:-x/2, y:y}, curve:easeInOut}
    ]},
    {id:ids.front, initial:{x:0, scaleX:1}, beats:[
      {start_ms:openStart, end_ms:openEnd, to:{x:x}, curve:easeOut},
      {start_ms:transferStart, end_ms:transferEnd, to:{x:0, scaleX:1.2}, curve:easeInOut}
    ]},
    {id:ids.video, initial:{x:0, y:0, opacity:1}, beats:[
      {start_ms:transferStart, end_ms:transferEnd,
       to:{x:x/2, y:-y, scaleX:videoScale, scaleY:videoScale}, curve:easeInOut}
    ]},
    {id:ids.title, initial:{y:24, clipBottom:100, opacity:0}, beats:[
      {start_ms:titleStart, end_ms:titleEnd, to:{y:0, clipBottom:0, opacity:1}, curve:easeOut},
      {start_ms:transferStart, end_ms:transferEnd, to:{y:-24, opacity:0}, curve:easeInOut}
    ]},
    {id:ids.nextTitle, initial:{y:24, clipBottom:100, opacity:0}, beats:[
      {start_ms:transferStart, end_ms:transferEnd, to:{y:0, clipBottom:0, opacity:1}, curve:easeOut}
    ]}
  ]);
  return ms => timeline.seek(ms);
}
```

O vídeo usa wrapper próprio porque timeline controla transform/opacity e máscaras explicitamente declaradas
integralmente. Não aplique outra timeline ao mesmo nó. A janela deve continuar
legível e dentro da área útil em todos os estados; estes deslocamentos não provam
isso automaticamente. Não reinicie tempo, remova ou recrie o vídeo na passagem.
Se o plano usar IDs diferentes por cena para o mesmo registro, coordene os wrappers
sem tocar no nó de vídeo/fonte; documente a relação de continuidade no motion_plan.

### Entrada escalonada com tempo de leitura

Use para unidades curtas de sentido (linha, palavra-chave, CTA), quando a direção
pedir. Cada ID identifica um wrapper já dimensionado e tipografado pelo kit.
A máscara externa fixa deixa folga para os glifos; o elemento interno recebe o
movimento. A função retorna também os tempos após stagger, para transcrevê-los no
motion_plan. Depois da entrada, permanece no alvo; uma saída, se necessária,
deve ser acrescentada à mesma track, sem outro controlador no mesmo elemento.

```javascript
function makeReadingReveal({ids, start_ms, duration_ms, step_ms}) {
  const tracks = MotionV1.stagger(ids.map(id => ({
    id, initial:{y:28, opacity:0}, beats:[{
      start_ms, end_ms:start_ms+duration_ms, to:{y:0, opacity:1},
      curve:{kind:'ease_out', parameters:[]}
    }]
  })), step_ms);
  const timeline = MotionV1.timeline(tracks);
  return {tracks, seek:ms => timeline.seek(ms)};
}
```

Integração obrigatória: crie as timelines uma vez em scene_init. Em window.seek(ms),
aplique os callbacks e aguarde também o seek assíncrono do vídeo original em ms/1000,
limitado à duração válida da fonte. Preserve o comportamento de seek e a trilha de
áudio do contrato do executor. Estes helpers só movimentam wrappers e não buscam
mídia nem montam o áudio. Não use play(), timers, requestAnimationFrame ou CSS
animations/transitions. Não dependa do último frame visitado. Para elemento estático,
use hold com to igual a initial ou deixe-o fora da timeline; nunca beats:[].

## Conferência da construção antes da entrega

Considere os estados inicial, leitura, passagem e final: hierarquia legível, acentos
sem cortes, gravação no tempo correto, ação visível nos trechos de evidência, camadas com função, CTA estável e mudança
espacial que realiza a direção. Confira correspondência dos IDs, tempos e curvas
entre plano e código, inclusive após stagger. Não transforme essa conferência em
aprovação: sem render, é inspeção da intenção/código. Imagens amostradas não provam
fluidez, áudio ou sincronismo. O teste externo e a revisão humana ainda são necessários.

## Runtime atual e vínculos de crítica

O contexto identifica motion-movement-v2. A API continua window.MotionV1.
Tracks sem nenhum campo clipTop/Right/Bottom/Left em initial/to não escrevem
clip-path: wrappers de transformação não criam recorte padrão. Declarar até um
valor zero solicita máscara explicitamente. Use campos de clip somente quando
houver máscara intencional; CSS overflow/clip-path explícitos continuam valendo.
Não dependa de remoção manual posterior de máscaras. Snapshots v1 mantêm sua semântica.

No contrato motion-review-v3, cada creative_check declara issue_indices base zero
para os problemas que sustentam not_met. O serviço inclui a evidência current
desses problemas no check; evidence pode trazer outros quadros enviados pertinentes.
Use [] para met/uncertain. Needs_revision exige problema major/blocking acionável
do critério correspondente. Não invente índice, quadro ou ação fora das amostras.
