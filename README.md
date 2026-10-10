# DPS970 Activity 1: Intelligent Agents and Search

This project has two programs.

* **Question 1** is a spam filter. It reads one email at a time, checks four if-then rules, and moves the file into a spam folder or a normal email folder. It does not remember earlier emails. That kind of program is a simple reflex agent.
* **Question 2** is the three-jug problem. The jugs hold 12, 8, and 3 gallons. Breadth-first search finds a way to measure exactly 1 gallon.

The programs use only the Python standard library. `pytest` is needed only when you want to run the tests.

## Setup

You need Python 3.10 or newer. Run every command below from the project folder, the folder that contains this file.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`source .venv/bin/activate` turns the virtual environment on.  After that, open a new terminal and run `source .venv/bin/activate` again before the commands below.

## Question 1: spam filter

### How to run it

```bash
python q1_spam_filter/main.py
```

There are no extra flags. That one command does all of this:

1. It deletes the old `inbox`, `spam`, and `email` folders, if they exist, so the run starts empty.
2. It copies the 12 sample emails from `q1_spam_filter/test_data/` into `q1_spam_filter/inbox/`. The originals in `test_data` stay there.
3. It reads `allow_list.txt`, `restrict_list.txt`, and `bad_words.txt` into three dictionaries.
4. It checks each email and moves the file out of `inbox`.
5. It prints one line per email, then a total.

A normal run ends like this:

```
FILE  DOMAIN  BAD WORDS  ACTION  RULE
01_allow_list_override.eml senecapolytechnic.ca 9 EMAIL allow-list domain
02_restrict_list_override.eml spammy-deals.biz 0 SPAM restrict-list domain
...
12 emails: 6 -> .../q1_spam_filter/spam, 6 -> .../q1_spam_filter/email
```

Each printed line has five pieces:

| Column | Meaning |
| --- | --- |
| FILE | The email file name. |
| DOMAIN | The sender's domain, taken from the `From` line. |
| BAD WORDS | How many bad words were found in the body. |
| ACTION | `EMAIL` means the normal folder. `SPAM` means the spam folder. |
| RULE | Which of the four rules matched. |

After the run, `inbox` is empty because every file was moved. Six files are in `q1_spam_filter/spam/` and six are in `q1_spam_filter/email/`.

### How to put the folders back

The samples in `test_data` are never moved. To delete the folders the run created:

```bash
rm -rf q1_spam_filter/inbox q1_spam_filter/spam q1_spam_filter/email
```

Running `python q1_spam_filter/main.py` again also deletes those folders first, then sorts the samples once more. That is a new run, not an undo.

### What the program checks

The three text files are loaded once, before any email is opened. Each line becomes a dictionary key. The value `True` only means "this item is on the list." Blank lines and lines that start with `#` are skipped. Capital letters are ignored.

`allow_list.txt` holds safe domains. Mail from these domains is never spam:

* `senecapolytechnic.ca`
* `myseneca.ca`
* `github.com`

`restrict_list.txt` holds blocked domains. Mail from these domains is always spam:

* `cheap-pills.biz`
* `lottery-winner.example`
* `spammy-deals.biz`

A subdomain matches its parent. `mail.cheap-pills.biz` matches `cheap-pills.biz`. `notspammy-deals.biz` does not match `spammy-deals.biz`.

`bad_words.txt` holds the spam words: `free`, `winner`, `prize`, `cash`, `urgent`, `guarantee`, `viagra`, `lottery`, `bitcoin`, `crypto`, `discount`, `offer`, `click`, `unsubscribe`, `congratulations`, `claim`, `million`, `investment`, `bonus`, and `risk-free`.

The body is split into words. Each word is looked up with `if word in bad_words`. `FREE free` counts as 2. `freedom` does not count as `free`, because the whole word has to match. `risk-free` stays one word. Only the body counts, plus attachments that are plain text. The subject line is ignored. If the same body is stored as both plain text and HTML, only the plain text is counted.

The four rules are checked in this order. The first one that fits wins.

1. The sender is on the allow list. The email goes to the normal folder, even if the body has many bad words.
2. The sender is on the restrict list. The email goes to spam, even if the body is clean.
3. The body has more than 5 bad words. The email goes to spam. Exactly 5 is still a normal email.
4. None of those matched. The email goes to the normal folder.

### What calls what

`main.py` is the start. It prepares the folders, then calls two functions in `spam_agent.py`.

