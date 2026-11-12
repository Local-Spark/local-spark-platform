# BL04 — contexto seletivo e produção visual com IA

**Revisão da seleção visual — 12/11/2026.** Titular examinou os prints e
questionou sua contribuição. Decidido retirar os oito da próxima rodada, sem
apagar histórico, demais evidências, skills ou exemplos úteis. Não contabilizar
anexos recebidos como melhoria criativa. Documentados arquivos/instantes,
cinco enviados versus três somente preparados, critérios de curadoria e uso
parcial dos repositórios de origem em
`docs/evals/ensaio-acompanhado-motion-2026-11-12.md`. Só documentação nesta fatia;
seleção revisada no produto e qualidade resultante ainda não implementadas/validadas.

**Primeira fronteira do ensaio acompanhado — 12/11/2026.** Pacote montado pelo
produto, não enviado, revelou direção herdada restritiva e nenhuma seleção de
SFX. Titular corrigiu entrada técnica e uso da referência como molde; escolheu
biblioteca pública com licença comercial verificada. Entrada revisada separa
mensagem do cliente, controles do produto e piso funcional. Inventário confirma
orientações sonoras existentes no estudo Maestros/skills, sem integração de
obtenção/seleção. Plano/código ainda não gerados; não se concluiu `awaiting_render`.
Registro, provas e pendências: `docs/evals/ensaio-acompanhado-motion-2026-11-12.md`.
Sem alteração de produção/banco; cinco serviços parados e orçamento antigo intacto.

**Fases 1–3 da preparação acompanhada — 12/11/2026.** Implementação mantém
capacidades anteriores e adiciona origem das decisões, evidência conferida no
builder, repertório opcional v3 e pausas duráveis após plano/código. API do titular
expõe payload/retorno armazenados e manifesto, com aprovação vinculada ao hash.
Retomada pelo Temporal existente; nenhuma chamada ao renderer antes de aprovar
`render`, que libera só storyboard. 65 testes dirigidos passaram com cobertura
100% nos quatro módulos novos; 1.533 motion/exportadores (dois skipped), seis
integrações de regressão e Mypy 330 módulos aprovados. CI global continua pendente
na formatação preexistente. Migração 0118 somente no `_test` autorizado; dev e
serviços preservados. Sem chamada paga ou peça nova. Escopo técnico e qualidade
ainda não validada: `docs/design/motion-preparacao-e-revisao-fases-1-3-2026-11-12.md`.
Chat/trace OpenCode levantado pelo titular: proposta separada, sem integração
executada, em `docs/design/opencode-e-inspecao-do-produto-2026-11-12.md`.

**Fluxo efetivamente executado — 12/11/2026.** Auditoria ampliada a pedido do
titular: brief manual/API direta, chamadas e retornos reais, normalização pelo
servidor e caminho de avaliação MP4. Diferenciar do percurso completo de cliente
e da revisão/correção que não rodou. Evidências extraídas localmente; sem nova
chamada, render ou mudança de runtime. Ver
`docs/evals/auditoria-fluxo-motion-2026-11-12.md`.

**Prioridade: auditoria por etapa — 12/11/2026.** Conferência inicial compara
pedido/snapshot/payload da rodada anterior e reproduz entrada com builder real
offline. Mantidos skill/kit/repertório/base; limitações de amostragem, escuta,
seleção e direção registradas. Pausa antes da implementação ainda precisa ser
habilitada para nova execução acompanhada. Sem geração/gasto nesta entrega.
`docs/evals/auditoria-fluxo-motion-2026-11-12.md`.

**Feedback sobre direção — 12/11/2026.** Não universalizar exemplos nem congelar
soluções artísticas de uma rodada. Estudo temporal de ação completa em cerca de
4–5 s e aplicação numa janela da peça são propostas; movimento/escuta e conexão
com o conjunto ainda precisam de avaliação. Sem nova etapa, código, geração ou
gasto. Atualização, evidência das restrições na direção e pendências em
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

**Recuperação da etapa 7 planejada — 11/11/2026.** Cinco fatias R1–R5 preservam
implementações das etapas 1–6 e o aprendizado das referências. Entregas e aceites
separam contexto, direção, cobertura, seleção e resultado visual. Base principal:
“Nova — quatro melhorias”; versão desenhada como referência complementar de ação.
Nenhuma fatia iniciada nesta entrega de planejamento. Sem nova peça, chamada,
banco ou serviço; execução paga/render depende de autorização nova. Plano:
`docs/design/plano-recuperacao-e-evolucao-motion-2026-11-11.md`.

**Restrição do titular para recuperação — 11/11/2026.** Manter capacidades
implementadas a partir das referências/YouTube e evoluir a qualidade com comparação
evidenciada. Não restaurar arquitetura antiga nem desativar as etapas 1–6. Bases
indicadas são referências de resultado. Aplicação efetiva da rubrica comparativa
como condição de conclusão/seleção permanece pendente; requisitos registrados nas
Regras transversais do contrato. Sem código, geração, render, banco ou serviços.

**Etapa 7 — causa da regressão, 11/11/2026.** As referências corretas são as duas
peças da comparação “Anterior / Nova — quatro melhorias” de 11/11, indicadas pelo
titular. Sete elementos e suas funções de ligação saíram na direção da etapa 1;
nenhum vínculo com a composição anterior entrou no payload efetivo. Controles
de integridade mantiveram o plano reduzido. A espera de 2,52 s já era de 2,56 s
na base; a perda é de ações e continuidade, incluindo xícara removida no retorno.
Evidências locais, contraprova com validadores e pendências registradas em
`docs/evals/diagnostico-regressao-motion-2026-11-11.md`. Sem código de produção,
geração, render, banco ou serviços alterados. Etapa 7 permanece aberta.

**Etapa 7 — reprovação visual do titular, 11/11/2026.** Storyboard não atendeu:
vídeo, frase e xícara percebidos como blocos separados. Inspeção do plano confirma
longa espera e ações pequenas, apesar das descrições de coordenação. Revisar
concepção antes de outra execução; não tentar resolver com MP4 ou crítica paga.
Sem gasto adicional, mudança de código ou estado terminal na API. Etapa 7 aberta.
Evidências: `docs/evals/comparacao-qualidade-motion-etapa7-2026-11-11.md`.

**Etapa 7 de qualidade motion — storyboard entregue, 11/11/2026.** Plano, uma
imagem e implementação executados pelo produto; entradas conferidas por hash e
ASR novo igual à proposta. Fonte/kit/voz preservados; áudio somente original.
Galeria real com 18 quadros aguarda decisão do titular antes do MP4. Reserva
US$ 3,00 do teto novo US$ 6,75; estimativa US$ 0,372465 sem fatura confirmada.
Sombra difusa e quadro vazio no retorno registrados; fluidez/áudio não avaliados.
Worker dedicado encerrado; sem crítica paga, correção ou aceite criativo. Etapa 7
aberta; nenhuma etapa 8 definida. Evidências:
`docs/evals/comparacao-qualidade-motion-etapa7-2026-11-11.md`.

**Etapa 7 de qualidade motion — preparação, 11/11/2026.** Pacote da comparação
montado pelo produto, com igualdade de fonte/kit/voz/perfil e diferenças declaradas.
Proposta de uma xícara conceitual fotográfica; titular escolheu somente áudio
original. Até cinco chamadas de modelo, uma imagem e uma correção condicional:
reserva nova proposta US$ 6,75, sem autorização ou execução. Executor reconstruído;
qualificação e produção pendentes. 24 testes dirigidos, Ruff e Mypy aprovados;
sem prova visual. Etapa 7 aberta; nenhuma etapa 8 definida. Detalhes:
`docs/design/motion-etapa-7-preparacao-comparacao-2026-11-11.md`.

**Etapa 6 de qualidade motion — 11/11/2026.** Crítica e payload reais carregam
escopo por cena/elementos, evidência, intervalo e margens. Correção sem replanejar;
render completo registra hashes de todos os quadros antes do H.264. Regressões
externas, ambiente diferente e evidência incompleta rejeitam a candidata. Plano,
assets e áudio preservados; operação e teto existentes. Fixture local aprovada,
sem comprovação do MP4 final ou qualidade artística. Imagem, CI e comparação real
pendentes; etapa 7 requer OK. Sem gastos, serviços iniciados ou banco. Detalhes:
`docs/design/motion-etapa-6-correcao-delimitada-2026-11-11.md`.

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

**Próximo trabalho planejado — 11/11/2026.** Contrato de sete etapas consolida
os seis gaps e o inventário de capacidades do vídeo Maestros. Começar por direção
verificável/repertório e seguir aceites técnicos separados da validação criativa.
Comparação exige orçamento novo e entrada preparada pelo produto; não reutilizar
tetos anteriores. Recorte/tracking/OCR/stock/3D e EDL não bloqueiam esta entrega.
Planejamento apenas; nenhuma etapa implementada nesta alteração. Referência:
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

**Correção estrutural da geração implementada, sem comparação paga.** Contrato
v3 para novas direções fornecidas: planejamento sem código e implementação sem
repetir plano, com validação intermediária e vínculo por hash. Dois recibos/reservas
duráveis, sem retry automático, preservando contratos anteriores. Corrigida ordem
do schema e exportação das duas etapas. Pacote offline conserva as 12 imagens da
última tentativa. Causa raiz do limite do provedor ainda não comprovada; novo MP4
e qualidade pendentes. Dev conferido em 0116, sem migração necessária. As melhorias
do vídeo Maestros ficam para depois da comparação, conforme orientação do titular.
Detalhes: `docs/design/motion-construcao-em-etapas-2026-11-11.md`.
473 testes dirigidos passaram, cobertura integral nos seis módulos medidos e
Mypy/Ruff OK. 23 testes de integração passaram; execução mais ampla interrompida
por Temporal local indisponível. Não houve CI integral ou chamada real ao modelo.

**Estudo da referência WuzMxEKJHkQ entregue.** Download 1080p, legendas automáticas,
114 quadros distribuídos e seis detalhes analisados. Mapeadas ferramentas,
composição, profundidade, alinhamento, percepção espacial, som e revisão ao fluxo
atual. Um pedido humano não demonstra uma única completion. Recomendada recuperação
por artefato antes de outra comparação; preservar as quatro melhorias visuais e
qualificá-las no resultado. Estudo não implementa recorte, tracking, 3D ou cortes
longos. Sem código alterado, chamadas pagas, render ou CI; validação documental.
Sem nova tentativa autorizada. Relatório:
`docs/evals/analise-video-maestros-WuzMxEKJHkQ-2026-11-11.md`.

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
[Escopo, decisões e validação](../design/evolucao-qualidade-motion-referencias-2026-11-09.md).

**Pesquisa de composição concluída:** Maestro contém geração de objetos
recortados, busca de takes e captura de páginas; Finalizador contém 70 cenas em
código; claude-video já prevê arte por cena antes da animação. Fontes externas
oficiais confirmam catálogo de componentes e mídia. Na pesquisa, esses recursos ainda não estavam
integrados ao Reel; adaptação parcial registrada acima; a pesquisa não demonstra qualidade nem autoriza gastos.
O titular posteriormente confirmou liberação do conteúdo Maestro para nosso uso;
a observação anterior sobre o ZIP não bloqueia o escopo autorizado.
[Inventário, fontes e próximo recorte](../evals/pesquisa-elementos-motion-2026-11-09.md).

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
[Plano concreto](../evals/plano-prova-motion-temporal-integrada-2026-11-09.md).
[Plano de retomada](../evals/plano-retomada-motion-temporal-2026-11-09.md).

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

O [CI da base anterior à proteção completa de orçamento](../../.local/ci-motion-integration-20261109/run-20261109T154537Z/result.json) passou: **5.353 testes, 100% de 18.570 linhas e 5.090 branches**,
sem skips. Passaram também 363 testes Python do laboratório, 137 Node dos
renderers, lint/formatação e tipos. Web: 524 testes/100% nas quatro métricas,
tipos, build, formatação e QA de interface em 390/1440 px. O código daquela execução permaneceu
estável durante o CI; os bancos eram exclusivos `_test`, com roles restritas.

Os quatro replays Linux preservaram código/assets: Intensa 67,3 s, Dog 75,2 s,
Luma 73,3 s e Giz B 107,2 s. A prova do pedido ao download passou em 97,6 s
com API/auth, SQL/RLS, relay, Temporal, renderer e storage reais; **modelo e
crítico simulados**. Reentrega não repetiu efeitos; acesso de outro tenant e
anônimo foi bloqueado. Não houve aprovação humana fabricada nem chamada paga.
[Comparações, resultados e limites](../evals/qualificacao-integracao-reel-2026-11-09.md).

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
[Vídeos, resultado, custos e limites](../evals/plano-prova-reel-integrada-2026-11-09.md).
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
[Plano da nova rodada](../evals/plano-comparacao-criativa-integrada-2026-11-09.md).
Avaliação humana recebida: B ficou um pouco melhor, mas continua muito aquém dos
motion graphics e exemplos das bibliotecas esperados. O nível criativo pretendido
não foi atingido; não há aprovação de qualidade comercial. Áudio e outras possíveis
regressões não foram avaliados explicitamente na resposta. Os quatro checks `met`
do modelo não equivalem ao patamar criativo desejado. A rodada usou calibrações
textuais, sem comparar visualmente com as referências. Próxima necessidade:
definir uma referência concreta e calibrar geração/crítica contra seu acabamento,
preservando diversidade; escopo e orçamento de nova execução ainda não definidos.

