import jwt
payload = {
    "sub": "narasimha@beskar.tech",
    "name": "Narasimha CI",
    "admin": True,
    "iat": 1847577798
}
token = jwt.encode(payload, "your-super-secret-key", algorithm="HS256")
print(token)