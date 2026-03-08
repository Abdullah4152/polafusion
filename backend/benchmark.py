# benchmark.py — Phase 2: Latency benchmarking for fallback vs ensemble
# Run with: python benchmark.py
# Requires: server NOT running (runs inference directly, no HTTP)
# OR use --http flag to benchmark against a live server

import sys
import time
import json
import argparse

# ── Direct mode (no server needed) ───────────────────────────────────────────
def run_direct():
    import os
    os.environ.setdefault("HF_TOKEN", input("Enter HF_TOKEN: ").strip())

    sys.path.insert(0, ".")
    from ml.fallback import run_fallback
    from ml.ensemble import run_ensemble
    from ml.lang_detect import detect

    TEST_TEXTS = {
        "eng": "These immigrants are destroying our culture and stealing our jobs. They are not welcome here.",
        "hin": "ये लोग हमारे देश को बर्बाद कर रहे हैं, इन्हें यहाँ से निकालना होगा।",
        "arb": "هؤلاء المهاجرون يدمرون ثقافتنا ويسرقون وظائفنا ولا مكان لهم هنا.",
        "zho": "这些移民正在破坏我们的文化，抢走我们的工作，他们不受欢迎。",
    }

    results = []
    print("\n" + "="*60)
    print("POLAFUSION BENCHMARK — Direct Inference")
    print("="*60)

    for lang_code, text in TEST_TEXTS.items():
        print(f"\n[{lang_code.upper()}] {text[:50]}...")

        # Fallback
        t0 = time.time()
        fb_result = run_fallback(text, lang_code)
        fb_ms = round((time.time() - t0) * 1000)
        st1 = fb_result["subtask1"]["label"]
        print(f"  ⚡ Fallback:  {fb_ms:>6}ms  |  ST1={'POLARIZED' if st1 else 'NEUTRAL'}")

        # Ensemble
        t0 = time.time()
        en_result = run_ensemble(text, lang_code)
        en_ms = round((time.time() - t0) * 1000)
        st1 = en_result["subtask1"]["label"]
        print(f"  🔥 Ensemble: {en_ms:>6}ms  |  ST1={'POLARIZED' if st1 else 'NEUTRAL'}")

        results.append({
            "lang": lang_code,
            "fallback_ms": fb_ms,
            "ensemble_ms": en_ms,
            "fallback_st1": fb_result["subtask1"]["label"],
            "ensemble_st1": en_result["subtask1"]["label"],
        })

    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    avg_fb = sum(r["fallback_ms"] for r in results) / len(results)
    avg_en = sum(r["ensemble_ms"] for r in results) / len(results)
    print(f"  Avg fallback:  {avg_fb:.0f}ms")
    print(f"  Avg ensemble:  {avg_en:.0f}ms")
    print(f"  Speedup:       {avg_en/avg_fb:.1f}x slower for ensemble")

    with open("benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\n✅ Results saved to benchmark_results.json")


# ── HTTP mode (against live server) ──────────────────────────────────────────
def run_http(base_url: str):
    import urllib.request

    TEST_CASES = [
        {
            "text": "These immigrants are destroying our culture and stealing our jobs.",
            "label": "English polarized",
        },
        {
            "text": "The weather today is quite pleasant and everyone seems happy.",
            "label": "English neutral",
        },
        {
            "text": "ये लोग हमारे देश को बर्बाद कर रहे हैं।",
            "label": "Hindi polarized",
        },
    ]

    print("\n" + "="*60)
    print(f"POLAFUSION BENCHMARK — HTTP against {base_url}")
    print("="*60)

    for case in TEST_CASES:
        for mode in ["fallback", "ensemble"]:
            payload = json.dumps({"text": case["text"], "mode": mode}).encode()
            req = urllib.request.Request(
                f"{base_url}/predict",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            t0 = time.time()
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    result = json.loads(resp.read())
                ms = round((time.time() - t0) * 1000)
                st1 = result["subtask1"]["label"]
                lang = result["detected_language"]
                icon = "⚡" if mode == "fallback" else "🔥"
                print(f"  {icon} {mode:8s} | {case['label']:25s} | lang={lang} | ST1={st1} | {ms}ms")
            except Exception as e:
                ms = round((time.time() - t0) * 1000)
                print(f"  ❌ {mode:8s} | {case['label']:25s} | ERROR: {e} | {ms}ms")

    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PolaFusion benchmark")
    parser.add_argument("--http", type=str, default=None,
                        help="Base URL for HTTP mode, e.g. http://127.0.0.1:8000")
    args = parser.parse_args()

    if args.http:
        run_http(args.http)
    else:
        run_direct()
