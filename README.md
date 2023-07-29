# get-some-ncbi-genomes

Download one or more NCBI genomes, given accession.

Build a CSV file containing download info:
```
get-some-ncbi-genomes GCA_002440745.1 --csv xyz.csv
```

Download the genome files directly:
```
get-some-ncbi-genomes --output-dir genomes/ -G
```
