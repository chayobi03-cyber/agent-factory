"""Synthetic RE (Radiated Emission) legacy document corpus for the M1 RE
Hybrid RAG Domain Pack.

Per docs/RE_POC.md, the PoC target is "20+ representative legacy documents".
This module meets it: 30 documents over 25 distinct document identifiers, five
of which carry a second revision so revision-comparison queries have real
before/after pairs rather than a single synthetic one. Between them they cover
every ontology entity named in RE_POC.md -- equipment, DUT, chamber, antenna,
cable, connector, enclosure, frequency, limit, test_setup, measurement, peak,
mitigation, failure_mode -- and every relation: tested_with, connected_to,
measured_at, exceeds, mitigated_by, correlates_with, reproduced_by.

The documents interlock on purpose. A guideline document names the failure it
was written for; a retest names the report it supersedes; two analyses of
EUT-44 reach opposite conclusions from the same measurement. Queries that need
two documents to answer are therefore answerable, and a retriever that returns
only the lexically-nearest fragment is measurably wrong rather than merely
unlucky.

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
    {
        "document_id": "DOC-RE-004",
        "revision_id": "REV-B",
        "title": "EUT-12 Radiated Emissions Retest After Common-Mode Choke",
        "doc_type": "test_report",
        "text": (
            "Retest of EUT-12 following the mitigation recommended in the "
            "original failure analysis. A common-mode choke was fitted to "
            "the DC output cable at the connector end and a shielded "
            "backshell was installed. The 340 MHz peak fell from 46.1 "
            "dBuV/m to 39.8 dBuV/m, now 2.8 dB below the CISPR 32 Class B "
            "limit of 42.6 dBuV/m. A secondary peak at 680 MHz, the next "
            "switching harmonic, rose slightly to 38.4 dBuV/m but remains "
            "compliant. The choke is confirmed effective at the fundamental "
            "harmonic; the shielded backshell contribution could not be "
            "separated in this test because both changes were applied "
            "together."
        ),
    },
    {
        "document_id": "DOC-RE-005",
        "revision_id": "REV-B",
        "title": "EUT-19 Radiated Emissions Retest at 10 Meters in Chamber CH-5",
        "doc_type": "test_report",
        "text": (
            "EUT-19 was re-measured at 10 meters in fully-anechoic chamber "
            "CH-5 to confirm the 3 meter result obtained in CH-2. The "
            "highest emission was again at 210 MHz, measuring 19.4 dBuV/m "
            "against the 10 meter Class B limit of 25.6 dBuV/m, a 6.2 dB "
            "margin. The margin at 10 meters agrees with the 6.6 dB margin "
            "measured at 3 meters to within measurement uncertainty, so "
            "the EUT-19 pass is reproduced at both distances. No mitigation "
            "was required."
        ),
    },
    {
        "document_id": "DOC-RE-010",
        "revision_id": "REV-A",
        "title": "EUT-31 Clock Harmonic Radiated Emissions Test Report",
        "doc_type": "test_report",
        "text": (
            "EUT-31 was tested in chamber CH-2 against CISPR 32 Class B. A "
            "narrowband peak of 44.3 dBuV/m was measured at 375 MHz, "
            "exceeding the 42.6 dBuV/m limit by 1.7 dB. The frequency is "
            "the fifteenth harmonic of the 25 MHz main board crystal "
            "oscillator, and the peak was narrowband with a bandwidth "
            "below the 120 kHz receiver resolution bandwidth, which "
            "distinguishes it from the broadband switching-supply "
            "signatures seen on EUT-12 and EUT-63. Emission was maximized "
            "at 180 degrees turntable azimuth with the antenna at 1.4 "
            "meters mast height, horizontal polarization."
        ),
    },
    {
        "document_id": "DOC-RE-010",
        "revision_id": "REV-B",
        "title": "EUT-31 Retest With Spread-Spectrum Clocking Enabled",
        "doc_type": "test_report",
        "text": (
            "EUT-31 was retested with spread-spectrum clocking enabled on "
            "the 25 MHz oscillator at a modulation depth of 0.5 percent "
            "down-spread. The 375 MHz peak dropped to 38.1 dBuV/m, 4.5 dB "
            "below the Class B limit, because the harmonic energy is "
            "redistributed across a wider band and the quasi-peak detector "
            "no longer integrates it into a single narrow bin. No new "
            "peaks appeared elsewhere in the 30 MHz to 1 GHz scan. Note "
            "that spread-spectrum clocking reduces the measured level "
            "without reducing total emitted energy, so it is a measurement-"
            "compliance mitigation rather than a source-level fix."
        ),
    },
    {
        "document_id": "DOC-RE-011",
        "revision_id": "REV-A",
        "title": "Chamber CH-5 Fully-Anechoic Chamber Qualification Record",
        "doc_type": "internal_wiki",
        "text": (
            "Fully-anechoic chamber CH-5 supports 3 meter and 10 meter "
            "test distances and is qualified for free-space site voltage "
            "standing wave ratio per CISPR 16-1-4 across 30 MHz to 18 GHz. "
            "Unlike semi-anechoic chamber CH-2, the ground plane is "
            "absorber-lined, so no height scan for ground-reflection "
            "maximization is required and results are typically 2 to 4 dB "
            "lower than the same EUT measured in CH-2. Standard antenna "
            "set: hybrid biconical-log-periodic antenna for 30 MHz to 3 "
            "GHz, horn antenna above 3 GHz."
        ),
    },
    {
        "document_id": "DOC-RE-012",
        "revision_id": "REV-A",
        "title": "CISPR 25 Automotive Component Radiated Emission Limits Excerpt",
        "doc_type": "specification",
        "text": (
            "CISPR 25 Class 5 radiated emission limits for automotive "
            "components measured at 1 meter in an absorber-lined shielded "
            "enclosure, broadband peak detector: "
            "30-75 MHz: 32.0 dBuV/m. "
            "75-400 MHz: 36.0 dBuV/m. "
            "400 MHz-1 GHz: 42.0 dBuV/m. "
            "These limits apply to components installed in a vehicle and "
            "are not interchangeable with the CISPR 32 limits used for "
            "information technology equipment, which are specified at 3 "
            "meters with a quasi-peak detector."
        ),
    },
    {
        "document_id": "DOC-RE-013",
        "revision_id": "REV-A",
        "title": "Antenna Factor and Cable Loss Correction Procedure",
        "doc_type": "internal_wiki",
        "text": (
            "Measured field strength in dBuV/m is obtained from the "
            "receiver reading in dBuV by adding the antenna factor in "
            "dB/m and the cable loss in dB, then subtracting the "
            "preamplifier gain in dB. Antenna factors are frequency "
            "dependent and must be interpolated from the calibration "
            "certificate of the specific antenna serial number in use, not "
            "from a generic model curve. Cable loss for the 10 meter "
            "chamber run in CH-2 is approximately 1.8 dB at 200 MHz and "
            "3.4 dB at 1 GHz. Using an uncorrected reading is the single "
            "most common cause of a pre-compliance result disagreeing with "
            "a full-compliance result."
        ),
    },
    {
        "document_id": "DOC-RE-014",
        "revision_id": "REV-A",
        "title": "EUT-44 Display Panel Radiated Emissions Failure Report",
        "doc_type": "test_report",
        "text": (
            "EUT-44 failed CISPR 32 Class B with a peak of 40.2 dBuV/m at "
            "220 MHz against the 35.6 dBuV/m limit, an exceedance of 4.6 "
            "dB. The emission correlates with the LVDS display interface "
            "pixel clock, whose third harmonic falls at 220 MHz. The "
            "flexible flat cable between the main board and the display "
            "panel was identified as the radiating element. Touching the "
            "cable with a ferrite clamp during the scan reduced the peak "
            "by 5 dB, which supports the cable as the dominant radiator "
            "rather than the enclosure seam."
        ),
    },
    {
        "document_id": "DOC-RE-014",
        "revision_id": "REV-B",
        "title": "EUT-44 Second Analysis: Enclosure Seam as Primary Radiator",
        "doc_type": "test_report",
        "text": (
            "A second investigation of the EUT-44 220 MHz exceedance "
            "reaches a different conclusion from the first report. With "
            "the flexible flat cable fully shielded and the ferrite clamp "
            "left in place, the 220 MHz peak fell only to 38.9 dBuV/m, "
            "still 3.3 dB above the limit. Applying conductive gasket to "
            "the display bezel seam without any cable treatment reduced "
            "the peak to 34.1 dBuV/m, below the limit. This analysis "
            "concludes the bezel seam is the primary radiator and the "
            "flexible flat cable is a secondary contributor, contradicting "
            "the cable-dominant finding of the first report."
        ),
    },
    {
        "document_id": "DOC-RE-015",
        "revision_id": "REV-A",
        "title": "CISPR 16-1-1 Receiver and Detector Settings",
        "doc_type": "specification",
        "text": (
            "Measuring receiver settings required by CISPR 16-1-1 for "
            "radiated emission measurement: "
            "9 kHz to 150 kHz: 200 Hz resolution bandwidth. "
            "150 kHz to 30 MHz: 9 kHz resolution bandwidth. "
            "30 MHz to 1 GHz: 120 kHz resolution bandwidth. "
            "Above 1 GHz: 1 MHz resolution bandwidth. "
            "Quasi-peak detection is required below 1 GHz for compliance "
            "assessment. Average and peak detectors are used above 1 GHz. "
            "A measurement made with the wrong resolution bandwidth is not "
            "comparable to a limit line and cannot support a compliance "
            "claim."
        ),
    },
    {
        "document_id": "DOC-RE-016",
        "revision_id": "REV-A",
        "title": "EUT-51 Ethernet Port Radiated Emissions Test Report",
        "doc_type": "test_report",
        "text": (
            "EUT-51 was tested with a 1 meter unshielded Ethernet patch "
            "cable connected and active at 100 Mbit per second. A peak of "
            "37.9 dBuV/m was measured at 125 MHz, exceeding the CISPR 32 "
            "Class B limit of 35.6 dBuV/m by 2.3 dB. 125 MHz is the "
            "fundamental of the 100BASE-TX line rate. Repeating the scan "
            "with the Ethernet cable disconnected removed the peak "
            "entirely, confirming common-mode current on the patch cable "
            "as the radiating mechanism rather than any emission from the "
            "EUT enclosure itself."
        ),
    },
    {
        "document_id": "DOC-RE-017",
        "revision_id": "REV-A",
        "title": "Enclosure Gasket Material Shielding Effectiveness Notes",
        "doc_type": "internal_wiki",
        "text": (
            "Shielding effectiveness of the gasket stock held in the lab, "
            "measured per a modified coaxial transmission line method at "
            "200 MHz: beryllium copper finger stock, 78 dB; conductive "
            "elastomer with silver-plated aluminium filler, 65 dB; nickel-"
            "graphite filled elastomer, 52 dB; conductive foam tape, 34 dB. "
            "Effectiveness in an assembled product is almost always lower "
            "than the material figure because it is limited by compression "
            "and by the longest unbonded seam length, not by the material. "
            "A seam longer than one twentieth of a wavelength should be "
            "treated as an aperture regardless of gasket choice."
        ),
    },
    {
        "document_id": "DOC-RE-018",
        "revision_id": "REV-A",
        "title": "EUT-63 Motor Drive Broadband Radiated Emissions Analysis",
        "doc_type": "test_report",
        "text": (
            "EUT-63 exhibited broadband radiated emissions from 30 MHz to "
            "approximately 200 MHz, peaking at 48.7 dBuV/m at 96 MHz "
            "against a 35.6 dBuV/m limit, an exceedance of 13.1 dB and the "
            "largest recorded in this document set. The emission profile "
            "is broadband, filling the receiver resolution bandwidth "
            "continuously rather than appearing as discrete harmonics, and "
            "is characteristic of fast switching edges in the brushless "
            "motor drive inverter. The unshielded three-phase motor cable "
            "carries the common-mode current to the outside of the "
            "enclosure. This failure mode differs from the narrowband "
            "clock harmonic seen on EUT-31."
        ),
    },
    {
        "document_id": "DOC-RE-019",
        "revision_id": "REV-A",
        "title": "Measurement Uncertainty for Radiated Emission Results",
        "doc_type": "specification",
        "text": (
            "The laboratory expanded measurement uncertainty for radiated "
            "emission measurement, computed per CISPR 16-4-2 with a "
            "coverage factor of 2, is 5.2 dB for 30 MHz to 1 GHz and 5.6 "
            "dB above 1 GHz. Per CISPR 16-4-2 the compliance decision is "
            "made against the limit line without subtracting uncertainty, "
            "provided the laboratory uncertainty does not exceed the "
            "tabulated Ucispr value. A margin smaller than the expanded "
            "uncertainty should be reported as such, because it cannot be "
            "distinguished from a marginal exceedance by measurement "
            "alone."
        ),
    },
    {
        "document_id": "DOC-RE-020",
        "revision_id": "REV-A",
        "title": "Turntable Azimuth and Mast Height Maximization Procedure",
        "doc_type": "internal_wiki",
        "text": (
            "For each candidate frequency identified in the prescan, the "
            "emission must be maximized before the final quasi-peak "
            "reading is taken. Rotate the turntable through a full 360 "
            "degrees in steps no coarser than 15 degrees, and scan the "
            "antenna mast from 1 to 4 meters in both horizontal and "
            "vertical polarization. In semi-anechoic chamber CH-2 the "
            "height scan is mandatory because the ground reflection "
            "produces nulls and peaks that can differ by more than 10 dB "
            "at a fixed height. In fully-anechoic chamber CH-5 the height "
            "scan may be reduced since there is no ground reflection to "
            "maximize against."
        ),
    },
    {
        "document_id": "DOC-RE-021",
        "revision_id": "REV-A",
        "title": "Radiated Emission Failure Escalation and Rework Policy",
        "doc_type": "specification",
        "text": (
            "An exceedance of 3 dB or less may be addressed by a cable-"
            "level mitigation such as a ferrite choke without a design "
            "review, provided the retest is performed in the same chamber "
            "with the same setup. An exceedance greater than 3 dB, or any "
            "broadband exceedance, requires a documented root cause "
            "analysis identifying the radiating element and the coupling "
            "path before rework is authorized. An exceedance greater than "
            "10 dB additionally requires a hardware design review, since "
            "cable and enclosure treatments alone are unlikely to recover "
            "that margin."
        ),
    },
    {
        "document_id": "DOC-RE-022",
        "revision_id": "REV-A",
        "title": "Chamber CH-2 Normalized Site Attenuation Validation Record",
        "doc_type": "internal_wiki",
        "text": (
            "Normalized site attenuation for semi-anechoic chamber CH-2 "
            "was validated per CISPR 16-1-4 at the 3 meter distance in "
            "March. Deviation from theoretical normalized site attenuation "
            "remained within plus or minus 3.4 dB across 30 MHz to 1 GHz, "
            "inside the plus or minus 4 dB acceptance criterion. The worst "
            "deviation occurred at 45 MHz in vertical polarization. "
            "Validation is due for repeat every 24 months or after any "
            "change to absorber layout, turntable position, or antenna "
            "mast geometry."
        ),
    },
    {
        "document_id": "DOC-RE-023",
        "revision_id": "REV-A",
        "title": "Ferrite Core Material Selection for Cable Mitigation",
        "doc_type": "internal_wiki",
        "text": (
            "Ferrite core material determines the frequency band over "
            "which a choke is useful. Manganese-zinc material gives its "
            "highest impedance from about 1 MHz to 30 MHz and is the wrong "
            "choice for a radiated emission problem above 30 MHz. Nickel-"
            "zinc material peaks between roughly 30 MHz and 300 MHz and is "
            "the usual first choice for cable-borne radiated emission. For "
            "problems above 300 MHz a smaller nickel-zinc core with fewer "
            "turns, or a shielded cable, is more effective, because "
            "inter-turn capacitance shunts the choke impedance at higher "
            "frequencies. Impedance also depends on the number of turns "
            "through the core, roughly as the square of the turn count "
            "until capacitance dominates."
        ),
    },
    {
        "document_id": "DOC-RE-024",
        "revision_id": "REV-A",
        "title": "EUT-51 Ferrite Selection Study and Retest Results",
        "doc_type": "test_report",
        "text": (
            "Three ferrite clamps were trialled on the EUT-51 Ethernet "
            "patch cable to address the 125 MHz exceedance. A manganese-"
            "zinc clamp produced no measurable change, consistent with its "
            "impedance band lying below 30 MHz. A single-turn nickel-zinc "
            "clamp reduced the peak by 3.1 dB to 34.8 dBuV/m, just inside "
            "the 35.6 dBuV/m limit. A three-turn nickel-zinc clamp on the "
            "same core reduced it by 7.4 dB to 30.5 dBuV/m and was "
            "selected for production. The result supports the material and "
            "turn-count guidance in the ferrite core selection notes."
        ),
    },
    {
        "document_id": "DOC-RE-025",
        "revision_id": "REV-A",
        "title": "Prescan Versus Final Measurement Workflow",
        "doc_type": "internal_wiki",
        "text": (
            "A prescan is performed with a peak detector and a fast sweep "
            "to identify candidate frequencies, typically all points "
            "within 10 dB of the limit line. Only those candidates are "
            "then maximized and re-measured with the quasi-peak detector, "
            "because quasi-peak measurement is slow and cannot practically "
            "be run across the whole band. A prescan peak reading is "
            "always equal to or higher than the corresponding quasi-peak "
            "reading, so a prescan point below the limit needs no further "
            "work, while a prescan point above the limit is not yet a "
            "failure."
        ),
    },
]


# --- adversarial corpus ------------------------------------------------------
#
# CORPUS above is written so the benchmark queries are answerable. That makes it
# a harness, not a test of retrieval: there are no competing documents, no
# revisions that differ by one number, no contradictions, and every fact is
# spelled exactly one way.
#
# These generators add the difficulty a real legacy corpus has, at whatever size
# a test asks for. They are deterministic -- no randomness -- so a failure is
# reproducible and a stability test can compare results across corpus sizes and
# attribute any difference to the retriever rather than to sampling.


# Chamber identifiers reserved for generated distractors. Nothing in the
# baseline corpus and no benchmark query may use one, in either direction:
#
#   - A distractor that supplies the identifier a query discriminates on stops
#     being a distractor. An early draft used CH-{i % 4} and hid OPEN_DECISIONS
#     D-10 completely -- every stability test passed against a broken gate.
#   - An abstention case that names one stops being an abstention case as soon
#     as distractors are added, because the subject it asserts is absent is
#     then present. RE-BC-147 asked about CH-9 and flipped at every corpus
#     shape for exactly that reason.
#
# tests/test_re_retrieval_stability.py asserts both directions, so a future
# document or query that reuses one of these fails there rather than silently
# weakening a probe.
DISTRACTOR_CHAMBERS = (7, 8, 9)


def distractor_documents(count: int) -> list[RawDocument]:
    """Plausible RE documents that answer none of the benchmark queries.

    Same vocabulary, same units, same chambers and antennas -- differing only
    in the specifics. This is what a real archive looks like: mostly documents
    that are *near* your question without being it.
    """
    docs: list[RawDocument] = []
    for i in range(count):
        chamber = f"CH-{DISTRACTOR_CHAMBERS[i % len(DISTRACTOR_CHAMBERS)]}"
        docs.append({
            "document_id": f"DOC-RE-AMB-{i:04d}",
            "revision_id": "REV-A",
            "title": f"Chamber {chamber} Ambient Scan {i:04d}",
            "doc_type": "measurement_log",
            "text": (
                f"Ambient radiated emission scan {i:04d} recorded in semi-anechoic chamber "
                f"{chamber} per CISPR 32 Class B with no equipment energised. Biconical "
                f"antenna at 3 meters for the 30-1000 MHz sweep and a horn antenna above "
                f"1 GHz. Highest ambient was {18 + i % 11}.{i % 10} dBuV/m at "
                f"{101 + (i * 13) % 800} MHz, below the Class B limit line at that "
                f"frequency. Cable routing and connector placement followed the standard "
                f"test setup. No exceedance and no mitigation required."
            ),
        })
    return docs


def near_duplicate_revisions() -> list[RawDocument]:
    """Later revisions of baseline documents differing by one measurement.

    Revision-compare queries are only meaningfully tested when two revisions are
    nearly identical -- if REV-B were obviously different, matching it would not
    demonstrate revision discrimination.
    """
    return [
        {
            "document_id": "DOC-RE-001",
            "revision_id": "REV-B",
            "title": "EUT-7 Radiated Emissions Test Report",
            "doc_type": "test_report",
            "text": (
                "Device under test EUT-7 was evaluated for radiated emissions in "
                "semi-anechoic chamber CH-2 per CISPR 32 Class B limits. Test setup used "
                "a biconical antenna at 3 meters for 30-1000 MHz and a horn antenna above "
                "1 GHz. A peak emission of 41.7 dBuV/m was measured at 148 MHz, exceeding "
                "the Class B limit of 35.6 dBuV/m by 6.1 dB at that frequency. No other "
                "peaks exceeded the limit line. The exceedance was traced to the "
                "unshielded power cable connecting EUT-7 to the enclosure fan connector."
            ),
        },
    ]


def contradicting_documents() -> list[RawDocument]:
    """A document asserting the opposite of a baseline finding.

    Retrieval that silently returns one side of a contradiction, with no signal
    that the other exists, is not evidence handling. The RE_POC query category
    "evidence supporting or contradicting a hypothesis" depends on both being
    reachable.
    """
    return [
        {
            "document_id": "DOC-RE-CON-001",
            "revision_id": "REV-A",
            "title": "EUT-7 Re-test After Cable Replacement",
            "doc_type": "test_report",
            "text": (
                "A re-test of EUT-7 in chamber CH-2 found no exceedance at 132 MHz. The "
                "peak at that frequency measured 31.4 dBuV/m, below the CISPR 32 Class B "
                "limit of 35.6 dBuV/m. The earlier attribution to the unshielded power "
                "cable was not reproduced; the original exceedance is now believed to "
                "have been an ambient artefact rather than an emission from the device "
                "under test."
            ),
        },
    ]


def notation_variant_documents() -> list[RawDocument]:
    """The same facts spelled the way different authors and eras spell them.

    Legacy archives are inconsistent: the field-strength unit appears as dBuV/m
    and dB(uV)/m, antennas are called biconical or bicon, and the device is the
    DUT in one document and the EUT in the next.
    """
    return [
        {
            "document_id": "DOC-RE-VAR-001",
            "revision_id": "REV-A",
            "title": "Bicon Setup Note (legacy notation)",
            "doc_type": "internal_wiki",
            "text": (
                "Legacy setup note. The bicon is positioned at 3 meters from the DUT for "
                "the 30-1000 MHz sweep in chamber CH-2. Historical logs record the field "
                "strength in dB(uV)/m rather than dBuV/m; the two are the same unit. A "
                "measurement of 35.6 dB(uV)/m is the Class B limit at 3 m for this band."
            ),
        },
    ]


def adversarial_corpus(
    distractors: int = 0,
    *,
    revisions: bool = True,
    contradictions: bool = True,
    variants: bool = True,
) -> list[RawDocument]:
    """CORPUS plus whichever kinds of difficulty the caller asks for."""
    docs = list(CORPUS)
    if revisions:
        docs.extend(near_duplicate_revisions())
    if contradictions:
        docs.extend(contradicting_documents())
    if variants:
        docs.extend(notation_variant_documents())
    docs.extend(distractor_documents(distractors))
    return docs


def term_saturating_documents(count: int, *, phrase: str = "antenna setup") -> list[RawDocument]:
    """Documents that push a specific query term's document frequency upward.

    `retrieve()` admits a query term as discriminating only while its document
    frequency stays under a fraction of the corpus. Whether a term is under that
    fraction is a property of the corpus, not of the query -- so a term can
    cross the line purely because unrelated documents were added, changing which
    terms gate retrieval and how many literal hits are required.

    Generic distractors do not reliably reach that boundary: if they mention a
    term in a constant fraction of their text, its ratio stays roughly constant
    however many are added. Crossing it takes documents that mention the term
    far more densely than the baseline corpus does, which is what this builds.

    Deliberately never mentions a chamber or device identifier, so it saturates
    the *descriptive* vocabulary without supplying anything a query
    discriminates on.
    """
    docs: list[RawDocument] = []
    for i in range(count):
        docs.append({
            "document_id": f"DOC-RE-SAT-{i:04d}",
            "revision_id": "REV-A",
            "title": f"Generic {phrase} reference note {i:04d}",
            "doc_type": "internal_wiki",
            "text": (
                f"General {phrase} guidance. The {phrase} is described in the standard "
                f"{phrase} reference. Review the {phrase} before each measurement; the "
                f"{phrase} determines repeatability. Any {phrase} deviation is recorded "
                f"in the {phrase} log alongside the {phrase} checklist."
            ),
        })
    return docs
