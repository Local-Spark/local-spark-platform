# Ensaio Café Aurora v9 — gaps e próxima fatia — 18/11/2026

## Atualização — S1–S3 implementados, aceite audiovisual pendente

Autorização posterior: suplemento `motion-photo-finish-v1` em novas capturas,
sem alterar intent v10/guarda v2 ou snapshots históricos. Exceção contain+blur
limitada a 2000 ms; energia mínima por foto/logo até end; entrada/saída de texto
verificada no DOM; inspeção estruturada de identidade para fotos selecionadas
com logo do kit. Detalhes, limites e validação em PROJECT/SDD/BL04/DECISIONS.
S4 não autorizado/incluído. Sem chamada paga ou novo MP4 nesta mudança.
O diagnóstico original abaixo permanece como evidência histórica.

Estado: **diagnóstico e backlog documentados** a partir de
`/Users/israelsilva/Downloads/versao-1 (9).mp4`. Não autoriza, por si,
implementação, chamada paga, A5b nem alteração de Music/renderer. Destinado a
um próximo chat/modelo.

Referências: R1–R3 e guarda v2 em
[motion-ensaio-cafe-aurora-v8-gaps-2026-11-18.md](motion-ensaio-cafe-aurora-v8-gaps-2026-11-18.md);
Q1–Q3 em
[motion-ensaio-cafe-aurora-v7-gaps-2026-11-18.md](motion-ensaio-cafe-aurora-v7-gaps-2026-11-18.md);
Maestros [WuzMxEKJHkQ](../evals/analise-video-maestros-WuzMxEKJHkQ-2026-11-11.md).

## Contexto imediato (já validado noutro chat)

- Pedido anterior falhou com `MOTION_RENDER_EXECUTION_FAILED` por **falso
  positivo da guarda v1** (opacity na dissolve aprovada; CTA antes da entrada;
  inset zero como máscara). Corrigido em intent **v10** / guarda DOM **v2**.
- Logo transparente sintética Aurora cadastrada; R3 (sem placa creme) **passou**
  neste ensaio.
- Esta peça é a **nova captura** pós-worker reload; não é replay do pedido
  falho. Aceite audiovisual do titular: evolução perceptível, ainda longe das
  refs “incríveis”.

## Evidência do ensaio v9

Arquivo: 15,0 s · 720×1280 · H.264 + AAC · ~1,81 Mbps (~3,4 MB).
Loudness ~**−31,5 LUFS** (inalterado vs v7/v8).

Amostragem a 5 fps (cinza 90×160), mesmo critério dos ensaios anteriores:

| Medida | v8 | **v9** |
| --- | --- | --- |
| Quase estático (diff &lt; 2) | ~89% | **~38%** |
| Diff médio | ~3,6 | **~4,4** |
| Holds ≥0,8 s | ~4,4 / 4,4 / 3,8 s | **~2,2 / 2,8 s** |
| Picos (cortes/dissolve) | ~5,2 e ~10–11 s | **~3,6–3,8 / 7,6 / 11,2–11,4 s** |

Leitura humana / frames-chave: gancho e 3º beat em **cover**; miolo ainda
**Stories** (janela + blur + faixa escura de texto); fecho com **logo
transparente** + CTA sobre foto (sem placa creme). Estimativa vs propaganda
“incrível” das refs (~40 vídeos / Maestros): **~55%** (era ~35–40% no v8).

### Storyboard observado

1. **~0–3,5 s** — interior café em cover; “O dia pede” (com acentos gráficos).
2. **~4–7,5 s** — **Stories** latte/croissant (janela + blur + bloco escuro);
   “Uma pausa / com sabor de começo”.
3. **~8–11 s** — cover/profundidade de campo nos copos; “No seu tempo.”
4. **~11–15 s** — dissolve → logo AURORA overlay + “Conheça nosso cardápio” +
   “Imagens ilustrativas.”; trecho final **quase parado** (~12–15 s 100%
   estático na amostragem).

### Evolução vs gaps

| Melhorou | Ainda falha / incompleto |
| --- | --- |
| Energia métrica (38% estático vs 89%) | Miolo **ainda** contain+blur (R1 incompleto) |
| Cover no gancho e no 3º beat | Fecho ~3 s sem Ken Burns (R2/M3 no render) |
| Logo sem placa creme (R3) | Mix −31,5 LUFS (R4) |
| Holds mais curtos no miolo | Tipografia ainda pousa e fica |
| Guarda v2 deixou dissolve passar | Identidade no material: Belize Coffee, Mackbear, Red Bull, watermark vs Aurora |
| | Disclaimer “Imagens ilustrativas.” enfraquece propaganda |

Diagnóstico: R1/R2 **parcialmente** cumpridos (cover ≠ dominante no tempo útil;
energia some no fecho). R3 **ok** neste MP4. Próxima fatia precisa fechar cover
no miolo, movimento até `end`, e **materiais sem marca concorrente** — não só
mais adjetivos no prompt.

