# AutoScoring — Problem Type, Model, Evaluation & Hyperparameters

**Project:** Automatic Subjective Questions Scoring System using NLP and Deep Learning  
**Institution:** Karakoram International University, Gilgit-Baltistan  
**Team:** Sheraz Karim (2262), Liliyom (2249) · Supervisor: Imran  

Use this document in FYP-II theory chapters (Methodology, Evaluation, Limitations).

---

## 1. What is our problem type?

| Question | Answer for AutoScoring |
|----------|------------------------|
| Task | Score a student’s free-text answer against a teacher’s model answer |
| Output | A **continuous / ordinal score** (e.g. 0–10), not a class label like “spam/not spam” |
| Supervision | Compare system score with **human teacher score** (ground truth) |
| Formal ML category | **Regression / ordinal regression** (Automated Essay Scoring style), optionally treated as ordinal ratings |

This is **not** a standard multi-class classification problem.

### Why that matters for metrics

- **Precision / Recall / F1 / Accuracy** are designed for **labels** (TP, FP, FN, TN).
- Our system outputs a **number**. If we force “Accuracy = exact same score as teacher”, we punish near-misses (e.g. 7.5 vs 8.0) the same as disasters (0 vs 10).
- Therefore AES / short-answer grading research prefers: **Pearson**, **Spearman**, **QWK**, **MAE**, **RMSE**, agreement within ±1 / ±2.

We may still use Precision/Recall **only if** we redefine the task as classification (e.g. Pass/Fail bands: `score ≥ 5`). That is a **different framing**, not the core continuous scoring task.

---

## 2. Model: what we used, under what conditions

### 2.1 Architecture (what “BERT” means in our system)

We did **not** train a BERT classifier from scratch.

We use:

**`sentence-transformers/all-MiniLM-L6-v2`**

- Based on **MiniLM** (distilled Transformer, BERT-family embeddings)
- Outputs a **384-dimensional sentence embedding**
- Used in **inference only** (pretrained; not fine-tuned on KIU exam data yet)

**Pipeline:**

```
Student answer ─┐
                ├─► MiniLM encoder ─► embeddings ─► cosine similarity ─► semantic score (0–1)
Model answer  ─┘

+ Keyword overlap (token Jaccard-like coverage)
+ Coherence heuristic (length, sentences, repetition)

Final score = (0.60×semantic + 0.25×keywords + 0.15×coherence) × max_score
```

Optional path: **EasyOCR** extracts text from PDF/photo → same scorer.

### 2.2 Hardware / environment (record honestly in report)

| Item | Typical FYP setup |
|------|-------------------|
| Device | MacBook / Docker CPU container (no GPU required for MiniLM) |
| Backend | FastAPI + Uvicorn |
| DB | PostgreSQL 16 |
| Deploy | Docker Compose; frontend React/Vite |
| Model load | First request downloads HuggingFace weights (~90MB for MiniLM); kept in container cache |

**Conditions of use:**

- Short / medium English subjective answers
- One model answer per question
- Pretrained semantic similarity — **domain not fine-tuned** on KIU CS exams
- OCR path depends on scan quality (handwriting harder than typed text)

### 2.3 Hyperparameters currently in the system (tune these)

These are the knobs your professor means by “focus on hyperparameter tuning”:

| Hyperparameter | Current default | Role |
|----------------|-----------------|------|
| Embedding model | `all-MiniLM-L6-v2` | Quality vs speed of semantic score |
| Semantic weight \(w_s\) | **0.60** | How much meaning similarity counts |
| Keyword weight \(w_k\) | **0.25** | How much lexical overlap counts |
| Coherence weight \(w_c\) | **0.15** | How much writing structure counts |
| Concept match threshold | 0.72 | “Fully matched” concept |
| Concept partial threshold | 0.45 | “Partially matched” concept |
| Max score scaling | question `max_score` | Maps [0,1] → marks |

Constraint: \(w_s + w_k + w_c = 1\).

**Tuning plan (required for report):**

