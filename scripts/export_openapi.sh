#!/usr/bin/env bash
set -euo pipefail
cd backend
./.venv/bin/python - <<'PY' > /tmp/openapi.yaml
import json
from main import app

print(json.dumps(app.openapi(), indent=2, sort_keys=True))
PY
