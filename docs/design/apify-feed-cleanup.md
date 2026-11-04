# Integração Apify: resposta e dados transitórios

O titular esclareceu que deseja o fluxo de chamada e resposta, sem uma etapa de
exclusão dos armazenamentos internos do Apify. Publicações, imagens e legendas
são processadas apenas em memória na nossa plataforma; não entram no nosso
banco, logs, auditoria, outbox ou histórico Temporal. Apenas os perfis e
aprendizados autorizados poderão ser persistidos. O adapter experimental de
DELETE preparado anteriormente foi removido; nenhuma exclusão real ocorreu.

A API pode iniciar uma execução do Actor e, em seguida, ler o resultado dessa
mesma execução. A leitura não inicia outra pesquisa; eventuais custos de leitura
ou de recursos da plataforma continuam sujeitos ao orçamento. O
[endpoint síncrono](https://docs.apify.com/api/v2/actor-run-sync-get-dataset-items-post)
retorna itens diretamente, mas uma conexão perdida pode deixar o chamador sem o
estado ou o ID do run. A preparação atual usa o ID recebido na submissão para
recuperar o resultado; perda anterior ao recebimento desse ID permanece ambígua,
conserva a reserva e não autoriza reenvio automático.

A migration `0093_reference_feed_resources` prepara registro privado dos IDs
do run, dataset, store, fila e build associados à tentativa. Sua função segue
sem GRANT runtime e ainda não comprova, sozinha, a resposta recebida. A activity
futura precisa autenticar o vínculo entre a resposta e a operação cercada; o
registro não inclui publicações, legendas ou imagens.

O Actor de perfil Instagram pode retornar, além do nome, posts recentes no
dataset do fornecedor. O adapter simulado descarta esses campos e não persiste
conteúdo na nossa plataforma. Ainda faltam guarda, origem comprovada, integração
e reconciliação; nenhuma chamada paga foi realizada nesta fatia.

Falha remota pode ter custo. Uma nova tentativa exige prova durável e
autenticada da falha conclusiva, nova identidade e nova reserva, mantendo o
hold anterior até reconciliação. Estado incerto não autoriza repetição. O
adapter `apify_contacts_terminal_failure` interpreta apenas respostas
simuladas e não cria essa prova nem autoriza retry. A configuração autenticada
do Actor, o vínculo de run/build/credencial e a reconciliação continuam pendentes.
