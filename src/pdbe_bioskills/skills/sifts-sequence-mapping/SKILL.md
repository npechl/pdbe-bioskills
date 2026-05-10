---
name: sifts-sequence-mapping
description: Run the open-source SIFTS pipeline to map PDBx/mmCIF structure sequences to a reference sequence database (UniProtKB or custom FASTA), producing residue-level structure-to-sequence alignments.
---

# Goal

Produce global structure-to-sequence mappings between PDBx/mmCIF structure files and a reference sequence database using the open-source SIFTS pipeline (`pdbe-sifts` / `https://github.com/PDBeurope/SIFTS`).

# Inputs

- One or more structure files in **PDBx/mmCIF format**
- One of:
  - A reference sequence FASTA file (`.fasta` or `.fasta.gz`)
  - A flag to download UniProtKB/TrEMBL automatically
- (Optional) Directory from a previous run containing existing SIFTS outputs and hashes for incremental processing
- Output directory path (`ref_db_file`)

# Workflow

The pipeline runs in three sequential stages. Each stage can be executed independently.

## Stage 1 — Create Reference Database

Build or update the reference sequence database.

**CLI entry point**: `pdbe_sifts_create_ref_db`

Steps:
1. Accept FASTA input or download UniProtKB/TrEMBL.
2. Optionally generate an indexed database for faster alignment.
3. Save the database and version metadata to `ref_db_file`.

**Output**: FASTA or indexed database files in `ref_db_file`.

## Stage 2 — Global Structure-to-Sequence Alignments

Align each structure's sequences against the reference database using BLAST or MMseqs2.

**CLI entry point**: `pdbe_sifts_structure_to_seq`

Arguments:
- `ref_db_file` — path to the reference database from Stage 1

Steps:
1. For each input mmCIF file:
   a. Compute a hash of the file content (e.g. using `hashlib`).
   b. Check whether this hash already exists in the output registry.
   c. If a match is found, reuse previous results (skip reprocessing).
   d. If new, run the sequence alignment and save results (CSV files) to the output directory, using the hash as the folder or file name.
2. Store structure-chain-accession mappings from the alignment output.

**Why hashes?** Input mmCIF files in the open-source pipeline may not have unique identifiers (unlike PDB codes in the internal `orc-sifts` pipeline). Hashes provide a robust way to track processed files and avoid redundant computation.

**Output**: Per-structure CSV files with alignment results and associated hashes.

## Stage 3 — Segment Generation

Convert global alignment results into SIFTS-style residue-level segment mappings.

**CLI entry point**: `pdbe_sifts_segment_generation`

Arguments:
- File containing structure-chain-accession mappings (output of Stage 2)

**Output**: Segment-level mapping files (format TBD in upstream documentation).

## Running the Full Pipeline

To run all three stages end-to-end:

**CLI entry point**: `pdbe_sifts_whole`

To skip Stage 1 (reference database already exists):

**CLI entry point**: `pdbe_sifts_whole_nodb`

Arguments:
- `ref_db_file` — path to existing reference database

# Requirements

- Input structure files must be in PDBx/mmCIF format.
- Always compute file hashes before processing to enable incremental runs.
- Store hashes in a central registry file or as folder/file names in the output directory.
- Do not reprocess a structure whose hash is already in the registry.
- Document the reference database version used for reproducibility.

# Dependencies

- `pdbe-sifts` package (`https://github.com/PDBeurope/SIFTS`)
- BLAST or MMseqs2 (for sequence alignment in Stage 2)
- `hashlib` (Python standard library, for hash computation)

# Outputs

- Reference sequence database (Stage 1)
- Per-structure alignment CSV files with hashes (Stage 2)
- Structure-chain-accession mapping file (Stage 2)
- Residue-level segment mapping files (Stage 3)
