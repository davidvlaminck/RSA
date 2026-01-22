# Archived reports

This folder contains snapshots of older report implementations for quick lookup.

## How to use
- Use your editor search (or ripgrep) in this folder when you need to find an older query/approach.
- Treat these files as **read-only historical reference**. The runnable reports live in `Reports/`.

## Index

| File | Notes |
|------|-------|
| `Report0001.py` | Onderdelen hebben een HoortBij relatie |
| `Report0008.py` | Camera's hebben HoortBij relatie met dezelfde naam |
| `Report0011.py` | Omvormers en PoEInjectors hebben een HoortBij relatie naar OmvormerLegacy of Encoder objecten |
| `Report0021.py` | OTN Netwerkelement verband HoortBij relaties en merk |
| `Report0022.py` | OTN Netwerkelement naamgeving |
| `Report0028.py` | IP Netwerkelementen (niet OTN) hebben een HoortBij relatie met een legacy object van type IP |
| `Report0029.py` | IP elementen hebben een bijbehorend Netwerkelement |
| `Report0036.py` | Netwerkpoorten met type 'UNI' hebben een hoortbij relatie naar installatie VLAN |
| `Report0074.py` | Datcleaning van verkeersregelaar uit VRI script |
| `Report0103.py` | Inconsistente EAN nummers tusen legacy en OTL |
| `Report0104.py` | Dubbele EAN nummers over legacy en OTL assets |
| `Report0115.py` | EAN Nummer is steeds ingevuld (Legacy-data) |
| `Report0117.py` | DNBHoogspanning of DNBLaagspanning eanNummer stemt overeen met de legacy waarde. (dubbel) |
| `Report0133.py` | Dubbele bomen |
| `Report0135.py` | Dubbele Straatkolken |
| `Report0144.py` | Assets (legacy) met ingevuld kenmerk: "elektrische aansluiting" |
| `Report0158.py` | EAN-opzoeklijst |
| `Report0178.py` | Bestekken zonder aannemer |

## Suggested convention (optional)
If you archive more reports later, consider adding a short note next to the file in the table above:
- why it was archived
- which current report replaced it
- the date of the snapshot
