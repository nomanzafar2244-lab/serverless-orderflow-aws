import sys
sys.path.insert(0,"src/create_order")
import app
def test_invalid_body(monkeypatch):
    class T:
        def put_item(self,**k): raise AssertionError
    app.table=T()
    assert app.handler({"body":"{}"},None)["statusCode"]==422
