# Crítica de acabamento e resposta compacta — etapa 5

**Retorno posterior do titular:** a candidata tipográfica recebeu `adequate`, mas
não realizou a expectativa de interação entre mensagem e objetos. A skill v4
amplia a orientação compartilhada da geração/crítica para esse requisito, usando
os mesmos checks e contrato v2. Não altera o parecer anterior nem acrescenta
garantia algorítmica de julgamento semântico. Ver
[ajuste de direção e avaliação](motion-interacao-mensagem-2026-11-10.md).

**Prova posterior:** a recuperação semântica apontou um recorte real, mas seu
`brief_alignment` citou current-2/5/13 e a issue correspondente current-6.
O contrato compacto era válido; a validação semântica rejeitou a falta de evidência
compartilhada (`MOTION_CREATIVE_CORRECTION_UNGROUNDED`). O parecer não foi corrigido
manualmente nem tratado como aprovado. Skill v5 reforça a instrução de usar IDs
exatamente compartilhados, sem mudar a guarda. Ainda sem nova prova paga da v5.

Status: implementada e validada localmente em 10/11/2026. Sem crítica paga,
geração de assets ou render. A etapa 6 foi autorizada na solicitação seguinte;
ver [pacote externo entregue](../evals/pacote-externo-motion-2026-11-10.md).

## Alvo e evidência

Novos snapshots incluem `review_contract.version=motion-review-v2`. O mesmo alvo
chega à geração, à revisão e à correção: realização do pedido/direção, hierarquia
tipográfica, profundidade e relações entre camadas/gravação, ação com resultado,
continuidade e leitura nos intervalos amostrados. Esses aspectos usam os checks
criativos e temporais existentes, sem criar outra nota de qualidade.

Fatos, kit, legibilidade e integridade são obrigatórios, mas não demonstram
acabamento. Variação de pixels, número de efeitos e intensidade não são métricas
de qualidade. Desenho não implica aparência infantil; o crítico deve localizar
a diferença observável em relação à direção, sem impor neon, órbitas, ícones ou
identidade das referências. Aprovação continua sendo humana.

As imagens de acabamento seguem em `finish_reference_only`, fora dos assets e
do índice de evidências. `current`, `previous` e `source` mantêm seus papéis.
Amostras não comprovam áudio, sincronismo ou fluidez integral. Falta de evidência
gera incerteza, não autorização para refazer. Plano e direção continuam intenções.

Um problema acionável deve apontar cena/elemento, quadro atual e ajuste viável
com os recursos autorizados. Em novos contratos, uma falha criativa que pede
correção precisa compartilhar evidência atual com o problema correspondente.
Se exigir nova direção, material, fato ou capacidade, a regra orienta registrar
a dependência como não acionável; não autoriza uma nova direção automaticamente.
A verificação estrutural não consegue provar a qualidade da observação textual
nem a viabilidade artística de cada sugestão: essa parte continua sujeita à revisão.

## Entrada e saída

Somente na crítica com o contrato novo, `input_projection` identifica
`review-composition-without-code-v1`: `current_composition` e `previous_composition`
omitem HTML e `scene_init`. Mantêm direção, plano, concept, descrição de fontes e
plano de áudio como intenção, além dos quadros/diagnósticos já fornecidos.
Geração e correção continuam recebendo o código completo quando disponível.
Contexto autorizado, skill, kit e repertório permanecem no corpo contado; esta
projeção não altera snapshots nem pretende remover toda redundância da entrada.

`review_evidence_index` relaciona IDs como `current-0`, `previous-2` e `source-1`
a versão, tempo e SHA-256 dos quadros realmente enviados. A resposta usa esses
IDs em `evidence`/`preference_evidence`; cada problema usa `evidence_id` de current.
Não é preciso repetir hashes de 64 caracteres em cada check.

O schema `CompactMotionReview` limita:

- Sete critérios gerais, até quatro checks criativos e quatro temporais. Os
  contratos existentes exigem os quatro de cada grupo quando aplicáveis.
- Observações/motivo de preferência em até 240 caracteres; base do pedido em 160.
- Até seis problemas distintos, com correção em até 320 caracteres, e quatro
  limitações em até 240 caracteres cada. Se houver mais problemas, o parecer
  deve declarar seu escopo limitado; o limite não autoriza falsa adequação.
- Evidências apenas pelos IDs enviados, sem repetição dentro do mesmo campo.
  Sequências temporais completas e comparação A/B continuam obrigatórias.

O serviço expande os IDs para o `MotionReview` durável já existente e então
aplica as mesmas validações de evidência, checks e decisão. Índice desconhecido,
referência externa como prova, problema ligado a source/previous e prosa acima
dos limites são rejeitados. A resposta bruta compacta e o parecer normalizado
seguem os registros privados existentes; não há tabela ou operação adicional.

Snapshots sem `review_contract` conservam o formato anterior de resposta.
Recaptura não acrescenta a política retroativamente. O fixture local continua
produzindo o parecer normalizado e não demonstra qualidade criativa real.

## Tamanho, orçamento e falhas

A crítica anterior consumiu 39.445 tokens de entrada e atingiu 8.000 na saída
sem parecer válido. A alteração reduz repetição estrutural e limita a prosa;
não atribui esse truncamento ao modelo nem presume sua causa exata.

Na fixture temporal sintética, o mesmo parecer ocupa 17.272 bytes JSON normalizado
e 4.120 bytes no formato compacto: redução de 76,1% em bytes. Não é contagem de
tokens, estimativa de custo ou medição de uma resposta criativa real. Remover o
código da entrada poupa seus bytes, mas acrescentar contrato/índice tem custo;
a contagem real continua sendo aplicada ao corpo final, incluindo todas as imagens.

O teto da crítica continua `min(limite_configurado, 8000)`, com o esforço de
raciocínio existente. Não aumentamos orçamento ou teto, nem mudamos provedor.
Ainda pode ocorrer truncamento; a nova estrutura não garante que toda crítica
caiba no limite. Isso só pode ser medido numa execução futura autorizada.

`incomplete/max_output_tokens` continua como `MOTION_AI_OUTPUT_LIMIT`: conserva
resposta/uso/estimativa privados, sem interpretar JSON parcial, retry automático,
correção, aprovação ou aumento de limite. JSON quebrado também não vira parecer.
Ledger, reservas, Temporal, versões anteriores e parada por falha permanecem.

## Verificação

214 testes direcionados passaram: transporte simulado, captura/recaptura,
serialização/contagem, expansão exata de evidências, checks criativos/temporais,
rejeição de referência indevida, correção condicional e parada por truncamento.
Cobertura dirigida de `motion_review` e `motion_review_wire`: 100% de linhas/ramos.
Ruff, tipos dos quatro módulos alterados nesta etapa e diff aprovados.
Sem CI global, testes SQL, APIs reais, geração de assets ou renderização.

```sh
.venv/bin/pytest -q app/tests/unit/test_motion_review_wire.py app/tests/unit/test_motion_context_requests.py app/tests/unit/test_motion_ai.py app/tests/unit/test_motion_creative.py app/tests/unit/test_motion_temporal.py app/tests/unit/test_motion_orchestrator.py app/tests/unit/test_motion_effects.py
```

A etapa 6 exportará pelo montador do produto o pacote completo para o teste do
titular. Nenhum pacote externo foi gerado ou enviado nesta etapa.
