# Refatoração da criação de motion — plano em etapas

Data: 10/11/2026. Estado: **etapas 1–6 implementadas e validadas localmente; pacote externo entregue**.
Aguardar resultado externo do titular; sem autorização para nova produção integrada.
Este documento consolida a sequência vigente. Não executar os planos pagos
anteriores nem preparar outra geração completa com o contexto antigo.

## Decisão do titular

Corrigir primeiro o fluxo e a entrada efetivamente entregue ao modelo. Depois,
antes de executar a produção integrada, exportar o prompt completo e seus anexos
para teste manual em um modelo escolhido pelo titular (ChatGPT, Grok ou outro).
O resultado será devolvido pelo titular e orientará a próxima decisão. A preparação
não autoriza novas chamadas pagas, render integral, reconstrução Docker, migração
ou execução longa de CI. Usar validação curta e pertinente a cada alteração.

O teste externo avalia criação e acabamento; não comprova por si só equivalência
entre fornecedores ou funcionamento no produto. Ferramentas, contexto, modelos
e anexos do chat externo podem diferir. Registrar essas diferenças.

## Objetivo e limites

Postagem profissional do negócio, com composição e movimento elaborados ao redor
da gravação preservada. Kit, fatos, acervo e voz do negócio continuam como fontes
de identidade/conteúdo. Referências orientam mecanismos e acabamento, não cópia
de paleta, marca, textos ou mídia de terceiros para a peça.

Preservar Python/API, Temporal, RLS, ledger, isolamento do renderer, auditoria,
outbox, identidades de tentativas e versões. Não desenvolver edição longa para
YouTube, importação integral de bibliotecas, outro executor ou novos formatos.
Não prometer qualidade/viralidade antes do resultado observado.

## Etapa 1 — corrigir o contrato real de criação

**Problema comprovado:** a chamada exige HTML/JavaScript, mas inclui fichas antigas
com proibição de HTML executável, áudio ainda indisponível e subset de cut/fade.
A skill também descreve seleção de trechos, enquanto esta integração preserva
a gravação inteira. É necessário distinguir capacidades, política desta prova
e repertório estético.

**Trabalho:** revisar `motion_context.py`, `motion_styles.py`, `motion_skills.py`,
`motion_creative.py` e `motion_ai.py`. Criar versões compatíveis ou uma projeção
explicitamente versionada para o executor HTML. Não modificar snapshots antigos
referenciados por pedidos existentes. Remover contradições da entrada de novos
pedidos, sem retirar preservação de identidade, fatos, áudio e isolamento.

**Entrega/aceite:** payload novo sem instruções conflitantes, com capacidades
claras; regressão curta verifica compatibilidade dos snapshots anteriores e
conteúdo efetivamente serializado. Sem chamada ao provedor.

**Implementação:** novos pedidos usam a skill `instagram-reel-v2`, específica
para HTML, o contrato `html-motion-executor-v1` e a projeção
`html-executor-style-v1` das fichas, que separa repertório estético das
restrições do executor anterior. Fontes e hashes históricos não foram alterados;
a recaptura preserva o formato de pedidos anteriores. Mantidas as regras de kit,
fatos, gravação e voz, e o isolamento existente. Passaram 95 testes direcionados
de contexto, skills, estilos e adaptador; Ruff check/format e `git diff --check`
aprovados, sem CI completo. Sem prova visual nesta etapa.

## Etapa 2 — fazer o repertório chegar à geração

**Problema comprovado:** referência visual de acabamento ausente na chamada;
skills/bibliotecas locais não são consultadas automaticamente pelo modelo.

**Trabalho:** selecionar um conjunto pequeno de instruções, exemplos executáveis
compatíveis e sequências visuais dos materiais já fornecidos. Maestro, Finalizador,
claude-video e Lucas Leite são fontes complementares; não transformar o último
exemplo no único padrão. Seleção deve apontar o mecanismo útil à mensagem, com
origem, licença/permissão, versão/hash e limitações. Distinguir referências de
acabamento dos materiais autorizados a aparecer na peça.

