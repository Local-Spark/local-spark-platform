# Retomada da prova temporal — 09/11/2026

Estado: fluxo técnico concluído; avaliação humana recebida — melhora parcial, ainda muito longe do alvo.
Sem repetição automática ou correção.

## Motivo e alteração limitada

A primeira tentativa terminou `incomplete/max_output_tokens`: 16.000 tokens de
saída, dos quais 10.876 de raciocínio. O JSON ficou truncado, sem composição
válida, render ou crítica. O registro original permanece falho e imutável.
Uso estimado recuperado: US$ 0,183570; reserva retida: US$ 0,85.

A proposta mantém fonte, kit, briefing, modelo `gpt-6.1-sol` e reasoning high,
aumentando **somente o teto de geração para 32.000 tokens**. A crítica mantém
8.000. São **duas chamadas e duas contagens**, geração e crítica, sem correção
nesta retomada. Se a crítica reprovar ou faltar evidência, preservar o vídeo e
apresentar a limitação; não iniciar outra chamada automaticamente.

Não se remenda o JSON truncado nem se escreve manualmente o vídeo como substituto
para uma geração pelo produto. O baseline A continua preservado. A nova B será
comparada pelo titular, mesmo se a crítica impedir aprovação no produto.

## Reserva autorizada dentro do teto original

Até **US$ 1,70**, duas reservas de US$ 0,85. Somadas aos US$ 0,85 da tentativa
interrompida: até **US$ 2,55 nesta prova**, abaixo dos US$ 3,40 originalmente
autorizados. Global dev: US$ 5,10 já comprometidos + US$ 1,70 = **US$ 6,80**,
abaixo do teto anterior de US$ 7,65. Nenhuma reserva antiga será liberada.

A aprovação é necessária pela **retomada após falha e mudança de limite de
saída**, não por aumento do orçamento total. O novo pedido limita correções a
zero e orçamento a US$ 1,70. A guarda conta entrada completa e impede chamada
que ultrapasse sua reserva. Falha incerta não autoriza retry.

Envio permanece: briefing/kit fictícios, seis quadros da fonte, até 20 da peça,
código/plano temporal e calibrações textuais. Sem MP4/áudio ou quadros externos.

## Preparo concluído

- API autenticada retornou 202 para pedido fictício novo
  `97e362cd-d828-54ae-8ee8-056d664d1374`, no mesmo dev autorizado, sem migração/limpeza.
- Worker reconstruído sem rede e 14 arquivos/importações conferidos; renderer,
  Temporal local e storage existentes preservados. Worker da tentativa anterior
  confirmado encerrado; o novo inicia somente com a autorização registrada.
- Adapter distingue `MOTION_AI_OUTPUT_LIMIT` e transporta uso/estimativa conhecidos
  ao registro privado existente, preservando a reserva pendente. Não há nova
  tentativa automática nem alteração do resultado histórico.
- 80 testes direcionados passaram em 6,05 s; Ruff/mypy aprovados. Sem CI completo.

[Plano exato](../../.local/evals/reel-integrated-motion-resume-20261109/paid-plan.json)
· [preparo](../../.local/evals/reel-integrated-motion-resume-20261109/preparation.json)
· [worker](../../.local/evals/reel-integrated-motion-resume-20261109/worker-ready.json).

Conclusão esperada: nova versão real e crítica, custo/tempo e comparação visual
com A. Não se garante que o modelo julgue corretamente ou que o aumento do teto
seja suficiente; qualidade criativa e aceite continuam dependendo do resultado.

Autorização: entrevista `call_db971bece607432cb06b9a9401b769a5`, resposta
“Autorizar a retomada nesse limite”. Aprovação vinculada ao hash do plano exato;
até duas chamadas/contagens, US$ 1,70 e zero correções.

## Resultado da retomada autorizada

Pedido `97e362cd-d828-54ae-8ee8-056d664d1374`: **completed**, `simulated=false`.
Peça `f3430dea-a2d9-5995-95a4-f1317bd06b92`, uma versão, duas chamadas e duas
contagens; nenhuma correção. Worker próprio confirmado encerrado, sem alterar
os serviços existentes. Fonte/kit/briefing/modelo e baseline A preservados.

