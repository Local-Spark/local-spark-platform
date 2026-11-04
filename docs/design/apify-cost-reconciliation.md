# Reconciliação de custos Apify

O estado terminal do run não torna imediatamente definitivo o custo informado.
A [documentação do GET Actor run](https://docs.apify.com/api/v2/actor-run-get)
avisa que os primeiros dados de custo após o término podem estar incompletos e
recomenda consultar novamente após cerca de dez segundos. Os adapters locais
adotam margem de trinta segundos e verificam a concordância dos contadores de
eventos quando disponíveis. Até esse momento, preservam a reserva e repetem
somente GET do mesmo run; não repetem a coleta paga.

O ensaio controlado identificou cinco recibos provisórios entre onze runs.
O total previamente registrado era 89.801 micros de dólar; os metadados posteriores
totalizaram 120.501 micros. A diferença de 30.700 micros pertence às mesmas
execuções, não a chamadas novas. A conversão continua arredondando o valor
informado para cima no micros de dólar; não houve mudança de arredondamento.

## Regras da migração 0111

As funções públicas de contatos e feed conservam suas assinaturas e as guardas
de organização, negócio, ator, efeito, executor e run. Ambas usam um único
procedimento privado para aplicar os valores. O runtime não pode invocar esse
procedimento nem ler ou alterar diretamente as observações financeiras.

- O primeiro recibo troca a reserva pelo valor informado e retira o hold do
  agregado mensal, como antes. Ausência de recibo conserva a reserva.
- Um recibo maior posterior soma somente a diferença ao acumulado do piloto e
  ao comprometido do mês original. Não retira o hold uma segunda vez.
- Repetir o mesmo valor é idempotente. Um valor menor gera conflito explícito e
  não devolve verba automaticamente. Créditos ou estornos exigem evidência própria.
- Cada mudança aceita deixa uma linha imutável com valor anterior, valor recebido,
  reserva original, data, identificação durável e motivo de bloqueio, se houver.
  A mesma transação atualiza os agregados e insere audit/outbox.
- Valor acima da reserva também é evidência de custo e deve ser registrado. Ele
  bloqueia novas admissões no piloto. Valores acima dos tetos do piloto, mensal,
  fornecedor ou pesquisa também bloqueiam novas admissões.

O teto configurado nunca aumenta. O contador de despesa pode representar um
excesso observado: impedir essa representação ocultaria o custo verdadeiro.
Quando ocorre excesso, a transação desativa o piloto e conclui normalmente para
preservar a observação. Não levanta uma exceção depois dessa gravação, pois isso
desfaria o registro. As funções de admissão continuam exigindo piloto ativo e
saldo dentro do teto antes de qualquer efeito novo.

Todas as admissões e correções usam o mesmo advisory lock global de custos. Se
uma admissão consumir primeiro o saldo que havia sido liberado, a correção
registra a diferença e bloqueia o piloto antes de liberar o lock. Se a correção
ocorrer primeiro, a admissão enxerga o saldo atualizado ou o bloqueio. Nenhuma
requisição de rede ocorre durante essa transação.

O wrapper de contatos aceita somente inteiros não negativos até o mesmo limite
técnico do parser financeiro. Ele permite que o SQL registre um excesso real,
em vez de descartá-lo por superar a reserva. Isso não autoriza nova cobrança.

O downgrade automático é recusado depois de qualquer recibo novo ou revisão.
Em um banco vazio, restaura os procedimentos anteriores e o CHECK original.
A reconciliação de um banco já existente deve ocorrer pelos serviços guardados,
após backup, usando somente metadados autenticados do run e sem ajustes diretos
nos acumulados.

Validação: fixtures fictícias em banco PostgreSQL exclusivo `_test`, logins
restritos, roundtrip vazio da migração, replay concorrente, revisão de contatos
e feed, falta de permissão, token incorreto, isolamento de organização/ator,
overrun inicial e tardio, corrida com nova admissão, tetos por mês/fornecedor/
pesquisa e rollback diante de agregados inconsistentes. Nenhum teste desse
recorte inicia run externo.

Foram aprovadas 38 integrações PostgreSQL e 12 testes unitários com cobertura
integral do wrapper, além de Ruff, mypy e roundtrip vazio. A revisão independente
não encontrou bloqueador material. No banco local, após backup verificado, os
onze recibos foram reprocessados pelos writers restritos: o acumulado passou de
247.801 para 278.501 micros, diferença exata de 30.700. Os valores incluem os
holds Google/Jev preservados; não representam faturamento final desses fornecedores.
