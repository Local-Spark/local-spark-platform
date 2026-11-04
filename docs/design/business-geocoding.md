# Endereço próprio, localização e identidade na descoberta

A migration `0103_business_geocoding` conecta o endereço versionado de0100 à API,
relay, Temporal e Google Geocoding v4, com o adapter real e transportes simulados
nos testes. Nenhuma chamada paga foi realizada. O recurso depende de habilitação,
credenciais, pilot e tarifa ativos e política de orçamento persistida; sem isso,
a API recusa o início e continua permitindo consultar dados já resolvidos.

## Contrato do cadastro

Sob `/api/v1/organizations/{tenant}/businesses/{business}/address`:

- `GET /geocoding`: estado da versão atual e coordenadas próprias quando resolvidas.
- `POST /geocoding`: `{operation_id,address_version}`, retorna202 com o mesmo estado.
  Uma versão de endereço tem uma única intenção; repetir a chamada não cria outro
  efeito pago. O contexto inicial do negócio deve existir.
- `POST /geocoding/confirm`: `{operation_id,address_version,geocode_id,candidate_id}`.
  Só necessário quando o resultado não identifica inequivocamente o endereço.

O retorno é `{enabled,address_version,geocode_id,status,coordinates,candidates}`.
`status` é `unrequested`, `pending`, `resolved`, `confirmation_required`, `not_found`
ou `uncertain`; cada ponto é `{id,latitude,longitude}`. O titular pode abrir os pontos
num mapa e escolher um candidato. Não há seleção implícita entre opções ambíguas.
O identificador geocodificado de um endereço não comprova a identidade de uma loja.

Nome formatado, componentes e Place ID da resposta de geocodificação existem
somente na memória da activity. São persistidas coordenadas do endereço próprio;
quando o titular confirma uma opção, as demais opções são descartadas. A declaração
do endereço e o ponto confirmado continuam versionados no cadastro. Uma origem GPS
de pesquisa não se torna endereço da loja.

## Custos e recuperação

A intenção possui operação, origem, efeito e eventos duráveis. Um HMAC vincula o
endereço próprio, sua versão, o pedido exato e a credencial. O claim verifica o
endereço vigente, o titular, os eventos e limites antes de liberar a rede; a
transação termina antes do HTTP. O envelope Temporal contém somente IDs.
O resultado usa o executor token e é imutável após concluir; erro ou perda da
resposta mantém a reserva incerta e não permite novo HTTP automático.
Uma resposta válida não prova valor de fatura: sua reserva continua contabilizada
até conciliação com evidência adequada. Nenhum valor efetivo é inventado.

A origem geocodificada é reutilizável. Quando a pesquisa manual usa o mesmo
endereço declarado e resolvido, `geocode_origin_id` é associado à busca e seu
custo entra no limite por pesquisa e fornecedor de0102, além dos limites mensais
e do piloto. GPS utiliza seu próprio ponto; não herda o custo de uma origem que
não utilizou. Mudanças de preferências não invalidam um endereço já resolvido.

## Identidade do próprio negócio

A admissão Python existente passa a exigir o cadastro próprio. A antiga função
SQL sem vínculo perdeu acesso pelo app. Sob locks consistentes são carregados o
nome atual do cadastro, versão do negócio, endereço, contexto e origem utilizada;
o HMAC privado e o nome próprio fornecido pelo titular ficam vinculados à busca.
O loader privado da activity recomputa o HMAC. Os claims Google/Jev/recomendação
para buscas admitidas e a publicação revalidam nome/endereço/contexto.
Uma mudança de nome é detectada mesmo se um writer não incrementou `row_version`.
`load_business_identity` fornece nome/endereço somente em memória para o comparador
que exclui a própria loja. A orquestração da descoberta deve utilizar esse loader;
esta fatia não substitui a confirmação de identidade quando o comparador encontra
ambiguidade nem implementa o restante dos fornecedores.

## Configuração explícita

`MEU_BRACO_DIREITO_REFERENCE_GEOCODING_ENABLED` permanece falso. Para preparar
um ensaio local, configurar os campos `REFERENCE_GOOGLE_API_KEY`,
`REFERENCE_PROVIDER_HMAC_KEY`, `REFERENCE_PROVIDER_KEY_VERSION`,
`REFERENCE_GOOGLE_CREDENTIAL_VERSION`, `REFERENCE_PROVIDER_PILOT_ID`,
`REFERENCE_GEOCODING_TARIFF_VERSION`, `REFERENCE_GEOCODING_RESERVED_USD_MICROS`
e o login correlator restrito, todos com o prefixo `MEU_BRACO_DIREITO_`.
A tarifa deve cobrir exatamente o field mask do adapter. A configuração não cria
orçamentos ou tarifas automaticamente; devem ser revisados antes do ensaio pago.

## Validação e limites

21 testes passaram, com100% de linhas e branches dos módulos novos
(182 statements/26 branches); Ruff e mypy10 módulos também passaram. O downgrade
0103→0102 e upgrade em banco vazio foi validado. Testes usam dados sintéticos,
PostgreSQL exclusivo `_test`, logins temporários
restritos, Temporal local e HTTP simulado. Cobrem chamada única, custo anterior à
rede, fonte manual reutilizada, titular compartilhado, privacidade dos envelopes,
confirmação/replay, orçamento insuficiente, mudança do endereço/credencial,
resultado vazio/incerto, resposta perdida e alteração de nome. O ensaio pago e a
integração completa da descoberta, perfis e aprendizado são entregas separadas.