Construir entrada delimitada com quadros e tempos, regras de construção e API das
bibliotecas disponíveis. Aplicar contagem/teto de entrada também a esses anexos.
Nesta fatia, curadoria explícita para a prova basta: não desenvolver um buscador
automático de toda a coleção ou adicionar rede ao código gerado.

**Entrega/aceite:** pacote selecionado realmente aparece no payload; referência
nunca vira asset do cliente por engano; teste local verifica hashes, limites e
associação dos anexos. Nenhuma mídia enviada a provedor nesta implementação.

**Implementação:** `repertoire_id=business-reel-v1` é seleção opcional no pedido
existente, omitida da serialização quando ausente para preservar snapshots.
`motion_repertoire.py` monta texto e metadados fixados por hash. O loader verifica
arquivos locais e runtimes; o orquestrador repassa as imagens separadas para
geração/revisão/correção; o adapter serializa rótulo e bytes no mesmo corpo usado
pela contagem. Nenhum download ou busca automática no caminho de execução.

Curadoria: três funções completas adaptáveis (evidência em camadas de Maestro,
percurso/ação do Finalizador S16 e tipografia em camadas de claude-video); seis
quadros existentes de Felipe Borges e Lucas Leite com tempos aproximados,
sequências e limitações. Fontes, permissões e licenças constam no
[manifesto](../../app/assets/motion_repertoire/business-reel-v1/manifest.json).
Não se incorporou o catálogo inteiro nem se executam as skills originais. Os
runtimes existentes continuam fornecidos pelo renderer; os exemplos são código
que o modelo recebe para adaptar, não novas APIs automaticamente instaladas.

Referências não são assets da peça nem evidência de execução. Os originais
completos continuam locais; a curadoria contém apenas as seis amostras para a
prova privada, sem autorização inferida de reutilização na peça ou redistribuição
como acervo. Kit, voz, gravação e controles permanecem. Nenhuma arte nova foi
gerada: as amostras já existentes foram copiadas sem transformação.

Limites: 64 KiB de texto expandido, até oito imagens, 1 MiB por imagem e 4 MiB
no conjunto, além dos tetos de corpo/tokens/custo existentes. O pacote tem
19.916 bytes de texto JSON e 132.720 bytes de imagens, não uma contagem de tokens.
A etapa 3 registra uma proposta de seleção dos mecanismos para a mensagem, ainda sem aceite criativo.

**Validação:** 163 testes Python direcionados e dois testes Node aprovados;
100% de linhas/ramos do novo módulo na cobertura dirigida; Ruff, tipos dos sete
módulos alterados e `git diff --check` aprovados.
Testes verificam montagem/contagem com transporte falso, hashes, limites,
associação das imagens, compatibilidade histórica e passagem por todas as chamadas.
Os exemplos foram executados com DOM/Canvas substituídos e runtimes reais para
conferir repetição e retorno temporal, sem render de imagens ou vídeo. Sem banco,
API real, CI completo ou alegação de ganho visual. Uso e caminhos no
[README do pacote](../../app/assets/motion_repertoire/README.md).

## Etapa 3 — separar direção visual de construção

**Problema comprovado:** direção, plano e código são resolvidos na mesma resposta;
o briefing anterior já induziu jarra/xícara desenhadas e três composições específicas.

**Trabalho:** tornar explícita a entrada de direção que a construção deverá seguir:
ideia por momento, relação com o conteúdo, foco dominante, camadas/profundidade,
material visual, ação/transformação, relação com a gravação e continuidade.
Reaproveitar `scene_direction` e `motion_plan`; não inventar campos redundantes
ou uma segunda timeline sem necessidade demonstrada.

Na prova externa, a direção pode ser preparada e revisada aqui antes de compor
o prompt, sem reservar outra chamada. O adaptador deve distinguir direção fornecida
de direção sugerida e não anunciar aprovação inexistente. A aprovação de quadros
reais continua separada. Automatização de um planejador em chamada própria,
estado de aprovação anterior ao código e edição independente de cenas são
evoluções posteriores: só após comprovar valor e custo, sem novas tabelas agora.

