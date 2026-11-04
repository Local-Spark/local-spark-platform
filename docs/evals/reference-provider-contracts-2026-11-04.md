# Contratos de fornecedores — retomada de 04/11/2026

Foram lidas páginas oficiais e metadados públicos. Nenhum Actor foi executado e
nenhuma pesquisa paga foi enviada nesta conferência. O teto autorizado para o
ensaio continua sendo US$ 5 no total, não uma autorização mensal recorrente.

## Google e Jev

A máscara Nearby atual inclui avaliação, quantidade e site; a tabela oficial
publica US$ 35 por mil chamadas de Nearby Search Enterprise na faixa inicial,
antes de considerar franquia. A reserva deve usar a máscara efetivamente enviada.
[Preço Google](https://developers.google.com/maps/billing-and-pricing/pricing).

Jev 1.14 custa US$ 0,042 por milhão de tokens de entrada, com saída gratuita.
Os limites publicados são 64 mil tokens por requisição e 32 mil por pergunta;
não usar probabilidade como grau de semelhança.
[Modelos Jev](https://docs.typesafe.ai/models).

## Apify

O adaptador inicial usava campos fictícios `includeContacts`, `maxContactPages`
e `socialLinks`. O contrato Compass usa `scrapeContacts`,
`maxCrawledPlacesPerSearch`, idioma `pt-BR` e lista de saída `instagrams`.
Não persistir `title` do resultado: é nome proveniente do Google, não nome do
perfil Instagram. Na ausência de nome do perfil, apresentar o @ como decidido.
[Entrada](https://apify.com/compass/crawler-google-places/input-schema),
[saída](https://apify.com/compass/crawler-google-places).

Metadados públicos consultados identificaram Compass como
`nwua9Gu5YrADL7ZDj`, build `0.14.782`, e Instagram Scraper como
`shu8hvrXbJbY3Eb9W`, build `0.0.839`. Essas versões são observações datadas,
não aliases permanentes nem configuração automaticamente ativada.
[Metadados Compass](https://api.apify.com/v2/acts/compass~crawler-google-places),
[metadados Instagram](https://api.apify.com/v2/acts/apify~instagram-scraper).

O registro vigente de Compass exige um limite por execução de pelo menos
US$ 0,50. Esse é o menor teto aceito, não o preço cobrado por um estabelecimento.
O adaptador confere o preço vigente e a build antes de reservar/enviar a chamada;
recusa modelos fora de pay-per-event ou cobrança adicional de plataforma.
`maxTotalChargeUsd` limita eventos. Um Actor com
`isPPEPlatformUsagePaidByUser=true` exige outro orçamento e não é aceito por este
caminho. [Cobrança Apify](https://docs.apify.com/actors/monetize/pay-per-event).

O GET autenticado do run expõe `usageTotalUsd`, descrito pelo fornecedor como o
custo total para o titular do run. A atividade deve validar o run, arredondar
para cima a milionésimos e registrar essa declaração do fornecedor com a reserva.
Ausência de custo não é custo zero; falha de leitura mantém a reserva. Recuperar
o run usa GET, nunca outro POST. A plataforma não precisa apagar armazenamentos
remotos do Apify. [Contrato do run](https://docs.apify.com/api/v2/actor-run-get).

## Validação e pendências

O adaptador corrigido e o vínculo do request passaram em 164 testes unitários,
com 100% de linhas e ramos. Persistência do run, contabilização e guarda passaram
em 14 testes de integração PostgreSQL isolados, incluindo replay, conflito de
recibo, outro titular sem acesso ao token, rollback e recuperação por GET.
Executor Temporal e ensaio real ainda precisam ser integrados. Estes testes usam
HTTP fictício e não comprovam qualidade da coleta.

## Feed e imagens

A build pública Instagram consultada declara `directUrls`, `resultsType` e
`resultsLimit`; não declara `skipPinnedPosts`. O campo fictício foi retirado do
request/MAC. A coleta permanece limitada a até20 itens do feed e mantém todas
as imagens acessíveis de cada carrossel. O adapter valida Actor/build/preço e
custo terminal; o downloader restringe host/MIME/dimensões/tamanho e não segue
redirecionamentos. 357 testes locais, 100% dos cinco módulos envolvidos.
[Entrada oficial](https://apify.com/apify/instagram-scraper/input-schema),
[saída oficial](https://apify.com/apify/instagram-scraper).
