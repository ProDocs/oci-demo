# Checklist OCI DevOps para a demo

Use esta ordem para montar a demo no OCI DevOps com o minimo de complexidade.

## 1. Repositorio

- Confirme que o repositorio GitHub usado pelo OCI DevOps e este projeto.
- O `build_spec.yaml` ja esta pronto na raiz do repositorio.
- O review por IA ja esta implementado em `tools/ai_review/main.py`.
- O gate ja esta implementado em `scripts/gate-ai-review.sh`.
- O empacotamento final ja esta implementado em `scripts/package-demo-bundle.sh`.

## 2. GitHub connection

- Reutilize a external connection GitHub que voce ja tem no OCI DevOps.
- Valide a connection antes do primeiro build.
- Se a validacao falhar, revise o PAT armazenado no OCI Vault.

## 3. IAM

- Crie ou confirme um dynamic group para o build pipeline.
- Regra sugerida:

```text
ALL {resource.type = 'devopsbuildpipeline', resource.compartment.id = '<compartment_ocid>'}
```

- Policy minima para a chamada real ao Oracle Generative AI:

```text
Allow dynamic-group <BuildPipelineDynamicGroup> to use generative-ai-chat in compartment <genai_compartment_name>
```

- Se a external connection usar segredo em Vault e ainda nao houver policy suficiente:

```text
Allow dynamic-group <BuildPipelineDynamicGroup> to read secret-family in compartment <vault_compartment_name>
```

- Se voce quiser adicionar Deliver Artifacts stage depois:

```text
Allow dynamic-group <BuildPipelineDynamicGroup> to manage generic-artifacts in compartment <artifact_compartment_name>
```

## 4. DevOps project

- Habilite logging no DevOps Project antes do primeiro run.
- Se quiser uma demo mais simples, comece sem Notification Topic.

## 5. Build Pipeline minimo

- Crie um Build Pipeline.
- Adicione somente um Managed Build Stage.
- Source provider: GitHub.
- Repositorio: este repo.
- Branch inicial: a branch da demo.
- Build spec file path: `build_spec.yaml`.

## 6. Variaveis do build para a primeira demo

Use o caminho mais seguro para a apresentacao:

```text
AI_REVIEW_MODE=mock
AI_REVIEW_SCENARIO=pass
OCI_GENAI_AUTH_MODE=resource_principal
GRAALVM_PACKAGE=graalvm-21-native-image
GRAALVM_HOME=/usr/lib64/graalvm/graalvm-java21
```

Depois repita mudando apenas:

- `AI_REVIEW_SCENARIO=warn`
- `AI_REVIEW_SCENARIO=block`

## 7. Variaveis para Oracle Generative AI real

Quando sair do mock:

```text
AI_REVIEW_MODE=oci
OCI_GENAI_AUTH_MODE=resource_principal
OCI_GENAI_INFERENCE_ENDPOINT=https://inference.generativeai.<regiao>.oci.oraclecloud.com
OCI_GENAI_COMPARTMENT_OCID=<compartment_ocid>
OCI_GENAI_MODEL=<modelo-disponivel-na-sua-regiao>
GRAALVM_PACKAGE=graalvm-21-native-image
GRAALVM_HOME=/usr/lib64/graalvm/graalvm-java21
```

## 8. O que o stage faz

Dentro do Managed Build Stage, o fluxo ja esta pronto:

1. prepara workspace
2. executa revisao por IA
3. grava `ai-review.json`
4. aplica o gate
5. instala Oracle GraalVM for JDK 21
6. executa `mvn -Pnative -DskipTests package`
7. gera `dist/ai-review.json`
8. gera `dist/demo-bundle.zip`

## 9. Resultado esperado em cada cenario

- `pass`: pipeline segue para o native build e termina com sucesso.
- `warn`: pipeline segue para o native build e termina com sucesso.
- `block`: pipeline falha antes do native build.

Em todos os casos:

- `ai-review.json` e gerado
- o resultado aparece nos logs
- o bundle da demo e preparado pelos scripts

## 10. Roteiro recomendado para a apresentacao

Use duas execucoes manuais do mesmo pipeline:

1. Run de sucesso
   - `AI_REVIEW_MODE=mock`
   - `AI_REVIEW_SCENARIO=pass`
   - o publico ve que a IA aprova, o gate libera e o native build com GraalVM 21 acontece

2. Run de falha
   - `AI_REVIEW_MODE=mock`
   - `AI_REVIEW_SCENARIO=block`
   - o publico ve que a IA bloqueia, o build falha cedo e o `ai-review.json` continua disponivel

Opcional:

- rode um terceiro build com `AI_REVIEW_SCENARIO=warn` para mostrar que observacao nao bloqueia entrega

## 11. Trigger opcional

- Depois que o manual run estiver ok, crie um Trigger.
- Evento recomendado para demo: `Push`.
- Branch recomendada: a branch da demo.
- Configure o webhook no GitHub com `application/json`.

## 12. Deliver Artifacts stage opcional

Se voce quiser persistir os arquivos no Artifact Registry alem dos outputs do Managed Build:

- crie dois artifacts do tipo Generic Artifact
- use nomes alinhados aos outputs do build:
  - `ai-review-json`
  - `demo-bundle`
- depois adicione um Deliver Artifacts stage

Observacao pragmatica:

- para a demo ao vivo, o caminho mais simples continua sendo usar apenas o Managed Build Stage
- adicione Deliver Artifacts somente quando quiser guardar os arquivos fora do build run

## 13. Auth modes da implementacao

Nesta implementacao:

- `resource_principal`: modo recomendado para OCI DevOps Managed Build
- `instance_principal`: use apenas se mover o reviewer para uma OCI Compute instance
- `user_principal`: modo local usando `~/.oci/config`
- `api_key`: fallback legado

## 14. Roteiro de Console

Se voce quiser seguir a configuracao tela por tela na OCI Console, use:

- `docs/oci-console-click-runbook.md`
