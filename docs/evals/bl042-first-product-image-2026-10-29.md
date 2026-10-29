# BL04.2 parte 3 — primeira imagem real pelo produto

Executada em **29/10/2026**. Uma imagem real de feed foi gerada pelo worker do
produto para o **Café do Cedro fictício**, com fotografia CC0 e logo sintético
autorizados pelo proprietário nesta conversa. O teto novo foi **US$ 1 no total**,
incluindo interpretação e uma chamada de imagem, sem publicação nem repetição
automática. Os orçamentos de ensaios antigos não foram reutilizados.

**Resultado:** prévia privada `visual_ai` concluída, JPEG de **1024 × 1280**,
consultada e baixada pela API autenticada. A candidata continua com decisão
`pending`, sem aprovação de publicação, agendamento ou publicação. Esta execução
encerra a parte 3; qualidade e custo por peça aceita permanecem na BL04.3.

## Caminho efetivamente exercitado

Foi criada uma conta/organização de QA separada dos negócios existentes. O
onboarding, patrocínio local auditado, aceite único C01, catálogo, foto do acervo,
upload de logo e confirmação do kit usam os serviços existentes e roles restritas.
Não houve cobrança comercial, nova role ou ampliação de grants.

A entrada técnica simula uma foto WhatsApp já processada com legenda. O vínculo
e a comprovação do telefone são fixtures locais; não foi usado webhook Meta real.
A fotografia CC0 autorizada está na origem e no acervo. O pedido esclarecido foi:

> Crie uma foto estática para o feed do Instagram, proporção 4:5, do croissant de manteiga.

`ContentCandidateWorkflow` executou a interpretação Jev real, preparou briefing e
proposta, e solicitou uma prévia candidata. O roteiro foi montado pelo baseline
automático com fatos do catálogo; não houve edição manual nem chamada ao modelo
editorial de texto. Dispatcher, `VisualGenerationWorkflow`, activity, runner,
guarda concreta, reserva e claim são os mesmos do produto.

O adapter chamou `gpt-image-2.5-flare-2026-09-08` uma vez, qualidade `medium`,
resolução `1024x1280`, saída PNG, por `/v1/images/edits`. As duas referências eram
a mesma fotografia autorizada em papéis de origem e acervo. O logo não foi enviado
para redesenho: o acabamento determinístico aplicou o kit, os textos verificados
e o logo original. O resultado foi convertido em JPEG e gravado no armazenamento
privado real, com commit por fence e hash.

Consulta e download passaram pelo app ASGI autenticado, com sessão nativa do
owner de QA e armazenamento S3 local. A entrega de candidata registrada pelo
produto continua simulada. **A aprovação principal do cliente continua prevista
pelo WhatsApp**; seu envio e conversa reais dependem da integração/homologação.
Nenhuma aprovação web ou WhatsApp de publicação foi executada neste ensaio.

## Entrada anterior e prova de ausência de submissão

Antes da foto com legenda, houve uma entrada sintética somente textual: o Jev
reconheceu o item e a intenção, mas persistiu `suggested_format=NULL`. A regra
existente escolheu story para material textual. O executor desta chamada estava
autorizado apenas para feed e rejeitou `1152x2048` antes de incrementar o contador
ou delegar ao adapter HTTP. Resultado dessa etapa: **zero chamadas de imagem**.

O protocolo conservou tentativa, run e reserva como incertos. A conciliação
posterior foi limitada a essa execução controlada: contador original zero,
ausência dos arquivos de submissão/resposta, fontes ainda congeladas e hash do
pedido igual ao persistido. Reproduzir a mesma condição do wrapper voltou a
parar antes do delegate, com contador zero. A prova ficou em arquivo privado e
na auditoria `qa.visual_not_submitted_confirmed`.

Com essa prova positiva, `VisualCostLedger.finish(actual_usd_micros=0)` conciliou
a primeira reserva e `DatabaseVisualEffectGuard.finish(effect_resolved=True)`
encerrou o run. A tentativa, os marcadores e os eventos originais permaneceram.
Não foi inferida ausência de gasto a partir de lease ou timeout, nem criada uma
recuperação automática geral ou uma permissão de suporte C10.

A foto com legenda esclarecida entrou como **nova origem/operação**, dentro do
mesmo US$ 1 autorizado. Ela recebeu `suggested_format=photo`, consumiu uma segunda
interpretação curta e fez a única chamada real de imagem. Não houve reenvio de
uma imagem possivelmente submetida. A geração não dependeu de editar roteiro.

## Identidade e artefato privado

| Registro | Valor |
| --- | --- |
| Autorização/execução inicial | `fa43c127-38a9-4a84-8ea1-dba807db9efe` |
| Continuação, no mesmo teto | `884b252e-7ccf-5753-8bc6-307c947301cf` |
| Negócio de QA | `299cdf52-ade4-47bf-b663-29f2b4c95ebe` |
| Origem foto/legenda | `9f4a54a6-aa2d-5713-814e-c3b4d2b62f29` |
| Proposta automática | `4049cc58-67e2-4710-9898-03571f7c8d24` |
| Prévia concluída | `7cda1858-8b68-4350-8734-dc9f4ca115d2` |
| Workflow visual | `visual-preview/7cda1858-8b68-4350-8734-dc9f4ca115d2` |
| Fence / submissões HTTP de imagem | `1` / `1` |
| Reserva da imagem concluída | `30c748bf-5110-4fcb-a5bf-3a4bda0a39d4` |
| SHA-256 do JPEG | `18ee9ae8fe0edcee080fd6d2506b03c18ac4b95fdfa3bef17ba31fe12186e427` |

