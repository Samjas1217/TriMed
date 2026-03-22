
from flask import Flask, request, jsonify, session, render_template, redirect, send_from_directory
from flask_cors import CORS
from bson import ObjectId
from database.mongo import patients_collection, uploads_collection, staff_collection, admin_collection
from services.fax_pipeline import process_fax
from agents.patient_query_agent import get_patient_documents
from datetime import datetime
from pdf2image import convert_from_path
import os
import uuid
import cv2
from agents.patient_search_agent import ai_patient_search
from agents.document_search_agent import ai_document_search

app = Flask(__name__)
CORS(app, supports_credentials=True)

app.secret_key = "super_secret_key"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
PROCESSED_FOLDER = os.path.join(BASE_DIR, "processed")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

POPPLER_PATH = r"C:\poppler-25.12.0\Library\bin"


# -------------------------
# PAGE ROUTES
# -------------------------

@app.route("/")
def index():
    return render_template("Landing.html")


@app.route("/login")
def login_page():
    return render_template("login.html")


@app.route("/adminlogin")
def admin_login_page():
    return render_template("Adminlogin.html")


@app.route("/admindash")
def admin_dashboard():

    if "admin_id" not in session:
        return redirect("/adminlogin")

    return render_template("admindash.html")
# -------------------------
# ADD STAFF (ADMIN)
# -------------------------

@app.route("/add_staff", methods=["POST"])
def add_staff():

    if "admin_id" not in session:
        return jsonify({"status":"unauthorized"}), 401

    data = request.json

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")
    department = data.get("department")
    phone = data.get("phone")
    employee_id = data.get("employee_id")

    # check if employee already exists
    existing = staff_collection.find_one({"employee_id": employee_id})

    if existing:
        return jsonify({
            "status":"error",
            "message":"Employee ID already exists"
        })

    staff_collection.insert_one({

        "name": name,
        "email": email,
        "password": password,
        "role": role,
        "department": department,
        "phone": phone,
        "employee_id": employee_id,
        "is_active": True,
        "created_at": datetime.utcnow()

    })

    return jsonify({"status":"success"})


@app.route("/api/merge_patients", methods=["POST"])
def merge_patients():
    if "admin_id" not in session:
        return jsonify({"status": "unauthorized"}), 401

    data = request.json
    primary_id = data.get("primary_id")
    duplicate_id = data.get("duplicate_id")

    if not primary_id or not duplicate_id:
        return jsonify({"error": "Missing patient IDs"}), 400

    # 1. Reassign all uploads that belong to the duplicate
    uploads_collection.update_many(
        {"matched_patient_id": duplicate_id},
        {"$set": {"matched_patient_id": primary_id}}
    )

    # 2. Delete the duplicate patient
    patients_collection.delete_one({"patient_id": duplicate_id})

    return jsonify({"status": "success", "message": "Patients merged successfully"})


@app.route("/dashboard")
def dashboard():

    if "staff_id" not in session:
        return redirect("/login")

    return render_template("dashboard.html")

@app.route("/ai_patient_search", methods=["POST"])
def ai_patient_search_route():

    data = request.json

    query = data.get("query")

    if not query:
        return jsonify({"patients": []})

    patients = ai_patient_search(query)

    return jsonify({
        "patients": patients
    })

@app.route("/api/document_search", methods=["POST"])
def ai_document_search_route():
    if "staff_id" not in session and "admin_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    query = data.get("query")

    if not query:
        return jsonify({"documents": []})

    documents = ai_document_search(query)

    return jsonify({
        "documents": documents
    })

@app.route("/text_extraction")
def text_extraction():

    if "staff_id" not in session:
        return redirect("/login")

    image_path = session.get("last_processed_image")

    if not image_path:
        return redirect("/dashboard")

    filename = os.path.basename(image_path)

    return render_template(
        "ocr_extraction.html",
        image_filename=filename
    )


@app.route("/patient_timeline/<patient_id>")
def patient_timeline(patient_id):

    if "staff_id" not in session:
        return redirect("/login")

    docs = get_patient_documents(patient_id)

    # Basic Smart Dashboard aggregations
    doc_types = {}
    recent_visits = 0
    duplicate_warnings = 0
    alerts = []
    
    thirty_days_ago = datetime.utcnow().timestamp() - (30 * 24 * 60 * 60)
    
    for doc in docs:
        dtype = doc.get("document_type", "Unknown")
        doc_types[dtype] = doc_types.get(dtype, 0) + 1
        
        # Check if in last 30 days
        uploaded_at = doc.get("uploaded_at")
        if uploaded_at and uploaded_at.timestamp() > thirty_days_ago:
            recent_visits += 1
            
        risk = doc.get("duplicate_risk", 0)
        if hasattr(risk, 'real'): # might be a string from Gemini sometimes, ensure it's a number
             try:
                 if float(risk) > 50:
                     duplicate_warnings += 1
             except ValueError:
                 pass
                 
        summary = doc.get("medical_summary", {})
        action = summary.get("recommended_action", "").lower()
        if "urgent" in action or "immediate" in action or "er" in action:
            alerts.append(f"Urgent action in {dtype} on {uploaded_at.strftime('%Y-%m-%d') if uploaded_at else 'Unknown date'}")
            
    stats = {
       "doc_types": doc_types,
       "recent_visits": recent_visits,
       "duplicate_warnings": duplicate_warnings,
       "alerts": alerts
    }

    return render_template(
        "timeline.html",
        documents=docs,
        patient_id=patient_id,
        stats=stats
    )


