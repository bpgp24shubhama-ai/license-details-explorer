from io import BytesIO
from typing import Any

import pandas as pd

from shared.exceptions.app_exceptions import AppException


class ExcelService:
    VALUE_COLUMN_CANDIDATES = [
        "value",
        "name",
        "category",
        "location",
        "master_value",
    ]

    def parse_reference_rows(self, excel_bytes: bytes) -> tuple[list[dict[str, Any]], int]:
        try:
            dataframe = pd.read_excel(BytesIO(excel_bytes), dtype=str)
        except Exception as exc:
            raise AppException(
                status_code=400,
                code="invalid_excel",
                detail="Failed to parse Excel file",
            ) from exc

        if dataframe.empty:
            raise AppException(
                status_code=422,
                code="empty_excel",
                detail="Uploaded Excel does not contain rows",
            )

        normalized_columns = {
            column: str(column).strip().lower().replace(" ", "_")
            for column in dataframe.columns
        }
        dataframe = dataframe.rename(columns=normalized_columns)

        value_column = next(
            (col for col in self.VALUE_COLUMN_CANDIDATES if col in dataframe.columns),
            None,
        )
        if value_column is None:
            raise AppException(
                status_code=422,
                code="missing_value_column",
                detail=(
                    "Excel must include one of these columns: "
                    f"{', '.join(self.VALUE_COLUMN_CANDIDATES)}"
                ),
            )

        parsed_rows: list[dict[str, Any]] = []
        invalid_rows = 0

        for _, row in dataframe.iterrows():
            raw_value = str(row.get(value_column, "")).strip()
            if not raw_value or raw_value.lower() == "nan":
                invalid_rows += 1
                continue

            metadata: dict[str, Any] = {}
            for key, value in row.items():
                if key == value_column:
                    continue
                text_value = str(value).strip()
                if text_value and text_value.lower() != "nan":
                    metadata[key] = text_value

            parsed_rows.append({"raw_value": raw_value, "metadata_json": metadata})

        if not parsed_rows:
            raise AppException(
                status_code=422,
                code="no_valid_rows",
                detail="Excel has no valid non-empty reference values",
            )

        return parsed_rows, invalid_rows
