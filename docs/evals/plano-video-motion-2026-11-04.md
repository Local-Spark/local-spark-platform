# Plano de ensaios rápidos: edição de vídeo e carrossel com motion

Estado em 04/11/2026: plano de dois testes diretos, com prévias locais gratuitas
registradas no [relatório de ensaio](ensaio-video-motion-2026-11-04.md).
Nenhuma chamada paga foi realizada nesta etapa. São dois testes independentes,
ambos com a IA decidindo
narrativa, cortes e movimento; FFmpeg está autorizado como ferramenta técnica
de montagem e codificação. Cada vídeo final terá **até 60 segundos**. Isso é
uma restrição deste ensaio, não uma regra geral do Instagram. Não foi definido
um limite para a duração do material de entrada; registrar sua duração para
orçar a análise antes de processá-lo.

Os ensaios seguem o [procedimento de qualidade](../design/ensaios-rapidos-qualidade.md):
processo local direto, sem banco novo e sem montar o sistema completo. Não
significam teste de publicação ou homologação de integração.

## Fontes propostas e conferência prévia

- O negócio fictício de cafeteria do
  [ensaio BL04.3](bl043-reference-quality-2026-11-04.md), e o kit demonstrativo
  [cafe-pausas v1](../../catalog/kits/cafe-pausas/v1/manifest.json), com
  identidade e fotos de demonstração. Confirmar adequação de cada item e seu
  escopo de uso, anotar versões e hashes. Uma alternativa é a foto
  [croissant CC0](assets/croissant-cc0.jpg), já empregada no ensaio anterior;
  ela é ilustrativa, não registro de um negócio real.
- O arquivo demonstrativo `catalog/kits/cafe-pausas/v1/assets/reel-pausas.mp4`
  é composto de fotografias e não é gravação bruta de cliente: serve como
  referência de formato, **não satisfaz o primeiro teste**. Identificar uma
  gravação de demonstração apropriada e autorizada ou registrar uma nova cena
  fictícia antes da execução. Não presumir a existência de um vídeo bruto
  adequado; revisar se contém fala, pessoas, áudio e permissões aplicáveis.
