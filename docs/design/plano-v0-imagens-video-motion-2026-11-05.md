# Plano de desenvolvimento da v0: imagens, vídeo e carrossel com motion

Data: 05/11/2026. Proposta de trabalho baseada nas decisões do titular, no código
local, nos estudos dos repositórios e nos ensaios existentes. **Este documento é
um plano; não significa que o novo fluxo esteja implementado ou homologado.**

## 1. Resultado desejado

O cliente pede conteúdo em linguagem natural. O sistema usa informações do
negócio e o material que ele fornecer para entregar, para revisão:

1. **Imagem para feed e story:** preservar e concluir a geração já existente,
   com kit, skill e padrões de referências disponíveis.
2. **Vídeo para Reel/feed e story:** orientar uma eventual gravação, receber o
   vídeo do cliente e editá-lo com cortes, transições, movimento, áudio e
   legendas adequados ao conteúdo. O vídeo final terá no máximo 60 segundos,
   por decisão de produto; isso não define a duração da entrada.
3. **Carrossel com motion:** planejar uma sequência coesa e gerar um MP4 curto
   por página, com loop cuidadosamente produzido e prévia ordenada. Uma página
   de vídeo em carrossel é diferente de um Reel. PNG por página é uma opção de
   prévia/fallback a validar, não substitui os MP4s solicitados.

O cliente não precisa escolher estilo nem imagens do acervo. Para vídeo ele
fornece a gravação; acervo é opcional e não deve ser pressuposto. A IA toma as
decisões criativas; HyperFrames/FFmpeg executam composição e codificação. O
cliente revisa a peça antes de aprovar qualquer publicação. Geração integral
de vídeo por IA, avatares e escolha manual de estilos ficam fora deste recorte.
Um pedido de alteração em linguagem natural pode ser desenhado aproveitando a
jornada de revisão existente, sem supor que já funciona para esses formatos.

## 2. Ponto de partida e limites

- A geração de feed/story, skills versionadas e snapshot dos padrões derivados
  de referências já existem localmente. Os ensaios mostraram preferência pelas
  duas imagens com referências, mas há limitações e ajustes pendentes em
  [BL04.3](../evals/bl043-reference-quality-2026-11-04.md); isso não encerra a
  homologação comercial nem demonstra custo por peça aceita.
- O titular preferiu o [Reel v2 do ensaio](../evals/ensaio-motion-referencia-2026-11-05.md).
  É referência de direção para avaliação, não regra universal nem aprovação para
  publicar. Os ensaios foram diretos e não implementam o fluxo no produto.
- Jev pediu esclarecimento para vídeo e carrossel no ensaio; formatos e contratos
  ainda precisam ser estendidos. A transcrição atual aceita áudio e retorna texto,
  não alinhamento por palavra; extração de áudio do vídeo não está integrada.
- O renderer antigo de vídeo é fixo e silencioso, não satisfaz este objetivo. A
  web reproduz uma prévia de vídeo existente, mas ainda não oferece revisão de
  carrossel com vários arquivos. Não confundir esses recursos com o fluxo novo.
- A skill externa `claude-video` foi instalada no Codex e a galeria aberta para
  pesquisa. Isso não instala um serviço para clientes. Três skills próprias de
  Reel, story em vídeo e carrossel já têm versões iniciais no repositório de
  skills, ainda sem integração ou comprovação de qualidade.

## 3. Onde fica cada coisa

| Parte | Lugar recomendado | Responsabilidade |
| --- | --- | --- |
| Instruções criativas próprias | Repositório existente `meu-braco-direito-skills` | Versionar e avaliar skills por formato: briefing, roteiro, narrativa, cortes, legibilidade, som e critérios de revisão. Não é o renderizador. |
| Biblioteca de motion do produto | Inicialmente dentro de `local-spark-platform`, em módulo/pacote próprio a definir | Catálogo versionado de estilos-base, componentes de animação, contratos, exemplos e prévias próprias licenciadas. Evitar um novo repositório até haver necessidade real de ciclo independente. |
| Estilo e contexto de cada negócio | Dados/armazenamento do produto, isolados por negócio e versionados | Ficha derivada do kit, pedido, padrões e evidências autorizadas; snapshot da versão aplicada a cada peça. Dados privados não vão para o Git nem para o repositório global de skills. |
| Geração, custos e fluxo | `local-spark-platform` | Serviços, seleção, autorização, ledger, auditoria, persistência e workflow Temporal; integra adapters dos modelos e do render. |
| Motor de vídeo | Dependências fixadas do worker/ambiente de render do backend | Candidato principal: HyperFrames, com navegador e FFmpeg/FFprobe. Instalar e fixar versões na imagem/ambiente do produto quando a fatia for implementada, não baixar dependências em cada pedido. |
| Experiência do cliente | `local-spark-web` e jornada de mensagens existente | Pedido, recebimento de mídia, progresso, revisão das peças, sequência e download/publicação conforme capacidade comprovada. |

