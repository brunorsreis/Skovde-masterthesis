
Forensic Analysis of Computer File Systems Using Vector Search and Large Language Models (LLMs) For Enhanced Cybersecurity and Data Recovery
Creators

    Reis da Silva, Bruno (Other)
    ORCID icon: https://zenodo.org/records/15914817

Description

    This repository provides the source code for an academic forensic tool developed as part of a Master’s thesis in Informatics (Privacy, Information, and Cybersecurity) at the University of Skövde. The tool is designed to enhance digital forensic investigations on macOS systems by leveraging semantic vector search, regex-based pattern detection, and contextual risk classification using large language models (LLMs).

The system integrates the following core components:

    SentenceTransformer embeddings (all-MiniLM-L6-v2) to convert file content into high-dimensional semantic vectors for similarity-based retrieval.

    Oracle 23ai for Approximate Nearest Neighbor (ANN) search using HNSW indexing and cosine similarity.

    Regex scanning for deterministic detection of structured sensitive entities (e.g., passwords, emails, phone numbers, credit card numbers).

    LLM-based contextual analysis using Cohere APIs and Oracle Cloud Generative AI to classify risks and recommend mitigations.

    Gradio-powered interface for uploading files, executing scans, and visualizing risks.

The tool detects renamed, obfuscated, or semantically disguised sensitive content across .txt, .pdf, .csv, and .json formats, providing a hybrid detection pipeline that combines deterministic pattern recognition with semantic and contextual reasoning.
📎 Appendix Integration

    Appendix A contains the full source code and workflow for the local version of the forensic tool, including Cohere’s command-r-plus LLM integration for risk classification.

    Appendix B includes the cloud-enhanced version of the tool, demonstrating integration with Oracle Cloud Infrastructure (OCI) and the Cohere command-a-03-2025 model for scalable, multilingual forensic analysis.

Together, these components reflect a hybrid architecture that supports reproducible, explainable, and platform-independent digital forensics.
