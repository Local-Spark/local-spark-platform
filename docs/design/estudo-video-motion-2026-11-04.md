# Estudo: vídeos e carrosséis com movimento — 04/11/2026

Este é um estudo de produto e de referências técnicas, não uma capacidade já
implementada ou homologada. O titular deseja criar publicações com movimento a
partir do material do negócio, incluindo vídeos gravados pelo cliente e
carrosséis com um MP4 por página. Também quer roteiros para orientar a gravação,
limites de duração para previsibilidade de custos e skills próprias integradas
ao contexto já existente. Geração integral de vídeo por IA e avatar ficam como
possibilidades futuras, sem escolha de plano ou fornecedor neste estudo.

## Formatos e limites conhecidos

| Formato | Proposta | Evidência e ponto a validar |
| --- | --- | --- |
| Vídeo para feed | Editar gravação ou compor peças do negócio; um Reel pode ser compartilhado também no feed. | A [coleção oficial da Meta para Reels](https://www.postman.com/meta/instagram/folder/830j7my/reels-publishing) documenta, para a API consultada, vídeo de 3 segundos a 15 minutos, MP4/MOV, até 1 GB, H.264/HEVC e proporção 9:16 recomendada. O [exemplo de publicação](https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api?entity=request-23987686-15c537cd-a773-4b40-a87c-27829e49a439) inclui opção de compartilhar no feed. |
| Story em vídeo | Edição vertical para Story, com marca, legendas e movimento. | O limite de duração de Story pela API e o tratamento de vídeos maiores não foram confirmados nesta consulta. A [documentação oficial da Meta](https://www.postman.com/meta/instagram/documentation/6yqw8pt/instagram-api?entity=request-23987686-1ff01566-3509-48bd-a0f4-8571a91ccfdf) informa que a publicação de Stories está disponível para contas Business. |
| Carrossel animado | Planejar uma narrativa por páginas e renderizar um MP4 curto por página, com a opção de misturar imagens e vídeos conforme a publicação permitir. | A [Meta descreve carrosséis que combinam fotos e vídeos no aplicativo Edits](https://about.fb.com/ja/news/2026/10/carousal-creation-on-edits/). Não foi possível confirmar na documentação oficial acessível o máximo de páginas pela API, a duração por vídeo nem o comportamento de loop por página. Validar por formato, versão da API e conta antes de prometer publicação automática. Uma página de vídeo em carrossel não é, por isso, um Reel. |

O titular escolheu para a primeira versão **até 60 segundos por vídeo final** e
quer testar separadamente vídeo gravado e carrossel animado. Esse teto é decisão
do produto, não limite geral do Instagram. A duração máxima de entrada, número
de páginas, refações e orçamento permanecem por definir; limitar só a saída não
garante previsibilidade do custo de analisar material bruto mais longo.
A disponibilidade no aplicativo não comprova disponibilidade equivalente pela
API nem garante música, stickers ou demais recursos. A renderização de MP4 em
loop precisa de verificação visual da emenda e de teste real de reprodução;
não presumir que todos os clientes reproduzem cada página indefinidamente.

## Skills examinadas

Leitura dos repositórios públicos; não foram instalados, executados ou copiados.
As descrições são o que os próprios autores documentam, não uma validação
independente de qualidade ou de custo.

| Referência | O que oferece | Adaptação a considerar |
| --- | --- | --- |
| [criador-de-carrosseis-simples](https://github.com/Felpborges/criador-de-carrosseis-simples) | Direção de copy, capa, sequência, crítica e versão animada do carrossel, com composição em código. A própria skill utiliza FFmpeg em sua renderização. | Planejamento editorial por página, continuidade e revisão; gerar originais com identidade do cliente e padrões autorizados, sem copiar identidade de outra conta. |
| [skill-reel](https://github.com/Felpborges/skill-reel) | Edição de fala gravada: cortes, ritmo e tratamento audiovisual conforme o repositório, com ferramentas de processamento incluindo FFmpeg. | Roteiro, transcrição, seleção de trechos, plano de cortes, legendas e revisão de sentido e ritmo para material do próprio cliente. |
| [showreel-interface](https://github.com/Felpborges/showreel-interface) | Narrativa curta de marca com elementos gráficos, transições e ritmo musical. | Vocabulário de movimento e encadeamento de cenas orientado pelo kit; avaliar cada recurso conforme legibilidade e necessidade do pequeno negócio. |
| [motion-por-referencia](https://github.com/Felpborges/motion-por-referencia) | Decompõe estrutura, design e movimento de um vídeo e compara aspectos do resultado. | Extrair padrões gerais de ritmo e movimento de materiais cujo uso seja permitido; manter a identidade própria e não reproduzir peças alheias. |

Os READMEs dos dois últimos mencionam licença MIT; isso não esclarece direitos
de todas as fontes, músicas e outros ativos. Não foi identificada licença geral
clara nos repositórios de carrossel e Reel consultados. Confirmar licença e origem
de cada material antes de reutilizar qualquer código ou ativo. As instruções
externas para capturar referência ou usar cookies não autorizam adquirir
conteúdo, credenciais ou dados de terceiros; a política de referência do produto
continua valendo.

## Proposta de funcionamento

1. Uma mensagem simulada ou real e o formato desejado iniciam o briefing. O
   contexto pode combinar fatos confirmados, kit, acervo autorizado, skill
   versionada e padrões disponíveis de referências, identificando sua origem.
2. A IA propõe roteiro e direção: seleção de trechos, cortes, ordem de cenas,
   ritmo, textos, legendas e movimento. Para gravação do cliente, fornece
   orientações práticas e preserva o sentido do que foi dito.
3. Um executor de mídia materializa o plano em vídeo: renderiza composição,
   áudio e legendas e codifica o arquivo. IA escolhendo a edição e ferramenta
   executando-a são responsabilidades distintas. FFmpeg é uma ferramenta
   possível de execução, usada por referências estudadas, não o responsável
   criativo. O titular confirmou que pode ser usado na montagem técnica;
   decisões de edição e motion devem ser tomadas pela IA.
4. Apresentar prévia, roteiro ou plano aplicado, origem do acervo e padrões
   usados; o cliente revisa texto, cortes, som e imagem antes de publicação.
   Uma preferência em avaliação criativa não equivale a aprovar publicação.

As skills atuais de [feed](../../../meu-braco-direito-skills/skills/instagram-feed/SKILL.md)
e [story](../../../meu-braco-direito-skills/skills/instagram-story/SKILL.md)
produzem briefings, não arquivos finais nem publicação. Foram criadas versões
iniciais de [Reel](../../../meu-braco-direito-skills/skills/instagram-reel/SKILL.md),
[story em vídeo](../../../meu-braco-direito-skills/skills/instagram-story-video/SKILL.md)
e [carrossel com motion](../../../meu-braco-direito-skills/skills/instagram-carrossel-motion/SKILL.md)
no mesmo repositório. As três passaram na validação estrutural e ainda precisam
de revisão de qualidade pelo titular. Duas prévias locais foram montadas e estão
descritas no [relatório de ensaio](../evals/ensaio-video-motion-2026-11-04.md).
Motor de renderização de produto e integração permanecem em aberto;
criar uma skill não a integra automaticamente ao produto.

Para a futura integração de produto, preservar as regras existentes de
isolamento por negócio, versão do contexto, autorizações, identidade durável
de efeitos, auditoria, custos e execução por Temporal. Análise de mídia,
armazenamento e envio a fornecedores precisam respeitar permissão, retenção e
direitos do material e de pessoas retratadas. Músicas, fontes e vídeos de
terceiros precisam de direitos compatíveis; não tratar disponibilidade pública
como autorização de reprodução.

## Custo e próximo ensaio

Editar material existente pode custar menos do que gerar vídeo integral, mas
isso é hipótese a medir, não preço garantido. O custo depende de análise ou
transcrição da entrada, chamadas de modelos, minutos processados e renderizados,
armazenamento, saídas, falhas e refações. Comparar também tempo até peça aceita
e custo por peça aceita; reservas e estimativas não são fatura. Limitar duração
de entrada e saída ajuda a prever custo, sem por si só garantir um teto quando
o fornecedor não oferece máximo conhecido. Antes de cada rodada paga, apresentar
quantidade de chamadas, tarifas vigentes, reservas e risco, e obter orçamento
específico; a autorização histórica de US$ 2 não se renova.

Referências de preço consultadas em 04/11/2026 para **renderização**, sem tratar
esses serviços como modelos criativos equivalentes: [Shotstack pré-pago](https://shotstack.io/pricing/)
anuncia 50 minutos por US$ 10, equivalente a US$ 0,10 por 30 segundos de saída;
[JSON2Video pré-pago](https://json2video.com/pricing/) anuncia até 120 minutos
por US$ 49,95, equivalente a aproximadamente US$ 0,208 por 30 segundos se
aproveitado integralmente. As modalidades têm compra mínima, serviços e regras
distintas; geração ou análise por IA, transcrição, armazenamento, refações e
impostos podem acrescentar custos. São valores de tabela, não orçamento total
nem recomendação de contratação. Renderização no computador local não gerou
cobrança externa no ensaio, mas o custo de máquina e operação não foi medido.

Para aprender rápido, seguir o [procedimento de ensaios rápidos](ensaios-rapidos-qualidade.md):
caso fictício e mensagem WhatsApp simulada, entradas e saídas de cada etapa,
prévia e arquivos para o titular comparar no ambiente local existente. Não criar
outro banco nem montar o sistema completo apenas para avaliar qualidade criativa.
O ensaio isolado não comprova integração, publicação, conformidade técnica ou
capacidade comercial; esses testes permanecem separados e, quando exigem banco,
usam base dedicada `_test` e roles restritas.
