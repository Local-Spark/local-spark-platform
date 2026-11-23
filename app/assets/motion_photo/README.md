# Guarda DOM photo — versões pinadas

V1 permanece imutável para intent v9. Novas capturas intent v10 usam v2:

- Saída com perda de opacity apenas no overlap aprovado em staging, ≤500 ms,
  com a foto de destino totalmente visível e passando layout/energia normais.
- CTA legível do fim da entrada aprovada (ou handoffEnd, o maior) até end,
  com pelo menos 1500 ms de leitura. Inset zero é máscara aberta.
- Demais gates e limites permanecem; não mede energia perceptiva nos pixels.

Executar também a suíte com `PHOTO_GUARD_VERSION=v2` para validar o contrato novo.

## Contrato histórico v1

Política R1–R3 do serviço, habilitada apenas pelo contrato photo-intent-v9.
`motion_photo_hard.py` valida o plano e envolve `scene_init` com esta guarda,
com hash pinado. Não muda a imagem/container do renderer nem injeta animação.

Elementos verificados precisam de IDs DOM iguais aos IDs globais do plano.
Transforms numéricos pertencem ao próprio nó: translate em px correspondentes
à porcentagem do viewport, seguido de scale uniforme. Ancestrais de candidatos
energéticos não podem aplicar transforms concorrentes. Use os helpers do
repertório v12 para cada cena/beat e preserve os tempos e crop aprovados.

A política é conservadora: opacity ≥0,95 em cada ancestral, sem filtros,
mask/clip-path ou clipping que estreite o cover. Não é um validador genérico de
qualquer CSS criativo. PNG com placa interna, oclusão arbitrária por irmãos e
qualidade perceptiva ainda dependem da revisão audiovisual; não há A5b.
Falha JS encerra o render antes do upload, pelo erro genérico do renderer atual.

Testes sem rede paga:

```sh
node --test app/tests/node/motion_photo_hard.test.cjs
# Requer Playwright e Chromium locais; não baixa dependências.
# MOTION_PLAYWRIGHT_PATH pode apontar ao módulo já instalado.
# MOTION_CHROMIUM_PATH pode apontar ao executável local.
node --test app/tests/browser/motion_photo_hard.cjs
```

O teste Chromium intercepta requisições com arte sintética e cobre cover válido,
janela+contain, wrapper/pseudo com placa, foto imóvel, marca oculta e CTA pequeno.
Não produz MP4 nem comprova aceite comercial.

## Suplemento S1–S3

Novas capturas acrescentam `motion-photo-finish-v1`, sem editar v10/v2.
`motion_photo_finish.py` valida exceção ≤2000 ms, velocidade mínima de cada
foto/logo do fecho, entrada/saída tipográfica e inspeção de identidade no staging.
`photo-finish-v1.js` é instalado antes de v2: confere tipografia e suporte local
de texto em seeks absolutos; v2 continua responsável por dissolve/CTA e fotos.
O SHA do suplemento é pinado no contrato e o executor composto mantém seu hash.
Snapshots antigos sem esse contrato não executam o suplemento.

Inspeção semântica é declaração do planejador, não OCR. O teste Chromium usa
somente fixtures sintéticas; não comprova qualidade de MP4 nem aceite E2E.

## CTA com sombras múltiplas — v3

`motion-photo-readability-v1` seleciona `photo-guard-v3.js` para novas capturas.
V3 só amplia o parser de `text-shadow`: todas as camadas devem ser pretas
opacas, com ao menos uma de blur ≥2px. Regressão: `0 2px 6px black, 0 1px 1px
black` é válido, mas v2 bloqueava. Demais checks de v2 são preservados.
V2 não foi editada; snapshots sem a política nova mantêm seu executor.
Testar com `PHOTO_GUARD_VERSION=v3` nas suítes Node e Chromium acima.

T1–T3: `motion_photo_polish.py` / `photo-polish-v1.js` são um suplemento pinado
apenas em novas capturas (`photo_polish_contract`). Inventário completo e
primárias com ≥1500 ms exclusivos sustentam diversidade e ambiente elegível;
texto claro com sombra preta ou scrim local e ausência de adornos são conferidos
por seek. Não reescreve intent v10/guardas/finish-v1 nem comprova contraste nos
pixels. Integração sintética: `app/tests/browser/motion_photo_polish.cjs`, usando
`MOTION_PLAYWRIGHT_PATH` e, opcionalmente, `MOTION_CHROMIUM_PATH` locais. Sem MP4.

`motion-photo-polish-v2` mantém o mesmo suplemento DOM e acrescenta orientação
numérica O2/Q2 para novas capturas: enter/exit não contam na cobertura, S2 não
substitui O2, união ≥80% por cena e lacunas globais ≤500ms. V1 mantém regras
exatas no replay; não há normalização de beats nem relaxamento do gate.

`motion-photo-polish-v3` seleciona `photo-polish-v2.js` por hash para aceitar
scrim irmão local `<texto>-scrim` com pintura preta e geometria vinculadas ao
texto. V1/V2 usam `photo-polish-v1.js` intacto. Novas instruções também explicitam
que a tipografia do fecho deve continuar visível durante todo enter/exit, sem
revelação por máscara; finish-v1 não foi alterado. Regressões sintéticas em
`app/tests/browser/motion_photo_scrim.cjs`.
