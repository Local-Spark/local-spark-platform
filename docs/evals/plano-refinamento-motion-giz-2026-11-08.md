# Prova criativa do Giz antes da integração

Em 08/11/2026, após confirmar a melhora de títulos e legendas no Reel 1c, o
titular escolheu **comprovar melhora de motion primeiro**. O ensaio 1c continua
como prova de reparação de legibilidade; não vira referência criativa do produto.
O protótipo e o replay real estão concluídos e qualificados. O plano financeiro
concreto recebeu autorização em **09/11/2026**: **até duas chamadas e US$ 1,25
de teto de admissão**. O titular respondeu “Autorizar até US$ 1,25 para a prova
Giz”. A execução concluiu duas chamadas HTTP 200 e terminou
`completed_human_pending`: crítica favorável à v1, três requisitos `met`, seis
critérios `pass`, áudio `uncertain` e zero achados. Sem reenvio ou reparo visual
manual. O [resultado completo](ensaio-refinamento-motion-giz-2026-11-09.md)
registra custos, tempos, preservação de áudio e limites. QA do relatório
aprovado em 390/1440 px e dois modos. Na entrevista humana, o titular respondeu
“B ficou melhor.”, com [registro vinculado à comparação](../../.local/evals/motion-feedback-review-runs/1c758136-7530-43d8-96b7-39e4b0e44888/human-feedback.json).
A etapa 3 foi concluída no recorte de legibilidade 1c + refinamento guiado Giz;
prosseguir às implementações 4 e depois 5 já autorizadas, ainda não concluídas.
Não inferir aceite de áudio, de cada critério ou benefício geral de custo/qualidade.

O [registro de autorização](../../.local/evals/motion-feedback-review-runs/1c758136-7530-43d8-96b7-39e4b0e44888/authorization.json)
tem SHA-256 `1705ce1c3078f640846049f797649684319be9a7c287fecaaf7f58307cc008c6`.
Vincula a resposta da entrevista `call_d3ff68b65d724ed392cee307e73bdf9c`, item 0,
ao plano pago, à qualificação conferida e ao pedido inicial. O plano proposto
original fica preservado; a autorização é um registro posterior separado.

## Hipótese e atribuição

O candidato é o Giz `15adf19d-6edb-4073-9857-bd11684e4162`, do lote
`e2bbd3aa-e405-4411-9d56-82752537bc73`. Há desenho, escrita, apagamentos e
cortes no original. O feedback posterior registrado foi: “nao gostei tanto;
nao teve mudancas de theme, nem alteracoes de transicoes em formato do video”.

Não foi demonstrada uma violação inequívoca do briefing original. O objetivo
agora é **refinamento guiado pelo feedback**, com contexto adicional declarado.
Intensa e v2 existiam como comparadores locais, mas não foram enviados
visualmente ao gerador do Giz. O uso de seus quadros na revisão é uma nova
intervenção; eventual ganho não prova que o crítico teria descoberto sozinho
um defeito usando apenas o pedido original.

A hipótese é que mudanças de tema e transformação da janela, com função na
narrativa, melhorem a peça mantendo a linguagem de desenho do Giz. Não existe
uma intensidade universal ou obrigação de copiar a sequência/layout da Intensa.

## Insumos preservados

Pacote privado: `.local/evals/motion-creative-review-giz-proposal-2026-11-08/`.
São 68 arquivos inventariados, mais manifesto e digest, totalizando 70 arquivos.
Manifesto SHA-256:
`486f5a2467b704cb488416fccbd6b72d639aadea5fcbfa3df073d3fff03f7d0d`.

O pacote separa contexto original, feedback posterior, referências adicionais,
direção/código recebidos, seis assets executáveis, MP4, trace, custos e licenças.
Referências ficam fora da allowlist executável: orientar a revisão não autoriza
embutir seus vídeos na peça. Nenhuma mídia nova será comprada ou gerada.
O original e todas as respostas/versões serão conservados.

O custo histórico conhecido da geração do Giz é US$ 0,2203975 estimados;
não é fatura nem custo completo do material/produção. A operação Papel incerta
do lote histórico não será reenviada nem reconciliada por este ensaio.

## Percurso proposto — até duas chamadas

O feedback humano já fornece o ponto de partida. Não haverá uma crítica paga
inicial apenas para repetir os ajustes pedidos.

1. Preparar o pedido de refinamento com original, feedback, requisitos
   observáveis, quadros reais e referência adicional identificada. Solicitar
   uma composição completa no contrato HTML/JS existente.
