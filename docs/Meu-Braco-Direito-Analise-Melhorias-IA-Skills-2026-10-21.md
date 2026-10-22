# Meu Braço Direito — Análise de Melhorias, IA de Conteúdo e Skills por Negócio

**Data:** 21/10/2026  
**Contexto:** Análise solicitada durante finalização dos testes da F01.  
**Objetivo do documento:** Consolidar recomendações de melhorias tecnológicas (especialmente geração de conteúdo com IA), pesquisas de ferramentas 2026, definições de arquitetura e proposta de **Skills por negócio** para economia de tokens e melhoria de qualidade.  
**Destino:** Enviar para outro modelo/agente analisar e implementar o que fizer sentido no repositório `local-spark-platform` / `local-spark-web`.

---

## 1. Resumo Executivo

O projeto está em um caminho **sólido e acima da média** para o estágio atual (F01 em finalização). A arquitetura (FastAPI + PostgreSQL/RLS + Temporal + outbox/relay/lease/fencing + auth própria + multi-tenancy) é madura e preparada para escala. O uso de Temporal já segue o padrão de empresas que processam milhões de gerações de vídeo/avatar por dia (ex.: HeyGen).

A meta de **200 mil clientes pagantes recorrentes** é ambiciosa, mas factível **somente se**:
- O custo unitário de geração (especialmente avatar e vídeo) for controlado desde cedo.
- A qualidade e consistência de marca melhorarem com o tempo (sem explodir o consumo de tokens).
- A retenção for alta (WhatsApp + resultados semanais + pouco atrito).

Principais recomendações prioritárias:
1. Formalizar **adapter de geração de conteúdo** com múltiplos provedores (HeyGen + Kling + Veo + FFmpeg determinístico).
2. Introduzir **Skills por negócio** (conhecimento vivo e versionado do tenant) para reduzir tokens e aumentar consistência.
3. Bootstrap progressivo do conhecimento do cliente (onboarding leve + enriquecimento contínuo via aprovações e interações).
4. Ledger de custo/franquia o mais cedo possível (junto com F04/F05).

---

## 2. Estado Atual do Projeto (resumo dos documentos)

- **Nome:** Meu Braço Direito  
- **Repositórios:** `local-spark-platform`, `local-spark-web`, (infra futura)  
- **Fase atual:** F01 em finalização (F01.1–F01.6 implementadas localmente; staging/AWS e envio real Twilio ainda pendentes).  
- **F00:** Concluída localmente com 100% coverage.  
- **Arquitetura core:** FastAPI, PostgreSQL 17 + RLS, Temporal, Redis, S3, auth própria (Argon2id, sessões, MFA staff), Stripe (modo disabled/test), outbox + relay com lease/fencing.  
- **Jornada:** Pequeno empresário envia material/ideias pelo WhatsApp → pesquisa → roteiro → geração → aprovação → publicação (Instagram primeiro) → resultados.  
- **Avatar/voz do próprio dono** é diferencial planejado (F05).  
- **Testes:** Alta cobertura (244 backend / 107 web no último status), jornadas Playwright, migrations reversíveis.

Pontos fortes já existentes que facilitam as melhorias propostas:
- Multi-tenancy + RLS
- Temporal + workers isolados
- Aprovação por versão/hash
- Consentimentos separados
- Biblioteca de materiais e fatos autorizados (planejada em F02/F03)

---

## 3. Análise de Ferramentas de IA para Conteúdo (estado em out/2026)

### 3.1 Ferramentas recomendadas para avaliação

