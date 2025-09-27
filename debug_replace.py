import json
s = 'a\\b'
print(json.dumps(s))
s = s.replace('\\', '\\')
print(json.dumps(s))
