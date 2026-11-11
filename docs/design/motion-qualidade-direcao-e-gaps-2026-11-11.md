# Qualidade de motion: seis frentes e lacunas após a comparação Café Pausa

**Passagem para implementação:** a ordem e os aceites foram consolidados em
[contrato de sete etapas](contrato-evolucao-qualidade-motion-2026-11-11.md),
incluindo as considerações posteriores sobre ferramentas, percepção, EDL e som.
Este relatório permanece como diagnóstico; o contrato é o plano vigente.

Data: 11/11/2026. Estado: análise e proposta, não implementação. Pedido do titular:
reexaminar a referência Maestros WuzMxEKJHkQ e detalhar seis melhorias. A peça
funcionou e ganhou elaboração, mas a moldura foi percebida como estranha e a
xícara realista não produziu a expressividade esperada. Esse retorno é o critério
criativo vigente; `adequate` automático não o substitui.

## Diagnóstico principal

O fluxo conseguiu executar a direção recebida. A direção foi excessivamente
prescritiva em adornos e pouco específica sobre a experiência visual desejada.
Traduzimos integração da gravação em borda verde, filete cobre, padding papel,
raio e sombra. O pedido do titular não exigia essa combinação em toda presença
do vídeo. O resultado demonstra por que presença de recursos e acabamento são
avaliações distintas.

A xícara ganhou material fotográfico, mas sua ação permaneceu entrada com
opacidade/escala, pequeno assentamento e redução no retorno. Não há um momento
central de revelação com contraste forte entre preparação, ação e repouso. Essa
é uma interpretação da direção, código e quadros, coerente com o feedback do
titular; não é uma nota objetiva nem prova de incapacidade do modelo.

Os seis pontos continuam pertinentes. Parte já existe tecnicamente, parte está
subutilizada e parte exige capacidade nova. Acrescentar outra lista longa de
adjetivos ao prompt não é a proposta.

## Evidências e método desta revisão

Releitura integral da transcrição automática do vídeo de referência, do relatório
anterior e de sete folhas de contato (01, 02, 04–08). Nova extração/inspeção de
quatro sequências de oito segundos a 2 fps: 00:38–00:46, 02:40–02:48,
03:29–03:37 e 04:34–04:42. São 64 amostras adicionais, não análise contínua de
todos os quadros nem medição exata de curvas. Referência já baixada; não foi
necessário pedir o link ou baixar novamente. Não houve escuta integral nesta revisão.

Confronto com o MP4, quadros, código, plano, entrada efetivamente enviada e crítica
persistida de `.local/evals/motion-staged-retry-20261111/`. Auditoria reproduzível
em `.local/research/motion-quality-gaps-20261111/audit.json`, com hashes e folhas
de contato. Consultadas também as orientações locais de perícia do claude-video
como repertório; não executado seu fluxo de geração nem instaladas ferramentas.

Constatações da última rodada:

- Três cenas, 40 beats declarados: 16 ease_out, 23 ease_in_out e um linear. Isso
  não prova monotonia por si, nem significa que spring tornaria a peça melhor.
- O código aproxima o vídeo em apenas 2,5% na abertura e 2% no encerramento. A
  xícara entra entre 6,780–7,420 s e assenta até 7,780 s. Não há preparação visual
  própria do objeto antes desse início; o plano organiza principalmente a chegada.
- Entrada contém seis imagens Felipe/Lucas e seis quadros da fonte. O vídeo
  WuzMxEKJHkQ não está identificado no payload, e não há nele uma ficha temporal
  específica da nova referência. Os princípios gerais das bibliotecas continuam
  presentes; não repetir o diagnóstico antigo de ausência de todas as referências.
- A skill incorporada tem 41.791 caracteres e 629 linhas. Há orientações boas e
  exemplos, mas também acúmulo de instruções. Tamanho não prova a causa do resultado;
  recomenda seleção por necessidade, não corte arbitrário de contexto.
- `storyboard=false` e zero correções foram escolhas desta comparação. O produto
  tem captura/galeria/aprovação de storyboard; o portão não foi usado nesta rodada.
- O fluxo constrói o código antes de gerar a imagem. O compositor inicial recebe
  a descrição da xícara, não seus pixels. Só a crítica/correção posterior os recebe.