## % vs propaganda incrível (critério de referência)

| Dimensão | ~% |
| --- | --- |
| Foto / mood | 75 |
| Composição cover 9:16 | 55–60 |
| Motion / energia contínua | 45–50 |
| Marca / fecho | 65–70 |
| Mix | 20 |
| Tipografia cinética | 35–40 |
| **Síntese ponderada** | **~55** |

Evolução desde o silêncio estático inicial: grande. Distância até o alvo das
refs: ainda cerca da metade do caminho.

## Backlog priorizado (próxima implementação — S1–S4)

### S1 — Cover no **miolo** (prioridade máxima)

- R1 exige cover ≥2/3 do tempo; o ensaio ainda gasta um beat longo em Stories.
- Endurecer: `contain_blur` no miolo só se staging provar inviabilidade de crop
  **e** a cena for a única exceção; rejeitar faixa escura full-width como
  suporte de texto quando a foto poderia ser cover + scrim local.
- Objetivo: **nenhum** beat central em janela+blur por default; Stories no máximo
  uma exceção curta, se houver.

### S2 — Energia no **fecho** até `end`

- Fecho ~12–15 s ficou quase estático apesar de M3/closing_motion.
- Garantir Ken Burns (ou motion declarado) em foto(s)/logo do fecho **até**
  `duration_ms`, com a guarda v2 a confirmar estados distintos — sem relaxar
  CTA ≥1500 ms de leitura.
- Tipografia: pelo menos uma entrada/saída com ritmo (não só hold estático);
  sem trocar renderer.

### S3 — Identidade dos materiais (marca do cliente)

- Fotos com Belize Coffee, Mackbear, watermark diagonal e Red Bull competem com
  Aurora no quadro.
- Preferir / filtrar em staging ou seleção de asset: rejeitar ou despriorizar
  materiais com logo/watermark de **terceiros** legível no frame quando o kit
  tem marca própria; ou exigir crop/cover que oculte a marca alheia quando
  possível.
- Evitar disclaimer “Imagens ilustrativas.” no CTA a menos que o titular peça
  (parece stock, não ad).
- Não inventar fotos novas por IA nesta fatia; trabalhar com seleção/gates.

### S4 — Mix (opcional, só com OK)

- Subir presença da trilha alguns dB; sem mudar tarifa/credencial Music sem OK.

### Fora desta onda

- Troca de renderer / Remotion / TTS / avatar.
- Reescrever snapshots históricos / intent v9–v10 bytes.
- Aceite E2E sem novo MP4.
- A5b sem autorização explícita.

## Prompt sugerido para o próximo chat

```
Leia AGENTS.md, o topo de docs/PROJECT.md, docs/SDD.md,
docs/phases/BL04-context-and-ai-production.md e
docs/design/motion-ensaio-cafe-aurora-v9-gaps-2026-11-18.md
(contexto R1–R3/guarda v2 em motion-ensaio-cafe-aurora-v8-gaps-2026-11-18.md).

Implemente a próxima fatia (S1–S3; S4 mix só se eu autorizar).
PRIORIDADE: fechar o que R1–R2 deixaram passar no ensaio v9.

1) S1: cover 9:16 no miolo — contain+blur/Stories não pode ser beat central
   longo; manter regra ≥2/3 cover e no máx. 1 exceção estruturada. Preferir
   scrim local sobre foto cover em vez de faixa escura full-width + janela.
2) S2: energia no fecho até end (foto/logo com estados distintos; tipografia
   com pelo menos uma animação de entrada/saída). Preservar CTA ≥1500 ms e
   guarda v2 / intent v10 (não reverter dissolve/CTA timing).
3) S3: staging/seleção — despriorizar ou rejeitar assets com marca/watermark
   de terceiros legível (Belize, Mackbear, etc.) quando há logo do kit;
   não forçar “Imagens ilustrativas.” no CTA.

Preservar: crop v5, gates M3/N2/O2/Q2/R1–R3, intent v10, guarda v2, snapshots
históricos, vídeo, Music (salvo S4). Sem TTS/avatar/renderer novo.

Evidência: versao-1 (9).mp4 — evolução vs v8 (~55% vs ~35–40% propaganda
incrível); miolo Stories, fecho estático ~3s, identidade contaminada, mix
−31,5 LUFS.

Testes + PROJECT/SDD/BL04/CHANGELOG/DECISIONS na mesma mudança.
Não declare aceite E2E sem novo MP4 e minha revisão. Não rode chamada paga
sem eu autorizar.
```

## Aceite da próxima fatia

- Novo MP4: miolo em cover (Stories só se exceção curta e justificada).
- Fecho com movimento perceptível até o último segundo; CTA legível ≥1,5 s.
- Sem placa creme; logo overlay intacta.
- Marcas/watermarks de terceiros não dominam o quadro (ou ficam fora do crop).
- Mix melhor se S4 incluído.
- Sem upgrade silencioso de snapshots antigos.