| Necessidade                          | Ferramentas fortes em 2026                  | Observação para Meu Braço Direito                          |
|--------------------------------------|---------------------------------------------|-----------------------------------------------------|
| Avatar realista + voz do dono        | **HeyGen** (líder), Synthesia, VEED, D-ID, Tavus | Manter HeyGen como primário. Bom suporte a clonagem e PT-BR. |
| Vídeo gerado (B-roll, cenas, produto)| **Kling AI**, Google **Veo 3.1**, Seedance 2.5, Runway Gen-4 | Kling e Veo estão deliverando motion/física superiores em vários benchmarks. |
| Reel completo (ideia → vídeo vertical)| Revid, CapCut AI, InVideo AI, Predis.ai, ClipNova | Úteis como fallback barato ou planos entry-level. |
| Clipping / repurposing               | OpusClip                                    | Excelente quando o cliente envia vídeo longo.       |
| Consistência de face/estilo          | Sozee e ferramentas com face-lock           | Importante para séries de conteúdo.                 |

### 3.2 Recomendações de arquitetura de geração

- Criar um **ContentGenerationProvider** (adapter pattern) com implementações concretas:
  - `HeyGenAvatarProvider`
  - `KlingSceneProvider`
  - `VeoBrollProvider`
  - `FFmpegDeterministicProvider` (templates + assets autorizados)
  - `OpenAIImageProvider` (quando fizer sentido)
- O workflow Temporal escolhe o provedor com base em:
  - Orçamento restante do tenant
  - Tipo de conteúdo solicitado
  - Qualidade mínima exigida
  - Latência aceitável
  - Disponibilidade/circuit-breaker do provedor
- Pipeline **híbrido**: FFmpeg determinístico como base barata e previsível; IA generativa só quando agrega valor real.
- **Shadow eval** contínuo de novos modelos (mesmo espírito do Jev shadow): gera exemplos, mede preferência humana + métricas (lip-sync, face consistency, legibilidade de preço, etc.).

### 3.3 Custo e escala

Em 200k clientes o COGS de geração pode destruir a margem do plano de R$ 99.  
Por isso o **ledger de quota + reserva atômica** (planejado na F07) deve nascer junto com a geração real (F04/F05). Sem controle de custo unitário, a escala vira prejuízo.

---

## 4. Skills por Negócio (proposta central de economia de tokens)

### 4.1 Conceito

Uma **Skill por negócio** é um pacote vivo e versionado de conhecimento específico daquele tenant. Em vez de reinjetar contexto longo (descrição do negócio, tom de voz, produtos, restrições, histórico de aprovações) a cada geração, o sistema carrega a skill (compacta) + apenas o material novo do dia.

Benefícios:
- Redução progressiva de tokens por geração.
- Maior consistência de marca e tom.
- Custo mais previsível por cliente.
- Aprendizado controlado a partir de aprovações do cliente.

### 4.2 O que a Skill pode conter

- Tom de voz e vocabulário preferido (formal, descontraído, regionalismos)
- Fatos autorizados e fontes já validadas
- Produtos/serviços principais + atributos aprovados
- Estilo visual (cores, legenda, ritmo, uso de avatar)
- Padrões de conteúdo que performaram bem
- Regras negativas (“nunca falar de X”, “evitar emoji Y”)
- Preferências de orçamento e frequência de publicação

### 4.3 Bootstrap das informações (resposta à pergunta “como teremos todas essas informações prévias?”)

**Não é necessário (nem desejável) pedir tudo no onboarding.**

#### Princípio: Onboarding leve + enriquecimento progressivo

1. **No onboarding (F01.4 já existe)**  
   Coletar o mínimo viável com baixa fricção:
   - Atividade (sugerida ou livre)
   - Descrição curta do negócio
   - Cor principal
   - Cidade/UF (já implementado)
   - Tom de voz preferido (opcional, 3–4 opções simples: “profissional”, “descontraído”, “próximo e caloroso”, “técnico”)
   - Produtos/serviços principais (lista curta, opcional)

   Quanto **mais informação de qualidade**, melhor a primeira geração. Mas cada campo a mais aumenta abandono. O equilíbrio ideal é **mínimo obrigatório + opcionais claros**.

