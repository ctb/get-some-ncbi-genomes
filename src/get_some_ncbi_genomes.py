# @CTB document me!
import sys
import argparse
import urllib.request
import csv

import sourmash

from sourmash.logging import debug_literal
from sourmash.plugins import CommandLinePlugin

from lxml import etree


def url_for_accession(accession, *, verbose=False, quiet=False):
    accsplit = accession.strip().split("_")
    assert len(accsplit) == 2, f"ERROR: '{accession}' should have precisely one underscore!"

    db, acc = accsplit
    if '.' in acc:
        number, version = acc.split(".")
    else:
        number, version = acc, '1'
    number = "/".join([number[p : p + 3] for p in range(0, len(number), 3)])
    url = f"https://ftp.ncbi.nlm.nih.gov/genomes/all/{db}/{number}"
    if verbose:
        print(f"opening directory: {url}", file=sys.stderr)

    with urllib.request.urlopen(url) as response:
        all_names = response.read()

    if verbose:
        print("done!", file=sys.stderr)

    all_names = all_names.decode("utf-8")

    full_name = None
    for line in all_names.splitlines():
        if line.startswith(f'<a href='):
            name=line.split('"')[1][:-1]
            db_, acc_, *_ = name.split("_")
            if db_ == db and acc_.startswith(acc):
                full_name = name
                break

    if full_name is None:
        return None
    else:
        url = "htt" + url[3:]
        return (
            f"{url}/{full_name}/{full_name}_genomic.fna.gz",
            f"{url}/{full_name}/{full_name}_assembly_report.txt",
        )


def get_taxid_from_assembly_report(url, *, verbose=False, quiet=False):
    if verbose:
        print(f"opening assembly report: {url}", file=sys.stderr)
    with urllib.request.urlopen(url) as response:
        content = response.read()
    if verbose:
        print("done!", file=sys.stderr)

    content = content.decode("utf-8").splitlines()
    for line in content:
        if "Taxid:" in line:
            line = line.strip()
            pos = line.find("Taxid:")
            assert pos >= 0
            pos += len("Taxid:")
            taxid = line[pos:]
            taxid = taxid.strip()
            return taxid

    assert 0


def get_tax_name_for_taxid(taxid, *, verbose=False, quiet=False):
    tax_url = (
        f"https://www.ncbi.nlm.nih.gov/taxonomy/?term={taxid}&report=taxon&format=text"
    )
    if verbose:
        print(f"opening tax url: {tax_url}", file=sys.stderr)
    with urllib.request.urlopen(tax_url) as response:
        content = response.read()

    if verbose:
        print("done!", file=sys.stderr)

    root = etree.fromstring(content)
    notags = etree.tostring(root).decode("utf-8")
    if notags.startswith("<pre>"):
        notags = notags[5:]
    if notags.endswith("</pre>"):
        notags = notags[:-6]
    notags = notags.strip()

    return notags


def main():
    p = argparse.ArgumentParser()
    p.add_argument("accessions", nargs='+')
    p.add_argument("-o", "--output", default=None,
                   help='output CSV')
    p.add_argument("-v", "--verbose", action='store_true',
                   help='turn on verbose reporting')
    p.add_argument("-q", "--quiet", action='store_true',
                   help='turn off non-error output')
    args = p.parse_args()

    acc_info = []
    for ident in args.accessions:
        if not args.quiet:
            print(f"starting work on '{ident}'", file=sys.stderr)
        genome_url, assembly_report_url = url_for_accession(ident,
                                                            verbose=args.verbose,
                                                            quiet=args.quiet)
        taxid = get_taxid_from_assembly_report(assembly_report_url,
                                               verbose=args.verbose,
                                               quiet=args.quiet)
        tax_name = get_tax_name_for_taxid(taxid,
                                          verbose=args.verbose,
                                          quiet=args.quiet)

        d = dict(
            ident=ident,
            genome_url=genome_url,
            assembly_report_url=assembly_report_url,
            display_name=tax_name,
        )
        acc_info.append(d)

        if not args.quiet:
            print(f"info retrieved for {ident} - {tax_name}", file=sys.stderr)

    # initialize output, if desired
    if args.output:
        if not args.quiet:
            print(f"writing CSV output to '{args.output}'", file=sys.stderr)
        fieldnames = ["ident", "genome_url", "assembly_report_url", "display_name"]
        with open(args.output, "w", newline="") as fp:
            w = csv.DictWriter(fp, fieldnames=fieldnames)
            w.writeheader()
            for info_d in acc_info:
                w.writerow(info_d)

    return 0


#
# CLI plugin for sourmash - supports 'sourmash scripts get-genomes'
#

class Command_XYZ(CommandLinePlugin):
    command = 'get-genomes'
    description = "retrieve one or more NCBI Genomes"

    def __init__(self, subparser):
        super().__init__(subparser)
        # add argparse arguments here.
        debug_literal('RUNNING cmd_xyz.__init__')

    def main(self, args):
        # code that we actually run.
        super().main(args)
        print('RUNNING cmd', self, args)
