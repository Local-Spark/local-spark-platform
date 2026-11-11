# Confiabilidade de geração e captura — etapa 1

Data: 10/11/2026. Escopo autorizado: corrigir geração/captura e concluir a comparação.
Sem autorização nova de gasto. Nenhuma chamada de modelo, imagem paga, migração,
serviço ou runner novo. Mudanças anteriores do workspace preservadas.

## Resultado e limites

Concluído MP4 local da resposta completa anterior: 11,2 s, 720×1280, 30 fps,
336 quadros, H.264/AAC. Render integral em 99,35 s pelo executor existente,
com seus limites e sandbox preservados. Hash:
`d574c2b6c6b26de8d68d601f574c9c7b61789e91ec1f58ae3b012fd5fc947dbb`.

Pasta privada: `.local/evals/motion-reliability-20261110/`.
`comparacao.html` compara com as peças anteriores; `comparacao-alternancia.mp4`
é o novo arquivo concluído; `render-result.json`, `technical-inspection.json`
e `frames/` registram a prova. Áudio comparado à fonte, PCM mono 16 kHz sem ajuste
de deslocamento: correlação 0,99998847, razão RMS 0,99963559; áudio 11,176 s.
É comparação de sinal, não escuta ou alinhamento de fala. Foram inspecionados
quadros do trecho de motion, retorno da gravação e encerramento.

A origem é a primeira resposta completa, skill v6, com dois intervalos descritivos
do plano reunidos na rodada anterior. HTML e scene_init permanecem idênticos à
saída completa original. Não se executou/completou a resposta truncada da v7.
Não é geração automática aprovada no produto, nova direção criativa ou crítica
paga. O fundo ativo, a moldura e o objeto realista pedidos posteriormente ainda
precisam de prova visual específica. As duas operações automáticas anteriores
permanecem failed, com suas evidências e reservas intactas.

## Correções no produto

1. **Saída compacta com direção fornecida.** Novas capturas incluem
   `generation_contract=provided-direction-output-v1`. O schema de transporte
   `ProvidedDirectionOutput` pede código, plano, áudio e descrições; não pede
   `scene_direction`. `decode_provided_output` restaura a direção da entrada
   validada antes das validações posteriores, persistência, crítica e render.
   A saída do modelo não pode sobrescrevê-la. O prompt deixa explícitos beats
   ordenados sem sobreposição e um beat composto para partes simultâneas do
   mesmo elemento. Nenhum erro estrutural é aceito silenciosamente.
2. **Compatibilidade e fidelidade.** Sem direção fornecida, mantém-se a proposta
   de direção pelo modelo. Snapshots antigos conservam o schema anterior e seus
   contratos. Recapturas preservam a presença/ausência do novo contrato. A crítica
   continua recebendo a composição com direção integral. O exportador usa o mesmo
   montador e explica como a direção é restaurada, sem credenciais.
3. **Uso/custo em respostas inválidas.** O adaptador valida uso antes de analisar
   a composição. Respostas completas rejeitadas por JSON, plano, áudio ou evidência
   preservam uso, estimativa, request ID e resposta bruta privada. O serviço de
   efeitos já registra esses dados antes de finalizar o ledger. Uso inválido não
   vira custo zero; estimativa não é fatura, e os holds continuam conservadores.
4. **Encerramento do subprocesso.** Quando um leitor excedia o limite ou era
   cancelado, esperar o processo antes de drenar pipes podia bloquear a limpeza.
   Agora o processo é interrompido, os leitores são cancelados e os buffers
   residuais são drenados durante o encerramento. Regressão usa escrita de 4 MB,
   maior que o buffer do pipe, e exige conclusão limitada. Não se ampliou timeout.

A primeira resposta completa continha cerca de 23% de bytes de direção repetida.
A reconstrução offline da composição reparada confirmou direção, HTML e JS
inalterados. `generation-wire-analysis.json` contém a medição exata. Bytes não
são tokens; redução não prova resolução universal do truncamento. Nenhuma geração
paga foi feita com o contrato novo. Essa qualificação continua pendente de uma
rodada explicitamente autorizada, sem aproveitar orçamentos anteriores.

## Diagnóstico da captura

Uma imagem diagnóstica local, derivada da imagem já disponível, mediu nove quadros
com o mesmo HTML/JS, fontes, vídeo e controles. Não foi instalada no produto.
Antes da pausa, o ensaio levou 75,90 s; seek e screenshot somaram 11,87 s.
Cinco serviços tinham mais de 1.300 reinícios cada e consumiam CPU:
worker, billing, relay e auth-mail de `local-spark-platform`, mais relay de
`meu-braco-direito-platform`. O titular autorizou parar somente esses cinco
serviços temporariamente e restaurá-los após a comparação.

Depois da pausa, o ensaio levou 26,38 s; seek e screenshot somaram 2,84 s.
A captura integral seguinte concluiu em 99,35 s, sem segmentação ou mudança do
runner. Essa observação sustenta contribuição da disputa local de recursos;
não prova que todo timeout anterior teve a mesma causa. A restauração dos cinco
serviços foi executada. A causa dos seus reinícios não foi corrigida nesta fatia;
pode voltar a pressionar o ambiente. Não parar serviços automaticamente.

O render final usa a imagem histórica fixada
`sha256:e9884862762529bf49086fb579676a7be15a108a5ac1bb88c7c0f44496a6bf51`,
limite de captura 600 s, contêiner sem rede/credenciais, Chromium sandbox,
seccomp adicional do renderer, memória/CPU limitadas. O conserto de encerramento
está no adaptador Python. Nenhum relaxamento de isolamento ou de crítica.

## Validação e continuação

Testes dirigidos cobrem geração/correção com direção preservada, rejeição de
sobrescrita, contratos históricos, metadados de falha, gravação durável simulada,
limites de evidência, exportação e limpeza real de subprocessos. Sem CI global,
SQL, migração ou uso de banco de cliente. 441 testes passaram em 38,64 s; cobertura 100% de linhas/ramos nos quatro
módulos medidos (dois adaptadores, schema e serviço de geração). Ruff e Mypy
de seis módulos aprovados; exportação, links e JS da comparação verificados.

Pacote novo pelo montador do produto:
`.local/exports/motion-cafe-pausa-confiabilidade-final-20261110.zip`.
Inclui prompt integral, 12 imagens, JSON/schema/contexto, bibliotecas, fonte e
fontes tipográficas; nenhum envio remoto. Para prova externa, seguir README do
pacote. Retorno externo permanece não confiável e deve passar pelas validações.

Próximo passo criativo: titular comparar o MP4 disponível e decidir se precisa
qualificar agora a direção v7 com fundo/moldura/volume. Qualificação nova do
contrato compacto por modelo exige orçamento próprio. Antes do piloto, resolver
os ciclos de reinício do ambiente e comprovar uma geração completa pelo produto;
depois seguir jornada do Reel, fala alinhada e demais formatos no plano de fechamento.
