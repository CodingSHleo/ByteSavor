#!/usr/bin/env python3
"""离线黑箱 Eval Runner — mock + api 双模式。
用法:
  python evals/runner.py --quick                  # mock 模式（默认）
  python evals/runner.py --quick --mode api       # 真实 API 模式
  python evals/runner.py --quick --mode api --api-base http://127.0.0.1:8000
输出: evals/reports/latest.json + latest.md
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent.tools import ToolRegistry
from app.agent.langgraph_runtime import LangGraphAgent
from evals.scorer import score_result

REPORT_DIR = os.path.join(os.path.dirname(__file__), "reports")


def load_cases(path: str) -> list[dict]:
    cases = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


# ── mock 模式 ──
async def run_case_mock(case: dict) -> dict:
    tools = ToolRegistry()

    async def decision(state):
        ingredients = state.get("ingredients", [])
        titles = []
        if ingredients:
            titles.append(f"{'、'.join(ingredients[:2])}健康餐")
        titles.append("番茄炒蛋")
        titles.append("清炒时蔬")
        recipes = [{
            "recipe_id": f"eval_r_{i:03d}",
            "title": t,
            "match_score": 0.9 - i * 0.1,
            "cook_time": 20 + i * 5,
            "calories": 300 + i * 50,
            "ingredients": [{"name": ing} for ing in ingredients[:2]] if i == 0 else [],
        } for i, t in enumerate(titles[:3])]
        return {"recipes": recipes}

    async def task(state):
        recipes = state.get("recipes", [])
        items = []
        for r in recipes[:3]:
            for ing in (r.get("ingredients", []) or []):
                items.append({"name": ing.get("name", "食材"), "display": "300g"})
        return {"shopping_list": items}

    tools.register("decision", decision)
    tools.register("task", task)
    agent = LangGraphAgent(tools=tools, max_steps=4)
    return await agent.run(
        user_input=case["input"],
        conversation_id=case["conversation_id"],
        memory_context={},
    )


# ── API 模式 ──
async def run_case_api(case: dict, base_url: str) -> dict:
    import httpx
    url = f"{base_url.rstrip('/')}/v1/agent/execute"
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json={
            "input": case["input"],
            "conversation_id": case["conversation_id"],
        })
        if resp.status_code != 200:
            return {"error": f"HTTP {resp.status_code}: {resp.text[:200]}", "events": [], "recipes": []}
        body = resp.json()
        data = body.get("data", body)
        return data


async def run_all(cases: list[dict], mode: str = "mock", api_base: str = "http://127.0.0.1:8000") -> dict:
    scores = []
    started = time.perf_counter()
    for case in cases:
        try:
            if mode == "api":
                result = await run_case_api(case, api_base)
            else:
                result = await run_case_mock(case)
        except Exception as exc:
            result = {"error": str(exc), "events": [], "recipes": []}
        score = score_result(case, result)
        score["termination_reason"] = result.get("termination_reason", "")
        score["events_count"] = len(result.get("events", []))
        score["memory_used_count"] = len(result.get("memory_used", []))
        eval_events = [e for e in result.get("events", []) if e.get("type") == "evaluation"]
        score["evaluation_verdict"] = eval_events[0].get("verdict", "") if eval_events else ""
        score["error"] = result.get("error", "")
        scores.append(score)

    elapsed = round(time.perf_counter() - started, 2)
    total_passed = sum(s["total_score"] for s in scores)
    total_max = sum(s["max_score"] for s in scores)
    avg = round(total_passed / total_max * 100) if total_max else 0
    total_failed_checks = sum(len(s["failed_checks"]) for s in scores)
    failed_cases = [s for s in scores if s["failed_checks"]]

    return {
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": mode,
            "total_cases": len(cases),
            "total_score": total_passed,
            "total_max": total_max,
            "avg_pct": avg,
            "total_failed_checks": total_failed_checks,
            "failed_cases_count": len(failed_cases),
            "elapsed_sec": elapsed,
        },
        "scores": scores,
    }


def write_report(report: dict, prefix: str = "latest"):
    os.makedirs(REPORT_DIR, exist_ok=True)
    json_path = os.path.join(REPORT_DIR, f"{prefix}.json")
    md_path = os.path.join(REPORT_DIR, f"{prefix}.md")

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    meta = report["meta"]
    lines = [
        f"# ByteSavor Eval Report ({meta.get('mode', 'mock')})",
        f"**时间**: {meta['timestamp']}",
        f"**用例数**: {meta['total_cases']}",
        f"**总分**: {meta['total_score']}/{meta['total_max']} ({meta['avg_pct']}%)",
        f"**失败检查数**: {meta['total_failed_checks']}",
        f"**失败用例数**: {meta['failed_cases_count']}",
        f"**耗时**: {meta['elapsed_sec']}s",
        "",
        "## 用例详情",
    ]
    for s in report["scores"]:
        status = "PASS" if not s["failed_checks"] else f"FAIL ({', '.join(s['failed_checks'])})"
        lines.append(f"### {s['case_id']}: {s['name']} — {status}")
        lines.append(f"- score: {s['total_score']}/{s['max_score']}")
        lines.append(f"- termination_reason: {s['termination_reason']}")
        lines.append(f"- events: {s['events_count']}")
        lines.append(f"- evaluation verdict: {s['evaluation_verdict']}")
        if s["failed_checks"]:
            for fc in s["failed_checks"]:
                lines.append(f"  - FAIL: {fc} → {s['details'].get(fc, '')}")
        lines.append("")

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Report: {json_path}")
    print(f"Report: {md_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true", help="Run quick 10-case set")
    parser.add_argument("--cases", default="", help="Path to JSONL cases file")
    parser.add_argument("--mode", default="mock", choices=["mock", "api"], help="mock=内嵌Agent, api=HTTP请求")
    parser.add_argument("--api-base", default="http://127.0.0.1:8000", help="API base URL (仅 api mode)")
    parser.add_argument("--prefix", default="latest", help="Report file prefix")
    args = parser.parse_args()

    if args.quick:
        case_path = os.path.join(os.path.dirname(__file__), "cases", "quick.jsonl")
    elif args.cases:
        case_path = args.cases
    else:
        case_path = os.path.join(os.path.dirname(__file__), "cases", "quick.jsonl")

    if not os.path.exists(case_path):
        print(f"Cases file not found: {case_path}")
        sys.exit(1)

    cases = load_cases(case_path)
    print(f"Loaded {len(cases)} cases from {case_path} (mode={args.mode})")
    report = asyncio.run(run_all(cases, mode=args.mode, api_base=args.api_base))
    write_report(report, prefix=args.prefix)
    print(f"Score: {report['meta']['total_score']}/{report['meta']['total_max']} ({report['meta']['avg_pct']}%)")


if __name__ == "__main__":
    main()
