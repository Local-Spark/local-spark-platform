# Roteiro técnico: melhoria de motion até uma peça completa — 13/11/2026

Estado: roteiro proposto, ainda não implementado. A análise de referências está
concluída; a prévia anterior foi reprovada visualmente pelo titular. Este documento
organiza a próxima execução, não autoriza chamadas pagas ou migrações.

## Objetivo e evidência de partida

Gerar pelo processo do produto uma nova peça completa para a cafeteria, com
melhora demonstrável de conteúdo, encenação, integração de mídia, transições,
tipografia, ritmo e acabamento. A entrega inclui MP4 reproduzível e comparação
visual fundamentada. Uma composição escrita manualmente pelo assistente pode
qualificar uma capacidade, mas não prova que o gerador do produto melhorou.
Não encerrar o trabalho somente com testes, plano, storyboard ou efeito isolado.

Ler antes de executar:
- `docs/design/motion-orientacao-vigente-2026-11-13.md` (resolve gates e estados históricos).
- `docs/PROJECT.md`, `docs/SDD.md`, `docs/phases/BL04-context-and-ai-production.md`.
- `docs/evals/analise-41-referencias-motion-2026-11-12.md`.
- `docs/evals/referencias-motion-2026-11-12/anotacoes.md`.
- `docs/evals/previa-motion-completa-2026-11-12.md`.
- `docs/design/motion-planejamento-audiovisual-revisavel-2026-11-12.md`.

Evidência privada existente:
- `.local/research/coffee-owner-references-20261112/index.html`: galeria de 41 vídeos.
- Nesse diretório: `visual-notes.json`, `evidence-manifest.json`, `verification.json`.
- `.local/evals/motion-supervised-20261112/render-preview-v1/previa.mp4` e
  `owner-quality-feedback.json`: resultado reprovado e feedback vinculado.
- `.local/evals/motion-supervised-20261112/preparation-v9/`: entrada da rodada.
- `.local/evals/motion-supervised-20261112/status.json`: estado local atual.

A análise inspecionou sequências amostradas em toda a duração; não representa
escuta perceptiva nem observação contínua de todos os frames. Não repetir os
41 downloads ou toda a pesquisa sem uma lacuna concreta.

## 1. Fixar a linha de base e rastrear as lacunas

Inspecionar alterações existentes e confirmar o estado atual sem sobrescrever
trabalho. Conferir entrada efetivamente enviada, plano, código e saída anteriores.
Produzir uma matriz curta: problema observado → causa/hipótese no processo →
mudança proposta → evidência que poderá demonstrar melhora. Distinguir causa
comprovada de hipótese; não atribuir a pobreza visual simplesmente a Python.

Pontos de inspeção: `motion_quality`, `motion_creative`, `motion_styles`,
`motion_repertoire`, `motion_construction`, `motion_temporal`,
`motion_corrections`, `motion_storyboards` e adapters de IA/render.

Saída: baseline e escopo de uma fatia implementável. Aceite: cada mudança tem
relação explícita com um defeito visual e uma forma de avaliação na peça final.

## 2. Qualificar os mecanismos necessários no renderer real

Selecionar do estudo mecanismos adequados à peça: por exemplo, tipografia que
participa da imagem, máscaras/oclusões, mudanças de escala, camadas/profundidade,
transições motivadas e acabamento de material. Seleção não é uma lista obrigatória
de efeitos. Verificar suporte real no sandbox e dependências antes de prometer.

Transformar os mecanismos selecionados em exemplos executáveis e inspecionados,
com código, restrições, timings, evidência temporal e proveniência. Reaproveitar
os serviços e o catálogo existentes; versionar mudanças de contrato. Exemplos
não devem virar um template fixo de cafeteria ou cópia das referências.

Saída: repertório utilizável pelo gerador, com demonstração local das capacidades
escolhidas. Aceite: execução no renderer alvo e inspeção visual, não só sintaxe.
Esta etapa é um insumo para a peça inteira, não a entrega final.

## 3. Corrigir planejamento e seleção de materiais

Evoluir o contrato de planejamento para descrever, com dados consumidos pelo
fluxo, conteúdo novo por momento, protagonismo, relação mídia/grafismo, ações,
estados de transição e dependências de material. Evitar campos narrativos que
ninguém verifica. Preservar compatibilidade dos planos/checkpoints existentes.

Inventariar o que há na fonte; selecionar recortes e tratamentos realmente úteis.
Se a direção exigir material ausente, explicitar obtenção, identidade, direitos,
custo e impacto antes de aprovar a direção. Não prometer filmagens, produtos,
locais, 3D ou imagens geradas que o pipeline não sabe fornecer. Não substituir
silenciosamente material ausente por desenho simples.

Adicionar contexto seletivo de mecanismos e evidência visual quando aplicável,
com proveniência e política de uso. Não enviar os 41 vídeos indiscriminadamente.
O cliente continua podendo pedir uma peça com mensagem simples. A última peça
favorável do cliente não é insumo obrigatório. A prévia reprovada serve de baseline
da avaliação, não de modelo a reproduzir na geração.

Saída: entrada inspecionável e contrato implementado/testado. Aceite: é possível
explicar o desenvolvimento da peça e a origem dos elementos que o realizam;
preencher IDs e justificativas não constitui aprovação artística.

## 4. Integrar construção, render e revisão com correção delimitada

Usar Temporal e serviços existentes para construir e inspecionar a composição,
com efeitos duráveis/idempotentes, hashes, auditoria/outbox e orçamento. Definir
a menor integração necessária para o modelo receber evidência da execução e
corrigir o resultado. Não confundir instruções de uma skill com ferramentas
realmente disponíveis ao modelo. Não criar um runner concorrente.

