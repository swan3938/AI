import csv
from io import TextIOWrapper, BytesIO
import pandas as pd

def preview_csv(file) -> list:
    rows = []
    wrapper = TextIOWrapper(file, encoding="utf-8")
    reader = csv.DictReader(wrapper)
    for i, row in enumerate(reader):
        rows.append(row)
        if i >= 9:
            break
    return rows

def read_csv_all(path: str) -> list:
    out = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            out.append(row)
    return out

def preview_xlsx(file) -> list:
    data = file.read()
    df = pd.read_excel(BytesIO(data))
    rows = []
    for i in range(min(10, len(df))):
        rows.append({k: ("" if pd.isna(v) else v) for k, v in df.iloc[i].to_dict().items()})
    return rows

def read_xlsx_all(path: str) -> list:
    df = pd.read_excel(path)
    out = []
    for i in range(len(df)):
        out.append({k: ("" if pd.isna(v) else v) for k, v in df.iloc[i].to_dict().items()})
    return out

def read_all(path: str) -> list:
    if path.lower().endswith(".xlsx") or path.lower().endswith(".xls"):
        return read_xlsx_all(path)
    return read_csv_all(path)

def read_csv_stream(file) -> list:
    out = []
    wrapper = TextIOWrapper(file, encoding="utf-8")
    reader = csv.DictReader(wrapper)
    for row in reader:
        out.append(row)
    return out

def read_all_stream(file, filename: str) -> list:
    name = (filename or "").lower()
    if name.endswith(".xlsx") or name.endswith(".xls"):
        data = file.read()
        df = pd.read_excel(BytesIO(data))
        return [{k: ("" if pd.isna(v) else v) for k, v in df.iloc[i].to_dict().items()} for i in range(len(df))]
    return read_csv_stream(file)
