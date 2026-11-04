# Piloto local de referências

O titular autorizou até **US$ 5 no total**, usando dados fictícios. Esse teto não
é uma mensalidade aprovada para operação comercial. As credenciais ficam no
ambiente local, sem valores em comandos, documentação, relatórios ou logs.

## Configuração financeira

`scripts/configure_reference_pilot.py` mostra um plano por padrão. `--apply`
configura as tabelas existentes com uma transação administrativa e não liga
flags de fornecedores. Aceita somente development/testing, PostgreSQL localhost,
mesmo banco da conexão runtime e usuário administrativo separado. Testing exige
nome terminado em `_test`.

| Limite | Total | Google | Jev | Apify |
| --- | ---: | ---: | ---: | ---: |
| Uma pesquisa e suas ampliações | US$ 1,00 | US$ 0,15 | US$ 0,25 | US$ 0,80 |
| Contador mensal do piloto | US$ 5,00 | US$ 0,50 | US$ 0,50 | US$ 4,00 |

Além desses limites, o piloto tem **US$ 5 acumulados em toda sua duração**, sem
renovação mensal. O mesmo ID é reutilizado e o script jamais zera gasto/reserva.
Uma configuração diferente existente faz a aplicação falhar, preservando o banco.
Tarifa, política e ativação ficam versionadas; divergências causam rollback.

A política v2 redistribui os limites internos do mesmo piloto para permitir
analisar as publicações com o Jev. O script aceita a transição da v1 somente
quando seus valores correspondem exatamente à configuração anterior. Preserva
todos os consumos e reservas; o teto acumulado de US$ 5 continua o mesmo.

Reservas por chamada: Nearby US$ 0,035; geocodificação US$ 0,005; Jev US$ 0,003;
contatos Apify US$ 0,50; feed Apify US$ 0,10. São limites/reservas conservadores,
não promessa de custo efetivo. O limite mínimo de Compass é US$ 0,50 por run;
o recibo terminal pode reduzir a reserva ao custo declarado pelo fornecedor.
Sem recibo, a reserva permanece. Preços e contratos em
[conferência de 04/11](../evals/reference-provider-contracts-2026-11-04.md).

## Preparação

Conferir a build do Actor antes de configurar. As builds observadas em 04/11 foram
Compass `0.14.782` e Instagram `0.0.840`; não são aliases estáveis. A build
Instagram anterior, `0.0.839`, foi substituída pelo fornecedor durante a
validação local. O preflight bloqueou a versão antiga, sem coleta paga; a nova
build foi conferida como concluída e compatível com permissões limitadas.
Exemplo de
plano sem alteração de banco nem chamada ao fornecedor:

```sh
uv run python -m scripts.configure_reference_pilot \
  --contacts-build 0.14.782 --feed-build 0.0.840
```

Depois de conferir o plano, `uv run --env-file .env python -m
scripts.configure_reference_pilot` com os mesmos argumentos e `--apply` usa a
conexão de migração local. O JSON resultante contém somente IDs, tarifas e limites.
O script não copia credenciais nem altera `.env`.

A execução deve usar `reference_provider_pilot_id` e versões de tarifas
exatamente iguais ao plano. São necessários `reference_provider_hmac_key`, versão
da chave e versões das credenciais, além das credenciais Google/Apify/Jev. Não
imprimir chaves. O worker usa o correlator restrito, nunca a conexão administrativa.

Durante o ensaio, habilitar os provedores apenas nos processos temporários que
tratam a organização fictícia e sua fila Temporal específica. Não iniciar relay
genérico com as flags de ensaio nem consumir eventos de negócios reais. Confirmar
o ledger ao final e encerrar esses processos. Flags persistentes ficam desligadas.

## Estado de validação

Plano e restrições locais passaram em 14 unitários. Os cinco testes SQL de
replay, preservação do gasto, transição de política e rollback passaram em banco
isolado, junto de quatro testes de endereço. A primeira
rodada encontrou tentativa de inserir uma política já ativada; o replay agora
consulta a existência antes da inserção, preservando a imutabilidade. O plano foi
aplicado ao banco local de desenvolvimento em 04/11, incluindo a política v2; o piloto mantém o teto
acumulado de US$ 5 e as flags persistentes continuam desligadas. O ensaio real
já publicou dez candidatos com três destaques Jev e confirmou uma referência,
iniciando o prazo de seis meses. A primeira coleta de feed terminou sem padrões
pelo filtro de autoria/formato. Uma referência manual pública foi adicionada
apenas ao negócio fictício para validar o restante da análise: onze publicações,
quarenta imagens e nove padrões, preservando o estado parcial. A leitura
autenticada e o snapshot de geração foram conferidos. Worker dedicado encerrado.

O piloto também identificou campos opcionais Google rejeitados pelo parser e
recibos preliminares do Apify. As correções foram implementadas e testadas;
a 0111 reconciliou onze recibos sem refazer coletas ou zerar reservas. O custo
comprometido chegou a US$ 0,455502, incluindo reservas Google/Jev não liquidadas.
O [relatório do piloto](../evals/reference-feature-pilot-2026-11-04.md) distingue
essas reservas de custos informados e registra as limitações. O CI final passou
em 4.724 testes com 100% de linhas e ramos, Ruff e mypy. Nenhuma imagem nova foi
gerada ou publicada.
