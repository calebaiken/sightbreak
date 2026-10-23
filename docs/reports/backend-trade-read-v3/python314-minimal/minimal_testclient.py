"""No Sightbreak/database imports: isolate the local TestClient runtime failure."""
import sys
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

@app.get('/')
def root():
    return {'ok': True}

print(sys.version, flush=True)
print(TestClient(app).get('/').json(), flush=True)
