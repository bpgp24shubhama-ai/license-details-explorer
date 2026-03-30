from io import BytesIO

import pandas as pd
import pytest

from app.services.excel_service import ExcelService
from shared.exceptions.app_exceptions import AppException


def _build_excel_bytes(dataframe: pd.DataFrame) -> bytes:
    stream = BytesIO()
    dataframe.to_excel(stream, index=False)
    return stream.getvalue()


def test_excel_service_parses_valid_rows_and_invalid_rows():
    dataframe = pd.DataFrame(
        {
            "value": ["FSSAI", "", "Mumbai"],
            "description": ["Category", "Missing", "City"],
        }
    )
    file_bytes = _build_excel_bytes(dataframe)

    rows, invalid_rows = ExcelService().parse_reference_rows(file_bytes)

    assert len(rows) == 2
    assert invalid_rows == 1
    assert rows[0]["raw_value"] == "FSSAI"


def test_excel_service_raises_when_value_column_missing():
    dataframe = pd.DataFrame({"unexpected_column": ["A", "B"]})
    file_bytes = _build_excel_bytes(dataframe)

    with pytest.raises(AppException) as exc:
        ExcelService().parse_reference_rows(file_bytes)

    assert exc.value.code == "missing_value_column"
