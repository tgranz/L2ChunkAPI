"""One-shot script to delete NexradJobQueue so it can be recreated with correct settings."""
import os, time, boto3

REGION = "us-east-1"
QUEUE_NAME = "NexradJobQueue"

profile = os.getenv("AWS_PROFILE")
session = boto3.Session(profile_name=profile, region_name=REGION) if profile else boto3.Session(region_name=REGION)
sqs = session.client("sqs")

account_id = session.client("sts").get_caller_identity()["Account"]
queue_url = f"https://sqs.{REGION}.amazonaws.com/{account_id}/{QUEUE_NAME}"

sqs.delete_queue(QueueUrl=queue_url)
print(f"Deleted: {queue_url}")
print("Waiting 60 seconds for SQS to fully remove it...")
time.sleep(60)
print("Done. You can now run main.py.")
