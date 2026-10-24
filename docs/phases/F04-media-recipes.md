# F04 — Artes, carrosséis e edição de vídeo

Status: Planejada. Atualizado em 20/10/2026.
Dependências: F02, F03.

Próxima fatia F04.1 (24/10/2026): consumir somente roteiro F03.3 aceito e
contexto/material ainda válidos; produzir prévia estática com template de marca,
texto comercial legível, proveniência e arquivo privado. A chave de render deve
incluir versão do roteiro, template e entradas; reserva de trabalho, lock, retry e
falha parcial não podem gerar duas peças finais. O proprietário revisa a prévia,
sem publicação. F04.2 amplia para vídeo curto com FFmpeg e legenda sincronizada;
F05 mantém avatar opcional. Edição direta e revisão iterativa do roteiro F03.3
permanecem como melhoria antes de ativação comercial.

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
