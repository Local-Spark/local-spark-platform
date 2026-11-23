# Ensaio Café Aurora v11 — gaps e próxima fatia — 23/11/2026

## Correção posterior — timing v5

O run `8d3e45a9…` com v4 revelou uma transição fora do overlap e um wrapper
de texto oculto no endpoint. Polish-v5 acrescenta admissão de handoff e helper
versionado de visibilidade inclusiva para texto. A cópia corrigida passou em
451 seeks locais; detalhes e testes em PROJECT/SDD/BL04/DECISIONS/CHANGELOG.
Run original preservado; sem novo MP4 ou aceite E2E.

## Atualização — U1–U3 implementados, aceite audiovisual pendente

Autorização posterior: polish-v4/guarda photo-polish-v3.js implementam
legibilidade sem radial/glow, continuidade primária no plano/DOM e orientação
de variedade/ambiente. Detalhes, decisões e validação em PROJECT/SDD/BL04,
DECISIONS e CHANGELOG. Polish v1–v3/replay, crop e gates anteriores preservados.
U4 não autorizado. Sem chamada paga, MP4 novo ou aceite E2E. O diagnóstico
original abaixo permanece como histórico e critério para a revisão futura.

Estado: **diagnóstico e backlog documentados** a partir de
`/Users/israelsilva/Downloads/versao-1 (10).mp4`
(hash `053e43701753b367f42fbdd09377dc9795a522ad9b8f05c99692718bd6ec68a7`).
Não autoriza, por si, implementação, chamada paga, A5b nem alteração de
Music/renderer. Destinado a um próximo chat/modelo.

Referências: T1–T4 / ensaio recuperado em
[motion-ensaio-cafe-aurora-v10-gaps-2026-11-18.md](motion-ensaio-cafe-aurora-v10-gaps-2026-11-18.md);
S1–S3 em
[motion-ensaio-cafe-aurora-v9-gaps-2026-11-18.md](motion-ensaio-cafe-aurora-v9-gaps-2026-11-18.md);
Maestros [WuzMxEKJHkQ](../evals/analise-video-maestros-WuzMxEKJHkQ-2026-11-11.md).

## Contexto imediato

- Briefing do titular (inalterado): *“Quero um reel mostrando o clima do Café
  Aurora. Uma coisa aconchegante, com movimento suave e frases curtinhas sobre
  fazer uma pausa no dia. Pode usar nossas fotos.”*
- Comparação principal: MP4 recuperado `cefe9071`
  (`Cafe-Aurora-render-recuperado-cefe9071.mp4`, hash `8cba7ed7…`) — melhor
  peça soft da série (~60–65% vs propaganda; ~70–75% vs briefing).
- Desde o v10: T1–T3 (`polish-v1`), correção inventário `photo-music`, orientação
  energética `polish-v2`, e `polish-v3` (scrim irmão + restrição de máscara no
  fecho). Gates passaram a admitir scrim `<texto>-scrim` e sombra preta opaca.
- Titular: peça **fraca e pior** que o anterior; tipografia com sombra preta
  estranha. Análise confirma **regressão audiovisual**.

## Evidência do ensaio v11

Arquivo: 15,0 s · 720×1280 · H.264 + AAC · ~1,16 Mbps (~2,2 MB).
Loudness ~**−31,5 LUFS** (inalterado).

Amostragem a 5 fps (cinza 90×160), mesmo critério dos ensaios anteriores:

| Medida | v10 (`cefe9071`) | **v11 (`versao-1 (10)`)** |
| --- | --- | --- |
| Quase estático (diff &lt; 2) | **0%** | **~70%** |
| Diff médio | ~5,3 | **~4,0** |
| Holds ≥0,8 s | nenhum | **~2,2 / 2,4 / 2,2 / 2,4 s** |
| Picos (cortes) | ~3,6–3,8 / 7,2–7,4 / 11,6–11,8 s | **~5,6–5,8 / 11,0–11,2 s** |

Leitura humana: cover ainda presente; frases “No meio do dia…” / “uma pausa.” /
“Um café.” / “Um tempo seu.”; fecho logo AURORA + “Conheça nosso cardápio”.
**Scrim radial preto** atrás do texto (mancha/oval) e **glow/sombra preta
grossa** nas letras — passam T2/`polish-v3`, falham visualmente. Loop de
produto (espresso vermelho ↔ latte) continua. Estimativa vs propaganda
“incrível”: **~50–55%** (v10 ~60–65%). Vs briefing soft: **~55–60%** (v10
~70–75%).

### Storyboard observado

1. **~0–5 s** — espresso top-down; “No meio do dia…” com blob/scrim escuro.
2. **~5–6 s** — corte; “uma pausa.” com sombra preta marcada.
3. **~6–11 s** — latte; “Um café.” / “Um tempo seu.” + sombra/glow.
4. **~11–15 s** — espresso + logo + CTA; sombra no CTA ainda pesada.

### Evolução vs gaps

| Melhorou / estável | Regrediu / falhou |
| --- | --- |
| Gates T2/T3 “cumpridos” (sem cantoneiras) | Energia: 0% → **~70%** estático |
| Cover (não voltou Stories longo) | Legibilidade virou **blob/glow** antiestético |
| Logo transparente / sem disclaimer | Tipografia inconsistente (serif vs sans + sombras) |
| Mix inalterado | Variedade/clima ainda fracos (~2 closes) |
| | Acabamento pior que `cefe9071` no julgamento do titular |

Diagnóstico: os suplementos de **admissão** (sombra opaca + scrim irmão radial)
empurraram o modelo para soluções que **satisfazem o DOM** e **pioram a peça**.
O2/Q2/`polish-v2` não impediram holds longos neste render. Próxima fatia precisa
de **legibilidade estética** (sem relaxar contraste mínimo) e **energia
contínua de volta**, sem hard-sell e sem reabrir Music.

