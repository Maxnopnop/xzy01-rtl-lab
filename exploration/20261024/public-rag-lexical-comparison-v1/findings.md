# Findings

Primary sources: DeepV arXiv2510.05327 usesMiniLM embedding/FAISS and example code corpus; VeriRAG HArt-Git requiresOpenAI embedding/APIkey and hasColab/RDF/SPARQL/Chroma components; RTLRepoCoder arXiv2504.08862 targets repository next-line completion with fine-tuning and embeddings. These cannot be faithfully executed under no-model restriction. No code-example corpus incorporated. AuthorPDF VeriRAG link returned404 once, retained; no repeat.

Local NumPy present; scipy/sklearn/rank_bm25 absent. Fixed upstream rank_bm25 can run with NumPy only. Vendor source rather than installing dependencies. All method differences will be measured on same existing generic48chunks and adopted20prompts, no ref/TB or outcomes used in retrieval.
