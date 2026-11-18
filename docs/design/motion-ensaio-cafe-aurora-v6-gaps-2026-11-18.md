# Ensaio Café Aurora v6 — gaps e próxima fatia — 18/11/2026


## Atualização — O1–O3 implementados; aceite audiovisual pendente

Autorização posterior do titular: intent/regras v7, skill photo v18 e repertório
v10. Cover por cena, energia com velocidade e amplitude mínimas, logo overlay
e CTA até end. Crop v5, M3 e replay v6 preservados. O4 adiado; sem chamada paga,
A5b ou novo MP4. Validação e limites em PROJECT/SDD/BL04/CHANGELOG/DECISIONS.
O diagnóstico abaixo permanece a evidência anterior; aceite exige novo ensaio
autorizado e revisão do titular.

## Diagnóstico original

Estado: **diagnóstico e backlog documentados** a partir de
`/Users/israelsilva/Downloads/versao-1 (6).mp4`. Não autoriza, por si,
implementação, chamada paga, A5b nem alteração de Music/renderer. Destinado a
um próximo chat/modelo.

Referências: N1–N3 em
[motion-ensaio-cafe-aurora-v5-gaps-2026-11-18.md](motion-ensaio-cafe-aurora-v5-gaps-2026-11-18.md);
crop/M1–M3 em
[motion-ensaio-cafe-aurora-v4-gaps-2026-11-17.md](motion-ensaio-cafe-aurora-v4-gaps-2026-11-17.md);
Maestros [WuzMxEKJHkQ](../evals/analise-video-maestros-WuzMxEKJHkQ-2026-11-11.md).

## Evidência do ensaio v6

Arquivo: 15,0 s · 720×1280 · H.264 + AAC · ~1,16 Mbps (~2,2 MB).
Loudness ~**−31,6 LUFS** (inalterado).

Amostragem a 5 fps (cinza 90×160):

| Medida | v5 | **v6** |
| --- | --- | --- |
| Quase estático (diff &lt; 2) | ~89% | **~88%** |
| Diff médio | ~2,4 | **~2,8** |
| Holds ≥0,8 s | ~3,0 / **6,6** / 3,0 s | **~3,0 / 2,8 / 3,2 / 3,2 s** |
| Picos | ~4 s e ~11 s | **~3,8 / 7,4 / 11,4 s** (trocas) |

Leitura humana (titular): **melhorou**; ainda abaixo do nível máximo / propaganda.

### Storyboard observado

1. **~0–3,5 s** — **cover 9:16** da xícara vermelha (gancho imersivo); tipografia
   overlay “O dia pede…”; protagonista majoritariamente preservado.
2. **~4–7 s** — **regressão Stories**: janela landscape + barras blur; “uma pausa.”
3. **~8–11 s** — cover do latte; “No seu tempo.”
4. **~12–15 s** — fecho: foto full-ish + **logo em placa creme** AURORA + CTA
   “Conheça nosso cardápio” (contraste fraco em trechos).

### Evolução vs gaps

| Melhorou | Ainda falha |
| --- | --- |
| Abertura **cover real** (N1 parcial) | Miolo **volta** contain+blur |
| Holds longos de 6,6 s sumiram da amostragem | Energia entre trocas ainda ~0 (N2 no plano ≠ percepção) |
| Ritmo com mais cortes (~3 atos + fecho) | Logo ainda em **card creme** (N3 incompleto) |
| Fora do cartaz tipográfico puro | Mix −31,6 LUFS; tipografia pouco cinética |

Diagnóstico: N1/N2/N3 **moveram** a peça (cover no gancho; sem hold de 6+ s
óbvio), mas o modelo ainda **mistura** cover e Stories, declara energia mínima
que o olho lê como quase estático, e traz a placa creme no fecho.

## Backlog priorizado (próxima implementação)

### O1 — Cover contínuo (fechar N1)

- Preferência dura: **todas** as cenas fotográficas em cover 9:16 com foco
  protegido, salvo exceção de crop **por cena** com justificativa explícita.
- Proibir regressão “janela + blur” no miolo quando a abertura já usou cover
  viável na mesma peça / mesmo material (orientação + validação de plano se
  houver campo de layout; senão skill/exemplo + rejeição de padrão Stories).
- Não tratar contain+blur como estilo alternativo livre.

### O2 — Energia perceptível (além do limiar N2)

- Subir o que conta como energético **ou** exigir magnitude maior no miolo
  (ex.: scale/pan mais agressivos no exemplo e no gate), sem A5b de pixels
  salvo OK do titular.
- KB contínuo visível no cover; overlays tipográficos com entrada/saída clara.
- Evitar “transform canônico mínimo” que passa N2 e congela o quadro.

### O3 — Fecho: logo PNG sem placa

- Logo como overlay/`<img>` sobre foto (scrim local ok); **sem** retângulo creme
  / card editorial.
- CTA legível (contraste); micro-movimento até `end`.
- Se necessário: gate/orientação que rejeite “placa” como container da marca.

### O4 — Mix (N4)

- Subir presença da trilha alguns dB; sem mudar tarifa/credencial Music sem OK.

### Fora desta onda

- A5b pixel completo (só se O1–O3 ainda falharem no próximo ensaio).
- TTS/Voice, avatar, troca de renderer.
- Auto-injeção cega de helpers.
- Reescrever snapshots históricos.

## Prompt sugerido para o próximo chat

```
Leia AGENTS.md, o topo de docs/PROJECT.md, docs/SDD.md,
docs/phases/BL04-context-and-ai-production.md e
docs/design/motion-ensaio-cafe-aurora-v6-gaps-2026-11-18.md
(contexto N1–N3 em motion-ensaio-cafe-aurora-v5-gaps-2026-11-18.md).

Implemente a próxima fatia (O1–O3 do doc v6; O4 mix se couber sem mudar Music):
1) Cover 9:16 contínuo nas cenas fotográficas; contain+blur só exceção por
   cena com inviabilidade de crop — sem regressão Stories no miolo
2) Energia perceptível no miolo: reforçar exemplo/gate (magnitude) além do
   limiar mínimo atual; KB/overlays visíveis (sem A5b de pixels sem meu OK)
3) Fecho: logo PNG overlay sem placa creme; CTA legível; movimento até end

Preservar: crop v5, gates M3/N2 existentes (pode endurecer limiares), snapshots
históricos, vídeo, Music (salvo O4). Sem TTS/avatar/renderer novo.

Evidência: versao-1 (6).mp4 — melhorou (cover na abertura) mas miolo volta
blur, ~88% estático entre trocas, logo em card creme, mix −31,6 LUFS.

Testes + PROJECT/SDD/BL04/CHANGELOG/DECISIONS na mesma mudança.
Não declare aceite E2E sem novo MP4 e minha revisão. Não rode chamada paga
sem eu autorizar.
```

## Aceite da próxima fatia

- Novo MP4: cover 9:16 na maior parte do tempo, sem janela+blur no miolo salvo
  exceção justificada e rara.
- Miolo com movimento **visível** entre trocas (não só declaração N2).
- Logo no fecho sem placa creme; CTA legível.
- Mix melhor se O4 incluído.
- Protagonista preservado quando cover for usado.
- Sem upgrade silencioso de snapshots antigos.
