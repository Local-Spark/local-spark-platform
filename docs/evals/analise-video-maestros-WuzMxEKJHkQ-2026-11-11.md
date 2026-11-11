# Análise da referência Maestros da IA — WuzMxEKJHkQ

Atualização posterior à comparação: a peça foi produzida, mas seu acabamento não
atendeu ao titular. A reanálise dos seis pontos, incluindo gaps concretos do fluxo,
está em [Direção e gaps de qualidade](../design/motion-qualidade-direcao-e-gaps-2026-11-11.md).
O texto abaixo preserva o diagnóstico histórico anterior à comparação; referências
a ausência de imagem/MP4 ou construção indivisível descrevem aquele momento.


Data: 11/11/2026. Escopo: analisar o vídeo indicado pelo titular, relacionar suas
técnicas ao produto e propor correções. Não implementa features nem autoriza gasto.

## Conclusão

O caminho técnico é compatível com nossa arquitetura: composição por código,
tempo explícito, navegador e FFmpeg. O ganho mais relevante está em organizar a
produção em partes verificáveis, integrar a gravação ao cenário e revisar o
resultado durante a construção. Adicionar bibliotecas ou mudar o modelo sem
resolver a geração indivisível não trata a fragilidade encontrada nas três falhas.

Há um caminho concreto de correção, mas a causa raiz da interrupção reportada
pelo provedor ainda não está comprovada. Não confundir mitigação estrutural com
garantia de sucesso de uma próxima chamada.

## Material e método