Estas melhorias são do **gerador photo** (novas capturas), não um template fixo
do Café Aurora nem deste briefing.

## % vs referências

| Dimensão | v10 | **v11** |
| --- | --- | --- |
| Foto / mood | 75–80 | 70–75 |
| Cover 9:16 | 75–80 | 70–75 |
| Motion / energia | 55–60 | **25–35** |
| Marca / fecho | 70–75 | 65–70 |
| Mix | 20 | 20 |
| Tipografia / contraste estético | 40–45 | **25–35** |
| Variedade / clima | 40–45 | 40–45 |
| **Síntese vs propaganda** | **~60–65** | **~50–55** |
| **Vs briefing soft** | **~70–75** | **~55–60** |

## Backlog priorizado (próxima implementação — U1–U4)

### U1 — Legibilidade **sem blob** (prioridade máxima)

- Manter exigência de texto claro legível (T2/readability), mas **rejeitar**
  soluções que parecem mancha/glow de admissão:
  - scrim irmão com mancha radial grande ou alpha alto demais cobrindo área
    desproporcional ao texto;
  - `text-shadow` com blur excessivo / glow “auréola” (definir teto numérico
    conservador no DOM, ex.: blur máximo baixo e offsets pequenos, já
    parcialmente limitados — endurecer o que o ensaio mostrou como feio).
- Preferir, nesta ordem: (1) texto sobre região já escura da foto; (2) scrim
  **local suave** (retângulo/gradiente contido, alpha moderado, sem “poça”
  radial óbvia); (3) sombra preta **discreta** (opaca ok, sem glow largo).
- Não relaxar CTA ≥1500 ms, finish-v1 (texto visível o beat inteiro) nem
  proibição de faixa full-width.
- Versionar suplemento (ex. polish-v4) sem editar bytes de v1–v3/replay.

### U2 — Energia contínua de volta

- O ensaio v11 regrediu aos holds ~2 s apesar de O2/Q2/`polish-v2`.
- Reforçar orientação **e**, se necessário, pressão de plano/DOM já existente
  (sem A5b sem OK): KB/transforms elegíveis cobrindo o miolo; evitar agenda que
  só “acorda” nos cortes.
- Preservar tom suave do briefing: energia contínua ≠ hard-sell.

### U3 — Variedade / clima (ainda aberto do T1)

- Continuar exigindo diversidade/ambiente quando elegível; o render ainda
  parece loop de dois closes.
- Não inventar fotos; não relaxar S3/crop v5.

### U4 — Mix (opcional, só com OK)

- S4/T4 adiado: subir presença da trilha; sem mudar Music sem autorização.

### Fora desta onda

- Relaxar T2/finish até “sumir” a proteção (só refinar a forma).
- Trocar briefing por propaganda dura.
- Renderer / Remotion / TTS / avatar.
- Reescrever snapshots / hashes de v1–v3.
- Aceite E2E sem novo MP4 autorizado.
- A5b sem autorização explícita.

## Prompt sugerido para o próximo chat

```
Leia AGENTS.md, o topo de docs/PROJECT.md, docs/SDD.md,
docs/phases/BL04-context-and-ai-production.md e
docs/design/motion-ensaio-cafe-aurora-v11-gaps-2026-11-23.md
(contexto T1–T3/polish-v3 em motion-ensaio-cafe-aurora-v10-gaps e PROJECT).

Briefing do titular (preservar o tom; não hard-sell):
"Quero um reel mostrando o clima do Café Aurora. Uma coisa aconchegante,
com movimento suave e frases curtinhas sobre fazer uma pausa no dia.
Pode usar nossas fotos."

Implemente a próxima fatia (U1–U3; U4 mix só se eu autorizar).
PRIORIDADE: desfazer a regressão estética/energética do versao-1 (10)
sem relaxar contraste mínimo nem finish-v1.

1) U1: legibilidade sem blob — versionar polish (ex. v4); rejeitar scrim
   radial/mancha e glow preto largo; preferir região escura → scrim local
   suave → sombra discreta. Manter CTA ≥1500 ms, faixa full-width proibida,
   texto visível o beat inteiro (finish-v1). Replay v1–v3 intacto.
2) U2: energia contínua no miolo de volta (holds ~2 s do v11 são regressão
   vs cefe9071); reforçar O2/Q2/orientação sem A5b sem OK.
3) U3: variedade/ambiente quando elegível; sem inventar fotos; S3/crop v5.

Preservar: crop v5, gates M3/N2/O2/Q2/R1–R3/S1–S3/T1–T3, intent v10,
guardas v2/v3, finish-v1, readability-v1, polish v1–v3 bytes/replay,
Music (salvo U4). Sem TTS/avatar/renderer novo.

Evidência: versao-1 (10).mp4 pior que Cafe-Aurora-render-recuperado-cefe9071.mp4
(~50–55% vs propaganda; ~55–60% vs briefing). ~70% estático; scrim/glow feio
passando T2; tipografia inconsistente; loop de closes.

Testes + PROJECT/SDD/BL04/CHANGELOG/DECISIONS na mesma mudança.
Não declare aceite E2E sem novo MP4 autorizado e minha revisão.
Não rode chamada paga sem eu autorizar.
```

## Aceite da próxima fatia

- Novo MP4: texto legível **sem** mancha radial/glow óbvio; sombra discreta ou
  scrim contido.
- Energia perceptível no miolo (sem holds longos como no v11); cover mantido.
- Variedade/ambiente melhor se o inventário permitir.
- Mix melhor se U4 incluído.
- Sem upgrade silencioso de snapshots antigos; sem aceitar v11 como referência
  de qualidade (referência positiva continua `cefe9071`).
