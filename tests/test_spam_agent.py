"""Tests for Question 1: the simple reflex spam filter agent."""

import shutil
from email.message import EmailMessage
from pathlib import Path

import pytest

from make_test_data import EXPECTED
from spam_agent import (EMAIL, SPAM, EmailState, SimpleReflexAgent, body_text,
                        domain_in_list, find_bad_words, make_agent, read_email,
                        run_agent)

ROOT = Path(__file__).resolve().parent.parent
Q1 = ROOT / "q1_spam_filter"
TEST_DATA = Q1 / "test_data"


@pytest.fixture
def agent():
    return make_agent(Q1)


@pytest.fixture
def inbox(tmp_path):
    """A fresh copy of the sample emails, so the real test data never moves."""
    box = tmp_path / "inbox"
    shutil.copytree(TEST_DATA, box)
    return box


def test_every_sample_has_an_expected_label():
    files = sorted(p.name for p in TEST_DATA.glob("*.eml"))
    assert files == sorted(EXPECTED)


@pytest.mark.parametrize("name,expected", sorted(EXPECTED.items()))
def test_agent_labels_each_sample(agent, name, expected):
    assert agent.check_email(TEST_DATA / name) == expected


def test_run_agent_moves_files_to_right_directory(agent, inbox, tmp_path):
    spam_dir, email_dir = tmp_path / "spam", tmp_path / "email"
    run_agent(agent, inbox, spam_dir, email_dir)

    expected_spam = {n for n, a in EXPECTED.items() if a == SPAM}
    expected_email = {n for n, a in EXPECTED.items() if a == EMAIL}
    assert {p.name for p in spam_dir.glob("*.eml")} == expected_spam
    assert {p.name for p in email_dir.glob("*.eml")} == expected_email
    assert list(inbox.glob("*.eml")) == []  # files were moved, inbox is empty


def test_copy_mode_keeps_inbox(agent, inbox, tmp_path):
    run_agent(agent, inbox, tmp_path / "spam", tmp_path / "email", copy=True)
    assert len(list(inbox.glob("*.eml"))) == len(EXPECTED)


def test_boundary_exactly_five_is_not_spam_six_is_spam(agent):
    five = agent.interpret_input(TEST_DATA / "06_exactly_five_bad_words.eml")
    six = agent.interpret_input(TEST_DATA / "07_six_bad_words.eml")
    assert five.bad_word_count == 5 and agent.rule_match(five).action == EMAIL
    assert six.bad_word_count == 6 and agent.rule_match(six).action == SPAM


def test_allow_list_beats_bad_words(agent):
    state = agent.interpret_input(TEST_DATA / "01_allow_list_override.eml")
    assert state.bad_word_count > 5
    assert state.on_allow_list
    assert agent.rule_match(state).name == "allow-list domain"


def test_restrict_list_beats_clean_body(agent):
    state = agent.interpret_input(TEST_DATA / "02_restrict_list_override.eml")
    assert state.bad_word_count == 0
    assert agent.rule_match(state).name == "restrict-list domain"


def test_allow_list_has_priority_over_restrict_list(tmp_path):
    # A domain on both lists: the allow list rule comes first.
    agent = SimpleReflexAgent({"both.com"}, {"both.com"}, set())
    path = write_email(tmp_path / "both.eml", "x@both.com", "hello")
    assert agent.check_email(path) == EMAIL


def test_text_attachment_is_read():
    msg = read_email(TEST_DATA / "08_text_attachment_spam.eml")
    assert "lottery winner" in body_text(msg)


def test_domain_matching_includes_subdomains_only():
    assert domain_in_list("mail.spammy-deals.biz", {"spammy-deals.biz"})
    assert domain_in_list("spammy-deals.biz", {"spammy-deals.biz"})
    assert not domain_in_list("notspammy-deals.biz", {"spammy-deals.biz"})


def test_bad_words_counted_case_insensitive_each_occurrence():
    assert len(find_bad_words("FREE free Free, freedom", {"free"})) == 3


def test_rules_are_in_priority_order():
    agent = SimpleReflexAgent(set(), set(), set())
    allow = EmailState("x.eml", "both.com", True, True, 9, ["free"])
    restrict = EmailState("x.eml", "spam.biz", False, True, 0, [])
    normal = EmailState("x.eml", "gmail.com", False, False, 0, [])
    assert agent.rule_match(allow).name == "allow-list domain"
    assert agent.rule_match(restrict).name == "restrict-list domain"
    assert agent.rule_match(normal).name == "default (not spam)"


# Helper: write a small email to a file and return its path.
def write_email(path, sender, body):
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = sender, "me@example.com", "test"
    msg.set_content(body)
    path.write_bytes(bytes(msg))
    return path


def test_missing_from_header_uses_bad_word_rule(agent, tmp_path):
    # No sender domain: only the bad word rule can decide.
    path = write_email(tmp_path / "x.eml", "", "free cash prize winner lottery bonus")
    assert agent.interpret_input(path).sender_domain == ""
    assert agent.check_email(path) == SPAM
