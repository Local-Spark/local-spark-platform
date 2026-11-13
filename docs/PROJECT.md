# Meu Braço Direito — contexto vigente

**Piso estrutural v3 (13/11/2026): recusa o plano antes do render se o pedido selecionar `motion-production-quality-v3`.**
Sem esse campo, a geração continua no v2. Não há MP4 novo nem crítica de pixel. Ver `docs/design/motion-piso-estrutural-v3-2026-11-13.md`.

**Estado vigente após o feedback do titular — 13/11/2026: entrega REPROVADA.**
O titular rejeitou o MP4 final desta rodada e apontou repetição visual, perda de
frases e de encenação com café/xícara, e distância das 41 referências. O objetivo
de qualidade não foi alcançado. O parecer automático `adequate` e os avanços
pontuais descritos abaixo não demonstram melhoria artística aceita. A conclusão
técnica do fluxo permanece válida, separada da reprovação visual.

Após interromper a rodada, o titular solicitou os 336 quadros (exportados com
manifesto e ZIP em `.local/evals/motion-quality-20261113/`) e depois pediu estudo
próximo de uma referência, admitindo cópia como exercício. Esse pedido permite
trabalho local; não renova orçamento pago. Uma reconstrução manual deve ser
identificada como estudo e não como prova de melhoria do gerador. A avaliação do
texto externo sobre motion por código confirmou que essa arquitetura já existe
no produto; trocar renderer, por si só, não tem ganho visual demonstrado.

Atualização documental: sem código de produção, render ou chamada paga novos;
`git diff --check` é a validação desta atualização. O CI registrado abaixo é da
implementação anterior. Permanecem a reconstrução comparativa e a demonstração
de qualidade no processo do produto; não há nova peça aprovada.

**Registro da entrega anterior ao feedback (histórico):**

**Motion — entrega local de 13/11/2026.**
Peça revisada completa gerada pelo produto e concluída no fluxo nativo, com
Temporal, checkpoints, render e crítica persistidos. MP4 H.264/AAC, 11,2 s,
720×1280 a 30 fps; decodificação integral independente aprovada. Entrega privada:
`.local/evals/motion-quality-20261113/cafe-pausa-final.mp4`, comparação em
`comparacao.html` e avaliação/custos em `RELATORIO-FINAL.md` no mesmo diretório.
Hash da entrega: `834fefbcabe842b4e254666ccebb8ee1ee76dc1a7df8b74d69f7b2524e2b9992`.

Avaliação visual amostrada do assistente: ganho na presença do preparo, imagem
participando das letras em 3,57–3,70 s e transformação de Pausa em Café Pausa
entre 8,44–9,44 s. CTA maior e estado final mais longo que na primeira candidata
desta rodada. Limites: uma tomada, composição sóbria, integração tipográfica
breve; sem afirmar equivalência geral às 41 referências. Sem escuta perceptiva
do assistente; **aceite visual/sonoro do titular pendente**. Parecer nativo
`adequate` não substitui esse aceite: a primeira candidata também foi considerada
adequada pelo modelo e recebeu revisão de direção pela observação do assistente.

Implementados repertório executável v5, encenação consumida na construção e
inspeção, inventário de materiais reais, amostragem por risco, correção delimitada
e retorno ao plano por crítica nativa ou observação explícita do operador,
vinculada ao MP4/quadros. A mensagem simples é mantida, sem baseline obrigatório
de cliente ou meta de cenas. Plano e código finais foram gerados pelo modelo,
sem edição manual da composição. A revisão ocorreu no serviço do produto;
a rodada demonstra melhoria supervisionada, não garantia autônoma de acabamento.

Continuações explícitas preservam planos/MP4 recebidos e histórico de falhas,
sem replay pago. Orçamento menor do pedido é conservado perante o padrão do
worker; recuperação de admissão só ocorre após recusa sem efeitos. Auditoria,
outbox, RLS, idempotência e execução por Temporal mantidos. Executor local
qualificado com áudio v2/fingerprints; sem migração de dev, publicação, commit,
habilitação global ou alteração em spotlight-api. Cinco serviços restritos parados.

**Validação vigente:** `make ci` passou com 6.351 testes Python e 100%
linhas/branches (22.728 statements, 6.602 branches), lint, tipos, 391 testes de
avaliação e 189 testes Node. Manifesto do código conferido; nenhum gate desse
comando pendente. Seis chamadas pagas: **US$ 1,286597 estimados**, US$ 7,50 em
reservas internas, teto autorizado US$ 12,50; materiais novos pagos US$ 0.
Nenhum efeito pago sem estimativa; fatura não reconciliada.

Pendências: aceite do titular, escuta da mistura e calibração da crítica automática,
que foi permissiva na primeira candidata. Motion global permanece desabilitado.
Decisões, validações e histórico no [registro da execução](design/motion-execucao-melhoria-2026-11-13.md).

**Histórico documental anterior à implementação desta sessão:**

**Leitura das instruções de motion — 13/11/2026.**
A auditoria documental identificou gates históricos, versões, custos e estados
operacionais descritos como “atuais” em registros antigos. Para a próxima rodada,
consultar `docs/design/motion-orientacao-vigente-2026-11-13.md` e o roteiro de 13/11.
Relatos abaixo permanecem históricos no escopo de cada entrega; não renovam
orçamento, não repetem migração e não substituem instruções atuais do titular.
Correção somente documental; capacidades propostas ainda não implementadas.

**Roteiro técnico até uma nova peça completa — 13/11/2026.**
Análise convertida em sete etapas com entregáveis e critérios de avanço:
baseline, mecanismos executados, planejamento/material, ciclo de revisão,
validação/orçamento, geração completa e avaliação do resultado. Roteiro em
`docs/design/motion-roteiro-melhoria-peca-completa-2026-11-13.md`.
Estado: proposto, ainda não implementado. Esta alteração é documental;
nenhuma nova chamada paga, migração, render ou mudança de produção. A próxima
execução deve entregar MP4 pelo processo melhorado, distinguindo prova técnica,
melhora visual e aceite do titular. Orçamento novo exige autorização explícita.

**Prévia reprovada visualmente; 41 referências analisadas — 12/11/2026.**
Titular considera a peça abaixo do mínimo em cenas/conteúdo/transições/impacto;
áudio é avanço pontual, sem aprovação global da mistura. Não é falta de exemplos
nem escolha obrigatória de um estilo. Analisados 16 links e 26 Shorts do canal
PropagandaIA (um em comum): 41 vídeos, 542,586 s, 2.166 amostras em toda a duração,
87 amostras adicionais de quatro passagens e notas individuais/galeria privada.
Sem escuta perceptiva ou auditoria de ferramentas dos autores. Diagnóstico:
conteúdo/material, encenação e inspeção executada são insuficientes na rodada;
fidelidade ao plano e cobertura declarada não garantiram elaboração visual.
Capacidade de imagem disponível no produto estava desabilitada; vídeo gerado/3D
não podem ser presumidos. Parte importante das referências é motion por código.
Mudança proposta: material/direção factíveis, construção por partes, revisão da
peça completa e aceite calibrado; sem impor 100 quadros ou quantidade de cenas.
Nenhum código de produção, chamada paga, render novo, migração ou serviço
iniciado nesta análise. Estudo e 41 fichas:
`docs/evals/analise-41-referencias-motion-2026-11-12.md`.
Relatos anteriores de avanço técnico não representam aceite visual do titular.

**Prévia audiovisual completa entregue — 12/11/2026.** Titular autorizou gerar
a peça. MP4 local de 11,2 s, 720 × 1280 a 30 fps, H.264/AAC, 336 quadros,
voz + servir conforme plano, sem outra chamada paga. Código exato conferido no
checkpoint/owner/RLS e materiais restaurados pelo serviço existente; execução
Temporal de tentativa única com renderer isolado, sem alterar código de produção.
Quadros decodificados mostram xícara → U de PAUSA, campo móvel e convite; avaliação
de fluidez/integração tipográfica/escuta ainda cabe à reprodução da peça.
Prévia supervisionada privada, sem fabricar aprovação artística, publicação ou
conclusão nativa: checkpoint nativo render autoriza storyboard e produção posterior
exige revisão paga; pedido nativo permanece no checkpoint, sem alterar decisões.
Workflow da prévia COMPLETED, MP4/35 evidências privados em render-preview-v1.
Saída validada/decodificada, -15,3 LUFS e pico amostral -3,6 dBFS; métricas não
substituem escuta. Global disabled/execução false, cinco serviços exited, nenhum
banco migrado; custo pago acumulado estimado continua US$ 0,774901. CI global
mantém os gates anteriores. Resultado e limites:
`docs/evals/previa-motion-completa-2026-11-12.md`.
Registros anteriores de ausência de render descrevem o estado antes desta autorização.

**Código do plano aprovado gerado e revisado — 12/11/2026.** Titular autorizou
avançar para implementação com parada antes do render. Aprovação exata persistida;
uma chamada de código pelo fluxo real, composição recebida e awaiting_render.
Metadados idênticos ao plano, um vídeo contínuo e áudio original + servir previsto.
Sintaxe/bundle sem execução passaram; fórmulas da trajetória em arco evitam a
janela do vídeo em 10.001 amostras por passagem. Sem prévia/escuta ou certificação
artística. Guarda privada inicial confundiu ordem de chaves JSON; falhou antes
de claim/contagem/reserva/submissão. Corrigida e criada continuação interna
explícita, auditada/idempotente, somente sem efeito de código/upload iniciado;
aprovação e falha preservadas. Sem retry pago, endpoint ou migração novos.
1.657 testes motion (dois skipped), casos PostgreSQL de checkpoints e 40 unitários
do orquestrador passaram; checkpoints 100% linhas/branches. Ruff/formato/Mypy e
diff --check aprovados; CI global ainda pendente nos gates anteriores.
Código US$ 0,332548 estimados, reserva US$ 1,25 uncertain mantida; três chamadas
da sequência somam US$ 0,774901 estimados, sem fatura conciliada. Workflow
COMPLETED, pedido running/token liberado, checkpoint de render sem decisão.
Nenhum render/quadro/asset de IA, migração ou serviço iniciado; global disabled,
cinco serviços restritos exited. Escopo, revisão, custos e pendências:
`docs/evals/implementacao-motion-plano-aprovado-2026-11-12.md`.
Registros de awaiting_plan/código não autorizado abaixo são históricos.

**Correção validada em novo plano — 12/11/2026.** Após autorização de uma
chamada substituta até US$ 1,25, encerrada a rodada anterior pelo checkpoint com
feedback e histórico preservados. Correções: piso v2 exige desenvolvimento visual
no pedido simples; entrada separa escuta por fase; guard permite ação dentro do
vídeo-fonte com layout em hold, sem liberar outro vídeo/grafismo parado. Entrada
final v9 (v8 superada antes de envio), ASR novo e fluxo real até awaiting_plan.
Novo plano transforma xícara no U de PAUSA e apoio em campo de leitura; propõe
servir em 1.900–3.680 ms ligado ao vídeo parado e omite contato sem ação observada.
Validadores e compilação de soundtrack em memória passaram; raw e plano iguais.
Pontos anteriores tratados na proposta escrita; metamorfose, proteção da fonte,
leitura e som/mistura ainda exigem execução/prévia/escuta. Sem aprovação artística
ou decisão de implementar. Estimativa desta chamada US$ 0,228198, reserva US$ 1,25
uncertain mantida; duas chamadas somam US$ 0,442353 estimados, sem fatura.
1.657 testes motion (dois skipped), 24 integrações e 100 dirigidos passaram;
qualidade/catálogo com 100% de linhas/branches, lint/formato/Mypy aprovados.
CI global continua pendente. Nenhuma nova migração, código, asset de IA, render
ou serviço iniciado; global disabled e cinco serviços restritos exited. Resultado:
`docs/evals/plano-audiovisual-corrigido-2026-11-12.md`.
Os estados anteriores de entrada v8/espera de orçamento/ausência de plano são históricos.

**Correção da preparação do planejamento — 12/11/2026.** Pedido posterior
mandou encontrar o problema e ajustar. Identificadas lacunas verificáveis:
desenvolvimento visual aparecia em orientações condicionais, mas não como critério
próprio do piso; escuta humana e pendência da mistura não eram sintetizadas por
fase na entrada. Perfil novo motion-production-quality-v2 exige oitavo critério
visual_development no pedido simples e explicita a escolha composicional;
planning_input agrupa disponibilidade/relato humano/hash/revisão futura de som,
sem exigir efeitos ou apagar limitações. Snapshots v1 preservados na recaptura;
plano/checkpoint original intactos, payload anterior reproduzido byte a byte.
Pacote v8 montado com ASR local novo e conferido, sem nova geração paga/admissão/
render. 1.652 testes motion (dois skipped), 23 integrações e 26 dirigidos passaram;
100% linhas/branches em motion_quality, lint/formato e Mypy 334 + oito scripts
aprovados. CI global segue pendente. A correção da entrada não demonstra melhora
artística; novo plano precisa ser gerado/revisado. Chamada anterior consumida;
nova proposta de uma chamada até US$ 1,25 ainda não autorizada. Detalhes:
`docs/design/motion-correcao-planejamento-2026-11-12.md`.
Estados de sete critérios e preparação v7 abaixo descrevem o histórico.

**Plano audiovisual recebido e revisado — 12/11/2026.** Titular autorizou
explicitamente somente a migração 0118 e uma chamada de plano até US$ 1,25.
Backup privado verificado; dev 0117 → 0118, sem tabela nova ou dados removidos.
Admissão/owner/RLS → Temporal/ASR novo → contagem/reserva → plano → checkpoint
real awaiting_plan. Payload exato v7, 15 quadros da fonte/zero de peça anterior;
nenhum código, asset de IA, render ou aprovação automática. Workflow completado;
pedido running com execution_token liberado, aguardando decisão. Retorno/entrada/
raw e custo preservados. Estimativa US$ 0,214155 (39.898 tokens entrada/11.441 saída),
sem fatura; reserva US$ 1,25 uncertain mantida no ledger. Direção propõe três
momentos tipográficos com vídeo contínuo e omite ambos os efeitos. Validadores
passaram; revisão do assistente recomenda desenvolver composição além de títulos/
barras/reposicionamento e melhorar motivo da omissão de servir café; omissão de
contato tem base na fonte. Não é reprovação de vídeo ainda não renderizado nem
exigência de usar som. Plano original/checkpoint não foram alterados ou aprovados.
Configuração paga só no processo já encerrado; global disabled, cinco serviços
restritos exited. CI integral permanece pendente. Resultado, revisão e limites:
`docs/evals/plano-audiovisual-motion-2026-11-12.md`.
Os estados anteriores de espera de autorização/ausência de plano são históricos.

**Plano solicitado, execução preparada — 12/11/2026.** Titular autorizou
somente gerar/revisar plano, até US$ 1,25 da proposta nova; código/render seguem
sem autorização. Corrigida formatação dos 13 arquivos com AST idêntico, sem
alterar lógica. Lint, formato de 905 arquivos e Mypy (334 módulos app + oito
scripts) passaram; 1.646 testes motion (dois skipped) e 23 integrações de motion/
checkpoints passaram. CI integral continua pendente: cobertura Node abaixo de
100%; backend ampliado interrompido após 108 aprovados/sete falhas de geocodificação,
incluindo policy_id ausente no _test. Sem corrigir schema implicitamente.
Execução privada preparada com admissão/RLS, ledger/Temporal e limite de uma
chamada, payload v7 exato, sem aprovação automática ou renderer. Dev confirmado
0117: aplicar 0118 para persistir checkpoint depende da autorização específica
solicitada, conforme restrição original contra migração implícita. Credenciais
presentes/Temporal saudável; backup compatível preparado, ainda não executado.
Sem migração, admissão ou chamada paga nesta rodada; plano ainda não existe.
Registro: `docs/evals/plano-motion-solicitado-2026-11-12.md`.
Os estados anteriores de 13 arquivos pendentes de formato foram superados.

**ASR real e avaliação dos arquivos fechados — 12/11/2026.** ASR local novo
com modelo existente e mesmo serviço/adapter do runtime; 30 palavras, uma abaixo
de 0,6, transcrição/tempos ainda não revisados. Sua escuta confirma voz clara,
sem sons de café audíveis na fonte e ambos os candidatos adequados para planejar;
relatos vinculados aos bytes no builder, sem aprovar eventos/mistura. Loader agora
mede áudio localmente e limita cortes à duração decodificada. Preparação v7 com
15 quadros da fonte, zero de peça anterior, ASR novo e três relatos humanos;
manifesto/entrada conferidos. Proposta de teto novo US$ 2,50 (US$ 1,25 plano +
US$ 1,25 código após aprovação exata), não autorizada/aplicada. 1.646 testes
motion/exportadores (dois skipped), quatro integrações e Ruff/Mypy 334 aprovados;
100% nos módulos de análise/catálogo, CI global bloqueado por 13 arquivos de
formatação preexistente. Dev 0117, sem migração, gasto/render ou admissão; cinco
serviços parados. Detalhes e gates restantes:
`docs/design/motion-asr-avaliacao-sonora-orcamento-2026-11-12.md`.
Os estados v5/v6 e lacunas de ASR/escuta abaixo são históricos; mistura e qualidade
artística continuam pendentes.

**Piso do produto independente de peça anterior — 12/11/2026.** Correção do
titular: última prévia serve à avaliação desta evolução, não ao contexto obrigatório
para criar uma peça nova. Novo percurso acompanhado recebe perfil de qualidade
do produto automaticamente, com cobertura no plano e guardas contra anexar base,
composição ou material recuperado do render anterior. Bibliotecas, kit, fonte e
checkpoints preservados; histórico de revisão continua disponível. Preparação v5
remontada: 15 quadros da fonte, zero da base, sem PNG herdado ou ASR arquivado.
ASR desabilitado agora bloqueia gasto com o plano; v5 é inspeção com lacuna,
sem submissão autorizada. 1.605 testes motion/exportadores (dois skipped), 67
dirigidos e quatro integrações passaram; grupos sobrepostos. Novo módulo de
qualidade com 100% de linhas/branches, Ruff/Mypy 333 aprovados. CI integral ainda
para na formatação preexistente de 14 arquivos. Sem chamada paga, render, migração
ou novo serviço. Qualidade artística e as outras correções continuam pendentes.
Decisão, implementação e próximos passos:
`docs/design/motion-piso-qualidade-independente-2026-11-12.md`.
O pacote v4 citado abaixo foi superado para a geração nova; arquivos preservados.

**Preparação audiovisual pelo produto — 12/11/2026.** Implementado modo de
planejamento que interpreta a mensagem simples e propõe direção/plano antes do
código, sem congelar três cenas ou os 18 elementos. Piso funcional v2 exige
cobertura/justificativa; checkpoints/hash continuam protegendo o plano aprovado.
Biblioteca local com dois candidatos públicos CC0 reais, origem/licença/bytes
verificados e seleção por ação no plano; nenhuma escuta ou geração paga. Repertório
v4 mantém exemplos e retira os oito prints somente da próxima seleção.
Pacote real em `.local/evals/motion-supervised-20261112/preparation-v4/`: 15 quadros
da fonte, 20 da base registrada e um preview. Mensagem simulada preservada; contexto
recuperado com RLS. Sem admissão, plano/código novos ou render. Base registrada é
anterior à última prévia favorável, que continua sem versão/aprovação fictícia.
1.584 testes motion/exportadores passaram (dois skipped); 47 dirigidos finais;
55 integrações e uma prova Temporal repetida com sucesso na instância CI ativa.
100% de linhas/branches nos dois módulos novos, sem afirmar cobertura integral.
Ruff/Mypy aprovados; `make ci` bloqueado por formatação preexistente em 14 arquivos.
Dev permanece 0117 e runtime disabled; `_test` 0118, sem migração reaplicada;
cinco serviços parados. Revisar entrada, definir orçamento novo e autorizar
configuração antes de qualquer chamada; depois plano → aprovação específica →
código → parar antes de render. Entrega, fontes/capacidades e pendências:
`docs/design/motion-planejamento-audiovisual-revisavel-2026-11-12.md`.
Os registros abaixo descrevem etapas anteriores, preservadas como histórico.

**Revisão dos prints de referência — 12/11/2026.** Após ver os anexos, o titular
rejeitou a seleção genérica. Próxima rodada deve retirar os oito prints mostrados,
preservando histórico, evidências da gravação/base, materiais, skills e código.
Cinco foram enviados na última geração; três adicionais só constam no rascunho.
Ganho criativo não foi demonstrado. Critérios de seleção pertinente e distinção
entre fontes consultadas/conteúdo anexado/capacidade integrada registrados em
`docs/evals/ensaio-acompanhado-motion-2026-11-12.md`. Decisão documentada; alteração
da seleção no montador ainda pendente, sem mudança de runtime ou nova geração.

**Ensaio acompanhado, entrada revisada — 12/11/2026.** Montador real conferido
sem envio: 15 quadros da fonte, 20 da base, oito referências e um preview. A
entrevista invalidou o rascunho: cliente fala simples, peça anterior é piso de
qualidade e efeitos devem ser selecionados de biblioteca pública licenciada.
Direção herdada fixa três cenas/18 preservações e ainda restringe SFX. Probes
confirmam que checkpoints exigem direção fornecida; não traduzem sozinhos o
pedido natural. Fontes existentes já documentam ElevenLabs/síntese e mixagem,
mas obtenção/seleção não está integrada. Preparação corrigida e lacunas em
`docs/evals/ensaio-acompanhado-motion-2026-11-12.md`. Sem chamada paga, novo pedido,
download, render ou mudança de produção/banco; cinco serviços continuam parados.

**Preparação/revisão, fases 1–3 — 12/11/2026.** Implementados origem/alcance das
decisões, evidência vinculada aos anexos do builder real e duas pausas opt-in:
depois do plano e depois do código, antes de qualquer render. Inspeção privada
mostra chamada/retorno efetivos; aprovação exata retoma uma vez via Temporal.
Repertório v3 acrescenta amostras existentes de luz/camadas; v1/v2 preservados.
65 testes dirigidos passaram, cobertura de linhas/branches 100% nos quatro módulos
novos; 1.533 testes motion/exportadores passaram (dois skipped) e seis integrações
de regressão passaram. Mypy: 330 módulos; CI global ainda bloqueado pela
formatação preexistente em 17 arquivos. Migração 0118 aplicada somente ao `_test`
existente explicitamente autorizado, após reconciliar divergência antiga da 0075;
dev intocado, cinco serviços `exited`. Sem geração paga, asset novo ou render de
peça; qualidade visual não validada. Entrega/limites:
`docs/design/motion-preparacao-e-revisao-fases-1-3-2026-11-12.md`.
Titular identificou OpenCode como possível chat de diagnóstico; pesquisa/proposta
registrada em `docs/design/opencode-e-inspecao-do-produto-2026-11-12.md`, sem
instalação ou substituição do runtime. Registros anteriores abaixo são históricos.

