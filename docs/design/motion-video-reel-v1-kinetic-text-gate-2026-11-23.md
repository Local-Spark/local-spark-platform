# Video-reel v1 — falha `MOTION_VIDEO_KINETIC_TEXT_REQUIRED` pós-Fatia A

## 24/11/2026 — execução DOM após v17

A falha seguinte de render e a correção de orientação v18 estão em
[DOM/overlays](motion-video-reel-v1-dom-overlay-2026-11-24.md).
Gates e pins históricos preservados; aceite audiovisual continua pendente.

## 24/11/2026 — video-reel v17: transform próprio em cada texto

Run `028a10c5…` confirmou v16/v2 e wiring automático ativos, mas os dois textos
da cena final usaram enter → hold → exit, sem transform. Deslocamentos de
entrada/saída e das hastes não substituem essa fase no próprio texto.
Nova skill pinada `instagram-reel-video-v17` explicita a obrigação para cada
text_element_id, inclusive título/CTA finais, e inclui beats JSON canônicos
com enter → transform → hold → exit. Transform linear/visível desloca ≥4px;
CTA preserva hold ≥1500ms. Exemplo e plano de duas cenas passam pelo gate real.

Validação: 199 unitários e oito integrações em PostgreSQL dedicado `_test`,
roles restritas/fornecedores simulados; 100% linhas/branches nos serviços
motion_skills, motion_repertoire, motion_video_reel e motion_video_requests
(178 statements/78 branches), sem exclusões. Regressão recusa falta de transform
em cada texto isolado e nos dois juntos, mesmo com grafismo animado e enter/exit
com deslocamento. Payload real transmite a orientação; replay v16/v2 preservado.
182 arquivos históricos de assets/validador conferidos byte a byte: intactos.
Ruff do recorte passou; `make ci` permanece bloqueado nos 66 lints preexistentes.
CI integral e cobertura global 100% continuam pendentes.

Sem alteração do gate/DOM, repertório v2, contratos de captura ou photo polish.
Sem VR4–VR6, nova chamada paga, alteração do run, reload ou MP4. A nova skill
vale para novas capturas com código atualizado; replay não promove v16 para v17.
Aceite audiovisual depende de execução autorizada e revisão do titular.

## 23/11/2026 — reforço de orientação VR3, sem alteração do gate

Novas capturas usam `instagram-reel-video-v15` e, no staging padrão, o
`business-video-reel-v2` (revisão do v1). Pins de skill, manifesto e conteúdo
foram adicionados; v14/v1 permanecem carregáveis para replay. Repertório
explicitamente selecionado continua respeitado. As regras transmitidas exigem
que cada texto cubra a cena: primeiro beat enter em scene.start_ms, último
exit em scene.end_ms, continuidade, nenhum hold opacity=0 e invisibilidade
somente via enter/exit. CTA final com hold estável visível ≥1500ms entre ambos.
Exemplo canônico pinado no repertório é validado pelo gate existente.

`VIDEO_REEL_CONTRACT`, validate_video_reel e DOM guard permanecem intactos;
não há mudança nos bytes/replay photo polish v1–v6. Testes sintéticos reproduzem
a topologia de pausa/tempo/cta do run `853327f8…`, isolada e conjuntamente,
sem usar conteúdo do cliente nem alegar seus tempos intermediários exatos.
Validação: 118 unitários aprovados; 100% de linhas e branches nos serviços
motion_skills, motion_repertoire e motion_video_reel (174 statements/78 branches),
sem exclusões novas. Três integrações aprovadas em PostgreSQL dedicado `_test`,
roles restritas e fornecedores simulados. Ruff/formato do recorte e mypy desses
três serviços passaram (cache temporário limpo). Os 175 assets existentes,
contrato, validador e DOM guard foram comparados com o índice inicial: bytes
intactos. A suíte adicional contexto/photo teve 52 aprovados e 18 falhas;
as mesmas 18 falhas foram reproduzidas em checkout isolado do índice anterior.
`make ci` executado, bloqueado nos 66 lints preexistentes. CI integral e
cobertura global 100% continuam pendentes; não houve correções fora do escopo.

Sem VR4–VR6/Fatia B, chamada paga, captura, reload, MP4 ou aceite E2E.
Próximo passo depende de autorização para nova captura e revisão do titular.

O diagnóstico e os pins abaixo documentam o estado anterior ao reforço.

Data: 23/11/2026. Diagnóstico read-only; **sem** mudança de código nesta nota.

## Evidência

| Campo | Valor |
| --- | --- |
| Run | `853327f8-b3d3-5d6b-ad86-11c574de9dce` |
| Estado | `failed` / `MOTION_VIDEO_KINETIC_TEXT_REQUIRED` |
| Janela | 20:23:13 → 20:26:08 UTC |
| Custo | `committed_usd_micros=852688` (~US$0,85) no generate OpenAI |
| Skill | `instagram-reel-video-v14` |
| Contrato | `motion-video-reel-v1` (presente no snapshot) |
| MP4 | **não** gerado (recusa no validate do plano pós-generate) |

