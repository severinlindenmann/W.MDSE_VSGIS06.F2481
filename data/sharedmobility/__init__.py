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
    
    sql_view = f"""
    SELECT * FROM `seli-data-storage.data_storage_1.unique_stations`
    """

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

    return query_bigquery_return_gdf(sql_view)


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
    sql_view = f"""
      SELECT * FROM `seli-data-storage.data_storage_1.districts_and_stations`
    """

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
    d.geometry,
    d.u65,
    d.z20_64,
    d.z0_19,
    d.diche_per_ha,
    d.auslaender,
    d.total,
    d.quartier_id,
    d.name
  FROM
    DistrictsWithCounts dc
  JOIN
    `seli-data-storage.data_storage_1.districts` d ON dc.district_name = d.name
)

SELECT
  district_name,
  station_count,
  geometry,
  u65,
  z20_64,
  z0_19,
  diche_per_ha,
  auslaender,
  total,
FROM
  FinalResults

    """

    return query_bigquery_return_gdf(sql_view)

def bigquery_rivers():
    sql_view = f"""
    SELECT * FROM `seli-data-storage.data_storage_1.rivers_in_city` LIMIT 1000
    """

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

    return query_bigquery_return_gdf(sql_view)

def bigquery_stations_and_bikes():
    sql_view = f"""
SELECT * FROM `seli-data-storage.data_storage_1.stations_and_bikes` 
"""
    sql = f"""
    WITH city_limits AS (
    SELECT geometry
    FROM `seli-data-storage.data_storage_1.city`
),
filtered_station_information AS (
    SELECT 
        station_id, 
        ARRAY_AGG(name ORDER BY crawl_time LIMIT 1)[OFFSET(0)] AS first_name,
        ARRAY_AGG(lat ORDER BY crawl_time LIMIT 1)[OFFSET(0)] AS first_lat, 
        ARRAY_AGG(lon ORDER BY crawl_time LIMIT 1)[OFFSET(0)] AS first_lon
    FROM `seli-data-storage.data_storage_1.station_information` si
    JOIN city_limits cl
    ON ST_WITHIN(ST_GEOGPOINT(si.lon, si.lat), cl.geometry)
    GROUP BY station_id
),
filtered_station_information_excluding_teststation AS (
    SELECT *
    FROM filtered_station_information
    WHERE first_name NOT LIKE '%Teststation%'
),
filtered_station_status AS (
    SELECT 
        station_id, 
        num_bikes_available, 
        EXTRACT(HOUR FROM crawl_time) AS hour_of_day
    FROM `seli-data-storage.data_storage_1.station_status`
    WHERE provider_id LIKE '%nextbike%'
    AND EXTRACT(YEAR FROM crawl_time) = 2023
),
aggregated_station_status AS (
    SELECT 
        station_id, 
        hour_of_day, 
        AVG(num_bikes_available) AS avg_num_bikes_available
    FROM filtered_station_status
    GROUP BY station_id, hour_of_day
)

SELECT 
    fsi.station_id, 
    ST_GEOGPOINT(fsi.first_lon, fsi.first_lat) AS geometry,
    fsi.first_name AS name,
    ass.hour_of_day, 
    ROUND(ass.avg_num_bikes_available,2) AS avg_num_bikes_available
FROM filtered_station_information_excluding_teststation fsi
JOIN aggregated_station_status ass ON fsi.station_id = ass.station_id
ORDER BY fsi.station_id, ass.hour_of_day;
"""

    return query_bigquery_return_gdf(sql_view)