# F04 — Artes, carrosséis e edição de vídeo

Status: F04.1 implementada localmente em 25/10/2026; F04.2 e demais receitas planejadas.
Dependências: F02, F03.

F04.1 consome apenas roteiro F03.3 aceito, contexto e material vigentes. Produz
prévia JPEG privada de foto (1080×1350) ou story (1080×1920) com identidade de
marca, foto real opcional, fato confirmado e convite genérico. O proprietário
pede e abre a prévia em `/app/ideas`; isso não aprova uma publicação. F04.2
amplia para vídeo curto com FFmpeg e legenda sincronizada; F05 mantém avatar
opcional. Edição direta e revisão iterativa do roteiro F03.3 permanecem como
melhoria antes de ativação comercial.

Exemplo visual: [arte do Hot Dog da Ana](../assets/f04-hotdog-preview.jpg),
renderizada pelo adapter F04.1 com uma foto sintética usada somente para
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
