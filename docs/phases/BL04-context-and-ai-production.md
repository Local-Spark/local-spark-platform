# BL04 — contexto seletivo e produção visual com IA

Estado: **em implementação local**, sem aprovação comercial. Complementa a [trilha BL](BL-brand-library.md#bl04--recuperar-contexto-e-produzir-uma-peça-nova), o [SDD geral](../SDD.md) e os contratos transversais F03/F04.

## Objetivo

A partir de um pedido livre e de informações autorizadas do negócio, identificar o que o cliente pretende divulgar, selecionar somente as fontes pertinentes e produzir uma prévia privada com identidade visual e IA. A revisão e eventual publicação permanecem ações distintas. O WhatsApp real depende de homologação Meta; os testes usam entradas sintéticas e mocks.

## Entregas e gates

1. **BL04.1 — Interpretação e contexto:** interpretar intenção e formato dentro das opções efetivamente disponíveis; localizar candidatos no acervo do mesmo negócio com produtos/aliases ativos e validade no fuso do negócio. Correspondência lexical é só candidato: negação, ambiguidade ou ausência de fonte não autorizam escolher produto automaticamente. Fotografias precisam de direito válido; dados de outro tenant, item arquivado e preços vencidos não podem compor o briefing. Kit confirmado, fatos, itens e mídias devem ter versões e proveniência verificáveis. Revalidar antes de efeito externo e antes de liberar o resultado; revogação, exclusão e alteração invalidam as dependências afetadas.
2. **BL04.2 — Imagem e custo:** integrar um provedor de imagem ao caminho real da prévia, com consentimento aplicável, referências mínimas e saída privada; registrar operação, versão de modelo/briefing, fontes e uso. Uma referência de kit no máximo, quando necessária; fotos reais pertinentes do negócio são referências separadas. Se a promessa for retratar local/produto reais, não apresentar um ambiente inventado como fotografia documental. Texto/preço/CTA exigem conferência literal; resultado generativo não comprova fidelidade por si só. Falta de fonte deve gerar pergunta ou conceito identificado, não fato inventado.
3. **BL04.3 — Qualidade e economia:** avaliar post e story novos em celular com titular e materiais consentidos. Registrar rejeições, retrabalho, todas as tentativas e custo por peça aceita; avaliar separadamente legibilidade, identidade, fidelidade e texto. Ensaios fictícios e comparação entre modelos medem viabilidade técnica, mas não substituem aceite do titular nem comprovam margem.

## Fornecedores e controle de risco

A opção de imagem é um adapter por capacidade, comparado com receitas aplicáveis usando qualidade e custo por peça aceita; não prometer que todas as peças serão boas por trocar de modelo. A hipótese é R$ 99 de mensalidade e **custo total máximo pretendido de R$ 50/mês**, incluindo serviços externos, infraestrutura, retentativas e suporte. O valor não foi validado. Vídeo, animação e avatar têm gates próprios e não são automaticamente entregues pela integração de imagem.

Antes de qualquer geração paga para cliente, reservar o limite de gasto por operação e tenant de forma atômica, registrar o intento durável, executar fora da transação, liquidar uso conhecido e tratar como **resultado incerto** qualquer timeout após possível submissão. Não repetir nem trocar provedor automaticamente quando houver risco de cobrança duplicada. Validade do direito, acesso e referências deve ser verificada também após a chamada. Auditoria/telemetria não expõem segredos, imagens ou prompts privados por padrão.

Para a avaliação inicial, o usuário autorizou até **US$ 1 no total para chamadas de imagem com dados fictícios**. Esse teto é para o ensaio, não é franquia comercial e não autoriza dados de clientes nem gastos ilimitados. Testes automatizados usam mocks e não fazem chamadas pagas. O custo informado pelo provedor deve ser distinguido de estimativas e da fatura final.

## Avaliação do Jev

Jev é candidato para classificação curta, necessidade de esclarecimento e escolha entre formatos já elegíveis; não é gerador de imagem e não decide permissões, consentimento, fatos ou limite de gasto. Um corpus PT-BR sintético com gabarito e casos de ambiguidade/negação compara baseline e modelo pinado, taxa de acerto, abstenções, latência e custo; medir erros críticos separadamente. O ensaio é offline por padrão, sem dados de clientes. A chamada real exige chave local, teto explícito e execução deliberada. Um ensaio exploratório com cinco casos foi realizado; a amostra não comprova precisão e não houve decisão de adoção. Ver [eval Jev](../evals/jev-intent-ptbr-v1.md).

## O que não encerra a fase

Um helper de busca, eval isolado ou renderer técnico não significa fluxo integrado. São necessários conexão das fontes ao processo durável, geração de imagem com orçamento e consentimentos, verificação das alterações durante o processamento, prévia utilizável e os gates acima. A importação assistida de cardápio continua BL03.3 posterior. BL05 integra conversa, ajuste, aprovação e publicação simuladas sem depender da Meta.
