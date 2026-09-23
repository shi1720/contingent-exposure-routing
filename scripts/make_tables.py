"""Generate all manuscript table rows from the recorded results."""
import json
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]

def main():
    s=json.loads((ROOT/'results/summary.json').read_text())
    pct=lambda x:f'{100*x:.2f}'
    rows=[]
    for x in s['synthetic']:
        if x['feedback']==.4:
            m,lo,hi=x['gain']
            rows.append(f"{x['correlation']:.1f} & {x['outage_size']} & {pct(m)} & [{pct(lo)}, {pct(hi)}] & {pct(x['mean_relaxation_gap'])} "+r'\\')
    (ROOT/'paper/synthetic-table.tex').write_text('\n'.join(rows)+'\n')
    labels={'cer':'CER (full second moment)','diagonal':'Diagonal second moment','equal':'Equal-variance exposure balance','robust':'Ridge-envelope diagnostic','common':'Common best (different counts)'}
    rows=[]
    for x in s['api']:
        if x['outage_size']==0:
            m,lo,hi=x['gain']
            rows.append(f"{labels[x['method']]} & {pct(m)} & [{pct(lo)}, {pct(hi)}] "+r'\\')
    (ROOT/'paper/api-table.tex').write_text('\n'.join(rows)+'\n')
    frame=pd.read_csv(ROOT/'results/api-models.csv'); rows=[]
    for _,x in frame[frame.split=='test'].iterrows():
        name=x['model'].replace('gpt-','GPT-').replace('-2025-04-14','').replace('-2024-07-18','')
        rows.append(f"{name} & {int(x['valid'])}/128 & {x['rmse_bps']:.1f} & {x['mae_bps']:.1f} & {int(x['within_one_bp'])}/128 "+r'\\')
    (ROOT/'paper/model-table.tex').write_text('\n'.join(rows)+'\n')
    rows=[]
    for x in map(json.loads,(ROOT/'data/raw/api-sanity.jsonl').read_text().splitlines()):
        rows.append(dict(model=x['model'],diagnostic=x['diagnostic'],expected=x['expected'],value=x['value'],valid=x['valid'],correct=x['valid'] and abs(x['value']-x['expected'])<.02))
    pd.DataFrame(rows).to_csv(ROOT/'results/api-sanity.csv',index=False)

if __name__=='__main__':main()
