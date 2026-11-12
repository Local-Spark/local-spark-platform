# Motion — etapa 4: espaço, integração e coreografia

Data: 11/11/2026. Entrega técnica de orientação e exemplo coordenado; não houve
nova peça, imagem, renderização ou avaliação criativa. O aceite visual continua
no portão da etapa 7 e depende de autorização e orçamento próprios.

## Decisão

O runtime `movement-v3` já suporta tracks coordenadas e seek determinístico.
Para não criar um motor paralelo, a skill HTML `instagram-reel-v13` acrescenta o
exemplo opcional `makeGroundedPassage`, transmitido dentro do contexto existente.
O exemplo coordena fundo, wrapper da gravação, objeto, sombra e texto em
preparação, passagem, revelação/acento, repouso e retorno. Usa as APIs do runtime
existente e devolve as tracks para confrontar seus tempos e estados com o plano.
Não acessa a fonte, manipula áudio ou altera o tempo do vídeo; o seek absoluto
continua sendo responsabilidade do código da peça. Não é biblioteca instalada,
peça pronta nem obrigação de usar objeto, borda, alternância ou esse roteiro.

A direção continua determinando apoio, luz, contraste, escala e espaço a partir do
kit e dos pixels efetivamente disponíveis. A origem do objeto/sombra é escolhida
conforme o ponto de apoio do recorte; o exemplo não deduz a geometria pela imagem.
Não simula rotação revelando faces ausentes, não faz tracking/OCR/recorte de
pessoa e não garante proteção automática de mãos ou produto. Esses limites não
são apresentados como capacidades implementadas.

Os snapshots v1–v12 permanecem preservados; v13 é selecionada somente em novas
capturas HTML. Seu SHA-256 é
`6d5ae9e0478756b1ef006f3babf6591c6c0bbe243d8cc6aee4a2d8f5dd754822`.
Sem mudança no runtime, executor, bibliotecas, banco, Temporal ou orçamento.

## Evidências

O teste Node extrai o código literalmente da skill e o executa com o runtime v3
e DOM sintético. Verifica deslocamento relativo do fundo, chegada do objeto com
sombra coordenada, leitura/repouso, remoção de objeto/sombra/texto no retorno,
retorno da gravação com tratamento preservado e busca repetida/reversa no mesmo
instante. Também usa fixture de página autorizada para verificar que o mecanismo
não depende de xícara, borda, órbita ou máscara. Testes com parâmetros inválidos
verificam falha antes de mutar os nós. O teste não usa navegador ou mídia real.

O exportador offline usou o montador real em
`.local/exports/motion-qualidade-etapa4-final-20261111/`: v13, contrato v4, seis
quadros da gravação e cinco referências. Fonte, kit, áudio e transcrição são
iguais à base; a entrada está na etapa de plano e não contém nova resposta de
implementação nem preview da xícara anterior. Manifesto SHA-256:
`d1c715ab62fabeb1465dc86215d1393b3a24d8aa32ae4cf2f9bf685327de6772`.
Sua presença no contexto não prova que o modelo seguirá ou executará o exemplo.

Passaram 14 testes Node, 133 testes Python dirigidos, Ruff e Mypy do loader;
CI integral e cobertura global não foram executados. Nenhum banco ou serviço foi
alterado; os cinco serviços anteriormente interrompidos não foram iniciados,
mas seu estado não foi consultado.

## Limitações e próximo portão

Não se pode concluir por esses testes que sombras, enquadramento, luz, ritmo ou
contraste estejam visualmente corretos numa peça. Também não foram verificados
os problemas históricos em 3,967 s e 8,767 s numa nova execução. A xícara
conceitual anterior permanece sem bytes disponíveis na busca local da etapa 3.
O produto não tem recuperação parcial automática de plano que exige revisão.
Esses pontos permanecem para a comparação futura e suas autorizações próprias.
A etapa 5 aguarda OK do titular.