1. Fix dataset (same CSV of human scores).
2. Sweep weights, e.g. semantic ∈ {0.5, 0.6, 0.7, 0.8}, redistribute rest to keywords/coherence.
3. Optionally try another embedding model (`all-mpnet-base-v2` stronger but slower).
4. Pick the setting that **maximizes QWK and Pearson**, while keeping MAE/RMSE low.
5. Report a small table: hyperparameters → metrics (do not change dataset mid-table).

---

## 3. Dataset (focus point for professor)

### 3.1 What we need

Each row must have:

- `model_answer` — teacher key  
- `student_answer` — student text (typed or OCR)  
- `human_score` — teacher mark  
- `max_score` — e.g. 10  
- optional `title`

Format: `backend/data/evaluation/sample_eval.csv`

### 3.2 Current limitation (write this as a real problem)

| Issue | Why it hurts accuracy |
|-------|------------------------|
| Sample CSV is **small** (~12 synthetic rows) | Correlations look good by chance; not academically trustworthy |
| Limited subjects / topics | Model not validated on real KIU scripts |
| Single human rater | No inter-rater reliability (teacher–teacher agreement) |
| No train/val/test split for fine-tuning | We never specialized MiniLM to our domain |
| OCR noise | System grades wrong text → looks like model failure |

**What to collect (recommended for FYP):**

- ≥ 50–100 real answers, preferably ≥ 200 if possible  
- Multiple questions, difficulty levels, good/average/poor answers  
- Marks from one (or ideally two) teachers  
- Separate **held-out** set used only for final metrics  

---

## 4. Performance measures — which apply, advantages, drawbacks

### 4.1 Why “simple average” / “accuracy %” is weak here

**If we only report mean system score ≈ mean human score:**

- Means can match while individual scores are wrong (systematic cancelation of errors).
- Does not measure agreement on *ordering* or *severity*.

**If we report Accuracy = exact match rate:**

- On a 0–10 scale with decimals, exact match is harsh.
- AES literature prefers tolerance and correlation / kappa.

### 4.2 Metrics we USE (and why)

Already implemented in `backend/app/services/evaluation.py`:

| Metric | What it measures | Advantage | Disadvantage |
|--------|------------------|-----------|--------------|
| **Pearson r** | Linear correlation human vs system | Standard; easy to explain | Sensitive to outliers; assumes linear relation |
| **Spearman ρ** | Rank-order agreement | Robust to score scaling | Ignores absolute error magnitude |
| **QWK (Quadratic Weighted Kappa)** | Agreement with heavier penalty for large gaps | **Gold standard in AES** | Needs score discretization (we round); harder to explain |
| **MAE** | Average absolute points off | Interpretable in marks | Treats all errors equally (2-pt vs 1-pt differently than RMSE) |
| **RMSE** | Error with large mistakes heavily punished | Good when big misses matter | Less intuitive; outlier-sensitive |
| **Within ±1 / ±2** | Practical teacher tolerance | Easy for viva | Thresholds are arbitrary |
| **Exact match rate** | Perfect equality | Strict upper bound | Too harsh as sole metric |

**Sample baseline** (small demo CSV; earlier run ≈):  
Pearson ~0.88 · QWK ~0.76 · MAE ~1.4 — **illustrative only**, not final academic claim until larger real data.

### 4.3 Metrics people confuse with ours (clarify in viva)

| Metric | Typical domain | Applicable to us? |
|--------|----------------|-------------------|
| Precision / Recall / F1 | Classification | Only if we band scores (Pass/Fail, A/B/C) |
| Accuracy | Classification | Misleading for continuous marks |
| R² (coefficient of determination) | Regression | Optional add-on; related to Pearson for simple cases |
| ROI / OEE etc. | Business / manufacturing | **Not applicable** to NLP scoring |
| Confusion matrix | Classification | Optional if we bin scores into grade bands |

### 4.4 R² vs Pearson (short theory)

- Pearson \(r\) = linear association between human and system.  
- \(R^2\) = fraction of variance in human scores explained by system (for linear fit).  
- High Pearson usually goes with high \(R^2\), but **report both error (MAE/RMSE) and agreement (QWK)** — correlation alone can ignore bias (always +1 mark too high but still correlate).

### 4.5 How we select metrics (decision rule for the report)

For **subjective score prediction**:

