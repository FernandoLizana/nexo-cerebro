# Docker validation

Build and run the pre-release gate **without host networking**:

```bash
docker compose -f docker-compose.validate.yml build
docker compose -f docker-compose.validate.yml run --rm --network none nexo-validate
```

Or:

```bash
docker build -t nexo-collective-swarm:validate .
docker run --rm --network none nexo-collective-swarm:validate
```

`--network none` ensures the validation image cannot phone home during the gate.

Host alternative (same script):

```bash
python -m pip install -e ".[dev]"
python scripts/validate_pre_release.py
```
