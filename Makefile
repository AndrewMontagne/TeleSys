.PHONY: *

help: ## Shows this help prompt
	@echo "Usage: make target1 [target2] ..."
	@echo ""
	@echo "Target                          Description"
	@echo "================================================================================"
	@awk -F ':|##' '/^[^\t].+?:.*?##/ {printf "\033[36m%-30s\033[0m %s\n", $$1, $$NF }' $(MAKEFILE_LIST)

build: ## Builds the font
	python3 bitmap2ttf/pngtottf.py --width 8 --height 16 --weight Medium -t TeleSys.ttf -n TeleSys -c "SIL Open Font Licence 1.1" --version "2.0.0-alpha+f8616e6" *.png