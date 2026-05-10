---
name: pdbe-llm-annotation-fetching
description: Fetch LLM-derived residue annotations for PDB entries or UniProt accessions from the PDBe LLM annotation REST API, and parse the structured response for notebook use.
---

# Goal

Retrieve LLM-extracted annotations from the PDBe API for a given PDB entry or UniProt accession, and return structured per-residue annotation data ready for analysis or visualisation.

# Inputs

One of:
- PDB ID (e.g. `8qvm`)
- PDB ID + chain ID + residue ID (e.g. `8qvm`, `A`, `467`)
- UniProt accession (e.g. `P34913`)
- UniProt accession + residue number (e.g. `P34913`, `466`)

# Workflow

## 1. Select the appropriate endpoint

Base URL: `https://www.ebi.ac.uk/pdbe/api/v2`

| Input | Endpoint |
|---|---|
| PDB ID only | `GET /llm_annotations/summary/{pdb_id}.json` |
| PDB ID + chain + residue | `GET /llm_annotations/summary/{pdb_id}/{chain_id}/{residue_id}.json` |
| UniProt accession only | `GET /llm_annotations/summary/{uniprot_accession}.json` |
| UniProt accession + residue | `GET /llm_annotations/summary/{uniprot_accession}/{uniprot_residue}.json` |

## 2. Make the HTTP GET request

- Use `requests` with a timeout.
- Handle `400` (bad input) and `501` (endpoint not implemented) explicitly.
- Raise on any other non-200 response.

## 3. Parse the response

The response has the shape:

```json
{
  "dataType": "ANNOTATIONS",
  "data": [
    {
      "provider": "IUCr",
      "residueList": [
        {
          "startIndex": 42,
          "endIndex": 42,
          "indexType": "PDB",
          "additionalData": [
            {
              "pubmedId": 1234567,
              "pmcId": "PMC1234567",
              "doi": "10.1234/abcd.efgh",
              "primaryCitation": "Y",
              "openAccess": "Y",
              "entityId": 1,
              "pdbResidue": 42,
              "authorResidueNumber": 42,
              "pdbChain": "A",
              "uniprotAccession": "P12345",
              "uniprotResidue": 42,
              "sentence": "...",
              "section": "...",
              "exact": "...",
              "entityType": "protein",
              "annotator": "...",
              "aiScore": 0.95
            }
          ]
        }
      ]
    }
  ]
}
```

## 4. Flatten to per-residue annotation table

Produce a flat table with columns:
`provider`, `pdb_id`, `chain_id`, `pdb_residue`, `uniprot_accession`, `uniprot_residue`, `index_type`, `start_index`, `end_index`, `entity_type`, `ai_score`, `sentence`, `doi`, `pubmed_id`, `open_access`

## 5. Filter and rank

- Optionally filter by `ai_score` threshold (default: keep all).
- Optionally filter by `provider`.
- Sort by `ai_score` descending within each residue.

# Requirements

- Use `requests` for HTTP calls.
- Handle missing optional fields gracefully (not all records contain all fields).
- Preserve `indexType` to distinguish PDB vs UniProt residue numbering.
- Do not symmetrize or merge annotations from different providers without flagging it.
- Record the retrieval timestamp for reproducibility.

# Dependencies

- `requests`
- `pandas` (for flat table output)

# Outputs

- Flat per-residue annotation DataFrame
- Retrieval metadata (endpoint used, timestamp, total annotation count)
- List of providers present in the response
