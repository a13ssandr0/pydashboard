from requests import get
from json import loads
from sys import argv
from re import compile
from basemod import BaseModule
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def color_state(state):
    match state.lower():
        case "on":
            return "\033[0;32mON \033[0m"
        case "off":
            return "\033[0;34mOFF\033[0m"
        case "unavailable":
            return "\033[0;31mN/A\033[0m"
        case _:
            return state


# headers = {
#     "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJiZDUzOTQ0Yzg5YjE0ZjgxYjg2MTBlNGE5NDJiZjE1OSIsImlhdCI6MTcwMjkwMDg4NywiZXhwIjoyMDE4MjYwODg3fQ.usCnaZQ7kMXxJPaxN73X2AXTtqYMCVx-vQ7UvXwUyas",
#     "content-type": "application/json",
# }

# url = "https://192.168.1.5:8123/api/states"



class HomeAssistant(BaseModule):
    def __init__(self, *, host, token, filters:list[str], port=8123, scheme='https', **kwargs):
        self.host=host
        self.token=token
        self.filters=filters
        self.port=port
        self.scheme=scheme
        self.url = f'{scheme}://{host}:{port}/api/states'
        self.headers = {
            "Authorization": f"Bearer {token}",
            "content-type": "application/json",
        }
        super().__init__(**kwargs)
        
    def __run__(self):
        states_dict = sorted(loads(get(self.url, headers=self.headers, verify=False).text), key = lambda o: o["entity_id"])

        out_str = ""

        for filter in self.filters:
            rexp = compile(filter)

            entities = []
            w = 0

            # fname_numbers = compile(r"(\d*)$")


            for ent in states_dict:
                if rexp.match(ent["entity_id"]):
                    fname = ent['attributes']['friendly_name'].strip()
                    try:
                        int(fname.split()[-1])
                    except:
                        fname += " 1" 
                    entities.append((fname, color_state(ent['state'])))
                    w = max(w,len(fname))

            ent_dict = {}

            for ent, state in entities:
                fname = ' '.join(ent.split()[:-1])
                if fname in ent_dict:
                    ent_dict[fname].append(state)
                else:
                    ent_dict[fname] = [state]

            for fname, states in ent_dict.items():
                out_str += f"{fname:<{w}}{'  '.join(states)}"

        return out_str

    
widget = HomeAssistant