**Rastreamento técnico da execução — 12/11/2026.** A rodada recuperada entrou
diretamente pela API com brief/direção do assistente; não qualificou entendimento
de mensagem natural do cliente. ASR local → duas chamadas (plano/código) → captura
com falha de persistência → MP4 de avaliação separado. Crítica/correção normais
não ocorreram. Chamadas, respostas originais e lacunas documentadas em
`docs/evals/auditoria-fluxo-motion-2026-11-12.md`. Sem nova execução/gasto.

**Auditoria por etapa — 12/11/2026.** Pedido posterior prioriza rastrear pedido,
entrada, saída, lacunas e impacto antes de avançar na geração. Primeira conferência
da rodada anterior reconstruída pelo builder real sem rede: seis quadros da fonte,
transcrição sem escuta, base histórica presente, cinco referências e direção fixa.
Falta parada humana entre plano e implementação. Nenhuma nova geração autorizada
por orçamento antigo; somente auditoria/documentação nesta entrega. Relatório:
`docs/evals/auditoria-fluxo-motion-2026-11-12.md`.

**Feedback e trechos curtos — 12/11/2026.** Exemplos do titular não devem virar
regras permanentes. Conferência confirma liberdade na skill, mas escolhas fixadas
na direção da rodada. Proposto estudo de ações completas de cerca de 4–5 s, com
contexto, imagem/som concebidos juntos e comparação na peça inteira; sem cortar
fala ou criar receita de intensidade. Somente documentação, sem execução/mudança
de runtime. Atualização e pendências em
`docs/evals/revisao-acabamento-cinematografico-motion-2026-11-11.md`.

**Feedback favorável e próximo acabamento — 11/11/2026.** Titular gostou do MP4
atual e o considera melhor que o último, mas distante do impacto da referência.
Preservar esta versão/hash como referência de continuidade; sem aceite final nem
aprovação fictícia no banco. Auditoria confirma 18 elementos, zero eventos sonoros
extras e referências Maestros de trajetória (80/84/88 s), não os trechos de
luz/câmera. Próximo foco proposto: preparação/revelação em ambiente coerente; A/B
sonoro separado. Distinguir incremento localizado de conclusão global do contrato
(o seletor atual exige ganho nas quatro dimensões); manter não regressão.
Revisão recorrente por rodada definida, ainda não automatizada. Somente análise
e documentação, sem nova geração/gasto/runtime. Evidências e prioridades:
`docs/evals/revisao-acabamento-cinematografico-motion-2026-11-11.md`.

**R5 — MP4 de avaliação autorizado e entregue, 11/11/2026.** Titular pediu o vídeo
após ver os quadros. Mesmo plano/código/material/áudio, renderizados no executor e
Temporal existentes: 720 × 1280, 30 fps, 11,2 s, áudio original; decodificação
verificada. Sem chamada paga adicional, edição do código gerado ou publicação.
Pedido original continua falho; não se fabricou aprovação persistida nem se
relaxou a recaptura. MP4 local para avaliação: `.local/evals/motion-recovery-run-20261111/nova-peca-avaliacao.mp4`.
Cinco serviços parados; qualidade criativa, persistência e CI ainda pendentes.
Evidências: `docs/evals/execucao-recuperacao-motion-2026-11-11.md`.

**R5 — geração recebida, entrega bloqueada, 11/11/2026.** Plano e implementação
concluídos; persistência do storyboard falhou por colisão de identidades dos quadros
globais v3. Bug corrigido, teste adicionado; migração 0117 permite dois eventos de
recaptura, sem novas tabelas. Recuperação por Temporal, sem provider, parou por
diferença de pixels. Diagnóstico guardou 20 quadros: 19 hashes iguais, diferença
em 2.800 ms ainda não localizada. Pedido `failed`, sem storyboard aprovado ou MP4.
US$ 2,50 reservados; estimativa US$ 0,568106, sem fatura. Não repetir chamadas nem
relaxar o controle. Prévia e evidências em
`docs/evals/execucao-recuperacao-motion-2026-11-11.md`. Qualidade visual não aprovada.

**Recuperação R5 — nova rodada autorizada, 11/11/2026.** Titular autorizou gerar
com teto novo da proposta US$ 6,25, sem imagens novas, somente áudio original,
até uma correção delimitada e aprovação do storyboard antes do MP4. Admissão
real e executor sintético conferidos; 77 testes dirigidos passaram. CI integral
permanece pendente; rodada operacional não equivale a merge/aceite visual.
Execução/evidências: `docs/evals/execucao-recuperacao-motion-2026-11-11.md`.

**Recuperação R1–R5 — entrega técnica, 11/11/2026.** Pedido posterior autorizou
implementar as cinco fatias. R1–R4: base histórica vinculada ao contexto real,
imagem original reutilizável, matriz de preservação, direção revista, cobertura
temporal v3 e seleção comparativa que bloqueia regressão/empate/incerteza.
R5: pacote real preparado e verificado; execução pendente, sem qualidade visual
nova validada. Etapas 1–6 preservadas; etapa 7 aberta. Nenhuma chamada paga,
asset novo, render, tabela ou serviço criado. Reserva nova proposta US$ 6,25,
não autorizada; storyboard continua anterior ao MP4. 1.114 testes passaram,
dois skipped; Mypy em 325 módulos. CI parou na formatação preexistente; cobertura
integral e integração `_test` pendentes. Evidências e limites:
`docs/evals/recuperacao-motion-r1-r5-2026-11-11.md`.
Os registros abaixo descrevem estados anteriores, superados por esta entrega.

**Plano de recuperação preparado — 11/11/2026.** Próximo trabalho organizado em
R1–R5: fixar comparação/recursos, vincular base ao contexto real, revisar direção
sem perdas silenciosas, verificar cobertura/seleção comparativa e só então executar
rodada autorizada. Mantém capacidades das etapas 1–6; recuperação do piso não é
evolução concluída. Etapa 7 continua aberta. Pedido atual produziu somente o plano,
sem implementação, banco, serviços, gastos ou render. Detalhes e aceites:
`docs/design/plano-recuperacao-e-evolucao-motion-2026-11-11.md`.

**Restrição de recuperação — 11/11/2026.** Titular exige manter as implementações
do aprendizado do YouTube/etapas 1–6 e demonstrar evolução na peça. As bases aceitas
são piso de avaliação, não autorização de rollback. A rubrica já existente precisa
ser aplicada como condição efetiva de conclusão/seleção; essa proteção ainda não
está implementada. Requisitos no contrato de qualidade, seção Regras transversais.
Somente documentação nesta atualização; sem alteração técnica ou execução.

**Diagnóstico comparativo da regressão — 11/11/2026.** Titular confirmou as duas
peças de “Anterior / Nova — quatro melhorias”, apresentadas em 11/11, como patamar
de referência. Sete elementos de ligação já haviam sido retirados na direção da
etapa 1; a base estava no pacote, mas não como composição anterior no payload.
Fidelidade ao plano preservou a simplificação, sem comparação com a peça aceita.
A espera pela xícara já existia na base; não explica sozinha a piora. Corrigida
a interpretação de “base preservada”: fonte/voz/kit não preservam a coreografia.
Análise local e documentação, sem correção de produto, gasto ou render novo.
Etapa 7 aberta e visualmente reprovada. Evidências e pendências em
`docs/evals/diagnostico-regressao-motion-2026-11-11.md`.

**Retorno criativo da etapa 7 — 11/11/2026.** Titular reprovou o storyboard:
sequência percebida como vídeo/texto, cartela “Uma pausa” e entrada da xícara,
sem ação visual compreensível. Diagnóstico confirma fragilidade no próprio plano,
incluindo cerca de 2,52 s entre a saída prevista da gravação e a entrada do objeto.
Não avançar ao MP4. Etapa 7 aberta; rever encadeamento antes de nova execução.
Sem gasto ou alteração técnica adicional. Feedback e evidências em
`docs/evals/comparacao-qualidade-motion-etapa7-2026-11-11.md`.

**Etapa 7 de qualidade motion — storyboard entregue, 11/11/2026.** Rodada
executada via API/Temporal dentro da autorização nova de US$ 6,75. Plano, uma
imagem e implementação concluídos; 18 quadros na galeria do produto. Reserva
US$ 3,00, estimativa por recibos US$ 0,372465, sem confirmação de fatura. Fonte,
kit e áudio original preservados; entradas enviadas conferidas por hash. Storyboard
aguarda decisão do titular; sem MP4 novo, crítica ou correção. Sombra difusa e
quadro só de fundo no retorno são ressalvas; qualidade visual e etapa 7 continuam
pendentes. Worker dedicado encerrado, serviços interrompidos não iniciados.
Evidências: `docs/evals/comparacao-qualidade-motion-etapa7-2026-11-11.md`.

**Etapa 7 de qualidade motion — preparação, 11/11/2026.** Montador real exportou
proposta de comparação com fonte/voz/kit preservados e chamadas futuras pendentes.
Titular escolheu somente áudio original; proposta de xícara fotográfica conceitual
aguarda aceite. Executor reconstruído, ainda sem qualificação em runtime. Reserva
nova proposta até US$ 6,75, não autorizada. 24 testes dirigidos, Ruff e Mypy passaram;
sem geração, peça ou avaliação visual nova. Etapa 7 continua aberta; não há etapa 8
definida. Detalhes: `docs/design/motion-etapa-7-preparacao-comparacao-2026-11-11.md`.

**Etapa 6 de qualidade motion — 11/11/2026.** Correção localizada por evidência,
cena, elementos e intervalo com margens explícitas. Plano, direção, assets e áudio
preservados; comparação exata de todos os rasters fora da janela rejeita regressões
antes da crítica seguinte/seleção. Identidade e auditoria existentes reutilizadas.
Prova sintética/local, anterior ao H.264; sem peça, gasto ou qualidade visual
validada. Imagem do executor, CI e comparação real pendentes. Etapa 7 requer OK.
Detalhes: `docs/design/motion-etapa-6-correcao-delimitada-2026-11-11.md`.

**Etapa 5 de qualidade motion — 11/11/2026.** Complementos selecionados e
atestados pelo titular usam acervo e vínculos existentes; ramo original protegido,
fades, ducking exclusivo da música e medição implementados. Testes sintéticos
locais aprovados; sem peça, escuta ou A/B. Falta material adequado autorizado e
reconstruir/fixar a imagem do executor antes do uso. Etapas 6–7 pendentes; etapa 6
requer OK. Detalhes: `docs/design/motion-etapa-5-som-e-voz-2026-11-11.md`.

**Etapa 4 de qualidade motion — 11/11/2026.** Skill HTML v13 acrescenta exemplo
opcional de preparação, objeto apoiado, repouso e retorno coordenado de gravação,
fundo e texto usando movement-v3. Snapshots anteriores, executor e bancos não foram
alterados. Montador real exportou entrada de plano v4 com fonte, kit, áudio,
transcrição e referências preservados, sem chamada ou render. 14 testes Node,
133 Python dirigidos, Ruff e Mypy do loader aprovados; sem CI integral. Isso não
comprova acabamento visual ou sincronia. Etapas 5–7 pendentes; etapa 5 requer OK.
Detalhes: `docs/design/motion-etapa-4-espaco-coreografia-2026-11-11.md`.

**Etapa 3 de qualidade motion — 11/11/2026.** Novas capturas com direção usam
v4: plano validado → materiais resolvidos → previews verificados → implementação;
v1–v3 históricas preservadas. Imagens ausentes interrompem a implementação;
pedido de revisão de plano preserva recibo e não gera nova chamada automática.
Exportação e adapters locais comprovam o vínculo, sem gasto ou render. Não há
prova visual nem retomada parcial automática; imagem anterior não foi encontrada
em `.local`. Etapas 4–7 pendentes; etapa 4 requer OK. Verificações e limites:
`docs/design/motion-etapa-3-assets-antes-do-codigo-2026-11-11.md`.

**Etapa 2 de qualidade motion — 11/11/2026.** Política temporal v2 distribui
janelas entre passagens e ação, respeitando o teto de 20 quadros e declarando
omissões; v1 histórica preservada. Storyboard apresenta sequências estáticas e
continua sendo portão após código, antes do MP4. Ao retomar, confere materiais,
direção e runtimes vinculados; quadros não comprovam movimento contínuo nem som.
Caso Café Pausa reproduz seleção de duas passagens e entrada da xícara, com
46 de 49 eventos omitidos; sem nova captura ou crítica. Testes dirigidos, Ruff
e Mypy aprovados; sem CI integral. Sem gasto, banco, geração ou render. Qualidade
visual e etapas 3–7 pendentes; etapa 3 requer OK do titular. Evidências e limites:
`docs/design/motion-etapa-2-revisao-representativa-2026-11-11.md`.

**Etapa 1 da evolução de qualidade motion — 11/11/2026.** Entrega técnica de
direção verificável e repertório aplicado: direção e brief revisados para Café
Pausa, matriz de problemas com instantes, regiões relevantes identificadas por
revisão humana e fichas selecionadas; sem impor borda ou efeito por palavra.
Novas capturas usam skill v12; o repertório opcional `business-reel-v2` incorpora
amostras e fichas rastreáveis, preservando versões históricas. Exportação offline
pelo montador do produto em `.local/exports/motion-qualidade-etapa1-final-20261111/`;
fonte, kit, áudio e transcrição iguais à base; seis quadros da fonte e cinco
imagens de referência. Restaurados, por autorização do titular, os contratos
removidos no commit posterior `4adb596` para manter o fluxo existente. Não há
peça nova nem qualidade visual aprovada.
Testes dirigidos: 96 Python, 62 de skill/contexto e 7 Node (grupos sobrepostos,
sem soma); Ruff e Mypy em quatro módulos aprovados. CI integral não executado. Verificação dos cinco contêineres
bloqueada pelo socket; não se afirma seu estado atual. Sem gastos, geração de
assets ou renderização. Etapas 2–7 permanecem pendentes, e a próxima depende de
OK do titular. Evidências e proposta:
`docs/design/motion-etapa-1-direcao-verificavel-2026-11-11.md`.

**Contrato da próxima evolução de qualidade — 11/11/2026.** Planejamento
consolidado em sete etapas: direção/repertório, revisão representativa, assets
antes do código, espaço/coreografia, som, correção delimitada e comparação com
aceite humano. Implementação técnica e ganho criativo têm aceites distintos;
tracking/OCR/stock/3D/EDL ficam condicionais. Todas as etapas estão pendentes;
sem nova geração, despesa ou mudança de produção. Contrato vigente:
`docs/design/contrato-evolucao-qualidade-motion-2026-11-11.md`.

**Reanálise de qualidade após feedback do titular — 11/11/2026.** A comparação
executou corretamente, mas a moldura foi considerada estranha e a xícara sem a
expressividade esperada. Seis frentes detalhadas: direção por sentido da fala,
integração da gravação, fundo, presença do objeto, som e revisão por cena.
Auditoria confirmou direção excessivamente prescritiva em moldura, código antes
dos pixels da imagem, storyboard desligado na rodada e seleção de três eventos
de fala concentrados no mesmo momento (46 de 49 eventos omitidos). A referência
Maestros foi reexaminada com transcrição e quatro sequências adicionais; não foi
incorporada automaticamente à entrada da peça. Prioridade proposta: direção e
repertório aplicáveis, cobertura da revisão, construção com asset visto, som e
refinamento delimitado; percepção/3D somente conforme necessidade. Nenhuma nova
implementação, geração, gasto, migração ou CI nesta análise. Plano e evidências:
`docs/design/motion-qualidade-direcao-e-gaps-2026-11-11.md`.


**Comparação concluída após reposição de créditos — 11/11/2026.** Novo pedido
pelo fluxo API/Temporal gerou plano e código completos, uma xícara conceitual
fotográfica, MP4 de 11,2 s (720×1280/30 fps) e crítica adequada. Mesma fonte/voz/kit
e 12 imagens, sem refações. Moldura, alternância e mudança dos planos de fundo
observadas; transições próximas de 4 s e 8,8 s ainda merecem refinamento. Crítica
limitada a amostras, sem escuta; nenhum aceite humano ou publicação.
Estimativa desta tentativa US$ 0,737973; reservas US$ 2,75 no teto US$ 3.
Pedido/reservas anteriores preservados separadamente. Worker exclusivo encerrado;
cinco serviços seguem parados. MP4 e comparação em
`.local/evals/motion-staged-retry-20261111/`. Relatório:
`docs/evals/comparacao-construcao-em-etapas-2026-11-11.md`.


**Prova real v3: plano completo; implementação bloqueada por créditos da API.**
Nova rodada de US$ 3 executada pela API/Temporal no banco de desenvolvimento
existente. Planejamento validado e preservado (3 cenas, 36 beats); segunda chamada
recusada pelo provedor com `insufficient_quota/credit_balance_exhausted`.
Não foi outra saída truncada. Nenhuma imagem, crítica ou nova peça produzida;
conclusão da implementação e acabamento continuam pendentes. Estimativa conhecida
US$ 0,22592, reservas US$ 1,50 mantidas; rejeição sem usage/custo conhecido.
Sem repetição ou reutilização de orçamento. Worker exclusivo encerrado; cinco
serviços seguem parados. Entrada exata da implementação exportada e verificada
por hash, sem chamadas adicionais. Evidências e próximo desbloqueio:
`docs/evals/comparacao-construcao-em-etapas-2026-11-11.md`.


## Atualização — 11/11/2026

**Construção em duas etapas implementada; prova real pendente.** Novas capturas
com direção fornecida usam contrato v3: plano completo sem código, seguido de
implementação vinculada por hash. Validações intermediárias, recibos cifrados e
reservas separadas no fluxo existente; sem retries implícitos ou retomada paga
automática. Corrigida ordem do schema no envio e exportação, mantendo hash canônico.
Mesma comparação preparada offline com as 12 imagens preservadas. Sem nova chamada
paga, imagem ou MP4. Desenvolvimento já está na revisão 0116, sem migração pendente;
defasagem encontrada era do banco de testes. Banco temporário anterior removido,
sem novos após orientação do titular. Detalhes e limites:
`docs/design/motion-construcao-em-etapas-2026-11-11.md`.
Validação: 473 testes dirigidos aprovados, cobertura integral nos seis módulos
medidos, Mypy em 15 módulos e Ruff OK. 23 integrações passaram; teste do Temporal
local bloqueado por conexão recusada. Sem afirmação de CI integral aprovado.

**Referência Maestros analisada, sem nova geração.** Vídeo WuzMxEKJHkQ baixado
com áudio português e legendas; conteúdo confrontado com 114 quadros distribuídos,
seis detalhes e documentação técnica. O relato de um prompt inclui horas de trabalho,
arquivos e revisão; não comprova uma única resposta de API. Recomendada construção
recuperável por artefato no Temporal existente e qualificação visual das quatro
melhorias. Recorte/tracking/3D são capacidades distintas, ainda não implementadas
por este estudo. Sem chamadas pagas, mudanças de produção ou nova peça.
Relatório: `docs/evals/analise-video-maestros-WuzMxEKJHkQ-2026-11-11.md`.

**Análise das interrupções concluída, sem chamada paga adicional.** Retornos
reproduzidos offline no parser: corte em scene_init vem marcado pela API; limites
locais de bytes, orçamento e falta de anexos não explicam a falha registrada.
Identificados saída indivisível, ordenação alfabética do schema colocando código
após plano e reasoning=high fixo. A causa raiz do limite reportado continua sem
comprovação: uso abaixo do teto e dos limites públicos do modelo. Compactação de
20,87% não era prova de conclusão. Próximos passos documentados, não implementados.
Relatório: `docs/evals/diagnostico-interrupcao-motion-2026-11-11.md`.

**Tentativa com contrato compacto concluída sem MP4.** O provedor voltou a retornar
MOTION_AI_OUTPUT_LIMIT, com JSON cortado em scene_init, após 562,74 s. Contrato v2
foi efetivamente enviado, mas a compactação não resolveu o bloqueio. Contagem:
35.340 tokens de entrada, 27.924 de saída (18.425 de reasoning); teto solicitado
e retornado 54.000. A causa do limite permanece indeterminada. Três tentativas
encerradas: estimativa acumulada US$ 0,998378, reservas US$ 2,80 mantidas. Nenhuma
imagem, crítica ou nova peça gerada. Sem novas tentativas autorizadas. Worker
exclusivo encerrado e cinco serviços seguem parados. Próxima geração exige uma
solução verificada para a saída incompleta; não repetir apenas ajustes de prompt.
Evidências: `docs/evals/comparacao-quatro-melhorias-2026-11-10.md`.

## Estado vigente — 10/11/2026

**Histórico — contrato compacto v2 preparado em 10/11/2026.**
Representação dos beats reduzida em 20,87% no plano completo da resposta anterior,
com igualdade exata dos 63 movimentos após expansão. Contratos antigos preservados;
mesmas validações e formato completo na persistência/crítica/render. 234 testes
dirigidos aprovados; cobertura integral dos dois módulos medidos, Ruff/Mypy OK.
Nenhuma nova chamada paga ou peça gerada. Entrevista de autorização pendente para
uma tentativa adicional: reservas acumuladas máximas US$ 3,95 no teto US$ 4.
A causa da interrupção anterior permanece indeterminada; redução não garante
sucesso. Detalhes: `docs/design/motion-contrato-compacto-2026-11-10.md`.

**Histórico — duas tentativas da comparação bloqueadas; sem novo MP4.** Duas
composições tentadas, incluindo a recuperação explicitamente autorizada dentro
do teto acumulado US$ 4. Ambas retornaram MOTION_AI_OUTPUT_LIMIT e JSON cortado
em scene_init. Recuperação: 364,07 s, 35.075 tokens de entrada e 19.856 de saída
(8.804 de reasoning), apesar de max_output_tokens=64.000 solicitado e retornado.
Não atribuir causa definitiva ao modelo nem confundir com falha de renderização.
Estimativa acumulada US$ 0,630788; reservas US$ 2,15 mantidas. Nenhuma imagem,
crítica ou MP4 produzido; não há terceira tentativa autorizada. ASR local funcionou
nas duas operações e registrou 30 palavras com custo zero. Qualidade visual ainda
não qualificada. Cinco serviços continuam parados; worker exclusivo encerrado.
Antes de outro gasto, investigar a saída interrompida e reduzir a repetição entre
plano e código sem perder as quatro melhorias. Detalhes e evidências:
`docs/evals/comparacao-quatro-melhorias-2026-11-10.md`.

