# DealJudge — on-chain freelance deal arbitration on GenLayer

A stateful Intelligent Contract with a full deal lifecycle: `OPEN → SUBMITTED → APPROVED / REJECTED / NEEDS_REVISION`.

- `create_deal(title, terms)`: the client defines what the work must contain.
- `submit_work(deal_id, work_url)`: a different account (the worker) submits a URL with the deliverable.
- `judge(deal_id)`: client or worker requests judgment. Validators fetch the live page, an LLM compares it with the terms, and they must agree on the verdict (comparative equivalence: verdict identical, reason may differ).
- Access rules: the client cannot submit work, only one worker per deal, only the two parties can request judgment, a `NEEDS_REVISION` deal can be resubmitted.

**Problem:** disputes over "was the work delivered as agreed" normally need a trusted human arbiter.

Files: `contract.py`, `index.html` (frontend using genlayer-js).

## Deployed
GenLayer Studio (studionet) contract: `0x7a974De2B050Cbc01c8c6873AccDBfb82c2B0bD8`
