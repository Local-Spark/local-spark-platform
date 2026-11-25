# Video-reel — replanejamento por qualidade (não por proibição)

## Implementação C — 24/11/2026 (aceite audiovisual pendente)

### Contratos e execução

- Pins novos: reel-v2, edit-v3, design-v1, skill video-v22, repertório video-v5,
  geração proposed-video-output-v3 e áudio-v3. `previous` conserva pins; arquivos
  reel-v1/edit-v1/scene-visibility-v1 e repertórios/skills A/B não foram editados.
- `video_layout.design` tem viewport e layers. Cada layer referencia um elemento
  do plano, asset autorizado quando imagem, retângulo normalizado, ordem,
  rectangle/ellipse, cor e beats lineares `{x,y,opacity}`. DIV gráfico e IMG são
  capacidades executáveis; SVG/canvas/3D arbitrários não integram este schema.
- Runtime cria os nós declarados, aplica estados absolutos, visibilidade por cena
  e seeks, inclusive reversos. O modelo implementa logo/textos/VIDEO único.
  Camadas 0–9 ficam atrás do vídeo (10); 11–18 podem assumir o primeiro plano;
  logo/textos ficam acima (>=20). PIP revela fundo estável; imagem autorizada
  à frente da gravação é alternativa ao PIP. Referência externa nunca vira asset.
- Guarda reel-v2 aceita a allowlist e continua a verificar texto puro, scrim,
  logo, mídia e cover quando escolhido. Extras não declarados, inclusive
  pseudo-elementos, falham `UNPLANNED_OVERLAY`; execução alterada de camada
  falha `MOTION_VIDEO_LAYER_NOT_EXECUTED`.
- O primeiro mecanismo de transição qualificado é **cut com função entre estados
  distintos**. Não há promessa de dissolve/wipe/máscara de pessoa nesta versão.
  A mudança de composição dura >=800ms; um grafismo exposto desloca >=48px por
  >=800ms, com presença substancial. Essas medidas evitam o anti-padrão conhecido;
  não medem beleza, desejo ou progressão semântica. Soft não obriga imobilidade.

### EDL e proteção de fala

In/out são livres na fonte medida, sem speed ramp. Cenas contíguas na saída;
duração final pode ser menor que `output.duration_ms`, que passa a ser teto no
planejamento C. Só o último frame admite padding medido de 1–34ms. A versão A/B
conserva igualdade de duração e demais regras históricas.

Corte visual com fonte contígua não interrompe áudio. Em descontinuidade,
ambos os lados precisam de fronteira segura: silêncio por energia local com
limiar <=−45dBFS, medição vinculada ao SHA da fonte, sem intervalos omitidos e
margem de 120ms; ou lacuna entre cues automáticos completos com confiança >=.8
e margem. Cues reconhecidos perto do corte prevalecem sobre baixa energia.
Transcrição parcial do titular não comprova silêncio. Tempos ASR são estimativas;
essa regra reduz risco de corte de palavra, não certifica o sentido da montagem.
Sem prova suficiente: `MOTION_VIDEO_SPEECH_CUT_UNSAFE`, não banimento de remonte.

O campo `audio` do modelo continua o manifesto original autorizado. O servidor
compila os intervalos da EDL numa faixa original montada, sem alterar ganho ou
velocidade. Cues visuais são projetados da fonte para a cena. Duração encurtada é
recalculada antes da implementação/render e validada na restauração do checkpoint.

### VR6 sem nova compra

Seleção explícita já autorizada ou cache `motion_music` do mesmo tenant/negócio,
com identidade `video-music-library:0`, reserva zero e audit/outbox. Falta de faixa
compatível fica durável como `no_eligible_music`; o ramo C não possui dispatch
para ElevenLabs. Biblioteca CC0 atual tem coffee-pour/cup-contact, não trilha:
SFX não substituem música nem são apresentados como som original da gravação.

Mixer V3 monta um único bus original a partir dos segmentos, usa esse bus no
sidechain e reduz somente música. Duck: threshold .02, ratio 6, attack 15ms,
release 250ms. Fade/trim da trilha respeitam a duração final. SFX precisam de
licença e vínculo ao plano já validados. Medições de áudio final e integridade
continuam obrigatórias; escuta, inteligibilidade e adequação estética permanecem
pendentes de revisão humana. A/B/photo seguem o mixer histórico quando pinados.

### Review e limites de aceite

