"""
app.py — Flask Backend for Electronic Voting System
Discrete Mathematics College Project

Python (Flask) handles:
  - All HTTP routing and session management
  - Voter authentication and vote recording
  - Reading/writing JSON data files
  - Writing election_data.txt for C++ consumption
  - Calling compiled C++ verifier via subprocess
  - Parsing C++ output and passing to HTML templates

C++ (verifier.cpp) handles:
  - Vote counting using Counting Principle
  - Duplicate detection using Set Theory
  - Candidate validation using Function domain checks
  - Pigeonhole Principle violation detection
  - Winner calculation using logical comparisons
  - Total consistency verification
"""

import json
import os
import random
import secrets
import string
import subprocess
from datetime import datetime

from flask import (Flask, flash, jsonify, redirect, render_template,
                   request, session, url_for)

app = Flask(__name__)
# The session key signs login cookies, so it must not sit in the source of a
# public repository. Set EVS_SECRET_KEY for any real deployment; without it a
# fresh random key is generated per run, which keeps local development working
# and simply logs everyone out when the server restarts.
app.secret_key = os.environ.get("EVS_SECRET_KEY") or secrets.token_hex(32)

# ─── File paths ───────────────────────────────────────────────────────────────
BASE      = os.path.dirname(os.path.abspath(__file__))
VOTERS    = os.path.join(BASE, "voters.json")
CANDS     = os.path.join(BASE, "candidates.json")
VOTES     = os.path.join(BASE, "votes.json")
STATS     = os.path.join(BASE, "stats.json")
ELEC_DATA = os.path.join(BASE, "election_data.txt")

# C++ executable path (platform aware)
VERIFIER  = os.path.join(BASE, "verifier.exe" if os.name == "nt" else "verifier")


# ─── JSON helpers (Python handles all file I/O) ───────────────────────────────

def load(path):
    if not os.path.exists(path):
        return [] if path != STATS else {"duplicate_attempts": 0, "invalid_attempts": 0}
    with open(path, "r") as f:
        return json.load(f)

