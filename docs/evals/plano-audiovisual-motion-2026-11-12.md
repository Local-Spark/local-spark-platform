# Plano audiovisual real e revisão antes do código — 12/11/2026

Uma chamada de plano autorizada foi concluída pelo fluxo real. Parada em
`awaiting_plan`, sem código, asset de IA, storyboard ou render. Revisão do
assistente recomenda ajustar a direção antes da implementação; não houve decisão
persistida do titular ou alteração silenciosa no plano recebido.

## Autorização e execução

Titular respondeu expressamente: “Autorizar somente a migração 0118 e o plano”.
Escopo: dev existente, backup prévio, uma chamada até US$ 1,25 e cinco contêineres
restritos parados. Backup privado de 91.953.385 bytes, índice validado com
pg_restore e SHA-256 registrado. pg_dump/pg_restore 18.3 compatíveis com servidor
17.6. Migração dev 0117 → 0118 acrescentou quatro eventos à restrição do outbox,
sem tabelas novas ou remoção de dados; não reaplicada no _test.

Admissão pelos serviços de owner/RLS existentes; workflow MotionProductionWorkflow
no Temporal já ativo, fila exclusiva e worker efêmero do processo. ASR local novo
capturado como efeito durável; nenhuma transcrição arquivada injetada. Ledger
reserva antes da chamada, fora de locks SQL. Wrapper limita a generate:plan:0,
criação exclusiva impede segunda submissão e renderer é recusado. Não foi criado
runner de produção concorrente. Configuração paga somente em memória do processo,
que encerrou ao concluir o checkpoint; .env/global continuam disabled.

Entrada efetivamente enviada idêntica aos bytes v7 aprovados para uso:
`6be0608f467776acfe1efcf97bfe9e88afc94d6ddbaaa40ff1e5dda613c2b158`.
São 15 quadros da fonte, zero de peça anterior, ASR novo e três relatos de escuta
vinculados aos arquivos. Contratos/bibliotecas/kit/repertório v4 preservados.
Nenhum dado de cliente foi adicionado a fixtures ou ao código versionado.

Checkpoint: `98565fcf618142cb5e157933d43ff3320e2e263338a5787ef66a7dd337d1a51d`.
Workflow COMPLETED; retorno awaiting_plan. Pedido permanece running, sem token
de execução, conforme o contrato de espera. Eventos somente motion.requested e
motion.plan_ready; não há aprovação, operação de implementação ou captura.
Entrada, resposta bruta/normalizada, artifact, usage e hashes preservados em
`.local/evals/motion-supervised-20261112/plan-only-v1/`.

A serialização criptografada canônica reordena chaves de objetos. Verificação
posterior compara igualdade semântica do payload armazenado e wire_sha256
preservado; o wrapper verificou bytes exatos antes da contagem e submissão. Não
confundir reconstrução ordenada depois de abrir o storage com o envio original.

## Proposta recebida

Conceito: duas barras abrem espaço para a palavra pausa e depois se transformam
em apoio do nome do negócio. Vídeo sempre visível, na ordem original, sem recorte
adicional; áudio integral. O modelo escolheu o estilo editorial-janela-v1 e três
cenas, não fornecidos como direção obrigatória do operador.

| Intervalo | Registro/espaço | Texto e transformação | Som |
| --- | --- | --- | --- |
| 0–3.680 ms | Janela central 504×896, fundo claro do kit | Chamada editorial e par de barras entram; textos liberam o cabeçalho | Original |
| 3.680–8.440 ms | Mesma fonte desce e reduz para 468×832 | Barras afastam/alongam e a palavra ocupa o intervalo; repouso após 4.480 ms | Original |
| 8.440–11.200 ms | Janela retorna a 504×896, sem reiniciar | Barras viram apoio horizontal; nome e convite final entram em sequência | Original |

Omissões declaradas: contato da xícara, porque a fonte amostrada não demonstra
apoio e a direção não cria essa ação; servir café, por falta de correspondência
contínua/escuta da mistura verificadas. Reconhece adequação isolada relatada pelo
titular, sem inventar escuta própria. Nenhum evento sonoro adicional proposto.

