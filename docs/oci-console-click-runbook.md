# Roteiro de clique na Console OCI

Este runbook foi escrito para a sua apresentacao ao vivo.

Objetivo:

- deixar um pipeline OCI DevOps pronto para demonstrar um caso verde
- deixar o mesmo pipeline pronto para demonstrar um caso vermelho
- evitar depender de troca manual de variavel no palco

## Estrategia recomendada para a demo

Para este repositorio, o jeito mais limpo de demonstrar e usar dois branches:

- `demo-pass`: codigo aderente, IA retorna `PASS`, build segue ate o native image
- `demo-block`: controller acessa repository diretamente, IA retorna `BLOCK`, build falha antes da compilacao

O `build_spec.yaml` ja esta preparado para isso porque usa:

- `AI_REVIEW_MODE=mock`
- `AI_REVIEW_SCENARIO=auto`

Assim, o resultado da revisao depende do codigo do commit escolhido no build run.

## 0. Preparacao no GitHub antes da Console

No repositorio local:

```bash
cd /Users/jonesncosta/Documents/GitHub/oci-demo

bash scripts/apply-scenario.sh pass
git switch -c demo-pass
git add .
git commit -m "demo: pass baseline"
git push -u origin demo-pass

git switch -c demo-block
bash scripts/apply-scenario.sh block
git add .
git commit -m "demo: block controller reaches repository"
git push -u origin demo-block

git switch demo-pass
bash scripts/apply-scenario.sh pass
```

Se os branches ja existirem, apenas atualize e faca push.

## 1. IAM do pipeline

### 1.1 Dynamic group

Caminho:

- `Identity & Security`
- `Dynamic Groups`

Crie um dynamic group com nome sugerido:

- `dg-oci-ai-review-demo`

Matching rule sugerida:

```text
ALL {resource.type = 'devopsbuildpipeline', resource.compartment.id = '<compartment_ocid>'}
```

## 1.2 Policies

Caminho:

- `Identity & Security`
- `Policies`
- `Create Policy`
- ative o editor manual

Nome sugerido:

- `policy-oci-ai-review-demo`

Statements minimos para o pipeline:

```text
Allow dynamic-group dg-oci-ai-review-demo to manage devops-family in compartment <compartment_name>
Allow dynamic-group dg-oci-ai-review-demo to read secret-family in compartment <vault_compartment_name>
```

Se sua tenancy usa identity domains, prefixe o dynamic group:

```text
Allow dynamic-group <domain-name>/dg-oci-ai-review-demo to manage devops-family in compartment <compartment_name>
```

Para Oracle Generative AI real, adicione tambem:

```text
Allow dynamic-group dg-oci-ai-review-demo to use generative-ai-chat in compartment <genai_compartment_name>
```

Se voce quiser usar um `Deliver Artifacts` stage depois, adicione:

```text
Allow dynamic-group dg-oci-ai-review-demo to manage generic-artifacts in compartment <artifact_compartment_name>
```

Se for validar ou criar a conexao GitHub a partir de um usuario que nao e administrador, o grupo humano tambem precisa de:

```text
Allow group <seu-grupo-de-usuarios> to use devops-connection in compartment <compartment_name>
```

## 2. DevOps Project

Caminho:

- `Developer Services`
- `DevOps`
- `Projects`

Crie ou reutilize um projeto.

Nome sugerido:

- `oci-ai-review-demo`

Antes do primeiro build:

- habilite logging do projeto

## 3. External Connection com GitHub

Se a sua conexao GitHub ja existe, faca apenas a validacao e pule a criacao.

Caminho:

- `Developer Services`
- `DevOps`
- `Projects`
- selecione `oci-ai-review-demo`
- `External Connections`

### 3.1 Se a conexao ja existe

- abra a conexao existente
- valide a conexao
- confirme que ela enxerga o repositorio `oci-demo`

### 3.2 Se precisar criar

- clique `Create External Connection`
- tipo: `GitHub`
- nome sugerido: `github-oci-demo`
- selecione o Vault e o secret que contem o PAT do GitHub
- crie a conexao

