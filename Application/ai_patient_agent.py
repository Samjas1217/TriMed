from google.adk.agents import Agent


class PatientInfoAgent(Agent):

    instruction: str = """
You are a medical document extraction assistant.

Extract patient information from the text.

Return JSON with fields:
first_name
last_name
date_of_birth
age
gender
phone
email
"""

    def run(self, text: str):

        result = self.llm(text)

        return result