## Revisão do assistente

**Verificação técnica aprovada:** schema, duração/IDs/vínculos, sete funções do
produto, direção/material/áudio/fala/som passaram novamente pelos validadores.
Áudio original 0–11.176 ms/volume 1; saída 11.200 ms por adequação a 30 fps, sem
reordenar/cortar a voz. Seis beats ligados a word-14 e word-25; word-17 de baixa
confiança não usada. Nenhuma ilustração ou asset novo.

**Recomendação: revisar a direção antes de autorizar implementação.** Não é um
veredito sobre vídeo renderizado, que não existe nesta rodada.

1. A metáfora de abrir espaço tem função e a identidade é coerente. Contudo,
   toda a direção permanece em textos, duas barras e reposicionamento moderado
   da mesma janela. O contrato criativo já pede desenvolvimento visual além
   desses recursos para a elaboração buscada. Pedir uma interação composicional
   concreta entre gesto, texto e espaço com consequência narrativa além da
   mudança de tamanho/posição. Não impor contagem de objetos/cenas ou uma
   representação fixa para satisfazer essa expectativa.
2. Omitir o contato tem justificativa concreta na ação disponível. Omitir servir
   é permitido, mas a falta de escuta da mistura, ainda futura, não deve bloquear
   circularmente propor um evento. Pedir motivo narrativo específico para voz
   sozinha ou proposta delimitada de servir com escuta posterior; não obrigar
   usar um candidato por ele existir. Correspondência contínua não foi verificada.
3. Para prévia posterior: avaliar fechamento (CTA totalmente assentado por
   1.140 ms), deslocamento assimétrico das barras (518/18 px em 520 ms), máscaras,
   continuidade de um único vídeo e inteligibilidade. Nenhum desses riscos foi
   declarado como defeito observado sem render/escuta.

Revisão legível por cena em `REVISAO-DO-PLANO.md`, com fala, gravação, objeto,
fundo, texto, transição, som e limitações; `plan-review.json` preserva critérios,
evidências e pedidos de ajuste. Revisão feita pelo assistente, sem chamada paga
adicional de crítica. Plano original e checkpoint permanecem intactos.

## Custo e limites

Uma chamada gpt-6.1-sol/high/default; contagem prévia 39.898 tokens e teto
calculado US$ 0,639745, abaixo da reserva US$ 1,25. Retorno informou 39.898 tokens
de entrada e 11.441 de saída. Estimativa conservadora pelo uso: US$ 0,214155.
Não é fatura conciliada. Reserva de US$ 1,25 permanece uncertain no ledger,
actual_usd_micros nulo; não liberar nem reutilizar automaticamente.

Capacidade de duas etapas exigida pelo runtime foi mantida, mas somente US$ 1,25
de headroom novo e uma operação de plano estavam autorizados no ledger/processo.
Nenhuma autorização para código, retry, regeneração ou render decorre da sobra
estimada. Próxima chamada requer autorização correspondente; código exige decisão
específica sobre o conteúdo exato do plano.

## Estado restante

- Cinco contêineres restritos confirmados exited; nenhum serviço iniciado.
- Formatação/lint/tipagem e regressões anteriores permanecem verificadas: 1.646
  testes motion (dois skipped), 23 integrações motion/checkpoints. Nesta entrega
  operacional, validação adicional foi de backup/migração, entrada/recibos,
  produto e ausência de implementação/render; sem alterar código de produção.
- CI/cobertura global ainda não qualificados: cobertura Node abaixo de 100% e
  falhas de geocodificação/schema policy_id ausente no _test, já documentadas.
  Não houve migração implícita ou saneamento desse banco nesta execução.
- Qualidade artística, execução de movimento, legibilidade integral, sincronismo,
  fidelidade do ASR e voz/mistura continuam sem certificação. Preparação correta
  e plano válido não demonstram melhora da peça final.

Entrega solicitada encerrada na revisão do plano, antes do código. Titular ainda
precisa decidir sobre os ajustes; nenhum aceite/rejeição foi fabricado no banco.