2. Validar e renderizar a resposta sem reparos visuais manuais. Preservar o
   áudio original por cópia e comparar pacotes, tempos e PCM. Qualquer falha
   fica registrada; não haverá nova geração ou reenvio automático.
3. Solicitar uma avaliação comparativa de A/B contra o briefing atualizado,
   separando movimento observado, atendimento de cada requisito e incertezas.
4. Entregar os vídeos completos, custos, tempos e limitações para decisão
   humana. Mais movimento, preferência do modelo ou última versão não
   equivalem a aprovação criativa.

Máximo: uma revisão criativa e uma avaliação final. O
[plano pago proposto](../../.local/evals/motion-feedback-review-runs/1c758136-7530-43d8-96b7-39e4b0e44888/paid-plan-proposed.json)
conserva seu estado histórico `proposed_not_authorized`. A autorização específica
do Giz foi recebida depois, em 09/11, e está registrada separadamente acima;
não transfere tetos de Intensa/Dog/Luma ou do 1c.

- Teto proposto de admissão: **US$ 1,25**. Reservas de US$ 0,75 para refinamento
  e US$ 0,25 para comparação, com US$ 0,25 de folga para uso observado. Reserva
  controla a admissão; não é garantia de fatura ou custo completo.
- Mesmo provedor/modelo do preparo: OpenAI, `gpt-6.1-sol`, reasoning `high`,
  `store=false`, sem retry. Falha ou cobrança incerta interrompe novos efeitos.
- Pedido inicial preparado: 32 imagens, 19.738.876 bytes, SHA-256
  `4760e47ac1e57a27dd175b988e1773ea37b58d0785d3cae4e2eacfea12cdd7cf`.
  O hash coincide com a qualificação.
- Comparação prevista com 52 imagens. O corpo exato só será construído após B
  inspecionada e ficará preservado antes do envio. Limite de 45.000.000 bytes;
  não truncar evidências para caber nem enviar um pedido diferente silenciosamente.

Há duas inspeções locais antes da comparação paga: código/conteúdo/licenças e
artefato renderizado, incluindo prova de preservação do áudio. São verificações
do executor, não uma nova etapa de aprovação pelo titular. A decisão humana
sobre a peça completa continua posterior à comparação.

## Critérios e limites da próxima avaliação

Os requisitos propostos em `proposed-review-requirements.json` são:

- `theme_change`: variação visível e legível entre estados da paleta existente,
  relacionada à narrativa. Dois estados são a interpretação operacional de
  uma mudança, não uma citação literal ou regra para todos os clientes.
- `window_transformation`: mudança perceptível do formato da janela, com
  estados intermediários e preservação da preparação real do café.
- `narrative_role`: transformações a serviço da progressão da mensagem,
  conservando escrita, traços e apagamentos característicos do Giz.

O contrato implementado exige confrontar cada requisito congelado com
evidências e marcar atendido, não atendido ou incerto, separando movimento
observado de atendimento criativo. Sua calibração criativa real ainda depende
de amostras mais amplas; neste caso, o titular confirmou preferência por B.
Observar um fade ou zoom
não encerra essa avaliação. Uma composição discreta pode ser adequada quando
esse for o objetivo; não se força intensidade ou refação por gosto arbitrário.

Quadros e código não equivalem a assistir ao movimento completo. A amostragem
preparada inclui transições, abertura, fechamento e texto; a comparação deve
usar os mesmos tempos em A/B. Tempos das referências e proveniência do MP4 bruto
ou remuxado estão registrados. Tempos de busca não são apresentados como
timestamps medidos quando não forem.
Áudio perceptual e fluidez integral continuam exigindo avaliação humana.

Fatos, textos, materiais, fontes, paleta, créditos, duração e áudio devem ser
preservados. **HTML/JS livre não garante texto/fatos imutáveis por schema** como
a ponte declarativa do 1c: instruções e declarações do modelo não são prova.
Inspeção de código e da peça devem identificar e rejeitar mudanças indevidas,
sem corrigi-las silenciosamente ou declarar invariância apenas por validação
estrutural. A mistura e a seleção de músicas não fazem parte desta hipótese.

## Qualificação local concluída — sem API paga

Run privado: `1c758136-7530-43d8-96b7-39e4b0e44888`, em
`.local/evals/motion-feedback-review-runs/`. A
[qualificação](../../.local/evals/motion-feedback-review-runs/1c758136-7530-43d8-96b7-39e4b0e44888/qualification.json)
tem SHA-256 `c899ac2d7f84c6328599a10adb4dc6d4db42218748c7edd1d9df926162517e69`
e vincula o pedido inicial, insumos, código e ferramentas usados.

