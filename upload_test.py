import urllib.request
import json

# Upload test Excel file using urllib
with open('test_with_x.xlsx', 'rb') as f:
    boundary = '----WebKitFormBoundary'
    body = []
    body.append(f'--{boundary}'.encode())
    body.append(b'Content-Disposition: form-data; name="file"; filename="test_with_x.xlsx"')
    body.append(b'Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    body.append(b'')
    body.append(f.read())
    body.append(f'--{boundary}--'.encode())
    body.append(b'')
    
    data = b'\r\n'.join(body)
    
    req = urllib.request.Request(
        'http://127.0.0.1:8010/api/v1/import-excel',
        data=data,
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'}
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            print(f"Status: {response.status}")
            print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
    except urllib.error.HTTPError as e:
        print(f"Error: {e.status}")
        print(e.read().decode())
