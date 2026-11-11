# Plano de desenvolvimento da v0: imagens, vídeo e carrossel com motion

**Prioridade atual, 06/11:** experimentar o
[ciclo de revisão de Reel](../evals/plano-ciclo-revisao-motion-2026-11-06.md),
com critérios versionados, até duas correções e comparação humana da mesma
composição inicial. O protótipo privado está implementado; a rodada de três casos
tem teto autorizado de US$ 6,75 em reservas e até 15 chamadas, conforme o plano.
A avaliação do clipe pessoal continua pendente. A sequência histórica
abaixo preserva o contexto de suas rodadas; publicação continua posterior.

Esclarecimento de 06/11/2026: o v2 é piso mínimo aceito, não composição a
reproduzir. A [nova rodada preparada](../evals/plano-motion-biblioteca-2026-11-06.md)
usa exemplos reais da biblioteca e skill própria, com demonstração comparativa
HTML após geração. Aprovação de orçamento adicional permanece separada.

Atualização de 06/11/2026: o titular escolheu [um comando para o ensaio rápido](../evals/como-executar-ensaio-motion.md),
com avaliação somente do MP4 final. As aprovações intermediárias de cards/frames
da skill foram dispensadas para esse modo; não ampliar isso para publicação.
Preparação de cenário, seleção criativa e dependências ficam reutilizáveis;
cada execução preserva inputs, resposta, código, custo e trace. A primeira
fixture não demonstra entrada arbitrária nem a integração completa do produto.

Data: 05/11/2026. Proposta de trabalho baseada nas decisões do titular, no código
local, nos estudos dos repositórios e nos ensaios existentes. **Este documento é
um plano; não significa que o novo fluxo esteja implementado ou homologado.**

As entrevistas de 05/11 confirmaram os limites e o critério de conclusão abaixo.
Decisões aceitas estão em [DECISIONS](../DECISIONS.md); dúvidas remanescentes
de produto devem ser resolvidas por entrevista antes da implementação dependente.
Na revisão posterior de prioridades, o titular separou a entrega das peças finais
da integração de postagem. Este plano reflete a nova ordem: geração primeiro;
viabilidade Meta e fluxo de postagem depois.

## Histórico — retomada criativa de 06/11/2026

Após a rejeição dos três formatos 1c, o trabalho imediato é o
[ensaio de qualidade](../evals/plano-retomada-qualidade-motion-2026-11-06.md),
começando por um Reel com a mesma mídia/kit. O v2 é patamar mínimo de qualidade;
sua direção concreta deve entrar na avaliação. Reutilizar código permitido de
`cartaz-gritado`, `cartaz-risografia` e `diagrama-azul-marinho` conforme a direção
automática escolhida, sem impor os três estilos ou um padrão universal.
Preservar resposta bruta, adaptações e peças comparáveis. Integrações de WhatsApp
e Instagram ficam fora desta prova; as fases de produto abaixo são o roteiro
posterior, não requisitos para executar o ensaio.

O executor privado reproduziu o MP4 WAAPI anterior com hash idêntico nesta
configuração. Isso confirma reprodução local, não uma peça criativa nova nem
o renderer de produção. Após a preparação, o titular autorizou duas chamadas
até US$ 1,50 adicionais e o envio do pacote local. A primeira concluiu e gerou
cinco cards, já capturados e aguardando aceite. A segunda depende desse aceite
e ainda não ocorreu; nenhum vídeo novo foi gerado. Custos, autorização e arquivos
constam no plano específico.

## 1. Resultado desejado

O cliente pede conteúdo em linguagem natural. O sistema usa informações do
negócio e o material que ele fornecer para entregar, para revisão:

1. **Imagem para feed e story:** preservar e concluir a geração já existente,
   com kit, skill e padrões de referências disponíveis.
