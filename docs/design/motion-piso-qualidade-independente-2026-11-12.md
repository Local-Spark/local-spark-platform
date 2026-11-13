# Piso de qualidade independente de peças anteriores

> **Escopo histórico — esclarecido em 13/11/2026.** Estados, versões selecionadas,
> orçamentos e ordens de parada abaixo descrevem a entrega desta data; não são
> automaticamente instruções para uma rodada nova. Contratos capturados continuam
> preservados. Consulte a [orientação vigente](motion-orientacao-vigente-2026-11-13.md)
> para diferenças entre geração nova/evolução, estado operacional e próximo roteiro.

Atualização posterior nesta data: a lacuna de ASR e a escuta dos arquivos foram
fechadas na preparação v7; entrada conferida e orçamento novo proposto em
`motion-asr-avaliacao-sonora-orcamento-2026-11-12.md`. Estados v5 abaixo são
históricos; transcrição não revisada, mistura e qualidade artística continuam
pendentes.

12/11/2026. Correção de escopo definida pelo titular após revisar a preparação v4.
A sugestão de enviar quadros da última prévia favorável para gerar a nova peça
confundia avaliação do produto com contexto de criação. Essa sugestão foi retirada.

## Decisão

Uma solicitação nova deve partir de pedido, contexto do negócio, kit, fatos e
materiais autorizados atuais. A última peça enviada ao cliente não é exemplo
obrigatório nem dependência da geração. As peças dos ensaios anteriores continuam
como evidência para medir evolução e regressões do produto, fora da entrada de
criação desta rodada. Não se acrescentaram seus quadros, versões ou aprovações.

O piso é uma exigência do produto: sentido/ação, integração da gravação e voz,
espaço/hierarquia, continuidade, ritmo/leitura, identidade e som. Cada peça resolve
essas funções conforme sua mensagem e recursos. Não há obrigação de repetir
objeto, borda, cenário, três cenas, 18 elementos ou passagem com saída/retorno do vídeo.

Isso não impede continuidade em um ajuste explicitamente pedido ou uso legítimo
de material do acervo que já apareceu em outra peça. Material autorizado e plano
de uma peça anterior são coisas diferentes. Não se recupera uma ilustração pelo
vínculo com um render antigo apenas para alimentar uma nova criação. Os caminhos
históricos de revisão/comparação explícita permanecem disponíveis e versionados.

## Alterações efetivas

- Novas solicitações no percurso acompanhado, com `propose_direction=true` e sem
  seleção explícita de evolução histórica, recebem automaticamente
  `motion-production-quality-v1`, geração `proposed-audiovisual-output-v2`, criativo
  v9 e contrato de preparação v3. O cliente não fornece essa rubrica técnica.
- O perfil substitui a dependência de funções/IDs/evidências da base anterior por
  sete critérios estáveis do produto. O plano precisa vincular cada critério a
  alvos próprios, justificativa, verificação e limites. Uma mesma composição pode
  atender vários critérios; não se mede qualidade pelo número de elementos.
- O builder rejeita histórico misturado à geração nova: seleção/composição de
  base, quadros de baseline, evidência declarada de baseline e imagem recuperada
  pelo mecanismo de reutilização de um render anterior. Calibrações com nomes de
  peças dos ensaios foram retiradas somente do novo contrato criativo; bibliotecas,
  skill, repertório de mecanismos e controles úteis permanecem.
- Ausência/adulteração do perfil, falta/duplicação de critério ou alvo inexistente
  são rejeitadas. Os checkpoints continuam exigindo aprovação do plano exato e
  preservação integral no código. Correções da candidata da mesma execução podem
  continuar recebendo a candidata corrente/incumbente; não se confundem com uma
  peça anterior do cliente usada como molde para criar outra.
- A preparação v5 não contém evolução histórica, composição anterior, quadros de
  comparação ou o PNG da xícara recuperado da peça antiga. As amostras da fonte
  têm descrições observacionais; foram removidas as sugestões herdadas de chegada
  do objeto e retorno da gravação. Não se substituíram esses itens por referências
  arbitrárias.
