# Proposta de revisão do Reel 1c com falha histórica de legibilidade

Estado em **08/11/2026: execução autorizada concluída, melhora de legibilidade
confirmada pelo titular e qualidade criativa global ainda não aprovada**.
O run `3a52c376-e8ea-4bea-b997-94ba59c628de` terminou `completed_human_pending`;
esse é o estado preservado pelo executor. Foram três chamadas HTTP 200 sem
retry ou resultado incerto, com estimativa incremental de US$ 0,527685 dentro
das reservas autorizadas de US$ 1,25.

O titular confirmou que B tem títulos e legendas melhores, mas questionou o
formato e a falta de motion. O contexto original era `reel`, com cortes,
transições, motion graphics e legendas; a mídia é ilustrativa/licenciada com
voz sintética, não gravação de cliente real. O 1c tem apenas movimento discreto,
principalmente ajustes de enquadramento/fades. Sua reparação tipográfica não
valida o acabamento criativo solicitado. Intensa/Dog/Luma continuam referências.
[Feedback integral, resultado e comparação](ensaio-revisao-reel-1c-2026-11-08.md).

O relatório original passou no QA. A apresentação foi corrigida para mostrar
`limitations[]` com escape de HTML e explicar que `adequate`/parada automática
não equivalem a aceite criativo. Passaram 15 testes do relatório, Ruff e mypy;
HTML original/código preservados e novo QA dirigido aprovado em 390/1440 px,
nos dois modos, sem overflow, erro JavaScript ou rede externa. Vídeos,
críticas, summary e custos não mudaram. O CI foi concluído em 09/11, com
5.043 testes aprovados e dois inicialmente pulados completados separadamente
após ajuste de PATH; cobertura app 100%. [Evidência final](../../.local/ci-20261108/ci-final-result.json).
Isso não altera o resultado criativo limitado deste ensaio.

Em **09/11**, o [refinamento Giz](ensaio-refinamento-motion-giz-2026-11-09.md)
concluiu duas chamadas dentro de sua autorização própria e recebeu a resposta
humana **“B ficou melhor.”**. Com a legibilidade reconhecida aqui, isso conclui
a etapa 3 no recorte demonstrado. A nova evidência não aprova globalmente a
direção 1c, o áudio, todos os critérios ou a economia de toda revisão.