**Histórico da entrega — etapa visual 4 implementada antes da comparação.**
Backend local faster-whisper baseado na abordagem do Clipador Viral dos Maestros
da IA: tempos por palavra, confiança e origem não revisada, com possibilidade de
entrada humana revisada. Execução no fluxo Temporal existente, claim durável e
reutilização em correção/storyboard. Skill v11, validação de fonte/onsets/focos e
amostragem dos eventos ligados. Mantidas moldura, fundo, objeto e alternância.
Configuração desabilitada por padrão; dependências/modelo ainda não instalados no
worker e nenhuma inferência real executada. Sem chamadas pagas, asset novo, MP4
ou Docker. 346 testes Python e 11 Node aprovados; cobertura integral nos sete
módulos medidos. Precisão/qualidade dependem da comparação.
Aguardar OK do titular para iniciar essa comparação, com escopo/orçamento próprios.
Vídeos brutos longos e cortes continuam futuros. Detalhes em
`docs/design/motion-fala-alinhada-2026-11-10.md`.

**Histórico — etapa visual 3: objeto realista em camadas.**
Novas capturas usam skill v10: seleção de imagem autorizada ou conceitual gerada,
material/luz coerentes e helper executável de recorte com sombra coordenada.
Moldura, fundo narrativo e alternância preservados; snapshots v1–v9 intactos.
Direção Café Pausa e especificação de uma única imagem preparadas; substituem
preenchimento do desenho por chegada/assentamento. Dependem de asset e capacidade
configurada; nenhuma imagem ou novo MP4 foi gerado. 131 testes Python e 11 Node
passaram, cobertura integral no loader medido e Ruff/Mypy aprovados. Sem chamadas
pagas ou Docker. Etapa 4 (fala alinhada) aguarda OK; qualificação visual pendente.
Detalhes: `docs/design/motion-objeto-realista-2026-11-10.md`.

**Histórico — etapa visual 2: fundo narrativo.**
Novas capturas usam skill v9, preservando moldura/escala da etapa 1 e movement-v3.
Incluído exemplo executável de base opaca, campo de cor e detalhe com movimentos
coordenados, repouso e contraste planejado. Café Pausa recebe três elementos de
fundo; os 16 elementos anteriores permanecem intactos. Capturas antigas conservam
suas skills. 97 testes Python e 9 Node passaram; cobertura integral no loader
medido, Ruff/Mypy aprovados. Pacote offline montado/verificado, sem geração paga,
asset novo ou MP4 nesta fatia. Acabamento visual permanece por qualificar.
Etapa 3 (objeto realista) aguarda OK. Detalhes em
`docs/design/motion-fundo-narrativo-2026-11-10.md`.

**Histórico — etapa visual 1: tratamento da gravação.**
Novas capturas usam skill v8 e movement-v3: orientação e exemplo executável de
moldura, entrada/assentamento, aproximação uniforme e saída coordenada. Corrigido
reset implícito do arredondamento CSS; radius explícito mantém controle. V1/v2 e
skills anteriores preservados por hash, inclusive recapturas e repertório v2.
99 testes Python e 30 Node passaram; cobertura 100% nos três serviços medidos,
Ruff e Mypy aprovados. Sem CI global, geração paga, asset novo ou MP4 nesta fatia.
Pacote offline preparado pelo montador; acabamento visual ainda não qualificado.
Etapa 2 (fundo vivo) aguarda OK do titular. Detalhes em
`docs/design/motion-tratamento-gravacao-2026-11-10.md`.

**Docker — pedido paralelo de diagnóstico atendido.** Cinco serviços em ciclo de
reinício consumiam mais de quatro núcleos na amostra inicial. Foram parados com
autorização explícita para mantê-los parados, sem restaurar ao final. Nenhum dado,
volume ou contêiner foi removido. Nove contêineres ativos na leitura posterior,
aproximadamente 492 MiB; limite da VM de ~3,83 GiB não é uso por contêiner.
Detalhes/limites em `docs/evals/diagnostico-docker-2026-11-10.md`.

**Histórico — etapa 1 de confiabilidade; comparação local concluída.**
Novas capturas com direção fornecida usam `provided-direction-output-v1`: o
modelo não repete scene_direction; o servidor a restaura integralmente antes
das validações/persistência. Snapshots antigos e direção proposta pelo modelo
preservados. Respostas inválidas agora conservam uso/custo estimado/request ID;
encerramento do subprocesso drena pipes após interrupção, evitando espera com
buffer cheio. Sem retry pago implícito ou relaxamento das validações.

O MP4 local da composição completa v6 foi concluído em 99,35 s: 11,2 s,
720×1280/30 fps, 336 quadros e áudio original, correlação de sinal 0,99998847.
A pausa temporária de cinco serviços com mais de 1.300 reinícios cada foi
explicitamente autorizada; os cinco foram restaurados após a captura. O teste
curto caiu de 75,90 para 26,38 s; limites e sandbox não foram ampliados.
Causa dos reinícios permanece fora desta fatia e pode voltar a afetar o ambiente.

Comparação: `.local/evals/motion-reliability-20261110/comparacao.html` e
`comparacao-alternancia.mp4` na mesma pasta. HTML/JS gerados preservados; apenas
os dois ajustes descritivos anteriores do plano. Não é nova geração v7 nem
qualificação automática: os pedidos anteriores continuam failed. Fundo ativo,
moldura e asset realista ainda precisam da prova específica. Zero novas chamadas
pagas; nenhuma reutilização de orçamento. Contrato compacto validado offline;
qualificação por modelo requer rodada própria autorizada.

Validação final: 441 testes Python dirigidos passaram (38,64 s), com 100% de
linhas/ramos nos quatro módulos medidos: adapters motion_ai/motion_html_renderer,
schema e serviço motion_generation. Ruff e Mypy de seis módulos aprovados;
exportação final verificada, links e JavaScript da comparação conferidos.
Sem CI global, testes SQL ou migração. A saída de exemplo cai de 39.029 para
29.970 bytes (23,21%); reconstrução offline preserva direção validada, HTML e JS.

Detalhes, evidências e pacote externo novo em
`docs/design/motion-confiabilidade-geracao-captura-2026-11-10.md`.

**Histórico anterior — alternância, fundo e confiabilidade; comparação então pendente.**
O titular pediu alternância entre gravação e motion e correção dos defeitos de
recorte/crítica; depois acrescentou fundo ativo, variação de moldura/escala do
vídeo e objetos mais realistas. Novas capturas usam skill v7, executor v2,
criativo v6/v7, movimento v2 e crítica v3. Snapshots antigos permanecem intactos.

Movement-v2 não cria máscara em tracks sem clip explícito. A crítica v3 liga
checks aos problemas por índices e inclui os quadros reais desses problemas,
sem relaxar mínimos de evidência ou inventar suporte. Passaram 393 testes Python
com cobertura integral nos cinco módulos avaliados; 66 testes de contexto/skills/
exportação após o feedback v7; 25 Node, Ruff e Mypy dos dez módulos. A prova
sintética no Chromium confirmou o conserto do recorte com máscaras preservadas.
Sem CI global ou SQL nesta fatia.

A rodada de até US$ 3 teve duas gerações autorizadas: primeira completa mas com
plano inválido (v6), recuperação incompleta (v7). Zero renders/críticas pelo fluxo,
pedidos failed e workers encerrados. Uso estimado total US$ 0,572968, incluindo
cálculo local da primeira resposta cujo ledger ficou sem estimativa; reservas
retidas US$ 2,15. Nenhuma imagem paga, retry adicional ou uso do saldo autorizado.

Não foi concluído novo MP4 para comparação. A variante local da primeira resposta
completa reuniu apenas dois intervalos descritivos do plano, HTML/JS intactos.
A captura integral excedeu 600 s; a tentativa local em trechos falhou por timeout
do navegador. Restaram três quadros estáticos, sem validação de movimento/áudio.
Processo diagnóstico encerrado; nenhum renderer remanescente. A resposta parcial
v7 não foi executada. Ver `previas-parciais.html` na pasta local do ensaio.
Asset realista em camadas (2.5D) é viável com os recursos de imagem existentes;
geometria 3D giratória ainda exige outra integração. Qualificação visual pendente.

Próximo gate: saída completa/validável, captura confiável, recuperação limitada e uso/custo de erros
preservados, antes de liberar a jornada do Reel. Depois: pedido/ajuste/aprovação/
download, fala alinhada, story em vídeo, carrossel e operação. Postagem é posterior.
Detalhes em `docs/design/motion-alternancia-e-confiabilidade-2026-11-10.md`,
`docs/evals/plano-motion-alternancia-2026-11-10.md` e
`docs/design/fechamento-produto-geracao-2026-11-10.md`.

**Histórico — interação entre mensagem e elementos, comparação entregue.** O titular pediu
setas, ícones e objetos com acabamento adulto e ações ligadas às frases. A direção
anterior restringia esses recursos indevidamente. A skill v4 e a nova direção
Café Pausa orientaram tempo→percurso, café→preenchimento, pausa→repouso/convite.
A coreografia usa texto editorial; não há transcrição alinhada nem sincronismo
vocal comprovado. Fonte, áudio, kit e versões históricas foram preservados.

A primeira geração veio incompleta. A recuperação explicitamente autorizada
renderizou, mas contêineres aninhados recortaram o vídeo; a crítica apontou o
defeito e falhou na vinculação exata das evidências. O pedido permaneceu `failed`.
Foi entregue uma variante com correção CSS local apenas desses recortes, pelo
mesmo renderer isolado, sem novas chamadas pagas ou aprovação automática.
Novas capturas usam skill v5, que acrescenta orientações sobre esses dois problemas;
recapturas conservam seus hashes. A v5 ainda não foi qualificada em geração real.

Teto acumulado US$ 3 respeitado: reservas US$ 2,90; estimativa pelo uso retornado
US$ 0,758614, distinta de fatura. O ledger da crítica inválida ficou sem estimativa;
o total inclui cálculo local explicitamente separado. Worker encerrado, ambiente
temporário removido. Passaram 100 testes Python e quatro Node; cobertura dirigida
do loader 100% de linhas/ramos, sem CI global. MP4 local: 11,2 s, 720×1280/30 fps.
Amostras visuais e sinal de áudio conferidos; acabamento depende do titular.
Ver `docs/design/motion-interacao-mensagem-2026-11-10.md` e
`docs/evals/plano-motion-interacao-2026-11-10.md`. Pendentes: confiabilidade do fluxo
automático, qualidade da v5 em prova futura e sincronismo com fala real. Nenhuma
nova chamada ou uso do saldo está autorizado.

**Comparação após a refatoração concluída.** Sob teto novo de US$ 5, o fluxo
API/Temporal gerou e renderizou uma candidata Café Pausa e concluiu uma crítica,
sem refações nem imagens pagas. Uso total estimado US$ 0,322005; reservas US$ 2,80,
distintas de fatura. MP4 720×1280/30 fps, 11,2 s; parecer `adequate` sem truncamento
nesta rodada, sem comparação automática com a peça anterior ou aceite humano.
Worker dedicado encerrado. Comparação A/B, custos, validação e limites em
`docs/evals/plano-comparacao-refatoracao-motion-2026-11-10.md`.
Aguardar avaliação do titular; saldo restante não autoriza novos efeitos.

**Decisão mais recente — etapa 6 concluída; pacote externo entregue.**
O titular confirmou a proposta Café Pausa em entrevista. O exportador usa o mesmo
montador de instruções/contexto do produto e `build_request`, com dados factuais
e amostras verificados da prova registrada. Nenhum prompt paralelo de construção.
ZIP com 39 arquivos em `.local/exports/motion-cafe-pausa-20261110.zip`: prompt
integral, JSON/schema/parâmetros, 12 imagens, contexto, direção, repertório/licenças,
fonte MP4, fontes e runtimes. Manifesto separa entrada do modelo de execução.
Uso e caminhos em `docs/evals/pacote-externo-motion-2026-11-10.md`.

Sem credenciais, consulta ao banco, despacho Temporal, contagem remota, API paga,
novos assets ou render. IDs locais novos e ilustrações desabilitadas nesta entrada;
nenhuma autorização anterior de orçamento reutilizada. Dados factuais e amostras
são históricos, não uma recaptura/admissão operacional atual. O chat externo pode
alterar papéis, schema ou leitura; vídeo/runtimes extras são variações documentadas.

Passaram 69 testes curtos com insumos sintéticos: igualdade do payload, anexos,
hashes, ZIP, ausência de dados privados de teste, bloqueio de rede e compatibilidade
do montador. Contexto com 100% de linhas/ramos na cobertura dirigida; Ruff, tipos
e diff aprovados. Pacote real e ZIP verificados, sem CI global ou teste SQL.
As seis etapas de preparação estão concluídas; aguardar o resultado externo.
Acabamento, movimento e áudio continuam sem nova prova, sem autorização de produção.

**Histórico — etapa 5 implementada e validada localmente.**
Novos snapshots incluem `motion-review-v2`, com o mesmo alvo de acabamento na
geração, crítica e correção. Integridade técnica, legibilidade e preservação do
kit são distintas de desenvolvimento visual; evidências da peça permanecem
separadas das referências. Falha criativa acionável deve compartilhar quadro
atual com o problema correspondente; ausência de evidência não autoriza refação.

A resposta compacta usa IDs de quadros, convertidos ao parecer durável com tempo
e SHA antes das validações. Prosa/problemas são limitados, mantendo os checks.
Somente a entrada da crítica omite HTML/JavaScript das composições; a correção
recebe código completo. Snapshots anteriores conservam o contrato anterior.
Sem novo serviço, tabela, executor ou aumento de orçamento/teto: crítica permanece
limitada a 8.000 tokens ou ao limite configurado menor, sem retry automático.

Passaram 214 testes dirigidos; cobertura de linhas/ramos em 100% no serviço de
crítica e no schema compacto. Ruff, tipos dos quatro módulos e diff aprovados.
Na fixture sintética, 76,1% menos bytes de resposta para o mesmo parecer; não é
medição de tokens/custo nem garantia contra truncamento. Sem CI global, banco,
API real, geração de assets ou render. Detalhes e limites em
`docs/design/critica-motion-2026-11-10.md`. Acabamento continua sem prova visual.
O OK para a etapa 6 foi dado na solicitação seguinte.

**Histórico — etapa 4 implementada e validada localmente.**
Novos pedidos HTML usam a skill `instagram-reel-v3`, com orientações concretas de
hierarquia tipográfica, máscaras, planos em profundidade, ação com resultado,
contraste de movimento, leitura e continuidade. Dois exemplos completos usam
MotionV1 existente: passagem entre focos com gravação contínua e entrada escalonada
com tempos finais disponíveis para o plano. Não são cenas impostas nem APIs novas.
A direção fornecida orienta a implementação; identidade, gravação e voz permanecem.

O texto e os exemplos chegam por `authorized_context.skill`, no mesmo corpo
contado/limitado. O mapa de uso orienta a adaptação do repertório da etapa 2 sem
copiar identidade. Recapturas HTML carregam o ID/hash original da skill; v1/v2,
pacote de referências, renderer e runtimes permanecem intactos. Sem novo serviço,
componente, tabela, motor ou geração de mídia. Caminhos e uso em
`app/assets/motion_skills/README.md`.

Passaram 170 testes Python e quatro testes Node direcionados. Os dois módulos
de produção alterados atingiram 100% de linhas/ramos na cobertura dirigida.
Ruff, tipos e diff aprovados; sem CI global, banco, API real ou render.
Os testes JavaScript executam os exemplos da própria skill com DOM substituído;
validam continuidade de estado e busca temporal, não qualidade visual. A proposta
Café Pausa continua sem aceite criativo. O OK para a etapa 5 foi dado na
solicitação seguinte. Exportação integral permanece na etapa 6.

**Histórico — etapa 3 implementada e validada localmente.**
O pedido aceita `scene_direction` opcional com o schema existente. Quando fornecida,
a direção fica no snapshot antes da construção, sob `reel-creative-v5`, e orienta
plano e código. O payload distingue direção fornecida de proposta pelo modelo,
identifica origem/hash e não infere aprovação humana. O serviço rejeita troca da
direção na geração/correção antes de imagens ou render; tempos e curvas continuam
no único `motion_plan`. Sem direção fornecida, mantém o fluxo existente em v4.

Proposta revisável Café Pausa: “abrir espaço para uma pausa”, com gravação contínua,
planos e tipografia em dois momentos específicos da prova. Não exige jarra/xícara
desenhadas; usa o kit e preserva a voz. A proposta ainda não foi aprovada pelo titular.
Contrato, uso e briefing substituto em `docs/design/direcao-visual-motion-2026-11-10.md`;
entrada em `docs/evals/direcao-cafe-pausa-2026-11-10.json`. Sem planejador automático,
nova chamada, tabela ou alteração do executor. Aprovação de quadros continua separada.

Passaram 228 testes Python direcionados; novo módulo com 100% de linhas/ramos na
cobertura dirigida. Ruff, tipos dos seis módulos de produção e diff aprovados.
Sem CI global, banco, API real, geração de assets ou render. Igualdade da direção
não comprova fidelidade visual do HTML nem acabamento. O OK para a etapa 4 foi
dado na solicitação seguinte. Exportação integral fica na etapa 6.

**Histórico — etapa 2 implementada e validada localmente.**
O pedido pode selecionar explicitamente `repertoire_id=business-reel-v1`.
O mesmo montador do produto captura três exemplos completos adaptados de
Maestro, Finalizador e claude-video, com fontes/licenças/hashes, e entrega seis
quadros de Felipe Borges e Lucas Leite ao modelo. Referências têm rótulo, tempo
aproximado, sequência, uso permitido e limitações; ficam fora dos assets de render.
Não há estilo imposto globalmente, novas tabelas ou novo executor. Pedidos sem
seleção e snapshots históricos conservam seu conteúdo.

Os anexos seguem para geração, revisão e correção e integram o mesmo corpo da
contagem/tetos de entrada existentes. Limites locais de texto/imagens e hashes
falham antes de envio quando há ausência, alteração ou associação incorreta.
Pacote: `app/assets/motion_repertoire/README.md`. Passaram 163 testes Python
focados e dois testes Node sem mídia renderizada; novo módulo com 100% de
cobertura de linhas/ramos na verificação dirigida. Ruff, tipos dos sete módulos
alterados e `git diff --check` aprovados; sem CI global.
Nenhuma API real, geração de assets ou render. Acabamento visual ainda não provado.
O OK para a etapa 3 foi dado na solicitação seguinte.

**Histórico — etapa 1 da refatoração implementada e validada localmente.**
O titular pediu documentar a execução em etapas: (1) contrato/contexto sem
contradições; (2) repertório e referências efetivamente enviados; (3) direção
visual distinta da construção; (4) orientações e exemplos de construção/movimento;
(5) crítica alinhada ao alvo e aos limites; (6) exportação do payload completo.
Plano: `docs/design/refatoracao-contexto-motion-2026-11-10.md`.
Novos pedidos usam a skill `instagram-reel-v2`, o contrato
`html-motion-executor-v1` e a projeção `html-executor-style-v1` das fichas;
arquivos e hashes históricos permanecem intactos, assim como a recaptura de
pedidos anteriores. Passaram 95 testes direcionados de contexto, skills, estilos
e adaptador; Ruff check/format e `git diff --check` aprovados, sem CI completo.
O OK para a etapa 2 foi dado na solicitação seguinte. Ao final da sequência, entregar
prompt, anexos e manifesto para teste manual em ChatGPT, Grok ou outro modelo.
Parar antes de chamadas pagas, geração de assets ou render da peça. Não preparar
um prompt paralelo como se fosse a entrada exata do produto. Aguardar resultado
externo para decidir prova integrada. Infraestrutura existente e kit preservados.

**10/11 — vídeo renderizado; melhora parcial, qualidade desejada não atingida.**
Após a recuperação dos quadros (migração 0115), o titular aprovou a versão exata.
A API registrou o aceite e o Temporal montou o MP4 reutilizando composição e
materiais. Comparativo: `.local/evals/reel-storyboard-composition-20261109/comparison.html`.
O titular reconheceu mais elementos visuais, mas considerou o desenho infantil e
o resultado ainda distante do acabamento profissional das referências. Esse
feedback não é aprovação criativa final. Pediu analisar dois novos vídeos como
referência de acabamento. Esclareceu que edição de bruto para YouTube é outra
ideia, fora do escopo atual: manter a gravação do cliente e explorar muito mais
a composição/movimento ao redor dela na postagem do negócio. Cortes do bruto
não são pré-requisito para esta melhoria.

A única crítica prevista veio truncada no limite de 8.000 tokens, sem parecer
válido. Pedido encerrado como `failed/MOTION_AI_OUTPUT_LIMIT`, MP4 e recibos
preservados. Corrigida a identidade de falha da continuação para não colidir com
a falha anterior em audit/outbox; migração aditiva 0116 aplicada no dev, sem
limpeza. Nenhuma repetição de IA, render ou correção automática nessa recuperação.

Acumulado da prova: quatro chamadas textuais, estimativa US$ 0,775244 e reservas
US$ 3,40 retidas; nenhuma imagem gerada paga. Estimativa não equivale à fatura.
Qualquer nova chamada exige plano/autorização próprios; não reutilizar o saldo
como autorização automática. 69 testes unitários direcionados (1,55 s) e três
testes SQL em banco `_test` (7,52 s) passaram, com Ruff aprovado. Sem CI completo.
Ponto 4 não qualificado; etapa 5 não iniciada. Resultado detalhado em
`docs/evals/resultado-video-composicao-2026-11-10.md`.

**Análise posterior das referências:** download e inspeção dos dois vídeos de Lucas
Leite concluídos por amostragem visual. Auditoria da chamada confirmou seis quadros
da fonte, nenhuma referência visual de acabamento, skill resumida e três fichas
antigas com restrições incompatíveis com o executor HTML. Modelo `gpt-6.1-sol`,
esforço alto, geração completa; não há benchmark que atribua a causa ao modelo.
A direção da prova também induziu os desenhos de jarra/xícara. Corrigir contexto
e testar uma cena exigente é o próximo recorte proposto, ainda não implementado.
Detalhes: `docs/evals/analise-acabamento-motion-2026-11-10.md`. Nenhuma nova chamada paga.