Referência concreta recebida: vídeo de Felipe Borges, analisado visualmente desde
o início por sequências de quadros. [Análise e trechos](../evals/referencia-motion-youtube-fqaEZqPzKZs-2026-11-09.md).
Os exemplos usam cenas gráficas, interfaces, diagramas e composição em camadas.
A referência esclarece o alvo, mas não conclui a qualidade do produto. Próximo
recorte proposto: enriquecer o planejamento de cenas e calibrar a crítica visual;
cortes e áudio alinhado exigem ampliação explícita da integração. Sem nova API paga.

O [Reel específico enviado depois](../evals/referencia-reel-Db9axeiOotS-2026-11-09.md) foi baixado e
inspecionado por sequências de quadros. Ele prioriza hierarquia, revelação
progressiva, estados e alternância de composição. Recorte de pessoa e imagens
geradas não são pré-requisitos dessa próxima prova. Eventos ligados à fala
exigem alinhamento; em peças sem fala, usar tempos do roteiro. Sem nova geração.

Quatro Shorts adicionais foram analisados, incluindo legendas do tutorial de
cinco passos. [Plano consolidado de evolução](../design/evolucao-qualidade-motion-referencias-2026-11-09.md).
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
[Contrato da integração](../design/integracao-reel-2026-11-09.md).

**Etapa 3 concluída no recorte demonstrado:** legibilidade do 1c e preferência
humana por Giz B (“B ficou melhor.”). Giz é refinamento com feedback/referência
adicionais; não prova ganho universal de autocrítica ou economia. Artefatos,
feedback e custos históricos permanecem separados no [registro](../evals/motion-registro-de-validacao.md).

**Etapa 5 ainda não implementada.** O escopo autorizado anteriormente inclui
o ciclo de imagem feed/story, seguido de story em vídeo e carrossel animado.
A sequência vigente termina primeiro os três pontos do Reel, um por comando. O
[desenho de imagens](../design/ciclo-revisao-imagens-2026-11-09.md) prevê inspeção do JPEG final antes da entrega,
correção condicional e preservação de versões; planejamento não é entrega.
A [matriz](../design/v0-motion-etapa-0-formatos-e-casos.md) registra o reuso e as lacunas por formato.

WhatsApp (6) e piloto/operação comercial (7) continuam posteriores. Piloto de
autoatendimento com cobrança, ainda sem participantes reais; usar os quatro
casos fictícios. Preço/franquias dependem de custo por peça aceita. Publicação
automática no Instagram permanece posterior. Dúvidas de produto serão tratadas
em entrevista; manter o foco nas fatias autorizadas.

## Histórico da retomada — 08–09/11/2026, antes da preferência humana por Giz

Os registros abaixo preservam a sequência de preparo, execução e validação.
Pendências de avaliação humana descritas nessa sequência eram o estado de cada
momento; a conclusão vigente e os próximos trabalhos são os do bloco acima.

O titular confirmou o texto do [roteiro de sete etapas](../design/execucao-ate-etapa-7-2026-11-07.md).
A prioridade é alinhar documentos, corrigir a checagem de tipos e restaurar as
ferramentas locais de mídia, concluir a prova comparativa (3), integrar o Reel
após comparação e revisão humana (4) e avançar aos outros formatos (5). As
etapas de jornada (6) e preparação do piloto/comercial (7) permanecem no roteiro.
Entrevistas tratarão definições faltantes; preparar ou testar não encerra os gates.

A entrevista já definiu autoatendimento com cobrança, sem participantes reais
escolhidos. Os exemplos de cafeteria, loja física Ponto do Dog, delivery Dog em
Casa e manicure Estúdio da Luma orientam validação sintética. Valores de plano,
franquias e limites comerciais dependem da medição. Instagram permanece depois
da geração/revisão/download; WhatsApp oficial é necessário para a jornada real.

A continuação independente `4338880a-10f2-48a7-96cd-54138f87dbdd` terminou em
`completed_partial_human_pending`: Dog/Luma receberam críticas v2 `adequate`,
sem achados ou correções; Intensa e sua reserva incerta continuam bloqueadas.
Duas novas chamadas somam US$ 0,175165 estimados. Acumulado de Intensa/Dog/Luma: seis
tentativas, US$ 0,427215 conhecidos, custo da tentativa anterior incerta ainda
desconhecido e US$ 1,50 em reservas. O teto de US$ 6,75 não foi esgotado.
[Resultado e relatório](../evals/ensaio-ciclo-revisao-motion-2026-11-06.md).

A tipagem foi corrigida e as ferramentas locais de mídia recuperadas com
hashes conferidos. Passaram 107 testes Python de motion e o preflight dos três
casos. O relatório foi corrigido para caminhos longos e validado a 390/1440 px,
nos modos cego/identificado, com três players e sem overflow, erro JavaScript
ou rede externa; vídeos/críticas/ledger intactos. Após reproduzir o timeout e
ajustar a preparação dos testes de concorrência, o módulo passou em quatro
testes (93,61 s). As falhas posteriores de CI são históricas; a execução final
de 09/11 passou, conforme abaixo. No
recorte `app`/`migrations`, apenas `test_destination_lock_proof.py` mudou desde
a tentativa anterior desta retomada; produção e migrations intactas. O CI de
06/11 registra a árvore daquela execução.
A comparação real do 1c abaixo teve a legibilidade reconhecida pelo titular,
sem aprovação criativa global. Etapa 3, ganho geral e integração permanecem abertos.

Em entrevista, o titular escolheu testar a correção do [Reel histórico 1c](../evals/plano-revisao-reel-1c-2026-11-08.md)
com defeito conhecido. O pacote offline de 69 arquivos foi concluído e preserva
dez normalizações históricas. A ponte declarativa foi implementada; passaram
146 testes locais (57 da orquestração e 89 da ponte), Ruff e mypy estrito.
Não transforma a origem em resposta HTML/JS. A primeira qualificação do run
`3a52c376-e8ea-4bea-b997-94ba59c628de` falhou no parsing de metadados FFprobe 4.4.8;
a tentativa foi preservada e não houve API. Após correção estrita, o preflight
real confirmou MP4 arquivado idêntico ao original e remux preservando 526 pacotes
AAC, PCM e tempos, mais 336 quadros RGB24 e tempos. A segunda qualificação
completa passou depois, recompilando/renderizando a direção original e
confirmando quadros, tempos e áudio. A prova e seu hash foram preservados.

O titular autorizou em entrevista até três chamadas/US$ 1,25 e o envio à OpenAI.
O registro `authorization.json` vincula decisão, plano, primeiro pedido e
qualificação. A execução paga do 1c foi concluída; resultado, custos e comparação
estão abaixo; o titular confirmou legibilidade, sem aprovação global. A falha de
unidade tipográfica já foi corrigida na geração atual; esta prova limitada não
demonstra por si só ganho criativo geral ou economia da revisão em todos os
pedidos. Prova e julgamento humano (3) precedem integração do Reel (4) e demais
formatos (5); qualificação técnica não equivale a ganho criativo ou integração.

O [ensaio 1c concluído](../evals/ensaio-revisao-reel-1c-2026-11-08.md) produziu
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

No ensaio 1c, três chamadas HTTP 200, sem retry ou incerteza: **US$ 0,527685 estimados novos**,
US$ 1,25 reservados. Subtotal histórico de APIs US$ 0,106892; subtotal com revisão
US$ 0,634577, sem fatura ou COGS completo. Chamadas somaram 154,561 s; render e
evidências, 151,928 s; subtotal medido 306,489 s exclui setup/preflight/intervalos.
A prova e o feedback sustentam reparação desse defeito histórico, não ganho
criativo ou retorno financeiro geral. O CI foi concluído; a avaliação humana
da prova criativa precede integração do Reel (4) e demais formatos (5). A etapa 3
não recebeu aprovação global; a autorização posterior de Giz não altera esses
resultados ou o aceite limitado do 1c.

## Histórico: início do ciclo de revisão de Reel — 06/11/2026

O titular priorizou o ensaio em Python/API de gerar, renderizar, inspecionar,
corrigir e renderizar novamente. O braço revisado parte da mesma composição
histórica do baseline; são até duas correções, crítica por versão e escolha
humana explícita. [Desenho](../design/ciclo-revisao-motion-2026-11-06.md) e
[plano](../evals/plano-ciclo-revisao-motion-2026-11-06.md) descrevem o
protótipo privado implementado, sem comparação concluída. O titular autorizou até US$ 6,75
em reservas, até 15 chamadas e envio de quadros/contexto/código à OpenAI para
Intensa/Dog/Luma; áudio técnico mantém a mixagem e exige escuta humana. O clipe pessoal
continua aguardando avaliação. Skills e componentes permitidos são fontes de
estudo; não se prevê servidor Claude Code ou agentes hospedados. A comparação
precede integração em produto; postagem segue fase posterior à geração.
Blocos datados seguintes descrevem decisões e estados de seus momentos.

Primeira execução real: três críticas `adequate`, sem correções, estimativa
US$ 0,2520500 e reservas US$ 0,75. A auditoria constatou que o contexto criativo
do crítico estava incompleto; isso prova execução, não qualidade ou ganho. A
[continuação](../evals/plano-ciclo-revisao-motion-2026-11-06.md) com contexto
corrigido parou na primeira crítica com resultado incerto, sem resposta ou
refações. Total: quatro chamadas, US$ 0,2520500 conhecidos de estimativa,
custo da última desconhecido e US$ 1,00 em reservas. Sem retry; A/B pendente.
[Resultado parcial e limites](../evals/ensaio-ciclo-revisao-motion-2026-11-06.md).
`make ci` aprovado na árvore de 06/11: 5.045 testes da aplicação, cobertura
100% de linhas e branches; 91 testes Python de motion, três Node de áudio e 62
Node do renderer, Ruff e mypy. PostgreSQL `_test` e Temporal descartáveis,
`TZ=UTC`; [detalhes](../CHANGELOG.md). Não encerra comparação criativa.

## Histórico: caso pessoal musical como foco único — 06/11/2026

Titular solicitou editar sua gravação de 46,5s com formas/realismo ligados à letra.
Preparação local concluída, fonte intacta, 12 quadros e áudio separados; teste
técnico de modo pessoal explícito passou. Sem envio real ou gasto novo até
autorização específica. [Plano de três chamadas](../evals/plano-clipe-musical-pessoal-2026-11-06.md),
reserva adicional US$ 1,60. Posteriormente titular autorizou verba e envio pessoal;
ASR recebido, estimativa US$ 0,0047, com conferência parcial pelas legendas
incorporadas e originais preservados. MP4 de 46,5s e comparação entregues;
estimativa total US$ 0,51148, sem retry ou ajuste visual manual. Áudio original
identificado por payload/PCM/tempos; qualidade humana pendente.
[Resultado](../evals/ensaio-clipe-musical-pessoal-2026-11-06.md).
Demais frentes ficam adiadas durante esta peça.

## Preparação do step 1: Dog/Luma — 06/11/2026

Titular solicitou executar outros negócios e confirmou marca/experiência sem
preço. Cenários incluem gravações ilustrativas, kit/skill/fontes concretos e
metas de contraste e transformação do vídeo, no mesmo renderer qualificado.
Revisão dos termos Pexels não identificou vedação concreta à inferência pontual;
ausência de autorização IA específica foi antes tratada com cautela excessiva.
Proveniência, limites e registros anteriores preservados. [Plano](../evals/plano-motion-outros-negocios-2026-11-06.md).
Preflight passou; titular autorizou as duas chamadas/envio dos pacotes, até
US$ 1,50 adicionais. Dois MP4s/comparação entregues, estimativa US$ 0,5906725,
sem retry pago. Dog traduziu IDs de áudio e renderizou offline, sem alteração
visual; falha original preservada. [Resultado](../evals/ensaio-motion-outros-negocios-2026-11-06.md).
Titular gostou bastante e confirmou o nível da Intensa nos dois casos curtos;
mesma música foi apontada como possível problema. Geração/avaliação criativa
deste step concluídas, com diversidade musical pendente: só havia uma trilha
obrigatória. Próximos testes devem oferecer alternativas licenciadas adequadas,
sem inferir validação de story/carrossel, durações longas ou integração.
Titular confirmou variedade musical com escolha automática por negócio/peça e
repetição permitida para continuidade de série/campanha. Seleção entre opções
e registro do contexto ainda são pendências; decisão não gera nova peça/gasto.

## Validar outras linguagens antes da integração — 06/11/2026

Reel intenso recebeu feedback positivo: “muito legal. melhorou bastante.”
Próxima sequência solicitada: diversidade no mesmo material, outros negócios
fictícios, story, carrossel e transferência do caminho qualificado ao produto.
Vozes mais naturais serão comparação separada com orçamento próprio. Instagram
permanece posterior; intensidade exploratória não vira regra universal.
[Registro e pendências](../evals/motion-registro-de-validacao.md).

Preparados três estilos com fichas e código MIT concretos; CLI de lote gera
comparação de cinco vídeos sem banco/WhatsApp. Preflight e 40 testes Python/três
Node passaram; CI integral não repetido. Após preparação, titular autorizou as
três chamadas/envio do pacote, até US$ 2,25 adicionais: duas peças concluídas e
Papel incerto sem resposta/custo salvos, sem retry. Intensa preferida; Cartaz
bem avaliado; Giz menos convincente por tema/enquadramento. Próximo passo:
outros negócios, depois story/carrossel. [Resultado](../evals/ensaio-motion-diversidade-2026-11-06.md).
Para Dog em Casa/Luma o titular escolheu
vídeos ilustrativos licenciados; verificação de direitos de envio a provedor
continua anterior à rodada desses negócios. A feature segue incompleta.

## Intensidade exploratória entregue — 06/11/2026

Disponíveis [versão intensa e comparação](../evals/ensaio-motion-intenso-2026-11-06.md).
Uma chamada autorizada, estimativa US$ 0,3086025; código executado como recebido,
inversões de tema e mecanismos adicionais conferidos por código/quadros.
Ganho criativo e intensidade preferida aguardam o titular; não é padrão universal
nem conclusão de integração, demais formatos ou publicação.

