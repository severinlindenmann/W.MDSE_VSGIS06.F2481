from datetime import datetime
import os
from google.cloud import bigquery


def create_bigquery_connection():
    service_account_key_path = "service_key.json"

    if os.path.exists(service_account_key_path):
        return bigquery.Client.from_service_account_json(
            service_account_key_path, project="seli-data-storage"
        )
    else:
        return bigquery.Client(project="seli-data-storage")


def query_bigquery_return_df(query):
    query_job = create_bigquery_connection().query(query)
    results = query_job.result()

    return results.to_dataframe()

def query_bigquery_return_gdf(query):
    query_job = create_bigquery_connection().query(query)
    results = query_job.result()

    return results.to_geodataframe()

def bigquery_unique_stations(
    timefilter=datetime.now().strftime("%Y-%m-%d"), inside_city=False
):
    # Basic SQL query without the ST_CONTAINS clause
    sql = f"""
    SELECT DISTINCT station_id, name, lat, lon
    FROM `seli-data-storage.data_storage_1.station_information`
    WHERE TIMESTAMP_TRUNC(crawl_time, DAY) = TIMESTAMP("{timefilter}") 
    AND station_id LIKE '%nextbike%'
    """

    # If inside_city is True, add the ST_CONTAINS clause
    if inside_city:
        sql += """
        AND ST_CONTAINS((SELECT geometry
                         FROM `seli-data-storage.data_storage_1.city`
                         LIMIT 1), ST_GEOGPOINT(lon, lat))
        """

    return query_bigquery_return_df(sql)


def bigquery_unique_bikes():
    sql = f"""
WITH FirstCrawlTime AS (
  SELECT *
  FROM `seli-data-storage.data_storage_1.nextbike_free_bike_status` AS s
  ORDER BY s.crawl_time DESC
  LIMIT 1
)

SELECT *
FROM `seli-data-storage.data_storage_1.nextbike_free_bike_status` AS s
WHERE s.crawl_time = (SELECT crawl_time FROM FirstCrawlTime);
  """

    return query_bigquery_return_df(sql)

def bigquery_city_boundary():
    sql = f"""
    SELECT geometry
    FROM `seli-data-storage.data_storage_1.city`
    LIMIT 1
    """

    return query_bigquery_return_gdf(sql)

def bigquery_districts_and_stations(timefilter=datetime.now().strftime("%Y-%m-%d")):
    sql = f"""
WITH DistinctStations AS (
  SELECT
    DISTINCT station_id,
    lat,
    lon
  FROM
    `seli-data-storage.data_storage_1.station_information`
  WHERE
    TIMESTAMP_TRUNC(crawl_time, DAY) = TIMESTAMP("{timefilter}")
    AND station_id LIKE '%nextbike%'
),
StationPoints AS (
  SELECT
    station_id,
    ST_GEOGPOINT(lon, lat) AS station_point
  FROM
    DistinctStations
),
DistrictsWithCounts AS (
  SELECT
    d.name AS district_name,
    COUNT(s.station_id) AS station_count
  FROM
    `seli-data-storage.data_storage_1.districts` d
  LEFT JOIN
    StationPoints s
  ON
    ST_WITHIN(s.station_point, d.geometry)
  GROUP BY
    d.name
),
FinalResults AS (
  SELECT
    dc.district_name,
    dc.station_count,
    d.geometry
  FROM
    DistrictsWithCounts dc
  JOIN
    `seli-data-storage.data_storage_1.districts` d ON dc.district_name = d.name
)

SELECT
  district_name,
  station_count,
  geometry
FROM
  FinalResults

    """

    return query_bigquery_return_gdf(sql)

def bigquery_rivers():
    sql = f"""
    WITH Canton AS (
  SELECT 
    geometry 
  FROM 
    `seli-data-storage.data_storage_1.canton`
)

SELECT
  r.*
FROM
  `seli-data-storage.data_storage_1.geo_rivers` r,
  Canton c
WHERE
  ST_INTERSECTS(ST_STARTPOINT(r.geometry), c.geometry)
  OR ST_INTERSECTS(ST_ENDPOINT(r.geometry), c.geometry)
"""

    return query_bigquery_return_gdf(sql)