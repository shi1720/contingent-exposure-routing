"""Collect at most the locally declared number of real API observations.

Credential is read from OPENAI_API_KEY or a no-echo terminal prompt; never saved.
Synthetic prompts contain no personal information. Offline reproduction is free.
"""
import argparse, concurrent.futures, datetime, getpass, hashlib, json, os, threading, time
from pathlib import Path
import requests
from cer.tasks import generate_tasks, parse_trade

ROOT = Path(__file__).resolve().parents[1]
RATES = {"gpt-4.1-nano-2025-04-14":(.1,.4), "gpt-4.1-mini-2025-04-14":(.4,1.6),
         "gpt-4o-mini-2024-07-18":(.15,.6), "gpt-4.1-2025-04-14":(2.,8.)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true", help="Explicit opt-in to paid API calls")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    protocol = json.loads((ROOT/"config/protocol.json").read_text())
    tasks = generate_tasks(protocol["seed"], protocol["tasks"])
    task_path = ROOT/"data/raw/tasks.jsonl"
    task_text = "".join(json.dumps(x,sort_keys=True)+"\n" for x in tasks)
    if task_path.exists() and task_path.read_text() != task_text:
        raise RuntimeError("Refusing to alter a frozen task file")
    task_path.write_text(task_text)
    manifest = {"protocol_sha256":hashlib.sha256((ROOT/"config/protocol.json").read_bytes()).hexdigest(),
                "tasks_sha256":hashlib.sha256(task_text.encode()).hexdigest()}
    (ROOT/"data/raw/protocol-hashes.json").write_text(json.dumps(manifest,indent=2)+"\n")
    if not args.execute:
        print("Prepared tasks and hashes; no requests sent.", flush=True)
        return
    key = os.environ.get("OPENAI_API_KEY") or getpass.getpass("OpenAI API key (not saved): ")
    path = ROOT/"data/raw/api-responses.jsonl"
    existing = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    completed = {(x["task_id"],x["requested_model"]) for x in existing}
    counters = {"requests":sum(x.get("attempts",1) for x in existing),
                "cost":sum(x.get("estimated_cost_usd",0.) for x in existing)}
    lock = threading.Lock()
    def collect(task, model):
        payload = {"model":model,"temperature":protocol["temperature"],
                   "max_completion_tokens":protocol["max_completion_tokens"],
                   "response_format":{"type":"json_object"},
                   "messages":[{"role":"system","content":"Solve the specified financial arithmetic. Follow the output format exactly."},
                               {"role":"user","content":task["prompt"]}]}
        started = datetime.datetime.now(datetime.timezone.utc).isoformat()
        attempts, output, error, response_id, returned_model, fingerprint, usage = 0, "", None, None, None, None, {}
        cost = 0.
        while attempts < 2:
            with lock:
                if counters["requests"] >= protocol["maximum_requests_including_retries"] or counters["cost"] >= protocol["api_cost_guard_usd"]:
                    raise RuntimeError("Declared request or cost guard reached")
                counters["requests"] += 1
            attempts += 1
            try:
                r = requests.post("https://api.openai.com/v1/chat/completions",headers={"Authorization":f"Bearer {key}"},json=payload,timeout=90)
                if r.status_code in (401,403):
                    raise RuntimeError(f"Authentication/permission failure: HTTP {r.status_code}")
                if not r.ok:
                    error = f"HTTP {r.status_code}"
                    if r.status_code in (429,500,502,503,504) and attempts < 2:
                        time.sleep(2)
                        continue
                    break
                data = r.json()
                response_id, returned_model = data.get("id"), data.get("model")
                fingerprint, usage = data.get("system_fingerprint"),data.get("usage",{})
                choice = data["choices"][0]
                output = choice["message"].get("content") or ""
                error = None if choice.get("finish_reason") == "stop" else str(choice.get("finish_reason"))
                rates = RATES[model]
                cost = (usage.get("prompt_tokens",0)*rates[0]+usage.get("completion_tokens",0)*rates[1])/1e6
                with lock: counters["cost"] += cost
                break
            except requests.RequestException as exc:
                error = type(exc).__name__
        value, valid = parse_trade(output)
        if error: value, valid = 0., False
        row = dict(task_id=task["id"],requested_model=model,returned_model=returned_model,
                   started_utc=started,response_id=response_id,system_fingerprint=fingerprint,
                   output=output,trade_dollars=value,valid=valid,error=error,usage=usage,
                   attempts=attempts,estimated_cost_usd=cost)
        with lock:
            with path.open("a") as f: f.write(json.dumps(row,sort_keys=True)+"\n")
        return row
    jobs = [(t,m) for t in tasks for m in protocol["models"] if (t["id"],m) not in completed]
    print(f"Collecting {len(jobs)} observations; max requests {protocol['maximum_requests_including_retries']}; cost guard ${protocol['api_cost_guard_usd']}.",flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(collect,t,m) for t,m in jobs]
        for i,f in enumerate(concurrent.futures.as_completed(futures),1):
            f.result()
            if i % 64 == 0 or i == len(jobs): print(f"Completed {i}/{len(jobs)}; requests={counters['requests']}; estimated cost=${counters['cost']:.4f}",flush=True)
    print("Collection complete. Credentials were not saved.",flush=True)

if __name__ == "__main__": main()
