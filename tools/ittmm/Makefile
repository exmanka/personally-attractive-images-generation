FILE = `cat NAME`


all:
	pdflatex $(FILE)
	pdflatex $(FILE)
	-pybtex $(FILE)
	pdflatex $(FILE)
	pdflatex $(FILE)
	mv $(FILE).pdf ../../doc/ittmm

cleanall: clean

clean:
	-rm -f *.{log,toc,tac,aux,dvi,ps,bbl,blg,tmp,nav,out,snm,vrb,rel,thm,rel,*~} $(FILE).pdf
	-rm -f split*
	rm -rf out auto
	for i in $(ALLSUBDIRS); do \
	    (cd $$i; make clean) || exit 1; \
	done