def save(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def load_stats():
    return load(STATS)

def inc_stat(key):
    s = load_stats()
    s[key] = s.get(key, 0) + 1
    save(STATS, s)


# ─── Transaction ID generator ─────────────────────────────────────────────────

def gen_txn():
    chars = string.ascii_uppercase + string.digits
    return "TXN" + "".join(random.choices(chars, k=8))


# ─── Write election_data.txt for C++ ─────────────────────────────────────────
# Python serialises current state into a flat key=value file.
# C++ reads this file; no JSON library required in C++.

def write_election_data():
    voters     = load(VOTERS)
    votes      = load(VOTES)
    candidates = load(CANDS)

    with open(ELEC_DATA, "w") as f:
        f.write(f"REGISTERED_VOTERS={len(voters)}\n")
        f.write("VALID_CANDIDATES=" + ",".join(c["id"] for c in candidates) + "\n")
        f.write(f"TOTAL_VOTE_RECORDS={len(votes)}\n")
        for c in candidates:
            f.write(f"CANDIDATE={c['id']},{c['name']}\n")
        for v in votes:
            f.write(f"VOTE={v['voter_id']},{v['candidate_id']},{v['transaction_id']}\n")


# ─── Run C++ verifier via subprocess ─────────────────────────────────────────
# Python calls the compiled C++ binary and captures stdout.
# Output is key=value lines; parsed into a Python dict.

def run_verifier():
    write_election_data()

    if not os.path.exists(VERIFIER):
        return {
            "ERROR": "C++ verifier not compiled.",
            "HINT": "Run: g++ verifier.cpp -o verifier  (Linux/Mac) or g++ verifier.cpp -o verifier.exe (Windows)",
            "ALL_CHECKS": "NOT_RUN"
        }

    try:
        res = subprocess.run(
            [VERIFIER, ELEC_DATA],
            capture_output=True, text=True, timeout=15
        )
        return parse_output(res.stdout)
    except subprocess.TimeoutExpired:
        return {"ERROR": "Verifier timed out", "ALL_CHECKS": "ERROR"}
    except Exception as e:
        return {"ERROR": str(e), "ALL_CHECKS": "ERROR"}


def parse_output(raw):
    result = {}
    for line in raw.strip().splitlines():
        if "=" in line:
            k, _, v = line.partition("=")
            result[k.strip()] = v.strip()
    return result


# ─── Route helpers ────────────────────────────────────────────────────────────

def compute_results():
    """Python counts votes and derives stats for results/report pages."""
    votes      = load(VOTES)
    candidates = load(CANDS)
    voters     = load(VOTERS)

    counts = {c["id"]: 0 for c in candidates}
    for v in votes:
        if v["candidate_id"] in counts:
            counts[v["candidate_id"]] += 1

    results = []
    for c in candidates:
        results.append({**c, "votes": counts.get(c["id"], 0)})

    total_v    = len(voters)
    total_cast = len(votes)
    turnout    = round(total_cast / total_v * 100, 2) if total_v > 0 else 0

    sorted_r = sorted(results, key=lambda x: x["votes"], reverse=True)
    winner   = sorted_r[0] if sorted_r else None
    second   = sorted_r[1] if len(sorted_r) > 1 else None
    is_tie   = bool(winner and second and
                    winner["votes"] == second["votes"] and winner["votes"] > 0)
    margin   = (winner["votes"] - second["votes"]) if (winner and second and not is_tie) else 0

    return {
        "results": results,
        "sorted_results": sorted_r,
        "winner": None if is_tie else winner,
        "is_tie": is_tie,
        "winning_margin": margin,
        "total_votes": total_cast,
        "total_registered": total_v,
        "turnout": turnout,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ROUTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    voters = load(VOTERS)
    votes  = load(VOTES)
    stats  = load_stats()
    summary = {
        "registered": len(voters),
        "cast":       len(votes),
        "remaining":  len(voters) - len(votes),
    }
    return render_template("index.html", summary=summary)


# ── Voter Login ────────────────────────────────────────────────────────────────

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        vid   = request.form.get("voter_id",   "").strip().upper()
        vname = request.form.get("voter_name", "").strip()
        pin   = request.form.get("pin",        "").strip()

        voters = load(VOTERS)
        voter  = next(
            (v for v in voters
             if v["id"] == vid
             and v["name"].lower() == vname.lower()
             and v["pin"] == pin),
            None
        )

        if not voter:
            inc_stat("invalid_attempts")
            flash("Invalid voter details. Please check your Voter ID, Name, and PIN.", "error")
            return render_template("login.html")

        if voter.get("voted", False):
            # Track duplicate attempt
            for v in voters:
                if v["id"] == vid:
                    v["duplicate_attempts"] = v.get("duplicate_attempts", 0) + 1
            save(VOTERS, voters)
            inc_stat("duplicate_attempts")
            flash("Access Denied: You have already voted.", "error")
            return render_template("login.html")

        session["voter_id"]   = voter["id"]
        session["voter_name"] = voter["name"]
        return redirect(url_for("vote"))

    return render_template("login.html")


# ── Cast Vote ──────────────────────────────────────────────────────────────────

@app.route("/vote", methods=["GET", "POST"])
def vote():
    if "voter_id" not in session:
        flash("Please log in to vote.", "error")
        return redirect(url_for("login"))

    candidates = load(CANDS)

    if request.method == "POST":
        cid = request.form.get("candidate_id", "").strip()

        if not cid:
            flash("Please select a candidate before submitting.", "error")
            return render_template("vote.html", candidates=candidates,
                                   voter_name=session.get("voter_name"))

        valid_ids = [c["id"] for c in candidates]
        if cid not in valid_ids:
            inc_stat("invalid_attempts")
            flash("Invalid candidate selection.", "error")
            return render_template("vote.html", candidates=candidates,
                                   voter_name=session.get("voter_name"))

        voter_id   = session["voter_id"]
        voter_name = session["voter_name"]

        # Double-check voter hasn't already voted (concurrency safety)
        voters = load(VOTERS)
        voter  = next((v for v in voters if v["id"] == voter_id), None)
        if voter and voter.get("voted", False):
            inc_stat("duplicate_attempts")
            flash("Access Denied: You have already voted.", "error")
            session.clear()
            return redirect(url_for("login"))

        # Record vote
        now    = datetime.now()
        txn_id = gen_txn()
        record = {
            "voter_id":      voter_id,
            "voter_name":    voter_name,
            "candidate_id":  cid,
            "date":          now.strftime("%Y-%m-%d"),
            "time":          now.strftime("%H:%M:%S"),
            "transaction_id": txn_id,
            "status":        "Verified"
        }

        votes = load(VOTES)
        votes.append(record)
        save(VOTES, votes)

        # Mark voter as voted
        for v in voters:
            if v["id"] == voter_id:
                v["voted"] = True
                break
        save(VOTERS, voters)

        session.clear()
        return redirect(url_for("confirmation", txn=txn_id))

    return render_template("vote.html", candidates=candidates,
                           voter_name=session.get("voter_name"))


@app.route("/confirmation/<txn>")
def confirmation(txn):
    return render_template("confirmation.html", transaction_id=txn)


# ── Audit Log ──────────────────────────────────────────────────────────────────

@app.route("/audit")
def audit():
    votes = load(VOTES)
    # Privacy: candidate_id intentionally excluded from public audit log
    audit_log = [
        {
            "voter_id":      v["voter_id"],
            "voter_name":    v["voter_name"],
            "date":          v["date"],
            "time":          v["time"],
            "transaction_id": v["transaction_id"],
            "status":        v.get("status", "Verified"),
        }
        for v in votes
    ]
    return render_template("audit.html", audit_log=audit_log)


# ── Admin Dashboard ────────────────────────────────────────────────────────────

@app.route("/dashboard")
def dashboard():
    voters     = load(VOTERS)
    votes      = load(VOTES)
    candidates = load(CANDS)
    stats      = load_stats()

    total_reg  = len(voters)
    total_cast = len(votes)

    return render_template("dashboard.html", stats={
        "total_registered":   total_reg,
        "total_votes":        total_cast,
        "remaining":          total_reg - total_cast,
        "duplicate_attempts": stats.get("duplicate_attempts", 0),
        "invalid_attempts":   stats.get("invalid_attempts", 0),
        "total_candidates":   len(candidates),
        "voting_status":      "Closed" if total_cast >= total_reg else "Open",
        "turnout":            round(total_cast / total_reg * 100, 1) if total_reg else 0,
    })


# ── Results ────────────────────────────────────────────────────────────────────

@app.route("/results")
def results():
    data = compute_results()
    return render_template("results.html", **data)


# ── Verification (calls C++ verifier) ─────────────────────────────────────────

@app.route("/verification")
def verification():
    result = run_verifier()
    votes  = load(VOTES)
    return render_template("verification.html", result=result, total_votes=len(votes))


# ── Mathematical Concepts ──────────────────────────────────────────────────────

@app.route("/concepts")
def concepts():
    return render_template("concepts.html")


# ── Simulation ─────────────────────────────────────────────────────────────────

@app.route("/simulation")
def simulation():
    return render_template("simulation.html")


@app.route("/run_simulation", methods=["POST"])
def run_simulation():
    voters     = load(VOTERS)
    candidates = load(CANDS)

    # Reset state for fresh simulation
    for v in voters:
        v["voted"] = False
        v["duplicate_attempts"] = 0
    save(VOTERS, voters)
    save(VOTES, [])
    save(STATS, {"duplicate_attempts": 0, "invalid_attempts": 0})

    # Random subset of voters cast votes
    num_voters   = random.randint(max(1, len(voters) // 2), len(voters))
    sim_voters   = random.sample(voters, num_voters)
    now          = datetime.now()
    sim_votes    = []

    for sv in sim_voters:
        cand = random.choice(candidates)
        sim_votes.append({
            "voter_id":       sv["id"],
            "voter_name":     sv["name"],
            "candidate_id":   cand["id"],
            "date":           now.strftime("%Y-%m-%d"),
            "time":           now.strftime("%H:%M:%S"),
            "transaction_id": gen_txn(),
            "status":         "Verified"
        })
        sv["voted"] = True

    save(VOTES, sim_votes)
    save(VOTERS, voters)

    # Call C++ verifier on generated data
    ver = run_verifier()

    # Tally results (Python counting for display)
    counts = {c["id"]: 0 for c in candidates}
    for v in sim_votes:
        counts[v["candidate_id"]] = counts.get(v["candidate_id"], 0) + 1

    sim_results = [
        {**c, "votes": counts.get(c["id"], 0)}
        for c in candidates
    ]
    sim_results.sort(key=lambda x: x["votes"], reverse=True)

    return jsonify({
        "success":          True,
        "total_votes":      len(sim_votes),
        "total_registered": len(voters),
        "results":          sim_results,
        "verifier":         ver,
    })


# ── Final Report ───────────────────────────────────────────────────────────────

@app.route("/report")
def report():
    data = compute_results()
    ver  = run_verifier()
    report_obj = {
        "election_name":      "College Discrete Mathematics Simulation Election 2026",
        "generated_at":       datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "verification_status": ver.get("ALL_CHECKS", "NOT_RUN"),
        **data,
    }
    return render_template("report.html", report=report_obj, verifier=ver)


# ── Reset simulation ───────────────────────────────────────────────────────────

@app.route("/reset", methods=["POST"])
def reset():
    voters = load(VOTERS)
    for v in voters:
        v["voted"] = False
        v["duplicate_attempts"] = 0
    save(VOTERS, voters)
    save(VOTES, [])
    save(STATS, {"duplicate_attempts": 0, "invalid_attempts": 0})
    flash("Simulation reset successfully. All votes have been cleared.", "success")
    return redirect(url_for("dashboard"))


# ─── Entrypoint ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not os.path.exists(VOTES):
        save(VOTES, [])
    if not os.path.exists(STATS):
        save(STATS, {"duplicate_attempts": 0, "invalid_attempts": 0})
    app.run(debug=True)