* `make_agent` reads the three text files and builds the agent.
* `run_agent` loops over the inbox. For each file it calls `check_email`, then moves the file.

`check_email` does two steps:

* `interpret_input` opens the `.eml` file and records the sender domain, whether each list matched, and the bad-word count.
* `rule_match` runs the four `if` statements above and returns `SPAM` or `EMAIL`.

### The 12 sample emails

| File | What it checks | Result |
| --- | --- | --- |
| `01_allow_list_override.eml` | Allow-list sender, 9 bad words | EMAIL |
| `02_restrict_list_override.eml` | Restrict-list sender, clean body | SPAM |
| `03_restrict_list_subdomain.eml` | Subdomain of a restricted domain | SPAM |
| `04_many_bad_words.eml` | 10 bad words | SPAM |
| `05_few_bad_words.eml` | 2 bad words | EMAIL |
| `06_exactly_five_bad_words.eml` | Exactly 5 bad words | EMAIL |
| `07_six_bad_words.eml` | Exactly 6 bad words | SPAM |
| `08_text_attachment_spam.eml` | Bad words in a text attachment | SPAM |
| `09_html_body_spam.eml` | Bad words inside HTML | SPAM |
| `10_clean_email.eml` | No bad words | EMAIL |
| `11_bad_words_in_subject_only.eml` | Bad words only in the subject | EMAIL |
| `12_plain_and_html_not_double_counted.eml` | Same words in plain text and HTML | EMAIL |

To rebuild those sample files:

```bash
python q1_spam_filter/make_test_data.py
```

You can edit the three list files. Put one domain or one word on each line. A line that starts with `#` is a comment.

## Question 2: three jugs

```bash
python q2_search/main.py
```

The jugs start empty, written as `(0, 0, 0)`. The search fills, empties, and pours until one jug holds exactly 1 gallon. It finds this 3-step solution:

```
Jugs: (12, 8, 3)  start: (0, 0, 0)  goal: a jug holds 1
Reachable states: 314
Solution found with 3 actions:

  0. Start                                       -> (0, 0, 0)
  1. Fill the 12-gal jug from the faucet         -> (12, 0, 0)
  2. Pour the 12-gal jug into the 8-gal jug      -> (4, 8, 0)
  3. Pour the 12-gal jug into the 3-gal jug      -> (1, 8, 3)
```

The numbers in parentheses are the gallons in the 12-gallon jug, the 8-gallon jug, and the 3-gallon jug.

To try a different target amount:

```bash
python q2_search/main.py --target 4
```

To try different jug sizes:

```bash
python q2_search/main.py --capacities 12 8 3 --target 1
```

The search itself is in `q2_search/jugs_bfs.py`. `q2_search/main.py` only reads the options and prints the steps.

## Tests

From the project folder, with the virtual environment on:

```bash
python -m pytest
```

`pytest.ini` tells pytest to look in `tests/` and to import the two program folders. The tests copy sample emails into a temporary folder. They do not change `test_data/`.

* `tests/test_spam_agent.py` checks every sample email, the folders files land in, the rule order, the 5-versus-6 bad-word boundary, subdomains, and text attachments.
* `tests/test_jugs_bfs.py` checks that breadth-first search finds a goal, that every step is a legal pour, and that the solution is the shortest one.

## Files

```
assign1/
├── README.md                     This file
├── ANSWERS.md                    Written answers for question 1 and question 2
├── requirements.txt              pytest, used only for the tests
├── pytest.ini                    Where pytest looks for tests
├── q1_spam_filter/
│   ├── main.py                   Starts the spam filter
│   ├── spam_agent.py             Reads each email and applies the four rules
│   ├── make_test_data.py         Rebuilds the 12 sample emails
│   ├── allow_list.txt            Safe domains
│   ├── restrict_list.txt         Blocked domains
│   ├── bad_words.txt             Spam words
│   └── test_data/                The 12 sample .eml files
├── q2_search/
│   ├── main.py                   Starts the jug search and prints the steps
│   └── jugs_bfs.py               The jug problem and breadth-first search
└── tests/
    ├── test_spam_agent.py
    └── test_jugs_bfs.py
```

`inbox`, `spam`, and `email` appear inside `q1_spam_filter/` only after you run the spam filter. They are the working folders, not source files.

GitHub Actions runs the tests, the spam filter, and the jug search on every push and pull request, on Python 3.10 and Python 3.12. That workflow is `.github/workflows/tests.yml`.
