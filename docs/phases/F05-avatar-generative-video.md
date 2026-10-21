# F05 — Avatar, voz e cenas geradas

Status: Planejada. Atualizado em 20/10/2026.
Dependências: F01, F03, F04.

## Objetivo

Permitir vídeos do próprio dono e composições híbridas sem nova gravação em cada publicação.

## Features e contratos

- Captura guiada, consentimento comprovado e IDs de identidade separados por fornecedor/tenant.
- owner_avatar_reel, hybrid_reel e generated_scene_reel com limites de duração/franquia.
- Submit/status/callback/polling, UNKNOWN e controles de custo antes de chamada paga.
- Revogação impede novas gerações e cancela pendentes; exclusão é operação rastreável.

## Critérios de aceite e testes

- Qualidade PT-BR, sotaques, preço/nome e latência/custo medidos.
- Callback duplicado/perdido e submit ambíguo não disparam gasto cego.
- Revogação concorrente e falha de compensação com suporte auditado.

## Limites e decisões pendentes

- API, slots de identidades, licença de uso e quotas contratadas precisam de evidência.
- Fallback não muda aparência/voz do cliente silenciosamente.

## Integração e manutenção

Dividir as features acima em mudanças revisáveis. Cada mudança atualiza este SDD,
`docs/PROJECT.md` e `docs/CHANGELOG.md`, incluindo evidências de testes e pendências.
Contratos que afetam outras fases devem ser refletidos no SDD geral e nos consumidores.
Não marcar como concluído por possuir mocks ou documentação de uma API ainda não validada.

## Consentimento e interfaces

Autorização de voz/avatar usa página curta complementar e registro específico;
termos do onboarding não autorizam identidade sintética. Cliente vê estado da
geração; admin acompanha custo e falha, com acesso mínimo e auditado.
