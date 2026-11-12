# Recuperação e evolução de peças motion

Data: 11/11/2026. Estado: implementação técnica de R1–R4 entregue; preparação
reproduzível de R5 entregue. Execução/aceite visual de R5 pendentes de CI,
qualificação e nova autorização de gasto; nenhuma peça gerada nesta recuperação.
Evidências, limites e pendências no [relatório R1–R5](../evals/recuperacao-motion-r1-r5-2026-11-11.md).

Este plano organiza a recuperação da etapa 7 do
[contrato de qualidade](contrato-evolucao-qualidade-motion-2026-11-11.md).
Não reinicia as etapas 1–6, não cria uma etapa 8 e não substitui suas capacidades.
Os identificadores R1–R5 distinguem estas fatias de recuperação das etapas já
implementadas. O titular autorizou posteriormente implementar as cinco fatias
em conjunto. Isso dispensa novo OK entre essas implementações, mas não equivale
a autorização de gasto/render.

## Resultado procurado

O produto atual deve produzir uma peça que preserve as qualidades das versões
indicadas pelo titular e demonstre melhora perceptível em sentido/ação, gravação,
espaço/objeto e ritmo/acabamento. Voz e identidade permanecem protegidas.
Recuperar o patamar anterior é um marco intermediário; não basta para declarar
concluída a evolução prevista no contrato.

Uma tentativa pode falhar. O compromisso verificável é não promover a tentativa
inferior a nova referência, não descartar a base e não usar uma falha como motivo
para reiniciar a arquitetura ou desativar os aprendizados implementados.

Referências de resultado, confirmadas pelo titular na conversa:

| Papel | Arquivo existente | Identidade |
| --- | --- | --- |
| Comparação principal: “Nova — quatro melhorias” de 11/11, xícara fotográfica | `.local/evals/motion-staged-retry-20261111/v0.mp4` | SHA-256 `187b611018d2b24c27edb99f07a4a21aecd5599e7333a64ad1b227147df0c451` |
| Referência complementar de ação/alternância: “Anterior” na mesma comparação, xícara desenhada | `.local/evals/motion-reliability-20261110/comparacao-alternancia.mp4` | SHA-256 `d574c2b6c6b26de8d68d601f574c9c7b61789e91ec1f58ae3b012fd5fc947dbb` |
| Evidência negativa, nunca base de qualidade | Storyboard da etapa 7 em `.local/evals/motion-qualidade-etapa7-20261111/` | 18 quadros; reprovado visualmente; sem MP4 novo |

Usar a versão fotográfica como comparador principal controla melhor a diferença
de representação; não mistura arbitrariamente as melhores partes de duas versões
num alvo impossível de reproduzir. A desenhada ajuda a avaliar legibilidade das
ações, sem obrigar a trocar novamente a representação. O aceite na conversa não
deve ser convertido em evento de aprovação do produto que nunca aconteceu.

As recuperações manuais presentes em peças anteriores precisam permanecer
declaradas. A nova execução deve demonstrar resultado pelo fluxo real, sem
alterar HTML/JS por fora e apresentá-lo como geração automática.

## O que já sabemos e não deve ser investigado do zero

O [diagnóstico](../evals/diagnostico-regressao-motion-2026-11-11.md) comprovou:

- Sete elementos de ligação saíram na direção da etapa 1, antes da geração.
- A composição anterior estava no pacote de auditoria, mas ausente dos payloads
  reais de planejamento e implementação.
- Fidelidade à direção e ao plano consolidou a simplificação; o controle de
  correção protege candidatas da mesma rodada, não a base histórica.
- A demora pela xícara já existia na base: 2,56 s antes e 2,52 s agora. A perda
  de ações durante o intervalo e de continuidade no retorno é mais explicativa.
- A skill v13, o kit confirmado, o repertório v2, cinco referências visuais e os
  runtimes chegaram à geração. Isso não comprova aplicação competente.
- Fotos adicionais do acervo não foram selecionadas; referências do negócio
  vieram vazias. Ainda falta determinar se havia dados elegíveis que deveriam
  entrar. Não confundir esse campo com as cinco referências visuais enviadas.
- `motion-sources` continua presente e fornece adaptações/fichas selecionadas;
  o produto não executa automaticamente todo o repositório ou skills externas.

