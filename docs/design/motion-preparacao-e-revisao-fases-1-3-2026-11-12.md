# Preparação verificável e revisão antes do render — fases 1–3

> **Escopo histórico — esclarecido em 13/11/2026.** Estados, versões selecionadas,
> orçamentos e ordens de parada abaixo descrevem a entrega desta data; não são
> automaticamente instruções para uma rodada nova. Contratos capturados continuam
> preservados. Consulte a [orientação vigente](motion-orientacao-vigente-2026-11-13.md)
> para diferenças entre geração nova/evolução, estado operacional e próximo roteiro.

**Continuação de 12/11:** o [modo de planejamento audiovisual proposto](motion-planejamento-audiovisual-revisavel-2026-11-12.md)
permite mensagem simples sem direção fixa, com piso funcional e catálogo sonoro
real local. Reutiliza as duas pausas descritas aqui e mantém seus hashes/garantias;
o caminho com direção fornecida continua disponível. Repertório v4 retira os oito
prints somente da próxima seleção. Preparação v4 montada, ainda sem chamada paga,
plano/código novos ou render; qualidade continua pendente.

**Inspeção posterior:** o [ensaio acompanhado](../evals/ensaio-acompanhado-motion-2026-11-12.md)
montou a entrada real sem chamada paga e identificou direção herdada restritiva,
seleção sonora ausente e a fronteira de interpretação natural ainda não exercitada.
A entrevista definiu mensagem simples, piso de qualidade sem template e busca de
efeitos em biblioteca pública licenciada. Rascunho superado; nenhuma nova peça
ou qualidade validada. Isso não desfaz a entrega técnica descrita abaixo.

Entrega técnica de 12/11/2026, posterior à
[auditoria do fluxo](../evals/auditoria-fluxo-motion-2026-11-12.md).
Estas são as três fases de correção da preparação/inspeção pedidas após a
auditoria; não reiniciam as sete etapas originais nem removem a recuperação R1–R5.
HEAD conferido: `4adb596`; alterações anteriores já staged preservadas. Mudanças
desta entrega permanecem no working tree, sem commit/stage automático.

## Escopo implementado

| Fase | Alteração efetiva | Evidência verificável | Limite |
| --- | --- | --- | --- |
| 1. Origem e alcance da direção | `MotionRequest.preparation` preserva mensagem e decisões classificadas como requisito, observação, exemplo ou hipótese, com origem e cenas | Mensagem chega ao builder real; requisito exige origem cliente e citação literal presente; todas as cenas precisam de fundamento declarado | Não é um interpretador automático nem prova de que a classificação humana está correta |
| 2. Evidência pertinente | Intenção, observação e limites ligados a instantes, referências e materiais realmente anexados; novo repertório opcional v3 | IDs/tempos/hashes conferidos contra bytes; ausência bloqueia a montagem antes do provider; amostras extras da fonte chegam à chamada | Quadros não demonstram movimento contínuo, escuta ou qualidade; relevância artística exige revisão |
| 3. Revisão antes de continuar | Pausa persistida após plano e outra após implementação, antes de qualquer captura/render | API privada entrega entrada efetiva, resposta armazenada, artefato normalizado e hashes; aprovação exata dispara outbox/Temporal uma única vez | Sem nova peça, avaliação visual ou UI de chat integrada nesta entrega |

`review_checkpoints=true` ativa o percurso acompanhado e exige `preparation`,
`scene_direction` e `storyboard=true`. Pedidos históricos omitem os campos novos
na serialização e mantêm seu percurso. As escolhas de direção continuam fixas
dentro de uma execução; o checkpoint permite recusá-las antes de pagar pelo
código. A classificação como hipótese não transforma a direção em campo livre
nem garante que o modelo fará uma boa proposta.

Não se impõem borda, xícara, objeto fotográfico, cenário escuro, efeito por palavra
ou duração de 4–5 s a todas as peças. Essas possibilidades precisam de fundamento
e escopo na preparação da rodada. O contrato de áudio e seus materiais autorizados
continuam vigentes; esta implementação não cria efeitos sonoros.

## Fluxo exato e fronteiras

1. API recebe `MotionRequest`. `preparation.client_message` contém a mensagem
   preservada; `instruction` continua sendo o brief operacional. `decisions`
   registra `source_excerpt`, `interpretation`, `origin`, `kind`, `scope` e
   `scene_ids`. `unresolved` registra definições ainda pendentes.
