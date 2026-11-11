# Reel 1c — legibilidade melhorada, qualidade criativa ainda não aprovada

Em 08/11/2026, o ciclo autorizado do Reel histórico 1c concluiu três chamadas
HTTP 200, sem retry ou resultado incerto. O run
`3a52c376-e8ea-4bea-b997-94ba59c628de` terminou `completed_human_pending`.
A crítica inicial encontrou o defeito de legibilidade; a correção gerou v1,
e a crítica final preferiu v1 e retornou `adequate`, sem achados. O titular
confirmou que B tem títulos e legendas melhores, mas questionou o formato e a
falta de motion. **A reparação de legibilidade foi reconhecida; qualidade global,
motion e áudio do 1c não foram aprovados.** Essa confirmação parcial, sozinha,
não encerrava a etapa 3. Em 09/11, a preferência humana “B ficou melhor.” no
[refinamento Giz](ensaio-refinamento-motion-giz-2026-11-09.md) completou a prova
no recorte demonstrado. Prosseguir à integração do Reel (4) e depois demais
formatos (5), já autorizados, sem promover o 1c a padrão criativo.
O estado `completed_human_pending` é preservado como registro do executor;
o feedback humano do 1c está descrito abaixo.

[Comparação privada com vídeos, críticas, custos e formulário de avaliação](../../.local/evals/motion-declarative-review-runs/3a52c376-e8ea-4bea-b997-94ba59c628de/report.html).
O relatório inicial e o QA dirigido da apresentação das limitações passaram.
A entrevista de legibilidade foi respondida
com confirmação de legibilidade e dúvidas sobre motion. O QA do relatório não
substitui a inspeção criativa ou a escuta humana dos vídeos.
O [plano do ensaio](plano-revisao-reel-1c-2026-11-08.md) preserva escopo,
autorização, preparação e limites.

## Original, correção e julgamento automático

| Versão | Evidência | Avaliação disponível |
| --- | --- | --- |
| [v0 histórica](../../.local/evals/motion-declarative-review-runs/3a52c376-e8ea-4bea-b997-94ba59c628de/reel1c/v0/render.mp4) | Primeira montagem do 1c, com dez normalizações técnicas históricas e nenhum dos sete ajustes manuais da variante posterior. | `needs_correction`: um achado `major`, `i01`, de títulos/legendas/convite pequenos, sustentado por seis quadros. |
| [v1 do modelo](../../.local/evals/motion-declarative-review-runs/3a52c376-e8ea-4bea-b997-94ba59c628de/reel1c/v1/render.mp4) | Direção corrigida validada e renderizada, preservando fatos, textos, fontes/materiais, cores, cortes, intervalos e plano de áudio. | `adequate`, sem achados; crítico prefere v1, com seis critérios `pass` e áudio `uncertain`. O titular confirmou melhora de títulos/legendas, mas questionou a ausência de motion; sem aceite global. |

Na v1, os três títulos passaram de `font_size=46` para `375` (48 px) e as quatro
legendas de `32` para `250` (32 px). Caixas de legenda têm largura `8800`; a
terceira usa `letter_spacing=-500`. A resposta foi executada após validação
contratual, sem ajuste visual manual para produzir sucesso. O crítico final
comparou evidências das versões e recomendou v1; essa recomendação é provisória,
não uma aprovação global do titular nem escolha automática definitiva. O
feedback posterior confirmou a melhora de legibilidade, com ressalva criativa.

Hashes dos arquivos finais:

- v0: `1c5e8d8f91f8d3aed6c49a45f37e69ffaa887523ccf4f1c144ca070b08c66f98`.
- v1: `5305dfda85284fd9a762320dc6e8fe6e0c95cbd20acbea3810fab2f030013eca`.

AAC, PCM decodificado e tempos da v1 conferem com o baseline. Isso comprova
preservação técnica do áudio, não a qualidade perceptiva da mixagem. Nenhum
áudio foi enviado para escuta pelo crítico. Os critérios de fatos, marca,
legibilidade, composição, movimento e integridade tiveram `pass` na crítica
final; o julgamento de movimento é limitado aos quadros observados.

## Feedback humano e lacuna de avaliação criativa

Resposta do titular em 08/11, preservada integralmente:

> sim. o B tem os titulos e legendas bem melhor. mas o que é isso. seria um story? era para ter motion? porque é só um video gravado pelo cliente com legenda e titulo em cima? o que ele deveria ter?

