# Recuperação motion — nova rodada autorizada

**Atualização posterior — MP4 de avaliação entregue.** Após ver a prévia, o titular
pediu “gere o video para eu ver como ficou”. Essa autorização foi vinculada aos
hashes da composição e do manifesto de diagnóstico. Renderizado o código já
recebido, sem edição manual, nova geração ou chamada paga, pelo executor existente
sob o workflow Temporal `MotionProductionWorkflow`, em fila dedicada temporária.
Nenhum controle de recaptura foi relaxado: o pedido original segue falho e não
recebeu aprovação fictícia no banco. O MP4 é uma prévia autorizada para avaliação,
não conclusão automática de qualidade, publicação ou recuperação concluída.

Arquivo: `.local/evals/motion-recovery-run-20261111/nova-peca-avaliacao.mp4`.
Player: `assistir.html` no mesmo diretório. SHA-256
`e4bfabe68500189d6cd147f440f8ef4f2bccabd6e3001dff08cebf9e7e5d47f0`.
1.242.383 bytes; H.264, 720 × 1280, 30 fps, 336 quadros/11,2 s. Áudio original
como única faixa, AAC/11,176009 s. FFprobe e decodificação completa passaram.
Plano/composição foram confrontados com o recibo recebido do backend; fonte,
kit, assets e áudio conferidos. Sem chamadas ao modelo/novos assets; estimativa
acumulada US$ 0,568106 e reservas US$ 2,50 não aumentaram por esta renderização.

Recibos: `mp4-preview-approval.json`, `preview-mp4-result.json`,
`preview-workflow-result.json` e `preview-verification.json`. Os cinco serviços
continuam `exited`, worker dedicado encerrado e índice Git preservado. Não houve
alteração de código de produção ou do estado do pedido nesta renderização.
Persistência do storyboard/estabilidade de recaptura, CI integral e aceite criativo
continuam pendentes. Os registros abaixo preservam o histórico da falha.

Data: 11/11/2026. O titular autorizou gerar a nova peça após receber a entrega
R1–R5. Aplica-se o teto novo da proposta: US$ 6,25, zero imagens novas e até uma
correção delimitada com nova crítica. A aprovação do storyboard continua
obrigatória antes do MP4. Orçamento antigo não foi reutilizado.

## Preparação e limites

- Montador real conferiu fonte, kit, áudio e saída; 20 quadros da base, seis da
  gravação, cinco referências e xícara original incluídos.
- 77 testes dirigidos passaram nesta rodada. Executor existente qualificado com
  vídeo sintético mínimo e storyboard, sem conteúdo do cliente.
- CI integral/100% de cobertura continua pendente conforme relatório R1–R5.
  A autorização posterior permite esta rodada operacional limitada; não é aceite
  de merge, implantação nem comprovação artística. Não se alterou código para
  contornar validações ou reduzir requisitos de CI.
- API autenticada, identidade durável nova, outbox e Temporal existentes, fila
  exclusiva e worker dedicado temporário. Cinco serviços interrompidos preservados.
- ASR local será registrado pelo workflow; chamadas pagas têm contagem real de
  entrada, reserva e limite por efeito. Sem repetição automática de chamada.

## Execução

Solicitação `2d6bc06c-d12e-5cac-afc8-66667f872dae`, admitida pela API (HTTP 202).
Plano e implementação recebidos; captura inicial de 20 quadros concluída, mas
persistência interrompida por `MOTION_EFFECT_ALREADY_CLAIMED`. Pedido terminou
`failed`; não existe storyboard persistido, aprovação nem MP4 do cliente.

Estimativa somada dos dois recibos: US$ 0,568106 (plano US$ 0,247888;
implementação US$ 0,320218). Reservas US$ 2,50 permanecem no ledger como incertas;
não são fatura confirmada. Teto US$ 6,25, sem terceira chamada paga ou imagem nova.
Transcrição efetiva igual à proposta. Os dois payloads foram reconstruídos pelos
montadores e conferidos contra os hashes duráveis.
Recibos locais: `.local/evals/motion-recovery-run-20261111/`.

A base continua sendo “Nova — quatro melhorias”; a candidata não recebe status
de evolução sem comparação fundamentada e avaliação do titular. Nenhuma aprovação
retroativa será gravada para o storyboard anterior reprovado.

## Falha, correção e recuperação interrompida

Causa comprovada: a amostragem v3 adicionou vários momentos `kind=global` por
cena, enquanto o nome de upload só incluía `frame_index` quando havia `event_id`.
Dois quadros globais da mesma cena receberam a mesma identidade. Corrigido por
`storyboard_upload_name`, compartilhado entre captura e reconciliação; cartões
históricos sem `kind` mantêm sua identidade. Adicionado teste v3 que percorre a
persistência, não somente o cálculo dos instantes.

Implementada recaptura técnica explícita e única, sem repetir modelos ou gerar
assets: exige falha específica, recibos completos, mesma composição/plano/inputs,
sem peça/storyboard existente e orçamento já respeitado. Usa outbox/Temporal,
identidade própria e novo token; não apaga efeitos anteriores. A chamada ao modelo
foi também bloqueada no executor operacional da recuperação.

A primeira tentativa de enfileirar a recuperação foi revertida: o banco ainda
não permitia os novos tipos de evento. A migração `0117_motion_recapture_events`
acrescenta somente `motion.storyboard_recapture_requested` e
`motion.storyboard_recapture_started` à restrição existente. Testada em transação
revertida no `_test` existente, preservando sua revisão/conteúdo; aplicada depois
ao dev existente de 0116 para 0117, sem tabelas novas ou exclusão de linhas.
O `_test` está em revisão 0076; não foi criado banco vazio nem aplicado o conjunto
de migrações pendentes para realizar esse teste delimitado.

A recuperação foi executada por Temporal e parou com
`MOTION_RECAPTURE_PIXELS_CHANGED`. O controle exige todos os hashes iguais aos
registrados na primeira captura; não foi relaxado. O pedido permanece `failed`,
com a segunda operação de captura em `claimed`. Não repetir automaticamente.

Uma operação diagnóstica separada no mesmo Temporal guardou os quadros do código
recebido, sem alterar o pedido nem executar provider. Nessa captura, 19/20 hashes
coincidiram; o quadro de 2.800 ms diferiu. Não há bytes arquivados do quadro original
de 2.800 ms para localizar a diferença pixel a pixel. A região/técnica responsável
continua não comprovada; não atribuir a falha automaticamente ao vídeo-fonte.

Prévia local: `.local/evals/motion-recovery-run-20261111/diagnostico-comparativo.html`.
É diagnóstico identificado como tal, não galeria de storyboard aprovado nem
reconciliação bem-sucedida. `diagnostic-frames.json` registra hashes e 20 PNGs;
`diagnostic-contact.jpg` oferece visão conjunta. Os quadros mostram a xícara no
retorno da gravação, mas ainda há vazio visual antes de sua entrada. Não está
comprovada melhora sobre a base aceita; movimento e áudio não avaliados.

## Validação e próximos limites

113 testes de motion/captura/recuperação passaram; 95 testes relacionados ao
outbox/controle passaram; um teste PostgreSQL verificou a migração com rollback.
Mypy passou em 326 módulos. Ruff e diff verificados nos arquivos tocados. CI
integral/100% continua pendente. Não alterar o índice Git ou o código recebido
para disfarçar a falha, não repetir chamadas pagas nem aprovar o MP4.

Falta resolver a estabilidade da captura e completar a persistência por caminho
verificável; a tentativa não pode ser declarada concluída. A inspeção da prévia
pelo titular pode orientar se vale manter esta direção antes de nova geração.
