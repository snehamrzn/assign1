"""
Question 1: Spam Filter Email Agent.

This is a simple reflex agent. It looks at one email at a time and
follows if-then rules. It does not remember the emails it already saw.

For each email the agent does three things:

    1. It reads the email file.
    2. It checks the rules from top to bottom and stops at the first
       rule that fits.
    3. It moves the file into the spam folder or the email folder.

The rules are:

    1. If the sender is on the allow list, the email is not spam.
    2. If the sender is on the restrict list, the email is spam.
    3. If the body has more than 5 bad words, the email is spam.
    4. Otherwise the email is not spam.

The bad words are kept in a dictionary. The agent reads the body one
word at a time and asks whether that word is a key in the dictionary.
"""

import shutil
from email import message_from_binary_file, policy
from email.utils import parseaddr
from pathlib import Path


# Folder that holds this file, and the three list files.
HERE = Path(__file__).resolve().parent

# The two actions the agent can take.
SPAM = "SPAM"
EMAIL = "EMAIL"

# The rule says MORE THAN 5 bad words. Five bad words is still not spam.
BAD_WORD_THRESHOLD = 5


def to_dictionary(items):
    """Turn a list, set, or dictionary of words into a lookup dictionary.

    The word is the key. The value True only means "this item is on the list".
    A later check is: if item in dictionary
    """
    lookup = {}
    for item in items:
        lookup[str(item).lower()] = True
    return lookup


def load_dictionary(path):
    """Read one list file. Skip blank lines and lines that start with #."""
    items = []
    file_text = Path(path).read_text(encoding="utf-8")
    for line in file_text.splitlines():
        cleaned_line = line.strip().lower()
        if cleaned_line == "" or cleaned_line.startswith("#"):
            continue
        items.append(cleaned_line)
    return to_dictionary(items)


def domain_in_list(domain, domains):
    """Return True if this domain, or a parent of it, is in the list.

    mail.spammy-deals.biz matches spammy-deals.biz.
    notspammy-deals.biz does not match spammy-deals.biz.
    """
    parts = domain.split(".")
    # Start at the full domain, then drop the leftmost label each time.
    # "mail.spammy-deals.biz" is checked, then "spammy-deals.biz".
    for index in range(len(parts) - 1):
        candidate = ".".join(parts[index:])
        if candidate in domains:
            return True
    return False


def words_in(text):
    """Break a piece of text into a list of words.

    The text is made lower case first, so "FREE" and "free" are the
    same word. Commas and other punctuation are thrown away.
    "Free," becomes "free".

    A hyphen stays inside the word, so "risk-free" stays one word.
    "freedom" stays "freedom". It does not count as the word "free".
    """
    words = []
    current_word = ""
    lower_text = text.lower()

    for character in lower_text:
        is_letter_or_number = character.isalnum()
        is_hyphen_or_apostrophe = character == "-" or character == "'"
        if is_letter_or_number or is_hyphen_or_apostrophe:
            current_word = current_word + character
        else:
            if current_word != "":
                words.append(current_word)
                current_word = ""

    if current_word != "":
        words.append(current_word)

    return words


def find_bad_words(text, bad_words):
    """Return every bad word that appears in the text.

    Each time a word appears, it is counted again. The sentence
    "FREE free Free" contains the bad word "free" three times.
    """
    bad_words = to_dictionary(bad_words)
    found = []
    for word in words_in(text):
        if word in bad_words:
            found.append(word)
    return found


def strip_tags(text):
    """Remove HTML tags so only the words inside them are left.

    The characters between < and > are skipped. The words outside
    the tags are kept.
    """
    visible_text = []
    inside_tag = False

    for character in text:
        if character == "<":
            inside_tag = True
        elif character == ">":
            inside_tag = False
            visible_text.append(" ")
        elif not inside_tag:
            visible_text.append(character)

    return "".join(visible_text)


def read_email(path):
    """Open one .eml file and return the parsed email."""
    with open(path, "rb") as email_file:
        return message_from_binary_file(email_file, policy=policy.default)


def sender_domain(msg):
    """Return the domain of the From address, in lower case.

    From "Professor <prof@senecapolytechnic.ca>" this returns
    "senecapolytechnic.ca". If there is no From address, it returns
    an empty string.
    """
    from_header = str(msg.get("From", ""))
    name, address = parseaddr(from_header)
    if "@" not in address:
        return ""

    pieces = address.rsplit("@", 1)
    domain = pieces[1]
    domain = domain.strip()
    domain = domain.strip(">")
    domain = domain.lower()
    return domain


