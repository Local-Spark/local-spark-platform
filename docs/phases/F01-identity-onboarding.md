# F01 — Identidade, cadastro e autorização

Status: Planejada. Atualizado em 20/10/2026.
Dependências: F00.

## Objetivo

Estabelecer identidade do usuário e do negócio com onboarding seguro e contexto confirmado.

## Features e contratos

- Definir emissor OIDC e validar assinatura, issuer, audience e expiração, com rotação de chaves.
- Criar tenant, membership, negócio, marca, fatos e preferências com ownership explícito.
- Vincular telefone verificado e consentimentos; convite entre usuários não transfere propriedade.
- Exportar contratos de API e iniciar interface complementar de OAuth/consentimento.

## Critérios de aceite e testes

- Acesso cruzado, usuário revogado, convite expirado e troca de tenant negados.
- Provisionamento repetido idempotente e rollback sem recursos órfãos.
- Journey real com usuário fora da equipe em staging.

## Limites e decisões pendentes

- Nome comercial e provedor de identidade ainda não confirmados.
- Não incluir integração paga apenas para simular cadastro.

## Integração e manutenção

Dividir as features acima em mudanças revisáveis. Cada mudança atualiza este SDD,
`docs/PROJECT.md` e `docs/CHANGELOG.md`, incluindo evidências de testes e pendências.
Contratos que afetam outras fases devem ser refletidos no SDD geral e nos consumidores.
Não marcar como concluído por possuir mocks ou documentação de uma API ainda não validada.
