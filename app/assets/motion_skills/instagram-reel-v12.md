---
name: instagram-reel-html
version: 12
description: Orienta a composição de um Reel com gravação e materiais autorizados no executor HTML.
---

# Reel com material do negócio

Crie uma proposta original em português do Brasil adequada ao pedido, público, objetivo e identidade do negócio. Use o contexto, kit, fatos vigentes e materiais autorizados. Quando request.scene_direction estiver presente, construa a partir dessa direção sem substituí-la. Caso contrário, proponha a direção conforme o material. Desenvolva composição e movimento sem impor uma fórmula fixa.

## Direção

Para cada momento relevante, registre nos campos existentes de scene_direction a
intenção e foco, preparação, ação principal e seu acento, consequência ou
repouso e passagem ao próximo momento. Relacione gravação, fundo, objeto e
texto quando fizerem sentido; um elemento pode permanecer em repouso ou estar
ausente. Identifique manualmente regiões importantes da fonte a proteger, sem
alegar detecção automática. Os tempos absolutos, inclusive o acento, pertencem
aos beats do motion_plan; não crie outro relógio. Escolha gravação dominante,
motion em tela inteira e retorno quando a ideia justificar, sem percentual fixo.
Acento é o momento da transformação significativa, não apenas da aparição.

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

A gravação também atua. Escolha entrada, eventual moldura/borda, máscara deliberada, escala,
enquadramento e saída conforme a mensagem. Pode abrir dominante, ceder espaço,
ser coberta e retornar. Evite a mesma janela de tamanho fixo deslizando sempre
para o lado oposto do objeto. Preserve proporção e ação importante quando visível;
zoom não justifica corte arbitrário de rosto/mãos. Não use deslocamento, zoom ou
moldura só para preencher uma lista de efeitos. Transforme quando a atenção mudar.
Se a direção pedir raio animado, declare radius; na movement-v3, tracks sem
radius preservam o arredondamento CSS. Molduras e sombras podem usar um wrapper próprio coordenado.

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

| Fonte, quando presente no pacote selecionado | Aplicação de construção | Limite da adaptação |
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
de ícones: agrupe unidades de sentido quando uma mesma ação as representar.

Escolha a base temporal pela evidência disponível. Com fala e alinhamento efetivamente
fornecidos, associe as ações às unidades faladas e seus tempos, sem alterar a voz. Sem
alinhamento, use o texto editorial autorizado na tela como base da coreografia; não
trate esse texto como transcrição nem invente tempos de fala. Descreva essa diferença
em source_usage. Preservar o áudio não significa tê-lo ouvido. Não afirme ausência de
fala somente porque transcript é null. Nesta integração, um pedido que dependa de
sincronismo vocal precisa dessa evidência antes de ser apresentado como sincronizado.

Quando texto e objeto participarem da mesma ideia, podem reagir um ao outro:
o percurso pode ligar causa a resultado,
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

Quando a direção pedir desenho por código, construa silhueta e partes coerentes, espessuras deliberadas,
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

## Tratamento da gravação — escolhas e passagem

Para um pedido de acabamento como este, planeje as presenças visíveis da gravação
conforme sua função; entrada, assentamento, mudança de foco e saída são
possibilidades. Uma pausa estável para observar a ação faz parte da coreografia. O retorno do motion pode ter outro tamanho e
tratamento, mantendo continuidade de direção e o instante corrente da fonte.
Não basta trocar a janela de lado. Não há obrigação de usar todos os efeitos.

- Moldura ou borda é opcional: use somente quando a cena justificar sua função.
  Se escolhida, adapte ao kit e verifique contraste e proporção; não copie a
  identidade de uma referência nem aplique decoração por padrão.
- Separe o wrapper de transformação, a área da mídia e eventual decoração. Borda/padding
  não podem comprimir a proporção da gravação. Use dimensões coerentes com a fonte,
  object-fit:contain e escala uniforme no conjunto. Se houver moldura, uma
  aproximação pode incluir o conjunto; cover pode cortar ação relevante.
- Faça entrada/saída conectar a gravação ao próximo foco. Máscara só é deliberada
  durante a passagem; no estado de observação, a ação relevante deve estar inteira.
  Não mantenha uma faixa residual da gravação quando a direção pedir motion pleno.
- Dimensione o retângulo externo considerando eventuais padding, borda, sombra e escala máxima.
  Verifique os extremos e estados intermediários dentro da área útil e longe de
  textos/CTA. Overshoot não pode esconder ação importante. Não anime borda a ponto
  de pulsar nem use quique/elástico por padrão para simular vida.
