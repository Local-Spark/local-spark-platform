# Ensaio mecânico WAAPI e vídeo — 05/11/2026

A prova avaliou se um navegador local consegue buscar tempos fixos em duas
animações próprias e produzir quadros para um MP4, sem GSAP. Ela não mede
qualidade criativa e não implementa a geração de produto. Nenhum Jev, modelo,
API paga, banco ou conteúdo de cliente foi usado.

## Caso, execução e resultados

O HTML contém apenas fundo, retângulo e texto fictício; o retângulo se desloca
linearmente e o texto aumenta de opacidade. Aos tempos 0, 500 e 1.000 ms, as
posições `x` observadas foram 20, 110 e 200 px, e as opacidades foram 0, 0,5 e
1. Após retornar ao tempo zero, o PNG foi idêntico ao primeiro por SHA-256.

Foram capturados 31 quadros a 30 fps e gerado [MP4 de teste](../../.local/evals/motion-waapi-probe-2026-11-05/synthetic.mp4)
H.264, 320 × 240, 1,034 s e 8.514 bytes. SHA-256:
`46e67801e9ce1b9cc14f88db311ab2aa447b207b7acaffeada5cd6b7f434677c`.
O arquivo foi decodificado integralmente pelo FFmpeg sem erro.

| Tempo | Quadro | SHA-256 |
| --- | --- | --- |
| 0 ms | [Inicial](../../.local/evals/motion-waapi-probe-2026-11-05/frame-000.png) | `b0a5a00aa42a6138076690d7925235308732db424e5a4abc5378a934acef28d8` |
| 500 ms | [Meio](../../.local/evals/motion-waapi-probe-2026-11-05/frame-015.png) | `cae7fca40c1d0b715cdee4aa56f3d67368fd4f3a2627f2404957c921753438a8` |
| 1.000 ms | [Final](../../.local/evals/motion-waapi-probe-2026-11-05/frame-030.png) | `571860513feed57b202f43a6e1a24d0e1ac529a8cb54dc45789df6bcbbdb6ede` |
| Retorno a 0 | [Repetição](../../.local/evals/motion-waapi-probe-2026-11-05/rewind.png) | `b0a5a00aa42a6138076690d7925235308732db424e5a4abc5378a934acef28d8` |

O [relatório da execução inicial](../../.local/evals/motion-waapi-probe-2026-11-05/report.json)
contém os dados da página e do MP4. `.local` é privado e ignorado pelo Git; os
arquivos podem não existir em outro checkout. O primeiro script de ensaio ficou
em `/private/tmp/motion-waapi-probe.js`, SHA-256
`5d133de20faa5f28531b23f4d846a761f3d6a0106c903ceb3f78769e8743cdf4`.

A execução usou Playwright Core 1.64.1, Chromium Headless Shell 156.0.8078.4
(cache Playwright revisão 1248), FFmpeg 9.0 e FFprobe 4.4.8, em macOS arm64.
Chromium foi iniciado com sua sandbox habilitada após a sandbox da ferramenta
impedir sua inicialização. CSP `default-src 'none'`, bloqueio de rotas e zero
requisições observadas na página; o processo recebeu ambiente limitado sem
credenciais. Isso **não prova bloqueio de rede no nível do sistema operacional**.

O [executor parametrizado](../../scripts/evals/motion_waapi_probe.cjs), SHA-256
`f2b82f41e6688799f2fb4de5e5302bb0ac90aa683977e006dc942accd2d53965`, foi
executado depois com os mesmos binários e diretório temporário novo. Ele
reproduziu os três hashes de quadro e o hash do MP4 da execução inicial. A
conferência de sintaxe `node --check` passou. Os binários locais e a fonte do
sistema usada no texto não são dependências preservadas ou empacotadas.

## Reprodução

Fornecer caminhos **absolutos e confiáveis**, já instalados, e uma pasta de saída
que ainda não exista. Não há instalação, download ou fallback de dependência.
O binário FFmpeg precisa suportar `libx264`; a fonte padrão pode variar por
ambiente, de modo que hashes entre sistemas não são garantidos. O Node executa
o módulo Playwright informado: não apontar para código não confiável.

```sh
node scripts/evals/motion_waapi_probe.cjs \
  --playwright /caminho/para/playwright-core \
  --chromium /caminho/para/chromium-headless-shell \
  --ffmpeg /caminho/para/ffmpeg \
  --ffprobe /caminho/para/ffprobe \
  --out /caminho/para/pasta-nova
```

O executor guarda apenas quadros de três tempos, repetição, MP4 e relatório;
apaga os quadros intermediários temporários. Resultado parcial pode permanecer
na pasta de saída em caso de erro, sem relatório de sucesso. Não usar com
material privado ou considerar a sandbox do navegador equivalente à política
de isolamento de produção.

## Próximo ensaio: adaptar a direção do Reel v2

Usar o [Reel v2 e seu trace](ensaio-motion-referencia-2026-11-05.md) como
referência de qualidade para esse caso, não como estilo universal. Reaproveitar
o vídeo fictício autorizado e seu áudio sintético com direitos identificados;
nenhum deles representa um cliente real ou a fala da pessoa retratada. Registrar
pedido, fontes e hashes, kit, saída de cada etapa e eventual diferença de
direção. Preservar o original e separar claramente qualquer adaptação.

Como hipótese técnica, expressar texto, máscaras, movimentos e transições em
dados validados e composição HTML/WAAPI própria; usar FFmpeg local para cortar,
sincronizar e mixar a gravação, áudio e resultado visual. Recriar batidas e
hierarquia do v2 com fidelidade suficiente para compará-lo, sem executar HTML
gerado pelo modelo. Conferir quadros, movimento, legibilidade, áudio e legenda;
pedir avaliação humana. Essa hipótese ainda precisa de contratos, implementação
e isolamento; um teste de dois elementos não comprova a qualidade do Reel.

Um ensaio inteiramente local com materiais e direção já disponíveis prevê zero
chamadas pagas, mas tempo de computação e infraestrutura não foram medidos. Se
forem necessárias novas interpretações, transcrições ou direções por modelo,
apresentar antes o número de chamadas, preços vigentes, estimativa e orçamento
específico, com ledger próprio; não reutilizar as autorizações anteriores.
