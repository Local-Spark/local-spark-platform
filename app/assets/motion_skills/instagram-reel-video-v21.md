---
name: instagram-reel-video
version: 21
description: Reel com uma gravação full-bleed, marca do kit e tipografia cinética sobre ação.
---

# Reel de vídeo — Fatia B (VR1–VR5)

Preserve pedido, fatos confirmados, identidade e tom. Um pedido de pausa
aconchegante continua soft: frases curtas e convite, sem oferta ou urgência inventada.
A gravação é o quadro inteiro 9:16, cover do início ao fim; proteja mãos, produto
e rosto no crop usando as amostras. Se o crop inviabilizar a ação, declare a
pendência antes de construir. Nunca use cartaz creme, janela, moldura ou letterbox.
A marca vem do logo autorizado do kit em overlay discreto, sem label fixo hero.
Sem logo, peça material: não fabrique identidade nem promova nome a logotipo.

VR1–VR3: gravação assets/source.mp4 full-bleed cover 9:16 do primeiro ao último frame; sem janela, cartaz, letterbox, moldura ou ocultação. Preserve a fala e áudio da gravação até 60s/50MiB. EDL e crop conforme contrato B. Sem música nova, TTS, avatar ou novo renderer. Cada cena declara video_layout={mode:cover,video_element_id,brand_element_id,text_element_ids,cta_element_id:null|id}. Marca é IMG assets/logo.png discreta sobre a ação, nunca nome fixo como hero. Sem logo autorizado, solicitar material; não fabricar logo nem substituir por label. Todos os textos são declarados em text_element_ids e relacionados ao vídeo via related_element_ids. Frases curtas conforme briefing, sem hard-sell inventado. Enter, transform e exit suaves, lineares; start_state/end_state são JSON exato {x:number,y:number,opacity:number}, em px, sem escala/rotação. Beats contíguos com estados contínuos, cobrindo a cena; enter parte de opacity=0 e termina em 1, exit termina em 0; transform desloca pelo menos 4px. Execute translate(xpx,ypx) e opacity no próprio nó de texto, com interpolação absoluta, inclusive após seeks reversos. Texto legível sobre ação: fonte >=28px no canvas 720, cor branca, scrim preto local opacidade .75–.8 no pai direto, padding <=16px, largura <90% e altura <25% do quadro. Sem sombra/blur/placa/rodapé. Limites do texto entre 12% e 78% da altura; marca <=25% largura e <=12% altura. Última cena declara CTA com hold estável opacity=1 de pelo menos 1500ms antes da saída. A guarda confere plano e execução, não qualidade perceptual; revisão humana continua necessária.

Use fontes e cores do kit no tratamento, reservando contraste branco/scrim preto
local para a leitura. A cor não justifica fundo sólido de tela inteira.
No plano, declare video_layout em cada cena e todos os IDs existentes no DOM.
O scrim é pai direto do texto e acompanha seu deslocamento pelo padding real;
não use transform nem overflow nos ancestrais do texto. Corpo sem overflow hidden.
Cada cena ativa tem um único nó VIDEO, asset autorizado, seek absoluto e áudio original inteiro.
A EDL declara cortes e crop obrigatórios. Com áudio, mantenha tempo contínuo da fonte; sem áudio pode remontar.
O repertório action-type demonstra apenas a interpolação; ajuste composição e
intervalos ao material. Não inferir qualidade, sincronismo ou aceite pelos helpers.

Entregue scene_direction, motion_plan e demais campos no schema do integrador;
HTML e scene_init somente na etapa de implementação. O mesmo plano aprovado
é executado no storyboard e render. Preserve limites, isolamento, proveniência,
IDs, determinismo e os cues de fala fornecidos. Ligue speech_cue_id ao início
do beat (tolerância 34ms), sem redistribuir palavras nem inventar sincronismo. Não invente transcrição a partir
de quadros; ASR não revisado continua incerto. Sem rede, imports ou novas bibliotecas.
As referências orientam mecanismos, nunca fornecem assets ou fatos do cliente.
O novo MP4 e a revisão humana precisam de autorização posterior do titular.

## Fronteiras obrigatórias VR3

