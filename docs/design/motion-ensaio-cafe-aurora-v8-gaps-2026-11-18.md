# Ensaio Café Aurora v8 — gaps e próxima fatia — 18/11/2026

## Ensaio v9 — próximo backlog noutro doc

Após R1–R3 + guarda v2, o ensaio `versao-1 (9).mp4` e o backlog S1–S4 estão em
[motion-ensaio-cafe-aurora-v9-gaps-2026-11-18.md](motion-ensaio-cafe-aurora-v9-gaps-2026-11-18.md).
Este documento permanece o diagnóstico v8 + histórico R1–R4.

## Atualização — R1–R3 implementados; aceite audiovisual pendente

Autorização posterior do titular: intent/regras v9, skill photo v20 e repertório
v12. `photo_layout` passa a ser obrigatório, com cover ≥2/3 do tempo exclusivo e
no máximo uma exceção estruturada em 1/3 das cenas. `photo_closing` só aceita
marca transparente. Guarda DOM versionada confere cover, execução dos transforms,
ancestrais/pseudos da logo e condições de leitura do CTA em cada seek do renderer
atual, incluindo storyboard/correções. Não injeta animações ou corrige crop.
Q2/O2/M3 e replay histórico preservados; R4 adiado, Music/mix intactos.
Detalhes, validação e limites em PROJECT/SDD/BL04/CHANGELOG/DECISIONS.
Sem A5b, chamada paga, novo MP4 ou aceite E2E; revisão humana continua pendente.

## Diagnóstico original e backlog que motivaram a fatia

Estado: **diagnóstico e backlog documentados** a partir de
`/Users/israelsilva/Downloads/versao-1 (8).mp4`. Não autoriza, por si,
implementação, chamada paga, A5b nem alteração de Music/renderer. Destinado a
um próximo chat/modelo.

Referências: Q1–Q3 em
[motion-ensaio-cafe-aurora-v7-gaps-2026-11-18.md](motion-ensaio-cafe-aurora-v7-gaps-2026-11-18.md);
O1–O3 em
[motion-ensaio-cafe-aurora-v6-gaps-2026-11-18.md](motion-ensaio-cafe-aurora-v6-gaps-2026-11-18.md);
Maestros [WuzMxEKJHkQ](../evals/analise-video-maestros-WuzMxEKJHkQ-2026-11-11.md).

## Evidência do ensaio v8

Arquivo: 15,0 s · 720×1280 · H.264 + AAC · ~1,72 Mbps (~3,2 MB).
Loudness ~**−31,6 LUFS** (inalterado).

Amostragem a 5 fps (cinza 90×160):

| Medida | v7 | **v8** |
| --- | --- | --- |
| Quase estático (diff &lt; 2) | ~80% | **~89%** |
| Diff médio | ~5,4 | **~3,6** |
| Holds ≥0,8 s | ~2,2–3,0 s | **~4,4 / 4,4 / 3,8 s** |
| Picos | várias trocas | **~5,2 s e ~10–11 s** |

Leitura humana / análise: fotos premium; **regrediu** vs v7 em cover e energia.
Peça inteira em template **Stories** (janela landscape + barras blur). Fecho com
**placa creme** AURORA + CTA. Estimativa vs propaganda “incrível” das refs
(~40 vídeos / Maestros): **~35–40%** (foto/mood alto; composição/motion/mix
baixos).

### Storyboard observado

1. **~0–5 s** — janela+blur (latte/croissant); “No meio do dia,” / “cabe uma pausa.”
2. **~5–10 s** — outra janela+blur (flat-lay vermelha); “Um café.” / “Um tempo seu.”
3. **~10–15 s** — díptico + card creme AURORA + “Conheça nosso cardápio”.

### Evolução vs regressão

| Melhorou / estável | Regrediu / falhou |
| --- | --- |
| Qualidade fotográfica / mood | Cover **sumiu** (v7 tinha gancho cover) |
| CTA legível no fecho | Energia métrica pior que v7 |
| Pipeline Music/logo presentes | Holds voltaram a ~4 s |
| | Logo ainda em **placa creme** |
| | Mix −31,6 LUFS |

