# Etapa 1 visual — tratamento da gravação

Data: 10/11/2026. Esta é a etapa 1 da nova sequência visual, posterior à etapa de
confiabilidade. O titular pediu implementação e parada para seu OK antes da etapa
2 (fundo vivo). Escopo: moldura/borda, aproximação, entrada/saída e enquadramento
quando a gravação aparece. Não iniciar fundo, realismo da xícara ou fala alinhada.

## Problema e implementação

A v7 já orientava genericamente moldura/escala, mas a peça entregue era da v6 e
não comprovava esse tratamento. Foi identificado também um comportamento concreto:
`movement-v2.js` escrevia `borderRadius=0px` em toda track que não declarasse radius,
apagando o arredondamento CSS durante uma simples transformação da janela.

- Novo `movement-v3.js`: só escreve border-radius quando initial ou algum destino
  declara radius. Valor explícito zero continua canto reto; raios animados continuam
  determinísticos. Mantém a proteção v2 contra clip-path implícito em ancestrais.
- V1/v2 permanecem byte a byte intactas e disponíveis por hash. Novas capturas
  usam v3. Repertório aceita os descritores exatos v2/v3 testados, sem liberar
  qualquer versão futura ou mudar o manifesto histórico.
- Nova skill `instagram-reel-v8`: orienta observar entrada, assentamento, foco e
  saída, com moldura escolhida pelo kit, dimensão externa incluindo padding/borda,
  aproximação uniforme do conjunto e estados de repouso. O vídeo mantém contain,
  proporções e ação relevante; zoom interno não justifica cortar mãos/rosto/produto.
- Exemplo executável `makeVideoFrameTreatment` dentro da própria skill usa o runtime
  existente. Expõe tracks/tempos para o plano, preserva moldura CSS e não troca mídia,
  reinicia relógio ou manipula áudio. É código adaptável enviado ao modelo, não nova
  biblioteca instalada nem animação universal obrigatória.
- A crítica usa os critérios/evidências atuais para comparar estados realmente
  observados. Não se adicionou campo, serviço, tabela, nota automática por quantidade
  de efeitos ou aceite por mera presença de borda.

A direção fornecida continua vinculante. Novas orientações não reescrevem uma
peça histórica nem autorizam contrariar seu projeto visual. A direção Café Pausa
preparada nesta etapa altera apenas o tratamento da gravação na abertura/retorno:
`docs/evals/direcao-cafe-pausa-tratamento-video-2026-11-10.json` e brief homônimo.
Cena gráfica, xícara, texto, fundo e alternância anterior são preservados.

## Validação e entrega

99 testes Python dirigidos passaram em 4,06 s, com 100% de linhas/ramos nos três
serviços medidos: movement, repertoire e skills. 30 testes Node passaram, incluindo
execução do exemplo transmitido, estados de leitura/foco/saída, retorno a instantes
anteriores, máscara e raio independentes, raio explícito zero e semântica antiga v2.
Ruff e Mypy dos três serviços aprovados. Sem CI global, banco, migração ou chamadas
pagas. Esses checks comprovam mecanismos/contratos, não acabamento de um Reel novo.

Pacote offline pelo mesmo montador do produto:
`.local/exports/motion-cafe-pausa-tratamento-video-20261110.zip`.
Contém prompt integral, 12 imagens de entrada, direção, JSON/schema, fonte, fontes
tipográficas e runtimes exatos. A biblioteca de movimento mantém o nome compatível
`execution/libraries/movement-v1.js`, mas os bytes/manifesto são v3. Sem credenciais,
contagem remota, envio a modelo, asset novo ou renderização de peça.

Não há novo MP4 desta etapa. A prova visual final ainda depende de geração/render
explicitamente delimitados; nenhum orçamento anterior autoriza isso. Etapa 2
permanece aguardando OK do titular, conforme solicitado. Não declarar fundo vivo
ou xícara realista entregues por esta mudança.
