# Correção do produto e plano substituto revisado — 12/11/2026

Titular pediu encontrar o problema e ajustar e, após a correção técnica/entrada
preparadas, autorizou expressamente: “Autorizar novo plano até US$ 1,25”.
Foi executada uma chamada substituta, pelo fluxo real, e entregue revisão do
retorno. Parada em awaiting_plan; nenhuma implementação ou render.

## Problemas corrigidos

1. Orientações sobre elaboração eram condicionais e o piso v1 não cobrava
   visual_development como função própria. Perfil v2 agora exige a justificativa
   de relações/estados concretos também no pedido simples, sem impor receita
   visual ou quantidade de elementos. Preenchimento continua sujeito à revisão.
2. Disponibilidade do arquivo, relato humano e avaliação futura da mistura eram
   informações dispersas. planning_input agrupa os relatos vinculados aos bytes
   e suas etapas, sem inventar escuta própria. Falta de mistura futura não é,
   sozinha, justificativa para omitir; voz sozinha permanece escolha narrativa.
3. Guard exigia beat não hold para qualquer evento. Isso confundia layout parado
   com ação dentro da gravação. Perfil v2 permite evento na ação do vídeo-fonte
   autorizado, dentro da sua duração, mesmo em hold. Exceção não vale para
   grafismo estático, outro vídeo, evento além da fonte ou perfil legado.

Compatibilidade: recaptura conserva a versão do perfil anterior, e validação usa
os requisitos capturados. Payload v7 original reproduzido byte a byte. Não houve
reescrita do plano anterior nem detector estético por palavras/quantidade.
Detalhes da implementação: [correção do planejamento](../design/motion-correcao-planejamento-2026-11-12.md).

## Execução e evidências

Entrada v8 inicial foi superada, antes de submissão, pela v9 ao incluir a correção
do guard da ação filmada. Mesmo escopo autorizado de uma chamada substituta;
nenhuma chamada v8 ou migração nova. Mensagem, fonte, áudio, kit, bibliotecas,
repertório e três relatos de escuta preservados; nenhuma peça/plano anterior foi
anexado como exemplo para o gerador.

Titular também autorizou encerrar a rodada anterior pelo fluxo de revisão.
MotionCheckpoints.decide registrou rejeição para revisão com feedback, hash exato
e histórico intacto. Pedido anterior ficou failed/MOTION_CHECKPOINT_REJECTED,
conforme a semântica existente de rejeição; não foi falha nova de provider ou
apagamento de evidência. Reserva antiga continua mantida.

Identidades completas estão nos artefatos privados request/workflow. Caminho da rodada:
`.local/evals/motion-supervised-20261112/plan-only-v2/`. Usou os mesmos serviços
reais de admissão/owner/RLS, Temporal existente em fila exclusiva, ASR novo,
contagem, ledger e checkpoint. Worker efêmero já encerrou; configuração somente
em memória. Wrapper de uma submissão e renderer proibido mantidos.

Payload efetivamente enviado, idêntico à preparação final v9:
`9602fb9c6e23f5c9bb18a2664798a4c398a76fe89862da0fcf042629685d9ff1`.
Quinze quadros da fonte, zero de peça anterior; perfil v2 com oito critérios e
relatos humanos por arquivo/hash. Nenhum asset gerado por IA ou direção fixa.
Checkpoint: `68877906f2ae87dcf2d01026b0bff84f97763229df8a4976ebd44addeffe8354`.

Workflow COMPLETED com retorno awaiting_plan. Novo pedido running, execution_token
liberado, nenhuma decisão do titular registrada. Eventos somente requested e
plan_ready; sem operação de implementação ou captura. Raw, artefato normalizado,
entrada exata e ledger foram preservados e conferidos.

## O que mudou na proposta

| Antes | Depois observado no plano escrito |
| --- | --- |
| Barras abrem espaço para um título, mesma janela central | Xícara gráfica se torna o U necessário à leitura de PAUSA; placa muda de apoio para campo de leitura |
| Omissão de servir citava falta de mistura futura | Evento de servir proposto para ação real de 1.900–3.680 ms, mesmo com layout em hold |
| Contato omitido por falta de ação | Decisão mantida: amostras não demonstram apoio e a metamorfose não inventa impacto |
| Sete funções preenchidas | Oito funções; visual_development compara uma alternativa e descreve mudança de função/estados |

