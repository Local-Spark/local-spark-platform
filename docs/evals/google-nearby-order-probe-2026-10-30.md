# Google Nearby Search: provas pontuais de ordenação e tipos — 30/10/2026

O titular autorizou uma chamada da Places API (New), usando uma coordenada
pública genérica no centro de Curitiba, sem localização de cliente. A consulta
solicitou `includedTypes: ["cafe"]`, raio de 5 km, `rankPreference: "POPULARITY"`
e no máximo 20 resultados. A máscara incluiu identificador, nome, endereço,
tipos, média de avaliações e quantidade de avaliações. A resposta veio na
ordem do Google, sem paginação ou classificação própria.

Foram retornados 20 resultados; sete incluíam `supermarket` em sua lista de
tipos. A presença desse tipo não prova, por si só, que um resultado não seja uma
cafeteria ou que seja inadequado como referência.

Na amostra, a posição não foi uma ordenação simplesmente decrescente pela
quantidade de avaliações: o resultado em 17º tinha a mesma média e mais
avaliações do que o primeiro. Isso não explica a fórmula de popularidade do
Google, não demonstra a causa da ordenação e não mede relevância ao negócio,
engajamento social, cobertura da cidade ou os melhores estabelecimentos.

Uma segunda chamada autorizada, também no ponto genérico em Curitiba, com raio
de 5 km, `POPULARITY` e máximo de 20 resultados, usou
`includedPrimaryTypes: ["cafe", "coffee_shop", "bakery", "pastry_shop"]` e
incluiu o tipo principal na máscara. Dos 20 resultados, 14 tinham `bakery` como
tipo principal, quatro `coffee_shop` e dois `pastry_shop`. Nenhum apresentava
`supermarket` na lista de tipos; na primeira amostra, sete apresentavam esse
tipo. As consultas diferem tanto no filtro de tipos quanto nas categorias e no
momento de execução. A comparação não demonstra causalidade nem cobertura e não
mede se os resultados são boas referências para o negócio do cliente.

Cada chamada teve reserva conservadora de **US$ 0,035**. Com os US$ 0,210
reservados anteriormente na prova Places, o total reservado passou a
**US$ 0,280**. Reserva não equivale à cobrança ou fatura; franquias, consumo e
valores reais devem ser conferidos na conta.

Conforme combinado, não foram registrados neste documento resultados individuais,
nomes, endereços, IDs ou resposta bruta dos negócios. A sonda mantém em ledger local apenas
operação, orçamento, reserva e estado; não armazena os resultados nem tenta
repetir automaticamente uma chamada incerta. A prova não implementa a busca no
produto, não envia dados ao Jev e não confirma direitos de retenção,
reordenação ou uso publicitário.

Referências de capacidade e condições: [Nearby Search (New)](https://developers.google.com/maps/documentation/places/web-service/nearby-search),
[preços Google Maps Platform](https://developers.google.com/maps/billing-and-pricing/pricing)
e [políticas do Places](https://developers.google.com/maps/documentation/places/web-service/policies).
