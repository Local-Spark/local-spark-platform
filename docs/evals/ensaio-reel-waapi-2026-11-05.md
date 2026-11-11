# Reel v2 com composição própria — 05/11/2026

Depois da [prova mecânica](ensaio-waapi-mecanico-2026-11-05.md), adaptamos a
direção do [Reel v2](ensaio-motion-referencia-2026-11-05.md) para HTML/CSS e
animações nativas do navegador, sem executar o JavaScript original nem GSAP.
Não houve nova chamada Jev, transcrição ou direção por API: as saídas anteriores
foram reutilizadas e a IA desta sessão fez a adaptação técnica. Não foram usados
banco, Temporal ou sistema completo para avaliar esta hipótese.

## Peça e rastreabilidade

- [MP4 adaptado](../../.local/evals/motion-waapi-reel-2026-11-05/reel-waapi.mp4).
- [Comparação de seis pares de quadros](../../.local/evals/motion-waapi-reel-2026-11-05/comparacao-quadros.jpg).
- [Relatório privado, fontes e execução](../../.local/evals/motion-waapi-reel-2026-11-05/LEIA-ME.md) e [trace](../../.local/evals/motion-waapi-reel-2026-11-05/trace.json).

A mensagem simulada pedia editar o preparo de café com cortes, transições,
motion e legendas. O Jev daquela rodada pediu esclarecimento; sua saída não foi
reescrita como se tivesse reconhecido motion. A fonte é um vídeo ilustrativo
de Stevenndori289 sob CC BY-SA 4.0, com voz sintética que não pertence à pessoa
retratada, música de Serolillo sob CC BY 2.5 e fontes DejaVu do kit. Os créditos,
links, correções anteriores e hashes permanecem nos traces. `.local` é privado
e ignorado pelo Git, não backup ou pacote de distribuição.

## Verificação técnica

O arquivo tem H.264/AAC, 720 × 1280, 30 fps e 11,200 segundos; foi decodificado
integralmente sem erro. SHA-256:
`2e9e38be97240745a7f5abbfa3dfea3962d445375f2df48575c6968bef4cb7d0`.
A primeira tentativa foi rejeitada e preservada: eventos de seek ocorriam, mas
a gravação permanecia no tempo zero. A resposta local de mídia passou a atender
intervalos de bytes, e os 336 seeks seguintes foram verificados com tolerância
inferior a 50 ms. Amostras da janela de vídeo confirmaram mudança dos pixels.

Os seis pares de quadros mantêm a hierarquia, texto, gravação e fechamento da
referência v2. Em 8 s o círculo da transição é maior; curvas de animação foram
aproximadas. A correlação técnica do áudio com o v2 foi 0,99978 em 178.880
amostras PCM, alinhadas no tempo zero; não é audição ou medida de qualidade.

Chromium usou sandbox habilitada, ambiente sem credenciais, CSP e rotas
restritas aos assets identificados. Isso não prova isolamento de rede no sistema
operacional. Dependências são binários locais temporários; não foram empacotadas
para produção. O executor é específico deste caso e não compila o contrato
`MotionDirection`, seleciona estilos ou executa um fluxo completo do produto.

## Avaliação e próximos passos

O titular avaliou a adaptação e confirmou em entrevista: **podemos avançar com
essa base técnica**. O aceite vale para este caso e não fixa um estilo para os
demais negócios, homologa produção ou autoriza gasto/postagem. A gravação
continua em sequência, sem demonstração
de cortes semânticos de fala humana. Story e carrossel ainda exigem avaliação
própria. Esta evidência permite continuar investigando o renderer; não conclui
geração integrada nem comprova uso seguro em produção ou postagem.

Custo de APIs nesta execução: **zero**. Trabalho e infraestrutura não medidos.
O [plano de nova rodada](plano-motion-v0-rodada-1-2026-11-05.md) tem orçamento
proposto separado e ainda não autoriza nenhuma chamada.