## Próxima prova criativa: versão “exagerada” — 06/11/2026

O titular gostou um pouco mais da rodada `276486e3`, ainda preferindo o v2,
e pediu motion mais robusta. O [plano de intensidade](../evals/plano-motion-intenso-2026-11-06.md)
explora esse pedido e o feedback sobre verde/creme, letras invertidas e ponto.
Não é rejeição da peça nem decisão de aplicar a mesma linguagem a todo negócio.
O aceite será sobre o resultado final; orçamento anterior não se renova e a
integração da feature continua fora desta prova criativa.

## Comparação da nova peça com o piso — 06/11/2026

Disponíveis o [MP4 e relatório comparativo](../evals/ensaio-motion-biblioteca-2026-11-06.md),
com a skill própria e adaptações reais de três fontes da biblioteca. Uma chamada,
estimativa US$ 0,28714; código executado sem ajuste manual. A revisão criativa
final e a integração do produto permanecem pendentes; não houve ampliação
automática do orçamento ou geração dos demais formatos.

## Evolução autoral acima do piso — 06/11/2026

V2 é mínimo aceito, não template, por esclarecimento do titular. O próximo
[ensaio preparado](../evals/plano-motion-biblioteca-2026-11-06.md) inclui skill
própria de Reel, código selecionado da biblioteca e relatório com três vídeos.
Escolha de linguagem permanece automática. 27 testes offline do CLI passaram;
o titular autorizou uma chamada/envio do pacote, até US$ 0,75 adicionais, e a
geração foi iniciada. Resultado e avaliação criativa permanecem pendentes.

## Ganho criativo esperado ainda não demonstrado — 06/11/2026

A peça nova não foi considerada ruim, mas o titular mantém o v2 como preferido:
janela horizontal/vertical contínua, formas e pontos, transições suaves.
O diagnóstico identificou escolha de direção e uso parcial das fontes/skill,
sem as skills próprias por formato no último CLI. Preservar essa preferência
antes de variar mecanismos. [Registro](../evals/ensaio-motion-comando-2026-11-06.md).
Sem chamada paga ou alteração no renderer nesta análise.

## Peça nova disponível para avaliação final — 06/11/2026

O comando concluiu a geração após reposição de saldo/retry autorizado: Reel
11,2 s com vídeo/áudio, sem alterar HTML/JS recebidos. Há componentes reais de
motion adaptados do motor `cartaz-risografia`. [Peça e trace](../evals/ensaio-motion-comando-2026-11-06.md).
Gasto desta geração estimado em US$ 0,3114475, não fatura. A validação técnica
não encerra o aceite criativo, os demais formatos ou a integração do produto.

## Comando pago sem saída por saldo esgotado — 06/11/2026

A tentativa de Reel novo recebeu HTTP 429 `credit_balance_exhausted`, sem
composição ou uso informado. Resposta/reserva preservadas; nenhum MP4 novo ou
retry. Qualidade criativa e nova geração permanecem pendentes.
[Evidências e continuação](../evals/ensaio-motion-comando-2026-11-06.md).

## Ensaio rápido sem portões intermediários — 06/11/2026

O titular escolheu revisão somente do MP4 final. O [comando local](../evals/como-executar-ensaio-motion.md)
concentra preflight, geração, render e comparação, com orçamento explícito e
sem refação automática. O cenário inicial permanece fictício, com fontes/kit
congelados e Jev/transcrição reaproveitados de forma identificada. Provas offline
do comando não equivalem a nova geração ou aceite criativo. A integração e os
critérios completos de saída da v0 continuam abertos.

## Histórico: ensaio criativo fiel — 06/11/2026

Executar a [retomada de qualidade](../evals/plano-retomada-qualidade-motion-2026-11-06.md)
com um Reel primeiro, mesma mídia/kit e v2 como patamar mínimo. Usar referência
concreta e componentes reais selecionados dos três projetos preservados, com
direção automática coerente. Registrar bruto e intervenções antes de avaliar a
peça; só depois ampliar a prova para story/carrossel. Integrações WhatsApp/Instagram
ficam fora deste ensaio. O titular autorizou duas chamadas até US$ 1,50 adicionais
e o envio do pacote local. A primeira concluiu; cinco cards estão capturados e
aguardam aceite. A segunda chamada depende desse aceite; nenhum vídeo novo foi
gerado. Custo e traces estão no plano da retomada.
As demais fatias e critérios de saída da v0 continuam pendentes.

## Reprovação criativa da rodada 1c — 06/11/2026

Reel/story/carrossel foram rejeitados pelo titular por simplicidade e falta de
motion perceptível. A referência continua sendo o Reel v2 anterior; a direção
concreta dele não foi levada aos novos inputs. Priorizar o diagnóstico do caminho
criativo e da fidelidade do executor. Os rascunhos seguintes de integração não
foram aplicados; o CI da clareza do contrato foi interrompido a pedido do titular,
sem resultado final, e continua independente da avaliação de qualidade.

## Rodada 1c encerrada; revisão das peças em andamento — 06/11/2026

Os três formatos foram reconhecidos pelo Jev e a transcrição do Reel corresponde
às palavras da fixture. A direção do Reel exigiu correções locais de contrato
e depois ajuste explícito de legibilidade; o MP4 resultante está pronto para
avaliação, sem aceite criativo presumido. [Arquivos e trace](../evals/ensaio-motion-v0-rodada-1c-2026-11-06.md).
O titular autorizou explicitamente a retomada de story/carrossel após o bloqueio
da revisão automática causado pela rejeição do Reel. As sete operações foram
executadas sem retry pago; as três direções foram rejeitadas localmente e têm
derivados separados para montagem. Estimativa global US$ 0,263073, reservas
US$ 1,55 no teto US$ 1,60. Não há nova chamada autorizada nessa rodada.
O app ficou preservado durante os efeitos. Depois, descrições de unidades,
keyframes e áudio foram incorporadas ao contrato/builder, sem afrouxar validação.
O CI dessa fatia foi interrompido a pedido do titular (saída 143), sem resultado
final; o baseline aprovado de 5.044 Python/62 Node é da fatia anterior.
A jornada e os critérios completos de saída
continuam pendentes.

## Correção após primeiro efeito da rodada 1b — 05/11/2026

A interpretação real reconheceu Reel, mas o limiar de seleção de item bloqueou
uma entrada sem candidatos. A rodada foi interrompida após uma chamada, com
reserva preservada, sem transcrição/direção. [Evidência e custo](../evals/ensaio-motion-v0-rodada-1b-2026-11-05.md).
O adapter agora omite a pergunta de item somente nessa ausência estrutural;
55 testes dirigidos/100% passaram. Na retomada de 06/11/2026, conferido CI
integral aprovado: 5.044 testes Python e 62 Node, sem pulados e com cobertura
de 100%. A admissão
de conteúdo sem item, com origem/material/fatos verificados, segue pendente.
Nenhuma nova chamada está autorizada como refação automática.

## Terceiro bloco: contexto, fichas e plano de áudio — 05/11/2026

Concluídos os módulos puros de catálogo próprio, entrada para direção e plano
de áudio. O catálogo fornece as três fichas verificadas; a escolha automática
por modelo continua pendente. O builder preserva proveniência e separa
observações de hipóteses, sem ler mídia, enviar rede ou autorizar acesso.
O plano de áudio mantém trims/ganhos/fades e evidência de fala, sem alegar
fidelidade semântica. Protótipos locais executaram cena e mixagem sintéticas,
com inspeção de frames e amostras PCM; não são renderer de produção nem ensaio
criativo. O terceiro CI integral passou: 5.042 testes Python e 62 Node, sem
pulados e com cobertura de 100%. Não houve novas chamadas pagas.

A preparação da [rodada 1b](../evals/plano-motion-v0-rodada-1b-2026-11-05.md)
usou os contratos e fichas reais, com sete operações propostas. O executor
privado gerou cinco MP4s sintéticos antes da autorização. A chamada real e a
interrupção posterior estão registradas no início deste documento. Mocks e
provas sintéticas não substituem os efeitos reais; a jornada de produto continua
pendente.

## Segundo bloco: compilador parametrizado — 05/11/2026

O primeiro CI fechou com 4.913 testes aprovados, 2 casos dependentes de binários
pulados e 100% de linhas/ramos; os casos reais de mídia passaram no recorte
dirigido. Depois, contrato v2 e serviço de composição foram conectados ao
compilador próprio. Testes dirigidos: 148 Python/100% e 62 Node/100% de linhas,
ramos e funções. A prova entre linguagens compila Reel, story e três páginas.
O titular confirmou carrossel 4:5 e aprovou avançar com a base WAAPI do ensaio.
CI integral do segundo bloco passou com FFmpeg/FFprobe no PATH: 4.987 testes
Python sem pulados e 62 Node, com cobertura integral de linhas/ramos e funções
Node.
Ainda faltam driver/áudio, seleção automática de estilos, verificação de arquivos
e snapshots no negócio, persistência/Temporal e revisão sem postagem. Nenhum
fluxo foi habilitado nem houve chamada paga por esse código.

## Implementação em andamento — 05/11/2026

Primeiras fatias: snapshots das três skills com loader isolado, contrato puro
de direção, elegibilidade explícita no adapter Jev e inspeção/extração de áudio
local. Contrato valida gravação, páginas/duração, cortes na fonte, timeline,
camadas, motion/transições e áudio/legendas opcionais; não comprova fidelidade
semântica dos cortes, alinhamento de fala ou direitos. A inspeção usa metadados,
limita bytes/tempo/saída e não recorta automaticamente gravação excedente.
A amostra original de `claude-video` tem licenças, origem, hashes e verificador
de arquivo/restauração. Dependências e backup independente ainda pendentes.
O CI do primeiro bloco passou, conforme registro acima. Formatos de motion
ainda não estão habilitados na jornada e não houve chamada paga.

O [Reel adaptado com WAAPI](../evals/ensaio-reel-waapi-2026-11-05.md) preserva
a direção geral do v2 e passou nas verificações técnicas; o titular confirmou
avançar com a base técnica desse caso. Não é compilador ou renderer integrado. A revisão final
precisa de [aceite independente de postagem](../design/revisao-peca-sem-postagem-2026-11-05.md),
pois a operação legada agenda publicação simulada. Nenhum código web foi alterado.

## Escopo confirmado por entrevista — 05/11/2026

A edição recebe uma gravação do cliente por pedido, com até 60 segundos de
material bruto e até 60 segundos no vídeo final. A prioridade revisada é concluir
geração, prévia, ajustes, aprovação da peça e download de imagens feed/story,
Reel, story em vídeo e carrossel com motion. Viabilidade e integração de postagem
no Instagram foram adiadas para a fase seguinte; conta Meta e publicação real
não bloqueiam a conclusão da geração. C11 segue vigente para a postagem futura.
Carrossel tem 3–5 páginas, com 5–8 segundos por MP4. Ajustar uma página preserva
as demais; mudanças nelas exigem confirmação prévia e a nova sequência requer
aprovação própria. O estilo é escolhido a cada pedido conforme objetivo, material
e referências, preservando o kit; guardar snapshots por peça, sem preferência
fixa por negócio. Integração e homologação seguem pendentes. O titular confirmou
50 MiB por gravação; excesso de tamanho ou duração pede uma versão menor,
sem cortar automaticamente. Os limites comerciais
seguem medição em P05. Retenção já segue C04/C09, com P03 adiada.

## Primeira fatia da v0 de conteúdo — 05/11/2026

A [matriz de formatos e casos](../design/v0-motion-etapa-0-formatos-e-casos.md)
consolida o ponto de partida para os ensaios; o
[inventário](../design/inventario-claude-video-2026-11-05.md) identifica fontes
e direitos ainda a conferir, sem declarar preservação ou integração. A guarda
de copy recusa padrões específicos da instrução de revisão vazada no ensaio
BL04.3, rejeitando a proposta sem corrigir o texto automaticamente.
No fluxo integral, a tentativa segue `uncertain` e não produz documento público.
Esse controle é limitado; avaliação criativa, novos ensaios e edição audiovisual
integrada permanecem pendentes. Não houve chamada paga nesta fatia.
O CI inicialmente interrompido foi concluído nos blocos registrados acima;
condições do banco efêmero constam no [changelog](../CHANGELOG.md).

