# Projeção preparada para aprendizados de referências

`reference_learning_projection` permanece um contrato puro. A fatia 0110 acrescenta
[integração editorial e visual](reference-generation-context.md) com o leitor 0108;
a validação combinada dessa cadeia deve acompanhar sua entrega. A projeção recebe
seleções e análises já carregadas por um futuro serviço confiável, preserva no
snapshot a identidade da referência, a versão da associação, a identidade da
análise, a origem e o estado concluído ou parcial. A projeção mantém somente
análises da versão exata selecionada, na ordem da seleção; ausência não inventa
conteúdo, e duplicatas válidas são recusadas. Perfis, posts, imagens e legendas
não são campos do contrato nem entram em sua projeção para modelo.

A fatia 0110 remove o limite técnico provisório de 32 referências sem truncar
escolhas manuais. Permanecem dez padrões por análise e 240 caracteres por padrão;
o pedido editorial completo continua limitado antes de qualquer efeito pago. As dimensões `visual` e `editorial` apenas
indicam a natureza da observação derivada. A indicação `parcial` permanece
explícita; `concluído` se refere ao estado informado da análise, não demonstra
acesso a todas as publicações nem a qualidade da referência.

Validação sintática rejeita campos adicionais, links, `@`, marcação simples e
caracteres de controle. **Isso não comprova** que uma observação seja realmente
derivada e não reproduza uma legenda, nem elimina injeção de prompt. Uma frase
nesse campo ainda é conteúdo não confiável de terceiro. O módulo não verifica
autoridade nem converte observações em fatos do negócio.

Os gates abaixo permanecem critérios de aceitação da cadeia completa; partes
são implementadas pelas fatias 0108–0110 e exigem prova conjunta:

- Persistir a seleção autorizada do titular, sua versão de associação e a
  procedência comprovada do perfil, inclusive troca manual; carregar tudo sob
  escopo de organização e negócio e revalidar titularidade e acesso.
- Ligar cada análise à versão selecionada, à execução autorizada, à origem
  realmente consultada e ao estado de cobertura; não aceitar como prova um
  rótulo ou snapshot fornecido pelo cliente.
- Coletar no máximo 20 publicações recentes acessíveis do feed conforme a
  decisão existente, com orçamento, identidade de efeito e recuperação. A coleta
  real ainda não existe; o titular não exige exclusão no fornecedor.
- Produzir e verificar abstrações derivadas, sem persistir postagens, imagens ou
  legendas. Campos e limites de entrada não provam essa propriedade; a política
  e os testes do produtor precisam verificá-la explicitamente.
- Definir e implementar transações e invalidações de substituição/retirada da
  referência e renovação automática, evitando usar análise de outra versão.
  Persistir no pedido editorial um único snapshot imutável autorizado e usar o
  mesmo snapshot na geração visual, com revalidação antes de efeitos pagos.
- Passar as observações como dados não confiáveis, em estrutura delimitada, com
  orientação explícita para não seguir instruções nem copiar conteúdo de
  terceiros. As validações independentes de fatos, preço, consentimento,
  orçamento e revisão continuam obrigatórias; a estrutura não é uma garantia
  de que o modelo ignorará injeção.
- Adicionar migrations, RLS, grants restritos, auditoria/outbox e testes de
  concorrência, cancelamento, proveniência, recuperação e isolamento antes de
  habilitar uso em produção. O armazenamento e a agenda pertencem à fatia 0108, e a pinagem à 0110.
