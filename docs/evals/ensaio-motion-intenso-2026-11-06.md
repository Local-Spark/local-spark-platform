# Resultado do ensaio de motion intenso — 06/11/2026

## Peça e comparação

- [Versão intensa, v2 mínimo e última versão com biblioteca](../../.local/evals/motion-runs/b14bc09d-4131-4018-b666-1f9d0fff8651/report.html).
- [MP4 intenso](../../.local/evals/motion-runs/b14bc09d-4131-4018-b666-1f9d0fff8651/render/render.mp4).
- [Direção/fontes](../../.local/evals/motion-runs/b14bc09d-4131-4018-b666-1f9d0fff8651/answer.json),
  [trace](../../.local/evals/motion-runs/b14bc09d-4131-4018-b666-1f9d0fff8651/render/trace.json)
  e [custo](../../.local/evals/motion-runs/b14bc09d-4131-4018-b666-1f9d0fff8651/cost.json).

O titular autorizou uma chamada e envio do pacote, até US$ 0,75 adicionais,
conforme o [plano](plano-motion-intenso-2026-11-06.md). Operação nova:
`b14bc09d-4131-4018-b666-1f9d0fff8651`. Nenhum retry ou provedor adicional.

## Composição recebida

Direção: **Um segundo muda o quadro**. Três impactos: chegada/compressão da
forma em 0,68 s, revelação do tema creme em 3,05–3,78 s e reorganização verde
em 8,06–9,04 s. Texto e fundo são revelados por máscaras de composição,
preservando a inversão de contraste; não é uma troca global por interpolação
que deixa letras e fundo iguais no meio.

O código inclui funções reais adaptadas da biblioteca:

- `showreel`: ponto, antecipação/compressão, morfose e máscaras tipográficas;
  **`cap5` recomposto em 42 arcos com semente fixa e ondas**, e **`cap6` nas
  letras que mudam de linha e assentam**. Não foi utilizada `faisca`.
- `app-de-motion`: interpolação contínua de posição, proporção, rotação,
  foco e zoom da mesma janela de vídeo.
- `diagrama`: percurso amostrado e ponto/rastro cuja chegada provoca a
  revelação. Não há representação de etapas não confirmadas do preparo.

Mesma gravação/voz/kit, skill própria Reel por versão/hash e mesmos oito
quadros do benchmark. Sem mídias da galeria. A gravação segue a ordem original,
sem os cortes de tempo da variante anterior; retenção final limitada aos
últimos milissegundos. Voz integral, música e três cliques no mix. Aparece
`Saiba mais`, previsto no kit, mas destino não confirmado continua pendente
para eventual publicação.

## Custo e fidelidade

Uma chamada `gpt-6.1-sol/high`, HTTP 200/completed em **345,746 s**.
47.321 tokens de entrada (47.318 cache-write) e 19.030 de saída, incluindo
9.735 de raciocínio. Estimativa conservadora: **US$ 0,3086025**, não fatura;
reserva US$ 0,75 preservada.

HTML/JS renderizados conferem integralmente com a resposta recebida. Não houve
ajuste manual da cena. Assets, referências, código, resposta, custo e avisos
MIT permaneceram congelados no diretório da execução.

Saída: **11,2 s, 720×1280, 30 fps, H.264/AAC**, 1.707.093 bytes, 336 quadros.
SHA-256: `61d3b3585378a08e3cdfe93bfebbd9dd0164e0185c3d468aa59747d1f0cb5bc8`.
Decodificação integral passou; sandbox normal do Chromium e nenhuma requisição
inesperada. Conferidos os arquivos de três players e 15 links locais.
Medição de áudio: média −14,6 dB e pico −3,7 dB; isso não substitui escuta.

## Avaliação e limites

**Feedback posterior do titular:** “muito legal. melhorou bastante.” Solicitou
validar outras linguagens intensas, outros negócios fictícios, story e carrossel.
Isso é avaliação positiva desta exploração, sem preferência comparativa declarada
ou adoção universal. [Registro vigente e sequência](motion-registro-de-validacao.md).

**Atualização após diversidade:** o titular declarou esta Intensa explicitamente
a melhor versão até agora, gostou também do Cartaz e menos do Giz. A preferência
comparativa foi declarada nessa avaliação posterior; não fixa estilo universal.

Código e quadros amostrados confirmam inversões de tema, vídeo presente desde
o início e mecanismos adicionais da biblioteca. As amostras não equivalem a
assistir à peça ou ouvir o mix; não houve escuta perceptiva nova. Legendas
mantêm tempos históricos estimados. A permanência de marca incidental no
material e a fluidez de todo o filme exigem revisão final.

Esta é a versão experimental mais intensa solicitada, não declaração de
qualidade máxima atingida ou estilo padrão do produto. O titular avalia o
resultado final e se prefere esta direção ao v2. Não houve nova alteração de
código de produção ou CI integral apenas para esta variante de prompt.
