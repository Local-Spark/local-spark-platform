# Estudo: encontrar negócios semelhantes e seus perfis

Pesquisa documental em 30/10/2026, sem consulta autenticada, gasto ou
implementação. Objetivo: encontrar referências para negócios de diferentes
segmentos, comparar relevância e sinais observáveis e submeter sugestões ao
cliente. Disponibilidade em documentação não prova cobertura no Brasil,
permissão de uso, qualidade dos dados ou engajamento no Instagram.

Uma [prova técnica posterior](../evals/google-places-technical-probe-2026-10-30.md)
consultou três categorias e confirmou presença de campos em uma amostra pequena;
não confirmou a relevância dos resultados ou os direitos de uso.

## Fontes pesquisadas

### Google Places

[Text Search](https://developers.google.com/maps/documentation/places/web-service/text-search)
permite pesquisar segmento e local, filtrar por nota mínima e solicitar campos
como nome, categoria, endereço, nota, número de avaliações e site. Os
[tipos suportados](https://developers.google.com/maps/documentation/places/web-service/place-types)
incluem, além de alimentação e hospedagem, lojas, serviços de beleza, saúde e
outras atividades. Cobertura real por município e atividade é desconhecida.

O endpoint documenta ordenação por relevância ou distância, não por nota. O
campo website é o site do negócio; não garante perfil Instagram. Nota e
quantidade de avaliações qualificam reputação na fonte, não desempenho da conta
social. Solicitar nota, contagem ou site em Text Search aciona o SKU Enterprise.
Na [tabela global de preços](https://developers.google.com/maps/billing-and-pricing/pricing)
consultada em 30/10, esse SKU inclui 1.000 eventos mensais sem cobrança e depois
US$ 35 por 1.000 na primeira faixa; franquias efetivas, região, impostos,
outras operações e faturamento da conta precisam ser conferidos. Uma consulta
adicional ou paginação pode gerar nova cobrança.

**Condição anterior à integração:** os [termos da plataforma Maps](https://cloud.google.com/maps-platform/terms)
contêm restrições sobre extração e armazenamento, modificação de resultados e
uso em produto de publicidade. Não assumir que coletar e reordenar resultados,
enviá-los ao Jev ou usá-los como base de peças seja permitido. Consultar o Google
sobre este caso concreto e contrato antes de decidir; uma chamada técnica não
prova o direito de uso. Também não assumir que o [Gemini Grounding com Google Search](https://ai.google.dev/gemini-api/terms)
permite análise ou extração automática para alimentar outro modelo.

#### Decisão do titular e confirmação necessária com o Google

O titular quer reutilizar por **seis meses**, entre negócios de clientes,
registros encontrados, incluindo nome, localização, nota e quantidade de
avaliações, e selecionar sugestões por similaridade e reputação. Escolheu o
Google Geocoding como opção para localizar endereços; o adaptador preparado
localmente permanece desligado e não comprova integração, autorização de gastos
ou permissão para armazenar resultados. O cliente ainda deverá confirmar o ponto
antes de iniciar uma busca.

As seguintes restrições são expressas nos documentos oficiais consultados:

- A [política do Places](https://developers.google.com/maps/documentation/places/web-service/policies)
  isenta o `place_id` da restrição de cache, permitindo armazená-lo sem prazo;
  ela não estende essa exceção a nome, nota ou número de avaliações.
- Os [termos gerais, §3.2.3](https://cloud.google.com/maps-platform/terms)
  restringem extração e armazenamento de conteúdo do Maps, proíbem cache salvo
  exceções expressas e determinam que os resultados não sejam modificados.
  Incluem ainda restrições a criar conteúdo a partir de dados Maps, a melhorar
  modelos de IA com esses dados e a criar ou ampliar produto publicitário.
- Os [termos específicos, §14](https://cloud.google.com/maps-platform/terms/maps-service-terms)
  permitem guardar coordenadas do Places por até 30 dias, depois exigem apagá-las.
  O [§6 do mesmo documento](https://cloud.google.com/maps-platform/terms/maps-service-terms)
  traz regras próprias de cache para coordenadas do Geocoding e uma exceção
  limitada a funcionalidade direta ao usuário, sem compartilhamento entre
  usuários nem substituição de chamadas futuras.
- É permitido apresentar conteúdo do Places sem mapa, observadas as
  [regras de atribuição Google Maps e identificação visual da fonte](https://developers.google.com/maps/documentation/places/web-service/policies).
  A atribuição não altera, por si só, as regras de cache.

A aplicação dessas cláusulas à seleção das três referências, à inferência por
um modelo externo sem treinamento, ao envio de `place_id` ou site para terceiros
e ao uso final na geração de peças exige confirmação do Google. Em particular,
o texto sobre melhoria de modelos não demonstra, por si só, que toda inferência
equivale a treinamento; tampouco confirma que essa inferência seja permitida.
Um actor que consulta apenas o site do negócio e outro que extrai conteúdo do
Google Maps não devem ser tratados como equivalentes. O TTL desejado não altera
as condições da licença. Até resposta e eventual contrato adequado, o acervo
compartilhado com os campos Google, a classificação e o uso em IA permanecem
pendentes, sem ativação de chamadas reais recorrentes.

#### Consulta proposta para o suporte do Google

O titular pode copiar a mensagem abaixo. Não foi enviada pelo projeto.
O [suporte oficial](https://developers.google.com/maps/support) orienta abrir
um caso em **Google Cloud Console → Google Maps Platform → Support → Create
Case**, com projeto que tenha API Maps habilitada, conta de faturamento válida
e permissão para criar casos.

> Olá! Temos um SaaS brasileiro que ajuda pequenos negócios a criar conteúdo
> para redes sociais. Queremos usar Places API (New) para buscar negócios do
> mesmo segmento por cidade ou raio e apresentar até três como possíveis
> referências; o cliente escolhe quais aceitar. Os dados não serão usados para
> treinar modelos.
>
> Nossa proposta é: obter place_id, nome, localização, site, nota média e
> quantidade de avaliações; manter esses dados por seis meses em PostgreSQL,
> compartilhando o acervo entre clientes para evitar consultas repetidas;
> classificar os candidatos pela semelhança do negócio, nota e quantidade de
> avaliações, inclusive com um modelo de IA apenas para inferência; e apresentar
> a seleção sem mapa, com atribuição Google Maps. Depois, enviar o site ou
> place_id a um serviço terceiro (Apify) para identificar links sociais,
> armazenando os perfis encontrados. Os perfis aceitos poderão orientar a
> geração de conteúdo publicitário original.
>
> Podem confirmar, item a item: (1) quais desses campos podem ser armazenados
> por seis meses e reutilizados entre clientes, e por quanto tempo; (2) se
> podemos filtrar/reordenar ou selecionar três resultados segundo esses
> critérios e fornecer os dados a uma IA para inferência; (3) se o uso final
> para orientar conteúdo publicitário é permitido; (4) se podemos enviar
> place_id ou website ao terceiro, distinguindo um serviço que consulta apenas
> o site do negócio de outro que também extrai informações do Google Maps;
> (5) as condições de atribuição na tela sem mapa; e (6) se existe contrato ou
> licença comercial que permita os itens não cobertos pelos termos padrão?
> Nossa conta está no Brasil. Agradecemos referências às cláusulas aplicáveis.

### Foursquare Places

[Place Search](https://docs.foursquare.com/fsq-developers-places/reference/place-search)
pesquisa nomes e categorias por localidade e documenta ordenação por nota,
relevância, distância ou popularidade. Os [campos de resposta](https://docs.foursquare.com/fsq-developers-places/reference/response-fields)
incluem `social_media.instagram`, quando disponível. Atributos `rating` e
`stats.total_ratings` pertencem ao conjunto Premium; sua nota usa escala 0–10 e
combina votos e outros sinais, não é equivalente à nota do Google. Não presumir
que todos os negócios tenham Instagram, nota ou contagem preenchidos.

É uma candidata para comparação porque pode reunir categoria, localização,
perfil e sinais de reputação. Precisamos medir cobertura e qualidade em cidades
brasileiras, elegibilidade, preço dos campos Premium e limites de uso. A
[licença da API](https://foursquare.com/legal/terms/apilicenseagreement/)
e contrato aplicável precisam ser confirmados especificamente para processamento
por IA externa, armazenamento e uso no produto.

Há também um [conjunto de dados aberto](https://docs.foursquare.com/data-products/docs/fsq-places-open-source)
sob licença Apache 2.0, separado dos campos e termos da API comercial. Seu
[esquema](https://docs.foursquare.com/data-products/docs/places-os-data-schema)
inclui categorias, localização e Instagram quando informado, mas não lista nota
ou quantidade de avaliações. A [forma atual de acesso](https://docs.foursquare.com/data-products/docs/access-fsq-os-places)
exige conta e token no portal. Ainda é necessário medir preenchimento no Brasil,
condições do portal, atualidade, custo operacional e recursos de consulta.

### Yelp Places

A [busca oficial](https://docs.developer.yelp.com/docs/places-intro) aceita
segmento e localização. O [plano Base](https://docs.developer.yelp.com/docs/plans)
inclui nota e número de avaliações; site do estabelecimento exige Enhanced ou
Premium. `pt_BR` é um [locale suportado](https://docs.developer.yelp.com/docs/resources-supported-locales),
mas isso não comprova a quantidade ou qualidade dos negócios brasileiros. O
cadastro exige conta Yelp e aplicativo para obter chave. O [trial](https://docs.developer.yelp.com/docs/places-faq)
permite até 5.000 chamadas em 30 dias somente para avaliação, sujeito a limites
diários; os planos pagos incluem volume mensal e condições variáveis. Conferir
preço e franquia vigentes antes de contratar.

A FAQ permite cache do conteúdo por até 24 horas e armazenamento de IDs, mas
informa que análise comercial não é permitida em integrações Places. A aplicação
dos dados em ranking, recomendação de concorrentes ou envio ao Jev requer consulta
específica ao Yelp, inclusive sobre o produto Insights. Os resultados exigem
[atribuição e requisitos de apresentação](https://docs.developer.yelp.com/docs/places-display-requirements).

### Recomendação prática para a pesquisa automática

Foursquare Places é o primeiro candidato a esclarecer com o fornecedor: tem
pesquisa multissetorial e pode fornecer tanto sinais de avaliação quanto perfil
social, reduzindo etapas quando os campos existem. A [EULA self-service](https://foursquare.com/legal/terms/apilicenseagreement/)
prevê integração e exibição nos serviços próprios, com atribuição, sob restrições;
isso não confirma que o nosso uso de ranking, persistência e IA externa esteja
coberto. Sua [política de uso](https://foursquare.com/legal/terms/aup/) restringe
combinação e armazenamento de dados e exige autorização prévia por escrito para
benchmark ou teste de disponibilidade/desempenho. Perguntar ao fornecedor sobre
esse teste, acesso Premium, campos para o Brasil, processamento por IA externa,
exibição ao cliente e preço antes de assumir viabilidade.

Yelp é alternativa técnica, condicionada à resposta sobre uso comercial dos
dados e à qualidade local. Places OS é uma alternativa aberta para localização,
categoria e @ quando disponível, mas sem nota ou contagem; não resolve sozinho o
requisito de reputação. Em qualquer opção, nota de estabelecimento não mede
engajamento social. Enquanto isso, manter indicação manual de referências e
provedores simulados, sem anunciar sugestões automáticas já disponíveis.

### Tripadvisor e dados abertos

A [busca do Tripadvisor](https://tripadvisor-content-api.readme.io/reference/searchforlocations)
abrange hotéis, restaurantes, atrações e localidades; é útil em turismo e
alimentação, mas não deve ser a única fonte multissetorial. A documentação aponta
uma transição para uma plataforma nova; acesso, custo e termos precisam ser
revalidados.

OpenStreetMap pode complementar dados de categoria e localização, sem pressupor
avaliações ou perfil social. A [política do Nominatim público](https://operations.osmfoundation.org/policies/nominatim/)
impõe limites e não deve ser tratada como serviço de varredura em escala.
Cobertura, licença, atribuição e infraestrutura devem ser estudadas.

## Critérios de comparação e seleção

### Alcance e localização

O cliente poderá optar por referências nacionais ou por uma busca próxima a um
ponto informado, com raio escolhido. Cidade e UF já existem no cadastro; CEP,
bairro ou cidade, sozinhos, não comprovam coordenadas exatas. Uma etapa de
referências deve permitir informar endereço ou usar a localização atual do
dispositivo mediante ação e permissão, mostrando a precisão conhecida e pedindo
confirmação do ponto. Endereço informado permanece pendente de localização até
ser resolvido e confirmado; busca nacional não depende de raio ou GPS.

O [Nearby Search (New)](https://developers.google.com/maps/documentation/places/web-service/nearby-search)
aceita centro e raio de até 50 km e oferece ordenação por distância ou
popularidade. O Text Search usa relevância ou distância e pode aplicar nota
mínima; nenhuma dessas opções documenta uma ordenação específica pela combinação
de estrelas e quantidade de avaliações. A pertinência de calcular ordenação
própria com dados Google deve ser esclarecida conforme os termos aplicáveis.
Busca nacional exige estratégia e amostragem próprias e não comprova obter os
melhores negócios do Brasil. Nada disso altera a indisponibilidade atual da
pesquisa automatizada.

### Como identificar redes sociais

Priorizar o link de perfil quando o campo de site já for uma URL social, como
ocorreu em parte da amostra de Places. Quando houver site do negócio, estudar
extração de links sociais declarados no próprio site e, quando necessário,
busca em fontes públicas adicionais. Os links são candidatos: verificar
correspondência, disponibilidade, origem e data, e permitir correção e aceite.
Página pública não concede direitos sobre posts ou autoriza cópia.

O [actor johnvc no Apify](https://apify.com/johnvc/google-maps-place-id-contact-api)
afirma consultar um identificador de lugar e procurar perfis no site; o
[actor seemuapps](https://apify.com/seemuapps/google-maps-business-links-scraper)
anuncia extração de links de fichas. São ferramentas de terceiros e suas
alegações, custos, limites, confiabilidade e condições ainda não foram validados.
O segundo informa descartar fichas sem links: isso deve ser considerado ao
medir cobertura, para não confundir resultados retornados com todas as buscas.
O [SerpAPI](https://serpapi.com/google-maps-api) é outro candidato a estudar;
consultar um perfil pelo @ não prova que o @ pertença ao negócio. Não assumir
taxa de sucesso de 40–70% sem medição própria. A presença de proxies ou uso de
terceiros não substitui confirmação dos direitos de acesso e dos termos.

#### Place ID, Apify e proveniência dos dados — consulta documental

Tecnicamente, há actors que recebem o Place ID e devolvem nome, endereço, nota
e quantidade de avaliações. Por exemplo, o fornecedor do
[Google Maps Places & Reviews Scraper](https://apify.com/itclan-bd/google-maps-scraper)
afirma que consulta fichas públicas do Google Maps e que todos esses campos vêm
delas; também esclarece que não é afiliado ao Google. O ID identifica a ficha,
mas executar outro serviço não transforma a origem dos valores em uma fonte
independente e não comprova permissão para guardá-los por seis meses. Os termos
e eventual contrato adequado para o uso pretendido continuam a confirmar.

O fornecedor do [actor johnvc](https://apify.com/johnvc/google-maps-place-id-contact-api)
distingue dados obtidos da ficha do Maps de redes sociais buscadas no site do
negócio. A prova autorizada, que consultou somente três sites com outro actor,
está registrada no [ensaio Apify](../evals/apify-sites-technical-probe-2026-10-30.md).
Uma URL encontrada no site é uma evidência distinta, não comprovação automática
de que o perfil pertence ao estabelecimento; termos do site e condições de
retenção continuam a verificar. A licença da plataforma Apify ou do actor não
substitui as condições aplicáveis aos dados de origem.

O [actor Open Places Business Leads](https://apify.com/plainsource/open-places-leads)
é uma alternativa pronta que declara consultar os dados abertos da
[Overture Places](https://docs.overturemaps.org/guides/places/) por local,
raio ou categoria, sem extrair fichas do Google. O fornecedor informa licença e
atribuição por registro: CDLA-Permissive 2.0, Apache 2.0 ou CC0, conforme a fonte.
Essas licenças permitem reutilização dos dados cobertos observadas suas condições;
enriquecimento posterior por sites pode ter outras condições. A documentação
afirma expressamente que essa base **não contém notas ou avaliações**. Não foi
comprovado que esse actor aceite Place ID do Google, nem sua cobertura no Brasil.
Assim, ele não satisfaz sozinho o critério de reputação escolhido pelo titular.

O [actor Local Business Leads](https://apify.com/flash_scraper/local-business-leads)
declara usar OpenStreetMap para descobrir negócios e consultar sites para
extrair `rating` e `review_count` de marcação `schema.org` quando existente.
O fornecedor relata preenchimento baixo em amostras fora do Brasil. Esses
valores podem ter proveniência e condições próprias, eventualmente envolver dados
de terceiros e não foram comprovados como reutilizáveis por seis meses no nosso
produto. Não foi comprovado que o actor aceite Place ID. Não inferir que a
nota declarada por um site seja a nota do Google ou que seja comparável entre
fontes. Nenhum dos dois actors foi executado nesta consulta documental.

Se houver coleta direta de sites, a implementação deve isolar e validar destinos,
redirecionamentos e tamanhos antes de acesso, além de respeitar limites e direitos
de uso; links para compartilhar conteúdo ou perfis de terceiros não confirmam
identidade do negócio. Nenhum actor ou scraping foi integrado ao produto, e não
houve autorização de consultas pagas recorrentes nesta etapa.

Usar dados fictícios primeiro, com pelo menos alimentação, manicure, pet shop,
oficina e serviços profissionais em cidades distintas. Incluir: 5,0 com duas
avaliações versus 4,8 com centenas; notas e contagens ausentes; filiais com mesmo
nome; negócios sem endereço público ou sem @; dados desatualizados; fonte
indisponível. A fórmula e os pesos ainda não foram aprovados: volume pode ajudar a
interpretar a nota, mas não garante legitimidade nem deve eliminar automaticamente
um negócio novo. Similaridade, reputação na fonte e engajamento social permanecem
dimensões distintas; dados ausentes não são zero.

Medir candidatos relevantes por segmento, presença e correção do @, proporção de
dados ausentes, falsos vínculos, tempo e custo. O cliente informa suas próprias
referências e pode aceitar ou rejeitar sugestões. O Jev só recebe candidatos e
evidências cujo processamento esteja autorizado. Não presumir que ele localiza
perfis ou explica decisões em texto sem componente adicional.

## Prova técnica proposta

1. Preparar uma amostra de consultas genéricas e contagem máxima; revisar
   elegibilidade da fonte e orçamento. Fazer provas com provedores simulados.
2. Em projeto Google separado de teste, habilitar Places API (New), limitar a
   chave à API e ao ambiente de execução e definir quota reduzida e alertas.
   [Alertas de orçamento não substituem quotas](https://developers.google.com/maps/billing-and-pricing/manage-costs).
   Não colocar credenciais em chat, Git, logs ou relatório.
3. Após autorização de gasto, testar no máximo a quantidade combinada de buscas
   e os campos necessários para conferir cobertura, nota e contagem. Exemplo de
   requisição, sem chave nem dados de cliente:

   ```http
   POST https://places.googleapis.com/v1/places:searchText
   X-Goog-FieldMask: places.id,places.displayName,places.types,places.formattedAddress,places.rating,places.userRatingCount,places.websiteUri
   Content-Type: application/json

   {"textQuery":"pet shops em Curitiba, Brasil","pageSize":10}
   ```

4. Registrar somente o que o contrato permitir, conferir resultados e custos;
   não persistir ou enviar resultados ao Jev até confirmar a elegibilidade.
5. Comparar uma amostra equivalente do Foursquare se o acesso Premium e as
   condições estiverem disponíveis, sem presumir cobertura ou custo.

Nenhuma conta ou chave foi criada nesta pesquisa. Nada autoriza publicar,
reproduzir peças de terceiros ou iniciar processamento pago recorrente.