Recibos existentes em `.local/evals/motion-regression-audit-20261111/`:
`audit.json`, `direction-lineage.json`, `causal-checks.json`, `resource-usage.json`,
`verification.json` e `comparacao.html`. Revalidar identidades quando necessário,
sem repetir downloads, pesquisas gerais ou renders já disponíveis.

## Capacidades que permanecem

| Trabalho já implementado | Como continua participando da recuperação |
| --- | --- |
| Direção verificável, skills e repertório | Manter versões históricas e o fluxo atual; corrigir a direção e comprovar seleção/aplicação por função. |
| Revisão representativa e storyboard | Melhorar cobertura dos momentos críticos usando o mecanismo existente; continuar separando composição estática de movimento/áudio. |
| Materiais antes da implementação | Manter resolução, proveniência, hashes e previews antes do código. Reusar material elegível quando possível. |
| Espaço e coreografia | Aplicar preparação, ação, apoio/repouso e passagem a relações concretas da peça; preservar bibliotecas e recursos. |
| Som e proteção da voz | Manter mixer, fades, ducking e medição disponíveis. Nesta comparação, continuar somente com o áudio original escolhido pelo titular. |
| Correção delimitada | Preservar plano/assets/áudio e proteção fora da janela. Acrescentar comparação com a base histórica sem confundir os dois controles. |

Disponibilidade não exige usar tudo em toda peça. Não impor um número de ícones,
efeitos, fontes externas, bordas, cenas ou chamadas a funções de biblioteca.
A seleção deve servir à mensagem e ao kit. Manter capacidades não significa
congelar defeitos de implementação: correções precisam preservar sua finalidade
e compatibilidade e explicar o que mudou.

## Ordem de produção a preservar

Gravação, fala e materiais conhecidos → direção concreta que evolui a base →
plano temporal validado → materiais resolvidos e vistos → implementação →
storyboard comparativo → aprovação do storyboard → render autorizado →
revisão de movimento/áudio → correção delimitada quando cabível → aceite final.

A [análise da referência Maestros](../evals/analise-video-maestros-WuzMxEKJHkQ-2026-11-11.md)
sustenta construção em partes, ações que explicam a fala e revisão localizada.
Ela não disponibiliza o código/log completo do autor nem prova que copiar uma
técnica dará o mesmo acabamento. Não acrescentar bibliotecas, tracking, 3D,
avatar ou música como tentativa de compensar a direção atual.

## R1 — Fixar o caso de comparação e fechar somente as lacunas de entrada

**Objetivo:** saber exatamente o que preservar, quais materiais estão disponíveis
e quais recursos devem chegar à geração. Nenhuma nova peça nesta fatia.

**Trabalho:** aproveitar o diagnóstico e organizar uma matriz por momento
narrativo: função na base, evidência/instante, defeito conhecido, mudança pretendida
e aspecto protegido. Começar por saída da gravação, preparação/revelação da
xícara e retorno com convite. Registrar também abertura e encerramento, para
não concentrar toda a avaliação na cena corrigida.

Fechar as lacunas restantes com leituras delimitadas: referências do negócio
vazias por ausência/inelegibilidade ou por perda na montagem; fotos do acervo
disponíveis versus selecionadas; localização e elegibilidade da xícara original
e da imagem já produzida na etapa 7. Consultas autenticadas somente de leitura,
se necessárias, não exigem iniciar os cinco serviços interrompidos nem recriar
banco. Não copiar dados de cliente para fixtures de testes de fundação.

Criar um inventário com recurso, versão/hash, origem, seleção, destino no payload
e uso esperado. Separar skill do produto, skills externas, acervo do negócio,
kit, referências do negócio, referências visuais e adaptações de motion-sources.
Não presumir que a presença do diretório equivale a uso em runtime.

**Entrega:** matriz de preservação e mudanças; mapa de recursos; manifesto das
bases e materiais; lista curta de lacunas comprovadas. Os arquivos existentes
permanecem intactos. Usar a peça fotográfica como referência não exige executar
seu código antigo ou incorporar automaticamente todos os seus assets.

**Aceite:** bases identificadas, áudio/fonte/kit definidos, funções a preservar
explícitas, ausência de materiais/referências explicada. Nenhum requisito depende
de asset supostamente disponível. Se uma decisão de material alterar a concepção,
levar a questão ao titular em entrevista antes do trabalho dependente.