def part_text(part):
    """Return the text of one part of the email.

    If that part is HTML, the tags are removed first.
    """
    try:
        text = part.get_content()
    except (LookupError, UnicodeDecodeError):
        payload = part.get_payload(decode=True) or b""
        text = payload.decode("utf-8", errors="replace")

    if part.get_content_subtype() == "html":
        text = strip_tags(text)
    return text


def body_text(msg):
    """Return the text the agent is allowed to look at.

    That is the main body, plus any attachment whose type is text.
    The subject line is not included.

    Some emails store the same body twice, once as plain text and
    once as HTML. Only one of those is read, so the same words are
    not counted twice. Plain text is preferred.
    """
    chunks = []

    body = msg.get_body(preferencelist=("plain", "html"))
    if body is not None:
        chunks.append(part_text(body))

    for part in msg.iter_attachments():
        if part.get_content_maintype() == "text":
            chunks.append(part_text(part))

    return "\n".join(chunks)


class EmailState:
    """The facts the rules look at, after the email has been read."""

    def __init__(self, path, sender_domain, on_allow_list, on_restrict_list,
                 bad_word_count, bad_words_found=None):
        self.path = path
        self.sender_domain = sender_domain
        self.on_allow_list = on_allow_list
        self.on_restrict_list = on_restrict_list
        self.bad_word_count = bad_word_count
        if bad_words_found is None:
            self.bad_words_found = []
        else:
            self.bad_words_found = bad_words_found


class Rule:
    """The rule that matched, and the action to take."""

    def __init__(self, name, action):
        self.name = name
        self.action = action


class SimpleReflexAgent:
    """Decides SPAM or EMAIL for one email, using only that email."""

    def __init__(self, allow_list, restrict_list, bad_words):
        self.allow_list = to_dictionary(allow_list)
        self.restrict_list = to_dictionary(restrict_list)
        self.bad_words = to_dictionary(bad_words)

    def interpret_input(self, email_path):
        """Read one email file and collect the facts the rules need."""
        path = Path(email_path)
        msg = read_email(path)
        domain = sender_domain(msg)
        text = body_text(msg)
        found = find_bad_words(text, self.bad_words)

        state = EmailState(
            path=path,
            sender_domain=domain,
            on_allow_list=domain_in_list(domain, self.allow_list),
            on_restrict_list=domain_in_list(domain, self.restrict_list),
            bad_word_count=len(found),
            bad_words_found=found,
        )
        return state

    def rule_match(self, state):
        """Check the four rules in order. The first true one wins."""
        if state.on_allow_list:
            return Rule("allow-list domain", EMAIL)

        if state.on_restrict_list:
            return Rule("restrict-list domain", SPAM)

        if state.bad_word_count > BAD_WORD_THRESHOLD:
            return Rule("more than " + str(BAD_WORD_THRESHOLD) + " bad words", SPAM)

        return Rule("default (not spam)", EMAIL)

    def check_email(self, email_path):
        """Read one email and return "SPAM" or "EMAIL"."""
        state = self.interpret_input(email_path)
        rule = self.rule_match(state)
        self.last_state = state
        self.last_rule = rule
        return rule.action


def make_agent(lists_folder=HERE):
    """Read the three list files and return an agent.

    Each file becomes a dictionary. The agent then checks a domain
    or a word by asking whether it is a key in that dictionary.
    """
    lists_folder = Path(lists_folder)
    allow_list = load_dictionary(lists_folder / "allow_list.txt")
    restrict_list = load_dictionary(lists_folder / "restrict_list.txt")
    bad_words = load_dictionary(lists_folder / "bad_words.txt")
    return SimpleReflexAgent(allow_list, restrict_list, bad_words)


def execute_action(action, path, spam_dir, email_dir, copy=False):
    """Put the email file into the spam folder or the email folder.

    If copy is true, the original file stays in the inbox.
    Otherwise the file is moved.
    """
    if action == SPAM:
        target_dir = Path(spam_dir)
    else:
        target_dir = Path(email_dir)

    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / Path(path).name

    if copy:
        shutil.copy2(path, target)
    else:
        shutil.move(str(path), str(target))

    return target


def run_agent(agent, inbox_dir, spam_dir, email_dir, copy=False):
    """Run the agent once for every .eml file in the inbox."""
    results = []
    inbox = Path(inbox_dir)

    for path in sorted(inbox.glob("*.eml")):
        action = agent.check_email(path)
        execute_action(action, path, spam_dir, email_dir, copy=copy)
        results.append((path.name, action, agent.last_rule.name, agent.last_state))

    return results