Review `adequate` exige passar novamente o gate de desenvolvimento do plano.
Take contínuo + texto + crop mínimo, layers invisíveis ou falta de desenvolvimento
não podem ser aprovados apenas por uma declaração do modelo. A verificação do
Chromium precede a crítica; as evidências temporais existentes continuam valendo.
Essa barreira fecha a regressão `(15)/(16)`; não permite declarar ~70% ou E2E.

Não foram executados provedores pagos, compra, captura do cliente, publicação,
reload de worker nem atualização da imagem instalada. Para usar C no lab será
necessário carregar os novos pins e incluir `audio-video.cjs` na imagem do renderer.
Uma nova captura do cliente/MP4 e seu aceite dependem de autorização posterior.
As alterações de photo-polish feitas em paralelo não fazem parte desta implementação.

### Validação técnica desta implementação

- 179 testes Python do recorte/replay/checkpoint: 100% de linhas e branches nos
  cinco serviços de vídeo medidos (345 statements, 172 branches), sem exclusões.
  Mais 85 testes de wiring/orquestração/checkpoint/fala passaram; cinco testes de
  orientação/replay foram atualizados para as capacidades C e passaram.
- 299 testes Node passaram: 100% de linhas/branches/funções nos oito módulos
  medidos, incluindo runtime de camadas, mixer V3 e renderer existente.
- 12 integrações em PostgreSQL dedicado `_test`, logins restritos e fornecedores
  falsos passaram: pins, gate antes de render, identidade durável, cache zero
  custo e isolamento entre tenants. Nenhum banco de projeto foi migrado/limpo.
- Chromium sintético: C (PIP, imagem auxiliar à frente, allowlist, seeks reversos),
  A, B e scene-visibility passaram. A prova de visibilidade foi repetida isolada
  depois de timeout causado pela execução concorrente dos quatro navegadores.
- FFmpeg com PCM sintético, sem MP4: ordem temporal, duração e amplitude da faixa
  original verificadas; energia da música cai sob duck. Isso não é escuta nem E2E.
- Ruff/formato do recorte e mypy dos 11 módulos verificados passaram. Trinta
  assets históricos de vídeo A/B foram comparados com o índice: nenhum byte mudou.
- `make ci` **não está verde**: para nos mesmos 66 lints fora do recorte. No
  checkout isolado de HEAD foram reproduzidas 20 falhas unitárias preexistentes
  em `test_motion_context_requests.py`/`test_motion_audio.py` (mocks de feedback
  e diagnóstico musical). CI/cobertura globais continuam pendentes; não foram
  relaxados gates nem excluídos módulos para ocultar essas falhas. A regressão
  ampla final teve 1867 testes aprovados e exatamente as mesmas 20 falhas de HEAD.

Aceite pendente: carregar worker/imagem novos em uma aplicação posteriormente
combinada, produzir MP4 somente quando autorizado e obter revisão do titular
contra 41 refs/Maestros. Nenhuma nota percentual de qualidade foi atribuída.

## 24/11/2026 — decisão do titular

Norte de qualidade: as **~41 referências** de propaganda
([analise-41-referencias-motion-2026-11-12.md](../evals/analise-41-referencias-motion-2026-11-12.md))
e o fluxo Maestros
([analise-video-maestros-WuzMxEKJHkQ-2026-11-11.md](../evals/analise-video-maestros-WuzMxEKJHkQ-2026-11-11.md)
+ [motion-qualidade-direcao-e-gaps-2026-11-11.md](motion-qualidade-direcao-e-gaps-2026-11-11.md)).

Ensaios `(15)`/`(16)` ~30–40% vs essas refs. Review `adequate` ≠ qualidade.
O titular rejeita otimizar para **proibição** (grafismo banido, remonte banido,
VR6 “unavailable”) quando o objetivo é peça próxima das refs.

Este documento **reorienta** o trabalho: capacidades versionadas + verificação,
não skill que ensina o modelo a não criar. Fatias A/B permanecem como base de
cover/logo/texto/EDL mínima; deixam de ser teto criativo. A Fatia C em
[slice-c](motion-video-reel-v1-slice-c.md) fica subordinada a este replano
(qualidade primeiro; C1–C5 são meios, não o fim).

## Por que existiam as proibições (histórico — não lei)

### Grafismos “proibidos”

1. Guarda Fatia A (`video-reel-v1.js`) só trata VIDEO + logo + textos/scrims
   como overlays legais; o resto → `UNPLANNED_OVERLAY`.
2. O modelo tentou hastes/`role=graphic` (run `c516f97b…`); a guarda rejeitou
   **mesmo declarado no plano**.
