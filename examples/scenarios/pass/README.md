O codigo atual em `src/main/java` representa o caso PASS.

Use:

```bash
python3 -m tools.ai_review.main \
  --guidelines docs/architecture-guidelines.md \
  --source-dir src/main/java \
  --output ai-review.json \
  --mode mock \
  --scenario auto
```