- Candidato para a gravação: [vídeo de preparo de café de Michael Burrows](https://www.pexels.com/video/person-making-coffee-7121116/),
  com 15 segundos, disponibilizado gratuitamente pela Pexels. Sua
  [licença](https://www.pexels.com/license/) permite edição e uso com condições;
  conferir o arquivo, inclusive presença de áudio e pessoas, antes de usar.
  Trata-se de material ilustrativo, não de gravação do negócio fictício; sem
  fala verificável, não serve para avaliar transcrição ou legendas faladas.
  O download respondeu HTTP 403 no ambiente; foi usado outro vídeo de demonstração,
  identificado no relatório de ensaio.
- Usar as skills próprias
  [instagram-reel](../../../meu-braco-direito-skills/skills/instagram-reel/SKILL.md)
  e [instagram-carrossel-motion](../../../meu-braco-direito-skills/skills/instagram-carrossel-motion/SKILL.md),
  respectivamente. São instruções iniciais de briefing, não editores executáveis;
  registrar versão ou hash efetivamente usado. Referências, se escolhidas, devem
  ser padrões já derivados e autorizados; indicar quais entraram em cada etapa e
  suas limitações. Não repetir coleta paga apenas para este teste.
- Jev pode ser real ou simulado; identificar a opção e mostrar a resposta. O
  processo pode chamar diretamente os componentes disponíveis, identificando
  qualquer etapa adaptada ou simulada. As entradas devem incluir apenas dados e
  materiais permitidos ao fornecedor escolhido.

## Ensaio 1 — edição de vídeo gravado

**Mensagem fictícia para WhatsApp:** “Gravei um pouco da preparação do café.
Pode transformar em um vídeo convidando o pessoal a fazer uma pausa? Use as
cores do meu negócio e coloque legendas se houver fala.”

**Objetivo:** entregar uma prévia vertical em MP4, de até 60 segundos, a partir
de gravação efetivamente registrada e autorizada. A IA deve analisar o conteúdo
disponível e propor a ideia, seleção e ordem de trechos, cortes, movimento,
texto na tela e tratamento sonoro. Se houver fala, conferir a transcrição e
preservar o sentido; se não houver, não inventá-la. O vídeo pode ser mais curto
que o teto, conforme o material e a direção criativa.

**Roteiro de execução:**

1. Confirmar arquivo, origem e direitos; medir duração e características.
   Registrar mensagem, resposta Jev real ou simulada, contexto, kit, fontes,
   skill e referências, sem inserir dados privados no repositório.
2. Preparar o roteiro de edição com trechos e tempos de origem, texto exato,
   composição, motion e plano de áudio. Verificar fatos e direitos antes de
   produzir; sem informação comercial confirmada, não inventar preço, oferta,
   produto ou endereço.
3. Executar o plano com ferramentas locais disponíveis, inclusive FFmpeg para
   montagem técnica se necessário. Anotar o que a IA decidiu e qualquer ajuste
   manual ou limitação técnica.
4. Exibir ao titular gravação de entrada e MP4 final, com roteiro, inputs e
   outputs e legenda proposta. Registrar tempo, tentativas, gastos e avaliação.

**Critérios:** narrativa compreensível, cenas e falas fiéis ao material,
legendas corretas e legíveis, cortes naturais, motion pertinente, identidade do
negócio, áudio utilizável quando presente e arquivo reproduzível. Verificar
qualidade em tela de celular e a duração com uma inspeção do arquivo. Uma peça
preferida ainda depende de aceite explícito.

## Ensaio 2 — carrossel com motion

**Mensagem fictícia para WhatsApp:** “Crie um carrossel para apresentar nosso
croissant e convidar para uma pausa, usando nossa identidade e as imagens
disponíveis.”

**Objetivo:** construir uma sequência que conte a ideia em páginas, com um PNG
composto e um MP4 com movimento por página. Como limite conservador do ensaio,
cada arquivo final terá até 60 segundos; a duração e quantidade de páginas
continuam em aberto. A IA
escolhe quantidade, conteúdo, composição, animação e duração de cada página;
a escolha concreta e o custo estimado devem ser apresentados antes de chamadas
pagas. O início e o fim de cada animação devem ser conferidos para uma repetição
visual fluida. O arquivo MP4 é finito: reprodução em loop depende do visualizador.

**Roteiro de execução:**

1. Confirmar os materiais e fontes do kit ou a foto CC0, seus direitos e hashes;
   registrar mensagem, resposta Jev, contexto, skill e referências usadas.
2. A IA propõe a sequência: função e texto de cada página, imagem, camadas,
   movimento, duração e legenda. Rejeitar dados de oferta não confirmados e
   manter informação essencial compreensível mesmo sem som.
3. Criar os PNGs e renderizar os MP4s das páginas com a direção proposta,
   usando ferramentas locais, inclusive FFmpeg quando adequado. Registrar
   adaptações e eventuais limitações.
4. Entregar visualização em ordem, PNGs e MP4s individuais, legenda, roteiro e
   proveniência. Registrar tempo, tentativas, gastos e revisão do titular.

**Critérios:** leitura fácil, continuidade narrativa, identidade coerente,
fidelidade às imagens usadas, movimento que ajude a mensagem, transição de
loop visualmente suave e arquivos reproduzíveis. Validar cada duração e observar
o conjunto no celular. A exportação não comprova que a API ou o aplicativo
aceitará todas as páginas, som ou loop; isso exige teste de publicação próprio.

## Orçamento a preencher antes da execução

Valores e quantidades abaixo permanecem em aberto. Preparar orçamento separado
por ensaio e consolidado, com moeda, impostos quando conhecidos e data das
tarifas. Identificar provedores, credenciais disponíveis sem revelá-las e risco
de ultrapassagem caso a cobrança não tenha teto técnico garantido.

| Componente | Ensaio 1 | Ensaio 2 | Como estimar |
| --- | --- | --- | --- |
| Jev/interpretação | A definir | A definir | Modelo, chamadas, tokens e tarifa ou simulação. |
| Análise/transcrição de mídia | A definir | A definir | Fornecedor, duração ou volume de entrada, tarifa e chamadas; zero apenas se não usada. |
| Direção editorial e motion por IA | A definir | A definir | Modelo, chamadas e volume de entrada e saída estimado. |
| Geração visual ou de áudio, se necessária | A definir | A definir | Modelo, quantidade, modalidade e tarifa; não presumir que será necessária. |
| Renderização/processamento | A definir | A definir | Ambiente local ou serviço, tempo e tarifa aplicável, sem confundir tempo local com fatura externa. |
| Armazenamento e transferência | A definir | A definir | Volume, retenção e tarifa aplicável. |
| Tentativas adicionais e refações | A definir | A definir | Número previsto e reservas por etapa, incluindo falhas cobradas. |
| Reserva por ensaio e total | A definir | A definir | Soma dos componentes, com margem e risco de chamada sem teto conhecido. |

Antes de rede paga, apresentar orçamento e obter autorização específica; não
reutilizar o teto de US$ 2 de outro ensaio. Cada efeito pago terá identidade,
hash e reserva em ledger durável com limite cumulativo, conforme o procedimento
vigente. Se o resultado for incerto, preservar a reserva e parar, sem reenviar
automaticamente. Depois, registrar uso, custo informado ou estimado e, quando
disponível, fatura; custo por peça aceita requer aceite e despesas apuráveis.

## Entrega e limites da evidência

Guardar arquivos privados sob `.local/evals/` com acesso restrito e um relatório
de avaliação em `docs/evals/`, sem credenciais, URLs assinadas ou material
privado no Git. Os resultados devem mostrar o conteúdo pedido, o que cada etapa
recebeu e retornou, como a IA dirigiu a edição, o que foi efetivamente
renderizado e o que o titular aprovou ou rejeitou. Identificar cada ensaio e
apresentar os resultados assim que estiverem prontos. Não publicar, nem tratar
o teste local como prova de integração, de preço comercial ou de aceitação do
Instagram. Ver também o [estudo de vídeo e motion](../design/estudo-video-motion-2026-11-04.md).
