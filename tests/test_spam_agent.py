"""Tests for Question 1: the simple reflex spam filter.

pytest runs every function whose name starts with test_.
assert means "this must be true". If it is false, that test fails.
tmp_path is a temporary folder pytest makes for that one test.
"""

import shutil
from email.message import EmailMessage
from pathlib import Path

from make_test_data import EXPECTED
from spam_agent import (
    EMAIL,
    SPAM,
    EmailState,
    SimpleReflexAgent,
    body_text,
    domain_in_list,
    find_bad_words,
    make_agent,
    read_email,
    run_agent,
)

ROOT = Path(__file__).resolve().parent.parent
Q1 = ROOT / "q1_spam_filter"
TEST_DATA = Q1 / "test_data"


def fresh_inbox(folder):
    """Copy the sample emails into a new inbox so the real files never move."""
    inbox = folder / "inbox"
    shutil.copytree(TEST_DATA, inbox)
    return inbox


def write_email(path, sender, body):
    """Write one small email file and return its path."""
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = "me@example.com"
    msg["Subject"] = "test"
    msg.set_content(body)
    path.write_bytes(bytes(msg))
    return path


def test_every_sample_has_an_expected_label():
    # Every .eml file in test_data must be listed in EXPECTED.
    file_names = []
    for path in TEST_DATA.glob("*.eml"):
        file_names.append(path.name)
    file_names.sort()

    expected_names = list(EXPECTED.keys())
    expected_names.sort()
    assert file_names == expected_names


def test_agent_labels_each_sample():
    # The agent must give each sample the label stored in EXPECTED.
    agent = make_agent(Q1)
    for file_name in EXPECTED:
        expected_label = EXPECTED[file_name]
        label = agent.check_email(TEST_DATA / file_name)
        assert label == expected_label, file_name


def test_run_agent_moves_files_to_right_directory(tmp_path):
    # Step 1. Copy the samples into a temporary inbox and run the agent.
    agent = make_agent(Q1)
    inbox = fresh_inbox(tmp_path)
    spam_dir = tmp_path / "spam"
    email_dir = tmp_path / "email"
    run_agent(agent, inbox, spam_dir, email_dir)

    # Step 2. Read the file names that landed in each folder.
    spam_names = []
    for path in spam_dir.glob("*.eml"):
        spam_names.append(path.name)
    email_names = []
    for path in email_dir.glob("*.eml"):
        email_names.append(path.name)

    # Step 3. Each sample must be in the folder that matches its label.
    for file_name in EXPECTED:
        if EXPECTED[file_name] == SPAM:
            assert file_name in spam_names
        if EXPECTED[file_name] == EMAIL:
            assert file_name in email_names

    # Step 4. The files were moved, so the inbox is empty.
    left_in_inbox = list(inbox.glob("*.eml"))
    assert left_in_inbox == []


def test_copy_mode_keeps_inbox(tmp_path):
    # copy=True leaves the original file in the inbox.
    agent = make_agent(Q1)
    inbox = fresh_inbox(tmp_path)
    run_agent(agent, inbox, tmp_path / "spam", tmp_path / "email", copy=True)

    still_there = list(inbox.glob("*.eml"))
    assert len(still_there) == len(EXPECTED)


def test_boundary_exactly_five_is_not_spam_six_is_spam():
    # More than 5 bad words is spam. Exactly 5 is still a normal email.
    agent = make_agent(Q1)

    five = agent.interpret_input(TEST_DATA / "06_exactly_five_bad_words.eml")
    assert five.bad_word_count == 5
    assert agent.rule_match(five).action == EMAIL

    six = agent.interpret_input(TEST_DATA / "07_six_bad_words.eml")
    assert six.bad_word_count == 6
    assert agent.rule_match(six).action == SPAM


def test_allow_list_beats_bad_words():
    # This sender is on the allow list, even though the body has many bad words.
    agent = make_agent(Q1)
    state = agent.interpret_input(TEST_DATA / "01_allow_list_override.eml")
    assert state.bad_word_count > 5
    assert state.on_allow_list is True
    assert agent.rule_match(state).name == "allow-list domain"


def test_restrict_list_beats_clean_body():
    # This sender is on the restrict list, even though the body is clean.
    agent = make_agent(Q1)
    state = agent.interpret_input(TEST_DATA / "02_restrict_list_override.eml")
    assert state.bad_word_count == 0
    assert agent.rule_match(state).name == "restrict-list domain"


def test_allow_list_has_priority_over_restrict_list(tmp_path):
    # The same domain is on both lists. The allow-list rule is checked first.
    agent = SimpleReflexAgent({"both.com"}, {"both.com"}, set())
    path = write_email(tmp_path / "both.eml", "x@both.com", "hello")
    assert agent.check_email(path) == EMAIL


def test_text_attachment_is_read():
    # Words inside a text attachment count. This file says "lottery winner" there.
    msg = read_email(TEST_DATA / "08_text_attachment_spam.eml")
    text = body_text(msg)
    assert "lottery winner" in text


def test_domain_matching_includes_subdomains_only():
    # mail.spammy-deals.biz matches the listed domain.
    # notspammy-deals.biz is a different name, so it does not match.
    listed = {"spammy-deals.biz"}
    assert domain_in_list("mail.spammy-deals.biz", listed) is True
    assert domain_in_list("spammy-deals.biz", listed) is True
    assert domain_in_list("notspammy-deals.biz", listed) is False


def test_bad_words_counted_case_insensitive_each_occurrence():
    # FREE, free, and Free each count. freedom is a different word.
    found = find_bad_words("FREE free Free, freedom", {"free"})
    assert len(found) == 3


def test_rules_are_in_priority_order():
    # Check the four rules with facts we write by hand, not by reading a file.
    agent = SimpleReflexAgent(set(), set(), set())

    on_both_lists = EmailState("x.eml", "both.com", True, True, 9, ["free"])
    on_restrict_only = EmailState("x.eml", "spam.biz", False, True, 0, [])
    on_neither = EmailState("x.eml", "gmail.com", False, False, 0, [])

    assert agent.rule_match(on_both_lists).name == "allow-list domain"
    assert agent.rule_match(on_restrict_only).name == "restrict-list domain"
    assert agent.rule_match(on_neither).name == "default (not spam)"


def test_missing_from_header_uses_bad_word_rule(tmp_path):
    # There is no sender domain, so only the bad-word rule can decide.
    agent = make_agent(Q1)
    path = write_email(
        tmp_path / "x.eml",
        "",
        "free cash prize winner lottery bonus",
    )
    state = agent.interpret_input(path)
    assert state.sender_domain == ""
    assert agent.check_email(path) == SPAM
