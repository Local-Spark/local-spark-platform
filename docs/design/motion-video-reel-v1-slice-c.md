# Video-reel v1 — Fatia C (camadas / transição / mix)

## 24/11/2026 — video-reel C: capacidade declarada e verificação

Implementado em código para novas capturas: `motion-video-reel-v2`,
`motion-video-edit-v3`, `video-design-v1`, `instagram-reel-video-v22`,
`business-video-reel-v5`, geração `proposed-video-output-v3` e mixer
`motion-audio-v3`. A/B mantêm seus contratos e bytes; ausência de pin não
promove replay. Esta mudança trata exclusivamente de vídeo; alterações
paralelas de photo-polish no workspace são preservadas, fora deste recorte.

O plano declara grafismos, imagens auxiliares e viewport/PIP. Runtime próprio
executa essas camadas, crop e relógio da EDL; guarda V2 verifica execução e
recusa pintura não declarada. Cover continua quando escolhido, além de logo do
kit, texto puro legível/scrim e scene-visibility. Desenvolvimento exige mudança
sustentada de composição e grafismo realmente exposto, não escondido atrás da
fonte. Review `adequate` recusa o anti-padrão take+texto+crop mínimo.

Remonte com áudio admite cortes com margem de 120ms em silêncio medido ou
intervalos ASR confiáveis; risco retorna `MOTION_VIDEO_SPEECH_CUT_UNSAFE`.
Saída pode encurtar: vídeo, áudio original, música e restauração do checkpoint
usam a mesma duração/EDL. Mix usa seleção autorizada ou cache do mesmo negócio,
com reserva zero, duck somente na música e SFX CC0 já existentes. Cache vazio
registra indisponibilidade; este caminho nunca chama o provedor de música.

Temporal, identidades duráveis, audit/outbox, RLS e HTML/Chromium/FFmpeg
permanecem. Sem chamada paga, compra, captura do Café, deploy ou reload.
Testes técnicos não constituem E2E nem nota perceptual. MP4 autorizado e revisão
do titular vs 41 refs/Maestros continuam pendentes. Detalhes e validação no
replanejamento de qualidade de 24/11.

Validação: 179 testes Python do recorte (100% linhas/branches em cinco serviços),
299 Node (100% linhas/branches/funções nos oito módulos medidos), 12 integrações
PostgreSQL `_test`, quatro provas Chromium sintéticas e uma prova FFmpeg de áudio
passaram. Ruff/formato do recorte e mypy de 11 módulos passaram. Trinta assets
históricos A/B conferidos byte a byte, intactos. `make ci` segue bloqueado por
66 lints preexistentes; 20 falhas unitárias antigas de feedback/áudio foram
reproduzidas em HEAD isolado. Regressão ampla final: 1867 passaram e somente essas
20 falharam (mesmo conjunto de HEAD). CI/cobertura globais e aceite audiovisual pendentes.

> **24/11 — subordinada ao replano de qualidade.** Vetos de grafismo/remonte/VR6
> não são meta. Norte e prompt atualizados em
> [qualidade-replanejamento-2026-11-24](motion-video-reel-qualidade-replanejamento-2026-11-24.md).

## 24/11/2026 — autorização após rejeição criativa do MP4 Fatia B

Titular rejeitou `versao-1 (16).mp4`
(`b1c3a153364e4129061fe705520a9c49531814664f8c6147cfa707be73e3607a`),
run `8ab63903-30fa-58c2-b44e-a91049c193d6`. Pins B ativos (`v21` / edit-v2 /
`business-video-reel-v4`); review automática `adequate`; revisão humana: ainda
péssimo. Sensação de vídeo parado; sem outro fundo, sem elemento/forma que
entre na peça, sem transição perceptível, sem efeitos, sem SFX/trilha.

O que B entregou de fato: EDL de **reenquadramento** com áudio contínuo (mesma
fita), crop na ordem do mínimo do gate (~1,00→1,04 e corte ~1,12), textos/scrim
e logo. Isso cumpre o contrato mínimo de B, **não** o nível de propaganda das
~41 refs / Maestros.

### % vs propaganda (orientação, ensaio 16)

| Dimensão | ~% | Nota |
| --- | --- | --- |
| Integração da gravação (full-bleed) | **70–80** | Cover ok; quase só a fita |
| Desenvolvimento editorial | **25–35** | 2 beats de texto; take contínuo |
| Tipografia / marca | **40–50** | Kit + scrim; caixas pretas simples |
| Motion / transição / efeito | **15–25** | Crop mínimo; sem camadas |
| Mix / música | **10–15** | Só mono da fonte; VR6 off |
| Tom soft / pausa (briefing) | **50–55** | Copy ok; execução rasa |
| **Síntese** | **~30–40** | **Longe de 70%** |

Fatia A+B ficam como fundação (não desfazer). Fatia C ataca o buraco que o
titular nomeou: camadas, saída da gravação para outro elemento, transição com
função, motion gráfico e som.

## Escopo autorizado (Fatia C)

Preservar: Temporal, HTML/Chromium/FFmpeg, tetos 60s/50MiB, briefing soft,
photo-reel Café congelado, VR1–VR3, scene-visibility, texto puro/scrim estável,
EDL B + padding v2, proteção de fala com áudio (sem inventar ASR palavra a
palavra). Versionar contratos/skill/repertório/guardas; snapshots A/B e polish
photo intactos.

