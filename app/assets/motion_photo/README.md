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
