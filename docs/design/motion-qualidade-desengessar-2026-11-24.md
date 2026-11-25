# Desengessar qualidade — inventário e decisão (24/11/2026)

Norte: peças alinháveis às ~41 refs + Maestros. **Não** otimizar por
proibição. Plano = allowlist; residual fora do plano continua rejeitado.

## Manter (segurança / escopo — titular confirmou)

| Item | Motivo |
| --- | --- |
| Não inventar assets | Identidade e direitos |
| Sem Remotion / TTS / avatar | Escopo de produto |
| Teto 60s / 50MiB | Runtime e orçamento |
| Logo do kit (`assets/logo.png`) | Marca autorizada |
| Sem secrets em git/logs | Segurança |
| Residual fora do plano | Allowlist (não é teto se o plano declarar) |
| Crop inseguro | Protagonista / bleed |

**Também permanece (orçamento, não estética):** geração **paga** de música só
com as mesmas gates de photo (`elevenlabs-music-v1`: chave, rights, reservation,
budget). Sem credencial: cache do negócio ou `music_not_configured` — sem
provedor e sem seed CC0 sintético. Com gates ok, video usa o mesmo caminho
ElevenLabs dos reels estáticos (edit-v3+ / mixer duck v3).

**Adiado (dívida técnica, não “proibir para sempre”):** speed ramp **com fala**
exige time-stretch (`atempo`) no mixer FFmpeg — ainda não existe no renderer.
Nesta fatia: speed 0,75–1,25 **só em modo silent**; com áudio, remonte speech-safe
já liberado (edit-v3) cobre o ganho editorial das refs.

## Engessamentos que atrapalhavam qualidade → ação nesta fatia

### Video-reel (novas capturas → edit-v4 / reel-v3 / design-v2 / skill-v23)

| Antes | Problema | Depois |
| --- | --- | --- |
| `transition: cut` só | Sem dissolve/fade com função | `cut\|dissolve\|fade`; overlap ≤500ms em dissolve/fade |
| Layers só `rectangle\|ellipse` + `#rgb` | Grafismo pobre | + `rounded\|bar`; cor `#RRGGBB` ou `#RRGGBBAA` |
| Beats de layer só `{x,y,opacity}` | Sem escala em acento | + `scale` opcional (default 1) |
| Texto sem filhos / scrim hiper-rígido | Tipografia limitada | Filhos de texto permitidos se legíveis; scrim local permanece |
| `EDITORIAL_DEVELOPMENT` amarrado a 48px + forma | Capacidade ≠ só um truque | Aceita PIP, imagem sustentada, graphic exposto, barra/rounded |
| Speed 1:1 obrigatório | Sem aceleração visual | Silent: rate 0,75–1,25 no seek; com áudio: 1:1 + speech-safe |
| Skill/regras “sem música” | Modelo evita trilha | Ensina mix biblioteca/duck; paid gen continua gated |

Replay A/B/C (edit-v1..v3, reel-v1/v2, skill≤v22) **intactos**.

### Photo-reel (novas capturas → polish-v8 / photo-v22)

| Antes | Problema | Depois |
| --- | --- | --- |
| Cover obrigatório em toda cena (v6/v7) | Sem contain deliberado | `cover\|contain_blur` de novo, com crop-safe / intent |
| Transform contínuo 100% na primária | Sem hold de leitura | Holds permitidos; energia via primária **ou** related |
| Continuidade 80%/≤500ms só na primária | KB numérico “morto” | Mesma régua da energia densa (related conta) |
| Hold ≤2,5s | Leitura curta demais vs refs | Hold ≤4s se houver energia na cena |
| Soft brief | Orientação (não gate) | Permanece tom; **não** vira veto de motion/grafismo |

Replay polish v1–v7 / photo-v21 **intactos**. Grafismo declarado (v7) permanece.

### Outros formatos

| Formato | Estado | Ação |
| --- | --- | --- |
| Story vídeo / carrossel | Só skill de direção; sem HTML executor | Fora desta fatia (fluxo incompleto ≠ trava estética do reel) |

## Validação esperada

- Unitário dos contratos novos + regressão de pins antigos
- Sem chamada paga / sem MP4 Café nesta mudança
- Aceite perceptual = MP4 + revisão humana vs refs (pendente)
