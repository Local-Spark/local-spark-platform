# Contrato de evolução da qualidade de motion

Data: 11/11/2026. Estado: planejado; nenhuma das etapas abaixo está concluída por
este documento. A autorização desta conversa cobre planejamento. O início do
desenvolvimento e cada comparação seguem as instruções e autorizações do titular.

## Objetivo e evidências de partida

Elevar o acabamento dos Reels de negócios: significado da fala expresso em ações,
gravação integrada, espaço coerente, objeto com presença, ritmo e som articulados.
Preservar voz, conteúdo e identidade do cliente. A entrega deve demonstrar melhora
em comparação visual; mais código, elementos, chamadas ou aprovação automática
não comprovam esse resultado. O aceite criativo final pertence ao titular.

Este é o contrato vigente para a próxima evolução. Consolida, sem apagar seu
histórico, `motion-qualidade-direcao-e-gaps-2026-11-11.md` e a análise em
`../evals/analise-video-maestros-WuzMxEKJHkQ-2026-11-11.md`.

Referência: https://www.youtube.com/watch?v=WuzMxEKJHkQ. Não solicitar o link de
novo. Vídeo, transcrição e quadros já estão em
`.local/research/youtube-WuzMxEKJHkQ-20261111/`; a análise é baseada nesses
materiais, não em acesso ao código original ou aos logs do autor.

Base de comparação: `.local/evals/motion-staged-retry-20261111/v0.mp4`, composição,
entrada, crítica e amostras no mesmo diretório. Relatório:
`../evals/comparacao-construcao-em-etapas-2026-11-11.md`.

Lacunas verificadas: receita obrigatória de moldura, imagem produzida depois do
código, pouca ação do objeto, fundo semelhante a cartelas, áudio sem complementos,
três eventos temporais selecionados de 49 concentrados na mesma fala. Há amostras
globais adicionais; não afirmar que as outras cenas ficaram totalmente invisíveis.

## Regras transversais

- Inspecionar mudanças existentes e estado real antes de cada etapa. Não repetir
  funcionalidades nem substituir alterações do titular. Entregar fatias pequenas.
- Manter Python/API, Temporal, PostgreSQL/RLS, kits, acervo, bibliotecas, executor
  isolado, auditoria, outbox, ledger e identidade durável dos efeitos existentes.
  Nenhum novo serviço, tabela ou runner é requisito inicial deste contrato.
- Usar HTML/JS, MotionV1, Chromium/Playwright e FFmpeg atuais. Remotion,
  HyperFrames, GSAP e Three.js são referências/candidatos, não dependências novas
  obrigatórias. Eventual adoção exige demonstrar limitação, benefício e custo.
- Não copiar identidade dos exemplos. Adaptar mecanismos de composição e movimento
  de Maestro, Finalizador, claude-video, Felipe Borges e Lucas Leite ao kit.
- Preservar a gravação integral e sua ordem temporal nesta rodada; cobrir trechos
  com motion não é cortar o arquivo. Tempos ASR são estimativas, não precisão
  garantida. Não impor um efeito por palavra ou um número fixo de cenas.
- Não executar chamadas pagas, gerar assets ou renderizar nova peça sem autorização
  específica. Orçamentos antigos não se renovam. Preparar entrada e preflight antes
  de pedir o teto; declarar chamadas, imagens, crítica, prévias e correções previstas.
  Falhas e resultados incertos não autorizam tentativas extras.
- Cada etapa termina com alterações, evidências, limitações e pendências informadas
  ao titular. A mensagem de início proposta pede seu OK antes da etapa seguinte.
  Esse OK de implementação não autoriza despesas nem renderização.
- Atualizar PROJECT, SDD, BL04 e CHANGELOG. Executar verificações dirigidas; não
  iniciar maratonas locais/CI. O gate de merge continua o do AGENTS.md, inclusive
  cobertura integral; não declarar esse gate aprovado apenas com testes parciais.
- Usar dev existente para a comparação autorizada; não criar banco vazio para
  simular o produto. Testes destrutivos somente no banco dedicado `_test`, nunca
  em dev. Migração necessária em dev deve preservar dados e ser registrada.
- Manter parados os cinco serviços em falha já interrompidos; não iniciar toda a
  stack. Não expor credenciais, arquivos privados de configuração ou conteúdo
  sensível nos relatórios.

