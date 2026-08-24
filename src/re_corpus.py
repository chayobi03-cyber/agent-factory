"""Synthetic RE (Radiated Emission) legacy document corpus for the M1 RE
Hybrid RAG Domain Pack.

Per docs/RE_POC.md, the PoC target is "20+ representative legacy documents".
This module ships a smaller, honestly-scoped starter corpus (8 documents,
2 of which are revisions of the same document to exercise revision-compare
queries) covering the ontology entities named in RE_POC.md: equipment, DUT,
chamber, antenna, cable, connector, enclosure, frequency, limit, test_setup,
measurement, peak, mitigation, failure_mode.

This is SYNTHETIC content written for this repository, consistent with the
project's existing convention (see scripts/factory_demo.py) of using labeled
synthetic evidence rather than real customer/test data. It is not sourced
from any real product, chamber, or lab report.
"""
from __future__ import annotations

from typing import TypedDict


class RawDocument(TypedDict):
    document_id: str
    revision_id: str
    title: str
    doc_type: str
    text: str


CORPUS: list[RawDocument] = [
    {
        "document_id": "DOC-RE-001",
        "revision_id": "REV-A",
        "title": "EUT-7 Radiated Emissions Test Report",
        "doc_type": "test_report",
        "text": (
            "Device under test EUT-7 was evaluated for radiated emissions in "
            "semi-anechoic chamber CH-2 per CISPR 32 Class B limits. "
            "Test setup used a biconical antenna at 3 meters for 30-1000 MHz "
            "and a horn antenna above 1 GHz. A peak emission of 38.2 dBuV/m "
            "was measured at 132 MHz, exceeding the Class B limit of 35.6 "
            "dBuV/m by 2.6 dB at that frequency. No other peaks exceeded "
            "the limit line. The exceedance was traced to the unshielded "
            "power cable connecting EUT-7 to the enclosure fan connector."
        ),
    },
    {
        "document_id": "DOC-RE-001",
        "revision_id": "REV-B",
        "title": "EUT-7 Radiated Emissions Test Report (Retest)",
        "doc_type": "test_report",
        "text": (
            "Retest of EUT-7 after mitigation. A ferrite choke was added to "
            "the power cable near the enclosure connector and the cable was "
            "rerouted away from the fan aperture. Radiated emissions were "
            "re-measured in chamber CH-2 with the same biconical antenna "
            "setup at 3 meters. The previously observed 132 MHz peak dropped "
            "to 31.4 dBuV/m, 4.2 dB below the Class B limit of 35.6 dBuV/m. "
            "No exceedances were observed across 30-1000 MHz. The mitigation "
            "is confirmed effective for EUT-7."
        ),
    },
    {
        "document_id": "DOC-RE-002",
        "revision_id": "REV-A",
        "title": "CISPR 32 Class B Limit Table Excerpt",
        "doc_type": "specification",
        "text": (
            "CISPR 32 Class B radiated emission limits at 3 meters: "
            "30-230 MHz: 35.6 dBuV/m (quasi-peak). "
            "230 MHz-1 GHz: 42.6 dBuV/m (quasi-peak). "
            "1-3 GHz: 50.0 dBuV/m (average), 70.0 dBuV/m (peak). "
            "These limits apply to information technology equipment intended "
            "for use in a residential environment."
        ),
    },
    {
        "document_id": "DOC-RE-003",
        "revision_id": "REV-A",
        "title": "Chamber CH-2 Calibration and Setup Notes",
        "doc_type": "internal_wiki",
        "text": (
            "Semi-anechoic chamber CH-2 supports 3 meter and 10 meter test "
            "distances. Standard antenna set: biconical antenna for "
            "30-300 MHz, log-periodic antenna for 300 MHz-1 GHz, horn "
            "antenna for 1-18 GHz. Turntable and antenna mast are automated "
            "via the chamber control PC. Site attenuation was last validated "
            "against CISPR 16-1-4 in March. Cable routing inside the chamber "
            "must avoid the direct line of sight between EUT and antenna to "
            "prevent scattering artifacts."
        ),
    },
    {
        "document_id": "DOC-RE-004",
        "revision_id": "REV-A",
        "title": "EUT-12 Power Supply Radiated Emissions Failure Analysis",
        "doc_type": "test_report",
        "text": (
            "EUT-12 switching power supply exhibited a radiated emission "
            "peak of 46.1 dBuV/m at 340 MHz, exceeding the CISPR 32 Class B "
            "limit of 42.6 dBuV/m by 3.5 dB. Root cause investigation traced "
            "the emission to common-mode current on the DC output cable "
            "connector, correlated with the switching frequency harmonics of "
            "the buck converter. A common-mode choke and a shielded "
            "connector backshell were recommended as mitigation. This "
            "failure mode (unshielded switching-supply output cable acting "
            "as an unintentional antenna) has also been observed on EUT-7 "
            "and EUT-19."
        ),
    },
    {
        "document_id": "DOC-RE-005",
        "revision_id": "REV-A",
        "title": "EUT-19 Radiated Emissions Test Report",
        "doc_type": "test_report",
        "text": (
            "EUT-19 was tested in chamber CH-2 per CISPR 32 Class B. All "
            "measured emissions from 30 MHz to 1 GHz remained below the "
            "applicable limit line, with the highest margin point at "
            "210 MHz measuring 29.0 dBuV/m against a 35.6 dBuV/m limit "
            "(6.6 dB margin). No mitigation was required. Test setup: "
            "biconical antenna, 3 meter distance, horizontal and vertical "
            "polarization both scanned."
        ),
    },
    {
        "document_id": "DOC-RE-006",
        "revision_id": "REV-A",
        "title": "Mitigation Techniques Reference Guide",
        "doc_type": "internal_wiki",
        "text": (
            "Common radiated emission mitigation techniques, in typical "
            "order of application: (1) ferrite choke or common-mode choke "
            "on the offending cable, closest to the source connector; "
            "(2) cable rerouting away from enclosure apertures and seams; "
            "(3) shielded cable or shielded connector backshell; "
            "(4) gasketing or additional enclosure seam shielding; "
            "(5) circuit-level filtering at the source (e.g. added output "
            "capacitance or snubber on a switching converter). Ferrite "
            "chokes are generally tried first because they require no "
            "hardware redesign."
        ),
    },
    {
        "document_id": "DOC-RE-007",
        "revision_id": "REV-A",
        "title": "DUT Preconditioning and Ground Loop Notes",
        "doc_type": "internal_wiki",
        "text": (
            "Devices under test should be powered up and allowed to reach "
            "thermal steady state for at least 15 minutes before radiated "
            "emissions measurement begins, as clock and switching-supply "
            "frequencies can drift while warming up. Ground loops between "
            "the EUT chassis and the chamber turntable ground can produce "
            "spurious low-frequency peaks unrelated to the DUT's actual "
            "emission profile; use an isolated ground strap if this is "
            "suspected."
        ),
    },
    {
        "document_id": "DOC-RE-008",
        "revision_id": "REV-A",
        "title": "EUT-24 Wiring Harness Radiated Emissions Failure Report",
        "doc_type": "test_report",
        "text": (
            "EUT-24 failed CISPR 32 Class B with a peak of 44.8 dBuV/m at "
            "185 MHz, exceeding the 35.6 dBuV/m limit by 9.2 dB. The "
            "unshielded internal wiring harness connecting the main board "
            "to the front-panel connector was identified as the radiating "
            "element: harness length was approximately one quarter "
            "wavelength at 185 MHz, making it an efficient unintentional "
            "antenna for common-mode current from the main board. The "
            "harness ran parallel to, and 4 mm from, an unshielded seam in "
            "the enclosure, which further coupled the emission to free "
            "space through the seam."
        ),
    },
    {
        "document_id": "DOC-RE-009",
        "revision_id": "REV-A",
        "title": "Wiring Harness Design Guidelines for Radiated Emissions Control",
        "doc_type": "specification",
        "text": (
            "Wiring harness routing guidelines to reduce radiated emissions: "
            "keep harness length short relative to a quarter wavelength of "
            "the highest switching harmonic of concern; route harnesses "
            "away from enclosure seams, vents, and apertures by at least "
            "20 mm where possible; twist signal-return pairs to reduce loop "
            "area; add a common-mode choke at the connector end of any "
            "harness carrying switching-supply return current; and avoid "
            "running a harness parallel to an unshielded seam, since "
            "parallel routing increases near-field coupling into the "
            "aperture. These guidelines directly address the failure mode "
            "seen on EUT-24 and are consistent with the general mitigation "
            "order in the mitigation techniques reference guide."
        ),
    },
]
