# Análise de padrões das publicações de referência

O adapter `JevReferencePostAnalysis` analisa uma legenda, uma imagem ou ambas em
uma chamada. A atividade coordenadora deve enviar cada legenda uma única vez,
junto da primeira imagem quando disponível, e analisar as demais imagens sem
repetir a legenda. O limite de 20 é de publicações, não de imagens de carrossel.

A saída contém somente escolhas dentro do vocabulário próprio versionado
`reference-patterns-v1`: tom, tema, formato visual, paleta, iluminação,
composição, quantidade visual de texto e assunto visual geral. As perguntas
editoriais usam só a legenda; as visuais usam só a imagem. A alternativa
`uncertain` permite abstenção. Empates de probabilidades resultam em abstenção;
respostas inconsistentes ou fora do vocabulário falham sem liberar a reserva.

O agregador conta as observações e projeta frases próprias fixas, sem aceitar
prosa livre do fornecedor. Guarda até dois temas e um padrão por outra dimensão,
no máximo nove observações. Empates de frequência seguem a ordem fixa do
vocabulário. Não retorna legendas, marcas, identificadores, preços, URLs ou
imagens. Esse método limita o tipo de saída; não comprova acerto semântico da
análise, que ainda precisa do ensaio real autorizado.

As imagens ficam em memória. O adapter valida bytes, MIME e dimensões de origem,
aplica orientação EXIF, reduz a área completa para até 1568 pixels por lado e
preenche lados menores que 280 com fundo branco, sem cortar conteúdo. Reencoda
PNG sem metadados. Isso segue os limites da API experimental documentados em
[imagens do Jev](https://docs.typesafe.ai/images). Uma imagem por chamada e os
limites de origem mantêm o corpo abaixo do teto documentado de 32 MiB.

Rede permanece opt-in e exige credencial, modelo e guarda durável do pedido exato.
A guarda confirma orçamento antes do POST; erro de transporte/resposta preserva
incerteza e não autoriza retry automático. O header experimental é enviado apenas
quando há imagem. Não há proxy, redirecionamento ou retry implícito.

Esta fatia fornece transporte e projeção puros. Persistência autorizada,
contabilização por análise, agenda de seis meses e snapshot usado na geração
estão sendo integrados separadamente. Nenhum conteúdo real foi enviado nesta
validação local.