## Etapa 1 — Direção verificável e repertório aplicado

**Entrega:** linha de base preservada, matriz de problemas com instantes e uma
direção revisada para Café Pausa, além do contrato reutilizável para outros kits.
Cada momento relevante descreve intenção, foco, preparação, ação principal,
resultado/repouso e passagem para o próximo. Definir o acento da ação, não apenas
o instante em que o elemento aparece. Reutilizar campos de scene_direction antes
de criar novos; qualquer extensão temporal deve ser versionada e compatível.

Selecionar poucas fichas de referência: trecho, antes/ação/depois, mecanismo
observado e adaptação ao negócio. Anexar evidência visual pelos montadores reais
de contexto; citar uma referência no texto não significa que seus pixels chegaram
ao modelo. Reduzir contradições e receitas cumulativas nas instruções vigentes.

Moldura é opcional, justificada pela cena. Definir uso dominante da gravação,
motion em tela inteira e retorno quando pertinentes. Registrar regiões importantes
da fonte (no café: mãos, jarra e xícara), mesmo que inicialmente revisadas à mão,
sem apresentar essa marcação como detecção automática implementada.

**Pontos de trabalho:** motion_scene_direction, motion_visual_direction,
motion_repertoire, skills vigentes e exportador de entrada.

**Aceite técnico:** entrada exportada pelo produto contém direção sem receita
obrigatória de bordas e referências selecionadas verificáveis; checks pertinentes
de contrato/seleção passam; fonte e kit continuam idênticos à base.
**Aceite criativo posterior:** proposta permite explicar uma transformação ligada
à fala, com começo e consequência, e não apenas listar efeitos. Aprovação textual
da direção não equivale a aprovação dos quadros que ainda serão produzidos.

## Etapa 2 — Cobertura da revisão e prévias representativas

**Entrega:** seleção temporal que distribui evidências entre cenas, ação principal
e transições. Evitar que múltiplos elementos do mesmo cue ocupem todas as vagas.
Incluir antes/durante/depois das passagens; declarar cobertura e omissões.

Reproduzir o caso de três eventos da mesma fala e verificar a nova distribuição.
Sob limites de quadros/tokens, priorizar eventos obrigatórios, deduplicar amostras
e declarar insuficiência quando faltar evidência; não aprovar ação não observada.
Não elevar o teto indiscriminadamente nem enviar todos os quadros ao modelo.

Usar a captura/galeria/decisão de storyboard existente como portão antes do MP4
final na comparação. Hoje ela ocorre após construção do código: não chamá-la de
aprovação de arte anterior à implementação. Examinar cards e sequências curtas de
transição; ampliar a evidência existente apenas onde necessário. Prévia fica
vinculada aos hashes de direção/plano/assets/código; mudança invalida seu aceite.

**Pontos:** motion_temporal, motion_review, motion_storyboards e evidências do render.
**Aceite:** caso Café Pausa cobre as duas transições e a revelação da xícara; casos
curtos/longos não excedem limites silenciosamente. Problemas conhecidos de moldura,
linha sobre a gravação e espaço vazio são apresentados com instante e evidência
para revisão. A crítica não deve receber obrigação de inventar um diagnóstico.

## Etapa 3 — Construção informada pelos assets reais

**Entrega:** plano validado → materiais resolvidos → previews reais → implementação.
Reutilizar a xícara existente na primeira comparação, se adequada e disponível,
preservando hash/proveniência; a mudança avaliada será de direção e execução.

A implementação recebe pixels, dimensões, transparência e restrições úteis do
objeto. Resolver declaração/geração da ilustração antes do código, sem gerar duas
vezes no caminho posterior do orquestrador. Preservar efeitos, recibos, reservas,
reutilização e contratos anteriores. Falha de asset interrompe a etapa dependente,
sem pagar implementação às cegas. O novo montador/exportador reproduz a mesma ordem.

Plano validado continua imutável para a implementação. Se o material inviabilizar
a direção ou exigir outra trajetória, produzir revisão explícita do plano com novo
hash; não contornar a validação. Nova chamada só com orçamento/escopo autorizado.

**Pontos:** motion_construction, motion_orchestrator, motion_illustrations,
motion_generation, motion_ai e exportador.
**Aceite:** prova com adapters locais mostra o preview correto chegando à construção,
ordem dos efeitos, falha sem chamada dependente, preservação do hash do plano e
ausência de geração duplicada. Um PNG permanece imagem plana, não um objeto 3D.

