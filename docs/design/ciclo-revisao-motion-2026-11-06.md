# Ciclo de revisão de motion — desenho de ensaio

Estado: **protótipo privado implementado**, 06/11/2026. A frente ativa é experimentar Reels com
Python e APIs configuradas: gerar → renderizar → inspecionar → corrigir →
renderizar novamente. O [plano de ensaio](../evals/plano-ciclo-revisao-motion-2026-11-06.md)
define a primeira comparação. O protótipo não demonstra comparação real ou ganho.
O titular autorizou a rodada delimitada no
plano: até US$ 6,75 para Intensa/Dog/Luma e até 15 chamadas.

O executor histórico recebe uma composição em uma chamada, renderiza e apresenta
o resultado. O novo CLI adiciona ao ensaio privado o ciclo de crítica descrito
abaixo, partindo de composições históricas. O titular avalia
o MP4 final; a dispensa anterior de aprovar cards/frames intermediários não
impede inspeção automática. O clipe pessoal já entregue continua aguardando
avaliação, sem bloquear esta frente. Fontes e técnicas autorizadas da análise
de skills podem orientar o trabalho; não se prevê servidor Claude Code nem
agentes hospedados. A adoção depende de direitos e evidência comparativa.

## Contrato da revisão v1

1. Congelar cenário, intenção, fatos e fontes autorizados, kit, skill e versão,
   composição inicial, assets, renderer e configurações. Reutilizar como A um
   Reel histórico íntegro e sua composição verificável; o braço de revisão
   começa exatamente nessa composição e nesse render inicial. Registros privados
   e hashes identificam cada entrada e saída.
2. Conferir o MP4: decodificação, duração, resolução e áudio, além de quadros
   amostrados a cada 500 ms e no quadro final estimado, com tempos solicitados.
   Sempre registrar seleção e intervalos efetivamente observados; amostras não
   comprovam integralmente movimento, legibilidade ou sincronismo.
3. Alimentar o crítico com as evidências visuais extraídas do arquivo, briefing,
   kit e fatos autorizados. Identificar o que recebeu. Nesta rodada o áudio será
   verificado tecnicamente e a mesma mixagem/trilha será congelada; escuta humana
   fica explícita. Não afirmar que o crítico ouviu o áudio. Imagens isoladas não
   equivalem a assistir ao MP4 completo.
4. Registrar crítica estruturada por critério, estado `pass`, `fail` ou
   `uncertain`, evidência e tempo quando aplicável, gravidade e proposta
   concreta. Ausência de evidência não é aprovação. Fato desconhecido não se
   torna fato confirmado. Uma correção exige falha concreta, relevante,
   sustentada por evidência e corrigível. Se ela não existir, se a crítica
   for incerta ou expressar apenas preferência estética, parar e explicitar a razão.
5. Permitir até **duas correções** e renderizar cada versão separadamente, com
   nova crítica por versão, inclusive após a última correção. Vincular cada
   correção aos achados e preservar a resposta original, código executado,
   artefatos e intervenções. A segunda correção exige evidência de que a primeira
   foi preferida pelo crítico com evidência e de que ainda há falha relevante e
   corrigível. Essa preferência do modelo é provisória, não avaliação humana.
   Sem evidência de melhora, parar; limite e orçamento são tetos, não metas. Não alterar
   significado da fala, preços, condições,
   identidade ou direitos por suposição. Falha, orçamento esgotado ou resultado
   incerto interrompem o ciclo; não reenviar efeito incerto automaticamente.
6. Comparar versões A e B, com seus limites e custos, e manter a melhor versão
   anterior disponível. Uma nota automática não decide que a última é melhor:
   a seleção e avaliação criativa finais são humanas. Preservar todas as versões,
   inclusive rejeitadas, e distinguir decisão sugerida e decisão do titular.

### Critérios de avaliação `motion-review-v1`

Aplicar por versão; itens não verificáveis permanecem `uncertain`, inclusive
áudio na crítica por modelo. A rubrica executável está versionada em
`scripts/evals/fixtures/motion-review-rubric-v1.json`.

| Critério | Evidência e julgamento |
| --- | --- |
| Fidelidade factual e identidade | Pedido/fatos/kit versus textos e imagens efetivamente observados; preço, condições, logo e produto não podem ser inventados ou alterados. |
| Legibilidade e composição | Texto e contraste em quadros identificados e contexto de exibição no celular; registrar lacunas temporais. |
| Narrativa e movimento | Sequência, ritmo, transições e foco com evidência temporal observável; explicitar limites da amostragem. |
| Fala, música e mix | Nesta rodada, preservar a mixagem e verificar integridade técnica; sentido, balanço e qualidade perceptiva dependem de escuta humana. |
| Integridade técnica | Resultado decodificável, duração, dimensões, mídia e áudio esperados; sucesso técnico não é aceite criativo. |

Fidelidade factual, legibilidade, narrativa e áudio não se reduzem a uma nota
única. A comparação mede preferência humana, falhas por critério, refações,
tempo e custo por versão, sem inferir ganho geral de uma amostra pequena.
Ocorrências recorrentes podem orientar melhora do briefing inicial em prova
futura; não alegar comparação desse braço sem executá-la.

## Limites e transferência posterior

O ensaio usa materiais fictícios e licenciados, sem banco, WhatsApp ou execução
de cliente. O sandbox atual de navegador não comprova isolamento de sistema
operacional. Antes de conteúdo real, qualificar isolamento de código e mídia,
rede, arquivos, segredos e recursos. A arquitetura de produção permanece aberta:
o compilador declarativo atual só executa código próprio, mas a rodada 1c perdeu
qualidade; o ensaio aberto usa HTML/JS gerado. Não presumir que qualquer um já
resolva simultaneamente segurança e fidelidade criativa.

Depois da comparação real e revisão humana, avaliar transferência para serviços
e activities Temporal com operações duráveis, RLS, orçamento, audit/outbox,
recuperação e revisão/download. WhatsApp integrado e publicação no Instagram
são etapas posteriores; a aprovação da peça não autoriza postagem.
