# Diversidade de linguagens de motion — 06/11/2026

## Execução autorizada

Após a preparação abaixo, o titular autorizou as três chamadas e o envio dos
pacotes, até US$ 2,25 adicionais, sem refação automática. Autorização preservada
em `authorization.json`, vinculada ao manifesto e aos três hashes de request.
Lote `e2bbd3aa-e405-4411-9d56-82752537bc73` em `.local/evals/motion-batches/`
encerrado com duas peças e uma operação incerta, sem retry. Cartaz bem avaliado,
Giz menos apreciado; Intensa segue preferida. Subtotal conhecido US$ 0,3751375;
total desconhecido por Papel. [Resultado e limites](ensaio-motion-diversidade-2026-11-06.md).

## Objetivo e comparação

Após o feedback positivo do Reel intenso `b14bc09d`, explorar três linguagens
distintas com intensidade alta, mantendo a mesma gravação fictícia, kit,
informações comerciais e duração. V2 é mínimo aceito; a peça intensa é referência
positiva, sem preferência comparativa presumida ou estilo universal.

| Peça | Fonte local da biblioteca | Mecanismos esperados |
| --- | --- | --- |
| Cartaz tipográfico de impacto | `cartaz-gritado` | Tipografia protagonista, cascatas, compressão/expansão, cortes gráficos intencionais. |
| Desenho e giz de cera | `giz-de-cera`, `_pintura.js` e dependências | Traços progressivos, textura, movimento orgânico determinístico e apagamentos. |
| Colagem de papel com profundidade | `livro-pop-up` | Camadas, parallax, sombras de contato, folhas e câmera 2,5D. |

Cada chamada recebe somente sua família, além da skill própria de Reel e das
instruções comuns. Não misturar todos os estilos no mesmo pedido. A entrega é
um relatório com três peças novas e dois comparadores, como nas rodadas anteriores.
O titular avalia somente o MP4 final; não há parada para aprovar cards/frames.

## Entradas congeladas e caminho executado

Base privada: `.local/evals/motion-diversity-round-2026-11-06/`.

- Cenários: `proposal/cartaz.json`, `giz.json`, `papel.json`.
- Manifesto do lote: `proposal/batch.json`; inventário: `proposal/manifest.json`.
- Fonte MIT original e dois avisos de licença: `library/source-snapshot/` e
  inventário de 20 arquivos em `library/inventory.json`.
- Skill própria resolvida pelo loader: `instagram-reel-v1`, SHA-256
  `4ed6a1307437b492cf423612855645752fda331e206920abfcf155c198271ec7`.
- Reutilização explícita de Jev/transcrição da fixture; sem novas chamadas para
  essas etapas. Não é teste de ponta a ponta do WhatsApp/produto.
- Mesmos seis quadros do vídeo fictício; nenhum quadro da galeria ou do v2 no
  novo request. Os dois vídeos comparadores ficam no relatório local.
- Kit/fatos preservados; projeção omite instruções legadas de layout fotográfico
  estático, conforme descrito no pacote. Não altera preço, oferta ou identidade.

| Request | SHA-256 do corpo preparado |
| --- | --- |
| Cartaz | `6c7b74970f7610bc8f990d036219bb1af0610dbb86c51d826343250a3e2de978` |
| Giz | `f5bde429105946329e9390ac2e5034fadc610b403d120afa0eaef00de3a52882` |
| Papel | `10b9e1fd8573ef1c184db8c2851634d689dafe3a47de95c884513d587a0cd748` |

Uma chamada Responses por peça, `gpt-6.1-sol/high`, até 32.000 tokens de saída,
`store:false`, sem retries. O modelo recebe quadros e transcrição, não vídeo/áudio
diretos. A resposta entrega composição HTML/JavaScript e plano de áudio; o
executor atual usa Chromium/Canvas/WAAPI e FFmpeg, sem GSAP ou HyperFrames.
Adaptar código da biblioteca não significa executar seu projeto original.
Código recebido e executado, uso concreto das fontes e possíveis falhas serão
conferidos no resultado, sem melhoria visual manual oculta.

## Chamadas e orçamento propostos

| Escopo | Chamadas | Estimativa | Reserva/teto operacional adicional |
| --- | ---: | ---: | ---: |
| Cada família | 1 | US$ 0,25–0,65 | US$ 0,75 |
| Rodada completa | 3 | US$ 0,75–1,95 | **US$ 2,25** |

Nenhuma chamada desta rodada foi enviada na preparação. Autorizações anteriores
não renovam verba. Antes da execução, solicitar autorização específica para o
gasto e o envio das skills/códigos MIT/documentação local e seis quadros fictícios
à `https://api.openai.com/v1/responses`. Sem refação automática; chamadas
independentes não são repetidas quando outra falha. O teto controla iniciar
chamadas, não limita cobrança de uma já enviada. Uso/custo são estimativas,
não conferência de fatura.

## Comando e controles

Pré-teste sem rede/gasto:

```sh
make motion-diversity-eval
```

Somente após autorização do titular:

```sh
make motion-diversity-eval EXECUTE=1 BUDGET_USD=2.25
```

`scripts/evals/motion_batch_eval.py` usa dois trabalhadores, com preflight e render
serializados, e reaproveita o executor individual. Congela plano/cenários/refs,
reserva antes da chamada e preserva resultados incertos sem reenviar. Relatório,
trace, reservas e custos ficam em `.local/evals/motion-batches/<uuid>/`.
Não requer banco, Temporal, integração WhatsApp ou publicação.

O lote consulta os registros anteriores de lotes e do CLI individual. O CLI
individual ainda não consulta os registros de lote: não há deduplicação global
bidirecional. Não executar os mesmos pedidos pelos dois comandos. Estes três
corpos são novos; esta rodada usa exclusivamente o comando de lote.

Testes offline do orquestrador cobrem limite total antes de efeitos, concorrência,
serialização, falhas/uso desconhecido, escape de relatório e bloqueio de reenvio.
Essa prova não substitui CI integral nem avaliação humana. Isolamento atual
continua limitado a fixtures; código/mídia não confiáveis de cliente exigem
qualificação própria antes de produção.

Validação executada: preflight do manifesto real; 40 testes Python (27 do
executor individual e 13 do lote), três testes Node de áudio, Ruff e mypy strict
do orquestrador aprovados. Nenhuma API paga pelos testes. CI integral não repetido.

Os 20 originais selecionados, incluindo os dois avisos MIT, foram verificados e copiados
para `../meu-braco-direito-motion-sources/snapshots/claude-video-diversity-selection-2026-11-06/`,
com manifesto e README de escopo. Não inclui mídia da galeria, fontes ou
dependências externas; não houve stage, commit ou push. Registro privado:
`source-preservation.json`. Não é pacote executável completo ou backup remoto.

## Etapas seguintes já solicitadas

Depois da diversidade: outros negócios fictícios, story, carrossel, e integração
do caminho criativo qualificado. [Registro e transferência](motion-registro-de-validacao.md).
O titular escolheu preparar vídeos ilustrativos licenciados para Dog em Casa e
Estúdio da Luma. Cópias e termos estão no inventário privado; permissão de edição
não deve ser confundida com direito de enviar quadros a outro provedor. Resolver
essa verificação antes da rodada desses negócios. Não representa nova verba.

Vozes PT-BR mais naturais terão comparação curta e orçamento próprios. Não há
geração de voz ou clonagem incluída nesta rodada. Preservação remota e pacote
completo de dependências continuam pendências explícitas do caminho de produção.
