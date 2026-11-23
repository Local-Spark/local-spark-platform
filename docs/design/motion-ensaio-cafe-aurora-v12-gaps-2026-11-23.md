# Ensaio Café Aurora v12 — gaps e última rodada — 23/11/2026

## Congelamento — ver v13

Aceite de `versao-1 (12).mp4` e decisão de **congelar** o photo-reel do Café
(sem V2; próximo = Reel vídeo do cliente) em
[motion-ensaio-cafe-aurora-v13-freeze-2026-11-23.md](motion-ensaio-cafe-aurora-v13-freeze-2026-11-23.md).

## Atualização — V1 implementada; aceite audiovisual pendente

Autorização posterior do titular implementou polish-v6 para novas capturas:
cover obrigatório em toda cena, sem exceção Stories; transforms primários
N2 sem lacunas até o fim ou a dissolução de saída validada, com continuidade
nos encontros. Guarda DOM nova, pinada, sem alterar arquivos históricos.
Detalhes e validação em PROJECT/SDD/BL04/CHANGELOG/DECISIONS. O estado de
diagnóstico abaixo permanece como histórico, não limita esta autorização.

Sem chamadas pagas ou novo MP4. Comparação ≥ cefe e aceite E2E continuam
pendentes da autorização de geração e revisão do titular. V2 somente se
pedido explicitamente; nenhuma nova rodada automática ou U4.


Estado: **diagnóstico e backlog documentados** a partir de
`/Users/israelsilva/Downloads/versao-1 (11).mp4`
(hash `456928a676f5a0df397295989fc815aad8281b81cd67962e9894cffa105427d8`).
Não autoriza, por si, implementação, chamada paga, A5b nem alteração de
Music/renderer. Destinado a um próximo chat/modelo.

Referências: U1–U4 / polish-v4–v5 em
[motion-ensaio-cafe-aurora-v11-gaps-2026-11-23.md](motion-ensaio-cafe-aurora-v11-gaps-2026-11-23.md);
T1–T4 / `cefe9071` em
[motion-ensaio-cafe-aurora-v10-gaps-2026-11-18.md](motion-ensaio-cafe-aurora-v10-gaps-2026-11-18.md);
S1–S3 em
[motion-ensaio-cafe-aurora-v9-gaps-2026-11-18.md](motion-ensaio-cafe-aurora-v9-gaps-2026-11-18.md).

## Contexto imediato

- Briefing do titular (inalterado): *“Quero um reel mostrando o clima do Café
  Aurora. Uma coisa aconchegante, com movimento suave e frases curtinhas sobre
  fazer uma pausa no dia. Pode usar nossas fotos.”*
- Cliente real escreverá pedidos leigos; o gerador deve viesar para
  **conversão** (cover, ritmo suave contínuo, legibilidade, CTA no fecho)
  **sem** desrespeitar o pedido soft. Não reescrever este briefing agora só
  para “testar propaganda”.
- Pós polish-v4 (U1–U3) + polish-v5 (handoff/timing): o render **fechou**
  (15 s / 450 frames). Falha restante é **audiovisual**, não timing de guarda.
- Referência positiva continua `cefe9071`
  (`Cafe-Aurora-render-recuperado-cefe9071.mp4`, hash `8cba7ed7…`).
- Titular: quase 1 semana de rodadas; **no máximo 1 rodada** (opcional 2º
  ajuste estreito se falhar). Depois congela Café e abre outros
  conteúdos/negócios. Go ≠ 80% propaganda dura.

## Evidência do ensaio v12

Arquivo: 15,0 s · 720×1280 · H.264 + AAC · ~1,16 Mbps (~2,18 MB).
Loudness ~**−31,5 LUFS** (inalterado).

Amostragem a 5 fps (cinza 90×160), mesmo pipeline relativo v10/v11/v12:

| Medida | v10 (`cefe9071`) | v11 (`versao-1 (10)`) | **v12 (`versao-1 (11)`)** |
| --- | --- | --- | --- |
| Quase estático (diff &lt; 2) | ~54%* | ~88% | **~84%** |
| Diff médio | ~4,8 | ~3,4 | **~3,7** |
| Holds ≥0,8 s | presentes | ~2,2–3,6 s | **~1,6 / 2,4 / 3,2 / 2,0 / 3,2 s** |
| Picos (cortes) | ~3,6 / 7,2 / 11,6 s | ~5,6 / 11,0 s | **~1,8 / 8,2 s** |

\*Valores absolutos do pipeline local desta rodada; a comparação **relativa**
v11→v12 e vs cefe é a que importa. Miolo 2–8 s e fecho 9–15 s quase parados.

Leitura humana / frames-chave:

1. **~0–1,5 s** — **Stories/letterbox**: janela horizontal (espresso+croissant)
   com blur em cima/baixo + “O dia pede…”. Regressão S1 vs cefe/v11 (cover).
2. **~2–8 s** — latte cover; “uma pausa.” / “Sem pressa.”; badge cinza retangular
   (sem blob/glow do v11); holds longos.
3. **~8–15 s** — espresso vermelho cover; logo AURORA + tagline; “A pausa é
   sua.” → CTA “Conheça nosso cardápio”.

### Evolução vs gaps

| Melhorou / estável | Regrediu / falhou |
| --- | --- |
| Render completo (polish-v5 timing ok) | **Cover:** gancho Stories (S1) |
| U1: sem mancha radial/glow do v11 | **Energia:** holds; U2 não perceptível |
| Copy alinhada a pausa | Variedade ainda loop de produto |
| Logo + CTA limpos | Mix −31,5 LUFS (fora desta rodada) |
| Tipografia legível (badge) | Badge cinza repetido = chip de UI |

