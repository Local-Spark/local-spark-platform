# BL04 — contexto seletivo e produção visual com IA

Estado: **em implementação local**, sem aprovação comercial. Complementa a [trilha BL](BL-brand-library.md#bl04--recuperar-contexto-e-produzir-uma-peça-nova), o [SDD geral](../SDD.md) e os contratos transversais F03/F04.

## Objetivo

A partir de um pedido livre e de informações autorizadas do negócio, identificar o que o cliente pretende divulgar, selecionar somente as fontes pertinentes e produzir uma prévia privada com identidade visual e IA. A revisão e eventual publicação permanecem ações distintas. O WhatsApp real depende de homologação Meta; os testes usam entradas sintéticas e mocks.

## Entregas e gates

### Andamento da BL04.1

O worker pode usar o **Jev como primeiro candidato** em desenvolvimento/teste,
desligado por padrão. O proprietário autoriza separadamente o envio de texto e
nomes de candidatos à TypeSafe. Uma operação durável reserva orçamento por tenant
antes da chamada; o acesso, origem e snapshot são revalidados, e uma resposta
incerta não é repetida automaticamente. Recusa de orçamento antes da submissão
tem estado próprio: a retomada usa verificação no ledger e operação atômica; o
workflow aguarda em intervalos de uma hora, por até sete dias, revalidando a
origem e o acesso. Estados `uncertain` antigos não são reclassificados. Um esclarecimento fica registrado no
adaptador local simulado, sem afirmar envio real pelo WhatsApp. A configuração
requer `TYPESAFE_API_KEY`, `MEU_BRACO_DIREITO_INTENT_AI_MODE=jev`, chave de
criptografia e orçamento diário positivo `MEU_BRACO_DIREITO_INTENT_AI_DAILY_BUDGET_USD_MICROS`.
Esse teto é por tenant/dia, em milionésimos de dólar; é conservador, não uma
fatura nem um limite global para outras APIs. A chamada real exige autorização de
gasto específica e uma avaliação PT-BR mais ampla antes de liberar produção.

Para a oferta inicial de **R$ 99/mês**, o proprietário definiu foto e story como
formatos iniciais; vídeo será definido depois. O interpretador consulta essa regra
única após a verificação do acesso e pede esclarecimento se o formato pedido for
indisponível. A regra estática descreve somente a oferta inicial e precisa ser
substituída por permissões persistidas quando houver múltiplos planos. Não define
quantidade de peças nem autoriza gerar ou publicar.

Permanecem limites relevantes da BL04.1: a interpretação de formato é experimental,
sem franquias de quantidade implementadas; preço e agenda não são confirmados pela IA.
O nome do item ativo e versionado pode servir de fonte factual do roteiro, com
identificador vinculado à versão do acervo e nova validação na edição. Nomes que
contenham alegações comerciais exigem outro fato confirmado; preços e ofertas não
são inferidos do nome. A pergunta simulada é genérica e não mantém uma conversa completa.
Prévia real com este briefing permanece bloqueada; há apenas o modo simulado da
BL04.2. Kit é congelado na proposta; as referências fotográficas ainda não são
enviadas a um gerador visual. Portanto
não afirmar que o fluxo completo ou a qualidade comercial estão concluídos.

### Andamento da BL04.2

O proprietário pode conceder, quando o modo visual estiver configurado, e
retirar em Sobre meu negócio uma autorização específica para o envio futuro de
contexto visual e fotos autorizadas à OpenAI; a API permite retirada mesmo com
o modo desligado.
É independente do consentimento de texto; a tela informa que a criação de
imagens ainda está em preparação. O serviço registra as mudanças por negócio e
mantém isolamento entre organizações. O modo visual continua desligado por
padrão e restrito a desenvolvimento/teste.

Há uma jornada simulada em desenvolvimento/teste: captura o contexto, lê até
uma foto enviada pelo WhatsApp e fotos pertinentes do item e do espaço, confere
hashes, normaliza orientação e remove metadados das cópias; preserva o original.
O pedido usa o kit, fato e CTA conferidos. Uma tentativa com fence e reserva
transacional produz um arquivo explicitamente marcado como simulação, privado e
sujeito a revisão. Isso **não é uma imagem criada pela OpenAI** e não comprova
qualidade. O resultado é revalidado antes do acesso e da decisão.

Para testes técnicos, `MEU_BRACO_DIREITO_VISUAL_AI_MODE=fake` e um teto mensal
positivo `MEU_BRACO_DIREITO_VISUAL_AI_MONTHLY_BUDGET_USD_MICROS` habilitam a
simulação apenas em desenvolvimento/teste. A reserva fictícia é de um
milionésimo de dólar e liquidada em zero; não aciona a OpenAI. A interface
identifica o arquivo como simulação e ele não deve ser publicado. A seleção
manual de modo é feita pela API; no worker, o modo fake é escolhido para proposta
com briefing quando configurado. O padrão permanece desligado. Não alterar para
`openai` para tentar usar essa rota: o fluxo real continua bloqueado.

A intenção e a reserva são atômicas com o fence, mas a verificação das fontes e
do consentimento ainda ocorre em outra transação, sob outra role. Não habilitar
chamadas reais enquanto essa lacuna persistir. A [proposta para atomicidade](../design/BL04-atomicity-proposal.md)
registra uma alternativa para revisão: uma tentativa de migração de permissões
foi rejeitada pela revisão automática do ambiente. Faltam ainda teto global do
ensaio de US$ 1, tratamento completo de respostas incertas, integração real com
provedor, validação de qualidade e custo. O fluxo de foto sem legenda ou produto
identificado continua dependente de um briefing BL04.1 válido. O pedido usa a
paleta e a composição do kit, mas ainda não aplica as fontes, o nome, a tagline
ou o logo; o hash do logo apenas participa da validação. Isso é uma lacuna de
fidelidade, não um kit aplicado integralmente.

Decisão do proprietário em 27/10/2026: se ele alterar o kit ou excluir uma
foto enquanto uma imagem estiver sendo criada, aplicar a alteração ou exclusão
imediatamente e descartar a prévia produzida a partir da versão antiga. Isso é
distinto da retirada de autorização visual, que aguarda as criações já iniciadas.
O comportamento real exige revalidação e testes concorrentes; não presumir que
está completo apenas por existir no fluxo simulado.

Um [ensaio isolado de feed](../evals/bl042-guarded-synthetic-feed-2026-10-27.md)
gerou uma imagem real da OpenAI usando exclusivamente dados fictícios e foto
CC0; uma chamada custou US$ 0,026272 estimados. Não utiliza o fluxo de cliente,
não comprova fatura nem margem, e a IA alterou logo e pontuação. Um acabamento
experimental pode aplicar nome, logo original e textos validados a uma cena
sem texto; não está integrado nem aprovado. O executor de provedor também está
isolado: um CAS no ledger impede reenvio, sem liberar o envio real de fontes.
Continuam obrigatórios coordenação das fontes, custos e revalidação completa.

Após a decisão de alteração imediata do kit/foto, dois testes concorrentes do
fluxo simulado confirmam que a modificação conclui sem esperar o renderer e a
prévia antiga é descartada. O acabamento experimental agora possui serviço que
revalida kit, logo, direitos e texto antes/depois, e um orquestrador com guarda
injetado exercita envio, revalidação, descarte e armazenamento com mocks. Nenhum
deles foi ligado ao worker ou constitui guarda real aprovado. A revalidação do
acabamento relê referências e precisa de medição antes de operar em escala.

### Retirada de autorização visual — decisão do produto

Quando o cliente solicitar a retirada, impedir imediatamente novas admissões
para geração; os trabalhos que ainda aguardam na fila devem ser cancelados. As
gerações que já começaram a usar as fotos podem terminar e a interface deve
informar que a retirada está pendente até seu encerramento. Sem uma tentativa
em andamento, retirar imediatamente. O estado pendente deve ser durável e
isolado por negócio, inclusive após reinício do worker. Resultado desconhecido
por falha não comprova conclusão: bloquear novos inícios e indicar que o pedido
está em verificação. A prévia de uma geração já iniciada que terminar durante a
pendência continuará visível para revisão do cliente após a retirada; isso não
autoriza uma nova geração nem equivale à aprovação ou publicação.

O fluxo **simulado** implementa esse controle com admissão e pedido serializados
por negócio, sem manter transação aberta durante o processamento. Trabalhos não
admitidos são ocultados imediatamente e o dispatcher os marca como falhos quando
os encontra. Somente a prévia comprovadamente concluída durante a pendência pode
ser consultada depois da retirada, inclusive após nova concessão; as demais
fontes continuam sujeitas à revalidação. A decisão de publicação após a retirada
continua bloqueada. Processos em estado incerto não são encerrados por timeout:
exigem verificação e não possuem reconciliação automática nesta entrega.

Essa implementação não autoriza contornar os limites de acesso existentes e
**não está conectada ao provedor real**. Não comprova exclusão de dados no
fornecedor. URLs privadas já emitidas mantêm sua validade limitada prevista;
o gate não revoga retroativamente um link já entregue.


1. **BL04.1 — Interpretação e contexto:** interpretar intenção e formato dentro das opções efetivamente disponíveis; localizar candidatos no acervo do mesmo negócio com produtos/aliases ativos e validade no fuso do negócio. Correspondência lexical é só candidato: negação, ambiguidade ou ausência de fonte não autorizam escolher produto automaticamente. Fotografias precisam de direito válido; dados de outro tenant, item arquivado e preços vencidos não podem compor o briefing. Kit confirmado, fatos, itens e mídias devem ter versões e proveniência verificáveis. Revalidar antes de efeito externo e antes de liberar o resultado; revogação, exclusão e alteração invalidam as dependências afetadas.
2. **BL04.2 — Imagem e custo:** integrar um provedor de imagem ao caminho real da prévia, com consentimento aplicável, referências mínimas e saída privada; registrar operação, versão de modelo/briefing, fontes e uso. Uma referência de kit no máximo, quando necessária; fotos reais pertinentes do negócio são referências separadas. Se a promessa for retratar local/produto reais, não apresentar um ambiente inventado como fotografia documental. Texto/preço/CTA exigem conferência literal; resultado generativo não comprova fidelidade por si só. Falta de fonte deve gerar pergunta ou conceito identificado, não fato inventado.
3. **BL04.3 — Qualidade e economia:** avaliar post e story novos em celular com titular e materiais consentidos. Registrar rejeições, retrabalho, todas as tentativas e custo por peça aceita; avaliar separadamente legibilidade, identidade, fidelidade e texto. Ensaios fictícios e comparação entre modelos medem viabilidade técnica, mas não substituem aceite do titular nem comprovam margem.

## Fornecedores e controle de risco

A opção de imagem é um adapter por capacidade, comparado com receitas aplicáveis usando qualidade e custo por peça aceita; não prometer que todas as peças serão boas por trocar de modelo. A hipótese é R$ 99 de mensalidade e **custo total máximo pretendido de R$ 50/mês**, incluindo serviços externos, infraestrutura, retentativas e suporte. O valor não foi validado. Vídeo, animação e avatar têm gates próprios e não são automaticamente entregues pela integração de imagem.

Antes de qualquer geração paga para cliente, reservar o limite de gasto por operação e tenant de forma atômica, registrar o intento durável, executar fora da transação, liquidar uso conhecido e tratar como **resultado incerto** qualquer timeout após possível submissão. Não repetir nem trocar provedor automaticamente quando houver risco de cobrança duplicada. Validade do direito, acesso e referências deve ser verificada também após a chamada. Auditoria/telemetria não expõem segredos, imagens ou prompts privados por padrão.

Para a avaliação inicial, o usuário autorizou até **US$ 1 no total para chamadas de imagem com dados fictícios**. Esse teto é para o ensaio, não é franquia comercial e não autoriza dados de clientes nem gastos ilimitados. Testes automatizados usam mocks e não fazem chamadas pagas. O custo informado pelo provedor deve ser distinguido de estimativas e da fatura final.

## Avaliação do Jev

Jev é o primeiro candidato para classificação curta, necessidade de esclarecimento e sugestão de formato; não é gerador de imagem e não decide permissões, consentimento, fatos ou limite de gasto. Um corpus PT-BR sintético com gabarito e casos de ambiguidade/negação compara baseline e modelos, taxa de acerto, abstenções, latência e custo. A [comparação Jev/OpenAI](../evals/intent-comparison-2026-10-27.md) aponta erros em ambos e saídas incompletas da OpenAI; não é holdout independente nem teste da memória do WhatsApp. O ensaio é offline por padrão, sem dados de clientes. A amostra não aprova uso comercial.

**Pendências da validação:** o runtime consulta nomes/aliases por correspondência
lexical e processa eventos isolados; não há memória de conversa validada. Os caminhos
de conversa e de conteúdo precisam coordenar uma única resposta por evento antes
do envio real. Circuit breaker/rate limit de provedor e capacidade em escala ainda
não foram homologados. A reserva de custo conhecida mantém o máximo diário, mesmo
após sucesso; avaliar liquidação segura para não limitar o throughput indevidamente.

## O que não encerra a fase

Um helper de busca, eval isolado ou renderer técnico não significa fluxo integrado. São necessários conexão das fontes ao processo durável, geração de imagem com orçamento e consentimentos, verificação das alterações durante o processamento, prévia utilizável e os gates acima. A importação assistida de cardápio continua BL03.3 posterior. BL05 integra conversa, ajuste, aprovação e publicação simuladas sem depender da Meta.

## Casos de QA planejados

Loja física de cachorro-quente, delivery e manicure com espaço próprio têm cenários
e roteiro de testes manuais em [guia de QA](../evals/manual-qa-negocios-ficticios.md).
Preparação de dados/imagens é distinta de completar o fluxo BL04/BL05.
