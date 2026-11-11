# Execução até a etapa 7 — roteiro de trabalho

Em 07/11/2026, o titular confirmou que deseja desenvolver até **preparar o
piloto e a operação comercial**, após concluir a frente atual, e solicitou
entrevista. Essa etapa 7 não é a fase 7 de story do [plano audiovisual de dez
fases](plano-v0-imagens-video-motion-2026-11-05.md). O roadmap histórico de oito
passos e o plano audiovisual são antecedentes com numerações próprias.

Em 08/11, o titular recuperou o texto original dos sete processos e confirmou
esta ordem. Este roteiro passa a usar seus nomes e dependências. Autorizou
alinhar documentos, resolver pendências técnicas e concluir a prova da etapa 3
antes de integrar o Reel; depois, implementar a etapa 5. Comparação e julgamento
humano precedem a integração. A autorização anterior para preparar o piloto
permanece, com dúvidas por entrevista e atualizações em cada avanço. Cada
entrega precisa de evidência; planejar não conclui o produto.

## Estado vigente — etapa 3 concluída no recorte provado, 09/11

O titular confirmou a reparação de legibilidade do [1c](../evals/ensaio-revisao-reel-1c-2026-11-08.md)
e respondeu **“B ficou melhor.”** à comparação de motion/narrativa do
[Giz](../evals/ensaio-refinamento-motion-giz-2026-11-09.md). QA e CI foram
concluídos. A etapa 3 está encerrada no recorte demonstrado: uma correção
legível e um refinamento criativo guiado por feedback/referência adicionais.
Não generalizar aprovação de áudio, de todo critério, custo ou qualidade para
outros pedidos. O status automático do run foi preservado; feedback separado
vincula os hashes das duas versões, relatório e summary.

A [qualificação técnica local da etapa 4](../evals/qualificacao-integracao-reel-2026-11-09.md)
foi concluída: pedidos/contexto, efeitos/Temporal, versões e interface, quatro
replays Linux e prova integrada com modelo/crítico simulados. CI backend
5.353/100%, web 524/100%; dez workers restaurados. Não há ativação comercial ou
prova do gerador integrado com API paga. Continuam pendentes
orçamento específico, aplicação ao ambiente e contrato para clientes reais. A proteção de
entrada/imagens foi implementada no ponto 1 em 09/11, com 100 testes unitários
direcionados, sem novo CI ou API real. O ponto 2 foi autorizado e implementado:
overlay API/relay/worker, CLI e scratch compartilhado, 130 testes direcionados
em 4,49 s e Compose validado. Sem build/subida/render real nesta fatia.
Aplicação ao ambiente e checagem sintética precederão a prova paga do ponto 3,
que aguarda novo comando e orçamento específico.

**Outros formatos (5)** foram autorizados anteriormente e ainda não foram
implementados. A sequência vigente conclui primeiro os três pontos do Reel,
um por comando do titular.
O [desenho de imagens](ciclo-revisao-imagens-2026-11-09.md) detalha a inspeção do
JPEG antes da entrega. A [matriz](v0-motion-etapa-0-formatos-e-casos.md) registra
as lacunas de foto/story, story em vídeo e carrossel. Etapas 6/7 continuam no
roteiro de WhatsApp e preparação comercial. Nenhuma nova API paga foi executada.

## Roteiro consolidado

