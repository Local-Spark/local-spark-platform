# Ensaio da feature de referências — 04/11/2026

**Estado: implementação local validada, incluindo as decisões finais de conteúdo.**
A descoberta real chegou à lista de sugestões e ao
aceite. A primeira análise de feed terminou sem publicações elegíveis pelo filtro
atual. A referência manual concluiu uma análise parcial com nove padrões,
confirmados na leitura autenticada e no snapshot para geração. O CI final da
árvore integrada até a migração 0111 passou em 4.724 testes com 100% de linhas e
ramos. Depois desse CI, o titular resolveu as duas decisões abaixo; a extensão
passou nas provas dirigidas e no novo CI integral de **4.734 testes/100%**.

O ensaio foi autorizado para negócios fictícios, com teto acumulado de **US$ 5**.
Os provedores foram habilitados somente nos processos temporários do piloto;
as flags persistentes continuam desligadas. Não houve geração de imagem nem
publicação de conteúdo em rede social. Nomes, perfis, endereços e identificadores
dos estabelecimentos externos são omitidos deste relatório.

| Etapa | Evidência observada | Limite dessa evidência |
| --- | --- | --- |
| Primeiras buscas Google | As tentativas de 5, 20 e 50 km tiveram respostas rejeitadas pelo parser de campos opcionais. As identidades e reservas dessas tentativas foram preservadas. | Erro de interpretação da resposta não prova custo zero nem ausência de negócios. |
| Correção Google | O parser passou a tratar valores opcionais de componentes de endereço conforme o contrato, mantendo a validação estrutural dos dados presentes. | A correção não reutilizou ou apagou as operações anteriores. |
| Descoberta no segundo negócio fictício | O lote de 20 candidatos foi aceito. O Jev filtrou a semelhança; o sistema calculou as notas e formou a lista de dez, com três destaques Jev. | Um ensaio não calibra definitivamente a fórmula nem comprova qualidade comercial para todos os segmentos. |
| Contatos Apify | Dez consultas de contatos integraram os dez candidatos publicados na lista de sugestões. Um perfil de Instagram ficou disponível. | A busca de contato não equivale à análise das publicações desse perfil. |
| Aceite | Uma referência foi confirmada em **04/11/2026 às 16:35:22 UTC**, iniciando o prazo até **04/05/2027**. | Não foi necessário selecionar três referências para confirmar o aceite. |
| Primeiro feed | O Apify retornou 20 publicações; nenhuma passou pelo filtro atual de autoria/formato. O resultado não produziu aprendizados. | Não comprova falta de conteúdo útil no perfil; revela a necessidade de resolver as duas decisões abaixo. |
| Referência manual | Uma referência pública foi adicionada exclusivamente ao segundo negócio fictício. A análise terminou como `partial` às **17:10:58 UTC**, cobrindo 11 publicações e 40 imagens, com nove padrões editoriais e visuais. As 41 amostras Jev terminaram como `completed`. | O estado parcial permanece explícito; as amostras concluídas não tornam a cobertura do perfil completa. |
| Contexto para geração | GET autenticado e snapshot foram validados: duas referências selecionadas, um conjunto de aprendizados e nove padrões projetados para o modelo. | Essa validação não executou geração de imagem nem comprova a qualidade de uma peça final. |

