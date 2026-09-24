---
title: AutoScoring API
emoji: 🎓
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# AutoScoring API

FastAPI backend for the AutoScoring FYP. Extracts questions from uploaded papers,
compares teacher-entered model answers against student answers using
`sentence-transformers/all-MiniLM-L6-v2`, and stores data in Neon Postgres with
uploads in Neon object storage.
