# Prova integrada — composição por cenas, 09/11/2026

Estado: preparação concluída; titular autorizou US$ 5,40 em novas reservas.
Tentativa interrompida com saída truncada; sem quadros para aprovação.

## Objetivo e caso

Produzir uma nova peça do negócio fictício Café Pausa com o kit e a fonte da
prova anterior, incluindo direção por cena, componentes e ilustrações quando
necessárias. Investigar a riqueza visual e a função narrativa dos elementos;
não copiar identidade dos exemplos nem afirmar equivalência já demonstrada.

Baseline preservado em `.local/evals/reel-integrated-motion-resume-20261109/selected.mp4`.
Nova rodada em `.local/evals/reel-storyboard-proof-20261109/`.
O briefing pede representações pertinentes ao preparo/pausa para café, além de
vídeo reposicionado, títulos e formas. Preserva a fonte inteira e seu áudio;
não inventa preços, ofertas, transcrição, produto ou local real.

## Sequência e aprovação

1. Preparar contexto e payload sem chamada externa de IA nem pedido enfileirado.
2. Após orçamento explícito, admitir pela API e despachar via outbox/Temporal,
   com worker dedicado à fila da prova e os serviços existentes do produto.
3. Gerar composição/plano/código numa chamada. Gerar até duas ilustrações PNG
   transparentes somente se declaradas e necessárias; código/componentes também
   podem bastar. Apresentar galeria dos quadros completos reais por cena.
4. Parar para decisão humana vinculada à versão/hash. Sem MP4 integral ou crítica
   paga antes desse aceite. Rejeição encerra o pedido; não autoriza regeneração.
5. Após aceite, retomar no Temporal, renderizar, criticar e corrigir no máximo
   uma vez se houver problema demonstrado e saldo. Apresentar baseline e resultado.

A crítica temporal atual examina até três eventos em até vinte quadros e declara
omissões; não certifica todo o movimento ou a mixagem. Galeria comprova aparência,
não ritmo. Avaliação humana do vídeo com som decide se houve ganho suficiente.
Uma possível correção posterior pode alterar a composição: o aceite dos quadros
não substitui a aprovação final da peça. Não expandir formatos nesta rodada.

## Plano proposto de custo e envio

| Operação | Limite | Reserva por chamada | Total máximo de reservas |
| --- | ---: | ---: | ---: |
| Geração/crítica/correção/crítica, `gpt-6.1-sol` | 4 | US$ 0,85 | US$ 3,40 |
| Ilustração, `gpt-image-2.5-flare-2026-09-08` | 2 | US$ 1,00 | US$ 2,00 |
| Total novo | 6 | — | **US$ 5,40** |

Até quatro consultas de contagem de entrada, vinculadas às chamadas textuais.
Geração/correção: máximo de 32.000 tokens de saída; críticas: 8.000.
Imagens: 1024 × 1024, medium, PNG transparente. Não geram novas imagens na correção.
Sem imagens necessárias, as duas reservas correspondentes não são consumidas.
O modelo recebe briefing/kit fictícios, quadros da fonte/peça, código, direção,
plano de movimento e miniaturas das ilustrações produzidas. Nenhum material de
cliente real; referências externas não são enviadas nesta rodada.

Reservas anteriores globais verificadas: US$ 6,80; teto agregado proposto US$ 12,20.
Não são crédito reutilizável. Orçamento de imagens integra o limite do pedido.
Reserva é admissão local: a Images API não impõe este valor como teto de fatura;
uso efetivo será registrado. Uso desconhecido, excesso, falha incerta, saída
inválida/truncada ou falha de render interrompem sem nova tentativa automática.
Nova autorização será necessária para mudar esse plano após falha.

## Preparação e validação

Migração aditiva `0114_motion_storyboards` aplicada no dev existente sem limpeza.
Renderer reconstruído com protocolo 2 e digest
`sha256:e9884862762529bf49086fb579676a7be15a108a5ac1bb88c7c0f44496a6bf51`.
Worker reconstruído sobre as dependências locais já qualificadas, sem rede de build
nem credenciais no contexto. A checagem real executou vídeo sintético de 34 ms e
um quadro isolado: MP4 1.939 bytes; dois frames do vídeo e um do storyboard.
O comando verifica também o protocolo de quadros quando a capacidade está ativa.

Oito testes unitários direcionados passaram em 0,71 s; Ruff/format aprovados.
Sem CI completo ou suíte de banco. Isso qualifica preparação do executor, não
resultado criativo, RLS completo ou fluxo pago fim a fim. O resultado desta prova
será registrado após execução e avaliação do titular.

Preparação confirmou duração 11.200 ms, seis quadros da fonte e payload de
1.778.485 bytes. SHA-256 do payload inicial:
`4dc66c9fcc27e11b5f592604bdb2b2df29ff39285b0c0a121559eb2cef5b54e0`.

## Resultado da primeira tentativa

Uma chamada de geração retornou `MOTION_AI_OUTPUT_LIMIT`; estimativa US$ 0,241478,
reserva US$ 0,85 retida. Nenhuma imagem/render/crítica. Retomada ainda depende de
autorização conforme [novo plano](plano-retomada-storyboard-integrada-2026-11-09.md).
