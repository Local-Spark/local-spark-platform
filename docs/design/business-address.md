# Endereço próprio do negócio

A API `GET/PUT /api/v1/organizations/{tenant_id}/businesses/{business_id}/address`
registra o endereço que o titular declara ser o da loja. A origem de uma pesquisa
por GPS ou endereço não é copiada para esse cadastro. Salvar não chama Google,
Apify ou Jev e não afirma que o endereço foi geocodificado.

A escrita exige `operation_id`, `expected_version` e endereço com rua, número,
cidade e UF; CEP, bairro e complemento são opcionais. A primeira versão esperada
é zero. Mudança efetiva cria versão imutável e conserva as anteriores. Endereço
idêntico conserva versão e data de criação. Duas alterações concorrentes sobre a
mesma versão resultam em uma gravação e um conflito, sem sobrescrever a primeira.
Repetir a mesma operação e payload pelo mesmo titular retorna a versão original,
mesmo que o endereço atual já tenha mudado; reutilização incompatível é recusada.

Titulares ativos da mesma organização compartilham leitura e gestão. O serviço
retém locks de conta/membership durante a transação e as tabelas usam RLS com
conta e associação ativas. Viewer, outra organização e titular revogado não têm
acesso. O helper existente de lock de identidade também pode ser executado pela
role da API; essa permissão não admite mutação de custos nem despacho de provedor.

Versão, cabeça, operação, auditoria e outbox são gravadas atomicamente. O evento
`business.address_saved` contém somente IDs e versão, sem o endereço. Não há
consumidor de provedor associado ao evento nesta fatia. O downgrade recusa
apagar versões ou operações existentes.

Ainda faltam interface conectada, geocodificação e armazenamento permanente do
ponto comprovado, ligação da versão do endereço à admissão e à publicação das
referências, e uso no comparador da própria loja. Esta API fornece a origem
explícita do endereço para essas integrações; não conclui a busca real.
