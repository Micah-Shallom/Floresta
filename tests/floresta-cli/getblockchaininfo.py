# SPDX-License-Identifier: MIT OR Apache-2.0

"""
floresta_cli_getblockchaininfo.py

Functional test for `getblockchaininfo`. Mines blocks via utreexod, then
compares florestad's response against bitcoind's field-by-field. Bitcoind is
treated as the source of truth, so future Core API changes surface as test
failures rather than silent drift.
"""

import time
import pytest

TIMEOUT_SECONDS = 30
MINE_BLOCKS = 10
# Fields where florestad intentionally diverges from bitcoind:
#   - `pruned` is always True for florestad (Utreexo discards full blocks)
#   - `size_on_disk` reports the mmap-allocated capacity for florestad, not
#     actual blk*.dat size
FLORESTA_SPECIFIC_FIELDS = ("pruned", "size_on_disk")


@pytest.mark.rpc
def test_get_blockchain_info(florestad_bitcoind_utreexod_with_chain):
    """
    Compare florestad's getblockchaininfo response against bitcoind's after a
    small chain extension. Iterates bitcoind's keys so any new field added in
    a future Core release fails the test until florestad implements it.
    """
    florestad, bitcoind, utreexod = florestad_bitcoind_utreexod_with_chain(MINE_BLOCKS)

    end = time.time() + TIMEOUT_SECONDS
    while time.time() < end:
        if (
            florestad.rpc.get_block_count()
            == bitcoind.rpc.get_block_count()
            == utreexod.rpc.get_block_count()
            == MINE_BLOCKS
        ):
            break
        time.sleep(0.5)

    floresta_info = florestad.rpc.get_blockchain_info()
    bitcoind_info = bitcoind.rpc.get_blockchain_info()

    for key, bval in bitcoind_info.items():
        if key in FLORESTA_SPECIFIC_FIELDS:
            continue
        fval = floresta_info[key]
        if key == "difficulty":
            # Allow small differences in floating-point representation
            assert round(fval, 3) == round(bval, 3)
        else:
            assert fval == bval, f"{key}: floresta={fval} bitcoind={bval}"
