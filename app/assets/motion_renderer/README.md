# Compilação declarativa de motion

Estes módulos são uma fatia interna, ainda sem ligação ao fluxo do produto. O
serviço deve validar e adaptar `MotionDirection`, autorizar e conferir os hashes
de mídias e fontes e selecionar um perfil confiável antes de chamar
`compileScene(scene, profile, registry)`. A cena intermediária não é um
contrato público nem deve receber JSON bruto de um modelo diretamente.

O perfil aceita `width_px`, `height_px` e `fps`. Esta versão limita a 30 fps,
720 × 1280 ou 1080 × 1920 para Reel/story e 1080 × 1350 para página de
carrossel. A duração do carrossel é de 5 a 8 segundos; a dos demais formatos é
de até 60 segundos. O catálogo de perfis é controle interno, não escolha do
cliente ou do modelo.

Cada camada tem UUID, intervalo `[start_ms, end_ms)` e ao menos dois keyframes
com tempos inicial zero e final igual à duração. Camadas posteriores ficam por
cima. A geometria é relativa ao quadro: x/y são o canto superior esquerdo;
largura e altura são frações do quadro; escala e rotação usam o centro da caixa;
o recorte é relativo à caixa. Keyframes têm todos os valores explícitos.
Transições de entrada e saída são `cut` instantâneo ou `fade` linear, com
durações inteiras cuja soma não ultrapassa a duração da camada. O envelope de
fade usa um wrapper separado e sua opacidade multiplica a opacidade animada da
camada, inclusive quando posição, recorte ou outros valores variam.
Imagens e vídeos usam UUID autorizado, `cover`/`contain` e foco; vídeos aceitam
apenas recortes sem alteração de velocidade. Texto usa fonte do kit identificada
por ID e é atribuído ao DOM com `textContent`, sem HTML ou CSS fornecido por
modelo. Valores fora das capacidades e campos não reconhecidos são rejeitados.

`mountScene` recebe apenas o resultado da compilação e um callback de seek
fornecido pelo driver confiável. Os caminhos `/media/<uuid>` são identificadores
locais, não uma implementação de serviço de arquivos. O chamador deverá
garantir fontes e imagens carregadas, servir apenas arquivos autorizados,
verificar seeks e timestamps, e isolar navegador e encoder sem rede nem
credenciais, com limites de recursos. Os testes atuais usam DOM simulado.

Não há ainda driver, codificação de vídeo, mixagem de áudio, persistência,
workflow, publicação ou garantia de qualidade criativa. Essas ausências não
devem ser interpretadas como suporte implícito nem ativar renderização.
