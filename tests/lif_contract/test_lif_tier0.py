"""Python and the documented vector must match. Silence cuts outgoing spikes only."""

from protocols.lif.tier0 import golden_slice, run_lif

SPIKES = [
    "4:0", "8:0", "8:1", "12:0", "12:2", "13:1", "16:0", "16:3", "17:2", "18:1",
    "20:0", "21:3", "22:2", "24:0", "24:1", "26:3", "28:0", "28:2", "29:1", "32:0",
    "32:3", "33:2", "34:1", "36:0", "37:3", "38:2", "40:0", "40:1",
]


def test_golden_slice_spikes() -> None:
    result = golden_slice()
    assert result["engine"] == "nexo-lif-tier0-v1"
    assert result["spikes"] == SPIKES
    assert result["rates_per_ks"] == [250, 175, 150, 125]


def test_silence_cuts_outgoing_only() -> None:
    edges = [(0, 1, 12), (1, 2, 12), (2, 3, 12)]
    cut = run_lif(n=4, edges=edges, ticks=40, drive=[0], silence=[1])
    assert cut["rates_per_ks"] == [250, 175, 0, 0]
