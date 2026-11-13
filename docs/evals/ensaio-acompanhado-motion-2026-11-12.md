# Ensaio acompanhado — preparação e lacunas antes do modelo

**Continuação implementada em 12/11:** proposta de direção no plano a partir da
mensagem/contexto, piso funcional independente dos alvos anteriores, catálogo
sonoro real local e repertório v4 sem os oito prints. Pacote real privado v4
montado sem envio, com fonte/base/materiais preservados. Ainda não há plano/código
novos, orçamento autorizado, render ou qualidade aprovada. Detalhes, validação e
limites em [Preparação audiovisual revisável](../design/motion-planejamento-audiovisual-revisavel-2026-11-12.md).
As afirmações abaixo sobre funcionalidades ausentes descrevem a inspeção anterior.

Data: 12/11/2026. Continuação das fases 1–3 de preparação/revisão. Nenhuma
chamada paga, nova geração de asset, render, criação de pedido ou alteração de
banco nesta inspeção. Na captura inicial, HEAD era `4adb596`; alterações staged
do titular foram preservadas. Esta entrega registra a primeira fronteira do ensaio, não uma nova
peça nem a conclusão do percurso até `awaiting_render`.

## Revisão posterior — prints e uso das fontes

Complemento de 12/11/2026, após o titular examinar os oito prints apresentados
no chat. HEAD conferido: `30c6575`; working tree estava limpo antes desta mudança
documental. Esta decisão estava na conversa/mensagem de transição e passa a
integrar a documentação. Os registros da captura inicial abaixo são históricos.

O titular considerou a seleção genérica e sem utilidade demonstrada para a
qualidade esperada. A inspeção confirmou arquivos idênticos aos bytes dos
respectivos payloads, distinguindo a geração executada do rascunho não enviado:

| Seleção | Arquivos/IDs | Instantes aproximados | Situação |
| --- | --- | --- | --- |
| Explicação de trajetória/interpolação, Maestros | `021.jpg`, `022.jpg`, `023.jpg` / `maestros-trajetoria-021/022/023` | 01:20, 01:24, 01:28 | Enviados na última geração, repertório v2 |
| Objetos orbitando a pessoa, Lucas Leite | `lucas-orbit-03.jpg`, `lucas-orbit-05.jpg` | 00:03, 00:05 | Enviados na última geração, repertório v2 |
| Planos, luz e sombra, Maestros | `maestros-space-041.jpg`, `maestros-space-042.jpg`, `maestros-space-043.jpg` | 02:40, 02:44, 02:48 | Acrescentados no rascunho v3, ainda não enviado |

Os cinco primeiros também estão no rascunho v3. São arquivos em
`app/assets/motion_repertoire/business-reel-v2/references/` e
`app/assets/motion_repertoire/business-reel-v3/references/`. A associação aos
payloads comprova entrega/integridade, não aproveitamento criativo. Não houve
comparação controlada que demonstre ganho causado por esses prints; também não
há evidência para atribuir a eles, isoladamente, toda a regressão das peças.
As fichas existentes descrevem mecanismos genéricos, mas não demonstram a
transferência para as ações, transições e o acabamento esperados nesta peça.

**Decisão para a próxima rodada:** retirar esses oito prints da seleção. Manter
arquivos, hashes e pacotes históricos; esta decisão não remove quadros da
gravação, previews dos materiais, evidências da base, skills, exemplos de código
ou bibliotecas úteis. Não substituir os prints por outra seleção arbitrária nem
tratar quantidade de anexos como ganho de qualidade.

Cada referência futura precisa explicitar:

1. A necessidade concreta da cena e o mecanismo pertinente que demonstra.
2. A evidência disponível: quadro para composição; sequência temporal adequada
   ou trecho para movimento. Não inferir curva, sincronismo ou escuta de prints.
3. A adaptação viável aos materiais, kit e executor existentes, sem transformar
   o exemplo em receita obrigatória de Café Pausa.
4. Os limites da referência e onde sua aplicação poderá ser conferida no plano
   e, após autorização, no resultado visual/sonoro.

Ausência de evidência pertinente deve ficar explícita; não anexar imagens apenas
para preencher um repertório. A seleção precisa passar pelo montador real. Hoje
ele exige as imagens exatas do pacote capturado; implementar a seleção revisada
requer evolução compatível do pacote/contrato, preservando validação de presença,
associação e hash. **A retirada ainda não foi implementada no runtime.**

