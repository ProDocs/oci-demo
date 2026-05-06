# Architecture Guidelines

Estas guidelines sao o contrato arquitetural usado pela etapa de IA antes do build.

## Regras obrigatorias

1. Controller nao deve acessar repository diretamente.
2. Business logic deve ficar na service layer.
3. A separacao entre controller, service e repository deve ser clara.
4. Dependencias proibidas ou violacoes arquiteturais claras devem gerar `BLOCK`.
5. Pontos discutiveis, pequenos riscos ou melhorias devem gerar `WARN`.
6. Codigo aderente, pequeno e facil de explicar deve gerar `PASS`.

## Exemplos que devem gerar BLOCK

- Controller importando ou instanciando um repository.
- Business logic relevante implementada dentro do controller.
- Acoplamento direto entre a camada HTTP e acesso a dados.

## Exemplos que podem gerar WARN

- TODOs em pontos importantes do fluxo.
- Nomes pouco claros.
- Comentarios indicando debito tecnico pequeno.

## Resposta esperada da IA

A resposta final deve ser exatamente:

```json
{
  "result": "PASS|WARN|BLOCK",
  "comments": "feedback textual"
}
```
