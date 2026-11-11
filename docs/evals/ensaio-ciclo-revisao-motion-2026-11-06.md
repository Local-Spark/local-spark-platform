# Ensaio do ciclo de revisão de Reel — resultado parcial

Atualizado em 08/11/2026. Critérios e protótipo privado foram implementados em
06/11. A continuação independente produziu críticas válidas de Dog/Luma com
contexto criativo v2, mas nenhuma correção. Este registro conserva o resultado
próprio de Intensa/Dog/Luma, sem comparação original/corrigida nesse trio. O
[ensaio separado do 1c](ensaio-revisao-reel-1c-2026-11-08.md) produziu v1 e crítica
favorável; o titular confirmou melhora de legibilidade, mas questionou o motion,
sem aceite global. **A etapa 3 continua incompleta** e o
fluxo ainda não está integrado ao produto. O
[plano e limites](plano-ciclo-revisao-motion-2026-11-06.md) documenta a rodada.

## Execuções e custos da revisão

| Execução | Resultado | Custo conhecido da execução | Reserva da execução |
| --- | --- | ---: | ---: |
| [Primeiro run](../../.local/evals/motion-review-runs/c1c45556-adab-4694-8495-1fcd327b9624/report.html) | Três críticas `adequate`, nenhuma correção. Auditoria constatou que direção, feedback, skill própria e instruções criativas estavam incompletos no contexto. | US$ 0,2520500 estimados | US$ 0,75 |
| [Continuação interrompida](../../.local/evals/motion-review-runs/87acffe2-12ef-488d-921e-8f1745691d1f/report.html) | Primeira crítica parou em `transport_or_recording_failed`, sem resposta salva. Operação `2b9fa3ad-c4c1-4bd1-8490-daf573fbf339` permanece incerta; sem retry nem refações. | Desconhecido | US$ 0,25 |
| [Continuação independente de Dog/Luma](../../.local/evals/motion-review-runs/4338880a-10f2-48a7-96cd-54138f87dbdd/report.html) | Duas críticas com contexto v2: `adequate`, sem achados acionáveis ou correções. Intensa bloqueada. Estado `completed_partial_human_pending`. | US$ 0,1751650 estimados | US$ 0,50 |
| Acumulado | Seis tentativas, cinco respostas; nenhuma peça derivada. | US$ 0,4272150 conhecidos; total desconhecido | US$ 1,50 |

Estimativa não é fatura. Os valores da tabela são custos da revisão; geração
histórica dos três vídeos permanece separada nos relatórios e não vira custo
zero por reutilizar o arquivo. O teto original autorizado, até 15 chamadas e
US$ 6,75 em reservas, não foi esgotado. Saldo disponível não prova custo nem
libera reenvio de operação incerta.

A primeira continuação foi iniciada com orçamento de US$ 6,75 e limite planejado
acumulado de US$ 4,50 em reservas; parou antes de completar esse plano. A
continuação independente admitia somente Dog/Luma: no máximo seis chamadas
novas e US$ 3,50 de reservas acumuladas, incluindo as anteriores. Usou duas
chamadas; nenhuma correção foi disparada porque não houve falha acionável
apontada. A operação incerta de Intensa continua no ledger e no relatório.

## Resultado observado e limites

As críticas v2 de Dog e Luma receberam o contexto criativo completo preparado,
com evidências da versão original. Ambas conservaram `v0` e declararam ausência
de defeito relevante acionável. Isso comprova que o executor respeitou a parada
sem refação desnecessária; não comprova que o crítico detecte todos os defeitos,
que corrija um problema real ou que melhore o resultado. A primeira rodada com
contexto incompleto permanece evidência funcional limitada, sem reclassificação.

O [relatório atual](../../.local/evals/motion-review-runs/4338880a-10f2-48a7-96cd-54138f87dbdd/report.html)
preserva os três originais, críticas disponíveis, operações e custos. Intensa
não recebe recomendação automática sem crítica v2 válida. A avaliação humana
e a escuta no celular continuam pendentes; não existe versão `v1` nesta rodada.
O titular escolheu em entrevista testar a correção do [Reel histórico 1c](plano-revisao-reel-1c-2026-11-08.md)
com falha conhecida de legibilidade. Há pacote offline de 69 arquivos, com dez
normalizações históricas preservadas, e a ponte declarativa está implementada,
com qualificação completa aprovada. Não é a resposta HTML/JS dos casos acima.
O titular autorizou em entrevista própria até três chamadas/US$ 1,25 e envio à
OpenAI. O [resultado separado do 1c](ensaio-revisao-reel-1c-2026-11-08.md)
concluiu três respostas e uma v1, preferida pela crítica final, com US$ 0,527685
estimados novos; o titular reconheceu melhora tipográfica e questionou o motion,
sem aceite global. A falha de unidades já foi
corrigida na geração atual; essa prova não demonstra ganho criativo geral.
O saldo desta rodada não se transfere ao 1c; custos e incerteza do trio permanecem.

Na preparação original, o cálculo do último quadro de Luma foi corrigido e
testado com duração de 284/30 s. Os tempos dos quadros são os tempos de seek
solicitados, não apresentação medida; amostras não comprovam o movimento
integral. Não houve escuta perceptiva pelo modelo; mix/trilha foram congeladas.
A escuta e a avaliação final no celular continuam humanas.

## Validação técnica e restante

Em 08/11, a tipagem do caminho independente foi corrigida e os binários locais
de mídia recuperados com hashes conferidos, em diretório persistente. Passaram
107 testes Python de motion e o preflight dos três casos; a verificação de
acesso ao modelo retornou HTTP 200. Após reproduzir o timeout e ajustar a
preparação dos testes de concorrência, o módulo passou em quatro casos
(93,61 s). Novo CI integral em execução, ainda sem aprovação.
Ver [recuperação das ferramentas](como-executar-ensaio-motion.md).

O relatório do run independente teve o CSS ajustado para caminhos longos e foi
regenerado sem modificar vídeos, críticas ou ledger. Conferência no navegador
em 390/1440 px e nos modos cego/identificado passou com três players, sem overflow,
erros JavaScript ou rede externa. Isso valida a apresentação e navegação do
relatório, não a qualidade criativa ou a audição dos vídeos.

O `make ci` integral de 06/11 passou na árvore daquela execução: 5.045 testes
Python da aplicação, 100% de linhas e branches, além de 91 testes Python de
motion, três Node de áudio e 62 Node do renderer; Ruff e mypy aprovados. Banco
`_test` e Temporal descartáveis, processo em UTC. Essa evidência histórica não
valida automaticamente a continuação atual. [Condições e tentativas](../CHANGELOG.md).

Critérios e protótipo existem localmente; a prova comparativa, o julgamento
humano e a decisão sobre custo-benefício permanecem abertos. Não afirmar
melhoria, aceite comercial, integração, WhatsApp ou publicação. Os relatórios e
artefatos em `.local` são privados e podem não existir em outro checkout.
