# Video-reel v1 — falha `MOTION_VIDEO_LAYOUT_REQUIRED` (multi-cena)

## 24/11/2026 — execução DOM após v17

A falha seguinte de render e a correção de orientação v18 estão em
[DOM/overlays](motion-video-reel-v1-dom-overlay-2026-11-24.md).
Gates e pins históricos preservados; aceite audiovisual continua pendente.

## 24/11/2026 — acompanhamento

Run `028a10c5…` confirmou o wiring v16/v2 e mídia local nas duas cenas.
Falha seguinte: ausência de transform próprio nos dois textos finais, corrigida
na orientação pinada v17. Ver [diagnóstico VR3](motion-video-reel-v1-kinetic-text-gate-2026-11-23.md).
Sem mudança de layout/DOM/repertório v2 ou replay.

## 23/11/2026 — video-reel: orientação por cena e captura automática do lab

Implementado `instagram-reel-video-v16` com SHA fixo: cada cena declara VIDEO
`assets/source.mp4` e IMG `assets/logo.png`, IDs locais em video_layout e
staging; não herda nós da cena anterior. Briefing soft pode usar uma cena
contínua. Multi-cena repete nós, preservando tempo absoluto/áudio da gravação.
VR3 mantém enter/exit nas fronteiras, sem hold fantasma e CTA visível ≥1500ms.
A orientação adicional de uso do repertório fica na skill v16: os bytes/pins
já capturados de `business-video-reel-v2` permanecem intactos para replay.

LabMotionRequests prepara novos pedidos com vídeo para planejamento automático;
`proposed-video-output-v1` deriva do contrato produtivo da Fatia A, com validação
automática antes da implementação, sem alegar aprovação humana ou inserir
checkpoints. Captura quality-v2, staging-v1 e `business-video-reel-v2`. Evidência
usa o frame inicial (0ms), já amostrado pelo preparador, sem inventar observações
sobre o vídeo. `previous` não é promovido: v15 sem repertório, v15/v2 e v14/v1
mantêm os snapshots. Photo e seus contratos/polish v1–v6 permanecem intactos.

Validação: 192 unitários do recorte e oito integrações locais em PostgreSQL
`_test`, roles restritas e fornecedores simulados. 100% de linhas/branches em
motion_skills, motion_repertoire, motion_video_reel e motion_video_requests
(178 statements/78 branches); motion_generation também atingiu 100% na suíte
ampliada. Todas as linhas/ramificações alteradas em schema/capture/wiring foram
exercitadas, sem exclusões. Isso não significa 100% dos módulos legados inteiros:
a medição ampliada com lab/context/schema ficou em 85,79%. Suíte ampliada:
1746 aprovados e 20 falhas, idênticas às reproduzidas no índice anterior isolado
(1737 aprovados). `make ci` bloqueado nos mesmos 66 lints preexistentes;
CI integral/cobertura global continuam pendentes. Ruff/formato do recorte passam.
181 arquivos históricos (assets e validador vídeo) comparados: bytes intactos.

Sem afrouxar validate_video_reel, DOM ou LAYOUT_REQUIRED; sem VR4–VR6/Fatia B,
chamada paga, reload ou novo MP4. Aceite E2E continua pendente de captura
explicitamente autorizada e revisão do titular.

## Decisões de compatibilidade

A guarda conta todos os VIDEO no DOM, inclusive ocultos. A v16 exige exatamente
um VIDEO por seek, associado ao ID da cena ativa; os demais ficam fora do DOM.
Repetição em elements não autoriza vários vídeos ocultos no documento. A fonte
e o tempo absoluto permanecem, inclusive em seeks reversos. A guarda não muda.

Não reescrever o manifesto v2: `load_repertoire_images` compara o descriptor
capturado aos bytes registrados, portanto mudar v2 invalidaria replays. A skill
v16 contém a orientação versionada de uso por cena do repertório v2 e é enviada
junto ao exemplo canônico existente; os testes verificam o payload real do
adapter, sem submetê-lo ao provedor.

Só marcar propose_direction no lab violaria o schema de entrada, que exigia
checkpoints ou automatic_plan exclusivo de foto. O novo contrato versionado
admite automatic_plan para produção vídeo com preparation, mantendo o caminho
humano e o contrato photo anterior. Evolução não aceita esse modo automático.
O gate de contexto continua recusando o contrato produtivo antigo com flags
automáticas, fonte ausente ou quality ausente. O orquestrador existente usa
plan/implementation; não há runner, efeito ou regra de vídeo concorrente.

Os testes reproduzem as três fronteiras documentadas (0/4320/8440/11200ms),
com conteúdo sintético: mídia ausente na cena 2, 3 ou ambas causa exatamente
MOTION_VIDEO_LAYOUT_REQUIRED. Nós locais em todas as cenas passam também pelo
validador completo de motion_plan. Integração exerce build_snapshot e captura
real de guidance com SQL restrito de anexos; contexto factual é simulado.
Isso não é prova de render nem de qualidade audiovisual.

Mypy dos seis módulos de produção tocados reportou sete erros em chamadas
já existentes de motion_context/LabMotionRequests; os mesmos locais aparecem
no checkout isolado do índice anterior. Nenhum erro novo de tipos identificado;
o resultado integral não está verde.

## Diagnóstico original (histórico)

