# Skills editoriais e referências externas — proposta por fases

Atualizado em **29/10/2026**. Este é um plano de implementação, não uma
declaração de capacidade entregue. O proprietário priorizou melhorar a criação
de conteúdo: primeiro skills para os formatos iniciais; depois pesquisa de
referências, incluindo **tanto perfis indicados pelo cliente quanto descoberta
automática de negócios semelhantes em destaque**. A descoberta automática é um
objetivo do produto, não uma extensão opcional da indicação do cliente.

**Direção de 30/10:** na jornada web, permitir ao cliente indicar perfis por
@ e, em outra etapa, apresentar até três candidatos semelhantes encontrados
pelo sistema, com justificativas e aceite ou rejeição pelo cliente. A descoberta
deve partir de fontes disponíveis e autorizadas; avaliar relevância e dados de
engajamento realmente observáveis, sem prometer métricas inacessíveis. Jev é
candidato a classificar/ordenar dados recebidos, não uma pesquisa do Instagram
por si só. Um kit de QA independente foi criado fora do catálogo; é necessário
integrá-lo ao próximo ensaio, pois as peças avaliadas usaram apenas
personalizações do mesmo exemplo de cafeteria.

O kit, contexto e acervo do próprio negócio continuam sendo a base para criar
peças pertinentes e fiéis. A pesquisa externa informa hipóteses criativas; não
fornece fatos do cliente nem autorização para copiar mídia de terceiros. A
[BL04](../phases/BL04-context-and-ai-production.md) mantém avaliação humana de
qualidade e custo por peça aceita; [DECISIONS](../DECISIONS.md) define produto
e resolve divergências. O código e os testes existentes não implementam este
catálogo de skills nem pesquisa automática ampla de concorrentes.

Sequência proposta: skills e prova com provedores simulados → pesquisa de
referências indicadas e descoberta automática → uso de padrões na geração →
avaliação do titular e gate comercial BL04.3 → jornada BL05. A pesquisa pode
começar após a prova simulada das skills; não depende de já ter fechado o gate
comercial com o titular. Validações com fontes reais e chamadas pagas continuam
dependendo de direitos e autorização de gasto próprios.

## Vocabulário e limites

- **Contexto interno:** fatos confirmados e vigentes, preferências, kit e
  materiais autorizados do negócio; dados versionados e isolados por negócio.
- **Skill editorial:** instruções e recursos reutilizáveis para executar uma
  tarefa ou formato; não contém dados privados de um cliente nem concede
  permissões. São diferentes de `BusinessContext`, que contém dados, não código.
- **Referência externa:** perfil, publicação ou padrão observado com fonte,
  data, métricas disponíveis, limites e proveniência. A indicação do cliente
  não prova que os dados estejam acessíveis ou que ele possua direitos sobre eles.
- **Resultado:** roteiro e peça originais, com versões de contexto, skill e
  referências efetivamente usadas; revisão e aprovação da publicação continuam
  explícitas e específicas para a peça, arquivo, legenda, destino e horário.

## Fase S1 — desenhar e avaliar as primeiras skills

Começar por **post de feed e story para Instagram**, formatos da oferta inicial.
Especificar objetivo, quando usar, insumos mínimos, como adaptar tom e kit,
possíveis abordagens, saída estruturada, critérios de qualidade e o que fazer
quando faltam fatos, direitos ou material. As instruções devem promover variedade
e utilidade sem inventar preços, ofertas, produto, local ou promessas.

