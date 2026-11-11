# Reformulação da composição — Café Pausa, 09/11/2026

## Decisão e objetivo

O titular gostou das xícaras desenhadas e autorizou explicitamente reformular a
composição antes do vídeo. Esse aceite não aprova os quadros anteriores para
animação nem encerra o ponto 4. Preservamos kit, fonte, áudio, desenhos figurativos,
skills, acervo, biblioteca de motion, Temporal e o gate de aprovação dos quadros.

A nova direção desta prova é:

1. **Gesto:** gravação do preparo em destaque, jarra desenhada em escala expressiva
   e tipografia integrada; introduzir o motivo visual que liga as cenas.
2. **Transformação:** desenho como protagonista, jarra/fio/xícara compondo uma
   ação ampla; gravação em janela secundária legível. Alterar escala e organização,
   sem apenas inverter os lados do arranjo anterior.
3. **Pausa:** outra hierarquia, com xícara e vapor organizando o convite e a área
   de leitura; continuidade visual com o objeto da cena anterior.

A IA continua responsável por desenho, composição final, código e movimento.
A direção acima é briefing específico da prova, não template universal para marcas.
Quadros reais ainda precisam ser gerados; este documento não é uma nova prévia.
Não copiar identidade de referência, inventar fatos ou substituir o produto real
por imagem sintética. Preservar toda a fonte e o áudio não implica fazer o vídeo
dominar todos os quadros. Desenhos que o titular gostou são uma direção de linguagem;
não prometemos reutilização pixel a pixel dos SVGs da tentativa anterior.

## Ajuste no produto

`motion_creative.py` orienta geração e crítica a considerar a evolução do foco,
da escala e da organização espacial. Acrescentar desenhos ao mesmo retângulo de
vídeo não demonstra elaboração por si só. Repetição com propósito narrativo é
válida: não se impõe variedade arbitrária ou quantidade de elementos.

A instrução corrigida de `MotionV1` também segue no novo snapshot/worker: toda
track precisa de 1–12 beats; elemento estático deve ter hold ou ficar fora da
timeline. Não alteramos o runtime, seu hash, os pedidos encerrados ou seus resultados.
Não há reparo silencioso de código nem reabertura SQL de tentativa com falha.

Vinte testes direcionados passaram em 1,09 s; Ruff/format aprovados. Worker local
reconstruído com os dois arquivos de orientação, sem rede de build ou credenciais.
Renderer permanece o mesmo já verificado; sem nova migração, CI ou suíte longa.

## Autorização e limites, sem ampliar o orçamento

Base: autorização explícita original de **US$ 5,40** para esta prova, limite de
64.000 tokens autorizado na retomada e novo comando explícito para reformular a
composição após visualizar os quadros. A nova execução é uma reformulação solicitada
pelo titular, não repetição automática após falha. O orçamento restante já aprovado
é suficiente: **US$ 1,70 retidos + até US$ 3,70 = US$ 5,40**.

- Até duas chamadas textuais: nova geração e crítica após aceite dos quadros;
  duas contagens correspondentes. Reserva US$ 0,85 por chamada.
- Geração até 64.000 tokens de saída; crítica até 8.000. Mesmos modelo e tarifas.
- Até duas ilustrações opcionais, reserva US$ 1,00 cada, nos mesmos parâmetros
  do plano original. Sem imagem necessária, não ocorre chamada/reserva de imagem.
- Total máximo das três tentativas: quatro chamadas textuais, quatro contagens,
  duas imagens; sem correção automática. Não ultrapassa os limites totais aprovados.
- Teto global US$ 12,20, incluindo US$ 8,50 já retidos. Reservas antigas não são
  liberadas/reutilizadas; uso estimado anterior US$ 0,421603, distinto de fatura.
- Mesmos dados fictícios enviados à OpenAI: briefing/kit, fonte e seus quadros,
  plano, código e resultados. Não enviamos novos materiais de terceiros.
- Reserva de imagens é admissão local, não teto de faturamento imposto pelo provedor.
  Uso desconhecido/excedido ou falha interrompe; nenhuma nova tentativa automática.
- Após captura pelo produto, apresentar galeria e aguardar aceite exato da versão
  antes de MP4/crítica. Não iniciar etapa 5.

Preparação e evidências em `.local/evals/reel-storyboard-composition-20261109/`.
O briefing completo está em `brief.txt`; os payloads e resultados ficam privados.