- Registre nos campos existentes o tratamento escolhido e sua função; nos beats,
  os tempos/estados e a permanência. IDs precisam corresponder
  ao plano; não crie outro relógio. Com direção fornecida, respeite-a: não imponha
  borda ou enquadramento que a contradiga. Mudança de direção pede nova entrada.
- Na crítica, compare entrada, observação, foco e saída nas amostras reais. Uma
  borda presente não comprova acabamento; vídeo imóvel também pode ser pertinente
  à ação. Quando tratamento foi pedido, identifique concretamente a janela fixa,
  o recorte ou a passagem ausente, com evidência e critérios existentes. Não
  certifique movimento completo ou sincronismo vocal por estados isolados.

### Exemplo executável: tratar uma presença da gravação

Helper original para copiar/adaptar em scene_init, não biblioteca nova instalada.
O `id` deve apontar ao wrapper do vídeo e corresponder ao motion_plan. Se a direção justificar moldura, monte-a no HTML/CSS do wrapper;
a mídia usa contain; não coloque overflow:hidden num ancestral que corta o
conjunto. `timing` usa tempos absolutos, ordenados e sem sobreposição. `pose` informa
x/y, enterOffset, startScale, restScale, focusScale e exitScale, calculados para a
área disponível. Registre esses estados no plano; ajuste os números à mensagem.

O helper move o conjunto sem tocar em src/currentTime/play/pause nem no áudio.
A função window.seek(ms) continua responsável por aguardar o seek da mesma fonte,
mesmo oculta. Para outro trecho/retorno, use o wrapper/ID previsto na respectiva
cena, com coordenação explícita; não reinicie nem duplique o nó de vídeo.

```javascript
window.makeVideoFrameTreatment = ({id, timing, pose}) => {
  const curve = {kind:'ease_in_out', parameters:[]};
  const tracks = [{id, initial:{x:pose.x, y:pose.y+pose.enterOffset,
    scaleX:pose.startScale, scaleY:pose.startScale, opacity:0}, beats:[
    {start_ms:timing.enterStart, end_ms:timing.enterEnd,
      to:{y:pose.y, scaleX:pose.restScale, scaleY:pose.restScale, opacity:1}, curve},
    {start_ms:timing.focusStart, end_ms:timing.focusEnd,
      to:{scaleX:pose.focusScale, scaleY:pose.focusScale}, curve},
    {start_ms:timing.exitStart, end_ms:timing.exitEnd,
      to:{y:pose.y-pose.enterOffset, scaleX:pose.exitScale, scaleY:pose.exitScale, opacity:0}, curve}
  ]}];
  const timeline = MotionV1.timeline(tracks);
  return {tracks, seek:ms => timeline.seek(ms)};
};
```

Na movement-v3, tracks sem `radius` preservam o border-radius CSS. Se quiser
animar o raio, declare o estado inicial e o destino explicitamente. `radius:0`
continua significando canto reto. Isso não altera o comportamento de snapshots
v1/v2; não atualizar automaticamente a biblioteca de uma peça histórica.

## Fundo narrativo — planos que preparam e conectam os focos

Quando a direção pede fundo vivo, desenhe seu estado na abertura, no trecho de
motion e no retorno da gravação. Diga qual mudança prepara a atenção seguinte:
abrir uma área para a palavra, sustentar o objeto, absorver a moldura ou devolver
espaço à gravação. Trocar apenas a cor do body ou mover uma textura em loop não
resolve essa relação. Não imponha mudança a cada palavra nem movimento contínuo.
Sem transcrição alinhada, os tempos respondem à direção/texto editorial, não a
uma fala supostamente ouvida.

- Use cores e materiais do kit com funções distintas: base, campo de destaque,
  área de leitura e detalhe. Um plano pode crescer e virar área do próximo foco;
  uma faixa pode acompanhar o percurso e depois abrir espaço para o convite.
  Varie proporção/posição e profundidade entre momentos, não só o matiz global.
- Conserve uma base opaca cobrindo o quadro. Dimensione planos e margem excedente
  para não revelar preto/transparência nas bordas durante transformações. Recorte
  planos no host exclusivo do fundo; não use esse host como ancestral do vídeo,
  das molduras, do texto ou das sombras da etapa 1.
- Fundo, gravação e objeto devem se relacionar sem perseguir todos o mesmo ponto.
  Deslocamentos diferentes podem sugerir profundidade. Não exigir órbita, neon,
  partículas, flashes, degradê pulsante ou textura por obrigação. Textura discreta
  opcional deve ser estática/determinística, feita por código ou material autorizado;
  não baixar imagens nem chamar geração de assets para preencher o fundo.
