# Café Pausa — alternância entre gravação e motion

Estado: primeira geração rejeitada antes do render; recuperação explicitamente autorizada. Nova autorização explícita do titular:
**US$ 3**, uma geração, render e crítica, sem imagens pagas ou tentativas extras.
Reserva de US$ 1,40 por chamada, máximo US$ 2,80. Orçamentos antigos não reutilizados.

## Entrada e execução

- Mesma fonte, áudio, kit, 11,2 s, 720×1280/30 fps, `gpt-6.1-sol`, high,
  limite de 64.000 tokens na geração e 8.000 na crítica. Sem storyboard/refações.
- Seis referências de acabamento e seis quadros da fonte. Skill v6, runtime v2,
  executor v2, criativo v7, crítica v3 com vínculos explícitos de problemas.
- [Direção](direcao-cafe-pausa-alternancia-2026-11-10.json) e
  [briefing](brief-cafe-pausa-alternancia-2026-11-10.txt): gravação dominante,
  xícara/preenchimento em tela gráfica inteira, retorno por vapor e convite.
- Pacote pelo montador: `.local/exports/motion-cafe-pausa-alternancia-20261110.zip`.
  Sem credenciais. Fatos históricos na exportação; execução recaptura contexto atual.
- Pasta privada: `.local/evals/reel-alternancia-20261110/`.
  `run_proof.py` controla API/outbox/Temporal, identidade nova e trava de execução
  única; não é um segundo runner de produto. JSONs de preparo/custo/resultado
  permitem inspecionar a prova sem expor credenciais.
- Pedido `f6b50e05-ee27-59a6-af68-02e7462c19bf`, admitido e despachado.
  Worker dedicado `mbd-motion-worker:alternancia-20261110`, imagem
  `sha256:e7701633e0f7abfbb2bf8b60e69f8d00372528595864b7329ca2507546ef19c0`.
  358 arquivos verificados; renderer isolado existente e sem credenciais.

A checagem inicial encontrou pasta temporária ausente, antes de qualquer envio.
Criada a pasta, a checagem passou. Dois quadros sintéticos comprovaram o conserto
do clipping com máscara explícita preservada; nenhum custo de modelo.

## Comparação e critérios

Baseline principal: variante anterior com reparo local,
`reel-semantic-recovery-20261110/local-repair.mp4`, SHA-256
`87533d1b0794f5d70c0fa5c71de2a73748f3f24227d0d67718e107b6440e876a`.
Ela foi avaliada positivamente pelo titular, mas não foi sucesso automático.
Preservar também a versão apenas tipográfica para comparação opcional.

Verificar: abertura com evidência real; intervalo gráfico sem janela residual;
retorno no tempo correto; xícara/elementos com ação e resultado; leitura/kit;
nenhum recorte acidental; áudio preservado; parecer válido sem vínculo inventado.
Não editar a saída manualmente e apresentá-la como sucesso automático. Guardar
respostas e falhas. Parecer válido não é aceite humano nem prova de fluidez integral.

## Evolução pedida durante a geração

O titular perguntou sobre objetos mais realistas, como uma xícara com aparência
3D. A execução já despachada mantém a direção e o orçamento sem imagens pagas.
A análise de viabilidade integra o
[plano de fechamento](../design/fechamento-produto-geracao-2026-11-10.md), sem
alteração silenciosa da chamada, geração de assets ou integração 3D nesta rodada.

## Feedback adicional após o despacho — skill v7

O titular observou fundo constantemente clean/inativo e vídeo com tamanho fixo,
apenas reposicionado para acomodar a xícara. Novos pedidos passam a usar skill v7:
coordenação do quadro inteiro, função narrativa do fundo, variação pertinente de
moldura, escala, máscara, entrada/saída e enquadramento da gravação. Não exige
saturação, textura, agitação ou todos os efeitos em toda marca. Kit, ação legível,
leitura e limites dos materiais prevalecem. Crítica usa checks/evidências existentes.

