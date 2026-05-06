# Demo Scenarios

Voce pode demonstrar os tres resultados de duas formas:

1. Mais simples: use `AI_REVIEW_MODE=mock` e altere `AI_REVIEW_SCENARIO` para `pass`, `warn` ou `block`.
2. Mais visual: copie um dos arquivos desta pasta para `src/main/java/...` antes do commit e deixe o modo `mock` em `auto`.

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