**Adaptação do fluxo de Lucas Leite:** mapeamento das oito etapas e dos guias
publicados concluído em `docs/design/adaptacao-fluxo-edicao-2026-11-10.md`.
Base técnica existente reaproveitável; falta separar decisão visual de construção,
transmitir referências e instruções coerentes e demonstrar acabamento numa cena.
Hoje direção/plano/código são gerados juntos, antes da aprovação dos quadros.
O documento é proposta, não integração concluída. Sem nova API paga ou mudança
no executor; cortes de bruto para YouTube continuam fora do escopo.

**Histórico — reformulação da composição autorizada, antes do vídeo.**
O titular gostou das xícaras desenhadas e autorizou reformular a composição.
Isso não aprova a galeria anterior para animação. A nova direção alterna gesto
real, transformação ilustrada e convite à pausa, com foco, escala e organização
distintos; preserva desenhos figurativos, kit, fonte integral, áudio e aprovação
humana dos quadros. Esse roteiro é específico da prova Café Pausa.

Orientação geral de geração/crítica ajustada para avaliar evolução da composição,
sem impor variedade arbitrária: acrescentar desenhos a um layout repetido não
demonstra elaboração por si só. Repetição com função narrativa continua válida.
Vinte testes direcionados passaram em 1,09 s; Ruff/format aprovados. Worker
reconstruído; renderer, runtime, hashes históricos e banco não foram alterados.

Novo payload preparado para o produto, dentro da autorização original: até
US$ 3,70 restantes + US$ 1,70 retidos = US$ 5,40. Duas chamadas textuais/contagens,
até duas ilustrações opcionais, sem correção automática; parar nos quadros.
Plano: `docs/evals/plano-reformulacao-composicao-2026-11-09.md`.
Pendente: nova galeria real, aceite humano e vídeo/crítica. Etapa 5 não iniciada.

**Histórico da retomada anterior — três quadros após correção técnica local.**
Retomada autorizada executou uma geração completa, validada pelo contrato. O modelo
criou três cenas com desenhos SVG próprios; não solicitou ilustrações pagas.
O render integrado falhou (`MOTION_RENDER_EXECUTION_FAILED`): elementos estáticos
receberam tracks com `beats:[]`, mas a biblioteca exige ao menos um intervalo.

Diagnóstico local preservou o original e acrescentou somente holds idênticos ao
estado inicial dessas tracks. O mesmo renderer isolado capturou três PNGs reais,
sem nova IA, MP4 ou alteração/reabertura do pedido encerrado. Galeria aberta para
o titular: `.local/evals/reel-storyboard-resume-20261109/diagnostic-gallery.html`.
É uma captura após correção técnica, **não** uma galeria aprovada/persistida pelo
fluxo integrado. O titular depois solicitou reformular essa direção antes do vídeo. Movimento/áudio não
foram avaliados; a composição ainda repete vídeo à esquerda e desenho à direita.

Instruções da biblioteca agora explicitam 1–12 beats por track e hold para elementos
estáticos. Runtime e hashes dos snapshots permanecem intactos; não adicionamos
recuperação automática ou nova geração. Cinco testes direcionados passaram em
0,68 s, Ruff aprovado; captura real passou pelo sandbox/protocolo 2. Sem CI completo.

Uso estimado da retomada: US$ 0,180125; somado à tentativa truncada, US$ 0,421603.
Reservas das duas tentativas: US$ 1,70 retidos para conciliação. Nenhuma imagem ou
crítica paga, nenhuma correção paga. Os limites autorizados não foram ampliados.
Plano/resultado: `docs/evals/plano-retomada-storyboard-integrada-2026-11-09.md`.
Pendente: decisão visual, tratamento da falha na integração e vídeo/crítica final.
Nenhuma equivalência às referências demonstrada; nenhuma etapa 5 iniciada.

**Histórico da conclusão do ponto 3 — quadros completos por cena e aprovação antes do MP4.**
Pedidos com `storyboard=true`, quando a capacidade estiver explicitamente habilitada,
produzem um PNG completo por cena com a composição e os assets reais da geração.
O modelo indica o momento representativo; o renderer captura somente esses momentos,
sem codificar vídeo/áudio. Não são todos os frames nem evidência de ritmo/mixagem.

Galeria HTML e metadados privados ficam disponíveis pela API autenticada. O aceite
vincula versão e hash do conjunto; reprovação registra feedback e encerra o pedido,
sem tentar outra chamada paga. A aprovação emite outbox e retoma pelo Temporal,
reutilizando composição e ilustrações, revalidando fontes, consentimento e orçamento.
Reentregas são bloqueadas por identidade durável. A revisão/aprovação final da peça
continua distinta da aprovação inicial de composição.

Validação: 295 testes Python direcionados em 3,70 s e 72 testes Node em 0,55 s;
mypy e Ruff aprovados. IO de banco/browser/provedor substituído nos testes locais;
regressão SQL de isolamento/aceite/reentrega adicionada, não executada. Sem CI
completo, chamadas pagas, reconstrução Docker, migração aplicada ou prova criativa.

**Pendências registradas ao concluir o ponto 3 (resolvidas na preparação do ponto 4):** aplicar `0114_motion_storyboards`, reconstruir
renderer com protocolo 2 e configurar seu novo digest; habilitar
`motion_storyboard_enabled` (default false) e enviar `storyboard=true`.
Pedidos antigos continuam no fluxo anterior. Naquela conclusão, o ponto 4 aguardava comando: prova real
com IA, apresentação dos quadros para o titular e avaliação do vídeo após aceite.
Não há uma nova peça real produzida nesta implementação nem orçamento reutilizado.

**Histórico do ponto 2 — componentes, acervo e ilustrações sob demanda.**
O fluxo do Reel reúne 16 componentes vetoriais, desenho original por código,
até quatro fotos autorizadas do acervo e até duas ilustrações geradas quando
necessárias. A mesma geração textual declara a arte e seus caminhos; o serviço
cria os PNGs antes do render, e a crítica recebe os pixels gerados. Kits, skills,
biblioteca de movimento, Temporal e histórico privado continuam preservados.

Ilustrações têm identidade por pedido/asset, reserva própria no ledger compartilhado,
registro de uso/proveniência e upload privado verificado. Correções reutilizam os
mesmos arquivos e não podem alterar a lista para disparar novas imagens. Despacho
repetido, falha incerta, custo desconhecido/excedido e falta de orçamento interrompem.
A reserva é limite de admissão local, não teto de faturamento imposto pela Images API.

Ativação explícita desabilitada por padrão: `motion_illustrations_enabled=false`,
reserva e orçamento de imagens zero. O orçamento de imagens é parte do orçamento
total do Reel; precisa deixar espaço para geração e crítica. Sem novas permissões,
migração ou chamadas pagas. Modelos e contratos históricos preservados; não há
ativação retroativa para pedidos capturados sem essa capacidade.

**Na conclusão do ponto 2, o próximo ponto era:** quadros principais com a arte
pronta antes do vídeo (ponto 3, implementado conforme registro acima). Prova visual com IA real e aceite criativo continuam posteriores;
esta implementação não demonstra que o acabamento já atingiu as referências.
Validação: 273 testes direcionados aprovados em 3,76 s, Ruff/format e mypy
em 12 módulos aprovados. Pixels sintéticos e transporte simulado; sem CI completo,
banco ou render integrado. Regressão SQL adicionada para o `_test`, não executada.

**Histórico do ponto 1 — direção criativa por cena.**
Novos pedidos capturam `reel-creative-v3` e exigem `scene-direction-v1`: base no
briefing, representação visual, composição, ação narrativa, ordem de atenção e
aparência/construção de cada elemento. A direção se vincula às cenas/elementos
do `motion_plan-v1`, que conserva os tempos, estados, relações e transições.
Geração/correção usam a mesma chamada; não há geração de assets nesta fatia.
O serviço recusa vínculos incompletos/inválidos antes de reservar render. Direção
acompanha composição privada, crítica e correções; v1/v2 históricos permanecem
compatíveis. Kits, acervo, skills, motion lib, orçamento e Temporal preservados.

201 testes direcionados em 5,18 s; Ruff/format e mypy aprovados. Cobertura de
100% nos três módulos medidos de direção/plano/contrato, não CI da aplicação.
Regressão SQL acrescentada, não executada. Sem banco, API paga, render ou deploy.
À época, criação/seleção de elementos aguardava comando; estado atual acima. Quadros principais,
crítica aprimorada e comprovação visual continuam posteriores. Implementar o
contrato não comprova que o modelo atingirá o acabamento desejado.
[Escopo, decisões e validação](design/evolucao-qualidade-motion-referencias-2026-11-09.md).

**Pesquisa de composição concluída:** Maestro contém geração de objetos
recortados, busca de takes e captura de páginas; Finalizador contém 70 cenas em
código; claude-video já prevê arte por cena antes da animação. Fontes externas
oficiais confirmam catálogo de componentes e mídia. Na pesquisa, esses recursos ainda não estavam
integrados ao Reel; adaptação parcial registrada acima; a pesquisa não demonstra qualidade nem autoriza gastos.
O titular posteriormente confirmou liberação do conteúdo Maestro para nosso uso;
a observação anterior sobre o ZIP não bloqueia o escopo autorizado.
[Inventário, fontes e próximo recorte](evals/pesquisa-elementos-motion-2026-11-09.md).

**Quarto passo: fluxo técnico concluído; melhora parcial, alvo criativo não atingido.** A retomada
Café Pausa terminou `completed` pelo worker/Temporal dev, com uma versão real,
crítica e download autenticado conferido por SHA. Comparativo A/B aberto para o
titular; não houve correção. Duas chamadas/contagens, 574,11 s, US$ 0,379066 estimado.
Com a tentativa truncada anterior: US$ 0,562636 estimado e US$ 2,55 reservado,
dentro do teto original de US$ 3,40. Reservas não são fatura/uso conciliado.

Modelo retornou `adequate`, quatro checks criativos `met` e temporais `pass`.
Entretanto, as três janelas cobriram entrada de palavra, ponto gráfico e hold de
CTA; **37 de 40 eventos omitidos**, incluindo as principais transições sem sequência
próxima completa. Isso valida o fluxo técnico, não o acabamento esperado ou a
eficácia do crítico nesse alvo. Geração usou 18.102 tokens com override de 32.000;
defaults gerais de 16.000 não foram alterados. Crítica: 7.924 de 8.000 tokens.
Worker próprio encerrado; sem CI completo, migração, publicação ou expansão de
formato. Avaliação humana recebida: melhorou, mas ainda muito longe; faltam
componentes figurativos, imagens e ícones relacionados à mensagem. Não há aceite
criativo/comercial nem confirmação específica de áudio ou ausência de regressões.
A auditoria encontrou entrada restrita a vídeo/fontes/logo, direção centrada em
tipografia/enquadramento e ausência de transcrição. MotionV1 oferece movimento,
mas não constrói por si só esse repertório visual. Próximo recorte proposto:
planejamento visual por mensagem, materiais/componentes associados ao kit e
crítica das cenas principais. A direção foi implementada posteriormente, conforme
registro acima; demais pontos pendentes e nenhum novo gasto.
[Plano concreto](evals/plano-prova-motion-temporal-integrada-2026-11-09.md).
[Plano de retomada](evals/plano-retomada-motion-temporal-2026-11-09.md).

**Terceiro passo da evolução de motion implementado — crítica temporal.**
Novos snapshots incluem `motion-temporal-v1`: até três eventos distribuídos pela
peça, cinco quadros de contexto e até cinco por evento, mantendo **no máximo 20
quadros por versão**. Tempos do plano orientam a extração; somente quadros reais
decodificados do MP4 fundamentam a crítica. O manifesto privado registra IDs,
tempos, hashes, cobertura, bordas e eventos omitidos. Nenhuma chamada adicional
é obrigatória; texto e imagens continuam na contagem/reserva existente.

`MotionReview` passa a exigir, nessa capacidade, continuidade, sobreposição,
tempo de leitura e coordenação. Um parecer conclusivo requer sequência completa
com pelo menos três tempos citados, incluindo seus extremos. Correção temporal
precisa apontar issue acionável compatível e localizada nessa evidência; incerteza
não autoriza refação. Preferência pela versão nova requer sequências das duas
versões. Histórico sem capacidade temporal conserva o comportamento anterior.
Kit e referências continuam separados; calibrações externas são textuais, sem
alegar comparação visual com vídeos não enviados.

Validação: **292 testes direcionados em 7,29 s**, Ruff e mypy aprovados; proteção
adicional contra issue genérica de motion contornando incerteza confirmada em
41 testes (0,80 s). Extração do MP4 sintético anterior: 16 quadros, três eventos
completos e 12 omitidos explicitamente; sequências inspecionadas. Sem IA paga,
novo render, CI completo, teste SQL, migração ou deploy. Isso valida implementação
e vínculo das evidências, não acerto do julgamento da IA ou ganho criativo.
**Quarto passo com execução técnica concluída e qualidade criativa insuficiente**, conforme
avaliação humana acima. Não expandimos formatos nesta fatia.

**Segundo passo da evolução de motion implementado — execução reutilizável.**
`MotionV1` oferece timeline com estados numéricos, curvas cúbicas/Bézier/mola,
entradas escalonadas, máscaras e transformações coordenadas, calculadas por
`seek(ms)` sem relógio ou playhead acumulado. A API, versão e SHA-256 entram no
contrato capturado; o serviço verifica disponibilidade antes da geração paga.
O adapter inclui os bytes conferidos no início de `scene.js`, pelo canal isolado
já existente. Assim, a imagem do renderer não precisa incorporar uma nova
biblioteca; o worker precisa receber o código atualizado. Pedidos históricos
sem essa capacidade conservam os bytes originais da cena. Kit, acervo, skills,
estilos, áudio, versões e limites de orçamento permanecem no fluxo existente.

Validação: **266 testes Python em 4,20 s**, 8 testes Node em 0,51 s, Ruff e mypy
aprovados; após um ajuste de compatibilidade, 30 testes afetados em 1,98 s.
Reprodução sintética local de **4 s / 120 quadros / 360×640 / 30 fps**, com
Chromium, CSP/roteamento e FFmpeg reais; quadros extraídos do MP4 inspecionados.
A demonstração foi escrita manualmente, sem áudio ou geração por IA: comprova
execução dos recursos, não ganho criativo. Não houve CI completo, teste SQL,
migração, build/deploy, API paga ou nova prova Linux/Temporal naquela fatia. O
terceiro passo foi implementado posteriormente, conforme registro acima. A prova
integrada continua necessária para demonstrar qualidade do produto.

**Primeiro passo da evolução de motion implementado — contrato de movimento.**
Novos pedidos usam `reel-creative-v2` e exigem `motion-plan-v1` na mesma chamada
que produz/corrige HTML: cenas e elementos identificados, tempos absolutos,
estados, trajetória/curva, relações e propósito. Kit, acervo autorizado, skill e
biblioteca de motions continuam no contexto; referências orientam acabamento do
movimento, preservando a identidade do negócio. O plano acompanha as versões
cifradas e a crítica existente. Antes de reservar o efeito de render, o serviço
confere duração, estilo selecionado e assets autorizados; o schema rejeita
lacunas de cenas, eventos fora de intervalo e relações inválidas. Sobreposição
entre cenas é permitida para transições; entre beats do mesmo elemento, não.
Históricos sem plano e `reel-creative-v1` continuam legíveis e processáveis.

Validação desta fatia: **155 testes direcionados passaram em 8,75 s**, Ruff e
mypy aprovados. Regressão SQL adicionada para falha sem plano e reentrega sem
repetir geração; não executada nesta rodada. Sem CI completo, banco, render,
API paga ou deploy naquela fatia. A conformidade do plano **não comprova execução
visual** do HTML. O segundo passo foi implementado posteriormente, conforme
registro acima; a crítica temporal também está implementada. A prova integrada
(quarto passo) foi executada; o alvo criativo continua não atingido. Detalhes no plano de evolução de qualidade de motion.

**A fatia local de integração do Reel está implementada e tecnicamente
qualificada.** Pedido/contexto privado, efeitos duráveis, Temporal, renderer
HTML isolado, crítica/correção condicionais e versões imutáveis estão ligados.
A coleção permite revisão, cinco confirmações por arquivo e download privado;
a aprovação não cria postagem. A versão mais nova não é automaticamente a melhor.

O [CI da base anterior à proteção completa de orçamento](../.local/ci-motion-integration-20261109/run-20261109T154537Z/result.json) passou: **5.353 testes, 100% de 18.570 linhas e 5.090 branches**,
sem skips. Passaram também 363 testes Python do laboratório, 137 Node dos
renderers, lint/formatação e tipos. Web: 524 testes/100% nas quatro métricas,
tipos, build, formatação e QA de interface em 390/1440 px. O código daquela execução permaneceu
estável durante o CI; os bancos eram exclusivos `_test`, com roles restritas.

Os quatro replays Linux preservaram código/assets: Intensa 67,3 s, Dog 75,2 s,
Luma 73,3 s e Giz B 107,2 s. A prova do pedido ao download passou em 97,6 s
com API/auth, SQL/RLS, relay, Temporal, renderer e storage reais; **modelo e
crítico simulados**. Reentrega não repetiu efeitos; acesso de outro tenant e
anônimo foi bloqueado. Não houve aprovação humana fabricada nem chamada paga.
[Comparações, resultados e limites](evals/qualificacao-integracao-reel-2026-11-09.md).

Os dez workers parados com autorização foram restaurados. O storage descartável
da prova foi parado, preservando dados e arquivos. A primeira execução do CI
falhou numa expectativa antiga de tabela; o teste foi alinhado à guarda que
inclui Reels. Novas provas SQL cobrem bloqueio durante execução e repetição de
aprovação antiga após surgir outra versão, sem duplicar efeitos ou aprová-la.

**Isso não encerra a ativação comercial da etapa 4 nem a v0.** A configuração
continua desativada por padrão e restrita a negócios/materiais sintéticos.
A validação completa do orçamento (ponto 1) foi implementada: contagem da
entrada multimodal antes da geração, soma com a saída máxima e bloqueio
quando exceder a reserva compartilhada. A contagem inclui instruções, schema
e quadros de origem/versões, sem gerar conteúdo. Política qualificada para
`gpt-6.1-sol` Standard: tarifa conservadora cobre escrita de cache; entrada
acima de 272 mil tokens e modelos/tarifas não qualificados são bloqueados.
Cálculo e versão da política ficam no registro cifrado da operação.
Validação desta mudança: **100 testes unitários direcionados em 1,62 s**,
Ruff e mypy aprovados; sem CI completo, SQL, render ou chamada externa. O CI
acima documenta a base anterior, não uma nova execução desta mudança.
**Ponto 2 implementado após autorização:** target `motion-worker` com cliente
Docker, overlay opcional com configuração consistente de API/relay/worker e
pasta temporária compartilhada no mesmo caminho. O renderer recebe somente a
entrada da própria tentativa; socket/credenciais permanecem fora dele. Há um
comando de verificação sintética de dois quadros para executar antes da prova.
**130 testes direcionados passaram em 4,49 s**, Ruff/mypy e Compose resolvido
aprovados (desativado e fixture fake, sem carregar o `.env` real). Na entrega
do ponto 2 não houve build/render real; eles foram executados no ponto 3 abaixo.
**Primeira rodada do ponto 3 — histórico da falha:** a prova Café Pausa com IA real
produziu duas versões de 11,2 s pelo worker do produto, Temporal local autorizado
e banco dev existente (migrações 0112/0113 aplicadas com autorização, sem limpeza).
A crítica detectou acentos corrompidos; a correção preservou o JavaScript e
corrigiu o texto observado nos quadros. Foram três chamadas ao modelo e quatro
contagens (a última inferida pelo avanço até o claim); uso estimado conhecido
**US$ 0,412521**, reservas **US$ 2,55**, teto autorizado US$ 3,40. Fatura não conciliada.
O PostgreSQL cancelou o INSERT do pacote da crítica final em `motion_effects`
por ultrapassar o prazo de 10 s. A quarta chamada ao modelo não foi enviada.
Pedido `failed`, duas versões preservadas, sem peça liberada na coleção:
crítica final e download ficaram pendentes naquela rodada, concluídos em nova
operação no item 3 abaixo.
Não houve retry pago, aceite humano ou publicação. Worker próprio encerrado.

