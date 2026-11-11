# Pacote externo de motion — etapa 6

Implementado e exportado em 10/11/2026. O titular confirmou em entrevista o uso
da proposta Café Pausa da etapa 3: “abrir espaço para uma pausa”, em dois momentos.
Essa escolha autoriza preparar o teste; não aprova uma execução ainda inexistente.

## Entrega

- [ZIP completo](../../.local/exports/motion-cafe-pausa-20261110.zip).
- [Instruções de uso](../../.local/exports/motion-cafe-pausa-20261110/LEIA-ME.md).
- [Prompt integral](../../.local/exports/motion-cafe-pausa-20261110/PROMPT-INTEGRAL.md).
- [Corpo exato da chamada](../../.local/exports/motion-cafe-pausa-20261110/generation-request.json).
- [Manifesto e hashes](../../.local/exports/motion-cafe-pausa-20261110/manifest.json).
- [Contrato de saída](../../.local/exports/motion-cafe-pausa-20261110/output-contract.json).

São 39 arquivos. Para começar em um chat, anexar o prompt integral e as 12 imagens
na ordem de `input/order.json`: seis referências de Felipe Borges/Lucas Leite e
seis quadros da gravação. Os três exemplos do repertório e os dois da skill já
estão no texto integral. O LEIA-ME explica envio em lotes e registro de diferenças.

ZIP: 4.509.567 bytes; SHA-256
`45229038492e0e6842dac633397e6558e0ff679245291da5b8a313a218a5c3be`.
Payload exato: SHA-256
`cf50949e4b615a1398ed45755d8e64fe95bfd9ce7f840ee989c114e62efc2788`.

O pacote inclui fonte MP4, duas fontes tipográficas/licença e os runtimes reais
MotionV1/MotionElementsV1, com catálogo expandido e atribuição. Esses arquivos
ficam em `execution/`: a API de geração recebe seus metadados/APIs, não seus bytes.
Enviar o vídeo ou os runtimes também ao chat amplia a entrada e precisa ser
registrado como variação. Não há novas imagens geradas nem render da peça.

## Fidelidade ao produto e limites

`MotionContext.capture` e o exportador usam o mesmo `capture_motion_guidance`
extraído do montador existente, com contratos, skill, estilos e repertório atuais.
O corpo completo vem de `OpenAIMotionProvider.build_request`, inclusive schema,
parâmetros e imagens base64. Não foi criado um prompt de construção paralelo.
O arquivo legível acrescenta apenas títulos/caminhos para representar os campos
do JSON; os textos e o contrato de saída estão completos.

Contexto factual, metadados de mídia e seis PNGs são reutilizados da entrada
registrada em `reel-storyboard-composition-20261109/generation-request.json`.
Não houve consulta de estado atual no banco, extração de novos quadros ou alegação
de nova admissão operacional. Kit Café Pausa, fonte de 11.176 ms, saída de 11.200 ms
em 720×1280/30 fps e áudio original foram mantidos. O vídeo de entrada efetiva tem
SHA-256 `dd3f0265a4b2d94206188f46c094dc0177663e1a529b9ad2e0718a1dfad78a34`.

Mudanças explícitas para este teste:

- Briefing/direção da etapa 3, em vez das imposições antigas de desenhos/três cenas.
- Skill v3, contrato criativo v5, crítica v2 e repertório business-reel-v1 atuais.
- IDs locais novos, sem operação ou pedido gravado/despachado no produto.
- Ilustrações desabilitadas nesta entrada; nenhum orçamento anterior reaproveitado.
- Modelo/limite do JSON preservam os parâmetros de comparação da prova anterior
  (`gpt-6.1-sol`, high, 64.000 na geração), sem restringir o modelo externo do titular.

Dados operacionais privados, configuração de execução, orçamento antigo e campos
não selecionados não são exportados. O utilitário não carrega `.env`, credenciais,
banco ou cliente Temporal; seu transporte do modelo recusa qualquer envio.
Não executa contagem remota, submit, geração de assets ou render. Também não
executa automaticamente código que vier do modelo externo.

## Reprodução e validação

Na raiz do projeto, para nova pasta (não sobrescreve destino ou ZIP existentes):

```sh
.venv/bin/python -m scripts.evals.motion_external_export --output .local/exports/motion-cafe-pausa-nova-pasta
.venv/bin/python -m scripts.evals.motion_external_export --verify .local/exports/motion-cafe-pausa-nova-pasta
```

Os argumentos `--prior-payload`, `--source`, `--direction` e `--brief` permitem
apontar os mesmos insumos em outro local. O recorte suporta a prova registrada
sem fotos/logotipo/fatos adicionais; casos diferentes exigem revisão explícita,
não importação silenciosa de contexto. O script e os testes estão em `scripts/evals/`.

Passaram 69 testes curtos: 53 de contexto/skills/controles e 16 do exportador,
com mídia sintética nos testes. O módulo de contexto alterado atingiu 100% de
linhas/ramos na cobertura dirigida. Testes verificam igualdade com o payload do
produto, anexos/base64, ausência de sentinelas privadas, runtimes, ZIP, adulteração,
preservação dos insumos e bloqueio de rede. Ruff e tipos aprovados; sem CI global
ou teste SQL. O pacote real passou pela verificação de hashes, associação de
imagens e integridade do ZIP; padrões de credenciais não foram encontrados.

Payload: 1.995.484 bytes; prompt legível: 90.981 bytes. São tamanhos em bytes,
não contagem de tokens nem custo. Um chat pode mudar papéis, schema, raciocínio,
ferramentas e leitura dos anexos. O teste externo deve registrar essas diferenças.

## Próximo passo

As seis etapas de preparação estão concluídas localmente. Aguardar do titular a
resposta integral, modelo, anexos usados, alterações e avaliação do acabamento.
Ainda não há prova visual nova, validação do áudio nem comparação controlada de
modelos. Nenhuma chamada paga ou produção integrada está autorizada por este pacote.
