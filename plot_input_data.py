import pandas as pd
import matplotlib.pyplot as plt
import glob
import os

def plot_price_data(data_path=".", output_dir=None, normalise=False, selected_series=None):
    # Plots Close prices from multiple CSV files (columns: Index, Open, High, Low, Close, Volume).
    # Automatically merges by date and saves two charts to the output folder:
    #   1) input_data_plot.png               (raw Close prices)
    #   2) input_data_plot_normalised.png    (optional Min–Max scaled)
    #
    # Parameters:
    #     data_path (str): Directory containing the CSV files.
    #     normalise (bool): If True, also saves the normalised chart.
    #     selected_series (list[int] | None): Series numbers to include (e.g., [1,5]).
    #         If None, all available series are plotted.

    # --- Prepare output directory ---
    if output_dir is None:
        # Default to a subfolder named after the data folder (e.g., output/PART2)
        dataset_name = os.path.basename(os.path.normpath(data_path))
        output_dir = os.path.join(os.getcwd(), "output", dataset_name)
    
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")

    # --- Load all CSV files ---
    csv_files = glob.glob(os.path.join(data_path, "*.csv"))
    if not csv_files:
        print(f"No CSV files found in {data_path}")
        return

    dfs = {}
    for file in csv_files:
        name = os.path.splitext(os.path.basename(file))[0]  # e.g. "01" or "BTC"
        df = pd.read_csv(file)
        
        # Support both 'Index' and 'Date' for the time column
        if "Index" in df.columns:
            df["Date"] = pd.to_datetime(df["Index"])
        elif "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"])
        else:
            print(f"Skipping {name}: missing 'Index' or 'Date' column.")
            continue
        if "Close" not in df.columns:
            print(f"Skipping {name}: missing 'Close' column.")
            continue
        df = df[["Date", "Close"]].rename(columns={"Close": name})
        dfs[name] = df

    # --- Filter only selected series if provided ---
    if selected_series:
        # Allow both 1 and 01 to match filenames like '01.csv'
        selected_names = [f"{int(s):02d}" for s in selected_series] + [str(int(s)) for s in selected_series]
        dfs = {k: v for k, v in dfs.items() if k in selected_names}

        if not dfs:
            print(f"No matching series found for {selected_series}. "
                  f"Available series: {list(dfs.keys())}")
            return

        print(f"Plotting selected series: {', '.join(dfs.keys())}")
    else:
        print(f"Plotting all {len(dfs)} available series.")

    # --- Merge all dataframes on 'Date' ---
    merged = dfs[list(dfs.keys())[0]]
    for name, df in list(dfs.items())[1:]:
        merged = merged.merge(df, on="Date", how="inner")

    merged.set_index("Date", inplace=True)

    # --- Plot Close prices ---
    plt.figure(figsize=(12, 6))
    for col in merged.columns:
        plt.plot(merged.index, merged[col], label=col)
    plt.title("Close Price Series")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()

    # Save raw plot to output folder
    raw_path = os.path.join(output_dir, "input_data_plot.png")
    plt.savefig(raw_path, dpi=150)
    plt.close()
    print(f"Saved raw plot → {raw_path}")

    # --- Optional: Plot Min–Max scaled series ---
    if normalise:
        merged_minmax = (merged - merged.min()) / (merged.max() - merged.min())
        plt.figure(figsize=(12, 6))
        for col in merged_minmax.columns:
            plt.plot(merged_minmax.index, merged_minmax[col], label=col)
        plt.title("Min–Max Normalised Prices (0–1 Scale)")
        plt.xlabel("Date")
        plt.ylabel("Scaled Price (0–1)")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        norm_path = os.path.join(output_dir, "input_data_plot_normalised.png")
        plt.savefig(norm_path, dpi=150)
        plt.close()
        print(f"Saved normalised plot → {norm_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Plot price data from multiple CSVs.")
    parser.add_argument("--data-path", default="./DATA/PART2",
                        help="Directory containing the CSV files.")
    parser.add_argument("--output-dir", default=None,
                        help="Directory to save plots.")
    parser.add_argument("--normalise", action="store_true",
                        help="If set, also save Min–Max normalised prices.")
    parser.add_argument("--series", nargs="+", type=int, default=None,
                        help="Series numbers to plot (e.g., 1 3 5). If omitted, all are plotted.")
    args = parser.parse_args()

    plot_price_data(data_path=args.data_path,
                    output_dir=args.output_dir,
                    normalise=args.normalise,
                    selected_series=args.series)
