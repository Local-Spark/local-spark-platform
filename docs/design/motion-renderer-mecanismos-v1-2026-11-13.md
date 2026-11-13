# Renderer: palco e mecanismos v1

13/11/2026. Os estudos Maestros, Felipe Borges e as 41 referências pedem mecanismo executado e visto, não mais texto no prompt. Esta fatia faz só a parte do renderer.

## O que passou a ser código

Com `structural_floor: motion-production-quality-v3`, o HTML do modelo é descartado. O palco usa a caixa medida no primeiro quadro da fonte, quando ela existe. As palavras do Whisper, quando caem dentro da cena, definem o texto e o intervalo. Se houver cama de música e fala, o render aplica ducking. No storyboard, o PNG do início e do fim de cada batida estrutural são comparados. Se a foto não mudou, a batida é recusada.

Ainda não há MP4. Material que o clipe não tem, comparação com a referência e o `make ci` continuam fora.

Pedido sem o campo v3 continua no HTML do modelo.

## O que estas referências ainda exigem e esta fatia não faz

- Material antes da promessa: recorte, outra tomada, imagem conceitual. Não inventar o que o clipe não tem.
- Escuta humana da mistura. O ducking só entra quando já existe cama de música e palavras do Whisper.
- Calibrar a peça inteira contra uma referência e contra `cafe-pausa-final.mp4`. Teste e `adequate` não substituem isso.
- `make ci` desta branch e uma autorização nova. O executor de 13/11 não aponta para este código.
