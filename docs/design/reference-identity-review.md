# Identidade da loja e família de raios

A evidência de uma busca contém Place IDs, notas próprias, semelhança própria e a decisão sobre qual resultado corresponde à loja. O matcher usa dados transitórios do Google em memória; o banco não guarda esses nomes/endereço/tipos. O commit de notas, semelhança e conclusão do matcher é único, evitando depender de dados descartados em uma retomada.

A correspondência clara resolve a exclusão automaticamente. Na ambiguidade, GET/POST `reference-results/searches/{search_id}/own-business-review` permite escolher um Place ID ou `null` (nenhum). A operação exige titular ativo, versão atual da identidade e IDs do candidato; audit registra o titular que decidiu. O evento `reference.search_reviewed` identifica a busca/ator/operação originais, para sinalizar o workflow existente. Ranking e publicação recusam uma revisão pendente ou inclusão da própria loja.

Uma resposta Google realmente vazia habilita a transição para o próximo raio maior aprovado. A transição tem operação/evento determinísticos e vínculo durável; reexecutar não cria outro efeito. Raio já ocupado é cache, mesmo quando descoberto por outro titular. Esse compartilhamento expõe metadados e a prova booleana de vazio, nunca executor tokens. A alteração do raio efetivo exige o vínculo durável; o documento de preferências continua igual.

Todas as buscas pagas de uma família compartilham o teto por pesquisa/fornecedor. O custo da origem geocodificada aparece uma vez por reserva, sem duplicação por joins. Reservas incertas continuam contabilizadas. Resultado vazio final não cria evidência Jev inexistente. Um ciclo inteiramente vazio sem confirmação libera apenas o head para uma nova rodada; resultados, reservas, auditoria, ocupação histórica e seleções anteriores permanecem. Um ciclo confirmado nunca é liberado por essa regra.

O leitor da família devolve raiz, busca atual, estado e permissão canônica de retry. Recibos de transição/publicação permitem replay mesmo após head liberado ou preferências alteradas, sem novos efeitos. As novas tabelas não são graváveis pela aplicação; mutações entram por funções privadas com RLS, autorização e locks.
