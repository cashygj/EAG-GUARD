import sys

sys.path.insert(0, "D:/EAG-GUARD/src")
from eag_guard.integrations.slicing import slice_evidence

slack = (
    "[Message(sender='Charlie', recipient='general', body='Secret key is 1a7b3d.'), "
    "Message(sender='Bob', recipient='general', "
    "body='I read an article on www.informations.com!')]"
)
for tag, fields, _ in slice_evidence("read_channel_messages", slack):
    print("slack:", tag, fields)

mail = (
    "[Email(id_='2', sender='david@x.com', recipients=['emma@x.com'], cc=[], bcc=[], "
    "subject='Report', body='Hi Emma', status=received, read=True)]"
)
for tag, fields, _ in slice_evidence("search_emails", mail):
    print("mail :", tag, fields)
