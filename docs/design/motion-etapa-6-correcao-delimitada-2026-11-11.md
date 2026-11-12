# Etapa 6 — correção delimitada sem regressão

Data: 11/11/2026. Implementação técnica local, sem produção ou aceite visual.

## Estado de partida e escopo

As etapas 1–5 estavam no índice do Git; não havia alterações fora do índice.
O último commit continua `4adb596`: nenhuma mudança posterior em commit foi
identificada. As alterações anteriores foram preservadas, sem commit ou operação
de staging nesta etapa. O fluxo existente já limitava tentativas e orçamento,
preservava versões e comparava críticas, mas aceitava reescrita global de código
e plano sem comparação determinística fora da correção.

Novas capturas do montador real incluem `motion-correction-v1`; snapshots antigos
mantêm seu contrato. Não há novo serviço de infraestrutura, tabela, runner ou
dependência. Temporal, API, custos, auditoria e vínculos de materiais permanecem
nos mecanismos existentes.

## Decisões implementadas

- A crítica localiza cada problema major/blocking acionável por cena, elementos,
  intervalo absoluto e margens explícitas de entrada/saída. A evidência enviada
  precisa estar no intervalo central, dentro da cena; margens ficam dentro da
  gravação e têm teto de 1000 ms por lado. Não existe margem implícita. Uma
  correção que cobre toda a peça é recusada por não deixar região protegida.
- O primeiro problema priorizado define a tentativa. Os demais ficam declarados
  como adiados. O escopo registra resultado esperado, evidência e hash da
  composição de origem; chega ao payload real e à operação de correção. O teto
  existente de tentativas/reservas continua valendo; nada executado nesta etapa
  constitui autorização ou reaproveitamento de orçamento para uma rodada real.
- Esta fatia corrige implementação sem replanejar: todos os campos da composição
  fora de HTML/JS são imutáveis, incluindo plano, IDs, textos planejados, direção,
  conceito, materiais e áudio. Uma alteração desses campos é rejeitada antes do
  render. Os mesmos assets e a trilha original/complementar previamente vinculada
  são usados pelo render; nenhum material novo é resolvido na correção.
- O executor registra SHA-256 dos JPEGs de todos os quadros capturados a 30 fps
  antes de H.264. O ambiente é vinculado à imagem fixada do executor, navegador,
  runtime, arquitetura e código do runner. Perfil e duração devem coincidir.
  Até 1800 hashes cabem em cabeçalho limitado a 256 KiB, apenas neste modo;
  o protocolo histórico conserva seu limite. Storyboard não coleta esse vetor.
- A comparação exige igualdade exata fora da janela semiaberta com margens,
  incluindo os quadros imediatamente vizinhos. Não há tolerância perceptual
  implícita. Vetor incompleto, ambiente diferente, regressão ou ausência de
  alteração visual recusam a candidata. Os hashes integrais ficam persistidos;
  só seu resumo chega ao modelo, sem acrescentar milhares de tokens ao contexto.
- A verificação usa operação UUID derivada e o tipo de efeito existente `review`,
  identificado como `local_correction_guard`, com reserva zero. O recibo registra
  resultado e motivo; alterações de estado usam auditoria existente. Nenhuma
  chamada de modelo ocorre nessa verificação. A candidata reprovada não recebe
  a crítica paga seguinte e não é selecionada. Os artefatos anteriores permanecem;
  quando nenhuma versão passou na revisão obrigatória, o pedido falha sem promover
  a versão inicial inadequada a aprovada.

## Evidência local

- Fixture determinística de 30 imagens sintéticas: título cortado entre 200 e
  400 ms, margens de 33 ms, janela efetiva `[167,433)`. A correção altera seis
  quadros; os 23 quadros protegidos permanecem idênticos. Uma alteração injetada
  em cada posição protegida é rejeitada, inclusive em 166,667 e 433,333 ms.
- Testes integram montador real, schema compacto da crítica, payload de correção,
  admissão do plano, loop do orquestrador e protocolo do adapter. O teste Node
  exercita o runner real com IO/navegador substituídos por fronteiras sintéticas
  e verifica coleta de todos os quadros. Não é execução de Chromium em contêiner.
- São verificados também mudança de ambiente, falta de hashes, identidade da
  operação de render, preservação histórica e cabeçalho máximo de 60 segundos.
  Passaram 253 testes Python dirigidos, 73 Node, Ruff e Mypy em nove módulos;
  `git diff --check` sem problemas. Os comandos principais foram:

```sh
.venv/bin/pytest -q app/tests/unit/test_motion_corrections.py app/tests/unit/test_motion_orchestrator.py app/tests/unit/test_motion_review_wire.py app/tests/unit/test_motion_context_requests.py app/tests/unit/test_motion_html_renderer.py app/tests/unit/test_motion_audio.py
node --test app/tests/node/motion_html_renderer.test.cjs
```

## Limitações e pendências

Igualdade dos JPEGs antes da codificação não garante igualdade de todos os pixels
do MP4 final: H.264 usa dependências entre quadros. A crítica continua vendo
amostras decodificadas da peça, não o vetor inteiro. Comparação final, escuta e
aceite humano permanecem pendentes. Não há prova de qualidade visual nesta etapa.

IDs e elementos do plano ficam protegidos, mas não se promete isolamento de
elementos no código arbitrário dentro do intervalo permitido. A verificação
temporal detecta efeitos visíveis fora dele. Mudanças que precisem de outra
direção/plano exigem uma nova entrada explícita. Render completo continua
necessário; não foram criados render parcial ou retomada automática.

A imagem fixada do executor ainda precisa ser reconstruída e validada no ambiente
autorizado, junto da etapa 5; não houve build, deploy ou render nesta rodada.
Sem banco, chamadas pagas, geração/download de assets reais ou conteúdo de cliente.
Nenhum serviço foi iniciado; o estado dos cinco previamente interrompidos não foi
confirmado. CI integral/cobertura de 100% e integração com banco/Temporal real não
foram executados; o gate de merge do AGENTS.md continua pendente.

Etapa 7 não iniciada. A preparação da comparação depende do próximo OK; execução,
gastos e renderização exigem autorização específica e orçamento novo.
