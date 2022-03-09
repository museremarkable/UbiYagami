from dataclasses import dataclass
from enum import Enum

@dataclass
class OrderTick:
    # msg first arrivet ime
    timestamp: int
    timestamp1: int
    timestamp2: int
    timestamp3: int
    # eg:000001.sz
    symbol: str

    # exchagne info

    TradingDay: str
    # 2 exchange
    ExchangeId: str
    ExchagneInstID: str
    InstrumentID: str
    UpdateTime: str
    UpdateMillisec:int
    LastPrice: float
    PreSettlementPrice: float
    PreClosePrice: float
    PreOpenPrice: float
    OpenPrice: float
    HighestPrice: float
    LowestPrice: float
    Volume: float
    Turnover: float


class OrderBookType(Enum):
    BID = 0
    ASK = 1

class OrderStatusType(Enum):
    CREATED = 'CREATED'
    PENDING = 'PENDING'
    FILLING = 'FILLING'
    FILLED = 'FILLED'
    CANCELLED = 'CANCELLED'
    REJECTED = 'REJECTED'
    UNKNOWN = 'UNKNOWN'

class OrderDirectionType(Enum):
    BUY = 'BUY'
    SELL = 'SELL'



@dataclass
class OrderSent:
    timestamp: int
    nonce: str
    symbol: str
    id: int


@dataclass
class OrderSentFail:
    timestamp: int
    nonce: str
    symbol: str
    e: str


@dataclass
class SymbolFrozen:
    symbol: str


@dataclass
class Termination:
    message: str


@dataclass
class Fill:
    timestamp: int
    nonce: str
    symbol: str
    price: float
    quantity: float
    amount: float
    commission: float
    direction: OrderDirectionType


@dataclass
class Cancel:
    timestamp: int
    nonce: str
    symbol: str
    quantity: float
    direction: OrderDirectionType
