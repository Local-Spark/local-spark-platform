# Ensaios diretos HyperFrames — 05/11/2026

O titular pediu dois ensaios rápidos e esclareceu que o cliente não escolhe
imagens do acervo: envia uma imagem quando deseja usá-la e envia o vídeo a ser
editado. As duas peças abaixo usam anexos fictícios e foram criadas pela IA
desta sessão enquanto a autorização para chamadas pagas era considerada.

| Caso | Resultado | Entradas e direção |
| --- | --- | --- |
| Reel | [MP4](../../.local/evals/hyperframes-2026-11-05/agent-reel/reel-final.mp4) | Vídeo fictício com fala sintética, kit da cafeteria e padrões gerais parciais; pedido simulado, Jev simulado e direção/código pelo agente desta sessão. |
| Carrossel | [Página 1](../../.local/evals/hyperframes-2026-11-05/agent-carrossel/pagina-1.mp4), [página 2](../../.local/evals/hyperframes-2026-11-05/agent-carrossel/pagina-2.mp4), [página 3](../../.local/evals/hyperframes-2026-11-05/agent-carrossel/pagina-3.mp4) | Uma foto CC0 simula imagem enviada; kit da cafeteria e padrões gerais parciais. Jev simulado e direção/código pelo agente desta sessão. PNGs das páginas estão na mesma pasta. |

O processo usou HyperFrames 0.8.181, GSAP, Chromium e FFmpeg locais. O Reel tem
aproximadamente 11,21 s e 540 × 960, com cortes, movimento tipográfico, transições, legendas
por frases, voz sintética, trilha e efeitos. A voz foi adicionada ao vídeo
simulado antes do teste e não pertence à pessoa retratada; o áudio do cliente
real e sua transcrição ainda não foram avaliados. O vídeo original tem apenas
360 × 640. O carrossel tem três vídeos independentes de quatro segundos, cada
um com imagem, elementos animados e música, em 540 × 676. Os PNGs são prévias
extraídas das páginas, não composições editáveis separadas.

Os roteiros do [Reel](../../.local/evals/hyperframes-2026-11-05/agent-reel/ROTEIRO.md)
e do [carrossel](../../.local/evals/hyperframes-2026-11-05/agent-carrossel/ROTEIRO.md)
registram mensagens, respostas Jev simuladas, contexto, materiais, decisões,
skills e hashes. O código das composições está nos diretórios locais correspondentes.
As referências usadas são padrões gerais da análise parcial anterior, ainda não
conferidos individualmente. Os exemplos públicos e a skill externa foram
estudados como técnicas; não foram copiados vídeos, marcas ou identidade deles.

Fontes: imagem ilustrativa CC0 `docs/evals/assets/croissant-cc0.jpg`; vídeo de
[Stevenndori289](https://commons.wikimedia.org/wiki/File:Latte_Coffee_making.webm),
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), editado e com
voz sintética adicionada; música [Jazz Piano, Serolillo](https://commons.wikimedia.org/wiki/File:Jazz_Piano.ogg),
[CC BY 2.5](https://creativecommons.org/licenses/by/2.5/). O vídeo original é
ilustrativo, não é registro do negócio fictício. Respeitar os créditos e termos
ao compartilhar trabalhos derivados.

Não houve chamadas pagas de Jev, transcrição ou modelo editorial nestas peças;
custo de API externa US$ 0, sem estimativa do tempo ou infraestrutura local. O
transcritor real não foi acionado e os tempos das legendas usam as durações das
frases sintéticas conhecidas, não alinhamento por palavra. Foi preparado um
executor para teste separado com APIs reais e orçamento próprio, ainda sujeito
à autorização. Os MP4s foram decodificados, a presença de áudio foi verificada e
quadros foram inspecionados. A qualidade e sincronia do áudio não foram avaliadas
por audição perceptiva; emenda dos loops e aceitação pelo Instagram não foram
testadas. Não há integração nem publicação. Revisão do titular pendente.
