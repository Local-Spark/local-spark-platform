# Eval exploratório — Jev e intenções de conteúdo PT-BR

Data: 27/10/2026. Estado: ensaio real exploratório em 30 mensagens fictícias de desenvolvimento; Jev também está integrado de forma opcional ao worker local, desligado por padrão e sem aprovação comercial. O ensaio não envia mensagens a clientes, não consulta banco e não publica. Complementa [inteligência editorial](../design/v0-intelligence.md).

## Objetivo e dados

Comparar o classificador real de `editorial_conversation.classify()` com um
candidato Jev para reconhecer `price`, `availability`, `content_request`,
`question` e `other` em mensagens de pequenos negócios. O baseline atual só
reconhece preço e disponibilidade em padrões limitados; seu resultado `unknown`
é contabilizado como abstenção, não como classificação de `other`.

O [conjunto v1](jev-intent-ptbr-v1.json) tem **50 mensagens fictícias** de cinco
classes e diversos segmentos: 40 para desenvolvimento, 10 para holdout. Casos
são intercalados por classe para que os cinco primeiros não sejam todos iguais.
Ele é pequeno e contém amostragem artificial: não prova desempenho na população,
segurança ou qualidade em áudio transcrito real. O SDD exige pelo menos mil casos
revisados PT-BR, calibragem, limites de erro e staging antes da ativação.

A ordenação de intenção para o eval é explícita: pedido de criação prevalece
sobre um preço/horário mencionado na mesma frase; preço e disponibilidade são
informações sem pedido explícito de criação; `other` cobre cumprimentos ou frases
fora das categorias. Esses rótulos são hipóteses para testar, não autorização de
usar respostas como comandos reais. Confirmação, pausa, publicação, pagamento e
permissões continuam regras determinísticas do domínio.

O eval mede apenas **classificação da intenção**. Não avalia extração de valores,
datas, falta de contexto, seleção de formato, geração de texto/imagem, fidelidade
de mídia, qualidade de conversa nem taxas de conversão. Essas tarefas exigem
conjuntos, critérios e baselines próprios; formato deve ser escolhido somente
entre opções já elegíveis por plano, material e autorização.

## Execução sem rede nem chave

Na pasta do backend:

```bash
uv run python scripts/evaluate_jev_intent.py
```

O padrão roda somente o baseline, imprime JSON com IDs/rótulos e métricas, sem
mensagens de entrada nem chaves. `jev.status=not_run` sinaliza que Jev não foi
comparado. Pode separar amostras por `--split development` ou `--split holdout`.
O arquivo de casos tem hash fixado no runner: alteração inesperada falha antes
que dados sejam enviados a um provedor. Atualizar fixture e hash conscientemente
é parte de uma futura versão controlada.

Após corrigir a interpretação de negação, a execução offline de 27/10/2026
respondeu 13 dos 50 casos e acertou os 13; absteve-se nos outros 37. O caso
negado agora gera abstenção. São apenas dados sintéticos e a amostra é pequena;
esse resultado não comprova desempenho em produção. O baseline cobre apenas
parte das classes por construção e deve ser reavaliado a cada alteração.

## Primeiro ensaio real — 27/10/2026

Com a chave local configurada, foram testados os cinco primeiros casos da
partição de desenvolvimento, um de cada classe, com `jev-1.14.0` e limiar
experimental 0,5. Resultado: **5 acertos em 5 respostas**, sem abstenções.
No mesmo subconjunto o baseline respondeu corretamente a 2 e se absteve em 3.
Amostra selecionada e pequena: números descritivos, não estimativa de precisão
para clientes e não comparação de robustez em negações, transcrições ou erros.

Latência com rede: mediana **179,676 ms** e p95 amostral **304,439 ms**.
O provedor reportou **2.357 tokens de entrada** para as cinco chamadas; pelo
preço versionado do ensaio, custo estimado **US$ 0,000098994** para todas elas.
Não inclui impostos, infraestrutura, fallback ou outras etapas, e não equivale à
fatura. Não houve chamadas de cobrança incerta. O teto de US$ 0,02 e a reserva
conservadora de US$ 0,01344 são estimativas locais, não limite financeiro imposto
pelo provedor. O resultado não escolhe modelo nem autoriza produção; faltam novo
holdout cego, casos adversariais e avaliação da qualidade da decisão final.

## Quando a chave e um orçamento estiverem configurados

O runner lê `TYPESAFE_API_KEY` somente do ambiente; não grava `.env`, não imprime
chave nem executa chamada paga por padrão. O usuário pode configurar a variável
privadamente no `.env` local; nunca colocar a chave em comandos registrados,
Git, logs ou relatórios. Para uma avaliação explicitamente autorizada:

```bash
uv run --env-file .env python scripts/evaluate_jev_intent.py --live --split development --max-cases 5 --max-usd 0.02
```

