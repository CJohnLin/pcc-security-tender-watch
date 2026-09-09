import base64
import email

from pcc_tender_watch import gmail_draft


def test_build_raw_message_includes_recipients_and_attachment(tmp_path):
    attachment = tmp_path / "report.html"
    attachment.write_text("<html><body>hi</body></html>", encoding="utf-8")

    raw = gmail_draft._build_raw_message(
        to=["peggy.wu@rehfeldt.org"],
        cc=["supportlf@rehfeldt.org"],
        subject="SEP09 Tender Research",
        body_text="Hi Peggy:\nHere is the list.",
        attachment_path=str(attachment),
    )

    decoded = base64.urlsafe_b64decode(raw.encode("ascii"))
    msg = email.message_from_bytes(decoded)

    assert msg["To"] == "peggy.wu@rehfeldt.org"
    assert msg["Cc"] == "supportlf@rehfeldt.org"
    assert msg["Subject"] == "SEP09 Tender Research"

    filenames = [part.get_filename() for part in msg.walk() if part.get_filename()]
    assert filenames == ["report.html"]
