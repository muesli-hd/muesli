# -*- coding: utf-8 -*-
#
# muesli/email.py
#
# This file is part of MUESLI.
#
# Copyright (C) 2011, Matthias Kuemmerer <matthias (at) matthias-k.org>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.



import mimetypes

from email import encoders
from email.message import Message
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.message import MIMEMessage
from email.utils import parseaddr, formataddr

import smtplib

testing = False

# To be overwritten by value from config file
server = 'localhost'

"""Code adapted from http://docs.python.org/library/email-examples.html"""
def createAttachment(filename, data):
    # Guess the content type based on the file's extension.  Encoding
    # will be ignored, although we should check for simple things like
    # gzip'd or compressed files.
    ctype, encoding = mimetypes.guess_type(filename)
    if ctype is None or encoding is not None:
        # No guess could be made, or the file is encoded (compressed), so
        # use a generic bag-of-bits type.
        ctype = 'application/octet-stream'
    maintype, subtype = ctype.split('/', 1)
    if maintype == 'text':
        # Note: we should handle calculating the charset
        msg = MIMEText(data.read(), _subtype=subtype)
    elif maintype == 'image':
        msg = MIMEImage(data.read(), _subtype=subtype)
    elif maintype == 'audio':
        msg = MIMEAudio(data.read(), _subtype=subtype)
    else:
        msg = MIMEBase(maintype, subtype)
        msg.set_payload(data.read())
        # Encode the payload using Base64
        encoders.encode_base64(msg)
    # Set the filename parameter
    msg.add_header('Content-Disposition', 'attachment', filename=filename)
    return msg

class Message:
    def __init__(self, subject=None, sender=None, to=None, cc=None, bcc=None, body=None):
        COMMASPACE = ', '
        self.subject = subject
        self.sender = sender
        self.to = to or []
        self.cc = cc or []
        self.bcc = bcc or []
        self.body = body
        self.outer = MIMEMultipart()
        self.outer['Subject'] = self.subject
        self.outer['From'] = formataddr(parseaddr(self.sender))
        self.outer['To'] = ', '.join(self.to)
        self.outer['Cc'] = ', '.join(self.cc)
        self.outer['Bcc'] = ', '.join(self.bcc)
        self.outer.attach(MIMEText(self.body, 'plain', 'utf-8'))
    @property
    def send_to(self):
        return set(self.to) | set(self.cc) | set(self.bcc)
    def as_string(self):
        return self.outer.as_string()
    def attach(self, filename, data=None):
        data = data or open(filename)
        self.outer.attach(createAttachment(filename, data))

def sendMail(message, request=None):
    s = smtplib.SMTP(server)
    if not testing:
        try:
            s.sendmail(message.sender, message.send_to, message.as_string())
        except smtplib.SMTPSenderRefused as e:
            if request:
                request.session.flash(e[1], queue='errors')
            raise
    s.quit()
