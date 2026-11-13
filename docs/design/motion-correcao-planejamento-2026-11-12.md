# Correção do planejamento após revisão do plano real — 12/11/2026

Atualização: a autorização foi recebida e a chamada substituta v9 concluiu em
awaiting_plan, com proposta que trata os pontos anteriores. Resultado e revisão
em [plano corrigido](../evals/plano-audiovisual-corrigido-2026-11-12.md). Estados
de preparação/espera abaixo registram o percurso e ficam preservados.

Titular pediu encontrar o problema e ajustar, após a revisão apontar elaboração
visual limitada e justificativa sonora insuficiente. Corrigido o produto e
preparada inicialmente a entrada v8, superada pela v9 após corrigir também a
validação de ação filmada com layout parado. A nova chamada foi autorizada
expressamente e está sendo executada; resultado será registrado separadamente. Não se editou manualmente o plano
normalizado recebido nem o checkpoint já persistido.

## Diagnóstico com evidência

O plano real v1 era tecnicamente válido: três cenas com a mesma janela de vídeo,
barras e textos, sem efeitos sonoros. A metáfora de abrir espaço era pertinente;
a revisão pediu desenvolvimento além desses recursos e motivo mais específico
para omitir o som de servir. Isso foi avaliação da intenção escrita, não defeito
comprovado de vídeo que ainda não foi renderizado.

| Lacuna verificável | Evidência no produto/entrada | Correção |
| --- | --- | --- |
| Elaboração condicionada ao pedido técnico e cobertura indireta | Criativo trazia “Se o pedido exige elaboração”; qualidade v1 exigia sete funções sem visual_development próprio. Plano recebido passou no guard. | Perfil v2 exige visual_development também quando o cliente só pede um Reel e instrui justificar relações/estados concretos. |
| Etapas de avaliação sonora dispersas | Catálogo e medições mantinham origem sem escuta do sistema; relatos humanos eram evidências separadas. O retorno reconheceu escuta isolada, mas usou falta de mistura futura como parte da razão de omitir. | planning_input reúne evidências por arquivo/hash e distingue disponível, relato do arquivo e evento/mistura ainda futuros. |
| Risco de atualização retroativa do piso | capture_motion_guidance escolhia QUALITY_CONTRACT corrente ao recapturar uma geração de produção. Trocar a constante sem corrigir isso mudaria snapshots v1. | Recaptura conserva quality_contract anterior; validação usa os requisitos da versão capturada. |

Esses são problemas de especificação/propagação demonstráveis. Não há prova
causal de que uma única frase ou o estilo editorial causou sozinho a escolha
artística do modelo; não se removeu estilo, exemplo, biblioteca ou capacidade
com base nessa hipótese.

## Bloqueio adicional encontrado antes da chamada nova

O guard sonoro exigia beat.phase diferente de hold para qualquer ação. Isso
confundia layout da janela com ação dentro da gravação: servir podia continuar
com a janela parada, mas o evento era recusado. Perfil v2 agora permite esse
vínculo quando o elemento é o vídeo-fonte autorizado e o intervalo da ação cabe
na duração original. Grafismos parados, outro vídeo, intervalo além da fonte e
perfil legado não recebem essa exceção. A correspondência semântica/temporal
continua uma proposta a revisar; o validador não certifica movimento filmado.

Regras do perfil explicam isso ao planejador, evitando animar a janela ou criar
um grafismo só para habilitar som. A entrada final é v9; v8 permanece arquivada,
nunca submetida, e não deve ser enviada depois desse ajuste de preparação.

## Implementação

`motion_quality.py` preserva LEGACY_QUALITY_CONTRACT v1 e introduz
motion-production-quality-v2. O novo oitavo critério cobra interação entre gesto,
representação, texto e espaço, estados antes/depois e consequência narrativa.
Pede considerar outra abordagem e explicar a escolha. O nível de elaboração é
responsabilidade do produto, sem pedir linguagem técnica ao cliente.

A justificativa deve apontar estados e alvos reais, mas a suficiência artística
continua em revisão. Não se impõem número de cenas/objetos, objeto fotográfico,
3D, esconder vídeo, alternância por cronômetro ou inclusão de som. Tipografia,
barras, repetição e repouso podem ter função; não são proibidos nem provas
suficientes por si só.

