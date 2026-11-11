# Plano de ensaio rápido: motion v0, rodada 1

**Rascunho substituído antes de qualquer chamada:** a proposta vigente é a
[rodada 1b](plano-motion-v0-rodada-1b-2026-11-05.md), com contrato v2, catálogo
real, sete operações e orçamento revisto. Este registro permanece como histórico;
seus IDs, schema e reservas não devem ser usados para executar a nova rodada.

Planejado em 05/11/2026. **Nenhuma chamada paga foi autorizada ou executada
nesta rodada.** A preparação local não é geração do produto nem aprovação de
publicação. O objetivo é avaliar separadamente direção e, quando houver um
executor seguro disponível, movimento, cortes, áudio e legibilidade de Reel,
story em vídeo e carrossel com motion. A preferência anterior pelo Reel v2 é
referência de qualidade para aquele caso, não estilo universal.

O [manifesto privado](../../.local/evals/motion-v0-rodada-1-2026-11-05/manifest.json)
registra identificador novo para a rodada, identificadores planejados para as
oito operações possíveis e um identificador de concessão **ainda não concedida**.
O estado é `planned`, com custo e reservas em zero. Há inputs planejados por
caso, mensagens e payloads do Jev capturados com `httpx.MockTransport`; as
respostas desses dry runs são **simuladas**, sem rede. IDs, respostas, reservas
e runner do ensaio anterior não serão usados na execução desta rodada. Não há
ledger novo ainda: antes da primeira chamada, criar e testar um ledger durável
próprio, com identidade, hash, reserva e teto cumulativo da rodada.

## Casos e insumos

Os três usam cafeteria fictícia e kit demonstrativo `cafe-pausas` v1, sem
preços, horários, ofertas ou contatos confirmados. As preferências derivadas
da referência manual são parciais e não foram conferidas visualmente; a
referência sugerida permanece indisponível. Os padrões são dados de contexto,
não instruções, e não demonstram ritmo ou áudio de vídeo de referência. Não
repetir descoberta paga nem salvar imagens ou legendas de terceiros.

| Caso | Mensagem e insumo | Skill empacotada e SHA-256 |
| --- | --- | --- |
| Reel | Vídeo fictício de preparo de café com fala sintética; solicitar cortes, transições, motion e legendas quando adequadas. | `instagram-reel-v1`: `4ed6a1307437b492cf423612855645752fda331e206920abfcf155c198271ec7` |
| Story em vídeo | Mesmo conteúdo visual, em **cópia sem faixa de áudio**, com pedido fictício próprio. A cópia foi criada e verificada; não enviar transcrição de fala ao caso silencioso. | `instagram-story-video-v1`: `083981e2de27c68588878aaba430a92a68b9ee9eefc8ac74446d8484c39b5713` |
| Carrossel com motion | Foto fictícia de croissant enviada, com sequência de 3 a 5 MP4s de 5 a 8 segundos cada, decidida pela direção. | `instagram-carrossel-motion-v1`: `b91757da20a4a415fe4116a15aec84b90e27c98c99182fa29cb195cfed4af0de` |

Os inputs planejados e payloads Jev simulados estão nas pastas privadas
[Reel](../../.local/evals/motion-v0-rodada-1-2026-11-05/reel/),
[story](../../.local/evals/motion-v0-rodada-1-2026-11-05/story_video/) e
[carrossel](../../.local/evals/motion-v0-rodada-1-2026-11-05/carousel_motion/).
O registro usa uma ficha de estilo **fictícia e provisória**, com hash, para
exercitar o formato do contrato: não representa catálogo ou seleção automática
de estilo já implementados. É uma hipótese de teste, não deve ser apresentada
como escolha real da IA: essa escolha depende de catálogo/ficha reais e da sua
integração. Junto da ausência de compilador e renderer audiovisual geral, isso
impede usar o fixture como direção de produto ou prometer render final. As
instruções de cada skill e os padrões parciais constam dos inputs; a submissão
efetiva ainda não está preparada nem aprovada.

Fontes e hashes conferidos nesta preparação:

