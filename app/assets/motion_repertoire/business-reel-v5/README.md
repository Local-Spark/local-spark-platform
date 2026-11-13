# Repertório original v5

Dois exemplos consumidos pelo builder de motion, qualificados em Chromium/FFmpeg
no renderer isolado. Não são uma API adicional nem assets comerciais para colar
em peças. `manifest.json` fixa hashes de código, imagens e runtime.

- `makeTypePortal`: coloca o único nó de mídia sob máscara SVG tipográfica;
  revela por expansão radial sem controlar `currentTime` ou copiar o vídeo.
- `makeDepthHandoff`: coordena saída em perspectiva, chegada de outra camada e
  entrada posterior do título. Usa tempo absoluto para seeks repetidos/invertidos.

`images/` contém seis quadros de cada passagem executada, sem mídia de terceiros.
O estudo seletivo R10/R12/R17 está em
`docs/evals/referencias-motion-2026-11-12/anotacoes.md`; mecanismos podem ser
adaptados seletivamente, sem copiar conteúdo ou identidade das referências.

Reprodução: configurar explicitamente a imagem/socket do renderer local e rodar
`python -m scripts.evals.motion_mechanisms_qualify --output <diretório-novo>`.
O probe produz um MP4 sintético silencioso de quatro segundos e 12 imagens;
nenhum provider, negócio, admissão ou publicação participa. A sequência das duas
imagens deste catálogo é feita com esses quadros, nos tempos do manifesto.
O probe demonstra suporte de render, não melhora artística do gerador, fidelidade
sonora ou uma peça completa da cafeteria. As funções devem ser integradas em
`scene_init` e chamadas por `seek(ms)`; não são instaladas automaticamente.
