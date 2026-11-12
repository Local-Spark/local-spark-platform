# Motion — etapa 1: direção verificável e repertório aplicado

**Retificação posterior à etapa 7:** a afirmação abaixo de preservação da linha
de base foi ampla demais. Fonte, voz e kit foram preservados; sete elementos da
composição fotográfica e suas funções de ligação foram retirados nesta direção,
sem substitutos concretos equivalentes. O titular indicou a base fotográfica e
a anterior desenhada como patamar de qualidade, e reprovou a proposta executada.
A direção desta etapa não deve ser tratada como evolução visual validada.
Rastreamento: `../evals/diagnostico-regressao-motion-2026-11-11.md`.

Data: 11/11/2026. Esta proposta preserva a linha de base e desenvolve a etapa 1 do
[contrato](contrato-evolucao-qualidade-motion-2026-11-11.md). O resultado é uma
orientação de construção, não uma nova peça ou aceite criativo. A estrutura usa
`scene-direction-v1`, sem acrescentar campos temporais. A execução posterior terá
que demonstrar as ações, não apenas repetir sua descrição.

## Linha de base e problemas observados

A comparação existente é `.local/evals/motion-staged-retry-20261111/v0.mp4`,
SHA-256 `187b611018d2b24c27edb99f07a4a21aecd5599e7333a64ad1b227147df0c451`.
A fonte enviada naquela rodada tem SHA-256
`dd3f0265a4b2d94206188f46c094dc0177663e1a529b9ad2e0718a1dfad78a34`; o manifesto
do kit `catalog/kits/cafe-pausas/v1/manifest.json` tem SHA-256
`cd46b3e392156b367163c7e95325c53508aed2e0998d92cb9a00a2cd737b919e`.
A inspeção registrada em `manual-inspection.json`, `v0-frame-index.json` e
`transitions/` é de quadros da peça já existente, sem nova renderização. A
correlação registrada da faixa original é evidência de sinal, não escuta humana.

| Instante aproximado | Evidência e problema | Direção de resposta / verificação posterior |
| --- | --- | --- |
| Abertura e retorno | A direção anterior determinava borda verde/cobre, filete, padding, raio e sombra; o titular considerou a moldura estranha. | O gesto da gravação ganha protagonismo; janela, tela inteira ou borda devem ter função na cena. Conferir a composição e suas transições, sem proibir bordas globalmente. |
| 3,967 s | `manual-inspection.json`: passagem deixa porções da moldura e recorte retangular papel atrás de “Uma pausa.” | O espaço muda de função para receber a próxima ação; nenhum resíduo deve cruzar a gravação ou leitura sem intenção. |
| 5,600 s | Amostra `v0-frame-index.json`: bastante espaço vazio antes da xícara. | Preparação deve mudar foco ou espaço com intenção e proporcionar repouso reconhecível, em vez de esperar a chegada. |
| 6,780–7,780 s | Auditoria no [diagnóstico](motion-qualidade-direcao-e-gaps-2026-11-11.md): xícara entra até 7,420 s e assenta até 7,780 s, sem preparação visual própria anterior. | Preparar, revelar com acento e mostrar consequência/apoio; julgar movimento em sequência, não apenas estado final. |
| 8,767 s | `manual-inspection.json`: filete cobre cruza a gravação e xícara a sobrepõe parcialmente no retorno. | Fundo e objeto cedem espaço ao gesto real; avaliar entrada, passagem e estado após a volta. |

Em seis amostras da fonte enviadas na comparação, `input/image-08.png` aos
2,235 s mostra mãos, jarra, fluxo de leite e xícara. São regiões identificadas
por revisão humana e não caixas de detecção, máscara ou tracking. Devem orientar
o enquadramento sem alegar que o produto já as protege automaticamente. A leitura
dos demais instantes e a continuidade precisam de conferência visual futura.

## Proposta por unidade de sentido

A direção pronta para o contrato existente está em
[`direcao-cafe-pausa-qualidade-2026-11-11.json`](../evals/direcao-cafe-pausa-qualidade-2026-11-11.json)
e o brief sem as prescrições antigas em
[`brief-cafe-pausa-qualidade-2026-11-11.txt`](../evals/brief-cafe-pausa-qualidade-2026-11-11.txt).
Os identificadores `tempo`, `cafe` e `pausa` são nomes estáveis de cena, não
exigência de três cenas para outros negócios. Os tempos abaixo vêm do ASR local
não revisado em `speech-raw.json`; são pontos de atenção aproximados, não marcação
humana nem autorização de cortar ou reordenar a voz.

