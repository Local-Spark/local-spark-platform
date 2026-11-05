# Estudo: HyperFrames e motion design para o produto — 04/11/2026

**Correção do titular em 05/11/2026:** o cliente não escolhe imagens no acervo.
Pode enviar uma imagem e, para vídeo, envia o próprio vídeo; a edição do vídeo
não pressupõe uso do acervo. Onde abaixo aparecer acervo, trata-se de material
que o sistema pode ter disponível, e não de uma escolha feita pelo cliente.

O titular indicou os dois repositórios após rejeitar prévias de vídeo com pouca
qualidade de motion. Esta análise é documental; não instala nem executa código
externo, não gera peças e não faz chamadas pagas. Recomendações são hipóteses a
validar, não decisão de integração ou comprovação de qualidade.

## Os projetos e o que trazem

| Projeto | Papel | Oportunidade | Limite |
| --- | --- | --- | --- |
| [hyperframes-launches](https://github.com/heygen-com/hyperframes-launches) | Biblioteca de composições e fontes dos vídeos de lançamento da HeyGen, com HTML, cenas, storyboards e mídia. Não é o motor. | Estudar sequências, tipografia em movimento, transições, ritmo e projetos reconfiguráveis. | Os exemplos são peças de marcas existentes; não presumir autorização sobre marcas ou ativos. Git LFS é necessário para obter mídia. |
| [HyperFrames](https://github.com/heygen-com/hyperframes) | Motor separado, CLI e ferramentas para compor e renderizar vídeos de HTML; usa Chromium e FFmpeg. | Candidato para executar composições com vídeo, áudio e elementos animados, e gerar MP4s. O projeto oferece preview, lint e render. | Não decide a criação, não substitui modelo de IA, transcrição, alinhamento e revisão. Render local consome máquina. |
| [claude-motion-design](https://github.com/howseen-ai/claude-motion-design) | Skill para agente e exemplo de filme com HTML, Playwright e FFmpeg. | Método para briefing, direção por cena, beat map, tipografia animada, transições, som, prévias, QA e correções. | Não é um editor pronto integrado ao produto. O autor informa cinco iterações no exemplo; não há garantia de qualidade automática. |

O [código de HyperFrames e das composições originais da HeyGen](https://github.com/heygen-com/hyperframes-launches#license)
é publicado sob Apache 2.0 nos termos declarados pelos repositórios. Os ativos
de mídia, fontes, marcas e software de terceiros não recebem automaticamente
essa licença. O [código da skill Howseen](https://github.com/howseen-ai/claude-motion-design/blob/main/LICENSE)
é MIT; manter os avisos exigidos se houver reaproveitamento. Músicas, fontes,
imagens, vozes e marcas precisam de direitos próprios. Não copiar imagens,
textos, marca ou identidade de um perfil de referência; o modo de remake 1:1
do Howseen não é política autorizada do produto.

## Por que pode melhorar nosso resultado

No [último ensaio](../evals/ensaio-motion-valido-2026-11-04.md), a direção do
modelo foi limitada a um JSON de elementos e executada por um renderer
experimental simples, com adaptações manuais. O resultado não demonstra o que
um agente criando composição HTML e uma timeline expressiva conseguiria fazer.
Por outro lado, usar outra engine não garante peça boa: a direção, o material,
o modelo, a trilha, a revisão e a implementação da cena seguem determinantes.

O Howseen descreve escolhas de movimento por cena e sincronização com música,
além de rascunho e revisão de quadros e áudio. Essas técnicas respondem à falta
de ritmo, transições, efeitos e legendas apontada pelo titular. O exemplo de
[render](https://github.com/howseen-ai/claude-motion-design/blob/main/examples/howseen-launch/render.py)
configura 24 segundos, 60 fps e oito amostras por quadro: uma execução completa
pode exigir 11.520 capturas antes da codificação. Começar com draft de menor
resolução e sem múltiplas amostras, medir o tempo nesta máquina e só renderizar
uma versão final mais custosa após a direção estar satisfatória. Não tomar o
tempo ou custo do exemplo como previsão para nosso produto.

## Encaixe proposto no produto

1. Mensagem, Jev e contexto existentes entendem o pedido; o formato deve ser
   reconhecido explicitamente. Hoje Jev só oferece photo/story e devolve
   esclarecimento para vídeo e carrossel.
2. Um serviço de direção recebe pedido, fatos, kit, acervo autorizado, skill
   versionada e padrões gerais de referência. O modelo propõe narrativa,
   composição, trechos, cortes, tipografia, motion, áudio e legendas. Pode
   produzir uma composição executável compatível com HyperFrames, com versões e
   artefatos preservados. Essa etapa ainda não existe no produto.
3. Um adapter isolado executa a composição e renderiza preview, áudio e MP4.
   Em runtime, a execução assíncrona permanece sob Temporal; os serviços mantêm
   orçamento, identidade durável, audit/outbox e isolamento entre negócios. O
   HTML/JS criado por IA é código não confiável: processo isolado, sem segredos
   ou acesso livre à rede, com fontes permitidas e limites de recursos e tempo.
   Não adotar automaticamente a [orquestração Lambda do HyperFrames](https://hyperframes.heygen.com/deploy/aws-lambda),
   que usa Step Functions, como segundo gestor de workflow do produto.
4. Apresentar prévia privada, legenda e fontes para o cliente revisar. Para
   carrossel, criar contrato de coleção ordenada com um PNG e um MP4 por página,
   revisão da sequência e teste de aceitação e loop no Instagram. A prévia atual
   do produto representa um arquivo, não essa coleção.

Story em vídeo e Reel podem aproveitar a mesma base técnica com skills e
direção próprias. Preservar o teto decidido de 60 segundos por vídeo final, sem
confundi-lo com limite de entrada ou com o máximo aceito pelo Instagram. Para
fala real, incluir transcrição e alinhamento temporal confiável: o adapter atual
retorna texto, não tempos por palavra. O renderer antigo de oito segundos é
mudo e o caminho legado de novas prévias está bloqueado; não é edição inteligente.

O [cloud render da HeyGen](https://hyperframes.heygen.com/deploy/cloud)
documenta envio de mídia de 5 MB ou mais como asset referenciado por URL pública
sem assinatura. Não enviar conteúdo privado de cliente por esse caminho antes
de resolver adequadamente acesso e política; priorizar avaliação local. Mídia
licenciada, modelo, transcrição, computação, armazenamento, tentativas e tempo
de revisão entram no custo, mesmo que o renderizador local não cobre por chamada.

## Próximo ensaio direto recomendado

Fazer dois testes independentes no ambiente local existente, sem banco novo ou
fluxo completo: um Reel a partir de gravação autorizada e um carrossel de três
páginas com MP4 por página. Reutilizar as mensagens, kit, acervo e referências
da avaliação anterior quando pertinentes, e registrar entrada/saída do Jev,
modelo, skill, composição, timeline, trilha, direitos, duração, custo e tempo.
Usar um agente que crie composição para HyperFrames orientado pelas técnicas
adaptadas da Howseen, sem importar dados ou marcas dos exemplos. Começar com
draft pequeno, revisar visual e áudio, depois renderizar o que valer a pena.

Se for comparado **só o renderizador**, manter direção, timeline, mídia e áudio
iguais e mudar apenas o motor. Um teste com novo método de direção, modelo ou
animação responde à pergunta mais ampla de qualidade, mas não isola o efeito do
motor. A gravação fictícia anterior é ilustrativa, não tem fala revisada e tem
resolução baixa; serve como comparação limitada, não como prova de edição da
fala de cliente. Ao testar com voz real, exigir material autorizado e medir
transcrição e sincronização.

Antes de chamadas pagas, apresentar modelos, número de operações e orçamento
específico. A autorização anterior de US$ 0,50 era de outra rodada e não é
renovada automaticamente. Não instalar pacotes, enviar mídia ou acionar cloud
apenas por esta pesquisa. Avaliar qualidade visual, ritmo, edição, identidade,
legenda, áudio, direitos, legibilidade e custo por peça aceita após revisão do
titular; teste isolado não comprova integração ou publicação.
