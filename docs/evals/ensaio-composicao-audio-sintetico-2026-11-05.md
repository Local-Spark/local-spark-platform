# Prova técnica de composição e áudio — 05/11/2026

Esta prova verifica o compilador próprio com vídeo e sinais sintéticos. Não é
ensaio de qualidade criativa: não houve mensagem de cliente, Jev, transcrição
ou direção por API. Os dados foram preparados pelo agente para exercitar
geometria, fades, seeks e o plano técnico de áudio. Custo de APIs: zero.

## Evidência preservada

- [MP4 sintético com duas faixas](../../.local/evals/motion-composition-proof-2026-11-05/audio/proof.mp4): H.264/AAC, 720 × 1280, 30 fps, 3 segundos.
- [Trace de fontes, plano, frames e saída](../../.local/evals/motion-composition-proof-2026-11-05/audio/trace.json).
- [Comparação de amostras PCM e AAC](../../.local/evals/motion-composition-proof-2026-11-05/audio/pcm-check.json).
- [Inspeção visual de fades](../../.local/evals/motion-composition-proof-2026-11-05/visual/visual-check.json).
- [Manifesto dos scripts, entradas e resultados](../../.local/evals/motion-composition-proof-2026-11-05/manifest.json).

SHA-256 do MP4 com áudio:
`28efc01740c4d839cd4f5cee4133175371941c912143e126ff911ed7ad41240e`.
Os arquivos privados são ignorados pelo Git. Os scripts preservados ainda usam
paths específicos do ambiente e não são um executável distribuível. Esta cópia
local preserva a evidência da sessão; não constitui backup independente.

## Verificações

A direção passa pelo `compile_motion_composition` e pelos módulos reais
`compileScene`/`mountScene`. Mídias e fontes são vinculadas por UUID/hash;
o protótipo confere os glifos usados e os seeks de vídeo. Os cinco frames
amostrados diferem e os pixels observados acompanham o fade esperado.

O plano de áudio usa dois sinais gerados localmente, com trims, deslocamentos,
ganhos e fades distintos. O rótulo `recorded_voice` é apenas fixture: nenhum
sinal contém fala humana. A mistura usa ganho mestre fixo de 0,6661394246,
calculado conservadoramente pela soma dos ganhos das faixas, antes da soma,
sem normalização dinâmica, limitador ou corte pela menor duração. Isso assume
entrada PCM limitada a [-1, 1]; não prova ausência de overshoot em decoders reais.

As 48.000 amostras foram comparadas com uma referência calculada separadamente.
O erro máximo ficou abaixo de 0,5 unidade PCM16; o pico medido foi 23.241 de
32.767. Os impulsos esperados e o silêncio inicial coincidiram. Após AAC, a
correlação foi 0,999991 e o melhor deslocamento foi zero amostras. A variante
silenciosa não contém stream de áudio. Esses resultados medem esta fixture,
não inteligibilidade, mixagem musical ou sincronismo de fala real.

## Limites e próxima fatia

Chromium foi iniciado com sandbox, ambiente sem credenciais, CSP e rotas locais
restritas. Não há prova de isolamento de rede pelo sistema operacional. Binários
locais de navegador/FFmpeg/FFprobe não estão empacotados para produção.
`speech_semantics_verified=false` permanece no plano.

Faltam executor reutilizável validado, limites e recuperação de produção,
empacotamento e avaliação criativa separada de Reel/story/carrossel com mensagem,
entradas, saídas e trace. A próxima rodada paga exige autorização própria conforme
o [plano de chamadas](plano-motion-v0-rodada-1-2026-11-05.md).
