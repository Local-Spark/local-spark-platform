# Ensaio Café Aurora v7 — gaps e próxima fatia — 18/11/2026

## Atualização — Q1–Q3 implementados; aceite audiovisual pendente

Autorização posterior do titular: intent/regras v8, skill photo v19 e repertório
v11. Cover por cena e exceção rara documentada; energia declarada com lacunas
≤500 ms e cobertura ≥80% por cena; helper de cena contínua e wrapper de marca
transparente. Q1/Q3 seguem instruções/exemplos, sem gate DOM/pixels. Crop v5,
M3/N2/O2 e snapshots históricos preservados. Q4 adiado; Music/mix intactos.
273 unitários, 21 Node e três integrações passaram; recorte de cobertura 100%.
CI integral bloqueado por lint preexistente. Detalhes em PROJECT/SDD/BL04/
CHANGELOG/DECISIONS. Sem chamada paga, A5b, novo MP4 ou aceite E2E.

## Diagnóstico original

Estado: **diagnóstico e backlog documentados** a partir de
`/Users/israelsilva/Downloads/versao-1 (7).mp4`. Não autoriza, por si,
implementação, chamada paga, A5b nem alteração de Music/renderer. Destinado a
um próximo chat/modelo.

Referências: O1–O3 em
[motion-ensaio-cafe-aurora-v6-gaps-2026-11-18.md](motion-ensaio-cafe-aurora-v6-gaps-2026-11-18.md);
N1–N3 em
[motion-ensaio-cafe-aurora-v5-gaps-2026-11-18.md](motion-ensaio-cafe-aurora-v5-gaps-2026-11-18.md);
Maestros [WuzMxEKJHkQ](../evals/analise-video-maestros-WuzMxEKJHkQ-2026-11-11.md).

## Evidência do ensaio v7

Arquivo: 15,0 s · 720×1280 · H.264 + AAC · ~1,64 Mbps (~3,1 MB).
Loudness ~**−31,6 LUFS** (inalterado).

Amostragem a 5 fps (cinza 90×160):

| Medida | v6 | **v7** |
| --- | --- | --- |
| Quase estático (diff &lt; 2) | ~88% | **~80%** |
| Diff médio | ~2,8 | **~5,4** |
| Holds ≥0,8 s | ~3,0 / 2,8 / 3,2 / 3,2 s | **~2,2 / 2,8 / 3,0 / 2,8 s** |
| Picos | ~3,8 / 7,4 / 11,4 s | **~3,6–3,8 / 7,4–7,8 / 11,6–12 s** |

Leitura humana (titular): **parece melhor**. Ainda abaixo do nível máximo /
propaganda de referência.

### Storyboard observado

1. **~0–3 s** — **cover 9:16** do balcão (pilhas de copos); overlay “Entre uma
   coisa e outra.”; scrim inferior.
2. **~4–7 s** — **regressão Stories**: janela landscape (latte + croissant) +
   barras blur; “cabe uma pausa.”
3. **~8–11 s** — outra janela+blur (flat-lay xícara vermelha); “Com sabor de
   começo.”
4. **~12–15 s** — díptico + **placa creme** AURORA + CTA “Conheça nosso
   cardápio”.

### Evolução vs gaps

| Melhorou | Ainda falha |
| --- | --- |
| Energia ~2× vs v6 (mean ~5,4; ~80% estático) | Miolo **ainda** contain+blur (O1 incompleto) |
| Holds sem trecho de 6+ s | Energia em **pulsos** nas trocas; meios ~0,6–0,9 |
| Cover no gancho | Logo em **placa creme** (O3 incompleto) |
| CTA presente no fecho | Mix −31,6 LUFS; tipografia pouco cinética |
| | Abertura cover é interior genérico, não sempre “produto herói” |

Diagnóstico: O2 (magnitude) **fez efeito perceptível** no métrico. O1/O3
continuam soft na prática: o modelo cobre o gancho e volta ao Stories no miolo;
a marca no fecho segue em card creme apesar do exemplo overlay.

## Backlog priorizado (próxima implementação)

### Q1 — Cover no miolo (fechar O1 de verdade)

- Exigir cover 9:16 em **cada** cena fotográfica, ou exceção de crop **rara** e
  auditável (não como estilo default do miolo).
- Se houver campo/declaração de layout no plano: validar ausência de
  “janela+blur” sem justificativa por cena; senão reforçar skill/exemplo +
  instrução que **proíba** regressão após abertura cover na mesma peça.
- Preferir materiais que permitam cover do protagonista (produto/ambiente
  enquadrável), em vez de cair em contain por conveniência.

### Q2 — Energia contínua no miolo (além de pulsos)

- Exemplo/plano: KB contínuo **visível** durante a leitura, não só nas trocas.
- Considerar endurecer ainda o limiar O2 **ou** exigir cobertura energética
  mais densa no miolo (sem A5b de pixels salvo OK).
- Tipografia com entrada/saída temporal clara sobre cover.

### Q3 — Logo PNG sem placa (fechar O3)

- Gate ou orientação dura: marca = `<img src="assets/logo.png">` overlay;
  rejeitar / desencorajar wrapper com fundo creme/card/placa.
- CTA com contraste; movimento até `end`.

### Q4 — Mix

- Subir presença da trilha alguns dB; sem mudar tarifa/credencial Music sem OK.

### Fora desta onda

- A5b pixel completo (só se Q1–Q3 falharem de novo).
- TTS/Voice, avatar, troca de renderer.
- Auto-injeção cega de helpers.
- Reescrever snapshots históricos.

## Prompt sugerido para o próximo chat

```
Leia AGENTS.md, o topo de docs/PROJECT.md, docs/SDD.md,
docs/phases/BL04-context-and-ai-production.md e
docs/design/motion-ensaio-cafe-aurora-v7-gaps-2026-11-18.md
(contexto O1–O3 em motion-ensaio-cafe-aurora-v6-gaps-2026-11-18.md).

Implemente a próxima fatia (Q1–Q3 do doc v7; Q4 mix se couber sem mudar Music):
1) Cover 9:16 em TODAS as cenas fotográficas; contain+blur só exceção rara e
   justificada por cena — sem regressão Stories no miolo
2) Energia contínua no miolo (KB/overlays visíveis entre trocas); pode
   endurecer limiar O2 se necessário (sem A5b de pixels sem meu OK)
3) Fecho: logo PNG overlay sem placa/card creme; CTA legível; movimento até end

Preservar: crop v5, gates M3/N2/O2, snapshots históricos, vídeo, Music (salvo
Q4). Sem TTS/avatar/renderer novo.

Evidência: versao-1 (7).mp4 — melhorou (energia ~2× vs v6, cover no gancho)
mas miolo volta blur, logo em placa creme, mix −31,6 LUFS.

Testes + PROJECT/SDD/BL04/CHANGELOG/DECISIONS na mesma mudança.
Não declare aceite E2E sem novo MP4 e minha revisão. Não rode chamada paga
sem eu autorizar.
```

## Aceite da próxima fatia

- Novo MP4: cover 9:16 na maior parte do tempo, inclusive miolo.
- Meios com movimento perceptível, não só picos nas trocas.
- Logo no fecho sem placa creme; CTA legível.
- Mix melhor se Q4 incluído.
- Sem upgrade silencioso de snapshots antigos.