2. `MotionContext.capture` monta o snapshot com kit, skill, repertório, contratos,
   acervo/referências e base histórica quando selecionados. Não há prompt manual
   paralelo. Permissões, consentimento e orçamento continuam nos serviços atuais.
3. `MotionInputLoader.prepare` carrega/verifica materiais. Preserva seis amostras
   globais da fonte e acrescenta até 14 instantes escolhidos, dentro da duração.
   O conjunto fica limitado a 20. Seleções de base precisam existir nos quadros
   da base; esta fase não inventa novos quadros históricos.
4. ASR segue o mecanismo existente. `OpenAIMotionProvider.build_request` confere
   `preparation_contract` e produz `preparation_evidence`: cada observação/intenção
   vinculada aos anexos efetivos. O servidor verifica presença/integridade dos
   anexos, não a verdade da observação artística. A chamada de plano mantém seu
   recibo, custo e resposta originais em `motion_effects`.
5. Plano válido é persistido como checkpoint `plan`. Retorno do workflow:
   `awaiting_plan`. Nenhuma imagem é gerada e nenhum código ou quadro é produzido
   depois dessa pausa sem aprovação específica.
6. Aprovação do plano exato emite `motion.plan_approved`. Temporal retoma a
   implementação existente, incluindo resolução de imagens se já habilitada e
   orçada. Revalida contexto/consentimento/acesso, recupera a transcrição capturada
   e confere o manifesto. Não repete planejamento nem ASR.
7. Código precisa preservar os metadados do plano aprovado. Persiste checkpoint
   `render` e retorna `awaiting_render`, com zero chamadas ao renderizador até aqui.
8. Aprovação específica de `render` emite `motion.render_approved`. Retoma apenas
   a captura do storyboard. O MP4 continua condicionado à aprovação própria do
   storyboard já existente. Nesta entrega, esse caminho só foi testado com renderer
   simulado; nenhuma nova captura de peça foi executada.

Pedido permanece `running`, com `execution_token=NULL`, durante cada espera.
Assim continuam válidos os controles existentes de operação ativa, retenção de
assets e alterações pendentes. Decisão aceita é consumida uma única vez, antes
de revalidar/executar; erros posteriores ficam `failed` ou `uncertain`, sem
repetição automática de efeitos. Rejeição encerra o pedido, registra feedback e
aplica os mecanismos existentes de liberação de mudanças pendentes.

## API de inspeção

Prefixo existente:
`/api/v1/organizations/{tenant_id}/businesses/{business_id}/motion-requests/{request_id}`.

- `GET /checkpoints/plan` e `GET /checkpoints/render` exigem o titular original,
  sessão válida e escopo RLS. Respondem com `Cache-Control: no-store`.
- `model_input` é o payload arquivado da chamada, incluindo prompt/contexto e
  imagens codificadas; não é uma reconstrução posterior.
- `model_output` é o recibo armazenado: resposta normalizada, resposta bruta
  quando disponível, usage e estimativa. `packet.artifact` é conferido contra
  esse retorno. Direção reinserida pelo servidor continua identificável comparando
  retorno bruto e artefato normalizado.
- `packet.context`, `packet.inputs`, `model_request_hash` e `model_wire_sha256`
  ligam artefato, contexto e anexos. PNGs gerados ficam no pacote privado para
  retomada; o campo interno `resolved_images` não é duplicado na resposta pública.
- `content_sha256` identifica o pacote que será aprovado. `rendered=false`
  descreve o momento de captura desse checkpoint, não o estado atual de toda a
  execução após retomadas posteriores. `request_state`, `decision` e
  `decision_consumed` informam o estado consultado.
- `POST /checkpoints/{plan|render}/decisions` recebe:

```json
{
  "operation_id": "UUID novo da decisão",
  "content_sha256": "hash exato devolvido pelo GET",
  "decision": "approve",
  "note": "O que foi conferido e por que pode avançar"
}
```

`decision` também aceita `reject`. Mesmo conteúdo/operação é idempotente;
conteúdo diferente conflita. A API não chama modelo/render diretamente.
Pendências em `preparation.unresolved` impedem aprovação. Corrigir preparação ou
plano rejeitado requer novo pedido explícito; não há edição silenciosa do pacote
nem nova chamada automática. Requisição normal continua sujeita ao orçamento
configurado: aprovar uma etapa não cria saldo nem reutiliza teto antigo.

