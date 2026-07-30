from requests.models import Request
r = Request('GET', 'http://example.com')
def h1(x): pass
def h2(x): pass
r.register_hook('response', [h1, h2])
print('hooks count:', len(r.hooks['response']))
assert len(r.hooks['response']) == 2
print('OK!')
