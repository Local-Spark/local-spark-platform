# Apify — conclusão da execução e atualização da cobrança

Estado em 04/11/2026: espera de contabilização implementada nos adapters de
contatos e feed; revisão auditável de recibos anteriores pertence à migração
0111. Nenhuma coleta adicional foi iniciada durante esta correção.

## Evidência

O piloto com negócio fictício concluiu uma coleta de feed. A plataforma leu e
liquidou 51.301 micros de dólar apenas 6,31 segundos após `finishedAt`. Um GET
posterior do mesmo run apresentou 20 eventos cobrados e contabilizados e total
de US$ 0,054000000000000006. O arredondamento conservador existente resulta em
54.001 micros. O valor anterior era preliminar, não uma cobrança calculada a
partir do número de publicações.

Uma conferência somente leitura dos dez runs de contatos e desse run de feed
identificou cinco recibos diferentes: quatro de contatos e o de feed. A soma
persistida era 89.801 micros; a soma atual informada pelo fornecedor,
arredondada para cima, era 120.501 micros. O ajuste necessário era 30.700 micros.
Essa conferência exibiu apenas valores e contagens de cobrança; não consultou
datasets nem gravou dados externos das publicações.

O contrato oficial alerta que a primeira resposta após o término pode conter
custos e contadores preliminares, recomendando novo GET cerca de dez segundos
depois. `usageTotalUsd` é o total pago; `usageUsd` é um detalhamento de consumo
da plataforma e não deve ser somado ao total. [Apify: Get Actor run](https://docs.apify.com/api/v2/actor-run-get).

## Comportamento

Os adapters preservam o mesmo run e retornam `pending` enquanto não houver
`finishedAt` válido, com fuso horário e pelo menos trinta segundos transcorridos.
Data futura ou inválida mantém a pendência. Não consultam o dataset nessa espera,
não expõem custo final, não liberam reserva e não iniciam outro POST.

Quando os mapas `chargedEventCounts` e `accountedChargedEventCounts` são
expostos, precisam conter contagens inteiras não negativas e coincidir. Campos
incompletos ou divergentes prolongam o polling. Se ambos estiverem ausentes, a
margem temporal ainda é obrigatória. A ausência de `usageTotalUsd` continua
significando custo desconhecido e conserva a reserva existente.

O Temporal já sabe repetir a inspeção do run pendente. Portanto a janela de
análise não encerra antes dessa espera, e os contatos não são publicados com
um recibo prematuro. A margem de trinta segundos é uma medida conservadora;
não transforma o endpoint do fornecedor em garantia de imutabilidade. Mudanças
tardias ainda exigem revisão auditável do recibo, sem apagar histórico ou zerar
o consumo acumulado do piloto.

## Validação e trabalho restante

275 testes unitários passaram com 100% de 547 statements e 186 branches nos
adapters de feed, contatos e metadados. Casos com relógio controlado cobrem o
limite de trinta segundos, datas inválidas, fusos equivalentes, contadores
pendentes e passagem ao recibo atualizado usando apenas GET do mesmo run.
Ruff e mypy passaram. As fixtures de integração agora incluem término válido;
um teste PostgreSQL foi ampliado para verificar a reserva intacta durante a
espera e a liquidação posterior. A rodada PostgreSQL e o CI combinado ainda
precisam executar essa versão.

A correção não altera regras de coautoria, imagens ou vídeos. A conciliação dos
cinco recibos do piloto deve ocorrer pelo caminho auditável da migração 0111;
os números acima são evidência de leitura, não uma afirmação de ajuste aplicado.
