# F04 — Artes, carrosséis e edição de vídeo

Ordem vigente: [BL01–BL06](BL-brand-library.md) entrega o kit demonstrativo
local (BL01), sua escolha e edição guiada (BL02) e um acervo opcional e privado
do negócio (BL03). BL04 usa esse contexto e um pedido livre vindo de texto ou
áudio para gerar **uma nova peça** com o kit aplicado, medindo qualidade,
fidelidade ao produto/local e custo por peça aceita. BL05 encadeia a peça à
jornada local de WhatsApp com aprovação e ajustes; BL06 amplia os nichos e
publica o catálogo em objeto/CDN. A referência do kit, quando necessária, é
**uma única imagem da mesma receita/formato**; a foto/clipe do negócio é uma
entrada separada. F04.1b/F04.2b continuam responsáveis pelo gate visual e de
vídeo da peça real.

Referência do kit na produção real (pendente em BL04): F04 recebe manifesto
compacto da receita/estilo escolhidos e, quando a rota IA precisar, **no máximo
uma imagem** da biblioteca pertinente ao formato. O texto/logo fictícios são
retirados das referências e a saída é verificada contra marca, produto, local e
fatos reais. Usar somente fotos privadas autorizadas e recuperadas do acervo
BL03 ou da mensagem atual; ausência de acervo não bloqueia o pedido. Comparar
sem kit, manifesto, manifesto + referência e composição local no mesmo caso;
registrar tokens, tentativas e custo **por peça aceita**. Ver
[biblioteca visual](../design/brand-library.md#produção-e-custo).

Showroom do kit piloto (BL01 entregue localmente; expansão em BL06): a equipe
produz **uma vez por versão** dez exemplos, stories e reels com marca fictícia
para cada kit. A web serve os arquivos prontos do catálogo; nenhuma
renderização/IA visual é executada
para o visitante que apenas compara kits. F04 só gera peças personalizadas após
escolha, com fontes reais, orçamento e gate comercial próprios. Feed, stories e
reels têm apresentações distintas no simulador interno; Facebook/TikTok seguem
como visualizações demonstrativas até homologação. Ver
[contrato do showroom](../design/brand-library.md#simulação-da-presença-futura).

Decisão adicional (26/10/2026): uma [biblioteca de receitas originais](../design/brand-library.md)
aplica o kit aprovado em formatos diferentes. Comparar no mesmo material e
briefing uma composição local profissional com edição/geração visual por IA;
escolher pelo gate de qualidade, fidelidade ao produto, preferência do dono e
custo por peça aceita. Começar com uma receita foto/story e três direções,
sem substituir uma saída ruim pelo template v4. Nenhuma rota passou ainda no
gate comercial; biblioteca e roteador estão pendentes.

Atualização de 27/10/2026: o kit demonstrativo local de BL01 existe; a
biblioteca de receitas para produção real e o roteador visual seguem pendentes.

Eval de 26/10/2026: um
[perfil sintético preenchido](../evals/visual-context-eval-v1.md) e runner
`scripts/evaluate_visual_context.py` montam um briefing a partir de foto CC0,
logo fictício, marca, catálogo, preço vigente, histórico e padrões de formato.
Uma chamada Flare/high gerou arte visualmente promissora por US$ 0,060232, mas
alterou espaçamento literal do preço e pontuação do CTA e recriou a foto. A
receita segue bloqueada para cliente; o eval não é adapter de produção nem prova
de custo por peça aceita. F04 deve ligar ferramentas de contexto por tenant,
validação de direitos, gasto por tentativa e checagem da saída ao fluxo atual.
Flare/medium com a mesma entrada custou US$ 0,026272 e pareceu comparável nesta
amostra; comparar IA para cena com tipografia/logo exatos por composição leve é
o próximo teste de rota, sem retomar o template universal como peça final.

Decisão refinada (26/10/2026): geração/edição visual por IA e composição local
com kit/receita aprovados concorrem por qualidade, fidelidade e custo por peça
aceita. A peça pode sair completa do modelo; OCR e revisão factual/visual decidem
se texto, logo e produto estão corretos. Composição local deve ser uma receita
original validada, não o template v4, que segue como baseline técnico; nunca
usá-lo silenciosamente como substituto de uma geração ruim.
Nenhum adapter de imagem/vídeo generativo está integrado ao produto hoje.
[Contrato e sequência](../design/creative-production-quality.md).

Ensaio IA de 26/10/2026: [comparação privada com foto CC0](../evals/ai-visual-spike-2026-10-26.md)
mostrou direção visual mais forte que o template v4, mas recriou detalhes do
produto/cenário. A ferramenta integrada não forneceu custo; após recarga, uma
chamada direta de edição mediu US$ 0,054885 e 19,56 s. Não promover a receita
até avaliar fidelidade, texto final e custo por peça aceita com material autorizado.

Prioridade de qualidade (26/10/2026): seguir o
[plano de produção criativa](../design/creative-production-quality.md). O
renderer v4 permanece como baseline técnico, não receita comercial. A próxima
fatia de F04.1b compara `preserve/compose` com edição de foto real por IA,
após inspeção visual e briefing F03.3b; F04.2b usa clipe real, seleção de trechos
relevantes, áudio/legenda e motion de foto. Executar benchmark com originais
autorizados, API real do produto, avaliação do dono em celular e custo de todas
as tentativas por peça aceita antes de promover qualquer receita.

Status: F04.1 e primeira receita F04.2 implementadas localmente em 25/10/2026;
F04.1b tem template v4, ajustes versionados e avaliador; F04.2b começou em
26/10/2026 com narrativa, dois cortes e revisão de ritmo. O template de vídeo
v4 conserva o clipe inteiro e há benchmark sintético e gate de revisão humana.
Revisão consentida, medição de custo em staging e seleção semântica de trechos
seguem pendentes. A fatia local de F04.3 registra candidata e entrega simulada;
envio oficial e homologação ainda pendem.
Dependências: F02, F03.

F04.1 consome apenas roteiro F03.3 aceito, contexto e material vigentes. Produz
prévia JPEG privada de foto (1080×1350) ou story (1080×1920) com identidade de
marca, foto real opcional, fato confirmado e convite genérico. O proprietário
pede e abre a prévia em `/app/ideas`; isso não aprova uma publicação. F04.2
acrescenta MP4 curto e texto de cena temporizado; F05 mantém avatar
opcional. A edição versionada do roteiro F03.3b já existe; avaliação criativa
com negócios reais permanece obrigatória antes de ativação comercial.

Exemplo visual: [arte do Hot Dog da Ana](../assets/f04-hotdog-preview.jpg),
renderizada pelo adapter F04.1b v4 com uma foto sintética usada somente para
demonstração. Em uso real, a foto vem do material autorizado do negócio; este
arquivo de exemplo não representa envio pelo WhatsApp nem publicação.

Para a cafeteria sugerida como piloto, há uma
[análise da amostra pública](../evals/priscila-public-reference-2026-10-26.md).
As fotos reais observadas evidenciam que o produto precisa dominar a peça;
as artes geométricas sintéticas atuais não passam por esse critério. A análise
não substitui material autorizado, validação factual ou aceite da proprietária.

O [ensaio privado de PhotoCraft/FilmCraft](../evals/open-source-editors-2026-10-26.md)
comparou uma composição manual da mesma foto com o renderer v4 e exportou um
vídeo de dois quadros. Demonstrou automação CLI e melhor destaque visual da
torta nessa amostra, sem IA visual, revisão da cliente ou custo cloud medido.
Experimentar esses motores atrás de adapter versionado; classificação
`preserve`/`compose`, qualidade comercial e COGS <= R$ 50/cliente/mês continuam
gates. Não ampliar o template atual como se fosse peça aprovada.

## F04.1 — Contrato implementado localmente

- `POST/GET /api/v1/organizations/{tenant}/businesses/{business}/media-previews`
  exige proprietário e plano ativo. `POST` recebe `operation_id` e `proposal_id`;
  só aceita roteiro concluído e aceito, `photo` ou `story`, um fato atual cuja
  redação coincide com o texto da cena e, quando houver foto, asset do mesmo
  negócio ainda disponível. Consentimento de IA é revalidado apenas para roteiro
  gerado com provedor externo; `baseline-v1` local não o exige.
- `render_key` inclui roteiro/documento, versão do contexto, nome/cor da marca,
  hash da foto e versão do template. `UNIQUE` por negócio e operação impede
  duplicação; o worker Temporal faz claim com `SKIP LOCKED`, tentativas limitadas,
  lease de três minutos e fencing. O download da foto confere SHA-256; o worker
  revalida entradas após o upload antes de marcar `completed`. Falhas permanentes
  terminam em `failed`, transitórias voltam à fila até três tentativas. Nenhuma
  chamada ao armazenamento ocorre com lock de linha aberto.
- O objeto fica privado no bucket de materiais, em chave determinística. `GET
  /{preview_id}/download-link` devolve link temporário só ao proprietário, após
  verificar estado, prazo, roteiro e foto de origem. A listagem esconde imediatamente
  prévia cujo material foi excluído, expirou ou perdeu o roteiro. O reconciliador
  marca esses itens para limpeza, apaga inclusive upload parcial pela chave
  determinística e só então remove a linha; erro de armazenamento mantém o
  registro para retry. IDs de proposta e asset são referências denormalizadas
  para que exclusões anteriores não apaguem o registro necessário à limpeza.
- A tela mostra pendente, renderizando, pronto ou falho; não oferece publicar.
  Texto comercial é sempre o fato confirmado; o arquivo não leva hipótese da IA.
  Testes usam PostgreSQL restrito, Temporal e armazenamento falsos, sem Meta/OpenAI
  pagos. A receita Pillow é determinística; medição de qualidade visual com
  comerciantes reais e revisão de template ainda são necessárias antes do piloto.

## F04.1b — Qualidade da arte estática (em andamento)

Primeira fatia técnica em 25/10/2026: o template estático v4 preserva a foto
inteira em enquadramentos retrato, paisagem e panorâmico, usa o recorte apenas
para um fundo desfocado e separa o fato em painel opaco. A marca aparece fora
da foto; cor clara/escura recebe contraste calculado pela luminância relativa.
Arte sem foto usa composição geométrica, sem representar um produto inexistente.
O `render_key` inclui `TEMPLATE_VERSION=4`, mantendo cada versão de arquivo
privada e imutável. Testes cobrem as bordas da foto, contraste, texto longo,
determinismo e limites de mídia. O template anterior não é alterado em disco.

O corpus sintético versionado em `docs/evals/static-art-ptbr-v1.json` cobre
quatro segmentos, foto ausente/quadrada/retrato/paisagem/panorâmica, cores
claras/escuras e foto/story. `python scripts/evaluate_static_art.py` gera
artes, folha de contato, bytes/latência e CSV de revisão em `.local/evals/static-art/`.
Esses oito casos são **teste técnico**, não aprovação de qualidade comercial.

Critérios de entrada para o piloto, definidos antes da avaliação humana:

- Em amostra consentida de ao menos 20 peças, com comerciantes de ao menos
  quatro segmentos e ambos formatos, 90% das peças devem receber nota >= 4/5
  de legibilidade e de visibilidade do produto/serviço; pelo menos 80% devem
  ser aceitas sem ajuste. Avaliação em tela de celular; registrar tamanho de
  amostra e rejeições por segmento, sem ocultar casos difíceis na média.
- Zero erro crítico de preço, produto, oferta, validade, permissão de uso da
  foto ou afirmação inventada. Um único erro crítico bloqueia o piloto até
  correção e nova avaliação do caso. A transcrição factual do banco é a fonte;
  revisão visual humana confere a peça final.
- Registrar p50/p95 de tempo de render, bytes, CPU e custo real de armazenamento
  e tráfego em staging antes de fixar teto de COGS por peça. A receita local não
  chama API paga; custo de infraestrutura ainda não foi medido. O resultado
  sintético não substitui essa medição.

Fatia técnica de 26/10/2026: `POST /media-previews` aceita `parent_preview_id` e
`emphasis=photo|text|balanced` para foto/story. Cada ajuste cria uma nova versão
privada e imutável vinculada à anterior, com chave de render distinta, operação
idempotente, auditoria, limite de quatro versões e bloqueio de concorrência pelo
roteiro. O cliente escolhe composição na web e pode refazer uma tentativa que
falhou. A API impede ajuste de roteiro ou contexto obsoleto, pai que não
seja a versão mais recente e alteração do texto factual por essa via. O aceite
do roteiro não é aceite da peça; F06 deverá vincular aprovação ao ID/hash exato
da versão final e invalidá-la quando houver ajuste posterior. Editar o texto
factual ou roteiro continua sendo F03.3b e exige novo aceite.

Use [o cabeçalho de revisão](../evals/static-art-human-review-template.csv)
para preparar o CSV privado. `python scripts/score_static_art_reviews.py <csv-privado>` calcula os gates
acima a partir de avaliações humanas com consentimento, segmento, formato,
hash da peça, notas e decisão. O resultado exibe amostra e rejeições por
segmento, sem nomes ou peças. O corpus sintético não possui essa proveniência
e não pode passar por aprovação comercial. Guardar CSV apenas em área privada;
não incluir fotos, nomes, telefone ou texto do cliente nele.

Pendências da F04.1b para piloto: coletar 20 peças consentidas de quatro
segmentos, avaliar em celular com comerciantes, corrigir os achados e repetir a
avaliação; medir p50/p95 de render, CPU, bytes, armazenamento e tráfego em
staging. A comparação local com a cafeteria indicou duas correções prioritárias:
identificar arte já finalizada para não repetir chamada/logo, e oferecer foco
de produto para fotos ou frames com muito espaço vazio sem recortar o alimento.
Essas correções devem ser validadas com material bruto autorizado. Nenhuma
evidência externa de aceite foi produzida nesta entrega.

## F04.2 — Primeiro vídeo curto (implementado localmente)

- Roteiro `short_video` F03.3 aceito e ainda válido usa a mesma operação
  idempotente, Temporal, lease/fencing, hash de fonte, armazenamento privado e
  limpeza da F04.1. A migration 0032 distingue JPEG e MP4 e guarda duração.
- FFmpeg gera MP4 H.264, 1080×1920, cerca de oito segundos, a partir de foto
  autorizada, trecho inicial de clipe MP4/3GPP autorizado ou cartões de marca.
  Fonte tipográfica incluída no worker cobre acentos PT-BR; versão do template
  invalida renderizações anteriores com glifos ausentes.
  O clipe é enquadrado no formato vertical e tem o áudio original removido.
  Três cenas
  exibem apresentação genérica, fato confirmado literalmente e CTA genérico;
  texto permanece na tela pelo tempo da cena. O vídeo é **silencioso**: não há
  voz sintetizada nem transcrição de fala para chamar esses textos de legenda
  sincronizada ao áudio. Edição com seleção de trechos, cortes múltiplos e áudio
  alinhado fica para uma evolução da receita.
- Fonte limitada a 5 MiB (foto) ou 50 MiB (clipe), com dimensões de vídeo
  verificadas antes do render; saída a 20 MiB,
  até 90 s de processo FFmpeg, dois threads de encoder
  e worker isolado da API. O arquivo só aparece depois de revalidar roteiro,
  contexto, fato, plano e material de origem; o link assinado usa `video/mp4`. Fatos com validade
  fazem a prévia expirar no fim do dia local. A web reproduz o MP4, sem ação de
  publicar. Falhas recebem código estável e tentativas limitadas.
- Render real com FFmpeg é verificado em Docker. Ainda faltam avaliação visual e
  custo por peça com comerciantes, edição de múltiplos trechos e legendas alinhadas
  à fala real antes de chamar a receita de vídeo completo comercial.

## F04.2b — Qualidade criativa do vídeo (em andamento)

26/10/2026 — O template de vídeo v3 passa a usar o texto de abertura e CTA das
cenas do roteiro aceito, sem alterar o texto do fato comercial confirmado. Uma
foto real aparece inteira sobre um fundo desfocado. Para um clipe autorizado
de pelo menos 4,5 segundos, o render seleciona o trecho inicial e um segundo
trecho distinto para a abertura e o CTA; o fato fica em cartão legível entre
eles. Clipes curtos continuam com um único trecho e CTA de marca. A saída segue
MP4 vertical H.264, oito segundos, sem áudio, prévia privada e versionada pelo
hash do documento/contexto/material/template, com a revalidação e o worker
Temporal já existentes. Não há publicação nem envio automático nesta fatia.

O proprietário agora pode pedir até três revisões privadas da mesma prévia de
vídeo, mantendo roteiro, fatos e fonte. O controle de ritmo reutiliza a operação
idempotente e o encadeamento de versões da arte: equilíbrio = 2/4/2 s; mais
tempo de cena = 3/3/2 s; mais tempo para ler = 1/5/2 s. A API verifica que o
pai é a última versão válida, pertence ao mesmo formato e permanece no mesmo
roteiro/contexto. Uma falha permite retry com o mesmo ritmo; novas versões
possuem `render_key` distinto e não substituem o arquivo anterior.

Testes unitários e de integração cobrem a escolha de cenas, limites do clipe,
retentativas/versão e fonte autorizada. Smoke FFmpeg com mídia sintética verifica
dois cortes distintos, resolução 1080×1920, H.264 e duração 7,96 segundos;
`make ci` passou com 580 testes e 100% de cobertura de linhas/ramos. A inspeção visual em celular,
medição de custo por peça em staging e revisão consentida com negócios reais
continuam sendo gates antes de considerar esta fase concluída.

Fatia técnica seguinte em 26/10/2026: o template v4 mostra o **quadro inteiro**
do clipe em ambos os cortes, centralizado sobre cópia desfocada para preencher
1080×1920. Isto evita perder produto/serviço nas bordas de vídeos horizontais.
O áudio continua removido, e a mudança de versão força novo `render_key` sem
alterar os arquivos v3. Smoke com clipe horizontal sintético verifica pixels das
duas bordas, duração, codec e dimensões da saída. A escolha dos trechos ainda é
temporal (início e trecho posterior), sem análise semântica de onde está o
produto; isso permanece pendente para a edição avançada.

`docs/evals/video-ptbr-v1.json` contém quatro cenários **sintéticos** (clipe
horizontal longo, clipe vertical curto, foto quadrada e ausência de mídia).
`scripts/evaluate_video.py` renderiza MP4s e uma folha de contato com três
instantes por caso, e registra bytes, tempo de parede e CPU por render em
`.local/evals/video/`. Rodar no worker com FFmpeg e volume privado; esses números
servem de baseline técnico, não de custo AWS ou qualidade comercial. O CSV
gerado é apenas um rascunho sem consentimento e não pode aprovar piloto.

Execução local, com o worker já construído:

```sh
mkdir -p .local/evals/video
docker compose run --rm --no-deps -T --user "$(id -u):$(id -g)" \
  -e PYTHONPATH=/src \
  -v "$PWD/scripts:/src/scripts:ro" \
  -v "$PWD/docs/evals:/src/docs/evals:ro" \
  -v "$PWD/.local:/src/.local" \
  worker python scripts/evaluate_video.py
```

O benchmark não chama Meta, OpenAI nem publica qualquer peça.

Critérios de entrada **pré-definidos** para a revisão comercial de vídeo:

- Ao menos 20 peças de negócios com autorização, quatro segmentos, no mínimo
  cinco fotos e cinco clipes. Revisar todas em celular e registrar consentimento,
  hash exato e único da peça, origem, segmento e avaliador em CSV privado.
- Em pelo menos 90% das peças, legibilidade, visibilidade do assunto e coerência
  dos cortes recebem todas nota ≥ 4/5. Pelo menos 80% são aceitas sem ajuste.
  Um único erro crítico de fato, preço, produto, autorização ou material
  enganoso bloqueia o piloto. Contabilizar rejeições por segmento e fonte.
- `python scripts/score_video_reviews.py <csv-privado>` calcula esses gates
  usando o cabeçalho em `docs/evals/video-human-review-template.csv`.
  Não guardar mídia, nomes ou telefone nesse CSV; guardá-lo fora do Git.
- Medir p50/p95 de tempo, CPU e bytes sob carga representativa em staging,
  mais armazenamento, tráfego, retrabalho e custo real por peça antes de
  definir um teto de COGS. O corpus sintético não substitui essa medição.

F04.2b permanece **em andamento**: além dos gates externos, falta escolher
trechos por relevância sem alterar fatos, avaliar texto/ritmo com comerciantes
e decidir se fala e legenda sincronizadas agregam valor com custo e direito de
uso aceitáveis. F04.3 já tem uma fatia local testável antes da Meta,
mas o piloto comercial aguarda os gates criativos e de custo.

- Aproveitar as cenas do roteiro versionado F03.3b, o contexto de marca e os
  materiais autorizados para escolher trechos e compor narrativa, ritmo,
  tipografia e CTA adequados ao segmento. Preservar literalmente fatos
  comerciais confirmados; novas alegações exigem confirmação do proprietário.
- Evoluir a receita silenciosa para mais cortes e transições intencionais. Quando
  houver fala autorizada, avaliar transcrição, edição de áudio e legendas
  alinhadas à fala realmente presente no arquivo; música e voz só com direitos,
  consentimento e custo medidos. Disponibilizar prévia versionada e pedido de
  ajustes antes de qualquer aprovação de publicação.
- Testar com corpus PT-BR e comerciantes consentidos, em celular, medindo
  legibilidade, fidelidade ao produto, qualidade percebida, tempo de render,
  custo e taxa de correções. Bloquear o piloto para erros factuais, cortes que
  alterem o sentido ou qualidade abaixo dos critérios definidos na avaliação.

## F04.3 — Percurso principal pelo WhatsApp (fatia local em andamento)

Em 26/10/2026, o workflow filho do material processado passou a pedir proposta
editorial, aguardar a geração, solicitar prévia `candidate=true` e registrar
entrega simulada por evento. A candidata é privada, versionada e não altera
`review_state` do roteiro. O proprietário pode abrir o arquivo pela API e pela
web de desenvolvimento. Sem fato atual, a simulação registra pedido de
esclarecimento. A migração 0035 diferencia candidata da prévia de roteiro
revisado; a 0036 guarda a entrega local. Repetir a mesma operação não cria outra
prévia ou entrega. Material e consentimento são revalidados nas transições.
Ainda faltam envio pelo WhatsApp oficial, recibo real, resposta orientadora a
comandos ambíguos e homologação externa.

F04.3 encadeia material/fato confirmado → ideia/roteiro validado →
prévia sem exigir que o cliente abra a web ou aceite manualmente o roteiro apenas
para iniciar o render. A aceitação técnica para gerar uma **candidata** não é
aprovação do proprietário para publicar. Guardas de fatos, direitos, consentimento,
plano, quota, validade e proveniência continuam obrigatórios; dúvida pede
esclarecimento pelo WhatsApp. Se houver várias candidatas, cada resposta deve
referir-se à peça certa.

F04.3 registra hoje uma entrega falsa durável, sem chamada de rede. O envio real
usará o canal oficial e outbox após homologação Meta; recibo, retry e estado de
entrega do provedor ainda precisam ser implementados e testados, mantendo a web
como alternativa. Falha/resultado incerto de envio não vira
aprovação nem dispara reenvio inseguro. A decisão final sobre peça, legenda, destino e horário,
inclusive comandos "Aprovar" e "Pedir ajustes", é contrato da F06. O comando
"Confirmar" usado para preço/horário na F02 nunca autoriza publicação.

## Objetivo

Transformar roteiro e materiais em previews imutáveis com qualidade previsível e custo conhecido.

## Features e contratos

- photo_post, generated_art, carousel, photo_motion_reel e edited_video_reel.
- Templates determinísticos para preço/texto e marca; áreas seguras por formato.
- FFmpeg isolado, render_key estável, armazenamento privado e validação do arquivo final.
- Voz/alinhamento quando necessário; legenda sincronizada com a fala realmente renderizada.
- Portas por capacidade para texto, imagem, fala e render, com perfil versionado,
  custo previsto, ID externo/status e disponibilidade. FFmpeg é base determinística
  das receitas compatíveis; IA generativa entra quando o formato exigir ou houver
  benefício avaliado, sem substituir produto real por imagem sintética inadvertida.
- Reserva atômica de franquia/COGS por operação antes de submit pago, liquidação e
  reconciliação de resultado incerto. Medir custo por peça, latência e retrabalho.

## Critérios de aceite e testes

- Retries de render e saída parcial sem duplicar entrega/custo indevido.
- Preço legível/correto, áudio/duração e sincronização avaliados em corpus consentido.
- Recursos limitados e concorrência de render sem afetar mensagens/HTTP.
- Avaliação paralela só em amostra consentida e com teto de gasto; comparar qualidade
  de preço/texto, fidelidade ao produto e taxa de correção com a receita base.

## Limites e decisões pendentes

- Não substituir foto real por produto sintético sem identificar e aprovar.
- Música/fontes/imagens têm licença compatível.

## Integração e manutenção

Dividir as features acima em mudanças revisáveis. Cada mudança atualiza este SDD,
`docs/PROJECT.md` e `docs/CHANGELOG.md`, incluindo evidências de testes e pendências.
Contratos que afetam outras fases devem ser refletidos no SDD geral e nos consumidores.
Não marcar como concluído por possuir mocks ou documentação de uma API ainda não validada.

## Integração com a área do cliente

Prévia, versão e materiais usados compõem revisão posterior da área web e do
WhatsApp. UI só apresenta formatos efetivamente implementados; erro, refação e
consumo têm status rastreável. Admin acompanha falhas e custos reais.
