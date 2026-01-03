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

from email import encoders
from email.message import Message
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
    _SENDER_EMAIL_ADDRESS: str = "SENDER_EMAIL_ADDRESS"
    _GOOGLE_SMTP_APP_PASS: str = "GOOGLE_SMTP_APP_PASS"

    def __init__(self) -> None:
        self._cfg: SMTPConfig = SMTPConfig(
            sender_email_address=os.getenv(self._SENDER_EMAIL_ADDRESS, ""),
            google_smtp_app_passwd=os.getenv(self._GOOGLE_SMTP_APP_PASS, ""),
        )

        self._message: MIMEMultipart = MIMEMultipart(MIMESemantics.MULTIPART_ENTRY)
    
    def __post_init__(self) -> None:
        if self._cfg.sender_email_address is None:
            raise ValueError(f"SMTPClient: Could Not Find sender_email_address; {self._cfg.sender_email_address}")
        
        if self._cfg.google_smtp_app_passwd is None:
            raise ValueError("SMTPClient: Could Not find Google SMTP Server Passwd")

    def _init_MIMEMultipart_email( 
            self,
            subject: str, 
            destination_email_address: str,
            plain_text_body: str,
            html_body: str,
        ) -> None:
        """
        Create an email with a plain text and HTML semantics. The HTML Version
          always be attempted first, with the plain text as a fallback.

        :param subject: The Subject of the Email
        :param destination_email_address: The Received Party
        :param plain_text_body: The Plain text version of the Email
        :param html_body: The HTML Contents of the Email
        """
        if not plain_text_body:
            raise RunTimeError("Must Specify a plain text alternative to Email Contents")
        
        if not html_body:
            raise RuntTimeError("Must Specify a HTML body to Email Contents") 
        
        if not subject: 
            raise RuntTimeError("Must Specify subject in Email Contents")

        if not self._message:
            self._message = MIMEMultipart(MIMESemantics.MULTIPART_ENTRY)

        self._message[MIMESemantics.SUBJECT] = subject
        self._message[MIMESemantics.FROM] = self._cfg.sender_email_address
        self._message[MIMESemantics.TO] = destination_email_address

        text_part = MIMEText(plain_text_body, MIMESemantics.PLAIN_TEXT)
        html_part = MIMEText(html_body, MIMESemantics.HTML)

        # Adding the html alternative last, server will render last one first.
        self._message.attach(text_part)
        self._message.attach(html_part)

    def _add_attachments(self, files: list[Path]) -> None:
        """
        Add attachments to the instance's message. 
        Encode the file into ASCII Chars.
        
        Raises FileNotFoundError.

        :param: List of file Path objects 
        """
        for file in files:
            if not file.exists():
                raise FileNotFoundError(f"Could not find file: {file}")
                continue

            with open(file, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())

            encoders.encode_base64(part)
            part.add_header(
                "Content",
                f"attachment; filename = {str(file)}"
            )

            self._message.attach(part)

    def send_email(self, email_contents: EmailMessage) -> bool:
        """
        Create a MIME Email with plain text and html versions. 
        Connect to a SMTP Server (In this case: Gmail SMTP) through SSL.

        Raises SMTP Connection, Authentication

        """
        if not email_contents:
            raise SMTPEmailException("Must Specify Message Contents for Mail Transfer")

        self._init_MIMEMultipart_email(
            subject=email_contents.subject,
            destination_email_address=email_contents.destination_email_address,
            plain_text_body=email_contents.plain_text_body,
            html_body=email_contents.html_body,
        )

        # Add as many attachments to the email
        if email_contents.attachments:
            self._add_attachments(email_contents.attachments)
        
        try:
            with smtplib.SMTP_SSL(self._cfg.smtp_server, self._cfg.smtp_port, context=ssl.create_default_context()) as smtp_server:
                smtp_server.login(self._cfg.sender_email_address, self._cfg.google_smtp_app_passwd)
                smtp_server.sendmail(
                    self._cfg.sender_email_address, receiver_email, message.as_string()
                )
        
        # TODO: Get all of these in the logger when complete
        except smtplib.SMTPConnectError as e:
            print(f"Error Connecting to server. {type(e)}: {e}")
        except smtplib.SMTPAuthenticationError as e:
            print(f"Error with Server Auth. {type(e)}: {e}")
        except smtplib.SMTPSenderRefused as e:
            print(f"Sender Email Address Refused to comply. {type(e)}: {e}")
        except smtplib.SMTPException as e: 
            print(f"Error with SMTP Operation. {type(e)}: {e}")
        except Exception as e:
            print(f"Exception raised in SMTPClient.send_email() instance. {e}")

    def test_connection(self) -> bool:
        """ Python documentation has the .noop()"""
        pass



class EmailClient:
    """ 
    
    High-level Email sender class. Dependency Injection and whatnot

    Better yet, derive dependency injection from first principles.

    Composition with EmailMessage, SMTPClient class 
    
    
    """
    def __init__(self) -> None:
        self._client: SMTPClient = SMTPClient()

    def __post_init__(self) -> None:
        pass


    def send_email(self, email_message: EmailMessage) -> bool:
        """ 
        Title

        """
        self._client.send_email(email_message)


if __name__ == "__main__":
    # Prototype Function
    # TODO: 
    # Test Cases to cover with pytest:
    #   - One email to one address
    #   - Multiple Emails to many emails
    #   - Multiple Emails to one email
    #   - One email to many
    #
    my_email_contents: EmailMessage = EmailMessage(
        destination_email_address="jsamis311@gmail.com",
        subject="Example Test Subject",
        plain_text_body="Test Email",
        html_body="""\
        <html>
          <body>
            <p>Test Email<br>
                Test Automatic Email Sending<br>
            <a href="https://docs.python.org/3/library/smtplib.html#smtp-objects">smptlib python stdlib</a> 
            Is the source of Truth!
            </p>
          </body>
        </html>
        """,
        attachments=[Path("test_attachment.txt")],
    )

    manasi_email_contents: EmailMessage = EmailMessage(
        destination_email_address="manasi.pande@ottawa.ca",
        subject="Example Subject",
        plain_text_body="Test Email",
        html_body="""\
        <html>
          <body>
            <p>Te<br>
                Test Automatic Email Sending<br>
            <a href="https://docs.python.org/3/library/smtplib.html#smtp-objects">smptlib python stdlib</a> 
            Is the source of Truth!
            </p>
          </body>
        </html>
        """,
        attachments=[Path("test_attachment.txt")],
    )

    my_client = EmailClient()

    # Currently Getting auth errors (good error handling yay!)
    # It should work on my own device however.
    # This is due to the google app passwd being device specific... will need to look into how to overcome.

    print("=============================")
    print("       Start SMTP test       ")
    print("=============================")


    if not my_client.send_email(my_email_contents):
        print("Email to myself falied")
    else:
        print("Email to Myself PASS")

    if not my_client.send_email(manasi_email_contents):
        print("Email to manasi failed")
    else:
        print("Email to Manasi PASS")

    print("=============================")
    print("       END SMTP test         ")
    print("=============================")



    a = [1, 2, 3]

    if a:
        print("a has stuff")
    if not a:
        print("a is empty")
    else:
        print("a is not empty")
    
    