Diagnóstico: Q1/Q3 **soft falharam de novo**. Q2 (densidade no plano) não
impediu miolo quase estático no render. Próxima fatia precisa de **enforcement
de layout/marca**, não só mais adjetivos no prompt.

## % vs propaganda incrível (critério de referência)

| Dimensão | ~% |
| --- | --- |
| Foto / mood | 70 |
| Composição cover 9:16 | 20–25 |
| Motion / energia contínua | 25–30 |
| Marca / fecho | 40 |
| Mix | 20 |
| Tipografia cinética | 25 |
| **Síntese ponderada** | **~35–40** |

Evolução desde o silêncio estático inicial: grande. Distância até o alvo das
refs: ainda a maior parte do caminho.

## Backlog priorizado (próxima implementação)

### R1 — Layout cover **hard** (prioridade máxima)

- Declarar layout por cena fotográfica no plano (ex.: `cover` | `contain_blur`)
  **ou** validar HTML/CSS pós-implementação (`object-fit: cover` full-frame,
  ausência de padrão janela+blur).
- `contain_blur` só com justificativa estruturada de inviabilidade de crop;
  rejeitar peça se a maioria das cenas for Stories sem exceção válida.
- Objetivo: cover na **maior parte** do tempo útil, inclusive miolo — sem
  regressão para blur-only como no v8.

### R2 — Energia **percebida** no render

- Manter Q2; acrescentar pressão para KB contínuo no cover (exemplo + limiar
  se necessário).
- Opcional (só com OK): amostragem leve pós-render (A5b parcial) contra
  trechos longos quase estáticos — senão reforçar declaração + helper obrigatório
  por cena (`makePhotoSceneMotion` instanciado).

### R3 — Logo sem placa **hard**

- Validar HTML do fecho: `img[src="assets/logo.png"]` sem ancestral/pseudo com
  fundo creme/card; ou rejeitar plano/implementação que declare placa.
- CTA contraste; movimento até `end`.

### R4 — Mix

- Subir presença da trilha alguns dB; sem mudar tarifa/credencial Music sem OK.

### Fora desta onda

- Troca de renderer / Remotion / TTS / avatar.
- Reescrever snapshots históricos.
- Aceite E2E sem novo MP4.

## Prompt sugerido para o próximo chat

```
Leia AGENTS.md, o topo de docs/PROJECT.md, docs/SDD.md,
docs/phases/BL04-context-and-ai-production.md e
docs/design/motion-ensaio-cafe-aurora-v8-gaps-2026-11-18.md
(contexto Q1–Q3 em motion-ensaio-cafe-aurora-v7-gaps-2026-11-18.md).

Implemente a próxima fatia (R1–R3; R4 mix se couber sem mudar Music).
PRIORIDADE: enforcement hard — prompts soft falharam no v8.

1) R1: cover 9:16 obrigatório na maior parte das cenas (campo de layout no
   plano e/ou validação HTML). contain+blur só exceção estruturada rara.
   Rejeitar default Stories janela+blur.
2) R2: energia contínua no miolo (helpers por cena + manter/endurecer Q2;
   A5b só se eu autorizar explicitamente)
3) R3: logo PNG overlay sem placa/card — validar HTML ou rejeitar placa;
   CTA legível; movimento até end

Preservar: crop v5, gates M3/N2/O2/Q2, snapshots históricos, vídeo, Music
(salvo R4). Sem TTS/avatar/renderer novo.

Evidência: versao-1 (8).mp4 — regressão vs v7 (Stories o tempo todo, ~89%
estático, holds ~4s, placa creme). Estimativa ~35–40% vs propaganda incrível.

Testes + PROJECT/SDD/BL04/CHANGELOG/DECISIONS na mesma mudança.
Não declare aceite E2E sem novo MP4 e minha revisão. Não rode chamada paga
sem eu autorizar.
```

## Aceite da próxima fatia

- Novo MP4: cover 9:16 dominante (não Stories blur o tempo todo).
- Miolo com movimento perceptível; holds longos sem energia evitados.
- Logo sem placa creme; CTA legível.
- Mix melhor se R4 incluído.
- Sem upgrade silencioso de snapshots antigos.