O [registro privado do feedback](../../.local/evals/motion-declarative-review-runs/3a52c376-e8ea-4bea-b997-94ba59c628de/human-feedback-legibility-2026-11-08.json)
conserva a fala exata, hashes de v0/v1/summary e interpretação parcial. O feedback
confirma a melhora dos títulos e legendas de B. Não confirma aceite
da peça completa, qualidade do áudio, ausência de regressões ou adequação do
motion, nem constitui rejeição global explícita. O contexto original foi conferido: `format=reel`, com pedido de cortes,
transições, motion graphics e legendas. A entrada é uma gravação ilustrativa
licenciada com locução sintética; não é vídeo ou voz de cliente real.

A peça histórica tem movimento discreto, principalmente pequenos ajustes de
enquadramento e fades. A ampliação tipográfica reparou a legibilidade, mas não
transformou essa direção simples no acabamento criativo esperado. O objetivo
do ensaio 1c era deliberadamente estreito e não incluía redesenhar a linguagem.
A falha de unidades que originou o texto pequeno já foi corrigida no schema de
geração atual; não é benefício novo do revisor nas próximas gerações.

A avaliação automática classificou movimento como `pass`, apesar da dúvida
humana sobre a presença de motion relevante. Isso expõe uma lacuna: detectar
animação ou integridade técnica não demonstra adequação criativa ao briefing,
narrativa, ritmo, transições ou acabamento. A qualidade criativa precisa ser
avaliada com as referências aceitas, sem converter qualquer movimento em
aprovação. **Intensa, Dog e Luma continuam as referências; o Reel 1c não vira
padrão de produto.** Esse feedback não revoga as avaliações positivas anteriores
dessas referências. Esse diagnóstico exigiu separar movimento observado de
atendimento criativo ao pedido. O contrato posterior do Giz foi implementado
e testado, mas ainda depende de calibração criativa real e julgamento humano.
Ele não reclassifica as críticas históricas do 1c. A correção concreta do relatório
abaixo melhora a apresentação de limites existentes, sem alterar a regra ou
mudar o padrão criativo. O diagnóstico não autoriza nova rodada paga nem
reabre operação incerta.

## Operações, custo e tempo

| Efeito | Operação | Estimativa de API | Tempo observado |
| --- | --- | ---: | ---: |
| Crítica v0 | `f48e3377-c84b-474d-92b1-315edc39972e` | US$ 0,124605 | 40,358 s |
| Correção v1 | `b3205955-fdee-493f-943a-28035efda6f2` | US$ 0,208475 | 74,004 s |
| Crítica v1 | `1d9b8337-1711-4f03-ab38-447b752929e1` | US$ 0,194605 | 40,199 s |
| Total novo | Três respostas HTTP 200, sem retry ou operações incertas | **US$ 0,527685** | **154,561 s** |

O teto autorizado e as reservas acumuladas deste run são **US$ 1,25**; reserva
não é gasto faturado. O subtotal histórico das APIs do 1c, incluindo falha
anterior, é **US$ 0,106892**. Somado ao ciclo novo, o subtotal de APIs é
**US$ 0,634577**. Esses valores são estimativas, não fatura ou custo completo:
trabalho humano, computação local e operação não foram precificados. Nenhuma
peça completa foi aceita pelo titular neste ensaio; a confirmação de
legibilidade não autoriza declarar custo por peça aceita.

Render da v1 e extração de evidências somaram **151,928 s**. O subtotal medido
com as três chamadas é **306,489 s** (cerca de 5 min 6 s), excluindo preparação,
preflight, qualificação, intervalos e trabalho humano. Não é duração total da
retomada ou SLA de entrega do produto.

O orçamento do 1c é próprio e foi autorizado após qualificação. A rodada
[Intensa/Dog/Luma](ensaio-ciclo-revisao-motion-2026-11-06.md) conserva seus seis
efeitos, US$ 0,427215 conhecidos e US$ 1,50 em reservas, com custo incerto de
Intensa ainda pendente. Não transferir saldo nem reconciliar essa incerteza por
causa do sucesso do 1c.

## Preparação, falhas e validação

