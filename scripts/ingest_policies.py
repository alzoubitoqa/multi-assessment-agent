from app.policy.kb import index_policy_documents


if __name__ == "__main__":
    result = index_policy_documents()
    print(f"Indexed {result['records_indexed']} records into {result['collection']}")
    if result["missing_pdfs"]:
        print("Optional official PDFs not found:", *result["missing_pdfs"], sep="\n- ")
