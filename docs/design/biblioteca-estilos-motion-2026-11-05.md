# Proposta: biblioteca própria de estilos de motion — 05/11/2026

O titular prefere uma biblioteca interna de estilos de motion, semelhante ao
papel do kit, em que o sistema escolha o estilo mais apropriado ao negócio,
sem acrescentar ao cliente uma escolha que ele não precisa fazer. A proposta
está em estudo: ainda não há
biblioteca, seleção, preferência persistida ou integração implementada.

Na entrevista posterior de 05/11, o titular definiu que o sistema escolhe o
estilo a cada pedido, conforme objetivo, material e referências, preservando a
identidade do kit. A v0 guarda snapshots por peça; não fixa preferência de estilo
por negócio a partir das peças aprovadas.

Para pesquisa, a skill de Felipe Borges foi instalada no Codex e sua galeria
pública foi aberta em localhost temporário, com 21 prévias. Ela é fonte externa
de estudo, não a
biblioteca integrada do produto: exemplos em sua maioria horizontais exigem
adaptação para formatos verticais e verificação de direitos de cada ativo.

## Experiência proposta

Cada estilo pode ter nome, descrição curta e prévia animada que mostre ritmo,
tipografia, comportamento de imagens e transições para a equipe e o sistema.
O sistema deve escolher o estilo com base em pedido, negócio, kit, material
enviado e referências autorizadas, sem exigir decisão adicional do cliente.
O cliente segue revisando a peça e pode pedir alterações por mensagem natural;
a integração dessa jornada aos novos formatos permanece pendente. No carrossel,
ajustar uma página preserva as demais, pedindo confirmação antes de mudá-las
quando necessário e nova aprovação da sequência resultante. Escolha de estilo
não é escolha de imagens no acervo.

O **kit** continua fornecendo identidade do negócio: cores, fontes e demais
elementos autorizados. A **skill de formato** orienta Reel, story ou carrossel;
o **estilo de motion** define linguagem de movimento; a IA cria roteiro,
composição, cortes e movimentos concretos para o pedido. Padrões de referências
inspiram características gerais e não autorizam copiar a identidade de terceiros.
O estilo não deve substituir fatos confirmados, áudio original ou identidade.

Exemplos possíveis para protótipos, sujeitos à avaliação do titular:

- **Editorial acolhedor:** movimentos suaves, fotos em destaque e tipografia
  elegante. Pode servir a negócios que desejam uma apresentação tranquila.
- **Tipografia cinética:** palavras e formas acompanham falas ou batidas, com
  movimentos mais marcados e boa legibilidade em tela pequena.
- **Recortes dinâmicos:** imagens em camadas, máscaras e transições mais
  visíveis; adequado quando houver material visual suficiente.

São hipóteses, não estilos já produzidos nem uma regra que determine o estilo
somente pelo segmento do negócio. Para comparar, criar prévias com o mesmo
pedido, kit, áudio e material, variando o estilo; registrar IA, inputs, outputs,
versões, tempo, custos e preferências. A renderização de um MP4 curto por
estilo pode ser testada pelo procedimento rápido, sem banco novo.

## Integração futura

Um catálogo versionado pode guardar identificador, versão, descrição,
restrições e formatos suportados, código/instruções, hash e prévia licenciada.
Cada geração deve registrar a versão escolhida, dados usados e razão da escolha
automática. Preferência durável por negócio fica fora desta v0; uma evolução
nesse sentido exigirá decisão própria, escopo do negócio, RLS e auditoria.
Peças precisam conservar o snapshot do
estilo e kit efetivamente usados; alteração posterior não deve reescrever o
histórico. Os contratos e a revisão por formato, especialmente carrossel com
vários arquivos, ainda precisam de implementação e testes próprios.

Prévias, fontes, músicas, imagens, código e demais elementos exigem direitos
compatíveis. O uso de HyperFrames ou das skills estudadas não garante que as
mídias ou marcas dos exemplos possam ser redistribuídas. Custo e limite de
duração dependem de render, modelo, arquivos e refações; testar qualidade e
tempo antes de oferecer uma biblioteca como recurso concluído do produto.