O exemplo envia **cinco casos fictícios** ao endpoint oficial, sem SDK novo, e
usa `jev-1.14.0` pinado. `--live`, chave e orçamento positivo são obrigatórios;
o número de requisições é limitado e não há retries automáticos. O runner reserva
conservadoramente 64.000 tokens de entrada por requisição × US$ 0,042/1M,
portanto US$ 0,01344 para cinco casos. É uma estimativa pelo preço e limite
publicados em 27/10/2026, não limite financeiro imposto pelo fornecedor: conferir
preço/limites antes de executar e configurar também limites da conta. Impostos,
infraestrutura e chamadas de fallback não estão incluídos.

Timeout/erro podem ter sido cobrados: são marcados como custo incerto e reservam
o teto da chamada, sem repetir. Uso reportado acima do contexto documentado
interrompe novas chamadas; o relatório mostra o custo observado e casos não
executados. O custo representa somente os tokens de entrada medidos e o teto das
chamadas incertas. A resposta contém a versão efetiva, latência e estado do teste;
o conteúdo bruto de erro/resposta do fornecedor não é impresso.

A confiança de `Choice` serve para testar abstenção; o limiar inicial 0,5 é
**experimental e não calibrado**. Treinar o limiar somente em desenvolvimento e
avaliá-lo separadamente em um novo holdout cego (o holdout atual foi contaminado). A tabela de calibração agrupa a probabilidade
da opção escolhida e compara com os acertos observados: não confundir
`confidence` do fornecedor com probabilidade de acerto do nosso negócio.

## Ensaio ampliado com autorização de US$ 0,10 — 27/10/2026

Com 30 casos fictícios da partição de desenvolvimento, `jev-1.14.0` respondeu
os 30 e acertou **29/30**, com limiar experimental 0,5 e sem abstenções. O baseline
respondeu 11 corretamente e se absteve em 19; não houve erros nas respostas do
baseline. O Jev classificou como disponibilidade uma mensagem de fechamento
negado (`other-04`), cujo gabarito era `other`. A regra determinística atual do
fluxo integrado se abstém diante de negação, mas este ensaio isolado não mede a
eficácia desse fluxo de ponta a ponta. Os casos são sintéticos e de desenvolvimento;
não constituem holdout independente nem validam seleção de produto, formato ou
conversa com clientes.

O provedor reportou **14.135 tokens de entrada**, custo estimado de
**US$ 0,000593670**, sem chamadas de cobrança incerta; a reserva conservadora foi
**US$ 0,08064**, dentro do teto autorizado de US$ 0,10. Mediana **202,423 ms**,
p95 amostral **294,699 ms**. São estimativas sem impostos, infraestrutura ou
refações e não equivalem à fatura ou ao custo mensal por cliente. É preciso corpus
representativo e holdout novo antes de habilitar clientes reais.

No mesmo teto, o adapter de runtime foi chamado diretamente em [sete cenários
fictícios registrados](jev-briefing-smoke-v1.json) de intenção, seleção e formato: seis corresponderam ao gabarito.
O pedido “quero divulgar” foi classificado como `other` e encaminhado para
esclarecimento, em vez de ser reconhecido como solicitação de conteúdo. Foto,
story, vídeo indisponível, preço, pergunta e saudação tiveram os resultados
esperados neste conjunto mínimo. Esses testes não incluem o worker, o banco ou a
entrega WhatsApp e não são uma avaliação representativa.

Nessas sete chamadas, o provedor reportou **4.767 tokens de entrada**, com custo
estimado de **US$ 0,000200214** e nenhuma chamada incerta. Somando os dois ensaios
desta autorização: **US$ 0,000793884** estimados; as reservas máximas somadas
foram **US$ 0,099456**, dentro do teto de US$ 0,10. Melhorar o reconhecimento de
intenções implícitas e repetir a avaliação em conjunto novo antes de uso comercial.

## Métricas e limites de decisão

O relatório traz cobertura, abstenções e razões, acerto no total, acerto entre
respostas, erros, precisão/recall por intenção, p50/p95, tokens e custo estimado.
Abstenção aparece no denominador do acerto total e reduz recall; não é tratada
como resposta errada no acerto apenas entre respostas. Comparar os mesmos casos
entre candidatos. Tempo do baseline é execução local; latência Jev inclui rede.

A seleção final deve comparar também um modelo generativo pequeno ou outro
classificador apropriado, todos no mesmo corpus, com regras de confiança,
retentativas e custo de fallback incluídos. Uma amostra de cinco/50 casos não
valida o desempenho de Jev nem a meta de custo mensal de R$ 50. Não habilitar
cliente real até cumprir corpus representativo, avaliação independente,
consentimento de provedor e políticas operacionais de falhas.

Fontes: [TypeSafe — introdução](https://docs.typesafe.ai/introduction),
[modelos e preços](https://docs.typesafe.ai/models),
[confidence](https://docs.typesafe.ai/confidence) e
[Choice](https://docs.typesafe.ai/primitives/choice).

O caso `other-10` do holdout foi examinado e orientou a correção do baseline;
portanto, esse holdout está contaminado para o baseline e não estima desempenho
cego. Antes de qualquer conclusão, é necessário um holdout novo, não inspecionado
e revisado de forma independente.
