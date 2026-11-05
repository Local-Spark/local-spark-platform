# Ensaios locais iniciais: vídeo e carrossel com motion

Em 04/11/2026 foram feitas duas prévias independentes, sem chamadas de API
pagas, sem banco novo e sem publicação. A assistente decidiu diretamente as
peças e usou as novas skills como instruções; o Jev foi simulado. Isso exercita
o briefing e a montagem visual, não a integração dos modelos, a resposta do
Jev real ou o fluxo de produção. As prévias aguardam avaliação do titular.
Nenhum padrão de referência externa foi fornecido nesta rodada, portanto ela
não mede o efeito das referências.

## 1. Vídeo de gravação

- Pedido simulado: “Gravei um pouco da preparação do café. Pode transformar em
  um vídeo convidando o pessoal a fazer uma pausa? Use as cores do meu negócio e
  coloque legendas se houver fala.”
- Resposta Jev simulada: “Vou preparar uma versão curta com as cores do negócio
  e um convite para uma pausa.”
- Entradas: kit fictício `catalog/kits/cafe-pausas/v1`, skill `instagram-reel`
  SHA-256 `dcde210402790fda13a686135ac5f31962cb91182106af5470fd8a49b1921dd8`
  e [gravação pública de Stevenndori289](https://commons.wikimedia.org/wiki/File:Latte_Coffee_making.webm),
  17,7 segundos, 360 × 640. O vídeo é ilustrativo, não representa o negócio
  fictício. O arquivo inclui áudio, que não foi avaliado nem usado; não houve
  transcrição nem teste de fala ou legendas.
- A assistente examinou quadros amostrados e escolheu usar os primeiros 14
  segundos, cores verde e creme, três mensagens curtas e animação simples de
  texto e acento. O FFmpeg local materializou a direção; não foi acionado um
  modelo de análise de vídeo da plataforma.
- Saída: `.local/evals/video-motion-2026-11-04/video/video-editado.mp4`, H.264,
  720 × 1280, 14 segundos, silencioso. A resolução original baixa foi ampliada,
  o que limita a nitidez. O arquivo foi decodificado e quadros foram inspecionados;
  não houve teste de publicação, avaliação do áudio nem aprovação do titular.
- Direitos: vídeo original de Stevenndori289, [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/),
  editado para a prévia. A licença exige atribuição, indicação de alterações e
  compartilhamento pela mesma licença quando aplicável. O arquivo mostra pessoa
  e marca de terceiro: a prévia não deve sugerir endosso ou que seja registro da
  cafeteria fictícia. O código de montagem está em `video/filtro.txt` no mesmo
  diretório local.

## 2. Carrossel animado

Pedido e resposta Jev simulados, fontes, textos, movimentos e legenda estão em
`.local/evals/video-motion-2026-11-04/carrossel/roteiro.md`. A assistente usou
o kit fictício e a skill `instagram-carrossel-motion` e planejou três páginas.
Cada página tem PNG e MP4 próprio de quatro segundos, H.264, 720 × 900 e sem
áudio. O movimento é um deslocamento sutil e periódico da foto, com texto fixo;
é um ensaio simples, ainda distante da ambição de motion graphics sofisticados.
As capas foram inspecionadas e os arquivos decodificados; a emenda do loop em
reprodução contínua, compatibilidade no Instagram e aprovação do titular ainda
precisam ser verificadas. Os PNGs são quadros das peças, não camadas editáveis.

## Custos e próximos passos

Custos de chamadas externas: **US$ 0**; tempo de trabalho e infraestrutura
local não foram medidos. Este valor não é projeção de custo de produção, pois
nenhuma API de IA, transcrição ou renderização paga foi chamada. O FFmpeg veio
de `imageio-ffmpeg` instalado em diretório temporário, sem alteração das
dependências do projeto. Antes de uma rodada paga, apresentar orçamento
específico por etapa e obter autorização; não reutilizar a reserva anterior.

Após a revisão das prévias, testar footage autorizado com fala e áudio,
legendas, motion mais elaborado e uso explícito de aprendizados de referências.
A integração das skills, aceitação de arquivos pela API e publicação no Instagram
continuam pendentes, assim como testes próprios dos limites e tratamento de erro.