**Entrega/aceite:** briefing visual verificável e construção orientada por ele,
com liberdade de solução dentro do kit; desenhos, número de cenas ou efeitos
não obrigatórios. Não usar adjetivos como substituto de direção concreta.

**Implementado em 10/11:** `MotionRequest.scene_direction` opcional reutiliza o
schema existente. A captura escolhe v5 para direção fornecida e conserva v4 sem
ela. O payload identifica modo, origem, hash e ausência de aprovação; serviços
validam IDs/recursos e rejeitam mudança da direção antes de imagens/render,
inclusive na correção. Não foi criado planejador automático nem nova timeline.

[Contrato e briefing revisável](direcao-visual-motion-2026-11-10.md) e
[JSON Café Pausa](../evals/direcao-cafe-pausa-2026-11-10.json): dois momentos com
a ideia “abrir espaço para uma pausa”, gravação contínua, planos e tipografia.
Proposta ainda não aprovada criativamente; substitui, na próxima prova, o briefing
que impunha três cenas e objetos desenhados. Não é regra para outros negócios.

**Validação:** 228 testes direcionados aprovados; 100% de linhas/ramos do novo
módulo na cobertura dirigida. Ruff, tipos dos seis módulos de produção e diff
aprovados. Testes cobrem captura/recaptura, modos e contagem do payload, validade
do JSON, fidelidade na geração/correção e interrupção antes dos efeitos externos.
Sem CI global, banco, API real, assets ou render. Fidelidade visual e acabamento
continuam sem prova; o OK para a etapa 4 foi dado na solicitação seguinte.

## Etapa 4 — aplicar construção visual e movimento ao novo contexto

**Trabalho:** traduzir o repertório selecionado em orientações e exemplos úteis:
hierarquia tipográfica, revelações, escala/profundidade, ações entre elementos,
coordenação de entrada/leitura/saída e contraste de velocidade. Manter acervo,
componentes, SVG/Canvas/HTML próprios e ilustrações opcionais.

Primeiro usar as capacidades existentes de `MotionV1` e do renderer. Acrescentar
um componente somente quando uma lacuna concreta impedir a cena escolhida;
não incluir partículas, 3D, tracking, GSAP ou outro motor por hipótese. Não
duplicar curvas ou reescrever renderizador sem necessidade. A gravação permanece
íntegra; enquadramento não deve ocultar a ação/rosto. Transcrição alinhada e som
por evento são posteriores quando exigidos pela direção, não requisito para
explorar composição nesta prova.

**Entrega/aceite:** entrada de construção com exemplos compatíveis e critérios
observáveis, sem impor aparência infantil ou copiar o kit das referências.
Verificação dirigida de contratos; ainda sem afirmar ganho visual renderizado.

**Implementado em 10/11:** nova skill `instagram-reel-v3` selecionada para novos
pedidos HTML. Orientações relacionam hierarquia, máscaras com margem para glifos,
escala/profundidade, ações com resultado, contraste de velocidade, pausas de leitura
e continuidade à direção fornecida. Kit e gravação/voz permanecem; desenhos,
percursos, órbitas, neon ou número de cenas não são obrigatórios.

Dois helpers originais completos, dentro da skill, exemplificam passagem entre
focos com planos reaproveitados e revelação escalonada com tempos finais para o
motion_plan. Usam MotionV1 já disponível; não são funções prefixadas pelo renderer
nem autorização para gerar assets. Não foi encontrada lacuna que exigisse novo
componente ou motor. Os exemplos não são uma implementação da peça Café Pausa.

O montador envia texto e código no campo existente `authorized_context.skill`,
incluído na contagem e nos limites atuais. Recapturas HTML carregam a versão/hash
já registrada; arquivos v1/v2, repertório v1 e runtimes ficam intactos. A skill v3
tem 13.321 bytes UTF-8, não uma medida de tokens/custo. Referências visuais continuam
opcionais e separadas dos materiais do cliente. [Uso e hash da skill](../../app/assets/motion_skills/README.md).

