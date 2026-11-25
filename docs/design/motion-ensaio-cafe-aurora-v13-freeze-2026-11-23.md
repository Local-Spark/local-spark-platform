# Café Aurora — congelamento do reel foto (photo-reel) — 23/11/2026

Estado: **loop de qualidade do reel com fotos do cliente CONGELADO** no Café
Aurora. Sem nova implementação de polish/gates neste modo até o titular
reabrir. Próximo ensaio de formato: **Reel com vídeo enviado pelo cliente**.

## Onde paramos

| Item | Estado |
| --- | --- |
| Formato | Reel motion a partir de **fotos** (HTML photo-reel), não vídeo de entrada |
| Último contrato | `motion-photo-polish-v6` + `photo-polish-v4.js` (+ timing-v1) |
| Último MP4 | `/Users/israelsilva/Downloads/versao-1 (12).mp4` |
| Hash | `35d26da01f5bbbf74b0a7098be11c204d9c094e20a64b4a849ea9bf7bfa51b67` |
| Briefing | Soft inalterado (*clima / aconchegante / pausa / nossas fotos*) |
| Ref. positiva | `Cafe-Aurora-render-recuperado-cefe9071.mp4` (`8cba7ed7…`) |

Histórico imediato: diagnóstico `(11)` / V1 em
[motion-ensaio-cafe-aurora-v12-gaps-2026-11-23.md](motion-ensaio-cafe-aurora-v12-gaps-2026-11-23.md);
U1–U3 em
[motion-ensaio-cafe-aurora-v11-gaps-2026-11-23.md](motion-ensaio-cafe-aurora-v11-gaps-2026-11-23.md).

## Aceite do ensaio `(12)` / polish-v6

| Critério V1 | Resultado |
| --- | --- |
| Cover full-bleed 9:16, sem Stories/letterbox | **Passou** (gancho ao fecho) |
| Energia suave contínua no miolo (olho / pipeline) | **Não** — ~86% quase-estático; holds ~2 s; pior ou igual ao `(11)` no pipeline local |
| Tipografia sem blob; copy soft; logo + CTA | Ok |
| Mix | −31,5 LUFS (fora de escopo; U4 não autorizado) |

Estimativa: ~**60–65%** vs propaganda / ~**70–75%** vs briefing soft — cover
perto de `cefe9071`; energia abaixo. Go de congelar = cover ok + sem regressão
tipográfica, **não** igualdade a cefe em movimento nem 80% propaganda.

## Decisão do titular

1. **Não** implementar V2 nem nova rodada de polish no photo-reel do Café.
2. **Não** reescrever o briefing só para subir propaganda.
3. Congelar este modo no Café e seguir para teste de **Reel (vídeo do cliente)**.
4. Depois: repetir os 4 cenários (feed foto, story foto, reel fotos, reel
   vídeo) nos outros 2 negócios; só então implementar story vídeo + carrosséis.

## Teto conhecido (backlog adiado, não autorizado)

- Energia perceptual ainda fraca apesar de U2 e continuidade 100% no plano/DOM
  (N2 no piso pode “parecer” hold).
- Variedade/clima (ambiente) e mix (U4) abertos.
- Interpretação “conversão sem trair pedido leigo” no gerador geral — fora
  desta série Café.

**Atualização 24/11/2026:** titular reabriu explicitamente para remover o
engessamento `DECORATION_FORBIDDEN`/T3 e capacitar grafismos/camadas
declarados no photo-reel (qualidade máxima), sem afrouxar cover/crop-safe/
legibilidade/tom soft. Ver
[qualidade-replanejamento](motion-video-reel-qualidade-replanejamento-2026-11-24.md).

**Implementado 24/11:** novas capturas photo usam `motion-photo-polish-v7` +
`photo-polish-v5.js` + `instagram-reel-photo-v21` (allowlist de graphic).
Replay do ensaio `(12)` / v6 permanece pinado. MP4 E2E Café com v7 ainda
pendente.

Reabrir rodada de ensaio Café photo somente com pedido explícito do titular.

## Próximo passo de formato

- Ensaios de criação: **Reel com MP4 enviado pelo cliente** (caminho video-reel
  / `source_asset_id`), via testes de criação — WhatsApp/Meta publish fora.
- Não tratar este congelamento como homologação comercial do photo-reel nem
  como aceite E2E global.

### Material de entrada — Reel vídeo (Café Aurora)

Vídeo para simular envio do cliente (o pedido o titular escreve na UI):  
`/Users/israelsilva/Downloads/cafe-aurora-cliente-preparacao.mp4`  
(cópia de `.local/evals/motion-referencia-2026-11-05/assets/video-enviado-simulado.mp4`,
hash `dd3f0265…`, ~11,2 s, 360×640, H.264+AAC).  
Não usar `reel-pausas.mp4` do kit (peça composta, não gravação bruta).

### Ensaio v1 rejeitado — ver gaps video-reel

Saída `versao-1 (13).mp4` rejeitada (cartaz/inset/sem motion). Diagnóstico e
backlog VR1–VR6 em
[motion-ensaio-cafe-aurora-video-reel-v1-gaps-2026-11-23.md](motion-ensaio-cafe-aurora-video-reel-v1-gaps-2026-11-23.md).
