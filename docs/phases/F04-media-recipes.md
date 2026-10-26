# F04 — Artes, carrosséis e edição de vídeo

Status: F04.1 e primeira receita F04.2 implementadas localmente em 25/10/2026;
F04.1b iniciada com template v4 e avaliação sintética. Revisão humana, ajustes
da arte, F04.2b (qualidade do vídeo) e F04.3 continuam pendentes.
Dependências: F02, F03.

F04.1 consome apenas roteiro F03.3 aceito, contexto e material vigentes. Produz
prévia JPEG privada de foto (1080×1350) ou story (1080×1920) com identidade de
marca, foto real opcional, fato confirmado e convite genérico. O proprietário
pede e abre a prévia em `/app/ideas`; isso não aprova uma publicação. F04.2
acrescenta MP4 curto e texto de cena temporizado; F05 mantém avatar
opcional. A edição versionada do roteiro F03.3b já existe; avaliação criativa
com negócios reais permanece obrigatória antes de ativação comercial.

Exemplo visual: [arte do Hot Dog da Ana](../assets/f04-hotdog-preview.jpg),
renderizada pelo adapter F04.1b v4 com uma foto sintética usada somente para
demonstração. Em uso real, a foto vem do material autorizado do negócio; este
arquivo de exemplo não representa envio pelo WhatsApp nem publicação.

## F04.1 — Contrato implementado localmente

- `POST/GET /api/v1/organizations/{tenant}/businesses/{business}/media-previews`
  exige proprietário e plano ativo. `POST` recebe `operation_id` e `proposal_id`;
  só aceita roteiro concluído e aceito, `photo` ou `story`, um fato atual cuja
  redação coincide com o texto da cena e, quando houver foto, asset do mesmo
  negócio ainda disponível. Consentimento de IA é revalidado apenas para roteiro
  gerado com provedor externo; `baseline-v1` local não o exige.
- `render_key` inclui roteiro/documento, versão do contexto, nome/cor da marca,
  hash da foto e versão do template. `UNIQUE` por negócio e operação impede
  duplicação; o worker Temporal faz claim com `SKIP LOCKED`, tentativas limitadas,
  lease de três minutos e fencing. O download da foto confere SHA-256; o worker
  revalida entradas após o upload antes de marcar `completed`. Falhas permanentes
  terminam em `failed`, transitórias voltam à fila até três tentativas. Nenhuma
  chamada ao armazenamento ocorre com lock de linha aberto.
- O objeto fica privado no bucket de materiais, em chave determinística. `GET
  /{preview_id}/download-link` devolve link temporário só ao proprietário, após
  verificar estado, prazo, roteiro e foto de origem. A listagem esconde imediatamente
  prévia cujo material foi excluído, expirou ou perdeu o roteiro. O reconciliador
  marca esses itens para limpeza, apaga inclusive upload parcial pela chave
  determinística e só então remove a linha; erro de armazenamento mantém o
  registro para retry. IDs de proposta e asset são referências denormalizadas
  para que exclusões anteriores não apaguem o registro necessário à limpeza.
- A tela mostra pendente, renderizando, pronto ou falho; não oferece publicar.
  Texto comercial é sempre o fato confirmado; o arquivo não leva hipótese da IA.
  Testes usam PostgreSQL restrito, Temporal e armazenamento falsos, sem Meta/OpenAI
  pagos. A receita Pillow é determinística; medição de qualidade visual com
  comerciantes reais e revisão de template ainda são necessárias antes do piloto.

## F04.1b — Qualidade da arte estática (em andamento)

Primeira fatia técnica em 25/10/2026: o template estático v4 preserva a foto
inteira em enquadramentos retrato, paisagem e panorâmico, usa o recorte apenas
para um fundo desfocado e separa o fato em painel opaco. A marca aparece fora
da foto; cor clara/escura recebe contraste calculado pela luminância relativa.
Arte sem foto usa composição geométrica, sem representar um produto inexistente.
O `render_key` inclui `TEMPLATE_VERSION=4`, mantendo cada versão de arquivo
privada e imutável. Testes cobrem as bordas da foto, contraste, texto longo,
determinismo e limites de mídia. O template anterior não é alterado em disco.

