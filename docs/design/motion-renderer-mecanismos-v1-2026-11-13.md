# Renderer: palco e mecanismos v1

13/11/2026. Os estudos Maestros, Felipe Borges e as 41 referências pedem mecanismo executado e visto, não mais texto no prompt. Esta fatia faz só a parte do renderer.

## O que passou a ser código

Com `structural_floor: motion-production-quality-v3`, o HTML do modelo é descartado antes do storyboard e do render. `compose_structural_stage` monta um palco `720×1280`: o vídeo em cover, a palavra dentro dele, a segunda cópia do vídeo para o glifo e a placa do kit. `mechanisms-v1.js` aplica, em `MechanismsV1.seek(ms)`, máscara, elipse para glifo, texto no eixo ou placa. O retângulo do objeto ainda é fixo (`0.32, 0.42, 0.36, 0.28`); o plano ainda não carrega a caixa medida.

`prove_beat_pixels` compara RGB cru do miolo do quadro e recusa batida que não mudou a foto. Ainda não é chamado pelo runner do Chromium. Sem diferença de pixel no teste sintético, falha. Sem MP4 novo.

Pedido sem o campo v3 continua no HTML do modelo.

## O que estas referências ainda exigem e esta fatia não faz

- Caixa do objeto vinda do quadro, não do retângulo fixo.
- Comparar os PNG que o Chromium gravar, no início e no fim de cada batida, e devolver o plano se a foto não mudou.
- Material antes da promessa: recorte, outra tomada, imagem conceitual. Não inventar o que o clipe não tem.
- Som: evento, ducking e escuta. O mixer já existe; a direção sonora automática não.
- Calibrar a peça inteira contra uma referência e contra `cafe-pausa-final.mp4`. Teste e `adequate` não substituem isso.
- `make ci` desta branch e uma autorização nova. O executor de 13/11 não aponta para este código.