2. **Enriquecimento contínuo (o caminho principal)**  
   - Toda vez que o cliente **aprova** um conteúdo → extrair trechos úteis e atualizar a skill (com versionamento).
   - Correções explícitas via WhatsApp (“não use mais essa expressão”, “prefiro legenda mais curta”) → atualização da skill.
   - Material enviado pelo cliente (fotos, áudios, textos) → após validação, vira fato autorizado ou preferência.
   - Resultados de performance (quando existirem insights) → reforçar o que funcionou.

3. **Edição explícita pelo cliente**  
   Permitir que o dono veja e edite a skill (ou peça reset) pela web ou por comando no WhatsApp. Transparência aumenta confiança.

4. **Resumo da resposta**  
   - No momento da configuração do negócio: coletar o essencial + o que o cliente quiser informar espontaneamente.  
   - Com o passar do tempo: a skill cresce de forma controlada a partir de aprovações e interações reais.  
   - **Sim, quanto mais informação de qualidade, melhor** — desde que a coleta não gere atrito excessivo no onboarding e que a skill tenha limite de tamanho (ex.: 2–4k tokens).

### 4.4 Modelo de dados sugerido (MVP)

```sql
-- Exemplo simplificado
CREATE TABLE business_skills (
    id              UUID PRIMARY KEY,
    tenant_id       UUID NOT NULL,
    business_id     UUID NOT NULL,
    version         INTEGER NOT NULL,
    content         TEXT NOT NULL,          -- markdown ou JSON estruturado
    token_estimate  INTEGER NOT NULL,
    source          TEXT NOT NULL,          -- 'onboarding' | 'approved_content' | 'explicit_feedback' | 'manual'
    created_at      TIMESTAMPTZ NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL,
    UNIQUE (business_id, version)
);

-- Índice para buscar a versão atual rapidamente
CREATE INDEX idx_business_skills_current 
    ON business_skills (business_id, version DESC);
```

- Sempre carregar apenas a **versão mais recente**.
- Manter histórico para rollback.
- RLS obrigatório (tenant_id / business_id).

### 4.5 Integração no workflow Temporal

```
1. Recebe material novo / intenção
2. Activity: LoadBusinessSkill(business_id) → retorna skill atual + token_estimate
3. Activity: ExtractFacts + DecideGenerationStrategy
4. Activity: GenerateContent(skill + novos_fatos + provider escolhido)
5. Cliente aprova / rejeita / corrige
6. Activity: UpdateBusinessSkill (somente com conteúdo validado)
```

### 4.6 Progressive Disclosure (mesmo princípio das skills do Grok)

- Metadados da skill (resumo + versão) → sempre disponíveis.
- Corpo completo → carregado só quando o workflow de geração precisa.
- Referências longas (catálogo completo, histórico) → em storage e lidas sob demanda.

### 4.7 Cuidados obrigatórios

- Isolamento total por tenant (RLS).
- Hard limit de tamanho da skill (forçar consolidação/sumarização se passar).
- Nunca atualizar a skill a partir de material bruto não aprovado.
- Cliente deve poder ver, editar ou resetar.
- Consentimento claro de que o sistema aprende com as aprovações.

---

## 5. Outras Melhorias Recomendadas

### 5.1 Arquitetura de geração
- Adapter pattern + DecisionProvider (já alinhado com a ideia do Jev).
- Circuit breaker e fallback por provedor.
- Cache e reuso de assets gerados anteriormente.
- Workers de mídia com task queues separadas (CPU vs GPU).

### 5.2 Observabilidade
- Tokens consumidos por geração e por tenant.
- Custo real por peça publicada.
- Taxa de rejeição do cliente.
- Tempo de render por provedor.

### 5.3 Produto
- Manter FFmpeg determinístico como base barata.
- Relatório semanal com origem dos dados e lacunas (não inventar métricas).
- Diferenciar claramente pagantes, testes e patrocinados.

