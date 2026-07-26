# Knowledge Base Sources

Each subfolder maps to a selectable role. The backend ingests `.txt` and text-based `.pdf` files from these folders and rebuilds `data/vector_store.json` automatically when no vector store exists.

Recommended assignment book placement:

- `AI_ML_Engineer/`
  - `Machine Learning - Tom Mitchell.pdf`
  - `The Hundred-Page Machine Learning Book - Andriy Burkov.pdf`
  - `Machine Learning for Absolute Beginners.pdf`
- `Data_Science_Applied_ML/`
  - `Introduction to Machine Learning with Python.pdf`
  - `Master Machine Learning Algorithms - Jason Brownlee.pdf`
- Optional advanced sources can be added to `AI_ML_Engineer/` or a new role folder.

The included `.txt` files are lightweight seed corpora so the project runs immediately. For the strongest assignment submission, add the provided book PDFs here and delete `data/vector_store.json` before restarting the backend so the vector store is regenerated.
