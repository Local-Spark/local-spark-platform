# Ensaio Café Aurora — Reel com vídeo do cliente v1 — gaps — 23/11/2026

Atualização 23/11 (pós-Fatia A no worker): captura `(14)` ainda era cartaz creme
porque o worker rodava código antigo (`instagram-reel-v13`, sem contrato). Com
worker atualizado, run `853327f8…` pinou `v14` + `motion-video-reel-v1` e falhou
em `MOTION_VIDEO_KINETIC_TEXT_REQUIRED` (holds fantasmas nas pontas dos textos) —
ver [kinetic-text-gate](motion-video-reel-v1-kinetic-text-gate-2026-11-23.md).
Fatia A em [slice-a](motion-video-reel-v1-slice-a.md); B em
[slice-b](motion-video-reel-v1-slice-b.md). Em 24/11 o titular rejeitou o MP4 B
(`versao-1 (16)` / `8ab63903…`, ~30–40% vs propaganda); Fatia C autorizada em
[slice-c](motion-video-reel-v1-slice-c.md). VR4–VR6 /
aceite E2E / Fatia B continuam backlog. Diagnóstico histórico do `(13)` preservado.

Estado: **diagnóstico e backlog documentados** a partir de
`/Users/israelsilva/Downloads/versao-1 (13).mp4`
(hash `04973908e995f43a5842df2cecdedfde43b10e6542eb4d16091a057898e8974e`).
Run lab associado (após retries de stream): `0a24112c-46df-5540-bac8-7ab35746c27d`
(`MOTION_MANDATORY_REVIEW_FAILED` pós-render; MP4 existe). Entrada:
`cafe-aurora-cliente-preparacao.mp4` / `dd3f0265…`.

Não autoriza, por si, implementação, chamada paga, TTS/avatar novo, mudança de
renderer nem reabrir o loop polish do **photo-reel** (congelado em
[v13-freeze](motion-ensaio-cafe-aurora-v13-freeze-2026-11-23.md)). Destinado a
um próximo chat/modelo.

Referências de qualidade: conjunto de **41** vídeos em
[analise-41-referencias-motion-2026-11-12.md](../evals/analise-41-referencias-motion-2026-11-12.md)
e anotações; Maestros
[analise-video-maestros-WuzMxEKJHkQ-2026-11-11.md](../evals/analise-video-maestros-WuzMxEKJHkQ-2026-11-11.md);
matriz video-reel em
[v0-motion-etapa-0-formatos-e-casos.md](v0-motion-etapa-0-formatos-e-casos.md).

## Contexto

- Briefing soft do titular (pedido do ensaio): gravação da preparação + reel
  aconchegante / pausa / frases curtas / cores da marca — **sem** hard-sell.
- Formato: Reel com **vídeo enviado** (`source_asset_id`), skill/repertório
  `business-reel-v5` (não photo-reel / polish-v6).
- Photo-reel Café permanece congelado; este gap é do **caminho vídeo**.

## Evidência do ensaio

Arquivo: **11,2 s** · 720×1280 · H.264 + AAC mono · ~1,23 Mbps (~1,7 MB).  
Loudness integrado ~**−15,3 LUFS** (LRA ~1) — faixa de fala/ambiente da fonte;
**sem** trilha musical perceptível / mix de propaganda.

Pipeline local 5 fps (cinza 90×160): static ~5,5%, mean diff ~9,4 — o movimento
vem quase só do **vídeo-fonte** dentro da janela; a **moldura** (fundo creme,
título, rodapé) é estática.

### Storyboard observado

1. **Todo o tempo:** cartaz creme full-frame; texto fixo **“Café Aurora”** no
   topo (não logo do kit); **janela de vídeo inset** ao centro (não cover 9:16);
   filete/linha decorativa; grandes vazios acima/abaixo.
2. **~meio:** aparece frase **“Uma pausa no seu dia.”** no rodapé (estática).
3. **~fecho:** CTA **“Conheça nosso cardápio →”** sob a frase; sem packshot,
   sem corte editorial, sem tipografia cinética sobre a ação.
