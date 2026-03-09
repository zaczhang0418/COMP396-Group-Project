import pandas as pd
import os
import glob
import sys

def merge_parts():
    # Define paths relative to the script execution root (project root)
    # Assuming script is run from project root via "python scripts/merge_data_parts.py"
    base_dir = os.getcwd()
    p1_dir = os.path.join(base_dir, "DATA", "PART1")
    p2_dir = os.path.join(base_dir, "DATA", "PART2")
    out_dir = os.path.join(base_dir, "DATA", "COMBINED")

    # Check source directories
    if not os.path.exists(p1_dir):
        print(f"[ERROR] Part 1 directory not found: {p1_dir}")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(out_dir, exist_ok=True)
    print(f"[INFO] Merging data from:\n  - {p1_dir}\n  - {p2_dir}\n  -> To: {out_dir}\n")

    # Get all CSV files from Part 1
    files_p1 = glob.glob(os.path.join(p1_dir, "*.csv"))
    if not files_p1:
        print("[WARN] No CSV files found in Part 1.")
        return

    for f1 in files_p1:
        filename = os.path.basename(f1)
        asset_name = os.path.splitext(filename)[0]
        f2 = os.path.join(p2_dir, filename)

        # Read Part 1
        try:
            df1 = pd.read_csv(f1)
            # Normalize Date column
            if "Index" in df1.columns:
                df1.rename(columns={"Index": "Date"}, inplace=True)
        except Exception as e:
            print(f"[ERROR] Failed to read {filename} from Part 1: {e}")
            continue

        # Read Part 2 (if exists)
        df_combined = df1
        status = "Part 1 Only"
        
        if os.path.exists(f2):
            try:
                df2 = pd.read_csv(f2)
                if "Index" in df2.columns:
                    df2.rename(columns={"Index": "Date"}, inplace=True)
                
                # Concatenate
                df_combined = pd.concat([df1, df2], ignore_index=True)
                status = "Merged (P1 + P2)"
            except Exception as e:
                print(f"[ERROR] Failed to read {filename} from Part 2: {e}")
        else:
            status = "Part 1 Only (Part 2 missing)"

        # Data Cleaning: Convert Date, Sort, Drop Duplicates
        if "Date" in df_combined.columns:
            df_combined["Date"] = pd.to_datetime(df_combined["Date"])
            df_combined.sort_values("Date", inplace=True)
            # Drop duplicates based on Date, keeping the last entry (assuming newer data is better or same)
            df_combined.drop_duplicates(subset=["Date"], keep="last", inplace=True)
        else:
            print(f"[WARN] {filename} has no 'Date' or 'Index' column. Skipping sort.")

        # Save to COMBINED
        out_path = os.path.join(out_dir, filename)
        df_combined.to_csv(out_path, index=False)
        print(f"  [{asset_name}] {status} -> {len(df_combined)} rows saved.")

    print("\n[SUCCESS] Data merge completed.")

if __name__ == "__main__":
    merge_parts()