| ID | Objetivo | Critério mínimo |
| --- | --- | --- |
| **C1 — Camadas / saída da fita** | A gravação deixa de ser o único plano visual o tempo todo | Em ≥1 intervalo perceptível (≥800ms): (a) material autorizado do inventário/acervo do pedido (foto/kit) como plano de apoio **ou** (b) a gravação reduz/desloca (PIP/card/cover parcial) revelando fundo/cor do kit / segundo plano autorizado. Proibir inventar assets. Anti-padrão: full-bleed ininterrupto 0→fim só com texto. |
| **C2 — Grafismo / forma com intenção** | Linhas/formas/máscaras **declaradas** no plano | ≥1 elemento gráfico planejado (role/ids), alinhado ao tom soft; entra/sai com beats; guarda versionada aceita só o declarado e continua a recusar lixo `UNPLANNED`. Não hard-sell, partículas obrigatórias nem decoração livre. |
| **C3 — Transição como relação** | Corte/wipe/dissolve/oclusão curta com função editorial | ≥1 transição entre estados visuais distintos (não só troca de texto no mesmo enquadramento). Com áudio: não cortar fala no meio da palavra sem regra explícita; preferir transição visual sobre remonte agressivo. |
| **C4 — Motion perceptível** | Além do mínimo B | Crop/pan/scale **ou** movimento do grafismo/camada com amplitude que um revisor humano note sem magnifier; gates não podem premiar só o piso numérico de B se a peça continuar “parada”. |
| **C5 — Mix (VR6)** | Trilha + duck; SFX só de biblioteca | Reutilizar `motion_music` / sound library / photo-music já existentes. Duck sob narração quando houver fala. SFX sobrios de biblioteca. Se não houver trilha elegível: estado explícito — não inventar nem comprar. Qualificar mix de verdade (sair de `edl_music_mix_not_qualified`). |

## Fora desta fatia

- Desfazer cover/logo/texto puro/scene-visibility/EDL B para “ficar solto”.
- Remotion, TTS, avatar, HeyGen, Meta publish.
- Reabrir polish photo-reel Café.
- Compra/download de música nova ou chamada paga sem autorização.
- Declarar aceite E2E / “~70% propaganda” só por gates.

## Aceite audiovisual

Uma captura autorizada deve, na revisão humana: desenvolver a peça (não um
caption sobre take contínuo); mostrar ao menos uma mudança de plano/camada;
grafismo ou transição perceptível; trilha/duck ou motivo explícito de
indisponibilidade; manter tom soft. Meta de percepção: **subir da faixa ~30–40%
para ~55–70%** nas refs — 70% não é garantido só por implementar C.

## Prompt para o chat de implementação

```
Leia AGENTS.md e o topo de docs/PROJECT.md, docs/SDD.md,
docs/phases/BL04-context-and-ai-production.md,
docs/design/motion-ensaio-cafe-aurora-video-reel-v1-gaps-2026-11-23.md,
docs/design/motion-video-reel-v1-slice-a.md,
docs/design/motion-video-reel-v1-slice-b.md e
docs/design/motion-video-reel-v1-slice-c.md
(refs: docs/evals/analise-41-referencias-motion-2026-11-12.md,
docs/evals/analise-video-maestros-WuzMxEKJHkQ-2026-11-11.md;
photo-reel congelado).

Contexto: Fatia A+B ativas. Titular rejeitou versao-1 (16).mp4 hash
b1c3a153364e4129061fe705520a9c49531814664f8c6147cfa707be73e3607a
(run 8ab63903…, v21/edit-v2/v4): ainda parece vídeo parado — take contínuo +
textos/scrim + crop mínimo; sem outro fundo/camada, sem forma/grafismo, sem
transição forte, sem SFX/trilha. Review adequate ≠ aceite. Síntese ~30–40% vs
propaganda; NÃO estamos perto de 70%.

Briefing soft: pausa aconchegante, frases curtas, kit, sem hard-sell.

Implemente a Fatia C: C1 camadas/saída da fita, C2 grafismo declarado, C3
transição com função, C4 motion perceptível, C5 mix VR6 com biblioteca já
existente (duck; SFX só licenciados) ou indisponibilidade explícita.
NÃO desfazer VR1–VR3 / scene-visibility / texto puro / EDL B+padding v2.
NÃO editar bytes/replay polish photo v1–v6.
NÃO Remotion/TTS/avatar. NÃO reabrir photo-reel Café.
NÃO chamada paga / captura do cliente sem eu autorizar depois.

1) Versionar contrato/skill/repertório/guarda; pins novos; anti-padrão
   full-bleed 0→fim só com texto+crop mínimo deve falhar.
2) Permitir materiais do inventário/acervo do pedido como plano de apoio;
   sem inventar assets.
3) Grafismos só declarados; UNPLANNED continua a barrar o resto.
4) Qualificar mix (sair de edl_music_mix_not_qualified) via biblioteca local.
5) Testes sintéticos + 100% cobertura no recorte; PROJECT/SDD/BL04/CHANGELOG/
   DECISIONS + slice-c na mesma mudança.

Não declare aceite E2E nem “~70%” sem novo MP4 autorizado e minha revisão.
Não rode chamada paga sem eu autorizar.
```
