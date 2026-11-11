# Clipe musical pessoal — peça gerada

[Comparação privada: original, peça e Intensa](../../.local/evals/music-performance-2026-11-06/piece-final/report.html).
[MP4 final](../../.local/evals/music-performance-2026-11-06/piece-final/final.mp4).
[Plano autorizado](plano-clipe-musical-pessoal-2026-11-06.md).

## Resultado

Peça integral de **46,5 s, 720×1280, 30 fps, H.264/AAC**, 1.395 quadros,
12.955.930 bytes. Fonte pessoal de 480×848 preservada, sem alegar recuperação
de detalhes além da resolução original. SHA-256 final:
`130b8a7716eedcacc2c9dfc0cf0075bbed46ff5b59c5a3a112ebefdc2bfb5cc7`.

Composição “Fenda e ressonância”: mudanças de contraste, reenquadramentos que
em alguns momentos excluem o título incorporado, formas radiais que se separam
e achatam, contornos e rotas. Apoios realistas licenciados de vitrola e chuva,
com dois planos cheios de 18,15–19,8 s e 33–34,6 s. São associações poéticas,
identificadas como ilustrativas, não cenas da vida do intérprete.

Nos planos cheios, performance e legendas incorporadas ficam ocultas por
3,25 s; o áudio e o relógio da gravação continuam integralmente. Não há legenda
substituta nessas inserções. No restante, não foi adicionada transcrição visual
duplicada, nome artístico, autoria, marca, CTA ou letra nova.

Geração concluída; avaliação criativa e escuta perceptiva do titular pendentes.
Não constitui publicação autorizada ou feature de produto concluída.

## Etapas, custos e intervenções

Titular autorizou áudio/quadros pessoais, derivados, apoios licenciados e fontes
locais/MIT, três chamadas com teto adicional US$ 1,60, sem refação automática.

| Etapa | Operação | Modelo | Estimativa |
| --- | --- | --- | ---: |
| Transcrição/tempos | `6f4fdd0c-ff03-4dfe-b55c-efc5d396a760` | whisper-1 | US$ 0,0047 |
| Direção | `af272b4d-218e-4f1c-9913-2a64f31f959c` | gpt-6.1-sol/high | US$ 0,1481925 |
| Composição | `f44a5a44-efea-401e-9c25-ed8e80cadc0a` | gpt-6.1-sol/high | US$ 0,3585875 |
| Total | 3 chamadas, zero retries | | **US$ 0,51148** |

Estimativas a partir do uso, não fatura. Reservas US$ 0,10 + 0,75 + 0,75
preservadas. Nenhum Higgsfield, TTS ou geração paga de imagens/vídeos de apoio.
Arquivos/código da galeria não foram redistribuídos como mídia da peça.

ASR trouxe erros de canto em quatro trechos. Correções semânticas foram
fundamentadas nas legendas incorporadas; palavras não confiáveis de uma faixa
foram omitidas como gatilhos individuais. Original e revisão permanecem separados.
Não houve nova transcrição paga nem alinhamento auditivo/forçado comprovado.

A primeira direção restringiu excessivamente a criação a margens e pequenas
variações de escala. Uma revisão escrita do brief apontou essa regressão e
reabriu recortes editoriais, formas amplas e apoios proeminentes. A composição
recebeu **direção original + revisão**, dentro da terceira chamada já prevista;
o compositor escolheu a solução e registrou as diferenças no conceito.

HTML/JS finais foram executados em bytes idênticos aos recebidos, sem ajuste
visual manual. `direction-review.json`, pedidos, respostas e custos estão no
relatório. Isso distingue revisão de brief de alteração posterior da peça.

## Execução pessoal e verificação

Foi usado o renderer privado `owner_media_evaluation`, com consentimento e
hash da fonte específicos, sem marcar material real como fixture. Chromium com
sandbox normal, CSP, rotas/recursos allowlisted e ambiente sem credenciais;
nenhuma requisição inesperada. Não prova isolamento de SO ou segurança de
produção para clientes. O runner comum e o produto não foram alterados.

O visual foi renderizado mudo; em seguida o AAC original foi muxado por cópia.
Verificação confirmou **ADTS e PCM decodificado idênticos**, 2.004 pacotes em
ambos, início e duração do áudio com delta zero. Fonte original mantém SHA-256
`ec4063b5405b7e2c8c7d1a664ee201e52ee8e9e349a275efdc0dd1b15f39e474`.
Vídeo final tem 46,5 s e AAC 46,483333 s, como a gravação.

A primeira checagem interrompeu por `nb_frames` declarado no cabeçalho AAC:
original dizia 2.005, final 2.004. A contagem efetiva retornou 2.004 pacotes nos
dois, com payload, PCM e tempos iguais. Uma verificação separada registrou
essa divergência de metadados e confirmou a peça existente, sem novo render,
remux, alteração de áudio ou chamada. Falha/nota e validação permanecem preservadas.

Decodificação integral passou. Comparação conferida no Chromium em 390/1440 px:
três players carregados, 26 links existentes, sem erro, overflow ou acesso
externo. Código e amostras no início, meio, apoios e fim confirmam a presença
dos mecanismos e legibilidade nas amostras; não substituem assistir/ouvir tudo.
ASR/RMS são pistas aproximadas: não declarar sincronismo perfeito por palavra.

Preparação/executores privados passaram em seis testes de schema/cópia/mux,
três de ASR, três de chamadas/ledger e testes negativos do modo pessoal; sem
rede nos testes. CI integral não repetido: não houve código de produção,
instalação, banco, Temporal, WhatsApp ou publicação nesta rodada.

Evidências privadas em `.local/evals/music-performance-2026-11-06/`:
`piece-final/final-verification.json`, `initial-validation-note.json`,
`report-check.json`, `render/trace.json`, `qa-frames/`, respostas e ledger.
`piece-v1` é somente preparação anterior sem render; não é outra criação.

Próximo gate é o julgamento humano desta peça. Demais frentes permanecem
adiadas, conforme o pedido de trabalhar uma por vez.
