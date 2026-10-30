# Kit fictício para QA: Ateliê Aurora

Os exemplos vetoriais `feed.svg` e `story.svg` e as versões PNG foram criados
para este teste, sem fotos, cliente real ou material de concorrentes. A identidade
é uma referência de composição, não fonte de fatos, logomarca ou autorização de
publicação. O kit **não está cadastrado no produto** e precisa ser passado
explicitamente pelo harness de QA; `load_kit_example` aceita apenas o kit demo
do produto. Consulte `manifest.json` para paleta, fontes, direitos e hashes.

Valide com `.venv/bin/python docs/evals/kit-atelier-aurora-v1/verify.py`.
Os SVGs são a fonte editável. O `render.swift` rasteriza no macOS com AppKit e
as fontes DejaVu do projeto; as versões do sistema podem produzir PNGs diferentes.
Para reproduzir um exemplo a partir da raiz do repositório:

```sh
env CLANG_MODULE_CACHE_PATH=/private/tmp/qa-swift-cache SWIFT_MODULECACHE_PATH=/private/tmp/qa-swift-cache swift docs/evals/kit-atelier-aurora-v1/render.swift docs/evals/kit-atelier-aurora-v1/feed.svg /private/tmp/atelier-feed.png catalog/kits/cafe-pausas/v1/fonts/DejaVuSans.ttf catalog/kits/cafe-pausas/v1/fonts/DejaVuSerif.ttf
```

Para story, troque `feed.svg` por `story.svg` e escolha outro caminho de saída.