O pacote preserva 69 arquivos, manifesto anterior de 56, contexto original,
fontes e dez normalizações históricas. Não é resposta HTML/JS; a ponte usa o
contrato declarativo original. A primeira qualificação parou no parsing de
`size` textual e `pkt_pts` do FFprobe 4.4.8, sem API; artefatos foram preservados.
O leitor corrigido passou no preflight de mídia existente e na segunda
qualificação completa, que recompilou/renderizou a direção original e conferiu
336 quadros/tempos e 526 pacotes AAC/PCM/tempos. Qualificação SHA-256
`21d7f2da63889674eb4b607523be3287a3d1f45459ddb746fa545d7154eabd78`.

O snapshot privado `qualified-code` conserva 11 arquivos: dez ligados à
qualificação, incluindo `uv.lock`, e o gerador do relatório. Manifesto e hashes
foram conferidos para permitir auditoria depois de mudanças no código ativo.
O relatório original tem SHA-256
`8a93ab0561adf4300df3e559ee3f0a3c6bb230dc10dcc41877e7f06be473bc4e` e foi conservado
como `report-before-limitations.html` após a revisão de apresentação abaixo.
A cópia permanece local; não comprova backup remoto ou restauração homologada.

Passaram 146 testes locais da ponte/orquestração (57+89), Ruff e mypy estrito.
Naquele recorte o CI geral ainda estava pendente. Após reproduzir falhas na preparação dos testes
de concorrência, a espera preparatória foi unificada em 60 s com detecção de
saída antecipada da tarefa em três testes; timeouts do negócio e fases de
bloqueio conservam os valores originais. O módulo passou em quatro testes
(93,61 s); iniciou-se novo CI integral, ainda sem aprovação naquele momento. Não houve
exclusão de testes. No recorte `app`/`migrations`, somente
`test_destination_lock_proof.py` mudou desde a tentativa anterior desta retomada;
produção e migrations permanecem intactas. O snapshot antes da nova execução
contém 735 arquivos, SHA-256
`b4ecde70bc620ab7f2821e603191f6fc3220a9d7f4091bf8989bfa237417843f`.
O CI de 06/11 corresponde à árvore daquela execução. Depois, a [validação
final de 09/11](../../.local/ci-20261108/ci-final-result.json) concluiu `make ci`
com exit 0, 5.043 aprovações e dois skips iniciais. Os mesmos dois testes reais
de MP4 passaram separadamente em 4,97 s após corrigir só o PATH privado;
cobertura app 100% de linhas/branches, laboratório e snapshots conferidos.
Os resultados detalhados e limites do PostgreSQL descartável estão no
[resultado Giz](ensaio-refinamento-motion-giz-2026-11-09.md).

O [QA do relatório original](../../.local/evals/motion-declarative-review-runs/3a52c376-e8ea-4bea-b997-94ba59c628de/report-qa/qa.json)
passou em 390/1440 px, nos modos cego e identificado: dois players 720×1280,
11,2 s; oito reproduções completas mutadas; sete links; zero overflow, erro
JavaScript ou rede externa. Os hashes dos vídeos foram preservados. O registro
conserva 14 PNGs e cancelamentos locais de seek, sem erro de mídia. Reprodução
mutada comprova funcionamento técnico, não escuta ou avaliação perceptiva.

## Correção de apresentação das limitações — sem nova API

O gerador do relatório passou a renderizar `limitations[]`, com os textos
escapados para HTML. A apresentação explica `adequate` como ausência de outro
defeito acionável nas evidências observadas e separa encerramento automático
do ciclo de aceite criativo. As críticas e suas classificações originais
foram preservadas; a apresentação não afirma que a rubrica foi corrigida.

Passaram 15 testes do relatório, Ruff e mypy. Somente o HTML do 1c foi
regenerado; vídeos, críticas e `summary.json` não mudaram. O arquivo original
está preservado como
[report-before-limitations.html](../../.local/evals/motion-declarative-review-runs/3a52c376-e8ea-4bea-b997-94ba59c628de/report-before-limitations.html),
com hash `8a93ab0561adf4300df3e559ee3f0a3c6bb230dc10dcc41877e7f06be473bc4e`.
O [relatório atual](../../.local/evals/motion-declarative-review-runs/3a52c376-e8ea-4bea-b997-94ba59c628de/report.html)
tem SHA-256 `d532a425c861e3ffc0766116c7ceb96020e2628739e08689bd2ce439bf3b91ce`.
Código, testes e manifesto da revisão estão conservados no diretório privado
`report-revisions/2026-11-08-limitations`. O snapshot `qualified-code` mantém o
código original usado no ensaio.

