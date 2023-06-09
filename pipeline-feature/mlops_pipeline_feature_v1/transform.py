import pandas as pd


def cast_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # TODO: here is hardcoded
    df["utc_singapore_time"] = (
        df["utc_datetime"].dt.tz_localize("UTC").dt.tz_convert("Asia/Singapore")
    )
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")

    for column in [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "quote_asset_volume",
        "taker_buy_base_asset_volume",
        "taker_buy_quote_asset_volume",
    ]:
        df[column] = df[column].astype(float)
    return df
