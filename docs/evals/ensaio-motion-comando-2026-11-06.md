# Primeira geração pelo comando único — 06/11/2026

## Avaliação do titular e diagnóstico da diferença

O titular esclareceu: **a peça nova não ficou ruim**, mas esperava um salto
maior e continua preferindo o Reel v2. Valoriza a janela que passa de horizontal
para vertical e volta, as transições suaves e as formas/pontos como mecanismos
da composição. Não equiparar esse feedback à rejeição da rodada 1c nem
considerá-lo aprovação de superioridade ao v2. Feedback preservado em
`creative-feedback-2026-11-06.json` no diretório da geração, sem alterar o MP4.

Conferidos o request, a proposta anterior enviada como base e o código final:

- V2 interpola a mesma janela de 600×545 para 340×575 e depois 600×433;
  inclui conector, ponto e expansão circular. O novo usa predominantemente
  recortes largos, duas varreduras retangulares e trocas diretas em 4,3/6,55 s.
- A proposta da primeira chamada, reaproveitada na segunda, dizia expressamente
  “Sem círculo expansivo” e que não copiaria o ponto expansivo/composição em
  escada. O briefing deixou variar a direção sem proteger os mecanismos que
  sustentavam a preferência do titular. Mais fontes não obrigavam preservá-los.
- Último render: Canvas em Chromium/Playwright + FFmpeg, **sem HyperFrames
  ou GSAP**. O v2 histórico original usou HyperFrames; a adaptação WAAPI também
  aprovada e sua reprodução local não precisaram dele. Assim, ausência de
  HyperFrames não explica sozinha a diferença nem impede esses movimentos.
- O input forneceu `claude-video/SKILL.md`, fichas/código de três projetos,
  código v2 e 12 quadros. Houve adaptação concreta parcial de `cartaz-risografia`;
  não execução de todo o catálogo nem dos três motores completos.
- **As skills próprias por formato de `app/assets/motion_skills` não entraram
  no último request do CLI.** A skill externa foi contexto textual; seu
  procedimento completo não foi executado automaticamente. Este recorte não
  demonstra a orquestração completa das skills do produto.

Próximo critério proposto para este caso: partir da composição v2 aprovada,
preservar transformação contínua de janela, encadeamento de formas e curvas,
e avaliar melhorias isoladas. Usar a biblioteca para ampliar essa base em vez
de substituí-la por outra direção sem medir o ganho. Não tornar café, paleta
ou estilo v2 padrão de todos os negócios. Nenhuma chamada nova nesta análise.

## Retomada concluída: Reel novo disponível

O titular informou ter adicionado créditos e autorizou tentar novamente.
A retomada explícita criou a operação
`53054ac7-8968-44a1-99bb-4e3763135269`, vinculada ao 429 preservado. Foi
executado `make motion-eval EXECUTE=1 RETRY_REJECTED=1 BUDGET_USD=0.75`.

- [MP4 novo](../../.local/evals/motion-runs/53054ac7-8968-44a1-99bb-4e3763135269/render/render.mp4)
  e [comparação/trace](../../.local/evals/motion-runs/53054ac7-8968-44a1-99bb-4e3763135269/report.html).
- Provedor HTTP 200/completed em 348,062 s: 53.639 tokens de entrada
  (53.636 cache-write) e 17.735 de saída, incluindo 11.360 de raciocínio.
  Estimativa conservadora do CLI: **US$ 0,3114475**, não fatura; reserva US$ 0,75.
  A primeira direção/cards custou estimados US$ 0,2397635. A rejeição de saldo
  não informou uso; seu registro/reserva anteriores permanecem preservados.
- MP4: 11,2 s, 720×1280, 30 fps, H.264/AAC, 1.368.202 bytes, 336 quadros.
  Decodificação integral passou, sandbox normal do Chromium e nenhuma
  requisição inesperada. SHA-256:
  `27b35df9dcb7e5ab3c8372315aa9a9f6380672db8da6468d1ba0c91ef12d3fc7`.
