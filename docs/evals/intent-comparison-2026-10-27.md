# BL04.1 — comparação exploratória de interpretação

Em 27/10/2026 foram feitas chamadas reais apenas com dados fictícios sob teto
total autorizado de **US$ 1**. O [relatório sanitizado](intent-comparison-2026-10-27.json)
registra casos, saídas, tokens, falhas e parâmetros; não inclui chaves ou prompts.
O [runner](../../scripts/evaluate_intent_comparison.py) roda sem rede por padrão,
valida hashes dos datasets, reserva orçamento e requer journal exclusivo para
execução paga. Uma continuação recebe todos os journals anteriores e não repete
casos já submetidos. Não executar outro ensaio pago sem orçamento próprio.

## Escopo e método

O conjunto contempla 50 mensagens de intenção PT-BR existentes, sete cenários
de acervo/formato e quatro históricos fictícios concatenados. As entradas do
adaptador de acervo já trazem candidatos; isso **não mede o retrieval lexical do
runtime**. Os históricos são enviados numa única chamada e **não demonstram
memória de conversa WhatsApp**, esclarecimento em múltiplos turnos ou publicação.
Todos os conjuntos já foram inspecionados; o antigo holdout foi contaminado.
Não constituem teste cego nem estimativa representativa para clientes.

A comparação usa `jev-1.14.0` e o alias `gpt-6-luna`. Após dois testes iniciais
com limite de saída 320, a configuração comparável da OpenAI usou `reasoning=none`,
1.024 tokens de saída e tier padrão; o default do adapter não foi alterado. Como
`gpt-6-luna` é alias, não se assume snapshot datado. A avaliação confere intenção,
e, quando aplicável, decisão, item e formato; mede a coincidência **exata** com o
gabarito, não a qualidade final de uma conversa ou peça publicada.

| Recorte comparável | Jev | OpenAI |
| --- | --- | --- |
| 57 casos enviados aos dois com configuração final | 52/57 correspondências exatas | 40/57; 51 respostas completas, seis incompletas |
| 50 casos de intenção | 46/50 corretos | 38/50; cinco respostas incompletas |
| 4 históricos concatenados | 3/4 exatos | 2/4 exatos; uma resposta incompleta |
| 3 casos de acervo/formato restantes | 3/3 exatos | 0/3 exatos |

As seis respostas incompletas da configuração final foram contadas como falhas,
não removidas do denominador. Em um histórico com produto ambíguo, ambos pediram
esclarecimento e preservaram o formato story; o gabarito exigia formato nulo.
Isso é divergência estrita, não prova de ação insegura. Em duas respostas OpenAI,
`none` divergiu de `clarify` no gabarito, embora ambos levem a esclarecimento no
fluxo atual. Separar essa divergência de erros com potencial de publicação indevida.
O caso “quero divulgar o Dog da Casa” foi reconhecido pelo Jev com o critério novo;
a OpenAI sugeriu foto embora o formato não tivesse sido pedido. Os resultados
dependem do prompt, modelo, schemas e configurações; **não são ranking definitivo**.

Ao longo de todas as tentativas, incluindo configurações preliminares, Jev
completou 61 respostas e OpenAI completou 52; oito respostas OpenAI foram
incompletas e uma tentativa inicial ficou sem resultado conhecido. A chave
OpenAI tinha acesso ao modelo por consulta somente leitura; não se conclui que
erro de acesso tenha causado as respostas incompletas. Contagens e código de
falha são preservados; não houve retentativa de caso já submetido.

O limite superior conservador calculado para todo o ensaio foi **US$ 0,0172870085**,
incluindo a reserva de **US$ 0,008976** da tentativa de cobrança desconhecida.
Desse limite, as chamadas com uso conhecido representam **US$ 0,001788696**
estimados para Jev e **até US$ 0,0065223125** para OpenAI, inclusive as respostas
incompletas com uso reportado; a parcela desconhecida é reservada à OpenAI.
Trata-se de estimativa por token/tarifa com margem, não fatura, e exclui outros
serviços, impostos, retentativas reais e infraestrutura. Consultar [tarifa e
modelo oficiais](https://developers.openai.com/api/docs/models/gpt-6-luna) para
nova execução. Não usar esse valor como custo mensal por cliente.

## Decisão e gaps

Manter Jev como primeiro candidato **somente em desenvolvimento/teste**, com
autorização específica e orçamento; não instalar fallback automático que possa
duplicar cobrança. Esta comparação não valida o modelo para produção: criar
um holdout novo e independente, corpus PT-BR com negações, ambiguidade,
transcrições e setores diversos; avaliar erros críticos, segurança, regressões,
qualidade da conversa e custo por resultado. O objetivo de 1.000 casos revisados
consta no plano; não foi atingido. O modelo OpenAI precisa investigar saídas
incompletas e qualidade com outros prompts/tetos sob orçamento novo antes de
uma decisão comercial.

O sistema atual processa mensagens isoladas, tem recuperação lexical por nome e
alias e ainda não coordena integralmente as respostas dos caminhos de conversa e
conteúdo. A reserva Jev mantém o valor máximo por tentativa durante o dia mesmo
após sucesso: é conservador, mas restringe throughput. Não há evidência neste
ensaio de circuito aberto ou capacidade para 200 mil clientes. Esses itens são
gates de implementação/operação, não são resolvidos por mais chamadas ao modelo.
