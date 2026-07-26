"""
NextDrop – Data Ingestion Script
----------------------------------
Run data loading, validation, and merging pipeline:
    python -m scripts.ingest_data
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.ml.datasets.preprocessor import DatasetPreprocessor


def main():
    print("=" * 60)
    print("NextDrop AI Release Strategist – Data Ingestion Pipeline")
    print("=" * 60)

    preprocessor = DatasetPreprocessor()
    df, audit_summary = preprocessor.run_pipeline()

    print("\n" + "=" * 60)
    print("Ingestion Summary:")
    print("-" * 60)
    print(f"Total merged rows ready for training: {len(df):,}")
    print(f"Output saved to: {audit_summary.get('output_filepath')}")
    print("\nDataset Version Hashes:")
    for name, sha in audit_summary.get("dataset_hashes", {}).items():
        print(f"  - {name}: {sha[:16]}...")
    print("\nAudit Summary:")
    print(json.dumps(audit_summary.get("audit_log", []), indent=2))
    print("=" * 60)


if __name__ == "__main__":
    main()