@app.route("/processed/<filename>")
def serve_processed(filename):
    return send_from_directory(PROCESSED_FOLDER, filename)


# -------------------------
# STAFF LOGIN
# -------------------------

@app.route("/api/login", methods=["POST"])
def login():

    data = request.json

    employee_id = data.get("employee_id")
    password = data.get("password")

    staff = staff_collection.find_one({"employee_id": employee_id})

    if staff and staff["password"] == password and staff["is_active"]:

        session["staff_id"] = str(staff["_id"])

        return jsonify({"status": "success"})

    return jsonify({"error": "Invalid credentials"}), 401


# -------------------------
# ADMIN LOGIN
# -------------------------

@app.route("/api/adminlogin", methods=["POST"])
def admin_login():

    data = request.json

    admin = admin_collection.find_one({"email": data["email"]})

    if admin and admin["password"] == data["password"]:

        session["admin_id"] = str(admin["_id"])

        return jsonify({"status": "success"})

    return jsonify({"error": "Invalid credentials"}), 401


# -------------------------
# UPLOAD FAX
# -------------------------

@app.route("/upload", methods=["POST"])
def upload():

    if "staff_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    if "fax" not in request.files:
        return jsonify({"error": "No file uploaded"})

    file = request.files["fax"]

    if not file.filename.endswith(".pdf"):
        return jsonify({"error": "Only PDF allowed"})

    unique_id = str(uuid.uuid4())

    pdf_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}.pdf")

    file.save(pdf_path)

    pages = convert_from_path(
        pdf_path,
        dpi=300,
        first_page=1,
        last_page=1,
        poppler_path=POPPLER_PATH
    )

    image_path = os.path.join(
        PROCESSED_FOLDER,
        f"{unique_id}.jpg"
    )

    pages[0].save(image_path, "JPEG")

    image = cv2.imread(image_path)

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    _, thresh = cv2.threshold(gray,150,255,cv2.THRESH_BINARY)

    cv2.imwrite(image_path, thresh)

    result = uploads_collection.insert_one({

        "staff_id": session["staff_id"],
        "pdf_path": pdf_path,
        "processed_image": image_path,
        "uploaded_at": datetime.utcnow(),
        "matched_patient_id": None

    })

    session["last_upload_id"] = str(result.inserted_id)
    session["last_processed_image"] = image_path

    return jsonify({
        "success": True,
        "image_filename": os.path.basename(image_path)
    })


# -------------------------
# OCR + AI PROCESS
# -------------------------

@app.route("/extract_text", methods=["POST"])
def extract_text():

    upload_id = session.get("last_upload_id")

    if not upload_id:
        return jsonify({"status": "error", "message": "No upload session found"})

    upload = uploads_collection.find_one({"_id": ObjectId(upload_id)})

    if not upload:
        return jsonify({"status": "error", "message": "Upload not found"})

    image_path = upload["processed_image"]

    try:

        # Run full AI pipeline
        result = process_fax(image_path)

        # Update upload record
        uploads_collection.update_one(
            {"_id": ObjectId(upload_id)},
            {
                "$set": {

                    "ocr_text": result["ocr_text"],

                    "patient_data": result["patient_data"],

                    "matched_patient_id": result["patient_id"],

                    "match_confidence": result["match_confidence"],

                    "document_type": result["document_type"],
                    
                    "medical_summary": result.get("medical_summary")
                }
            }
        )

        return jsonify({

            "status": "success",

            "extracted_text": result["ocr_text"],

            "patient_id": result["patient_id"],

            "patient_data": result.get("patient_data", {}),

            "match_confidence": int(result.get("match_confidence", 0) or 0),

            "document_type": str(result.get("document_type", "Unknown")),

            "duplicates": result.get("duplicates", []),
            
            "ocr_confidence": int(result.get("ocr_confidence", 0) or 0),
            
            "extraction_confidence": int(result.get("extraction_confidence", 0) or 0),
            
            "duplicate_risk": int(result.get("duplicate_risk", 0) or 0),
            
            "medical_summary": result.get("medical_summary", {})

        })

    except Exception as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        })

# -------------------------
# LOGOUT
# -------------------------

@app.route("/logout", methods=["POST"])
def logout():

    session.clear()

    return jsonify({"status":"success"})


if __name__ == "__main__":
    app.run(debug=True)