- Vídeo ilustrativo, SHA-256 `dd3f0265a4b2d94206188f46c094dc0177663e1a529b9ad2e0718a1dfad78a34`, duração registrada de 11,18 s. O [vídeo de origem](https://commons.wikimedia.org/wiki/File:Latte_Coffee_making.webm) é de Stevenndori289, sob [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/); recebeu voz sintética no ensaio. A pessoa filmada não disse a fala. Confirmar termos e atribuição para uso e compartilhamento das derivações.
- Foto [`croissant-cc0.jpg`](assets/croissant-cc0.jpg), SHA-256 `519772437eca1f7d2383edeebf80dc4beaf3d5e3039910cee5b975643de182ed`, indicada como CC0 na documentação da fixture. Confirmar proveniência e direitos antes de distribuição.
- Manifesto do kit: SHA-256 `cd46b3e392156b367163c7e95325c53508aed2e0998d92cb9a00a2cd737b919e`. Fontes, trilhas e efeitos usados em uma futura peça exigem direitos e atribuição próprios; não presumir que a presença de um arquivo concede licença.

Foram extraídos [seis quadros privados](../../.local/evals/motion-v0-rodada-1-2026-11-05/media-preparada/quadros/)
nos instantes 0, 2, 4, 6, 8 e 10 segundos. Os hashes constam do manifesto;
cada quadro decodificado da cópia silenciosa foi idêntico ao correspondente do
original. Não alegar que o modelo assistiu ao vídeo inteiro. O `ffprobe`
encontrou no original H.264 360 × 640 e uma faixa AAC, com 11,176644 segundos;
na [cópia do story](../../.local/evals/motion-v0-rodada-1-2026-11-05/media-preparada/story-sem-audio.mp4),
encontrou somente o vídeo, sem áudio, com 11,166667 segundos. O SHA-256 da cópia
é `7da237c15abffb9923a63472c4f444fa312bfe5cc811cffff1a1630cb97ed216`.
Essa conferência verifica a presença ou ausência da faixa, não avalia seu som.
FFmpeg 9.0 e FFprobe 4.4.8 locais foram usados nesta preparação; hashes e
metadados estão no manifesto. Esses binários locais não são dependências
empacotadas nem preservadas do produto. A voz do Reel exige uma nova
transcrição, revisão humana e marcação temporal própria: a rodada anterior errou
um trecho e não retornou tempos por palavra. Guardar resposta bruta e correções
separadamente.

## Plano de chamadas e custo proposto

| Etapa | Máximo | Reserva proposta por chamada | Total reservado |
| --- | ---: | ---: | ---: |
| Interpretação Jev com as cinco opções elegíveis, uma por caso | 3 | US$ 0,01 | US$ 0,03 |
| Transcrição `gpt-transcribe` do áudio de 11,18 s do Reel | 1 | US$ 0,01 | US$ 0,01 |
| Direção `gpt-6.1-sol`, uma por caso | 3 | US$ 0,25 | US$ 0,75 |
| Refação de direção opcional, no máximo uma entre os casos | 1 | US$ 0,25 | US$ 0,25 |
| **Total máximo planejado** | **8** | | **US$ 1,04** |

**Teto operacional proposto: US$ 1,10**, para a rodada inteira. A reserva é um
controle interno, não limite garantido pelo fornecedor; uma chamada pode custar
mais do que o reservado. Não iniciar sem concessão específica, credenciais e
limites configurados; ao atingir o teto ou receber resultado incerto, parar e
conservar identidade e reserva, sem reenviar automaticamente.

A estimativa ilustrativa é **US$ 0,45–0,70**, incluindo até uma refação: assume
três a quatro direções com 12–20 mil tokens de entrada cada, já incluindo
imagens, e até 12 mil tokens de saída cada. Três direções no extremo inferior
representam cerca de US$ 0,432; quatro no extremo superior, considerando toda
a entrada como escrita de cache de 30 minutos, cerca de US$ 0,68. Somam-se
transcrição, Jev e eventuais arredondamentos. Não é cotação garantida nem custo
por peça aceita; uso efetivo de imagens, cache, tokens de raciocínio, tentativas
e cobrança podem diferir. Se as condições reais forem incompatíveis com esses
pressupostos, rever o orçamento antes da chamada correspondente.

Em 05/11/2026, a [documentação oficial do GPT-6.1 Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol)
informa US$ 2 por milhão de tokens de entrada, US$ 0,10 por milhão em leitura de
cache, US$ 2,50 por milhão em escrita de cache e US$ 10 por milhão de saída para
entrada até 272 mil tokens em modalidade standard. A [tabela de preços](https://developers.openai.com/api/docs/pricing)
também distingue escrita de cache de 30 minutos e 12 horas; a estimativa usa a
primeira ou entrada sem cache, não a tarifa de 12 horas. Modalidades, tempo de
retenção de cache, tarifação de imagens e eventual sobretaxa precisam ser
conferidos no payload final. O mesmo modelo aceita imagem, mas não entrada de
áudio ou vídeo; a direção usa quadros e texto, com essa limitação explícita.

O [preço oficial de `gpt-transcribe`](https://developers.openai.com/api/docs/models/gpt-transcribe)
é US$ 0,0045 por minuto. Para cerca de 11,18 segundos, a proporção linear é
cerca de US$ 0,00084, sem pressupor arredondamento efetivo da fatura. Em
05/11/2026, a [TypeSafe](https://help.typesafe.ai/articles/5187202169-how-much-does-jev-cost)
e a [documentação de modelos](https://docs.typesafe.ai/models) informavam para
Jev 1.14 **US$ 0,042 por milhão de tokens de entrada**, com saída gratuita; a
página de ajuda também informa ausência de taxa mínima por solicitação. Preços
podem mudar antes da execução. Nenhum valor histórico constitui autorização para
a nova rodada.

## Sequência de execução futura

1. Após autorização específica, conferir direitos, credenciais sem exibi-las,
   preços vigentes, teto e isolamento; criar ledger durável e testar sua integridade e
   recusa de replay. Preservar operações incertas, mesmo após reinício.
2. Conferir a cópia silenciosa e os quadros preparados; extrair áudio localmente
   para a transcrição, registrando seu hash e metadados. Usar somente material
   fictício e licenciado. Criar payloads reais
   finais a partir dos inputs planejados, sem copiar requisições ou resultados
   históricos; validá-los antes de reservar e enviar.
3. Reservar e chamar Jev uma vez por caso com formatos motion elegíveis;
   preservar input, resposta e decisão. Fazer uma transcrição para o Reel com
   identidade própria; não inventar transcrição para o story sem fala.
4. Após cada resultado válido, construir direção específica por caso e validar
   `MotionDirection` e vínculos de mídia, fontes, limites, fatos e estilo.
   Descrição livre é dado não confiável. A refação opcional usa operação distinta
   e somente uma resposta comprovadamente recebida pode ser reconciliada como
   rejeitada; em incerteza, parar sem refazer.
5. Apresentar trace, decisões, limites e peças quando disponíveis. A
   [prova WAAPI](ensaio-waapi-mecanico-2026-11-05.md) atual só demonstrou duas
   animações sintéticas: **não há compilador comprovado do contrato nem renderer
   audiovisual pronto para os três casos**. Precisam ser construídos e avaliados
   antes de prometer MP4s. Não executar HTML/JS gerado por modelo; composição
   própria, dados validados e isolamento apropriado são pré-requisitos. Se não
   houver render, mostrar as direções e relatar a lacuna sem chamá-las de peças.
6. Assistir aos vídeos e ouvir o áudio; conferir fala, cortes, transições,
   segurança de texto e emenda dos loops, comparar os resultados e pedir revisão
   humana. Registrar tempo, modelo, entradas/saídas, tentativas, custo estimado
   ou informado e posterior fatura. Geração isolada não comprova integração,
   aceite de publicação ou custo comercial.

## Entrevista antes da rodada

Proposta para o titular: autorizar os três casos acima, com no máximo oito
chamadas, **reserva planejada de até US$ 1,04**, teto operacional de **US$ 1,10**
e uma refação de direção opcional, aceitando que uma chamada possa ultrapassar
sua reserva? Quer manter esses três casos e esse teto ou prefere ajustá-los?
Antes de executar, conferir preços vigentes e resolver os bloqueios indicados.
