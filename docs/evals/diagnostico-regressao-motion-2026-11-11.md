# Diagnóstico da regressão visual — direção e preservação da base

Data: 11/11/2026. Análise posterior à reprovação da etapa 7, sem nova geração,
renderização, gasto, alteração de código de produção, banco ou serviços.

## Referências corretas e alcance

O titular identificou **as duas peças da comparação de 11/11**, “Anterior” e
“Nova — quatro melhorias”, como as versões recentes de que gostou. Esse retorno
é a referência desta análise; não substituir por outros benchmarks históricos.
Não implica aprovação terminal registrada no produto.

| Rótulo na comparação de 11/11 | Arquivo local existente | SHA-256 do MP4 |
| --- | --- | --- |
| Anterior: xícara desenhada, gravação sai e retorna | `.local/evals/motion-reliability-20261110/comparacao-alternancia.mp4` | `d574c2b6c6b26de8d68d601f574c9c7b61789e91ec1f58ae3b012fd5fc947dbb` |
| Nova — quatro melhorias: xícara fotográfica | `.local/evals/motion-staged-retry-20261111/v0.mp4` | `187b611018d2b24c27edb99f07a4a21aecd5599e7333a64ad1b227147df0c451` |

Os rótulos e destinos foram conferidos em
`.local/evals/motion-staged-retry-20261111/comparacao.html`. O nome da pasta da
primeira peça é de 10/11; ela foi apresentada como “Anterior” na comparação de
11/11. A terceira peça recuperada, `reel-semantic-recovery-20261110/local-repair.mp4`,
permanece na galeria apenas como histórico. As recuperações locais anteriores
não demonstram que o fluxo automático já reproduzia sozinho todos os resultados.

Comparação navegável: `.local/evals/motion-regression-audit-20261111/comparacao.html`.
Ela reúne os MP4s originais, amostras extraídas a cada 0,5 s e os 18 PNGs atuais;
o controle posiciona o vídeo anterior no instante do quadro atual. Não existe
MP4 atual. Inspeção visual de amostras e leitura do plano/código não equivalem
a assistir ao movimento contínuo atual ou escutar sua mixagem.

## Causa principal comprovada: simplificação introduzida na etapa 1

A composição fotográfica declara 18 elementos principais. A direção escrita
na etapa 1 passou a declarar 11; a direção da etapa 7 conserva os mesmos 11 e
o resultado gerado também. Os sete abaixo já estavam ausentes **antes da chamada
ao modelo**, em `docs/evals/direcao-cafe-pausa-qualidade-2026-11-11.json`.

| Elementos removidos | Função na composição anterior | Consequência observada/plano atual |
| --- | --- | --- |
| `tempo-marcador`, `tempo-percurso` | Marcar atenção e abrir um percurso ligado à gravação/texto | Abertura reduzida à gravação, frase e fundo |
| `cafe-percurso` | Dar continuidade ao percurso no espaço da xícara | Espera sem esse desenho de trajetória |
| `cafe-vapor`, `pausa-vapor` | Prolongar a presença do café e levar uma ação ao retorno | Objeto isolado; desaparecimento sem continuidade equivalente |
| `pausa-simbolo` | Materializar a pausa no encerramento | Convite apenas tipográfico |
| `pausa-xicara` | Reorganizar a xícara ao lado da gravação que retorna | Xícara retirada antes da entrada do vídeo |

Contar elementos ou beats não mede qualidade. A perda relevante é das funções
de ligação e transformação, sem substitutos de força comparável. Os planos
passaram de 40 para 21 beats; isso descreve a simplificação, não uma nota artística.

Também mudou a direção do cenário: a base descrevia campo verde abrindo área
papel, cobertura do vídeo e reorganização dos planos no retorno. A nova direção
fala em “mudança de foco e espaço”, “apoio” e “repouso”, mas não define uma
transformação espacial igualmente concreta. Nas amostras, o cenário atual se
resume a campo claro e faixa inferior discreta; a base mudava sua organização.

