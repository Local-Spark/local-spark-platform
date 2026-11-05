# Ensaio de motion com chamadas reais — 05/11/2026

O titular informou que **prefere o Reel v2**, pois faz mais sentido para a
direção de motion que busca. A preferência é específica deste ensaio e não é
aprovação de publicação ou demonstração de melhor qualidade em geral.

O titular autorizou chamadas pagas, pediu qualidade superior e acesso aos
inputs, prompts, respostas e resultados. O ensaio foi direto, sem banco novo,
Temporal, frontend ou publicação. O
[trace completo](../../.local/evals/motion-referencia-2026-11-05/real-v1/TRACE.md)
reúne os pedidos e respostas reais por etapa, quadros e hashes, arquivos de
áudio, prompts de direção e refação, saídas do modelo, ledger e adaptações.

O vídeo indicado pelo titular mostra, em quadros estáticos próximos de 10:36,
uma galeria de estilos. Não foi possível identificar uma única peça nem avaliar
seu movimento ou áudio com esses quadros; o modelo recebeu somente essa
descrição, não a referência em vídeo. Os arquivos da referência não foram
arquivados no projeto. Seu interesse em uma biblioteca própria foi registrado
na [proposta de estilos](../design/biblioteca-estilos-motion-2026-11-05.md).

## Execução e resultados

| Etapa | Resultado e limite |
| --- | --- |
| Jev real para Reel e carrossel | Ambos identificaram pedido de conteúdo e retornaram `clarify`: formatos de vídeo e carrossel não estão habilitados. A direção seguinte é experimental e não prova integração. |
| Transcrição real | O áudio extraído do vídeo fictício foi enviado a `gpt-transcribe`. Retornou “momentos só seu” em lugar de “um momento só seu”; saída bruta preservada e legenda corrigida com base na locução sintética conhecida. Não retornou tempos por palavra. |
| Direção real | `gpt-6.1-sol` recebeu mensagem, kit, skill, padrões parciais e seis quadros do vídeo ou uma foto; produziu HTML/GSAP HyperFrames. O modelo não recebeu o vídeo integral nem ouviu seu áudio. O código original permanece nas respostas. |
| Refação real do Reel | Uma terceira direção foi chamada dentro do limite operacional, após identificar que a primeira direção era contida. O modelo recebeu a versão anterior e a correção de fala, e propôs uma composição diferente. |
| Renderização | HyperFrames, GSAP, Chromium e FFmpeg locais em processo isolado; o HTML foi verificado e as adaptações registradas. A peça original e a cópia executada são distintas. |

O carrossel tem três MP4s e PNGs:
[página 1](../../.local/evals/motion-referencia-2026-11-05/real-v1/carrossel/pagina-01.mp4),
[página 2](../../.local/evals/motion-referencia-2026-11-05/real-v1/carrossel/pagina-02.mp4) e
[página 3](../../.local/evals/motion-referencia-2026-11-05/real-v1/carrossel/pagina-03.mp4).
O [Reel v1 corrigido](../../.local/evals/motion-referencia-2026-11-05/real-v1/video/adaptado-reel/reel-v1-corrigido.mp4)
e a [refação v2](../../.local/evals/motion-referencia-2026-11-05/real-v1/video/adaptado-reel-v2/reel-v2.mp4)
estão disponíveis para comparação.

A primeira renderização do Reel deixou a legenda inicial invisível; foi mantida
para evidência e outra versão a corrigiu. A refação do modelo omitiu um `id` de
vídeo necessário ao HyperFrames, o que o deixaria congelado; a cópia para render
recebeu `id` e ajustes de movimento/estado inicial. Os prompts e respostas não
foram reescritos. As adaptações incluem usar fontes e músicas locais licenciadas,
correção da fala e ajustes de áudio para ser audível.
O Reel v2 usa a gravação em continuidade, com reenquadramentos e transições
gráficas; isso não demonstra seleção de cortes semânticos de fala humana.

Fontes são fictícias: foto CC0 de croissant como imagem enviada, gravação
ilustrativa de [Stevenndori289](https://commons.wikimedia.org/wiki/File:Latte_Coffee_making.webm)
sob [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/) com fala
sintética adicionada, e trilha [Jazz Piano, Serolillo](https://commons.wikimedia.org/wiki/File:Jazz_Piano.ogg)
sob [CC BY 2.5](https://creativecommons.org/licenses/by/2.5/). A pessoa no vídeo
não é o cliente nem disse a fala; o original tem apenas 360 × 640 pixels.

## Custo e limites

Seis operações foram concluídas, com **US$ 0,78 em reservas** dentro do teto
operacional de US$ 0,80. O ledger estimou US$ 0,141136 com a tarifa básica de
entrada; incluindo tarifa de escrita no cache, a estimativa é **US$ 0,147533**,
pressupondo que esses tokens estão incluídos no total de entrada. A fatura
continua pendente, assim como infraestrutura e trabalho não medidos.

Os arquivos têm áudio e foram decodificados; imagens e legendas foram
inspecionadas. Não houve audição perceptiva, teste de compatibilidade com o
Instagram ou prova de loop contínuo. Falta revisão do titular. Esta rodada não
demonstra edição de uma fala humana real nem geração automática no produto.
