# Etapa visual 2 — fundo integrado à narrativa

Data: 10/11/2026. O titular autorizou a etapa 2 após o tratamento da gravação e
pediu parada antes da etapa 3. Escopo: fundo em camadas que organiza, prepara e
conecta os focos, mantendo o kit, a alternância e a moldura/escala da etapa 1.
Realismo da xícara e alinhamento temporal com fala não estão nesta fatia.

## Implementação

O executor e movement-v3 já possuem as primitivas necessárias; não foram criados
outro runtime, serviço, schema, tabela, runner ou integração. A orientação genérica
anterior de fundo vivo foi concretizada na skill `instagram-reel-v9`:

- Desenhar os estados de fundo na abertura, no motion pleno e no retorno da gravação,
  descrevendo a função de cada passagem nos campos existentes da direção/plano.
- Usar base opaca, campo de destaque e detalhe do kit, com geometria/posição e
  deslocamentos próprios; manter repouso durante observação e leitura. Variação
  de cor isolada ou textura em loop não é critério de acabamento.
- Preservar contraste também nos estados intermediários, com área opaca de leitura
  quando necessário, sem formas atravessando texto/CTA ou flashes nas bordas.
- Isolar a máscara do fundo num host próprio, atrás de vídeo/texto, evitando recortar
  a moldura ou sombra da etapa 1. Fonte, áudio e relógio continuam intactos.
- Usar os checks/evidências de crítica já existentes; sem dar nota por quantidade
  de camadas, aprovar por código ou inventar alinhamento com palavras do áudio.

A skill contém `makeNarrativeBackdrop`, código original executável para adaptar em
scene_init. Cria três partes internas de um elemento de fundo: base, campo e faixa.
Usa MotionV1.progress para entrada, repouso e saída determinísticos. Cada parte tem
posição própria; a base permanece opaca. IDs, tempos, dimensões e cores vêm da
direção/kit. A geometria deve ser dimensionada para o quadro, e o contraste com
texto deve ser conferido na peça: o helper não mede legibilidade automaticamente.

As partes internas são descritas em beats compostos do elemento, sem exigir três
IDs extras no plano por cena nem beats sobrepostos. O código não altera gravação,
áudio, tipografia ou moldura. Valida host e ordem das passagens; não usa rede, timer,
aleatoriedade ou geração de assets. É exemplo transmitido, não biblioteca instalada
automaticamente nem fundo universal imposto a todo negócio.

Novas capturas resolvem a v9 pelo loader. A v8 e todas as versões anteriores
permanecem registradas e inalteradas; recapturas mantêm seus bytes. Os helpers de
tratamento da gravação, composição e leitura continuam na nova skill. O mesmo
conteúdo chega à geração, à crítica e à correção no payload contado/exportado.

## Caso Café Pausa

Nova direção e brief em:

- `docs/evals/direcao-cafe-pausa-fundo-narrativo-2026-11-10.json`
- `docs/evals/brief-cafe-pausa-fundo-narrativo-2026-11-10.txt`

A abertura recebe planos que preparam a transição; café herda o campo e abre área
papel para o objeto/leitura; pausa recolhe os planos para a volta da gravação e o
convite. Foram acrescentados apenas `tempo-fundo`, `cafe-fundo` e `pausa-fundo`.
Os 16 elementos anteriores, incluindo xícara conceitual, mensagens e tratamento
da gravação, permanecem intactos. Composition/narrative_action foram ajustados
para coordená-los com o fundo. Atenção principal permanece nos focos anteriores.
A direção passa pelo validador do produto e não declara aprovação criativa.

## Validação e entrega

- 97 testes Python dirigidos aprovados em 3,84 s; 100% de linhas/ramos no loader
  medido. Incluem nova captura, preservação da v8, payload contado de geração/
  crítica/correção, fidelidade de direção e exportação.
- 9 testes Node aprovados: execução literal dos quatro exemplos enviados na skill,
  integridade do vídeo/moldura, base opaca, cores do kit, repouso, deslocamentos
  distintos, seek direto/repetido/inverso e rejeição de intervalos sobrepostos.
- Ruff/Mypy e verificação do pacote offline; sem CI global, SQL, geração paga ou
  novo MP4. Não houve acionamento do Docker nem mudança nos serviços mantidos parados.

Pacote pelo mesmo montador do produto:
`.local/exports/motion-cafe-pausa-fundo-narrativo-20261110.zip`.
Contém prompt integral, 12 imagens, JSON/contrato/contexto, direção e materiais de
execução; sem credenciais, contagem remota ou envio a modelo. Fonte e runtimes
preservados. O alias `execution/libraries/movement-v1.js` contém os bytes v3
identificados no manifesto, como na etapa 1.

Implementação e mecanismos foram validados; acabamento visual de uma peça nova
permanece por qualificar. Não declarar fundo vivo entregue num MP4 com base nesses
testes. Rodada paga/render de comparação exige escopo e orçamento próprios.
Etapa 3 (objeto mais realista) só começa após o OK solicitado pelo titular.