Para cada text_element_id, beats cobre exatamente [scene.start_ms, scene.end_ms]: beats[0].phase=enter e beats[0].start_ms=scene.start_ms; beats[-1].phase=exit e beats[-1].end_ms=scene.end_ms. Beats contíguos, sem lacunas e com estados contínuos. Proibido hold com opacity=0, inclusive antes de enter ou depois de exit: hold exige start_state=end_state e opacity=1. Invisibilidade só via enter/exit; transform permanece visível (opacity=1) e desloca pelo menos 4px. CTA final mantém hold estável >=1500ms entre enter e exit. Não preencher pontas do timeline com holds fantasmas para adiar uma frase. Se a sequência de frases não couber nestas fronteiras, reformule a composição/plano dentro de VR1–VR3; use a EDL aprovada e preserve fala e áudio.

## Uso do repertório business-video-reel-v4 por cena

Cada cena inclui em scene.elements seu próprio elemento role=video com
asset_id=assets/source.mp4 (VIDEO) e role=image com asset_id=assets/logo.png (IMG).
video_layout.video_element_id e video_layout.brand_element_id apontam para esses
IDs locais; proibir IDs de outra cena, inclusive referências a cena1-video ou
cena1-logo sem declará-los na cena atual. Use IDs únicos por cena e repita os nós
de mídia em cada cena, mesmo reutilizando os mesmos arquivos autorizados.
text_element_ids, cta_element_id e related_element_ids usam os IDs da própria cena.
Um briefing soft pode usar uma cena contínua; não há obrigação de dividir frases
em cenas. Se multi-cena, repetir VIDEO e IMG em elements de todas as cenas e
vincular staging.material_element_ids aos respectivos IDs locais. Na implementação,
existe exatamente um VIDEO no DOM em cada seek: associe seu id ao video_element_id
da cena ativa preservando a mesma gravação, ou mantenha os demais nós fora do DOM.
Ocultar vídeos extras com display:none não satisfaz a guarda. Repita as declarações
no plano, não vídeos simultâneos no documento. Logo/textos usam os IDs locais da
cena ativa. Seek absoluto da gravação inteira, inclusive ao voltar de cena,
sem reinício, cortes, EDL ou áudio duplicado. O exemplo cta-plan do repertório v2
orienta beats, não substitui a declaração dos elementos de mídia de cada cena.
Preserve enter no scene.start_ms e exit no scene.end_ms, sem hold fantasma;
CTA final com hold estável visível >=1500ms entre enter e exit.

## Transform obrigatório em CADA texto, inclusive título e CTA finais

Antes de entregar o plano, percorra cada cena e cada text_element_id: o próprio
texto deve ter phases enter, transform e exit. enter → hold → exit é inválido,
mesmo quando enter/exit deslocam 12px/8px. Movimento de hastes, molduras, vídeo,
pais ou outros textos não substitui o transform do texto. related_element_ids
não transfere essa obrigação. CTA com hold longo também precisa de transform.

Planeje enter → transform → hold → exit para CADA texto. O transform é um beat
separado, linear, opacity=1 nas duas pontas, com deslocamento de pelo menos 4px
no próprio texto. Pode ser suave e breve para preservar o briefing soft. Depois,
reserve hold estável visível >=1500ms no CTA antes do exit; não use transform
imóvel, não renomeie hold sem alterar estados e não conte enter/exit como transform.
Verifique continuidade de estados/tempos, enter no início e exit no fim da cena.

Exemplo de beats para UM texto de uma cena 6780–11200ms (replicar a estrutura
em cada texto, inclusive CTA, adaptando posições e tempos ao plano real):

