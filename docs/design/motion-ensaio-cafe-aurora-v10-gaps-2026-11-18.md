# Ensaio Café Aurora v10 — gaps e próxima fatia — 18/11/2026

## Ensaio v11 — próximo backlog noutro doc

Após T1–T3/`polish-v3`, o ensaio `versao-1 (10).mp4` (regressão vs `cefe9071`)
e o backlog U1–U4 estão em
[motion-ensaio-cafe-aurora-v11-gaps-2026-11-23.md](motion-ensaio-cafe-aurora-v11-gaps-2026-11-23.md).
Este documento permanece o diagnóstico v10 + histórico T1–T4.

## Atualização — T1–T3 implementados, aceite audiovisual pendente

Autorização posterior ao diagnóstico: suplemento `motion-photo-polish-v1`
para novas capturas, sem alterar contratos anteriores/replay. T1 exige revisão
do inventário e diversidade/ambiente elegível; T2 protege todas as frases;
T3 remove adornos de layout. Regras, decisões, testes e limites registrados em
PROJECT/SDD/BL04/DECISIONS/CHANGELOG. T4 segue fora do escopo. Sem chamada paga
ou novo MP4; o diagnóstico original abaixo permanece como histórico.

Estado: **diagnóstico e backlog documentados** a partir de
`/Users/israelsilva/Downloads/Cafe-Aurora-render-recuperado-cefe9071.mp4`
(hash `8cba7ed7beabbb68da7e2b56b2beda49ccebb24b6f5991c6ba25145223af6509`,
idêntico ao objeto de upload do run `cefe9071-7fc5-553a-9de4-709fb802101e`).
Não autoriza, por si, implementação, chamada paga, A5b nem alteração de
Music/renderer. Destinado a um próximo chat/modelo.

Referências: S1–S4 em
[motion-ensaio-cafe-aurora-v9-gaps-2026-11-18.md](motion-ensaio-cafe-aurora-v9-gaps-2026-11-18.md);
R1–R3/guarda v2 em
[motion-ensaio-cafe-aurora-v8-gaps-2026-11-18.md](motion-ensaio-cafe-aurora-v8-gaps-2026-11-18.md);
Maestros [WuzMxEKJHkQ](../evals/analise-video-maestros-WuzMxEKJHkQ-2026-11-11.md).

## Contexto imediato

- Briefing do titular (inalterado desde o início): *“Quero um reel mostrando o
  clima do Café Aurora. Uma coisa aconchegante, com movimento suave e frases
  curtinhas sobre fazer uma pausa no dia. Pode usar nossas fotos.”*
- Esse texto puxa lifestyle soft, não propaganda dura das refs. O teto realista
  sob o briefing é **~70–75%** “vs o pedido”; vs propaganda “incrível” das
  ~40 refs o alvo continua mais baixo.
- Run falhou com `MOTION_EXECUTION_FAILED` por **timeout ao gravar evidências**
  após render/upload ok (persistência corrigida noutro chat). O MP4 existe e
  foi recuperado; **não** é versão/aceite no produto. Snapshot tinha S1–S3 e
  `motion-photo-readability-v1` (guarda v3).
- Antes disso: falso positivo CTA multi-shadow (readability-v1) e S1–S3
  implementados; Music/mix (S4) intactos.

## Evidência do ensaio v10

Arquivo: 15,0 s · 720×1280 · H.264 + AAC · ~1,20 Mbps (~2,26 MB).
Loudness ~**−31,5 LUFS** (inalterado).

Amostragem a 5 fps (cinza 90×160), mesmo critério dos ensaios anteriores:

| Medida | v9 | **v10 (cefe9071)** |
| --- | --- | --- |
| Quase estático (diff &lt; 2) | ~38% | **0%** |
| Diff médio | ~4,4 | **~5,3** |
| Holds ≥0,8 s | ~2,2 / 2,8 s | **nenhum** |
| Picos (cortes) | ~3,6–3,8 / 7,6 / 11,2–11,4 s | **~3,6–3,8 / 7,2–7,4 / 11,6–11,8 s** |

Leitura humana / frames-chave: **cover full-bleed** em todos os beats
amostrados (sem Stories janela+blur no miolo). Alternância de duas fotos
premium (espresso xícara branca/pires vermelho; latte cerâmica marrom). Fecho
com logo AURORA transparente + CTA “Conheça nosso cardápio”, **sem** placa
creme e **sem** “Imagens ilustrativas.”. Frases: “Abra um espaço.” /
“Para um café.” / “E um instante seu.”. Estimativa vs propaganda “incrível”
das refs: **~60–65%** (v9 ~55%). Vs o próprio briefing soft: **~70–75%**.

### Storyboard observado

1. **~0–3,5 s** — espresso top-down cover; “Abra um espaço.” (+ acentos).
2. **~4–7 s** — latte cover; “Para um café.” (+ linha/acento).
3. **~8–11,5 s** — espresso de novo; “E um instante seu.”
4. **~12–15 s** — latte + logo AURORA overlay + CTA cardápio; KB contínuo
   (sem hold morto de ~3 s do v9).

### Evolução vs gaps

| Melhorou | Ainda falha / incompleto |
| --- | --- |
| S1: miolo cover (Stories longo sumiu) | Variedade fotográfica baixa (~2 assets) |
| S2: 0% quase-estático; fecho vivo | Contraste tipográfico frágil em madeira clara |
| S3: sem Belize/Mackbear/watermark óbvios | Acentos laranja (cantoneiras/linhas) parecem residual |
| Sem placa creme / sem disclaimer stock | Frases curtas ok, “pausa no dia” só implícita |
| Guarda v3 + persistência pós-upload (infra) | Mix −31,5 LUFS (S4) |
| Alinhamento ao briefing aconchegante/suave | Pouco “clima do salão” (ambiente/pessoas/balcão) |

