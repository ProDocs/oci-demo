# OCI DevOps + Oracle Generative AI + GraalVM 21 Demo

Demo minima para apresentar um pipeline OCI DevOps que faz revisao arquitetural por IA antes do build, gera `ai-review.json` e decide se o native build segue ou nao com Oracle GraalVM for JDK 21.

## O que a demo mostra

1. Checkout do codigo no OCI DevOps.
2. Revisao arquitetural antes da compilacao.
3. Geracao obrigatoria de `ai-review.json`.
4. Gate do pipeline por JSON:
   - `PASS` e `WARN` seguem para o native build.
   - `BLOCK` falha o build antes da compilacao.
5. Native build de uma API Java minima com Oracle GraalVM for JDK 21.
6. Publicacao de `dist/ai-review.json` e `dist/demo-bundle.zip`.

## Estrutura do repositorio

```text
.
|-- README.md
|-- build_spec.yaml
|-- docs
|   |-- architecture-guidelines.md
|   `-- oci-devops-setup.md
|-- examples
|   |-- oci-devops.env.example
|   `-- scenarios
|-- pom.xml
|-- scripts
|   |-- gate-ai-review.sh
|   `-- package-demo-bundle.sh
|-- src/main/java/com/example/ociaidemo
|   |-- Application.java
|   |-- controller/GreetingController.java
|   |-- model/GreetingResponse.java
|   |-- repository/GreetingRepository.java
|   `-- service/GreetingService.java
`-- tools/ai_review
    |-- clients.py
    |-- main.py
    |-- models.py
    |-- prompt_builder.py
    |-- review_engine.py
    `-- rules.py
```

## Aplicacao Java

- Endpoint REST: `GET /api/greetings?name=OCI`
- Healthcheck: `GET /health`
- Arquitetura propositalmente didatica:
  - controller recebe HTTP,
  - service aplica regra de negocio,
  - repository fica isolado do controller.

## Revisao por IA

O pipeline chama:

```bash
python3 -m tools.ai_review.main \
  --guidelines docs/architecture-guidelines.md \
  --source-dir src/main/java \
  --output ai-review.json
```

### Modos disponiveis

- `mock`: modo padrao da demo. Deterministico, rapido e sem credenciais.
- `oci`: chama Oracle Generative AI com autenticacao OCI.

### Modos de autenticacao OCI

- `resource_principal`: modo recomendado para OCI DevOps Managed Build.
- `instance_principal`: para quando o reviewer roda dentro de uma Compute instance OCI.
- `user_principal`: para rodar localmente com `~/.oci/config`.
- `api_key`: fallback legado usando endpoint OpenAI-compatible com API key.

### Saida obrigatoria

```json
{
  "result": "PASS|WARN|BLOCK",
  "comments": "feedback textual"
}
```

Se a chamada real ao Oracle Generative AI falhar, o script gera `BLOCK` com a mensagem de erro. Assim o `ai-review.json` continua existindo e o build para antes da compilacao.

No OCI DevOps, o caminho preferido e `resource_principal`, porque o build runner ja vem com OCI SDKs preautenticados pelo principal do build pipeline.

## Como executar localmente

### 1. Revisao por IA

```bash
python3 -m tools.ai_review.main \
  --guidelines docs/architecture-guidelines.md \
  --source-dir src/main/java \
  --output ai-review.json \
  --mode mock \
  --scenario auto
```

### 2. Gate local

```bash
bash scripts/gate-ai-review.sh ai-review.json
```

### 3. Rodar a API em JVM

```bash
mvn package
java -jar target/oci-ai-review-demo.jar
```

### 4. Native build com GraalVM 21

```bash
export JAVA_HOME=/usr/lib64/graalvm/graalvm-java21
export PATH="${JAVA_HOME}/bin:${PATH}"
mvn -Pnative -DskipTests package
```

O binario final esperado fica em `target/oci-ai-review-demo`.

## Como demonstrar PASS, WARN e BLOCK

### Roteiro curto de demo no OCI DevOps

Para apresentacao ao vivo, o melhor roteiro e fazer duas execucoes do mesmo pipeline:

1. **Execucao de sucesso**
   - `AI_REVIEW_MODE=mock`
   - `AI_REVIEW_SCENARIO=pass`
   - resultado esperado:
     - `ai-review.json` com `PASS`
     - gate libera o fluxo
     - native build com GraalVM 21 acontece
     - build termina com sucesso

