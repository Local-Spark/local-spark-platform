# Ensaio local: PhotoCraft e FilmCraft

Data: 26/10/2026. Objetivo: testar se editores locais automatizáveis são uma
opção para melhorar a execução visual e controlar o custo do plano de entrada.
Não é aprovação comercial nem benchmark de AWS. As fotos são amostras públicas do
perfil indicado pelo fundador, usadas apenas para comparação privada local. Não
foram adicionadas ao Git, enviadas a provedores de IA nem autorizadas pela
proprietária para produção/publicação. Texto e direção foram escolhidos
manualmente para o ensaio; **nenhuma IA visual foi chamada**.

## Reprodução e artefatos privados

- Referência: `docs/evals/priscila-public-reference-2026-10-26.md`.
- PhotoCraft CLI oficial v0.16.0: abriu o frame da torta cookie, aplicou
  `image.adjustments.vibrance`, criou um retângulo sólido e duas camadas de
  texto e exportou PNG. A arte pronta do croissant não recebeu outro título:
  reconhecer arte finalizada e preservá-la é uma decisão editorial que ainda
  precisa ser automatizada/avaliada.
- FilmCraft CLI oficial v0.13.0: importou o frame e a arte resultante, colocou
  quatro segundos de cada numa timeline vertical 720×1280 a 24 fps e exportou
  MP4 H.264 de oito segundos, sem áudio. O vídeo não tem movimento próprio,
  seleção semântica de trechos, fala nem legenda sincronizada.
- O renderer atual gerou uma story e um vídeo da mesma fonte para comparação.
  Os arquivos estão apenas em `.local/evals/editor-benchmark-2026-10-26/`:
  `comparacao.jpg`, `baseline-story.jpg`, `photocraft-story.png`,
  `baseline-video.mp4`, `filmcraft-8s.mp4`. Os binários ficam em
  `/tmp/meu-braco-direito-editor-benchmark/`; o produto não depende deles.

| Ensaio | Medição local | Limite da comparação |
| --- | --- | --- |
| PhotoCraft: cor em 720×1280 | 0,32 s; pico 60 MB | CLI no Mac ARM, sem fila |
| PhotoCraft: composição após cor | 0,59 s; pico 67 MB | direção e texto manuais |
| FilmCraft: dois quadros, oito segundos, 720×1280 | 5,6 s; pico 468 MB; 1,60 MB | CLI no Mac ARM, sem áudio ou motion |
| Renderer de vídeo atual, 1080×1920 | 10,5 s; 130 kB | FFmpeg num contêiner Linux, resolução e roteiro diferentes |

Os tempos **não** demonstram superioridade de um encoder: resolução, plataforma,
efeitos e conteúdo diferem. O tamanho do MP4 do renderer atual reflete cenas
estáticas mais compressíveis, não mais qualidade. O cartão de texto do PhotoCraft
ocupou menos da tela e deu mais espaço ao produto do que o template v4. Não há
revisão da proprietária nem nota de qualidade; a peça ainda é simples.

Um comando de forma do PhotoCraft com cor RGBA em array resultou em branco
apesar de retornar sucesso; trocamos por `#203C32` e inspecionamos os pixels.
Esse achado exige validação da saída e testes visuais por versão, não apenas
conferência de exit code. A imagem já finalizada com logo/texto precisa de rota
`preserve`, enquanto material bruto pode seguir `compose`. Essa classificação
não foi automatizada aqui.

## Decisão técnica e econômica

Fazer uma prova de conceito com PhotoCraft como **opção** de compositor em worker
isolado e binário/versão fixados, mantendo o compositor atual até avaliação
comparativa com material autorizado. FilmCraft é candidato a edição de timeline
mais complexa, não substituto automático de FFmpeg; o projeto declara fase
alpha. Em produção, comandos são gerados de uma receita JSON validada e
allowlisted pelo nosso backend, nunca texto livre executado como shell/MCP.
Cada saída é reaberta e verificada quanto a dimensões, integridade, conteúdo
factual e contraste; renderizações versionadas têm hash, custo e retry limitado.
O mesmo contrato permite trocar o motor sem mudar a aprovação/publicação.

O plano de R$ 99/mês só poderá ser comercializado com **custo total mensal por
cliente de no máximo R$ 50**, incluindo cobrança, mensageria/verificação, IA,
render, armazenamento/tráfego, parcela da infraestrutura compartilhada,
retentativas, impostos, atendimento humano atribuído e aquisição amortizada.
Definir franquia por número de peças **e** tentativas, reservar orçamento antes
de cada operação paga e impedir chamadas que excedam o saldo. Para começar a
modelar o plano, reservar até R$ 30 para tecnologia/cobrança/mensageria e R$ 20
para impostos, aquisição, atendimento e variação; essa divisão é **meta de
planejamento, não custo medido nem franquia aprovada**. A Stripe anuncia cobrança
por cartão nacional de 3,99% + R$ 0,39 e Billing de 0,7%; em R$ 99 isso é
aproximadamente R$ 5,03 antes de taxas adicionais, sujeitos ao contrato do
cliente. Outros componentes ainda não foram medidos. Se qualquer parcela exceder
o envelope, reduzir franquia ou rever preço antes de prometer o plano.

IA deve classificar/entender mídia, planejar narrativa, selecionar receita e
revisar a saída. Edição/generation visual paga é usada quando testes mostram
ganho real e o orçamento comporta. Nenhum editor por si só substitui direção
criativa, fotos reais boas ou revisão humana. Vídeo inteiramente gerado por IA
não é promessa ilimitada do plano de entrada.

## Próximas validações antes de produção

1. Obter mídia original e autorização explícita da proprietária ou de outros
   negócios; medir versões no celular com a avaliação F04.1b/F04.2b.
2. Comparar pelo menos duas receitas por fonte: `preserve` para arte pronta e
   `compose` para material bruto. Avaliar duplicação de texto, visibilidade do
   produto, identidade, fatos, aceitação e taxa de ajuste.
3. Ensaiar PhotoCraft e FilmCraft em contêiner Linux com limites de CPU/RAM e
   concorrência; registrar p50/p95, custo AWS real, crashes, segurança e licença.
4. Comparar edição local com geração/edição visual por IA em amostra autorizada
   e orçamento de teste explícito. Medir custo **por peça aceita**, incluindo
   versões descartadas, antes de escolher franquias e modelos.

Fontes: [PhotoCraft](https://github.com/storytold/photocraft),
[FilmCraft](https://github.com/storytold/filmcraft),
[preços da Stripe](https://stripe.com/br/pricing),
[Stripe Billing](https://stripe.com/br/billing/pricing).