2. **Vídeo para Reel/feed e story:** orientar uma eventual gravação, receber o
   vídeo do cliente e editá-lo com cortes, transições, movimento, áudio e
   legendas adequados ao conteúdo. O vídeo final terá no máximo 60 segundos,
   por decisão de produto. A edição recebe inicialmente **uma gravação do cliente
   por pedido, com até 60 segundos de material bruto e 50 MiB**. Se o tamanho
   ou a duração exceder o limite, explicar o motivo e pedir uma versão menor,
   sem cortar a gravação automaticamente.
3. **Carrossel com motion:** planejar uma sequência coesa e gerar um MP4 curto
   por página, com loop cuidadosamente produzido e prévia ordenada. A IA escolhe
   **de 3 a 5 páginas em 4:5 vertical, cada MP4 com 5 a 8 segundos**, conforme conteúdo e leitura.
   Esses limites precisam ser validados em qualidade, custo e arquivos finais. Uma página
   de vídeo em carrossel é diferente de um Reel. PNG por página é uma opção de
   prévia/fallback a validar, não substitui os MP4s solicitados.

O cliente não precisa escolher estilo nem imagens do acervo. Para vídeo ele
fornece a gravação; acervo é opcional e não deve ser pressuposto. A IA toma as
decisões criativas; o executor materializa composição e codificação. A base atual
usa compilador próprio DOM/WAAPI, navegador e FFmpeg; HyperFrames foi estudado
como candidato, mas não é dependência desse caminho. O empacotamento e a
validação do executor de produção continuam pendentes. O
cliente revisa e aprova a peça final; autorização de postagem pertence à fase
posterior. Geração integral
de vídeo por IA, avatares e escolha manual de estilos ficam fora deste recorte.
O cliente pode pedir alterações em linguagem natural, aproveitando a jornada
prevista de revisão; isso ainda não está integrado para os novos formatos.
No carrossel, um ajuste em uma página preserva as demais. Se a mudança exigir
alterá-las, pedir confirmação do cliente antes de aplicá-la; a versão resultante
sempre exige nova revisão/aprovação da peça completa. Isso não autoriza postagem;
C11 segue vigente para publicação futura.

