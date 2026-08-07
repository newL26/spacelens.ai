from ibm_watsonx_ai import Credentials
from ibm_watsonx_ai.foundation_models import Model

credentials = Credentials(
    url="https://eu-de.ml.cloud.ibm.com",
    api_key="ngkEGhhQnxm1bD3DKKN5YAkgSCvM1X03LjKjwLK68rI6"
)

model = Model(
    model_id="ibm/granite-4-h-small",
    credentials=credentials,
    project_id="86282315-ea95-4fa5-9dff-10de2d911b09"
)

response = model.generate_text("Hello!")
print(response)