import base64
import json

def lambda_handler(event, context):
    output = []

    for record in event['records']:
        print(record['recordId'])
        payload = base64.b64decode(record['data'])

        payload_dict = json.loads(payload)
        payload = json.dumps(payload_dict)
        
        payload = payload + "\n"

        output_record = {
            'recordId': record['recordId'],
            'result': 'Ok',
            'data': base64.b64encode(payload.encode()).decode("utf-8")
        }
        output.append(output_record)
        print(output[0])

    print('Successfully processed {} records.'.format(len(event['records'])))

    return {'records': output}

if __name__ == '__main__':
    context = ''
    event = {
        'records': [
            {
                'recordId': '123',
                'data': base64.b64encode('{ "test": "test" }'.encode())
            }
        ]
    }
    lambda_handler(event,context)