# Explainable AI for Diabetic Retinopathy Screening in Rural India
## FastAPI Backend Service

This directory contains the Python FastAPI backend for Diabetic Retinopathy screening and Grad-CAM visual explainability.

---

## 📁 Architecture & Directory Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI endpoints, CORS, static mounts, route handlers
│   ├── model_service.py     # EfficientNet-B0 loader, preprocessing, inference & Grad-CAM
│   └── schemas.py           # Pydantic request & response schemas
├── models/
│   └── dr_model.pth         # PyTorch model weights (Place your trained model here)
├── uploads/                 # Storage for validated fundus scans
├── results/                 # Output directory for generated Grad-CAM heatmap overlays
├── requirements.txt         # Python package dependencies
└── README.md                # Setup and usage guide
```

---

## 🚀 Setup & Installation Instructions

### 1. Create a Python Virtual Environment
Open a terminal in the `backend/` directory:

```bash
# Windows
py -3.12 -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Place Your Trained PyTorch Model
Place your trained EfficientNet-B0 `.pth` model file at:
```
backend/models/dr_model.pth
```

> **Note on Model Architecture:**
> - Architecture: `EfficientNet-B0`
> - Output Classes: 5 (`0: No DR`, `1: Mild`, `2: Moderate`, `3: Severe`, `4: Proliferative DR`)
> - If `dr_model.pth` is missing, the backend starts in standby mode and reports `model_loaded: false` on `/api/health`.

### 4. Run the FastAPI Server with Uvicorn
```bash
# From the backend/ directory
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The server will be live at: `http://127.0.0.1:8000`

---

## 📖 API Documentation

Interactive Swagger documentation is available at:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🧪 Testing the Endpoints

### 1. Health Check
```bash
curl -X GET "http://127.0.0.1:8000/api/health"
```
**Response:**
```json
{
  "status": "ok",
  "model_loaded": true,
  "device": "cuda",
  "model_path": "dr_model.pth"
}
```

### 2. Predict Diabetic Retinopathy Severity
```bash
curl -X POST "http://127.0.0.1:8000/api/predict" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/fundus_image.jpg"
```
**Response:**
```json
{
  "predicted_class": 2,
  "class_name": "Moderate",
  "confidence": 0.942,
  "probabilities": {
    "No DR": 0.012,
    "Mild": 0.035,
    "Moderate": 0.942,
    "Severe": 0.009,
    "Proliferative DR": 0.002
  },
  "inference_time": 0.038
}
```

### 3. Generate Grad-CAM Explainability Heatmap
```bash
curl -X POST "http://127.0.0.1:8000/api/explain" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/fundus_image.jpg"
```
**Response:**
```json
{
  "predicted_class": 2,
  "class_name": "Moderate",
  "gradcam_url": "/results/4b8a2c1f..._gradcam.jpg",
  "explanation": "Highlighted regions indicate image areas that contributed to the model's prediction. This visualization supports professional review and does not constitute a medical diagnosis.",
  "inference_time": 0.075
}
```

### 4. Combined Screening Analysis (Prediction + Grad-CAM)
```bash
curl -X POST "http://127.0.0.1:8000/api/screenings/analyze" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/fundus_image.jpg"
```

---

## 🔒 Security & Input Validation
- **File Format Validation**: Strictly accepts `.jpg`, `.jpeg`, `.png`.
- **Integrity Check**: Rejects corrupt or invalid image byte streams before processing.
- **Upload Limit**: 15MB max file size.
- **UUID File Naming**: Generates collision-free filenames without exposing patient metadata.
- **No Traceback Exposure**: Custom error handlers prevent stack trace leaks to the client.
