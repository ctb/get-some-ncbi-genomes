# get-some-ncbi-genomes

## Installation

```
pip install get-some-ncbi-genomes
```

## Usage

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

## Support

We suggest filing issues in [the main sourmash issue tracker](https://github.com/dib-lab/sourmash/issues) as that receives more attention!

## Dev docs

`get-some-ncbi-genomes` is developed at https://github.com/ctb/get-some-ncbi-genomes/

### Testing

Run:
```
pytest tests
```

### Generating a release

Bump version number in `pyproject.toml` and push.

Make a new release on github.

Then pull, and:

```
python -m build
```

followed by `twine upload dist/...`.
