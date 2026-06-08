PAPER=main

.PHONY: all figures clean

all: figures
	pdflatex -interaction=nonstopmode -halt-on-error $(PAPER).tex
	bibtex $(PAPER)
	pdflatex -interaction=nonstopmode -halt-on-error $(PAPER).tex
	pdflatex -interaction=nonstopmode -halt-on-error $(PAPER).tex

figures:
	cd .. && uv run python paper/scripts/build_assets.py

clean:
	rm -f $(PAPER).aux $(PAPER).bbl $(PAPER).blg $(PAPER).log $(PAPER).out