Contexto: captura anterior `(14)` / `01a7058c…` usou worker antigo (`instagram-reel-v13`, sem contrato) e renderizou cartaz creme. Worker recarregado; este run **prova** que a Fatia A está ativa.

## O que o modelo entregou (bom vs ruim)

**Alinhado à Fatia A (progresso):**

- `video_layout.mode=cover`
- `video_element_id` → `assets/source.mp4`
- `brand_element_id` → IMG `assets/logo.png` (não label “Café Aurora”)
- textos com `enter` / `transform` / `exit` e CTA com hold ≥1500 ms no miolo

**Rejeitado pelo gate VR3** (`validate_video_reel` em `app/services/motion_video_reel.py`):

Para **cada** id em `text_element_ids` o contrato exige:

1. `video_element_id` ∈ `related_element_ids`
2. fases `{enter, transform, exit}` presentes
3. `beats[0].phase == "enter"` e `beats[0].start_ms == scene.start_ms`
4. `beats[-1].phase == "exit"` e `beats[-1].end_ms == scene.end_ms`
5. beats contíguos no tempo; `hold` só com opacity 1 estável; `transform` desloca ≥4 px; curva linear

No plano deste run (1 cena, 0–11200 ms):

| Elemento | Violação |
| --- | --- |
| `cena1-pausa` | Após `exit` há `hold` final opacity 0 → último beat ≠ `exit` |
| `cena1-tempo` | Começa com `hold` opacity 0 → primeiro beat ≠ `enter` |
| `cena1-cta` | Idem: `hold` inicial opacity 0 antes do `enter` |

Padrão do modelo: “holds fantasmas” nas pontas para ocupar o timeline em vez de `enter` no `start_ms` da cena e `exit` no `end_ms`.

## Decisão / escopo da correção

- **Não** afrouxar o gate VR3 silenciosamente (não aceitar hold fantasma nas pontas).
- **Não** implementar Fatia B (VR4–VR6) nesta fatia.
- **Não** reabrir photo-reel Café / polish v1–v6.
- Corrigir **orientação do modelo** (skill + repertório + regras/schema transmitidos) e, se útil, **mensagens/testes** que documentem o anti-padrão; opcional: exemplo canônico no repertório `business-video-reel-v1`.
- Nova captura paga **só** com autorização explícita do titular após o patch.

## Prompt para o próximo chat / outra IA

```
Leia AGENTS.md e o topo de docs/PROJECT.md, docs/SDD.md,
docs/phases/BL04-context-and-ai-production.md,
docs/design/motion-video-reel-v1-slice-a.md e
docs/design/motion-video-reel-v1-kinetic-text-gate-2026-11-23.md.

Contexto: Fatia A (VR1–VR3) está ativa. Run 853327f8… falhou com
MOTION_VIDEO_KINETIC_TEXT_REQUIRED após generate (skill instagram-reel-video-v14,
contrato motion-video-reel-v1). Layout cover + logo kit ok; textos usaram
hold opacity-0 nas pontas do timeline em vez de enter no scene.start_ms e
exit no scene.end_ms (ver tabela no doc).

Implemente SOMENTE o reforço para o modelo cumprir o gate VR3 existente.
NÃO afrouxar validate_video_reel / DOM guard para aceitar hold fantasma.
NÃO implementar VR4–VR6 / Fatia B. NÃO editar bytes/replay do polish photo v1–v6.
NÃO chamada paga / captura do cliente sem eu autorizar depois.

1) Atualizar skill versionada (novo pin se o conteúdo mudar) e repertório
   business-video-reel-v1 / regras transmitidas: cada text_element_id deve
   cobrir [scene.start_ms, scene.end_ms] com beats[0]=enter e beats[-1]=exit;
   proibir hold com opacity 0; invisibilidade só via enter/exit; CTA final
   mantém hold estável ≥1500ms entre enter e exit.
2) Testes unitários que reproduzem o anti-padrão do run 853327f8 (pausa/tempo/cta
   com holds fantasmas) e assert MOTION_VIDEO_KINETIC_TEXT_REQUIRED; mais um
   plano mínimo válido que passa VR3.
3) PROJECT/SDD/BL04/CHANGELOG/DECISIONS + este design doc na mesma mudança.
4) make ci / cobertura 100% no recorte tocado; sem exclusões cosméticas.

Não declare aceite E2E sem novo MP4 autorizado e minha revisão.
```

## Fora desta nota

- Supervisor/compose do worker lab (fragilidade local SIGHUP) — trilha aparte.
- Aceite audiovisual E2E / Fatia B.
- Falha seguinte `MOTION_VIDEO_LAYOUT_REQUIRED` (multi-cena / repertório lab):
  [layout-per-scene](motion-video-reel-v1-layout-per-scene-2026-11-23.md).