A rodada já despachada permanece na v6; não foi alterada nem reenviada. V7 é um
ajuste de orientação posterior, **ainda sem prova visual paga**, e não muda runtime
ou schema novamente. 66 testes de contexto/skills/exportação e dois exemplos Node
passaram após o ajuste, incluindo recaptura v6. Não atribuir à saída da primeira tentativa
a realização de instruções que não estavam em sua entrada.

## Resultado da primeira geração e recuperação autorizada

Resposta completa, mas inválida: `tempo-percurso` tem ações 2450–4050 e 2750–3550
sobrepostas; `pausa-texto` tem 7700–8150 e 7850–8450. O contrato exige beats
sequenciais por elemento. `MOTION_AI_RESPONSE_INVALID`, zero versões/MP4,
nenhuma crítica. O renderer não foi executado com código inválido.

Uso retornado: 26.323 entrada, 24.221 saída (13.384 raciocínio). Cálculo local
conservador US$ 0,308018; a resposta inválida não preencheu estimativa no ledger.
Reserva retida US$ 1,40. Raw e diagnóstico preservados; worker encerrado e env
removido. Não é erro de clipping nem de vinculação da crítica, que não foi chamada.

O titular autorizou uma recuperação e crítica dentro dos mesmos US$ 3. Reservas
novas US$ 0,75 + US$ 0,75; acumuladas máximas US$ 2,90. Nenhuma liberação de hold
para abrir espaço. Preparação verifica teto global/tenant contra a rodada original.
Pasta `.local/evals/reel-alternancia-recovery-20261110/`, identidade própria,
sem reenvio automático. Contexto v7 e nova direção incluem o feedback de fundo,
variação de moldura/escala e objeto volumétrico por código, sem asset 3D/imagem paga.

[Direção completa](direcao-cafe-pausa-cena-completa-2026-11-10.json),
[briefing](brief-cafe-pausa-cena-completa-2026-11-10.txt) e pacote pelo montador em
`.local/exports/motion-cafe-pausa-cena-completa-20261110.zip`. A instrução torna
explícito que ações simultâneas de partes do mesmo elemento pertencem a um beat
composto, sem sequências sobrepostas no mesmo ID. Guarda não foi relaxada.


Recuperação admitida pela API/outbox/Temporal: pedido
`64388205-11af-590a-b4bb-5264833c6d5f`. Worker com 359 arquivos, imagem
`sha256:8acddd24c85b3398f04cb948c8fe84f8c3dc2c66e80604352074f110baa9bf5c`.
Checagem sintética curta aprovada antes do envio. Payload preparado com 2.015.482
bytes, seis referências e seis amostras da fonte. Skill v7, runtime v2, crítico v3;
estado final registrado abaixo. Esta tentativa, ao contrário da primeira, recebeu
os critérios adicionais de fundo e enquadramento. Não alegar resultado antecipado.


## Resultado da recuperação e variante local

A recuperação terminou `failed/MOTION_AI_OUTPUT_LIMIT`, sem versão renderizada
nem crítica. Resposta `incomplete/max_output_tokens`; teto declarado 64.000,
uso retornado 27.116 entrada e 19.716 saída (8.286 raciocínio). A causa da diferença
entre teto declarado e saída interrompida não foi estabelecida. Não executar,
completar manualmente ou apresentar essa resposta parcial como composição pronta.
Estimativa durável US$ 0,264950; reserva US$ 0,75. Worker encerrado, env removido.

Total da rodada: duas gerações, zero críticas; estimativa conservadora
US$ **0,572968**, incluindo cálculo local da primeira resposta inválida. Reservas
retidas **US$ 2,15**; teto acumulado US$ 3. Nenhuma outra chamada paga executada.

Para entregar uma comparação, foi preparada uma variante **local** somente da
primeira resposta completa (skill v6), mantendo HTML e scene_init byte a byte.
As descrições simultâneas de tempo-percurso e pausa-texto foram reunidas em um
beat composto por elemento, com seus subintervalos documentados; não mudou o
relógio/código da animação. Validaram schema, direção e vínculos do plano antes
do renderer. A saída incompleta da recuperação não foi usada.