- O exportador não injeta ASR arquivado no modo novo. Como o runtime atual está
  sem ASR configurado, a preparação declara `MOTION_QUALITY_SPEECH_REQUIRED`.
  O planejador recusa esse estado, ou pendência essencial da preparação, **antes
  de reservar/chamar o modelo**. Exportar para inspeção não torna o pedido executável.

O piso é aplicado à intenção no plano e articulado aos critérios de revisão já
existentes da própria candidata. Cobertura declarada, schema válido e código fiel
não comprovam acabamento. A qualificação do piso depende de casos avaliados e
resultado audiovisual observado; não se promete qualidade mínima garantida por
acrescentar instruções ou sete registros no JSON.

Esse recorte evolui o percurso acompanhado disponível. Não implementa uma nova
conversa WhatsApp nem qualifica toda a v0 comercial; pedidos históricos mantêm
seus contratos. Os ensaios comparativos separados continuam necessários.

## Pacote atual e evidências

`.local/evals/motion-supervised-20261112/preparation-v5/`, ZIP adjacente e
`preparation-v5-verification.json`. Mensagem simulada inalterada:
“Faça um Reel com esse vídeo para divulgar minha cafeteria.”

Captura nova pelo `MotionContext.capture`, loader e builder reais, com leitura RLS
do negócio existente: 15 quadros da fonte, **zero da base**, zero referências
externas e zero preview recuperado da peça anterior. Dois candidatos sonoros
locais continuam disponíveis, sem seleção ou escuta. O acervo consultado não
forneceu fotos elegíveis neste negócio; isso fica explícito, sem preencher a falta
com mídia de ensaios antigos.

Não há ASR/transcrição injetados, plano/código de modelo, pedido admitido, gasto ou
render novos. O pacote é de inspeção **com lacuna operacional**, não está liberado
para submissão. Runtime disabled e dev 0117 foram preservados. `intake-v3.json` e
`status.json` registram a correção do titular; v4 e entradas anteriores permanecem
intactas para auditoria, superadas para esta nova geração.

## Validação

- **1.605** testes motion/exportadores passaram, **dois skipped**.
- **67** testes dirigidos de qualidade/audiovisual/preparação passaram; o módulo
  novo `motion_quality.py` alcançou **100% de linhas e branches** (35 statements,
  22 branches). Grupos sobrepostos, sem soma nem alegação de cobertura integral.
- **Quatro integrações** no `_test` existente passaram, cobrindo o novo perfil
  propagado, original protegido, dados RLS, checkpoints duráveis e ausência de
  renderer antes da aprovação específica. Provedores/mídias dessas provas são
  sintéticos; nenhum conteúdo de cliente foi usado nos testes.
- Ruff lint global, Mypy (**333 módulos**), formato dos arquivos alterados,
  integridade do pacote e `git diff --check` aprovados. `make ci` ainda para na
  formatação preexistente de **14 arquivos**; gate/cobertura integral pendentes.
  Não se excluíram módulos de produção.
- Sem migração, banco novo, serviço/tabela/dependência nova, chamada paga ou
  render de peça. Integrações usam somente o `_test` já autorizado e logins
  restritos; dev não foi migrado. Cinco contêineres indicados continuam parados.

## Próximo passo

Fechar o ASR pelo caminho local real e conferir a entrada efetiva; concluir a
avaliação dos trechos sonoros/possível duplicação e resolver o CI. Em seguida,
revisar o pacote atualizado e um orçamento novo. Configuração e qualquer migração
continuam exigindo o escopo/autorização correspondentes; não se usam tetos antigos.

Gerar somente o plano autorizado, revisar por cena e aprovar especificamente
antes do código. Conferir fidelidade e parar em `awaiting_render`, antes de qualquer
storyboard/render. Peças anteriores apoiam a avaliação separada do avanço desta
implementação, não entram automaticamente como exemplo para a geração.
