"""
Data ingestion script to load Excel data into Qdrant vector database
"""
import pandas as pd
import sys
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.embedding import generate_embedding, prepare_text_for_embedding
from app.services.enhancement import process_description
from app.services.qdrant_service import insert_training_data, get_collection_stats
from app.config import get_settings

settings = get_settings()


def ingest_data(excel_path: str, max_rows: int = None):
    """
    Ingest data from Excel file into Qdrant
    
    Args:
        excel_path: Path to Excel file
        max_rows: Maximum number of rows to process (for testing)
    """
    print(f"Loading data from: {excel_path}")
    
    # Load Excel
    df = pd.read_excel(excel_path)
    print(f"Loaded {len(df)} rows")
    
    # Validate columns
    required_cols = ['Item Description', 'Item HS Code']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        print(f" Missing columns: {missing}")
        return
    
    # Clean data
    df = df[required_cols + ['Item Country Of Origin']].dropna(subset=required_cols)
    
    # Limit rows if specified
    if max_rows:
        df = df.head(max_rows)
        print(f"Processing first {max_rows} rows")
    
    print(f"Processing {len(df)} valid records")
    
    # Process each row
    success_count = 0
    error_count = 0
    
    start_time = time.time()
    
    for idx, row in df.iterrows():
        try:
            description = str(row['Item Description'])
            hs_code = str(row['Item HS Code']).replace('.', '')
            country = str(row.get('Item Country Of Origin', 'CN'))[:2]
            
            # Process description
            # processed = process_description(description, country)
            # enhanced_desc = processed["enhanced"]
            # quality_score = processed["quality_score"]
            enhanced_desc = description
            quality_score = 5
            # Generate embedding
            text_for_embedding = prepare_text_for_embedding(enhanced_desc, country)
            embedding = generate_embedding(text_for_embedding)
            
            # Insert into Qdrant
            insert_training_data(
                description_original=description,
                description_enhanced=enhanced_desc,
                hs_code=hs_code,
                country=country,
                embedding=embedding,
                enhancement_quality=quality_score,
            )
            
            success_count += 1
            
            if (idx + 1) % 100 == 0:
                elapsed = time.time() - start_time
                rate = success_count / elapsed
                print(f"Progress: {idx + 1}/{len(df)} ({success_count} success, {error_count} errors) - {rate:.1f} items/sec")
        
        except Exception as e:
            error_count += 1
            print(f" Error on row {idx}: {str(e)}")
            if error_count > 10:
                print("Too many errors, stopping...")
                break
    
    total_time = time.time() - start_time
    
    print("\n" + "="*60)
    print("INGESTION COMPLETE")
    print("="*60)
    print(f"Success: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Total time: {total_time:.1f} seconds")
    print(f"Average rate: {success_count/total_time:.1f} items/sec")
    
    # Show collection stats
    print("\n" + "="*60)
    print("COLLECTION STATISTICS")
    print("="*60)
    stats = get_collection_stats()
    for collection, info in stats.items():
        print(f"\n{collection}:")
        for key, value in info.items():
            print(f"  {key}: {value}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest Excel data into Qdrant")
    parser.add_argument("excel_path", help="Path to Excel file")
    parser.add_argument("--max-rows", type=int, help="Maximum rows to process (for testing)")
    
    args = parser.parse_args()
    
    ingest_data(args.excel_path, args.max_rows)