| Etapa | Trabalho e dependências | Evidência de saída |
| --- | --- | --- |
| 1 — Definir o que significa uma peça boa | Versionar critérios de fatos, identidade, legibilidade, movimento, áudio e integridade técnica. | Rubrica e evidências rastreáveis já implementadas no protótipo privado, sem prova de qualidade por si só. |
| 2 — Construir o primeiro ciclo de inspeção e correção | Gerar ou reutilizar composição, renderizar, inspecionar e corrigir somente falha relevante comprovada; preservar versões e custos. | Protótipo e testes offline; preferência automática provisória e resultado incerto sem retry. |
| 3 — Medir se a revisão realmente melhora o resultado | Comparar versões do mesmo caso, com intervenções, custos, tempos e limites explícitos. | Concluída no recorte 1c/legibilidade + Giz/refinamento guiado. Titular prefere B; QA e CI concluídos. Não prova benefício universal, áudio aprovado ou custo comercial completo. |
| 4 — Integrar o Reel ao produto | Fatia local implementada: serviços Python/Temporal, isolamento, versões, auditoria e custos. | Qualificação técnica local concluída com modelo fake, quatro replays e CI 5.353/100%. Ativação comercial, gerador pago, deploy, áudio/legendas completos e recuperação operacional permanecem pendentes. |
| 5 — Aplicar o processo aos demais formatos | Já autorizada após o Reel: imagem feed/story, story em vídeo e carrossel animado, com critérios próprios e revisão por página. | Implementação e qualificação por formato pendentes; preservar coerência, arquivos, limites, custos, voz, música e direitos. |
| 6 — Completar a jornada pelo WhatsApp | Conectar recepção, esclarecimentos, geração, progresso, prévia, ajustes, aprovação da peça e download; distinguir canal simulado do real. | Jornada, isolamento entre negócios, aprovação da versão e recuperação demonstrados; postagem segue posterior. |
| 7 — Preparar o piloto e a operação comercial | Preparar autoatendimento com cobrança: medir custo por peça aceita, definir franquias/limites, validar tempos e completar F07/F08, monitoramento, backup, recuperação e suporte. | Piloto controlado preparado, com qualidade e economia verificadas; participantes ainda não definidos e lançamento não presumido. Instagram automático permanece posterior. |

O plano audiovisual continua detalhando mídia, Reel, story, carrossel e revisão;
suas fases 7–9 não devem ser confundidas com os números deste roteiro. O
[roadmap de 29/10](delivery-roadmap-2026-10-27.md) identifica dependências
F07/F08, mas sua antiga ordem de publicação não substitui a decisão posterior
de geração, revisão e download primeiro. Desenvolver até preparar o piloto não
equivale a cobrar, publicar, fazer deploy ou iniciar operação comercial.

## Decisões já aceitas

- Edição inicial recebe uma gravação do cliente por pedido, até 60 segundos e
  50 MiB; se exceder, solicitar versão menor sem cortar automaticamente. Saída
  de vídeo tem até 60 segundos. Edição não pressupõe acervo.
- O sistema escolhe estilo por pedido, preservando o kit; o cliente não precisa
  escolher imagens do acervo. A escolha musical é contextual, varia entre
  pedidos e pode repetir em séries/campanhas; alternativas e direitos ainda
  precisam ser comprovados. Não inventar fatos, falas, produto ou local.
- A entrega de geração contempla prévia, ajustes, aprovação da peça e download;
  aprovação da peça não autoriza postagem. WhatsApp e Instagram reais exigem
  integração e homologação apropriadas, sem bloquear este ensaio local.
- Python/APIs são o caminho escolhido. Temporal coordena o runtime; atividades
  fazem IO, operações têm identidade durável e custos/auditoria/outbox, banco
  usa RLS e logins restritos. Testes de banco exigem `_test` exclusivo. A fatia
  atual preserva a composição HTML/`scene_init` do caminho aprovado, com execução
  isolada; não a reduz ao compilador declarativo anterior. A qualificação do
  isolamento e do caminho integrado continua necessária.
- R$ 99/mês e teto desejado de R$ 50 de custo por cliente/mês são hipóteses,
  não preço ou franquia final; P05 depende de medição e P03 adia o prazo de
  retenção após encerramento. C04/C09 continuam para conta ativa. Antes de
  ampliar nichos, comprovar uma peça personalizada; a coorte não está definida.

## Entrevista respondida e definições restantes

- **Participantes:** ainda não há negócios reais definidos. Reaproveitar os
  cenários já documentados: cafeteria (referência criativa Intensa), Ponto do Dog
  (loja física de alimentação), Dog em Casa (delivery) e Estúdio da Luma
  (manicure). Os [três cenários de QA](../evals/manual-qa-negocios-ficticios.md)
  e o [caso de cafeteria](v0-motion-etapa-0-formatos-e-casos.md) são fictícios;
  não constituem uma coorte de clientes. A prova atual usa Intensa/Dog/Luma.
