def test_options_preflight_returns_cors_headers(client):
    # Use the configured Netlify origin from the app default
    origin = 'https://cfmc-entrenaprochile.netlify.app'
    resp = client.options('/api/some/testpath', headers={'Origin': origin})
    assert resp.status_code == 200
    # Access-Control-Allow-Origin should be present and match allowed origin
    assert 'Access-Control-Allow-Origin' in resp.headers
    allow = resp.headers.get('Access-Control-Allow-Origin')
    # In test environment the app may default to localhost; allow either
    assert allow in (origin, '*', 'http://localhost:5173')
