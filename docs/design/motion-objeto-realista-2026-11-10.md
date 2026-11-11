# Etapa visual 3 — objeto realista em camadas

Data: 10/11/2026. Etapa 3 autorizada pelo titular; parar antes da etapa 4.
Implementação e testes concluídos. Nenhuma imagem ou peça nova foi gerada.

## Decisão e implementação

Usar recorte com aparência realista e animação em camadas (2.5D): material/luz
na imagem, sombra de apoio separada e vapor gráfico opcional. Uma imagem não
fornece geometria 3D nem vistas ocultas. A xícara genérica gerada é conceitual;
para representar a xícara real do cliente será necessária foto autorizada.

Novas capturas HTML Reel recebem `instagram-reel-v10`. V1–v9 permanecem
inalteradas/registradas por hash; recapturas preservam a versão original. A v10
preserva os exemplos de composição, leitura, moldura/escala e fundo narrativo.
A orientação chega pelo mesmo montador a geração, crítica, correção e exportação.

A skill acrescenta `makeCutoutObject`, exemplo executável em scene_init com
MotionV1.progress existente. Anima escala uniforme, posição e inclinação no plano;
a sombra acompanha o eixo horizontal, concentra e perde difusão ao assentar.
Há repouso e saída, sem loop/flutuação permanente. Seek absoluto, direto e inverso
produz o mesmo estado. O helper rejeita hosts/tempos/geometria inválidos antes de
alterar estilos; não modifica src, pixels, gravação, áudio, fundo ou moldura.
A imagem deve estar decodificada; CSS do layout define apoio, dimensões, cor da
sombra do kit e ordem de camadas. Não é instalado automaticamente no runtime:
o modelo recebe código concreto para adaptar à construção, com testes literais.

O fluxo existente de imagens já atende esta etapa: `MotionIllustration`,
`illustration_generation`, acervo autorizado, reserva/custo/proveniência privados,
PNG com transparência verificada, armazenamento e pixels na crítica. Nenhum novo
serviço, tabela, modelo, runner, política de preço ou capacidade foi habilitado.
A imagem conceitual usa `generated_asset`/role=image; foto autorizada usa
`authorized_asset`/role=image. Correção reutiliza o mesmo asset sem regeneração.
Ausência de material/capacidade não autoriza inventar arquivo nem trocar realismo
por outro desenho. Imagem com fundo opaco não é tratada como recorte pronto.

Na crítica, visual_development/motion_role devem avaliar os pixels, apoio,
material, recorte, interação e preservação das etapas anteriores. Não aprovar
pelo nome do helper/asset, nem afirmar movimento não mostrado nas amostras.

## Caso Café Pausa preparado, dependente de asset

Arquivos de entrada:

- `docs/evals/direcao-cafe-pausa-objeto-realista-2026-11-10.json`
- `docs/evals/brief-cafe-pausa-objeto-realista-2026-11-10.txt`
- `docs/evals/ilustracao-cafe-pausa-objeto-realista-2026-11-10.json`

A direção mantém abertura em vídeo tratado, motion pleno e retorno à gravação.
Preserva kit, fundo narrativo, voz e fonte. Substitui a xícara por um único recorte,
reutilizado no café e na pausa; remove `cafe-liquido` e a ação de preenchimento.
Cerâmica opaca numa imagem única não permite mostrar líquido subindo com coerência.
A ação passa a chegada/assentamento e transferência de atenção, com vapor separado.
Texto editorial continua sem alegação de alinhamento temporal ao áudio.

O JSON de ilustração é uma especificação, **não um arquivo PNG existente**.
A direção requer `illustration_generation` configurada e orçamento próprio para
execução futura. A captura do produto a rejeita quando a capacidade está ausente.
Não exportamos um pacote de execução fingindo conter a xícara: o exportador local
atual não transporta essa capacidade nem esse asset. O pacote anterior de fundo
continua sendo a proposta com desenho, não demonstração desta etapa.

Para a futura comparação: autorizar uma rodada com escopo/custos de imagem,
geração da composição, captura e crítica definidos; capturar pelo produto com
política de ilustração configurada, anexar direção/brief e exigir a única imagem
declarada conforme a especificação. Inspecionar pixels/alpha/material nos cards
antes da aprovação de render pelo fluxo existente. Uma imagem da xícara real do
cliente, se fornecida, exige direção `authorized_asset` e o ID do acervo efetivo.
Não reutilizar os orçamentos de rodadas anteriores.

## Verificações e limites

- 131 testes Python dirigidos passaram em 4,34 s. Cobertura 100% de linhas/ramos
  no loader medido; não é cobertura global. Incluem captura nova/antiga, payload
  contado de geração/crítica/correção, exportação, bloqueio sem capacidade e fluxo
  de imagem até armazenamento/preview/proveniência com provider simulado.
- 11 testes Node passaram em 0,17 s, executando os cinco exemplos reais da skill
  e regressões do movement-v3. Objeto/sombra, repouso, seeks direto/inverso/repetido,
  rejeição de tempos sobrepostos e integridade da mídia/kit cobertos.
- Ruff/Mypy do escopo aprovados. Sem CI global, SQL, chamada paga, geração de
  asset, render de peça ou uso do Docker. Os cinco serviços continuam sem ação.

Os testes sintéticos comprovam mecanismos e contratos, não realismo visual da
xícara ou acabamento de um novo Reel. Essa qualificação permanece pendente.
Etapa 4 (alinhamento com fala) aguarda OK do titular.