### 5.4 Escala para 200k
- Controle rigoroso de COGS desde a primeira geração real.
- Aquisição via YouTube dos sócios (já planejada).
- Retenção alta via WhatsApp + valor mesmo em dias sem material novo (F03 é crítica).

---

## 6. Priorização Sugerida de Implementação

| Prioridade | Item                                      | Fase sugerida     | Motivo |
|------------|-------------------------------------------|-------------------|--------|
| Alta       | Adapter de ContentGenerationProvider      | F04 / F05         | Flexibilidade e troca de modelos |
| Alta       | Skills por negócio (MVP)                  | Junto com F03/F04 | Economia de tokens + qualidade |
| Alta       | Ledger de custo/franquia mínimo           | F04/F05 + F07     | Sobrevivência da margem |
| Média      | Avaliação de Kling + Veo 3.1              | F04/F05           | Qualidade de vídeo em 2026 |
| Média      | Shadow eval de modelos                    | Contínuo          | Decisão data-driven |
| Média      | Enriquecimento automático da skill        | Após MVP de skill | Aprendizado controlado |
| Baixa      | Edição explícita da skill pelo cliente    | Após MVP          | Transparência |

---

## 7. Exemplos de Implementação (Skills)

### 7.1 Exemplo de conteúdo de uma Skill (markdown)

```markdown
# Skill — Padaria Pão Quente (versão 7)

## Tom de voz
- Próximo, caloroso, regional (SC)
- Usa “você” e ocasionalmente “tu”
- Evita linguagem corporativa e emojis excessivos
- Prefere frases curtas e diretas

## Fatos autorizados
- Abre todos os dias 6h–20h
- Especialidade: pão francês e cuca
- Entrega via WhatsApp no raio de 3 km (taxa R$ 5)
- Não faz bolo de aniversário sob encomenda no mesmo dia

## Preferências de conteúdo
- Legenda: máximo 2 linhas + 1 CTA
- Formatos preferidos: foto real do produto + texto; avatar só em dicas
- Nunca comparar preço com concorrente
- Sempre mostrar o produto “pronto para comer”

## O que já funcionou
- Hook “Saiu do forno agora…” → alta aprovação
- Vídeo de 12–15s com close no miolo do pão
```

### 7.2 Pseudocódigo da Activity de carga

```python
async def load_business_skill(business_id: UUID) -> BusinessSkill:
    skill = await repo.get_latest_skill(business_id)
    if skill is None:
        return BusinessSkill.empty()  # ou skill gerada a partir do onboarding
    if skill.token_estimate > MAX_SKILL_TOKENS:
        skill = await consolidate_skill(skill)  # sumarização controlada
    return skill
```

### 7.3 Atualização após aprovação

```python
async def update_skill_from_approval(
    business_id: UUID,
    approved_content: ApprovedContent,
    feedback: str | None = None,
) -> None:
    current = await load_business_skill(business_id)
    new_content = extract_useful_patterns(current, approved_content, feedback)
    await repo.save_new_version(business_id, new_content, source="approved_content")
```

---

## 8. Conclusão e Próximos Passos Recomendados

1. Manter a disciplina atual de fases, testes e SDD — está excelente.
2. Na F03/F04, introduzir o conceito de **Business Skill** com o modelo mínimo acima.
3. Formalizar o adapter de geração antes de travar em um único provedor.
4. Avaliar Kling e Veo 3.1 em paralelo a Runway/HeyGen com um corpus real de pequenos negócios.
5. Coletar no onboarding apenas o essencial; deixar a skill crescer com as aprovações.
6. Medir tokens e taxa de rejeição desde as primeiras gerações reais.

Este documento consolida a conversa de 21/10/2026.  
Pode ser usado diretamente como input para outro modelo implementar as partes que fizerem sentido no código e nos SDDs do projeto.

---

**Arquivo gerado em:** 21/10/2026  
**Fonte:** Análise de PROJECT.md, SDD.md, fases F00–F08 + pesquisa de ferramentas de IA (outubro 2026) + discussão sobre Skills.
