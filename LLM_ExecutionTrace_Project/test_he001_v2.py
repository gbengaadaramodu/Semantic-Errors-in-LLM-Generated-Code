from objective2.pipeline import Objective2Pipeline
from objective2.config import Objective2Config
import json

config = Objective2Config()
pipe = Objective2Pipeline(config)
records = pipe.corpus_loader.load_records()
r = [x for x in records if x.trace_id == 'HE001'][0]
r = pipe.trace_loader.enrich_record(r)

events = pipe._trace_execution(r)
failure_line = pipe._extract_failure_line(r)
pdg = pipe.pdg_builder.build_pdg(r.generated_code, events, failure_line)
candidates = pipe.candidate_generator.generate_candidates(pdg, top_k=5)
cf_results = pipe.diagnoser.diagnose_candidates(r, candidates)

rc = pipe.ranker.rank(candidates, cf_results)
if rc:
    loc = pipe.locator.locate_fault(r, rc, cf_results)
    root = pipe.root_cause_generator.diagnose(r, loc, cf_results)
    print("Root Cause Status:", root.root_cause_status)
    print("Candidate Expl:", root.candidate_explanation)
    print("Evidence:", root.evidence_summary)
