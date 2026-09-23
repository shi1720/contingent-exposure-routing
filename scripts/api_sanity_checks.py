"""Post-collection diagnostics motivated by unexpectedly poor arithmetic.

These are not part of the frozen primary experiment or a basis for selecting
models. All diagnostic requests and outcomes are saved separately.
"""
import argparse,datetime,getpass,json,os
from pathlib import Path
import requests
from cer.tasks import parse_trade

ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--execute',action='store_true',help='Explicit opt-in to 16 paid diagnostic API calls')
    args=parser.parse_args()
    if not args.execute:
        print('Post-collection diagnostic protocol: 16 requests. No requests sent; use --execute to collect.')
        return
    protocol=json.loads((ROOT/'config/protocol.json').read_text())
    path=ROOT/'data/raw/api-sanity.jsonl'
    if path.exists():raise RuntimeError('Diagnostics already exist; do not silently overwrite')
    key=os.environ.get('OPENAI_API_KEY') or getpass.getpass('OpenAI API key (not saved): ')
    tasks=[
        ('addition','Compute 2 + 2. Return only a JSON object with numeric field "trade_dollars".',4.),
        ('no_fee','An account has NAV 100000 dollars and a risky holding worth 20000 dollars. There are no fees or price changes. Target risky exposure is 50 percent of NAV. What is the signed dollar trade (positive buy, negative sell)? Return only JSON with numeric field "trade_dollars".',30000.),
        ('explicit_formula','Evaluate (1.39 * 168000 - 48720) / (1 + 1.39 * 0.0075). Return only JSON with numeric field "trade_dollars", rounded to cents.',182893.34),
        ('worked_formula','NAV V=168000, current risky dollars A=48720, target w=1.39, proportional fee c=0.0075. Buying u costs an additional c*u; solve A+u=w*(V-c*u). Thus u=(w*V-A)/(1+w*c). Return the numerical result only as JSON with numeric field "trade_dollars", rounded to cents.',182893.34)
    ]
    for model in protocol['models']:
        for name,prompt,expected in tasks:
            payload={'model':model,'temperature':0,'max_completion_tokens':1000,
                     'response_format':{'type':'json_object'},'messages':[{'role':'user','content':prompt}]}
            r=requests.post('https://api.openai.com/v1/chat/completions',headers={'Authorization':f'Bearer {key}'},json=payload,timeout=90)
            r.raise_for_status();data=r.json();choice=data['choices'][0]
            output=choice['message'].get('content') or '';value,valid=parse_trade(output)
            row=dict(model=model,diagnostic=name,prompt=prompt,expected=expected,output=output,
                     value=value,valid=valid,finish_reason=choice['finish_reason'],usage=data.get('usage'),
                     response_id=data.get('id'),returned_model=data.get('model'),system_fingerprint=data.get('system_fingerprint'),
                     utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
            with path.open('a') as f:f.write(json.dumps(row,sort_keys=True)+'\n')
            print(model,name,'correct',valid and abs(value-expected)<.02,'finish',choice['finish_reason'],flush=True)

if __name__=='__main__':main()
