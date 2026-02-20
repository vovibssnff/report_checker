# Сборка СРД (XeLaTeX, стиль по docs/practice_report)
MAIN = main
LATEX = xelatex
LATEXFLAGS = -interaction=nonstopmode -file-line-error

.PHONY: all clean view

all: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex src/*.tex
	$(LATEX) $(LATEXFLAGS) $(MAIN) || true
	$(LATEX) $(LATEXFLAGS) $(MAIN) || true
	@test -f $(MAIN).pdf && echo "OK: $(MAIN).pdf"

clean:
	rm -f $(MAIN).aux $(MAIN).log $(MAIN).out $(MAIN).toc $(MAIN).fdb_latexmk $(MAIN).fls $(MAIN).synctex.gz

view: $(MAIN).pdf
	@echo "Откройте $(MAIN).pdf"
