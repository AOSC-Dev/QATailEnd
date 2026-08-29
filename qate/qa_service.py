import json

from pydantic_client import RequestsWebClient, post, put
from models.models import QARequestBuilds,QAResponse


class QAAPIClient(RequestsWebClient):
    def __init__(self, url,token):
        super().__init__(
            base_url=url,
            headers={
                'Authorization':f"Bearer {token}"
            }
        )

    @post("/api/v1/builds")
    def add_build(self, body: QARequestBuilds) -> QAResponse:
        pass

    def upload_log(self, id: int, file) -> QAResponse:
        with open(file, 'rb') as file_reader:
            response = self.session.put(self._make_url(f"/api/v1/builds/{id}/logs"),
                                        headers=self.headers,
                                        files={'file': (f"{id}.log", file_reader , "application/octet-stream")})
            response.raise_for_status()
            response_str = response.content.decode()
            return QAResponse.model_validate_json(response_str)