O replay real passou. MP4 bruto byte a byte igual ao original, SHA-256
`230921ac23f714dcaa90c2d16b65dfbf5246d1c8d6b601d5af56695e52e58eb6`.
O remux tem SHA-256
`1a53e011f6e3e28e69487411742e320823c8e3ddcf13304e3e580bcee4b5e972`;
a diferença é de empacotamento, com todos os 336 quadros RGB24 e tempos iguais,
e 176 pacotes AAC, PCM e tempos de áudio iguais. Isso prova a equivalência do
baseline reproduzido. A versão refinada foi produzida depois e passou em sua
própria prova de 176 pacotes AAC, tempos e PCM preservados, sem escuta perceptual.

Código qualificado arquivado em 14 arquivos no run. Passaram 160 testes de
Giz/contratos/relatório/legado e 66 declarativos (57 mais nove casos de bloqueio
de caminhos indevidos). O executor e transporte genéricos agora impedem
contornar os caminhos próprios de Giz/1c; sidecar real, tempos de referência
e proveniência bruto/remuxado foram corrigidos. `make types` cobre oito módulos
do laboratório. Esses resultados não reclassificam execuções históricas.

## Verificação antes de gasto e integração

Preparo executável, vínculo dos pedidos, amostragem, replay e plano financeiro
estão prontos. **Autorização recebida e duas chamadas concluídas em 09/11.**
Código e artefato foram inspecionados localmente, com prova de áudio, antes da
segunda chamada comparativa. Estimativa incremental US$ 0,6482575; subtotal de
APIs com o histórico US$ 0,8686550. A comparação excedeu sua reserva em
US$ 0,0138475; comprometimento US$ 1,0138475, dentro do teto US$ 1,25. Sem
operações incertas; isso não é fatura, COGS completo ou custo por peça aceita.
Controles de identidade exclusiva, concorrência, custo conhecido/incerto e
interrupção sem retry permanecem obrigatórios. O protótipo é privado, com
materiais fictícios/ilustrativos; não é runner de produção nem qualificação de
isolamento para conteúdo arbitrário de clientes.

As [verificações finais do laboratório](../../.local/ci-20261108/lab-final-checks-result.json)
passaram: lint/formatação, mypy de 272 módulos da aplicação e oito scripts,
363 testes Python motion em 101,60 s e três testes Node de áudio. Os 29 arquivos
do laboratório conferidos antes/depois permaneceram idênticos. Os números
anteriores descrevem recortes de verificação; não somá-los a esta suíte final.

As tentativas anteriores do CI falharam em recibo após 785 aprovações, durante
diferença de cerca de 11 h entre relógios, e depois em token após 75 aprovações.
Essas falhas e o módulo isolado com dois testes aprovados permanecem históricos.
A [execução final de 09/11](../../.local/ci-20261108/ci-final-result.json)
terminou `make ci` exit 0: 5.043 aprovações e dois skips por FFmpeg/FFprobe fora
do PATH. Os mesmos dois testes reais de MP4 passaram separadamente em 4,97 s
após ajustar só o PATH privado, sem mudar teste/produção.

Cobertura app: 17.229/17.229 linhas e 4.726/4.726 branches (100%). Passaram
363 testes Python motion, três Node de áudio, 62 Node renderer (100% linhas/
branches/funções), Ruff/formatação e mypy 272+8. Os 735 arquivos app/migrations
e 29 do laboratório permaneceram iguais aos snapshots; logs sem credenciais.
As 69 amostras de relógio não indicaram repouso: diferença total −0,048 s em
1.114,6 s. Não há dependência de disponibilidade do Mac para esta execução já
concluída.

O PostgreSQL descartável do CI usou `fsync`, `synchronous_commit` e
`full_page_writes` desligados, sem alterar a configuração de produção. A suíte
não qualifica perda de energia ou recuperação de servidor. O CI está concluído;
a entrevista humana foi respondida com preferência por B. A resposta sobre
manter o Mac acordado não implica repetir esta execução já concluída.

A comparação real e a preferência humana concluíram a prova exigida da etapa 3
nesse recorte. A integração do Reel (4), seguida dos demais formatos (5), já
está autorizada e passa a ser o próximo trabalho; não está concluída pelo ensaio.
Intensa/Dog/Luma continuam referências já avaliadas; a revisão do Giz não revoga
esses resultados nem cria um padrão universal.
