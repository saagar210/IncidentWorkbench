.PHONY: verify unit integration contract

verify:
	cd .. && bash .codex/scripts/run_verify_commands.sh

unit:
	pytest -q -m "unit"

integration:
	pytest -q -m "integration"

contract:
	pytest -q -m "contract"