## Etapa 4 — Espaço, integração e coreografia

**Entrega:** qualificar composição e movimento com camadas atuais: plano de apoio,
direção de luz, sombra de contato, profundidades relativas e enquadramento. Usar
movimento relativo entre camadas quando fizer sentido, com texto legível.

Gravação, fundo, objeto e texto participam da mesma ação. A xícara tem preparação,
revelação, acento e repouso; o fundo prepara/recebe/devolve a atenção. Alternar
intensidade e descanso; calma não obriga movimentos quase imperceptíveis. Não
usar partículas, quique, borda ou zoom como substitutos de intenção.

Valorizar regiões importantes da gravação e escolher janela/máscara/moldura apenas
quando coerente. Neste escopo, máscara gráfica não significa recorte automático
da pessoa. Não simular rotação revelando faces ausentes no PNG. Prints e páginas
podem usar o mesmo mecanismo de camadas em fixtures próprias, sem impor OCR/3D.

**Pontos:** direção, skills, repertório/helpers, movement-v3 e validação do executor,
somente onde faltar capacidade demonstrada. Não reescrever o motor por princípio.
**Aceite:** nos quadros e movimentos autorizados, apoio/luz/escala concordam; a
gravação não perde tratamento no retorno; passagens não deixam linhas/painéis
acidentais. Mesmo instante deve reproduzir o mesmo estado. Evidência visual será
avaliada no portão da etapa 7; testes estruturais não concluem o aceite criativo.

## Etapa 5 — Som com função e voz protegida

**Entrega:** camada original imutável mais complementos explicitamente autorizados.
Rever a igualdade atual do plano inteiro de áudio sem enfraquecer a proteção da
fonte. Planejar efeitos em acentos selecionados e uma trilha compatível, quando
disponível/autorizada; verificar antes sons que já existem na fonte.

Integrar fades/envelopes, ducking da música e medição de picos/loudness no mixer
existente. Não aplicar ducking à voz, duplicar som original ou adotar meta universal
de volume sem contexto. Caso a fonte já misture música e voz, não prometer stems
separados; adaptar complementos ou omiti-los, registrando a limitação.

Acervo licenciado primeiro. Sem asset apropriado, usar fixtures sintéticas apenas
nos testes e informar pendência para a comparação; não baixar/gerar música sem
autorização. ElevenLabs/HeyGen e substituição da voz não são requisitos.

**Pontos:** schemas de áudio, motion_inputs, montadores, controles de assets/custo,
audio.cjs e evidência sonora da revisão.
**Aceite:** testes com sinais conhecidos verificam ducking/fades/sincronia e ausência
de clipping na fixture; fonte conserva identidade, ordem, offsets e integridade
de seu ramo antes da mixagem. A/B e escuta do resultado verificam voz e intenção.
Correlação da mistura inteira não substitui a verificação da faixa original.

## Etapa 6 — Correção delimitada sem regressão

**Entrega:** crítica localizada por cena/intervalo/elemento, com evidência e resultado
esperado. Corrigir a falha mantendo direção aprovada, assets, voz, texto e tempos
fora da região autorizada, incluindo margem de transição explicitamente delimitada.

O código atual é monolítico: pedir 'mude só esta cena' não garante isolamento.
Implementar limites verificáveis sobre plano/elementos e comparação visual externa
ao intervalo. Se necessário, encapsular cenas minimamente no executor existente;
não prometer edição isolada de código arbitrário sem checagem. Render completo
pode continuar necessário; correção localizada não implica render parcial.

Reaproveitar artefatos e efeitos existentes. Cada correção tem identidade, teto e
resultado rastreável; não altera retroativamente versão aceita. Verificar também
vizinhanças de entrada/saída, respeitando o tempo absoluto da fonte. Uma regressão
rejeita a candidata e conserva a anterior. Sem tentativas automáticas ilimitadas.

**Pontos:** motion_orchestrator, contratos de correção/review, artefatos e executor.
**Aceite:** fixture com defeito localizado é corrigida, e tentativa de alterar
região protegida é rejeitada. Plano/voz/asset hashes preservados; imagens fora da
região comparadas no mesmo ambiente determinístico e com critério explícito.

## Etapa 7 — Comparação controlada e aceite de qualidade

