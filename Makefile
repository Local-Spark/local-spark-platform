.PHONY: install lint format types motion-test motion-eval-test motion-eval motion-diversity-eval motion-review-eval unit test ci up migrate

MOTION_CASE ?= .local/evals/motion-library-round-2026-11-06/proposal/cafe-reel-library.json
BUDGET_USD ?= 0.75

install:
	uv sync --frozen
lint:
	uv run ruff check app migrations scripts
	uv run ruff format --check app migrations scripts
format:
	uv run ruff check app migrations scripts --fix
	uv run ruff format app migrations scripts
types:
	uv run mypy app --exclude app/tests
	uv run mypy --explicit-package-bases scripts/evals/motion_review_eval.py scripts/evals/motion_review_evidence.py scripts/evals/motion_review_report.py scripts/evals/motion_declarative_review_eval.py scripts/evals/motion_declarative_render.py scripts/evals/motion_feedback_contracts.py scripts/evals/motion_feedback_inputs.py scripts/evals/motion_feedback_review_eval.py
motion-eval-test:
	uv run pytest scripts/evals/test_motion*.py -q
	node --test scripts/evals/motion_audio.test.cjs
motion-test: motion-eval-test
	node --test --experimental-test-coverage --test-coverage-include='app/assets/motion*_renderer/*.cjs' --test-coverage-lines=100 --test-coverage-branches=100 --test-coverage-functions=100 app/tests/node/*.test.cjs
motion-eval:
	.venv/bin/python scripts/evals/motion_eval.py --case "$(MOTION_CASE)" --budget-usd "$(BUDGET_USD)" $(if $(filter 1,$(EXECUTE)),--execute --open,) $(if $(filter 1,$(RETRY_REJECTED)),--retry-rejected,) $(if $(RESPONSE),--from-response "$(RESPONSE)",)
motion-diversity-eval: BUDGET_USD = 2.25
motion-diversity-eval:
	.venv/bin/python scripts/evals/motion_batch_eval.py --manifest .local/evals/motion-diversity-round-2026-11-06/proposal/batch.json --budget-usd "$(BUDGET_USD)" $(if $(filter 1,$(EXECUTE)),--execute --open,)
motion-review-eval:
	.venv/bin/python scripts/evals/motion_review_eval.py $(if $(REVIEW_RUN),--run "$(REVIEW_RUN)",) $(if $(filter 1,$(EXECUTE)),--execute --budget-usd "$(REVIEW_BUDGET_USD)",)
unit: motion-test
	uv run pytest app/tests/unit -q
test: motion-test
	uv run pytest --cov=app --cov-report=term-missing --cov-report=xml -q
ci: lint types test
up:
	docker compose up -d postgres temporal mailpit
migrate:
	uv run alembic upgrade head