- Planeje contraste nos estados intermediários, não só nos cards finais. Quando
  um campo escuro atravessar uma área de texto escuro, mantenha uma placa opaca
  clara sob a leitura ou coordene a troca durante uma transição sem texto visível.
  Não faça crossfade de duas frases sobrepostas. Texto claro em campo escuro deve
  manter a mesma hierarquia do kit; trocar a cor não autoriza reescrever a mensagem.
- Distribua atenção: fundo prepara → foco atua → composição repousa. Durante
  observação do produto, leitura do convite e CTA, mantenha área de leitura estável
  e sem formas passando por trás dos glifos. Preserve o tratamento definido pela
  direção e não faça o vídeo perder proporção. Cobertura planejada continua permitida.
- Registre o fundo como elemento `construction=code` quando necessário, com ID
  do plano, aparência e função na direção. Suas partes podem compartilhar um beat
  composto; descreva coordenação/subintervalos sem criar beats sobrepostos para o
  mesmo ID. Reutilize o resultado visual entre cenas, mantendo IDs distintos quando
  o plano exigir. Não transforme cada faixa decorativa em uma cena independente.

### Exemplo executável: base, campo e detalhe sob um foco

Helper original para copiar/adaptar em scene_init, usando somente MotionV1 já
fornecido. O `id` aponta a um host vazio e exclusivo do fundo, posicionado atrás
da gravação/texto pelo z-index do HTML. Chame uma vez na inicialização. As três
partes são internas ao elemento do plano; descreva sua ação em beats compostos.
`colors` contém base, field e accent do kit (base/field opacas). `geometry` contém
enterX/exitX em px suficientes para o campo sair do quadro, bandWidth em px,
accentFrom/accentTo/accentExit em px e accentOpacity entre 0 e 1. Dimensões e
amplitudes dependem do quadro e da direção, não são valores universais.

`timing` usa openStart/openEnd e releaseStart/releaseEnd absolutos e ordenados.
O intervalo entre openEnd e releaseStart é estável para o foco/observação.
O helper não escolhe o contraste do texto: coordene as áreas de leitura acima
dessas camadas. Ele não toca em vídeo, áudio, texto ou moldura. window.seek(ms)
chama seu seek junto dos demais e aguarda o seek da mesma gravação.

```javascript
window.makeNarrativeBackdrop = ({id, colors, timing, geometry}) => {
  const host = document.getElementById(id);
  if (!host || timing.releaseStart < timing.openEnd) throw new Error('MOTION_BACKDROP_INVALID');
  const base = document.createElement('div');
  const field = document.createElement('div');
  const accent = document.createElement('div');
  Object.assign(host.style, {position:'absolute', inset:'0', overflow:'hidden', pointerEvents:'none'});
  for (const [node, color] of [[base,colors.base],[field,colors.field]]) {
    Object.assign(node.style, {position:'absolute', inset:'0', background:color, opacity:'1'});
  }
  Object.assign(accent.style, {position:'absolute', top:'0', bottom:'0', left:'0',
    width:geometry.bandWidth+'px', background:colors.accent});
  host.appendChild(base); host.appendChild(field); host.appendChild(accent);
  const curve = {kind:'ease_in_out', parameters:[]};
  const seek = ms => {
    const open = MotionV1.progress(ms, timing.openStart, timing.openEnd, curve);
    const release = MotionV1.progress(ms, timing.releaseStart, timing.releaseEnd, curve);
    field.style.transform = 'translateX('+(geometry.enterX*(1-open)+geometry.exitX*release)+'px)';
    accent.style.transform = 'translateX('+(geometry.accentFrom+
      (geometry.accentTo-geometry.accentFrom)*open+geometry.accentExit*release)+'px)';
    accent.style.opacity = String(Math.max(0,Math.min(1,open-release))*geometry.accentOpacity);
  };
  seek(0);
  return {seek, parts:{base,field,accent}};
};
```

Na crítica, use visual_development, motion_role e checks temporais existentes:
o fundo prepara ou conecta os focos observados? Conserva leitura, ação real e
tratamento escolhido? Há repouso onde a direção pede? Fundo estático não é falha universal;
quando a mudança foi explicitamente pedida e não aparece, cite os estados reais
e a lacuna concreta. Não aprovar por simples variação de cor nem inventar nota
por quantidade de camadas. Sem amostras suficientes, declare uncertain; plano e
código não comprovam a execução ou o sincronismo com a fala.

## Objeto com aparência realista — recorte e profundidade em camadas

