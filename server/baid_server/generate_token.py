import jwt
payload = {
    "sub": "narasimha@beskar.tech",
    "name": "Narasimha CI",
    "admin": True,
    "iat": 1715600000
}
token = jwt.encode(payload, "a-string-secret-at-least-256-bits-long", algorithm="HS256")
print(token)