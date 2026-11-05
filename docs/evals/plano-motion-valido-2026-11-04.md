# Plano do ensaio de motion com etapas rastreáveis — 04/11/2026

O titular rejeitou as prévias anteriores: textos quase parados e ausência de
áudio, cortes, transições, efeitos, motion graphics e legendas dinâmicas não
avaliaram o objetivo. Este é um novo ensaio rápido conforme o
[procedimento vigente](../design/ensaios-rapidos-qualidade.md), não uma
continuação da autorização financeira anterior. As quatro chamadas previstas
foram concluídas e as peças montadas para revisão, conforme o
[relatório](ensaio-motion-valido-2026-11-04.md). Reservas acumuladas de US$ 0,32
e uso estimado de US$ 0,019071, não faturado nem conciliado.

## Caso e etapas

Dois pedidos WhatsApp fictícios para a cafeteria de demonstração: um vídeo
vertical e um carrossel com um MP4 por página. Registrar mensagem, entrada e
saída reais do Jev; ele hoje aceita apenas foto e story, por isso deve-se
apresentar sua resposta efetiva de esclarecimento quando ocorrer. Não omitir
que seguir para vídeo/carrossel exige adaptação experimental. Usar o contexto e
kit `cafe-pausas` v1, as skills novas e os padrões derivados já disponíveis do
piloto, distinguindo seus estados e limitações. Não repetir coleta de perfis.

Usar os componentes reais adequados; o adapter editorial atual só aceita plano
de imagens e o renderizador atual produz prévia muda e fixa. Uma direção
audiovisual com modelo real será etapa **experimental**, não declarada como
funcionalidade integrada. O modelo deve receber pedido, kit, skill, contexto,
referências selecionadas e mídia descrita ou quadros amostrados, e devolver
roteiro com cortes e tempo, composições, motion, textos, áudio e transições;
registrar exatamente o que recebeu e respondeu. O executor materializa o plano
localmente com FFmpeg e outras ferramentas adequadas, registrando adaptações.
Não afirmar que o modelo analisou vídeo bruto se recebeu quadros.

Material ilustrativo: [gravação de Stevenndori289](https://commons.wikimedia.org/wiki/File:Latte_Coffee_making.webm),
CC BY-SA 4.0, com pessoa e marca de terceiro; não alegar que registra a cafeteria.
O áudio original não foi liberado para este teste; omiti-lo. Trilha candidata:
[Jazz Piano, Serolillo](https://commons.wikimedia.org/wiki/File:Jazz_Piano.ogg),
[CC BY 2.5](https://creativecommons.org/licenses/by/2.5/), com atribuição.
Locução sintética local em português será identificada como tal. Legendas devem
ser sincronizadas com tempos medidos da locução; se o alinhamento for manual,
declarar. Isso não comprova transcrição ou edição de fala real de cliente.
Informar duração final, hash, origem, licenças e limitações de cada entrada.

## Orçamento autorizado

O titular autorizou reservas totais de até **US$ 0,50**, aceitando o risco de
uma chamada iniciada ultrapassar sua reserva, incluindo até
duas chamadas Jev, duas de direção por modelo de texto/visão e uma chamada extra
se necessária. Montagem, música e locução locais não têm cobrança de API; não
estão incluídos tempo de trabalho nem custo da máquina. Não gerar vídeo por API
paga. Estimativa inicial de ordem de centavos: por exemplo, para 32 mil tokens de
entrada e 12 mil de saída em duas chamadas `gpt-5-mini`, aproximadamente US$ 0,032
às [tarifas publicadas](https://developers.openai.com/api/docs/models/gpt-5-mini);
somar Jev e demais efeitos, cujo custo depende da requisição efetiva. Tokens de
quadros e tamanho das saídas são hipóteses, não preço garantido. Modelo atual
está marcado como obsoleto pelo fornecedor; verificar disponibilidade antes de
eventual uso, sem trocar silenciosamente. Reservas bloqueiam novas admissões,
mas não garantem teto na fatura de uma chamada iniciada.

Cada efeito terá identidade nova, hash e reserva em ledger durável do ensaio,
com limite cumulativo, sem banco novo e sem lock durante rede. Conservar estado
incerto e não reenviar automaticamente. Manter artefatos privados sob `.local/`.

## Critérios

Apresentar vídeos, mensagem, Jev, briefing completo, saída do modelo, fontes e
o que de fato foi executado. Examinar som, sincronização, legibilidade e efeitos,
qualidade no celular e fidelidade das falas; no carrossel, conferir cada página
e a emenda visual/sonora do loop. Declarar renderização e tentativas, tempo e
custos reais ou estimados, rejeições e revisão do titular. Reprodução na API do
Instagram e edição de fala real permanecem testes independentes.
