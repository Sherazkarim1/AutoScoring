#!/usr/bin/env python3
"""Cross-check every numeric/file claim in details.md against actual repo state."""
import json
import csv
import re
from pathlib import Path

REPORT = []
PASS = 0
FAIL = 0


def check(name, cond, detail=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        REPORT.append(f"  ✅ {name}")
    else:
        FAIL += 1
        REPORT.append(f"  ❌ {name}  -> {detail}")


BASE = Path('/Users/macbookpro/Desktop/FYP')

# 1. Files exist
for rel in [
    'backend/data/evaluation/sample_eval.csv',
    'backend/data/evaluation/gsm8k_eval.csv',
    'backend/data/evaluation/asap_prompt3_handwritten.csv',
    'backend/data/evaluation/asap_prompt3_typed.csv',
    'backend/data/evaluation/asap_prompt_3.csv',
    'backend/data/evaluation/gsm8k_report.json',
    'backend/data/evaluation/asap_hw_report.json',
    'backend/data/evaluation/PERFORMANCE_SUMMARY.csv',
    'backend/data/evaluation/PERFORMANCE_README.txt',
    'backend/scripts/fix_gsm8k_eval.py',
    'backend/scripts/convert_asap_datasets.py',
    'backend/scripts/generate_performance_summary.py',
    'AutoScoring_Evaluation_Demo_Colab.ipynb',
]:
    p = BASE / rel
    check(f"File exists: {rel}", p.exists() and p.stat().st_size > 0)

# 2. Row counts
with open(BASE/'backend/data/evaluation/sample_eval.csv') as f:
    rows = list(csv.DictReader(f))
check("sample_eval.csv = 12 data rows (not 13)", len(rows)==12, f"got {len(rows)}")

with open(BASE/'backend/data/evaluation/gsm8k_eval.csv') as f:
    rows_g = list(csv.DictReader(f))
check("gsm8k_eval.csv = 200 data rows", len(rows_g)==200, f"got {len(rows_g)}")
check("gsm8k_eval.csv has subject column", 'subject' in rows_g[0], f"cols={list(rows_g[0].keys())}")

with open(BASE/'backend/data/evaluation/asap_prompt3_handwritten.csv') as f:
    rows_a = list(csv.DictReader(f))
check("asap_prompt3_handwritten.csv = 185 data rows", len(rows_a)==185, f"got {len(rows_a)}")

with open(BASE/'backend/data/evaluation/asap_prompt3_typed.csv') as f:
    rows_t = list(csv.DictReader(f))
check("asap_prompt3_typed.csv = 154 data rows", len(rows_t)==154, f"got {len(rows_t)}")

# 3. Metric values match saved reports
with open(BASE/'backend/data/evaluation/gsm8k_report.json') as f:
    gr = json.load(f)
with open(BASE/'backend/data/evaluation/asap_hw_report.json') as f:
    ar = json.load(f)
with open(BASE/'backend/data/evaluation/PERFORMANCE_SUMMARY.csv') as f:
    ps = list(csv.DictReader(f))

check("GSM8K report Pearson r = 0.9514", abs(gr['metrics']['pearson_correlation']-0.9514)<1e-4, f"got {gr['metrics']['pearson_correlation']}")
check("GSM8K report QWK = 0.9154", abs(gr['metrics']['quadratic_weighted_kappa']-0.9154)<1e-4, f"got {gr['metrics']['quadratic_weighted_kappa']}")
check("ASAP HW report Pearson r = 0.8373", abs(ar['metrics']['pearson_correlation']-0.8373)<1e-4, f"got {ar['metrics']['pearson_correlation']}")
check("ASAP HW within ±1 point = 75.14%", abs(ar['metrics']['within_1_point_rate']-0.7514)<1e-4, f"got {ar['metrics']['within_1_point_rate']}")
check("ASAP HW MAE ≈ 0.72/10", 0.70 <= ar['metrics']['mean_absolute_error'] <= 0.74, f"got {ar['metrics']['mean_absolute_error']}")

# 4. evaluate.py CLI args implemented
eval_src = (BASE/'backend/evaluate.py').read_text()
for token in ['--subject', '--rescale', '--output', 'subject_filter', 'rescale_factor']:
    check(f"evaluate.py contains '{token}'", token in eval_src)

# 5. requirements.txt deps
req = (BASE/'backend/requirements.txt').read_text()
for dep in ['scipy', 'sentence-transformers', 'torch', 'torchvision', 'alembic', 'pydantic-settings']:
    check(f"requirements.txt contains {dep}", dep in req)

# 6. config.py weights/thresholds
cfg = (BASE/'backend/app/config.py').read_text()
for pattern in ['weight_semantic: float = 0.60',
                'weight_keywords: float = 0.25',
                'weight_coherence: float = 0.15',
                'concept_match_threshold: float = 0.72',
                'concept_partial_threshold: float = 0.45']:
    check(f"config.py: {pattern}", pattern in cfg)

# 7. Colab notebook valid JSON
with open(BASE/'AutoScoring_Evaluation_Demo_Colab.ipynb') as f:
    nb = json.load(f)
cells = nb.get('cells', [])
nb_md = sum(1 for c in cells if c['cell_type']=='markdown')
nb_code = sum(1 for c in cells if c['cell_type']=='code')
check(f"Colab notebook valid JSON ({len(cells)} cells: md={nb_md}, code={nb_code})",
      len(cells) >= 15 and nb_md >= 5 and nb_code >= 10,
      f"got cells={len(cells)} md={nb_md} code={nb_code}")

# 8. Dockerfile does NOT wire wheels (matches §12.1 unknown #1)
df = (BASE/'backend/Dockerfile').read_text()
wired = bool(re.search(r"COPY\s+.*wheels|--find-links\s+.*wheels|install.*wheels", df, re.I))
check("backend/Dockerfile does NOT wire wheels/ (matches §12.1 Unknown #1)", not wired,
      "Update details.md §12.1 if you actually wired wheels into the Dockerfile")

# 9. Wheels directory sizes
whl_torch = (BASE/'backend/wheels/torch.whl').stat().st_size if (BASE/'backend/wheels/torch.whl').exists() else 0
whl_tv = (BASE/'backend/wheels/torchvision.whl').stat().st_size if (BASE/'backend/wheels/torchvision.whl').exists() else 0
check("wheels/torch.whl ≥ 170 MB (real PyTorch wheel)", whl_torch >= 170*1024*1024, f"size={whl_torch/1024/1024:.1f}MB")
check("wheels/torchvision.whl ≥ 1 MB", whl_tv >= 1*1024*1024, f"size={whl_tv/1024/1024:.1f}MB")

# 10. PERFORMANCE_SUMMARY.csv structure
check("PERFORMANCE_SUMMARY.csv = 2 dataset rows", len(ps)==2, f"got {len(ps)}")
check("PERFORMANCE_SUMMARY.csv ≥ 14 columns", len(ps[0].keys())>=14, f"cols={len(ps[0].keys())}")

# Print results
print()
print("="*70)
print(f"  CONSISTENCY AUDIT: {PASS} PASSED, {FAIL} FAILED, {PASS+FAIL} TOTAL CHECKS")
print("="*70)
for line in REPORT:
    print(line)
print("="*70)
if FAIL > 0:
    print(f"\n⛔ FAILURES DETECTED: {FAIL}. Fix details.md or the referenced files.")
    raise SystemExit(1)
else:
    print(f"\n✅ All {PASS} claims cross-checked against actual disk state. details.md is correct.")
