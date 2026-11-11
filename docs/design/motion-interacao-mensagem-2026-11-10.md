# Interação entre mensagem, elementos e transições

## Evidência e correção de direção

Após comparar a candidata de US$ 0,322005, o titular relatou pequena melhora,
mas percebeu apenas vídeo e letras em transição. Gostava dos ícones, setas e
xícaras; pediu acabamento menos infantil, não a remoção desses recursos. Espera
que palavras/frases importantes tenham interação visual ligada ao significado.

A direção fornecida por nós na etapa 3 restringia explicitamente xícaras
desenhadas e escolhia planos/tipografia. A candidata seguiu essa entrada e recebeu
`adequate`, mas o titular não aceitou esse alvo como suficiente. Isso demonstra
uma limitação da nossa direção/avaliação, não uma incapacidade medida do modelo.
Preservar o snapshot e resultado anteriores como evidência histórica.

## Ajuste aplicado no produto

Skill `instagram-reel-v4` introduzida para a rodada; v5 agora vigente em novas capturas HTML. Mantém contratos criativo v4/v5,
crítica v2, schemas, biblioteca, renderer, API/Python, Temporal e controles existentes.
Não muda callbacks, campos de saída, número de chamadas nem regras financeiras.

- Cada unidade importante do pedido deve motivar um elemento, ação, resultado
  e passagem ao próximo foco, descritos nos campos já existentes da direção/plano.
- Desenhos, ícones e setas seguem disponíveis. Melhorar proporções, partes,
  conexões, máscara interna, sobreposição e movimento; não trocar todo pedido
  elaborado por tipografia e janela reposicionada.
- A crítica recebe a mesma skill e usa `motion_role`/`visual_development` para
  conferir as interações pedidas. Presença de ícones ou direção copiada no JSON
  não é prova. Falta de evidência permanece incerta, sem correção automática.
- Ações não são impostas por sílaba ou preposição, nem por um catálogo fixo.
  Desenho simples pode ter acabamento adulto. Os exemplos não são identidade.

v1/v2/v3 permanecem imutáveis e carregáveis por hash. A recaptura não promove uma
operação existente para v4. Não foi criada uma validação algorítmica que consiga
julgar qualidade semântica: a orientação chega ao crítico, mas seu acerto continua
dependendo das amostras e da avaliação humana.

## Fala e base temporal escolhida

O titular delegou a escolha. Nesta prova, coreografar os textos editoriais já
autorizados, preservando o áudio original. `motion_inputs.py` continua entregando
`transcript=None`: não afirmar escuta, ausência de fala ou sincronismo com palavras
faladas. Nenhum ASR, serviço ou aquisição paga de áudio foi adicionado.

Para um pedido que dependa de fala real, a transcrição/alinhamento será uma
dependência explícita; texto editorial não deve ser promovido a fala observada.
As instruções da v4 distinguem essas bases, sem alegar que o produto já suporta
essa ingestão no fluxo HTML.

## Nova prova revisável

[Direção](../evals/direcao-cafe-pausa-interacao-2026-11-10.json) e
[briefing](../evals/brief-cafe-pausa-interacao-2026-11-10.txt), com três momentos:
tempo desenha percurso/seta; café preenche uma xícara composta; pausa desacelera
o motivo e abre o convite. O vídeo e áudio seguem inteiros. Não simular tracking
da gota real, inventar fatos, adicionar música ou usar imagens pagas.

Novo teto de **US$ 3 autorizado em entrevista**: uma geração, render e uma crítica,
sem tentativas extras. Plano e resultados em
[ensaio de interação](../evals/plano-motion-interacao-2026-11-10.md).

## Verificação da implementação

100 testes Python e quatro Node aprovados, com transporte simulado e insumos
sintéticos. Captura, recaptura v2/v3/v4, igualdade do corpo contado, envio da skill
a geração/revisão/correção, integridade de bytes e exportação exercitados.
A execução final atingiu 100% de linhas e ramos no único módulo de produção
alterado, `motion_skills.py` (29 instruções e oito ramos). Ruff check/format passou.

Mypy inicial encontrou erro interno no typeshed local; a checagem direcionada
`--follow-imports=skip --no-incremental app/services/motion_skills.py` passou.
Isso não é tipagem global. Sem CI extenso, banco de testes ou alteração de schema.
A prova paga tem identidade nova e controles existentes; resultado registrado
no plano do ensaio, sem converter testes estruturais em aceite criativo.

## Resultado e ajuste técnico posterior

A tentativa inicial foi incompleta; a recuperação autorizada gerou os elementos,
mas recortou o vídeo por máscaras padrão em wrappers aninhados. O crítico detectou
o recorte, porém o check criativo e a issue não compartilharam o mesmo quadro.
O produto rejeitou corretamente esse parecer, sem nova tentativa automática.

A v5 explicita ambos os cuidados nas instruções compartilhadas. V4 permanece
imutável, assim como os contratos e guardas. A mudança de orientação ainda precisa
de uma futura prova real; a presente geração usou v4.

Uma variante de avaliação local desativa somente `clip-path` nos quatro wrappers
`tempo-video`, `cafe-video`, `pausa-video` e `pausa-xicara`. Não altera plano, JS,
textos, desenhos, curvas ou áudio. Renderiza pelo executor isolado existente,
sem chamada paga, e preserva a saída automática defeituosa e o estado failed.
Portanto a variante permite avaliar a proposta visual, mas não comprova sucesso
integral do produto. Custos, arquivos e evidências no plano do ensaio.