Essa divisão é recomendação para implementação incremental; nomes exatos de
módulos e contratos serão definidos junto às fatias. **A direção é reutilizar
concretamente os materiais abertos**, quando suas licenças permitirem, e não
apenas estudá-los. Podemos incorporar arquivos, adaptá-los e usar o motor no
produto, com origem, versão, licença e avisos preservados. Os diretórios de
Codex e de Claude Code são locais de desenvolvimento, não distribuição do
produto; o servidor precisa receber seus próprios arquivos e dependências.

### O que vamos aproveitar de cada fonte

- [`claude-video`](https://github.com/Felpborges/claude-video): incorporar e
  adaptar instruções, referências técnicas e fichas `ESTILO.md`; avaliar os
  projetos HTML/JS de partida para reaproveitar componentes e composições;
  integrar quando adequados os scripts de medição de movimento, ritmo, loop,
  storyboard e render. A licença MIT permite uso, cópia, modificação e
  comercialização, com preservação dos avisos de copyright e licença, inclusive
  o aviso dos autores da estrutura anterior. O repositório atribui as fichas,
  estilos e vídeos a Felipe; conferir licença e eventuais ativos embutidos por
  item, sem presumir uma proibição geral. Substituir textos, identidade e
  materiais que não forem adequados ao negócio. A maioria dos exemplos é
  horizontal e precisa ser adaptada e testada em vertical.
- [`claude-motion-design`](https://github.com/howseen-ai/claude-motion-design):
  reutilizar/adaptar instruções e código MIT pertinentes a ritmo, transições,
  sincronização e QA. As mídias de terceiros e marcas seguem seus próprios
  termos; preservar avisos e substituir ativos quando necessário.
- [`hyperframes-launches`](https://github.com/heygen-com/hyperframes-launches):
  reutilizar/adaptar composições, configurações e documentação originais da
  HeyGen sob Apache 2.0. O próprio projeto exclui dessa licença mídias, marcas,
  fontes e software de terceiros; substituir ou verificar esses itens e manter
  as condições e avisos aplicáveis. É repositório de composições, não o motor.
- [`motion-por-referencia`](https://github.com/Felpborges/motion-por-referencia)
  e [`showreel-interface`](https://github.com/Felpborges/showreel-interface):
  os READMEs declaram MIT; avaliar e reaproveitar scripts de perícia, componentes,
  transições, som e ferramentas de aceite que acrescentem valor, com atribuição.
- [`skill-reel`](https://github.com/Felpborges/skill-reel): o README mostra
  instalação e uso, mas não encontramos licença geral de redistribuição do código;
  verificar a autorização antes de incorporar trechos ao produto.
- [HyperFrames](https://github.com/heygen-com/hyperframes): integrar como
  dependência de render, com versão fixada após validação local de funcionamento,
  desempenho, segurança e licenças. Não baixar pacotes por pedido.
- [`criador-de-carrosseis-simples`](https://github.com/Felpborges/criador-de-carrosseis-simples):
  o README orienta instalar e usar a skill; a licença geral para copiar,
  modificar e redistribuir no nosso produto não ficou clara na consulta.
  Verificar autorização específica antes dessa incorporação; isso não impede
  avançar com as demais fontes nem avaliar a skill em desenvolvimento.

### Cópias próprias e independência dos repositórios externos

O titular pediu que uma remoção de um repositório externo não interrompa o
produto. Para cada projeto e versão que adotarmos, criar e manter sob nosso
controle uma cópia completa dos arquivos necessários, inclusive dependências e
ativos cuja cópia seja permitida, com licença, avisos, commit de origem, data,
manifesto e hashes. Preservar o código original separado das nossas adaptações.
Um fork no GitHub, sozinho, não é plano completo de preservação: manter cópia e
backup independentes sob controle do projeto, incluindo os objetos reais de Git
LFS e submódulos quando existirem. Verificar integridade e restauração; arquivos
locais ignorados pelo Git ou disponíveis apenas no computador não são backup.

Distribuição proposta:

- **Fontes originais preservadas:** propor um único repositório próprio privado
  para snapshots dos projetos externos utilizados, com diretórios separados e
  histórico/origem identificados; mídias grandes permitidas podem usar
  armazenamento versionado próprio. Manter backup independente de ambos.
  Confirmar direitos antes de armazenar ou redistribuir cada mídia e documentar
  exceções. Nenhum repositório remoto, backup ou cópia de todos os projetos foi
  criado ainda por este plano.
- **Skills próprias adaptadas:** `meu-braco-direito-skills`, com origem e avisos
  dos trechos reutilizados. A cópia de código executável e estilos técnicos
  aprovados pode ficar no repositório da plataforma ou pacote interno próprio;
  não é necessário criar um repositório separado para cada projeto externo.
- **Produto implantado:** empacotar no artefato da aplicação/worker os arquivos
  de skill, fichas, scripts e componentes necessários, e usar dependências
  fixadas em imagens versionadas. Para fontes, motor, navegador e dependências
  transitivas, manter artefatos próprios conforme licença e arquitetura de
  deploy, com manifesto, hashes, backup e plano de reconstrução; pin de versão
  ou lockfile isolado não garante disponibilidade futura.
- **Operação:** geração e render não baixam instruções, scripts, bibliotecas ou
  mídia do GitHub por pedido. Pode haver chamadas explicitamente autorizadas aos
  provedores de modelos e transcrição; não confundir essas dependências com a
  disponibilidade do repositório do autor.

Validar a independência em teste de integração: bloquear o acesso aos repositórios
externos, executar uma geração com provedores simulados e render local a partir
apenas dos artefatos internos, conferir hashes, e restaurar um backup em ambiente
de teste. Documentar o que é reproduzível offline e qualquer dependência externa
remanescente. Atualizações das fontes entram deliberadamente como nova versão,
com revisão, testes e possibilidade de voltar à versão anterior; nunca por
atualização automática em cada pedido.

### Integração concreta da `claude-video`

1. Preservar uma cópia própria da versão da fonte instalada, registrar commit e licença;
   avaliar suas instruções, 21 fichas, projetos e scripts. Catalogar o que
   será incluído, adaptado, substituído ou excluído e a razão. Não depender de
   `~/.codex/skills` no servidor ou copiar todos os arquivos sem avaliação.
2. Versionar a adaptação das instruções no repositório de skills próprio;
   manter o arquivo de origem, avisos e atribuição onde trechos forem copiados.
   Empacotar snapshots aprovados no backend e estender
   `app/services/visual_skills.py`: hoje ele lê apenas arquivos de feed/story
   em `app/assets/visual_skills`, verifica hashes e não carrega a pasta Codex
   nem o repositório vizinho automaticamente.
3. Incluir fichas/estilos autorizados e úteis no catálogo interno, com origem,
   versão, formatos e limitações, adaptando composição para 9:16. Selecionar
   automaticamente com pedido, kit e material; o cliente não vê uma galeria
   obrigatória. Prévias externas podem apoiar a equipe conforme seus direitos.
4. Enviar ao modelo de direção a skill de formato mais as instruções e ficha
   selecionadas, kit, pedido, padrões disponíveis e mídia autorizada. A saída
   deve registrar roteiro, cenas, cortes, transições, textos, áudio e movimento.
   Não pressupor que um texto de skill dê acesso por si só a arquivos e ferramentas.
5. Adaptar os scripts úteis para o executor isolado: `pericia-movimento.py`
   mede mudanças entre quadros e cortes; `ritmo.py` avalia ritmo visual;
   `loop.py` avalia emenda; os demais auxiliam frames e storyboard. Essas
   medições não avaliam áudio nem substituem revisão humana. O `render.sh`
   original invoca `npx` com download de versão; substituí-lo ou adaptá-lo para
   o HyperFrames empacotado e fixado, sem dependência de rede por geração.
6. O worker, controlado por Temporal, executa as ferramentas com limites de
   recursos e sem credenciais do produto, gera MP4s, guarda versões e resultados
   das checagens e apresenta prévia. Testar qualidade, isolamento, orçamento e
   falhas antes de liberar. As perguntas e aprovações interativas da skill
   original devem ser adaptadas à jornada do produto, com revisão da peça pelo
   cliente e sem obrigá-lo a escolher estilo.

Os itens acima são o plano de implementação e ainda não estão integrados. Os
arquivos externos em análise são entradas técnicas, não instruções que
substituem regras de produto ou dados confirmados do cliente.

## 4. Como produzir um estilo adequado a cada negócio

1. **Reunir contexto autorizado:** segmento e descrição do negócio, pedido,
   kit, fatos confirmados, material enviado e padrões das referências já
   escolhidas. Registrar versões e origem, incluindo análise parcial ou ausente.
2. **Escolher uma base:** o sistema seleciona automaticamente um estilo-base
   próprio adequado ao pedido, material e personalidade da marca; nenhum estilo
   é escolhido apenas por segmento. Se não houver contexto suficiente, usa
   base neutra testada e sinaliza a limitação, sem bloquear o cliente.
3. **Criar uma ficha por negócio e peça:** adaptar ritmo, tipografia em
   movimento, transições, densidade visual e tratamento de som ao kit, ao
   formato e ao objetivo. A direção por cena continua sendo criada para cada
   pedido; a ficha não transforma todas as peças em um template idêntico.
4. **Distinguir observação de proposta:** padrões atuais de perfis são visuais
   e editoriais. Eles podem orientar uma hipótese de movimento, mas não provam
   como um vídeo se move ou soa. A análise temporal de um vídeo de referência
   só poderá ser oferecida depois de implementada, com fonte autorizada, regras
   de coleta, direitos e evidência de ritmo, transições ou som medidos.
5. **Guardar decisão reproduzível:** identificar versão/hash do estilo-base,
   ficha e skill, snapshots de kit/referências e material, justificativa,
   observações, suposições e direção efetivamente usada. Só guardar dados ou
   mídias de terceiros permitidos pelas políticas do produto.

O kit do negócio prevalece sobre a identidade de uma referência. Não reproduzir
logotipos, textos ou peças de terceiros. A galeria externa pode inspirar a
criação de um pequeno catálogo próprio; não é preciso disponibilizá-la ou
reproduzir seus vídeos para o cliente. Padrões de um negócio não devem afetar
outro. A decisão de persistir uma ficha reutilizável por negócio, além dos
snapshots por geração, deverá ser validada nos ensaios e no desenho de dados.

## 5. Sequência de desenvolvimento e critérios de saída

As fatias são pequenas e revisáveis; o trabalho criativo e a integração podem
avançar em paralelo onde não houver dependência. Nada desta lista representa
uma entrega já realizada.

### 0 — Alinhar contratos de produto e evidências

- Consolidar a preferência pelo Reel v2 e as falhas identificadas; preservar
  os traces dos ensaios, inclusive Jev, transcrição e correção manual.
- Definir formatos e estados do pedido, roteiro, mídia de entrada, saída e
  revisão. Identificar o que já funciona em imagem e as pendências de BL04.3.
- Preparar casos fictícios separados para Reel gravado, story gravado e
  carrossel; incluir fala, cenário sem fala e material insuficiente.
- **Saída:** casos reproduzíveis, matriz de formatos e lacunas priorizadas.

### 1 — Ensaios rápidos e catálogo inicial

- Usar o procedimento de [ensaios rápidos](ensaios-rapidos-qualidade.md):
  mensagem simulada, Jev real ou explicitamente simulado, inputs/outputs dos
  modelos, kit, skills, referências, decisões e resultados; sem montar banco
  novo ou sistema completo para julgar criatividade.
- Reutilizar fichas e componentes permitidos da galeria e das fontes, adaptá-los para
  hipóteses distintas e versões verticais; comparar com contexto e mídia iguais.
  Reel v2 é uma direção inicial, não padrão obrigatório para todo negócio.
- Fazer ensaios separados de vídeo e carrossel; ouvir áudio, assistir movimento
  e conferir legibilidade, cortes, sincronização e emenda do loop. Mostrar peças
  e trace ao titular. Registrar limitações e custo/tempo de cada tentativa.
- Antes de nova chamada paga, apresentar quantidade, modelos, preços vigentes,
  reserva e risco; usar autorização e ledger específicos da rodada.
- **Saída:** pelo menos uma direção aprovada para continuar desenvolvendo em
  cada caso testado e evidências das rejeições. Preferência em ensaio não é
  aceite de publicação nem prova de integração ou de custo comercial.

### 2 — Contratos, interpretação e roteiro

- Estender intenção do Jev e serviços para distinguir imagem feed/story, Reel,
  story em vídeo e carrossel; solicitar esclarecimento quando faltar material
  ou intenção, preservando compatibilidade das mensagens atuais.
- Integrar skills próprias por versão/hash; orientar roteiro de gravação sem
  inventar informações, com marca, duração e linguagem adequadas ao negócio.
- Definir um contrato estruturado e validado de roteiro e direção: cenas,
  tempo, fontes de mídia, cortes, textos, voz, trilha, efeitos, transições,
  formato e restrições; validar que os trechos existem e preservam o sentido.
- **Saída:** testes de intenção, contexto, roteiros e erros; trace claro e
  nenhuma promessa de edição antes de renderizar e avaliar a peça.

### 3 — Mídia do cliente, transcrição e alinhamento

- Receber vídeo com autorização e associá-lo ao negócio e pedido; verificar
  tamanho, duração, formato, áudio e processamento, usando armazenamento e
  permissões existentes. Definir retenção, limites de entrada e mensagens de
  erro antes de liberar uso real.
- Extrair áudio quando existir e reaproveitar o serviço de transcrição; avaliar
  estratégia de timestamps por trecho/palavra e sua precisão. Tratar silêncio,
  ruído, transcrição equivocada e opção de não ter legendas de fala.
- Preservar gravação original e versão editada; decidir cortes e sincronização
  a partir de mídia válida, não presumir acervo. O roteiro não deve atribuir
  ao cliente falas que ele não disse.
- **Saída:** extração e alinhamento comprovados com fala autorizada, sem fala e
  áudio problemático; testes de isolamento, limites e erros.

### 4 — Biblioteca e seleção automática de motion

- Integrar fichas e componentes permitidos, adaptados ao catálogo inicial versionado, com estilo-base, capacidades,
  exemplos originais, formatos compatíveis e restrições.
- Implementar seleção fundamentada no pedido/contexto e construção da ficha de
  direção; prever fallback, fonte dos padrões, proveniência e snapshots.
- Acrescentar análise temporal de referência em etapa própria somente se houver
  acesso e direitos adequados; não anunciar que já inferimos ritmo de imagens.
- **Saída:** seleção rastreável para negócios distintos, fidelidade ao kit,
  teste sem referência e isolamento entre negócios; validar diferença visual
  real em ensaios, não apenas um nome de estilo no trace.

### 5 — Render seguro e primeiro Reel do início ao fim

- Construir adapter de HyperFrames e ferramenta de mídia com versões fixadas;
  avaliar contrato de saída e licenças antes de adotar em produção.
- Converter a direção em composição/linha do tempo e renderizar rascunho e
  final. Implementar cortes, transições, tipografia cinética, legenda alinhada
  quando houver fala, tratamento e mixagem de som conforme a direção e os
  direitos disponíveis. Render com código gerado por IA é não confiável: isolar
  processo/contêiner sem segredos e sem rede livre, restringir arquivos, CPU,
  memória, duração e saídas; validar assets e formato.
- Em runtime, Temporal controla execução; efeitos têm identidade durável,
  idempotência, ledger, auditoria e outbox conforme serviços existentes; sem
  rede sob locks. Prever falha, retomada, operação incerta e limite de custo.
- **Saída:** Reel de vídeo enviado, até 60 s, revisável e reproduzível, com
  áudio e legendas conferidos, testes de segurança, falhas, custo e qualidade.

### 6 — Story em vídeo

- Reutilizar pipeline de mídia e render, com skill, duração e composição
  adequadas ao story; validar área segura, formato, legibilidade e áudio.
- Exercitar o cenário com vídeo do cliente, com e sem fala, e revisão na web.
- **Saída:** story em vídeo gerado e revisável; comprovar especificações do
  canal e identificar quaisquer restrições de publicação por tipo de conta.

### 7 — Carrossel com motion

- Gerar narrativa e direção por página, garantindo continuidade e ordem;
  definir limites de páginas e duração de cada MP4 após validação técnica e de
  custo. Planejar movimento, som e começo/fim do loop para cada página.
- Modelar coleção ordenada de artefatos, cada página com identidade e estado;
  prever falha parcial, reprocessamento idempotente, revisão da sequência e
  download das páginas, sem achatar tudo em um único vídeo.
- Criar prévia móvel, confirmar a emenda dos loops e testar como o Instagram
  reproduz e publica cada vídeo; não prometer loop infinito ou música contínua
  entre páginas. Decidir PNG de apoio e compatibilidade conforme ensaio real.
- **Saída:** coleção ordenada de MP4s aprovada para continuar, revisão e
  download funcionais; publicação automática depende de validação própria.

### 8 — Jornada integrada, avaliação e preparação da v0

- Na web/mensagens, exibir progresso e estados compreensíveis, pedido de mídia
  quando necessário, prévias, som, erros e recuperação; permitir revisão das
  imagens, do vídeo e das páginas na ordem, com ação explícita antes de publicar.
- Validar acessibilidade, tela pequena, segurança de acesso, falha parcial,
  revisão e preservação de histórico. Testar saída em aparelhos e na rede alvo.
- Confirmar viabilidade de publicação para cada tipo de conta e formato com
  a versão corrente da API; onde não houver comprovação, oferecer arquivos
  para download e deixar publicação automática pendente, sem simular sucesso.
- Fechar qualidade com o titular para cada formato e diferentes negócios,
  fidelidade ao kit, qualidade de áudio/cortes/legenda, fatos, direitos,
  tempo e custo medido por peça aceita, incluindo refações.
- **Saída:** jornada integrada revisada, critérios de qualidade e operação
  cumpridos; declarar separadamente funções ainda não homologadas.

## 6. Verificação, custo e decisões em aberto

Ensaios criativos seguem o procedimento rápido. Testes de integração, banco,
workflow, RLS, autenticação, concorrência, idempotência e recuperação são
separados: usam PostgreSQL próprio `_test`, logins restritos e serviços locais.
Mudanças de backend exigem testes significativos e `make ci` com 100% de linhas
e branches; a web segue suas próprias regras de cobertura e validação visual.
Teste rápido não substitui CI nem comprova publicação.

Medir por formato e etapa: duração e tamanho da entrada, minutos transcritos,
uso de modelos, reservas, tempo/recursos de render, armazenamento, tentativas,
revisões e valores faturados quando disponíveis. Orçamento deve cobrir modelos,
transcrição, render, mídia e refações; teto de 60 s na saída não limita sozinho
os custos de uma entrada longa. Uma reserva pode ser ultrapassada por uma
chamada cujo fornecedor não fornece teto garantido.

Pendências para decidir com evidência e, quando necessário, entrevista:

- duração/tamanho máximos de entrada e quantidade de clipes por pedido;
- número e duração de páginas, especificações e direitos de trilha/efeitos;
- retenção de mídia, limites de refação, preços e cotas de planos;
- tempo de processamento aceitável, estrutura de custos e critério de aceite;
- persistência e atualização de estilo por negócio e eventual análise de vídeos
  de referência, com autorização e regras próprias;
- caminho de publicação/manual, capacidades da conta e comportamento de loop
  conforme versão da API e teste real.

Fontes oficiais consultadas em 05/11/2026: [especificação de Reel pela Meta](https://www.postman.com/meta/instagram/folder/830j7my/reels-publishing)
aceita 3 s a 15 min, sendo 9:16 recomendado; nosso máximo de 60 s é escolha
própria. A [coleção Instagram da Meta](https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api?entity=request-23987686-15c537cd-a773-4b40-a87c-27829e49a439)
descreve condições de conta e Stories. Revalidar limites, API, publicação de
carrosséis com vídeos e reprodução em loop no momento da implementação.
