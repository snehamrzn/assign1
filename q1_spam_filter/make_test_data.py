"""
Generate the sample .eml files in test_data/.

The files are built with the standard library 'email' module, so they are
valid RFC 5322 messages. Run this script again to rebuild the samples:

    python q1_spam_filter/make_test_data.py

EXPECTED maps each file name to the label the agent must give it.
The tests in tests/test_spam_agent.py use the same table.
"""

from email.message import EmailMessage
from email.utils import formatdate
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent / "test_data"

# file name -> expected action ("SPAM" or "EMAIL")
EXPECTED = {
    "01_allow_list_override.eml": "EMAIL",
    "02_restrict_list_override.eml": "SPAM",
    "03_restrict_list_subdomain.eml": "SPAM",
    "04_many_bad_words.eml": "SPAM",
    "05_few_bad_words.eml": "EMAIL",
    "06_exactly_five_bad_words.eml": "EMAIL",
    "07_six_bad_words.eml": "SPAM",
    "08_text_attachment_spam.eml": "SPAM",
    "09_html_body_spam.eml": "SPAM",
    "10_clean_email.eml": "EMAIL",
    "11_bad_words_in_subject_only.eml": "EMAIL",
    "12_plain_and_html_not_double_counted.eml": "EMAIL",
}


def make(sender, subject, body, html=None, attachment=None):
    """Build one EmailMessage."""
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = "student@myseneca.ca"
    msg["Subject"] = subject
    msg["Date"] = formatdate(1791000000, localtime=False)  # fixed date
    if body is not None:
        msg.set_content(body)
        if html is not None:
            msg.add_alternative(html, subtype="html")
    else:
        msg.set_content(html, subtype="html")  # HTML-only email
    if attachment is not None:
        name, text = attachment
        msg.add_attachment(text, subtype="plain", filename=name)
    return msg


def build_all():
    return {
        # Allow list wins even with many bad words (9 here).
        "01_allow_list_override.eml": make(
            "Professor <prof@senecapolytechnic.ca>",
            "Lecture notes: spam examples",
            "Here are spam examples for class:\n"
            "free cash prize, winner of the lottery, claim your bonus now, "
            "urgent offer.\n",
        ),
        # Restrict list is spam even with a clean body.
        "02_restrict_list_override.eml": make(
            "Deals Team <news@spammy-deals.biz>",
            "Monthly newsletter",
            "Hello,\nThis is our monthly newsletter about gardening.\nBest regards.\n",
        ),
        # A subdomain of a restricted domain is also restricted.
        "03_restrict_list_subdomain.eml": make(
            "Pharmacy <promo@mail.cheap-pills.biz>",
            "Your order",
            "Your order has shipped.\n",
        ),
        # Unknown domain, 10 bad words -> spam.
        "04_many_bad_words.eml": make(
            "Lucky Draw <draw@unknown-shop.com>",
            "Hello",
            "Congratulations! You are a winner. Claim your free cash prize now.\n"
            "This urgent offer is a guarantee. Click here.\n",
        ),
        # Unknown domain, 2 bad words -> not spam.
        "05_few_bad_words.eml": make(
            "Sam <sam@gmail.com>",
            "Lunch on Friday",
            "Hi, I have a discount coupon for lunch. It is free on Friday.\n",
        ),
        # Exactly 5 bad words -> NOT spam (rule needs MORE THAN 5).
        "06_exactly_five_bad_words.eml": make(
            "Store <info@example-store.com>",
            "Weekly update",
            "We have a discount and a free gift. Click the offer to claim it.\n",
        ),
        # Exactly 6 bad words -> spam (first count above the threshold).
        "07_six_bad_words.eml": make(
            "Store <info@example-store.com>",
            "Weekly update",
            "We have a discount and a free gift. Click the offer to claim it.\n"
            "It is urgent.\n",
        ),
        # Body has 2 bad words, the text attachment has 5 more: 7 total -> spam.
        "08_text_attachment_spam.eml": make(
            "Mailer <mailer@random-host.net>",
            "Document attached",
            "Please read the attached file. It is urgent and free.\n",
            attachment=("details.txt",
                        "You are the lottery winner. Claim one million in bitcoin.\n"),
        ),
        # HTML-only body with 7 bad words inside tags -> spam.
        "09_html_body_spam.eml": make(
            "Crypto Club <club@crypto-club.io>",
            "Opportunity",
            None,
            html="<html><body><p><b>Crypto</b> investment, <i>risk-free</i>!</p>"
                 "<p>Get a <a href='#'>bonus</a> in bitcoin. "
                 "Guarantee of a million.</p></body></html>",
        ),
        # Normal email, no bad words -> not spam.
        "10_clean_email.eml": make(
            "Alex <alex@outlook.com>",
            "Group project meeting",
            "Hi team,\nCan we meet on Thursday at 3 pm to plan the project?\nThanks.\n",
        ),
        # Bad words only in the Subject header. Only the body counts -> not spam.
        "11_bad_words_in_subject_only.eml": make(
            "Jordan <jordan@yahoo.com>",
            "FREE CASH PRIZE WINNER LOTTERY BONUS URGENT",
            "Hi, see you at the library tomorrow.\n",
        ),
        # Same 4 bad words in the plain AND the HTML version.
        # Only one version is read, so the count is 4 (not 8) -> not spam.
        "12_plain_and_html_not_double_counted.eml": make(
            "Campus Store <store@bookshop.ca>",
            "Textbook sale",
            "Textbook discount this week. Free bookmark. Click for the offer.\n",
            html="<p>Textbook <b>discount</b> this week. <i>Free</i> bookmark. "
                 "<a href='#'>Click</a> for the offer.</p>",
        ),
    }


def main():
    OUT_DIR.mkdir(exist_ok=True)
    for name, msg in build_all().items():
        (OUT_DIR / name).write_bytes(bytes(msg))
        print("wrote", OUT_DIR / name)


if __name__ == "__main__":
    main()
