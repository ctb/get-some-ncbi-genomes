# get-some-ncbi-genomes

Download one or more NCBI genomes, given accession.

Build a CSV file containing download info:
```
get-some-ncbi-genomes GCA_002440745.1 --csv xyz.csv
```

Download the genome files directly:
```
get-some-ncbi-genomes --output-dir genomes/ --download-genomes GCA_002440745.1
```

Use the sourmash plugin to download genome files and make an info.csv:
```
sourmash scripts get-genomes GCA_002440745.1
```
