# Local working data (git-ignored). Do not commit raw CSVs.
# Planned layout (Phase 1+):
#   data/raw/       <- local extract of Sample - Superstore.csv (never commit)
#   data/processed/ <- cleaned, typed fact table parquet/csv (never commit raw; commit scripts only)
#   data/curated/   <- model outputs for Power BI (never commit; rebuild via src/)