## 4. Create Build Pipeline

Caminho:

- `Developer Services`
- `DevOps`
- `Projects`
- selecione `oci-ai-review-demo`
- `Create build pipeline`

Nome sugerido:

- `oci-ai-review-build`

Descricao sugerida:

- `AI review gate + GraalVM 21 native build`

## 5. Add Managed Build Stage

Caminho:

- abra o pipeline `oci-ai-review-build`
- clique no `+`
- `Add stage`
- tipo `Managed Build`

Preencha assim:

- `Stage name`: `ai-review-and-native-build`
- `Build runner shape`: `Quick start`
- `Base container image`: `Oracle Linux 8`
- `Build specification file path`: `build_spec.yaml`

Primary code repository:

- `Connection type`: `GitHub`
- `Connection`: sua conexao GitHub existente
- `Repository`: `oci-demo`
- `Branch`: `demo-pass`
- `Build Source Name`: `Source`

Observacoes:

- para esta demo minima, nao configure private access
- a shape quick start deve ser o primeiro teste; se native-image reclamar de memoria, volte e customize a shape

## 6. Primeiro run: caso de sucesso

Caminho:

- abra o pipeline `oci-ai-review-build`
- clique `Start Manual Run`

Preencha assim:

- `Build run name`: `demo-pass-run`

Para este repositorio, deixe sem override adicional.

Clique `Start Manual Run`.

O que mostrar no palco:

1. step `AI architecture review`
2. log com `ai-review.json`
3. `result = PASS`
4. step `Gate native build` liberado
5. step `Install GraalVM 21`
6. step `Build native executable`
7. outputs do build com `ai-review-json` e `demo-bundle`

## 7. Segundo run: caso de falha controlada pela IA

Caminho:

- abra o mesmo pipeline `oci-ai-review-build`
- clique `Start Manual Run`

Preencha assim:

- `Build run name`: `demo-block-run`
- clique `Show advanced options`
- escolha o mesmo repositorio GitHub
- selecione a branch `demo-block`
- selecione o commit mais recente dessa branch

Clique `Start Manual Run`.

O que mostrar no palco:

1. step `AI architecture review`
2. log com `ai-review.json`
3. `result = BLOCK`
4. step `Gate native build` falhando antes da compilacao
5. pipeline ficando `Failed`
6. `ai-review.json` e `demo-bundle.zip` ainda gerados pelo `onFailure`

## 8. O que exatamente o pipeline ja faz neste repositorio

O pipeline do repositorio ja esta preparado para:

1. gerar `ai-review.json`
2. copiar o review para `dist/ai-review.json`
3. interromper o build em `BLOCK`
4. instalar Oracle GraalVM for JDK 21 com `graalvm-21-native-image`
5. usar `JAVA_HOME=/usr/lib64/graalvm/graalvm-java21`
6. gerar `dist/demo-bundle.zip`

## 9. Salvar binario nativo e review no Artifact Registry

Observacao importante:

- o build gera um binario nativo, nao uma imagem Docker
- para esta demo, o destino correto e `Artifact Registry` com artifacts genericos

### 9.1 Crie ou reutilize um repositrio no Artifact Registry

Caminho:

- `Developer Services`
- `Artifact Registry`
- `Repositories`

Crie um repositorio generic, por exemplo:

- `oci-ai-review-demo-repo`

### 9.2 Crie referencias de artifact dentro do DevOps Project

Caminho:

- `Developer Services`
- `DevOps`
- `Projects`
- selecione `oci-ai-review-demo`
- `Artifacts`
- `Add artifact`

Crie estes dois artifacts:

1. Artifact do review JSON
   - `Name`: `ai-review-json-artifact`
   - `Type`: `General artifact`
   - `Artifact source`: `Artifact Registry repository`
   - `Repository`: `oci-ai-review-demo-repo`
   - `Set Custom Location`
   - `Path`: `oci-ai-review-demo/ai-review.json`
   - `Version`: `${ARTIFACT_VERSION}`
   - habilite parameterizacao

