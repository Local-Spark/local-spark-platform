# Ensaio pareado de skills — tentativa interrompida

Em 29/10/2026 o proprietário autorizou até **US$ 5 no total** para comparar
texto com e sem skills, usando quatro casos fictícios; não autorizou imagem ou
publicação. O plano previa oito chamadas à Responses API, `gpt-5-mini`, mesmo
caso, modelo, configuração e schema em cada par; somente a skill mudaria.
Era um ensaio isolado de instruções, não do fluxo da aplicação. Os casos não
constituem holdout independente e a avaliação de titulares continua pendente.

## Resultado e custo

O dry run preparou oito pedidos sem rede e 12 testes locais passaram. A primeira
operação (`F02:control`) ficou **incerta** e o lote parou; há **zero respostas
completas disponíveis** e nenhuma comparação de qualidade a relatar. O runner
capturou a exceção sem gravar categoria, HTTP status ou identificador de resposta;
não é possível determinar a causa ou afirmar que a requisição não chegou ao
provedor. Consulta posterior somente de acesso ao modelo retornou HTTP 200;
essa consulta não reconcilia nem explica a tentativa de geração.

O ledger privado `.local/evals/skills-paired-20261029/ledger.sqlite3` mantém
uma reserva de **US$ 0,625** e estado `uncertain`; nenhum valor foi liquidado.
Uso e custo efetivos são **desconhecidos**; reserva não é custo faturado e o
teto local não limita outras chamadas nem a fatura da conta. As sete operações
restantes não foram enviadas. Não repetir a tentativa, liberar a reserva ou
prosseguir automaticamente enquanto não houver prova de reconciliação segura.

## Identidade para apuração

- Data da tentativa: `2026-10-29T17:15:19.792267+00:00`.
- `X-Client-Request-Id`: `a16204b2-52ef-52f8-aecf-29bef425a633`.
- Hash do pedido: `db3320f24bc21bea5efda5c2854ec649ae922ca06ec772433874d9266c4eb889`.
- Modelo solicitado: `gpt-5-mini`; endpoint: `POST /v1/responses`; `store: false`.
- Não foram capturados `response_id`, `x-request-id`, uso ou saída do provedor.

O ID de cliente é recuperável da operação e do hash gravados antes do envio;
é útil para apuração, mas não comprova idempotência nem execução. Segundo a
[referência oficial da API](https://developers.openai.com/api/reference/overview),
o suporte pode pesquisar o recebimento usando esse ID. Não há garantia de que
consiga recuperar a resposta ou esclarecer o custo. O acesso a uso agregado não
comprova isoladamente o resultado desta operação. Contatar suporte requer ação
autorizada pelo usuário; não foi feito neste ensaio.

O runner usado, os testes e a entrada sem gabarito estão preservados junto ao
ledger em `.local/evals/skills-paired-20261029/`; o ledger não é apagado ou
alterado por esta documentação. O runner não deve ser reexecutado para tentar
resolver a incerteza. A versão de diagnóstico para ensaios futuros deve gravar
categoria segura, status e IDs disponíveis antes de descartar erros, mantendo
as mesmas reservas e a regra de não reenviar respostas incertas. Um protótipo
com execução real desabilitada foi preservado como `runner-diagnostic-prototype.py`
no mesmo diretório; três testes com transporte simulado passaram. Ele não recupera
o erro anterior nem autoriza uma nova tentativa.
