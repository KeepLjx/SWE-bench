from requests.sessions import Session
s = Session()
r = s.request(b'GET', 'https://httpbin.org/get')
print('Status:', r.status_code)
print('Method used:', r.request.method)
