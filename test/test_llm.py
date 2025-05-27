# import pytest
# from api.llm.agent import sql_chain

# @pytest.mark.asyncio
# async def test_sql_chain(monkeypatch):
#     class DummyLLM:
#         def __call__(self, *args, **kwargs):
#             return {"query": "SELECT 1;", "result": "1"}
#     monkeypatch.setattr("api.langchain_service.llm", DummyLLM())
#     output = sql_chain.run("Test?")
#     assert "1" in output