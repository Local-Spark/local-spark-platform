---
name: instagram-reel-video
version: 15
description: Reel com uma gravação full-bleed, marca do kit e tipografia cinética sobre ação.
---

# Reel de vídeo — Fatia A (VR1–VR3)

Preserve pedido, fatos confirmados, identidade e tom. Um pedido de pausa
aconchegante continua soft: frases curtas e convite, sem oferta ou urgência inventada.
A gravação é o quadro inteiro 9:16, cover do início ao fim; proteja mãos, produto
e rosto no crop usando as amostras. Se o crop inviabilizar a ação, declare a
pendência antes de construir. Nunca use cartaz creme, janela, moldura ou letterbox.
A marca vem do logo autorizado do kit em overlay discreto, sem label fixo hero.
Sem logo, peça material: não fabrique identidade nem promova nome a logotipo.

VR1–VR3: gravação assets/source.mp4 full-bleed cover 9:16 do primeiro ao último frame; sem janela, cartaz, letterbox, moldura ou ocultação. Preserve uma gravação inteira e seu áudio, até 60s/50MiB. Sem EDL, música nova, TTS, avatar ou novo renderer. Cada cena declara video_layout={mode:cover,video_element_id,brand_element_id,text_element_ids,cta_element_id:null|id}. Marca é IMG assets/logo.png discreta sobre a ação, nunca nome fixo como hero. Sem logo autorizado, solicitar material; não fabricar logo nem substituir por label. Todos os textos são declarados em text_element_ids e relacionados ao vídeo via related_element_ids. Frases curtas conforme briefing, sem hard-sell inventado. Enter, transform e exit suaves, lineares; start_state/end_state são JSON exato {x:number,y:number,opacity:number}, em px, sem escala/rotação. Beats contíguos com estados contínuos, cobrindo a cena; enter parte de opacity=0 e termina em 1, exit termina em 0; transform desloca pelo menos 4px. Execute translate(xpx,ypx) e opacity no próprio nó de texto, com interpolação absoluta, inclusive após seeks reversos. Texto legível sobre ação: fonte >=28px no canvas 720, cor branca, scrim preto local opacidade .75–.8 no pai direto, padding <=16px, largura <90% e altura <25% do quadro. Sem sombra/blur/placa/rodapé. Limites do texto entre 12% e 78% da altura; marca <=25% largura e <=12% altura. Última cena declara CTA com hold estável opacity=1 de pelo menos 1500ms antes da saída. A guarda confere plano e execução, não qualidade perceptual; revisão humana continua necessária.

Use fontes e cores do kit no tratamento, reservando contraste branco/scrim preto
local para a leitura. A cor não justifica fundo sólido de tela inteira.
No plano, declare video_layout em cada cena e todos os IDs existentes no DOM.
O scrim é pai direto do texto e acompanha seu deslocamento pelo padding real;
não use transform nem overflow nos ancestrais do texto. Corpo sem overflow hidden.
O vídeo tem um único nó, asset autorizado, seek absoluto e áudio original inteiro.
A fonte não é reiniciada nas cenas; não crie EDL, cortes, zoom obrigatório ou mix novo.
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

Para cada text_element_id, beats cobre exatamente [scene.start_ms, scene.end_ms]: beats[0].phase=enter e beats[0].start_ms=scene.start_ms; beats[-1].phase=exit e beats[-1].end_ms=scene.end_ms. Beats contíguos, sem lacunas e com estados contínuos. Proibido hold com opacity=0, inclusive antes de enter ou depois de exit: hold exige start_state=end_state e opacity=1. Invisibilidade só via enter/exit; transform permanece visível (opacity=1) e desloca pelo menos 4px. CTA final mantém hold estável >=1500ms entre enter e exit. Não preencher pontas do timeline com holds fantasmas para adiar uma frase. Se a sequência de frases não couber nestas fronteiras, reformule a composição/plano dentro de VR1–VR3; não invente EDL nem mude a gravação.
