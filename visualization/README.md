# Visualization Tools

## Setup

```bash
cd visualization
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```bash
python visualize.py ../results/analysis.csv --output-dir ./charts
```

## Output

Generates:
- Statistical charts (PNG files)
- Statistical report (TXT file)
- Decision recommendations
