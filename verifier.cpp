/*
 * verifier.cpp — Discrete Mathematics Vote Verifier
 *
 * This C++ program is the computational core of the Electronic Voting System.
 * Python (Flask) calls this via subprocess after writing election_data.txt.
 * C++ reads the data, applies discrete math checks, and prints results to stdout.
 * Python reads stdout to display verification results on the website.
 *
 * Discrete Math Concepts Applied:
 *   Set Theory        — Unique voter ID sets prevent duplicates
 *   Functions         — f(voter_id) = candidate_id (injective mapping)
 *   Counting Principle— Sum of per-candidate votes = total votes
 *   Logic             — Boolean checks for each verification rule
 *   Pigeonhole Principle — votes > registered_voters → contradiction
 *   Relations         — (voter, candidate) pair uniqueness
 */

#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <map>
#include <vector>
#include <set>
#include <algorithm>
#include <iomanip>

using namespace std;

struct VoteRecord {
    string voter_id;
    string candidate_id;
    string transaction_id;
};

// Trim whitespace from string
string trim(const string& s) {
    size_t start = s.find_first_not_of(" \t\r\n");
    size_t end   = s.find_last_not_of(" \t\r\n");
    return (start == string::npos) ? "" : s.substr(start, end - start + 1);
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        cout << "ERROR=No input file provided" << endl;
        return 1;
    }

    string filename = argv[1];
    ifstream file(filename);

    if (!file.is_open()) {
        cout << "ERROR=Cannot open file " << filename << endl;
        return 1;
    }

    // ── Parse election_data.txt written by Python ─────────────────────────────
    int registered_voters = 0;
    set<string>           valid_candidates;   // Set Theory: domain of valid candidate IDs
    map<string, string>   candidate_names;    // candidate_id → display name
    map<string, string>   candidate_parties;  // candidate_id → party
    vector<VoteRecord>    votes;              // All recorded votes

    string line;
    while (getline(file, line)) {
        line = trim(line);
        if (line.empty()) continue;

        size_t eq = line.find('=');
        if (eq == string::npos) continue;

        string key   = trim(line.substr(0, eq));
        string value = trim(line.substr(eq + 1));

        if (key == "REGISTERED_VOTERS") {
            registered_voters = stoi(value);

        } else if (key == "VALID_CANDIDATES") {
            // Set Theory: build set of valid candidate IDs
            stringstream ss(value);
            string token;
            while (getline(ss, token, ',')) {
                valid_candidates.insert(trim(token));
            }

        } else if (key == "CANDIDATE") {
            // Format: C1,Aman Sharma
            size_t comma = value.find(',');
            if (comma != string::npos) {
                string cid   = trim(value.substr(0, comma));
                string cname = trim(value.substr(comma + 1));
                candidate_names[cid] = cname;
            }

        } else if (key == "VOTE") {
            // Format: voter_id,candidate_id,transaction_id
            // Relations: represents (Voter, Candidate) relation
            VoteRecord rec;
            stringstream ss(value);
            string token;
            int col = 0;
            while (getline(ss, token, ',')) {
                token = trim(token);
                if      (col == 0) rec.voter_id       = token;
                else if (col == 1) rec.candidate_id   = token;
                else if (col == 2) rec.transaction_id = token;
                col++;
            }
            if (!rec.voter_id.empty() && !rec.candidate_id.empty()) {
                votes.push_back(rec);
            }
        }
    }
    file.close();

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // DISCRETE MATHEMATICS VERIFICATION CHECKS
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    // ── Check 1: Duplicate Voter IDs (Set Theory) ────────────────────────────
    // A set S of voter IDs must have |S| = |votes|.
    // If |S| < |votes|, a voter_id repeated → duplicate vote.
    set<string> seen_voters;
    vector<string> duplicate_voter_ids;
    bool has_duplicates = false;
    for (const auto& v : votes) {
        if (seen_voters.count(v.voter_id)) {
            has_duplicates = true;
            duplicate_voter_ids.push_back(v.voter_id);
        }
        seen_voters.insert(v.voter_id);
    }

    // ── Check 2: Valid Candidate IDs (Functions / Domain Check) ─────────────
    // f: VoterID → CandidateID must have codomain ⊆ valid_candidates.
    // Any vote pointing outside valid_candidates is an invalid mapping.
    vector<string> invalid_candidate_votes;
    bool has_invalid_candidates = false;
    for (const auto& v : votes) {
        if (valid_candidates.find(v.candidate_id) == valid_candidates.end()) {
            has_invalid_candidates = true;
            invalid_candidate_votes.push_back(v.voter_id);
        }
    }

    // ── Check 3: Unique Transaction IDs (Set Theory — Injection) ────────────
    // Transaction IDs form a set; duplicates violate uniqueness invariant.
    set<string> seen_transactions;
    bool has_duplicate_transactions = false;
    for (const auto& v : votes) {
        if (!v.transaction_id.empty()) {
            if (seen_transactions.count(v.transaction_id)) {
                has_duplicate_transactions = true;
            }
            seen_transactions.insert(v.transaction_id);
        }
    }

    // ── Check 4: Pigeonhole Principle ────────────────────────────────────────
    // Pigeonhole: n+1 votes cannot fit into n distinct voters without repetition.
    // If total_votes > registered_voters, at least one voter voted more than once.
    bool pigeonhole_violated = ((int)votes.size() > registered_voters) && (registered_voters > 0);

    // ── Check 5: Vote Count Consistency (Counting Principle) ─────────────────
    // By Addition Principle: Σ votes(candidate_i) = total valid votes cast.
    // Count votes per candidate using counting principle.
    map<string, int> vote_counts;
    for (const auto& cid : valid_candidates) {
        vote_counts[cid] = 0;
    }
    int valid_vote_count = 0;
    for (const auto& v : votes) {
        if (vote_counts.find(v.candidate_id) != vote_counts.end()) {
            vote_counts[v.candidate_id]++;
            valid_vote_count++;
        }
    }
    int sum_candidate_votes = 0;
    for (const auto& kv : vote_counts) {
        sum_candidate_votes += kv.second;
    }
    bool consistency_ok = (sum_candidate_votes == valid_vote_count);

    // ── Check 6: No Negative Votes (Logic / Constraint) ──────────────────────
    // Logical constraint: ∀ candidate c, votes(c) ≥ 0.
    bool no_negative = true;
    for (const auto& kv : vote_counts) {
        if (kv.second < 0) { no_negative = false; break; }
    }

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // WINNER CALCULATION (Logic + Counting Principle)
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    // Sort candidates by vote count descending
    vector<pair<string, int>> sorted_counts(vote_counts.begin(), vote_counts.end());
    sort(sorted_counts.begin(), sorted_counts.end(),
         [](const pair<string,int>& a, const pair<string,int>& b) {
             return a.second > b.second;
         });

    int max_votes    = sorted_counts.empty() ? 0 : sorted_counts[0].second;
    int second_max   = sorted_counts.size() > 1 ? sorted_counts[1].second : 0;
    string winner_id = sorted_counts.empty() ? "N/A" : sorted_counts[0].first;
    string winner_name = candidate_names.count(winner_id) ? candidate_names[winner_id] : winner_id;

    // Logic: tie ⟺ top two candidates have equal votes AND votes > 0
    bool is_tie = (sorted_counts.size() > 1) &&
                  (sorted_counts[0].second == sorted_counts[1].second) &&
                  (max_votes > 0);
    int winning_margin = (is_tie || max_votes == 0) ? 0 : max(0, max_votes - second_max);

    // ── Overall Verdict ───────────────────────────────────────────────────────
    bool all_pass = !has_duplicates &&
                    !has_invalid_candidates &&
                    !has_duplicate_transactions &&
                    !pigeonhole_violated &&
                    consistency_ok &&
                    no_negative;

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // OUTPUT — Python reads this via subprocess.run(capture_output=True)
    // Key=Value format; Python splits on '=' to build result dictionary.
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    cout << "CHECK_DUPLICATE="             << (has_duplicates             ? "FAIL" : "PASS") << endl;
    cout << "CHECK_VALID_CANDIDATES="      << (has_invalid_candidates     ? "FAIL" : "PASS") << endl;
    cout << "CHECK_UNIQUE_TRANSACTIONS="   << (has_duplicate_transactions ? "FAIL" : "PASS") << endl;
    cout << "CHECK_PIGEONHOLE="            << (pigeonhole_violated        ? "FAIL" : "PASS") << endl;
    cout << "CHECK_CONSISTENCY="           << (consistency_ok             ? "PASS" : "FAIL") << endl;
    cout << "CHECK_NO_NEGATIVE="           << (no_negative                ? "PASS" : "FAIL") << endl;
    cout << "ALL_CHECKS="                  << (all_pass                   ? "PASS" : "FAIL") << endl;

    // Per-candidate vote counts
    for (const auto& kv : vote_counts) {
        cout << kv.first << "_VOTES=" << kv.second << endl;
    }

    cout << "WINNER_ID="       << (is_tie ? "TIE"           : winner_id)   << endl;
    cout << "WINNER_NAME="     << (is_tie ? "TIE"           : winner_name) << endl;
    cout << "WINNER_VOTES="    << max_votes                                 << endl;
    cout << "SECOND_HIGHEST="  << second_max                                << endl;
    cout << "WINNING_MARGIN="  << winning_margin                            << endl;
    cout << "IS_TIE="          << (is_tie ? "YES"           : "NO")        << endl;
    cout << "TOTAL_VOTES="     << votes.size()                              << endl;
    cout << "REGISTERED="      << registered_voters                         << endl;

    double turnout = (registered_voters > 0)
                     ? (100.0 * (int)votes.size() / registered_voters)
                     : 0.0;
    cout << fixed << setprecision(2);
    cout << "TURNOUT=" << turnout << endl;

    return 0;
}
