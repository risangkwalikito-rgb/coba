# app.py
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


REQUIRED_COLUMNS = ["Kode Booking Awal", "Booking Code"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Kelompokkan data berdasarkan 'Kode Booking Awal', "
            "urutkan 'Booking Code', lalu beri nomor grup dan nomor urut."
        )
    )
    parser.add_argument(
        "input_file",
        help="Path file input (.xlsx, .xls, atau .csv)",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Path file output. Jika kosong, otomatis dibuat di folder yang sama.",
    )
    parser.add_argument(
        "-s",
        "--sheet",
        default=0,
        help="Nama sheet atau index sheet Excel. Default: 0",
    )
    return parser.parse_args()


def load_data(file_path: Path, sheet: str | int = 0) -> pd.DataFrame:
    suffix = file_path.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(file_path)

    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(file_path, sheet_name=sheet)

    raise ValueError("Format file tidak didukung. Gunakan .xlsx, .xls, atau .csv")


def validate_columns(df: pd.DataFrame) -> None:
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_columns:
        joined = ", ".join(missing_columns)
        raise ValueError(f"Kolom wajib tidak ditemukan: {joined}")


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    normalized = df.copy()

    for column in REQUIRED_COLUMNS:
        normalized[column] = (
            normalized[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    return normalized


def group_and_number(df: pd.DataFrame) -> pd.DataFrame:
    processed = normalize_columns(df)

    processed = processed.sort_values(
        by=["Kode Booking Awal", "Booking Code"],
        kind="mergesort",
    ).reset_index(drop=True)

    processed["Nomor Grup"] = pd.factorize(
        processed["Kode Booking Awal"],
        sort=False,
    )[0] + 1

    processed["Nomor Urut per Grup"] = (
        processed.groupby("Kode Booking Awal")
        .cumcount()
        .add(1)
    )

    processed["Nomor Urut Global"] = range(1, len(processed) + 1)

    ordered_columns = [
        "Nomor Grup",
        "Nomor Urut per Grup",
        "Nomor Urut Global",
        *[column for column in processed.columns if column not in {
            "Nomor Grup",
            "Nomor Urut per Grup",
            "Nomor Urut Global",
        }],
    ]

    return processed[ordered_columns]


def build_output_path(input_file: Path, output: str | None) -> Path:
    if output:
        return Path(output)

    return input_file.with_name(f"{input_file.stem}_grouped{input_file.suffix}")


def save_data(df: pd.DataFrame, output_path: Path) -> None:
    suffix = output_path.suffix.lower()

    if suffix == ".csv":
        df.to_csv(output_path, index=False)
        return

    if suffix in {".xlsx", ".xls"}:
        df.to_excel(output_path, index=False)
        return

    raise ValueError("Format output tidak didukung. Gunakan .xlsx, .xls, atau .csv")


def print_summary(df: pd.DataFrame) -> None:
    summary = (
        df.groupby(["Nomor Grup", "Kode Booking Awal"], dropna=False)
        .size()
        .reset_index(name="Jumlah Baris")
    )

    print("\nRingkasan grup:")
    for row in summary.itertuples(index=False):
        print(
            f"- Grup {row[0]} | Kode Booking Awal: {row[1]} | "
            f"Jumlah Baris: {row[2]}"
        )


def main() -> None:
    args = parse_args()
    input_file = Path(args.input_file)

    if not input_file.exists():
        raise FileNotFoundError(f"File tidak ditemukan: {input_file}")

    sheet = args.sheet
    if isinstance(sheet, str) and sheet.isdigit():
        sheet = int(sheet)

    df = load_data(input_file, sheet=sheet)
    validate_columns(df)

    result = group_and_number(df)

    output_path = build_output_path(input_file, args.output)
    save_data(result, output_path)

    print(f"Berhasil memproses file: {input_file}")
    print(f"Hasil disimpan ke: {output_path}")
    print_summary(result)


if __name__ == "__main__":
    main()
