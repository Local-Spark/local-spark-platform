# Apify: prova técnica isolada de links sociais — 30/10/2026

O titular autorizou uma prova limitada com teto de US$ 0,50. Foi feita uma
execução do actor de terceiros [Website Buyer Signal Scanner, `capi2/my-actor-1`](https://apify.com/capi2/my-actor-1),
com três URLs de sites públicos como entrada. Não foram enviados resultados do
Google Places ou URLs do Google Maps. A documentação do actor descreve extração
de links sociais a partir do HTML público da página inicial; essa descrição do
fornecedor não garante cobertura nem valida a identidade dos perfis.

| Site informado | Resposta da página informada pelo actor | Redes retornadas |
| --- | --- | --- |
| [URBE Café Bar](https://www.urbecafe.com.br/) | HTTP 200 | Nenhuma no retorno |
| [Mug SP](https://mugsp.com.br/) | HTTP 200 | Instagram `@mug.sp` |
| [Wanderlust Bar](https://www.wanderlustbar.com.br/) | HTTP 200 | Instagram `@wanderlustbar.sp` e Facebook `@wanderlustbarsp` |

Em pesquisa separada, o [Guia Abrasel SP para URBE Café Bar](https://www.guiaabraselsp.com.br/urbe-cafe-bar)
indicou `@urbecafebar`. Esse @ não veio do retorno do actor e sua associação
atual ao negócio não foi garantida. Ausência no retorno não prova ausência de
rede social; associação de links a um negócio ainda exige conferência.

A execução informou US$ 0,00005 em eventos. Custos adicionais de leitura e
armazenamento não estão incluídos nesse valor. A reserva de US$ 0,50 é o teto
autorizado para a prova e não representa a fatura nem o custo efetivamente
cobrado; a fatura deve ser conferida na conta. Os valores informados pertencem
a esta execução e não estabelecem preço para uso recorrente.

## Limites e próximos passos

- Uma única execução, três sites e nenhum teste de ranking, análise das contas
  sociais, engajamento, correspondência definitiva dos perfis ou cobertura por
  segmento. HTTP 200 e link detectado não garantem qualidade ou atualidade.
- Esta prova isolada não integra Apify ao produto, não consulta Places/Maps e
  não demonstra que a combinação Google → Apify é permitida ou funciona.
  Os [termos do Google Maps Platform](https://cloud.google.com/maps-platform/terms)
  restringem scraping e alteração de conteúdo; contrato, armazenamento,
  reordenação, processamento e uso pretendido devem ser verificados para o caso
  concreto antes de integrar resultados Google ou usá-los na geração.
- Comparar mais segmentos, origem e correspondência dos links, custos totais e
  comportamento em falhas somente com fontes, credenciais e orçamento autorizados.
  A rede Google/Apify e o consumidor dos eventos de referências na outbox
  continuam pendentes. A prova não autoriza consumo recorrente nem publicação.