A conferência também esclareceu a origem das skills: o repositório
`../meu-braco-direito-skills` mantém a skill de Reel original (22 linhas), igual
à cópia v1 local. O percurso HTML usa `instagram-reel-v13` (713 linhas), evoluída
dentro da plataforma. `../meu-braco-direito-motion-sources` e extratos
Maestro/Finalizador continuam como fontes de consulta. Seleções de orientações e
três exemplos adaptados chegam ao modelo; os agentes/processos completos dessas
fontes não são executados por essa chamada, que não oferece ferramentas de
busca. Não confundir fonte disponível, conteúdo anexado, capacidade integrada e
qualidade comprovada. Não importar tudo nem descartar os mecanismos existentes
para resolver a curadoria.

Escopo deste complemento: documentação e rastreabilidade. Sem mudança de código,
assets, pacotes, banco ou serviços; sem chamada paga, render ou novo teste de
qualidade. Diff e referências documentais conferidos; CI integral não foi
executado nesta alteração exclusivamente textual. A implementação e a avaliação do efeito
da nova seleção continuam pendentes.

## Entrada após a entrevista

Mensagem simulada proposta pelo operador após a correção do titular:

> Faça um Reel com esse vídeo para divulgar minha cafeteria.

O cliente não precisa pedir preservação técnica de voz, duração ou kit. O
negócio autenticado, o ID do vídeo e o kit confirmado são contexto do produto.
Preservação e direitos continuam nos controles existentes. Não atribuir essas
regras a uma frase fictícia do cliente.

O titular definiu também:

- Incluir seleção de efeitos autorizados, buscando biblioteca pública com
  licença comercial verificada. Isso não autoriza geração paga de sons.
- A peça anterior é um piso de qualidade. Suas funções e capacidades não podem
  desaparecer silenciosamente; composição, objeto, cenário, borda, número de
  elementos e transições não são um molde obrigatório.
- Revisar cada fronteira. A parada final solicitada continua anterior a qualquer
  render, inclusive captura de storyboard; plano e código têm revisões separadas.

Essas definições pertencem ao ensaio/produto, separadas da mensagem simulada.
O artefato privado `intake-v2.json` conserva essa distinção. Sua rubrica ainda é
uma proposta de avaliação do operador, não um novo contrato implementado.

## O que executamos realmente

O script privado `prepare.py` usou `MotionContext.capture` com owner/tenant e
negócio existentes, `MotionInputLoader.prepare` e o exportador que chama
`OpenAIMotionProvider.build_request`. A consulta foi ao banco existente com
escopo/RLS. Leitura de mídia ocorreu depois de sair da transação. Não houve POST
de admissão, workflow novo ou submissão ao provider. O transporte do exportador
impede envio ao modelo.

| Fronteira | Entrada | Saída efetiva | Lacuna e impacto seguinte |
| --- | --- | --- | --- |
| Mensagem → solicitação | Primeira mensagem simulada e direção herdada preenchidas pelo operador | `draft-request.json`, validado pelo schema | Não percorreu interpretação natural do cliente. Acrescentar `client_message` não implementa essa interpretação. |
| Solicitação → contexto | Fonte/negócio, kit confirmado, skill, repertório, seleção histórica | Snapshot novo lido do produto | Base registrada é anterior à última prévia; matriz e direção herdadas ainda condicionam a geração. |
| Contexto → mídia | Assets privados existentes, seleção de evidências | 15 quadros da fonte, 20 da base registrada, oito referências e um preview da xícara | Mais amostras não demonstram qualidade, movimento contínuo ou escuta. |
| Fala → cues | Transcrição histórica local da mesma fonte/hash | ASR reutilizado para esta preparação, com proveniência não revisada | Não houve nova transcrição nem análise de prosódia/eventos sonoros. |
| Contexto/mídia → payload | Contratos e anexos reais | `generation-request.json`, 44 imagens, manifesto verificado | O pacote chegou íntegro, mas carregava escolhas inadequadas ao feedback vigente. |
| Entrevista → revisão da entrada | Pedido simples, piso funcional e efeitos autorizados | `intake-v2.json`, `status.json` e provas locais de contrato | Rascunho anterior marcado `superseded_do_not_submit`; não existe payload novo pronto para envio. |
| Modelo → plano → código | Ainda não submetido | Nenhum retorno novo | Sem orçamento novo, direção reconciliada ou arquivos sonoros vinculados. |

