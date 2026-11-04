# Google Places: prova técnica limitada — 30/10/2026

O titular autorizou até US$ 0,50 para três consultas genéricas, sem dados de
cliente. Foram usadas Places API (New), `places:searchText`, cinco resultados
por consulta e máscara com identificador, nome, categoria, endereço, nota,
quantidade de avaliações e site. Todas retornaram HTTP 200.

| Consulta | Resultados | Com nota | Com quantidade | Com site |
| --- | ---: | ---: | ---: | ---: |
| Cafeterias em Curitiba | 5 | 5 | 5 | 5 |
| Pet shops em Campinas | 5 | 5 | 5 | 4 |
| Salões de beleza em Belo Horizonte | 5 | 5 | 5 | 5 |

O executor local guardou somente estados e reservas, sem salvar nomes ou
respostas brutas e sem enviar dados a modelos. A reserva conservadora é de
US$ 0,105 no total; **não representa a fatura**, que deve ser conferida na conta.
Sem paginação, repetição de efeitos, publicação ou CI.

A amostra mostra que a API respondeu e retornou campos em três consultas; não
prova representatividade, precisão, pertinência, presença ou identificação de
@ no Instagram, engajamento ou cobertura nacional. Site não equivale a perfil
social. Os termos e o contrato precisam ser confirmados para reordenar,
armazenar e usar resultados no produto e no Jev. Sem integração produtiva.

## Segunda prova: valores individuais

Após pedido explícito, três novas buscas com os mesmos parâmetros retornaram
HTTP 200 e cinco resultados cada. A primeira e a segunda rodada reservaram
US$ 0,210 sob o teto de US$ 0,50; reserva não equivale à fatura. Não houve
paginação nem reenvio após incerteza. Os sete campos solicitados foram exibidos
na ordem devolvida, sem salvar respostas brutas em arquivo e sem envio ao Jev.

- Entre cinco cafeterias de Curitiba, todas tinham nota e contagem, e duas
  tinham link direto do Instagram no campo de site.
- Entre cinco pet shops, quatro resultados eram de Campinas/SP; o primeiro era
  de Campinas, bairro de São José/SC. Isso mostra ambiguidade na consulta sem
  UF explícita. Todos tinham nota e contagem; quatro apresentavam site.
- Entre cinco salões de Belo Horizonte, todos tinham nota, contagem e site;
  um site era link direto do Instagram.

O resultado apoia a viabilidade técnica de obter candidatos e, em alguns casos,
links de Instagram. Não demonstra que os links são atuais ou oficiais, que os
perfis tenham engajamento, que a busca foi exaustiva ou que a API pode ser usada
para reordenar resultados e gerar conteúdo. Raio estrito e abrangência nacional
não foram testados; o custo e o uso em produto dependem de avaliação adicional.