O corpus sintético versionado em `docs/evals/static-art-ptbr-v1.json` cobre
quatro segmentos, foto ausente/quadrada/retrato/paisagem/panorâmica, cores
claras/escuras e foto/story. `python scripts/evaluate_static_art.py` gera
artes, folha de contato, bytes/latência e CSV de revisão em `.local/evals/static-art/`.
Esses oito casos são **teste técnico**, não aprovação de qualidade comercial.

Critérios de entrada para o piloto, definidos antes da avaliação humana:

- Em amostra consentida de ao menos 20 peças, com comerciantes de ao menos
  quatro segmentos e ambos formatos, 90% das peças devem receber nota >= 4/5
  de legibilidade e de visibilidade do produto/serviço; pelo menos 80% devem
  ser aceitas sem ajuste. Avaliação em tela de celular; registrar tamanho de
  amostra e rejeições por segmento, sem ocultar casos difíceis na média.
- Zero erro crítico de preço, produto, oferta, validade, permissão de uso da
  foto ou afirmação inventada. Um único erro crítico bloqueia o piloto até
  correção e nova avaliação do caso. A transcrição factual do banco é a fonte;
  revisão visual humana confere a peça final.
- Registrar p50/p95 de tempo de render, bytes, CPU e custo real de armazenamento
  e tráfego em staging antes de fixar teto de COGS por peça. A receita local não
  chama API paga; custo de infraestrutura ainda não foi medido. O resultado
  sintético não substitui essa medição.

Pendências desta fase: amostra real autorizada e revisão com comerciantes,
correções de template por feedback e fluxo de pedir ajuste visual que cria
outra versão privada sem herdar aprovação anterior. Editar o texto factual ou
o roteiro usa a F03.3b e exige novo aceite antes de renderizar.

## F04.2 — Primeiro vídeo curto (implementado localmente)

- Roteiro `short_video` F03.3 aceito e ainda válido usa a mesma operação
  idempotente, Temporal, lease/fencing, hash de fonte, armazenamento privado e
  limpeza da F04.1. A migration 0032 distingue JPEG e MP4 e guarda duração.
- FFmpeg gera MP4 H.264, 1080×1920, cerca de oito segundos, a partir de foto
  autorizada, trecho inicial de clipe MP4/3GPP autorizado ou cartões de marca.
  Fonte tipográfica incluída no worker cobre acentos PT-BR; versão do template
  invalida renderizações anteriores com glifos ausentes.
  O clipe é enquadrado no formato vertical e tem o áudio original removido.
  Três cenas
  exibem apresentação genérica, fato confirmado literalmente e CTA genérico;
  texto permanece na tela pelo tempo da cena. O vídeo é **silencioso**: não há
  voz sintetizada nem transcrição de fala para chamar esses textos de legenda
  sincronizada ao áudio. Edição com seleção de trechos, cortes múltiplos e áudio
  alinhado fica para uma evolução da receita.
- Fonte limitada a 5 MiB (foto) ou 50 MiB (clipe), com dimensões de vídeo
  verificadas antes do render; saída a 20 MiB,
  até 90 s de processo FFmpeg, dois threads de encoder
  e worker isolado da API. O arquivo só aparece depois de revalidar roteiro,
  contexto, fato, plano e material de origem; o link assinado usa `video/mp4`. Fatos com validade
  fazem a prévia expirar no fim do dia local. A web reproduz o MP4, sem ação de
  publicar. Falhas recebem código estável e tentativas limitadas.
- Render real com FFmpeg é verificado em Docker. Ainda faltam avaliação visual e
  custo por peça com comerciantes, edição de múltiplos trechos e legendas alinhadas
  à fala real antes de chamar a receita de vídeo completo comercial.

## F04.2b — Qualidade criativa do vídeo (planejada antes do piloto)

- Aproveitar as cenas do roteiro versionado F03.3b, o contexto de marca e os
  materiais autorizados para escolher trechos e compor narrativa, ritmo,
  tipografia e CTA adequados ao segmento. Preservar literalmente fatos
  comerciais confirmados; novas alegações exigem confirmação do proprietário.