**Preparação sem gasto:** conferir conclusão técnica das etapas 1–6 e exportar pelo
montador real contexto, prompts de cada chamada, referências/imagens, bibliotecas,
JSON, schemas/contratos, hashes e instruções sem credenciais. Artefatos que dependem
de uma futura resposta são identificados como pendentes, nunca inventados.

Usar mesma fonte, voz, kit, formato/duração e, quando possível, modelo/configuração
e xícara da base. Declarar qualquer diferença. A comparação mede o conjunto das
mudanças, não isola causalmente cada uma. Manter registro de intervenções manuais;
não entregar um render ajustado por fora como resultado automático do produto.

**Execução autorizada:** apresentar escopo e reserva máxima de plano, implementação,
assets faltantes, críticas, prévias, render e eventual correção. Preferir uma
candidata e no máximo uma correção delimitada, somente se incluída na autorização.
Usar API/Temporal e dev existentes, sem caminho especial Café Pausa no produto.
Apresentar storyboard/trechos críticos para decisão antes do MP4 final. Se o titular
autorizar execução autônoma desta rodada, documentar esse modo; não simular aceite.

**Entrega:** comparação anterior/nova lado a lado, MP4s, quadros e trechos críticos,
versão com/sem complementos sonoros, entrada exata de cada efeito executado,
cobertura de revisão, custo/reservas, limitações e parecer do titular.

Rubrica comparativa, preenchida com evidências e instantes:

| Dimensão | Condição de aceite |
| --- | --- |
| Sentido e ação | A ação principal expressa a fala; preparação, acento e consequência são percebidos. |
| Gravação | Regiões importantes protegidas; entradas/saídas e tratamento visual coerentes. |
| Espaço e objeto | Fundo participa, apoio/luz/escala concordam; não parece colagem de elementos independentes. |
| Ritmo e acabamento | Pausas intencionais, leitura confortável e transições sem artefatos conhecidos. |
| Som | Voz íntegra/inteligível; complementos reforçam ações e não encobrem fala. |
| Identidade | Kit e conteúdo preservados; referências não impõem identidade de terceiros. |

Registrar por dimensão: melhor/igual/pior/não avaliado, justificativa e evidência.
Meta de conclusão: titular percebe melhora nas quatro primeiras dimensões, som
aprovado quando adicionado, nenhuma regressão bloqueante em voz/identidade/leitura.
Sem isso, registrar implementação técnica concluída e qualidade pendente; não
declarar sucesso criativo pelo veredito `adequate`. Novos gastos exigem autorização.

## Evoluções condicionais após esta comparação

| Capacidade | Gatilho para abrir uma fatia própria |
| --- | --- |
| Detecção/recorte de pessoa ou produto | Direção precisa proteger/misturar primeiro plano e fundo; qualificar estabilidade temporal e fallback. |
| Tracking de objeto | Informação precisa acompanhar um objeto real filmado; medir deriva e oclusões. |
| Tracking planar/texto no chão | Texto precisa permanecer preso a uma superfície em perspectiva; não confundir com posição 2D. |
| OCR | Peça demonstra telas/documentos e precisa localizar palavras ou controles. |
| Busca de stock/Pexels | Acervo insuficiente; seleção semântica/visual, origem/licença e harmonia de cor verificadas. Não representar stock como produto real do cliente. |
| 3D/Three.js ou vídeo do objeto | Direção exige novo ângulo/rotação impossível com a foto; qualificar assets, render e orçamento. |
| EDL/edição de brutos longos | Nova feature de seleção e corte, com origem/destino, áudio/vídeo e fala remapeados. ASR atual não entrega EDL. |
| Voz/avatar/geração musical | Demanda explícita distinta, com direitos, configuração e orçamento; não substitui a gravação neste contrato. |

Essas capacidades não são pré-requisitos para encerrar esta melhoria. A decisão
de incorporá-las será sustentada pela peça e pela necessidade do produto.

## Validação deste documento e passagem de contexto

Confrontado com os contratos e fluxo atuais de construção, ilustrações, áudio,
storyboard e revisão; preservadas as lacunas da análise anterior. Nesta entrega:
somente documentação, sem alteração de produção, testes/CI, banco, serviços,
geração, assets ou render. Cada etapa inicia pendente. O próximo chat deve começar
na etapa 1, verificar se houve mudanças posteriores e atualizar o estado aqui.