Quando a direção pedir um objeto realista, use imagem com material, luz e volume
legíveis. Não substitua esse pedido por outro desenho SVG/CSS com mais gradientes.
Uma imagem em camadas permite movimento 2.5D, não geometria 3D: não revele costas,
interior oculto ou ângulos inexistentes com rotateY/rotateX, nem deforme o objeto.

Selecione a origem antes de construir:
- Foto/recorte autorizado disponível: construction=authorized_asset, role=image,
  asset_id exato do material. Preserve proporção, textura, marcas e proveniência.
  Uma foto com fundo opaco não vira recorte transparente por CSS; mantenha sua
  composição ou registre necessidade de preparar o recorte, sem inventar arquivo.
- Objeto genérico conceitual: somente se illustration_generation estiver presente,
  construction=generated_asset e role=image. Declare uma única entrada em
  illustrations e reutilize o mesmo asset_id em todas as cenas. Aparência
  fotográfica não transforma a imagem gerada em foto do produto real do cliente.
- Sem material adequado e sem capacidade de geração: registre a dependência de
  material/direção. Não invente caminho, autorização, imagem já gerada ou realismo
  entregue; uma direção fornecida incompatível precisa ser revista antes da execução.

Especifique o objeto e sua ação a partir da mensagem e dos materiais disponíveis.
Considere proporção, luz, apoio e transparência conforme a direção, sem repetir
uma receita de outro negócio. Não apresente objeto conceitual como produto real.
Uma imagem plana opaca não permite alterar independentemente partes ocultas;
planeje a ação segundo as camadas efetivamente disponíveis.

Objeto e sombra devem compartilhar posição horizontal e eixo de apoio. Ao se
aproximar do apoio, a sombra fica menos difusa e mais concentrada; em repouso,
objeto e sombra param juntos. Vapor opcional nasce na abertura e acompanha o
mesmo deslocamento da imagem, sem cruzar leitura. Preserve a luz pintada no asset, sem fabricar
reflexos móveis incoerentes. Entrada e saída podem se coordenar com fundo e gravação conforme a direção.
Preserve proporção, áudio e tempo absoluto da fonte; não imponha moldura, zoom
ou alternância como receita.

Exemplo original para adaptar: img existente e sombra elíptica irmã, no mesmo
wrapper de posicionamento, com origem inferior alinhada por CSS. A sombra fica
atrás da imagem (z-index explícito). Cor da sombra vem do kit; dimensões e
posição vertical vêm da área de apoio real do recorte, não da borda do PNG.
A imagem já deve ter src autorizado, estar decodificada e conter transparência
adequada. O helper não carrega/recorta/gera arquivos. Use um elemento image no
plano com beats compostos de entrada, repouso e saída, sem sobreposição por ID;
descreva sombra interna e chame seek(ms) a partir do relógio absoluto da peça.

```javascript
window.makeCutoutObject = ({ids, timing, pose}) => {
  const image = document.getElementById(ids.image);
  const shadow = document.getElementById(ids.shadow);
  const times = [timing.enterStart, timing.enterEnd, timing.exitStart, timing.exitEnd];
  const values = [pose.x, pose.y, pose.enterX, pose.exitX, pose.lift,
    pose.startScale, pose.restScale, pose.exitScale, pose.angle, pose.shadowOpacity, pose.shadowBlur];
  if (!image || !shadow || image === shadow || image.tagName !== 'IMG' ||
      !times.every(Number.isFinite) || !values.every(Number.isFinite) ||
      timing.enterStart < 0 || timing.enterEnd <= timing.enterStart ||
      timing.exitStart < timing.enterEnd || timing.exitEnd <= timing.exitStart ||
      Math.min(pose.startScale, pose.restScale, pose.exitScale) <= 0 ||
      pose.lift < 0 || pose.shadowBlur < 0 || pose.shadowOpacity < 0 || pose.shadowOpacity > 1) {
    throw new Error('MOTION_CUTOUT_INVALID');
  }
  image.style.objectFit = 'contain';
  image.style.transformOrigin = '50% 100%';
  shadow.style.transformOrigin = '50% 50%';
  shadow.style.borderRadius = '50%';
  shadow.style.pointerEvents = 'none';
  const curve = {kind:'ease_in_out', parameters:[]};
  const seek = ms => {
    const enter = MotionV1.progress(ms, timing.enterStart, timing.enterEnd, curve);
    const exit = MotionV1.progress(ms, timing.exitStart, timing.exitEnd, curve);
    const away = 1 - enter + exit;
    const visible = enter * (1 - exit);
    const x = pose.x + pose.enterX * (1 - enter) + pose.exitX * exit;
    const scale = pose.startScale + (pose.restScale - pose.startScale) * enter +
      (pose.exitScale - pose.restScale) * exit;
    image.style.transform = 'translate(' + x + 'px,' + (pose.y - pose.lift * away) +
      'px) rotate(' + (pose.angle * away) + 'deg) scale(' + scale + ')';
    image.style.opacity = String(visible);
    shadow.style.transform = 'translate(' + x + 'px,' + pose.y + 'px) scale(' + (1 - 0.25 * away) + ')';
    shadow.style.opacity = String(pose.shadowOpacity * visible * (1 - 0.5 * away));
    shadow.style.filter = 'blur(' + (pose.shadowBlur * (1 + away)) + 'px)';
  };
  seek(0);
  return {seek};
};
```

