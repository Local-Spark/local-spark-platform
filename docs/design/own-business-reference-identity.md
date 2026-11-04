# Identidade da própria loja na pesquisa de referências

O negócio do cliente não deve entrar nas sugestões. O titular autorizou
identificação automática quando nome e endereço corresponderem claramente, com
confirmação do cliente em caso de dúvida. Essa identificação deve ocorrer antes
da classificação, da nota e do ranking, sem consulta adicional inesperada.

A futura activity deverá comparar, em memória, os dados fornecidos pela resposta
da pesquisa já autorizada com o nome e o endereço confirmados da própria loja.
Uma regra conservadora é exigir correspondência normalizada exata do nome e dos
componentes de endereço disponíveis e suficientes, com um único resultado
compatível; ausência, divergência ou múltiplas opções levam a revisão. A regra
não pode tomar proximidade de coordenadas, nome isolado ou o Place ID de um
endereço geocodificado como prova de que a ficha comercial é a própria loja.

A identificação deverá criar ou atualizar, em operação autenticada e
versionada, o Place ID da ficha comercial e a proveniência da conclusão
(`correspondência clara` ou `confirmada pelo titular`). O commit deverá ligar a
versão da loja, a pesquisa, o resultado recebido, o efeito e sua reserva, com
audit/outbox sem dados privados. As linhas de endereço e os nomes obtidos do
Google são transitórios e não serão persistidos na plataforma. Uma conclusão
anterior incompatível com a versão atual exige nova avaliação. O cliente deve
poder resolver uma dúvida, sem que uma confirmação seja inferida pelo sistema.

A máscara da busca Nearby foi preparada para receber `formattedAddress` e
`addressComponents` na **mesma** chamada, somente em memória; ambos os campos
e a máscara participam dos MACs. O comparador usa componentes estruturados para
identificação, e endereço formatado isolado não prova identidade.
A tarifa correspondente e o teto ainda precisam ser validados antes de ativar
a busca. Uma mudança de máscara não autoriza chamada extra. Os dados usados na
comparação não são enviados a logs, Temporal ou resultados públicos.

Um comparador puro conservador verifica nome e endereço completos e retorna
identificação única, ausência ou candidatos para revisão. Ausência de endereço,
informações incompletas e resultados plausíveis ambíguos exigem revisão. Ele
passou em 36 testes unitários, com cobertura integral, mas ainda não tem acesso
a uma fonte versionada ou evidência autenticada e não está integrado ao fluxo.

Faltam
a fonte autorizada do endereço próprio, o produtor de componentes, o contrato
de confirmação, o vínculo transacional da identidade, a checagem nas cercas de
commit/publicação e testes de diferenças, ambiguidades e mudanças de contexto.
O armazenamento de semelhança e o fallback por ordem continuam inativos até que
ambas as evidências de identidade e origem estejam comprovadas.