Conceito novo: gesto documental → xícara conceitual → U de PAUSA → recuperação da
xícara e convite. Modelo escolheu tipografia-em-ritmo-v1 e três cenas, sem isso
ter sido imposto pelo operador.

| Intervalo | Ação planejada |
| --- | --- |
| 0–3.680 ms | Gravação dominante à esquerda; chamada abaixo; placa e xícara conceitual se formam à direita |
| 3.680–8.440 ms | Na âncora ASR estimada, xícara vira U, placa expande para campo e PA/SA completam a palavra; vídeo continua inteiro e reduz uniformemente |
| 8.440–11.200 ms | Palavra se desmonta, U recupera a xícara e campo se recolhe; marca e convite encerram |

Som: coffee-pour, trecho 290–2.070 ms, offset 1.900 ms, duração 1.780 ms,
volume 0,75 e fades 60/140 ms. Propósito evita alegar natureza do líquido ou
correspondência acústica exata. Arquivo previamente considerado adequado pelo
titular; evento/sincronismo/mistura continuam não ouvidos e não aprovados.

O plano realmente exercita a correção do guard: o alvo cena1-registro tem hold.
Validação nova aceita; a antiga rejeitaria esse evento. Compilação em memória
produz original protegido + um efeito, sem misturar/decodificar saída ou render.

## Revisão e limites

Os dois pontos anteriores foram tratados na proposta. Recomendo apresentar este
plano para decisão do titular, com os cuidados de execução/previsão registrados
na revisão privada REVISAO-DO-PLANO.md. Não houve aprovação automática.

- A mudança de função xícara/letra/campo vai além de reposicionar uma janela;
  isso é evidência observada de avanço do plano escrito, não qualidade executada.
- Fundo declara não cobrir a gravação na expansão. Interpolação geométrica direta
  de todas as propriedades cruza os retângulos no meio (placa x248/y736/448×328;
  vídeo x48/y140/396×704). Implementação precisa cumprir a proteção declarada
  por coreografia/recorte/camadas; extremos não comprovam a passagem. Nenhuma
  colisão visual foi afirmada sem render. Mudança do plano exige revisão própria.
- Metamorfose precisa conservar reconhecimento da xícara e legibilidade do U,
  com espessura/alinhamento adequados aos glifos do kit.
- CTA fica assentado por 1.580 ms. Conferir leitura, detalhe útil do vídeo
  reduzido, movimento e continuidade depois da implementação.
- Ouvir evento/voz posteriormente: sincronismo, adequação do trecho, término
  enquanto o gesto continua, timbre e ganho. Relato isolado/energia não certificam
  a mistura. ASR permanece não revisado; nenhuma âncora de confiança baixa usada.

## Verificação e custos

Validadores de schema, duração, direção, materiais, fala, som e oito funções
passaram. Raw decodifica exatamente para o artefato normalizado. Áudio autorizado
original preservado (0–11.176 ms, volume 1); saída 11.200 ms por arredondamento
30 fps. Fonte/vídeo/voz não reordenados, cortados ou gerados novamente.

Regressão final: 1.657 motion/exportadores aprovados, dois skipped; 24 integrações
motion/checkpoints e 100 dirigidos finais aprovados (grupos sobrepostos).
Qualidade/catálogo: 100% linhas/branches, 132 statements/62 branches. Ruff lint/
formato e Mypy 334 módulos app + oito scripts aprovados. CI global ainda pendente
nos gates anteriores de Node e geocodificação/schema do _test; sem migração
implícita, banco novo ou exclusão de módulos de produção.

Nova chamada: 41.087 tokens entrada, 12.548 saída. Estimativa conservadora
US$ 0,228198, sem fatura conciliada; teto calculado US$ 0,642718 dentro da reserva
US$ 1,25. Ledger mantém uncertain/actual nulo. Duas chamadas da sequência somam
US$ 0,442353 estimados e US$ 2,50 reservados. Não reutilizar reserva/sobra aparente
para outra chamada. Nenhuma crítica paga, retry ou geração extra.

Próximo passo é decisão específica sobre implementar o plano novo. Código,
assets, storyboard, render e publicação não foram autorizados nesta entrega.
Dev continua 0118, global disabled e cinco serviços restritos exited. Qualidade
artística final, voz/mistura e evolução da peça completa continuam abertas.