**Validação:** 170 testes Python e quatro Node aprovados; cobertura dirigida dos
dois módulos de produção alterados em 100% de linhas/ramos. Ruff, tipos e diff
aprovados. Testes integram captura, serialização e
contagem com transporte falso, combinando direção fornecida, repertório e skill.
Os exemplos extraídos da própria skill executam no runtime real com DOM substituído,
sem navegador, verificando leitura, transição, tempos de stagger e seeks repetidos,
reversos e diretos. Sem CI global, banco, chamada paga, geração de assets ou render.
Não demonstram acabamento, enquadramento ou legibilidade visual. O OK para a
etapa 5 foi dado na solicitação seguinte; a proposta criativa ainda não tem aceite humano.

## Etapa 5 — alinhar a crítica ao alvo e aos limites de custo

**Problema comprovado:** último parecer truncou em 8.000 tokens. Correção técnica
e integridade não comprovam acabamento; variação de pixels não mede qualidade.

**Trabalho:** fornecer ao crítico o mesmo alvo de acabamento, com evidências
da peça separadas das referências. Distinguir critérios obrigatórios de ganho
criativo. Exigir problema localizado e correção realizável; ausência de evidência
não autoriza refação. Rever redundância e tamanho esperado da resposta/entrada
antes de propor qualquer aumento de limite. Manter limites, parada por falha,
revisão condicional e preservação de versões.

**Entrega/aceite:** contrato de avaliação coerente com a direção, saída incompleta
tratada sem retry automático e sem aprovação fictícia. Testes curtos de montagem
do pedido e falha de resposta. Não executar crítica paga nesta preparação.

**Implementado em 10/11:** `motion-review-v2` capturado em novos pedidos, com
alvos de acabamento compartilhados por geração/crítica/correção. Mantidos checks
existentes, obrigatoriedade de evidência e distinção entre integridade e ganho
criativo. A falha criativa acionável precisa compartilhar quadro atual com o
problema correspondente. Referências de acabamento não entram como prova da peça.

Schema de resposta compacto usa IDs de quadros e limita prosa/problemas. O serviço
recupera versão/tempo/SHA e aplica as validações antes de usar o parecer normalizado
no fluxo existente. Entrada do crítico omite HTML/scene_init das composições por
projeção explícita; direção, plano, kit, skill, referências e evidências permanecem.
Correção recebe código completo. Snapshots históricos mantêm o formato anterior.

**Validação:** 214 testes dirigidos aprovados; 100% de linhas/ramos no serviço de
crítica e schema compacto, Ruff, tipos dos quatro módulos e diff aprovados.
Fixture temporal reduziu a resposta de 17.272 para 4.120 bytes (76,1%), mantendo
parecer equivalente após expansão. Não é medição de tokens/custo nem prova de
qualidade. Detalhes: [contrato e limites da crítica](critica-motion-2026-11-10.md).

Teto permanece em até 8.000 tokens; truncamento/JSON parcial encerram tentativa
sem retry ou correção. Uso e resposta privados preservados, sem aumentar orçamento.
Ainda pode truncar: eficácia criativa e tamanho real dependem de teste futuro
explicitamente autorizado. Sem APIs reais, assets, render, banco ou CI global.
O OK para a etapa 6 foi dado na solicitação seguinte.

## Etapa 6 — exportar a entrada exata para teste externo

Só executar após as etapas anteriores estarem coerentes. Preparar um pedido de
ensaio local sem gravar no banco do produto, despachar Temporal ou consumir APIs.
Usar o mesmo montador de contexto/payload da implementação, evitando escrever
um prompt paralelo mais elaborado e chamá-lo de entrada real do produto.

**Pacote de entrega:**

