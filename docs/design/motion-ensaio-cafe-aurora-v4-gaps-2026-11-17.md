# Ensaio Café Aurora v4 — gaps e próxima fatia — 17/11/2026

## Atualização — M1–M3 implementados; aceite audiovisual pendente

O pedido posterior do titular autorizou esta fatia: novas capturas usam intent
v4, skill photo v16 e repertório default v8, com hashes pinados. Contrato/skill/
exemplo reforçam foto full-bleed, overlay e logo âncora (36% no exemplo; mínimo
orientado 28%). O plano rejeita holds contínuos >2500 ms e exige fotos/logo com
transforms distintos sem gaps do fim do handoff até end. Tempos vêm do plano;
cenas vivas podem ser mais longas. Snapshots históricos, vídeo e Music/mix
preservados; M4 adiado. Sem A5b ou gate geométrico, sem auto-injeção de helpers.

286 unitários, 10 Node e três integrações `_test` passaram; intent/validador com
100% de linhas/branches no recorte. CI global continua bloqueado por 66 erros
de lint preexistentes. Detalhes e limites em PROJECT/SDD/BL04/CHANGELOG/DECISIONS.
Sem chamada paga, novo MP4 ou aceite E2E. O diagnóstico abaixo é a evidência
anterior à implementação; a melhora perceptiva continua pendente de ensaio
autorizado e revisão do titular.

## Registro original do diagnóstico

Estado: **diagnóstico e backlog documentados** a partir de
`/Users/israelsilva/Downloads/versao-1 (4).mp4`. Não autoriza, por si,
implementação, chamada paga, A5b nem alteração de Music/renderer. Destinado a
um próximo chat/modelo.

Referências: L1–L3 e ajuste fino em
[motion-ensaio-cafe-aurora-v3-gaps-2026-11-17.md](motion-ensaio-cafe-aurora-v3-gaps-2026-11-17.md);
P1–P3 em
[motion-melhorias-pos-ensaio-cafe-aurora-2026-11-17.md](motion-melhorias-pos-ensaio-cafe-aurora-2026-11-17.md);
Maestros [WuzMxEKJHkQ](../evals/analise-video-maestros-WuzMxEKJHkQ-2026-11-11.md);
qualidade [motion-qualidade-direcao-e-gaps-2026-11-11.md](motion-qualidade-direcao-e-gaps-2026-11-11.md).

## Evidência do ensaio v4

Arquivo: 15,0 s · 720×1280 · H.264 + AAC · ~490 kbps.
Loudness ~**−31,6 LUFS** (igual aos ensaios anteriores; True Peak ~−16,3 dBTP).

Amostragem a 5 fps (cinza 90×160):

| Medida | v3 | **v4** |
| --- | --- | --- |
| Quase estático (diff &lt; 2) | ~76% | **~82%** |
| Diff médio | ~7,0 | **~3,1** |
| Holds longos | ~2,8 / 3,0 / 4,0 s | **~3,2 / 3,4 / 4,4 s** |
| Fecho 12–15 s | frio | **mean ≈ 0** |

Leitura humana (titular): ainda distante de propaganda / refs de motion no
YouTube; **única diferença clara** = logo pequena no final ao lado do nome;
**não houve retrocesso de marca**, mas a peça **não** atingiu intenção de anúncio.
Melhoria incremental de contrato ≠ salto de acabamento.

### Storyboard observado

1. **0–1 s** — cartão creme tipográfico (“Abra espaço / para uma pausa.”).
2. **~1–5 s** — foto landscape em **janela** + texto partido; meio congelado.
3. **~5–6 s** — transição (quase só aqui há energia).
4. **~6–10 s** — díptico empilhado + “Sem pressa.”; hold longo.
5. **~10–15 s** — logo PNG **miniatura** + “Café Aurora” + uma foto inset +
   headline + CTA; **fecho morto** ~4 s+.

Composição: template **editorial/cartaz** (creme, margens, fotos &lt; ~meio quadro).
L3 (full-bleed) **não** se materializou. L1 (logo no plano/HTML) **sim**, mas
como favicon, não como âncora de marca.

## Diagnóstico

1. **Contratos soft não vencem o template** — full-bleed, holds curtos e KB
   contínuo são orientação; o modelo repete cartão creme + troca de slides.
2. **Motion = corte entre cartões**, não gesto que desenvolve uma ideia (gap vs
   Maestros / ads de referência).
