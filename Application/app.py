from flask import Flask, request, jsonify, session, render_template, redirect
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
from pdf2image import convert_from_path
from flask import send_from_directory
import pytesseract
from PIL import Image
from bson import ObjectId
import cv2
import numpy as np
import os
import uuid
from patient_extractor import extract_patient_info
from ocr_utils import extract_text_from_image

app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = "super_secret_key"

@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

client = MongoClient("mongodb://localhost:27017/")
db = client["hospitalDB"]
admin_collection = db["admin"]
staff_collection = db["staff"]
uploads_collection = db["uploads"]

# Folder Setup

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "input_fax")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "output_images")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

POPPLER_PATH = r"C:\poppler-25.12.0\Library\bin"

pytesseract.pytesseract.tesseract_cmd = \
r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# STAFF LOGIN 

@app.route("/api/login", methods=["POST"])
def login():
    data = request.json
    employee_id = data.get("employee_id")
    password = data.get("password")

    staff = staff_collection.find_one({"employee_id": employee_id})

    if staff and staff["password"] == password and staff["is_active"]:
        session["staff_id"] = str(staff["_id"])
        session["role"] = staff["role"]
        return jsonify({"status": "success"})
    else:
        return jsonify({"error": "Invalid credentials"}), 401


# ADMIN LOGIN 

@app.route("/api/adminlogin", methods=["POST"])
def admin_login():
    data = request.json
    admin = admin_collection.find_one({"email": data["email"]})

    if admin and admin["password"] == data["password"]:
         session["admin_id"] = str(admin["_id"])
         return jsonify({"status": "success"})
    else:
        return jsonify({"status": "invalid credentials"}), 401


# PAGE ROUTES

@app.route("/")
def index():
    return render_template("Landing.html")

@app.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")

@app.route("/adminlogin", methods=["GET"])
def adminlogin():
    return render_template("Adminlogin.html")

@app.route("/admindash")
def admindash():
    if "admin_id" not in session:
        return redirect("/adminlogin")
    return render_template("admindash.html")

@app.route("/dashboard")
def dashboard():
    if "staff_id" not in session:
        return redirect("/login")
    return render_template("dashboard.html")

@app.route("/text_extraction")
def text_extraction():
    if "staff_id" not in session:
        return redirect("/")

    image_path = session.get("last_processed_image")

    if not image_path:
        return redirect("/dashboard")

    filename = os.path.basename(image_path)

    return render_template(
        "ocr_extraction.html",
        image_filename=filename
    )

@app.route("/output_images/<filename>")
def serve_output(filename):
    return send_from_directory(OUTPUT_FOLDER, filename)

@app.route("/extract_text", methods=["POST"])
def extract_text():

    if "staff_id" not in session:
        return jsonify({"status": "unauthorized"}), 401

    image_path = session.get("last_processed_image")
    upload_id = session.get("last_upload_id")

    if not image_path or not upload_id:
        return jsonify({"status": "error", "message": "No image found"}), 400

    # Run OCR
    img = Image.open(image_path)
    custom_config = r'--oem 3 --psm 6'
    ocr_text = extract_text_from_image(image_path)

    patient_data = extract_patient_info(ocr_text)

    # Update MongoDB document
    uploads_collection.update_one(
        {"_id": ObjectId(upload_id)},
        {"$set": {
            "ocr_text": ocr_text,
            "patient_data": patient_data,
            "ocr_completed_at": datetime.utcnow()
        }}
    )

    return jsonify({
        "status": "success",
        "extracted_text": ocr_text,
        "patient_data": patient_data
    })

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"status": "success"})

@app.route("/force_logout", methods=["POST"])
def force_logout():
    session.clear()
    return "", 204

@app.route("/add_staff", methods=["POST"])
def add_staff():

    if "admin_id" not in session:
        return jsonify({"status": "unauthorized"}), 401

    data = request.json

    existing = staff_collection.find_one({"employee_id": data["employee_id"]})
    if existing:
        return jsonify({"status": "error", "message": "Employee ID already exists"})

    staff_collection.insert_one({
        "name": data["name"],
        "email": data["email"],
        "password": data["password"],  
        "role": data["role"],
        "department": data["department"],
        "phone": data["phone"],
        "employee_id": data["employee_id"],
        "is_active": True,
        "created_at": datetime.utcnow(),
        "last_login": None
    })

    return jsonify({"status": "success"})


# PDF UPLOAD + PREPROCESSING + OCR

@app.route("/upload", methods=["POST"])
def upload_file():

    if "staff_id" not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    if "fax" not in request.files:
        return jsonify({"success": False, "error": "No file uploaded"})

    file = request.files["fax"]

    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"success": False, "error": "Only PDF allowed"})

    try:
        unique_id = str(uuid.uuid4())

        # Save PDF
        pdf_path = os.path.join(UPLOAD_FOLDER, f"{unique_id}.pdf")
        file.save(pdf_path)

        # Extract first page
        pages = convert_from_path(
            pdf_path,
            dpi=300,
            first_page=1,
            last_page=1,
            poppler_path=POPPLER_PATH
        )

        extracted_image_path = os.path.join(
            OUTPUT_FOLDER,
            f"{unique_id}_page1.jpg"
        )

        pages[0].save(extracted_image_path, "JPEG")

        # PREPROCESSING

        image = cv2.imread(extracted_image_path)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        denoised = cv2.medianBlur(gray, 3)

        _, thresh = cv2.threshold(
            denoised, 150, 255, cv2.THRESH_BINARY
        )

        coords = np.column_stack(np.where(thresh > 0))

        if len(coords) > 0:
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle

            (h, w) = thresh.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)

            deskewed = cv2.warpAffine(
                thresh,
                M,
                (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )
        else:
            deskewed = thresh

        processed_image_path = os.path.join(
            OUTPUT_FOLDER,
            f"{unique_id}_processed.jpg"
        )

        cv2.imwrite(processed_image_path, deskewed)

        # Save to MongoDB

        result = uploads_collection.insert_one({
            "staff_id": session["staff_id"],
            "pdf_path": pdf_path,
            "extracted_image": extracted_image_path,
            "processed_image": processed_image_path,
            "ocr_text": None,
            "uploaded_at": datetime.utcnow()
        })
        session["last_upload_id"] = str(result.inserted_id)
        session["last_processed_image"] = processed_image_path


        filename = os.path.basename(processed_image_path)

        return jsonify({
           "success": True,
           "image_filename": filename
        })


    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        })

if __name__ == "__main__":
    app.run(debug=True)