- Prompt completo legível, com todas as instruções e contextos textuais enviados.
- Corpo JSON completo da chamada proposta, incluindo schema e parâmetros.
- Cada imagem de entrada com rótulo, tempo, origem e hash; fonte original à parte.
- Arquivos de biblioteca/assets necessários à execução, quando declarados.
- Manifesto que distingue o que o modelo recebe do que existe só no renderizador.
- Ordem de uso/anexação, caminhos e links de origem acessíveis; nenhum `.env`,
  token, chave, cookie, credencial ou URL privada assinada.

Adaptar a apresentação ao chat externo sem esconder transformações: um chat pode
não reproduzir papéis, schema estrito, raciocínio ou ferramentas da API. Anexar o
vídeo inteiro onde a API usou quadros é uma variação de entrada, não igualdade.
O modelo deve informar limitações de leitura/render. Código não executado não
será anunciado como MP4. Nenhuma saída externa será executada automaticamente
no produto; passará pelos contratos e isolamento existentes se for incorporada.

**Entrega/aceite:** usuário consegue conferir tudo o que foi preparado; hashes e
testes de serialização demonstram fidelidade ao payload. Parar antes de enviar
ao modelo, gerar assets ou renderizar a peça. Aguardar o resultado externo.

**Implementado e entregue em 10/11:** titular confirmou a proposta Café Pausa.
`capture_motion_guidance` é compartilhado pela captura do produto e pelo exportador;
`build_request` gera o corpo exato. Dados factuais e seis quadros são reutilizados
da chamada registrada, com fonte/fontes verificados por hash, sem nova consulta ao
banco ou geração de mídia. IDs operacionais locais e ilustrações desabilitadas;
orçamento antigo não é reutilizado.

[Entrega e instruções](../evals/pacote-externo-motion-2026-11-10.md): 39 arquivos,
incluindo prompt completo, JSON/schema/parâmetros, 12 imagens, direção/contexto,
repertório/licenças e materiais de execução separados. Manifesto explica projeção
legível, origem histórica e diferenças do chat. ZIP em
`.local/exports/motion-cafe-pausa-20261110.zip`, sem credenciais.

**Validação:** 69 testes dirigidos com dados sintéticos; 100% de linhas/ramos no
montador de contexto em cobertura dirigida, Ruff, tipos e diff aprovados. Igualdade
do payload, associação de anexos, hashes, arquivos de runtime, ZIP, preservação
dos insumos e bloqueio de rede verificados. Pacote real verificado; sem CI global,
SQL, contagem remota, chamada paga, assets gerados ou render. Aguardar teste externo,
sem declarar qualidade visual, execução ou aprovação da saída ainda inexistente.

## Avaliação posterior e pendências

Receber saída integral, modelo escolhido, anexos efetivamente usados, ajustes e
avaliação humana. Comparar acabamento, adequação ao kit, leitura, ação da gravação
e continuidade. Resultado bonito em imagem estática não valida movimento/áudio.

Somente então decidir adaptação adicional, comparação controlada de modelos ou
prova integrada. Qualquer API paga precisa de plano/orçamento específico. Não
reutilizar reservas antigas como autorização. O renderer não foi demonstrado
como limite de qualidade e o modelo não foi comparado sob entradas iguais.

## Validação e documentação

Por etapa: inspeção do diff, testes unitários pertinentes e checks estáticos curtos
nos módulos alterados. Teste SQL apenas se uma mudança o exigir, sempre em banco
dedicado `_test`; não rodar CI longo nesta rodada e não afirmar cobertura global.
Atualizar PROJECT, SDD, BL04 e CHANGELOG com resultado real e pendências.

Na elaboração inicial, o plano foi documentado sem implementação, instalação ou
chamadas pagas. O estado posterior consta no início deste documento. Referências:
[auditoria](../evals/analise-acabamento-motion-2026-11-10.md),
[adaptação do método](adaptacao-fluxo-edicao-2026-11-10.md) e
[resultado da prova anterior](../evals/resultado-video-composicao-2026-11-10.md).
