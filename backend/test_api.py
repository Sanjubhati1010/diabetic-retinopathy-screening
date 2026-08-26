import io
import json
import urllib.request
import urllib.error
from PIL import Image

def test_health():
    req = urllib.request.Request("http://127.0.0.1:8000/api/health")
    with urllib.request.urlopen(req) as response:
        print("Health Check Response:", response.status, json.loads(response.read().decode()))

def post_multipart(url, filename, file_bytes, content_type="image/jpeg"):
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("latin-1") + file_bytes + f"\r\n--{boundary}--\r\n".encode("latin-1")

    req = urllib.request.Request(url, data=body)
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

def run_tests():
    # 1. Health check
    test_health()

    # 2. Sample image
    img = Image.new("RGB", (224, 224), color=(180, 50, 20))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    jpeg_bytes = buf.getvalue()

    # 3. Predict without model -> Expected 503
    status_pred, body_pred = post_multipart("http://127.0.0.1:8000/api/predict", "sample.jpg", jpeg_bytes)
    print("Predict without model -> Status:", status_pred, body_pred)
    assert status_pred == 503
    assert body_pred["detail"] == "Trained model is not available."

    # 4. Explain without model -> Expected 503
    status_exp, body_exp = post_multipart("http://127.0.0.1:8000/api/explain", "sample.jpg", jpeg_bytes)
    print("Explain without model -> Status:", status_exp, body_exp)
    assert status_exp == 503
    assert body_exp["detail"] == "Trained model is not available."

    # 5. Invalid file format -> Expected 400
    status_inv, body_inv = post_multipart("http://127.0.0.1:8000/api/predict", "bad_file.txt", b"plain text", "text/plain")
    print("Invalid extension test -> Status:", status_inv, body_inv)
    assert status_inv == 400
    assert "Unsupported file format" in body_inv["detail"]

    print("\nALL BACKEND API TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
