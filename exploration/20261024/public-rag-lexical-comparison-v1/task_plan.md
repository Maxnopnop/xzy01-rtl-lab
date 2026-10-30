# Public no-model retrieval comparison

User explicitly authorizes offline retrieval only: no generative or embedding models. Adopted20 existing candidate prompts; no new candidate fetching. Preserve old evidence/grades.

1. Read primary public paper/repository evidence and screen dependencies; do not download code-example corpora or fit to tasks.
2. Vendor one fixed public rank_bm25 source plus license/README; inspect before import. NumPy already installed, no global package install.
3. Freeze uniform48-chunk corpus,20 original queries, common tokenizer/selection wrapper, upstream default parameters and metrics before experiment.
4. Execute once per method/query:3 public lexical retrievers + historical localTF-IDF comparator. No rerun on task results, no tuning.
5. Report rank/top3 overlap/context bytes/timing/nohits, preserve unknown relevance and no RTL score claim; audit inputs and old packet; seal.

Public framework results are NOT reproduced: DeepV/VeriRAG/RTLRepoCoder require embedding/model execution. Offline lexical component comparison is separately labeled. No cross-thread messages.