- A crítica selecionou três de 49 eventos, todos próximos de Sinta, e omitiu 46.
  Há ainda cinco amostras globais; não significa ausência absoluta das outras cenas.
- A faixa de áudio contém somente a fonte original, volume 1. Não houve camada
  adicional de som. Preservação da voz foi conferida tecnicamente na comparação.

## O que a referência ensina, com trechos verificáveis

| Trecho | Mecanismo observado | Aplicação pertinente |
| --- | --- | --- |
| [00:38–00:48](https://www.youtube.com/watch?v=WuzMxEKJHkQ&t=38s) | A mesma mídia vira pilha, leque de fotos e vídeo. O elemento permanece reconhecível enquanto sua função muda. | Desenvolver um motivo ao longo da peça. Café pode ligar gravação, objeto, vapor e convite; não precisa ser apenas um ícone que aparece. |
| [01:22–01:41](https://www.youtube.com/watch?v=WuzMxEKJHkQ&t=82s) | Demonstração de início/fim e respostas temporais distintas no mesmo trajeto. | Decidir preparação, acento e repouso, com curvas/durações adequadas a cada ação. |
| [02:38–02:54](https://www.youtube.com/watch?v=WuzMxEKJHkQ&t=158s) | Câmera revela camadas, superfície e sombras; a apresentadora integra o espaço. | Construir relações espaciais. Uma janela com borda não substitui essa integração. |
| [03:24–03:39](https://www.youtube.com/watch?v=WuzMxEKJHkQ&t=204s) | Rosto localizado, região protegida, máscara de pessoa e texto atrás dela. | Quando necessário, perceber a ação real e proteger regiões relevantes; máscara é uma capacidade distinta da moldura. |
| [04:34–04:42](https://www.youtube.com/watch?v=WuzMxEKJHkQ&t=274s) | Prints passam de uma grade para objetos organizados num espaço, percorridos pela câmera. | Usar mudança de enquadramento/hierarquia para revelar relações, conservando identidade entre estados. |
| [04:43–05:24](https://www.youtube.com/watch?v=WuzMxEKJHkQ&t=283s) | Efeitos, trilha, redução da música durante fala e medição de volume são demonstrados. | Planejar som para ações selecionadas e proteger a voz; não inserir um efeito por palavra. |
| [05:25–05:46](https://www.youtube.com/watch?v=WuzMxEKJHkQ&t=325s) | Sequências de conferência, proteção do rosto, comparação de transcrição e correção de um erro. | Observar o resultado e corrigir trechos concretos. Validar JSON não encerra o trabalho criativo. |

A referência declara 3h48 de trabalho, 89 arquivos e milhares de quadros conferidos.
São números do autor, não auditoria nossa. O relato de um pedido não significa uma
única resposta de API. Nosso ensaio de uma execução sem refação tem outra condição.
Isso ajuda a dimensionar o processo, mas não justifica a moldura inadequada nem
promete que mais chamadas, tempo ou outro modelo entregarão qualidade.

## 1. Direção por momentos da fala

**Existe:** ASR local com tempos, direction separada, plano por cenas/elementos e
vínculos speech_cue_id. **Lacuna:** coincidir o início de um movimento com a palavra
é uma validação temporal, não uma decisão de linguagem. A direção fornecida fica
imutável na construção/correção; se ela for fraca, o executor deve preservá-la.

Propor por unidade de sentido: intenção do trecho, protagonista, mudança visível,
resultado e passagem de atenção. Usar `brief_basis`, `visual_representation`,
`narrative_action`, `attention_order` e beats existentes antes de acrescentar
campos. Escolher um acento principal adequado à mensagem; não impor fórmula de
três cenas ou efeito por palavra a todos os negócios.

Para um objeto que assenta na palavra, preparar seu movimento antes dela pode ser
mais expressivo do que iniciar um fade na palavra e chegar depois. O contrato
atual ancora o início do beat, com tolerância de 34 ms. Ele já permite um beat de
antecipação separado; eventual vínculo explícito ao impacto/fim exigiria extensão
versionada, sem alterar silenciosamente os tempos da voz.

**Aceite proposto:** a transformação permanece compreensível mesmo ao ocultar
mentalmente a legenda; a legenda complementa a ação. Um card ou animatic deve
mostrar a ideia central antes de gastar na peça final. Intenção e efeito observado
precisam corresponder, com avaliação humana de ritmo/sincronismo quando necessária.

## 2. Gravação integrada ao cenário

**Existe:** alternância, máscaras geométricas, wrappers e transformação uniforme,
um único vídeo com relógio contínuo. **Lacuna:** enquadramento e decoração são
prescritos sem uma escolha visual convincente para a gravação específica.

Admitir vídeo em tela inteira, janela sem borda, recorte geométrico ou moldura
quando a direção justificar. Borda deve exercer uma função — por exemplo, separar
superfícies ou materializar uma janela — e desaparecer quando deixar de fazê-lo.
Não trocar a receita de bordas por uma proibição global de bordas.

Próxima capacidade condicional: regiões protegidas de rosto, mãos e produto,
com confiança/proveniência. Isso permite reenquadramento responsável. Para Café
Pausa, mãos, jarra e xícara importam mais que recortar uma pessoa inteira. A máscara
de pessoa é útil em depoimentos e demonstrações; exige estabilidade temporal,
tratamento de cabelo/mãos/oclusão e fallback para vídeo íntegro. Não está entregue.

**Aceite proposto:** o enquadramento acompanha a intenção e preserva a ação; não
há filete ou camada decorativa cruzando o assunto sem motivo. Conferir saída,
intervalo coberto e retorno — especialmente os 3,967 s e 8,767 s problemáticos.

## 3. Fundo com função narrativa

**Existe:** planos por código e mudanças de composição do fundo. **Lacuna:** a
última peça permanece muito próxima de cartelas: retângulos mudam, mas não se
forma um ambiente convincente para o objeto. Clareza/legibilidade não obrigam
um painel papel arredondado em toda cena.

Escolher uma lógica espacial de acordo com o kit: superfície de apoio, espaço
negativo, direção de luz e profundidades relativas. Fazer o fundo preparar uma
revelação, receber o objeto e devolver foco à gravação. Uma câmera simulada em
camadas pode deslocar fundo e primeiro plano em proporções distintas. Não requer
3D completo, luz pulsante nem movimento constante; a câmera de uma foto continua
limitada aos pixels disponíveis.

**Aceite proposto:** há mudança significativa de foco/escala/espaço e contraste
correto durante a passagem, não apenas no quadro final. A placa de proteção de
texto deve fazer parte do desenho, sem os recortes acidentais vistos na transição.
A cena calma precisa de repouso intencional, distinguível de tempo vazio.

## 4. Objetos com presença física

**Existe:** PNG realista com transparência, sombra separada, escala uniforme e
reutilização. **Lacuna:** material melhorou, mas a coreografia não transforma a
percepção da mensagem. O modelo também constrói antes de ver o recorte produzido.

Reordenar futuramente a construção com os serviços existentes: plano validado →
material disponível/gerado → preview e geometria útil → implementação informada
pelos pixels → conferência. `asset_previews` já pode entrar no builder; a lacuna é
no encadeamento e nas garantias de reaproveitamento, não num novo serviço de imagem.
Manter hashes, autorização, reservas, IDs de efeitos e não regenerar na correção.

Trabalhar preparação, aceleração, chegada, apoio e reação do cenário. Ângulo, luz,
sombra e textura precisam concordar. Uma aproximação pode revelar material e
criar presença; a sombra deve indicar apoio real, não só flutuar sob a imagem.
Uma imagem não permite revelar o verso de uma xícara. Se essa mudança de ponto de
vista for essencial à direção, avaliar vídeo apropriado ou um asset 3D, com custo
e qualificação próprios. Three.js fornece cena/câmera/render, não um modelo de
xícara pronto: [documentação oficial](https://threejs.org/manual/pages/creating-a-scene.html).

**Aceite proposto:** um momento principal com preparação e resultado perceptíveis;
material natural, apoio e escala coerentes; objeto mantém identidade. Não usar
quique, zoom, reflexos ou partículas só para tentar produzir surpresa.

## 5. Som acompanhando ações importantes

**Existe:** áudio original preservado; mixer HTML com trim, atraso, volume constante
e soma de faixas. **Lacuna:** o fluxo prepara apenas a faixa original e exige
igualdade integral do plano de áudio; não basta pedir música/SFX no prompt.
Não há ducking, envelopes ou medição de loudness integrados a esse caminho.

Separar futuramente voz original imutável de camadas adicionais autorizadas.
Usar assets licenciados do acervo, com função e instante declarados. Para o café,
um som de contato ou uma passagem discreta pode reforçar um acento; primeiro
verificar se a própria gravação já contém esse som, para não duplicá-lo. Não
precisamos de voz sintética, avatar ou assinatura de serviço novo para isso.

Ducking pode reduzir apenas a música durante a voz; conferir picos, inteligibilidade
e continuidade do áudio original. FFmpeg tem `sidechaincompress` e `loudnorm`, mas
é necessário integrá-los e qualificar parâmetros; não impor um valor universal
para toda plataforma. [Filtros oficiais](https://www.ffmpeg.org/ffmpeg-filters.html).

**Aceite proposto:** a voz continua clara e preservada; sons reforçam ações
selecionadas sem encobrir palavras ou criar eventos enganosos. Escuta/checagem de
áudio precisa ser uma evidência própria; a crítica de imagens não pode aprová-lo.

## 6. Revisão e correção por cena

**Existe:** evidências, rubrica, storyboard opcional, versionamento e correções
limitadas. **Lacunas concretas:**

1. `motion_temporal.events` ordena os eventos e, havendo fala, seleciona os três
   primeiros speech events. Como vários elementos respondem ao mesmo cue, o
   orçamento de amostras é consumido no mesmo momento. Foi exatamente o ocorrido.
2. `adequate` valida apenas os eventos apresentados; a revisão não teve A/B com
   a peça anterior. Não mede o nível de acabamento desejado pelo titular.
3. `storyboard=false` nesta rodada eliminou a chance de rejeitar a moldura antes
   do MP4. O storyboard atual é capturado após o código, não um estudo de arte
   antes de animar. Ainda assim, já é um portão aproveitável.
4. A correção recebe composição completa; não há edição localizada com garantia
   de preservar cenas aprovadas, nem retomada paga por artefato concluído.

Primeiro, selecionar grupos de eventos distribuídos por intenção/cena, incluindo
transições de saída/retorno e o objeto principal. Separar cobertura obrigatória
de amostras opcionais; com orçamento insuficiente, registrar cobertura pendente
em vez de apresentar a aprovação parcial como qualificação da peça inteira.
Uma sobreposição real não deve ser compensada por um texto positivo sobre a ideia.

Depois, prévias curtas dos momentos críticos e correção delimitada por cena/intervalo,
com contexto das transições vizinhas, comparação A/B e reaproveitamento de assets.
Pode continuar renderizando o MP4 inteiro para verificar integridade; correção
local não exige de início concatenar renders parciais. Preservar áudio, kit,
identidades de efeitos e partes aprovadas, com orçamento de correção explícito.

**Aceite proposto:** a amostragem inclui chegada da xícara e ambas as passagens
com vídeo, sem concentração nos três beats de Sinta. Bugs de sobreposição geram
observações acionáveis e localizadas. Ganho de acabamento exige comparação visual,
não somente aprovação estrutural. Critério criativo deve ser calibrado com os
resultados que o titular aceitou/rejeitou, sem transformar uma preferência de
Café Pausa em estilo obrigatório de todos os negócios.

## Ferramentas: aproveitar capacidades, não instalar o catálogo

HTML/JS, MotionV1, Chromium e FFmpeg existentes já sustentam boa parte das três
primeiras frentes. As curvas cubic_bezier e spring já existem; sua ausência no
plano não justifica acrescentar outra biblioteca. A referência demonstra Remotion,
HyperFrames e GSAP, mas não comprova que trocar nosso executor elevará a qualidade.

Detecção de regiões/máscaras/tracking é uma lacuna distinta. Apple Vision oferece
análise de imagens, detecção, reconhecimento de texto e segmentação, mas é uma
tecnologia do ecossistema Apple; não assumir integração direta no worker Linux.
Uma escolha de implementador deve partir do resultado necessário e de medições
locais: [Vision oficial](https://developer.apple.com/documentation/vision.md).
OCR, banco externo, avatar e edição longa não resolvem os problemas observados
nesta peça e ficam fora da fatia inicial.

## Ordem proposta para implementação

| Fatia | Mudança concreta e pontos principais | Como demonstrar o ganho |
| --- | --- | --- |
| 1. Direção e repertório aplicáveis | Atualizar direção Café Pausa conforme feedback; moldura opcional; escolher ação central e passagem. Selecionar fichas de mecanismos/trechos em motion_repertoire e orientações da skill, sem adicionar o vídeo inteiro ao contexto. Reutilizar scene_direction. | Direção curta e quadros de intenção com a mídia real, reconhecíveis como uma proposta diferente da atual; titular avalia arte antes de nova peça. |
| 2. Evidência representativa | Corrigir seleção em motion_temporal, calibrar motion_review e explicitar cobertura. Usar o portão de storyboard existente no próximo ensaio, com momentos de transição além dos cards. | Teste dirigido reproduz os três cues concentrados e passa a cobrir transições/objeto. Prévia aponta os defeitos concretos conhecidos. |
| 3. Objeto visto e coreografia | Ajustar motion_construction/orchestrator/illustrations para entregar preview do asset à implementação; qualificar composição por camadas, trajetórias e contraste de ritmo usando runtime atual. | Mesmo asset identificado por hash; antes/ação/depois convincente na chegada e retorno, sem perda do tratamento da gravação. |
| 4. Som autorizado | Estender plano protegido de voz + complementos; integrar envelopes/ducking/análise em inputs, schemas e audio.cjs. | A/B com e sem camada adicional, voz legível e medições de áudio; nenhuma geração paga implícita. |
| 5. Refinamento delimitado | Correção por intervalo/cena e reaproveitamento de artefatos no Temporal/ledger atuais, mantendo contexto de vizinhança. | Corrigir uma passagem sem alterar texto, aparência e timings já aceitos fora dela; custo e operação distintos. |
| 6. Percepção sob demanda | Regiões protegidas primeiro; máscara/tracking somente para uma direção que precise. 3D completo é decisão separada. | Reel de pessoa/produto demonstra integração com máscara estável ou tracking confiável e fallback íntegro. |

Fatia 1 e diagnóstico da amostragem podem avançar localmente antes de qualquer
chamada paga. Cards/previews e comparação real que dependam de geração deverão
ter custo e escopo próprios. Nenhum teto de rodada anterior é reutilizado.
Não criar novos serviços, tabelas ou um runner concorrente para iniciar isso.

## Aplicação revisada ao Café Pausa — hipótese para desenvolver

O eixo seria aproximar o espectador do ritual do café e depois abrir espaço para
a pausa. Calma pode ter contraste e uma revelação marcante; não precisa manter
intensidade baixa em todos os instantes. Isto é proposta, ainda sem novo desenho
ou aprovação; timings de ASR continuam estimados.

| Fala/momento | Função da composição | Diferença buscada |
| --- | --- | --- |
| Preparação / cheiro | Valorizar mãos, fluxo do leite e xícara reais; um detalhe de forma ou vapor entrega atenção à próxima cena. | Gravação integrada à ação, sem impor moldura dupla. Reenquadrar somente se a região importante estiver protegida. |
| Primeira pausa (~3,68 s) | Uma transformação abre um espaço coerente; a leitura fica estável e existe preparação do próximo foco. | Não sustentar só uma cartela vazia até o objeto aparecer. |
| Café (~6,78 s) | Revelação principal da xícara, com escala, apoio e trajetória decididos em conjunto com cenário e tipografia. | A chegada possui preparação e um acento; não apenas fade e pequeno deslocamento. |
| Pausa final / convite (~8,44 s em diante) | Movimento reduz e devolve atenção à gravação; elemento compartilhado conduz a passagem. | Sem filete cruzando o vídeo, reinício da gravação ou aparição arbitrária da xícara ao lado. |

A proposta deve ser avaliada pelos quadros e por uma prévia dos movimentos. Não
promete emoção por fórmula nem antecipa que qualquer imagem 3D produzirá o resultado.

## Validação e pendências

Somente análise, consulta de código/recibos/documentação e extração local de
quadros do vídeo já baixado. Sem alterar produção, banco, serviços, orçamento,
modelo ou peça; sem nova imagem, chamada paga, renderização de composição ou CI.
Verificados hashes, estado da entrada, eventos selecionados, curva declarada,
flags de storyboard e plano de áudio. Análise anterior continua como histórico
pré-comparação; este documento incorpora o resultado e o novo feedback.

Pendência: escolher/implementar a próxima fatia mediante instrução do titular,
começando por direção e cobertura de revisão. Não marcar as seis frentes como
concluídas pelo sucesso técnico da última geração.
