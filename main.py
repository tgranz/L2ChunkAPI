# Imports
import json, os, boto3
from datetime import datetime, timezone
from time import sleep
from threading import Thread

from database import update_database
from api import app

# Constants
REGION = "us-east-1"
TOPIC_ARN = "arn:aws:sns:us-east-1:684042711724:NewNEXRADLevel2ObjectFilterable"
QUEUE_NAME = "NexradJobQueue"
API_PORT = 5000

# Function to build a boto3 session, optionally using a specific AWS profile
def build_session() -> boto3.Session:
	profile = os.getenv("AWS_PROFILE")
	if profile:
		return boto3.Session(profile_name=profile, region_name=REGION)
	return boto3.Session(region_name=REGION)

# Build AWS session and clients
session = build_session()
sns = session.client("sns")
sqs = session.client("sqs")
sts = session.client("sts")

# Get AWS account ID for logging and policy construction
identity = sts.get_caller_identity()
account_id = identity["Account"]

# Create SQS queue and subscribe it to the SNS topic with a filter policy
queue = sqs.create_queue(
	QueueName=QUEUE_NAME,
	Attributes={
		"MessageRetentionPeriod": "60",  # Discard messages older than 60 seconds (SQS minimum)
	},
)
queue_url = queue["QueueUrl"]
queue_arn = sqs.get_queue_attributes(
	QueueUrl=queue_url,
	AttributeNames=["QueueArn"],
)["Attributes"]["QueueArn"]

# Ensure retention period is set even if queue already existed
sqs.set_queue_attributes(
	QueueUrl=queue_url,
	Attributes={"MessageRetentionPeriod": "60"},
)
policy = {
	"Version": "2012-10-17",
	"Statement": [
		{
			"Sid": "AllowNexradTopicSendMessage",
			"Effect": "Allow",
			"Principal": {"Service": "sns.amazonaws.com"},
			"Action": "sqs:SendMessage",
			"Resource": queue_arn,
			"Condition": {"ArnEquals": {"aws:SourceArn": TOPIC_ARN}},
		}
	],
}

# Set the queue policy to allow SNS to send messages to it
sqs.set_queue_attributes(
	QueueUrl=queue_url,
	Attributes={"Policy": json.dumps(policy)},
)

# Subscribe the SQS queue to the SNS topic
subscription = sns.subscribe(
	TopicArn=TOPIC_ARN,
	Protocol="sqs",
	Endpoint=queue_arn,
	ReturnSubscriptionArn=True,
)

# Filter to only receive messages where ChunkType == "E" (final chunk) and L2Version == "V06"
filter_policy = {
	"ChunkType": ["E"],
	"L2Version": ["V06"]
}

# Set the filter policy on the subscription
sns.set_subscription_attributes(
	SubscriptionArn=subscription["SubscriptionArn"],
	AttributeName="FilterPolicy",
	AttributeValue=json.dumps(filter_policy),
)

# Call a purge on undeleted messages in the queue
# This way incoming messages while the script was not running do not eat up unnecessary processing time
print("Purging any existing messages in the SQS queue... (this takes 60 seconds)")
sqs.purge_queue(QueueUrl=queue_url)
sleep(60)
print(f"Subscribed SQS queue '{QUEUE_NAME}' to SNS topic with filter policy: {json.dumps(filter_policy)}")

# Start Flask API in a background thread
api_thread = Thread(target=lambda: app.run(host="0.0.0.0", port=API_PORT, debug=False, use_reloader=False), daemon=True)
api_thread.start()
print(f"API running at http://localhost:{API_PORT}")

# Helper function to parse JSON if the value is a string, otherwise return as-is
def parse_json_maybe(value):
	if isinstance(value, dict):
		return value
	if isinstance(value, str):
		try:
			return json.loads(value)
		except json.JSONDecodeError:
			return value
	return value


print("Listening for new NEXRAD notifications... Press Ctrl+C to stop.")

# Message listener loop
try:
	while True:
		# Poll the SQS queue for messages with long polling
		response = sqs.receive_message(
			QueueUrl=queue_url,
			MaxNumberOfMessages=10,
			WaitTimeSeconds=20,
			MessageAttributeNames=["All"],
			AttributeNames=["All"],
		)

		messages = response.get("Messages", [])
		if not messages:
			continue

		for raw_msg in messages:
			receipt_handle = raw_msg["ReceiptHandle"]
			body = parse_json_maybe(raw_msg.get("Body", ""))

			sns_envelope = body if isinstance(body, dict) else {"Message": body}
			inner_message = parse_json_maybe(sns_envelope.get("Message"))

			print("\n" + "=" * 72)
			print(f"Received at: {datetime.now(timezone.utc).isoformat()}")
			print(f"SNS Topic: {sns_envelope.get('TopicArn', TOPIC_ARN)}")
			print(f"SNS Timestamp: {sns_envelope.get('Timestamp', 'N/A')}")

			if isinstance(inner_message, dict):
				print(
					"Summary: "
					f"SiteID={inner_message.get('SiteID')} "
					f"DateTime={inner_message.get('DateTime')} "
					f"ChunkType={inner_message.get('ChunkType')} "
					f"Key={inner_message.get('Key')}"
				)
				print("Payload:")
				print(json.dumps(inner_message, indent=2))
				
				# Update database with new data
				try:
					update_database(inner_message)
					print(f"[DB] Updated {inner_message.get('SiteID')}")
				except Exception as db_err:
					print(f"[DB ERROR] {db_err}")
			else:
				print("Payload (raw):")
				print(inner_message)

            # Delete the message from the queue after processing
			sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)

# Manually stop the listener with Ctrl+C
except KeyboardInterrupt:
	print("\nStopped listener.")

# Handle errors gracefully
except Exception as e:
	print(f"Error: {e}")