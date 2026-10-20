# F04 — Artes, carrosséis e edição de vídeo

Status: Planejada. Atualizado em 20/10/2026.
Dependências: F02, F03.

## Objetivo

Transformar roteiro e materiais em previews imutáveis com qualidade previsível e custo conhecido.

## Features e contratos

- photo_post, generated_art, carousel, photo_motion_reel e edited_video_reel.
- Templates determinísticos para preço/texto e marca; áreas seguras por formato.
- FFmpeg isolado, render_key estável, armazenamento privado e validação do arquivo final.
- Voz/alinhamento quando necessário; legenda sincronizada com a fala realmente renderizada.

## Critérios de aceite e testes

- Retries de render e saída parcial sem duplicar entrega/custo indevido.
- Preço legível/correto, áudio/duração e sincronização avaliados em corpus consentido.
- Recursos limitados e concorrência de render sem afetar mensagens/HTTP.

## Limites e decisões pendentes

- Não substituir foto real por produto sintético sem identificar e aprovar.
- Música/fontes/imagens têm licença compatível.

## Integração e manutenção

Dividir as features acima em mudanças revisáveis. Cada mudança atualiza este SDD,
`docs/PROJECT.md` e `docs/CHANGELOG.md`, incluindo evidências de testes e pendências.
Contratos que afetam outras fases devem ser refletidos no SDD geral e nos consumidores.
Não marcar como concluído por possuir mocks ou documentação de uma API ainda não validada.
