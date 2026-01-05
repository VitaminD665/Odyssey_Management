"""
Module using the built-in smtp and email libraries to send automated
emails over gmail smtp. Using Google Mail as a smtp server with
pre-authorized credentials. Encryption via SSL


"""

import os
import smtplib
import ssl

from pathlib import Path
from enum import StrEnum
from dataclasses import dataclass, field

import mimetypes
from email import encoders
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart


class SMTPServerConfig(StrEnum):
    SMTP_SERVER= "smtp.gmail.com"
    SMTP_PORT= "465"
    SECURITY_CONTRACT = "SSL"  # Secure Sockets Layer


@dataclass(frozen=True)
class EmailMessage:
    """ Dictate the Contents of an email to send. Html injected via stdlib string """
    destination_email_address: str
    subject: str
    plain_text_body: str
    html_body: str
    attachments: list[Path]


class SMTPEmailException(Exception):
    """ Custom Exception for this Module """


class MIMESemantics(StrEnum):
    MULTIPART_ENTRY = "alternative"
    SUBJECT = "Subject"
    FROM = "From"
    TO = "To"
    PLAIN_TEXT = "plain"
    HTML = "html"
    MIXED = "mixed"


@dataclass(frozen=True)
class SMTPConfig:
    sender_email_address: str
    google_smtp_app_passwd: str
    smtp_server: str = field(default=SMTPServerConfig.SMTP_SERVER)
    smtp_port: str = field(default=SMTPServerConfig.SMTP_PORT)
    security_contract: str = field(default=SMTPServerConfig.SECURITY_CONTRACT)


class SMTPClient:
    """
    SMTP Client from smtplib. Using MIME (Multipart International Mail Extensions)
    Composed of SMTPConfig and related defaults.

    Also handles the email structure via MIMEMultipart. Fallback to plain text.

    Exposes: send_email() public method, see related docstring.

    """
    # The service account for the Odyssey Management Software, stored via ENV VARS
    _SENDER_EMAIL_ADDRESS: str = "ODYSSEY_EMAIL_ADDRESS"
    _GOOGLE_SMTP_APP_PASS: str = "GOOGLE_SMTP_APP_PASS"

    def __init__(self) -> None:
        self._cfg: SMTPConfig = SMTPConfig(
            sender_email_address=os.getenv(self._SENDER_EMAIL_ADDRESS, ""),
            google_smtp_app_passwd=os.getenv(self._GOOGLE_SMTP_APP_PASS, ""),
        )
        self._check_env_vars()
    
    def _check_env_vars(self) -> None:
        if self._cfg.sender_email_address is None:
            raise ValueError(f"SMTPClient: Could Not Find sender_email_address; {self._cfg.sender_email_address}")
        
        if self._cfg.google_smtp_app_passwd is None:
            raise ValueError("SMTPClient: Could Not find Google SMTP Server Passwd")

    def _build_email_message(
            self,
            email_contents: EmailMessage,
        ) -> MIMEMultipart:
        """
        Create an email with a plain text and HTML semantics. The HTML Version
          always be attempted first, with the plain text as a fallback.

        :param email_contents: The EmailMessage dataclass
        """

        def _add_attachments(msg: MIMEBase, files: list[Path]) -> None:
            """
            Add attachments to the instance's message.
            Encode the file into ASCII Chars.

            Raises FileNotFoundError.

            :param: List of file Path objects
            """
            for file in files:
                if not file.exists():
                    raise FileNotFoundError(f"Could not find file: {file}")

                ctype, encoding = mimetypes.guess_type(str(file))
                if ctype is None or encoding is not None:
                    ctype = "application/octet-stream"

                maintype, subtype = ctype.split("/", 1)
                with open(file, "rb") as f:
                    data = f.read()

                if maintype == "text":
                    part = MIMEText(data.decode("utf-8", errors="replace"), _subtype=subtype)
                else:
                    part = MIMEBase(maintype, subtype)
                    part.set_payload(data)
                    encoders.encode_base64(part)

                part.add_header("Content-Disposition", f'attachment; filename="{file.name}"')
                msg.attach(part)

        if not email_contents.plain_text_body:
            raise RuntimeError("Must Specify a plain text alternative to Email Contents")

        if not email_contents.html_body:
            raise RuntimeError("Must Specify a HTML body to Email Contents")

        if not email_contents.subject:
            raise RuntimeError("Must Specify subject in Email Contents")

        message = MIMEMultipart(MIMESemantics.MIXED)
        message[MIMESemantics.SUBJECT] = email_contents.subject
        message[MIMESemantics.FROM] = self._cfg.sender_email_address
        message[MIMESemantics.TO] = email_contents.destination_email_address

        # Adding the html alternative last, server will render last one first.
        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText(email_contents.plain_text_body, MIMESemantics.PLAIN_TEXT))
        alt.attach(MIMEText(email_contents.html_body, MIMESemantics.HTML))
        message.attach(alt)

        _add_attachments(message, email_contents.attachments)

        return message


    def send_email(self, email_contents: EmailMessage) -> bool:
        """
        Create a MIME Email with plain text and html versions. 
        Connect to an SMTP Server (In this case: Gmail SMTP) through SSL.

        Raises SMTP Connection, Authentication

        """
        if not email_contents:
            raise SMTPEmailException("Must Specify Message Contents for Mail Transfer")

        email = self._build_email_message(email_contents)
        try:
            with smtplib.SMTP_SSL(
                    self._cfg.smtp_server,
                    int(self._cfg.smtp_port),
                    context=ssl.create_default_context()) as smtp_server:
                smtp_server.login(self._cfg.sender_email_address, self._cfg.google_smtp_app_passwd)
                smtp_server.send_message(email)
            return True

        # TODO: Get all of these in the logger when complete
        except smtplib.SMTPConnectError as e:
            print(f"Error Connecting to server. {type(e)}: {e}")
            return False
        except smtplib.SMTPAuthenticationError as e:
            print(f"Error with Server Auth. {type(e)}: {e}")
            return False
        except smtplib.SMTPSenderRefused as e:
            print(f"Sender Email Address Refused to comply. {type(e)}: {e}")
            return False
        except smtplib.SMTPException as e:
            print(f"Error with SMTP Operation. {type(e)}: {e}")
            return False
        except Exception as e:
            print(f"Exception raised in SMTPClient.send_email() instance. {e}")
            return False

    def test_connection(self) -> bool:
        """ Python documentation has the .noop() to test connectivity?"""
        pass