Novo planejamento v2 recebe planning_input no builder real, após conferir os
arquivos e os vínculos de evidência. Para a fonte e cada candidato: ID/hash,
relatos humanos com origem/escopo, arquivo disponível e evento/mistura ainda não
planejados/ouvidos. Sem inferir semanticamente aprovação a partir de texto ou
energia. system_listening=false permanece explícito. Regras pedem função
narrativa ou evidência concreta para omitir; falta de escuta da mistura futura,
sozinha, não é motivo. Eventos continuam propostas e mantêm checks posteriores.

Projeção só é anexada à etapa de plano do perfil v2. Implementação mantém o plano
exato aprovado sem obrigação de redesenhar ou planejar de novo. V1 e demais modos
mantêm payload/schema/contratos. Nenhuma tabela, migração, runner ou dependência
adicionada. Negócio permanece em serviços; adapter só inclui a projeção.

## Provas e limites

- Plano real recebido validado sob v1; ao confrontar com v2 sem alterar o plano,
  rejeitado por falta de visual_development. Isso comprova obrigação faltante,
  não falha estética detectada automaticamente. Não se trata de detector por
  palavras proibidas, estilo ou contagem de elementos.
- Payload v7 original reproduzido byte a byte pelo builder atual; SHA-256
  `6be0608f467776acfe1efcf97bfe9e88afc94d6ddbaaa40ff1e5dda613c2b158`.
  Artefato e checkpoint anteriores preservados. Após autorização expressa, o
  pedido anterior foi encerrado para revisão pelo fluxo de decisão, sem apagar
  seu plano ou liberar a reserva.
- 100 dirigidos finais passaram com 100% de linhas/branches nos módulos de
  qualidade e catálogo sonoro: 132 statements/62 branches. O grupo de 26 de
  qualidade está incluído. Verificam ausência do oitavo critério, versões,
  recaptura integral de v1, vínculo por bytes/hash, observações humanas presentes/
  ausentes/fora do arquivo, omissão de projeção na implementação e plano imutável.
- Regressão motion/exportadores: 1.657 passaram, dois skipped. Integrações de
  audiovisual/checkpoints: 24 passaram no dedicado _test com roles restritas,
  sem executar migrações novamente. Grupos sobrepostos.
- Lint/formato global (905 arquivos) e Mypy 334 módulos app + oito scripts
  passaram. CI global continua não qualificado pelos gates anteriores de Node
  e schema de geocodificação do _test; não se excluíram módulos de produção nem
  se alterou schema implicitamente para melhorar cobertura.

A validação estrutural não julga a qualidade da justificativa em prosa. Um modelo
pode preencher oito itens e ainda propor uma direção insuficiente; a revisão
continua necessária. O efeito desta correção na próxima proposta ainda não foi
observado; não se afirma melhora artística já comprovada.

## Preparação nova e continuação

Pacote privado `.local/evals/motion-supervised-20261112/preparation-v9/`, SHA-256
`9602fb9c6e23f5c9bb18a2664798a4c398a76fe89862da0fcf042629685d9ff1`.
Manifesto e bytes exatos do builder verificados. Fonte/áudio originais idênticos,
15 quadros da fonte, zero de peça anterior, oito critérios, três relatos humanos
e ASR local novo com recibo conferido. Nenhuma direção/cena foi fixada manualmente
nem plano anterior anexado como exemplo. Sem lacuna de prontidão técnica;
transcrição continua local_asr_unreviewed.

Verificações privadas e `planning-correction-legacy-verification.json`
registram as provas. status.json registra a entrada final v9,
sem apagar o plano/revisão anteriores. Runtime global disabled, dev já 0118;
nenhuma migração ou chamada paga adicional nesta correção. Sem código ou render.

Autorização anterior cobria uma única chamada, já consumida. Proposta concreta
nova em planning-correction-budget.json: uma chamada gpt-6.1-sol/high/default de
até US$ 1,25 para o plano v8, 54.000 tokens de saída, guard de contagem e teto
qualificado existentes. Nenhuma reutilização da reserva antiga ou autorização
para retry, código ou render. Titular respondeu “Autorizar novo plano até US$ 1,25”; escopo de uma chamada
substituta, com parada antes do código. A rodada anterior foi rejeitada para
revisão pelo serviço existente, com feedback autorizado e artefato intacto.

Na execução substituta, a rodada original foi resolvida pelo fluxo existente
de decisão, com feedback autorizado e histórico preservado; não editar seu
artefato/hash nem abrir planejamento paralelo para contornar estado ativo. Após
autorização correspondente: gerar somente plano, revisar resultado contra os
mesmos critérios e parar antes do código. Se a nova direção continuar limitada,
registrar a evidência; não aprovar por ter aumentado os campos obrigatórios.
