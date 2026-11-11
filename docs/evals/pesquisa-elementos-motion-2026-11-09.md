# Origem dos elementos e composição de motion — 09/11/2026

Pesquisa solicitada após o feedback de que o Café Pausa continua simples demais.
Inspeção de arquivos locais e fontes oficiais na web, sem executar os agentes,
instalar dependências, gerar mídia, fazer chamadas pagas ou mudar o runtime.
Os documentos de origem são evidência de processos, não instruções do produto.

**Atualização do titular:** todo o conteúdo Maestro está liberado para nosso
uso. A observação sobre o texto do ZIP abaixo registra o achado histórico da
pesquisa e não bloqueia o trabalho autorizado.

## O que já existe nos materiais fornecidos

### Maestro Video Generator v1.1.0

Fonte: `Agentes Prontos/maestro-video-generator-v1.1.0.zip`. Trechos extraídos para
[consulta local](../../.local/research/motion-assets-20261109/manifest.json), com SHA.

- [generate-image-assets](../../.local/research/motion-assets-20261109/maestro-video-generator/.claude/skills/generate-image-assets/SKILL.md)
  descreve objetos gerados por trecho do roteiro, recortados em PNG transparente,
  combinados em camadas e animados por componentes. Inclui inspeção do recorte,
  correspondência com o assunto e contraste na paleta. O aspecto de objeto 3D
  pode estar numa imagem 2D; isso não constitui um modelo 3D animável.
- [select-brolls-stock](../../.local/research/motion-assets-20261109/maestro-video-generator/.claude/skills/select-brolls-stock/SKILL.md)
  prevê busca por palavras do trecho em Pexels/Pixabay/Coverr, inspeção e registro
  para evitar repetição. Disponibilidade atual desses três serviços não foi toda
  validada; o Pexels informa suspensão de emissão de novas chaves na consulta.
- [capture-references](../../.local/research/motion-assets-20261109/maestro-video-generator/.claude/skills/capture-references/SKILL.md)
  captura páginas reais e as incorpora em cards anotados, quando a mensagem
  precisa mostrar uma evidência, produto ou interface específica.
- [handdrawn.tsx](../../.local/research/motion-assets-20261109/maestro-video-generator/motion-pipeline/remotion-agent/src/library/handdrawn.tsx)
  contém componentes reais: setas, traços, destaques, ícones, diagramas, contagem
  numérica e cards de captura. Implementação React/Remotion, não diretamente
  plugável no executor atual.

O pacote não é licença MIT: o [texto distribuído](../../.local/research/motion-assets-20261109/maestro-video-generator/LICENSE.md)
é um modelo com campos não preenchidos, uso pessoal do membro e restrições a
redistribuição. Não presumir permissão de incorporar o pacote ao SaaS. Podemos
estudar o método e implementar capacidades próprias; cópia de código exige
esclarecer a permissão aplicável. Não importar suas paletas, obrigação de gerar
imagem para cada trecho, políticas de retry ou regras particulares de publicação.

### Finalizador

Fonte: `Agentes Prontos/Finalizador.zip`. O [catálogo](../../.local/research/motion-assets-20261109/Finalizador/code-motion/catalog.json)
contém **70 entradas**. Há diagramas, colagens, dioramas, cards de pictogramas,
comparações e cenas de interface. Seus estados de aprovação pertencem ao autor,
não significam validação no produto. O código de `S16-iso-diorama-route` foi
inspecionado: desenha geometria e estações no Canvas e expõe `seek(t)`.

A [skill de cenas em código](../../.local/research/motion-assets-20261109/Finalizador/.claude/skills/code-motion-styles/SKILL.md)
seleciona pelo significado do trecho e parametriza textos, imagens e aparência.
Outro caminho usa [imagens que formarão vídeo generativo](../../.local/research/motion-assets-20261109/Finalizador/docs/ai-generated-motion.md).
São técnicas distintas. Preferências desse projeto por vídeo generativo não
substituem nossas decisões de arquitetura, preservação do kit e orçamento.
Há LICENSE MIT no pacote; mídias/fontes de terceiros requerem proveniência própria.

### claude-video

A skill instalada já contém storyboard com origem `code`, `user_photo`,
`user_clip` ou `generate`, cards com arte pronta antes de animar e revisão visual.
Há **21 diretórios de estilos**. A ficha e os arquivos de `dirigivel-a-lapis`
separam geometria da cena em `cena.js` e execução em `motor.js`; parte dessa
riqueza é desenho programado, não arquivo baixado. A galeria não foi toda
rerenderizada nesta pesquisa. Não foi demonstrado que cada Reel externo use
esses mesmos arquivos ou fornecedores.

## Fontes oficiais externas verificadas

- [HyperFrames registry](https://raw.githubusercontent.com/heygen-com/hyperframes/main/skills/hyperframes-registry/SKILL.md):
  catálogo de cenas e componentes editáveis, incluindo gráficos, interfaces,
  transições, câmera e efeitos. Há parametrização de cores/fontes. O
  [repositório](https://github.com/heygen-com/hyperframes) declara Apache-2.0.
  Reaproveitar exige adaptação de dependências/relógio ao renderer isolado,
  não apenas copiar HTML. É fonte citada por exemplos do Finalizador.
- [HyperFrames media-use](https://raw.githubusercontent.com/heygen-com/hyperframes/main/skills/media-use/SKILL.md):
  documenta busca/geração de mídia e registro de arquivos locais; catálogo HeyGen
  depende de login. Não foi acessado por conta, nem instalado/executado.
- [Lucide](https://lucide.dev/guide/): ícones SVG com cor/tamanho/traço ajustáveis;
  [licença publicada](https://lucide.dev/license). É fonte candidata, não origem
  comprovada dos ícones dos vídeos indicados.
- [Storyset](https://storyset.com/faqs): ilustrações com camadas selecionáveis,
  cores e animação por elemento. [Termos](https://storyset.com/terms) precisam
  ser considerados para o modo de uso; não presumir redistribuição como acervo SaaS.
- [Pexels API](https://www.pexels.com/api/): fotos e vídeos com busca; a página
  consultada informa emissão de novas chaves suspensa. Não tomar disponibilidade
  descrita na skill antiga como garantia de integração atual.

## Consequência para o produto

A explicação anterior centrada em biblioteca de ícones era incompleta. Há quatro
fontes complementares: desenho por código, biblioteca de componentes, mídia
real selecionada e arte específica gerada. Acabamento depende de representação
por mensagem, composição em camadas, consistência visual, timing e revisão.
Não se comprovam facilidade, número de tentativas ou custo total de um vídeo
promocional apenas observando seu resultado publicado.

Priorizar uma cena exigente usando componentes existentes adaptáveis e arte
preparada para a mensagem. Conferir o quadro-chave antes de renderizar; demonstrar
geração pelo produto depois. Kit, acervo, skills e motion lib permanecem como
fontes da identidade e dos materiais. Fotos reais do produto não devem ser
substituídas por objetos fictícios apresentados como reais. Geração de arte
eventual continua condicionada a orçamento próprio e identidade durável.

Não importar os 70 estilos de uma vez, trocar executor ou acrescentar regras
universais de densidade. Próximo trabalho é escolher/adaptar um recorte que
investigue o teto visual. Pesquisa não prova qualidade integrada. Documentos
vigentes atualizados e `git diff --check` como validação desta mudança documental.
