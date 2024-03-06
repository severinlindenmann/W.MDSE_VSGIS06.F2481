from datetime import datetime
import os
from google.cloud import bigquery

def create_bigquery_connection():
    service_account_key_path = 'service_key.json'
    
    if os.path.exists(service_account_key_path):
        return bigquery.Client.from_service_account_json(service_account_key_path, project="seli-data-storage")
    else:
        return bigquery.Client(project="seli-data-storage")
    
def query_bigquery_return_df(query):
    query_job = create_bigquery_connection().query(query)
    results = query_job.result()
    
    return results.to_dataframe()


def bigquery_unique_stations(timefilter=datetime.now().strftime("%Y-%m-%d")):
  sql = f"""
SELECT DISTINCT station_id, name, lat,lon
FROM `seli-data-storage.data_storage_1.station_information`
WHERE TIMESTAMP_TRUNC(crawl_time, DAY) = TIMESTAMP("{timefilter}") 
AND station_id LIKE '%nextbike%';
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