4. **Áudio:** narração/voz da gravação (ensaio com fala sintética); sem música
   de fundo, sem ducking de trilha, sem SFX de edição.

Julgamento do titular: peça **horrível** / longe do desejado — nome fixo,
vídeo fixo no meio, frase + narração, sem música/transições/motions/efeitos.

### % vs referências (orientação)

| Dimensão | ~% vs propaganda (41 refs) | Nota |
| --- | --- | --- |
| Integração da gravação (full-bleed / camadas) | **10–20** | Janela em cartaz creme |
| Desenvolvimento editorial (cortes / beats) | **10–20** | Um take contínuo em caixa |
| Tipografia / marca | **15–25** | Texto morto; sem kit logo |
| Motion / transição / efeito | **5–15** | Ausentes na moldura |
| Mix / música | **5–15** | Só mono da fonte |
| Tom soft / pausa (briefing) | **40–50** | Copy alinhada, execução não |
| **Síntese** | **~15–25** | Longe das refs e do photo-reel |

## O que as ~41 refs exigem (e este MP4 não entrega)

Síntese de
[analise-41-referencias-motion-2026-11-12.md](../evals/analise-41-referencias-motion-2026-11-12.md):

1. **A peça se desenvolve** — novos argumentos/planos ao longo do tempo (ex.
   preparo Dg9tw8p_fn0), não um único cartaz com take contínuo.
2. **Material full-bleed** entrega valor antes do overlay (espresso YTYOyY3BxMQ,
   ritmo suave gAPZ893OO7s) — janela pequena em creme falha.
3. **Transições são relações** entre estados (oclusão 8EBzWURWcwk; portal Aura
   sr_O6HSzm0c), não só “entrar texto no rodapé”.
4. **Tipografia vive com a ação** — não header/footer de slide.
5. **Som** (Maestros 04:43–05:24): trilha + duck na fala; loudness planejado —
   aqui só a faixa da gravação.

## Gaps / problemas (priorizados)

| ID | Problema | Evidência neste ensaio |
| --- | --- | --- |
| **VR1** | Gravação **não** é cover 9:16; layout “Stories/cartaz” com margem creme | Janela central o tempo todo |
| **VR2** | Marca como **texto fixo** “Café Aurora”, não logo/kit overlay | Topo estático |
| **VR3** | Tipografia de **slide** (frase/CTA no rodapé morto), sem cinética nem âncora na ação | “Uma pausa…” / CTA |
| **VR4** | Sem **EDL** / cortes com função; um inset contínuo ≈ duração da fonte | 11,2 s sem remonte |
| **VR5** | Sem transições / motion / efeitos com intenção (mesmo suaves) | Moldura congelada |
| **VR6** | Sem **música** / mix; áudio = só fonte mono | −15,3 LUFS, LRA~1 |
| **VR7** | Skill/`business-reel-v5` admite composição editorial fraca sem gates duros de cover/energia como no photo-reel | Resultado passou a gerar MP4 ruim |

## Backlog proposto (implementação — fatias)

Preservar: briefing soft; HTML/Chromium/FFmpeg; Temporal; uma gravação ≤60 s /
50 MiB; sem avatar/TTS novo sem OK; sem reabrir polish photo-reel.

**Ordem (23/11 → 24/11):** Fatia A = VR1–VR3 → captura → revisão. Captura A
feita e rejeitada criativamente; **Fatia B agora autorizada** (VR4–VR5; VR6 se
biblioteca de áudio existente permitir). Não desfazer A; não implementar tudo
de uma vez sem versionar contratos/guardas.

### VR1 — Cover obrigatório da gravação (P0)

- Vídeo-fonte (ou crop seguro) **full-bleed 9:16** do 1º ao último frame.
- Proibir cartaz creme / janela inset / letterbox como layout default.
- Gates plano+DOM análogos ao espírito S1/polish cover do photo-reel, versionados
  para **video-reel** (não editar bytes de polish photo v1–v6).

### VR2 — Marca do kit, não label morto (P0)

- Usar logo/assets do kit como overlay; proibir substituir por string “Nome do
  negócio” fixa no header o reel inteiro.