Arquivos locais privados, ignorados pelo Git:

- [Prévia final JPEG](../../.local/part3/feed-continuation/feed.jpg).
- [Cena PNG do provedor](../../.local/part3/feed-continuation/scene.png).
- [Resultado e identidades duráveis](../../.local/part3/feed-continuation/result.json).
- [Uso e identificador da resposta do provedor](../../.local/part3/feed-continuation/image-response.json).
- [Estimativa de custos](../../.local/part3/feed-continuation/cost-estimate.json).
- [Verificação final com geração desligada](../../.local/part3/feed-continuation/final-verification.json).
- [Prova da rejeição anterior ao HTTP](../../.local/part3/not-submitted-proof.json) e
  [conciliação em zero](../../.local/part3/not-submitted-reconciliation.json).

Os arquivos privados não acompanham um clone do repositório. A prévia e sua
proveniência também permanecem no banco e no storage local do produto, acessíveis
sob autorização do owner. Não registrar tokens, chaves, DSNs, URLs assinadas ou
base64 de imagens nos relatórios versionados.

## Uso e custo estimado

O provedor respondeu em **12,51 segundos**. Contagem retornada: **2.363 tokens de
entrada** (203 de texto e 2.160 de imagem) e **378 de saída de imagem**.

| Componente | Estimativa em USD |
| --- | ---: |
| Texto de entrada OpenAI, 203 × US$ 5/milhão | 0,001015 |
| Imagem de entrada OpenAI, 2.160 × US$ 8/milhão | 0,017280 |
| Imagem de saída OpenAI, 378 × US$ 30/milhão | 0,011340 |
| Total da única imagem OpenAI | **0,029635** |
| Duas interpretações Jev, arredondadas no ledger | 0,000066 |
| Total estimado de APIs desta execução | **0,029701** |

Tarifas OpenAI conferidas em 29/10 na
[documentação oficial do modelo](https://developers.openai.com/api/docs/models/gpt-image-2.5-flare);
o [contrato de edição](https://developers.openai.com/api/reference/resources/images/methods/edit)
confirma o snapshot, referências JSON e resolução arbitrária. Jev usou a tarifa
configurada de 42.000 USD micros por milhão de tokens de entrada, já registrada
pelo produto: 768/141 e 780/139 tokens de entrada/saída, 33 micros estimados por
operação. Isso é uma estimativa, **não uma fatura conciliada**, nem COGS completo.
Não inclui infraestrutura, storage, mensageria, suporte ou futuras refações.

A reserva da imagem bem-sucedida permanece em `uncertain`, `actual_usd_micros=NULL`,
com **US$ 0,99 preservado** no ledger. O uso de tokens não foi convertido em
liquidação financeira. O run está `finished` porque a imagem foi confirmada e
gravada; efeito resolvido e custo conciliado são estados distintos. A reserva
da etapa sem envio foi conciliada em zero com a prova descrita acima.

## Verificações e observações para BL04.3

- JPEG válido de 1024 × 1280; SHA-256 baixado igual ao commit do banco.
- Prévia `completed/visual_ai`, run `finished`, decisão `pending`, publicação nula.
- Leitura e download autenticados funcionam com geração persistente novamente
  `disabled`, flag `false` e limites zero. Consulta sem autenticação retorna 401.
- Processos habilitados encerrados; `.env` permaneceu inalterado. Filas Temporal
  exclusivas e marcadores privados impedem reiniciar as execuções por engano.
- Migração 0059 aplicada ao **ambiente local de desenvolvimento do produto**,
  preservando os dados existentes. Não houve limpeza ou teste destrutivo nessa base.
- Sem mudanças em código de produção ou testes: `make lint types` aprovado,
  mypy em 151 módulos e **94 testes unitários dirigidos** aprovados. O último
  `make ci`, da parte 2 e do mesmo código, permanece como evidência de **1.914
  testes e 100% de linhas/branches**; não foi repetido nesta execução operacional.

Inspeção inicial do desenvolvedor: o croissant continua reconhecível e sem
recheio, a paleta foi aplicada, o nome e o texto principal estão legíveis e o
logo original foi composto localmente. O logo ficou pequeno na área reservada e
a CTA é genérica. O roteiro incluiu o nome do produto, sem preço; não se afirma
equivalência com todos os textos do ensaio isolado anterior.

Essas observações não são aprovação de titular, fidelidade documental de um
negócio real ou aceite comercial. A classificação de formato do primeiro texto,
legibilidade do logo, CTA, fidelidade e custo incluindo refações precisam de
avaliação na **BL04.3**, com post e story e revisão humana no celular. Não houve
nova geração para corrigir a amostra. A **BL05** fecha o percurso principal de
ajuste/aprovação pelo WhatsApp e proatividade; o canal real mantém seus gates Meta.