```json
[
  {
    "phase": "enter",
    "start_ms": 6780,
    "end_ms": 7380,
    "start_state": "{\"x\":0,\"y\":0,\"opacity\":0}",
    "end_state": "{\"x\":0,\"y\":0,\"opacity\":1}",
    "trajectory": "gentle",
    "curve": {
      "kind": "linear",
      "parameters": []
    }
  },
  {
    "phase": "transform",
    "start_ms": 7380,
    "end_ms": 7780,
    "start_state": "{\"x\":0,\"y\":0,\"opacity\":1}",
    "end_state": "{\"x\":4,\"y\":0,\"opacity\":1}",
    "trajectory": "gentle",
    "curve": {
      "kind": "linear",
      "parameters": []
    }
  },
  {
    "phase": "hold",
    "start_ms": 7780,
    "end_ms": 10600,
    "start_state": "{\"x\":4,\"y\":0,\"opacity\":1}",
    "end_state": "{\"x\":4,\"y\":0,\"opacity\":1}",
    "trajectory": "gentle",
    "curve": {
      "kind": "linear",
      "parameters": []
    }
  },
  {
    "phase": "exit",
    "start_ms": 10600,
    "end_ms": 11200,
    "start_state": "{\"x\":4,\"y\":0,\"opacity\":1}",
    "end_state": "{\"x\":4,\"y\":0,\"opacity\":0}",
    "trajectory": "gentle",
    "curve": {
      "kind": "linear",
      "parameters": []
    }
  }
]
```

## Composição executável pela guarda DOM da Fatia A

No planejamento desta versão, use somente gravação, logo autorizado e textos
cinéticos com seus fundos locais de leitura. Não planeje hastes, barras decorativas,
molduras, linhas, ícones, SVG, canvas, pseudo-elementos ou outros grafismos pintados.
A guarda DOM rejeita esses overlays mesmo que estejam declarados com role=graphic
no motion_plan. Estarem declarados não os torna executáveis nesta Fatia A.
Desenvolva a mensagem pela gravação e pelo movimento dos próprios textos; requisitos
genéricos de elaboração não autorizam decoração incompatível com esta guarda.
Não entregue plano com grafismos para depois removê-los silenciosamente do HTML.

Na implementação, o scrim é o pai direto do texto: fundo preto com alpha constante
entre .75 e .8 SEMPRE que o texto tem opacity>0, inclusive no primeiro/último frame
visível de enter/exit. Nunca multiplique o alpha do scrim pela opacidade do texto.
Não anime opacity do pai/ancestrais: mantenha opacity=1, sem transições CSS,
transform, overflow que corte o texto, sombra ou border-radius nesses ancestrais.
Somente o próprio nó de texto interpola translate(x,y) e opacity conforme beats.
Quando o texto é exatamente invisível, o fundo pode ser transparente; não aplique
fade ao fundo. O scrim deve acompanhar o texto por left/top, com padding <=16px,
sem cancelar o transform declarado no próprio texto nem acumular posições entre seeks.

Exemplo de implementação para um span/div de texto com pai exclusivo de scrim,
ambos sem filhos decorativos. x/y são os estados interpolados do plano em px;
o origin opcional define a posição de layout de base (não altera os beats).
O pai fica num contêiner sem transform/clip, com origem conhecida. O texto usa
fonte >=28px, branco, sem quebra inesperada; dimensione a frase e origin para
respeitar os limites do quadro. Chame em TODO seek, inclusive reversos e opacity=0:

```javascript
function videoTextWithScrim(node, state, originX = 0, originY = 0) {
  const {x, y, opacity} = state;
  const backing = node.parentElement;
  Object.assign(backing.style, {
    position: 'absolute', left: (originX + x - 12) + 'px',
    top: (originY + y - 12) + 'px', width: 'max-content', height: 'max-content',
    padding: '12px', opacity: '1', transform: 'none', overflow: 'visible',
    transition: 'none', borderRadius: '0px', boxShadow: 'none',
    backgroundColor: opacity > 0 ? 'rgba(0,0,0,.76)' : 'transparent'
  });
  Object.assign(node.style, {
    position: 'relative', display: 'block', left: (-x) + 'px', top: (-y) + 'px',
    transform: 'translate(' + x + 'px,' + y + 'px)', opacity: String(opacity),
    transition: 'none', margin: '0', whiteSpace: 'nowrap'
  });
}
```

Este exemplo não instala dependências nem certifica qualidade artística. Use os
mesmos beats validados, um VIDEO no DOM em cada seek, logo por cena e texto sem
grafismos adicionais. Confira enter, transform, hold e exit antes de entregar.

## Texto puro: nenhum elemento filho, inclusive quebras de linha

