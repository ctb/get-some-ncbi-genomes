# @CTB document me!
import sys
import os
import argparse
import urllib.request
from urllib.parse import urlparse
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


def get_genome_info(ident, *, verbose=False, quiet=False):
        genome_url, assembly_report_url = url_for_accession(ident,
                                                            verbose=verbose,
                                                            quiet=quiet)
        taxid = get_taxid_from_assembly_report(assembly_report_url,
                                               verbose=verbose,
                                               quiet=quiet)
        tax_name = get_tax_name_for_taxid(taxid,
                                          verbose=verbose,
                                          quiet=quiet)

        d = dict(
            ident=ident,
            genome_url=genome_url,
            assembly_report_url=assembly_report_url,
            display_name=tax_name,
        )

        return d


def download_genome(info_d, *, output_filename=None, output_directory=None,
                    verbose=False, quiet=False):
    ident = info_d['ident']
    genome_url = info_d['genome_url']
    up = urlparse(genome_url)

    if not output_filename:
        outfilename = f"{ident}.genomic.fna.gz"
    if output_directory:
        outfilename = os.path.join(output_directory, outfilename)

    with urllib.request.urlopen(genome_url) as response:
        content = response.read()
        if not quiet:
            print(f"writing genome to '{outfilename}'", file=sys.stderr)
        with open(outfilename, 'wb') as outfp:
            outfp.write(content)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("accessions", nargs='*')
    p.add_argument("--from-file", help="load accessions from this file")
    p.add_argument("--csv", default=None,
                   help='output CSV information about genome')
    p.add_argument("--output-directory", help="save output files here")
    p.add_argument("-G", "--download-genomes", action='store_true',
                   help="download genome files")
    p.add_argument("-v", "--verbose", action='store_true',
                   help='turn on verbose reporting')
    p.add_argument("-q", "--quiet", action='store_true',
                   help='turn off non-error output')
    args = p.parse_args()

    accessions = list(args.accessions)
    if args.from_file:
        with open(args.from_file, 'rt') as fp:
            acclines = [ x.strip() for x in fp if x.strip() ]

        if not args.quiet:
            print(f"loaded {len(acclines)} accessions from '{args.from_file}'",
                  file=sys.stderr)
        accessions.extend(acclines)

    # remove redundancy
    accessions = set(accessions)

    # check input arguments
    if not accessions:
        print(f"error - no accessions given on command line or in from-file",
              file=sys.stderr)
        sys.exit(-1)

    # check output arguments
    errexit = False
    if not args.download_genomes and not args.csv:
        print(f"no output information given!? consider -G/--download-genomes and/or --csv", file=sys.stderr)
        errexit = True
    if args.download_genomes and not args.output_directory:
        print(f"-G/--download-genomes given, but no output directory.")
        errexit = True

    if errexit:
        sys.exit(-1)

    ### ok! in good shape! go forth and NCBI!

    acc_info = []
    for ident in accessions:
        if not args.quiet:
            print(f"starting work on '{ident}'", file=sys.stderr)

        info_d = get_genome_info(ident, verbose=args.verbose,
                                 quiet=args.quiet)
        acc_info.append(info_d)

        if not args.quiet:
            print(f"info retrieved for {ident} - {info_d['display_name']}", file=sys.stderr)

    # initialize output CSV, if desired
    if args.csv:
        if not args.quiet:
            print(f"writing CSV output to '{args.csv}'", file=sys.stderr)
        fieldnames = ["ident", "genome_url", "assembly_report_url", "display_name"]
        with open(args.csv, "w", newline="") as fp:
            w = csv.DictWriter(fp, fieldnames=fieldnames)
            w.writeheader()
            for info_d in acc_info:
                w.writerow(info_d)

    # save genomes?
    if args.download_genomes:
        try:
            os.mkdir(args.output_directory)
        except FileExistsError:
            pass

        for info_d in acc_info:
            download_genome(info_d, output_directory=args.output_directory,
                            verbose=args.verbose, quiet=args.quiet)
            ident = info_d['ident']
            genome_url = info_d['genome_url']
            up = urlparse(genome_url)
            outfilename = f"{ident}.genomic.fna.gz"
            outfilename = os.path.join(args.output_directory, outfilename)

            with urllib.request.urlopen(genome_url) as response:
                content = response.read()
                if not args.quiet:
                    print(f"writing to '{outfilename}'", file=sys.stderr)
                with open(outfilename, 'wb') as outfp:
                    outfp.write(content)

    return 0


#
# CLI plugin for sourmash - supports 'sourmash scripts get-genomes'
#

class Command_DownloadNCBI(CommandLinePlugin):
    command = 'get-genomes'
    description = "retrieve one or more NCBI genomes"

    def __init__(self, subparser):
        super().__init__(subparser)
        # add argparse arguments here.
        subparser.add_argument('accessions', nargs='+')
        subparser.add_argument('--output-directory', default=None,
                               help="directory to save genomes")

    def main(self, args):
        # code that we actually run.
        super().main(args)
        for ident in args.accessions:
            info_d = get_genome_info(ident, verbose=args.debug,
                                     quiet=args.quiet)

            csv_out = f"{ident}.info.csv"
            if args.output_directory:
                csv_out = os.path.join(args.output_directory, csv_out)

            if not args.quiet:
                print(f"writing CSV output to '{csv_out}'", file=sys.stderr)
            fieldnames = ["ident", "genome_url", "assembly_report_url", "display_name"]
            with open(csv_out, "w", newline="") as fp:
                w = csv.DictWriter(fp, fieldnames=fieldnames)
                w.writeheader()
                w.writerow(info_d)

            download_genome(info_d, output_directory=args.output_directory,
                            verbose=args.debug, quiet=args.quiet)
            
