# Plataforma de conteúdo para pequenos negócios

Documentação de produto e engenharia, revisada em 20/10/2026.
Nome adotado: Meu Braço Direito (`local-spark-platform`). Os documentos descrevem uma especificação para
implementação; não representam serviços desenvolvidos ou capacidade comprovada.

## Leitura

1. [SDD atual v0.2: arquitetura, escopo e planejamento proativo](v0-architecture.md).
2. [Integrações: fornecedores, APIs, modelos e contratos](v0-integrations.md).
3. [Resiliência: workflows, sagas, retry, circuit breaker e compensação](v0-reliability.md).
4. [Entrega: repositórios, estrutura, AWS, CI e critérios da v0](v0-delivery.md).
5. [Inteligência editorial, referências locais, Jev e escala de pesquisa](v0-intelligence.md).
6. [Garantias: idempotência, concorrência, transações, locks e logs](v0-consistency-observability.md).
7. [Multi-tenancy: tabelas compartilhadas, RLS e evolução de capacidade](v0-tenancy.md).
8. [Cobrança, checkout, confirmação e patrocínio — F01.5](billing.md).
9. [Contexto do negócio, geração e custo por peça — F02–F07](business-context-and-generation.md).
10. [Plano de qualidade criativa: fotos, stories, vídeos e avatar](creative-production-quality.md).
11. [Eval de contexto completo: campos da web, tools, qualidade e custo](../evals/visual-context-eval-v1.md).
12. [Biblioteca de identidade visual e formatos: escolha simples, receitas e avaliação](brand-library.md).
13. [Trilha BL01–BL05: catálogo, prova de reaplicação, vitrine e escolha](../phases/BL-brand-library.md).
14. [Cadência, limites dos planos e recomendações com evidência](editorial-planning-and-evidence.md).

## Decisão atual

FastAPI + PostgreSQL + Temporal com SDK Python + Redis + S3. Temporal substitui
Celery, RabbitMQ e o runner de workflows próprio da proposta anterior. Aplicação
modular, com API e pools de workers escalando separadamente. PostgreSQL guarda o
domínio; Temporal guarda o controle de execução; Redis guarda coordenação temporária.
FFmpeg compõe mídia em processos isolados. OpenAI, HeyGen e Runway têm contratos
pesquisados como candidatos; os provedores de mídia serão escolhidos por capacidade
e benchmark conforme a [decisão mais recente](business-context-and-generation.md).
Meta permanece o caminho oficial planejado para mensagens/publicação.

Repositórios propostos: `local-spark-platform`, `local-spark-web` e `local-spark-infra`.
Instagram é o destino da v0, com múltiplos formatos, avatar do dono e sugestões
proativas mesmo sem material novo. Outras redes são expansão posterior.
Pesquisa e escolha de temas alimentam a roteirização. Descoberta por raio e análise
de referências locais têm conectores e políticas de dados próprios. Jev é candidato
para decisões delimitadas após eval PT-BR, sem substituir geração de texto/mídia.

O produto recebe material pelo WhatsApp, entende o objetivo comercial, prepara
conteúdo, recebe aprovação, publica nas redes habilitadas e apresenta resultados.
O cadastro web complementar atende conexão de contas, captura de consentimento e
etapas que as plataformas exigem fora do chat.

## Histórico v0.1

Os documentos abaixo preservam o desenho anterior e não definem mais a stack ou
o sequenciamento da v0. Em conflito, os documentos `v0-*` acima prevalecem.

- [SDD anterior](SDD.md).
- [ADRs anteriores](architecture-decisions.md).
- [Plano anterior](implementation-plan.md).

## Escopo deste diretório

Esta pasta preserva as especificações de produto e engenharia originadas antes
da implementação. O estado implementado é descrito em `../PROJECT.md`, `../SDD.md`
e `../phases/`; esses documentos prevalecem sobre estruturas antigas sugeridas aqui.
O frontend de origem não faz parte deste backend. Não foram usadas credenciais do curso.

## Referência dos Maestros da IA

A página pública do curso apresenta automações de conteúdo e publicação. Isso
ajuda a identificar capacidades, mas não revela a infraestrutura interna nem
substitui o desenho de um SaaS com isolamento de clientes, faturamento e recuperação
de falhas. O conteúdo privado do curso não foi acessado.

Fonte: [página pública da formação de conteúdo](https://conteudo.maestrosdaia.com/).

Decisão vigente de identidade: [Autenticação própria](native-auth.md), que substitui
a opção inicial de provedor OIDC da F01. OAuth das redes e OIDC do CI/AWS são independentes.