3. **Logo gate só garante declaração/uso mínimo** — PNG aparece; escala,
   contraste e papel de herói não são validados.
4. **Energia de movimento piorou** no v4 vs v3 (mais estático, mean menor) —
   progresso de marca, não de “peça viva”.
5. **Mix (L4) e A5b** continuam fora; trilha inaudível para sensação de anúncio.
6. Helper/repertório **não auto-injetados**; meios com diff ≈ 0 sugerem KB
   ausente ou imperceptível.

## Backlog priorizado (próxima implementação)

### M1 — Quebrar o template editorial (maior impacto visual)

- Default forte: foto dominante **full-bleed 9:16** (`object-fit: cover` + foco
  protegido) na maior parte do tempo útil.
- Desencorajar / rejeitar planos cujo material fotográfico fique em janela com
  faixas creme mortas sem justificativa explícita na intenção (orientação dura
  no contrato; gate de área mínima da foto no quadro **somente** se o titular
  autorizar validação geométrica — senão, validação de plano + skill + exemplo).
- Tipografia/overlay **sobre** a foto com contraste; evitar cartaz tipográfico
  de abertura que consuma segundos sem imagem.

### M2 — Marca como âncora, não favicon

- No fecho/handoff (tempos do plano): logo com **escala mínima legível** no
  mobile (orientação numérica no contrato/exemplo, ex. fração do frame),
  contraste e micro-movimento até `end`.
- `brand_name` tipográfico pode acompanhar; não dominar nem substituir o PNG.
- Exemplo v7+ com logo em tamanho de fecho de anúncio, não ícone de canto.

### M3 — Ritmo duro no plano (sem A5b ainda)

- Holds de leitura / beats sustentados: teto ~2–2,5 s **no planejamento**
  (validar duração de cenas/beats se o schema permitir sem inventar estética).
- Fecho: exigir janela `handoffEnd < end` com movimento declarado (KB nas fotos
  + scale na logo); nenhum fecho “cartão congelado” multi-segundo.
- Storyboard alvo: gancho com imagem → acento → 2º material vivo → handoff →
  marca/CTA vivos — sem alongar contemplação.

### M4 — L4 mix

- Subir presença da trilha alguns dB (instrumental de fundo); fades ok.
- Sem mudar tarifa/credencial Music sem OK explícito.

### Fora desta onda

- A5b limiares de pixel/congelamento (só após 1–2 ensaios M1–M3).
- TTS/Voice, avatar, troca de renderer.
- Auto-injeção cega de helpers sem autorização explícita.
- Reescrever snapshots históricos.

## Prompt sugerido para o próximo chat

```
Leia AGENTS.md, o topo de docs/PROJECT.md, docs/SDD.md,
docs/phases/BL04-context-and-ai-production.md e
docs/design/motion-ensaio-cafe-aurora-v4-gaps-2026-11-17.md
(contexto L1–L3 em motion-ensaio-cafe-aurora-v3-gaps-2026-11-17.md).

Implemente a próxima fatia de qualidade photo reel (M1–M3 do doc v4; M4 mix
se couber sem mudar Music):
1) Quebrar template editorial: default full-bleed 9:16 / foto sobre foto;
   desencorajar forte cartão creme com foto em janela
2) Logo no fecho como âncora (escala mínima legível + micro-movimento até end),
   não favicon ao lado do nome
3) Ritmo: holds ≤ ~2–2,5 s no plano; fecho com movimento até end (tempos do
   plano, sem janela fixa 11–15s)

Preservar snapshots históricos, vídeo e Music (salvo M4 se autorizado no texto
acima). Sem A5b, TTS/avatar, troca de renderer.

Evidência: versao-1 (4).mp4 — logo pequena no fecho ok; ~82% quase estático
(pior que v3 em energia); ainda cartaz editorial, distante de propaganda.

Testes + PROJECT/SDD/BL04/CHANGELOG/DECISIONS na mesma mudança.
Não declare aceite E2E sem novo MP4 e minha revisão. Não rode chamada paga
sem eu autorizar.
```

## Aceite da próxima fatia

- Novo MP4: foto dominante cobrindo o 9:16 na maior parte do tempo; não o mesmo
  cartaz creme com janelas.
- Logo no fecho legível como marca (não miniatura irrelevante).
- Holds de miolo e fecho perceptivelmente vivos; sem ~4 s finais congelados.
- Mix melhor se M4 incluído.
- Sem gate A5b automático; sem upgrade silencioso de snapshots antigos.