- Evoluir a receita silenciosa para cortes e transições intencionais. Quando
  houver fala autorizada, avaliar transcrição, edição de áudio e legendas
  alinhadas à fala realmente presente no arquivo; música e voz só com direitos,
  consentimento e custo medidos. Disponibilizar prévia versionada e pedido de
  ajustes antes de qualquer aprovação de publicação.
- Testar com corpus PT-BR e comerciantes consentidos, em celular, medindo
  legibilidade, fidelidade ao produto, qualidade percebida, tempo de render,
  custo e taxa de correções. Bloquear o piloto para erros factuais, cortes que
  alterem o sentido ou qualidade abaixo dos critérios definidos na avaliação.

## F04.3 — Percurso principal pelo WhatsApp (planejado)

F04.3 encadeia material/fato confirmado → ideia/roteiro validado →
prévia sem exigir que o cliente abra a web ou aceite manualmente o roteiro apenas
para iniciar o render. A aceitação técnica para gerar uma **candidata** não é
aprovação do proprietário para publicar. Guardas de fatos, direitos, consentimento,
plano, quota, validade e proveniência continuam obrigatórios; dúvida pede
esclarecimento pelo WhatsApp. Se houver várias candidatas, cada resposta deve
referir-se à peça certa.

F04.3 ensaia envio com adapter fake e eventos assinados localmente; o envio real
usa o canal oficial após homologação Meta. Ambos usam outbox e estado de entrega,
mantendo a web como alternativa. Falha/resultado incerto de envio não vira
aprovação nem dispara reenvio inseguro. A decisão final sobre peça, legenda, destino e horário,
inclusive comandos "Aprovar" e "Pedir ajustes", é contrato da F06. O comando
"Confirmar" usado para preço/horário na F02 nunca autoriza publicação.

## Objetivo

Transformar roteiro e materiais em previews imutáveis com qualidade previsível e custo conhecido.

## Features e contratos

- photo_post, generated_art, carousel, photo_motion_reel e edited_video_reel.
- Templates determinísticos para preço/texto e marca; áreas seguras por formato.
- FFmpeg isolado, render_key estável, armazenamento privado e validação do arquivo final.
- Voz/alinhamento quando necessário; legenda sincronizada com a fala realmente renderizada.
- Portas por capacidade para texto, imagem, fala e render, com perfil versionado,
  custo previsto, ID externo/status e disponibilidade. FFmpeg é base determinística
  das receitas compatíveis; IA generativa entra quando o formato exigir ou houver
  benefício avaliado, sem substituir produto real por imagem sintética inadvertida.
- Reserva atômica de franquia/COGS por operação antes de submit pago, liquidação e
  reconciliação de resultado incerto. Medir custo por peça, latência e retrabalho.

## Critérios de aceite e testes

- Retries de render e saída parcial sem duplicar entrega/custo indevido.
- Preço legível/correto, áudio/duração e sincronização avaliados em corpus consentido.
- Recursos limitados e concorrência de render sem afetar mensagens/HTTP.
- Avaliação paralela só em amostra consentida e com teto de gasto; comparar qualidade
  de preço/texto, fidelidade ao produto e taxa de correção com a receita base.

## Limites e decisões pendentes

- Não substituir foto real por produto sintético sem identificar e aprovar.
- Música/fontes/imagens têm licença compatível.

## Integração e manutenção

Dividir as features acima em mudanças revisáveis. Cada mudança atualiza este SDD,
`docs/PROJECT.md` e `docs/CHANGELOG.md`, incluindo evidências de testes e pendências.
Contratos que afetam outras fases devem ser refletidos no SDD geral e nos consumidores.
Não marcar como concluído por possuir mocks ou documentação de uma API ainda não validada.

## Integração com a área do cliente

Prévia, versão e materiais usados compõem revisão posterior da área web e do
WhatsApp. UI só apresenta formatos efetivamente implementados; erro, refação e
consumo têm status rastreável. Admin acompanha falhas e custos reais.
