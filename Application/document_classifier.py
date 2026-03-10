from google.adk.agents import Agent


class DocumentClassifier(Agent):

    instruction: str = """
You are a medical document classifier.

Based on the given text, classify the document into one of these categories:

Lab Report
Prescription
Referral
Insurance
Discharge Summary
Other

Return ONLY the category name.
"""

    def run(self, text: str):

        result = self.llm(text)

        return result.strip()