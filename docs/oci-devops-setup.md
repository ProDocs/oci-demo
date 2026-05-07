# OCI DevOps Setup

Esta demo foi desenhada para o caminho mais curto possivel em OCI DevOps: um unico **Managed Build Stage** lendo o `build_spec.yaml` na raiz do repositorio.

Se o seu projeto DevOps ja esta conectado ao GitHub, use a conexao GitHub existente como source do Managed Build. Nao ha necessidade de OCI Code Repository para esta demo.

## Recursos OCI sugeridos

1. DevOps Project.
2. Source connection para o repositorio Git que contem este projeto. No seu caso, reutilize a conexao GitHub ja existente.
3. Build Pipeline com um Managed Build Stage apontando para `build_spec.yaml`.
4. Artifact Registry com tres artifacts binarios:
   - `ai-review-json`
   - `native-binary`
   - `demo-bundle`
5. Notification Topic opcional para avisar quando um build PASS/WARN/BLOCK terminar.

## Por que um unico Managed Build Stage

- Fica mais facil de explicar em slide.
- O gate da IA acontece antes do native build.
- O `ai-review.json` e o `demo-bundle.zip` saem do mesmo fluxo.
- Em caso de `BLOCK`, o build falha cedo sem gastar tempo com Oracle GraalVM for JDK 21.

## Variaveis uteis do build

| Variavel | Uso |
| --- | --- |
| `AI_REVIEW_MODE` | `mock` para demo deterministica, `oci` para chamada real ao Oracle Generative AI |
| `AI_REVIEW_SCENARIO` | `auto`, `pass`, `warn` ou `block` |
| `OCI_GENAI_AUTH_MODE` | `resource_principal`, `instance_principal`, `user_principal` ou `api_key` |
| `OCI_GENAI_INFERENCE_ENDPOINT` | Endpoint raiz do Inference API, sem `/openai/v1` |
| `OCI_GENAI_COMPARTMENT_OCID` | Compartment OCID usado na chamada de chat |
| `OCI_CONFIG_PROFILE` | Profile OCI usado com `user_principal` |
| `OCI_GENAI_BASE_URL` | Base URL OpenAI-compatible, apenas para o fallback `api_key` |
| `OCI_GENAI_ENDPOINT` | Endpoint completo do chat completions, apenas para o fallback `api_key` |
| `OCI_GENAI_MODEL` | Modelo Oracle Generative AI a ser usado |
| `OCI_GENAI_API_KEY` | API key do Oracle Generative AI, apenas para fallback legado |
| `JAVA_HOME` | Caminho do Oracle GraalVM for JDK 21 no build runner |

## Mapeamento do fluxo

1. Checkout do codigo: feito automaticamente pelo Managed Build.
2. Revisao por IA: `python3 -m tools.ai_review.main`.
3. Geracao do JSON: `ai-review.json`.
4. Gate do pipeline: `scripts/gate-ai-review.sh`.
5. Build nativo: `mvn -Pnative -DskipTests package`.
6. Publicacao de artifacts: `dist/ai-review.json`, `target/oci-ai-review-demo` e `dist/demo-bundle.zip`.

Os steps de gate, instalacao do GraalVM e native build usam `onFailure` para ainda empacotar o bundle de demo quando o pipeline falha depois da revisao por IA.

O build tambem exporta `ARTIFACT_VERSION`, para ser reutilizado em um `Deliver Artifacts` stage.

## Resource Principal para OCI DevOps

Para usar o modo recomendado no Managed Build:

1. Defina `AI_REVIEW_MODE=oci`.
2. Defina `OCI_GENAI_AUTH_MODE=resource_principal`.
3. Informe `OCI_GENAI_INFERENCE_ENDPOINT`, `OCI_GENAI_COMPARTMENT_OCID` e `OCI_GENAI_MODEL`.
4. Garanta que o build pipeline esteja em um dynamic group.
5. Adicione a policy minima para o pipeline chamar o chat do Generative AI.

### Dynamic group sugerido

```text
ALL {resource.type = 'devopsbuildpipeline', resource.compartment.id = '<compartment_ocid>'}
```

### Policies minimas sugeridas

```text
Allow dynamic-group <BuildPipelineDynamicGroup> to use generative-ai-chat in compartment <genai_compartment_name>
Allow dynamic-group <BuildPipelineDynamicGroup> to manage generic-artifacts in compartment <artifact_compartment_name>
```

Se voce quiser simplificar o primeiro setup em sandbox, pode usar uma policy mais ampla em Generative AI. Para demo madura, prefira o menor privilegio necessario.

## Observacoes pragmaticas

- Para a demo ao vivo, use `AI_REVIEW_MODE=mock` e altere apenas `AI_REVIEW_SCENARIO`.
- Para a demo real com Oracle Generative AI no OCI DevOps, mude para `AI_REVIEW_MODE=oci`, `OCI_GENAI_AUTH_MODE=resource_principal` e preencha endpoint, compartment e modelo.
- Para rodar localmente na sua maquina, prefira `OCI_GENAI_AUTH_MODE=user_principal`.
- Para rodar em uma OCI Compute fora do DevOps, use `OCI_GENAI_AUTH_MODE=instance_principal`.
- O build spec instala o RPM `graalvm-21-native-image` e usa `JAVA_HOME=/usr/lib64/graalvm/graalvm-java21`.
- No OCI DevOps Managed Build em Oracle Linux 8, o build spec tambem instala `glibc-static`, `libstdc++-static` e `zlib-static` com `--enablerepo=ol8_codeready_builder`, porque o RPM do `native-image` depende desses pacotes.
- Para publicar no Artifact Registry, use um `Deliver Artifacts` stage mapeando os outputs `ai-review-json` e `native-binary` para artifacts genericos versionados com `${ARTIFACT_VERSION}`.
