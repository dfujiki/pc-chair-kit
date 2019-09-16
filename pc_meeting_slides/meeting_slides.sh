python meeting_slides_generator.py $1 $2 > presentation.tex
latex presentation.tex 
latex presentation.tex 
dvips presentation.dvi 
ps2pdf presentation.ps 
mv presentation.pdf ${2}_presentation.pdf  
rm -rf presentation.out presentation.toc presentation.snm presentation.nav presentation.log presentation.dvi presentation.aux presentation.ps
evince ${2}_presentation.pdf  