Recomendação técnica: **um repositório próprio de skills**, com uma pasta por
capacidade e `SKILL.md` compatível com a [especificação Agent Skills](https://agentskills.io/specification),
referências opcionais e exemplos sintéticos. Repositório único facilita revisão,
reuso e evolução; não obriga carregar todas as skills em cada pedido. Visibilidade,
nome, licença, localização e mecanismo de distribuição serão definidos antes de
criá-lo. Avaliar separar uma skill em outro repositório quando houver necessidade
real de distribuição ou manutenção independente. Não criar uma skill para toda
rede/formato antes de haver caso e avaliação.

Cada versão deve ter identificação imutável, escopo, dependências, origem e
critérios de revisão; atualizações passam por revisão e avaliação antes de serem
usadas. Fontes e exemplos externos exigem direitos verificáveis. Conteúdo privado,
credenciais e dados de clientes não entram no repositório ou nas avaliações locais.
Scripts, se necessários no futuro, exigem revisão de segurança, isolamento e
dependências fixadas; uma instrução da skill nunca autoriza execução arbitrária.

Preparar corpus de casos fictícios com nichos, objetivos e cenários completos,
ambíguos ou sem fotos/fatos, incluindo restrições e exemplos positivos/negativos.
Comparar baseline atual e skill na mesma amostra: pertinência ao negócio,
originalidade, clareza, fidelidade ao kit e produto, literalidade factual,
legibilidade, abstenção quando faltam dados, rejeições, refações, latência e custo.
Registrar critérios e limitações; não atribuir melhora a uma skill sem comparação
e sem revisão. A avaliação sintética prepara o gate, mas não comprova qualidade
comercial nem substitui a avaliação do titular.

**Gate:** documentação da skill, casos reproduzíveis e comparação com baseline
revisados; erros factuais críticos bloqueiam avanço. Provedores simulados e dados
fictícios iniciam a validação; chamadas pagas exigem autorização e orçamento
explícitos próprios. Saídas simuladas verificam contrato e segurança, mas não
demonstram ganho criativo de um modelo real: a comparação de qualidade exige
geração efetiva em ensaio autorizado e revisão humana. Não instalar ou executar repositório de terceiros sem avaliar
licença, direitos, segurança e dependências.

## Fase S2 — integrar skills ao percurso do produto

Ao criar um roteiro/peça, o serviço seleciona uma skill aprovada para a tarefa,
rede e formato, fixa sua versão e monta o briefing com o pedido, fatos e kit
versionados e somente o material autorizado pertinente. Definir contrato de
entrada/saída, tratamento de informação ausente e limites de contexto. A skill
orienta a criação e é carregada conforme a capacidade do adapter: instalá-la em
um agente de desenvolvimento não a torna automaticamente disponível numa API.

O contrato exato de armazenamento e distribuição será definido na implementação;
não buscar a versão móvel do GitHub a cada geração. Artefato revisado e versão
fixa devem estar disponíveis para replay/auditoria. Registrar identidade e versão
da skill, contexto/fontes, versão do modelo/configuração, operações, resultado e
custo sem expor material privado ou prompts em logs. Mudança de skill não altera
as prévias e aprovações anteriores. Histórico com versão indisponível deve ter
comportamento definido, sem trocar silenciosamente por uma skill diferente.

Serviços do domínio preservam as regras de autorização, fatos, direitos, plano,
admissão visual, orçamento e aprovação. Instruções de fonte não confiável não
alteram essas regras. Temporal continua coordenando efeitos duráveis; adapters
não substituem regras de negócio, e não há rede sob locks ou IO no workflow
determinístico. Reservar antes de efeito pago, conservar resultado incerto e
reconciliar sem reenvio inseguro.

**Gate técnico:** testes unitários e de integração com provedores simulados, PostgreSQL
`_test` e roles restritas, cobrindo escolha/versão, fontes faltantes, RLS,
replay, alterações durante execução, orçamento e efeito incerto; `make ci` com
100% de linhas e branches sem excluir código produtivo. Comparar post e story
na mesma amostra. O gate comercial não impede iniciar R1/R2. Para BL04.3,
revisar o feed existente e produzir post/story
novos pelo produto com fontes autorizadas e avaliação do titular no celular,
medindo qualidade, rejeições, refações e custo por peça aceita. Simulação não
fecha o gate comercial e autorização histórica de gasto não autoriza nova chamada.

## Fase R1 — base de referências indicadas e curadas

Definir contrato para o cliente indicar perfil ou exemplo e, se desejar, explicar
o que aprecia. A equipe pode curar referências permitidas para estudar o nicho.
Guardar origem da indicação, identificador/URL, data, rede, formato, região quando
conhecida, atributos observados, licença/direitos, métricas disponíveis e suas
limitações. Tratar leitura indisponível, perfil removido e dados insuficientes
como estados explícitos; uma URL indicada não garante acesso ou veracidade.

Extrair padrões abstratos, como uma demonstração próxima do produto, uma pergunta
ou uma sequência de conteúdo; registrar observação separada da fonte. Uma página
pública não autoriza copiar foto, texto, marca, pessoa, voz ou layout identificável.
Resultados de pesquisa são dados não confiáveis, não instruções para o agente nem
fatos confirmados do cliente. Fontes e evidências permanecem privadas quando
apropriado, com acesso por tenant/negócio; não compartilhar dados de um cliente
com outro sem base e autorização adequadas.

**Gate:** casos sintéticos de indicação, fonte inacessível, instrução maliciosa,
ausência de direitos, conflitos e isolamento; revisão humana de pertinência e
distinção entre inspiração abstrata e material publicável. A curadoria prepara,
mas não substitui, a descoberta automática prevista em R2.

## Fase R2 — descobrir e avaliar referências automaticamente

Projetar um fluxo que, com informações disponíveis e confirmadas sobre o negócio,
procure perfis públicos ou outras fontes **permitidas** de negócios semelhantes
e identifique candidatos potencialmente relevantes e em destaque. Critérios de
semelhança podem incluir segmento, produtos/serviços e região quando houver dado
suficiente. Cidade/UF não comprovam endereço ou distância; não inventar raio.
Registrar critérios, fonte, período, evidências, incertezas, quando foi pesquisado
e por que uma sugestão se parece com o negócio. Permitir ao cliente indicar,
aceitar, recusar ou corrigir sugestões; suas indicações e a descoberta automática
coexistem.

Separar **semelhança** de **destaque**. Curtidas, visualizações ou seguidores
isolados podem refletir tamanho da audiência, promoção paga, momento e formato.
Comparações só usam os dados e denominadores realmente disponíveis e períodos
compatíveis; ausência de dados resulta em estado desconhecido, não em ranking
inventado. Alto engajamento não demonstra aumento de vendas. Quando fontes ou
permissões forem insuficientes, comunicar a lacuna e manter as indicações e
curadoria disponíveis, sem fingir que houve descoberta automática.

Antes de adotar um conector, verificar uso comercial, termos, permissões reais,
campos, cobertura, quotas, custo, retenção e direitos dos resultados. Não assumir
acesso a métricas privadas de terceiros, nem contornar restrições da plataforma.
Jev é **candidato a avaliar**, por exemplo para comparar atributos e explicar
similaridade a partir de dados obtidos por meios permitidos; sua capacidade de
descoberta, acesso a fontes, qualidade, custo e adequação ainda não foram
demonstrados. A escolha depende de comparação com alternativas e baseline.

Para pesquisa assíncrona, prever operação durável, tenant, snapshot da consulta,
controle de concorrência, fonte/provedor e versão, orçamento configurado, limites,
tentativas e estados de falha/incerteza. Validar URLs e destinos contra acessos
indevidos; não transmitir contexto de cliente sem necessidade e autorização.
IO ocorre em activities/adapters, fora de locks; logs usam campos permitidos,
sem credenciais, mensagens ou mídia privada. Qualquer nova persistência aplica
RLS, role restrita, auditoria e outbox quando houver efeito assíncrono.

**Gate:** testes locais com fontes e provedores simulados, isolamento de tenant,
similaridade sem dados suficientes, métricas ausentes, origem inacessível,
injeção, custos e concorrência. Validar separadamente com fontes autorizadas e
orçamento aprovado; medir pertinência das sugestões, rejeição do cliente e custo
por pesquisa. Não declarar capacidade comercial antes de comprovar cobertura e
acesso real das fontes escolhidas.

## Fase R3 — usar padrões na geração e avaliar ganho

Acrescentar ao briefing apenas padrões selecionados e sua proveniência, com
escopo, validade e limitações. O kit e fatos do cliente determinam identidade e
afirmações; preferências explícitas podem orientar a direção. As referências não
autorizam reproduzir conteúdo, não se tornam fatos e não substituem a skill ou
os controles de revisão e publicação. Persistir quais versões/padrões influíram
na peça para inspeção e comparação.

Comparar na mesma amostra a geração com skills **sem** e **com** referências;
avaliar relevância, originalidade, aderência ao negócio, qualidade, aceitação,
rejeições, refações e custo total por peça aceita, incluindo pesquisa e tentativas
descartadas. Se a origem estiver incompleta ou indisponível, não inventar padrão
ou prometer melhor desempenho. A avaliação humana e a autorização de publicação
continuam separadas.

**Gate:** simulações e testes de isolamento, procedência e não incorporação de
instruções externas; avaliação controlada pelo titular com fontes autorizadas e
registro de custo/qualidade. Não inferir ganho comercial a partir de uma peça ou
somente de engajamento público.

## Evoluções e decisões ainda abertas

### Ideia para evolução da jornada de referências e kits — 30/10/2026

O proprietário propôs investigar uma jornada em que o cliente indica primeiro
concorrentes ou publicações que admira e depois recebe até três sugestões de
negócios semelhantes, selecionadas pela plataforma. O cliente decidiria quais
referências deseja usar. As indicações e recomendações coexistem; não inferir
aceite de uma recomendação ou afirmar que os candidatos são os três melhores
sem evidências e métricas suficientes. Esta sequência e a quantidade são uma
**ideia para estudo**, não regra de produto fechada ou implementação entregue.

A análise das referências aceitas poderia sugerir opções para o kit, incluindo
fontes, combinações tipográficas, formatos e outros padrões visuais. Uma fonte
semelhante e adequada ao perfil poderia aparecer primeiro e pré-selecionada,
sempre com possibilidade de alteração pelo cliente. A identificação da fonte
em imagem pode ser incerta; apresentar identificação, similaridade e confiança
como hipóteses, sem afirmar que a fonte detectada é exata. Verificar acesso,
disponibilidade e licença de uso antes de disponibilizar uma fonte; oferecer
alternativas quando isso não for possível. Padrões inspiram uma identidade
própria, sem reproduzir a marca, peças ou identidade visual de terceiros.

A pesquisa deve examinar como a sequência afeta a jornada de **Meu negócio**,
seleção e confirmação do kit, visualização das opções, indicação do que foi
inferido e alteração posterior. Manter caminho útil mesmo sem referências,
métricas ou acesso a concorrentes. Definir critérios de relevância, destaque,
escolha do cliente, privacidade, custos, origem e rastreabilidade antes de
implementar. A geração atual não contém essa descoberta ou sugestão de fontes.

Reels, carrosséis e outras redes terão skills e gates próprios depois da validação
dos formatos iniciais e de decisões de oferta/custo; vídeo, avatar e voz mantêm
seus limites e autorizações específicos. O [skill-reel](https://github.com/Felpborges/skill-reel)
é referência de edição de vídeo de pessoa falando, não solução já integrada ou
autorização para reutilizar seu código ou materiais.

Ainda será necessário definir provedor/fontes efetivamente acessíveis, critérios
de semelhança e destaque conforme evidências, cadência de atualização, experiência
de indicação/rejeição, política de retenção de referências, orçamento de pesquisa
e requisitos de operação. Nenhuma dessas escolhas está decidida por este desenho.
Não confundir aceitação das direções pelo proprietário com aprovação de gastos,
direitos, franquias ou publicação.
