from src.orchestrator import run_lexverify_pipeline


QUESTIONS = [
    "Can a person get bail in a criminal case?",
    "What are the conditions for pre-arrest bail in Pakistan?",
    "What is the purpose of pre-arrest bail?",
    "What factors are considered when deciding bail?",
    "Can bail be granted in a case involving serious criminal charges?",
    "What is the difference between pre-arrest and post-arrest bail?",
    "What role does section 497 of the Criminal Procedure Code play in bail?",
    "Can a court consider the circumstances of the accused when deciding bail?",
    "What principles have Pakistani courts applied in bail cases?",
    "Can bail be refused even when an accused seeks protection from arrest?",
]


def evaluate_question(question, number):
    print("\n" + "=" * 80)
    print(f"QUESTION {number}")
    print("=" * 80)
    print(question)

    state = run_lexverify_pipeline(question)

    print("\nSTATUS:")
    print(state.get("status"))

    print("\nERRORS:")
    print(state.get("errors"))

    print("\nRESEARCH PLAN:")
    print(state.get("research_plan"))

    print("\nRETRIEVED CHUNKS:")
    for chunk in state.get("retrieved_chunks", []):
        print(
            f"- {chunk.get('source_file')} | "
            f"page={chunk.get('page')} | "
            f"score={chunk.get('score')}"
        )

    print("\nCANDIDATE CITATIONS:")
    print(state.get("candidate_citations"))

    print("\nVERIFIED CITATIONS:")
    for item in state.get("verified_citations", []):
        print(
            f"- {item.get('citation')} | "
            f"match={item.get('match_type')} | "
            f"score={item.get('match_score')}"
        )

    print("\nMETRICS:")
    print(state.get("metrics_summary"))

    print("\nFINAL ANSWER:")
    print(state.get("final_answer"))

    return state


def main():
    results = []

    for i, question in enumerate(QUESTIONS, start=1):
        state = evaluate_question(question, i)
        results.append(state)

    print("\n\n" + "#" * 80)
    print("FINAL EVALUATION SUMMARY")
    print("#" * 80)

    successful = 0
    with_verified_citations = 0

    for i, state in enumerate(results, start=1):
        status = state.get("status")
        verified = state.get("verified_citations", [])
        errors = state.get("errors", [])

        if status == "synthesis_completed":
            successful += 1

        if verified:
            with_verified_citations += 1

        print(
            f"{i:02d}. "
            f"status={status} | "
            f"verified={len(verified)} | "
            f"errors={len(errors)}"
        )

    print("\nPipeline success:", f"{successful}/{len(results)}")
    print(
        "Questions with verified citations:",
        f"{with_verified_citations}/{len(results)}"
    )


if __name__ == "__main__":
    main()