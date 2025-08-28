"""
Tests for get-some-ncbi-genomes.
"""
import os
import pytest
import csv

import sourmash
import sourmash_tst_utils as utils
from sourmash_tst_utils import SourmashCommandFailed


def test_run_sourmash(runtmp):
    with pytest.raises(SourmashCommandFailed):
        runtmp.sourmash('', fail_ok=True)

    print(runtmp.last_result.out)
    print(runtmp.last_result.err)
    assert runtmp.last_result.status != 0                    # no args provided, ok ;)


def test_run_sourmash_plugin(runtmp):
    runtmp.sourmash('scripts', 'get-genomes', 'GCA_002440745.1',
                    '--output-dir', runtmp.output(''))

    print(runtmp.last_result.out)
    print(runtmp.last_result.err)
    assert runtmp.last_result.status == 0

    assert os.path.exists(runtmp.output('GCA_002440745.1.info.csv'))
    assert os.path.exists(runtmp.output('GCA_002440745.1_genomic.fna.gz'))


def test_empty_display_name(runtmp):
    # if display_name is empty, output ident when using sourmash plugin
    runtmp.sourmash('scripts', 'get-genomes', 'GCA_000272025.2',
                    '--output-dir', runtmp.output(''))

    print(runtmp.last_result.out)
    print(runtmp.last_result.err)
    assert runtmp.last_result.status == 0

    with open(runtmp.output('GCA_000272025.2.info.csv'), 'r', newline='') as fp:
        r = csv.DictReader(fp)
        rows = list(r)
        assert len(rows) == 1

        assert rows[0]['display_name'] == 'GCA_000272025.2'
