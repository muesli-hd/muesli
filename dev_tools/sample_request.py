import requests
import json

url = "http://127.0.0.1:8080"
r = requests.post(url+"/debug/login", data={"email": "test@test.de", "password": "1234"})


token = r.json()["token"]
headers = {'Accept': 'application/json', 'Authorization': str('JWT '+token)}

lecture_endpoint = url + "/api/lectures"
get = requests.get(lecture_endpoint, headers=headers)

# print(r.json())

# lecture = {"term": 20182, "name": "Informatik", "assistants": [{"email": "test@test.de"}]}
lecture = {}
post = requests.post(lecture_endpoint, headers=headers, json=lecture)
print(post.json())
print(post)
