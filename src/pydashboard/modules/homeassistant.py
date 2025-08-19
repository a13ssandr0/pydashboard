from json import JSONDecodeError
from re import compile
from typing import Any

import urllib3
from requests import get
from requests.exceptions import ConnectionError

from pydashboard.containers import BaseModule

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def color_state(state):
    match state.lower():
        case "on":
            return "[green]ON [/green]"
        case "off":
            return "[blue]OFF[/blue]"
        case "unavailable":
            return "[red]N/A[/red]"
        case _:
            return state


class HomeAssistant(BaseModule):
    def __init__(self, *, host: str, token: str, filters: list[str], port: int = 8123, scheme: str = 'https',
                 **kwargs: Any):
        """

        Args:
            host: HomeAssistant server IP or FQDN
            token: HomeAssistant API token
            filters: RegEx string to filter entities
            port: HomeAssistant server port
            scheme: http or https
            **kwargs: See [BaseModule](../containers/basemodule.md)

        # Example filters
        ```title="Show all lights"
        light\\.
        ```
        ```title="Show all lights except hidden ones"
        light\\.(?!.*_hidden$).*
        ```
        ```title="Show all binary sensors with `switch` or `button` in their name"
        binary_sensor\\.(?:(?:switch)|(?:button))
        ```

        Filters must be enclosed in quotes and passed as a list:
        ```yaml
        homeassistant:
          host: ...
          token: ...
          filters: ["binary_sensor\\.(?:(?:switch)|(?:button))"]
        ```
        """
        super().__init__(host=host, token=token, filters=filters, port=port, scheme=scheme, **kwargs)
        self.host = host
        self.token = token
        self.filters = filters
        self.port = port
        self.scheme = scheme
        self.url = f'{scheme}://{host}:{port}/api/states'
        self.headers = {
            "Authorization": f"Bearer {token}",
            "content-type" : "application/json",
        }

    def __call__(self):
        try:
            response = get(self.url, headers=self.headers, verify=False)
            if response.status_code == 200:
                states_dict = sorted(response.json(), key=lambda o: o["entity_id"])
                out_str = ""

                for _filter in self.filters:
                    rexp = compile(_filter)

                    entities = []
                    w = 0

                    for ent in states_dict:
                        if rexp.match(ent["entity_id"]):
                            fname = ent['attributes']['friendly_name'].strip()
                            try:
                                int(fname.split()[-1])
                            except:
                                fname += " 1"
                            entities.append((fname, color_state(ent['state'])))
                            w = max(w, len(fname))

                    ent_dict = {}

                    for ent, state in entities:
                        fname = ' '.join(ent.split()[:-1])
                        if fname in ent_dict:
                            ent_dict[fname].append(state)
                        else:
                            ent_dict[fname] = [state]

                    for fname, states in ent_dict.items():
                        out_str += f"{fname:<{w}}{'  '.join(states)}\n"

                self.reset_settings('border_subtitle')
                self.reset_settings('styles.border_subtitle_color')

                return out_str

            else:
                self.border_subtitle = f'{response.status_code} {response.reason}'
                self.styles.border_subtitle_color = 'red'
                self.logger.error('Request returned status code {} - {}', response.status_code, response.reason)

        except ConnectionError as e:
            self.border_subtitle = f'ConnectionError'
            self.styles.border_subtitle_color = 'red'
            self.logger.critical(str(e))
        except JSONDecodeError as e:
            self.border_subtitle = f'JSONDecodeError'
            self.styles.border_subtitle_color = 'red'
            self.logger.critical(str(e))


widget = HomeAssistant
