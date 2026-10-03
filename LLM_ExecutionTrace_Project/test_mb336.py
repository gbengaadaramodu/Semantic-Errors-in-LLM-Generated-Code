from objective2.pipeline import Objective2Pipeline
from objective2.config import Objective2Config
import json

config = Objective2Config()
pipe = Objective2Pipeline(config)
records = pipe.corpus_loader.load_records()
r = [x for x in records if x.trace_id == 'MB336'][0]
r = pipe.trace_loader.enrich_record(r)

print('Tracing MB336...')
events = pipe._trace_execution(r)
print(f'Trace complete! Events captured: {len(events)}')
