import sys
sys.path.append('/home/team-3/UbiYagami/python')
import data_type
import json
import pysnooper


def convert_obj2msg(obj):
    msg_content = json.dumps(obj.to_dict()).encode()
    msg_type = type(obj).__name__.encode()
    return msg_type+ b'#'+ msg_content

def convert_msg2obj(msg):
    msg_type, msg_content = [x.decode() for x in msg.split(b'#')]
    msg_content = json.loads(msg_content)
    obj = getattr(data_type, msg_type)(**msg_content)
    return obj