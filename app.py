from igpt import IgptAgent
import getpass
import os
from pprint import pprint

if not os.environ.get("IGPT_API_KEY"):
    os.environ["IGPT_API_KEY"] = getpass.getpass("IGPT API KEY:\n")

if not os.environ.get("IGPT_API_USER"):
    os.environ["IGPT_API_USER"] = getpass.getpass("IGPT API USER:\n")

agent = IgptAgent(user=os.getenv("IGPT_API_USER"), api_key=os.getenv("IGPT_API_KEY"))

data = agent.run()
if data.get("error"):
    print(data)
else:
    pprint(data["output"], sort_dicts=False)