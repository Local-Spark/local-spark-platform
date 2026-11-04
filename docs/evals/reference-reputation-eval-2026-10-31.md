# Avaliação fictícia da pontuação experimental de reputação

Data: 31/10/2026. Todos os números abaixo são exemplos fictícios. Esta avaliação
não consulta fornecedores, não usa dados reais e não autoriza o uso ou a retenção
de informações derivadas de fonte externa.

## Regra inicial em teste

A média observada `m`, de 1 a 5 estrelas, é suavizada com uma média prévia de
4,0 equivalente a 50 avaliações. O resultado é convertido para a escala de 0 a
10, sem arredondamento antes da apresentação:

```text
nota = 2,5 × (((n × m + 50 × 4,0) / (n + 50)) − 1)
```

O titular revisou a regra anterior: **menos de 10 avaliações também podem
receber pontuação**. Com zero avaliações ou sem média disponível não há nota.
A pontuação de reputação é separada da avaliação de semelhança entre negócios.

## Exemplos

Os valores calculados estão arredondados a duas casas apenas nesta tabela.

| Média observada | Quantidade de avaliações | Pontuação experimental |
| --- | ---: | ---: |
| 5,0 | 2 | 7,60 |
| 5,0 | 10 | 7,92 |
| 4,7 | 2.000 | 9,21 |
| 4,9 | 100 | 9,00 |
| 4,2 | 500 | 7,95 |
| 1,0 | 11 | 6,15 |
| 3,0 | 2.000 | 5,06 |

## Limitação e trabalho pendente

A média prévia eleva médias observadas inferiores a 4,0. O exemplo de
1,0 com 11 avaliações recebe uma
pontuação maior que o de 3,0 com 2.000. Esse comportamento é indesejado e não é
corrigido por um limiar. A primeira fórmula permanece apenas para comparação.

Trata-se de uma hipótese inicial, não de um modelo final ou de uma medida de
confiabilidade estatística. A pontuação não mede engajamento em redes sociais.
Sua integração a uma fonte real, retenção e apresentação no produto permanecem
pendentes.

## Segunda alternativa experimental

Para avaliar a preferência do titular por combinar nota e quantidade sem
valorizar uma nota baixa, uma segunda função aceita uma ou mais avaliações e
subtrai uma penalidade da nota normalizada. O resultado não fica abaixo de zero:

```text
nota = max(0, 2,5 × (m − 1) − 3,4 / √n)
```

O coeficiente 3,4 é uma escolha provisória para experimentação; não expressa
intervalo de confiança ou garantia estatística. O titular escolheu continuar os
testes com a segunda fórmula; nenhuma foi escolhida para ordenar negócios reais.

| Média observada | Avaliações | Primeira fórmula | Alternativa penalizada |
| --- | ---: | ---: | ---: |
| 5,0 | 1 | 7,55 | 6,60 |
| 5,0 | 2 | 7,60 | 7,60 |
| 4,9 | 9 | 7,84 | 8,62 |
| 1,0 | 11 | 6,15 | 0,00 |
| 3,0 | 10 | 7,08 | 3,92 |
| 3,0 | 2.000 | 5,06 | 4,92 |
| 4,8 | 10 | 7,83 | 8,42 |
| 4,8 | 100 | 8,83 | 9,16 |
| 4,8 | 1.000 | 9,40 | 9,39 |
| 5,0 | 11 | 7,95 | 8,97 |
| 4,7 | 2.000 | 9,21 | 9,17 |

A alternativa nunca eleva a nota normalizada e, para a mesma média, mais
avaliações não diminuem a pontuação. O limite em zero pode causar empates: por
exemplo, 1,1 com 10 ou 100 avaliações recebe zero. O coeficiente influencia
quanto negócios com poucas avaliações são penalizados; ainda é necessário
avaliar exemplos e decidir se esse comportamento atende ao produto. Nota e
quantidade, isoladamente, não comprovam engajamento ou semelhança do negócio.
Nessa fórmula, uma estrela produz zero por causa da escala usada, embora o
titular tenha esclarecido que zero exato não é obrigatório; a calibração final
segue em aberto. Com 5 estrelas e 9 avaliações, a nota experimental é 8,87:
poucas avaliações não impedem que um resultado apareça entre os primeiros.

## Validação local

Os testes direcionados das funções com dados fictícios tiveram **45 testes
aprovados** e **100% de cobertura de linhas e ramos no módulo isolado**. Ruff e
mypy direcionados também passaram. O CI completo não foi executado.

Uma verificação adicional examinou 4.010 combinações fictícias de médias e
quantidades: a pontuação ficou entre 0 e 10 e não diminuiu ao aumentar a média
ou a quantidade, mantida a outra variável. A precisão do cálculo foi fixada em
28 dígitos, independente da precisão decimal do chamador. Isso não comprova a
calibração nem a adequação da fórmula a uma fonte real.
