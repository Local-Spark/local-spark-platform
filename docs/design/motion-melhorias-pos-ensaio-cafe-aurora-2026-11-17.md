# Melhorias pós-ensaio Café Aurora — 17/11/2026

## Ensaio v3 — próximo backlog noutro doc

Ensaio `versao-1 (3).mp4` após P1–P3 + staging v2: melhora parcial; gaps de logo,
ritmo/fecho, bleed e mix em
[motion-ensaio-cafe-aurora-v3-gaps-2026-11-17.md](motion-ensaio-cafe-aurora-v3-gaps-2026-11-17.md).
Este documento permanece o baseline v2 + histórico P1–P3.

## Revisão de consistência antes do ensaio

Scaffolding P1–P3 não garante correção visual. O conflito remanescente de staging
foi removido para novas capturas em `motion-staging-photo-v2`; regras photo v2
pedem KB contínuo também no executor. Contratos antigos continuam aceitos e
imutáveis, inclusive os snapshots P1–P3 anteriores a esta correção. Usar nova
captura no ensaio. Testes conferem payload completo, schema e replay; não
comprovam que o modelo chamará o helper nem acabamento comercial. Nenhum MP4
novo ou aceite humano nesta correção. Validação detalhada em PROJECT/CHANGELOG.


## Atualização — P1–P3 implementados; aceite audiovisual pendente

O pedido posterior do titular autorizou esta fatia de código e testes.
Novas capturas photo usam intent v2, skill `instagram-reel-photo-v14` derivada
localmente de v13 e repertório `business-reel-v6` derivado de v5. Os originais
continuam pinados para replay. Exemplo executável local: `makePhotoReelMotion`,
com Ken Burns contínuo, stagger/saída antes do handoff e scale-down/assentamento.
Integração exige adaptação e chamada explícita em scene_init/seek, sem novo runner.
As janelas do exemplo são argumentos do plano, não um storyboard fixo de produto.
A margem inicial 1,04 acomoda pan de até 1%; scale chega a 1,12. O foco/crop deve
ser escolhido pela composição para preservar o protagonista da fotografia.

Testes: 135 unitários, quatro Node e três PostgreSQL passaram; intent com 100%
de linhas/branches. CI global bloqueado por lint e fixtures de contexto anteriores
(ver PROJECT/CHANGELOG). Sem novo MP4, chamada paga ou aceite E2E. P4/P5 e A5b
não foram implementados. O diagnóstico e as medições abaixo são o baseline,
não resultado desta implementação.


Estado: **diagnóstico e backlog documentados** a partir do MP4
`versao-1 (2).mp4` (Downloads). Não autoriza, por si, implementação, chamada
paga, A5b nem alteração de skill/repertório. Destinado a um próximo chat/modelo.

Referências: plano A0–A5
[motion-plano-reels-15s-foto-2026-11-17.md](motion-plano-reels-15s-foto-2026-11-17.md);
peça anterior muda `versao-1.mp4`; checkpoint de plano do lab (díptico/pausa);
[análise Maestros WuzMxEKJHkQ](../evals/analise-video-maestros-WuzMxEKJHkQ-2026-11-11.md).

## Evidência do ensaio

Arquivo: 15,0 s · 720×1280 · H.264 + **AAC stereo** (trilha presente).
Loudness aproximado ~−31,6 LUFS (trilha baixa).

Amostragem a 5 fps (cinza 90×160):

| Medida | Valor |
| --- | --- |
| Pares quase estáticos (diff &lt; 2) | **~89%** (66/74) |
| Holds longos | **~2,8–7,6 s (~4,8 s)** e **~8,2–14,8 s (~6,6 s)** |
| Picos de movimento (diff &gt; 10) | ~2,2 s e ~7,8 s (trocas) |

Leitura humana: música melhorou muito vs silêncio; visual ainda é **post/editorial
estático** — foto em janela + tipografia serif no creme; transições entre imagens
aceitáveis; **falta zoom/pan contínuo, tipografia cinética e micro-movimento nos
holds**. Não atinge peça de propaganda / motion de referência.

## Causa provável no processo

1. Plano A2 aprovado **autorizou holds longos** de leitura/contemplação.
2. Contrato A3 (`motion-photo-intent-v1`) **não obriga** MotionV1/scale/Ken Burns;
   o modelo escolheu enter → hold → exit mínimo.
3. A4 só **informa** estagnação; A5b (gates) ainda não existe e **não** deve
   ligar sem calibração.
4. Skill/repertório estão no prompt/snapshot, mas **não executam** helpers
   (`type-portal`, `depth-handoff`) sozinhos — skill ≠ agente com ferramentas.

## Backlog priorizado (próxima implementação)

### P1 — Vida nos holds (maior impacto)

- Ken Burns **contínuo** nas fotos durante leitura (scale suave ~1,00→1,06–1,12
  + pan leve), sem fingir filmagem nem animar objetos dentro da foto.
