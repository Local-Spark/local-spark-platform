# Integração do Reel com composição HTML — 09/11/2026

O titular preferiu B no ensaio Giz ao avaliar movimento/narrativa. Esse aceite
específico permite iniciar a etapa 4; não comprova ganho universal de autocrítica,
custo por peça aceita ou qualidade de todos os formatos. A integração preserva
HTML, `scene_init`, áudio e proveniência; não recompila a composição aprovada no
subconjunto declarativo antigo.

## Qualificação local concluída

[Resultado técnico](../evals/qualificacao-integracao-reel-2026-11-09.md): CI
backend 5.353 testes/100%, web 524/100%, quatro replays Linux e prova do pedido ao
download com API/SQL/Temporal/renderer/storage reais e modelo/crítico simulados.
Os dez workers temporariamente parados foram restaurados. Ativação comercial
e avaliação criativa do gerador integrado continuam pendentes.
A proteção completa de orçamento foi implementada depois desse CI, com
100 testes unitários direcionados (1,62 s), Ruff e mypy aprovados. Não houve
novo CI completo, execução SQL, render ou chamada externa nessa fatia.
Depois, o titular autorizou os pontos 2 e 3. A configuração foi entregue; a
prova paga do ponto 3 foi interrompida na persistência da crítica final.
[Histórico da primeira rodada](../evals/plano-prova-reel-integrada-2026-11-09.md).
A [nova comparação integrada](../evals/plano-comparacao-criativa-integrada-2026-11-09.md#resultado-da-execução-autorizada)
concluiu o caminho real até o download: persistência corrigida, quatro checks
criativos atendidos segundo o modelo, uma versão nova e nenhuma correção.
Duas chamadas/duas contagens, US$ 0,266156 estimados. A/B disponível para avaliação
humana recebida: pequena melhora, ainda abaixo do nível esperado. Qualidade
criativa e ativação comercial não estão aprovadas.

## Direção e critérios criativos — item 2

Novos pedidos incluem `creative_contract` com versão `reel-creative-v2`, capturado
pelo serviço de contexto e protegido pelo mesmo snapshot/fingerprint. O contrato
acompanha geração, crítica e correção. Não é uma chamada separada de planejamento:
o gerador resume a ideia no `concept` e descreve tempos, estados, curvas, relações
e função narrativa em `motion_plan` (`motion-plan-v1`), implementando a intenção
no HTML/JavaScript. O serviço valida duração, estilo e assets antes do render.
Históricos v1/sem plano continuam compatíveis. O plano não é evidência de execução
pelo crítico. Os recursos do executor (`MotionV1`) foram implementados no segundo
passo, com versão/hash no snapshot e prefixo conferido no pacote de cena. A
avaliação temporal (`motion-temporal-v1`) agora seleciona até três eventos e
20 quadros por versão; exige sequências observadas, cobre incerteza e vincula
correções aos problemas demonstrados. A prova real concluiu o fluxo técnico
com A/B disponível; o titular reconheceu melhora parcial, ainda muito longe do
alvo, por falta de componentes visuais associados à mensagem. Sem aceite criativo. A
amostragem cobriu três de 40 eventos, deixando transições principais sem sequência
próxima completa. Ver [resultado medido](../evals/plano-retomada-motion-temporal-2026-11-09.md). Capacidade/manifesto no snapshot e no pacote privado preservam a
leitura histórica; não há chamada paga adicional obrigatória.
Ver [contrato e validação](evolucao-qualidade-motion-referencias-2026-11-09.md#primeiro-passo-entregue--09112026).

Calibrações textuais, derivadas dos registros existentes:

| Referência | Qualidade a orientar | Limite |
| --- | --- | --- |
| Intensa | Tipografia, revelações e janela/fundo organizam a mensagem | Intensidade não é padrão universal |
| Dog | Linguagem de cartaz e contraste adaptados ao negócio | Não copiar kit, textos ou assets |
| Luma | Hierarquia editorial e variação visual próprias da marca | Sobriedade pode ter desenvolvimento visual |
| Giz B | Transformações acompanham pergunta, sensação e convite | Preferência específica, não prova universal de autocrítica |

Fontes: [Intensa](../evals/ensaio-motion-intenso-2026-11-06.md),
[Dog/Luma](../evals/ensaio-motion-outros-negocios-2026-11-06.md),
[Giz B](../evals/ensaio-refinamento-motion-giz-2026-11-09.md).
Nenhum quadro desses vídeos foi acrescentado ao payload; não se promete comparação
visual com uma referência não enviada. Os snapshots imutáveis das skills v1
permanecem intactos; o novo contrato é específico desta integração do Reel.
Preservação da gravação inteira/áudio prevalece sobre sugestões genéricas de cortes.

A resposta da crítica ganha `creative_checks` estruturados, cada qual com nome,
`met|not_met|uncertain`, base no briefing, observação e referências a quadros:

| Verificação | Critério associado | Evidência mínima para met/not_met |
| --- | --- | --- |
| brief_alignment | composition | Um quadro atual |
| narrative_progression | motion | Dois tempos distintos atuais |
| motion_role | motion | Dois tempos distintos atuais |
| visual_development | composition | Dois tempos distintos atuais |

O validador exige os quatro nomes sem duplicação em novos pedidos e confere SHA,
versão e tempo contra os quadros realmente enviados. `adequate` não admite falha
nos sete critérios nem creative_checks diferentes de `met`. Crítica antiga sem
os quatro checks não libera um pedido com o contrato novo; históricos ainda podem
ser lidos com checks vazios. Isso não reabre ou reavalia pedidos anteriores.

`not_met` com `needs_revision` exige também issue major/blocking acionável no
critério correspondente, marcado fail. A correção pode reorganizar a composição
quando a lacuna criativa justificar, preservando fatos, marca, material e áudio.
Dúvida sem evidência gera avaliação insuficiente; não se cria uma refação paga.
Limites de rodadas, reserva, contagem multimodal e preferência comparativa permanecem.
Não são exigidos três cards, troca de paleta, máscaras, número de efeitos ou
intensidade fixa. Uma peça discreta com evolução funcional pode atender. Para
briefing de motion elaborado, zoom/reposição da janela e texto sobreposto por si
sós não demonstram atendimento. Corrigir acentos com a mesma animação melhora
legibilidade; não comprova ganho de motion.

Validação: 98 testes direcionados em 1,50 s, Ruff/mypy. Cobrem rejeição de crítica
apenas técnica, checks ausentes/duplicados, evidências não enviadas ou de uma só
posição temporal, requisitos falhos/incertos, correção criativa fundamentada,
preservação de histórico e aceite estrutural de direção discreta. A fixture fake
identifica explicitamente que suas afirmações são sintéticas. Adicionada regressão
SQL que impede liberar peça com crítica antiga num contrato novo, sem executá-la.

Na implementação do item 2 não houve API, render, migração, implantação ou CI
completo. A prova posterior do item 3 já concluiu o download com IA real e exibe
os quatro checks no A/B. Validação do contrato e julgamento positivo do modelo
não provam qualidade artística: o titular reconheceu pequena melhora, mas
considerou o resultado ainda muito abaixo das referências esperadas.

## Correção da persistência — item 1 após a prova paga

`MotionPayloads` prepara a cifra fora da transação. Pedidos aos modelos e
quadros renderizados até 64 KiB cifrados continuam inline. Acima disso, ficam
no storage privado, cifrados com a chave já configurada e limitados a 64 MiB;
SQL armazena um manifesto também cifrado com chave privada do objeto, tamanho,
SHA dos bytes cifrados e SHA canônico do conteúdo original. O payload enviado
ao modelo e seu hash de admissão permanecem integrais, sem reduzir quadros.

`MotionEffects.persist_payload` cria um efeito `upload` derivado da operação e
do slot (`request`/`evidence`). Claim/auditoria são commitados antes de PUT/GET;
registro e arquivo usam a mesma identidade. PUT é único, com SSE já existente,
e o GET verifica tamanho/hash antes de registrar recebimento. Upload incerto
permanece claimed e o pedido fica incerto, impedindo repetição automática.
Somente depois dessa persistência o claim do modelo e a reserva podem avançar.
Falha em armazenar evidências impede a chamada paga seguinte.

Leitura de evidências deve obter a referência sob RLS e usar
`runner.effects.payloads.open(row, ciphertext)` **fora da transação SQL**.
O leitor aceita registros inline históricos e confere que a chave pertence ao
tenant, negócio, pedido e operação esperados, além de ambos os hashes. Não há
URL pública ou acesso direto pelo cliente. Objetos ficam preservados com a
trilha de auditoria, inclusive após falha; não há limpeza nem retomada automática.

As respostas do modelo continuam inline, limitadas pelo adapter a 4 MiB de
resposta bruta (o envelope cifrado pode ser maior); não contêm o pacote de quadros
de entrada. Sua cifra foi movida para antes da transação. Isso mantém a função
restrita que conserva a resposta após revogação do owner. Composição, diagnóstico
e crítica também são cifrados antes de abrir a transação da versão.

Não há migração nem aumento de timeout. A configuração usa o bucket e as
credenciais privadas existentes. É necessário reconstruir o worker na próxima
execução; não foi alterado o contêiner existente nesta fatia. O pedido falho
anterior não foi reaberto nem aprovado.

Validação: 81 testes direcionados em 1,42 s, Ruff/mypy; erros de storage, hash,
referência de outro tenant, limites, replay, ausência de IO sob locks e bloqueio
antes do provedor cobertos. Duas regressões de integração SQL foram adicionadas
para o CI futuro, sem executar ou migrar banco nesta rodada. Medição offline do
pacote real salvo do caso fictício: **42.205.388 bytes cifrados → referência SQL
de 716 bytes**, roundtrip exato em 1,417 s. Nenhuma API paga ou nova renderização.
[Registro de tamanho](../../.local/motion-persistence-20261109/sizing.json).

Item 1 entregue em código; critérios criativos (item 2) implementados acima.
A prova com IA/download (item 3) foi concluída posteriormente, conforme resultado
no início deste documento; a avaliação humana apontou qualidade ainda insuficiente.

## Ponto 2 — configuração do executor entregue

O [guia do worker](../../docker/motion-worker/README.md) e
[overlay](../../docker-compose.motion.yml) conectam os serviços existentes,
sem outro runner: API admite, relay entrega o outbox e Temporal executa.
O novo target Docker `motion-worker` herda FFmpeg e dependências do
`media-worker`, acrescentando o CLI Docker 28.0.4. Apenas o worker confiável
recebe o socket e a pasta compartilhada, com UID/GID configuráveis e grupo do
socket explícito. O acesso ao socket confere controle do daemon ao worker;
o renderer continua sem socket, rede, credenciais ou acesso a outras tentativas.

`motion_renderer_scratch_directory` é opcional no host e explícito no overlay.
O adapter cria uma pasta privada por tentativa nesse diretório, mantém o bind
somente leitura de `/input` e a limpeza existente. Caminhos relativos, travessia
ou caracteres que alterariam o mount são recusados. Pasta indisponível falha
antes de chamar Docker. O Compose não cria a origem dos mounts automaticamente.

Configuração segue desativada por padrão; nenhum provedor/orçamento/negócio foi
habilitado. `python -m app.entrypoints.motion_executor_check` oferece uma
verificação real pequena, sem banco/IA: 64×64, dois quadros, sem assets/áudio,
timeout de render de 60 s, usando o adapter e a sandbox existentes.

Validação da implementação: **130 testes unitários direcionados em 4,49 s**,
Ruff/formatação e mypy aprovados; Compose resolvido validado com settings reais
em modo desativado e fake sintético, sem ler `.env` de projeto. O primeiro
check ad hoc tratava um campo `false` omitido pelo serializador como obrigatório;
foi corrigido para conferir o default e o YAML fonte, sem mudar o Compose.
[Resultado do Compose](../../.local/motion-executor-config-20261109/compose-check.json).
Não foram executados CI completo, build, subida dos serviços ou render real.
O ponto 2 entrega implementação/configuração; aplicação ao ambiente e prova
operacional do contêiner precedem a API paga no ponto 3, após novo comando.
Não é evidência de homologação em produção ou nova qualificação de arquitetura.

## Recorte e contratos

O fluxo será pedido explícito do owner → snapshot privado → geração → render
isolado → crítica com evidências → correção condicional limitada → melhor versão
→ coleção privada para revisão/download. A aceitação da peça pertence a
`content_pieces`, independente de publicação. Nem pedido motion nem aceite criam
`content_deliveries`, agendamento ou evento de postagem.

- `MotionRequest`: operação, instrução, formato Reel e identidade de uma
  gravação já pertencente ao negócio. A origem é explícita; não se infere vínculo
  pela janela técnica WhatsApp. Catálogo/proposta não são obrigatórios.
- `MotionContext`: snapshot cifrado de kit confirmado, contexto/fatos
  vigentes, referências selecionadas, gravação e skill. IDs, bytes, tipo,
  tamanho e hash são verificados pelo servidor. Fingerprint HMAC revalidado
  antes dos efeitos e do commit; nenhuma rede sob locks.
- `HTMLMotionComposition`: `html`, `scene_init`, `audio`, `concept`, `source_usage`.
  `MotionModelProvider.build_request(request)` prepara o payload exato antes do
  claim; `submit(request,payload)` faz uma tentativa. `request.kind` identifica
  geração, crítica ou correção. Protocols permitem testes sem API.
- `MotionRenderer.render(bundle,operation_id=...)` recebe composição e assets por ID/hash,
  perfil e identidade de operação. Devolve MP4 verificado, quadros identificados,
  métricas e proveniência. HTML só executa em ambiente isolado sem credenciais,
  rede, host filesystem ou privilégios; não importar executor do laboratório.
- `MotionOrchestrator` grava o resultado via função
  `content_pieces.write_version(session, tenant, business, actor, piece_id,
  operation_id, format, artifacts, parent_id=None, source_preview_id=None)`.
  Artefatos têm IDs, ordem, chave privada, SHA, MIME e tamanho; somente conjunto
  concluído, verificado e revisado fica disponível para decisão humana.

A fonte continua sendo a gravação inteira, sem corte ou aceleração nesta fatia.
Se houver áudio, o mux lê a faixa do MP4 original; o WAV mono de 16 kHz destinado
à transcrição não alimenta o vídeo final. O mixer reencoda em AAC e não promete
identidade binária com o original. Ainda não há transcrição/legendas alinhadas ou
seleção automática de música nesta integração. Seis quadros da fonte são enviados
na geração e, separadamente como `source`, na crítica e correção; eles não são
confundidos com a versão anterior. A revisão usa até 64 quadros do MP4 final (20 por padrão), com tempos
e hashes reais, repetindo a mesma amostragem entre versões.

## Persistência e execução

Migration `0113_motion_production`, sucessora de `0112_piece_reviews`, cria
pedidos, snapshots cifrados e operações/versionamento de produção. FKs compostas
tenant/negócio, RLS FORCE, permissões mínimas, operação idempotente e auditoria
transacional. Repetição com mesmo digest reconsulta; digest diferente conflita.
Outbox transporta somente identidades e inicia `MotionProductionWorkflow` na
fila Temporal existente. Workflow não faz IO; activities chamam os serviços.

Cada efeito tem identidade própria, fence, pedido vinculado e resultado
durável. Reservas usam **VisualCostLedger existente**, inclusive teto mensal e
global, sem ledger financeiro concorrente. O claim precede HTTP. Resposta
incerta não autoriza retry ou outra cobrança. Uso estimado é proveniência, não
fatura. Correção só ocorre com problema acionável e orçamento para terminar a
avaliação. A versão mais recente não é automaticamente escolhida.

A reserva operacional não é um teto de faturamento imposto ao provedor.
A guarda agora cobre a entrada e a saída antes da geração:

1. Verifica a tarifa configurada e se a saída máxima já excederia a reserva.
2. Consulta `POST /v1/responses/input_tokens` com o mesmo modelo, instruções,
   schema, reasoning e entrada completa (textos e quadros source/current/previous).
   É uma consulta de contagem, não outra geração. Usa identidade derivada da
   operação durável, timeout de 60 s, resposta limitada a 4 KiB e nenhum retry.
3. Soma entrada contada × tarifa de entrada e saída máxima × tarifa de saída,
   arredondando para cima em milionésimos de dólar. Só permite prosseguir se
   o total couber na reserva. Não corta evidências nem reduz qualidade para caber.
4. Grava contagem, teto e política no pedido cifrado do efeito; a reserva usa
   o `VisualCostLedger` existente e continua sujeita aos tetos por pedido/mês/global.

A contagem acontece sem row locks, antes de claim/reserva da geração. Falha,
resposta inválida ou excesso impedem a geração e não criam reserva financeira.
A identidade deriva do pedido já registrado; não há novo workflow/runner.
As regras anteriores para resultado incerto e proibição de repetição continuam.
A implementação acrescenta uma consulta de contagem por tentativa paga futura;
ela também enviará os mesmos materiais e deve constar do plano do ensaio.
Nenhuma consulta real foi executada nesta entrega.

Política `sol-standard-2026-11-09`, delimitada ao modelo já utilizado nos ensaios,
`gpt-6.1-sol`, em Standard: exige tarifas configuradas de pelo menos US$ 2,50
por milhão na entrada (inclui a tarifa maior de escrita de cache) e US$ 10 na
saída. Não presume desconto de cache. Bloqueia entrada acima de 272.000 tokens,
onde a tarifação muda, e modelos não qualificados. Não escolhe modelo, configura
credenciais ou aumenta orçamento automaticamente. A tarifa configurada deve
cobrir eventuais adicionais específicos da conta; reserva e estimativa não são
fatura. Mudanças de modelo/preço exigem revisão dessa política antes da ativação.

Fontes conferidas em 09/11/2026: [contagem multimodal](https://developers.openai.com/api/docs/guides/token-counting),
[contrato da contagem](https://developers.openai.com/api/reference/resources/responses/subresources/input_tokens/methods/count)
e [tarifas/limites do Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol).

A versão elegível exige `adequate` e quatro critérios obrigatórios aprovados.
Achados menores não obrigam correção; somente `major`/`blocking` acionável e
fundamentado permite outra rodada. Uma correção precisa ser preferida com evidências
de ambas as versões; empate/dúvida conserva a incumbente. Uma segunda correção
exige ganho na primeira e problema relevante restante. Se nenhuma versão passar,
o pedido termina sem expor uma peça como pronta. Os sete critérios preservam a
incerteza de áudio sem escuta e os limites de movimento entre quadros.

Atividades motion participam da mesma exclusão de alterações de kit/contexto,
canal e consentimento das atividades visuais existentes, por guarda comum.
Operação incerta mantém retenção financeira e bloqueio de atividade até
reconciliação. Arquivos completos seguem C04/C09; validade factual, URL
temporária e retenção são conceitos distintos. Upload ambíguo não é sucesso.

## Ativação e validação

A primeira integração é qualificada com fixtures sintéticas, adapters locais
e provedores simulados. Configuração padrão permanece desativada. Aceite antigo
de textos/imagens não é ampliado implicitamente para edição de vídeo: ativação
para clientes reais exige versão própria de contrato, isolamento comprovado,
credenciais e orçamento explícitos. Nenhuma nova API paga faz parte desta
implementação.

O gate atual exige ambiente de desenvolvimento/teste, negócio e IDs de materiais
sintéticos configurados no servidor. Não existe ativação de vídeo para cliente
real por simples reutilização do aceite antigo. O `FixtureMotionProvider` comprova
o encadeamento técnico; sua crítica determinística não é evidência de qualidade
criativa. A API oferece criar, listar e consultar pedidos; o resultado utiliza
a revisão privada existente em `content_pieces`.

Resultados do modelo e payloads são cifrados, e o transporte conserva a resposta
antes de finalizar o registro de custo. Uma função restrita ao worker registra
o resultado com o token da execução original mesmo se o titular perder acesso
durante a chamada. A atividade tem cancelamento local antes do timeout Temporal;
interrupção abrupta do processo pode requerer reconciliação operacional do estado
`running`, sem reenvio automático. Não há rotina paralela de execução/recobrança.

Validar serviços e workflow ponta a ponta com PostgreSQL `_test`, roles
restritas e Temporal local: RLS/IDs cruzados, repetição/conflito, concorrência,
revogação/fonte alterada, falha antes/depois de claim, resultado incerto sem
retry, áudio e fontes preservados, revisão condicional, seleção de versão,
storage privado e ausência de postagem. `make ci` e cobertura exigida continuam
obrigatórios e passaram na fatia local acima. Isso não declara o runner
homologado no ambiente de produção nem autoriza ativação comercial.