3. A skill passou a dizer “não planeje grafismos” para evitar gasto em HTML que
   o Chromium mataria — **congelou a limitação da guarda na orientação**.

Isso não veio das 41 refs. Veio de um gate incompleto tratado como estética.

### Remonte temporal “proibido” com áudio

1. Fatia B quis preservar fala sem ASR palavra-a-palavra confiável.
2. Regra simples: com áudio, `source_in_ms = scene.start_ms` → mesma fita,
   só reenquadramento; áudio original intocado.
3. Evitou corte no meio da palavra, mas também **impediu** a edição que as refs
   usam (gancho → detalhe → packshot com remonte).

Proteção de fala é válida; banir remonte inteiro foi atalho, não qualidade.

### VR6 “unavailable”

Mix com biblioteca existente não foi qualificado no caminho video-edit; o
contrato marcou indisponível. Photo já tem trilha. De novo: dívida técnica
virando proibição de produto.

### Photo-reel: `MOTION_PHOTO_DECORATION_FORBIDDEN` / polish T3

No reel **estático** (fotos), o polish-v1–v6 exige só fotos + logo + tipografia/
scrim e rejeita `role=graphic`, cantoneiras, SVG/canvas decorativo
(`MOTION_PHOTO_DECORATION_FORBIDDEN`). Motivo histórico: ensaio com “UI
residual” / crop-marks; o polish engessou **toda** decoração para não
regredir. A skill ainda menciona HTML/SVG/Canvas; o gate contradiz.

**24/11 — implementado (caminho photo, separado do vídeo):**
`motion-photo-polish-v7` + `photo-polish-v5.js` + `instagram-reel-photo-v21`.
Grafismo declarado (`role=graphic` + id DOM) é allowlist; residual sem plano
continua DECORATION. Cover/crop/legibilidade/Music intactos.

**24/11 — titular:** remover esse engessamento. Quanto mais qualidade
implementável na peça, melhor. O congelamento Café
([v13-freeze](motion-ensaio-cafe-aurora-v13-freeze-2026-11-24.md) /
`motion-ensaio-cafe-aurora-v13-freeze-2026-11-23.md`) **não** barra mais a
reabertura para **capacitar grafismo/camadas declarados** no photo-reel;
permanecem cover/crop-safe, inventário elegível, legibilidade, tom soft e
pins versionados (sem inventar asset, sem hard-sell).

## O que as refs exigem (norte)

1. **A peça se desenvolve** — novos planos/argumentos no tempo (não caption
   sobre um take).
2. **Material full-bleed entrega valor** — e depois **integra** overlay/camada
   (não só caixa preta).
3. **Transições são relações** entre estados (oclusão, portal, corte com
   função) — não só troca de frase.
4. **Tipografia vive com a ação**; marca do kit, não label morto.
5. **Som**: trilha + duck na fala; SFX de edição sobrios (Maestros 04:43–05:24).
6. Arquitetura continua HTML/Chromium/FFmpeg/Temporal — Maestros não pede
   Remotion; pede construção verificável e integração da gravação ao cenário.

Briefing soft (pausa, sem hard-sell) permanece; **não** é desculpa para peça
parada. Soft ≠ sem desenvolvimento.

## Replano: capacidades, não vetos

Substituir na orientação e nos contratos a linguagem “não faça X” por
“faça X assim, e o gate verifica”.

| Capacidade | Em vez de proibir | Verificar |
| --- | --- | --- |
| **Grafismos / formas** | Banir overlays | Plano declara ids/role/beats; guarda **aceita allowlist do plano** e rejeita só o não declarado |
| **Camadas / 2º plano** | Só VIDEO full-bleed | Intervalos com foto/kit autorizado, PIP, fundo kit, ou gravação que cede espaço |
| **Remonte temporal** | `source_in = scene.start` sempre | EDL com in/out livres **com regra de fala**: cortar em silêncio / fim de utterance ASR / margem segura; se ASR fraco, recusar remonte arriscado com código claro — não banir remonte |
| **Transições** | Só cut de reframe | Cut/dissolve/wipe/oclusão curta com função entre estados visuais distintos |
| **Motion** | Piso numérico mínimo | Amplitude perceptível + desenvolvimento editorial |
| **Mix (vídeo)** | `edl_music_mix_not_qualified` | Qualificar biblioteca existente + duck; SFX licenciados; indisponível só se biblioteca vazia |
| **Decoração photo** | `DECORATION_FORBIDDEN` / T3 | Plano allowlist: graphic/SVG/formas declarados + beats; polish/DOM aceitam o declarado; rejeitam só residual não planejado |