- HTML e JavaScript renderizados conferem por hash e conteúdo com a resposta
  recebida. **Não houve correção manual do desenho, código ou montagem**.
- Conferidos código e quadros: duas varreduras, máscaras tipográficas,
  mudanças de enquadramento/hierarquia e gravação visível no primeiro quadro.
  Há adaptação concreta de `medir`, `rotulo` e mecanismo de rolo de
  `cartaz-risografia`; os demais motores foram opções fornecidas ao modelo,
  não componentes todos usados. A gravação permanece contínua: os cortes
  são reenquadramentos, não cortes semânticos do conteúdo.
- Mix com voz, música e duas ocorrências de clique. Quadros e metadados não
  equivalem a assistir à peça ou ouvir o mix; não houve escuta perceptiva nova.
  **Aceite criativo e superioridade ao v2 aguardam avaliação do titular.**

O CLI recebeu recuperação restrita à rejeição de saldo comprovada e autorização
explícita; resultado incerto continua bloqueando retry. 25 testes offline, Ruff
e mypy passaram. Não se repetiu o CI integral da aplicação nesta fatia.

O relato abaixo preserva a primeira tentativa recusada; ele não descreve o
estado final após esta retomada.

## Resultado

O titular pediu o vídeo gerado depois da entrega do comando. Foi executado
`make motion-eval EXECUTE=1 BUDGET_USD=0.75`, usando a segunda reserva de
US$ 0,75 da rodada já autorizada, sem ampliar o teto de US$ 1,50.
O modo de revisão somente do resultado final permanece autorizado.

O preflight local passou. O provedor devolveu HTTP 429 em 2,508 s:

```json
{"type":"insufficient_quota","code":"credit_balance_exhausted"}
```

A resposta informa saldo esgotado. Não contém composição, `usage` ou vídeo.
Portanto, **nenhum MP4 novo foi gerado nesta tentativa**. A ausência de uso
informado não é uma fatura conferida; a reserva de US$ 0,75 foi preservada.
Não houve retry automático nem alteração de modelo, chave ou pedido.

## Evidências privadas

Diretório:
`.local/evals/motion-runs/49472d46-487d-4226-9021-b6bd2d888591/`.

- `request.body`: pedido integral enviado, SHA-256
  `21f8ca8100e35eaa073831d1fcdd3334a1c2c5e38e9acf501967c40428bcf958`.
- `response.body`: resposta bruta, SHA-256
  `48d9f03c6f9b357bc078fb3eb43d1a51aaa9a2c3257727dc310158e50b086fa3`.
- `ledger.jsonl`: operação `49472d46-487d-4226-9021-b6bd2d888591`,
  reserva antes da rede, recebimento e rejeição.
- `cost.json`: estimativa indisponível, sem uso informado; não tratar como
  custo de uma peça aprovada ou zerar a reserva.
- `case.json`, `frozen-case.json`, assets e avisos preservados antes da rede.
- A continuação está vinculada à autorização original em
  `.local/evals/motion-quality-reset-2026-11-06/round/continuation-via-cli.json`.

## Continuação

O usuário foi informado e recebeu entrevista entre repor o saldo para manter
o teste pelo endpoint preparado e produzir uma prévia pelo Codex da sessão,
identificada como outro modo de criação. A prévia alternativa não poderá ser
apresentada como resposta deste endpoint ou prova de sua integração.

Não repetir uma operação incerta, apagar o marcador ou mudar detalhes do pedido
apenas para contornar o bloqueio. Uma retomada após rejeição conhecida precisa
de identidade nova, autorização explícita e vínculo com o histórico preservado.
Reprodução offline do v2, cards da primeira direção e esta rejeição são
resultados distintos. [Prova do comando sem API](como-executar-ensaio-motion.md).
