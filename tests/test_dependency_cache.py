from fastapi import APIRouter, Depends, FastAPI, Security
from fastapi.testclient import TestClient

app = FastAPI()

counter_holder = {"counter": 0}


async def dep_counter():
    counter_holder["counter"] += 1
    return counter_holder["counter"]


async def super_dep(count: int = Depends(dep_counter)):
    return count


@app.get("/counter/")
async def get_counter(count: int = Depends(dep_counter)):
    return {"counter": count}


@app.get("/sub-counter/")
async def get_sub_counter(
    subcount: int = Depends(super_dep), count: int = Depends(dep_counter)
):
    return {"counter": count, "subcounter": subcount}


@app.get("/sub-counter-no-cache/")
async def get_sub_counter_no_cache(
    subcount: int = Depends(super_dep),
    count: int = Depends(dep_counter, use_cache=False),
):
    return {"counter": count, "subcounter": subcount}


@app.get("/scope-counter")
async def get_scope_counter(
    count: int = Security(dep_counter),
    scope_count_1: int = Security(dep_counter, scopes=["scope"]),
    scope_count_2: int = Security(dep_counter, scopes=["scope"]),
):
    return {
        "counter": count,
        "scope_counter_1": scope_count_1,
        "scope_counter_2": scope_count_2,
    }


@app.get(
    "/parameterless-no-cache/",
    dependencies=[Depends(dep_counter), Depends(dep_counter, use_cache=False)],
)
async def get_parameterless_no_cache():
    return {"counter": counter_holder["counter"]}


@app.get(
    "/parameterless-security-no-cache/",
    dependencies=[Security(dep_counter), Security(dep_counter, use_cache=False)],
)
async def get_parameterless_security_no_cache():
    return {"counter": counter_holder["counter"]}


router = APIRouter(dependencies=[Depends(dep_counter)])


@router.get(
    "/router-parameterless-no-cache/",
    dependencies=[Depends(dep_counter, use_cache=False)],
)
async def get_router_parameterless_no_cache():
    return {"counter": counter_holder["counter"]}


app.include_router(router)


client = TestClient(app)


def test_normal_counter():
    counter_holder["counter"] = 0
    response = client.get("/counter/")
    assert response.status_code == 200, response.text
    assert response.json() == {"counter": 1}
    response = client.get("/counter/")
    assert response.status_code == 200, response.text
    assert response.json() == {"counter": 2}


def test_sub_counter():
    counter_holder["counter"] = 0
    response = client.get("/sub-counter/")
    assert response.status_code == 200, response.text
    assert response.json() == {"counter": 1, "subcounter": 1}
    response = client.get("/sub-counter/")
    assert response.status_code == 200, response.text
    assert response.json() == {"counter": 2, "subcounter": 2}


def test_sub_counter_no_cache():
    counter_holder["counter"] = 0
    response = client.get("/sub-counter-no-cache/")
    assert response.status_code == 200, response.text
    assert response.json() == {"counter": 2, "subcounter": 1}
    response = client.get("/sub-counter-no-cache/")
    assert response.status_code == 200, response.text
    assert response.json() == {"counter": 4, "subcounter": 3}


def test_security_cache():
    counter_holder["counter"] = 0
    response = client.get("/scope-counter/")
    assert response.status_code == 200, response.text
    assert response.json() == {"counter": 1, "scope_counter_1": 2, "scope_counter_2": 2}
    response = client.get("/scope-counter/")
    assert response.status_code == 200, response.text
    assert response.json() == {"counter": 3, "scope_counter_1": 4, "scope_counter_2": 4}


def test_parameterless_no_cache():
    counter_holder["counter"] = 0
    response = client.get("/parameterless-no-cache/")
    assert response.status_code == 200, response.text
    assert response.json() == {"counter": 2}
    response = client.get("/parameterless-no-cache/")
    assert response.status_code == 200, response.text
    assert response.json() == {"counter": 4}


def test_parameterless_security_no_cache():
    counter_holder["counter"] = 0
    response = client.get("/parameterless-security-no-cache/")
    assert response.status_code == 200, response.text
    assert response.json() == {"counter": 2}
    response = client.get("/parameterless-security-no-cache/")
    assert response.status_code == 200, response.text
    assert response.json() == {"counter": 4}


def test_router_parameterless_no_cache():
    counter_holder["counter"] = 0
    response = client.get("/router-parameterless-no-cache/")
    assert response.status_code == 200, response.text
    assert response.json() == {"counter": 2}
    response = client.get("/router-parameterless-no-cache/")
    assert response.status_code == 200, response.text
    assert response.json() == {"counter": 4}
