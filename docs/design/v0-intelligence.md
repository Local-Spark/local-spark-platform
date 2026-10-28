# Inteligência editorial — interpretação local e pesquisa futura

Reconciliado em **28/10/2026**. O estudo v0 original e suas estimativas de preço/
escala estão preservados como evidência datada. O [SDD](../SDD.md), a
[BL04](../phases/BL04-context-and-ai-production.md) e as [decisões](../DECISIONS.md)
prevalecem; este desenho não implementa conectores ou pesquisa apenas por citá-los.

## O que existe

Fatos/preferências do negócio, kit e acervo são versionados e privados. O
retrieval experimental recupera candidatos pertinentes no mesmo negócio. O
worker pode usar Jev/TypeSafe em desenvolvimento/teste, desligado por padrão,
sob aceite único do serviço e budget diário por tenant. Não existe autorização
TypeSafe separada na web. Saídas estruturadas ajudam a interpretar intenção,
sem serem autoridade para acesso, preço, direitos ou publicação.

Antes da chamada são revalidados origem/acesso/snapshot e reservada a operação.
Orçamento recusado antes da submissão possui retomada limitada/atômica; resposta
incerta não é reenviada. O esclarecimento é simulado e genérico, sem conversa
completa de memória. A comparação PT-BR sintética encontrou erros/saídas
incompletas e não homologa diálogo real.

O nome ativo e versionado do item pode fundamentar roteiro, sem transformar
preço, promoção ou alegação no nome em fato. Não é preciso criar registro
artificial de contexto apenas para repetir esse nome. Mídia recebida é preservada,
sem virar automaticamente catálogo, fato confirmado, índice pesquisável ou skill.

## Contratos permanentes

- Banco/Python decidem identidade, membership, plano, contrato, orçamento,
  validade factual e transições. Um score probabilístico não autoriza efeito.
- Texto do WhatsApp, web e fontes externas é entrada não confiável, sem permissão
  para executar código/tools ou alterar regras de sistema.
- Briefing mínimo usa fontes/versões/hashes pertinentes. Não enviar todo o
  histórico ou galeria. Resumo não converte hipótese em fato ou remove restrição.
- Modelos/roteadores precisam de benchmark PT-BR, casos negativos/ambíguos,
  fallback seguro e custo total. Trocar o modelo sozinho não resolve criatividade,
  conversa, qualidade visual e validação factual.
- Armazenar conversa não treina modelo automaticamente. Economia de tokens é
  hipótese a medir com retrieval/compactação/cache e qualidade comparável.

## Pesquisa e recomendação futuras

Pesquisa por nicho/região, concorrentes, temas/horários, referências permitidas e
métricas próprias continuam futuras. O desenho original avaliou Google Places,
busca/extração e APIs de redes como candidatos; termos de armazenamento,
atribuição, finalidade, compartilhamento e uso em inferência precisam ser
verificados para cada fonte e escopo antes de integrar. Acesso público não
concede direito de copiar mídia nem fornece insights privados de concorrentes.

Cada evidência futura deve informar origem/URL, instante, escopo/permissão,
validade/completude e limitação. Inferência editorial é hipótese, sem inventar
causalidade entre formato e vendas. Aprendizado entre negócios exige política
própria e proteção dos dados, sem expor conversas ou desempenho individual.
Agendas de proatividade e relatórios ainda não estão implementados.
Ver [cadência e evidência](editorial-planning-and-evidence.md).

## Custos, expansão e aceite

Amostra shadow é controlada, com dados autorizados e teto explícito; não duplicar
inferências de toda a base. Medir ganho contra baseline determinístico: intenção,
negação/ambiguidade, fonte correta, pedido de esclarecimento, latência, uso e
custo por decisão/peça aceita. Valores e releases do estudo original são datados,
sem alegação de modelo mais recente ou tarifa atual.

A meta de 200 mil clientes exige atualização incremental, isolamento, admissão,
quotas, orçamento, medição de contenção e carga F08. Tabelas de estimativas e
workflows conceituais anteriores não são runtime existente. A prioridade é fechar
BL04.2/BL04.3 e BL05; pesquisa ampla e otimizações vêm depois da primeira receita
personalizada com qualidade/custo aprovados.

Versão anterior integral: [snapshot de 28/10/2026](../history/2026-10-28-pre-documentation-reconciliation/design/v0-intelligence.md).
