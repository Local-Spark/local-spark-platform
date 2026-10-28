# Avaliação: HyperFrames, Remotion, VoiceStudio e Superpowers

Data: 27/10/2026. Análise preliminar para o Meu Braço Direito, não uma decisão
de contratação, instalação ou implantação. Confirmar versões, dependências,
licenças e preços antes de adoção comercial. O usuário confirmou que o
VoiceStudio é o repositório `debpalash/VoiceStudio`; o nome Superpowers pode
referir-se a outros repositórios.

## Vídeo e motion

O [HyperFrames da HeyGen](https://github.com/heygen-com/hyperframes) transforma
composições HTML/CSS/JavaScript em vídeo. É candidato para animar fotos e vídeos
reais recebidos do cliente, adicionando legendas, transições e CTA. A licença do
projeto é Apache-2.0 e o projeto anuncia ausência de cobrança por render, mas
Chrome, FFmpeg, CPU/memória, armazenamento e operação têm custo. Não é gerador
de cenas por IA e não garante qualidade criativa por si só.

O [Remotion](https://www.remotion.pro/license) oferece composições programáticas
em React. Sua licença é própria, não uma licença open source padrão. A página
do fornecedor informa uso gratuito para indivíduos e empresas elegíveis de até
três pessoas; para as entidades que precisam de licença empresarial, anuncia
automação a US$ 0,01 por render e mínimo de US$ 100/mês. Confirmar critérios,
contrato e versão aplicáveis antes de uma decisão; infraestrutura é adicional.

Não integrar os dois neste momento. Para a fase de vídeo com material real,
propor POC isolada com o mesmo vídeo fictício vertical de 15 segundos, kit,
legendas e CTA: avaliar qualidade no celular, tempo, CPU/memória, recursos,
licença, retrabalho e custo por peça aprovada. Priorizar HyperFrames como
candidato; comparar Remotion se houver benefício a validar. Sem benchmark não
afirmar economia nem qualidade comercial.

A [documentação de segurança do HyperFrames](https://github.com/heygen-com/hyperframes/blob/main/packages/core/README.md)
alerta para código e recursos externos em composições. Na hipótese de adoção,
usar templates confiáveis e versionados com dados validados e renderização
isolada, sem executar HTML/JS arbitrário gerado por IA com segredos e acesso
livre a dados de clientes. Limitar rede, memória, CPU, tempo e armazenamento.

## Voz

O **VoiceStudio** confirmado é o
[debpalash/VoiceStudio](https://github.com/debpalash/VoiceStudio/blob/main/LICENSE-NOTICE.md).
Sua aplicação usa AGPL-3.0 e oferece condições comerciais; licenças e custos dos
modelos são separados. Os pesos padrão [k2-fsa/OmniVoice](https://huggingface.co/k2-fsa/OmniVoice)
estão identificados como CC-BY-NC: não presumir permissão de uso comercial.

Manter clonagem de voz após o primeiro piloto. Exige direito e consentimento
específicos, retirada, proteção da voz, qualidade em português, licença de cada
modelo e comparação de custo de infraestrutura com fornecedores por API.

## Desenvolvimento

O [obra/superpowers](https://github.com/obra/superpowers) é um conjunto de
skills e práticas para agentes de desenvolvimento, sob licença MIT. Pode ajudar
em planejamento, diagnóstico e revisão, mas não cria automaticamente conteúdo
para os clientes. Avaliar skills específicas antes de instalar; preservar as
instruções do usuário, SDD, política de testes e revisão existentes. Não é
dependência do runtime do produto.

Versão anterior à reconciliação: [snapshot integral de 28/10/2026](../history/2026-10-28-pre-documentation-reconciliation/design/video-tool-candidates-2026-10-27.md).
