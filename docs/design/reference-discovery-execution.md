# Execução integrada da descoberta de referências

As revisões `0106_reference_execution` e `0107_reference_identity_review`
conectam a admissão ao workflow Temporal com identidade estável por busca. A API
recebe somente a operação; raio, contexto versionado e identidade da loja vêm do
servidor. Credenciais, piloto, política, tarifas e flag explícitos são necessários.
A configuração desta fatia permite execução somente em desenvolvimento/testes.

O executor resolve o tipo oficial Google com Jev, consulta até 20 negócios,
identifica a própria loja, filtra semelhança e somente então calcula notas. Após
resolver uma eventual ambiguidade da loja, prepara até dez candidatos elegíveis,
obtém até três destaques estruturados e associa Instagram pelo Apify. Não existe
nota de corte. A dúvida sobre semelhança exclui o candidato. Dados brutos do
Google e inputs Jev ficam em memória; as projeções persistidas são restritas aos
IDs e dados próprios aprovados.

As etapas persistem resultados próprios para recuperação. Polling Apify usa o
mesmo run. Uma falha terminal comprovada admite retomada explícita do perfil,
sem repetir Google/Jev; POST com resultado incerto não é repetido. Revisão da
loja e retry sinalizam o workflow existente. O workflow pausa após polling
limitado e pode retomar; suas activities ocultam diagnósticos privados de erros
que seriam gravados no histórico Temporal.

O leitor fornece o estado canônico da família de raios, publicação e permissão
de retry. A tela conectada acompanha esses campos sem iniciar chamadas pagas por
polling. O comportamento de família vazia, exclusão da loja e orçamento comum
está em [identidade e raios](reference-identity-review.md).

Validação dirigida: 57 testes (incluindo 17 integrações) e 100% de linhas/branches
nos módulos de execução, guarda e armazenamento; 94 unitários dos adapters Jev
e 56 de configuração, API e Temporal, também com cobertura integral dos recortes.
O roundtrip vazio 0107 → 0105 → 0107 passou. As provas usam dados e HTTP simulados;
o ensaio pago e o CI de toda a árvore integrada são etapas distintas.
