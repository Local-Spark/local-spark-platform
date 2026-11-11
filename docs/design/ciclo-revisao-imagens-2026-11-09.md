# Próxima fatia: revisão de imagens antes da entrega

Planejamento da etapa 5, ainda sem implementação. Começar depois da qualificação
técnica do Reel. O usuário já autorizou os demais formatos; este desenho não
autoriza novas chamadas pagas nem afirma melhora visual comprovada.

## Ponto de integração

Reutilizar a produção `full_piece_v1`, seu contexto/kit/skills, a atividade
Temporal e as guardas existentes. Inspecionar o **JPEG final**, depois de
`_encode_preview` e antes de disponibilizar a prévia. Revisar o PNG bruto não
comprovaria o arquivo que o cliente recebe.

Na primeira fatia, manter foto 4:5 (1024×1280) e story 9:16 (1152×2048), conforme
os perfis existentes. Não substituir a peça por um novo template. O estado de
execução deve continuar protegendo kit, fontes e consentimentos durante crítica
e edição; encerrar a primeira geração não encerra esses efeitos adicionais.

## Crítica e seleção

- Critérios próprios: fatos, marca, legibilidade, composição e integridade.
  Fatos, marca, legibilidade e integridade são obrigatórios e precisam de
  evidência suficiente. Não reutilizar critérios de áudio/motion.
- Cada achado tem problema, evidência na imagem atual por SHA-256, região
  normalizada, gravidade e correção sugerida. Fonte ou versão anterior não
  comprovam sozinhas a condição da candidata.
- Sem problema relevante acionável, conservar a primeira versão. Na primeira
  fatia, permitir no máximo uma edição e uma avaliação comparativa posterior;
  dúvida, empate ou regressão não tornam a candidata a versão escolhida.
- Preservar original e candidata. A nova versão só pode ser selecionada após
  atender os obrigatórios e demonstrar ganho fundamentado na comparação.
  Critério automático satisfeito não representa aprovação humana.

O formato final, texto autorizado, produto/local e identidade devem permanecer
vinculados ao contexto da primeira geração. Uma nova informação de cliente é
outro pedido de ajuste; não pode ser introduzida silenciosamente pela crítica.

## Edição e referências

O provider de imagem existente já usa `edits` quando recebe referências, mas
isso não implementa correção de uma peça anterior. A nova requisição deve
identificar explicitamente o JPEG a corrigir e os achados, além das fontes
originais necessárias. Reutilizar seu transporte de tentativa única.

O limite atual é cinco referências. Priorizar a peça anterior e as referências
de fidelidade: imagem enviada, produto, espaço e logo. O exemplo visual do kit
é complementar; quando não couber, omitir somente esse exemplo, registrando a
seleção e mantendo a direção textual e os hashes de contexto. Não truncar a
lista arbitrariamente nem retirar uma fonte factual para inserir estilo.

## Persistência, custo e falhas

Crítica, edição, avaliação e upload têm identidades próprias vinculadas à
prévia/fence e aos hashes. Persistir pedido/resposta privados antes de concluir
o registro financeiro. Usar `VisualCostLedger`; não criar um segundo ledger ou
runner. Nenhum HTTP pode acontecer sob lock de banco.

Uma resposta incerta interrompe o ciclo e conserva a reserva. A primeira
geração ter terminado não permite liberar a execução se outra chamada estiver
incerta. Verificar orçamento para edição **e** avaliação antes de editar.
Registrar custo/tempo de geração inicial, revisão, falhas e refações separados
do valor efetivamente faturado. Ativação paga exige plano, credenciais e teto
explícitos, inclusive limite suficiente para entrada/saída do modelo de crítica.

O conjunto completo de versões deve chegar a `content_pieces`, mantendo o
JPEG escolhido compatível com a leitura da prévia existente. A persistência
precisa resistir a falha entre conclusão da prévia e registro da coleção, sem
repetir geração paga. A forma concreta dessa finalização ainda precisa ser
implementada e testada; não basta chamar dois commits e supor atomicidade.

## Evidências para encerrar a fatia

Testes locais: preservar a primeira versão adequada; corrigir somente achado
fundamentado; rejeitar regressão; guardar versões sem escolher automaticamente
a última; respeitar referências, orçamento e identidade; impedir repetição
após incerteza; sobreviver a falhas na finalização; confirmar tenant/fence,
revogação e ausência de postagem. CI e cobertura exigidos pelo repositório.

Depois, comparação real com casos fictícios, orçamento próprio e avaliação
humana. Story em vídeo reutiliza o caminho de motion com skill/perfil próprios;
carrossel exige produção por página, coerência da sequência e ajuste seletivo.
Essas duas fatias continuam pendentes, sem serem consideradas implementadas
pela presença de tipos e metadados na coleção.