Selecionar evidência por evento/risco: início, travessia e destino de transições,
camadas, legibilidade, passagens entre mídia/grafismo e trechos de permanência.
Rever os limites atuais de três janelas/20 quadros conforme cobertura e orçamento,
sem converter 100 quadros em meta. Cobertura insuficiente deve ficar explícita.

Separar defeito de direção/material de defeito de implementação. O primeiro
retorna ao planejamento pelo fluxo de revisão, preservando aprovações anteriores;
o segundo pode receber correção delimitada de código. Não alterar silenciosamente
um plano aprovado. Configurar limite de rodadas, custo total e condição de parada
antes da execução; a rodada anterior tinha max_corrections=0.

Saída: ciclo integrado e verificável, incluindo falha/retomada sem duplicar gastos.
Aceite: testes demonstram os caminhos e uma execução local demonstra que a
crítica recebe evidências corretas; não declarar qualidade visual por isso.

## 5. Validar a fatia e preparar o orçamento real

Executar testes unitários/integrados relevantes, lint, tipos e `make ci` conforme
AGENTS, com cobertura de linhas/branches exigida. Banco de teste dedicado `_test`,
roles restritas, nunca limpar/migrar dev para testes. Registrar bloqueios globais
existentes separadamente, sem anunciar CI verde quando houver falhas.

Antes de qualquer chamada paga, produzir entrada final inspecionável e orçamento
com modelos/provedores, tokens/limites, materiais, planejamento, código, crítica,
correções e teto acumulado. Incluir as contingências dentro do teto, não como
retry ilimitado. Não reutilizar reservas antigas como saldo livre.

Saída: mudança revisável, evidência dos checks e proposta concreta de execução.
Aceite: autorização explícita do novo teto antes dos efeitos pagos. Trabalho
local autorizado deve avançar até esse ponto sem pedir permissões repetidas.

## 6. Gerar e revisar a peça completa

Com orçamento autorizado, executar a nova rodada pelo fluxo integrado, com
material suficiente e direção revista antes do código. Inspecionar composições
chave e transições; gerar uma primeira montagem completa cedo, antes de gastar
todo o orçamento em polimento. Executar as correções previstas dentro do teto.

Preservar voz, conteúdo verdadeiro e integridade da fonte conforme o contrato;
isso não obriga uma janela de vídeo fixa ou sempre visível. Manter o avanço
sonoro sem supor aprovação da nova mixagem. Verificar sincronismo e níveis;
avaliação perceptiva exige escuta, não apenas medição.

Saída obrigatória: MP4 completo acessível, entrada/plano/código vinculados,
evidências, custos e limitações. Se houver bloqueio ou teto atingido, entregar
o resultado existente e declarar o que falta; não marcar objetivo como concluído.
Não simular conclusão nativa usando uma prévia privada fora do ciclo do produto.

## 7. Demonstrar o resultado e registrar o aceite

Comparar a peça inteira com a baseline reprovada e com mecanismos relevantes
estudados: desenvolvimento de conteúdo, presença do material, encenação,
transições, integração tipográfica, timing, acabamento e coerência comercial.
Apontar momentos concretos e problemas remanescentes. Testes, número de efeitos,
quantidade de cortes e ausência de erros não substituem essa avaliação.

Entregar MP4, comparação, resumo das mudanças efetivamente exercitadas pelo
produto, custo observado/estimado e estado de reconciliação. Separar aprovação
técnica, avaliação visual do assistente e aceite perceptivo do titular. Uma única
peça melhor é uma prova inicial, não garantia do piso para todo cliente; registrar
os próximos casos de regressão/generalização sem adiar a entrega desta peça.

## Restrições e estado a preservar

- Não alterar `spotlight-api`, não sobrescrever alterações locais nem fazer commit
  ou publicação sem solicitação. Atualizar PROJECT, SDD, fase e CHANGELOG por fatia.
- Não migrar dev implicitamente. A autorização antiga para 0118 foi específica.
- Manter global `motion_ai_mode=disabled` e `motion_execution_enabled=False`, salvo
  autorização específica; ensaio deve ter escopo explícito, sem habilitação global.
- Manter parados `local-spark-platform-worker-1`, `local-spark-platform-billing-1`,
  `local-spark-platform-relay-1`, `local-spark-platform-auth-mail-1` e
  `meu-braco-direito-platform-relay-1`.
- Pedido anterior `1a890ed5-1c62-533f-a5ec-693f89301aa8` permanece no checkpoint
  nativo awaiting_render; prévia local não o concluiu. Conferir estado ao retomar.
- Estimativa anterior US$ 0,774901; reservas US$ 3,75 ainda sem reconciliação.
  Nenhum desses valores autoriza gasto novo. Confirmar ledger antes de executar.
- Evidências/mídia do cliente permanecem privadas em `.local/`, sem segredos em
  logs/git. Referências de terceiros não se tornam ativos comerciais por download.
- Não reabrir entrevistas genéricas nem impor um estilo único. O estudo já
  esclarece o patamar; perguntas só para dependências concretas não recuperáveis.

## Registro desta alteração

Somente documentação: criação do roteiro e referências nos documentos centrais.
Nenhum mecanismo, contrato, ciclo de revisão ou nova peça implementado aqui.
Validação: existência das referências locais e `git diff --check`. Testes de
produção não se aplicam a esta alteração documental; gates globais continuam
pendentes conforme registros anteriores.