Fonte, kit, áudio original, duração de saída e transcrição do primeiro pacote
coincidem com os artefatos da rodada anterior. Skill efetiva:
`instagram-reel-v13`; repertório: `business-reel-v3`; contrato de geração:
`provided-direction-output-v4`. As oito referências incluem as três amostras
adicionais de luz/camadas. O negócio desta prova não tinha fotos de acervo,
referências de negócio ou áudios adicionais elegíveis na consulta. Isso não é
uma afirmação sobre todo o conteúdo do repositório ou sobre outros negócios.

O payload montado, **não enviado**, configurava `gpt-6.1-sol`, esforço `high`,
54.000 tokens máximos de saída, schema estruturado e textos/imagens. Não contém
ferramentas de busca ou geração de áudio. Portanto, citar uma biblioteca em uma
skill não faz esse modelo buscar arquivos durante a chamada.

SHA-256 do payload histórico desta preparação:
`ac1c210517e93988881b367ee7b5ab72b77a5c0e212abf69c7c61abc5a76b172`.
SHA-256 do manifesto:
`9453bd5080173e003a8c3895ba0a0c621e46a2ff2f8ee322ba83a3010694070b`.
Ambos preservados para investigar a entrada incorreta; não representam aprovação.

## Falhas concretas encontradas antes de gastar

1. **Mensagem simples ainda não alimenta este percurso acompanhado sozinha.**
   `MotionRequest` aceita uma instrução simples no caminho legado. Com
   `review_checkpoints=true`, exige preparação, direção fornecida e storyboard.
   A prova local sem direção devolveu `Checkpoints require preparation, supplied
   direction and storyboard`. A inspeção adicionada nas fases 1–3 não é um
   planejador que transforma mensagem/contexto em direção audiovisual.
2. **A direção herdada continua vinculante.** O pacote fixa três cenas e traz
   18 disposições `preserve`. O contrato permite `replace`, mas exige que o
   operador já declare os alvos. Não é um piso independente do desenho anterior.
   A prova local alterando uma composição foi rejeitada por
   `MOTION_VISUAL_DIRECTION_CHANGED`. Chamar a direção de hipótese não muda isso.
3. **Existe instrução sonora conflitante herdada.** `cafe-vapor.appearance`
   ainda contém “sem caricatura, nuvem ou novo SFX”. `sound_events` está vazio.
   Não devemos enviar essa preparação e esperar que o modelo resolva o conflito.
4. **Obtenção/seleção de som não foi integrada.** `MotionSoundEvent` exige um
   UUID de material já existente, trecho, início, ganho, fades e declarações de
   direitos/não duplicação. `MotionContext.capture` consulta somente esses IDs;
   o mixer compila os eventos. Nenhum desses mecanismos pesquisa efeitos ou
   escolhe eventos a partir da fala. Metadados de um candidato externo ainda não
   são um `sound_event` utilizável.
5. **A base formal não é a última prévia.** O seletor consulta
   `motion_render_versions`. A prévia de hash
   `e4bfabe68500189d6cd147f440f8ef4f2bccabd6e3001dff08cebf9e7e5d47f0`
   pertence ao pedido ainda falho, sem versão de render registrada. A base
   disponível, `187b611018d2b24c27edb99f07a4a21aecd5599e7333a64ad1b227147df0c451`,
   é “Nova — quatro melhorias”. Não foi inserida aprovação ou versão fictícia.
   O feedback posterior esclarece que ambas servem como evidência de avaliação,
   não como autorização para congelar um template.

São lacunas de preparação e integração, não uma nova piora visual observada:
nenhuma candidata nova foi produzida. Não apagar contratos úteis para contornar
as falhas; separar proposta de direção, critério de qualidade e plano aprovado.

## Onde nossas fontes já falam de áudio

| Fonte existente | O que registra | O que não chegou a este fluxo |
| --- | --- | --- |
| [Análise Maestros, 04:43–05:24](analise-video-maestros-WuzMxEKJHkQ-2026-11-11.md) | ElevenLabs para efeitos/música, efeitos a partir de texto, ducking e medição | Obtenção de efeitos por esse provedor e direção sonora automática não foram integradas. |
| [Contrato original, etapa 5](../design/contrato-evolucao-qualidade-motion-2026-11-11.md) | Acervo licenciado primeiro; efeitos com função; conferir sons da fonte; geração paga não obrigatória | Catálogo populado, seleção pertinente e escuta real continuaram pendentes. |
| [Entrega da etapa 5](../design/motion-etapa-5-som-e-voz-2026-11-11.md) | API/mixer para material previamente selecionado; modelo não escolhe complementos | Documento declara seleção/obtenção e interface pendentes. O ensaio manteve lista vazia. |
| `claude-video/estilos/porto-de-nova-york/LEIA-ME.md` e `sessao-na-mesa/ESTILO.md` da skill instalada | Exemplos de efeitos sintetizados em código e trilha por filme/banco General MIDI | Exemplos não são um catálogo de sons já autorizado no negócio nem serviço integrado de geração sonora. |
| `meu-braco-direito-motion-sources` e extratos Maestro/Finalizador consultados | Snapshots de estilos e, nos extratos, busca de b-roll em Pexels/Pixabay/Coverr | Busca de b-roll é de vídeo; não foi encontrada nesses extratos uma seleção de efeitos conectada ao nosso produto. Não afirmar busca exaustiva no ZIP original. |