Na revisão, use visual_development/motion_role e as evidências existentes para
verificar recorte, partes, material, luz coerente, apoio/sombra e interação conforme o objeto.
Verifique também o tratamento da gravação e fundo escolhido pela direção. Se o pedido é realismo,
um desenho infantil continua inadequado mesmo se o plano declarar generated_asset.
Não aprove pelo helper/description: só os pixels gerados mostram o material.
Frames espaçados não comprovam todo o movimento; registre uncertain quando não
houver evidência. Reaproveite o asset na correção, sem regeneração silenciosa.

## Fala com tempos revisados — ligação explícita ao movimento

Quando request.speech_timing/transcript estiver disponível, use seus cues como
base temporal. Eles são vinculados ao hash da gravação; provenance informa se foram revisados
pelo titular ou reconhecidos automaticamente e ainda não revisados.
Não promova seu conteúdo a fato comercial confirmado. Regiões sem cue podem conter
fala. Sem essa entrada, mantenha coreografia editorial e declare falta de alinhamento.

Cada focus_cue_id exige uma ação visual ligada por speech_cue_id em um beat não
hold do motion_plan. O início do beat deve coincidir com start_ms do cue (até 34 ms
de arredondamento a 30 fps). Use esse mesmo tempo em scene_init/MotionV1, sem outro
relógio, timer ou deslocamento do áudio. Exemplo: cue `ideia` em 2400–2900 ms pode
ancorar uma transformação em 2400–2800 ms e a mudança do fundo no mesmo
onset; declare ambos com speech_cue_id=ideia, em seus IDs distintos. A antecipação
pode ter outro beat antes de 2400, sem esse vínculo. Não sobreponha beats do mesmo
ID. Duração do efeito não precisa ser igual à palavra: preserve leitura e repouso.

Para alignment=segment, responda ao sentido da frase; não invente os tempos das
palavras internas. Para alignment=word, escolha palavras relevantes e reúna ações
complementares, evitando efeito para cada preposição. Coordene significado e
movimento: percurso orientado por tempo, presença/material do objeto por café,
desaceleração/abertura de espaço por pausa são possibilidades, não receitas para
outros negócios. Declaração de vínculo não dispensa interação concreta: não usar
um beat invisível, opacidade já zero ou fade irrelevante só para satisfazer o plano.

Relacione fala e elementos escolhidos pela direção; não exija objeto realista,
moldura ou alternância em toda peça. Se direção
fornecida conflitar com os trechos, registre a dependência de revisão da direção;
não mude texto falado, identidade, fonte ou áudio para encaixar a composição.
Os IDs/tempos fazem parte do input e permanecem iguais na correção. Ajuste curvas,
estados e duração do movimento preservando os onsets fornecidos.

Na crítica, motion_role e coordination devem relacionar cue, ação e estados
observados. Vínculo temporal passa por validação do produto, mas não comprova que
o código realizou a ação. Quadros ao redor dos eventos ligados ajudam a examinar
antes/ação/depois; amostragem limitada não prova sincronia audiovisual ou correção
da transcrição. Declare uncertain na falta de evidência e mantenha escuta humana
na comparação. Não diga que o áudio foi analisado só porque há texto com tempos.

Reconhecimento automático local: quando transcript.provenance=local_asr_unreviewed,
os tempos vieram do ASR sobre a faixa original; são estimativas não revisadas,
não declaração do titular. Escolha palavras relevantes (ao menos uma quando
houver fala reconhecida) e vincule ações por speech_cue_id. Não ancore movimentos
em palavras com confidence abaixo de 0,6; registre a incerteza no source_usage.
Sem palavras reconhecidas, não invente falas nem declare silêncio confirmado.
Correção reutiliza o resultado; nomes próprios exigem revisão e não viram fatos
comerciais. Um pedido posterior pode fornecer speech_timing revisado para corrigir
texto/tempos, sem alterar o áudio. Não redistribua palavras proporcionalmente ao
texto nem use silêncio detectado como prova de fronteiras lexicais.