| Momento e intenção | Foco e preparação | Ação/acento | Consequência, repouso e passagem |
| --- | --- | --- | --- |
| 0–2,88 s: convidar a sentir o ritual | Gravação dominante; valorizar mãos, jarra, fluxo e xícara reais. O fundo começa a preparar espaço, e o texto complementa o gesto. | Em “Sinta o cheiro” (~1,90–2,88 s), a atenção acompanha a ação filmada; fundo e texto respondem sem cobrir o assunto. | Dar tempo à leitura e conduzir a atenção para a pausa sem borda obrigatória ou reinício do vídeo. |
| ~3,68–6,50 s: abrir uma pausa | Enquanto a gravação cede foco, o espaço prepara a futura revelação e a leitura de “uma pausa”/convite. | A mudança de espaço cria expectativa, sem um efeito separado para cada palavra. | Conservar uma pausa com função e preparar a chegada do objeto; a fonte continua em tempo absoluto sob a cena. |
| ~6,78–8,32 s: tornar o café presente | Fundo, apoio e luz preparam a xícara; o movimento começa antes do acento quando fizer sentido. | Em “café” (~6,78 s), a revelação assume protagonismo; o acento deve ser percebido junto à ação, não apenas ao aparecimento do elemento. | O objeto encontra apoio, o cenário reage e a composição repousa em “calma”; preparar a volta sem simular outra face de uma imagem plana. |
| ~8,44–11,2 s: devolver atenção e convidar | Durante o repouso, o fundo e o objeto preparam a saída. | Na pausa final, a gravação retorna no instante corrente, com suas regiões importantes visíveis. | Um convite legível entra depois da passagem; a assinatura repousa, sem filete residual nem repetição arbitrária da xícara. |

`brief_basis` guarda o fundamento na fala; `visual_representation` a ideia de
transformação; `composition` a relação de camadas e foco; `narrative_action` a
preparação, ação, resultado e passagem; `attention_order` e `elements` discriminam
o protagonismo. Beats e tempos continuam no plano. No contrato atual o início do
beat associado à fala é ancorado no cue; uma preparação antecipada precisa de beat
separado. A proposta não altera silenciosamente essa regra nem afirma vínculo ao
fim de um beat. Uma extensão temporal explícita exigiria versão e compatibilidade.

A xícara desta entrada é uma **representação conceitual provisória por código**;
não há fotografia integrada nem garantia visual nesta etapa. A resolução e o envio
dos pixels do material real antes da implementação pertencem à etapa 3. O asset
conceitual da comparação anterior pode ser avaliado para reúso então, com hash e
proveniência, sem sugerir que foi incluído neste pacote.

## Fichas selecionadas

A seleção abaixo é orientada por mecanismos, não pela identidade dos autores.
Imagens são referências de acabamento, sem licença implícita para virar mídia da
peça. As amostras são estados discretos, não comprovação de curva ou sincronismo.

| Ficha | Trecho e antes / ação / depois | Mecanismo e adaptação |
| --- | --- | --- |
| `maestros-acao-com-consequencia` | [Maestros, 01:22–01:41](https://www.youtube.com/watch?v=WuzMxEKJHkQ&t=82s), amostras aproximadamente 01:20, 01:24 e 01:28: esfera e espaço, estados de trajetória e posições resultantes na explicação visual. | Preparação, acento e repouso distinguíveis; aplicar como critério à revelação e ao apoio da xícara, sem copiar visual, duração ou curvas. |
| `lucas-hierarquia-espacial` | [Lucas Leite](https://www.youtube.com/watch?v=W7E7Ln0z6aY), amostras aproximadamente 00:03 e 00:05: objetos mudam posição/ênfase em relação à pessoa. | Relação entre planos altera o foco. Aplicar à troca de protagonismo entre gravação e objeto, preservando regiões relevantes e identidade do kit; dois estados não comprovam trajetória intermediária. |

A relação entre fichas e imagens deve ser verificada na saída do montador real;
texto de uma ficha isolado não prova que seus pixels foram enviados. Verificação
da entrada desta etapa e hashes ficam no registro da implementação, sem confundir
pacote offline com uma chamada ao modelo.

## Limites e próximos portões

A direção é hipótese para avaliação: texto e validação estrutural não demonstram
acabamento, presença física, leitura, ritmo ou sincronismo. Não houve nova peça,
asset, chamada paga ou aprovação visual. A etapa 2, sujeita ao OK do titular,
tratará distribuição representativa da revisão; a etapa 3, a ordem entre material
e código. As demais etapas e a comparação autorizada permanecem pendentes.

## Verificação técnica desta entrega

O montador real do produto exportou o pacote offline em
`.local/exports/motion-qualidade-etapa1-final-20261111/`, sem consulta nova ao banco ou
chamada ao provedor. A entrada preserva fonte, kit, áudio e transcrição da base,
com seis quadros da fonte e cinco imagens de referência. O SHA-256 do manifesto
do pacote final é `35e433142a20ed0e24149f6d26b6d2d66fd4c4dbe8036d147105005e87acce5c`.
O pacote preliminar `.local/exports/motion-qualidade-etapa1-20261111/` foi
superado: seu README indicava quantidade incorreta de imagens e aprovação antiga.
As fichas e imagens da seleção v2 constam no contexto; uma exportação não
representa envio ao modelo.
Skill v12 e repertório `business-reel-v2` foram acrescentados preservando versões
anteriores. A direção passou `MotionSceneDirection` e `supplied_direction`.

O commit posterior `4adb596` havia removido contratos usados pelo fluxo. Com
instrução explícita do titular, foram restaurados `MotionConstructionPlan`, os
campos `scene_direction`, `repertoire_id`, `speech_timing` e a validação de
proveniência; a seleção v2 foi adicionada. A implementação não modifica a regra
de que tempos automáticos são não revisados.

Passaram 96 testes Python dirigidos, 62 de skill/contexto, 148 de schema/geração/
construção e 7 Node, com sobreposição entre grupos, além de Ruff e Mypy em quatro
módulos. CI integral não foi executado. Não foi possível
verificar os cinco contêineres porque o acesso ao socket foi bloqueado; seu estado
atual não é afirmado. Não houve geração de assets, despesa ou renderização.