O defeito de UTF-8 foi corrigido no runner, com 71 testes direcionados (1,17 s)
e verificação real mínima da imagem nova; a prova paga preservou o digest antigo.
**Correção de persistência implementada após a rodada:** pedidos multimodais e
quadros cifrados acima de 64 KiB passam ao armazenamento privado existente;
SQL mantém referência cifrada pequena, hashes e identidade de operação.
Upload é registrado antes do IO, conferido por tamanho/hash e nunca repetido
automaticamente; falha interrompe antes da chamada paga. Serialização/cifra saíram
das transações desses registros. Leitura recupera registros inline antigos e
referências novas, validando tenant/negócio/pedido antes de buscar o objeto.
No pacote salvo do Café Pausa, o campo SQL caiu de **42.205.388 para 716 bytes**,
com conteúdo recuperado exatamente (medição offline, 1,417 s). **81 testes
unitários direcionados passaram em 1,42 s**, Ruff/mypy aprovados. Acrescentadas
duas regressões SQL para o CI futuro; não executadas nesta fatia.
Não houve migração, alteração do dev, build/deploy, CI completo ou API paga.
O pedido antigo continua falho; a nova prova integrada está registrada abaixo.
Não foi aumentado o timeout global nem removida a trava de custos.
A exportação somente leitura usou prazo local de 60 s para recuperar as evidências.
Temporal dev voltou ao estado parado original, com histórico preservado; seu
problema permanece separado. Sem CI completo nesta rodada.
[Vídeos, resultado, custos e limites](evals/plano-prova-reel-integrada-2026-11-09.md).
**Item 2 anterior — direção e critérios criativos:** esta entrega introduziu
`reel-creative-v1` (novos pedidos agora usam v2, conforme atualização acima) no contexto cifrado e no fingerprint. Geração/correção recebem
orientação para planejar tempos, estados visuais e função das transformações no
`concept`, com calibrações textuais de Intensa, Dog, Luma e Giz B. Nenhuma mídia
desses ensaios foi incorporada ou enviada; estilo/intensidade não são universais.
A crítica exige quatro avaliações: atendimento ao briefing, progressão narrativa,
função do movimento e desenvolvimento visual. Cada uma liga pedido, observação
e quadros; as três temporais exigem dois tempos distintos da versão atual.
`adequate` não admite requisito criativo falho/incerto; lacuna criativa acionável
usa a correção condicional existente. Incerteza sem defeito concreto não dispara
refação. Acentos corrigidos não são ganho de motion. Leitura histórica preservada.
**98 testes direcionados passaram em 1,50 s**, Ruff/mypy aprovados. Acrescentada
regressão SQL de bloqueio de crítica apenas técnica, para execução futura.
Sem render, API paga, migração, build/deploy ou CI completo. Esses testes provam
as regras de validação, não a qualidade criativa do julgamento do modelo.
Itens 1 e 2 implementados; **item 3: prova técnica real concluída; melhora criativa
parcial, abaixo do nível esperado pelo titular**. Nova operação Café Pausa terminou `completed`, com
geração, render, crítica, coleção privada e download autenticado conferido por
SHA-256. Duas chamadas ao modelo e duas contagens; estimativa **US$ 0,266156**,
reservas novas **US$ 1,70**. Com US$ 2,55 anteriores, permanecem US$ 4,25 retidos
sob teto agregado autorizado de US$ 5,95; fatura ainda não conciliada.
A crítica marcou os quatro requisitos criativos `met` e não pediu correção:
há uma única versão nova. O A/B compara a peça histórica com a nova geração;
não demonstra ganho de correção automática. Payloads grandes usaram referências
SQL cifradas de 716 bytes, sem aumentar o timeout. Workflow em 667,63 s, incluindo
310,30 s de render; essa medição isolada não define tempo comercial de entrega.
Worker próprio encerrado. Sem migração, limpeza, retry pago ou CI completo.
[Plano da nova rodada](evals/plano-comparacao-criativa-integrada-2026-11-09.md).
Avaliação humana recebida: B ficou um pouco melhor, mas continua muito aquém dos
motion graphics e exemplos das bibliotecas esperados. O nível criativo pretendido
não foi atingido; não há aprovação de qualidade comercial. Áudio e outras possíveis
regressões não foram avaliados explicitamente na resposta. Os quatro checks `met`
do modelo não equivalem ao patamar criativo desejado. A rodada usou calibrações
textuais, sem comparar visualmente com as referências. Próxima necessidade:
definir uma referência concreta e calibrar geração/crítica contra seu acabamento,
preservando diversidade; escopo e orçamento de nova execução ainda não definidos.

Referência concreta recebida: vídeo de Felipe Borges, analisado visualmente desde
o início por sequências de quadros. [Análise e trechos](evals/referencia-motion-youtube-fqaEZqPzKZs-2026-11-09.md).
Os exemplos usam cenas gráficas, interfaces, diagramas e composição em camadas.
A referência esclarece o alvo, mas não conclui a qualidade do produto. Próximo
recorte proposto: enriquecer o planejamento de cenas e calibrar a crítica visual;
cortes e áudio alinhado exigem ampliação explícita da integração. Sem nova API paga.

O [Reel específico enviado depois](evals/referencia-reel-Db9axeiOotS-2026-11-09.md) foi baixado e
inspecionado por sequências de quadros. Ele prioriza hierarquia, revelação
progressiva, estados e alternância de composição. Recorte de pessoa e imagens
geradas não são pré-requisitos dessa próxima prova. Eventos ligados à fala
exigem alinhamento; em peças sem fala, usar tempos do roteiro. Sem nova geração.

Quatro Shorts adicionais foram analisados, incluindo legendas do tutorial de
cinco passos. [Plano consolidado de evolução](design/evolucao-qualidade-motion-referencias-2026-11-09.md).
Cálculo determinístico e render quadro a quadro já existem. A próxima evolução
proposta concentra direção visual/quadros-chave, comportamento dos elementos,
materiais próprios e crítica comparativa. Sem migração de executor ou exigência
automática de 60 fps. Nenhuma nova geração paga ou mudança de runtime.
Esclarecimento do titular: as referências orientam qualidade do movimento; kit
visual, fontes, cores e logo continuam sendo os do negócio. A sequência proposta
é contrato de movimento → recursos determinísticos → crítica temporal → prova
integrada; primeira prévia possível após as duas primeiras fatias, sem biblioteca
completa. Criticar movimento não exige parecer visualmente com a marca da referência.




Contrato para clientes reais e aceite criativo desta peça permanecem pendentes.
Esta fatia usa a gravação inteira e seu áudio reencodado; não acrescenta
transcrição, legendas alinhadas ou seleção de música. Quadros não comprovam
movimento integral ou escuta.
[Contrato da integração](design/integracao-reel-2026-11-09.md).

**Etapa 3 concluída no recorte demonstrado:** legibilidade do 1c e preferência
humana por Giz B (“B ficou melhor.”). Giz é refinamento com feedback/referência
adicionais; não prova ganho universal de autocrítica ou economia. Artefatos,
feedback e custos históricos permanecem separados no [registro](evals/motion-registro-de-validacao.md).

**Etapa 5 ainda não implementada.** O escopo autorizado anteriormente inclui
o ciclo de imagem feed/story, seguido de story em vídeo e carrossel animado.
A sequência vigente termina primeiro os três pontos do Reel, um por comando. O
[desenho de imagens](design/ciclo-revisao-imagens-2026-11-09.md) prevê inspeção do JPEG final antes da entrega,
correção condicional e preservação de versões; planejamento não é entrega.
A [matriz](design/v0-motion-etapa-0-formatos-e-casos.md) registra o reuso e as lacunas por formato.

WhatsApp (6) e piloto/operação comercial (7) continuam posteriores. Piloto de
autoatendimento com cobrança, ainda sem participantes reais; usar os quatro
casos fictícios. Preço/franquias dependem de custo por peça aceita. Publicação
automática no Instagram permanece posterior. Dúvidas de produto serão tratadas
em entrevista; manter o foco nas fatias autorizadas.

## Histórico da retomada — 08–09/11/2026, antes da preferência humana por Giz

Os registros abaixo preservam a sequência de preparo, execução e validação.
Pendências de avaliação humana descritas nessa sequência eram o estado de cada
momento; a conclusão vigente e os próximos trabalhos são os do bloco acima.

O titular recuperou o texto dos [sete processos de trabalho](design/execucao-ate-etapa-7-2026-11-07.md)
e autorizou alinhar a documentação, resolver pendências técnicas e concluir a
prova comparativa da etapa 3 antes de integrar o Reel (etapa 4). Depois, avançar
para os demais formatos (etapa 5), em fatias qualificadas. A integração depende
da comparação e da avaliação humana; não se presume ganho ou aprovação.
Dúvidas de definição serão tratadas em entrevista e os avanços comunicados.
O objetivo posterior de preparar o piloto e a operação comercial (etapa 7)
continua registrado, sem confundir essa numeração com as dez fases audiovisuais.

A entrevista foi respondida: ainda não há participantes reais definidos e o
modelo escolhido é **autoatendimento com cobrança**. A validação pode usar os
cenários fictícios já documentados: cafeteria, Ponto do Dog (loja física), Dog em
Casa (delivery) e Estúdio da Luma (manicure). Preço e franquias dependem de
custo por peça aceita; R$ 99/R$ 50 permanecem hipóteses. Instagram fica depois
da geração, revisão e download; WhatsApp oficial é requisito da jornada real.

A continuação independente `4338880a-10f2-48a7-96cd-54138f87dbdd` terminou em
`completed_partial_human_pending`. Dog e Luma receberam críticas com contexto
criativo v2: ambas `adequate`, sem achados acionáveis ou versões corrigidas.
Intensa permanece bloqueada pela operação incerta anterior, sem retry. Duas
novas chamadas somaram US$ 0,175165 estimados; o acumulado da revisão é de seis
tentativas para Intensa/Dog/Luma, US$ 0,427215 conhecidos e US$ 1,50 em reservas,
com custo da tentativa
incerta ainda desconhecido. O teto autorizado de US$ 6,75 não foi esgotado.
[Resultado e relatório](evals/ensaio-ciclo-revisao-motion-2026-11-06.md).

A tipagem foi corrigida e as ferramentas de mídia recuperadas em diretório
local persistente, com hashes conferidos. Passaram 107 testes Python de motion
e o preflight dos três casos. O relatório foi corrigido para caminhos longos e
validado em 390/1440 px, nos modos cego/identificado: três players, sem overflow,
erros JavaScript ou rede externa. Vídeos, críticas e ledger foram preservados.
Após reproduzir o timeout e ajustar a preparação dos testes de concorrência,
o módulo passou em quatro testes (93,61 s). Houve falhas posteriores de CI,
preservadas como histórico; a execução final de 09/11 passou, conforme abaixo. No recorte `app`/`migrations`, somente o teste
`test_destination_lock_proof.py` mudou desde a tentativa anterior desta retomada;
produção e migrations foram preservadas. O CI de 06/11 abaixo valida sua árvore histórica. A etapa 3 já
tem reparação de legibilidade reconhecida pelo titular, mas ainda não aprovação
global criativa. A validação técnica foi concluída em 09/11; custo por peça
aceita ainda não foi comprovado.

O titular escolheu em entrevista **testar a correção do Reel antigo com problema
conhecido**. O [plano do Reel 1c](evals/plano-revisao-reel-1c-2026-11-08.md)
preserva o baseline histórico de tipografia pequena, dez normalizações anteriores
e o pacote concluído de 69 arquivos privados, com o manifesto original preservado.
A ponte declarativa foi implementada; passaram 146 testes locais (57 da
orquestração e 89 da ponte), Ruff e mypy estrito. Essa origem não é HTML/JS.
A primeira qualificação do run `3a52c376-e8ea-4bea-b997-94ba59c628de` parou no
parsing de metadados do FFprobe 4.4.8, sem API; artefatos e falha foram preservados.
Após correção estrita do leitor, o preflight real passou: o MP4 arquivado é
idêntico ao original e o remux preservou 526 pacotes AAC, PCM e tempos, além de
336 quadros RGB24 e tempos. Depois, a segunda qualificação completa passou,
recompilando/renderizando a direção original e confirmando quadros/tempos e
AAC/PCM iguais; o registro de qualificação foi preservado por hash.

O titular autorizou explicitamente até três chamadas/US$ 1,25 e o envio à OpenAI
na entrevista de orçamento. `authorization.json` vincula a decisão ao plano,
primeiro pedido e qualificação. A execução paga do 1c foi concluída, com
resultado e custos abaixo; o feedback humano confirmou apenas a legibilidade. A autorização é
própria desse caso, sem transferir saldo de Intensa/Dog/Luma. A falha de unidades já foi corrigida
na geração atual: esta prova mede reparação histórica, sem atribuir ao crítico
a correção anterior ou presumir ganho criativo geral. Prova e avaliação humana
(etapa 3) continuam anteriores à integração do Reel (4) e aos outros formatos (5).

O [ensaio 1c concluído](evals/ensaio-revisao-reel-1c-2026-11-08.md) produziu
original e v1 comparáveis. A crítica inicial encontrou uma falha `major` de
legibilidade; a correção ampliou títulos/legendas e foi renderizada sem ajuste
manual. A crítica final retornou `adequate`, sem achados, e preferiu v1; seis
critérios passaram e áudio ficou `uncertain`. AAC/PCM/tempos foram preservados.
O executor registra `completed_human_pending`. Depois, o titular confirmou:
“o B tem os titulos e legendas bem melhor”, mas questionou se era story e por
que faltava motion. A melhora de legibilidade foi reconhecida; não há aceite
global, de áudio ou de motion. O pedido original era `reel` com cortes,
transições, motion e legendas; a entrada era ilustrativa/licenciada com voz
sintética, não gravação de cliente real.

O 1c tem pequenos ajustes de enquadramento/fades. A prova reparou tipografia,
mas não qualificou acabamento criativo: presença de animação não comprova
adequação ao briefing. Intensa/Dog/Luma continuam as referências; 1c não vira
padrão. O relatório inicial passou em 390/1440 px, dois modos e oito reproduções
mutadas; isso comprova apresentação, não escuta humana ou qualidade criativa.

A apresentação foi corrigida depois: agora exibe `limitations[]` com escape de
HTML, explica `adequate` como ausência de outro defeito acionável nas evidências
e distingue parada automática de aceite criativo. Passaram 15 testes do
relatório, Ruff e mypy. Somente o HTML foi regenerado, preservando original,
código e hashes; vídeos, críticas e summary permanecem intactos. O QA dirigido
do novo HTML passou em 390/1440 px nos dois modos, com limites visíveis apenas
no identificado, dois players, sete links e nenhum overflow, erro JavaScript
ou rede externa. O QA anterior foi conservado. Sem API ou custo adicional.

Separar movimento observado de atendimento criativo pertence ao próximo
contrato de avaliação do Giz, agora implementado e testado, com calibração
criativa ainda pendente. A correção de apresentação do relatório 1c não
reclassifica as críticas históricas nem qualifica a criatividade por si só.

O titular respondeu **“Comprovar melhora do motion primeiro (recomendado)”**.
A etapa 3 exige prova criativa antes da integração. O candidato em análise é
Giz (`15adf19d`, lote `e2bbd3aa`), anteriormente avaliado abaixo de Intensa.
A auditoria não encontrou violação inequívoca do briefing original: motion e
desenho existem; pedidos de tema e janela contínua vieram no feedback posterior.
A próxima prova será de refinamento guiado por feedback/contexto adicional
declarado, sem atribuí-lo à descoberta de um erro do pedido inicial. O
[plano do Giz](evals/plano-refinamento-motion-giz-2026-11-08.md) e o pacote privado
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

O [resultado Giz](evals/ensaio-refinamento-motion-giz-2026-11-09.md) registra
US$ 0,6482575 estimados incrementais e US$ 0,8686550 de subtotal de APIs com o
histórico. Comprometimento US$ 1,0138475, dentro de US$ 1,25; a comparação
excedeu sua reserva em US$ 0,0138475. Subtotal medido de 483,872 s exclui preparo,
qualificação, inspeções e intervalos. Não são fatura, COGS ou custo por peça aceita.
QA do relatório aprovado em 390/1440 px e dois modos, com oito reproduções
mutadas completas, links válidos e 248 arquivos preservados. Comparação aberta
no navegador e entrevista humana enviada com link; resposta/aceite pendentes.
O ganho avaliado é refinamento com feedback e referência posteriores, sem atribuí-lo à
autocrítica do briefing original ou generalizar benefício da revisão.

A [validação técnica de 09/11](../.local/ci-20261108/ci-final-result.json)
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

No ensaio 1c, três chamadas HTTP 200, sem retry ou incerteza: **US$ 0,527685 estimados novos**,
US$ 1,25 reservados. Subtotal histórico de APIs US$ 0,106892; subtotal com revisão
US$ 0,634577, sem fatura ou COGS completo. Chamadas somaram 154,561 s; render e
evidências, 151,928 s; subtotal medido 306,489 s exclui setup/preflight/intervalos.
A prova e o feedback sustentam reparação desse defeito histórico, não ganho
criativo ou retorno financeiro geral. O CI foi concluído; a avaliação humana
da prova criativa precede integração do Reel (4) e demais formatos (5). A etapa 3
não recebeu aprovação global; a autorização posterior de Giz não altera esses
resultados ou o aceite limitado do 1c.

## Histórico: início da revisão iterativa de Reel — 06/11/2026

O titular escolheu Python e APIs configuradas para experimentar geração,
renderização, inspeção por evidências, correção limitada e novo render. A
comparação começa pela mesma composição histórica no braço sem e com revisão;
até duas correções e crítica por versão, com julgamento humano da melhor peça.
Os [critérios e limites](design/ciclo-revisao-motion-2026-11-06.md) foram
implementados no protótipo privado; o [plano do ensaio](evals/plano-ciclo-revisao-motion-2026-11-06.md)
registra o trabalho e a comparação real e avaliação humana
permanecem pendentes. O titular autorizou até
US$ 6,75 para três casos, até 15 chamadas e envio de quadros/contexto/código à
OpenAI, conforme o plano; áudio recebe avaliação técnica e escuta humana.
Primeira execução: três críticas `adequate`, sem correções, custo estimado
US$ 0,2520500 e reservas US$ 0,75; auditoria identificou contexto criativo
incompleto. A [continuação delimitada](evals/plano-ciclo-revisao-motion-2026-11-06.md)
parou com resultado incerto na primeira crítica, sem resposta salva ou refações;
não houve ganho comprovado. Total: quatro chamadas, US$ 0,2520500 conhecidos
de estimativa, custo da última desconhecido e US$ 1,00 reservados.
[Resultado parcial e limites](evals/ensaio-ciclo-revisao-motion-2026-11-06.md).
Validação da árvore de 06/11: `make ci` passou com 5.045 testes Python da aplicação
e 100% de linhas/branches; também passaram 91 testes Python de motion, três
Node de áudio, 62 Node do renderer, Ruff e mypy. Banco exclusivo `_test`,
Temporal local, `TZ=UTC` e prevenção temporária de repouso; detalhes e tentativas
anteriores no [changelog](CHANGELOG.md). A aprovação técnica não comprova ganho.
Esta prioridade substitui o foco anterior no clipe; sua avaliação continua
pendente. Não se prevê servidor Claude Code ou agentes hospedados. Integração
com Temporal e jornada WhatsApp vem depois de evidência criativa; postagem é
fase posterior à geração, revisão e download. Os marcos datados abaixo
preservam o estado e as autorizações de cada momento.

## Histórico: clipe pessoal de 46,5 segundos — 06/11/2026

Titular pediu uma frente por vez e solicitou gerar peça do próprio vídeo musical,
com motion e apoios realistas ligados à letra, preservando canto/execução.
Material preparado localmente e pré-teste técnico de renderer pessoal passou;
não rotular gravação real como fixture sintética. [Plano](evals/plano-clipe-musical-pessoal-2026-11-06.md).
Três chamadas, estimativa US$ 0,60–1,50 e teto adicional US$ 1,60 propostos;
titular autorizou a verba/envio pessoal. Transcrição recebida e conferência
parcial das legendas registrada; direção/composição concluídas e MP4 de 46,5s
entregue, com áudio original idêntico e comparação local. Estimativa US$ 0,51148,
três chamadas sem retry. [Resultado](evals/ensaio-clipe-musical-pessoal-2026-11-06.md).
Avaliação criativa desta peça pessoal aguarda o titular; produto segue incompleto.
Higgsfield/Brabo e demais etapas adiados.

## Step 1: outros negócios com a qualidade da Intensa — 06/11/2026

Preparados Reels de Dog em Casa e Estúdio da Luma; titular confirmou foco em
marca/experiência, sem preços. Dois clipes ilustrativos licenciados, kits próprios,
skill Reel e fontes concretas da biblioteca; contraste de temas e transformação
do enquadramento entram explicitamente na direção. [Plano e limites](evals/plano-motion-outros-negocios-2026-11-06.md).
Preflight dos dois cenários passou, sem mudar executor/produto. Nova rodada
propôs duas chamadas e US$ 1,50 adicionais; titular autorizou verba/envio e o
lote `04e48db9-1313-4a52-a188-7a151a9d0e80` entregou os dois MP4s e comparação.
Estimativa total US$ 0,5906725. Dog precisou tradução de IDs de áudio e render
offline, sem nova geração ou alteração visual. [Resultado](evals/ensaio-motion-outros-negocios-2026-11-06.md).
Titular gostou bastante: os dois mantiveram o nível da Intensa, mesmo curtos.
Step 1 validado criativamente nestes casos; mesma música foi apontada como
possível problema. Ambos tinham uma única trilha obrigatória: seleção entre
alternativas continua pendente e deve entrar em prova específica antes da integração;
o novo A/B do ciclo preserva a trilha para isolar a revisão visual.
Política confirmada: escolha automática contextual, variedade entre pedidos e
repetição permitida para continuidade de séries/campanhas; implementação pendente.

## Diversidade após feedback positivo; registro para integração — 06/11/2026

O titular avaliou o Reel intenso: “muito legal. melhorou bastante.” Autorizou
seguir diversidade de linguagens, outros negócios fictícios, story e carrossel,
antes da integração do caminho qualificado. Para os outros negócios, escolheu
preparar vídeos ilustrativos licenciados. Novas chamadas exigem verba própria.
O [registro vigente](evals/motion-registro-de-validacao.md) reúne feedback,
evidências e requisitos de transferência, sem presumir produto concluído.

Três cenários distintos da biblioteca estão preparados para a mesma cafeteria;
[plano da rodada](evals/plano-motion-diversidade-2026-11-06.md). O comando de lote
passou em preflight e os testes offline passaram (40 Python e três Node).
Após a preparação, o titular autorizou três chamadas/envio do pacote, com teto
adicional de US$ 2,25 e sem refação automática. Lote
`e2bbd3aa-e405-4411-9d56-82752537bc73`: duas peças concluídas, Papel incerto sem
resposta/custo salvos, sem retry. Cartaz bem avaliado; Giz menos convincente;
**Intensa é a preferida até agora**. [Resultados](evals/ensaio-motion-diversidade-2026-11-06.md).
Próximo passo: levar esse nível aos outros negócios; depois story/carrossel.
Artefatos privados continuam locais; backup remoto/restauração e empacotamento
de dependências são pendências explícitas, não entregas presumidas.

## Versão intensa disponível para comparação — 06/11/2026

A [exploração intensa](evals/ensaio-motion-intenso-2026-11-06.md) entregou MP4
e relatório com v2 mínimo/última versão. Inclui inversões verde–creme–verde,
arcos em ondas, letras com deslocamento e janela contínua, com código da
biblioteca adaptado. Uma chamada autorizada, estimativa US$ 0,3086025, sem
ajuste manual. É ensaio de intensidade; qualidade e preferência aguardam o titular.

## Próximo ensaio: intensidade de motion — 06/11/2026

O titular gostou um pouco mais da rodada `276486e3`, mas ainda prefere o v2;
não rejeitou a peça. Pediu uma versão “exagerada”, com motion mais robusta,
destacando mudanças entre verde/creme, letras invertidas e o ponto no feedback.
O [ensaio de intensidade](evals/plano-motion-intenso-2026-11-06.md) explora esse
pedido sem copiar o v2 ou fixar estilo universal. A solicitação não renova
automaticamente orçamento; novas chamadas dependem do plano de custos da rodada.

