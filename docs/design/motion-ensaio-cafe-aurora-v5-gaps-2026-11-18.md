# Ensaio Café Aurora v5 — gaps e próxima fatia — 18/11/2026

## Atualização — N1–N3 implementados, aceite audiovisual pendente

Pedido posterior do titular autorizou a implementação: intent/regras v6, skill
photo v17 e repertório v9. Cover real, exceção de crop justificada, logo sem placa
e energia numérica no plano; gates M3 preservados. Sem A5b ou alteração de
Music/mix (N4 adiado). Snapshots históricos intactos. Validação e limites em
PROJECT/SDD/BL04/CHANGELOG/DECISIONS. Novo MP4 autorizado e revisão do titular
continuam necessários; o diagnóstico abaixo é a evidência anterior à mudança.

## Diagnóstico original

Estado: **diagnóstico e backlog documentados** a partir de
`/Users/israelsilva/Downloads/versao-1 (5).mp4`. Não autoriza, por si,
implementação, chamada paga, A5b nem alteração de Music/renderer. Destinado a
um próximo chat/modelo.

Referências: M1–M3 e crop v5 em
[motion-ensaio-cafe-aurora-v4-gaps-2026-11-17.md](motion-ensaio-cafe-aurora-v4-gaps-2026-11-17.md);
L1–L3 em
[motion-ensaio-cafe-aurora-v3-gaps-2026-11-17.md](motion-ensaio-cafe-aurora-v3-gaps-2026-11-17.md);
Maestros [WuzMxEKJHkQ](../evals/analise-video-maestros-WuzMxEKJHkQ-2026-11-11.md).

## Evidência do ensaio v5

Arquivo: 15,0 s · 720×1280 · H.264 + AAC · ~1,34 Mbps (~2,5 MB; maior que v3/v4).
Loudness ~**−31,6 LUFS** (inalterado; True Peak ~−16,3 dBTP).

Amostragem a 5 fps (cinza 90×160):

| Medida | v4 | **v5** |
| --- | --- | --- |
| Quase estático (diff &lt; 2) | ~82% | **~89%** |
| Diff médio | ~3,1 | **~2,4** |
| Holds longos | ~3,2 / 3,4 / 4,4 s | **~3,0 / ~6,6 / ~3,0 s** |
| Picos | trocas | **~4 s e ~11 s** |

Leitura humana (titular): **estamos evoluindo**, ainda não no nível máximo /
propaganda das refs YouTube.

### Storyboard observado

1. **~0–4 s** — foto flat-lay (xícara vermelha + croissant) em **janela landscape**
   sobre fundo blur da mesma foto; tipografia “Faça uma pausa.”; objetos **inteiros**
   (crop conflict resolvido).
2. **~4–11 s** — 2ª foto lifestyle na mesma fórmula (janela + blur); “Um café.” /
   “Um tempo seu.”; **miolo ~6,6 s quase parado**.
3. **~11–15 s** — díptico + **placa creme** com logo AURORA (âncora visual maior)
   + CTA “Conheça nosso cardápio”.

### Evolução vs regressão

| Melhorou | Ainda falha |
| --- | --- |
| Fora do cartaz creme puro tipográfico | Template **Stories**: landscape + barras blur |
| Protagonista preservado (contain/camadas) | Não é full-bleed 9:16 imersivo |
| Logo âncora no fecho (não favicon) | Logo em **placa creme** (estilo desencorajado) |
| Bitrate/foto no quadro | Energia de movimento **pior** no métrico; hold ~6,6 s |
| Sem revisão por corte de xícara | Mix −31,6 LUFS; tipografia ainda simples |

Diagnóstico: contratos de crop + logo fizeram efeito parcial; **M1 (full-bleed)**
e **energia contínua** não. O modelo escolheu a alternativa “contain sobre fundo”
como **default visual**, não como exceção justificada — e o fundo blur não
substitui cover 9:16. Gate `hold ≤2500 ms` não impede miolo estático rotulado
como movimento.

## Backlog priorizado (próxima implementação)

### N1 — Full-bleed real (não Stories blur)

- Default: foto dominante **cover 9:16** com foco/região essencial protegida e
  margem de KB compatível (já coberta por crop v5).
- “Contain + fundo blur/ampliado” só como **exceção** com justificativa explícita
  quando cover for inviável — não como layout padrão de todas as cenas.
- Proibir / desencorajar forte o padrão “faixa landscape central + barras blur”
  como estética automática.
- Tipografia/CTA como **overlay** sobre a foto full-bleed, com scrim local.

### N2 — Energia no miolo (além do rótulo transform)

- Evitar trechos longos com mudança imperceptível: orientação +, se autorizado,
  reforço no validador (ex.: exigir magnitude mínima declarada de scale/pan nos
  beats de foto, ou rejeitar `start_state`/`end_state` trivialmente distintos).
- Helper/exemplo: KB perceptível no cover full-bleed; não drift micro em janela.
- Sem A5b de pixels ainda, salvo OK explícito do titular.

### N3 — Fecho sem placa creme

- Logo PNG como overlay/âncora sobre foto (ou fundo fotográfico), **sem** card
  creme/editorial que traga de volta o template antigo.
- Micro-movimento até `end`; CTA integrado, não rodapé de cartaz.

### N4 — Mix (L4/M4)

- Subir presença da trilha alguns dB; sem mudar tarifa/credencial Music sem OK.

### Fora desta onda

- A5b geométrico/pixel completo (só após ensaio N1–N3, se ainda necessário).
- TTS/Voice, avatar, troca de renderer.
- Auto-injeção cega de helpers.
- Reescrever snapshots históricos / run falha antiga.

## Prompt sugerido para o próximo chat

```
Leia AGENTS.md, o topo de docs/PROJECT.md, docs/SDD.md,
docs/phases/BL04-context-and-ai-production.md e
docs/design/motion-ensaio-cafe-aurora-v5-gaps-2026-11-18.md
(contexto M1–M3/crop em motion-ensaio-cafe-aurora-v4-gaps-2026-11-17.md).

Implemente a próxima fatia (N1–N3 do doc v5; N4 mix se couber sem mudar Music):
1) Full-bleed 9:16 cover como default real; contain+blur só exceção justificada
   quando crop impedir protagonista — proibir default “janela landscape + barras blur”
2) Energia no miolo: KB/overlay perceptíveis; reforçar plano/exemplo/validador
   contra holds longos disfarçados de transform (sem A5b de pixels sem meu OK)
3) Fecho: logo PNG âncora sem placa creme; micro-movimento até end

Preservar: crop v5 (protagonista > bleed inviável), gates M3, snapshots
históricos, vídeo, Music (salvo N4). Sem TTS/avatar/renderer novo.

Evidência: versao-1 (5).mp4 — evoluiu (crop ok, logo âncora) mas ~89% estático,
hold ~6,6s no miolo, layout Stories blur, placa creme no fecho, mix −31,6 LUFS.

Testes + PROJECT/SDD/BL04/CHANGELOG/DECISIONS na mesma mudança.
Não declare aceite E2E sem novo MP4 e minha revisão. Não rode chamada paga
sem eu autorizar.
```

## Aceite da próxima fatia

- Novo MP4: maior parte do tempo em foto **cover 9:16**, não janela+blur.
- Miolo sem ~6 s “parados”; movimento perceptível entre trocas.
- Fecho com logo legível **sem** card creme dominante.
- Mix melhor se N4 incluído.
- Protagonista ainda preservado quando cover for usado (crop v5 intacto).
- Sem upgrade silencioso de snapshots antigos.
