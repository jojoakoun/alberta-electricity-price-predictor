from pathlib import Path
from electricity_predictor.config import load_configuration
from electricity_predictor.data.ingestion import load_historical_data

def build_interim_dataset() -> Path:
  """Build the cleaned interim dataset from the raw historical CSV."""
  configuration = load_configuration()
  
  raw_data_dir = Path(configuration["paths"]["raw_data_dir"])
  interim_data_dir = Path(configuration["paths"]["interim_data_dir"])
  csv_name = configuration["data"]["historical_csv_name"]

  raw_csv_path = raw_data_dir / csv_name
  interim_output_path = interim_data_dir / "historical_prices_clean.csv"
  
  # Create the output folder if it does not exist yet.
  interim_data_dir.mkdir(parents=True, exist_ok=True)
  data = load_historical_data(raw_csv_path)
  data.to_csv(interim_output_path, index=False)
  return interim_output_path

if __name__ == "__main__":
  output_path = build_interim_dataset()
  print(f"Interim dataset written to: {output_path}")