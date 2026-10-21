# F02 — WhatsApp e biblioteca de materiais

Status: Planejada. Atualizado em 20/10/2026.
Dependências: F00, F01.

## Objetivo

Receber texto, áudio, fotos e vídeo no número oficial da plataforma e montar solicitações com fatos rastreáveis.

## Features e contratos

- Handshake/assinatura Meta, inbox, subeventos, recibos e deduplicação por adapter.
- Download autorizado, inspeção de mídia, biblioteca S3 privada e agrupamento de mensagens.
- Extrair áudio, transcrever e identificar ambiguidades de preço/data; perguntar o necessário.
- Anexos são dados não confiáveis; limites, SSRF e sandbox de mídia implementados.

## Critérios de aceite e testes

- Webhook duplicado/parcial/reordenado, callback antes da correlação, arquivo inválido e expiração de URL.
- Agrupamento concorrente e contexto de duas empresas sem mistura.
- Smoke com WhatsApp oficial e material consentido.

## Limites e decisões pendentes

- App/WABA, número e templates precisam de configuração e validação.
- A caixa de entrada do produto não equivale às conversas de vendas do cliente.

## Integração e manutenção

Dividir as features acima em mudanças revisáveis. Cada mudança atualiza este SDD,
`docs/PROJECT.md` e `docs/CHANGELOG.md`, incluindo evidências de testes e pendências.
Contratos que afetam outras fases devem ser refletidos no SDD geral e nos consumidores.
Não marcar como concluído por possuir mocks ou documentação de uma API ainda não validada.

## Integração com onboarding e interfaces

A identidade é iniciada na web; a posse do WhatsApp é verificada nesta fase, antes
de associar mensagens à contratação/organização. Telefone digitado no checkout ou
perfil não é verificação. Onboarding conversacional complementa o perfil inicial,
sem exigir uso diário do painel. Consentimentos são específicos por finalidade.
