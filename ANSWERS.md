# DPS970 Activity 1: Written Answers

## Question 1: Spam Filter Email Agent

### 1(a) PEAS description


| PEAS                | Description                                                                                                                                                                     |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Performance measure | Each email goes to the right folder. Spam goes to `spam/`. Everything else goes to `email/`. Marking a real email as spam is the worst mistake, because the person can miss it. |
| Environment         | The inbox of `.eml` files, the sender of each email, the `spam/` and `email/` folders, and the three lists (allow, restrict, bad words).                                        |
| Actuators           | Move the file into `spam/` or into `email/`.                                                                                                                                    |
| Sensors             | Read the file. Take the domain from the `From` line and the words from the body, including text attachments.                                                                    |


### 1(b) Properties of the task environment


| Property                   | Value            | Reason                                                                                        |
| -------------------------- | ---------------- | --------------------------------------------------------------------------------------------- |
| Observable                 | Fully observable | The rules only need the sender domain and the body. Both are in the file.                     |
| Deterministic / stochastic | Deterministic    | The same email always gets the same label, and moving a file into a folder does what it says. |
| Episodic / sequential      | Episodic         | One email does not change the decision for the next one.                                      |
| Static / dynamic           | Static           | The email stays the same while the agent decides.                                             |
| Discrete / continuous      | Discrete         | Emails, words, and domains are separate items, and there are only two actions.                |
| Single / multi-agent       | Single agent     | Only the filter acts. Spammers are just part of the environment.                              |
| Known / unknown            | Known            | The rules and the result of each action are given.                                            |


### 1(c) Most appropriate agent type

A simple reflex agent.

It looks at the current email only and follows if-then rules (AIMA Figure 2.10). Each email is its own episode, and the rules can see everything they need, so there is no reason to remember past emails or keep a model of hidden state. There is also no sequence of moves to plan, and no trade-off to score, so a goal-based or utility-based agent is more than this task needs.

A learning agent could add words to the bad-word list from user feedback. The brief does not ask for that.

### 1(d) Implementation

The code is `q1_spam_filter/spam_agent.py`. Run it with `python q1_spam_filter/main.py`.

I followed Figure 2.10:


| Figure 2.10     | Code                                                                                      |
| --------------- | ----------------------------------------------------------------------------------------- |
| percept         | Path of one `.eml` file (`email_path`)                                                    |
| rules           | The three dictionaries, and the `if` statements in `rule_match()`                         |
| INTERPRET-INPUT | `interpret_input()` returns an `EmailState` (domain, which lists matched, bad-word count) |
| RULE-MATCH      | `rule_match()`                                                                            |
| action          | `"SPAM"` or `"EMAIL"`                                                                     |
| agent function  | `check_email()`                                                                           |
| actuator        | `execute_action()` moves the file                                                         |


`rule_match` checks these in order and stops at the first hit:

1. Sender is on the allow list: `EMAIL`, even if the body is full of bad words.
2. Sender is on the restrict list: `SPAM`, even if the body is clean.
3. More than 5 bad words in the body: `SPAM`.
4. Otherwise: `EMAIL`.

The brief calls the restrict list "safe domains." I treated it as blocked domains, because the same sentence says mail from those domains is spam.

All three lists are dictionaries. A word or domain is checked with `if item in dictionary`. Matching ignores case. `"free"` twice counts as 2. `"freedom"` does not count as `"free"`. A subdomain matches its parent, so `mail.cheap-pills.biz` matches `cheap-pills.biz`. Only the body counts, plus text attachments. The subject line does not. If the body is stored as both plain text and HTML, only the plain text is read.

The tests are in `tests/test_spam_agent.py`, with the 12 sample emails in `q1_spam_filter/test_data/`.

## Question 2: Three-Jug Search Problem

Jugs of 12, 8, and 3 gallons, plus a faucet. Goal: get exactly 1 gallon in a jug.

### 2(a) Problem formulation

**States.** `(a, b, c)` is the gallons in the 12, 8, and 3 gallon jugs. Amounts are whole numbers. `a` is 0 to 12, `b` is 0 to 8, `c` is 0 to 3.

**Initial state.** `(0, 0, 0)`. All empty.

**Goal.** Any state where one jug holds exactly 1. So `a = 1`, or `b = 1`, or `c = 1`.

**Actions.**

- Fill a jug from the faucet, if it is not already full.
- Empty a jug onto the ground, if it is not already empty.
- Pour from one jug into another, if the first has water and the second is not full.

**Transition model.**

- Fill sets the chosen jug to 12, 8, or 3. The other two stay the same.
- Empty sets the chosen jug to 0. The other two stay the same.
- Pour moves water until the source is empty or the destination is full, whichever happens first. The third jug stays the same.

### 2(b) Does a heuristic make sense?

Yes. A rough guess of the actions still needed is the smallest distance from 1 gallon among the three jugs. If a jug already holds 1, the guess is 0. In `(0, 0, 0)` the guess is 1. In `(1, 8, 3)` it is 0.

The guess can be high. In `(10, 8, 3)` the closest jug is 2 away, but one pour reaches `(12, 8, 1)`. It is still a useful guide. It does not promise the shortest path.

I did not use a heuristic. There are only 314 reachable states, and breadth-first search finds a goal without one.

### 2(c) Is a search guaranteed to reach a goal?

Breadth-first search is. That property is called complete: if a goal exists it will find one, and if none exists it will stop.

A goal exists. Fill the 12-gallon jug `(12, 0, 0)`, pour into the 8 `(4, 8, 0)`, then pour what is left into the 3 `(1, 8, 3)`.

The search also stops. There are finitely many fillings (at most 13 x 9 x 4 = 468), and finitely many actions from each one. Breadth-first search tries shorter action lists before longer ones, and it remembers fillings it has already seen, so it cannot loop.

Depth-first search that does not remember old fillings is not guaranteed. It can fill the 3-gallon jug, empty it, and repeat that forever. Depth-first search that does remember, iterative deepening, and uniform-cost search are guaranteed too, for the same reason: the state space is finite.

### 2(d) Implementation

The code is `q2_search/jugs_bfs.py`. It follows Figure 3.9.

- `Problem` has `initial`, `actions()`, `result()`, `goal_test()`, and `path_cost()` (every action costs 1).
- `Node` has `state`, `parent`, `action`, and `path_cost`.
- `breadth_first_search()` uses a `deque` as the FIFO queue (`append` to insert, `popleft` to pop) and a `set` named `reached` for states already seen.
- The goal test runs when a child is generated. `goal.solution()` is the list of actions. If there is no goal, the function returns `None`.

`python q2_search/main.py` prints:

```
  0. Start                                       -> (0, 0, 0)
  1. Fill the 12-gal jug from the faucet         -> (12, 0, 0)
  2. Pour the 12-gal jug into the 8-gal jug      -> (4, 8, 0)
  3. Pour the 12-gal jug into the 3-gal jug      -> (1, 8, 3)
```

`tests/test_jugs_bfs.py` checks that this path is legal, that a jug holds 1, that 3 actions is the shortest solution, and that the search returns failure when 1 gallon is impossible (jugs of 4 and 2).