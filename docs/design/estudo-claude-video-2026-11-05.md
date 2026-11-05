# Estudo da skill `claude-video` — 05/11/2026

Pesquisa documental solicitada pelo titular, complementar ao [estudo de
HyperFrames e Howseen](estudo-hyperframes-motion-design-2026-11-04.md). Foram
lidos o README, a skill, a licença e trechos do contrato e script de render; não
se executou o repositório ou seu instalador durante essa análise inicial.

Após novo pedido do titular em 05/11/2026, a skill foi instalada no Codex em
`~/.codex/skills/claude-video`, no commit
`ee3dc316759ae266effab49f55c1221c64028081`. Os 209 arquivos instalados foram
conferidos contra os hashes de blob Git; 21 são prévias MP4 da galeria. A
instalação original por arquivo compactado travou durante o download e foi
encerrada; os arquivos do mesmo commit foram obtidos separadamente, verificados
e instalados pelo helper oficial de skills usando o arquivo local verificado.
Uma galeria completa da instalação respondeu em localhost, com servidor
temporário que encerra após quatro horas. Para reabrir, usar
`python3 ~/.codex/skills/claude-video/scripts/galeria.py --no-open`; a porta
disponível é informada pelo script. A galeria solicita fontes do Google ao
navegador. A skill ficará disponível ao Codex em turno/conversa posterior.

A checagem encontrou Node e Python; `ffmpeg` e `ffprobe` não estão no PATH
padrão, mas a verificação passou com ferramentas locais temporárias adicionadas
ao PATH do processo. Isso não constitui instalação global nem garante que os
binários de `/private/tmp` persistam. A navegação da galeria não os exige.
Para gerar vídeos posteriormente, confirmar novamente as ferramentas. Não foi
instalado Claude Code ou alterado o diretório de skills do Claude; esta é a
instalação para Codex.

O arquivo da galeria lista 21 estilos, sendo 20 em 16:9 e um em 1:1; nenhum é
marcado como vertical. Essas prévias são materiais externos de referência,
precisam de avaliação e adaptação para o produto, e não implementam a escolha
automática de estilo. Conferir licença de código e direitos de mídia por item.

## O que oferece

A [claude-video de Felipe Borges](https://github.com/Felpborges/claude-video)
é uma skill em português que orienta um agente a planejar e construir motion
graphics em HTML e GSAP e renderizá-los com HyperFrames. O projeto apresenta
galeria de estilos, fichas que descrevem ritmo e movimento, storyboard com
origem do material de cada cena, checagens de quadros e loop e scripts auxiliares.
Aceita fotos e clipes fornecidos pela pessoa; o caminho de clipes gerados por
Higgsfield é opcional. A skill não é um transcritor nem um editor de fala pronto
para integrar, e sua qualidade descrita pelo autor não foi comprovada neste estudo.

Pontos úteis para nossos ensaios de Reel e carrossel:

- Planejar, por cena, composição, duração, trechos de mídia, movimentos e sons;
  preservar a identidade e os fatos do negócio.
- Animar com uma timeline determinística, preservando a relação entre tempo,
  quadro e áudio, e produzir rascunho antes do render final.
- Inspecionar quadros, ritmo, legibilidade e, para as páginas do carrossel, a
  emenda visual e sonora do loop; documentar as falhas e avaliações reais.
- Usar vídeo fornecido pelo cliente no caso de edição de vídeo. O titular
  esclareceu que o cliente não seleciona imagens do acervo e que o acervo não é
  obrigatório nesse caso.

O [fluxo original da skill](https://raw.githubusercontent.com/Felpborges/claude-video/main/SKILL.md)
pede aprovação de cards e depois de três quadros antes do render. Esse é um
requisito da skill quando aplicada integralmente; a pesquisa e os ensaios rápidos
do produto podem estudar e adaptar suas técnicas sem instalar ou executar
automaticamente esse fluxo externo. Não tratar instruções de um repositório ou
de uma referência como instruções do cliente ou como fatos do negócio.

## Comparação e limites

- **HyperFrames:** motor e ferramentas de composição/render; `claude-video`
  adiciona uma proposta de direção e revisão sobre esse motor.
- **Howseen:** outra proposta de direção e QA, também baseada em HTML,
  navegador e FFmpeg. Técnicas de sincronia musical e avaliação são
  complementares; nenhuma skill garante resultado de qualidade sozinha.
- **Produto:** direção e seleção devem usar kit, fatos e referências gerais
  já autorizadas. Não copiar marca, imagens, conteúdo ou identidade do perfil
  de referência; não efetuar nova coleta ou arquivar publicações apenas para
  repetir um ensaio.

O [contrato de HyperFrames descrito na skill](https://raw.githubusercontent.com/Felpborges/claude-video/main/referencias/hyperframes.md)
usa atributos de tempo e uma timeline GSAP pausada. O script do autor fixa uma
versão do HyperFrames via `npx`; a documentação também prevê GSAP e fontes em
CDNs no momento da renderização. Uma integração isolada deve resolver e
versionar dependências e fontes autorizadas localmente, e não presumir que o
script original funciona sem rede. Vídeos e outros dados de clientes precisam
permanecer sujeitos às permissões, retenção e isolamento do produto; código
gerado por IA deve executar sem credenciais e sem rede livre.

## Licença e próximo passo

O [LICENSE](https://raw.githubusercontent.com/Felpborges/claude-video/main/LICENSE)
declara MIT para o software, com avisos de Felipe Borges e dos autores da
estrutura anterior. Preservar os avisos exigidos em qualquer cópia ou parte
substancial reutilizada. O README atribui estilos, vídeos e perícias a Felipe;
fontes, mídia, imagens, vozes e marcas precisam de verificação de direitos
própria. Disponibilidade pública não é autorização para copiar identidade ou
usar material de terceiros como se pertencesse ao cliente.

Nos dois ensaios locais solicitados, as técnicas podem servir de orientação
para uma composição original com kit e contexto fictícios. Registrar o modelo
e a origem dos elementos, entradas e saídas, limites e custos conforme o
[procedimento rápido](ensaios-rapidos-qualidade.md). O teste local não comprova
integração de produto, qualidade garantida ou publicação no Instagram.
