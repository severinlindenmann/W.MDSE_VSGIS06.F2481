from data.sharedmobility import (
    bigquery_unique_stations,
    bigquery_unique_bikes,
    query_bigquery_return_df,
    bigquery_city_boundary,
)
from joblib import Memory

# Create a Memory object with the specified cache directory to store the cached data
memory = Memory("cache", verbose=0)

# @memory.cache
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
    elif type=="city_boundary":
        return bigquery_city_boundary()
    else:
        raise ValueError("Invalid type. Please choose from: unique_stations, unique_bikes, city_boundary.")