O contrato do Giz separa movimento observado de atendimento criativo e foi
exercitado com feedback/referências adicionais declarados. A calibração ampla
continua dependente de mais casos. A implementação do Reel (4), seguida dos
demais formatos (5), já está autorizada e é o próximo trabalho; o ensaio não
representa integração concluída. [Estado e limites da continuação](ensaio-revisao-reel-1c-2026-11-08.md#alcance-da-prova-e-próximo-gate).

## Pergunta do ensaio

Verificar se o crítico reconhece uma falha real de legibilidade no arquivo
renderizado, se uma correção condicionada ao achado a resolve e quanto custa
esse percurso. A seleção é intencional: um caso histórico com defeito conhecido,
não uma amostra da frequência de erros nas gerações atuais.

Dog e Luma não apresentaram achados acionáveis na revisão com contexto completo;
isso não autoriza forçar refações nessas peças. O [resultado da rodada atual](ensaio-ciclo-revisao-motion-2026-11-06.md)
permanece separado. Uma reparação bem-sucedida do 1c não provará melhoria criativa
geral, economia da revisão em todos os pedidos ou qualificação do executor antigo.

## Ponto de partida preservado

Usar a **primeira montagem do Reel 1c**, com tipografia pequena, e não a variante
`reel-legibility-v2`, que já recebeu sete ajustes visuais manuais. A origem é
fictícia: gravação ilustrativa com locução sintética, sem material pessoal de cliente.

- Vídeo: `.local/evals/motion-v0-rodada-1c-2026-11-05/local-adaptation/reel/render/page-1.mp4`.
- SHA-256: `1c5e8d8f91f8d3aed6c49a45f37e69ffaa887523ccf4f1c144ca070b08c66f98`.
- Direção inicial: `local-adaptation/reel/direction-derived.json`, SHA-256
  `f835a3532cd118b2e87ade114ded0a81501ec01983ae3e8d247b4367ff6c95a2`.
- Resposta original: operação `df8d9caf-46b0-42f2-a483-c9ccd2341df0`, preservada
  como rejeitada; estimativa histórica de US$ 0,105925, sem conferência em fatura.

A direção inicial contém dez normalizações históricas documentadas: nove
interpolações `linear` entre estados idênticos e a classificação da faixa como
`recorded_voice`, mantendo fonte, intervalos, ganho e áudio. Não houve ajuste
tipográfico nessas dez mudanças. Reaplicá-las à resposta original reproduziu
exatamente os bytes e o hash do documento derivado.

Os títulos mantêm `font_size=46`; as quatro legendas, `font_size=32`. São
pontos-base da altura, correspondendo a 5,888 px e 4,096 px em 1280 px. A
[avaliação histórica](ensaio-motion-v0-rodada-1c-2026-11-06.md) registra o defeito
e distingue a montagem inicial da adaptação manual posterior. A descrição de
unidades já foi corrigida no schema atual: este ensaio não atribui ao revisor
uma melhoria já obtida no briefing de novas gerações.

## Pacote privado e verificações concluídas

Preparação: `.local/evals/motion-review-1c-proposal-2026-11-08/`.
O `manifest.json` revisão 2 fixa hashes, tamanhos e origens de 69 arquivos.
O manifesto anterior de 56 arquivos está preservado integralmente como
`manifest-original-56.json`; as 13 adições registram evidências e cálculo de custo.
Conserva
MP4 e trace, resposta/pedido originais, snapshot, direção normalizada, provas
das dez normalizações, fontes/mídias, transcrição, custos históricos e código.
Arquivos privados não acompanham automaticamente outro checkout.

`computation.json` soma as estimativas históricas conservadoras das APIs deste
Reel: direção de US$ 0,105925, interpretação Jev de US$ 0,000032, transcrição
de US$ 0,000900 e interpretação anterior rejeitada da rodada 1b de US$ 0,000035.
O subtotal é **US$ 0,106892**, arredondado para micros de dólar. Pedidos,
respostas, ledger anterior e auditoria do lote foram copiados e conferidos por
hash. Não foram alterados os ledgers históricos. Esse subtotal inclui a falha
anterior, exclui os outros formatos do lote e não representa COGS completo:
trabalho humano e computação local não foram precificados; não é fatura.

`context.json` preserva o primeiro contexto JSON completo e as instruções do
pedido original, incluindo fatos, kit, mídia, skill, catálogo e configuração.
As referências continuam vazias: não se acrescenta retroativamente a Intensa.
As seis imagens copiadas conferem com os bytes enviados no pedido original.
O preparador de contexto do ensaio HTML não deve ser usado como se interpretasse
esse outro formato de entrada.

Verificações offline concluídas:

- Integridade de vídeos, respostas, documentos, fontes e mídias copiados.
- Reprodução exata das dez normalizações, sem mudanças de tamanho de texto.
- Compilador e runtime atuais com os mesmos hashes registrados no trace histórico.
- `renderer/prepare.py`, executado em memória, reproduz os dados preparados
  históricos; a cópia para replay altera somente os caminhos de assets confiáveis.
- Ausência de efeitos pagos ou novo render nesta preparação.

A primeira preparação parou ao usar uma chave inexistente na estrutura histórica
das imagens. As cópias foram preservadas, a chave correta foi conferida contra
o pedido real e a preparação foi concluída. O registro privado
`preparation-history.json` conserva esse evento; ele não envolveu API ou vídeo novo.

## Prova local concluída: preflight e qualificação completa

Run preparado: `.local/evals/motion-declarative-review-runs/3a52c376-e8ea-4bea-b997-94ba59c628de`.
A primeira qualificação parou no parsing dos metadados do FFprobe 4.4.8: `size`
em formato textual e tempos em `pkt_pts`. A tentativa está preservada em
`qualification-attempt-1-failed`; a falha foi local, sem API. O leitor foi
corrigido mantendo validação estrita de formatos e valores, sem dispensar as
provas de igualdade de mídia.

O [preflight real de mídia](../../.local/evals/motion-declarative-review-runs/3a52c376-e8ea-4bea-b997-94ba59c628de/media-preflight-ffprobe-4.4.8/result.json)
passou sobre vídeo **já renderizado**, sem nova execução de renderer ou API:

- MP4 arquivado byte a byte igual ao original, SHA-256
  `1c5e8d8f91f8d3aed6c49a45f37e69ffaa887523ccf4f1c144ca070b08c66f98`.
- Remux com SHA-256 `7e07d6470d414082e821b58b9da03f00f89d3f02b4a99eb35e08441621422bd4`:
  empacotamento distinto, conservando os 526 pacotes AAC, PCM decodificado e tempos.
- Os 336 quadros decodificados em RGB24 e seus tempos são iguais; o hash RGB24 é
  `36a9484b6fab43fabe68e48e42616bcfd30b4efad01f1707d7f3e28a08ca371d` em ambos.

A **segunda qualificação completa passou**, recompilando e renderizando a direção
original, com os hashes de código e ferramentas verificados. Confirmou os 336
quadros RGB24 e tempos iguais, além da preservação de AAC/PCM/tempos. O remux
permaneceu com o hash `7e07d6470d414082e821b58b9da03f00f89d3f02b4a99eb35e08441621422bd4`.
O registro [qualification.json](../../.local/evals/motion-declarative-review-runs/3a52c376-e8ea-4bea-b997-94ba59c628de/qualification.json)
tem SHA-256 `21d7f2da63889674eb4b607523be3287a3d1f45459ddb746fa545d7154eabd78`.

Essa qualificação completa é distinta do preflight intermediário sobre mídia
já renderizada. A admissão paga só foi iniciada depois da qualificação válida e
da autorização explícita de orçamento/envio, registrada separadamente. A
primeira tentativa falha e todos os artefatos foram preservados.

O replay usou prioridade de CPU reduzida (`nice`), sem mudar os parâmetros do
encoder. O CI geral, inicialmente paralelo, parou em timeout de integração;
após reprodução e ajuste da preparação, o módulo de concorrência passou em
quatro testes (93,61 s). Naquele momento foi iniciado outro CI integral;
a validação final foi concluída em 09/11, conforme evidência acima.
Produção e migrations não mudaram; somente o teste de concorrência mudou nesse
recorte desde a tentativa anterior. Isso é separado da qualificação local;
não atribuir a falha ao replay sem evidência ou pular testes.

## Ciclo proposto e áudio congelado

1. Criticar quadros reais da v0 com tempos e contexto original completo. O
   diagnóstico histórico, o tamanho esperado de fonte e a variante manual
   corrigida não são enviados ao crítico.
2. Somente diante de defeito relevante, observado e corrigível, solicitar uma
   direção corrigida. Revalidar schema, fontes, kit, fatos, texto, duração e
   identidades; não corrigir manualmente uma resposta inválida para fabricar sucesso.
3. Compilar/renderizar a resposta e criticar a versão resultante, preservando A
   e B. Comparação e decisão humana permanecem necessárias; empate e regressão
   são resultados possíveis.

O plano de áudio completo fica congelado, assim como duração e voz. Como o
driver histórico remixa e reencoda, igualdade do plano não comprova igualdade
da faixa final. A proposta prevê copiar o AAC da v0 para o derivado sem
reencodificar e verificar payload, tempos e PCM antes de afirmar preservação.
O preflight real comprovou essa preservação no remux de mídia já renderizada,
a qualificação completa passou e a v1 final também conservou AAC/PCM/tempos do
baseline. Quadros e métricas não equivalem a ouvir o som; a transcrição histórica
não tem alinhamento por palavra.

A variante declarativa explícita está implementada em
`scripts/evals/motion_declarative_review_eval.py`, com a ponte local
`scripts/evals/motion_declarative_render.py`. Reutiliza os contratos de crítica,
evidências, ledger, transporte sem retry e relatório do ensaio existente.
Preserva a resposta declarativa, sem tratá-la como código HTML/JS.

O preparo valida os 69 arquivos e o subtotal histórico contra as fontes, copia
o baseline intacto, conserva todo o contexto e extrai evidências locais. A
qualificação obrigatória recompila e renderiza a direção original; compara a
decodificação RGB24 de todos os quadros, seus tempos e a prova de AAC/PCM.
Hashes ligam essa qualificação às entradas, pedido inicial, código ativo,
Python e ferramentas, inclusive dependências do Playwright. Mudança posterior
recusa a admissão de uma chamada. A ausência de qualificação impede criar o
claim de execução ou reservar uma API.

O corretor recebe a direção atual, achados vinculados ao vídeo e schema atual
com unidades explícitas. O schema enviado remove anotações `default`, mantendo
todos os campos requeridos; a validação local continua completa. Somente
tipografia permitida, keyframes e transições das camadas visuais podem mudar;
conteúdo, fontes, cores, áudio, fontes de mídia, IDs e intervalos ficam
congelados. Resposta inválida interrompe o ensaio, sem normalização posterior.

Verificação local concluída: **146 testes, sendo 57 da orquestração e 89 da
ponte**, com mocks, além de Ruff e mypy estrito nos dois módulos. Cobrem orçamento exato,
chamadas concorrentes ou fora de ordem, resultado incerto sem nova chamada,
vínculo de custos/evidências, campos imutáveis, versões preservadas,
qualificação adulterada, encerramento de subprocessos e divergências de
pacotes AAC/tempos/PCM, incluindo os formatos reais de saída do FFprobe 4.4.8.
Essas verificações não substituem o CI integral da aplicação. A qualificação
completa real foi executada separadamente e passou, conforme o registro acima.

Comandos usados na preparação local, sem API (o run abaixo já foi qualificado
e sua execução paga foi iniciada):

```text
.venv/bin/python scripts/evals/motion_declarative_review_eval.py --proposal .local/evals/motion-review-1c-proposal-2026-11-08
.venv/bin/python scripts/evals/motion_declarative_review_eval.py --run <diretório retornado> --qualify
```

O modo `--execute --budget-usd 1.25` foi iniciado após qualificação válida e
autorização explícita do titular. O orçamento e a identidade de execução são
registrados uma única vez; repetir o comando não autoriza repetir efeitos.
Não executar outra rodada ou reenviar uma operação incerta por este registro.
Uma resposta adequada ou insuficiência de evidências encerra após a primeira
crítica. A última versão não é automaticamente escolhida nem aprovada.

## Orçamento autorizado e execução concluída

O titular autorizou **US$ 1,25 em reservas para até três chamadas e envio à
OpenAI**: crítica inicial com reserva de US$ 0,25, uma correção condicional de
US$ 0,75 e crítica final de US$ 0,25. A autorização foi registrada em
`authorization.json`, vinculando pergunta/resposta, plano, primeiro pedido e
qualificação. Ela é específica deste caso; os US$ 6,75 de Intensa/Dog/Luma não
foram transferidos.

O registro anterior `paid-plan-proposed.json` permanece intacto como evidência
da proposta ainda não autorizada naquele momento, com zero chamadas pagas e
SHA-256 do primeiro pedido
`e07798c39a9c5d4a0583569c3a42f27a0c01bf1436877395c3b2637b9d97cc0b`.
O pedido qualificado coincide com esse hash. Reserva não é fatura nem garantia
de limite da cobrança externa. Falha incerta preserva identidade/reserva e
interrompe o percurso sem retry pago automático.

A crítica inicial, operação `f48e3377-c84b-474d-92b1-315edc39972e`, retornou
`needs_correction`: um achado `major` de legibilidade, `i01`, com títulos,
legendas e convite pequenos, fundamentado em seis quadros ao longo do vídeo.
Custo estimado conhecido desta crítica: **US$ 0,124605**, sem conferência em
fatura. Isso prova detecção desse defeito histórico no caso selecionado, não
qualidade geral do crítico ou ganho de uma correção ainda não avaliada.

A correção, operação `b3205955-fdee-493f-943a-28035efda6f2`, retornou e passou
na validação contratual, com estimativa de **US$ 0,208475**. O subtotal conhecido
das duas chamadas do 1c é **US$ 0,333080**, antes da crítica final; não é fatura.
A resposta aborda `i01`: os três títulos passam de `font_size=46` para `375`
(48 px), e as quatro legendas de `32` para `250` (32 px). As caixas de legenda
têm largura `8800`; a terceira usa `letter_spacing=-500`. Fatos, textos,
materiais, plano de áudio, cortes e intervalos permanecem congelados.

A v1 foi renderizada com SHA-256
`5305dfda85284fd9a762320dc6e8fe6e0c95cbd20acbea3810fab2f030013eca`; AAC, PCM e
tempos conferem com o baseline. A crítica final, operação
`1d9b8337-1711-4f03-ab38-447b752929e1`, retornou `adequate`, sem achados, preferindo
v1; seis critérios `pass`, áudio `uncertain`. Estimativa dessa crítica:
US$ 0,194605. Total incremental das três chamadas: **US$ 0,527685**, sem retry
ou operações incertas. Com o subtotal histórico de US$ 0,106892, o subtotal de
APIs é US$ 0,634577, sem fatura ou COGS completo.

Chamadas somaram 154,561 s; render e evidências, 151,928 s; subtotal medido
306,489 s exclui setup, preflight, qualificação, intervalos e trabalho humano.
O [relatório final e resultado](ensaio-revisao-reel-1c-2026-11-08.md) contém
original/corrigida, avaliação automática e o feedback humano registrado na
documentação. QA final do HTML passou em 390/1440 px, modos cego/identificado,
com dois players e oito reproduções completas mutadas, sem overflow, erro
JavaScript ou rede externa. O titular reconheceu melhora de títulos/legendas,
mas questionou a ausência de motion. O 1c continua aprovado somente quanto à
melhora tipográfica; a conclusão posterior da etapa 3 inclui a preferência por
B no Giz. Áudio, qualidade e retorno financeiro gerais não foram demonstrados.
Integração do Reel, outros formatos e operação comercial conservam seus critérios
próprios, sem serem concluídos por estes ensaios.
