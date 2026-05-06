# Demo Scenarios

Voce pode demonstrar os tres resultados de duas formas:

1. Mais simples: use `AI_REVIEW_MODE=mock` e altere `AI_REVIEW_SCENARIO` para `pass`, `warn` ou `block`.
2. Mais visual: troque o codigo-fonte antes do commit e rode a IA em `auto`.

## Jeito recomendado para trocar o codigo

Use o script abaixo:

```bash
bash scripts/apply-scenario.sh pass
bash scripts/apply-scenario.sh warn
bash scripts/apply-scenario.sh block
```

Depois valide localmente:

```bash
python3 -m tools.ai_review.main \
  --guidelines docs/architecture-guidelines.md \
  --source-dir src/main/java \
  --output ai-review.json \
  --mode mock \
  --scenario auto
```

Com isso voce passa a ter dois codigos de exemplo reais para demo:

- `pass`: baseline aderente a arquitetura
- `block`: controller acessando repository diretamente, o que deve gerar `BLOCK`

## Copia rapida dos cenarios visuais

### WARN

```bash
cp examples/scenarios/warn/GreetingService.java src/main/java/com/example/ociaidemo/service/GreetingService.java
```

### BLOCK

```bash
cp examples/scenarios/block/GreetingController.java src/main/java/com/example/ociaidemo/controller/GreetingController.java
```

### PASS

O codigo atual em `src/main/java` e o baseline PASS da demo.