O erro de direção foi tratar problemas localizados — moldura, filete residual,
sobreposição e repetição sem função — com uma reescrita ampla. A instrução do
titular de não impor bordas, efeitos por palavra ou receitas a toda peça não
pedia retirar as relações que funcionavam nesta peça. Essa interpretação foi
inadequada. Não há motivo técnico demonstrado para abandonar essas funções.

## Como o fluxo consolidou a perda

1. **A base foi arquivada, mas não usada como composição anterior na geração.**
   `scripts/evals/motion_comparison_prepare.py::comparison_files` verifica
   fonte, kit, áudio, saída, transcrição, modelo e limite de tokens. Executa
   `export.assemble_files` e só depois anexa `baseline/video.mp4` e
   `baseline/composition.json` ao pacote. Isso não os injeta no payload.
   Os arquivos efetivamente enviados, `planning-input.json` e
   `implementation-input.json`, têm `current_composition=null` e
   `previous_composition=null`. As referências visuais são cinco imagens de
   repertório, além das seis amostras da fonte; não são quadros da peça aceita.
   Conferir hashes comprovou integridade do envio, não suficiência desse contexto.
2. **A direção reduzida tornou-se obrigação.**
   `motion_visual_direction.validate_direction_fidelity` exige igualdade da
   direção; `motion_plan.validate_scene_direction` exige os mesmos IDs de
   elementos na direção e no plano. Prova local, em cópias na memória: recolocar
   `tempo-marcador` só no plano causa `MOTION_SCENE_DIRECTION_ELEMENTS_INVALID`;
   recolocá-lo na direção causa `MOTION_VISUAL_DIRECTION_CHANGED`. O resultado
   atual sem alteração passa nos dois controles. Isso não impede todo detalhe
   adicional no HTML, mas impede recuperar livremente esses elementos como
   protagonistas declarados do plano.
3. **A implementação preservou esse plano.**
   `motion_construction` compara todos os campos do plano com a composição,
   exceto HTML/JS. O controle funciona para integridade; não verifica se o plano
   mantém o patamar criativo da peça anterior.
4. **A proteção da etapa 6 tem outro alcance.**
   A correção delimitada protege o plano e regiões da candidata desta rodada.
   Não compara a nova concepção com uma peça aceita de outra rodada. Não houve
   correção nem crítica paga nesta execução: a reprovação ocorreu no storyboard.
5. **A verificação privilegiou contratos e entrega.**
   Os testes da preparação verificam invariantes e a presença da base no pacote;
   a rubrica permanece não avaliada. Não demonstram preservação das funções
   visuais. Os 18 quadros atuais também deixam a primeira dissolução incompleta
   e não mostram o miolo entre 3,800 e 6,733 s. A inspeção inicial do assistente
   destacou sombra e um quadro vazio, subestimando a perda de estrutura.

O mecanismo encontrado é: direção empobrecida → base sem vínculo comparativo
na entrada → fidelidade obrigatória à nova direção → validação estrutural sem
barreira de regressão contra o resultado aceito. As etapas ampliaram capacidades,
mas não asseguraram sua aplicação nem a continuidade do trabalho já aprovado.

## Correções de hipóteses anteriores

- **O preenchimento da xícara não explica a piora atual.** Ele saiu na passagem
  do desenho à imagem fotográfica, já documentada em
  `docs/design/motion-objeto-realista-2026-11-10.md`. O titular gostou também da
  versão fotográfica. A regressão agora analisada ocorreu depois dessa mudança.
- **A espera de 2,52 s não é uma nova demora causada pelas sete etapas.** Na base,
  a saída prevista da gravação termina em 4,220 s e a xícara começa em 6,780 s:
  intervalo de 2,56 s. Agora, 4,260→6,780 s: 2,52 s. A perda está principalmente
  no que conduz essa espera. A demora já era uma limitação a melhorar na base.