**Limite da prova:** inventário e análise de quadros não validam uma nova peça.

## R2 — Fazer o contexto completo chegar ao fluxo real

**Depende de:** R1. **Objetivo:** corrigir a omissão da base e qualquer perda de
recursos confirmada, preservando os contratos e snapshots anteriores.

**Trabalho:** vincular uma referência de comparação à operação de evolução,
com identidade, proveniência, hashes de composição/evidências e escopo autorizado.
Reutilizar armazenamento, snapshots e operações existentes. Não aceitar caminho
local arbitrário ou referência a material de outro negócio na API. As bases
históricas locais exigem vínculo explícito e rastreável, sem inventar uma versão
aprovada no banco. Resolver esse vínculo como parte desta fatia antes da execução.

Transmitir a base e os quadros pertinentes pelo montador real até planejamento,
implementação e revisão, distinguindo: fonte do cliente, referência de acabamento,
base histórica e candidata atual. O papel da base é evoluir um resultado; seus
textos/HTML não ganham autoridade sobre o pedido atual. Material de comparação
não se torna automaticamente asset autorizado de render.

`incumbent_composition` já representa candidatas comparadas durante uma rodada.
Não preencher esse campo indiscriminadamente com a base histórica e alterar a
semântica da correção. Preferir um descritor separado no contexto versionado e
uma projeção explícita no adapter; reutilizar estruturas existentes quando isso
preservar a distinção. A fatia deve entregar o contrato concreto e seus testes,
sem adicionar tabela ou serviço por conveniência.

Pontos existentes a revisar: `motion_context.py`, `motion_inputs.py`,
`motion_protocols.py`, `motion_ai.py`, `motion_construction.py` e exportadores.
Rotas continuam delegando regras aos serviços. Referências devem ser selecionadas
por pertinência e limite de contexto; não carregar o repositório inteiro nem
trocar a skill por um prompt manual.

**Verificações:** referência ausente/alterada ou fora do escopo impede admissão;
payload contém identidades e evidências esperadas; exportação e caminho do produto
usam o mesmo montador; snapshots antigos continuam válidos; kit, voz e recursos
selecionados sobrevivem à passagem entre plano e implementação. Usar fixtures
sintéticas para testes, e inspeção local do caso real sem chamada ao provedor.

**Entrega/aceite:** payload real exportado e legível, manifesto verificável e
testes pertinentes. Não basta haver arquivos `baseline/*` no ZIP. Quando houver
execução autorizada, comparar novamente esse contrato com o payload enviado.

**Limite da prova:** entrega correta de contexto não demonstra seu bom uso.

## R3 — Corrigir a direção e impedir perdas declaradas antes da construção

**Depende de:** R1–R2. **Objetivo:** evoluir a composição aceita, mantendo os
aprendizados, sem repetir a reescrita ampla que causou a regressão.

**Trabalho:** preparar uma revisão explícita da direção, usando os campos de
`scene_direction` e beats existentes. Para cada momento, relacionar significado
da fala, protagonista, estado inicial, preparação, ação/acento, resultado/repouso
e passagem. Comparar com a matriz de R1: mantido, modificado com justificativa
ou substituído por uma ação concreta. Retirada sem substituição fica visível.

Primeira hipótese a testar: a passagem gravação → cenário/xícara → gravação
ganha clareza quando os elementos se reorganizam de forma coordenada e deixam
uma continuidade perceptível no retorno. O cenário prepara a revelação; o objeto
encontra apoio; o retorno preserva a relação com o café. A versão anterior já
oferece partes dessa solução. Não redesenhar também abertura, tipografia,
representação do objeto e tratamento sonoro no mesmo experimento.

Especificar estados concretos e consequências observáveis; “mais cinematográfico”
ou “melhor coreografia” não são critérios. A xícara permanecer no encerramento é
uma função deste caso, não uma obrigação universal. Não restaurar sete elementos
mecanicamente para aumentar contagem: preservar suas funções ou justificar uma
substituição que possa ser avaliada.

Implementar verificação das obrigações declaradas antes de autorizar os efeitos
dependentes. Ela deve detectar ausência de vínculo da base, remoção não declarada
de funções/elementos protegidos e plano incompatível com a direção. Não vender
essa verificação como interpretação automática de qualidade. Manter a fidelidade
ao plano depois dessa conferência, em vez de liberar alterações silenciosas.