Gates úteis a **preservar** (vídeo e foto): cover quando a cena pede cover;
logo kit; texto legível; crop-safe / inventário elegível; sem inventar asset;
sem secrets; Temporal; tetos 60s/50MiB; tom soft. Gates que **bloqueiam
qualidade** (UNPLANNED/DECORATION absoluto a qualquer grafismo declarado;
remonte zero com áudio; VR6 forever) devem ser **versionados/substituídos**.

Sem Remotion/TTS/avatar sem OK. Sem compra de música nova sem autorização
(biblioteca do repo primeiro). Congelamento Café: **reaberto só** para esta
linha de capacidade/qualidade; não é carta branca para hard-sell ou afrouxar
crop/legibilidade.

## Ordem de implementação (qualidade primeiro)

Uma onda coesa (vídeo + photo onde a trava for a mesma família):

1. **Guarda + schema “plano = allowlist”** (vídeo **e** photo-polish) —
   overlays/grafismos/camadas declarados executáveis; fora do plano continua
   rejeitado. Remover T3/`DECORATION_FORBIDDEN` cego e o “não planeje graphic”
   das skills.
2. **EDL com remonte speech-safe** (vídeo) — ASR/silêncio; código específico
   se inseguro — não banir remonte.
3. **Skill/repertório** vídeo e photo — exemplares alinhados às 41 refs;
   motion graphics coerentes com kit; sem mandamentos de pobreza visual.
4. **Mix VR6** (vídeo) — biblioteca + duck; photo mantém/`aprimora` trilha.
5. **Review** — não premiar take/foto+texto mínimo sem desenvolvimento.
6. **Capturas autorizadas** (vídeo e, se couber, photo) + revisão humana;
   meta percepção **≥55–70%** vs refs.

Não declarar 70%/E2E só por testes unitários.

## Prompt para o chat de implementação

```
Leia AGENTS.md e o topo de docs/PROJECT.md, docs/SDD.md,
docs/phases/BL04-context-and-ai-production.md,
docs/design/motion-video-reel-qualidade-replanejamento-2026-11-24.md,
docs/design/motion-ensaio-cafe-aurora-video-reel-v1-gaps-2026-11-23.md,
docs/design/motion-video-reel-v1-slice-c.md,
docs/design/motion-ensaio-cafe-aurora-v13-freeze-2026-11-23.md,
docs/evals/analise-41-referencias-motion-2026-11-12.md,
docs/evals/analise-video-maestros-WuzMxEKJHkQ-2026-11-11.md e
docs/design/motion-qualidade-direcao-e-gaps-2026-11-11.md.

Decisão do titular: NÃO otimizar por proibição. Norte = máxima qualidade
implementável alinhada às ~41 refs + Maestros. Ensaios vídeo (15)/(16)
~30–40%; adequate ≠ bom. Quanto mais qualidade possível na peça, melhor.

Proibições a eliminar (foram atalho de gate, NÃO pedido do titular):
- vídeo: UNPLANNED absoluto / “não planeje grafismos”; remonte banido com
  áudio (source_in=scene.start); VR6 unavailable por omissão
- photo-reel: MOTION_PHOTO_DECORATION_FORBIDDEN / polish T3 (“só tipografia,
  sem graphic/SVG”). Congelamento Café REABERTO para capacitar isso;
  manter cover/crop-safe/legibilidade/tom soft.

Replaneje e implemente CAPACIDADE + verificação (vídeo e photo):
1) Plano = allowlist: grafismos/camadas/PIP/formas DECLARADOS executam;
   rejeitar só o não declarado. Versionar guardas video-reel e photo-polish.
2) Vídeo: EDL remonte speech-safe; mix VR6 com biblioteca + duck; transições
   com função; anti-padrão take+texto+crop mínimo falha.
3) Photo: remover DECORATION_FORBIDDEN cego; skill/repertório orientam motion
   graphics coerentes com kit; sem reintroduzir UI residual NÃO planejada.
4) Review não premia peça mínima legal.
5) Preservar Temporal, HTML/Chromium/FFmpeg, logo kit, texto legível, sem
   inventar assets, tetos 60s/50MiB. Soft ≠ parado. Sem Remotion/TTS/avatar.
   Sem compra de música sem eu autorizar.
6) Versionar pins; replay de snapshots antigos intacto onde couber.
7) Testes + PROJECT/SDD/BL04/CHANGELOG/DECISIONS + este design doc.
8) Não declare E2E nem “~70%” sem MP4 autorizado e minha revisão.
   Não rode chamada paga sem eu autorizar.
```
