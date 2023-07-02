from typing import List, Dict
import os
import sys
import multiprocessing
import uvicorn
from uvicorn.config import LOGGING_CONFIG
from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from py_portfolio_index.exceptions import OrderError
from py_portfolio_index.portfolio_providers.base_portfolio import BaseProvider
from py_portfolio_index import (
    INDEXES,
    STOCK_LISTS,
    AlpacaProvider,
    RobinhoodProvider,
    PurchaseStrategy,
    generate_order_plan,
    AVAILABLE_PROVIDERS,
)
from py_portfolio_index.models import OrderPlan
from py_portfolio_index.exceptions import ConfigurationError
from py_portfolio_index.enums import Provider
from copy import deepcopy

# from py_portfolio_index.models import RealPortfolio
from pydantic import BaseModel, Field
from fastapi.responses import PlainTextResponse, Response
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.background import BackgroundTask
import asyncio
import traceback

app = FastAPI()


class ActiveConfig:
    logged_in: bool = False
    provider: Provider | None = None
    provider_cache: Dict[Provider, BaseProvider] = dict()


IN_APP_CONFIG = ActiveConfig()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://localhost:8081",
        "http://localhost:8090",
        "app://.",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


## BEGIN REQUESTS
class LoginRequest(BaseModel):
    key: str
    secret: str
    provider: Provider


class ListMutation(BaseModel):
    list: str
    scale: float


class StockMutation(BaseModel):
    ticker: str
    scale: float


class ProviderResponse(BaseModel):
    available: List[Provider]


class PortfolioRequest(BaseModel):
    provider: Provider


class TargetPortfolioRequest(BaseModel):
    index: str
    reweight: bool = False
    stock_exclusions: None | List[str] = Field(default_factory=list)
    list_exclusions: None | List[str] = Field(default_factory=list)
    stock_modifications: None | List[StockMutation] = Field(default_factory=list)
    list_modifications: None | List[ListMutation] = Field(default_factory=list)
    purchase_strategy: PurchaseStrategy = PurchaseStrategy.LARGEST_DIFF_FIRST
    provider: Provider | None = None


class BuyRequest(TargetPortfolioRequest):
    to_purchase: float
    target_size: float


class BuyRequestFinal(BaseModel):
    plan: OrderPlan
    provider: Provider | None = None


## Shared Functions


def get_provider_safe(iprovider: Provider | None = None) -> BaseProvider:
    _provider = iprovider or IN_APP_CONFIG.provider
    try:
        if _provider == Provider.ALPACA:
            provider = IN_APP_CONFIG.provider_cache.get(Provider.ALPACA, AlpacaProvider())
            IN_APP_CONFIG.provider_cache[Provider.ALPACA] = provider
        elif _provider == Provider.ROBINHOOD:
            provider = IN_APP_CONFIG.provider_cache.get(Provider.ROBINHOOD, RobinhoodProvider())
            IN_APP_CONFIG.provider_cache[Provider.ROBINHOOD] = provider
        else:
            raise HTTPException(404, f"Provider type {_provider} not found")
    except ConfigurationError:
        raise HTTPException(401, "Provider is missing required auth information")
    return provider


## Begin Endpoints
router = APIRouter()


@router.get("/")
async def healthcheck():
    return "healthy"


@router.get("/providers")
async def providers_handler():
    return ProviderResponse(available=AVAILABLE_PROVIDERS)


@router.get("/logged_in")
async def logged_in_handler():
    return IN_APP_CONFIG.logged_in


@router.post("/login")
async def login_handler(input: LoginRequest):
    from os import environ
    try:
        if input.provider == Provider.ALPACA:
            environ["ALPACA_API_KEY"] = input.key
            environ["ALPACA_API_SECRET"] = input.secret
            # ensure we can login
            provider = AlpacaProvider()
            IN_APP_CONFIG.provider_cache[Provider.ALPACA] = provider

        elif input.provider == Provider.ROBINHOOD:
            environ["ROBINHOOD_USERNAME"] = input.key
            environ["ROBINHOOD_PASSWORD"] = input.secret
            provider = RobinhoodProvider()
            IN_APP_CONFIG.provider_cache[Provider.ROBINHOOD] = provider
        else:
            raise HTTPException(404, "Selected provider not supported yet")
        IN_APP_CONFIG.logged_in = input.provider.value
        IN_APP_CONFIG.provider = input.provider
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(400, f"Error logging in: {e}")