Se o plano recebido violar o contrato, registrar a falha e parar antes de gerar
imagem/código; não corrigir semanticamente o plano por heurística ou efetuar
nova chamada automática. Usar a identidade e os recibos existentes. Um defeito
criativo não detectável por essas verificações continua sujeito ao storyboard.

**Entrega:** direção revisada, comparação por funções, hipótese e mudanças
delimitadas, exemplos de entrada aceita/rejeitada e testes de omissões conhecidas.
Testar papéis genéricos, sem regra de Café Pausa no código de produção. Validar
também que substituir uma função explicitamente é possível; não congelar o design.

**Aceite:** nenhuma perda silenciosa identificada; direção compreensível e
compatível com materiais disponíveis; alvo visual pronto para revisão do titular
na entrega desta fatia. Ainda não há alegação de melhoria observada.

## R4 — Tornar a comparação condição real de conclusão

**Depende de:** R2–R3. **Objetivo:** conseguir enxergar o resultado da mudança e
impedir que uma candidata inferior ou não avaliada substitua a referência.

**Trabalho:** corrigir seleção temporal para cobrir início, transformação e
conclusão das passagens críticas. As janelas atuais terminam antes de alguns
fades e deixam um intervalo central sem evidência. Usar tempos de beats e estados
relevantes; distribuir o orçamento de quadros por cobertura, evitando sequências
muito próximas que não mostram a ação. Preservar políticas históricas.

Respeitar os limites existentes de evidências; se não couber a cobertura necessária,
declarar o que falta e não afirmar revisão completa. Não ampliar silenciosamente
tokens, imagens ou custo. Levar necessidade de evidência adicional à preparação
de R5. Sequência de PNGs não substitui avaliação de fluidez e som do MP4 posterior.

Usar a rubrica existente com base/candidata identificadas, instantes ou intervalos
correspondentes, justificativa e evidência por dimensão. Alinhar por momento
narrativo; o mesmo segundo não garante a mesma mensagem em versões diferentes.
Registrar separadamente avaliação técnica, parecer do modelo e parecer do titular.

Na seleção/conclusão, exigir resultado comparativo e evidências suficientes.
`adequate` isolado não promove evolução. “Pior” ou “não avaliado” em dimensão
necessária mantém a base; empate pode demonstrar recuperação, não melhoria.
Preservar recibos de candidatas rejeitadas sem convertê-las em nova base.
Não usar a comparação exata de pixels da etapa 6 entre peças redesenhadas:
ela continua valendo somente para regiões protegidas da correção delimitada.

Pontos existentes a revisar: `motion_temporal.py`, `motion_storyboard_frames.py`,
`motion_storyboards.py`, `motion_review.py` e seleção em `motion_orchestrator.py`.
Reutilizar armazenamento de revisões/decisões e auditoria. Não alterar a semântica
histórica de conclusão técnica para afirmar aprovação criativa inexistente.

**Verificações:** fixtures de transição com começo/fim cobertos; omissão indicada
quando o limite impede cobertura; candidata tecnicamente válida mas inferior
não promovida; empate não declarado evolução; base ausente/evidência insuficiente
não passam; correção local continua protegendo seu intervalo; modo histórico
sem pedido de evolução mantém compatibilidade.

**Entrega/aceite:** comportamento de comparação e seleção demonstrado em testes,
galeria comparativa preparada usando artefatos existentes e limites explícitos.
Conferir o caminho que persiste/seleciona, não apenas um helper ou relatório.
Teste com vereditos simulados comprova o bloqueio, não a qualidade artística.

## R5 — Uma execução controlada, somente após nova autorização

**Depende de:** R1–R4 aceitos. **Objetivo:** obter a evidência visual que falta,
mantendo a comparação principal e todos os controles do produto atual.

**Preparação sem gasto:** verificar fonte, kit, voz, transcrição, materiais,
versões, executor e hipótese da rodada. Preferir material existente autorizado;
não gerar outra xícara apenas para repetir a experiência. Se o material original
não puder ser reutilizado, explicitar a diferença e sua consequência no A/B.
Não fingir que um recorte extraído do MP4 é o asset original.