Estimativa vs propaganda “incrível”: **~55–60%** (cefe ~60–65; v11 ~50–55).
Vs briefing soft: **~65–70%** (cefe ~70–75; v11 ~55–60). O briefing soft
limita o teto de propaganda; **não** explica sozinho o gap vs cefe — execução
(cover + energia) sim.

## % vs referências

| Dimensão | cefe | v11 | **v12** |
| --- | --- | --- | --- |
| Foto / mood | 75–80 | 70–75 | 70–75 |
| Cover 9:16 | 75–80 | 70–75 | **45–55** |
| Motion / energia | 55–60 | 25–35 | **30–40** |
| Marca / fecho | 70–75 | 65–70 | 70–75 |
| Mix | 20 | 20 | 20 |
| Tipografia / contraste estético | 40–45 | 25–35 | **50–55** |
| Variedade / clima | 40–45 | 40–45 | 45–50 |
| **Síntese vs propaganda** | **~60–65** | **~50–55** | **~55–60** |
| **Vs briefing soft** | **~70–75** | **~55–60** | **~65–70** |

## Backlog — última rodada (V1–V2)

### V1 — Cover full-bleed + energia suave (prioridade; escopo desta fatia)

- **Cover 9:16 do 1º ao último frame.** Rejeitar letterbox / janela horizontal
  + blur (gancho do v12). Reforçar S1 no plano/DOM para novas capturas; sem
  exceção “foto paisagem ⇒ Stories”.
- **Energia contínua no miolo:** sem holds de 2–3 s; KB/transforms lineares N2
  cobrindo o miolo de cada cena (U2 perceptível de volta). Tom aconchegante:
  movimento sempre presente ≠ hard-cut / hard-sell.
- Versionar polish (ex. `motion-photo-polish-v6`) sem editar bytes/replay
  v1–v5; preservar finish-v1, timing-v1, intent v10, crop v5, guardas,
  Music.
- Ambiente (U3) só se o inventário já tiver material elegível — não forçar
  inventar fotos nesta rodada.

### V2 — Ajuste estreito opcional (só se V1 falhar no aceite)

- Um único patch focado no que falhou (anti-Stories ou KB). Sem abrir mix,
  briefing novo, A5b sem OK, nem 3º tema.

### Fora desta onda

- U4 / Music / mix (−31,5 LUFS).
- Reescrever o briefing do titular para “testar propaganda”.
- Meta go/no-go de **80% propaganda dura** (teto soft ~70–75; conversão via
  defaults do gerador, não via hard-sell neste ensaio).
- Relaxar T2/finish/guardas; TTS/avatar/renderer novo.
- Aceite E2E sem novo MP4 autorizado; chamada paga sem OK do titular.
- Continuar o loop Café além de V1 (+V2 se preciso).

## Prompt sugerido para o próximo chat

```
Leia AGENTS.md, o topo de docs/PROJECT.md, docs/SDD.md,
docs/phases/BL04-context-and-ai-production.md e
docs/design/motion-ensaio-cafe-aurora-v12-gaps-2026-11-23.md
(contexto U1–U3/polish-v4–v5 em motion-ensaio-cafe-aurora-v11-gaps e PROJECT).

Briefing do titular (preservar o tom; não hard-sell; não reescrever o pedido):
"Quero um reel mostrando o clima do Café Aurora. Uma coisa aconchegante,
com movimento suave e frases curtinhas sobre fazer uma pausa no dia.
Pode usar nossas fotos."

Cliente real será leigo: viesar o gerador photo para conversão (cover,
ritmo suave contínuo, legibilidade, CTA) sem desrespeitar pedido soft.

Implemente a ÚLTIMA rodada Café (V1). No máximo um V2 estreito depois se
eu pedir. Depois congelamos este ensaio.

1) V1 cover: full-bleed 9:16 do 1º ao último frame; rejeitar
   letterbox/Stories (janela horizontal + blur) visto no gancho de
   versao-1 (11). Reforçar S1 no plano/DOM. Versionar polish (ex. v6);
   replay polish/timing v1–v5 intacto.
2) V1 energia: KB/transform suave contínuo no miolo; sem holds ~2–3 s
   do (11). U2 perceptível de volta; tom aconchegante ≠ hard-sell.
3) Ambiente só se inventário elegível; sem inventar fotos; S3/crop v5.

Preservar: crop v5, gates M3/N2/O2/Q2/R1–R3/S1–S3/T1–T3/U1–U3,
intent v10, finish-v1, readability-v1, photo-timing-v1, polish v1–v5
bytes/replay, Music (sem U4). Sem TTS/avatar/renderer novo.

Evidência: versao-1 (11).mp4 hash
456928a676f5a0df397295989fc815aad8281b81cd67962e9894cffa105427d8
pior que Cafe-Aurora-render-recuperado-cefe9071.mp4 no cover/energia
(~55–60% vs propaganda; ~65–70% vs briefing). Tipografia sem blob ok;
render polish-v5 ok. Go: ≥ cefe no olho (cover + vivo), não 80% propaganda.

Testes + PROJECT/SDD/BL04/CHANGELOG/DECISIONS na mesma mudança.
Não declare aceite E2E sem novo MP4 autorizado e minha revisão.
Não rode chamada paga sem eu autorizar.
```

## Aceite desta fatia

- Novo MP4: cover full-bleed do início ao fim; **sem** Stories no gancho.
- Energia perceptível no miolo (sem holds longos como no v12).
- Tipografia sem regressão a blob/glow; copy soft ok.
- Julgamento ≥ `cefe9071` no olho (cover + movimento).
- Se passar: **congela Café** e segue outros conteúdos/negócios.
- Se falhar: no máximo V2 estreito; senão congela com teto documentado.
- Sem upgrade silencioso de snapshots antigos; referência positiva = `cefe9071`.
