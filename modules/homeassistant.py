from json import loads
from re import compile

import urllib3
from requests import get

from basemod import BaseModule

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
        try:
            states_dict = sorted(loads(get(self.url, headers=self.headers, verify=False).text), key = lambda o: o["entity_id"])
        except ConnectionError as e:
            return e.strerror

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
                out_str += f"{fname:<{w}}{'  '.join(states)}\n"

        return out_str

    
widget = HomeAssistant