A rejeição inicial do Google foi localizada em componentes opcionais de endereço.
O diagnóstico preservou somente contagens e metadados técnicos, sem salvar nomes,
endereços ou corpo da resposta. O ajuste segue o
[schema REST de AddressComponent](https://developers.google.com/maps/documentation/places/web-service/reference/rest/v1/places#AddressComponent)
e as regras de presença de valores padrão do
[ProtoJSON](https://protobuf.dev/programming-guides/json/#presence-and-default-values).
Os casos e limites da correção estão no
[desenho do parser](../design/google-places-address-components.md).

Das 20 publicações do primeiro feed, cinco eram carrosséis (`Sidecar`) atribuídos
a outro autor; quatro deles traziam coautoria explícita do perfil escolhido.
As outras quinze eram vídeos (`Video`). O filtro usado naquele ensaio deixou
esses itens fora da análise. O titular respondeu posteriormente:

1. Usar somente autoria direta; a condição de coautor não habilita uma publicação
   de outro autor.
2. Analisar capa e legenda de vídeos/Reels, sem analisar o vídeo em si.

O adapter foi atualizado com essas decisões. Vídeos usam apenas sua capa e
legenda; carrosséis mistos incluem capas explícitas dos itens de vídeo, com
resultado parcial. Cinco integrações com dados sintéticos e 164 unitários/100%
comprovaram autoria, downloads apenas das capas, legendas, padrões persistidos
e sua projeção para geração. Nenhuma nova chamada paga foi iniciada nessa extensão.

A coleta manual usou o escopo implementado na época. Seus resultados não foram
reescritos pela alteração posterior. A referência sugerida permanece indisponível para
aprendizados, com próxima análise em **04/05/2027 às 16:35:22.030995 UTC**. A manual
foi aceita em **04/11/2026 às 17:06:43.626416 UTC**, e sua próxima análise ficou
agendada para **04/05/2027 às 17:06:43.626416 UTC**. As datas preservam o instante
do aceite de cada associação. O worker dedicado do ensaio foi encerrado.

O piloto também revelou recibos Apify preliminares. Em cinco dos onze runs
conferidos, os valores posteriores diferiam dos registrados inicialmente. A
migração 0111 foi aplicada após backup verificado, e os onze recibos foram
reprocessados pelas funções restritas. A correção acrescentou **30.700 micros de
dólar**, sem repetir coletas, zerar reservas ou aumentar o teto.

O contrato do [GET Actor run](https://docs.apify.com/api/v2/actor-run-get) alerta
para custos e contadores ainda preliminares imediatamente após o término. Os
adapters agora aguardam pelo menos trinta segundos após `finishedAt` e verificam
os contadores de cobrança quando disponíveis. Nesse intervalo, repetem apenas
GET do mesmo run e conservam a reserva. Ajustes posteriores continuam aceitos
como revisões auditadas; a espera não é tratada como garantia de imutabilidade.
Ver [espera de contabilização](../design/apify-cost-settlement.md) e
[reconciliação 0111](../design/apify-cost-reconciliation.md).

Após a reconciliação e antes da referência manual, o total comprometido era
278.501 micros. Com a análise manual concluída, o retrato financeiro passou a:

| Componente | Micros de dólar | US$ | Tratamento no ledger |
| --- | ---: | ---: | --- |
| Apify | 174.502 | 0,174502 | Valores informados pelo fornecedor em doze runs, incluindo a coleta manual. |
| Google | 140.000 | 0,140000 | Reservas conservadas em quatro efeitos; não liquidadas como custo efetivo. |
| Jev | 141.000 | 0,141000 | Reservas de 47 efeitos: 41 amostras de análise e seis efeitos da descoberta. |
| **Total comprometido** | **455.502** | **0,455502** | Soma de valores informados e reservas ainda mantidas. |
| **Teto acumulado autorizado** | **5.000.000** | **5,00** | Permanece inalterado. |

Esse total não representa uma fatura final consolidada de Google e Jev.
As reservas sem recibo não foram convertidas em zero. A política e os limites
do ensaio estão em [operação do piloto](../design/reference-pilot-operations.md).

A plataforma conserva Place IDs, notas e conclusões próprias, associações de
perfis, versões de seleção e metadados de execução/custo. Na análise, conserva
somente os padrões e aprendizados derivados. Publicações, legendas, URLs de
publicações/imagens e bytes de imagens não são persistidos na base, no histórico
Temporal ou na auditoria. O primeiro feed não gerou padrões; a análise manual
confirmou a persistência e a projeção dos nove padrões próprios. Não foi
implementada limpeza dos armazenamentos remotos do Apify, conforme o escopo já
decidido.

A suíte web integral passou em **508 testes, com cobertura de 100%**, além de
TypeScript, build e verificação no navegador. Depois dessa rodada, duas mensagens
de endereço foram ajustadas e passaram na validação dirigida de **13 testes com
100%**, TypeScript e Prettier; os demais módulos mantêm a validação integral
anterior. A reconciliação 0111 passou em
38 testes de integração PostgreSQL, 12 unitários com cobertura integral do
wrapper, Ruff, mypy e roundtrip vazio da migração. Esses testes usam bancos
exclusivos `_test`, roles restritas e dados fictícios. O **CI final integrado
até 0111 passou em 4.724 testes**, com 16.470 statements e 4.464 branches cobertos
integralmente, Ruff/format e mypy aprovados. Durou 1.018,29 segundos; o runner
removeu somente seu banco e logins exclusivos ao terminar. Houve um aviso de
depreciação de dependência do TestClient, sem falhas.

O CI posterior às capas passou em **4.734 testes**, com **16.471 statements** e
**4.466 branches** cobertos integralmente, Ruff/format e mypy aprovados. Duração:
1.196,10 segundos. O runner removeu seu banco `_test` e seus logins exclusivos.
A explicação na web passou em dez testes dirigidos/100% do componente, TypeScript
e Prettier. Não houve nova chamada paga ou alteração do resultado histórico do piloto.

O escopo de conteúdo está respondido, implementado e validado. A fidelidade comercial das peças geradas
continua sendo um gate próprio da BL04, pois este ensaio não gerou nem publicou
uma peça final.
