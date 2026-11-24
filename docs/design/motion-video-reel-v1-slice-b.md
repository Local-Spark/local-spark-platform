# Video-reel v1 — Fatia B (VR4–VR5; VR6 se biblioteca permitir)

## 24/11/2026 — autorização após rejeição criativa do primeiro MP4 Fatia A

Titular rejeitou `versao-1 (15).mp4`
(`f446d636d8ad24388c00603478f34153698ed195dc0ad2aa81962cda008550e9`),
run `86990c48-457f-51e8-b3f8-dc9d078ac3c4`. Review automática `adequate`;
revisão humana: peça fraca. Gravação integral full-bleed + três textos com
scrim preto + logo; sem EDL, sem motion no vídeo, sem grafismos planejados,
sem uso de outros materiais do acervo, sem trilha/SFX. Skill v19 / repertório
v2 / scene-visibility-v1 / guarda Fatia A cumpridos — **gate ≠ qualidade**.

Ordem vigente desde
[gaps](motion-ensaio-cafe-aurora-video-reel-v1-gaps-2026-11-23.md): Fatia A
(VR1–VR3) → uma captura → Fatia B. Fatia A está **tecnicamente** no ar e não
deve ser desfeita. Fatia B é a fatia autorizada agora para subir a qualidade.

## Escopo autorizado

Preservar Temporal, HTML/Chromium/FFmpeg, uma gravação ≤60s/50MiB, briefing
soft (pausa aconchegante, sem hard-sell), photo-reel Café congelado, pins e
replay Fatia A (cover, logo kit, tipografia cinética, texto puro, scrim
estável, scene-visibility, diagnóstico do renderer).

| ID | Objetivo | Critério mínimo |
| --- | --- | --- |
| **VR4** | EDL / remonte com função | ≥2 segmentos com papel distinto (ex.: gancho → preparo/detalhe → convite). Cortes ou dissolves curtos entre segmentos; não um único play-through da fonte com textos trocados. Respeitar fala quando houver (não cortar no meio da palavra sem regra). |
| **VR5** | Motion e grafismo com intenção | Pelo menos um de: (a) pan/scale/crop intencional da gravação ainda em cover 9:16; (b) grafismos **declarados no plano** e permitidos por guarda versionada (linhas/formas mínimas alinhadas ao tom soft); (c) transição perceptível entre segmentos. Rejeitar plano em que só a mídia-fonte “se move sozinha” e a UI/texto fazem todo o trabalho. Materiais do inventário/acervo autorizado (fotos do kit/anexos) podem entrar como apoio se estiverem no pedido — não inventar assets. |
| **VR6** | Mix (condicional) | Reutilizar biblioteca já existente (`motion_music` / sound library / photo-music), com duck sob narração quando houver fala. Se não houver trilha elegível: estado explícito de indisponível — não inventar música nem compra nova sem autorização. SFX só da biblioteca licenciada, sobrios. Se a extensão de áudio bloquear a fatia visual, entregar VR4–VR5 primeiro e documentar VR6 pendente; não atrasar B só por áudio. |

## O que mudar (direção técnica)

1. **Contrato / skill / repertório versionados** para video-reel Fatia B (novos
   pins). Snapshots Fatia A e photo permanecem reproduzíveis; não editar bytes
   de polish photo v1–v6 nem afrouxar silenciosamente a guarda v1 antiga.
2. **Plano:** modelar segmentos EDL (in/out na fonte, função, transição) e
   motion permitido no elemento de vídeo/crop; grafismos só com role/ids
   declarados e regras DOM novas — não reabrir `UNPLANNED_OVERLAY` para lixo
   decorativo livre.
3. **Guarda DOM / validate:** versionar (ex. video-reel-v2 ou extensão pinada)
   para aceitar o que B autoriza e continuar recusando cartaz/janela, label
   morto, texto com filhos, scrim fade indevido, overlays não planejados.
   Scene-visibility continua para textos/scrims por cena/segmento ativo.