Operação local `85ff3e8e-919a-4bc3-90f5-3a63d7790a76`; renderer isolado existente,
runtime v2 selecionado pelo contexto original. Arquivos na pasta da primeira
rodada: `render_local_plan_repair.py`, `local-plan-repair-composition.json` e
`local-plan-repair-started.json`. Render posteriormente falhou, conforme registro abaixo. Não é versão aprovada no
produto; pedidos automáticos permanecem failed. A variante não recebeu crítica
paga nem as orientações posteriores da v7 sobre fundo/enquadramento/volume.

Os dois consertos têm prova dirigida e do mecanismo de clipping no Chromium;
a rodada real não alcançou a crítica v3. O próximo trabalho obrigatório é a
confiabilidade de geração completa/validável, antes de liberar a jornada a clientes.
Não tratar outro render local como fechamento desse gate.


A captura local integral atingiu `MOTION_RENDER_DEADLINE`: o runner limita a
captura a 600 s, independentemente do limite externo de 900 s. Não produziu MP4.
Para concluir o artefato comparável sem desabilitar controles, a captura local
foi dividida em 0–4 s, 4–8 s e 8–11,2 s, usando o mesmo renderer e seu limite por
execução. Um wrapper só traduz seek local para tempo absoluto; código original
intacto. Trechos são silenciosos, reunidos sem nova codificação do vídeo, e uma
única faixa original 0–11,176 s é codificada ao final. Não concatenar áudio por
trecho nem reiniciar o instante da gravação.

`render_local_chunks.py` e registros por trecho identificam essa montagem local,
com no máximo duas capturas simultâneas. Não é implementação de captura segmentada
no produto/Temporal, não muda o renderer de produção e não foi apresentada como
recuperação automática. Sem nova chamada paga; verificar frames, duração, áudio e
limites da comparação antes da entrega.


## Encerramento — comparação em vídeo não concluída

A captura segmentada falhou com `MOTION_RENDER_BROWSER_TIMEOUT`, sem seção MP4
persistida. O processo Python permaneceu aguardando cancelamento assíncrono após
a falha; não havia contêineres ou subprocessos de render ativos na inspeção. Foi
interrompido somente esse processo diagnóstico, preservando arquivos e evidências.
Não estabelecer causa específica do timeout sem reprodução isolada. Não elevar
limites ou mudar sandbox como correção presumida.

Não existe `local-plan-repair.mp4` nem comparação final de vídeo desta rodada.
`comparison.pending.html` é rascunho incompleto e não deve ser entregue como resultado.
Artefatos disponíveis em `.local/evals/reel-alternancia-20261110/`:

- `previas-parciais.html`: três quadros capturados aos 1, 3 e 4,5 s, com limites explícitos;
- `local-preview-1000.jpg`, `local-preview-3000.jpg`, `local-preview-4500.jpg`;
- `local-chunks-failure.json`: falha local e ausência de MP4;
- respostas originais, composição reparada e scripts diagnósticos preservados.

Esses quadros não comprovam continuidade, retorno da gravação, áudio ou qualidade
final. A entrega comparativa solicitada permanece pendente. Nenhuma outra chamada
paga foi executada. Próxima fatia: confiabilidade da saída e captura, incluindo
cancelamento do subprocesso, antes de nova prova paga ou liberação a clientes.


## Continuação autorizada — etapa 1 de confiabilidade

A comparação antes pendente foi concluída localmente, em captura integral de
99,35 s após pausa autorizada de cinco serviços em reinício contínuo. Os cinco
foram restaurados. Arquivo, inspeção e limites em
`docs/design/motion-confiabilidade-geracao-captura-2026-11-10.md`. Não houve nova
chamada paga, uso da resposta truncada nem alteração retroativa dos pedidos failed.
