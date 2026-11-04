# Mapeamento de atividade para Google Places — 04/11/2026

A pesquisa deve usar um tipo sustentado pelos termos e características do negócio.
`restaurant` não é fallback para contexto insuficiente ou para ramo desconhecido.

## Vocabulário e contrato

`google_places_taxonomy.py` fixa a versão
`google-places-table-a-2026-11-04-v1`, com 478 códigos únicos em 19 categorias da
[Table A oficial do Places API New](https://developers.google.com/maps/documentation/places/web-service/place-types).
A conferência foi feita em 04/11/2026. Só os identificadores públicos foram
transcritos; descrições de categorias são nossas e os rótulos curtos de tipos
são derivados dos próprios códigos. Não são armazenados dados de estabelecimentos.
`food`, `establishment`, `point_of_interest` e `geocode` não integram esse
vocabulário de filtros. O hash do conjunto ordenado é
`3f50c714ae2f715cd557726907e3dcc7e33cf5f3559ab6554585eaf8dd1364a0`.

O [OpenAPI oficial do Jev](https://api.typesafe.ai/openapi.json), consultado na
mesma data, limita cada pergunta Choice a 255 critérios. O adapter faz uma
requisição com uma pergunta de categoria principal e uma pergunta de tipo por
categoria. São 20 perguntas; a maior contém 168 opções incluindo abstenções.
A escolha final usa apenas o tipo da categoria principal. Incerteza sobre
categorias que não se aplicam não elimina um resultado conclusivo. Um empate
na maior probabilidade retorna `uncertain`; não há limiar de reputação nem
substituição por tipo presumido.

`JevPrimaryPlaceTypeMapper.map(business_terms, business_description, operation_id)`
retorna `mapped`, `no_match` ou `uncertain`, até um código, versão do vocabulário,
modelo informado e uso de tokens. Uma abstenção válida ainda é uma resposta
conhecida do fornecedor e tem uso contabilizável. Falha de transporte ou resposta
inválida usa `TYPE_MAPPING_RESULT_UNCERTAIN` e preserva reserva para recuperação.

## Efeito, segurança e validação

A chave, modelo, ativação e guard são obrigatórios. Rede real exige também
`network_enabled=True`; testes usam `MockTransport`. O guard recebe a requisição
completa antes de qualquer efeito, com identidade durável e credencial encapsulada.
O transporte não segue redirects nem repete automaticamente chamadas. O adapter
não persiste contexto, probabilidades ou payloads e usa apenas erros estáveis.
A execução/contabilização duráveis pertencem ao guard e workflow 0106.

Validação local: 66 testes unitários, 100% de linhas e ramos nos dois módulos;
Ruff e tipagem estrita. Casos incluem ramo não alimentar, abstenção, empate,
incerteza de categorias alheias, vocabulário fechado, limites do contrato,
binding exato, replay sem novo efeito, falhas e reserva incerta. Nenhuma chamada
real ao Jev ou Google foi realizada. Qualidade semântica requer o ensaio
controlado autorizado; transportes simulados não demonstram acurácia do modelo.