4. **Orientação:** skill + repertório devem exigir progressão editorial e
   motion; exemplos canônicos que passem nos novos gates. Prompt sozinho não
   basta — a Fatia A mostrou isso.
5. **Testes** sintéticos (sem mídia do cliente): anti-padrões do run
   `86990c48…` (play-through único + só texto) devem falhar no plano/DOM;
   casos mínimos VR4/VR5 devem passar. Cobertura 100% no recorte; integrações
   `_test`. Docs PROJECT/SDD/BL04/CHANGELOG/DECISIONS na mesma mudança.

## Fora desta fatia

- Desfazer ou afrouxar VR1–VR3 / scene-visibility / texto puro para “ficar bonito”.
- Remotion, TTS, avatar, HeyGen, Meta publish.
- Reabrir polish photo-reel Café.
- Compra/download de música nova ou chamada paga sem autorização do titular.
- Declarar aceite E2E sem novo MP4 autorizado e revisão humana.

## Aceite audiovisual (após implementação)

Uma captura autorizada: full-bleed preservado; logo kit; tipografia legível;
progressão editorial perceptível (cortes/segmentos); motion ou grafismo
planejado alinhado ao tom soft; áudio com trilha/duck ou motivo explícito de
indisponibilidade. Revisão do titular — gates sozinhos não fecham o aceite.

## Prompt para o chat de implementação

```
Leia AGENTS.md e o topo de docs/PROJECT.md, docs/SDD.md,
docs/phases/BL04-context-and-ai-production.md,
docs/design/motion-ensaio-cafe-aurora-video-reel-v1-gaps-2026-11-23.md,
docs/design/motion-video-reel-v1-slice-a.md e
docs/design/motion-video-reel-v1-slice-b.md
(refs: docs/evals/analise-41-referencias-motion-2026-11-12.md,
docs/evals/analise-video-maestros-WuzMxEKJHkQ-2026-11-11.md;
photo-reel congelado).

Contexto: Fatia A (VR1–VR3 + scene-visibility + v19) está ativa e gerou MP4.
Titular rejeitou versao-1 (15).mp4 hash
f446d636d8ad24388c00603478f34153698ed195dc0ad2aa81962cda008550e9
(run 86990c48…): gravação integral + textos/scrim, sem EDL/motion/grafismo/
acervo/trilha. Review automática adequate ≠ aceite humano. Gate A não deve
ser desfeito; o teto criativo atual é o problema.

Briefing soft a preservar: reel aconchegante de pausa a partir da gravação,
frases curtas, identidade do kit, sem hard-sell.

Implemente a Fatia B do video-reel: VR4 e VR5 obrigatórios; VR6 somente
reutilizando biblioteca de áudio já existente (duck sob fala) ou estado
explícito de indisponível — sem música inventada nem compra nova.
NÃO afrouxar VR1–VR3 / texto puro / scrim estável / scene-visibility.
NÃO editar bytes/replay do polish photo v1–v6.
NÃO Remotion/TTS/avatar. NÃO reabrir photo-reel Café.
NÃO chamada paga / captura do cliente sem eu autorizar depois.

1) VR4: EDL com ≥2 segmentos com função; cortes/dissolves curtos; anti-padrão
   play-through único da fonte só com troca de texto deve falhar no gate.
2) VR5: motion intencional no crop/cover (pan/scale) e/ou grafismos mínimos
   DECLARADOS no plano com guarda versionada; transição perceptível entre
   segmentos; materiais do inventário autorizado podem apoiar — sem inventar.
3) Versionar contrato/skill/repertório/guarda; pins novos; snapshots A intactos.
4) Testes sintéticos + 100% cobertura no recorte; PROJECT/SDD/BL04/CHANGELOG/
   DECISIONS + slice-b na mesma mudança.
5) Se VR6 bloquear, entregue VR4–VR5 e documente VR6 pendente.

Não declare aceite E2E sem novo MP4 autorizado e minha revisão.
Não rode chamada paga sem eu autorizar.
```
