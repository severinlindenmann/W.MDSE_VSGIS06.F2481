from data.sharedmobility import (
    bigquery_unique_stations,
    bigquery_unique_bikes,
    query_bigquery_return_df,
    bigquery_city_boundary,
    bigquery_districts_and_stations,
    bigquery_rivers,
    bigquery_stations_and_bikes
)


def sharedmobility(type="unique_stations", inside_city=False, custom_sql=None):
    """
    Shared mobility data for the region of Luzern.

    Returns:
    DataFrame: A DataFrame containing shared mobility data.

    Args:
    type (str): The type of shared mobility data to retrieve. Options are:
        - unique_stations
        - unique_bikes
    """
    if custom_sql:
        return query_bigquery_return_df(custom_sql)
    if type == "unique_stations":
        return bigquery_unique_stations(inside_city=inside_city)
    elif type == "unique_bikes":
        return bigquery_unique_bikes()
    elif type == "city_boundary":
        return bigquery_city_boundary()
    elif type == "districts_and_stations":
        return bigquery_districts_and_stations()
    elif type == "rivers":
        return bigquery_rivers()
    elif type == 'stations_and_bikes':
        return bigquery_stations_and_bikes()
    else:
        raise ValueError("Invalid type. Please choose the available types.")