[Comparativo A/B com som](../../.local/evals/reel-integrated-motion-resume-20261109/report.html)
· [vídeo B](../../.local/evals/reel-integrated-motion-resume-20261109/selected.mp4)
· [verificação](../../.local/evals/reel-integrated-motion-resume-20261109/verification.json)
· [manifesto temporal](../../.local/evals/reel-integrated-motion-resume-20261109/v0-sampling.json).

| Efeito | Duração | Entrada / saída (tokens) | Uso estimado (US$) |
| --- | ---: | ---: | ---: |
| Geração | 290,217 s | 9.433 / 18.102 | 0,204603 |
| Render | 74,005 s | — | — |
| Crítica | 108,770 s | 38.089 / 7.924 | 0,174463 |

Workflow: **574,11 s (9 min 34 s)**. Uso estimado desta retomada: **US$ 0,379066**;
reservas: US$ 1,70. Incluindo a geração truncada anterior: **US$ 0,562636** estimado
e **US$ 2,55** reservado, dentro dos US$ 3,40 autorizados originalmente. Global
retido dev: US$ 6,80. Estimativas não são fatura ou conciliação: reservas continuam
retidas. Limites calculados antes das chamadas: US$ 0,343583 e US$ 0,175223,
ambos inferiores às reservas individuais de US$ 0,85.

Geração completa com plano temporal e código usando `MotionV1`; hash da biblioteca
conferido no efeito de render contra o worker. MP4: 11,2 s, 720×1280, H.264/30 fps
e AAC; 1.288.976 bytes. Plano de áudio idêntico ao autorizado, sem certificação
humana de escuta. API autenticada da peça/link e download real retornaram 200.
SHA-256 selecionado e baixado:
`ae462cb07cb8223ba1e2197f86c4e7150e074a85f651145fb69fd838c9452881`.

A crítica retornou `adequate`: quatro checks criativos `met`, quatro temporais
`pass`, sem issues. O parecer se limita aos quadros enviados. A inspeção local
de quadros A/B mostra mudanças de texto, enquadramento e organização final,
mantendo linguagem editorial e o kit do negócio; isso não demonstra, sozinho,
ganho de fluidez ou proximidade às referências externas.

## Limitação revelada pela prova

O plano continha **40 eventos**, mas só três receberam janelas próximas: entrada
de “Dê”, entrada de um ponto gráfico e permanência do CTA. Os outros **37**
ficaram explicitamente omitidos. As principais transições entre composições
aparecem apenas em quadros de contexto; não receberam sequências próximas
completas. O próprio crítico registrou esse limite. A seleção distribuída por
índice preservou o teto de imagens, mas não priorizou os movimentos mais relevantes.

Portanto, o resultado prova o transporte/validação das evidências e o caminho real
até o download, **não a eficácia do crítico para o acabamento desejado**. Calibração
por referências continua textual, sem comparação visual automatizada com vídeos
externos. A/B compara nova geração; não houve ciclo B→correção→C nesta retomada.

Outra condição medida: a geração usou 18.102 tokens de saída, acima dos 16.000 do
perfil anterior. A crítica ficou perto do teto de 8.000 (7.924). Esta prova usou
override explícito de 32.000 na geração; defaults/exemplos gerais de 16.000 não
foram alterados silenciosamente. O perfil qualificado precisa ser considerado
antes de uma próxima ativação, sempre com orçamento de entrada/saída validado.

**Avaliação humana recebida:** “melhorou mas ainda está muito longe”. O titular
apontou vídeo reposicionado, textos e poucas formas; faltam componentes figurativos,
imagens e ícones relacionados à mensagem, como nas referências. Quer investigar
o limite de qualidade, não encerrar no patamar atual. A hipótese de atender um
pequeno cliente não é aprovação comercial. Sem confirmação específica de áudio,
enquadramento ou ausência de regressões. Feedback literal preservado no relatório
local e em `human-feedback.json`, separado do parecer automático imutável.

O alvo criativo não foi aceito. Diagnóstico e próximo recorte proposto estão no
[plano de evolução](../design/evolucao-qualidade-motion-referencias-2026-11-09.md#diagnóstico-após-avaliação-humana--composição-visual-insuficiente).
Sem novo render, rodada paga, alteração de runtime, publicação ou expansão de formato.