A transcrição local do vídeo (`transcript-working.txt`, 04:54–05:21) descreve
efeitos por texto e música ajustada à duração, seguida de ducking e medição.
Não confundir a informação já documentada com disponibilidade de arquivos no
negócio. A pergunta sobre origem deveria ter partido desse inventário existente.

O titular escolheu biblioteca pública com licença comercial verificada para a
rodada atual. Foram identificados por pesquisa do operador, fora do runtime:

- [Pouring coffee — Maajora](https://freesound.org/people/Maajora/sounds/432775/):
  página declara CC0, WAV, 5,052 s. Só considerar quando houver ação de servir
  correspondente; não induzir a direção a criar esse gesto apenas pelo arquivo.
- [Tea cup set down — TheHiraHira](https://freesound.org/people/TheHiraHira/sounds/460242/):
  página declara CC0, MP3, 5,073 s. Só considerar para contato/apoio pertinente.

Páginas originais conferidas; download oficial indica login. Não houve download,
escuta, importação nem geração. Licença declarada, qualidade sonora, adequação,
hash do arquivo, trecho e vínculo de runtime são verificações distintas.
ElevenLabs continua documentado como alternativa de geração, sem nova chamada
ou autorização de gasto. Fixtures sintéticas antigas não foram promovidas a
efeitos reais para preencher artificialmente a ausência.

## Piso de qualidade e próxima fronteira

A proposta em `intake-v2.json` separa significado, integração da gravação,
coerência espacial, continuidade, ritmo, identidade e som. A referência dá o
mínimo de funções/qualidade; cada peça pode realizá-las de outra forma. O número
de elementos não mede ganho. O contato existente da prévia foi inspecionado:
há objeto com apoio e retorno da gravação, mas também amostras com grande área
sem assunto central durante a espera. Não transformar limitações da referência
em qualidades a preservar. Quadros não provam duração percebida nem som.

Antes do próximo gasto, precisamos reconciliar a mensagem/contexto com uma
proposta de direção audiovisual, materiais efetivamente disponíveis e uma
avaliação funcional que não obrigue repetição da composição. O pacote precisa
mostrar como cada intenção chega ao plano e registrar o que não pode executar.
Não basta retirar a matriz de preservação, acrescentar um prompt ou importar um
clique. As pausas e as garantias técnicas existentes continuam necessárias.

Condições operacionais ainda abertas: dev na revisão 0117 (0118 aplicada somente
ao `_test` autorizado); orçamento novo inexistente; `plan_motion` exige capacidade
de três reservas mesmo com pausa após plano. Não reutilizar orçamento histórico,
migrar dev implicitamente ou aumentar teto para contornar a admissão.

## Artefatos e verificações desta inspeção

Pasta privada ignorada pelo Git: `.local/evals/motion-supervised-20261112/`.

- `draft-input/`: pacote real preservado para auditoria, superado pela entrevista.
- `preparation-report.json`: resultado da captura inicial, com suas pendências
  históricas; consultar `status.json` para a situação posterior.
- `intake-v2.json`: mensagem e decisões vigentes, rubrica proposta e bloqueios.
- `sound-candidates.json`: candidatos e limites da pesquisa, sem assets vinculados.
- `contract-probes.json` e `reconcile_interview.py`: provas offline no schema e
  no validador reais; manifesto/hash conferidos, direção herdada rejeita alteração.

Consultas ao negócio apenas de leitura; probes posteriores sem banco, provider
ou renderer. Os cinco contêineres foram novamente consultados e continuam
`exited`. Nenhum serviço, tabela ou dependência foi criado. Produção não foi
alterada nesta fatia; não se repetiu CI integral. Os resultados de testes das
fases 1–3 continuam históricos e não certificam esta rubrica ou qualidade visual.
