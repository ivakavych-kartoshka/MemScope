.PHONY: install test demo plot calibrate ablate

install:
	python3 -m pip install -e .

test:
	pytest -q

demo:
	python3 scripts/run_synthetic_demo.py --config configs/synthetic_demo.yaml

plot:
	python3 scripts/make_plots.py --input outputs/synthetic_demo/metrics.json --output outputs/synthetic_demo/metrics.png

calibrate:
	python3 scripts/run_experiment.py --config configs/synthetic_demo.yaml --stage calibrate

ablate:
	python3 scripts/run_experiment.py --config configs/synthetic_demo.yaml --stage ablate