1. Primary: **QWK** + **Pearson/Spearman**  
2. Secondary: **MAE**, **RMSE**, within ±1  
3. Diagnostic: mean human vs mean system (bias check)  
4. Avoid relying on Accuracy / F1 unless score bands are defined  

---

## 5. Problems identified so far (write honestly)

1. **Accuracy feels bad on real answers**  
   - Pretrained MiniLM is general English, not fine-tuned on exam answers.  
   - Fixed weights (0.60/0.25/0.15) not tuned on your data.  
   - Keyword metric rewards synonyms poorly (“AI” vs “artificial intelligence”) unless embedding helps.

2. **Dataset too small / too synthetic**  
   - Overfitting to demo examples; metrics inflate; professor will question credibility.

3. **No hyperparameter search done yet**  
   - Professor explicitly asked to focus here — run weight sweeps and table them.

4. **OCR error ≠ scoring error**  
   - Handwriting misread changes student text → wrong score. Must report OCR confidence / teacher edit.

5. **Coherence is a heuristic**, not deep discourse modeling  
   - Short correct answers can be under-scored; long waffle can gain coherence points.

6. **Single reference answer**  
   - Valid alternative phrasings that miss keywords but are semantically correct may still lose keyword points.

7. **Engineering issues faced during build** (also mention)  
   - Docker / PyTorch–EasyOCR dependency conflicts  
   - Frontend-only cloud deploy (Vercel) without API → “Failed to fetch”  
   - Heavy model image hard to host on free PaaS  

---

## 6. What “good theory understanding” looks like in viva (checklist)

1. **Task:** ordinal/regression scoring of subjective answers, not classification.  
2. **Model:** pretrained MiniLM embeddings + cosine similarity + hybrid features.  
3. **Why not only F1:** outputs are marks, not classes.  
4. **Why QWK:** standard AES agreement; penalizes large disagreements more.  
5. **Why not only average:** averages hide pairwise disagreement.  
6. **Hyperparameters:** weights + thresholds + model choice → tune on validation set.  
7. **Dataset:** size, diversity, human marks quality → biggest lever for trust.  
8. **Limitations:** no fine-tuning yet; OCR noise; small eval set.  
9. **Next improvements:** larger labeled set, weight grid search, optional fine-tuning / cross-encoder, inter-rater kappa between two teachers.

---

## 7. Suggested experiment tables for the report

### Table A — Hyperparameter tuning (fill after you run sweeps)

| \(w_s\) | \(w_k\) | \(w_c\) | Pearson | QWK | MAE | RMSE | Notes |
|--------|--------|--------|---------|-----|-----|------|-------|
| 0.60 | 0.25 | 0.15 | | | | | baseline |
| 0.70 | 0.20 | 0.10 | | | | | |
| 0.50 | 0.35 | 0.15 | | | | | |
| 0.80 | 0.15 | 0.05 | | | | | |

### Table B — Dataset statistics

| Item | Value |
|------|-------|
| # answers | |
| # questions | |
| Score range | |
| Mean human score | |
| Subjects / courses | |
| # human markers | |

### Table C — Hardware for evaluation run

| Item | Value |
|------|-------|
| Machine | |
| CPU/RAM | |
| GPU (if any) | |
| Model | all-MiniLM-L6-v2 |
| Runtime for N samples | |

---

## 8. How to run evaluation (after dataset is ready)

```bash
cd backend
python evaluate.py data/evaluation/YOUR_FILE.csv --output reports/eval_report.json
```

Replace the sample CSV with **real teacher-scored answers** before claiming final accuracy in the thesis.

---

## Bottom line for professor

| Theme | Our position |
|-------|----------------|
| Problem | Subjective answer **scoring** (regression / AES) |
| Model | Pretrained **MiniLM** embeddings + hybrid scoring |
| Primary metrics | **QWK, Pearson, Spearman, MAE, RMSE** |
| Not primary | Accuracy / F1 / ROI (wrong problem type unless reformulated) |
| Accuracy weak because | Small data + untuned hyperparameters + no domain fine-tuning + OCR noise |
| Focus next | **Larger dataset + systematic hyperparameter tuning + honest metric tables** |
