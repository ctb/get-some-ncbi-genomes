"""
Tests for get-some-ncbi-genomes.
"""
import os
import pytest

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
    assert os.path.exists(runtmp.output('GCA_002440745.1.genomic.fna.gz'))
