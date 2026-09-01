reference: https://www.datacamp.com/tutorial/python-uv?utm_cid=23781701478&utm_aid=196565213035&utm_campaign=260417_1-ps-dscia~amx-tofu~python_2-b2c_3-emea_4-prc_5-na_6-na_7-le_8-pdsh-go_9-nb-e_10-na_11-na&utm_loc=9063678-&utm_mtd=p-c&utm_kw=python%20uv&utm_source=google&utm_medium=paid_search&utm_content=ps-dscia~emea-en~amx~tofu~tutorial~python&gad_source=1&gad_campaignid=23781701478&gbraid=0AAAAADQ9WsHBM3dnw-wNX_Oez6WjMQWzX&gclid=Cj0KCQjw7eXTBhDBARIsAKF-w47IAcjVZ3lvFZbFhpwAGCP0Bud-zv7yr6aAXv0c7rUcmpUgT5KpKecaAq5CEALw_wcB


step 1: execute with curl -LsSf https://astral.sh/uv/install.sh | sh
step 1.1: Optionally update uv with: uv self update
step 2: check if the installation was successful: uv self version
step 3: add command line completion to shell (zsh): echo 'eval "$(uv generate-shell-completion zsh)"' >> ~/.zshrc
step 4: create a project in the PWD/CWD using init: uv init fastapi-hw --no-package
step 5: add fastapi to the project: uv add "fastapi[standard]" (note the creation of the .venv)
step 6: insert the following into the main.py file:
'''
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def read_root():
    return {"Hello": "World"}
'''


step 7: run the code by; uv run fastapi dev
step 8: explain the code and show the results


