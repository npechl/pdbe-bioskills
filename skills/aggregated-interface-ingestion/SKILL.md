---
name: aggregated-interface-ingestion
description: Build or validate the aggregated interface schema for a set of PDB complexes from chain correspondence data, following the PDBe-KB four-stage ingestion pipeline.
---

# Goal

Compute aggregated protein-protein interface groups from per-instance interface data and chain correspondence pairings, producing stable content-derived identifiers and cached statistics for use in PDBe-KB Complexes pages or notebook analysis.

# Inputs

- **Chain correspondence CSV**: pairwise biological chain equivalences.
  Format per row: `pdb_complex_id, asm1, author_chain_id1, asm2, author_chain_id2`
- **Interface table** (DataFrame or DB query result) with columns:
  `entry_id`, `assembly_id`, `author_chain_id1`, `author_chain_id2`

# Workflow

## Stage 1 — Compute Equivalence Classes

For each `pdb_complex_id` independently:

1. Represent each unique chain as a node: `(entry_id, assembly_id, author_chain_id)`.
2. Represent each CSV row as an undirected edge between two chain nodes.
3. Run connected-component analysis (e.g. `scipy.sparse.csgraph.connected_components`) to find equivalence classes.
4. Each connected component becomes one `chain_class`.

**Properties**: grouping is deterministic — identical input always produces identical groups regardless of row ordering.

## Stage 2 — Assign Stable Identifiers

### chain_class_id

For each equivalence class:
1. Select the lexicographically smallest chain tuple `(entry_id, assembly_id, author_chain_id)` as canonical representative.
2. Generate: `CC_ + short_hash(pdb_complex_id, canonical_tuple)`
   Example: `CC_a3f8b2`

### agg_interface_id

For each unordered pair of chain classes:
1. Enforce canonical ordering: `chain_class_id_1 <= chain_class_id_2`.
2. Generate: `AI_ + short_hash(pdb_complex_id, chain_class_id_1, chain_class_id_2)`
   Example: `AI_8e2c19`

IDs are content-derived and remain stable across reingestion runs.

## Stage 3 — Populate Chain Class Tables

### complex_chain_class

Insert one row per equivalence class:
- `chain_class_id`
- `pdb_complex_id`
- `uniprot_accession` or `rfam_accession` (must be shared by all chains in the class)
- `component_index`: sequential integer within the complex per accession (NULL if only one class for that accession)
- Display label: `P69905`, `P69905-1`, `P69905-2`, `RF00001-1`, etc.

### complex_chain_instance

Insert one row per physical chain mapping:
`(entry_id, assembly_id, author_chain_id)` → `chain_class_id`

## Stage 4 — Build Aggregated Interfaces

For each row in the interface table:
1. Resolve `author_chain_id1` and `author_chain_id2` via `complex_chain_instance`.
2. Canonicalise the chain class pair: enforce `chain_class_id_1 <= chain_class_id_2`.
3. Generate `agg_interface_id`.
4. Insert into `aggregated_interface` if not already present.
5. Update `interface.agg_interface_id` to point to the matching group.
6. Compute cached statistics per aggregated interface:
   - `instance_count`
   - `median_bsa` (buried surface area)
   - `median_solvation_energy`

# Sanity Checks

Run these validations before committing results:

- **Consistent accessions within a class**: all chains in a class must share the same UniProt or Rfam accession and sequence length. Violations indicate bad upstream correspondence data.
- **No duplicate pairwise relationships**: each unordered chain pair should appear only once in the CSV. Union-find tolerates duplicates silently — validate explicitly.
- **All interface chains must resolve**: every chain referenced in the interface table must map to a row in `complex_chain_instance`. Log warnings for unresolved chains.

# Reingestion Strategy

Rebuild from scratch each run:
- `complex_chain_class`
- `complex_chain_instance`
- `aggregated_interface`

Because IDs are content-derived, URLs and external references remain stable across rebuilds.

# Requirements

- Process each `pdb_complex_id` independently.
- Use a deterministic hash function (e.g. SHA-256 truncated) for ID generation.
- Never renumber existing classes on reingestion.
- Log all sanity check violations before raising errors.

# Dependencies

- `scipy` (connected component analysis)
- `pandas` (table manipulation)
- `hashlib` (ID generation)

# Outputs

- `complex_chain_class` table
- `complex_chain_instance` table
- `aggregated_interface` table with cached statistics
- Sanity check report (pass / warnings / failures)