class EmailClient:
    """ 
    High-level Email sender class. Dependency Injection and whatnot

    Better yet, derive dependency injection from first principles.
    Composition with EmailMessage, SMTPClient class 

    """
    def __init__(self) -> None:
        self._client: SMTPClient = SMTPClient()

    def send_email(self, email_message: EmailMessage) -> bool:
        """ Title """
        return True if self._client.send_email(email_message) else False
    



if __name__ == "__main__":
    # Prototype Function
    # TODO: 
    # Test Cases to cover with pytest:
    #   - One email to one address
    #   - Multiple Emails to many emails
    #   - Multiple Emails to one email
    #   - One email to many
    #
    EMAIL_ADDR1 = "jsamis311@gmail.com"
    EMAIL_ADDR2 = "jsamisrb@gmail.com"
    EMAIL_ADDR3: str ="nasso.samis@gmail.com"

    my_email_contents: EmailMessage = EmailMessage(
        destination_email_address=EMAIL_ADDR1,
        subject="[Odyssey Management] Automated Test Email Subject",
        plain_text_body="Test Email",
        html_body="""\
        <html>
          <body>
            <p>Testing Automatic Emails<br>
            Test Automatic Email Sending for tool expansion. This is an old attendance record. <br>
 
            Using Python's built-in SMTP library! for automated emails via google as a smtp server.
            <a href="https://docs.python.org/3/library/smtplib.html#smtp-objects">smptlib python stdlib</a>
            
            This will allow for HTML emails with attachments!<br>

            This is an Automated Email Sent from the Odyssey Management Software.
            </p>
          </body>
        </html>
        """,
        attachments=[Path("attendance_dec16.csv")],
    )

    other_email_contents: EmailMessage = EmailMessage(
        destination_email_address=EMAIL_ADDR2,
        subject="[Odyssey Management] Automated Test Email Subject",
        plain_text_body="Test Email",
        html_body="""\
        <html>
          <body>
            <p>Testing Automatic Emails<br>
            Test Automatic Email Sending for tool expansion. This is an old attendance record. <br>
 
            Using Python's built-in SMTP library! for automated emails via google as a smtp server.
            <a href="https://docs.python.org/3/library/smtplib.html#smtp-objects">smptlib python stdlib</a>
            
            This will allow for HTML emails with attachments!<br>

            This is an Automated Email Sent from the Odyssey Management Software.
            </p>
          </body>
        </html>
        """,
        attachments=[Path("attendance_dec16.csv")],
    )


    print("=============================")
    print("       Start SMTP test       ")
    print("=============================")

    my_client = EmailClient()

    if not my_client.send_email(my_email_contents):
        print(f"Email to {EMAIL_ADDR1} failed")
    else:
        print(f"Email to {EMAIL_ADDR1} PASS")

    if not my_client.send_email(other_email_contents):
        print(f"Email to {EMAIL_ADDR2} failed")
    else:
        print(f"Email to {EMAIL_ADDR2} PASS")

    print("=============================")
    print("       END SMTP test         ")
    print("=============================")
