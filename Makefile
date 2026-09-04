.PHONY: install fetch classify analyze gold eval test all

install:  ; pip install -r requirements.txt
fetch:    ; python -m src.fetch
classify: ; python -m src.classify
analyze:  ; python -m src.analyze
gold:     ; python -m eval.build_gold_template
eval:     ; python -m eval.eval_classify
test:     ; python -m pytest tests/ -q

all: fetch classify analyze
	@echo "Done. See RESULTS.md and data/results.json"