Diagnóstico: S1–S3 **cumpriram** o que o ensaio v9 pediu no audiovisual.
Próxima fatia não é reabrir cover/energia básica; é **seleção de materiais de
ambiente**, **legibilidade tipográfica** e **limpeza gráfica**, sem virar
hard-sell contra o briefing.

## % vs referências

| Dimensão | ~% vs propaganda | ~% vs briefing soft |
| --- | --- | --- |
| Foto / mood | 75–80 | 80 |
| Cover 9:16 | 75–80 | 80 |
| Motion / energia suave | 55–60 | 75–80 |
| Marca / fecho | 70–75 | 75 |
| Mix | 20 | 25 |
| Tipografia / contraste | 40–45 | 55 |
| Variedade / clima do lugar | 40–45 | 50 |
| **Síntese** | **~60–65** | **~70–75** |

## Backlog priorizado (próxima implementação — T1–T4)

### T1 — Variedade e “clima do café” (prioridade máxima)

- Exigir diversidade mínima de materiais fotográficos no plano (ex.: ≥3 assets
  distintos; preferir pelo menos um beat de **ambiente** — salão, balcão,
  mesa ampla — além de close de xícara), quando o inventário tiver opções.
- Manter S3: sem marca de terceiros legível; crop v5 prevalece.
- Objetivo: o reel “mostrar o clima”, não só duas stills de produto em loop.

### T2 — Legibilidade tipográfica sobre foto clara

- Texto branco sobre madeira/highlight precisa de scrim **local** suficiente,
  sombra preta opaca adequada (v3 já aceita multi-shadow) ou reposicionamento
  sobre região escura — sem faixa full-width proibida por S1.
- Conferir no DOM/plano que o texto permanece legível; não relaxar CTA ≥1500 ms
  nem readability-v1.

### T3 — Limpeza de acentos gráficos residuais

- Rejeitar ou despriorizar cantoneiras/“crop marks”/linhas-guia laranja que
  parecem UI de layout, não editorial de marca.
- Preferir tipografia + scrim; se houver gráfico, deve ser intencional e da marca.

### T4 — Mix (opcional, só com OK)

- S4 adiado: subir presença da trilha alguns dB; sem mudar tarifa/credencial
  Music sem autorização explícita.

### Fora desta onda

- Trocar o briefing por propaganda dura / Maestros (só se o titular pedir).
- Troca de renderer / Remotion / TTS / avatar.
- Reescrever snapshots / intent v10 / guarda v2–v3 bytes.
- Aceite E2E sem novo pedido autorizado + MP4 (o recuperado não conta como
  versão aprovada no fluxo).
- A5b sem autorização explícita.
- Re-render só para “salvar” o arquivo já existente.

## Prompt sugerido para o próximo chat

```
Leia AGENTS.md, o topo de docs/PROJECT.md, docs/SDD.md,
docs/phases/BL04-context-and-ai-production.md e
docs/design/motion-ensaio-cafe-aurora-v10-gaps-2026-11-18.md
(contexto S1–S3 em motion-ensaio-cafe-aurora-v9-gaps-2026-11-18.md).

Briefing do titular (preservar o tom; não virar hard-sell):
"Quero um reel mostrando o clima do Café Aurora. Uma coisa aconchegante,
com movimento suave e frases curtinhas sobre fazer uma pausa no dia.
Pode usar nossas fotos."

Implemente a próxima fatia (T1–T3; T4 mix só se eu autorizar).
PRIORIDADE: clima/variedade + legibilidade + limpeza gráfica.
S1–S3, intent v10, guarda v2/v3 (readability), finish-v1 e persistência
pós-upload já ok — não reabrir nem reverter.

1) T1: diversidade fotográfica / beat de ambiente quando houver material;
   evitar loop de só 2 closes de xícara; manter S3 e crop v5.
2) T2: texto legível sobre foto clara (scrim local / sombra / posição),
   sem faixa full-width; preservar CTA ≥1500 ms e readability-v1.
3) T3: sem cantoneiras/crop-marks/acentos que pareçam UI residual.

Preservar: crop v5, gates M3/N2/O2/Q2/R1–R3/S1–S3, intent v10, guarda v2/v3,
finish-v1, snapshots históricos, vídeo, Music (salvo T4). Sem TTS/avatar/
renderer novo.

Evidência: Cafe-Aurora-render-recuperado-cefe9071.mp4 — ~60–65% vs propaganda,
~70–75% vs briefing; cover+energia ok; pouca variedade; contraste tipográfico;
mix −31,5 LUFS. Run falhou só na persistência de evidências (já corrigida).

Testes + PROJECT/SDD/BL04/CHANGELOG/DECISIONS na mesma mudança.
Não declare aceite E2E sem novo MP4 autorizado e minha revisão.
Não rode chamada paga sem eu autorizar.
```

## Aceite da próxima fatia

- Novo MP4 autorizado: ≥3 materiais distintos e/ou beat de ambiente perceptível.
- Frases curtas legíveis sobre a foto (sem Stories/faixa full-width).
- Sem acentos tipo crop-mark; logo/CTA limpos; cover e energia S1–S2 mantidos.
- Mix melhor se T4 incluído.
- Sem upgrade silencioso de snapshots antigos; sem reaproveitar o run failed
  como versão aprovada.
