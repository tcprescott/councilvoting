import json
import os
import re

import gspread
import pyrankvote
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
import pyrankvote

load_dotenv()

CANDIDATE_REGEX = re.compile('Ranked Choice \[(.*)\]')

def main():
    gc = gspread.authorize(get_creds())
    wb = gc.open_by_key(os.environ['gsheet_id'])
    worksheet = wb.get_worksheet(0)

    candidates = {}
    for candidate in [CANDIDATE_REGEX.search(c).group(1) for c in worksheet.row_values(1) if CANDIDATE_REGEX.search(c)]:
        candidates[candidate] = pyrankvote.Candidate(candidate)

    raw_ballots = worksheet.get_all_records()

    ballots = []
    for raw_ballot in raw_ballots:
        ballot = sorted({candidates[CANDIDATE_REGEX.search(c).group(1)]:r for (c, r) in raw_ballot.items() if CANDIDATE_REGEX.search(c)}.items(), key=lambda x: x[1])
        ballots.append(pyrankvote.Ballot(ranked_candidates=[c for c, r in ballot]))
        print(ballot)

    
    election_result = pyrankvote.single_transferable_vote(candidates=candidates.values(), ballots=ballots, number_of_seats=3)

    winners = election_result.get_winners()
    with open('output/results.txt', 'w+') as f:
        f.write(str(election_result))

def get_creds():
    return Credentials.from_service_account_info(
            json.loads(os.environ['gsheet_api_oauth'], strict=False),
            scopes=['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive',
                'https://www.googleapis.com/auth/spreadsheets']
        )

if __name__ == "__main__":
    main()
