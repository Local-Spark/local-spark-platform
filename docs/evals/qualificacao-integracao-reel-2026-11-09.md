# Qualificação local da integração do Reel — 09/11/2026

A qualificação técnica local passou: quatro replays Linux, suíte web, prova
integrada com modelo/crítico simulados e CI integral backend. Foram 5.353 testes
backend, 100% de 18.570 linhas/5.090 branches, sem skips; web 524 testes/100%.
Esta qualificação anterior não usou API paga; os dez workers foram restaurados.
A [prova paga posterior](plano-prova-reel-integrada-2026-11-09.md) gerou duas
versões, mas falhou ao persistir o pacote da crítica final. Após a correção, a
[nova rodada real](plano-comparacao-criativa-integrada-2026-11-09.md#resultado-da-execução-autorizada)
concluiu geração, crítica, coleção e download verificado por SHA. Duas chamadas e
duas contagens, US$ 0,266156 estimados, sem correção. O titular reconheceu pequena
melhora, ainda muito abaixo das referências esperadas. Qualificação criativa,
ativação comercial e etapa 5 continuam pendentes.

## Executor real

Imagem `sha256:52920e12d4002de757bc67c0324333548f6685c5aea1952e7b192e7c886ff024`.
Mesmo HTML, JavaScript e assets dos arquivos aprovados, conferidos por SHA-256;
somente aliases de IDs de áudio foram normalizados. Sem rede, credenciais ou
filesystem gravável do host no contêiner de render; sandbox Chromium comprovada.

| Caso | Tempo | Quadros comparados | SSIM médio / mínimo |
| --- | ---: | ---: | ---: |
| Intensa | 67,320 s | 336 | 0,9857 / 0,9829 |
| Dog | 75,193 s | 259 | 0,9710 / 0,9610 |
| Luma | 73,281 s | 284 | 0,9820 / 0,9776 |
| Giz B | 107,174 s | 336 | 0,9837 / 0,9779 |

[Comparação com vídeos e quadros](../../.local/motion-linux-qualification-20261109/cases-ba846f182fa8440fbeef6e5a115f03f8/comparison.html),
[resultados do renderer](../../.local/motion-linux-qualification-20261109/cases-ba846f182fa8440fbeef6e5a115f03f8/results.json)
e [comparação de todos os quadros](../../.local/motion-linux-qualification-20261109/cases-ba846f182fa8440fbeef6e5a115f03f8/all-frames-comparison.json).
Geometria, duração e contagem de quadros coincidem. Inspeção de três pares por
caso não mostrou perda evidente de texto, cores ou composição. SSIM mede
semelhança de pixels, não mérito criativo ou áudio; não se promete igualdade
binária entre sistemas/encoders. Os 20 quadros de evidência por vídeo foram
decodificados do MP4 final. Arquivos históricos não foram sobrescritos.

O Intensa anterior excedera 600 s sob disputa de CPU. O titular autorizou parar
temporariamente dez workers Docker identificados; após isso passou em 67,3 s,
sem aumentar prazo ou reduzir qualidade. O
[registro das ações](../../.local/ci-motion-integration-20261109/development-worker-actions.json)
confirma os dez restaurados às 16:06:23 UTC. O
[executor de restauração](../../.local/ci-motion-integration-20261109/automatic-worker-restoration.json)
terminou com exit 0 após o CI. Isso não autoriza
alterar os serviços de desenvolvimento ou corrigir seus loops nesta fatia.

Na [prova sintética adicional](../../.local/motion-linux-qualification-20261109/audio-denial-711b038e3e2541a6a89abba8ea27400a/results.json),
áudio de MP4 manteve 44,1 kHz/estéreo após reencodificação AAC; imagem de host
externo foi rejeitada e o contêiner próprio removido. Não é escuta perceptual.
Passaram também 137 testes Node com 100% de linhas, branches e funções.

## Interface

[Suíte integral](../../.local/web-piece-review/full-coverage-resources-freed.log):
40 arquivos, 524 testes, exit 0, 204,15 s; 100% de instruções (2.060), branches
(2.702), funções (828) e linhas (1.947). Uma worker, timeouts padrão; sem
exclusões de produção. Tipos, build e Prettier passaram. O aviso de bundle maior
que 500 kB não foi tratado como uma nova frente de otimização.

O [QA de interface](../../.local/piece-ui-qa-20261109/result-2026-11-09T14-29-08-411Z/qa.json)
usa API e MP4 sintéticos, em 390/1440 px. A
[regressão textual](../../.local/piece-ui-qa-20261109/text-result-2026-11-09T14-52-30-675Z/qa.json)
confere uma alternativa posterior à versão selecionada. Nenhuma dessas provas
é aprovação humana ou jornada de navegador com backend real.

## Integração completa e pendências

O [storage exclusivo](../../.local/evals/reel-integrated-local-proof-2026-11-09/storage-verification.json)
passou em PUT/GET autenticados, download assinado e 403 para objeto/listagem
anônimos. Docker Desktop não publicou a porta na rede exclusivamente interna;
o recurso de teste ganhou bridge, mantendo publicação somente em 127.0.0.1.
Tentativa inicial preservada; o renderer continua com rede `none`.

Banco novo `mbd_reel_proof_20261109_e2755b324b0d_test`, migrations até 0113 e
roles restritas. A [prova integrada](../../.local/evals/reel-integrated-local-proof-2026-11-09/result.json)
passou em 97,637 s com API/auth via ASGI, SQL/RLS, relay, Temporal, preparo de
mídia, renderer e storage reais; modelo/crítico simulados. Download conferido
por SHA-256 (`ae2de9eb6693182580d23fb174f08faad53396c71436ded4cdb30777ff7e9cb9`),
2.641.725 bytes e 20 quadros finais. Outro tenant e download anônimo retornam
403; RLS não expõe pedidos/peças do negócio alheio. Reentrega do outbox manteve
o mesmo workflow terminal e os quatro efeitos, sem nova geração ou cobrança.
Duas reservas fake concluídas a custo zero; `simulated=true`, sem decisões
humanas ou publicação. Código/fontes permaneceram iguais durante a execução.
O status `completed_human_pending` conserva a ausência de aprovação humana;
a prova confirma encadeamento técnico, não qualidade criativa do modelo fake.

O CI integral usa outro banco exclusivo `_test`. A primeira execução parou em
um teste legado após 4.658 aprovados: a expectativa literal `visual_consent_runs`
não acompanhara a guarda compartilhada `creative_active_runs`. Nenhum arquivo
de código mudou durante aquela execução; relógios divergiram somente 0,007 s.
O teste foi atualizado e acrescentou-se uma prova SQL de que o Reel admitido
bloqueia novo aceite enquanto está em execução, sem gravação parcial. A primeira
versão desse teste usara pedido apenas enfileirado; foi corrigida para verificar
no efeito de geração, sem alterar comportamento de produção. A segunda prova
verifica repetição da decisão antiga depois de nova versão, sem aprová-la nem
duplicar eventos. As duas passaram; cobertura dirigida acumulada dos 18 módulos
novos chegou a 100% de 1.311 linhas/362 branches. Suíte unitária passou nessa
validação, com integrações próprias; não substitui o
[novo CI integral](../../.local/ci-motion-integration-20261109/run-20261109T154537Z/ci.log)
concluído com exit 0: 5.353 testes, 100% de 18.570 linhas/5.090 branches, sem
skips; 363 Python motion, 137 Node renderer, lint/formatação e tipos aprovados.
[Resultado final](../../.local/ci-motion-integration-20261109/run-20261109T154537Z/result.json):
1.235,05 s, 828 arquivos estáveis e diferença de relógios de 0,006 s. A suíte web
já havia passado; não foi repetida sem mudança de código.
O storage exclusivo foi parado, com volume/arquivos preservados. A qualificação
local está concluída; ampliar aos demais formatos em fatias próprias.
A proteção de entrada/imagens foi implementada após esta qualificação,
com 100 testes unitários direcionados; não houve novo CI integral ou prova paga.
A configuração do executor em contêiner também foi implementada depois, com
130 testes direcionados e Compose validado. Build, subida e render real no worker
foram executados nas provas posteriores, culminando no download com IA real da
nova rodada vinculada acima. Contrato para clientes reais e qualidade criativa
suficiente permanecem pendentes. Não houve novo CI integral nessas rodadas.