Data: 23/11/2026. Diagnóstico read-only; **sem** mudança de código nesta nota.

## Evidência

| Campo | Valor |
| --- | --- |
| Run | `da6dd899-4fca-5e9f-a1b2-6dd8aac524d7` |
| Estado | `failed` / `MOTION_VIDEO_LAYOUT_REQUIRED` |
| Janela | 21:00:19 → 21:03:06 UTC |
| Custo | `committed_usd_micros=852688` (~US$0,85) |
| Skill no snapshot | `instagram-reel-video-v15` |
| Contrato | `motion-video-reel-v1` |
| Repertório no snapshot | **`None`** (não pinou `business-video-reel-v2`) |
| MP4 | não gerado |

Worker PID 85488 (pós-v15) estava ativo. Não é regressão de processo antigo.

## O que o modelo entregou

Plano com **3 cenas** (0–4320 / 4320–8440 / 8440–11200), `mode=cover`.

| Cena | `video_layout` | `elements` | Gate |
| --- | --- | --- | --- |
| cena1 | `cena1-video`, `cena1-logo`, texto | video + logo + texto | ok estrutural |
| cena2 | refs aos IDs da cena1 | **só** `cena2-momento` | **falha**: video/brand ausentes na cena |
| cena3 | refs cena1 + CTA | **só** textos | **falha**: video/brand ausentes |

`validate_video_reel` exige, **por cena**, que `video_element_id` e `brand_element_id` existam em `scene.elements` com `assets/source.mp4` / `assets/logo.png`. Referência cruzada a outra cena não vale.

## Bug de wiring (lab)

`LabMotionRequests.build_snapshot` monta `MotionRequest` **sem** `propose_direction`. Em `capture_motion_guidance`, isso deixa `generation_contract` ausente → sem `quality_contract` → sem `staging_contract` → **sem** default `business-video-reel-v2`. A skill v15 ainda entra via HTML; o **exemplo canônico / rules do repertório v2 não**.

Isso explica `repertoire=None` no snapshot deste run e enfraquece o reforço VR3 anterior no caminho lab.

## Decisão / escopo

- **Não** afrouxar `MOTION_VIDEO_LAYOUT_REQUIRED` / DOM guard.
- **Não** Fatia B (VR4–VR6), photo polish, captura paga sem OK.
- Corrigir **duas** frentes na mesma fatia:
  1. **Orientação:** skill (novo pin se mudar bytes) + repertório: cada cena declara de novo VIDEO+logo nos `elements`; proibir IDs de mídia só “herdados”; se multi-cena, repetir nós ou preferir uma cena contínua no soft briefing.
  2. **Wiring lab:** ensaios lab com `source_asset_id` devem receber staging + `business-video-reel-v2` (e quality/generation coerentes com capturas vídeo Fatia A), sem quebrar replay de snapshots antigos.
- Testes: anti-padrão multi-cena do run `da6dd899…`; lab snapshot com repertoire v2; replay v15/v2 e v14/v1 intactos onde cabível.
- Nova captura só com autorização do titular.

## Prompt para o próximo chat / outra IA

```
Leia AGENTS.md e o topo de docs/PROJECT.md, docs/SDD.md,
docs/phases/BL04-context-and-ai-production.md,
docs/design/motion-video-reel-v1-slice-a.md,
docs/design/motion-video-reel-v1-kinetic-text-gate-2026-11-23.md e
docs/design/motion-video-reel-v1-layout-per-scene-2026-11-23.md.

Contexto: após skill v15, run da6dd899… falhou com MOTION_VIDEO_LAYOUT_REQUIRED.
Skill v15 + motion-video-reel-v1 ativos; repertoire=None no snapshot lab.
Plano com 3 cenas: só cena1 tem video+logo nos elements; cena2/cena3
referenciam cena1-video/cena1-logo sem declará-los → gate por cena recusa.

Implemente correção de orientação + wiring lab. NÃO afrouxar
validate_video_reel / DOM / LAYOUT_REQUIRED. NÃO Fatia B / VR4–VR6.
NÃO editar polish photo v1–v6. NÃO chamada paga sem eu autorizar depois.

1) Skill versionada nova (pin) + repertório video: cada cena deve incluir nos
   elements o VIDEO assets/source.mp4 e o IMG assets/logo.png referenciados
   por video_layout; proibir layout que aponte IDs de outra cena; briefing soft
   pode usar uma cena contínua; se multi-cena, repetir nós de mídia por cena.
   Manter fronteiras VR3 (enter/exit, sem hold fantasma).
2) Corrigir LabMotionRequests / capture para lab com source_asset_id pinarem
   staging + business-video-reel-v2 (quality/generation conforme contrato Fatia A),
   preservando snapshots previous/replay.
3) Testes: topologia da6dd899 (multi-cena sem mídia nas cenas 2+) →
   MOTION_VIDEO_LAYOUT_REQUIRED; plano multi-cena válido com video+logo por cena
   passa; snapshot lab novo inclui repertoire id business-video-reel-v2;
   regressão v14/v1 e photo intacta.
4) PROJECT/SDD/BL04/CHANGELOG/DECISIONS + este design doc na mesma mudança.
5) Cobertura 100% no recorte; sem exclusões cosméticas; não declare E2E sem MP4
   autorizado e minha revisão.
```
