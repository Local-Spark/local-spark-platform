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
Prévia com este briefing fica bloqueada até BL04.2. Kit é congelado na proposta;
as referências fotográficas ainda não são enviadas a um gerador visual. Portanto
não afirmar que o fluxo completo ou a qualidade comercial estão concluídos.


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
