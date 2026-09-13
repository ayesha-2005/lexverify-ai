def run_lexverify_mock(user_question):
    """
    Temporary mock backend for testing the LexVerify AI UI.
    """

    question = user_question.lower()

    # Scenario 1: Grounded legal question
    if "bail" in question:
        return {
            "answer": (
                "For non-bailable offenses, bail is generally considered "
                "according to the applicable legal standards and circumstances "
                "of the case."
            ),
            "citations": [
                {
                    "citation": "PLD 2021 SC 450",
                    "status": "VERIFIED"
                }
            ],
            "evidence": [
                {
                    "citation": "PLD 2021 SC 450",
                    "snippet": "Relevant court record supporting the bail standard."
                }
            ],
            "audit_trail": []
        }

    # Scenario 2: Fake citation
    elif "pld 2025 sc 999" in question:
        return {
            "answer": (
                "The requested precedent could not be verified and has "
                "therefore been blocked."
            ),
            "citations": [
                {
                    "citation": "PLD 2025 SC 999",
                    "status": "REJECTED"
                }
            ],
            "evidence": [],
            "audit_trail": []
        }

    # Scenario 3: Out of corpus
    else:
        return {
            "answer": (
                "No relevant legal precedent was found in the available corpus."
            ),
            "citations": [],
            "evidence": [],
            "audit_trail": []
        }