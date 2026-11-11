# Step 1 — Dog em Casa e Estúdio da Luma gerados

[Comparação final: Dog, Luma, Intensa e Cartaz](../../.local/evals/motion-batches/04e48db9-1313-4a52-a188-7a151a9d0e80/review/report.html).
Titular confirmou foco em marca/experiência sem preço e autorizou duas chamadas
e envio dos pacotes, até US$ 1,50 adicionais, sem refação automática.
[Plano, direitos e hashes dos inputs](plano-motion-outros-negocios-2026-11-06.md).

## Peças e operações

| Peça | Resultado | Duração / arquivo | Estimativa da chamada |
| --- | --- | --- | ---: |
| Dog em Casa | Gráfica de cartaz, inversões creme/vinho, janela retrato→ampla→elevada | 8,640159 s; 1.500.978 bytes | US$ 0,290055 |
| Estúdio da Luma | Editorial de beleza, inversões claro/ameixa, janela ampla→retrato→ampla | 9,466667 s; 1.425.655 bytes | US$ 0,3006175 |

Ambos 720×1280, 30 fps, H.264/AAC, material ilustrativo, música/cliques e sem
narração. Não há preços, contato inventado ou afirmação de que mostram trabalhos
dos negócios. Luma usa descrição genérica de cuidado de unhas, sem comprovar
procedimento. Geração do step 1 entregue e avaliada positivamente pelo titular:
Dog/Luma mantiveram o padrão da Intensa. Ver feedback posterior abaixo.

## Feedback do titular e pendência de música

Após assistir, o titular declarou: “eu gostei bastante. mantiveram o padrao ao
nivel intensa”. Considerou as durações menores, em torno de nove segundos,
adequadas e as peças boas. Observou que usaram a mesma música e que isso
talvez fosse um problema. A aceitação criativa destes dois casos não comprova
vídeos próximos a 60 segundos, outros formatos ou integração de produto.

A repetição teve causa concreta: os dois pacotes disponibilizavam e exigiam
uma única trilha, `music`/`assets/trilha.ogg`, mesmo SHA-256
`ec14f24280835548dcf9a5ef0a32e418f43aefc3664cfc038afb0a5752e13e92`.
`click` era somente efeito. A direção podia mudar trecho, volume e efeitos;
não tinha outra música autorizada para selecionar. Portanto, esta rodada não
validou seleção de trilha entre alternativas por negócio.

Próxima prova de áudio deve disponibilizar algumas faixas efetivamente distintas,
com direitos, cópias próprias, hashes e metadados, permitindo escolha automática
conforme negócio, objetivo, material/fala e direção. Registrar escolha e conferir
o mix por escuta. Na entrevista posterior, o titular confirmou escolha automática
conforme negócio/peça, variedade entre pedidos e repetição permitida para
continuidade de séries/campanhas. Não exige música inédita em toda peça; política
definida não significa seleção/histórico implementados ou testados no produto.
Não houve refação, gasto ou mudança nas peças após esse feedback.

Lote pago `04e48db9-1313-4a52-a188-7a151a9d0e80`:

- Dog pago: `fc3d6447-a4f7-4cc5-8507-db74deb58f33`, HTTP 200/completed em
  230,453 s; 61.110 tokens de entrada e 13.728 de saída (6.938 de raciocínio).
- Luma: `40c72fda-0c69-4866-be57-1ae26fa7314f`, HTTP 200/completed em
  282,832 s; 55.411 de entrada e 16.209 de saída (8.672 de raciocínio).
- Dog render offline: `72973f12-9b18-426f-af63-112562dfca51`, sem rede/modelo,
  após adaptação técnica abaixo. A geração paga não foi repetida.

**Total estimado US$ 0,5906725**, não fatura; reserva adicional US$ 1,50 preservada.
Exatamente duas chamadas pagas, zero retries pagos; recuperação offline não
adiciona geração nem deve duplicar o custo. Reservas anteriores, inclusive Papel
incerto da rodada anterior, continuam preservadas e não integram este subtotal.

## Adaptação técnica do Dog, sem mudança visual

O modelo devolveu os caminhos `assets/trilha.ogg` e `assets/sfx-clique.wav`
como `audio.tracks[].asset_id`, onde o mixer espera IDs `music`/`click`.
O pacote continha ambos os vocabulários sem enum específico por caso; isso
permitiu ambiguidade. O contrato recusou `required_audio_missing` após salvar
resposta/direção/custo; essa falha e relatório originais foram preservados.

Foi aplicada correspondência estrita de cinco strings com os ativos congelados:
trilha→`music`, quatro cliques→`click`. Nenhum tempo, volume, ativo escolhido,
conceito, HTML ou JavaScript mudou. A resposta original não foi sobrescrita.
Derivado/mapeamento estão em
`.local/evals/motion-other-businesses-2026-11-06/audio-recovery/` e o render foi
feito pelo CLI com `--from-response`, sem chave/rede/modelo.

Comparação verifica que a única diferença de resposta são esses IDs; HTML/JS
recebidos e executados conferem integralmente por bytes/hash em ambas as peças.
Não houve correção visual manual. O relatório final liga respostas/custos
ORIGINAIS pagos, código/trace efetivamente renderizados e mapeamento. O relatório
original do lote continua mostrando a rejeição, não foi convertido em sucesso.
Antes das próximas rodadas, esclarecer IDs/enum do schema por caso para evitar
esta recuperação; não é necessário gastar para refazer a peça atual.

## Biblioteca, validação e limites

Skill própria Reel carregada pelo loader; fichas/motores MIT reais e código
da Intensa presentes. Dog chama tipografia de cartaz (`palavra`, `medidas`,
`soco`, `tranco`), texto por máscara, câmera interpolada e máscaras de tema.
Luma chama `sobe`, `camAt`/`hs`/`mixC`, `rota`/`pontoEm`/`tracaTrecho` e máscaras.
Funções são chamadas nas cenas, não apenas declaradas em `source_usage`.
Coordenação é por tempo; não há tracking de mãos ou colisão física comprovados.

Preflight dos casos passou. Decodificação integral dos dois MP4s passou no
renderer: Dog 259 quadros e Luma 284; sandbox normal Chromium, nenhuma requisição
inesperada. Conferência final em 390/1440 px: quatro players carregados,
22 links existentes, sem erro, acesso externo ou overflow horizontal.

SHA-256 dos MP4s:

- Dog: `7ada678f4f715354b176a77f4c538ed14f1a62e17c483c310ecad1e22f55abbd`.
- Luma: `47e7fc8120bfb4eb016db31c4b319b30c23d00af3d4a168c21ef4398657ecaf4`.

Código e alguns quadros confirmam inversão de tema, orientação variável e texto
legível nas amostras. Isso não equivale a assistir/ouvir integralmente. Medidas
de áudio: Dog média −28,0/pico −11,8 dB; Luma −30,2/−13,9 dB. Há sinal, sem nova
escuta perceptiva ou aprovação do balanço. Qualidade completa, ritmo, foco e
preferência dependem de avaliação do MP4 final pelo titular.

`review/QA.md`, `verification.json`, `review/report-check.json` e traces guardam
evidências. Não houve alteração de código do produto/executor, instalação,
novo banco, WhatsApp ou publicação. CI integral não repetido por cenários/dados
e recuperação local; não declarar integração ou feature concluída.

Feedback humano confirmou o nível de qualidade nestes dois negócios curtos,
com ressalva de diversidade musical. Story, carrossel, voz natural e integração seguem no
[registro de validação](motion-registro-de-validacao.md), com novas chamadas
dependentes de plano/orçamento próprios.