**A entrega atual termina com geração, prévia, ajustes, aprovação da peça e
download dos arquivos finais.** O titular adiou a verificação da viabilidade e a
integração de postagem no Instagram para uma fase posterior, substituindo a
exigência anterior de publicação nesta entrega. Conta Meta, permissões da API e
postagem real não são critérios de conclusão da geração. Os arquivos terão as
características pretendidas de cada formato, sem declarar compatibilidade de
postagem ainda não comprovada. Concluir geração não significa entregar publicação.

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
| Motor de vídeo | Dependências fixadas do worker/ambiente de render do backend | Compilador próprio DOM/WAAPI, navegador e FFmpeg/FFprobe, com provas locais já executadas. Fixar e empacotar as dependências de produção; não baixar por pedido. |
| Experiência do cliente | `local-spark-web` e jornada de mensagens existente | Pedido, recebimento de mídia, progresso, revisão das peças e sequência, ajustes, aprovação da peça e download final; integração de postagem em fase posterior. |

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
- [HyperFrames](https://github.com/heygen-com/hyperframes): candidato estudado
  nos ensaios anteriores; a implementação atual usa DOM/WAAPI próprio e não
  exige esse pacote. Uma adoção futura dependeria de validação de funcionamento,
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

- **Fontes originais preservadas:** o titular autorizou criar um repositório
  próprio privado no GitHub quando necessário, informando nome e link após criar.
  A proposta é um único repositório para snapshots dos projetos externos
  utilizados, com diretórios separados e
  histórico/origem identificados; mídias grandes permitidas podem usar
  armazenamento versionado próprio. Manter backup independente de ambos.
  Confirmar direitos antes de armazenar ou redistribuir cada mídia e documentar
  exceções. Em 06/11, o repositório próprio informado pelo titular recebeu
  localmente `snapshots/claude-video-2026-11-05`: 24 arquivos originais, 30 no
  pacote, com licenças e verificação offline. README/Git preservados, sem
  commit/push; privacidade remota não verificada. O snapshot não é espelho
  completo ou backup remoto e não inclui mídias, fontes tipográficas ou
  dependências externas; seus direitos/empacotamento continuam pendentes.
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
   o executor próprio e suas dependências empacotadas, sem rede por geração.
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
2. **Escolher uma base:** a cada pedido, o sistema seleciona automaticamente um
   estilo-base próprio adequado ao pedido, material e personalidade da marca; nenhum estilo
   é escolhido apenas por segmento. Se não houver contexto suficiente, usa
   base neutra testada e sinaliza a limitação. Essa saída é apenas para falta de
   sinais de estilo; fatos ou gravação indispensáveis ausentes exigem esclarecimento.
   Na v0 não há estilo fixo aprendido das peças aprovadas nem preferência de motion
   persistida por negócio: escolher conforme objetivo, material e referências de
   cada pedido, preservando a identidade do kit. Manter snapshots por peça.
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
outro. Uma ficha reutilizável de preferência por negócio fica fora desta v0;
as fichas e decisões por geração permanecem preservadas no respectivo snapshot.

## 5. Sequência de desenvolvimento e critérios de saída

Execução iniciada: skills empacotadas, contrato puro, elegibilidade explícita no
adapter Jev e inspeção/extração de áudio validados em testes dirigidos. Amostra
técnica original de `claude-video` preservada localmente com licenças, hashes
e verificador de arquivo/restauração. O primeiro CI integral passou (4.913 testes,
2 pulados por binários no PATH, 100% de linhas/ramos). Fases que exigem
integração, render, backup independente ou avaliação criativa não estão concluídas
por essas fatias; o produto ainda não habilita os novos formatos.

O [ensaio do Reel em WAAPI](../evals/ensaio-reel-waapi-2026-11-05.md) passou
nas verificações técnicas sem nova chamada paga; o titular aprovou avançar com
essa base técnica para o caso testado, sem fixar o estilo dos demais negócios.
Ele usa composição específica e ainda não compila o contrato geral. A alternativa
HTML/WAAPI própria com navegador e FFmpeg foi implementada nas fatias abaixo;
não exige o pacote completo HyperFrames. Executor e distribuição de produção
continuam sujeitos à validação. O reaproveitamento das fichas, scripts e fontes
permitidas continua no escopo, independentemente do motor escolhido.

O segundo bloco implementa contrato v2, tradutor de snapshots confiáveis e
compilador visual próprio com keyframes/fades/texto seguro; o CI completo passou
(4.987 testes Python sem pulados e 62 Node, cobertura integral). Ele ainda não
renderiza MP4 no produto ou integra
os novos formatos na jornada. O aceite da peça exige o
[contrato próprio sem postagem](revisao-peca-sem-postagem-2026-11-05.md).

O terceiro bloco acrescenta catálogo de três fichas próprias, builder de contexto
e plano técnico de áudio. CI integral passou: 5.042 testes Python e 62 Node,
sem pulados e com cobertura de 100%.
Protótipos isolados executaram o compilador e a mixagem com sinais sintéticos,
sem chamada paga ou avaliação criativa. Direção por modelo, renderer de produção,
empacotamento, persistência e jornada continuam pendentes.

Na retomada de 06/11/2026, conferido o CI da correção Jev sem candidatos:
**5.044 testes Python e 62 Node**, sem pulados e com cobertura de 100%.
A rodada 1b parou após uma interpretação real; ainda não produziu peças
criativas. A [continuação 1c](../evals/plano-motion-v0-rodada-1c-2026-11-05.md)
foi autorizada e suas sete chamadas foram concluídas, mantendo o teto global
de US$ 1,60 e a reserva anterior. Isso não conclui as fases de integração.

O [resultado 1c](../evals/ensaio-motion-v0-rodada-1c-2026-11-06.md)
inclui Reel, story e três páginas de carrossel gerados com intervenções locais
explícitas. As três direções completaram no provedor, mas foram rejeitadas pelo
contrato, preservado no trace. O titular autorizou a retomada e a revisão
automática permitiu a chamada final com as rejeições informadas. Nenhuma
chamada foi repetida. Custo global estimado US$ 0,263073, reservas US$ 1,55.
Aceite criativo continua pendente. Descrições do contrato foram melhoradas
somente após os efeitos pagos; o CI da nova fatia foi interrompido a pedido do
titular (saída 143), sem resultado final. O baseline aprovado de 5.044 testes
Python e 62 Node acima pertence à correção anterior.

Estado por fase neste ponto (não confundir módulos isolados com critério de saída):

| Fase | Situação |
| --- | --- |
| 1 — Base e CI | Base validada; cada nova fatia continua exigindo CI próprio. |
| 2 — Fontes e dependências | Amostra original, licenças e restauração local prontas; pacote de produção e backup independente pendentes. |
| 3 — Ensaios e catálogo | Três fichas próprias e direções reais dos três formatos; derivados locais em revisão, sem aceite criativo da rodada 1c. |
| 4 — Contratos e roteiro | Contrato v2, builder e elegibilidade no adapter prontos; admissão e estados duráveis ainda não integrados. |
| 5 — Mídia e fala | Inspeção/extração local e plano de áudio prontos; transcrição integrada, alinhamento e semântica dos cortes pendentes. |
| 6 — Primeiro Reel integrado | Compilador próprio e provas isoladas; modelo, executor e fluxo durável ainda não integrados. |
| 7 — Story em vídeo | Perfil 9:16 e peça experimental montada; aceite criativo e jornada pendentes. |
| 8 — Carrossel | Contrato 3–5 páginas, 5–8 s e perfil 4:5 prontos; coleção durável e refação seletiva pendentes. |
| 9 — Revisão e download | Contrato de aceite sem postagem documentado; API e interface pendentes. |
| 10 — Qualidade e operação | Critérios definidos; homologação, custos por peça aceita e recuperação do fluxo completo pendentes. |

As dez fases abaixo concluem a geração das peças finais. São pequenas e
revisáveis; o trabalho criativo e a integração podem avançar em paralelo onde
não houver dependência. A
[matriz e os casos da etapa 0](v0-motion-etapa-0-formatos-e-casos.md) já foram
registrados; as integrações e os critérios de qualidade da geração abaixo
continuam pendentes. A integração de postagem é um bloco posterior separado.

### 1 — Fechar a base atual e o CI

- Consolidar a preferência pelo Reel v2 e as falhas identificadas; preservar
  os traces dos ensaios, inclusive Jev, transcrição e correção manual.
- Definir formatos e estados do pedido, roteiro, mídia de entrada, saída e
  revisão. Identificar o que já funciona em imagem e as pendências de BL04.3.
- Preparar casos fictícios separados para Reel gravado, story gravado e
  carrossel; incluir fala, cenário sem fala e material insuficiente.
- Manter o CI aprovado a cada fatia, com PostgreSQL `_test`, logins restritos
  e 100% de cobertura de linhas/ramos, preservando alterações locais.
- **Saída:** casos reproduzíveis, matriz de formatos e lacunas priorizadas,
  base atual validada. Documentos e casos existem; CI do primeiro bloco concluído.

### 2 — Preservar e empacotar fontes e dependências

A [revisão dos binários e do pacote Linux](motion-dependencias-linux-2026-11-05.md)
registra versões/hashes/avisos locais e a próxima aquisição controlada. O alvo
Docker publicado atualmente não contém o conjunto motion; binários macOS dos
ensaios não são artefatos de deploy. Arquitetura e pacote Linux ainda precisam
ser confirmados e preservados, com fontes correspondentes e teste sem rede.

- Aplicar a estratégia de cópias próprias acima: revisar direitos por item,
  preservar originais e licenças, registrar versões/hashes e separar adaptações.
  Criar o repositório privado autorizado quando necessário e informar nome/link.
- Empacotar as três skills próprias, fichas, scripts, componentes e dependências
  aprovados. Não ler diretórios pessoais nem baixar fontes por pedido no produto.
- Manter backup independente e testar restauração. Verificar a integridade dos
  artefatos e, com o render disponível, executar a prova sem repositórios externos.
- **Saída:** fontes adotadas sob controle próprio, pacotes verificáveis e backup
  restaurado; independência de execução validada antes de concluir a geração.

### 3 — Ensaios rápidos e catálogo inicial

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

### 4 — Contratos, interpretação e roteiro

A [admissão durável sem item obrigatório](admissao-motion-sem-item-2026-11-05.md)
detalha a próxima fatia de integração. Lista de candidatos vazia não prova ausência
de produto na mensagem; material/fatos devem ter origem e validade próprias.
O agrupamento temporal de mensagens não comprova vínculo ao mesmo pedido.

- Estender intenção do Jev e serviços para distinguir imagem feed/story, Reel,
  story em vídeo e carrossel; solicitar esclarecimento quando faltar material
  ou intenção, preservando compatibilidade das mensagens atuais.
- Integrar skills próprias por versão/hash; orientar roteiro de gravação sem
  inventar informações, com marca, duração e linguagem adequadas ao negócio.
  Os textos locais já foram alinhados à gravação obrigatória na edição, teto de
  60 segundos, carrossel de 3–5 páginas/5–8 segundos e PNG opcional; empacotamento
  e validação pelo integrador permanecem pendentes.
- Definir um contrato estruturado e validado de roteiro e direção: cenas,
  tempo, fontes de mídia, cortes, textos, voz, trilha, efeitos, transições,
  formato e restrições; validar que os trechos existem e preservam o sentido.
- **Saída:** testes de intenção, contexto, roteiros e erros; trace claro e
  nenhuma promessa de edição antes de renderizar e avaliar a peça.

### 5 — Mídia do cliente, transcrição e alinhamento

- Receber uma gravação de até 60 segundos com autorização e associá-la ao negócio
  e pedido; verificar tamanho, duração, formato, áudio e processamento, usando
  armazenamento e permissões existentes. O limite confirmado é 50 MiB;
  excedentes de tamanho ou duração pedem versão menor, sem corte automático.
  Aplicar C04 aos envios WhatsApp
  associados e C09 às prévias concluídas, sem expiração automática com conta ativa.
  Encerramento continua adiado em P03; categorias temporárias e canais ainda não
  cobertos precisam de política explícita sem reabrir as regras já aprovadas.
- Extrair áudio quando existir e reaproveitar o serviço de transcrição; avaliar
  estratégia de timestamps por trecho/palavra e sua precisão. Tratar silêncio,
  ruído, transcrição equivocada e opção de não ter legendas de fala.
- Preservar gravação original e versão editada; decidir cortes e sincronização
  a partir de mídia válida, não presumir acervo. O roteiro não deve atribuir
  ao cliente falas que ele não disse.
- **Saída:** extração e alinhamento comprovados com fala autorizada, sem fala e
  áudio problemático; testes de isolamento, limites e erros.

### 6 — Seleção automática e primeiro Reel integrado

- Integrar fichas e componentes permitidos, adaptados ao catálogo inicial versionado, com estilo-base, capacidades,
  exemplos originais, formatos compatíveis e restrições.
- Implementar seleção fundamentada no pedido/contexto e construção da ficha de
  direção; prever fallback, fonte dos padrões, proveniência e snapshots.
- Acrescentar análise temporal de referência em etapa própria somente se houver
  acesso e direitos adequados; não anunciar que já inferimos ritmo de imagens.
- Validar seleção rastreável para negócios distintos, fidelidade ao kit,
  ausência de referência e isolamento; comprovar diferenças visuais reais,
  não apenas um nome de estilo no trace.
- Integrar e validar o executor próprio DOM/WAAPI e ferramentas de mídia com
  versões fixadas; empacotar dependências e avisos e verificar isolamento antes
  de adotar em produção. O protótipo local não substitui essa validação.
- Converter a direção em composição/linha do tempo e renderizar rascunho e
  final. Implementar cortes, transições, tipografia cinética, legenda alinhada
  quando houver fala e a legenda for adequada ao pedido, tratamento e mixagem de
  som conforme a direção e os direitos disponíveis. A saída da IA é dado
  declarativo não confiável; o executor usa somente código próprio. Isolar
  processo/contêiner sem segredos e sem rede livre, restringir arquivos, CPU,
  memória, duração e saídas; validar assets e formato.
- Em runtime, Temporal controla execução; efeitos têm identidade durável,
  idempotência, ledger, auditoria e outbox conforme serviços existentes; sem
  rede sob locks. Prever falha, retomada, operação incerta e limite de custo.
- **Saída:** Reel de vídeo enviado, até 60 s, revisável e reproduzível, com
  áudio e legendas conferidos, testes de segurança, falhas, custo e qualidade.

### 7 — Story em vídeo

- Reutilizar pipeline de mídia e render, com skill, duração e composição
  adequadas ao story; validar área segura, formato, legibilidade e áudio.
- Exercitar o cenário com vídeo do cliente, com e sem fala, e revisão na web.
- **Saída:** story em vídeo gerado e revisável, com arquivo, área segura,
  leitura, movimento e áudio verificados. Homologação de postagem fica para depois.

### 8 — Carrossel com motion

- Gerar narrativa e direção de 3 a 5 páginas, com 5 a 8 segundos por MP4,
  garantindo continuidade e ordem. A IA escolhe quantidade e tempos nessa faixa.
  Validar os limites em qualidade, arquivos finais e custo. Planejar movimento, som
  e começo/fim do loop para cada página.
- Modelar coleção ordenada de artefatos, cada página com identidade e estado;
  prever falha parcial, reprocessamento idempotente, revisão da sequência e
  download das páginas, sem achatar tudo em um único vídeo.
- Um ajuste em uma página preserva as demais. Se for necessário mudá-las,
  apresentar o alcance proposto e aguardar confirmação antes de aplicar.
  Registrar nova versão do conjunto, mantendo histórico e nova aprovação da
  sequência completa; aprovação da peça não é aprovação de publicação.
- Criar prévia móvel e confirmar a emenda dos loops nos arquivos gerados;
  reprodução e postagem pelo Instagram serão verificadas na fase posterior.
  Não prometer loop infinito ou música contínua entre páginas na rede social.
  Decidir PNG de apoio conforme ensaio, sem substituir os MP4s.
- **Saída:** coleção ordenada de MP4s finais, com revisão, ajustes e download
  funcionais, limites e qualidade conferidos por página e na sequência.

### 9 — Jornada de revisão, ajustes, aprovação e download

- Na web/mensagens, exibir progresso e estados compreensíveis, pedido de mídia
  quando necessário, prévias, som, erros e recuperação; permitir revisão das
  imagens, do vídeo e das páginas na ordem, com aprovação da versão da peça final.
  Essa aprovação não aciona postagem nem substitui autorização futura C11.
- Validar acessibilidade, tela pequena, segurança de acesso, falha parcial,
  revisão e preservação de histórico. Testar prévia e arquivos finais em aparelhos.
- Entregar download privado da versão aprovada e das páginas na ordem correta;
  impedir troca silenciosa do arquivo após a aprovação e preservar as anteriores.
- **Saída:** pedido, prévia, ajuste, aprovação e download funcionam no fluxo
  integrado, com mensagens claras, histórico e regras de acesso verificadas.

### 10 — Qualidade, custos e operação da geração

- Fechar qualidade com o titular para cada formato e diferentes negócios,
  fidelidade ao kit, qualidade de áudio/cortes/legenda, fatos, direitos,
  tempo e custo medido por peça aceita, incluindo refações.
- Comprovar testes de integração/CI, isolamento, privacidade, limites de recursos,
  idempotência, recuperação de falhas, métricas e alertas da geração. Verificar
  restauração dos artefatos/fontes e reprodução sem repositórios externos.
- Medir tempo e custo por peça aceita, incluindo refações, para discutir franquias
  e preços conforme P05. Não inventar capacidade ou custo comercial por estimativa
  isolada; prontidão comercial completa continua sendo uma entrega própria.
- **Saída:** imagens feed/story e vídeos Reel/story/carrossel gerados pelo produto,
  revisados e ajustáveis, aprovados quanto à peça, baixáveis, com qualidade,
  rastreabilidade, recuperação e custos medidos. Esta saída encerra a fase de
  geração; não exige conta Meta ou publicação real.

### Fase posterior — Viabilidade e integração de postagem no Instagram

Somente após a entrega de geração, conferir requisitos/API e capacidades de conta,
desenhar conexão e autorizações, implementar publicação dos formatos e validar
resultados reais, falhas e incertezas. Manter a aprovação específica C11 vinculada
à versão, arquivos, legenda, destino e horário aplicáveis; não reaproveitar aceite
da peça como permissão automática de postagem. Esta fase terá seu próprio plano,
credenciais, orçamento e testes autorizados; não bloqueia a geração atual.

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
transcrição, render, mídia e refações; os tetos de 60 s de entrada/saída não
determinam sozinhos o custo de processamento e tentativas. Uma reserva pode ser
ultrapassada por uma chamada cujo fornecedor não fornece teto garantido.

Pendências para decidir com evidência e, quando necessário, entrevista:

- formatos/codecs de entrada e limites técnicos de processamento; o teto de
  50 MiB/60s e o reenvio sem corte automático já foram confirmados;
- especificações e comprovação de direitos de trilha/efeitos e dependências;
- política de arquivos temporários ainda não cobertos por C04/C09;
- limites comerciais de refação, preços e cotas de planos conforme P05;
- tempo de processamento aceitável, estrutura de custos e critério de aceite;
- eventual análise temporal de vídeos de referência em evolução própria,
  com autorização, direitos e regras de coleta, sem anunciar essa capacidade na v0;
- comprovação de leitura, áudio, movimento e loop nos arquivos finais. Capacidades
  de conta/API, reprodução na rede social e publicação serão tratadas depois.

Não repetir como dúvidas os limites de uma gravação/60 segundos de entrada,
60 segundos de saída, carrossel de 3–5 páginas/5–8 segundos, preservação das demais
páginas ao ajustar uma delas, seleção de estilo a cada pedido ou prioridade de
geração antes da integração de postagem. Qualquer mudança deve passar por entrevista. Direitos,
compatibilidade e desempenho exigem evidência técnica; uma escolha de produto
não substitui essa verificação nem autoriza chamadas pagas sem orçamento.

Fontes oficiais consultadas em 05/11/2026: [especificação de Reel pela Meta](https://www.postman.com/meta/instagram/folder/830j7my/reels-publishing)
aceita 3 s a 15 min, sendo 9:16 recomendado; nosso máximo de 60 s é escolha
própria. A [coleção Instagram da Meta](https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api?entity=request-23987686-15c537cd-a773-4b40-a87c-27829e49a439)
descreve condições de conta e Stories. Revalidar limites, API, publicação de
carrosséis com vídeos e reprodução em loop quando começar a fase de postagem.
Essas referências históricas não são pré-requisito de homologação da geração.