- **Modalidade:** autoatendimento com cobrança. Onboarding, contratação,
  geração, revisão/download e tratamento de falhas precisam funcionar sem
  acompanhamento obrigatório; suporte operacional continua necessário.

Preço, franquias e limites finais serão propostos com base no custo completo
por peça aceita. Definir participantes e capacidade antes de iniciar o piloto;
ninguém foi recrutado por essa decisão. As respostas orientam desenvolvimento,
sem ativar por si só cobrança real, publicação ou deploy. A capacidade existente de patrocínio por seis meses não é concedida
automaticamente ao piloto. Fala incerta, direitos de música incidental, tempo
de processamento e retenção de temporários ainda exigem tratamento quando
pertinente. Trabalho independente pode avançar com fixtures e provedores
simulados, sem presumir cliente real ou efeitos pagos. [Plano e pendências](plano-v0-imagens-video-motion-2026-11-05.md#6-verificação-custo-e-decisões-em-aberto).


## Depois dos sete processos — proposta de priorização

O roteiro aprovado termina na preparação do piloto. A sequência abaixo é uma
recomendação a revisar pelos resultados, sem compromisso novo de implementação:

8. Executar o piloto pago controlado, acompanhando cadastro, pagamento, primeiro
   pedido, entrega e suporte com participantes definidos.
9. Medir uso recorrente, aceitação, ajustes, tempos, custo completo por peça,
   margem e cancelamentos; corrigir problemas antes de ampliar a aquisição.
10. Qualificar publicação/agendamento no Instagram, com autorização específica
    por peça, permissões oficiais, reconciliação e recuperação de falhas.
11. Ampliar segmentos, aquisição e capacidade conforme qualidade, retenção e
    margem verificadas. Importação de acervo, proatividade, novos canais e
    avatar/voz sintética permanecem candidatos a priorização própria.

As antigas numerações de F00–F08, BL e do roadmap histórico identificam domínios
ou planos de outra data. Elas não substituem esta ordem nem tornam uma etapa
implementada por existir um documento.

## Histórico da preparação — antes da preferência humana de 09/11

Este bloco preserva os estados anteriores ao feedback “B ficou melhor.”;
as pendências humanas nele descritas não são o estado vigente acima.

O [ensaio de crítica e correção](../evals/ensaio-ciclo-revisao-motion-2026-11-06.md)
preserva a rodada Intensa/Dog/Luma sem versões corrigidas. As três críticas
iniciais usaram contexto incompleto e uma tentativa posterior de Intensa ficou
incerta; essa operação/reserva foi preservada sem retry. O ensaio separado do
1c agora tem original/corrigida, crítica final favorável à v1 e melhora de
legibilidade reconhecida pelo titular, sem aprovação criativa global ou
conclusão da etapa 3.

A continuação independente `4338880a-10f2-48a7-96cd-54138f87dbdd` executou somente
Dog/Luma com contexto criativo v2: ambos `adequate`, sem achados acionáveis ou
correções. Terminou `completed_partial_human_pending`, com Intensa bloqueada.
Foram duas novas chamadas e US$ 0,175165 estimados; acumulado da revisão de seis
tentativas, US$ 0,427215 conhecidos e US$ 1,50 em reservas. Custo da tentativa
incerta segue desconhecido; o teto original de US$ 6,75 não foi esgotado.

Tipagem corrigida e ferramentas locais de mídia recuperadas com hashes
conferidos; 107 testes Python de motion e preflight dos três casos passaram.
O relatório foi corrigido e validado em 390/1440 px nos modos cego/identificado,
sem overflow, erro JavaScript ou rede externa. Após reproduzir o timeout e
ajustar a preparação dos testes de concorrência, o módulo passou em quatro
casos (93,61 s). As falhas posteriores de CI são históricas; a execução final
de 09/11 passou, conforme abaixo.
Produção e migrations permanecem intactas; o CI de 06/11 é da árvore anterior. Críticas válidas que conservam o
original não demonstram capacidade de corrigir um defeito nem ganho criativo.
A etapa 3 permanece aberta: o feedback humano do 1c confirmou legibilidade,
mas questionou a falta de motion e não aprovou a peça globalmente.

Em entrevista, o titular escolheu **testar a correção do Reel antigo com problema
conhecido**. O [plano 1c](../evals/plano-revisao-reel-1c-2026-11-08.md) usa a
montagem histórica de tipografia pequena, preservando 69 arquivos e dez
normalizações anteriores. A ponte declarativa está implementada: 146 testes
locais (57+89), Ruff e mypy estrito passaram. A primeira qualificação local
parou no parsing FFprobe 4.4.8 e foi preservada, sem API. O leitor corrigido
passou no preflight real de mídia já renderizada, incluindo igualdade dos
336 quadros/tempos e 526 pacotes AAC/PCM/tempos após remux. A segunda
qualificação completa passou, recompilando/renderizando a direção e confirmando
essas provas. Registros e hashes foram preservados.

O titular autorizou em entrevista própria até três chamadas/US$ 1,25 e envio à
OpenAI. O registro de autorização vincula decisão, plano, primeiro pedido e
qualificação. A execução do 1c concluiu três chamadas HTTP 200, sem retry ou
incerteza: crítica inicial identificou a falha de legibilidade, v1 foi corrigida
e renderizada, e a crítica final retornou `adequate`, sem achados, preferindo v1.
Áudio preservado tecnicamente, com avaliação perceptiva humana pendente.

O [resultado 1c](../evals/ensaio-revisao-reel-1c-2026-11-08.md) registra
US$ 0,527685 estimados novos, US$ 1,25 reservados e US$ 0,634577 de subtotal de
APIs com o histórico; não é fatura ou COGS. Subtotal medido de 306,489 s exclui
setup/preflight/intervalos. O relatório original passou no QA em 390/1440 px,
modos cego/identificado, sem overflow, erro JavaScript ou rede externa. A
entrevista humana foi respondida: B tem títulos/legendas melhores, mas o titular
questionou o formato e a falta de motion. O original era um Reel com pedido de
cortes, transições, motion e legendas, usando mídia ilustrativa/licenciada e
voz sintética. Pequenos enquadramentos/fades não comprovam acabamento criativo;
o `pass` automático de movimento precisa ser entendido dentro dessa limitação.

A falha de unidades já foi corrigida na geração atual; a prova é específica
de reparação histórica, sem ganho criativo ou retorno financeiro geral.
Intensa/Dog/Luma continuam referências; o 1c não é padrão de produto. A etapa 3
teve confirmação parcial de legibilidade, sem aceite global, de áudio ou motion.
O relatório agora exibe `limitations[]` escapadas e distingue `adequate`/parada
automática de aceite criativo; 15 testes, Ruff e mypy passaram. Somente o HTML
foi regenerado, com original/código preservados; novo QA dirigido aprovado em
390/1440 px nos dois modos, sem overflow, erro JavaScript ou rede externa,
sem API ou custo novo. O próximo contrato deve separar movimento observado de
atendimento criativo; o contrato do Giz está implementado e testado, com
calibração criativa ainda pendente.
O titular respondeu **“Comprovar melhora do motion primeiro (recomendado)”**.
A etapa 3 exige prova criativa antes da integração. O candidato em análise é
Giz (`15adf19d`, lote `e2bbd3aa`), anteriormente avaliado abaixo de Intensa.
A auditoria não encontrou violação inequívoca do briefing original: motion e
desenho existem; pedidos de tema e janela contínua vieram no feedback posterior.
A próxima prova será de refinamento guiado por feedback/contexto adicional
declarado, sem atribuí-lo à descoberta de um erro do pedido inicial. O
[plano do Giz](../evals/plano-refinamento-motion-giz-2026-11-08.md) e o pacote privado
foram concluídos: 70 arquivos (68 inventariados mais manifesto/digest), com
contexto original separado do feedback e das referências novas. O percurso
proposto tem até duas chamadas: refinamento pelo feedback conhecido e avaliação
comparativa; não repete esse feedback em uma crítica paga inicial.

O protótipo privado e o contrato estão implementados: confrontam
`theme_change`, `window_transformation` e `narrative_role`, separando movimento
observado de atendimento criativo. Passaram 160 testes de Giz/contratos/relatório/
legado e 66 declarativos; os caminhos genéricos não podem contornar as guardas
próprias de Giz/1c. `make types` passou a cobrir oito módulos do laboratório.

O replay real do run `1c758136-7530-43d8-96b7-39e4b0e44888` passou: MP4 bruto
byte a byte igual ao original e remux com 336 quadros RGB24/tempos e AAC/PCM/
tempos iguais. Código qualificado preservado em 14 arquivos. A equivalência do
baseline não demonstra ganho criativo. Depois, B passou nas inspeções locais de
código/artefato e preservação de 176 pacotes AAC, tempos e PCM. HTML, dois avisos
MIT, textos, assets e fontes foram conferidos; não houve reparo visual manual.
HTML/JS livre não garante invariância geral de fatos/textos por schema.

O teto de até duas chamadas/US$ 1,25 foi autorizado em **09/11/2026**, com
registro vinculado ao plano, qualificação e pedido. O ensaio Giz concluiu as
duas chamadas HTTP 200, sem retry ou operação incerta, e terminou
`completed_human_pending`. A crítica preferiu v1: três requisitos `met`, seis
critérios `pass`, áudio `uncertain` e nenhum achado. As amostras mostram mudança
verde → creme → verde e janela em arco com estados intermediários, preservando
a linguagem Giz. Isso ainda não é aceite humano de motion ou narrativa.

O [resultado Giz](../evals/ensaio-refinamento-motion-giz-2026-11-09.md) registra
US$ 0,6482575 estimados incrementais e US$ 0,8686550 de subtotal de APIs com o
histórico. Comprometimento US$ 1,0138475, dentro de US$ 1,25; a comparação
excedeu sua reserva em US$ 0,0138475. Subtotal medido de 483,872 s exclui preparo,
qualificação, inspeções e intervalos. Não são fatura, COGS ou custo por peça aceita.
QA do relatório aprovado em 390/1440 px e dois modos, com oito reproduções
mutadas completas, links válidos e 248 arquivos preservados. Comparação aberta
no navegador e entrevista humana enviada com link; resposta/aceite pendentes.
O ganho avaliado é refinamento com feedback e referência posteriores, sem atribuí-lo à
autocrítica do briefing original ou generalizar benefício da revisão.

A [validação técnica de 09/11](../../.local/ci-20261108/ci-final-result.json)
foi concluída: `make ci` terminou com exit 0, 5.043 testes aprovados e dois
inicialmente pulados por FFmpeg/FFprobe ausentes do PATH. Esses mesmos dois
testes reais de MP4 passaram separadamente em 4,97 s após corrigir somente o
PATH privado, sem alterar testes ou produção. Cobertura da aplicação: 100% das
17.229 linhas e dos 4.726 branches. Passaram também 363 testes Python motion,
três Node de áudio, 62 Node do renderer (100% linhas/branches/funções),
Ruff/formatação e mypy de 272 módulos app mais oito scripts.

Os 735 arquivos app/migrations e 29 do laboratório permaneceram iguais aos
snapshots. As 69 amostras de relógio não indicaram repouso, com diferença total
de −0,048 s em 1.114,6 s. As falhas anteriores de recibo/token e seus logs estão
preservados como histórico, sem credenciais; não são o estado da execução final.
O PostgreSQL descartável do CI usou `fsync`, `synchronous_commit` e
`full_page_writes` desligados: esta prova não qualifica perda de energia ou
recuperação do servidor e não altera requisitos de produção. A entrevista
humana da comparação Giz continua pendente; nenhuma integração foi iniciada.
O CI foi concluído; a avaliação humana da prova criativa precede Reel integrado
(4) e demais formatos (5).