- Hierarquia: ação da gravação > tipografia > marca discreta.

### VR3 — Tipografia sobre a ação (P0/P1)

- Frases curtas **sobre** o full-bleed, legíveis (scrim local / região escura),
  com enter/transform/exit; CTA ≥1500 ms no fecho.
- Proibir bloco de rodapé estilo apresentação PowerPoint como única tipografia.

### VR4 — Edição com EDL mínima (P1)

- Pelo menos N cortes/segmentos com função (gancho → preparo → detalhe → convite),
  respeitando fala quando houver (não cortar no meio da palavra sem regra).
- Transições curtas (corte seco / dissolve curto) entre segmentos — relações,
  não adorno.

### VR5 — Motion suave com intenção (P1)

- KB/pan leve no crop, ou grafismo mínimo alinhado ao tom soft; sem hard-sell
  nem partículas obrigatórias.
- Rejeitar plano em que **só** a mídia-fonte se move e UI permanece 100% estática.

### VR6 — Mix música + fala (P1, com direitos)

- Trilha licenciada da biblioteca (como photo-music) com duck sob narração;
  se não houver trilha elegível, estado explícito — não silenciar a falha.
- Não inventar música sem política/direitos.

### Fora desta onda

- Reabrir photo-reel Café / V2 energia foto.
- Avatar, voz clonada, HeyGen.
- Trocar renderer (Remotion) só por desejo estético.
- Meta publish / WhatsApp.
- Meta 80% propaganda dura contra o briefing soft — teto é conversão **respeitando**
  o pedido.

## Aceite da próxima fatia (audiovisual)

Novo MP4 video-reel: gravação full-bleed; logo/kit; frases sobre a ação; ao menos
uma progressão editorial (cortes ou beats claros); trilha ou motivo documentado
se indisponível; sem cartaz creme/janela. Tom aconchegante. Revisão humana do
titular; não declarar aceite E2E só por gates DOM.

## Prompt sugerido para o próximo chat

```
Leia AGENTS.md, o topo de docs/PROJECT.md, docs/SDD.md,
docs/phases/BL04-context-and-ai-production.md e
docs/design/motion-ensaio-cafe-aurora-video-reel-v1-gaps-2026-11-23.md
(refs: docs/evals/analise-41-referencias-motion-2026-11-12.md,
docs/evals/analise-video-maestros-WuzMxEKJHkQ-2026-11-11.md;
photo-reel congelado em motion-ensaio-cafe-aurora-v13-freeze).

Ensaio rejeitado: versao-1 (13).mp4 hash
04973908e995f43a5842df2cecdedfde43b10e6542eb4d16091a057898e8974e
(run 0a24112c…; entrada dd3f0265…). Cartaz creme, “Café Aurora” fixo, vídeo
inset, frase/CTA no rodapé, narração sem música/transições/motion — ~15–25%
vs refs de propaganda.

Briefing soft a preservar (não hard-sell): reel aconchegante de pausa a partir
da gravação do cliente, frases curtas, cores da marca.

Implemente SOMENTE a Fatia A do video-reel: VR1–VR3. NÃO implemente VR4–VR6
nesta mudança. Depois eu autorizo UMA captura e reviso; Fatia B (VR4–VR5;
VR6 se couber) só se eu pedir.

Versionar contratos/skill/repertório de vídeo; NÃO editar bytes/replay do
polish photo v1–v6.

1) VR1: gravação full-bleed 9:16; proibir layout cartaz/janela creme.
2) VR2: marca via kit/logo overlay; proibir label de nome fixo como hero.
3) VR3: tipografia cinética/legível SOBRE a ação; CTA ≥1500ms; sem rodapé slide.

Preservar Temporal, HTML renderer, tetos 60s/50MiB, uma gravação por pedido.
Sem TTS/avatar/Remotion novo. Sem reabrir photo-reel Café. Sem música nova
nesta fatia (VR6 fora).

Testes + PROJECT/SDD/BL04/CHANGELOG/DECISIONS na mesma mudança.
Não declare aceite E2E sem novo MP4 autorizado e minha revisão.
Não rode chamada paga sem eu autorizar.
```
