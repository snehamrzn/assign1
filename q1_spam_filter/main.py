"""
Run the spam filter on the sample emails.

    python q1_spam_filter/main.py
"""

import shutil

from spam_agent import HERE, make_agent, run_agent


def main():
    inbox_folder = HERE / "inbox"
    spam_folder = HERE / "spam"
    email_folder = HERE / "email"

    # Start clean, then copy the sample emails into the inbox.
    for folder in (inbox_folder, spam_folder, email_folder):
        shutil.rmtree(folder, ignore_errors=True)
    inbox_folder.mkdir(parents=True)
    sample_folder = HERE / "test_data"
    for sample_email in sorted(sample_folder.glob("*.eml")):
        shutil.copy2(sample_email, inbox_folder / sample_email.name)

    agent = make_agent(HERE)
    sorted_emails = run_agent(agent, inbox_folder, spam_folder, email_folder)

    print("FILE  DOMAIN  BAD WORDS  ACTION  RULE")
    spam_count = 0
    for file_name, action, rule_name, email_info in sorted_emails:
        print(
            file_name,
            email_info.sender_domain,
            email_info.bad_word_count,
            action,
            rule_name,
        )
        if action == "SPAM":
            spam_count = spam_count + 1
    normal_count = len(sorted_emails) - spam_count
    print(f"\n{len(sorted_emails)} emails: {spam_count} -> {spam_folder}, "
          f"{normal_count} -> {email_folder}")


if __name__ == "__main__":
    main()
