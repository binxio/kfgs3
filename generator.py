import random
import uuid
import pprint
import json
import datetime
import boto3
import sys

names = ["martijn", "dennis", "bart", "thijs", "mark", "constantijn", "kevin", "walter", "rob"]
cities = ["hoorn", "amsterdam", "hilversum", "utrecht", "wijk bij duurstede", "new york", "rotterdam"]
amount = random.randint(1,10000)
percentage = random.uniform(0, 1)

message = {
    "id": str(uuid.uuid4()),
    "name": random.choice(names),
    "city": random.choice(cities),
    "amount": amount,
    "percentage": percentage
}
string_message = json.dumps(message)
print(string_message)

client = boto3.client('kinesis')
response = client.put_record(
    StreamName=sys.argv[1],
    Data=string_message.encode(),
    PartitionKey='1'
)
print(response)