==============================================================================
  AutoScoring System — PERFORMANCE REPORT FOR PROFESSOR
  Generated: 2026-09-23 19:02:51
==============================================================================

1. WHAT THE SYSTEM DOES
   AutoScoring combines a BERT sentence-embedding model
   (sentence-transformers/all-MiniLM-L6-v2) with keyword and coherence
   heuristics to grade short-answer responses. Scoring weights:
       Semantic similarity  = 60%    (BERT cosine similarity)
       Keyword coverage     = 25%    (stopword-free token overlap)
       Coherence heuristic  = 15%    (length, sentences, repetitions)

2. EVALUATION PROTOCOL
   For every question, we run the model_answer vs student_answer through
   the scorer, then compare the output score to a HUMAN-GIVEN reference.
   Agreement is measured with 8 standard metrics used in the ASAP AES
   short-answer grading competition.

3. DATASETS EVALUATED
   • GSM8K Math Word Problems (200 samples, 0-100 scale)  [math]
   • ASAP Prompt 3 Handwritten (185 samples, 0-10 scale)  [science (handwritten OCR)]

4. METRIC INTERPRETATION (show this column to the professor)
------------------------------------------------------------------------------
  Pearson r                       LINEAR AGREEMENT between system and human scores. ≥0.9 = excellent, ≥0.8 = very good, ≥0.7 = good, ≥0.5 = acceptable. p-value < 0.05 means the correlation is statistically significant.
  Spearman ρ                      RANK-ORDER AGREEMENT (robust to outliers and non-linear score scales). Similar thresholds to Pearson. Measures whether the system correctly 'ranks' answers from worst to best the way a human would.
  R²                              VARIANCE EXPLAINED: what fraction of human score variance is captured by the system. ≥0.8 = very strong, ≥0.6 = strong. Complement (1-R²) is unexplained variance.
  Quadratic Weighted Kappa        QWK — STANDARD EDUCATIONAL AGREEMENT METRIC for automated scoring (ASAP AES benchmark, Kaggle competitions, etc.). Penalizes disagreements by the SQUARE of the grade distance, so being off by 3 points is 9× worse than being off by 1. ≥0.8 = excellent, ≥0.6 = substantial. This is the MOST IMPORTANT metric for a professor comparing to ASAP competition baselines.
  MAE                             MAE — AVERAGE POINT ERROR between human and system score. Lower is better. Interpret using the scale: for 0-10 scale, MAE<1 means within a grade boundary on average; for 0-100, MAE<15 is good.
  RMSE                            RMSE — penalizes LARGE errors quadratically. Always ≥MAE. If RMSE >> MAE it means a few answers are badly misgraded.
  Exact Match Rate                Fraction of samples where system score == human score exactly (after rounding). 15% is typical for continuous scoring.
  Within ±1 Point                 Fraction within ±1 point of the human score. ≥70% = reliable classroom tool. For 0-100 scale interpret as ±1 pt out of 100.
  Within ±2 Points                Fraction within ±2 points. ≥95% = very robust grading system.

5. CONSOLIDATED SCORES
------------------------------------------------------------------------------
  Dataset                                        Pearson  Spearman      R²     QWK     MAE   ±1pt%
  GSM8K Math Word Problems (200 samples, 0-10     0.9514    0.9203  0.8512  0.9154  9.6181  22.50%
  ASAP Prompt 3 Handwritten (185 samples, 0-1     0.8373    0.8263  0.5730  0.6110  0.7156  75.14%

6. VERDICT / PROFESSOR SUMMARY
------------------------------------------------------------------------------

  GSM8K Math Word Problems (200 samples, 0-100 scale)
    ✅ Pearson r ≥ 0.90 — EXCELLENT linear agreement with human graders.
    ✅ QWK ≥ 0.80 — EXCELLENT inter-rater agreement (ASAP competition standard).
    ⚠️  22.5% within ±1 point, needs improvement.

  ASAP Prompt 3 Handwritten (185 samples, 0-10 scale)
    ✅ Pearson r ≥ 0.80 — VERY GOOD linear agreement.
    🟢 QWK ≥ 0.60 — SUBSTANTIAL inter-rater agreement.
    ✅ 75.1% of scores within ±1 point of human grade — classroom-ready.

7. HOW TO REPRODUCE (run inside Docker backend container)
   $ docker exec fyp-backend-1 python evaluate.py \
        data/evaluation/gsm8k_eval.csv \
        --output /app/data/evaluation/gsm8k_report.json
   $ docker exec fyp-backend-1 python evaluate.py \
        data/evaluation/asap_prompt3_handwritten.csv \
        --output /app/data/evaluation/asap_hw_report.json
   Or re-run everything locally:
   $ python backend/scripts/generate_performance_summary.py

==============================================================================
  End of report
==============================================================================