2. **Execucao de falha**
   - `AI_REVIEW_MODE=mock`
   - `AI_REVIEW_SCENARIO=block`
   - resultado esperado:
     - `ai-review.json` com `BLOCK`
     - gate interrompe o pipeline antes da compilacao
     - build termina como failed
     - `dist/ai-review.json` e `dist/demo-bundle.zip` continuam sendo gerados

Esse roteiro e o mais simples porque demonstra o valor do gate por IA sem depender de mudanca de codigo entre um run e outro.

### Jeito mais simples para live demo

Mantenha `AI_REVIEW_MODE=mock` e altere apenas `AI_REVIEW_SCENARIO` no build run:

- `pass`: revisao aprova.
- `warn`: revisao aprova com observacoes.
- `block`: revisao barra o native build.
- `auto`: avalia o codigo atual com heuristica simples.

### Jeito mais visual com mudanca de codigo

- PASS: rode `bash scripts/apply-scenario.sh pass`.
- WARN: rode `bash scripts/apply-scenario.sh warn`.
- BLOCK: rode `bash scripts/apply-scenario.sh block`.

Depois execute a revisao com `--scenario auto` para a IA inferir o resultado a partir do codigo atual:

```bash
python3 -m tools.ai_review.main \
  --guidelines docs/architecture-guidelines.md \
  --source-dir src/main/java \
  --output ai-review.json \
  --mode mock \
  --scenario auto
```

Detalhes adicionais estao em `examples/scenarios/README.md`.

## OCI DevOps

Use um unico Managed Build Stage apontando para `build_spec.yaml`.

Se o seu projeto DevOps ja esta integrado com GitHub, use a conexao GitHub existente como fonte primaria do Managed Build. Nao e necessario mover o codigo para OCI Code Repository para esta demo.

O fluxo e:

1. OCI faz checkout do codigo.
2. O step de IA gera `ai-review.json`.
3. O gate le `result`.
4. Em `PASS` ou `WARN`, instala Oracle GraalVM for JDK 21 e roda `mvn -Pnative -DskipTests package`.
5. Em `BLOCK`, empacota o review e falha o build antes da compilacao.
6. Se houver falha depois do gate, o pipeline ainda empacota o review no bundle.
7. Publica `dist/ai-review.json` e `dist/demo-bundle.zip`.

Veja `docs/oci-devops-setup.md` para o setup recomendado.
Para o passo a passo tela por tela da Console OCI, veja `docs/oci-console-click-runbook.md`.

## Oracle Generative AI real

Quando quiser trocar o mock por integracao real no OCI DevOps, configure as variaveis abaixo em um branch dedicado do `build_spec.yaml` ou no ambiente do runner:

```bash
export AI_REVIEW_MODE=oci
export OCI_GENAI_AUTH_MODE=resource_principal
export OCI_GENAI_MODEL="<modelo-disponivel-na-sua-regiao>"
export OCI_GENAI_COMPARTMENT_OCID="<compartment-ocid-do-genai>"
export OCI_GENAI_INFERENCE_ENDPOINT="https://inference.generativeai.<regiao>.oci.oraclecloud.com"
```

### Rodando localmente com autenticacao OCI

```bash
python3 -m pip install oci
export AI_REVIEW_MODE=oci
export OCI_GENAI_AUTH_MODE=user_principal
export OCI_CONFIG_PROFILE=DEFAULT
export OCI_GENAI_MODEL="<modelo-disponivel-na-sua-regiao>"
export OCI_GENAI_COMPARTMENT_OCID="<compartment-ocid-do-genai>"
export OCI_GENAI_INFERENCE_ENDPOINT="https://inference.generativeai.<regiao>.oci.oraclecloud.com"
```

### Fallback por API key

Se voce realmente quiser manter o caminho antigo por API key:

```bash
export AI_REVIEW_MODE=oci
export OCI_GENAI_AUTH_MODE=api_key
export OCI_GENAI_MODEL="<modelo-disponivel-na-sua-regiao>"
export OCI_GENAI_BASE_URL="https://inference.generativeai.<regiao>.oci.oraclecloud.com/openai/v1"
export OCI_GENAI_API_KEY="<api-key>"
```

## Assuncoes pragmaticas

- A demo envia **codigo relevante** para a IA, nao diff Git, para manter o OCI DevOps simples.
- O build runner esperado e Oracle Linux com `yum`.
- O exemplo assume Oracle GraalVM for JDK 21 instalado pelo pacote `graalvm-21-native-image`.
- Se o seu tenancy usar outro pacote, ajuste apenas `GRAALVM_PACKAGE` e `GRAALVM_HOME`.
- No modo `oci`, a demo usa OCI Python SDK com IAM auth como caminho principal e API key apenas como fallback legado.
