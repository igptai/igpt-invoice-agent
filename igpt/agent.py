from igptai import IGPT
from typing import Optional
from .prompts import SYSTEM_PROMPT
from .schema import OUTPUT_FORMAT



class IgptAgent:
    def __init__(self, api_key: Optional[str] = None, user: Optional[str] = None): 
        self.client = IGPT(api_key=api_key, user=user)

    def run(self) -> dict:
        ds_resp = self.client.datasources.list()
        if ds_resp.get("error"):
            return ds_resp
        elif not ds_resp.get("datasources"):
            connect = self.client.connectors.authorize(service="spike", scope="messages")
            if connect.get("error"):
                return connect
            else:
                return {"error":  f"No datasources found. Open this URL to authorize: {connect.get('url')}"}


        return self.client.recall.ask(input=SYSTEM_PROMPT, quality="cef-1-normal", output_format=OUTPUT_FORMAT)