A futura integração deve preservar fontes externas e dependências sob controle próprio e provar o runtime sem acesso ao GitHub original; detalhes e estado no [plano](../design/plano-v0-imagens-video-motion-2026-11-05.md#cópias-próprias-e-independência-dos-repositórios-externos).

O plano inclui reaproveitar instruções, fichas, projetos e scripts externos permitidos na integração, em vez de restringi-los a estudo; ver [etapas concretas](../design/plano-v0-imagens-video-motion-2026-11-05.md#integração-concreta-da-claude-video). Amostra e fichas próprias estão disponíveis conforme os blocos acima; a jornada e o empacotamento ainda não estão integrados.

## Plano para concluir a v0 com motion — 05/11/2026

O [plano de integração](../design/plano-v0-imagens-video-motion-2026-11-05.md)
organiza conclusão de imagem, ensaios rápidos, contratos, análise de mídia,
seleção automática de estilo, render seguro, Reel, story, carrossel e jornada
integrada. Não altera o estado das entregas existentes: as novas capacidades e
seus critérios de qualidade da geração permanecem pendentes; postagem fica para
a fase posterior definida pelo titular.

## Ensaio de motion com modelos reais — 05/11/2026

O [ensaio direto](../evals/ensaio-motion-referencia-2026-11-05.md) produziu carrossel e duas direções de Reel, com inputs, prompts, respostas e custos disponíveis; não comprova integração. O Jev não reconheceu os formatos, houve erro de transcrição e o HTML da refação necessitou ajustes. O titular preferiu o Reel v2; avaliação completa de som/movimento e aprovação de publicação permanecem pendentes.

## Proposta de estilos de motion — 05/11/2026

O titular sugeriu uma biblioteca própria de estilos de motion com escolha automática pelo sistema, sem exigir escolha do cliente. Ver [proposta](../design/biblioteca-estilos-motion-2026-11-05.md); integração e avaliação estão pendentes.

A skill externa `claude-video` foi instalada no Codex e sua galeria aberta localmente para estudo, conforme [registro](../design/estudo-claude-video-2026-11-05.md); não é integração do produto.

## Pesquisa adicional de vídeo e motion, 04/11/2026

Em 05/11/2026 o titular esclareceu que o cliente não escolhe imagens do acervo; pode enviar uma imagem e envia o vídeo para edição. Não exigir acervo na edição de vídeo. Áudio pode ser extraído para transcrição, com integração e sincronização ainda pendentes.

Ver [estudo da skill claude-video](../design/estudo-claude-video-2026-11-05.md) e [plano dos ensaios](../evals/plano-hyperframes-2026-11-05.md).

As [prévias locais HyperFrames](../evals/ensaio-hyperframes-2026-11-05.md) foram geradas sem chamadas pagas, com direção do agente e Jev simulado; ainda não comprovam integração, transcrição real ou publicação.

Pesquisa documental dos repositórios indicados resultou em [proposta de ensaio e integração](../design/estudo-hyperframes-motion-design-2026-11-04.md): testar direção audiovisual criada por agente e HyperFrames local; separar a experiência de qualidade da futura integração ao produto. Nenhuma nova chamada paga ou render foi realizado nesta pesquisa.

As primeiras prévias foram rejeitadas por falta de motion, áudio e edição. O [novo ensaio](../evals/ensaio-motion-valido-2026-11-04.md) produziu as peças com rastreabilidade e orçamento próprio; a direção audiovisual é experimental e não demonstra integração do produto. Revisão do titular pendente.

Um vídeo e três páginas animadas foram montados como ensaio local gratuito de direção criativa, sem Jev real ou referências; ainda aguardam avaliação do titular. O [relatório](../evals/ensaio-video-motion-2026-11-04.md) registra fontes, limitações e verificações. Não houve integração de produto ou teste de publicação.

O titular quer estudar skills de terceiros e preparar skills próprias para vídeo gravado no feed/Reel, story em vídeo e carrossel com um MP4 em loop por página. A IA decide a edição criativa e FFmpeg pode executar a montagem. O titular escolheu até 60 segundos por vídeo final e testar vídeo e carrossel separadamente; orçamento e integração seguem em avaliação; as três skills iniciais foram criadas, mas ainda não estão integradas ou avaliadas com peças reais. Detalhes em [estudo](../design/estudo-video-motion-2026-11-04.md).

## Ensaios de qualidade — procedimento vigente

Avaliações criativas futuras usam o [procedimento direto e rápido](../design/ensaios-rapidos-qualidade.md)
solicitado pelo titular: inputs/outputs de mensagem, Jev, editorial e visual;
comparação e revisão das peças, sem criar banco nem montar o produto completo para
esse objetivo. Identidade, orçamento, retenção de resultados incertos e fontes
autorizadas permanecem obrigatórios. O ensaio não comprova integração; testes
de banco, integração e CI seguem exigindo base `_test` exclusiva e roles restritas.
Os preparativos mais antigos abaixo são histórico, não pré-requisito do ensaio.

Os dois pares de feed/story foram gerados no ensaio direto com/sem referências; [relatório e artefatos](../evals/bl043-reference-quality-2026-11-04.md#resultado-do-ensaio-direto--04112026). Uma resposta editorial foi rejeitada e reconciliada; uma nova tentativa com orientação adicional limita a comparação do feed. Revisão humana e correções permanecem pendentes.

O titular esclareceu que a avaliação comparativa deve seguir um ensaio direto e rápido, semelhante aos anteriores, sem executar o sistema completo. A variável continua sendo a inclusão dos padrões nas etapas editorial e visual, com identidades e orçamento duráveis; conferir [plano atualizado](../evals/bl043-reference-quality-2026-11-04.md). Essa evidência não comprova integração de produto.

## BL04.3 — preparação iniciada em 04/11/2026

Registro histórico anterior ao ensaio executado; não reabrir a preparação como
pré-requisito atual nem reutilizar seu orçamento em outra rodada.

O [relatório preliminar](../evals/bl043-reference-quality-2026-11-04.md) inventaria os estados disponíveis, propõe dois pares e explicita fontes, critérios, custos ilustrativos e limites. As duas associações v1 e os nove padrões foram lidos pelo serviço restrito; a verificação individual contra evidências permanece pendente. O produto ainda não oferece controle seguro para retirar apenas padrões: preparar e testar a intervenção sem enfraquecer snapshot ou revalidação antes de qualquer efeito. O titular escolheu dois pares do negócio do piloto, limite de US$ 2 em reservas incluindo refações, aceitando risco de cobrança maior; fará a revisão visual pontual; nenhuma geração, revisão de peças ou refação ocorreu.

## Ajuste da origem de pesquisa — 04/11/2026

A web usa o endereço próprio salvo como única fonte dos campos da origem por
endereço, todos somente para leitura. Sem cadastro, apresenta a orientação para
preencher **Endereço do negócio** e impede salvar essa origem. Mudanças no
cadastro atualizam a exibição e o próximo envio explícito das preferências, sem
salvamento ou consulta automáticos. GPS confirmado, raios e ciclos são preservados.
Indicações de outras regiões seguem pelo @ manual em **Perfis que inspiram seu
negócio**, conforme decisão do titular; não se acrescenta outro endereço de busca.

Critérios de validação: campos não editáveis; cadastro obrigatório para origem por
endereço; valores persistidos prevalecem sobre uma origem antiga; atualização do
cadastro refletida sem salvar automaticamente; GPS e indicação manual preservados.
Testes e validação da interface são registrados no changelog da web.

A mensagem de busca indisponível é controlada por `discovery_available`, vindo da
prontidão operacional da API. As flags locais persistentes de descoberta,
geocodificação e análise seguem desligadas. Credenciais presentes não substituem
a configuração de execução/custos usada temporariamente no piloto. Esse estado
é independente do endereço e do prazo semestral. Este ajuste não ativa chamadas
pagas; o próximo trabalho de qualidade continua sendo BL04.3.

## Referências — gate de fechamento em 04/11/2026

As fatias de descoberta, seleção, análise e projeção na geração estão integradas
localmente. A 0109 foi validada contra a seleção real da 0108 em 22 integrações
PostgreSQL, além de 46 unitários com cobertura integral do guardião. A política
v2 do piloto redistribui os limites por fornecedor dentro dos mesmos US$ 5,
preservando o consumo. A interface passou em 508 testes/100%, TypeScript, build
e navegação em Chromium. O banco local está em 0111 após backups verificados.
O CI conjunto passou: 4.734 testes, 100% de linhas/ramos, Ruff e mypy.
A análise de referência manual do ensaio gerou nove
padrões a partir de onze publicações e quarenta imagens, com estado parcial e
snapshot de geração conferidos. A fórmula de reputação
continua experimental, conforme decisão do titular.

No piloto real, o Google expôs campos opcionais que o parser rejeitava. A
[correção](../design/google-places-address-components.md) foi validada em 160
testes e na nova resposta real de 20 candidatos, com três destaques Jev salvos.
As tentativas anteriores conservaram suas reservas. O banco local foi atualizado
até 0111 após backups verificados; análise e CI concluídos no escopo atual.

A descoberta real publicou dez candidatos com três destaques; o aceite iniciou
o ciclo. O primeiro feed foi coletado com sucesso, mas não gerou padrões pelo
filtro inicial de autoria/formato. O titular resolveu a entrevista: somente
autoria direta, incluindo capa/legenda de vídeos e Reels. O adapter foi atualizado
e passou em 164 unitários/100% e cinco integrações, incluindo ausência de acesso
ao arquivo de vídeo e padrões no snapshot. O CI integral também passou.
O piloto expôs contabilização preliminar do Apify: espera de trinta segundos
validada em 275 testes/100%; revisão auditável de recibos 0111 validada em 38
integrações e 12 unitários/100%. Os onze recibos foram reconciliados no mesmo
piloto de US$ 5, preservando reservas e histórico. O total comprometido após a
análise manual é US$ 0,455502, incluindo holds ainda não liquidados de Google/Jev.
Decisões de conteúdo resolvidas; [evidências](../evals/reference-feature-pilot-2026-11-04.md).

Atualizado em **29/10/2026**, com a primeira imagem real pelo produto concluída
na parte 3 e a priorização de skills de geração antes da avaliação BL04.3.
Estado: **em implementação local**, sem aprovação
comercial. Este é o contrato vigente da fase, junto ao [SDD geral](../SDD.md), à
[trilha BL](BL-brand-library.md#bl04--recuperar-contexto-e-produzir-uma-peça-nova)
e ao [registro de decisões](../DECISIONS.md). A versão anterior foi preservada
[integralmente no histórico](../history/2026-10-28-pre-documentation-reconciliation/phases/BL04-context-and-ai-production.md);
pendências datadas de permissões por fornecedor nesse histórico não são novas
etapas da jornada contratada.

A [análise da jornada WhatsApp e orquestração](../design/arquitetura-jornada-whatsapp.md)
registra o encadeamento atual, as fronteiras entre estados de domínio e Temporal,
as partes simuladas e pontos para discussão futura sobre organização; não altera
o escopo desta fase nem decide uma extração de serviços ou repositórios.

## Qualidade de copy e ação — 30/10/2026

Ensaios diretos em negócios fictícios expuseram bloqueios por notação visual,
identificadores vazados na copy e CTAs que pressupunham interação. A fatia
local corrige a distinção de direção/fatos, valida campos públicos e permite
ao titular informar o canal comercial no contexto versionado. A checagem é
conservadora e não valida o conteúdo semântico ou a imagem final: revisão humana
continua obrigatória. O novo caminho precisa de nova avaliação real controlada;
os ensaios anteriores exigiram ajustes manuais e não provam essa correção.

Foi criado um segundo [kit fictício Ateliê Aurora](../evals/kit-atelier-aurora-v1/README.md), como fixture isolada de QA,
sem inclusão no catálogo nem execução pelo produto. Próximos trabalhos: usá-lo
em ensaio e implementar recomendações para aceite do cliente. Fonte,
disponibilidade de métricas e custos da descoberta
automática ainda precisam ser demonstrados; não inferir acesso do Jev ao Instagram.

Foi entregue a configuração inicial do alcance de referências: a web oferece
raios locais de 5, 20 e 50 km, endereço manual ou ponto confirmado do dispositivo;
raios anteriores de 1–50 km são preservados. Preferências nacionais anteriores
ficam visíveis até substituição explícita, sem nova opção nacional. A origem
manual ainda aguarda geocodificação/confirmação; não há busca automática real
de concorrentes nesta fatia. A preferência permanece no contexto versionado e é
omitida dos prompts editorial e visual. A indicação manual, o snapshot para
briefing/trace e a revisão visual da tela foram implementados localmente; o perfil
indicado não é verificado nem analisado automaticamente.
No serviço, novas alterações só aceitam os três raios locais. Valores legados
iguais ou omitidos são preservados, `null` explícito os remove, e replay e
alterações pendentes já admitidas mantêm compatibilidade.

Palavras do negócio e características gerais foram adicionadas ao contexto
versionado. A interface removeu os formulários de fatos livres e promoções;
fatos legados do contexto não alimentam novas peças e novos snapshots editoriais
ignoram promoções antigas do catálogo. Snapshots antigos mantêm sua política e
registros físicos históricos não foram purgados. O fluxo WhatsApp/Jev de ofertas,
horários, revisões e cálculo de descontos ainda não foi entregue.

## Resultado esperado

Um pedido livre identifica o que divulgar, recupera somente fontes pertinentes
do mesmo negócio e produz uma prévia privada com o kit aplicado. Falta de fonte,
negação ou ambiguidade pede esclarecimento; material hipotético não vira fato.
Revisão da peça e autorização de publicação são ações distintas. WhatsApp real
e publicação oficial continuam dependentes de homologação Meta.

## Contrato vigente

- **IA integra o serviço.** O cliente aceita uma vez em **Plano e acesso**, antes
  do checkout, o uso para texto, imagem, interpretação/Jev e transcrição. Contas
  existentes usam essa mesma jornada. WhatsApp e Informações e preferências não
  oferecem controles individuais de IA, áudio ou fornecedor. O aceite versionado
  por negócio registra versão/hash, ator, data e auditoria; não ativa pagamento,
  provedor ou publicação. Configuração, acesso, plano, orçamento e direitos das
  fontes permanecem verificações internas.
- **Compatibilidade preservada.** Registros e APIs antigos de consentimento não
  são reativados nem reescritos pelo aceite. Após o aceite único, mutações dessas
  permissões são recusadas com `SERVICE_AGREEMENT_MANAGES_PROCESSING`. Retirada
  individual por fornecedor não é uma nova funcionalidade a entregar. A geração
  contratual dos pedidos impede que o aceite reviva trabalho editorial antigo.
  O aceite inicial aguarda efeitos visuais e alterações legadas pendentes.
- **Fontes privadas e versionadas.** Kit confirmado, fatos vigentes, itens ativos,
  direitos, hashes e proveniência acompanham o briefing. Correspondência lexical
  identifica candidatos; não confirma preço, produto, oferta ou interpretação.
  Nomes com alegações comerciais exigem fato confirmado adicional. Enviar apenas
  fotos pertinentes, com no máximo uma referência do kit quando necessária.
- **WhatsApp preservado; acervo editável.** Envios associados de texto, foto,
  áudio e vídeo permanecem sem prazo automático e sem exclusão pelo histórico;
  migration `0058` aplicada localmente. Fotos desatualizadas do acervo podem ser
  removidas. Preservar envios não implementa memória pesquisável, cadastro de
  produto ou skill automática. Eventos técnicos não atribuídos e uploads órfãos
  continuam sujeitos a limpeza; objetos já apagados não são recuperáveis.
- **Troca de número não interrompe a criação.** Material já associado continua
  no mesmo negócio. Na entrega simulada, a ausência de canal adia o envio; após
  vínculo verificado, o destino é o número ativo novo. A origem histórica não
  fixa o destinatário. Há um número ativo por negócio na versão inicial.
- **Plano vencido e prévias — C08/C09 entregues no recorte local.** A criação
  `visual_fake` ou `visual_ai` admitida tem prova durável para concluir após o vencimento
  financeiro e permitir revisão privada. Novas criações e publicação continuam
  exigindo plano vigente. Bloqueio financeiro explícito, revogação de patrocínio
  e perda de identidade/membership não são vencimento. A exceção de conclusão
  ainda não cobre o renderer local legado. Prévias concluídas e proveniência
  são conservadas sem limpeza automática por prazo; tentativas visuais iniciadas
  sem resultado resolvido também são preservadas. `expires_at` continua sendo
  janela de criação/aprovação. URL assinada curta, validade factual e aprovação
  permanecem conceitos separados da preservação, sem atualização implícita de fatos.
  A revisão de resultados concluídos não depende de manter o modo de execução ativo.
- **Alterações aguardam trabalhos admitidos.** Solicitações de mudança de fonte
  bloqueiam novas admissões e cancelam a fila não iniciada. Trabalhos já admitidos
  terminam antes da aplicação da mudança. A prévia concluída permanece para
  revisão, identificada como anterior à alteração; direitos e publicação seguem
  suas verificações. A cobertura atual dessa coordenação é parcial, abaixo.

## BL04.1 — interpretação e contexto: implementado e limites

O worker pode usar **Jev**, opcionalmente em desenvolvimento/teste, desligado por
padrão. A interpretação usa o aceite único; não pede consentimento TypeSafe
separado. Uma operação durável reserva orçamento por tenant/dia, revalida ator,
origem e snapshot e não repete submissão incerta. Recusa de orçamento anterior
à submissão pode aguardar no workflow em intervalos de uma hora, por até sete
dias, com nova verificação no ledger e revalidação. Estados incertos antigos
não são reclassificados como recusa de orçamento.

A configuração exige `TYPESAFE_API_KEY`,
`MEU_BRACO_DIREITO_INTENT_AI_MODE=jev`, chave de criptografia e teto positivo
`MEU_BRACO_DIREITO_INTENT_AI_DAILY_BUDGET_USD_MICROS`. Configurar não homologa
produção nem autoriza um novo ensaio pago. O teto é conservador por tenant/dia;
a reserva conhecida ainda conserva o máximo reservado após sucesso, sem provar
custo faturado ou capacidade em escala.

O briefing experimental liga intenção, formato, catálogo, kit, fatos e fotos.
O nome do item ativo pode ser fonte factual versionada; preço e oferta não são
inferidos dele. O formato inicial definido para a hipótese de R$ 99 é foto/feed
e story; vídeo e quantidades aguardam decisão comercial. A regra é estática,
ainda sem franquias persistidas por múltiplos planos.

A pergunta local é simulada e genérica. Não há conversa completa, memória de
múltiplas mensagens validada, ferramentas arbitrárias ou pesquisa de concorrentes.
Os caminhos de conversa e conteúdo ainda precisam coordenar uma única resposta
por evento antes do envio real. O [ensaio Jev/OpenAI](../evals/intent-comparison-2026-10-27.md)
identificou erros e saídas incompletas; não é holdout independente nem homologação.

## BL04.2 — prévia simulada: implementado e limites

O modo `fake` captura snapshot privado, lê até uma foto WhatsApp e fotos
pertinentes do item/espaço, confere hashes, normaliza orientação e remove
metadados das cópias. Preserva originais. Usa kit, fato e CTA conferidos;
identidade durável, fence e reserva transacional protegem a tentativa.
O acabamento aplica fontes, nome, tagline, logo autorizado e texto do kit sobre
cena neutra, com marca explícita de **simulação**. Não cria a cena com OpenAI e
não comprova qualidade comercial. O resultado é revalidado no acesso e na revisão.

`MEU_BRACO_DIREITO_VISUAL_AI_MODE=fake` e teto positivo
`MEU_BRACO_DIREITO_VISUAL_AI_MONTHLY_BUDGET_USD_MICROS` habilitam a simulação
somente em desenvolvimento/teste. A reserva fictícia é de um milionésimo de dólar,
liquidada em zero. API/schema preservam esses caminhos; mudar somente a
configuração para `openai` não habilita a execução conectada descrita na parte 2.

Um teste sintético usa Temporal e PostgreSQL reais: material já processado,
contexto/acervo, roteiro, dispatchers, prévia simulada com kit e revisão. Intérprete
e storage são stubs; não chama Meta/OpenAI e não começa no webhook completo.
Os testes iniciais uniam preparo, reserva, adapter e orquestrador com HTTP/guarda
simulados. A parte 1 abaixo acrescenta a guarda concreta com PostgreSQL restrito.

A admissão simulada agora bloqueia a proposta, depois o gate visual e o domínio
comercial, revalidando fontes/fingerprint, usuário ativo, membership, aceite e
plano antes de inserir o run e sua auditoria na mesma transação owner. A revogação
de patrocínio participa do lock comercial existente. A reserva/fence e o ledger
continuam em transação correlator separada, com os tetos já existentes; um run
gravado não autoriza repetição quando a etapa seguinte falha ou fica incerta.
Os testes adicionados exercitam captura real e concorrência PostgreSQL com
catálogo e alteração comercial. Isso não prova serialização de todos os escritores
nem autoriza o provedor real.

### Recuperação sem reserva e concorrência — 29/10/2026

`VisualAdmissionRecovery` cobre uma queda entre a admissão owner e a reserva
correlator usando somente as tabelas, locks e roles existentes:

1. Consulta o run com o ator original e o gate owner, sem transferir sua autoria.
2. Em outra transação, bloqueia a prévia fake e depois o ledger tenant. Exige
   prévia falhada, lease vencida ou fence substituído, sem arquivo/hash concluídos,
   e prova ausência de tentativa e de reserva, inclusive uma reserva não vinculada.
3. Marca a prévia como `failed`/`VISUAL_ADMISSION_ABORTED` e grava auditoria.
   O commit impede reserva e conclusão por um worker atrasado antes de liberar
   qualquer alteração de fonte pendente.
4. Somente após confirmação do commit correlator chama `finish` owner com o
   fence original. Crash/confirmação perdida permite repetir essa reconciliação;
   a auditoria da prova terminal não duplica, e a geração nunca é retomada.

Uma duplicata de execução ainda viva retorna `skipped`, conservando o trabalho
original. Reserva existente ou incerta impede a liberação; uma liquidação sem
confirmação também conserva a admissão. O renderer usa a recuperação ao reencontrar
um run no redispatch e após uma falha conhecida sem reserva. Registros já fora
da fila (prévia vencida, falhada ou tentativas exauridas) exigem invocação interna
explícita do serviço; ainda não existe varredura automática nem ação web/staff.
O autor sem acesso continua bloqueado conforme C10, adiada.

Reserva e claim verificam `clock_timestamp()` após adquirir os locks, em nova
instrução. A reserva verifica novamente após os locks financeiros e reverte
tentativa/reserva/total agregado se os prazos venceram durante a espera. Os testes
usam PostgreSQL restrito e cobrem locks da prévia, do tenant e do agregado, sem
submeter imagem. Tetos concorrentes por tenant e agregado são exercitados com
run owner real → tentativa correlator; custo incerto conserva a reserva e custo
tardio comprovado ajusta apenas a diferença, sem crédito duplicado.

A composição kit/logo também tem prova: upload de outro logo imutável não muda a
fonte pronta; draft e confirmação participam do gate; confirmação espera os runs,
bloqueia novos inícios e cancela a fila anterior. A prévia concluída continua
revisável com o kit/logo anterior. A recuperação de PUT incerto de logo ainda
pendente continua operacional; a parte 1 abaixo coordena edição/revisão de roteiro.

A consulta e o download para revisão preservam concluídas após o prazo da prévia
ou da proposta, sem usar esse acesso como autorização de geração/publicação.
O purge conserva seus objetos e a reconciliação conserva propostas, versões de
roteiro e snapshots referenciados como proveniência. No modo visual, revisão
após vencimento financeiro exige prova do run, fence e resultado concluído,
além de identidade e permissões das fontes. O prazo de aprovação permanece
independente; uma candidata vencida não ganha nova autorização por ser preservada.
Antes do rollout, drenar os workers antigos de limpeza e revisar suas leases.
Registros legados em `purging` com chave e hash conhecidos não são reclamados
pela limpeza nova; conservam estado e bytes para conciliação manual. Não inferir
que um arquivo já apagado foi recuperado. A revisão visual por outro owner ainda
pode depender do ator/vínculo original, e permanece fora deste recorte.

A fila durável de alterações cobre atualização/restauração do
contexto, catálogo, confirmação de kit e criação/alteração/exclusão de fotos do
acervo. Bloqueia novas admissões, espera as iniciadas e preserva a prévia anterior
com indicação visível. Erros previstos mantêm a alteração explícita e o bloqueio.
Edição/revisão de roteiro e writers financeiros são cobertos pela parte 1 abaixo;
logo ready é imutável e novas capacidades de acesso devem seguir o protocolo.
A decisão C10 já definiu recuperação exclusiva
pela equipe da plataforma, com ação registrada/auditada. Esta fatia recusa que
outro owner substitua ou descarte a pendência do autor original. A recuperação
staff foi adiada pelo proprietário em 29/10 para evolução de gestão de acesso e
suporte. Não bloqueia o encerramento da fatia simulada já validada. Até sua entrega,
a pendência excepcional continua bloqueada; nenhuma nova permissão foi aprovada.

Upload do acervo reserva a alteração antes de transferir, sem rede sob row lock.
Após vencer a reserva, o autor pode descartar upload incerto; a chave fica privada
em quarentena e a próxima operação usa outra chave. Retomada exige prova persistida
de PUT de tentativa única. Não há limpeza física automática da quarentena nem
fluxo de suporte para recuperar a pendência se o autor perder acesso. O rollout
requer drenagem e avaliação dos órfãos legados conforme o [procedimento](../design/BL04-quarantine-rollout.md).

## BL04.2 — parte 1: guarda concreta e escritores coordenados

`DatabaseVisualEffectGuard` e `GuardedVisualSubmissionClaims` implementam a prova
owner de fontes/aceite/run, reserva por tenant/agregado, claim única com revalidação
financeira/de identidade e commit privado por versão/fence/hash. As duas roles
continuam com commits separados; run durável conserva as fontes entre eles.
O [protocolo e inventário dos escritores atuais](../design/BL04-effect-guard.md)
documenta a ordem dos locks, o ponto de início durável e as falhas conservadas.
Não foram criados grants, roles ou tabelas para contornar a fronteira.

Edição e revisão de roteiro agora enfileiram comandos e conservam a versão atual
durante a criação. Após o commit de finish, a aplicação adquire proposta → visual
em outra transação; nunca adquire proposta a partir do gate visual. Leituras do
autor retomam aplicação pendente. O editor é ferramenta interna DEV; a IA cria o
roteiro a partir do WhatsApp/contexto, e o cliente revisa a peça. O laboratório
aguarda alteração de outra fonte pendente/falhada, conservando o formulário para
retry. Contratos opcionais `pending_change` e polling não antecipam sucesso.

`BillingProcessor.save` participa do lock comercial antes de mudar acesso.
Revogação de patrocínio usa o relógio real após a espera. Usuário/membership são
revalidados; não há writer runtime ou grant de atualização de active/papel de
cliente. Fontes WhatsApp processadas, transcrição concluída, logo ready e briefing
preparado são imutáveis nos fluxos atuais; mudanças de seleção usam comandos
coordenados. Upload de logo pendente é evolução de órfãos, não fonte selecionável.

Troca de telefone não muda mais o fingerprint de material já atribuído (C05),
e a entrega usa o vínculo novo verificado. Drenar fila/criações com fingerprints
antigos antes do rollout; concluídas antigas mantêm revisão por prova durável.

O orquestrador instala/restaura `admitted_visual_run` e distingue efeito terminado
de custo liquidado. Resposta conhecida permite concluir o run sem liberar custo
incerto. Resposta tardia não vence fence novo; confirmação perdida de claim,
reserva ou commit conserva prova/hold e, quando aplicável, objeto. Nenhum reenvio
automático. Na entrega da parte 1, essa guarda foi exercitada somente com
simulação persistida; a parte 2 acrescenta o modo explícito abaixo.

## BL04.2 — parte 2: caminho completo conectado

O modo persistido/API `visual_ai` identifica geração pelo adapter de imagem,
sem confundir resultados com `local` ou `visual_fake`. A migration 0059 exige
fingerprint para ambos os modos visuais, preserva os registros existentes e
recusa downgrade com prévias `visual_ai`. Não altera grants; foi aplicada
somente ao banco `_test` na parte 2. Para a execução autorizada da parte 3,
também foi aplicada ao banco local da aplicação.

`DatabaseVisualGenerationRunner` liga o pedido ao preparo/normalização de fontes,
guarda concreta, reserva, claim única, adapter OpenAI, acabamento, storage privado
e commit por versão/fence/hash. A API somente enfileira: não faz chamada de imagem
nem precisa receber o pool correlator. O worker usa pools owner e correlator
restritos e registra workflow/activity visual apenas com a execução habilitada.
Os testes usam o adapter real com transporte HTTP simulado, PostgreSQL e Temporal
locais; storage/interpretação externos são simulados. Não houve chamada paga.
Essa é a validação da parte 2; a chamada controlada posterior está registrada abaixo.

A ativação exige desenvolvimento/teste e, com prefixo `MEU_BRACO_DIREITO_`,
`VISUAL_AI_MODE=openai`, `VISUAL_AI_EXECUTION_ENABLED=true`,
`VISUAL_AI_RESERVATION_USD_MICROS>0`, tetos mensal por tenant e agregado pelo
menos iguais à reserva, chaves de provedor/criptografia e enforcement do aceite
único C01. A flag é desligada e a reserva zero por padrão; configuração incompleta
é recusada e não troca a geração por um placeholder local. Seleção automática de
item/fontes exige a interpretação Jev existente, com sua chave/teto próprios;
correspondência lexical de candidatos não vira seleção automática silenciosa.

O fence/reserva são atômicos entre si. Fontes, aceite, plano e run compartilham
a transação owner; a reserva continua em outra transação/role.
Falha entre os commits conserva uma admissão bloqueante, sem reenvio automático.
Essa sequência não é uma transação única; a barreira durável e a claim coordenam
os escritores atuais conforme o desenho. Novas capacidades de acesso precisam
participar do protocolo, sem inferir novos privilégios de banco.

O dispatcher inicia `VisualGenerationWorkflow` com ID estável
`visual-preview/<preview>`, rejeição de duplicata e lease de 12 minutos. A activity
tem até dez minutos, espera de agendamento de um minuto e uma tentativa. Uma
confirmação de início perdida conserva a mesma identidade/fence; prévia real já
reclamada não é redispatchada. Lease vencida marca `VISUAL_OUTCOME_UNCERTAIN`,
conservando run/reserva e sem inferir que o provedor parou. Recuperação só libera
admissão após prova de ausência de tentativa e reserva; não há varredura automática
de todos os runs abandonados. `StaticPreviewWorkflow` conserva IDs/tempos antigos;
o patch `visual-preview-wait-v1` amplia a espera da candidata sem alterar replay
dos históricos anteriores. A revisão privada conserva resultados concluídos e
proveniência de ambos os modos visuais mesmo com execução desligada.

O ledger já possui teto mensal agregado de reservas OpenAI, além do teto por
tenant (`0049`). Valores incertos permanecem reservados. É controle das operações
que passam por esse ledger, não limite da fatura OpenAI nem cobertura de chamadas
externas ao fluxo. A guarda concreta já usa os tetos por tenant e agregado na
reserva; não é uma tabela ainda a criar. Resultado desconhecido exige prova/reconciliação;
lease vencido não demonstra que a chamada terminou. Não repetir nem trocar
provedor automaticamente após possível submissão paga.

O [desenho de atomicidade](../design/BL04-atomicity-proposal.md) registra as
lacunas e a ordem de locks existente; não copiar uma ordem comercial → visual
sem resolver as inversões atuais. Não há rede enquanto se mantém row lock.
Propostas anteriores de grants e retirada de consentimento por modalidade ficam
como histórico técnico, sem tornar novos controles de IA requisito do produto.

## BL04.2 — parte 3: primeira imagem real pelo produto concluída

O proprietário autorizou Café do Cedro com foto CC0 e logo, uma imagem e teto
total de **US$ 1**, sem publicação. A execução concluiu um feed `visual_ai`
1024×1280 com `gpt-image-2.5-flare-2026-09-08`, qualidade medium, Jev real,
guarda/claim/ledger, Temporal/worker e acabamento determinístico do kit/logo.
O JPEG foi obtido pela API autenticada e S3 privado; run `finished`, prévia
`completed`, candidata com decisão pendente e publicação nula. Evidência no
[relatório de 29/10](../evals/bl042-first-product-image-2026-10-29.md).

Foram **uma chamada OpenAI de imagem e duas interpretações Jev**, com estimativa
de uso de **US$ 0,029701** no conjunto. Não é fatura nem custo por peça aceita:
a reserva visual de **US$ 0,99** permanece `uncertain`, com custo efetivo
desconhecido (`actual_usd_micros=NULL`), sem crédito inferido
da resposta. A primeira interpretação retornou formato nulo e o baseline criou
story; o wrapper de autorização recusou esse formato antes de delegar ao HTTP,
com zero chamadas de imagem demonstradas. A reconciliação em zero dessa reserva
antiga e o término explícito do run preservaram tentativa, marcadores e auditoria.
Uma nova origem esclareceu foto/feed e legenda sob a mesma autorização; não
houve edição manual de roteiro, reenvio de imagem incerta ou aprovação/publicação.

A migration 0059 foi aplicada ao banco local para esse percurso. Flags
persistentes continuam desligadas, sem novos grants ou mudanças no código de
produção. Ingresso Meta e prova de canal continuaram sintéticos, com entrega de
candidata simulada: não é prova de WhatsApp completo nem homologação Meta.
Validação dirigida aprovada: 94 unitários e `make lint types` (151 módulos).
Owner listou/baixou o hash idêntico com geração desligada e limites zero;
acesso anônimo retornou 401. Os processos habilitados foram encerrados.
O último CI completo continua o da parte 2, sem repetição nesta execução.
Os testes C08/C09 permanecem a
evidência das suas demais condições; esta única imagem não as demonstra novamente.

## Próxima fatia de desenvolvimento

Esta seção registra o plano de 30/10 e as pendências então observadas; a frente
ativa é o ciclo de revisão de Reel no início do documento. A integração de
referências avançou até 0111, conforme o gate de 04/11 acima.

O banco de desenvolvimento foi atualizado da revisão 0059 à 0099 em 03/11,
após backups privados com leitura integral verificada. A API iniciada antes da
0099 precisa de reinício para reconhecer a nova revisão e confirmar prontidão.

**Direção de 30/10/2026:** usar pedido, fatos, kit, acervo, skill adequada e
referências externas aceitas quando disponíveis para construir briefing e pedir
ao modelo a peça final completa. Conferir a peça produzida e oferecer trace
privado; não tratar texto no prompt como prova de que preço ou marca aparecem
corretamente. À época, a indicação manual estava implementada localmente e a
pesquisa e aceite de sugestões ainda não estavam entregues; a integração local
e o piloto posteriores estão registrados no gate de referências acima. A
ideia posterior de orientar seleção de fontes e
formatos do kit está registrada para estudo no
[plano de skills e referências](../design/skills-e-referencias-editoriais.md).
Conforme C18, uma oferta explicitamente promocional informada no WhatsApp é
fato para aquela criação e suas revisões. Exemplo: R$ 19,90 no pedido com preço
de catálogo R$ 25 não exige confirmar a diferença nem altera o catálogo. Para
um desconto percentual é necessário preço válido de catálogo; informação
ausente ou ambígua exige esclarecimento. Promoções, ofertas e horários não terão
cadastro na interface; o campo simples de características gerais permanece.
O titular autorizou remover informações antigas dessa área sem preservar
histórico. Essa jornada ainda não está implementada: o WhatsApp/Jev não extrai
e vincula integralmente os fatos, e o código de promoções do catálogo permanece
legado; novos snapshots editoriais ignoram essas promoções. Não presumir que a
peça atual já aplica a regra.

A implementação local descontinua novas gerações de fundo/overlay e snapshota
`full_piece_v1` por prévia. Skill editorial, logo autorizada, fotos e um exemplo
do kit demo entram no pedido completo; o provedor devolve a peça inteira. O
trace é cifrado e owner-scoped; a API exige checklist humano por hash antes da
aprovação. Checagem automática da imagem, checklist no WhatsApp/web, múltiplos
fatos temporários, análise dos concorrentes e avaliação de qualidade real permanecem abertos.

A busca começa no raio solicitado, uma vez por raio por ciclo, com até dez
candidatos por raio, sem prometer 30 negócios únicos; falha comprovada não
consome tentativa. Pela decisão de 04/11, Google vazio amplia automaticamente
de 5 para 20 e depois 50 km. Se todos vierem vazios, permitir nova tentativa
sem iniciar seis meses; os limites financeiros continuam valendo para a sequência. O cliente verá até dez candidatos elegíveis, com até três
recomendações do Jev destacadas com critérios e nota quando houver candidatos suficientes,
e escolherá de uma a três entre os exibidos, podendo combinar raios. A primeira
confirmação inicia um prazo comum de seis meses; cada raio pode ser pesquisado
uma vez no ciclo, mesmo após confirmação em outro raio. Todos ficam disponíveis
ao fim do prazo original; mudar endereço ou segmento não libera raio já pesquisado.
Trocas não renovam o prazo e a seleção permanece até outra confirmação; as
referências ainda selecionadas de ciclos anteriores podem ser combinadas com as novas. @ manuais
são adicionais. O Apify não deve repetir consultas bem-sucedidas a negócios já
encontrados durante o ciclo, mas pode consultar negócios novos de outro raio e
repetir tentativa que falhou sem retornar o perfil. O titular quer
guardar até dez negócios apresentados por pesquisa, com Place ID, nota própria
e perfis disponíveis. Confirmou que apenas Place ID será persistido dos dados
Google, usando estrelas e contagem somente como entrada para a nota; confirmou
também que a nota própria e a associação dos perfis do Apify podem ser guardadas.
Até vinte Place IDs/notas podem ser guardados temporariamente para recuperação,
com filtro de semelhança antes do cálculo; a lista exibida continua até dez.
O nome exibido virá do Apify quando houver; na ausência, mostrar o perfil ou
outro identificador disponível, sem persistir o nome fornecido pelo Google.
O titular esclareceu que cada rodada forma até dez candidatos pela mesma regra a
partir da nova resposta Google. Negócio reencontrado usa a nota mais recente na
nova lista, com notas de pesquisas anteriores preservadas no histórico. Se uma
referência escolhida ficar fora dos dez, o cliente decidirá se a mantém; essa
jornada ainda não existe no fake. Nesta primeira versão só serão considerados perfis do Instagram;
um único perfil retornado pelo Apify será usado automaticamente, sem exigir
confirmação. Com várias opções, usar o principal indicado ou, se não houver, o
primeiro retornado; o cliente pode informar outro @ se estiverem incorretas. O titular deseja
analisar via Apify até 20 publicações recentes do feed por perfil, incluindo imagens
e legendas públicas acessíveis quando disponíveis. Somente padrões extraídos serão
guardados, sem cópias de posts; acesso parcial será utilizado e identificado como
tal, e os padrões serão atualizados automaticamente a cada seis meses. Jev destacará até três negócios considerando
semelhança e nota; a interface mostrará critérios e nota, sem frase livre. Candidatos
com semelhança incerta ficam fora; não há nota mínima de corte.
A pesquisa nacional não será oferecida. Negócios sem @ devem ser
exibidos e o cliente poderá informar o perfil. O @ informado já é uma referência
escolhida, mas não se deve afirmar que foi verificado. Falha ou limite de acesso
a perfil público deve ser informado e permitir nova tentativa posteriormente.
Essas capacidades automáticas ainda não existem no produto real. Os eventos transacionais de
criação e remoção de referências ficam pendentes na outbox, sem consumidor;
seu acúmulo deve ser resolvido antes da operação continuada. Places é a fonte da
busca inicial e Apify é previsto para enriquecimento; custos, acesso,
correspondência e cobertura ainda precisam de integração. A infraestrutura fake, desligada
por padrão, exercita via Temporal os raios 5/20/50, a confirmação de uma a três
fixtures anônimas, pesquisa de raios ainda não usados durante os seis meses,
troca sem renovação, preservação da
seleção, compensação de falhas e reconciliação de autor revogado. Isso não cria
nem valida candidatos reais. Os adapters Google Places multitype e Geocoding estão
isolados/desativados e ainda não integrados ao produto;
geocodificação real e confirmação do ponto manual continuam necessárias para
raio; avaliações não medem engajamento. Um adapter de consulta de perfil via
Apify também foi preparado isoladamente e permanece desativado, sem integração
ou guardião real. A indicação de perfil não encontrado, com fonte não comprovada,
é inconclusiva; o adapter não comprova associação ou análise dos posts. A
plataforma conserva apenas padrões derivados; não há etapa obrigatória de
exclusão dos armazenamentos internos do Apify, conforme decisão do titular. Adapters isolados e
desativados para enriquecimento via Place ID no Apify e para mapeamento de tipos
fornecidos com Jev não comprovam titularidade, oficialidade da taxonomia ou
qualidade semântica; precisam de guardiões concretos e integração. Ver
[simulação](../design/reference-discovery-simulation.md).
Durante a implementação das fases seguintes, foram preparados o vínculo exato
do pedido Places e da credencial à intenção e à reserva, o teto compartilhado
do ensaio, e uma cadeia Google → Jev → filtro e gravação privada exercitada
somente com HTTP simulado. A reserva do Jev e o lote filtrado têm identidade
durável, RLS e proteção contra reenvio; até dez posições finais têm armazenamento
privado sem publicação. Há também contrato puro para projetar aprendizados, sem
coleta nem conexão à geração. A admissão da pesquisa real, a recomendação de três,
o Apify, publicação e conciliação permanecem
pendentes; estas preparações não habilitam provedores nem concluem uma fase real.
A leitura interna das listas publicadas e seleções foi testada com dois titulares,
RLS e histórico; ainda não está disponível no produto.
A admissão privada por localização de dispositivo e os ciclos reais separados
do fake foram preparados e testados sem despacho. Uma função interna ainda sem
grant libera o raio se nenhuma intenção de fornecedor existir; outros estados
conservam o raio até comprovação adequada. A seleção real que inicia os seis
meses continua sem acesso ao produto.
O titular confirmou raios 5/20/50 e início manual da próxima busca quando o
prazo terminar. Referências anteriores fora dos dez exigem decisão apenas no
início de nova rodada, sem repetir a pergunta para outro raio do mesmo ciclo.
O próprio negócio será excluído das sugestões, identificado por
nome e endereço quando houver correspondência clara e com confirmação apenas na
dúvida. Um comparador conservador foi testado isoladamente; vínculo e integração
ainda faltam. Empates na décima posição serão resolvidos pelo Jev por
semelhança; os três destaques combinarão semelhança e nota. Os titulares ativos
compartilharão as referências. Endereço e coordenadas do próprio negócio devem
permanecer no cadastro. O aprendizado abrangerá
tom, temas, formatos e elementos visuais, considerando todas as imagens
acessíveis dos carrosséis; perfil novo é analisado após confirmação e atualizado
a cada seis meses.
Essas regras ainda não estão integralmente implementadas.
O desempate possui adapter simulado, ainda sem orçamento, prova das candidatas
e publicação. Na abstenção, usar a ordem da resposta Google; a conclusão de
semelhança do Jev poderá ser guardada para recuperação sem nova pesquisa.
Um carregador restrito de contexto confere identidade, evento e versão vigente
e retorna somente dados necessários em memória; falta conectá-lo à activity.
Um adapter separado prepara coleta de até 20 publicações de imagem/carrossel do
feed por perfil usando HTTP simulado. Imagens e legendas retornam apenas em memória;
análise e conexão com efeitos pagos permanecem pendentes. O titular optou pelo
fluxo de chamada/resposta sem etapa obrigatória de exclusão no fornecedor; a
plataforma não persistirá as publicações coletadas.
O titular escolheu testar pontuação de 0 a 10 baseada em nota e quantidade,
sem armazenar os campos originais. A restrição anterior de não pontuar menos de
dez avaliações foi revista: pode-se calcular a partir de uma avaliação; sem
média ou avaliações disponíveis, o código atual não pontua nem inclui o
candidato, conforme confirmação do titular.
O titular confirmou em 03/11 que continuará testando e calibrando a
segunda fórmula; ela penaliza pouca evidência sem elevar a média e tem peso
provisório. A descoberta fake
aplica semelhança predefinida na fixture e grava a nota integral e as versões
da fórmula e fixture por pesquisa antes da leitura ordenada. Isso não implementa
avaliação real pelo Jev nem ordenação de candidatos reais.
Ver [avaliação](../evals/reference-reputation-eval-2026-10-31.md).
A fórmula final ainda não foi definida e a nota própria ainda não foi integrada
à descoberta real. Jev deverá eliminar candidatos inadequados antes de
pontuar os restantes. O titular escolheu limite financeiro por pesquisa, por
fornecedor e mensal total em UTC; valores e ativação continuam explícitos.
Política compartilhada, reservas e consumidores de efeitos fictícios foram
testados isoladamente, com retenção de resultado incerto e sem política ativa
por padrão. Isso não integra providers reais nem comprova conciliação de fatura;
parâmetros e identidade reais, chave HMAC versionada e provisionamento restrito
continuam pendentes. Trocar a chave fictícia com operação pendente interrompe o
processamento até restaurar a chave anterior, sem liberar uma reserva existente.
Na [prova pontual Nearby](../evals/google-nearby-order-probe-2026-10-30.md),
`POPULARITY` não correspondeu simplesmente a ordenar pela contagem quando a nota
era igual. As reservas Places somam US$ 0,280, sem comprovar fatura; o registro
da prova não salvou nomes ou respostas brutas.
Suporte real continua limitado a desenvolvimento/teste e desligado por padrão.

**Preparação de três cenários em 29/10:** foi ligada ao percurso visual uma orientação
experimental de skill para feed/story, selecionada por prévia somente em
desenvolvimento/teste e desligada por padrão. A migration 0060 adiciona ID/hash,
protegidos pela identidade do pedido e revalidados no preparo/acabamento. Naquela
etapa não integrava o briefing editorial completo; o caminho automático do
WhatsApp ainda não escolhe skill. O A/B local usou a mesma origem e segunda prévia selecionada
internamente. Três negócios e seis prévias passaram com provedores simulados e
PostgreSQL/Temporal locais; o evento de imagem entra já processado e a foto do
acervo é cópia dos mesmos bytes, sem provar webhook Meta ou retrieval entre fotos
distintas. O ensaio real subsequente gerou seis prévias com Jev e imagem reais:
todos os pares omitiram o preço confirmado solicitado. Naquele ensaio a skill
orientava a imagem e a copy seguia baseline. O contrato editorial real foi
alterado para solicitar ao modelo texto da arte, legenda e CTA, com vínculo a
fato confirmado ou preço válido do catálogo e rejeição sem fallback fixo. O
modo simulado continua separado. A barreira lexical daquele ensaio não verificava
sentido e não substituía revisão humana. O pedido de preço ainda não tem
interpretação estruturada que garanta sua inclusão; teste real do novo caminho
integral segue pendente.
[Evidência](../evals/three-business-visual-ab-2026-10-29.md).
Validação da correção com provedores simulados: `make ci` aprovado com 1.969
testes, 100% de linhas e branches, Ruff/formatação e mypy em 152 módulos.
Ensaio real isolado posterior produziu seis peças: preço em quatro artes, mas
não nas duas de manicure, e copy artificial em café/delivery. A skill permaneceu
restrita à imagem e cada par compartilhou a proposta; o executor não exercitou
seleção factual ou jornada completa. CI não repetido por orientação do titular.
[Evidência](../evals/editorial-copy-visual-after-2026-10-29.md).

1. **Skills para geração:** estudar e especificar as primeiras skills de feed e
   story; compará-las com o baseline em casos fictícios e integrar versões
   aprovadas à geração com kit, contexto e acervo pertinentes. No repositório
   separado `meu-braco-direito-skills`, há instruções iniciais para feed/story,
   quatro casos fictícios e protocolo de comparação. Validação estrutural e dois
   exercícios independentes passaram, sem comparação com baseline ou geração
   paga; a integração ao produto e a qualidade comercial continuam pendentes.
   Uma sonda exploratória posterior confrontou baseline isolado e saídas de
   agentes, com entradas e contratos diferentes. A skill de story não perguntou
   sobre serviços ambíguos; uma alteração dirigida e uma repetição independente
   corrigiram o caso observado. Não é comparação controlada nem prova de ganho.
   Ensaio pareado real de texto sob teto de US$ 5 foi interrompido na primeira
   tentativa incerta, sem saída e sem custo conhecido; ledger e hold preservados.
   A [evidência](../evals/skills-paired-attempt-2026-10-29.md) não autoriza
   reenvio ou avanço automático. Comparação controlada segue pendente.
   Um novo ensaio visual isolado, sob teto próprio de US$ 5, gerou duas peças
   de feed para caso fictício com e sem skill, mesma foto/kit/acabamento; duas
   chamadas textuais orientaram as cenas. Não usa o worker nem comprova ganho,
   aprovação comercial ou custo por peça aceita. [Evidência](../evals/skills-visual-comparison-2026-10-29.md).
2. **Pesquisa e referências externas:** completar a descoberta automática de
   negócios semelhantes em destaque além da indicação manual já implementada; avaliar
   fontes, permissões, métricas e relevância antes de aplicar padrões à geração.
   Jev deve avaliar semelhança e eliminar candidatos inadequados antes de aplicar
   a pontuação aos restantes e explicar até três recomendações destacadas entre
   os até dez candidatos exibidos, com fonte e uso permitidos;
   isso ainda não está implementado e não mede engajamento social. Referência não autoriza cópia;
   seu estudo pode começar após a comparação simulada das skills, sem esperar
   o fechamento integral do gate comercial BL04.3.
3. **BL04.3:** integrar padrões externos aprovados como referência e avaliar
   post/story pelo produto com titular e fontes autorizadas, incluindo revisão
   do feed já produzido. Medir pertinência, fidelidade, legibilidade, texto
   literal, rejeições, refações e custo por peça aceita. Uma chamada bem-sucedida
   ou um teste fictício não encerra esse gate.
4. **BL05:** WhatsApp como jornada principal de prévia, ajuste, aprovação e
   publicação simulada, incluindo proatividade sem nova mensagem. BL03.3 não
   bloqueia esta sequência. Novas chamadas precisam de autorização de gasto;
   a execução delimitada da parte 3 não habilita uso recorrente.

As fases, hipóteses e gates de skills e referências estão no
[plano editorial](../design/skills-e-referencias-editoriais.md). A escolha de
viabilidade e os termos das fontes automáticas permanecem abertos;
o cliente indicar um perfil não substitui a descoberta automática pretendida.

C10, recuperação automática fora do redispatch, limpeza física de PUT incerto e
suporte operacional seguem como evoluções próprias, com exceções bloqueadas até
prova segura. Não são novos poderes concedidos nem autorização para duplicar
um efeito. Retenção pós-encerramento continua adiada, sem exclusão automática.

**Adiada em 29/10/2026:** recuperação exclusiva e auditada de staff para autor
sem acesso (C10), na evolução de gestão de acesso/suporte. A proteção que impede
outro owner de assumir ou descartar a pendência permanece entregue. Até a entrega
futura, conservar a exceção bloqueada. A [proposta](../design/BL04-staff-recovery-review.md)
fica como referência, sem aprovação de novas permissões. O adiamento permite
encerrar o recorte simulado validado; os demais gates da BL04/provedor real continuam.

## BL04.3 — qualidade e economia: pendente

### Ponto de retomada histórico — 04/11/2026

O gate de qualidade de feed/story permanece pendente. A frente ativa atual é o
ciclo de revisão de Reel acima; a rodada exploratória mencionada foi executada
posteriormente, com limites e revisão pendente no relatório da BL04.3.

**Próximo trabalho: preparar a avaliação BL04.3 em quatro passos abaixo.** A
implementação local das referências está concluída até 0111, com 4.734 testes e
100% de linhas/ramos. As skills iniciais de feed/story já estão integradas. O
piloto de referências comprovou descoberta, escolha, análise e padrões no
snapshot, mas não gerou nem avaliou uma peça final usando esses aprendizados.
A nova rodada comparativa de qualidade ainda não foi executada.

O contexto a avaliar reúne pedido, informações do negócio, acervo, kit, skill e
aprendizados das referências. Referências orientam a criação; fatos, produto,
local, preço, logo e identidade continuam vindo das fontes do próprio negócio.
Testes de software aprovados não demonstram ganho criativo ou aceite comercial.

### Quatro passos da avaliação

1. **Conferir os aprendizados extraídos.** Inventariar as referências escolhidas,
   versões de associação, padrões, datas e cobertura da análise. Conferir se os
   padrões de tom, temas, formatos e elementos visuais descrevem as evidências
   acessíveis. Registrar concordâncias, erros e pontos não verificáveis. Não
   inventar conteúdo para um perfil indisponível nem arquivar suas publicações.
   Saída: quadro de revisão dos aprendizados aptos a entrar no ensaio.
2. **Gerar uma comparação controlada com e sem aprendizados.** Preparar casos
   de feed e story com o mesmo pedido, contexto, acervo, kit, versão da skill,
   modelos e configurações nos dois braços. A variável do par é a inclusão dos
   aprendizados, tanto no editorial quanto no visual. Usar fixtures autorizadas
   e as guardas do produto, sem enfraquecer snapshots ou revalidação de fontes.
   Registrar inputs versionados, operações, peças e custos de cada tentativa.
   Uma única amostra por braço é exploratória e não comprova ganho geral.
   Saída: pares comparáveis de arte e texto, com limites do ensaio explícitos.
3. **Avaliar as peças lado a lado com o titular.** Revisar no celular identidade,
   fidelidade ao produto/local, clareza e literalidade do texto, preços, CTA,
   logo, legibilidade, composição, originalidade e utilidade para o pedido.
   Registrar preferência, aprovação, rejeição ou necessidade de ajuste, com
   motivos. Avaliação automática pode auxiliar, mas não substituir esse aceite.
   Saída: revisão humana por peça e comparação documentada dos dois braços.
4. **Corrigir os problemas medidos e repetir.** Ajustar briefing, seleção de
   contexto ou instruções conforme os erros observados, em fatias revisáveis.
   Reexecutar os casos afetados com versões rastreáveis, preservando tentativas
   anteriores e registrando rejeições, refações, latência e custo completo por
   peça aceita. Distinguir reserva, estimativa e custo informado; nunca reenviar
   uma operação incerta como se fosse uma tentativa nova. Saída: correções
   validadas e relatório que explicite ganho, regressões e limites encontrados.

### Orientação histórica para a retomada de 04/11

Ler as instruções dos dois repositórios e inspecionar Git/código, preservando as
alterações existentes, inclusive as já staged. Começar pelo inventário dos casos,
aprendizados e executores de avaliação disponíveis; preparar o quadro do passo 1
e um plano revisável do passo 2 antes de qualquer chamada paga. Não reimplementar
a feature de referências nem retomar pendências de seus marcos históricos.

O plano deve informar casos, fontes/kit, formatos, quantidade de pares/tentativas,
modelos/configurações, critérios de aceite e estimativa de gasto. Apresentar as
escolhas de produto ainda abertas em entrevista, como solicitado pelo titular.
Conferir autorização e orçamento aplicáveis antes de executar: os US$ 5 do piloto
Google/Apify/Jev não autorizam esta nova rodada de geração de imagens. Tetos dos
ensaios antigos não devem ser renovados ou reaproveitados automaticamente.
Preparação local e documentação podem avançar enquanto essas escolhas são resolvidas.

Reutilizar aprendizados persistidos quando adequados, sem reiniciar ciclos,
reescrever resultados históricos ou refazer Google/Apify apenas para QA. No piloto,
a referência sugerida ficou indisponível e a manual tem nove padrões com análise
parcial; essa distinção deve continuar explícita. Flags persistentes permanecem
desligadas. O banco local está em 0111; testes de banco continuam exclusivamente
em bases novas `_test` com roles restritas, sem limpar o banco da aplicação.

Consultar antes de preparar o ensaio:

- [Piloto de referências e seus limites](../evals/reference-feature-pilot-2026-11-04.md).
- [Comparação editorial/visual anterior](../evals/editorial-copy-visual-after-2026-10-29.md):
  texto artificial, CTA e preços exigiram atenção; os pares compartilhavam a
  proposta editorial e variavam apenas o visual, limitando a conclusão.
- [Tentativa pareada interrompida](../evals/skills-paired-attempt-2026-10-29.md):
  conservar a operação incerta e sua reserva; não reenviar para iniciar a nova rodada.
- [Kit de QA Ateliê Aurora](../evals/kit-atelier-aurora-v1/README.md): existe como
  fixture independente, mas ainda não está no catálogo/executor; não presumir
  essa integração nem usá-lo como se já estivesse disponível no produto.

Registrar o plano e os resultados em um relatório datado em `docs/evals/`, com
links aos artefatos privados autorizados, sem credenciais ou publicações das
referências. Avançar automaticamente entre os quatro passos dentro do escopo e
orçamento autorizados, avisando ao concluir cada passo. Dúvidas de produto devem
ser feitas em entrevista. BL05 continua posterior à avaliação BL04.3.

### Critérios de fechamento preservados

O trabalho com dados fictícios prepara a avaliação e não comprova aceite comercial.
Gerar ao menos um post e um story novos para um caso com fontes autorizadas;
revisar no celular com titular. Medir identidade, legibilidade, texto literal,
fidelidade de produto/local, rejeições, retrabalho, todas as tentativas e custo
completo por peça aceita. A hipótese econômica é R$ 99/mês e custo total máximo
pretendido de R$ 50 por cliente/mês, incluindo serviços, infraestrutura e suporte;
não foi demonstrada. Vídeo, motion e avatar não integram automaticamente essa oferta.

Um lugar/produto inventado não pode aparecer como fotografia documental do
negócio. Referência visual não comprova fidelidade por si só; texto, preço, CTA
e logo precisam de conferência literal. Cenas conceituais devem ser identificadas.
Os [casos fictícios de QA](../evals/manual-qa-negocios-ficticios.md) preparam
cenários, sem substituir os gates de qualidade e aceite.

## Evidência datada e histórico

- Parte 3, primeira imagem: uma chamada real de imagem, duas Jev e JPEG privado
  pelo fluxo do produto, sem aprovação/publicação e com reserva de custo incerta.
  Meta de entrada/canal e entrega de candidata permaneceram simuladas. Estimativa
  total US$ 0,029701, sem fatura ou gate de qualidade comercial. Validação dirigida
  aprovada: 94 unitários, lint/types (151 módulos) e leitura/hash com geração
  desligada; CI completo da parte 2 não repetido.
  [Evidência](../evals/bl042-first-product-image-2026-10-29.md).
- Parte 2, conexão completa: `make ci` aprovado com **1.914 testes**,
  **100% de linhas e branches** (9.394 statements, 2.582 branches), Ruff/formatação
  e mypy (151 módulos). Web: **375 testes**, **100% nas quatro métricas**,
  build/formatação e **quatro jornadas Chromium** na árvore final. O percurso API →
  dispatcher → Temporal → runner/guarda → adapter com HTTP simulado → acabamento
  → prévia privada exercita modo persistido, fontes, versão/hash, revisão e
  orçamento; complementos cobrem resultado incerto sem nova submissão,
  continuidade/preservação e leitura com execução desligada. A migration 0059 foi
  aplicada somente ao `_test`; sem chamada paga ou novos grants.
- Parte 1, guarda concreta: `make ci` aprovado com **1.829 testes**, **100% de
  linhas e branches** (9.284 statements/2.550 branches), Ruff/formatação e mypy
  (149 módulos), PostgreSQL `_test`/roles restritas e Temporal locais. Prova de
  fontes/roteiro, finanças/acesso, relink por outro owner, validade factual após
  locks, claim única, resposta tardia e commits incertos. Web: 365 testes/100% nas
  quatro métricas, build/formatação e três jornadas Chromium. Sem chamada paga
  ou novos grants; à época, a próxima entrega era modo/API e wiring da parte 2.
- Recuperação sem reserva e concorrência, 29/10: `make ci` aprovado com 1.688
  testes, 100% de linhas e branches (8.989 statements, 2.462 branches), Ruff,
  formatação e mypy. PostgreSQL `_test`/roles restritas e Temporal locais; crash,
  confirmações perdidas, tentativa tardia, RLS/autoria, orçamento concorrente e
  custo tardio, prazos após locks e kit/logo. Nenhuma chamada paga, mudança web
  ou liberação da guarda real. Limites do consumidor de recuperação acima.
- Entrega anterior de admissão/continuidade/preservação: novos testes unitários e
  PostgreSQL para fontes e transição comercial concorrentes, plano vencendo após
  admissão, retenção/proveniência, prazos de aprovação e recusa de outro owner.
  `make ci`: 1.642 testes aprovados, 100% de linhas e branches (8.942 statements,
  2.446 branches), Ruff/formatação e mypy. PostgreSQL `_test` com roles restritas
  e Temporal locais; nenhuma chamada paga ou integração visual real habilitada.

- [Ensaio de feed de 27/10](../evals/bl042-guarded-synthetic-feed-2026-10-27.md):
  uma chamada com dados fictícios/CC0, US$ 0,026272 estimados; alterou logo e
  pontuação. Não usa worker do cliente nem comprova fatura, margem ou fidelidade.
- [Ensaio com acabamento de 28/10](../evals/bl042-synthetic-brand-finish-2026-10-28.md):
  US$ 0,020615 estimados, também isolado. A autorização de até US$ 1 para o ensaio
  fictício é histórica, não franquia comercial nem liberação de novos gastos.
- Aceite único: suíte backend de 1.583 testes e complemento de 24 execuções
  (sete testes novos), com cobertura final agregada de 100% de linhas e branches;
  web com 360 testes/cobertura integral, build e três jornadas Chromium. Serviços
  locais RLS/Temporal e efeitos externos simulados. Ver [CHANGELOG](../CHANGELOG.md).
- As decisões anteriores de descarte imediato de prévias, expiração dos envios
  WhatsApp e controles individuais de IA foram substituídas. As evidências originais,
  datas, contagens e propostas rejeitadas permanecem no snapshot desta fase e nos
  evals/changelogs; não são pendências de produto a reintroduzir.

## Cadastro de endereço próprio — 04/11

A API autenticada de endereço próprio conserva versões e exige controle de
concorrência e identidade de operação. Ela estabelece a origem declarada pelo
titular, sem copiar GPS ou origem de pesquisa. Geocodificação, persistência do ponto
comprovado e vínculo à identidade da busca permanecem pendentes; nenhuma chamada
externa foi habilitada. Ver [contrato](../design/business-address.md).

## 04/11/2026 — Classificação prévia de atividade

Taxonomia Google Table A versionada e adapter Jev pré-Google implementados
com uma requisição, código de tipo fechado e retorno de uso. O vocabulário
contém 478 códigos e foi conferido em fonte oficial; não usa `restaurant`
como padrão. Incerteza de categorias não escolhidas não impede um match válido.
Validação local: 66 testes unitários, 100% linhas/ramos dos dois módulos, Ruff
e tipagem estrita; sem efeitos pagos. Integração do guard e execução 0106 e
ensaio semântico real permanecem gates da descoberta completa.

### Fatia0103 — endereço, geocodificação e identidade própria

A API de endereço passou a ter início, consulta e confirmação de geocodificação,
com relay/Temporal e orçamento persistido. O ponto preciso é aceito automaticamente;
resultados ambíguos aguardam o titular. O endereço próprio e suas coordenadas
continuam no cadastro, e a origem manual de busca pode reutilizá-los com o custo
incluído na mesma pesquisa. O cadastro próprio é obrigatório na admissão real;
nome/endereço têm vínculo HMAC e são revalidados no carregamento, nos claims da
busca e na publicação. A validação usa serviços locais e transportes HTTP falsos,
sem gastar o teto autorizado. Ver [contrato](../design/business-geocoding.md).
A descoberta completa ainda precisa chamar o loader de identidade e tratar o
comparador, a ambiguidade, perfis e aprendizado; não declarar a feature concluída
por causa desta integração de endereço.

## Retomada 04/11 — integração até 0105

Resultados reais e seleção têm rotas autenticadas; publicação privada preserva
IDs/notas e exige revisão de escolhas ausentes só no início da nova rodada.
Correção manual de perfil possui versão, replay e auditoria. Endereço/geocodificação
e identidade própria foram conectados pela 0103. A execução completa Google →
Jev → Apify → publicação ainda está em integração, não concluída.

O custo por pesquisa agrega titulares; run Apify persistido permite consultar a
mesma coleta e reconciliar seu custo terminal sem novo POST. Adapter Compass
usa contrato oficial, build explícita e limite por execução. Os testes dirigidos
passaram; a suíte integral inicial terminou com 3.993 aprovados, duas falhas e
99,38% de cobertura, em correção. Falta validar a árvore final, conectar análise
de publicações/atualização semestral e aprendizados à criação, e executar o ensaio
fictício autorizado de até US$ 5 quando as credenciais locais estiverem disponíveis.

### Transporte real de feed, 04/11

Adapter Instagram e downloader de imagens preparados para o executor, com
network opt-in e controles de custo/identidade/limites. 357 unitários passaram
com 100% dos cinco módulos, Ruff e mypy aprovados. Publicações continuam apenas
em memória. Persistência de aprendizados, agenda Temporal semestral e uso na
criação ainda estão em implementação. Google vazio terá ampliação automática
5 → 20 → 50; ausência nos três permite nova tentativa sem iniciar seis meses, conforme
entrevista. A integração completa dessa ampliação permanece pendente.

### Configuração do piloto de referências, 04/11

O script `scripts/configure_reference_pilot.py` prepara a política local e o
piloto acumulado de US$ 5, sem zerar consumo ou habilitar fornecedores. Plano
por padrão; aplicação exige banco local/admin separado e preserva configurações
divergentes. 14 unitários e três testes SQL aprovados; execução real ainda pendente. Ver
[operação](../design/reference-pilot-operations.md).

## Revisão do baseline — 04/11/2026

A [retomada do CI](../evals/ci-resume-2026-11-04.md) identificou código morto
após C17/C18. Criação local permanece recusada, com auditoria/fence do job
legado e leitura privada histórica preservados. Geração editorial mantém o
percurso obrigatório de catálogo/skill e trace, sem alternativa sem skill
inacessível. Prova de role aceita o login restrito efetivamente configurado;
Temporal conserva timeout de 45s e diagnóstico apenas de estados/códigos.
3.555 testes relacionados passaram; o gate integral de 100% segue pendente.

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

### Fatia 0107 — identidade própria e busca vazia

Implementados: conclusão de identidade atômica com a evidência sanitizada; revisão compartilhada por titulares; exclusão antes do ranking/publicação; ampliação automática de respostas Google vazias; orçamento agregado por família; cache entre raios; resultado vazio terminal e retry sem iniciar ciclo não confirmado; histórico preservado. Estado canônico de família inclui a busca atual, sem inferência da UI.

Validação local usa PostgreSQL exclusivo `_test`, logins restritos e fornecedores simulados. Upgrade/downgrade vazio foi exercitado. Testes cobrem confirmação por segundo titular, rejeição de viewer/revogado, rollback atômico, exclusão antes do ranking, cadeia 5/20/50, limite financeiro da cadeia e replay depois de liberar o head. A entrega final continua condicionada à integração Temporal completa, análise de publicações/agenda e CI integral; esta fatia não demonstra chamada paga real.

Validação concluída da fatia: oito integrações e 45 unitários aprovados; 100% de cobertura em 149 linhas/30 ramos dos cinco módulos, mypy e Ruff. Roundtrip vazio 0107 → 0106 → 0107 aprovado. Cache compartilhado mantém dados históricos sem expor tokens.

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

Contrato e validação em [integração de referências na geração](../design/reference-generation-context.md).
177 testes unitários e 13 casos PostgreSQL passaram nos recortes desta fatia,
incluindo leitura 0108 e geração visual com HTTP simulado. Naquele recorte, a
agenda completa e o CI integral ainda estavam pendentes; essas provas não
demonstravam qualidade comercial. O CI vigente foi concluído em 09/11, conforme
o estado atual no início deste documento.

### 0108 — seleção, persistência e atualização dos aprendizados

A análise passa a ter associação de perfil, janela e evento duráveis derivados
da seleção real. Perfis manuais e sugeridos escolhidos usam a mesma autoridade;
correções de candidatos não selecionados não coletam publicações. Remover ou
trocar o perfil invalida a janela anterior antes de outro efeito. A agenda
semestral deriva do aceite, e resultados mantêm somente padrões próprios
comprovados, nome oportunista Apify e metadados. Captura/revalidação para geração
e leitura de status não confundem perfil escolhido com análise concluída.
As provas locais usam PostgreSQL isolado, roles restritas e fornecedores simulados.
Integração do executor, snapshot editorial/visual e tela vem nas fatias adjacentes;
ensaio real controlado e qualidade comercial continuam gates próprios.

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
