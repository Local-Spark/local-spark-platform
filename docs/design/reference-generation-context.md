# Referências escolhidas na geração

A fatia 0110 liga as referências selecionadas ao pedido editorial e à composição
visual. O leitor 0108 fornece referências manuais e sugeridas, identidade própria,
versão positiva da associação, perfil, observação do titular, nota e semelhança
quando disponíveis, estado da análise e aprendizados derivados vinculados à
mesma associação. O cliente não envia essas evidências no pedido de geração.

## Captura e proveniência

`reference_capture_generation_context(business)` roda na transação do titular
que solicita a proposta. O resultado estrito de versão 1 é gravado na nova coluna
`editorial_proposals.reference_generation_snapshot`. A coluna antiga
`owner_reference_snapshot` conserva seu significado. Replay de uma operação
existente retorna a proposta original sem recapturar referências ou análises.
O trigger 0110 rejeita qualquer troca posterior da nova coluna; registros
anteriores permanecem nulos, sem backfill implícito.

Cada aprendizado deve corresponder à identidade e versão de uma escolha.
Duplicatas, outra versão, outra referência, análise ausente declarada concluída,
status divergente e campos brutos são rejeitados. A projeção omite IDs de perfil,
análise e resultado do payload enviado aos modelos. Não há limite silencioso
de 32 indicações manuais: todas seguem para a verificação existente de tamanho do
pedido, que rejeita um pedido excessivo antes de reservar tokens.

## Uso editorial e visual

`EditorialProposalService._inputs` usa a cópia da proposta. O request estruturado
mantém essas informações separadas dos fatos confirmados do catálogo. O mesmo
conteúdo orienta a peça em `VisualBrandFinishService`; não existe coleta de feed
durante geração nem envio de posts ou imagens de terceiros. As imagens reais
continuam vindas de fontes autorizadas do negócio e do exemplo de kit.

As instruções compartilham uma regra: padrões podem orientar tom, temas,
formatos e elementos visuais gerais, sem copiar texto, marca, imagem ou layout.
Nota e semelhança são sinais de seleção, não evidência de qualidade ou fatos do
cliente. Opinião do titular e padrões são dados não confiáveis; instruções
contidas neles não alteram as regras. Cobertura parcial e ausência de análise
permanecem explícitas. Essa delimitação não prova qualidade nem eliminação de
injeção de prompt; revisão humana e avaliação real continuam necessárias.

## Atualidade e histórico

Antes da submissão editorial e ao receber seu resultado,
`reference_generation_context_is_current` confere que todas as associações
utilizadas continuam selecionadas e na mesma versão. O correlator usa tenant e ator da proposta durável já bloqueada e validada;
a consulta conserva o lock da seleção até o mesmo commit da submissão ou do
resultado. Nenhuma rede ocorre sob locks. Mudança antes da submissão rejeita sem reserva ou
HTTP; mudança durante a chamada torna o resultado incerto, conservando o ledger.
Adições posteriores não substituem o conjunto já capturado.

A captura visual inclui o snapshot no fingerprint e revalida sua atualidade
antes de novo efeito. O claim financeiro visual também revalida a seleção
na mesma transação que marca a tentativa, fechando a janela entre o preparo e
o efeito. O acesso a uma prévia já concluída preserva sua cópia
histórica. Quando o snapshot é nulo, o campo não é acrescentado ao HMAC e o
fingerprint legado continua idêntico. Traces editoriais já concluídos também
permanecem como evidência do pedido original.

## Validação e limite desta entrega

177 testes unitários dirigidos passaram. Os módulos de contexto e projeção
tiveram 100% de linhas e branches; Ruff e mypy nos sete módulos envolvidos
passaram. Seis testes PostgreSQL de storage passaram em banco isolado com
roles restritas; o banco e seus logins foram removidos ao final. Casos incluem versão e proveniência, estados sem análise e parciais,
ausência de truncamento, retirada antes de reserva, paridade editorial/visual,
fingerprint legado e revisão histórica. Sete casos integrados da cadeia com 0108/0109 passaram: captura, replay,
imutabilidade, retirada antes/durante a submissão e uma peça visual com
aprendizados persistidos fictícios. O teste da peça exigiu projeção idêntica
nos prompts editorial e visual, com HTTP simulado e somente fotos/kit autorizados.
Uma fixture UUID foi corrigida e seu caso repetido; não houve chamada paga.

Esta integração não afirma que todos os perfis já têm análise. A disponibilidade
depende da execução e persistência 0108/0109. CI integral, agenda completa e avaliação do resultado comercial permanecem
gates distintos.