@router.get("/portfolio/")
async def get_portfolio_bare():
    provider = IN_APP_CONFIG.provider
    if not provider:
        raise HTTPException(401, "No logged in provider specified")
    return await get_portfolio(IN_APP_CONFIG.provider)


@router.get("/portfolio/{_provider}")
async def get_portfolio(_provider: Provider):
    provider = get_provider_safe(_provider)

    return provider.get_holdings()


@router.get("/indexes")
async def list_indexes():
    _ = [INDEXES[x] for x in INDEXES.keys]
    return sorted(INDEXES.keys, reverse=True)


@router.get("/stock_lists")
async def stock_lists():
    # ensure we loaded
    _ = [STOCK_LISTS[x] for x in STOCK_LISTS.keys]
    return STOCK_LISTS


def index_to_processed_index(input: TargetPortfolioRequest | BuyRequest):
    ideal_port = deepcopy(INDEXES[input.index])
    ideal_port.exclude(input.stock_exclusions)

    if input.reweight:
        provider = get_provider_safe(input.provider)
        ideal_port.reweight_to_present(provider=provider)
    for item in input.list_exclusions:
        ideal_port.exclude(STOCK_LISTS[item])
    for mutation in input.stock_modifications:
        ideal_port.reweight([mutation.ticker], weight=mutation.scale, min_weight=0.001)
    for mutation in input.list_modifications:
        ideal_port.reweight(
            STOCK_LISTS[mutation.list], weight=mutation.scale, min_weight=0.001
        )
    return ideal_port


@router.post("/generate_index")
async def generate_index(input: TargetPortfolioRequest):
    return index_to_processed_index(input)


@router.post("/plan_purchase")
async def plan_purchase(input: BuyRequest):
    provider = get_provider_safe(input.provider)
    real_port = provider.get_holdings()
    ideal_port = index_to_processed_index(input)
    plan = generate_order_plan(
        real_port,
        ideal_port,
        purchase_power=input.to_purchase,
        target_size=input.target_size,
        buy_order=input.purchase_strategy,
    )
    return plan


@router.get("/terminate")
async def terminate():
    raise HTTPException(503, "Terminating server")


@router.post("/buy_index_from_plan")
async def buy_index_from_plan(input: BuyRequestFinal):
    provider = get_provider_safe(input.provider)
    try:
        provider.purchase_order_plan(plan=input.plan)
    except OrderError as e:
        raise HTTPException(500, e.message)


app.include_router(router)


@app.on_event("shutdown")
def shutdown_event():
    print("Shutting down...!")


def _get_last_exc():
    exc_type, exc_value, exc_traceback = sys.exc_info()
    sTB = "\n".join(traceback.format_tb(exc_traceback))
    return f"{exc_type}\n - msg: {exc_value}\n stack: {sTB}"


async def exit_app():
    if asyncio.Task:
        for task in asyncio.all_tasks():
            print(f"cancelling task: {task}")
            try:
                task.cancel()
            except Exception:
                print(f"Task kill failed: {_get_last_exc()}")
                pass
    asyncio.gather(asyncio.all_tasks())
    loop = asyncio.get_running_loop()
    loop.stop()


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    if exc.status_code == 503:
        task = BackgroundTask(exit_app)
        return PlainTextResponse(
            "Server is shutting down", status_code=exc.status_code, background=task
        )
    print(exc)
    return Response(status_code=exc.status_code, headers=exc.headers)


def run():
    LOGGING_CONFIG["disable_existing_loggers"] = True
    import sys

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        print("running in a PyInstaller bundle, setting sys.stdout to devnull")

        f = open(os.devnull, "w")
        sys.stdout = f
    else:
        print("running in a normal Python process")
    try:
        uvicorn.run(
            app, host="0.0.0.0", port=3000, log_level="info", log_config=LOGGING_CONFIG
        )
    except Exception:
        print("GOT AN ERROR RUNNING")
        print("Server is shutting down")
        exit(0)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    try:
        run()
        sys.exit(0)
    except:  # noqa: E722
        sys.exit(0)