- Regra de produto sugerida: **nenhum trecho &gt; ~2 s sem mudança perceptível**
  de escala, posição ou tipografia (orientação forte no plano/intent/skill
  photo; ainda não gate A5b automático).

### P2 — Tipografia cinética

- Entrada/saída com stagger ou hierarquia temporal; não só opacity fade + hold.
- Saída antes do handoff; tempo de leitura sem congelar a foto.

### P3 — Escala na passagem / handoff

- Além de slide/afastamento: acento com scale; push/scale-down na entrega à marca.
- Opcional: máscara/clip/sombra que acompanhe o gesto (repertório v5 como
  **exemplo a chamar** no `scene_init`, não template fixo).

### P4 — Ritmo do storyboard em 15 s

- Reduzir holds de 5–6 s; estrutura alvo sugerida:
  gancho → acento+frase → 2º material com KB → handoff → marca/CTA com
  micro-movimento.

### P5 — Mix

- Subir presença da trilha alguns dB (ainda instrumental de fundo); fades ok.

### Fora desta onda

- A5b com limiares automáticos (só após 2–3 ensaios humanos + métricas A4).
- TTS/Voice, avatar, troca de renderer/GSAP/Remotion.
- Inchar a skill com adjetivos; preferir contrato photo + exemplos repertório +
  revisão/correção delimitada.

## Skills e fontes externas — uso real

| Fonte | Papel | Usada em runtime? |
| --- | --- | --- |
| `meu-braco-direito-skills` | Origem histórica das skills editoriais | **Não ao vivo.** Snapshots pinados em `app/assets/motion_skills/` (hoje HTML reel = `instagram-reel-v13`). Mudança no outro repo **não** altera o produto até nova versão/hash. |
| `meu-braco-direito-motion-sources` | Acervo/estudo de referências/snapshots | **Não ao vivo.** Mecanismos qualificados viram repertório local (`business-reel-v5` etc.) quando versionados aqui. |
| `app/assets/motion_repertoire/business-reel-v5` | Exemplos `makeTypePortal` / `makeDepthHandoff` | **Sim, como contexto** quando `repertoire_id` está no snapshot (default com staging). **Não** se auto-injeta no `scene_init`. |
| `PHOTO_MOTION_RULES` + `motion-photo-intent-v1` | Regras photo + intenção A3 | **Sim**, no snapshot/instruções. |

Conclusão: o caminho certo é **continuar com skills/repertório pinados no
produto**, evoluindo versões locais a partir do aprendizado dos ensaios — não
esperar que o working tree dos outros repositórios “entre” sozinho na geração.

## Estamos no caminho certo vs. vídeo Maestros?

**Sim no método; ainda não no acabamento.**

Alinhado ao [WuzMxEKJHkQ](https://www.youtube.com/watch?v=WuzMxEKJHkQ):

- Cena por código + timeline + browser/FFmpeg
- Etapas (plano → implementação → render → fiscal)
- Som com função (trilha agora presente)
- Correção por evidência (lab checkpoint)

Ainda abaixo da referência:

- Poucos “gestos que explicam a ideia” contínuos (lá o objeto se transforma;
  aqui a foto quase só troca de slide)
- Tipografia/espaço pouco coreografados no hold
- Fiscal estético ainda fraco (de propósito até calibrar)
- Sem voz/avatar (fora de escopo — ok)

Não precisamos copiar Remotion/GSAP/ElevenLabs Voice para “editar como o vídeo”;
precisamos **obrigar/orientar** Ken Burns + tipografia + escala no caminho photo
já existente.

## Prompt sugerido para o próximo chat

```
Leia AGENTS.md, PROJECT/SDD/BL04 (topo) e
docs/design/motion-melhorias-pos-ensaio-cafe-aurora-2026-11-17.md.

Implemente a próxima fatia de qualidade visual photo reel (P1–P3 do doc):
Ken Burns contínuo nos holds, tipografia cinética, scale no handoff —
via contrato/intent/skill photo versionados + exemplos de repertório,
SEM A5b (gates automáticos), SEM TTS/avatar, SEM mudar tarifa Music
sem meu OK.

Evidência de partida: ensaio Café Aurora versao-1 (2).mp4 — ~89% quase
estático, holds ~4.8s e ~6.6s; música ok, motion fraco.

Testes + docs PROJECT/SDD/BL04/CHANGELOG na mesma mudança.
Não declarar aceite E2E sem novo MP4 e minha escuta/visual.
```

## Aceite da próxima fatia

- Novo MP4 photo reel com holds claramente “vivos” (KB ou equivalente).
- Nenhum trecho longo perceptivelmente congelado (critério humano + métricas A4
  informativas no trace).
- Tipografia com entrada/saída temporal; handoff com escala/gesto, não só cut.
- Trilha preservada; SFX só se justificados.
- Sem gate A5b automático nesta fatia.