Cada nó identificado em video_layout.text_element_ids deve conter somente texto:
node.children.length === 0. Não insira <br>, <span>, <strong>, <em>, ícones ou
qualquer outro elemento dentro dele, nem use innerHTML para formatar a frase.
Use textContent. <br> é elemento filho e será rejeitado mesmo sem decoração.
O pai direto continua sendo o scrim; o próprio nó de texto recebe transform/opacity.

Para várias linhas no MESMO texto, use caracteres de nova linha em textContent
com CSS white-space:pre-line, ou quebra natural com white-space:normal e largura
adequada. Não confunda a string literal barra+n com uma nova linha real. Se usar
videoTextWithScrim, aplique whiteSpace='pre-line' após a chamada em CADA seek,
pois o exemplo configura nowrap. A alternativa é texto curto em uma única linha.
Não divida em spans internos nem crie IDs extras fora do plano para contornar a regra.

Meça a frase inteira com as fontes carregadas, incluindo todas as linhas. Preserve
fonte mínima, altura do scrim <25%, largura <90%, margens e texto entre 12–78% da
altura do quadro; max-width com nowrap não garante que os glifos caibam. O CTA
continua com transform próprio e hold visível >=1500ms. Antes de entregar a
implementação, confira children.length===0 em TODOS os textos de TODAS as cenas,
inclusive os que começam invisíveis; a falha aparece no primeiro frame visível.

## EDL e motion obrigatórios

Fatia B VR4–VR5: cada video_layout declara edit={source_in_ms,source_out_ms,purpose,transition,intent,crop_from,crop_to}. purpose: hook/detail/invitation; >=2 funções distintas. transition=cut. Cenas contíguas, sem sobreposição; duração de cada segmento igual ao intervalo na fonte, sem speed ramp. Tempos na fonte dentro da duração original; duração final preservada nesta versão. Com áudio, source_in_ms=scene.start_ms: manter fala e áudio inteiros; cortes são de reenquadramento. Sem áudio, remonte temporal permitido. Cada corte muda escala >=.06 ou x/y >=.04. crop_from/crop_to={scale:1..1.35,x,y}; x/y são frações do canvas. Em cada segmento, variar escala >=.03 ou x/y >=.02 com intenção, linearmente. Cobertura: abs(x),abs(y)<=(scale-1)/2. VIDEO absoluto 0,0, dimensões do canvas, object-fit:cover, object-position:50% 50%, transform-origin:50% 50%; transform translate(x*width px,y*height px) scale(scale). Seek da fonte = source_in_ms + ms - scene.start_ms; aguardar seeked; clamp a min(out,duração real)-1ms, tolerando só padding final de até 34ms. Um único VIDEO, renomeado para o ID da cena ativa. Não duplicar mídia. VR1–VR3, texto puro, scrim estável e scene-visibility permanecem obrigatórios. Grafismos e assets adicionais não são habilitados nesta versão. Sem inventar materiais. VR6 unavailable: edl_music_mix_not_qualified. Não adicionar música/SFX nem chamar provedor. Briefing soft: pausa aconchegante, frases curtas e kit, sem hard-sell.

O executor confere, não aplica o crop nem o seek da fonte. Use o exemplo videoEditSeek do repertório antes de retornar de window.seek(ms). O modelo ainda executa texto, logo e scrim. Descreva em intent o que o reenquadramento destaca sem cortar mãos, produto ou rosto essenciais. Dois rótulos sem mudança perceptível da gravação falham.

## Duração real da fonte e arredondamento da saída

Exceção final verificada: somente a última cena pode ter intervalo na fonte menor que sua duração por 1–34ms, quando source_out_ms é exatamente source.duration_ms medido pelo servidor. Esse restante é padding do último frame, não corte nem speed ramp. Nunca aplicar em cenas internas, com duração desconhecida ou fim inventado. Duração de saída e áudio autorizado permanecem intactos.
Não confundir source.duration_ms com output.duration_ms. Exemplo sintético: fonte 5976ms, saída 6000ms, cena final 3000–6000ms com in/out 3000–5976ms deixa 24ms de último frame. Demais cenas mantêm duração exata. O áudio original não é estendido.