## Repertório e compatibilidade

`business-reel-v3` acrescenta três amostras de luz/camadas já existentes no estudo
Maestros (aproximadamente 160/164/168 s), além das cinco imagens anteriores.
Ficha declara observação, adaptação e limites. v1/v2, hashes, skills, executor,
bibliotecas, kit e contratos anteriores permanecem disponíveis. Referências são
insumos do modelo, nunca assets autorizados para render. Não houve geração de
imagem nem download de novo material para essa biblioteca.

## Persistência, migração e validação

Sem tabela ou serviço novo. Checkpoints e decisões usam efeitos privados já
existentes, criptografados; payload grande usa o armazenamento privado existente.
Nenhuma chamada de storage/provider ocorre sob row lock. A migração
`0118_motion_checkpoint_events` amplia apenas a restrição dos tipos de outbox
para quatro eventos; rollback não apaga histórico para forçar downgrade.

O titular autorizou expressamente migrar somente
`meu_braco_direito_platform_test` de 0076 para 0118. A primeira tentativa encontrou
divergência anterior: `reference_provider_profile_options` não tinha
`source_position`/`is_primary` e respectivos índices definidos na 0075 do código.
A tabela estava vazia, verificado sob lock; reconciliou-se apenas essa estrutura
no `_test`, sem apagar dados, e a migração foi concluída. Não se criou banco novo
nem se migrou dev. Os testes de integração usam limpeza apenas desse `_test`
dedicado e logins restritos, conforme as guardas existentes.

Validação registrada nesta entrega:

- Suíte de motion unitária/exportadores: **1.533 passaram, dois skipped**.
- Integração de regressão do fluxo existente: **seis passaram**, incluindo plano/
  implementação sem checkpoints, correção, storyboard e isolamento.
- Testes dirigidos de preparação/checkpoints/migração: **65 passaram**, cobertura
  de linhas/branches **100% nos quatro módulos novos** (307 statements/96 branches).
  Isso não é cobertura integral de todo o projeto.
- Ruff lint global aprovado; Mypy aprovado em **330 módulos**.
- `make ci` foi executado e parou na formatação de **17 arquivos preexistentes**.
  Não se reformata em massa a alteração anterior do titular. CI integral e
  cobertura global continuam pendentes; não houve exclusão de módulos de produção.
- Os cinco contêineres identificados no diagnóstico Docker foram consultados e
  continuam `exited`. Nenhum serviço foi iniciado.

Os testes da nova pausa usam modelo/mídia/renderer sintéticos. Provam fluxo,
integridade, orçamento/escopo existentes, decisão exata, erro e não repetição;
não demonstram que uma peça ficou bonita, mais cinematográfica ou melhor que a
base. Cobertura mede execução de código; qualidade precisa de casos reais de
referência, avaliação do resultado e critérios de não regressão.

## Pendências e próxima inspeção

1. Revisar esta fatia e resolver o CI global antes de considerar merge qualificado.
2. Aplicar migração em outro ambiente somente dentro de autorização correspondente.
3. Preparar nova rodada com mensagem simulada identificada como tal, origem das
   decisões, seleção de evidências, base de comparação e orçamento novo; revisar
   pacote montado pelo produto antes de qualquer chamada paga. Nenhuma nova
   geração está registrada como feita nesta entrega.
4. Avaliar plano e depois código pelos checkpoints. O ponto solicitado para parar
   é `awaiting_render`; não aprovar `render` nessa inspeção.
5. Conferir qualidade visual/sonora posteriormente, contra a base aceita. Continuam
   abertas a divergência histórica de recaptura em 2.800 ms e a qualificação da
   rodada anterior, sem relaxar seus controles.
6. Chat local OpenCode com trace foi identificado pelo titular durante a implementação.
   [Pesquisa e proposta de integração](opencode-e-inspecao-do-produto-2026-11-12.md)
   seguem separadas: ainda não há nova UI ou
   framework instalado. Um chat de diagnóstico deve chamar os serviços reais e
   mostrar as evidências persistidas; chamadas de modelo isoladas no chat não
   validariam o percurso do produto desde a mensagem natural.
