#!/usr/bin/env bash
set -euo pipefail

DIR="${1:-.}"
cd "$DIR"

has() { command -v "$1" >/dev/null 2>&1; }
if ! has rg; then
  echo "ripgrep (rg) not found. Install with: brew install ripgrep" >&2
  exit 1
fi

shopt -s nullglob
TEXT_GLOBS=( *.txt *.csv )
if [ ${#TEXT_GLOBS[@]} -eq 0 ]; then
  echo "No .txt or .csv files found in: $PWD" >&2
  exit 1
fi

IP_REGEX='\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
EMAIL_REGEX='[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'

echo "==> Searching for IPs..."
rg -n -H -o -e "$IP_REGEX" "${TEXT_GLOBS[@]}" 2>/dev/null | tee ripgrep_ip_hits.txt >/dev/null || true

echo "==> Searching for emails..."
rg -n -H -o -e "$EMAIL_REGEX" "${TEXT_GLOBS[@]}" 2>/dev/null | tee ripgrep_email_hits.txt >/dev/null || true

summarize() {
  local infile="$1" outtsv="$2"
  # If no hits, still emit a header so downstream steps don't break
  if [ ! -s "$infile" ]; then
    printf "file\ttotal_matches\tunique_matches\n" > "$outtsv"
    return 0
  fi
  # ripgrep lines: file:line[:col]:hit  -> take last colon field as the hit
  awk -F: '
    {
      f=$1; h=$NF;
      total[f]++
      k=f SUBSEP h
      if (!(k in seen)) { seen[k]=1; uniq[f]++ }
    }
    END {
      print "file\ttotal_matches\tunique_matches"
      for (f in total) {
        u=(f in uniq? uniq[f]:0)
        printf "%s\t%d\t%d\n", f, total[f], u
      }
    }' "$infile" | sort -t$'\t' -k1,1 > "$outtsv"
}

unique_count() {
  local infile="$1"
  [ -s "$infile" ] || { echo 0; return; }
  awk -F: '{print $NF}' "$infile" | sort -u | wc -l | tr -d ' '
}

echo "==> Summarizing…"
summarize ripgrep_ip_hits.txt     ip_counts_by_file.tsv
summarize ripgrep_email_hits.txt  email_counts_by_file.tsv

TOTAL_IP=$( [ -s ripgrep_ip_hits.txt ] && wc -l < ripgrep_ip_hits.txt || echo 0 )
TOTAL_EMAIL=$( [ -s ripgrep_email_hits.txt ] && wc -l < ripgrep_email_hits.txt || echo 0 )
UNIQ_IP=$(unique_count ripgrep_ip_hits.txt)
UNIQ_EMAIL=$(unique_count ripgrep_email_hits.txt)

echo
echo "========== SUMMARY =========="
echo "Total IP matches:    ${TOTAL_IP}   (unique: ${UNIQ_IP})"
echo "Total Email matches: ${TOTAL_EMAIL} (unique: ${UNIQ_EMAIL})"
echo "Per-file tables:"
echo "  ip_counts_by_file.tsv"
echo "  email_counts_by_file.tsv"
echo "Raw hits:"
echo "  ripgrep_ip_hits.txt"
echo "  ripgrep_email_hits.txt"
echo "============================="
echo

# Optional GT check if samples23.txt exists
if [ -f "samples23.txt" ]; then
  echo "==> Checking samples23.txt against GT (IPs=100, Emails=200)…"
  IP_23=$(rg -n -H -o -e "$IP_REGEX" samples23.txt | awk -F: '{print $NF}' | sort -u | wc -l | tr -d " ")
  EM_23=$(rg -n -H -o -e "$EMAIL_REGEX" samples23.txt | awk -F: '{print $NF}' | sort -u | wc -l | tr -d " ")
  echo "samples23.txt unique IPs:    $IP_23 (GT 100)"
  echo "samples23.txt unique Emails: $EM_23 (GT 200)"
else
  echo "Note: samples23.txt not found. Convert DOCX first (docx2txt samples23.docx samples23.txt)."
fi