- **O retorno ficou diferente.** Na base, vídeo e xícara se reorganizam juntos
  entre 8,440 e 9,060 s; ambos aparecem no encerramento. Agora a xícara sai entre
  8,440 e 8,840 s, e o vídeo entra entre 8,840 e 9,340 s. O quadro de 8,833 s
  mostra praticamente apenas o fundo. São substituições sucessivas, em lugar
  da coexistência que sustentava o encerramento.
- **Somente voz original não causou essa perda.** O contrato de áudio atual é
  idêntico ao das duas referências. Não atribuir a regressão à escolha do titular
  de não acrescentar música/efeitos.
- **Não foi demonstrada perda das bibliotecas ou redução de orçamento de tokens.**
  Os três exemplos de repertório mantêm seus hashes; geração atual usa o mesmo
  modelo e limite de 54.000 tokens da base fotográfica. Referências e instruções
  mudaram juntas; não houve experimento que isole a contribuição de cada mudança.
  A ausência dos sete elementos precede o renderer, portanto não é explicada
  por uma falha dele em desenhar elementos presentes no plano.

## Decisão e trabalho restante

O trabalho seguinte foi organizado, a pedido do titular, no
[plano de recuperação R1–R5](../design/plano-recuperacao-e-evolucao-motion-2026-11-11.md).
É planejamento, sem implementação dos controles propostos ou nova execução.

As duas peças indicadas pelo titular constituem o patamar de referência para
esta comparação. Preservar esse patamar significa preservar funções e relações
perceptíveis, não obrigar todo Reel a usar xícara, moldura, vapor ou 18 elementos.

Antes de uma nova execução, falta tornar concreta e verificável a evolução da
base: vincular a peça de referência ao contexto real; registrar funções mantidas,
substituições e justificativas; revisar a direção antes de fixá-la no plano;
comparar resultado e base nos mesmos momentos narrativos. Testes de contrato
podem impedir omissões identificáveis, mas o aceite visual comparativo continua
necessário. Não basta acrescentar ao prompt “faça melhor” nem remover as travas
de fidelidade sem corrigir seu alvo.

Nenhuma dessas correções de produto foi implementada nesta análise. Etapa 7
continua reprovada visualmente e aberta; não avançar ao MP4 ou a outra etapa.
O estado persistido `awaiting_approval` não foi modificado. Orçamento anterior
não autoriza replanejamento, nova imagem ou repetição de chamadas.

## Evidências e validação local

Conferência posterior dos recursos enviados, registrada em `resource-usage.json`
na pasta abaixo: skill v13 integral/hash conferidos, kit cafe-pausas v1, três
fichas de estilo, repertório v2 com três exemplos e cinco referências visuais.
Referências do negócio e seleção de fotos do acervo vieram vazias; causa da
ausência ainda depende de leitura do contexto elegível. Código atual usa
MotionV1, não declara componentes da biblioteca e não contém diretamente as
três funções de exemplo. Isso não demonstra ausência de toda influência do
repertório nem justifica uso obrigatório dos exemplos. Motion-sources entra por
adaptações selecionadas, não execução integral das skills externas.

Pasta `.local/evals/motion-regression-audit-20261111/`:

- `audit.json`: identidade dos três MP4s, composições, referências e amostras.
- `direction-lineage.json`: IDs desde a base e etapa 1 até o resultado, hashes
  do repertório, invariantes e igualdade dos contratos de áudio.
- `causal-checks.json`: experimento local das duas rejeições e tempos dos planos.
- `comparacao.html` e quatro folhas de contato: arquivos existentes comparáveis,
  23 amostras de cada MP4 histórico e 18 quadros atuais.

Validação: esquemas reais carregados; validadores exercitados sem banco/rede;
integridade dos arquivos e links locais, sintaxe do JavaScript da galeria e
`git diff --check`. Sem `make ci`: não houve mudança de código de produção e
esta análise não comprova o CI integral das alterações anteriores. Arquivos
locais de auditoria não substituem evidência durável do produto.