2. Artifact do binario nativo
   - `Name`: `native-binary-artifact`
   - `Type`: `General artifact`
   - `Artifact source`: `Artifact Registry repository`
   - `Repository`: `oci-ai-review-demo-repo`
   - `Set Custom Location`
   - `Path`: `oci-ai-review-demo/oci-ai-review-demo`
   - `Version`: `${ARTIFACT_VERSION}`
   - habilite parameterizacao

### 9.3 Adicione o Deliver Artifacts stage

Caminho:

- abra o pipeline `oci-ai-review-build`
- clique no `+` depois do Managed Build stage
- `Add stage`
- tipo `Deliver Artifacts`

Preencha assim:

- `Stage name`: `deliver-build-artifacts`

Associe os artifacts com os outputs do Managed Build:

- artifact `ai-review-json-artifact` <- build output `ai-review-json`
- artifact `native-binary-artifact` <- build output `native-binary`

O `ARTIFACT_VERSION` vem do proprio build spec e sera mostrado como exported variable no build run.

Resultado:

- o `ai-review.json` vai para o Artifact Registry
- o binario nativo `oci-ai-review-demo` vai para o Artifact Registry

## 10. Trigger opcional para depois da validacao manual

Crie o trigger apenas depois que os dois runs manuais estiverem funcionando.

Caminho:

- `Developer Services`
- `DevOps`
- `Projects`
- selecione `oci-ai-review-demo`
- `Triggers`
- `Create Trigger`

Preencha assim:

- `Name`: `github-push-demo-pass`
- `Source connection`: sua conexao GitHub
- `Action`: pipeline `oci-ai-review-build`
- `Event`: `Push`
- `Source branch`: `demo-pass`

No final:

- copie a `trigger URL`
- copie o `trigger secret`

Depois, no GitHub:

- adicione um webhook para essa URL
- configure o secret informado pela OCI
- `Content type`: `application/json`

## 11. Ativando Oracle Generative AI real depois

Depois que a demo mock estiver estavel, ative a integracao real.

Para este repositorio, o jeito mais simples e criar um branch dedicado, por exemplo:

- `demo-real-genai`

Nesse branch, ajuste os defaults de ambiente do `build_spec.yaml` para:

```text
AI_REVIEW_MODE=oci
OCI_GENAI_AUTH_MODE=resource_principal
OCI_GENAI_INFERENCE_ENDPOINT=https://inference.generativeai.<regiao>.oci.oraclecloud.com
OCI_GENAI_COMPARTMENT_OCID=<compartment_ocid>
OCI_GENAI_MODEL=<modelo-disponivel-na-sua-regiao>
```

O restante do pipeline pode continuar igual.

Quando voce rodar esse branch, abra o log do step `AI architecture review` e confirme estas linhas:

```text
[AI_REVIEW] mode=oci auth_mode=resource_principal ...
[AI_REVIEW] client=oci-sdk auth_mode=resource_principal ...
[AI_REVIEW] invoking OCI Generative AI chat
[AI_REVIEW] oci_response status=200 opc_request_id=<valor-retornado-pelo-servico>
[AI_REVIEW] OCI Generative AI chat completed
```

Esse `opc_request_id` e a melhor evidencia de apresentacao de que a chamada saiu do runner e chegou ao servico real do Oracle Generative AI.

## 12. Ordem ideal da apresentacao

1. Mostre rapidamente o repositrio GitHub com os dois branches `demo-pass` e `demo-block`.
2. Abra o pipeline no OCI DevOps.
3. Rode `demo-pass-run`.
4. Mostre o `PASS`, o native build e os outputs.
5. Rode `demo-block-run` escolhendo `demo-block` em `Show advanced options`.
6. Mostre o `BLOCK` e o fail fast antes da compilacao.
7. Feche reforcando que o desperdicio de CI foi evitado.

## 13. Se quiser manter a demo mais simples ainda

Nao adicione agora:

- `Deliver Artifacts` stage
- `Notification Topic`
- `Private access`

Para a sua apresentacao, um unico `Managed Build` stage e suficiente.
