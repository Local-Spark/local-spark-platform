# Resultado do Reel orientado pela biblioteca — 06/11/2026

## Peça e demonstração

- [Comparação: nova peça, v2 mínimo e rodada anterior](../../.local/evals/motion-runs/276486e3-f312-4c5c-aaa6-4975536b9fb3/report.html).
- [MP4 novo](../../.local/evals/motion-runs/276486e3-f312-4c5c-aaa6-4975536b9fb3/render/render.mp4).
- [Direção e fontes declaradas](../../.local/evals/motion-runs/276486e3-f312-4c5c-aaa6-4975536b9fb3/answer.json),
  [trace](../../.local/evals/motion-runs/276486e3-f312-4c5c-aaa6-4975536b9fb3/render/trace.json)
  e [custo](../../.local/evals/motion-runs/276486e3-f312-4c5c-aaa6-4975536b9fb3/cost.json).

O titular autorizou uma chamada e o envio do pacote, até US$ 0,75 adicionais.
O [plano](plano-motion-biblioteca-2026-11-06.md) registra a seleção de referências,
skills, fontes, direitos, orçamento e limites. A operação nova foi
`276486e3-f312-4c5c-aaa6-4975536b9fb3`; nenhuma chamada foi repetida.

## Entrada e direção

O caso preservou gravação, kit, voz e interpretação/transcrição históricas
identificadas. Incluiu a skill **`instagram-reel-v1`**, resolvida pelo loader
real e verificada por hash, mais `claude-video`, fichas e código de três
projetos selecionados após análise amostrada da galeria. O v2 foi apresentado
como piso, sem copiar seu código/layout/roteiro. Oito quadros foram enviados;
vídeos ou quadros da galeria não foram transmitidos. Não houve outra consulta
paga a Jev, transcrição ou geração de mídia.

Código conferido por leitura e comparação das funções:

| Origem | Reutilização concreta na cena nova |
| --- | --- |
| `showreel` | `sobe`/`borrado`, arcos e compressão do ponto, `pontoEstado`, geometria polar/morfose de círculo e superelipse; ponto se divide no sinal de pausa. |
| `app-de-motion` | `hs`, `mixC`, `camAt`: a mesma janela interpola posição, proporção, raio e foco entre retrato e paisagem. |
| `diagrama-azul-marinho` | `rota`, `pontoEm`, `tracaTrecho`, `cavalga`: comprimento de percurso e ponto/rastro cuja chegada antecede a próxima transformação. |

Janela inicial: 360×640 px à direita. Passa para 576×384 entre 2,98–4,10 s e
retorna ao retrato, 324×576, entre 6,80–7,90 s, agora à esquerda. O ponto nasce
como pontuação, percorre trajetória e muda de função no fechamento. São
mecanismos implementados, não apenas nomes citados no prompt.

A gravação tem dois cortes internos de tempo, de aproximadamente 0,36 e
0,14 s, enquanto a geometria da janela permanece contínua. O áudio fica contínuo
e integral; o caso é uma voz sintética sobre gravação ilustrativa. Há retenção
do último quadro por aproximadamente 0,54 s no fechamento. Esses recursos
precisam ser avaliados no MP4, sem presumir adequação a uma fala com rosto/lábios.

Os títulos repetem a expressão genérica “Abra espaço.” presente no v2; os
enquadramentos, trajetórias, cronograma e fechamento são diferentes. Isso fica
registrado para avaliação do grau de originalidade, sem afirmar superioridade
criativa antes do retorno do titular.

## Uso, custo e fidelidade

Modelo `gpt-6.1-sol`, esforço alto, serviço padrão. HTTP 200/completed em
323,935 s; 46.212 tokens de entrada (46.209 cache-write) e 17.161 de saída,
incluindo 8.804 de raciocínio. Estimativa conservadora do CLI:
**US$ 0,28714**, não fatura. Reserva de **US$ 0,75** preservada.

HTML e JavaScript renderizados são idênticos à resposta recebida. Não houve
correção manual de desenho/código nem mudança de edição após a chamada.
Assets, referências, avisos MIT, input/output, custo e código ficaram congelados
no diretório da execução. Os originais adotados também foram preservados no
repositório próprio de fontes, conforme o plano.

MP4: **11,2 s, 720×1280, 30 fps, H.264/AAC**, 1.160.887 bytes, 336 quadros.
SHA-256: `c7d02f9285fd7be891e0c046e999c731681aa4c094fb6fd2019c80447cb0ddf5`.
Decodificação integral passou; sandbox normal do Chromium e nenhuma requisição
inesperada. Quinze links locais e os arquivos dos três players foram conferidos.

27 testes offline do CLI, Ruff e mypy estrito passaram antes da geração. Não
foi repetido o CI integral da aplicação: esta fatia alterou somente o ensaio
e seu relatório, sem habilitar formatos ou fluxos de produto.

## Avaliação ainda aberta

Quadros amostrados e código confirmam vídeo desde o início, mudança de proporção
e componentes reais da biblioteca. Não equivalem a assistir à peça ou ouvir o
mix; não houve escuta perceptiva nova. Legendas usam limites históricos estimados.
**Superar o v2 continua sendo avaliação do titular.** Esta execução não encerra
qualidade dos demais formatos, integração da aplicação ou publicação.
