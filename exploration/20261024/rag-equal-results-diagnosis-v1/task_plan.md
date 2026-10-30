# Diagnose equal aggregate RAG/no-RAG results

User prioritizes causal interpretation of existing outcomes; read-only analysis authorized, not method tuning. Embedding comparison recorded separately, not executed.
1. Separate aggregate equality, per-slot pass status equality and generated RTL byte equality.
2. Check actual requests contain frozen context, transport binding and saved result integrity.
3. Compare saved RTL hashes, failure categories, task saturation and relevance limitations without executing anything.
4. State established facts vs hypotheses; no claims about hidden providerRAG, training-data membership or causal effect from unseeded pairs.
5. Preserve all old evidence; report in this new directory only.

Existing240 report: both arms97/120;5helps+5worse+2service-unpaired. Existing96:47/48each;1help+1worse. Need independent read-only verification and code comparison.

Completed: new read-only audit of336actual requests and168pairs;2320read evidence hashes stable. Same aggregate scores independently reproduced; RTL exact bytes differ83/112old and25/48new. All168RAG contexts sent exactly. Report distinguishes established observations, hypotheses and missing causal evidence. Embedding proposal saved, not executed. Stop without method modification or production calls.
