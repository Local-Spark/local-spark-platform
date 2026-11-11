# Claude Video: amostra original para estudo

Esta amostra contém somente fontes originais selecionadas, sem adaptação. A
licença MIT e os dois avisos de copyright estão preservados em `original/LICENSE`
e `original/LICENSE-original.txt`. O [manifesto](manifest.json) lista SHA-256,
tamanho, caminho de origem e Git blob SHA-1 de cada arquivo. Cada cópia foi
comparada com a instalação local e com uma cópia temporária verificada contra a
árvore de blobs obtida para o commit `ee3dc316759ae266effab49f55c1221c64028081`.
A origem temporária não é checkout Git; a relação com o commit é uma evidência
do inventário anterior, não uma nova conferência de commit com Git.

A amostra inclui instruções técnicas de movimento e loop, duas fichas e cinco
scripts para perícia, ritmo, loop e storyboard. A composição original
`cartaz-risografia` é desenho em código, sem imagem ou áudio embutidos; a ficha
registra a origem e os avisos. Nenhum vídeo da galeria, mídia, fonte, marca ou
biblioteca externa foi copiado. Fichas e código são material de estudo, não
orientações de produto ou estilos que já tenham sido avaliados para um negócio.

## Limites de segurança e execução

**Não executar diretamente no runtime do produto.** Os originais não são
adaptados às regras de privacidade, orçamento, isolamento ou experiência deste
projeto. A composição carrega GSAP e fontes por CDN; não é offline nem está
pronta para render seguro. Não a executar com dados de clientes.

Os scripts também não foram executados nesta fatia. A inspeção de código aponta:

- `pericia-movimento.py` pode imprimir caminho de entrada e saída e gravar JSON
  com nomes e medições; `ritmo.py` grava imagens de contato e JSON junto à saída.
- `storyboard.py` grava o storyboard e imprime textos, caminhos e prompts; para
  asset `generate`, tenta executar `higgsfield.py`, não incluído aqui. Não usar
  sua estimativa como controle financeiro nem expor conteúdo em logs.
- `loop.py --project` cria cópias temporárias e invoca `npx --yes`, que pode
  buscar pacotes na rede. Os scripts chamam `ffmpeg`/`ffprobe` externos e não
  aplicam os controles de isolamento do produto. Seu tratamento de arquivos e
  saídas requer revisão antes de integração.

## Dependências encontradas no ensaio anterior

São observações de desenvolvimento local, não artefatos preservados nem uma
declaração de licença de todas as dependências transitivas. Não depender desses
caminhos temporários para reconstrução ou produção.

| Dependência | Evidência local | Próxima verificação |
| --- | --- | --- |
| HyperFrames | `/private/tmp/local-spark-hyperframes/node_modules/hyperframes`, versão 0.8.181, pacote declara Apache-2.0, cerca de 22 MB; há dependências transitivas separadas. | Preservar pacote, licença, avisos e dependências completas, com hashes, segurança e teste offline. |
| GSAP | Cópia `gsap.min.js` do ensaio declara versão 3.15.1 e licença padrão GreenSock; projeto original referencia versão 3.14.2 em CDN. Pacote local de 3.15.1 ocupa cerca de 6,4 MB. | Verificar os termos aplicáveis, inclusive uso e distribuição comercial, e preservar pacote/avisos permitidos; não supor que versões sejam equivalentes. |
| FFmpeg | `/private/tmp/local-spark-hyperframes-tools/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v9.0`, cerca de 50 MB; o wrapper `imageio-ffmpeg` declara BSD-2-Clause. | Verificar configuração e licença do binário e seus componentes separadamente; a licença do wrapper não prova a do binário. Selecionar artefato do ambiente de deploy. |
| FFprobe | `/private/tmp/local-spark-ffprobe/node_modules/@w6s/ffprobe-static/bin/darwin/arm64/ffprobe`, cerca de 18 MB. `BUILD_INFO.md` informa FFmpeg 4.4.8 e LGPL 2.1 ou posterior; pacote `@w6s/ffprobe-static` 3.1.1 remete aos avisos de terceiros. | Conferir binário, código-fonte correspondente, avisos e obrigações de distribuição antes de empacotar. |
| Chromium | Cache local Playwright `chromium-1248` (~366 MB) e `chromium_headless_shell-1248` (~203 MB), para macOS arm64. | Identificar versão, avisos/licenças transitivas e binários adequados ao deploy; fixar e preservar a distribuição própria. |

O snapshot é parcial e não substitui cópia própria independente das fontes
adotadas, backup restaurável, empacotamento dos binários ou teste offline.

## Conferência e restauração local

Na raiz do projeto, `python scripts/verify_motion_sources.py verify
vendor/motion_sources/claude-video` confere os 16 arquivos, seus tamanhos,
SHA-256 e blobs Git. O verificador fixa também o SHA-256 deste manifesto e do
README; uma atualização intencional exige revisar os arquivos e o verificador em
conjunto. A verificação detecta alterações, mas não é assinatura criptográfica
da origem.

Para testar o arquivo em diretório temporário novo:

```sh
python scripts/verify_motion_sources.py archive vendor/motion_sources/claude-video /private/tmp/motion-sources.tar
python scripts/verify_motion_sources.py restore /private/tmp/motion-sources.tar /private/tmp/motion-sources-restored
python scripts/verify_motion_sources.py verify /private/tmp/motion-sources-restored
```

Os caminhos de saída não podem existir previamente. A restauração valida todos
os membros antes de escrever e recusa arquivos adicionais, links e caminhos
perigosos. A cópia temporária verificada ainda não é backup independente.