O [QA dirigido desta apresentação](../../.local/evals/motion-declarative-review-runs/3a52c376-e8ea-4bea-b997-94ba59c628de/report-qa-limitations/qa.json)
passou em 390/1440 px nos modos cego/identificado. Limitações e explicação de
`adequate` aparecem somente no modo identificado. Os dois players carregaram
metadados de 11,2 s; sete links foram conferidos, sem overflow, erro JavaScript
ou rede externa. Ledger, manifesto, summary e MP4s coincidem com o QA anterior;
as críticas coincidem com o ledger. HTML e QA anteriores continuam preservados.
Não houve API, custo ou alteração de resultado da avaliação. A separação entre
movimento observado e atendimento criativo foi implementada depois no contrato
do Giz; a calibração criativa permanece pendente. Não é uma alteração retroativa
das críticas deste ensaio.

## Alcance da prova e próximo gate

O titular respondeu **“Comprovar melhora do motion primeiro (recomendado)”**.
A próxima prova criativa deverá preceder a integração. O candidato preparado
para análise é Giz, operação `15adf19d-6edb-4073-9857-bd11684e4162` do lote
`e2bbd3aa-e405-4411-9d56-82752537bc73`, anteriormente avaliado abaixo de Intensa.
[Ensaio histórico de diversidade](ensaio-motion-diversidade-2026-11-06.md).

A auditoria não encontrou violação inequívoca do briefing original: existem
motion e desenho, e as mudanças de tema/janela contínua vieram no feedback
posterior. A nova prova será de refinamento guiado por feedback e contexto
adicional declarado, não descoberta de erro do pedido inicial. Isso deve ficar
explícito na comparação e limita a atribuição da melhoria ao ciclo de revisão.
O [plano do Giz](plano-refinamento-motion-giz-2026-11-08.md) e pacote de 70
arquivos estão concluídos, separando contexto original, feedback e referências
novas. O percurso proposto usa até duas chamadas: refinamento pelo feedback já
conhecido e avaliação comparativa; dispensa crítica paga inicial redundante.
Protótipo/contrato estão implementados para confrontar três requisitos e
separar movimento observado de atendimento criativo. O replay real passou,
com quadros/áudio preservados e código qualificado arquivado. Isso ainda não
comprova ganho criativo. HTML livre não garante fatos/textos por schema; B
passou depois nas inspeções locais e na prova própria de preservação de áudio.
Plano financeiro de até duas chamadas/US$ 1,25 autorizado em 09/11, com registro
vinculado ao plano, qualificação e pedido. O [refinamento Giz](ensaio-refinamento-motion-giz-2026-11-09.md)
concluiu duas chamadas, com inspeções locais e áudio preservado; crítica favorece
v1 nos três requisitos. QA aprovado; o titular respondeu “B ficou melhor.” à
entrevista de motion/narrativa. O feedback posterior foi registrado com hashes,
sem alterar summary, crítica, relatório ou vídeos.
Nenhuma degradação artificial foi criada. O novo resultado não altera custos
ou aceite limitado do 1c nem as avaliações do trio Intensa/Dog/Luma.

Este caso foi selecionado por um defeito conhecido. O esquema atual já corrige
a descrição de unidades que originou o problema; não atribuir ao revisor uma
melhoria anterior do briefing. O resultado demonstra o percurso de detecção,
correção e nova crítica nesse caso histórico. Não mede frequência de erros atuais,
ganho criativo global, retorno financeiro geral da revisão ou qualidade dos
outros formatos. O feedback humano confirmou melhora de legibilidade e
questionou a simplicidade/presença do motion, sem aceite global, rejeição global
explícita ou avaliação de áudio.

A etapa 3 foi concluída no recorte 1c/legibilidade + Giz/refinamento guiado,
com preferência humana por B e validação técnica concluída. Prosseguir à
implementação do Reel (4) e depois aos demais formatos (5), já autorizados,
preservando o nível das referências Intensa/Dog/Luma. As entregas integradas
ainda não estão concluídas. A confirmação tipográfica não aprova a direção 1c,
e a preferência por Giz não aprova isoladamente áudio ou publicação.
Os dois ensaios e seus orçamentos continuam separados; não há ganho universal
ou custo comercial completo demonstrado.
