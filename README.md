# Electronic Voting System
### Discrete Mathematics College Project 2026

**Project Title:** Electronic Voting System that Verifies Election Outcomes  
Using Counting Principles and Logical Consistency Checks

**Tech Stack:** Python Flask · C++ · HTML · CSS · JavaScript

---

## Architecture

```
Python Flask (app.py)          C++ (verifier.cpp)
      │                               │
      ├─ Routing & session mgmt       ├─ Vote counting
      ├─ Voter authentication         ├─ Duplicate detection (Set Theory)
      ├─ Vote recording (JSON)        ├─ Candidate validation (Functions)
      ├─ Writes election_data.txt ──► ├─ Pigeonhole check
      ├─ subprocess.run(verifier) ──► ├─ Total consistency
      └─ Reads C++ stdout output ◄─── └─ Winner calculation
```

---

## Folder Structure

```
electronic_voting_system/
│
├── app.py                  ← Flask backend (Python)
├── verifier.cpp            ← Discrete math verifier (C++)
├── verifier.exe / verifier ← Compiled C++ binary (you compile this)
│
├── voters.json             ← Registered voter data
├── candidates.json         ← Candidate list
├── votes.json              ← Vote records (auto-updated)
├── stats.json              ← Attempt counters (auto-updated)
├── election_data.txt       ← Written by Python, read by C++
│
├── templates/
│   ├── base.html           ← Shared navbar + layout
│   ├── index.html          ← Home page
│   ├── login.html          ← Voter login
│   ├── vote.html           ← Candidate selection
│   ├── confirmation.html   ← Vote confirmation
│   ├── dashboard.html      ← Admin dashboard
│   ├── results.html        ← Live results + charts
│   ├── audit.html          ← Audit log (privacy-safe)
│   ├── verification.html   ← C++ verification checks
│   ├── concepts.html       ← Discrete math concepts
│   ├── simulation.html     ← Random simulation runner
│   └── report.html         ← Final election report
│
├── static/
│   ├── style.css           ← Complete stylesheet
│   └── script.js           ← Frontend interactivity
│
└── README.md
```

---

## Step 1 — Install Python dependencies

```bash
pip install flask
```

---

## Step 2 — Compile the C++ Verifier

### Windows (MinGW / g++)
```bash
cd electronic_voting_system
g++ verifier.cpp -o verifier.exe -std=c++17
```

### Linux / Mac
```bash
cd electronic_voting_system
g++ verifier.cpp -o verifier -std=c++17
```

> If g++ is not installed on Windows, download MinGW from https://www.mingw-w64.org/  
> or install via: `winget install -e --id MSYS2.MSYS2`

---

## Step 3 — Run the Flask App

```bash
python app.py
```

Then open your browser at: **http://127.0.0.1:5000**

---

## Sample Voters (for testing)

| Voter ID | Name         | PIN  |
|----------|--------------|------|
| V001     | Arjun Kumar  | 1234 |
| V002     | Priya Sharma | 2345 |
| V003     | Rahul Verma  | 3456 |
| V004     | Ananya Singh | 4567 |
| V005     | Vikram Patel | 5678 |
| V006     | Sneha Reddy  | 6789 |
| V007     | Rohit Gupta  | 7890 |
| V008     | Deepa Nair   | 8901 |
| V009     | Aditya Joshi | 9012 |
| V010     | Kavya Iyer   | 0123 |

---

## Candidates

| ID | Name        | Symbol | Party                    |
|----|-------------|--------|--------------------------|
| C1 | Aman Sharma | Star   | Progressive Alliance      |
| C2 | Riya Mehta  | Sun    | Democratic Front          |
| C3 | Kabir Verma | Tree   | Green Development Party   |
| C4 | Neha Singh  | Lotus  | National Unity Party      |

---

## Discrete Mathematics Concepts Used

| Concept              | Where Used                            | C++ Check |
|----------------------|---------------------------------------|-----------|
| Set Theory           | Unique voter ID set, TXN ID set       | Check 1, 4|
| Functions            | VoterID → CandidateID mapping         | Check 2   |
| Propositional Logic  | Vote acceptance/rejection rules       | All checks|
| Counting Principle   | Total vote summation                  | Check 5   |
| Relations            | (Voter, Candidate) relation model     | Data model|
| Pigeonhole Principle | Fraud detection (votes > voters)      | Check 6   |

---

## Python–C++ Communication

1. Python writes `election_data.txt` with registered voter count, candidate list, and all vote records.
2. Python calls `subprocess.run(['verifier.exe', 'election_data.txt'], capture_output=True)`.
3. C++ reads the file, performs all 6 discrete math checks, and prints `KEY=VALUE` lines to stdout.
4. Python reads stdout, parses it into a dictionary, and passes it to the Jinja2 HTML template.

---

## Pages Reference

| URL              | Page                  |
|------------------|-----------------------|
| `/`              | Home                  |
| `/login`         | Voter Login           |
| `/vote`          | Cast Vote             |
| `/audit`         | Audit Log             |
| `/dashboard`     | Admin Dashboard       |
| `/results`       | Election Results      |
| `/verification`  | C++ Verification      |
| `/concepts`      | Discrete Math Concepts|
| `/simulation`    | Random Simulation     |
| `/report`        | Final Report          |
| `/reset`         | Reset (POST)          |

---

*Educational simulation only. Not intended for real elections.*