Fonte: [vídeo publicado por Maestros da IA](https://www.youtube.com/watch?v=WuzMxEKJHkQ).
Título publicado: “CLAUDE FABLE 5.2 Produziu Este Vídeo Para Te Ensinar Como a IA Edita Vídeos”.

Baixados MP4 1920×1080/30 fps com áudio original português e legendas automáticas
pt-orig. Duração medida do vídeo: 455,700 s; áudio: 455,738 s. Arquivo: 93.195.674
bytes. SHA-256: `4f838b0801f3caa7cd32ccc2390f6b41933228b84baf635ae555b38a9124d12f`.

Leitura integral das legendas normalizadas, descrição e capítulos; inspeção visual
de 114 quadros distribuídos a cada quatro segundos e de seis quadros adicionais
em resolução integral nos instantes 02:50, 03:08, 03:22, 05:42, 06:02 e 06:18.
Não equivale a assistir continuamente a cada quadro ou auditar os arquivos-fonte
do autor. Não foram medidas curvas de movimento nem qualidade perceptiva do áudio.
Os rótulos das folhas de contato são aproximados; os seis detalhes usam busca
explícita pelo instante. Legendas automáticas contêm erros em nomes de ferramentas.

Evidências locais, ignoradas pelo Git:
`.local/research/youtube-WuzMxEKJHkQ-20261111/` — `source.mp4`, `manifest.json`,
legendas originais, `captions-normalized.json`, `transcript-working.txt`,
`frames/`, `sheets/01.jpg` a `10.jpg` e `details/`.
A transcrição integral é material de trabalho local; este documento resume e
analisa. Nenhum trecho foi incorporado ao acervo comercial ou ao kit do cliente.

## O que “um prompt” significa nesta referência

Em [06:02](https://www.youtube.com/watch?v=WuzMxEKJHkQ&t=362s), o próprio quadro
identifica o pedido como uma versão estruturada do original. O pedido inclui
pesquisa, roteiro, narração, animação, som, edição e renderização. Também dispensa
limites de custo de tokens e tempo. Essa condição difere do nosso teste controlado.

Em [06:18](https://www.youtube.com/watch?v=WuzMxEKJHkQ&t=378s), o autor declara
3h48 de produção, 89 arquivos de código, 7.874 linhas, 91 cenas, 13.671 quadros,
312 deixas de som e 3.196 quadros conferidos. São números apresentados pelo autor,
não uma auditoria independente. A descrição confirma parte deles. O MP4 medido
é compatível com 13.671 quadros a 30 fps, mas isso não comprova os demais números.

O vídeo também informa que avatar, voz, contas de ferramentas e 419 linhas do
motor de cinema já existiam. A afirmação de nenhuma correção humana não significa
ausência de correções automáticas: há uma seção mostrando revisão e conserto.
Não há logs integrais, número de chamadas de modelo, custo total, código completo
ou comparação controlada entre modelos no material público consultado.

Portanto, um pedido humano pode iniciar muitas ações e respostas intermediárias.
Não há evidência de que os 89 arquivos tenham sido emitidos em uma única resposta.
O nome do modelo é tratado aqui como atribuição da publicação, não como prova de
superioridade ou requisito para reproduzir as técnicas.

## Etapas e ferramentas demonstradas

| Trecho | O que aparece e como funciona | O que aproveitar no produto |
|---|---|---|
| [00:38–01:41](https://www.youtube.com/watch?v=WuzMxEKJHkQ&t=38s) | Quadros, posições inicial/final e curvas de aceleração. As representações visuais explicam a fala: pilha, sequência e trajetória. | Os movimentos precisam expressar uma ideia e ter preparação, ação e repouso. Não basta animar a entrada das letras. |
| [01:42–02:35](https://www.youtube.com/watch?v=WuzMxEKJHkQ&t=102s) | Remotion organiza vídeo com React; HyperFrames trabalha com HTML; GSAP controla animações; Three.js apresenta geometria 3D. Chrome e FFmpeg produzem o arquivo. | Já temos navegador, FFmpeg e movimento por tempo. Avaliar lacunas específicas antes de substituir o executor. |
| [02:38–02:54](https://www.youtube.com/watch?v=WuzMxEKJHkQ&t=158s) | Câmera, luz, sombra e camadas separadas. O detalhe de 02:50 mostra cinco camadas, incluindo a imagem da apresentadora. | Usar profundidade e composição entre planos. A pessoa continua uma imagem recortada dentro do espaço; não foi transformada em um corpo 3D completo. |
| [02:56–03:12](https://www.youtube.com/watch?v=WuzMxEKJHkQ&t=176s) | Forma de onda e palavras com início/fim. O rodapé identifica alinhamento forçado. | Temos ASR com tempos; falta qualificar precisão e considerar realinhamento quando o texto for corrigido. O provedor específico desse alinhamento não está identificado no trecho. |
| [03:13–03:23](https://www.youtube.com/watch?v=WuzMxEKJHkQ&t=193s) | EDL: lista de decisões de edição. Há um exemplo didático de corte e, depois, a lista declarada da narração real, com seleção de tomadas e ajuste de respiros. | Para futuros cortes, armazenar intervalos de origem e sua posição na montagem. Timestamps sozinhos não escolhem bons cortes nem preservam o sentido. |
| [03:24–03:39](https://www.youtube.com/watch?v=WuzMxEKJHkQ&t=204s) | Apple Vision encontra o rosto e separa a pessoa do fundo. Uma máscara permite colocar texto atrás da pessoa. | Reenquadramento protegido e composição em camadas podem integrar melhor a gravação. Máscara de pessoa é diferente de arredondar a borda do vídeo. |
| [03:40–03:59](https://www.youtube.com/watch?v=WuzMxEKJHkQ&t=220s) | Etiqueta acompanha uma prancha; depois texto acompanha a perspectiva do chão. Rodapés atribuem rastreamento a Apple Vision e plano a OpenCV. | Posicionar gráficos relativamente a objetos reais. Exige rastreamento confiável, não apenas coordenadas escolhidas pelo modelo. |
| [04:01–04:12](https://www.youtube.com/watch?v=WuzMxEKJHkQ&t=241s) | OCR localiza palavras em um print e permite destacar regiões específicas. | Útil para tutoriais, ofertas e demonstrações de tela; não é prioridade para o Reel Café Pausa. |
| [04:13–04:42](https://www.youtube.com/watch?v=WuzMxEKJHkQ&t=253s) | Pesquisa de vídeos no Pexels por assunto, seleção e harmonização de cor; prints e vídeos aparecem em planos com perspectiva. | Primeiro selecionar do acervo existente. Banco externo pode complementar quando necessário, mantendo origem e sem representar material genérico como produto real do cliente. |
| [04:43–05:24](https://www.youtube.com/watch?v=WuzMxEKJHkQ&t=283s) | ElevenLabs para voz, efeitos e música; HeyGen para avatar. A trilha baixa durante a fala; há medição de loudness. | Preservar a voz original. Podemos melhorar mixagem e efeitos disponíveis sem introduzir avatar ou clonagem. O valor de LUFS mostrado não é uma regra universal para plataformas. |
| [05:25–05:46](https://www.youtube.com/watch?v=WuzMxEKJHkQ&t=325s) | Folhas de contato, distância de texto ao rosto, transcrição do áudio final comparada ao roteiro e correção de um número ausente. | Verificar texto, enquadramento, continuidade e áudio com evidências; corrigir somente a parte defeituosa. |
| [05:47–06:35](https://www.youtube.com/watch?v=WuzMxEKJHkQ&t=347s) | Recursos prévios, pedido estruturado e números da produção. | Planejar limites e recuperação; não importar a instrução de ignorar custos. |
| [06:36–fim](https://www.youtube.com/watch?v=WuzMxEKJHkQ&t=396s) | Exemplos de aplicações, glossário e divulgação da comunidade. | Os exemplos de vídeos longos são possibilidades demonstradas, não capacidade já entregue pelo nosso produto. |

O catálogo visual de bibliotecas em 01:48 inclui mais nomes que as demonstrações
principais. Não prova que todas foram necessárias ou usadas em produção. Não há
justificativa para instalar o catálogo inteiro.

## Por que o acabamento parece mais integrado

Esta é uma avaliação visual dos quadros e da sequência, não uma medição comparativa
com o nosso MP4:

- **Uma ação explica a fala.** O conceito de quadros vira uma sequência de imagens;
  transcrição vira palavras ancoradas na onda; rastreamento vira uma etiqueta presa
  ao objeto. O objeto tem função narrativa, em vez de ser decoração ao lado do texto.
- **A hierarquia muda.** Apresentadora, demonstração em tela inteira e objetos
  alternam protagonismo. A gravação não precisa permanecer pequena ao lado de tudo.
- **O fundo é cenário.** Grades, iluminação, superfícies, textura e mudança entre
  campos claros/escuros sustentam a cena. Não é necessário trocar cor em toda palavra.
- **Há relação espacial.** Oclusão, sombra, planos e enquadramento aproximam elementos
  que de outro modo pareceriam colados por cima do vídeo.
- **Existe consistência.** Tipografia, contraste e linguagem gráfica unem cenas
  diferentes. Podemos absorver esses princípios usando o kit Café Pausa, sem copiar
  a paleta, as fontes ou os grafismos da referência.
- **O ritmo tem pausas.** Ênfases pontuais e momentos de leitura permitem perceber
  a intenção. Efeito independente em cada palavra pode voltar a produzir um aspecto
  infantil e dispersar a atenção.

## Ferramentas: entradas, saídas e limites relevantes

**Remotion:** componentes React e número do quadro produzem a imagem daquele instante.
**HyperFrames:** composição web e busca temporal produzem capturas; seu engine documenta
controle determinístico de quadros e integração com FFmpeg. Ambos ajudam a executar;
não escolhem, por si, uma boa direção visual.
[Remotion](https://www.remotion.dev/docs/idea),
[HyperFrames](https://hyperframes.app/docs/5-packages/engine).

**GSAP:** transforma propriedades ao longo de uma timeline; `seek` posiciona o tempo.
O equivalente funcional necessário no produto é uma animação reproduzível para
qualquer instante solicitado. Não depende de o navegador tocar em tempo real.
[Documentação de seek](https://gsap.com/docs/v3/GSAP/Timeline/seek()/).

**Three.js:** cena, câmera e renderer permitem representar geometria no navegador.
Para uma xícara volumétrica seriam necessários geometria, materiais, iluminação e
animação apropriados. A biblioteca não converte automaticamente uma foto em um
objeto completo. Sua adoção exige qualificar WebGL e recursos no sandbox existente.
[Cena Three.js](https://threejs.org/manual/pages/creating-a-scene.html).

**Whisper/faster-whisper:** áudio produz texto e estimativas de tempo por palavra.
**Alinhamento forçado:** áudio mais texto conhecido produzem posições temporais
associadas a esse texto. É útil depois da revisão da transcrição; ainda exige
verificação de qualidade. A documentação ElevenLabs confirma essa capacidade,
mas não comprova que seja o serviço usado no trecho do vídeo.
[faster-whisper](https://github.com/SYSTRAN/faster-whisper/blob/master/README.md),
[alinhamento forçado](https://elevenlabs.io/docs/overview/capabilities/forced-alignment).

**Apple Vision:** imagens produzem observações como caixas de rosto/texto e máscaras.
No produto precisamos do resultado dessa análise, não necessariamente desse SDK.
É um framework do ecossistema Apple; não assumir disponibilidade no worker Linux.
**OpenCV:** correspondências entre imagens podem produzir uma homografia para
projetar texto sobre um plano. Isso não equivale a reconstruir toda a cena em 3D.
[Vision](https://developer.apple.com/documentation/vision.md),
[homografia](https://docs.opencv.org/5.0/tutorials/features/homography/homography.html).

**Pexels:** consulta por assunto retorna opções de mídia com metadados. Seleção,
compatibilidade visual e origem continuam sendo responsabilidades do produto.
[API oficial](https://www.pexels.com/api/documentation/).

**ElevenLabs e HeyGen:** na referência fornecem som e apresentadora sintética,
respectivamente. Isso resolve a produção daquele narrador, não o problema de editar
a gravação original do nosso cliente. Geração de efeitos/música é uma capacidade
separada e paga, dispensável para corrigir o bloqueio atual.
[Efeitos](https://elevenlabs.io/docs/overview/capabilities/sound-effects),
[música](https://elevenlabs.io/docs/overview/capabilities/music).

**FFmpeg:** combina quadros e áudio. Pode também reduzir a trilha em função da voz
com `sidechaincompress` e medir/normalizar loudness com filtros próprios. Esses
recursos precisam de parâmetros e verificação; a mixagem atual não os ativa.
[Filtros oficiais](https://ffmpeg.org/ffmpeg-filters.html).

## Comparação com o produto inspecionado

| Capacidade | Estado encontrado | Consequência |
|---|---|---|
| Render por código e tempo | HTML/JS, Chromium isolado, `window.seek(ms)`, FFmpeg e assets locais | A base é compatível com a abordagem demonstrada. Não foi o render que interrompeu as três tentativas. |
| Direção antes da construção | Já separada em serviços e contratos | A correção proposta é decompor a construção recuperável; não refazer a etapa de direção já existente. |
| Moldura, fundo narrativo, objeto realista, fala alinhada | Contratos, skills e helpers implementados | Implementação não comprova qualidade; a nova peça conjunta ainda não chegou a ser produzida. |
| Tempos de fala | `motion_local_speech_worker.py`: faster-whisper local, palavras e confiança, até 60 s | Já funcionou com 30 palavras na comparação. Não é um editor de gravação longa nem alinhador separado de texto revisado. |
| Objeto realista | Contrato de imagem/recorte e movimento em camadas | Nenhuma imagem realista foi gerada nas três tentativas interrompidas. Não existe evidência de uma nova xícara pronta. |
| Percepção espacial | Não identificados no fluxo motion contratos de rosto, máscara de pessoa, OCR ou rastreamento de objeto | O modelo hoje não recebe essas medições estruturadas para integrar a gravação. |
| Som | `audio.cjs`: recorte, atraso, ganho constante por evento e soma | Sem ducking/envelope/loudness no fluxo HTML inspecionado; não declarar ausência em todo e qualquer outro fluxo do repositório. |
| Revisão | Critérios criativos/temporais e amostragem com teto de 20 quadros | É uma base útil. Não cobre automaticamente todos os frames nem confere o áudio final contra a transcrição. |
| Recuperação | Composição ainda retorna plano e código no mesmo JSON | Um corte em `scene_init` invalida a composição inteira, mesmo quando o plano chegou completo. |

Código consultado: `app/adapters/motion_ai.py`,
`app/adapters/motion_local_speech_worker.py`, `app/services/motion_orchestrator.py`,
`app/services/motion_visual_direction.py`, `app/services/motion_review.py`,
`app/services/motion_temporal.py`, `app/assets/motion_html_renderer/runner.cjs`,
`audio.cjs` e bibliotecas de movimento/elementos existentes.

## Correção recomendada antes de outra comparação

1. **Separar construção e recuperação por artefato.** Reutilizar a direção já
   aprovada/preparada; obter e validar um plano limitado; construir a execução
   usando esse plano; persistir cada resultado completo. Uma falha deve permitir
   retomar a etapa autorizada sem recomeçar tudo. Usar Temporal, operações,
   auditoria, storage e ledger existentes. Não completar JSON truncado na mão.
2. **Fornecer infraestrutura pronta ao modelo.** Seek de mídia, montagem da cena e
   helpers de moldura/fundo/objeto devem ser reutilizáveis. O modelo escolhe
   composição, parâmetros e movimentos específicos. Evitar duas descrições
   independentes do mesmo movimento que possam divergir entre plano e código.
3. **Corrigir a serialização e selecionar o contexto.** Separar ordenação canônica
   para hash da ordem deliberada do schema enviado. Remover repetição e incluir
   bibliotecas relevantes, preservando kit, fonte e referências. Só trocar a ordem
   ou compactar nomes de campos não é solução comprovada.
4. **Verificar recuperação offline e conclusão real separadamente.** Testar
   persistência, retomada, igualdade plano/execução e limites com fixtures curtas.
   Investigar a discrepância de tokens por IDs/metadados. Uma prova de API futura
   requer autorização própria; não promete custo menor ou sucesso garantido.
5. **Qualificar visualmente a peça.** Conferir estados e transições críticos antes
   da renderização final, com orçamento definido para eventuais correções. Comparar
   contra a peça anterior usando a mesma fala, kit, duração e critérios observáveis.

Detalhes da falha e replay offline já registrados em
`docs/evals/diagnostico-interrupcao-motion-2026-11-11.md`.
Não há quarta tentativa paga autorizada. As três anteriores interromperam antes
de imagem, MP4 e crítica. A estimativa acumulada é US$ 0,998378; reservas US$ 2,80.

## Aplicação visual proposta para Café Pausa

Proposta de direção, ainda sem geração ou render:

| Momento da fala | Gravação | Fundo e objeto | Verificação |
|---|---|---|---|
| Convite inicial | Cliente em destaque, aproximação suave e moldura deliberada | Ambiente do kit prepara a abertura | Rosto preservado; tratamento visível sem distração |
| Referência ao cheiro/café | Gravação dá lugar a uma cena de motion com áudio contínuo | Xícara fotográfica recortada, superfície e sombra; vapor discreto associado ao assunto | Aparência adulta, recorte limpo, objeto assentado e leitura clara |
| Ideia de pausa/calma | Movimento desacelera e abre espaço | Campo de luz/cor muda junto da composição; objeto repousa | Fundo participa da ação; existe pausa perceptível |
| Convite final | Retorno à gravação por transição que compartilha a forma ou o enquadramento | Elementos cedem espaço à mensagem e ao kit | Retorno intencional, sem mera troca de lado |

As fronteiras devem seguir os tempos reais da fala preservada. Esta tabela não
autoriza reordenar ou cortar a voz. Não é necessário acionar um efeito por palavra;
palavras-chave podem disparar ações conectadas dentro da mesma frase.

Para a xícara, escolher conscientemente entre três capacidades: fotografia recortada
com profundidade aparente (mais próxima do contrato atual), vídeo real do objeto
(movimento físico registrado) ou modelo 3D (mudança real de ponto de vista). Uma
foto pode entrar, assentar, aproximar e participar de uma cena convincente; não
permite revelar seu verso com uma rotação. Nenhuma dessas opções foi produzida
nesta análise.

Depois da confiabilidade, priorizar revisão visual da moldura/fundo/objeto e
proteção do rosto. Recorte da pessoa e tracking entram quando a direção precisar
deles, com qualidade e custo local medidos. Ducking/normalização complementam o
acabamento sonoro. OCR, banco externo, 3D completo e edição longa ficam em fatias
posteriores conforme necessidade comprovada; não são pré-requisitos para entregar
um bom Reel de negócios.

## Validação e limites desta entrega

Somente pesquisa, download, extração de quadros, leitura de código e documentação.
Sem alteração de código de produção, nova dependência, container iniciado, geração
paga, asset de cliente ou renderização de peça. Cinco serviços permanecem parados.
Não executado CI: não há mudança executável nesta entrega. Verificados existência
dos artefatos, metadados, hashes e caminhos da documentação. Próximo trabalho é
implementar a recuperação descrita e qualificá-la; não está concluído por este estudo.
