# Google Places — componentes de endereço opcionais

Estado: correção local validada em 04/11/2026; retomada do piloto real e CI
integral pertencem ao fechamento da feature de referências.

## Evidência e contrato

O piloto autorizado com negócio fictício recebeu HTTP 200 do Nearby. Uma
observação posterior registrou somente metadados de diagnóstico: 20 candidatos,
dois rejeitados no bloco de validação de componentes de endereço. Nenhum nome,
endereço, avaliação ou corpo Google foi salvo nessa observação. Esse resultado
localiza o defeito no parser; os metadados não identificam qual valor opcional
estava ausente. As tentativas anteriores conservam suas identidades e reservas;
esta correção não autoriza reenviá-las.

O schema oficial declara textos simples e uma coleção repetida de tipos em
`AddressComponent`, sem exigir que estejam preenchidos. O formato ProtoJSON
pode omitir strings e coleções com valores padrão, ou representá-los vazios.
Fontes consultadas em 04/11/2026: [schema Places mantido pelo Google](https://raw.githubusercontent.com/googleapis/googleapis/master/google/maps/places/v1/place.proto),
[referência REST de AddressComponent](https://developers.google.com/maps/documentation/places/web-service/reference/rest/v1/places#AddressComponent)
e [presença e valores padrão em ProtoJSON](https://protobuf.dev/programming-guides/json/#presence-and-default-values).

## Ajuste

O adapter normaliza `longText` e `shortText` exatamente vazios para ausência,
apenas dentro dos componentes de endereço. Tipos omitidos equivalem a uma
coleção vazia. Valida os campos presentes antes de descartar componentes sem
texto longo ou tipos utilizáveis. Não inventa endereço nem significado para
componentes incompletos.

Objetos, listas, elementos e limites inválidos continuam sendo rejeitados,
inclusive quando outro campo do componente está ausente. `types: null`
continua inválido no contrato restrito do adapter. Identificador, nome, nota,
contagem e demais campos conservam suas validações. O DTO entregue ao matcher
e ao MAC mantém os invariantes existentes; esses dois módulos não mudaram.

Se um componente ignorado retirar evidência necessária de endereço, a
identificação da própria loja continua pedindo revisão. Componentes sem tipo
não interferem em uma correspondência completa obtida pelos demais campos.

## Validação

160 testes unitários passaram em Google Places, identificação da própria loja
e MAC do lote: 100% de 283 statements e 104 branches. Os casos novos usam
somente fixtures fictícias e HTTP simulado. Provam aceitação dos valores padrão,
rejeição estrutural antes de ignorar campos, preservação da nota/contagem,
correspondência clara ou revisão conforme a evidência disponível e MAC igual
para a mesma evidência normalizada.

Comando: `pytest app/tests/unit/test_google_places.py app/tests/unit/test_reference_own_business_match.py app/tests/unit/test_reference_google_batch_mac.py --cov=app.adapters.google_places --cov=app.services.reference_own_business_match --cov=app.services.reference_google_batch_mac --cov-branch`.

Não houve chamada paga, migração ou alteração dos efeitos existentes durante
a correção. Faltam o CI da árvore combinada e nova validação controlada do
caminho real; o teste do parser não comprova qualidade final das referências.
