# SYNC TODO (auto-created)

- [ ] Fix THINKER model name mismatches: mistral -> mistral:latest (config + router + tests)
- [ ] Update backend/.env to the exact Phase 5 values
- [ ] Restart backend and verify:
  - [ ] /health returns database/redis ok
  - [ ] /api/models/health shows all_models_ok=true and both models available=true
- [ ] Delete this file after the batch is completed
