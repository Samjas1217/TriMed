from database.mongo import uploads_collection
from bson import ObjectId

def get_patient_documents(patient_id):

    """
    Retrieve all fax documents linked to a patient
    """

    try:

        documents = list(

            uploads_collection.find(
                {"matched_patient_id": patient_id}
            ).sort("uploaded_at", -1)

        )

        return documents

    except Exception as e:

        print("Timeline retrieval failed:", e)

        return []
