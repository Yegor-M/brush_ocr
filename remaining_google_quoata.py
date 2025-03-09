from google.cloud import monitoring_v3
from google.protobuf.timestamp_pb2 import Timestamp
import datetime
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv(dotenv_path=Path('../.env'))

# Path to your service account JSON file
credentials_path = os.getenv("GOOGLE_CRED_PATH")

# Initialize the Monitoring client with credentials
client = monitoring_v3.MetricServiceClient.from_service_account_json(credentials_path)

# Configuration
project_id = os.getenv("PROJECT_ID")  # Replace with your Google Cloud project ID
metric_type_request_count = "serviceruntime.googleapis.com/api/request_count"  # Metric for API requests
metric_type_quota_usage = "serviceruntime.googleapis.com/quota/allocation/usage"  # Correct metric for quota usage

# Create a time range (last 30 days)
end_time = datetime.datetime.now(datetime.timezone.utc)
start_time = end_time - datetime.timedelta(days=30)

# Convert datetime to Timestamp
start_timestamp = Timestamp()
start_timestamp.FromDatetime(start_time)
end_timestamp = Timestamp()
end_timestamp.FromDatetime(end_time)

# Create a TimeInterval
time_interval = monitoring_v3.TimeInterval(
    start_time=start_timestamp,
    end_time=end_timestamp,
)

# Fetch request count
request_count_series = client.list_time_series(
    name=f"projects/{project_id}",
    filter=f'metric.type = "{metric_type_request_count}"',
    interval=time_interval,
    view=monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
)

total_requests = 0
for series in request_count_series:
    for point in series.points:
        total_requests += int(point.value.int64_value)

print(f"Total API requests in the last 30 days: {total_requests}")

# Fetch quota usage
quota_usage_series = client.list_time_series(
    name=f"projects/{project_id}",
    filter=f'metric.type = "{metric_type_quota_usage}"',
    interval=time_interval,
    view=monitoring_v3.ListTimeSeriesRequest.TimeSeriesView.FULL,
)

total_quota_used = 0
for series in quota_usage_series:
    for point in series.points:
        total_quota_used += int(point.value.double_value)

print(f"Total quota used in the last 30 days: {total_quota_used} units")

# Check free tier usage
free_tier_limit = 1000  # First 1,000 units are free
if total_quota_used <= free_tier_limit:
    print(f"You are within the free tier limit. Units used: {total_quota_used}/{free_tier_limit}")
else:
    print(f"You have exceeded the free tier limit. Units used: {total_quota_used}/{free_tier_limit}")