## Nova peça com biblioteca e skill própria disponível — 06/11/2026

A [rodada orientada pela biblioteca](evals/ensaio-motion-biblioteca-2026-11-06.md)
gerou MP4 e comparação com o v2 mínimo e a rodada anterior. Skill própria Reel
incluída; código adapta mecanismos de ponto/forma, câmera e percurso dos três
exemplos selecionados. Cena renderizada como recebida, sem ajustes manuais;
estimativa conservadora US$ 0,28714. Aceite criativo permanece com o titular.

## V2 é piso; nova direção pela biblioteca — 06/11/2026

O titular esclareceu que o v2 não deve virar molde. A [rodada preparada](evals/plano-motion-biblioteca-2026-11-06.md)
usa análise dos exemplos locais, código de três candidatos e a skill própria
de Reel, sem reaproveitar o roteiro da peça anterior. O relatório compara nova
peça, v2 mínimo e rodada anterior. Fontes originais selecionadas preservadas no
repositório próprio. O titular autorizou uma chamada e o envio do pacote, até
US$ 0,75 adicionais; geração em andamento, sem resultado criativo presumido.

## Preferência criativa permanece no v2 — 06/11/2026

O titular considerou a peça nova razoável, mas abaixo do salto esperado;
prefere a transformação contínua horizontal/vertical e formas/pontos do v2.
O novo render usou Canvas/Chromium/FFmpeg, skill externa como contexto e
adaptação parcial da biblioteca; as skills próprias por formato não entraram
nesse request. [Feedback e diagnóstico](evals/ensaio-motion-comando-2026-11-06.md).
Preservar os mecanismos aprovados antes de testar melhorias; não houve nova
geração ou autorização paga nesta análise.

## Reel novo gerado pelo comando — 06/11/2026

Após reposição de créditos e retry explicitamente autorizado, o comando
produziu o [MP4 novo e comparação](evals/ensaio-motion-comando-2026-11-06.md).
11,2 s, 720×1280, com áudio; estimativa desta geração US$ 0,3114475.
HTML/JS foram renderizados como recebidos, sem ajustes manuais. Há mecanismos
reais de máscara/varredura adaptados da biblioteca. Aceite criativo e comparação
com o v2 aguardam o titular; a feature do produto continua incompleta.

## Geração pelo comando bloqueada por saldo — 06/11/2026

A tentativa paga para entregar o Reel novo passou no preflight, mas recebeu
HTTP 429 `credit_balance_exhausted`, sem conteúdo/uso informado. Não houve MP4
novo nem retry; reserva e resposta foram preservadas. A continuação depende
do saldo ou de escolha explícita de outro modo de criação.
[Tentativa e evidências](evals/ensaio-motion-comando-2026-11-06.md).

## Ensaio rápido em um comando — 06/11/2026

O titular escolheu gerar o MP4 e avaliar somente o resultado final, dispensando
as aprovações intermediárias de cards/frames da skill neste ensaio. O comando
`make motion-eval` confere o cenário sem gasto; `EXECUTE=1 BUDGET_USD=0.75`
autoriza uma chamada e encadeia composição, render e comparação com custo/trace.
O primeiro cenário reaproveita Jev/transcrição da fixture fictícia; geração
arbitrária de cenários e integração do produto continuam pendentes.
Ver [execução do ensaio](evals/como-executar-ensaio-motion.md).

## Histórico: retomada centrada na qualidade criativa — 06/11/2026

O foco imediato é um Reel com a mesma mídia fictícia e o mesmo kit, tomando o
v2 como patamar mínimo. O ensaio usará a referência concreta e código real de
`cartaz-gritado`, `cartaz-risografia` e `diagrama-azul-marinho`, selecionado e
adaptado para uma direção coerente; isso não fixa estilo por negócio. Integração
WhatsApp/Instagram fica fora desta prova. Resposta bruta e intervenções terão
traces separados. [Plano da retomada](evals/plano-retomada-qualidade-motion-2026-11-06.md).

O executor privado reproduziu o MP4 WAAPI anterior com SHA-256 idêntico nesta
configuração local; é prova de reprodução, não nova criação ou produto pronto.
Foram importados 24 arquivos originais de fontes, em um snapshot de 30 arquivos,
para `../meu-braco-direito-motion-sources/snapshots/claude-video-2026-11-05`,
com verificação offline e avisos MIT. Sem commit/push; privacidade remota não
verificada. Não é espelho completo, backup remoto ou pacote de dependências.
Fontes tipográficas e dependências externas ainda exigem tratamento próprio.
O titular autorizou duas chamadas, até US$ 1,50 adicionais, e o envio do pacote
local ao provedor. A primeira concluiu em 236,653 s, com estimativa de
US$ 0,2397635, sem fatura conferida. Cinco cards estão capturados e aguardam
aceite; a segunda chamada ainda não ocorreu e depende dessa aprovação.
Nenhum vídeo novo foi gerado. Detalhes e arquivos no plano da retomada.

## Rodada 1c rejeitada criativamente — 06/11/2026

O titular considerou Reel/story simples demais e carrossel praticamente estático,
com forte regressão frente ao Reel v2. A rodada não é base criativa aprovada.
A direção v2 aprovada não entrou efetivamente nos novos inputs; as referências
foram enviadas vazias. Revisar o caminho criativo e a fidelidade do compilador
antes de avançar essa saída na integração. CI técnico continua separado;
descrições e normalização de contrato não resolvem qualidade. Novas chamadas
pagas permanecem dependentes de plano e autorização. [Diagnóstico](evals/ensaio-motion-v0-rodada-1c-2026-11-06.md).

## Ensaio 1c concluído nos provedores; montagem e revisão — 06/11/2026

As sete chamadas da continuação autorizada foram executadas: três Jev e uma
transcrição aceitas; três direções recebidas e rejeitadas pelo contrato local.
Uma cópia derivada recebeu dez correções técnicas, depois sete ajustes visuais
de tamanho de texto pelo agente. O MP4 de 11,2 s foi gerado e decodificado;
não é saída intocada do modelo nem peça aprovada. [Peça, trace e custo](evals/ensaio-motion-v0-rodada-1c-2026-11-06.md).

O titular autorizou explicitamente retomar story/carrossel após o bloqueio
da revisão automática. A chamada final também passou pela revisão automática,
informando a nova rejeição do story. Story foi montado com sete correções locais;
carrossel foi montado com nove, preservando as respostas rejeitadas. Seus três
MP4s 1080×1350 têm 6 s cada e passaram na decodificação; o movimento é discreto.
Estimativa acumulada incluindo 1b: US$ 0,263073; reservas conservadoras
US$ 1,55, dentro do teto US$ 1,60. Nenhuma chamada foi repetida.

Após encerrar os efeitos pagos, o contrato passou a descrever unidades de fonte,
tempos relativos, sequência completa de keyframes e regras de áudio nas entradas
do modelo. A validação integral dessa fatia foi interrompida a pedido do titular
(saída 143), sem resultado final. O esclarecimento não
garante uma saída válida: as respostas recebidas não concluíram o fluxo automático.
Geração/revisão/download integrados e aceite criativo continuam pendentes.

## Interpretação sem candidatos — 05/11/2026

A [rodada 1b autorizada](evals/ensaio-motion-v0-rodada-1b-2026-11-05.md) parou
na primeira chamada: Jev reconheceu pedido/Reel, mas a confiança na escolha de
item foi 0,46, abaixo de 0,50, embora não houvesse candidatos selecionáveis.
Reserva de US$ 0,01 preservada; estimativa US$ 0,000035. Sem outras chamadas ou
peças novas. O adapter foi corrigido para omitir somente essa pergunta quando
a lista é vazia, mantendo os outros controles. Conferido na retomada de
06/11/2026: o CI integral terminou aprovado, com 5.044 testes Python e 62 Node,
sem pulados e com cobertura de 100%. Isso não resolve a admissão durável sem
item no produto.

## Contexto de direção e áudio — terceiro bloco, 05/11/2026

O catálogo próprio agora preserva três fichas com versão, hash e atribuições,
sem escolher estilo por segmento. O builder puro reúne kit, fatos, referências,
skill e todas as fichas para a futura escolha por pedido. Quadros e transcrição
somente aparecem quando fornecidos; hashes não substituem anexos e texto não
prova alinhamento temporal. Nenhum provedor foi chamado por essa preparação.

A composição também gera planos de áudio por página, com fontes verificadas,
cortes, deslocamentos, ganho e fades. Um protótipo isolado executou esse plano
com [sinais sintéticos](evals/ensaio-composicao-audio-sintetico-2026-11-05.md)
e verificou sincronismo e variante silenciosa; isso não
comprova fala humana ou qualidade criativa. O renderer do produto ainda não
executa áudio. O CI integral do terceiro bloco passou: 5.042 testes Python, sem pulados,
e 62 Node, com cobertura de 100%. Continuam pendentes direção por modelo, renderer empacotado, persistência,
revisão/download e backup independente das fontes.

O executor privado do ensaio gerou e decodificou cinco MP4s sintéticos nos três
formatos antes da chamada real. A [rodada criativa 1b](evals/ensaio-motion-v0-rodada-1b-2026-11-05.md)
foi autorizada e interrompida conforme o registro acima. A
[continuação 1c](evals/plano-motion-v0-rodada-1c-2026-11-05.md) está preparada,
e foi autorizada em 06/11/2026, preservando o teto global e a reserva anterior. Isso não
habilita o produto.

## Composição parametrizada — segundo bloco, 05/11/2026

O contrato evoluiu para `motion-direction-v2`, ainda sem API pública. O serviço
`motion_composition` revalida o documento, vincula skill/kit/estilo/fontes/mídia
a snapshots fornecidos pelo chamador confiável e gera cenas para o compilador
próprio. Texto vira conteúdo do DOM; geometria, keyframes, tipografia e fades
são dados limitados. Os perfis de render ficam separados da direção. O titular
confirmou carrossel 4:5; Reel/story seguem 9:16.
Os 148 testes Python dirigidos e 62 testes Node passaram com cobertura integral
dos respectivos módulos. O CI agora inclui Node 24.18.0 e exige 100% de linhas,
ramos e funções do compilador. O CI completo deste segundo bloco passou:
4.987 testes Python, sem pulados, e 62 Node, com cobertura de 100%.
Isso não gera MP4: driver, áudio mixado, isolamento de produção, persistência,
seleção de estilo por modelo e jornada de revisão continuam pendentes.

## Implementação incremental de motion — 05/11/2026

As três skills próprias agora têm snapshots e hashes em `app/assets/motion_skills`,
com carregador separado do fluxo de imagens. O contrato em `app/schemas/motion.py`
valida Reel, story em vídeo e carrossel, fontes por UUID, cortes, duração,
movimento declarativo, transições, áudio e legendas opcionais. O adapter Jev
reconhece esses formatos quando explicitamente elegíveis, mas a jornada atual
continua oferecendo imagem: essas fatias não habilitam edição no produto.
`motion_media` inspeciona uma gravação e extrai áudio localmente quando presente;
metadados não comprovam que todos os quadros decodificam ou têm a duração alegada.
A amostra técnica de `claude-video` está em `vendor/motion_sources`, com licenças,
manifesto, hashes e verificador de arquivo/restauração. Dependências, backup remoto,
render, transcrição alinhada, persistência e jornada integrada seguem pendentes.
O CI desse primeiro bloco passou: 4.913 testes, 2 casos de binários pulados e
100% de linhas/ramos. Esses dois casos foram exercitados com binários locais nos
testes dirigidos; o segundo CI os inclui no PATH. Nenhuma chamada paga.

O [ensaio de Reel sem GSAP](evals/ensaio-reel-waapi-2026-11-05.md) adaptou a
direção v2 com material fictício, sem chamadas novas; arquivo e som foram
verificados tecnicamente. O titular aprovou avançar com essa base técnica,
sem fixar o estilo dos demais casos nem homologar produção.
O aceite da peça ainda precisa de [contrato separado de postagem](design/revisao-peca-sem-postagem-2026-11-05.md):
a decisão legada de conteúdo agenda publicação simulada. A web recebeu somente
documentação nesta rodada; não se reaproveitou essa decisão como aceite isolado.

## Escopo confirmado por entrevista — 05/11/2026

A edição recebe inicialmente uma gravação do cliente por pedido, com até
60 segundos de entrada e até 60 segundos no vídeo final. A prioridade revisada
é concluir geração, prévia, ajustes, aprovação da peça e download. Viabilidade
e integração de postagem no Instagram ficam para fase posterior e não bloqueiam
esta entrega de geração. A integração dos contratos e do processamento ainda
precisa ser implementada e comprovada. Carrossel: 3–5
páginas, 5–8 segundos por MP4, preservando as demais páginas quando uma for
ajustada; alterações nelas exigem confirmação prévia. O estilo é escolhido a
cada pedido, preservando o kit, sem preferência fixa por negócio. O arquivo de
entrada tem teto de 50 MiB; excesso de tamanho ou duração pede versão menor,
sem corte automático. Franquias/preços seguem a medição já prevista. Ver
[decisões](DECISIONS.md).

## Início da v0 de conteúdo com motion — 05/11/2026

A [matriz inicial e os casos fictícios](design/v0-motion-etapa-0-formatos-e-casos.md)
registram o estado dos formatos e as lacunas de Reel, story e carrossel. O
[inventário da claude-video](design/inventario-claude-video-2026-11-05.md)
identifica fontes e direitos a verificar; preservação independente e
empacotamento ainda não foram realizados. A primeira correção de imagem rejeita
um padrão específico de instrução interna de revisão vazada em texto público;
não garante qualidade de toda legenda. Ensaios adicionais, integração audiovisual
e avaliação criativa permanecem pendentes, sem novas chamadas pagas nesta etapa.
O CI inicialmente interrompido foi concluído nos blocos registrados acima;
a guarda de copy passou junto da suíte integral.

