# v0.2.16
# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
import json


class DealJudge(gl.Contract):
    """On-chain freelance deal lifecycle: OPEN -> SUBMITTED -> APPROVED / REJECTED / NEEDS_REVISION.
    Validators fetch the delivered work and judge it against the agreed terms."""

    deals: TreeMap[str, str]
    count: u256

    def __init__(self):
        self.count = u256(0)

    def _load(self, deal_id: str) -> dict:
        raw = self.deals.get(deal_id, "")
        if raw == "":
            raise Exception("deal not found")
        return json.loads(raw)

    def _save(self, deal_id: str, deal: dict) -> None:
        self.deals[deal_id] = json.dumps(deal, sort_keys=True)

    @gl.public.write
    def create_deal(self, title: str, terms: str) -> str:
        deal_id = str(self.count)
        self._save(
            deal_id,
            {
                "id": deal_id,
                "title": title,
                "terms": terms,
                "client": str(gl.message.sender_address),
                "worker": "",
                "work_url": "",
                "status": "OPEN",
                "reason": "",
                "attempts": 0,
            },
        )
        self.count = u256(int(self.count) + 1)
        return deal_id

    @gl.public.write
    def submit_work(self, deal_id: str, work_url: str) -> None:
        deal = self._load(deal_id)
        sender = str(gl.message.sender_address)
        if deal["status"] not in ("OPEN", "NEEDS_REVISION"):
            raise Exception("deal is not accepting work")
        if sender == deal["client"]:
            raise Exception("client cannot submit work")
        if deal["worker"] not in ("", sender):
            raise Exception("another worker already took this deal")
        deal["worker"] = sender
        deal["work_url"] = work_url
        deal["status"] = "SUBMITTED"
        self._save(deal_id, deal)

    @gl.public.write
    def judge(self, deal_id: str) -> str:
        deal = self._load(deal_id)
        sender = str(gl.message.sender_address)
        if deal["status"] != "SUBMITTED":
            raise Exception("nothing to judge")
        if sender not in (deal["client"], deal["worker"]):
            raise Exception("only the client or worker can request judgment")

        terms = deal["terms"]
        work_url = deal["work_url"]

        def run() -> str:
            page = gl.nondet.web.render(work_url, mode="text")
            prompt = f"""You are a neutral arbiter for a freelance deal.
AGREED TERMS:
{terms}

DELIVERED WORK (page content, may be truncated):
{page[:6000]}

Does the delivered work satisfy every requirement in the agreed terms?
Answer with JSON only, no markdown:
{{"verdict": "APPROVED" | "REJECTED" | "NEEDS_REVISION", "reason": "max 2 short sentences"}}"""
            raw = gl.nondet.exec_prompt(prompt)
            raw = raw.replace("```json", "").replace("```", "").strip()
            data = json.loads(raw)
            verdict = str(data.get("verdict", "NEEDS_REVISION")).upper()
            if verdict not in ("APPROVED", "REJECTED", "NEEDS_REVISION"):
                verdict = "NEEDS_REVISION"
            return json.dumps(
                {"verdict": verdict, "reason": str(data.get("reason", ""))[:300]},
                sort_keys=True,
            )

        result = json.loads(
            gl.eq_principle.prompt_comparative(
                run,
                "The 'verdict' field must be identical. The 'reason' may be worded differently.",
            )
        )
        deal["status"] = result["verdict"]
        deal["reason"] = result["reason"]
        deal["attempts"] = int(deal["attempts"]) + 1
        self._save(deal_id, deal)
        return result["verdict"]

    @gl.public.view
    def get_count(self) -> int:
        return int(self.count)

    @gl.public.view
    def get_deal(self, deal_id: str) -> str:
        return self.deals.get(deal_id, "")