Apresentar proposta nova com quantidades, limites por efeito e teto total.
Planejar uma candidata: uma chamada de plano e uma de implementação; crítica
posterior ao render quando autorizada; no máximo uma correção delimitada e sua
nova crítica, se incluídas. Imagem adicional somente se houver necessidade
demonstrada e autorização específica. Não reaproveitar os US$ 6,75 nem saldos
históricos como consentimento. Contagem remota e qualquer efeito pago também
dependem da autorização aplicável; não presumir preços atuais nesta preparação.

**Execução:** API/outbox/Temporal e armazenamento existentes; uma operação
rastreável, sem editar resposta manualmente ou disparar tentativas extras.
Conferir entradas realmente enviadas e etapas executadas. Parar no storyboard,
apresentar comparação e aguardar aprovação antes do MP4. Reprovação do storyboard
interrompe a rodada; orçamento disponível não é permissão para replanejar.

Após aprovação do storyboard e autorização correspondente, renderizar e avaliar
movimento contínuo, leitura, transições e áudio. Se o problema for localizado na
implementação e a correção estiver autorizada, usar a etapa 6. Se exigir mudar
direção, plano ou material, registrar a causa e retornar somente à fatia afetada;
não reiniciar R1–R4 nem aplicar replanejamento disfarçado de correção.

**Entrega:** base/candidata lado a lado, quadro de resultados com instantes,
entradas verificadas, versões/materiais, intervenções, custos/reservas e limites.
Manter a peça anterior preservada. Uma eventual candidata melhor só se torna
referência após aceite comparativo do titular, registrado sem implicar publicação.

**Aceite e classificação:**

| Resultado observado | Classificação e próximo movimento |
| --- | --- |
| Perda em aspecto protegido ou dimensão necessária | Regressão; rejeitar candidata como referência, localizar causa e revisar somente o trecho/fatia responsável. |
| Evidência insuficiente | Inconclusivo; manter base, explicitar evidência faltante, sem nova execução automática. |
| Equivalência ao patamar anterior | Recuperação do piso; ainda não encerra a meta de evolução. |
| Ganho comprovado na hipótese delimitada, restante sem regressão | Avanço parcial; registrar o que melhorou e o que continua pendente, sem atribuir causalidade isolada a todas as seis etapas. |
| Melhora aceita nas quatro dimensões criativas do contrato, voz/identidade protegidas | Evolução validada neste caso; encerrar a recuperação da etapa 7 com evidência e parecer do titular. |

O resultado de Café Pausa não qualifica automaticamente todos os negócios.
Generalização exige casos posteriores, preservando autorização e orçamento
próprios; não ampliar agora este plano com uma nova campanha de gerações.

## Verificações e restrições para todas as fatias

Inspecionar mudanças existentes e commits posteriores antes de alterar arquivos.
Preservar trabalho do titular, snapshots e artefatos; sem reset, substituição do
índice ou remoção de módulos. Python/API, Temporal, banco/RLS, executor, bibliotecas,
acervo, kits e controles existentes continuam. Nenhum novo serviço/tabela é
necessário por definição deste plano; qualquer necessidade real exige evidência.

Executar testes curtos e pertinentes à mudança. Testes de banco somente em base
dedicada terminada em `_test`, com logins restritos; nunca limpar ou migrar dev
para testar e nunca usar banco temporário vazio como prova do fluxo real.
`make ci` com cobertura integral continua condição de merge conforme AGENTS.md;
checks parciais não equivalem ao CI completo. Não iniciar os cinco serviços
anteriormente interrompidos para satisfazer uma verificação.

Cada entrega deve registrar: mudança concreta, hipótese/defeito tratado, arquivos,
evidências, testes, resultado técnico, situação visual, custos e próximo passo.
Atualizar PROJECT, SDD, BL04 e CHANGELOG na mesma fatia. Perguntas em formato de
entrevista apenas quando faltar uma definição necessária; não pedir novamente
o vídeo, as referências já identificadas ou preferências respondidas.

O plano não garante que toda geração melhore. Ele exige preservação das capacidades,
comparação real e rejeição de regressões, reduzindo a possibilidade de declarar
progresso sem resultado. Esses bloqueios ainda precisam ser implementados em
R2–R4 e comprovados no fluxo; este documento não os apresenta como existentes.