O titular solicitou preservar cópias próprias versionadas das fontes externas e empacotar as dependências do produto, com backups, para não depender da continuidade dos repositórios originais. A [estratégia de preservação](design/plano-v0-imagens-video-motion-2026-11-05.md#cópias-próprias-e-independência-dos-repositórios-externos) é planejamento; espelhos e backups ainda não foram criados.

A integração reutiliza e adapta fontes permitidas; o catálogo próprio já preserva atribuições e a amostra original está versionável localmente. A jornada completa e o empacotamento seguem pendentes; detalhes no [plano](design/plano-v0-imagens-video-motion-2026-11-05.md#integração-concreta-da-claude-video).

## Plano da v0 de imagens, vídeo e motion — 05/11/2026

O titular pediu um plano completo para concluir a v0 com imagens de feed/story,
edição de vídeo enviado para Reel/story e carrossel com motion. O [plano de
integração](design/plano-v0-imagens-video-motion-2026-11-05.md) separa pesquisa,
ensaios rápidos e implementação em fatias; é proposta de desenvolvimento, não
capacidade já entregue. O estilo é escolhido pelo sistema e adaptado ao negócio.

## Ensaio de motion com modelos reais — 05/11/2026

O titular autorizou chamadas pagas naquela rodada. O [ensaio direto](evals/ensaio-motion-referencia-2026-11-05.md) gerou um carrossel e duas direções de Reel, com trace completo; Jev pediu esclarecimento, transcrição errou um trecho e a segunda direção precisou de correção técnica antes do render. Reservas US$ 0,78; uso estimado ajustado US$ 0,147533, sujeito à fatura. O titular preferiu o Reel v2; revisão completa de som/movimento, homologação e aprovação de publicação permanecem pendentes. Esse orçamento não autoriza nova rodada.

## Proposta de biblioteca de estilos de motion — 05/11/2026

O titular propôs estilos próprios internos, escolhidos automaticamente pelo sistema conforme o negócio e o pedido, sem exigir que o cliente escolha. A [proposta](design/biblioteca-estilos-motion-2026-11-05.md) ainda precisa de protótipo e avaliação; não existe integração implementada.

A skill `claude-video` foi instalada no Codex e sua galeria de 21 estilos foi aberta localmente como fonte de estudo; condições e limites constam no [estudo](design/estudo-claude-video-2026-11-05.md). Não integra automaticamente o produto.

## Próxima pesquisa: vídeo e motion, 04/11/2026

Em 05/11/2026 o titular esclareceu o fluxo: o cliente não seleciona imagens do acervo; pode enviar uma imagem própria e, para editar vídeo, envia o vídeo. O acervo não é obrigatório na edição de vídeo. Dois ensaios locais de HyperFrames foram solicitados; detalhes no [estudo](design/estudo-hyperframes-motion-design-2026-11-04.md).

A skill adicional indicada foi analisada em [claude-video](design/estudo-claude-video-2026-11-05.md); os [ensaios diretos](evals/plano-hyperframes-2026-11-05.md) usam vídeo e imagem simulados como anexos.

As [prévias HyperFrames](evals/ensaio-hyperframes-2026-11-05.md) foram montadas com direção da IA desta sessão e Jev simulado, sem APIs pagas; aguardam revisão. A execução opcional com modelos externos e transcrição real requer orçamento próprio.

O [estudo HyperFrames e motion design](design/estudo-hyperframes-motion-design-2026-11-04.md) recomenda testar uma composição criada por agente e renderizada com HyperFrames, orientada por técnicas de motion da Howseen. É análise, sem integração ou teste novo; referência anterior de orçamento não autoriza nova rodada.

O titular rejeitou as prévias de motion por falta de áudio, cortes, transições, efeitos e legendas dinâmicas. O [novo ensaio direto](evals/ensaio-motion-valido-2026-11-04.md) produziu vídeo e carrossel para revisão, com reservas de US$ 0,32 e custo estimado de US$ 0,019071; o Jev real pediu esclarecimento e a direção de motion é experimental, não integrada.

Uma prévia de vídeo e um carrossel de três páginas foram montados localmente, sem chamadas pagas e com Jev simulado. A avaliação visual pelo titular e a integração estão pendentes; as prévias não exercitam referências externas nem fala. Ver [relatório](evals/ensaio-video-motion-2026-11-04.md).

O titular quer edição criativa por IA para vídeo de feed/Reel e story, além de carrossel com motion e um MP4 em loop por página. A IA decide cortes, ritmo, tipografia, áudio e movimento conforme caso, kit, acervo e referências; FFmpeg pode executar a montagem técnica. O titular escolheu até 60 segundos por vídeo final e testes separados de vídeo gravado e carrossel. A entrevista posterior definiu uma gravação de até 60 segundos e 50 MiB por pedido; limites comerciais seguem pendentes. Foram criadas três skills iniciais para avaliação; não estão integradas à plataforma. Ver [estudo](design/estudo-video-motion-2026-11-04.md).

## Procedimento vigente para ensaios rápidos de qualidade

O titular pediu que próximas avaliações criativas usem o mesmo ensaio direto e
rápido: mensagem WhatsApp simulada, interpretação Jev identificada como real ou
simulada, inputs/outputs editoriais e visuais e apresentação das peças. Não
criar banco separado nem montar o sistema completo apenas para esse objetivo.
Ver [procedimento](design/ensaios-rapidos-qualidade.md), inclusive orçamento,
operações incertas e limites de evidência. Testes de banco/integração/CI continuam
exigindo banco próprio `_test` e roles restritas. As seções datadas abaixo são
históricas quando descrevem preparativos anteriores.

Dois pares foram gerados no ensaio direto da BL04.3, com Jev e modelos reais. [Compare as peças](evals/bl043-reference-quality-2026-11-04.md#resultado-do-ensaio-direto--04112026); revisão do titular e correções continuam pendentes. Reservas US$ 1,52; estimativa US$ 0,216691, não fatura.

O titular pediu um ensaio direto e rápido, sem percorrer o sistema completo: mensagem fictícia, resposta Jev, inputs editoriais/visuais e peças com/sem padrões. O [plano atualizado](evals/bl043-reference-quality-2026-11-04.md) substituiu a preparação anterior para aquela avaliação exploratória, executada sob teto de US$ 2 em reservas. Essa autorização histórica não cobre novas rodadas.

## BL04.3 — preparação do ensaio, 04/11/2026

Registro histórico anterior à execução; não representa a próxima ação vigente.

Inventário inicial e plano pareado preliminar em [avaliação de referências](evals/bl043-reference-quality-2026-11-04.md). A referência manual tem análise parcial e a sugerida permanece indisponível; a conferência individual contra evidências está pendente. O controle exige mecanismo de avaliação que preserve snapshot e revalidação, ainda não preparado. O titular escolheu dois pares do negócio fictício do piloto, reservas de até US$ 2 incluindo refações, aceitando risco de cobrança maior, e informará sua revisão visual da referência pública; nenhuma geração paga ou aceite ocorreu. Os tetos anteriores não autorizam a rodada.

## Próxima retomada — BL04.3, 04/11/2026

Registro histórico: a rodada descrita abaixo foi executada posteriormente,
conforme o relatório do ensaio. Restam avaliação completa e correções.

Continuar a avaliação de qualidade das peças com kit, acervo, skills e referências.
A feature de referências está implementada e validada localmente; a nova rodada
de peças com seus aprendizados ainda não foi executada. O
[SDD ativo detalha os quatro passos](phases/BL04-context-and-ai-production.md#quatro-passos-da-avaliação):
conferir aprendizados, comparar com/sem referências, avaliar com o titular e
corrigir/repetir medindo custo por peça aceita. Começar pelo inventário e plano
do ensaio. Casos, quantidade e orçamento devem ser preparados para entrevista;
não reutilizar automaticamente tetos históricos nem refazer a descoberta.
O ponto de retomada inclui evidências anteriores, limites e instruções para o
próximo chat, sem depender da conversa. Preservar as alterações Git existentes.

## Referências — estado da integração em 04/11/2026

No ajuste de interface confirmado pelo titular, a origem por endereço mostra
os campos de **Endereço do negócio** somente para leitura. Sem cadastro salvo,
é necessário preenchê-lo antes de salvar essa origem; alterar o cadastro atualiza
os campos exibidos, mas não salva preferências de pesquisa automaticamente.
Referências de outras regiões continuam podendo ser informadas por @ em
**Perfis que inspiram seu negócio**. A origem pelo dispositivo permanece disponível.

O aviso de busca indisponível reflete `discovery_available=false`, calculado pela
prontidão operacional da API. Na configuração local consultada, as credenciais
Google, Apify e Jev estão presentes, mas as flags de execução estão desligadas e
a configuração complementar do piloto não está carregada. O ensaio anterior usou
processos temporários configurados para esse fim. Esse aviso não representa
ausência de endereço nem bloqueio semestral; a alteração de interface não ativa
serviços pagos. A avaliação BL04.3 permanece um gate de qualidade pendente; a
frente ativa atual é o ciclo de revisão de Reel descrito no início deste documento.

A árvore local reúne descoberta Google com custos, classificação Jev, contatos
Instagram pelo Apify, seleção compartilhada, interface de pesquisa, análise de
publicações e uso dos padrões na criação editorial/visual. As revisões 0108–0110
acrescentam associação versionada, agenda semestral a partir do aceite, ledger
por amostra e snapshot imutável da proposta. A análise guarda padrões próprios;
publicações e imagens permanecem em memória. Eventos aguardam configuração
quando a execução está desligada.

O CI combinado passou em 4.734 testes com 100% de linhas e ramos, Ruff e mypy.
O piloto fictício autorizado de US$ 5 foi executado e comprometeu US$ 0,455502,
incluindo reservas Google/Jev ainda não liquidadas. Isso não equivale a avaliar
a qualidade comercial de peças geradas. O banco da aplicação foi atualizado de
0105 para 0111 após backups privados verificados; a API aberta antes dessas
migrações precisa de reinício. Este estado substitui as pendências de
implementação de referências nos registros datados abaixo.

O ensaio real encontrou um parser excessivamente restrito para componentes
opcionais de endereço do Google. A [correção do contrato](design/google-places-address-components.md)
passou em 160 testes com cobertura integral dos três módulos verificados. No
novo caso fictício, os 20 resultados foram aceitos e o Jev salvou três destaques
distintos. Os dez contatos foram publicados e uma referência foi confirmada.
A primeira análise real terminou indisponível pelo filtro inicial de autoria/formato.
Depois do ensaio, o titular confirmou autoria direta apenas e autorizou capa e
legenda de vídeos/Reels. O filtro foi atualizado, incluindo capas de itens de
vídeo em carrosséis, com estado parcial explícito e sem download do vídeo.
A alteração passou em 164 unitários/100% do adapter, cinco integrações e no CI
integral acima. A interface explica autoria direta e capa/legenda; dez testes
dirigidos/100% do componente, TypeScript e Prettier passaram. O ensaio também
expôs recibos Apify preliminares: a espera por contabilização está implementada,
e a revisão auditável 0111 foi aplicada e reconciliou os onze recibos sem alterar
o teto. A interface passou em 508 testes com cobertura integral, TypeScript,
build e navegação em Chromium. Uma referência manual pública no negócio
fictício foi analisada: 11 publicações, 40 imagens e nove padrões disponíveis
no contexto de geração, com resultado parcial explícito. As decisões de conteúdo
foram resolvidas; fórmula em calibração e orçamento mensal comercial
foram adiados pelo titular. Flags persistentes seguem desligadas. Ver o
[relatório do piloto](evals/reference-feature-pilot-2026-11-04.md) e
[consolidação de custos](design/apify-cost-settlement.md).

Atualizado em **30/10/2026**, após a decisão de gerar a peça integralmente com
briefing, skill e referências pertinentes, e descontinuar o acabamento antigo.
O repositório separado de skills agora tem versões iniciais de briefing para feed
e story e casos fictícios; um ensaio exploratório comparou saídas de agentes com
uma sonda isolada do baseline, sem controle suficiente para demonstrar ganho.
A aplicação seleciona a skill versionada em briefings de feed/story e a usa na
direção da peça integral em desenvolvimento/teste. O efeito visual pago segue
desligado por padrão; homologação e avaliação real do novo caminho estão
pendentes. Decisões de produto e pendências ficam em
[DECISIONS](DECISIONS.md); contratos no [SDD](SDD.md); sequência no
[índice de fases](phases/README.md) e na [trilha BL](phases/BL-brand-library.md).
As versões anteriores foram [preservadas integralmente](history/2026-10-28-pre-documentation-reconciliation/index.md).
Uma entrega local não equivale a uma capacidade comercial homologada.

Em 03/11 o banco de desenvolvimento foi atualizado da revisão 0059 à 0072,
após backup privado com leitura integral verificada, para acompanhar o código
local. Em seguida, a revisão 0073 foi aplicada após outro backup verificado por
leitura. Posteriormente, o banco foi atualizado à revisão 0099 após novo backup
privado com leitura integral verificada; a API iniciada antes dela precisa de
reinício para reconhecer a revisão. Nenhum backup foi restaurado em teste.

Em 30/10, após ensaios diretos com três negócios fictícios, a fatia local
passou a distinguir números de direção de arte de alegações, verificar artefatos
internos na copy e usar um canal comercial opcional confirmado pelo titular.
Esse destino é configurado em Sobre meu negócio e versionado com o contexto;
não se presume que o telefone de identificação seja um canal comercial. A
validação é limitada e a peça continua sujeita a revisão humana.

O cliente pode registrar palavras que descrevem seu negócio e características
gerais no contexto versionado. A interface removeu os formulários de fatos
livres e promoções; fatos antigos do contexto não alimentam novas peças e novos
snapshots editoriais ignoram promoções legadas do catálogo. Snapshots antigos
mantêm sua política e registros físicos históricos não foram purgados. O fluxo
de ofertas e horários pelo WhatsApp e pelas revisões continua pendente.

Os ensaios usaram personalizações diferentes do mesmo kit demonstrativo. O kit
[fictício Ateliê Aurora](evals/kit-atelier-aurora-v1/README.md) foi criado como
fixture independente de QA, com manifesto e exemplos próprios; ainda não integra
o catálogo ou o executor de geração.
A indicação manual, descoberta automática e seleção das sugestões estão
implementadas localmente. A indicação sozinha não comprova análise do perfil;
apenas resultados derivados persistidos alimentam os padrões usados na criação.

A pesquisa pretendida é somente por raio local, a partir de endereço manual ou
posição confirmada do dispositivo; não há nova busca para todo o Brasil. A web
oferece raios de 5, 20 e 50 km; valores anteriores de 1–50 km e preferências
nacionais antigas são preservados até substituição explícita. A posição é
apresentada sem latitude/longitude e exige confirmação. A preferência é versionada
com o contexto e não é enviada aos modelos editorial ou visual nesta fatia.
O serviço também restringe novas escolhas a esses três raios locais. Preferência
legada igual ou omitida é preservada; `null` explícito a remove. Replays e
alterações pendentes já admitidas mantêm a compatibilidade anterior.

A busca começa no raio pedido, uma por raio por ciclo, com até dez candidatos,
sem garantia de 30 negócios únicos; falha comprovada não consome a tentativa.
Em 04/11 foi definida a exceção de resultado Google vazio: ampliar de 5 para
20 e depois 50 km; todos vazios permitem tentar novamente sem iniciar seis meses. Em 03/11, o titular esclareceu que até dez candidatos serão
exibidos, com até três recomendações do Jev destacadas com critérios e nota; o cliente
poderá escolher de uma a três entre os exibidos, combinando raios. A primeira
confirmação inicia um prazo de seis meses; cada raio pode ser pesquisado uma vez
no ciclo, inclusive depois da confirmação, e todos voltam a ficar disponíveis no
fim do prazo original. Mudar endereço ou segmento não libera raio já pesquisado;
trocar referências não renova o prazo e a seleção permanece até outra confirmação;
referências ainda selecionadas de ciclos anteriores podem ser combinadas com as novas.
Cada nova pesquisa formará novamente até dez resultados a partir dos negócios
retornados pelo Google, com nota mais recente e três destaques do Jev. A nota de
cada pesquisa permanece no histórico. Se uma referência escolhida ficar fora dos
dez, o cliente decidirá se a mantém; o fake ainda não implementa essa jornada.
@ manuais são adicionais. O titular quer guardar os até dez negócios apresentados
por pesquisa, com Place ID, nota própria e perfis disponíveis. O titular confirmou
que apenas o Place ID será guardado dentre os dados Google; estrelas e contagem
servem de entrada transitória para a nota própria, que poderá ser armazenada junto
à associação dos perfis do Apify. O nome exibido virá do Apify quando disponível;
caso contrário, mostrar o perfil ou outro identificador disponível. O Apify pode
consultar negócios novos de outro raio, mas não repetir
consulta bem-sucedida aos já encontrados durante o ciclo; uma tentativa que
falhou sem retornar o perfil pode ser refeita.
Na primeira versão, são considerados perfis de Instagram; um único perfil
retornado pelo Apify será usado e analisado automaticamente, sem confirmação do
cliente. Com vários perfis, usar o principal indicado ou, se não houver, o primeiro
retornado; se estiverem incorretos, o cliente poderá informar outro @. O titular deseja
analisar via Apify até 20 publicações recentes do feed por perfil, incluindo
imagens e legendas públicas acessíveis, guardar apenas padrões extraídos e
informar quando a análise for parcial, atualizando automaticamente os padrões a
cada seis meses. Jev deverá destacar até três negócios considerando
semelhança e nota, com critérios e nota exibidos; semelhança incerta não entra nas
sugestões. Não há nota mínima de corte.
A infraestrutura privada `fake`, desligada por padrão, usa fixtures anônimas e
Temporal e permite pesquisar raios ainda não usados após a confirmação, no prazo
original. Ela exercita seleção entre raios, compensação de falha comprovada e
reconciliação de autor revogado. Ela não consulta fontes externas nem apresenta candidatos
reais. Busca real, verificação de perfis, aceite de candidatas reais e uso dessas
referências no produto continuam pendentes. Os adapters Google Places com tipos
principais múltiplos, Geocoding, consulta de perfil e enriquecimento por Place ID
via Apify, e mapeamento de tipos com Jev estão isolados e desativados, sem
guardião de custos integrado a efeitos reais; a origem manual exige localização
confiável, com confirmação apenas se houver dúvida. O resultado de perfil não
encontrado sem fonte comprovada é inconclusivo. O perfil retornado pelo Apify
será utilizado conforme a regra aprovada, após vincular a resposta à consulta
autorizada; a análise de publicações ainda não está conectada. O titular não
exige uma etapa de exclusão dos dados retidos pelo fornecedor.
Em desenvolvimento, uma base privada separada para buscas e resultados reais
foi preparada com RLS e somente leitura, sem writer nem rota. A requisição Places
já entrega seus parâmetros exatos à futura guarda, e existe adapter de
semelhança Jev restrito a HTTP simulado; nenhum deles liga fornecedores reais.
O ledger comum, limite cumulativo do ensaio e fence do executor foram exercitados
para Google com HTTP simulado. Commit sanitizado de resultado, Apify/Jev no mesmo
teto e reconciliação continuam em implementação antes da integração externa.
Um adapter de feed Instagram aceita apenas HTTP simulado e prepara até 20 posts
de imagem/carrossel, com legenda em memória e estado de análise parcial. Não
baixa imagens nem grava publicações na plataforma.
O titular escolheu testar pontuação de reputação de 0 a 10, combinando nota e
quantidade, sem armazenar os campos originais. A regra anterior de não pontuar
com menos de dez avaliações foi revogada: a partir de uma avaliação pode haver
nota; sem média ou avaliações disponíveis, não há pontuação e o negócio não é
incluído nas sugestões. Duas fórmulas foram exercitadas apenas com dados
fictícios. O titular escolheu continuar testando a segunda, que penaliza pouca
evidência sem elevar a média; seu peso continua provisório. O titular confirmou
em 03/11 que a fórmula seguirá em teste e calibração. A descoberta fake
aplica o filtro de semelhança definido na fixture e salva a pontuação integral
e as versões da fórmula e da fixture por pesquisa; leituras posteriores usam o
snapshot e o ordenam sem arredondar. Não há ranking real ou avaliação real pelo Jev. Ver
[avaliação](evals/reference-reputation-eval-2026-10-31.md).
Jev deverá primeiro eliminar candidatos inadequados na busca real; a nota própria
e a associação dos perfis ainda não são persistidas para negócios reais.
Uma política financeira compartilhada e versionada e o tratamento de efeitos
fictícios por outbox/Temporal foram testados isoladamente: limites por pesquisa,
fornecedor e mês em UTC, sem política ativa por padrão. Retornos incertos
mantêm reserva, sem liquidar por valor informado sem evidência. Integração de
efeitos reais, identidade/hash reais, conciliação da fatura e rotação de chave
permanecem pendentes; essa fundação não autoriza chamadas externas. A chave
HMAC fictícia ainda não tem versão: trocá-la com trabalho pendente interrompe
o processamento até restaurar a chave anterior, mantendo qualquer reserva.
Uma [prova pontual do Google Nearby](evals/google-nearby-order-probe-2026-10-30.md)
observou que a ordem `POPULARITY` não corresponde simplesmente a ordenar por
nota e contagem na amostra. A reserva cumulativa das consultas Places foi de
US$ 0,280, não a fatura; o registro não salvou nomes ou respostas brutas.

## Produto

Pequenos negócios enviam texto, foto, áudio ou vídeo pelo WhatsApp. A plataforma
usa os fatos confirmados, o kit e os materiais do próprio negócio para preparar
conteúdo, pedir aprovação específica, publicar nos canais habilitados e mostrar
resultados observáveis. Também deverá propor conteúdo sem envio novo, dentro de
uma cadência aceita e da franquia; essa proatividade ainda não está implementada.
O cliente não precisa escrever prompt ou operar um editor.

A web complementa identidade, contratação, canal, contexto, acervo, kits e revisão.
A vitrine pública usa exemplos fictícios já produzidos; uma visita não chama IA
nem conecta contas sociais. A escolha do kit não aprova publicação.

Uma conta de cliente e uma organização por negócio, com cobrança e aceite
próprios. O runtime garante no máximo um negócio por organização; memberships e
seleção legadas são preservadas. Staff é independente de cadastro de negócio.
Um número WhatsApp de cliente ativo por negócio na primeira versão.

## Decisões atuais sobre IA, materiais e prévias

- **Aceite único entregue localmente (C01):** em Plano e acesso, antes do
  checkout, o cliente concorda uma vez com IA para interpretação, texto, imagem
  e transcrição. Contas existentes recebem o mesmo passo. Não há permissões por
  fornecedor em WhatsApp ou Informações e preferências. Credenciais, plano,
  orçamento e versões são controles internos. Aceitar não confirma pagamento.
- **Envios WhatsApp preservados (C04/C05):** materiais associados ficam sem
  expiração automática; histórico e API não oferecem sua exclusão. A troca de
  número não interrompe material já associado; a entrega simulada usa o novo
  vínculo. Envio real de candidata ainda falta. Eventos técnicos não atribuídos
  e uploads órfãos têm limpeza separada.
- **Acervo:** fotos desatualizadas de item/espaço podem ser removidas. A cópia
  explícita de uma foto do WhatsApp cria outro objeto; preservar o envio não
  cria uma ficha de produto, fato confirmado, memória pesquisável ou skill.
- **Mudanças durante criação (C06/C07):** aguardar processos iniciados, cancelar
  a fila que não começou e impedir novos inícios até aplicar a mudança de kit,
  foto ou contexto. A prévia anterior continua para revisão, identificada como
  anterior à alteração. Os caminhos `visual_fake` e `visual_ai` compartilham
  essa coordenação dos escritores atuais.
- **Continuidade e preservação (C08/C09):** a criação `visual_fake` ou `visual_ai` já admitida
  tem prova durável para concluir após o vencimento financeiro e permitir revisão
  privada. Bloqueio financeiro explícito e revogação de patrocínio continuam
  distintos do vencimento. Novas criações e publicação exigem plano vigente.
  Prévias concluídas e sua proveniência saem da limpeza automática por prazo;
  tentativas visuais iniciadas sem resultado resolvido também são conservadas.
- **Autor sem acesso (C10), implementação de suporte adiada em 29/10:** outro
  owner não pode substituir nem descartar sua alteração pendente. Essa proteção
  permanece; a recuperação staff fica para evolução de gestão de acesso/suporte.
  A exceção continua bloqueada e não impede fechar a fatia simulada validada.

A admissão visual verifica proposta, fontes, usuário/membership, aceite e plano
sob locks na ordem proposta → visual → comercial, antes de gravar o run. A reserva
financeira continua em outra transação/role: falha ou confirmação perdida mantém
o run bloqueante e não libera repetição. A recuperação local pode encerrar uma
tentativa obsoleta/falhada somente após tornar a prévia terminal e comprovar,
sob locks correlator, ausência de tentativa e de reserva, inclusive não vinculada.
O commit confirmado precede a conclusão owner; confirmação perdida permite repetir
somente a reconciliação. Uma duplicata viva não derruba a criação original.
`DatabaseVisualEffectGuard` agora reúne admissão, fontes, reserva, claim única e
commit privado com prova owner e revalidação correlator. Roteiro aguarda runs em
transação separada proposta → visual; writers financeiros participam do comercial.
Troca de telefone não muda a identidade de fonte já atribuída. O protocolo dos
escritores atuais está no [desenho da guarda](design/BL04-effect-guard.md).
O modo persistido `visual_ai` agora liga essa guarda ao adapter OpenAI por um
runner e workflow próprios; os testes usam transporte HTTP simulado. A ativação
continua desligada por padrão. A parte 3 executou uma chamada real de imagem com
Jev, guarda, kit/logo e prévia privada, sob autorização delimitada; ver
[evidência](evals/bl042-first-product-image-2026-10-29.md).
C08 cobre `visual_fake` e `visual_ai`; o
renderer local legado ainda não recebe a mesma exceção de conclusão. `expires_at`
continua delimitando criação/aprovação, sem apagar uma prévia concluída. URL
assinada, validade factual e prazo de aprovação permanecem separados da preservação.
Revisão histórica não depende de manter a execução visual habilitada.

O prazo de exclusão após encerramento da conta foi explicitamente adiado para
essa fase; não implementar exclusão automática nesta etapa (P03). Vencimento do
plano não equivale a encerrar conta nem a perder membership.

## Estado implementado e limites

| Área | Existe localmente | Falta demonstrar ou entregar |
| --- | --- | --- |
| Fundação e identidade | FastAPI, PostgreSQL/RLS, auth própria, sessões, recuperação, e-mail HTML, onboarding, MFA/convites de staff | Homologação de operação e segurança em staging/produção. |
| Contratação | Stripe sandbox, webhook/jobs/reconciliação, patrocínio e aceite único versionado por negócio | Contratos comerciais definitivos, franquias e cenários externos restantes. Cadastro e retorno de checkout não ativam plano. |
| WhatsApp | Inbox assinada/cifrada, vínculo, correlação, processamento, transcrição configurável e preservação de materiais | Meta oficial, envio real de candidata e conversa completa ainda não homologados. |
| Contexto e texto | Fatos/preferências versionados, propostas/roteiros, adapter editorial, reservas/tokens e projeção administrativa restrita | Qualidade comercial, conversa com memória, pesquisa ampla e skills executáveis. |
| Skills de geração | Briefing com skill de feed/story selecionada e versionada; referências externas e seus padrões foram integrados localmente e exercitados em piloto. | Avaliação real de ganho, tratamento de múltiplos fatos e homologação permanecem pendentes. |
| BL01/BL02 | Vitrine fictícia de cafeteria, escolha/edição de kit e logo privado; kit/logo aplicados à primeira imagem real controlada | Kit `public_demo` não tem liberação comercial; fidelidade precisa de revisão. |
| BL03.1/BL03.2 | Catálogo/fotos privadas e uso seletivo de fontes na primeira imagem real controlada | Importação de cardápio é BL03.3 futura; qualidade/fidelidade do contexto aplicado ainda requer avaliação. |
| BL04 | Caminho `visual_ai`, Jev, guarda e adapter exercitados com uma imagem real de feed e prévia privada preservada | BL04.3: revisão de post/story, fidelidade e custo por peça aceita. Uma chamada não comprova qualidade, fatura ou margem. |
| F04/F06 | Prévias técnicas estáticas/vídeo, candidata, revisão e publicação simulada com versão/hash | Ajuste não regenera automaticamente; candidata WhatsApp e Instagram reais pendentes. |
| F08 | Compose, CI e workflow manual de deploy preparados | AWS/staging, recuperação coordenada, observabilidade operacional e capacidade não homologadas. |

**Histórico anterior à integração 0106–0111:** a implementação de referências tinha uma cadeia privada Google/Jev apenas com
provedores simulados, reservas e recuperação idempotente, além de contratos
preparatórios para resultados e aprendizados. Ainda faltam admissão da pesquisa
real, recomendação dos três destaques, Apify, publicação, análise e integração à
geração; nenhuma fase completa de referência real foi entregue nesta fatia.
A admissão por dispositivo e o carregamento privado da versão autorizada foram
testados, mas ainda não estão ligados a uma execução real.
O titular confirmou a combinação de semelhança e nota nos três destaques, o
desempate por semelhança na décima posição, os raios 5/20/50, a busca manual
após o prazo, a exclusão do próprio negócio e o compartilhamento entre titulares. A análise deverá considerar
todas as imagens acessíveis de carrosséis e aprender tom, temas, formatos e
elementos visuais; essas capacidades ainda não estão integradas ao produto.
Se o Jev não resolver o empate, prevalecerá a ordem Google; sua conclusão
estruturada de semelhança poderá ser armazenada para recuperação. Um perfil
recém-escolhido será analisado após confirmação e atualizado a cada seis meses.
O endereço e as coordenadas do próprio negócio permanecem no cadastro. A comparação
para excluí-lo possuía testes isolados, mas ainda não estava integrada à busca real.
O [estado posterior](#referências--estado-da-integração-em-04112026) registra a
integração local e o piloto; as pendências acima descrevem a fase anterior.

Os ensaios em [evals](evals/) são evidências datadas, não features ou aceites
comerciais. As imagens reais de IA de 27/10 e 28/10 foram geradas em ensaios
isolados, fora do worker do cliente. Não comprovam fidelidade, margem ou custo
mensal. Consultar perfil público não concede direitos sobre o material observado.
A [execução de 29/10](evals/bl042-first-product-image-2026-10-29.md) percorreu o
worker do produto e exportou o JPEG pela API autenticada e S3 privado. Meta de
entrada/prova de canal foram sintéticas e a entrega da candidata permaneceu
simulada; isso ainda não comprova conversa WhatsApp completa ou homologação.

## Jornada web vigente

| Área | Finalidade |
| --- | --- |
| Início | Resumo e orientações com estados reais do negócio. |
| Plano e acesso | Aceite único do serviço, assinatura, patrocínio e situação financeira. |
| WhatsApp | Telefone/SMS, vínculo e histórico preservado de envios como consulta secundária. |
| Sobre meu negócio | Informações e preferências, Produtos e serviços e Meu espaço. |
| Conteúdos | Acompanhar propostas/prévias e decisões disponíveis; simulações identificadas. |
| Kits visuais | Explorar, escolher e editar a direção visual. |

Organização/negócio ativos são compartilhados em memória; a autorização é
verificada na API/RLS. `/app/content` é a rota vigente; `/app/ideas` redireciona
para ela e `/app/guide` para Início. `/app/phone` é utilitária do WhatsApp.
`/app/editorial-lab` mantém os controles técnicos só no build DEV. O valor
histórico `posts_per_week` é preservado, sem campo manual de frequência.

## Sequência histórica de 30/10 e pendências preservadas

A frente ativa é o ciclo de revisão de Reel no início deste documento. As
etapas históricas abaixo mantêm seus gates próprios e não substituem essa ordem.

Em 30/10/2026 o proprietário direcionou a geração a construir um briefing com
pedido, fatos, kit, acervo pertinente, skill do formato e referências externas
aceitas quando existirem; pedir ao modelo a peça completa, conferir o resultado
e disponibilizar trace privado. A indicação manual e seu snapshot foram
implementados localmente, assim como descoberta e aceite de sugestões automáticas.
O proprietário decidiu descontinuar novas
gerações pelo acabamento antigo de fundo e layout fixo; registros anteriores
podem ser preservados sem gerar novas peças por esse caminho. A ideia posterior
de usar padrões/fontes das referências como sugestões editáveis para o kit
está registrada no [plano de referências](design/skills-e-referencias-editoriais.md).
O proprietário definiu que promoções, ofertas e horários para uma peça vêm do
pedido e de suas revisões no WhatsApp, sem cadastro desses fatos na interface.
Por exemplo, o pedido promocional de R$ 19,90 vale para a peça mesmo com preço
de catálogo de R$ 25; não se pergunta sobre a diferença nem se altera o catálogo.
Desconto percentual depende de preço de catálogo válido; dados ausentes ou
ambíguos pedem esclarecimento. Um campo simples de características gerais do
negócio permanece. O titular autorizou remover as informações antigas dessa
área sem preservar histórico. A mudança ainda não foi implementada: o fluxo
WhatsApp/Jev não extrai e vincula esses fatos integralmente. O código anterior
de promoções de catálogo continua para compatibilidade histórica; novos
snapshots editoriais as ignoram.

O novo caminho local de feed/story reúne briefing com skill, pedido, contexto,
kit, fotos pertinentes e logo; a referência visual demo do kit é enviada
separadamente. O modelo produz a peça inteira, sem overlay fixo. O trace fica
cifrado e acessível ao proprietário; aprovação por API requer conferência humana
dos itens e hash da imagem. O checklist ainda não existe no WhatsApp/web. O uso
real segue restrito a desenvolvimento/teste, desligado por padrão, sem prova de
qualidade comercial. Os ensaios diretos pagos de 30/10 ocorreram fora do worker
e antes das correções atuais. Previews antigas
concluídas ficam acessíveis; jobs antigos não são reexecutados.

Em 29/10, três negócios fictícios foram exercitados pelo fluxo local com Jev e
geração de imagem reais, produzindo seis prévias A/B. Todas omitiram o preço
confirmado solicitado; naquele ensaio a skill atuava só na imagem. A geração
integral posterior recebe texto natural com verificações de valores e origem,
sem fallback fixo. Essas verificações não provam verdade semântica. Ainda não há
interpretação estruturada que garanta que um pedido de preço seja obedecido;
o prompt solicita seu uso, mas a resposta pode omiti-lo. A validação com
seleção factual do produto e a avaliação do efeito editorial da skill
continuam pendentes.
[Evidência](evals/three-business-visual-ab-2026-10-29.md).

Um ensaio isolado de 29/10 gerou seis imagens com modelo editorial real: quatro
exibem preço; nas duas de manicure ele aparece só na legenda. Café e delivery
receberam copy artificial com “apresente”. Cada par compartilhou a copy; a skill
atuou só na imagem. O teste não percorreu seleção factual ou jornada completa e
não comprova qualidade comercial. [Resultado](evals/editorial-copy-visual-after-2026-10-29.md).

O primeiro ensaio autorizado de texto foi interrompido com resultado incerto;
custo desconhecido e hold mantido. Um segundo ensaio, visual e independente,
concluiu duas peças fictícias com e sem skill para revisão, sem comprovar ganho
geral ou execução pelo produto. [Evidência visual](evals/skills-visual-comparison-2026-10-29.md)
e [tentativa anterior](evals/skills-paired-attempt-2026-10-29.md).

No repositório `meu-braco-direito-skills`, as duas skills iniciais orientam
briefings de feed/story, sem gerar arquivo ou publicar. A validação estrutural e
dois exercícios independentes com dados fictícios passaram; não houve comparação
controlada com baseline, geração paga ou avaliação comercial. Um ensaio posterior
identificou ambiguidade não esclarecida em story; a instrução foi ajustada e uma
repetição independente fez a pergunta. Não prova qualidade geral. Seus casos e
protocolo preparam a próxima avaliação.

1. **Skills e geração:** estudar e estruturar skills para feed e story; comparar
   geração com e sem elas em casos fictícios e provedores simulados, integrando
   versões aprovadas ao produto. Kit, acervo e fatos do negócio são suas fontes.
2. **Referências externas:** permitir indicação de perfis pelo cliente e pesquisar
   automaticamente negócios semelhantes em destaque; avaliar fontes, métricas e
   uso de padrões sem copiar. Places é a fonte escolhida para estudar a busca
   inicial e Apify é previsto para enriquecimento de perfis; custos, cobertura e
   vinculação técnica ainda precisam ser verificados. Jev deve avaliar
   semelhança e eliminar candidatos inadequados antes da pontuação de reputação
   dos restantes, além de destacar até três recomendações entre os até dez
   candidatos exibidos, mostrando critérios e nota; não é fonte de dados nem acesso direto ao
   Instagram. Avaliações do estabelecimento não medem engajamento social.
3. **BL04.3:** revisar o feed produzido e completar post/story pelo produto com
   titular e fontes consentidas; medir fidelidade, texto, legibilidade, rejeições
   e custo por peça aceita, incluindo refações. Novas chamadas exigem autorização
   própria; a autorização delimitada de US$ 1 não ativa uso recorrente.
4. **BL05:** fechar WhatsApp como jornada principal de mensagem → prévia → ajuste
   → aprovação da peça → download, incluindo iniciativa sem mensagem e pausa.
5. **Piloto:** homologar o WhatsApp oficial, aplicar franquias F07 e operar staging,
   observabilidade e recuperação F08 para autoatendimento com cobrança. Publicação
   no Instagram fica para depois e não bloqueia esse piloto; o canal pendente não
   impede testes locais.
6. **Expansão:** BL03.3 importa cardápio como rascunho; BL06 amplia kits/nichos e
   catálogo/CDN. Avatar/voz e multicanal seguem fases próprias.

A [proposta por fases](design/skills-e-referencias-editoriais.md) detalha os
gates, a pesquisa automática e as decisões ainda abertas. A atualização
documental não autoriza gasto nem comprova os trabalhos ainda pendentes.

O runtime atual oferece foto/story; o escopo planejado de vídeo já prevê uma
gravação por pedido, até 60 segundos e 50 MiB, e saída até 60 segundos.
Franquias e preço de vídeo seguem pendentes. R$ 99/mês e teto total de R$ 50/cliente/mês orientam
medição, sem margem comprovada. Avatar/voz sintética ficam após o primeiro
piloto. HyperFrames/Remotion e outros estudos são candidatos, não integrações.
A aquisição por vídeos longos dos três sócios segue estratégia comercial; a
meta de 200 mil clientes orienta capacidade gradual, sem comprovação atual.

`visual_ai` exige `VISUAL_AI_MODE=openai`, `VISUAL_AI_EXECUTION_ENABLED=true`,
reserva positiva por tentativa, tetos mensal por tenant e agregado suficientes,
chaves de provedor/criptografia e enforcement do aceite único C01. Os nomes de
variáveis usam o prefixo `MEU_BRACO_DIREITO_`; o padrão é flag desligada e reserva
zero. A API usa apenas o pool owner; o worker exige seu pool correlator restrito.
O dispatcher usa ID estável por prévia e lease de 12 minutos, sem redispatch do
efeito visual incerto. A resolução automática do item exige a configuração Jev
existente, com credencial/orçamento próprios; correspondência lexical não a substitui.

## Arquitetura, validação e continuidade

Backend Python modular, FastAPI, PostgreSQL compartilhado/RLS, Temporal e S3;
React em `local-spark-web`. API, dispatchers e workers escalam separadamente.
Redis não é dependência ativa; não adicionar outro runner para os processos de
Temporal. Sem rede sob row lock e sem IO em workflows determinísticos.

A [análise da jornada WhatsApp e orquestração](design/arquitetura-jornada-whatsapp.md)
documenta processos, workflows e limites atuais, diferencia o percurso de uma
saga clássica e registra recomendações para discussão, sem decisão de separar
serviços ou repositórios.

Negócios/kits usam auditoria transacional; relay, tabelas e handlers antigos
ficam só para compatibilidade, sem novos recibos de CRUD. Auth é própria;
access token em memória e refresh HttpOnly. Staff/MFA não equivale a owner.
Os modelos atuais são configuração, não escolha comercial definitiva. Contexto
versionado não treina automaticamente modelos e tokens não são COGS monetário.

Evidência anterior de aplicação: 1.583 testes backend e complemento de 24 testes
com sete casos novos; cobertura final de 100% de linhas/branches. Web: 360 testes,
100% nos quatro critérios, build e três jornadas Chromium. Evidências datadas
no [CHANGELOG](CHANGELOG.md). A parte 1 passou em `make ci`: **1.829 testes**,
**100% de linhas e branches** (9.284 statements e 2.550 branches), Ruff/formatação
e mypy (149 módulos). PostgreSQL `_test` restrito e Temporal locais cobrem admissão,
continuidade, preservação, autoria, recuperação entre commits e confirmações
perdidas, tentativa tardia, orçamento concorrente e fontes kit/logo. Não houve chamada
paga, novos grants ou homologação externa. A guarda concreta também cobre roteiro,
relink por outro owner, acesso financeiro e prazo factual após locks. Web:
**365 testes e 100% nos quatro critérios**, build/formatação e três jornadas
Chromium (laboratório pendente, conteúdo e aceite).

A parte 2 acrescenta testes da API até `VisualGenerationWorkflow`, runner,
adapter real com transporte HTTP simulado, acabamento e revisão privada, com
PostgreSQL/Temporal locais. `make ci` aprovado: **1.914 testes**, **100% de
linhas e branches** (9.394 statements, 2.582 branches), Ruff/formatação e mypy
(151 módulos). Web: **375 testes**, **100% nas quatro métricas**, build/formatação
e **quatro jornadas Chromium** na árvore final (conteúdo local/IA, laboratório e
aceite). As contagens anteriores são evidências da parte 1. A migration 0059 foi
aplicada somente ao `_test`, sem migrar o banco da aplicação, chamar fornecedor
pago ou alterar grants naquela entrega.

A parte 3 concluiu uma imagem real de feed com `gpt-image-2.5-flare-2026-09-08`,
Jev real e acabamento determinístico do kit/logo, preservando candidata pendente
e publicação nula. Estimativa por uso: **US$ 0,029701**, incluindo duas
interpretações Jev; não é fatura. A reserva visual de **US$ 0,99** continua
`uncertain`, com custo efetivo desconhecido, e o run terminou. A primeira entrada
resultou em story e o wrapper bloqueou antes do HTTP de imagem; prova de zero
submissões permitiu reconciliar a reserva antiga em zero, preservando tentativa
e auditoria. Uma nova origem esclarecida gerou o feed sob a mesma autorização;
não houve edição manual de roteiro nem aprovação/publicação. A migration 0059
agora também foi aplicada ao banco local da aplicação para essa execução.
Flags persistentes seguem desligadas, sem novos grants ou código de produção.
`make lint types` aprovado (151 módulos) e **94 testes unitários dirigidos**
aprovados; código de produção inalterado. O `make ci` acima é da parte 2 e não
foi repetido nesta execução operacional. Com geração `disabled`, flag desligada
e limites zero, owner listou/baixou o mesmo hash; acesso anônimo retornou 401.
Os processos temporariamente habilitados foram encerrados. Uma imagem isolada
não substitui as provas C08/C09 da suíte ou a revisão humana de BL04.3.

Diretórios/remotos continuam `local-spark-platform` e `local-spark-web`, com marca
Meu Braço Direito, prefixo `MEU_BRACO_DIREITO_` e bancos renomeados conforme
[registro](product-rename.md). Operação em [operations](operations.md).
Atualizar PROJECT, SDD, fase e CHANGELOG em cada entrega; decisões novas entram
em [DECISIONS](DECISIONS.md), sem recolocar perguntas já respondidas na fila.

## Atualização de 04/11 — endereço próprio

O cadastro próprio de endereço possui API autenticada GET/PUT, versões imutáveis,
conflito otimista, replay de operação, RLS e audit/outbox. Nenhuma origem de pesquisa
é promovida automaticamente a endereço da loja. Geocodificação, ponto permanente
comprovado, interface e vínculo à descoberta continuam pendentes. Ver
[contrato](design/business-address.md).

## 04/11/2026 — Vocabulário de atividade para a busca

A classificação pré-Google agora dispõe de taxonomia versionada da Table A
(478 tipos), adapter Jev com uma chamada identificada e guard antes da rede.
A escolha considera o ramo informado, sem fallback `restaurant`, e retorna
abstenção quando necessário. O [design](design/google-place-type-mapping.md)
descreve limites, fontes e validação. Execução durável e contabilização são
conectadas na fatia 0106; os testes locais não demonstram busca real concluída.

## Atualização de04/11 — localização própria integrada

A [geocodificação do endereço próprio](design/business-geocoding.md) conecta API,
outbox, Temporal e adapter com orçamento, sem chamada paga. Correspondência
precisa resolve automaticamente; ambiguidade aceita escolha explícita do ponto.
Pesquisa manual reutiliza a localização e inclui seu custo no limite da busca.
A admissão vincula nome/endereço atuais por HMAC e a publicação revalida a identidade;
origem GPS permanece separada. A orquestração dos demais fornecedores e o ensaio
real continuam pendentes desta fatia.

## Integração de referências em 04/11 — resultados e custos

A API permite consultar resultados reais publicados, confirmar de uma a três
referências e corrigir o Instagram associado. A revisão de escolhas ausentes
fica vinculada ao primeiro resultado da nova rodada após seis meses. A troca
de raio no mesmo ciclo não solicita essa revisão. O publicador interno usa
somente IDs, notas próprias e perfis já obtidos; ainda depende do executor real.

O teto por pesquisa agora soma o consumo de todos os titulares ativos do negócio.
O run Apify pode ser recuperado por GET sem repetir a coleta, e o custo informado
pelo run terminal atualiza a reserva de forma idempotente. Contrato Compass
corrigido para os campos oficiais; nenhum POST pago foi realizado. As migrações
0101–0105 estão integradas no código; o banco local ainda precisa de atualização.
A suíte completa da retomada encontrou duas falhas e cobertura de 99,38%; a
correção e nova validação integral continuam pendentes.

## Coleta de publicações — adapter integrado em 04/11

Instagram feed e download de imagens possuem opt-in de rede, guardas, limites e
contrato oficial. Foram retirados campos de entrada não suportados pelo coletor.
Os dados de publicações ficam somente em memória; os padrões derivados serão
persistidos pela análise ainda em implementação. A guarda financeira e os custos
terminais usam a mesma semântica do coletor de contatos. 357 testes unitários
passaram com cobertura integral dos cinco módulos; nenhuma coleta paga realizada.

### Configuração do piloto de referências, 04/11

O script `scripts/configure_reference_pilot.py` prepara a política local e o
piloto acumulado de US$ 5, sem zerar consumo ou habilitar fornecedores. Plano
por padrão; aplicação exige banco local/admin separado e preserva configurações
divergentes. 14 unitários e três testes SQL aprovados; execução real ainda pendente. Ver
[operação](design/reference-pilot-operations.md).

## Retomada da validação — 04/11/2026

A revisão do CI removeu trechos inacessíveis de criação local e execução
editorial sem skill após C17/C18, preservando replay e consulta histórica,
rejeições duráveis e controles de acesso/custo. Os testes deixam de fabricar
sucesso do caminho descontinuado. Foram aprovados 3.555 testes relacionados;
a cobertura do recorte foi 98,31%, com guards adicionais posteriores. O CI
integral final continua pendente. [Evidência](evals/ci-resume-2026-11-04.md).

### Banco local e leitura de referências, 04/11

Banco de desenvolvimento atualizado de 0099 para 0105 após backup privado
`.local/backups/pre-reference-20261104-111303-372421.dump`, com índice do arquivo
validado pelo pg_restore da mesma versão. A leitura de referências do negócio
informado passou usando runtime restrito e autorização de titular ativo. Isso
valida o serviço/banco; a sessão autenticada do navegador ainda não foi repetida.
O banco da aplicação não foi usado como banco de testes.

### Análise estruturada de publicações, 04/11

O adapter Jev aceita legenda e/ou imagem em memória e devolve apenas códigos
de um vocabulário próprio. A agregação gera até nove padrões gerais de tom, temas,
formatos e elementos visuais, sem conteúdo das publicações. 65 testes passaram
com 100% de linhas e branches nos dois módulos novos; Ruff e mypy aprovados.
Persistência, agenda de seis meses e uso no gerador permanecem em integração.
O teto local acumulado de US$ 5 foi configurado; flags persistentes continuam
desligadas e não houve chamadas pagas nesta retomada.

### Retomada — identidade própria e resposta vazia (0107)

A descoberta agora persiste a conclusão própria de identidade na mesma transação das notas e da semelhança. Uma correspondência clara exclui a loja; ambiguidade oferece apenas Place IDs ao titular e retoma a mesma execução após sua decisão. Titulares ativos compartilham essa decisão sem compartilhar tokens de fornecedores.

Google sem resultados amplia automaticamente 5 → 20 → 50 km, sem mudar a preferência salva nem consultar novamente um raio ocupado. A família compartilha o teto financeiro e reutiliza o cache. Uma rodada inteiramente vazia e ainda não confirmada permite tentar novamente, preservando escolhas anteriores; um ciclo já confirmado continua respeitando seu prazo. Ainda faltam a integração completa de análise/agenda de publicações, consumo dos aprendizados e ensaio externo configurado.

### Execução integrada da descoberta, 04/11

0106+0107 conectam admissão, Temporal, Google, Jev, Apify e publicação sob o
ledger existente. A API recebe operação e carrega contexto/raio do servidor;
retomada comprovada do Apify não repete Google/Jev. A tela usa o estado canônico
da família de raios. Flags persistentes continuam desligadas. A validação dirigida
passou em 57 testes, incluindo 17 integrações, com cobertura integral dos módulos
novos de execução; adapters e wiring passaram nos recortes próprios. CI integral
e ensaio pago permanecem pendentes. Veja docs/design/reference-discovery-execution.md.


### Referências escolhidas na geração — fatia 0110

Novas propostas capturam a seleção canônica e os aprendizados da versão exata
do perfil em `reference_generation_snapshot`, separado do histórico manual.
Briefing editorial e peça visual usam a mesma cópia imutável. Ausência de análise
e cobertura parcial permanecem explícitas; notas internas e semelhança orientam
a seleção e não autorizam afirmações comerciais. Posts, legendas e imagens de
terceiros não são armazenados nem enviados como referências visuais.

Retirada ou troca de perfil bloqueia novo efeito que utilizaria a associação
antiga; uma alteração durante o efeito impede aceitar o resultado editorial.
A revalidação não substitui a cópia histórica. Prévias concluídas e traces
continuam acessíveis pelas regras existentes. Propostas legadas com coluna
nula conservam o fingerprint e o significado de suas indicações manuais.
Não há truncamento silencioso a32 referências; o limite de tamanho do pedido
editorial continua sendo conferido antes da reserva.

Contrato e validação em [integração de referências na geração](design/reference-generation-context.md).
177 testes unitários e 13 casos PostgreSQL passaram nos recortes desta fatia,
incluindo leitura 0108 e geração visual com HTTP simulado. Naquele recorte, a
agenda completa e o CI integral ainda estavam pendentes; essas provas não
demonstravam qualidade comercial. O CI vigente foi concluído em 09/11, conforme
o estado atual no início deste documento.

### Aprendizados das referências — persistência e agenda, 04/11

A fatia 0108 liga referências manuais e sugeridas escolhidas a associações
versionadas e janelas duráveis de análise. Aceite e troca de perfil agendam a
primeira análise; atualizações posteriores derivam do aceite a cada seis meses.
O banco guarda padrões próprios comprovados, metadados e, quando disponível na
resposta já obtida, o nome do perfil Apify. Não guarda publicações ou imagens.
O leitor de status é somente leitura, e a captura para geração permite revalidar
seleção e associação antes de efeitos pagos. Execução Temporal, snapshot e UI são
integrados nas fatias adjacentes; o ensaio real e CI final continuam necessários.
Veja [persistência e agenda](design/reference-learning-storage.md).

### Aprendizados das referências na API e na jornada, 04/11

O GET autenticado `reference-learnings` entrega somente os estados, datas e
padrões persistidos para as referências escolhidas e sua associação vigente.
Titulares ativos compartilham essa leitura; viewer, outro tenant e sessão ausente
são rejeitados. A consulta não inicia efeitos nem altera a agenda. Quando o feed
já obtido forneceu um nome válido, a tela o apresenta junto ao @; na ausência,
continua usando o perfil. Não há nova chamada para obter nome.

O painel distingue espera, execução, indisponibilidade, análise concluída/parcial
e atualização programada. Seleção, correção do @ e referências próprias
invalidam a leitura. Não afirma sucesso enquanto os padrões não estão salvos.
16 testes unitários passaram com 100% de linhas/branches dos três módulos de
leitura; dois testes HTTP/PostgreSQL passaram com runtime restrito e provaram
isolamento e ausência de novas reservas, resultados, eventos ou auditorias no
GET. Mypy e Ruff passaram. A web passou em 100 testes focados/100% das quatro
métricas e em Chromium 390/1440px com fixtures locais. CI integral combinado e
ensaio externo controlado continuam como gates da entrega completa.
