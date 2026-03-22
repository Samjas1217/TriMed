from agents.patient_extraction_agent import get_api_key
from agents.medical_summary_agent import generate_medical_summary
from dotenv import load_dotenv
import os

load_dotenv()
print("API KEY:", get_api_key()[:10] if get_api_key() else "None")

res = generate_medical_summary("Patient is complaining of severe headaches for the past 3 days. Recommend MRI scan.")
print("RESULT:", res)
