# Contrato de construção compacto v2

As duas tentativas da comparação das quatro melhorias foram interrompidas pelo
provedor como incomplete/max_output_tokens. Ambas entregaram plano completo e
scene_init truncado; não existe MP4 novo. A causa do limite reportado continua
indeterminada, pois a contagem de saída foi inferior ao teto solicitado/retornado.
A orientação textual de código mais compacto não resolveu.

## Fatia implementada

Novas capturas com direção fornecida usam provided-direction-output-v2. A v1
continua aceita integralmente e recapturas preservam a versão já armazenada.
Sem direção fornecida, o contrato anterior continua em vigor. Sem serviços,
tabelas, runners ou chamadas adicionais.

A v2 troca apenas a representação de cada beat na resposta: p=phase, s=start_ms,
e=end_ms, a=start_state, z=end_state, path=trajectory, c=curve, cue=speech_cue_id.
Curvas nomeadas podem usar string; cúbicas/springs mantêm kind/parameters. O
serviço expande o formato e restaura a direção, depois executa todas as validações
normais. Persistência, crítica, renderer, runtime e campos públicos permanecem
com o plano completo. Nenhum tempo, estado, vínculo ou curva é inferido/removido
pela expansão. Não há aceite automático de JSON truncado.

O contrato também orienta a não descrever holds redundantes entre ações, pois o
runtime mantém o estado nos intervalos; elementos totalmente estáticos continuam
com hold. Isso é orientação para próximas gerações, não reescrita de planos
existentes. Referências, fontes, bibliotecas, moldura, fundo, xícara e fala foram
preservados. O exportador explica a expansão v2 pelo decoder do produto.

## Evidência e limites

Medição offline sobre apenas o campo completo motion_plan da última resposta:
23.850 → 18.873 bytes JSON minificado (20,87%). Os 63 beats permanecem; a igualdade
exata do MotionPlan após expansão foi verificada. Código parcial continua inválido
para execução. Relatório em `.local/evals/motion-compact-wire-20261110/measurement.json`.
Não é medição de tokens nem garantia de evitar nova interrupção do provedor.

234 testes dirigidos aprovados (20 do contrato, 130 provider/plano/direção/exportação,
84 contexto/inputs/runtime/fala). Cobertura 100% de linhas/ramos nos dois módulos
medidos schema/service motion_generation. Mypy de três módulos, Ruff e diff-check
aprovados. Uma invocação inicial apontou arquivo de teste inexistente e não rodou;
foi corrigida usando test_motion_context_requests.py. Sem CI global, chamadas
pagas, imagem nova ou render da peça nesta fatia.

## Comparação preparada

Pasta `.local/evals/reel-four-improvements-compact-20261110/`, mesmo montador do
produto, 12 imagens e transcrição local prévia de 30 palavras, ainda não revisada.
Reserva proposta US$ 1,80: composição 0,65 + imagem 0,50 + crítica 0,65. Somada às
reservas anteriores US$ 2,15, máximo acumulado US$ 3,95 dentro do teto US$ 4. Saída
configurada até 54.000 tokens; preflight deve confirmar que a chamada cabe na
reserva. Nenhuma reserva anterior foi liberada. Autorização de tentativa extra
solicitada em entrevista, ainda sem resposta. Não criar pedido ou gastar antes
resposta afirmativa. Depois: uma execução, conferir MP4/áudio e comparação visual;
sem prometer qualidade ou sucesso antecipadamente.

## Atualização — 11/11/2026

O titular autorizou explicitamente mais uma tentativa de composição, imagem e
crítica dentro do mesmo teto acumulado US$ 4. Execução do contrato compacto v2
iniciada; verificação durável das duas tentativas anteriores mantém reservas e
limita o acumulado proposto a US$ 3,95. Sem tentativa adicional além desta.
Tentativa concluída: o schema compacto foi enviado, mas houve novamente saída
incompleta. Sem MP4. Evidências no relatório da comparação; não considerar essa
compactação uma solução já comprovada para a falha do provedor.

