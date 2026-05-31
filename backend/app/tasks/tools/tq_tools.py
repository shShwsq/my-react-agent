import os
import time
import math
import asyncio
import logging
from typing import Any, Dict, Optional
from app.tasks.tools import BaseTool, ToolResult, tool_registry
from app.config import settings

logger = logging.getLogger(__name__)


def _get_tq_auth():
    from tqsdk import TqAuth
    account = getattr(settings, "TQ_ACCOUNT_NAME", "") or os.getenv("TQ_ACCOUNT_NAME", "")
    password = getattr(settings, "TQ_PASSWORD", "") or os.getenv("TQ_PASSWORD", "")
    if not account or not password:
        raise ValueError("天勤账户未配置，请在 .env 中设置 TQ_ACCOUNT_NAME 和 TQ_PASSWORD")
    return TqAuth(account, password)


def _sanitize_value(value: Any) -> Any:
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
    return value


def _quote_to_dict(quote: Any) -> Dict[str, Any]:
    def _safe(value: Any) -> Any:
        if isinstance(value, float) and math.isnan(value):
            return None
        return value

    def _get(attr: str, default=None):
        return getattr(quote, attr, default)

    trading_time_raw = _get('trading_time', None)
    if trading_time_raw is not None and hasattr(trading_time_raw, '__dict__') and not isinstance(trading_time_raw, (str, dict, list)):
        trading_time_raw = str(trading_time_raw)
    trading_time_raw = _safe(trading_time_raw)

    return {
        "datetime": _safe(_get('datetime')),
        "ask_price1": _safe(_get('ask_price1')),
        "ask_volume1": _safe(_get('ask_volume1')),
        "bid_price1": _safe(_get('bid_price1')),
        "bid_volume1": _safe(_get('bid_volume1')),
        "ask_price2": _safe(_get('ask_price2')),
        "ask_volume2": _safe(_get('ask_volume2')),
        "bid_price2": _safe(_get('bid_price2')),
        "bid_volume2": _safe(_get('bid_volume2')),
        "ask_price3": _safe(_get('ask_price3')),
        "ask_volume3": _safe(_get('ask_volume3')),
        "bid_price3": _safe(_get('bid_price3')),
        "bid_volume3": _safe(_get('bid_volume3')),
        "ask_price4": _safe(_get('ask_price4')),
        "ask_volume4": _safe(_get('ask_volume4')),
        "bid_price4": _safe(_get('bid_price4')),
        "bid_volume4": _safe(_get('bid_volume4')),
        "ask_price5": _safe(_get('ask_price5')),
        "ask_volume5": _safe(_get('ask_volume5')),
        "bid_price5": _safe(_get('bid_price5')),
        "bid_volume5": _safe(_get('bid_volume5')),
        "last_price": _safe(_get('last_price')),
        "highest": _safe(_get('highest')),
        "lowest": _safe(_get('lowest')),
        "open": _safe(_get('open')),
        "close": _safe(_get('close')),
        "average": _safe(_get('average')),
        "volume": _safe(_get('volume')),
        "amount": _safe(_get('amount')),
        "open_interest": _safe(_get('open_interest')),
        "settlement": _safe(_get('settlement')),
        "upper_limit": _safe(_get('upper_limit')),
        "lower_limit": _safe(_get('lower_limit')),
        "pre_open_interest": _safe(_get('pre_open_interest')),
        "pre_settlement": _safe(_get('pre_settlement')),
        "pre_close": _safe(_get('pre_close')),
        "price_tick": _safe(_get('price_tick')),
        "price_decs": _safe(_get('price_decs')),
        "volume_multiple": _safe(_get('volume_multiple')),
        "max_limit_order_volume": _safe(_get('max_limit_order_volume')),
        "max_market_order_volume": _safe(_get('max_market_order_volume')),
        "min_limit_order_volume": _safe(_get('min_limit_order_volume')),
        "min_market_order_volume": _safe(_get('min_market_order_volume')),
        "underlying_symbol": _safe(_get('underlying_symbol')),
        "strike_price": _safe(_get('strike_price')),
        "ins_class": _safe(_get('ins_class')),
        "instrument_id": _safe(_get('instrument_id')),
        "instrument_name": _safe(_get('instrument_name')),
        "exchange_id": _safe(_get('exchange_id')),
        "expired": _safe(_get('expired')),
        "trading_time": trading_time_raw,
        "expire_datetime": _safe(_get('expire_datetime')),
        "delivery_year": _safe(_get('delivery_year')),
        "delivery_month": _safe(_get('delivery_month')),
        "last_exercise_datetime": _safe(_get('last_exercise_datetime')),
        "exercise_year": _safe(_get('exercise_year')),
        "exercise_month": _safe(_get('exercise_month')),
        "option_class": _safe(_get('option_class')),
        "exercise_type": _safe(_get('exercise_type')),
        "product_id": _safe(_get('product_id')),
        "iopv": _safe(_get('iopv')),
        "public_float_share_quantity": _safe(_get('public_float_share_quantity')),
        "stock_dividend_ratio": _safe(_get('stock_dividend_ratio')),
        "cash_dividend_ratio": _safe(_get('cash_dividend_ratio')),
        "expire_rest_days": _safe(_get('expire_rest_days')),
        "commission": _safe(_get('commission')),
        "margin": _safe(_get('margin')),
    }


def _run_query_quotes(ins_class, exchange_id, product_id, expired, has_night):
    from tqsdk import TqApi
    api = None
    try:
        auth = _get_tq_auth()
        api = TqApi(auth=auth)

        query_kwargs = {}
        if ins_class is not None:
            query_kwargs["ins_class"] = ins_class
        if exchange_id is not None:
            query_kwargs["exchange_id"] = exchange_id
        if product_id is not None:
            query_kwargs["product_id"] = product_id
        if expired is not None:
            query_kwargs["expired"] = expired
        if has_night is not None:
            query_kwargs["has_night"] = has_night

        result = api.query_quotes(**query_kwargs)

        return ToolResult(
            success=True,
            output={
                "symbols": list(result),
                "count": len(result),
                "query_params": query_kwargs,
            }
        )
    except ValueError as e:
        return ToolResult(success=False, output=None, error=str(e))
    except Exception as e:
        logger.error(f"[QueryQuotesTool] Error: {e}")
        return ToolResult(success=False, output=None, error=f"查询合约代码失败: {str(e)}")
    finally:
        if api:
            api.close()


def _run_get_quote(symbols):
    from tqsdk import TqApi
    api = None
    try:
        auth = _get_tq_auth()
        api = TqApi(auth=auth)

        symbol_list = [s.strip() for s in symbols.split(',') if s.strip()]

        quotes = {s: api.get_quote(s) for s in symbol_list}

        deadline = time.time() + 5
        while time.time() < deadline:
            api.wait_update(deadline=deadline)
            if all(q.instrument_id for q in quotes.values()):
                break

        valid_symbols = []
        failed_symbols = []
        for symbol in symbol_list:
            quote = quotes[symbol]
            if quote.instrument_id:
                valid_symbols.append(symbol)
            else:
                failed_symbols.append(symbol)

        if not valid_symbols:
            return ToolResult(
                success=False,
                output=None,
                error=f"没有有效的合约，失败的合约: {', '.join(failed_symbols)}"
            )

        result = {}
        for symbol in valid_symbols:
            quote = quotes[symbol]
            try:
                result[symbol] = _quote_to_dict(quote)
            except Exception as e:
                result[symbol] = {"error": f"获取行情失败: {str(e)}"}

        if failed_symbols:
            result["_failed_symbols"] = failed_symbols

        return ToolResult(
            success=True,
            output=result,
            metadata={
                "valid_count": len(valid_symbols),
                "failed_count": len(failed_symbols),
            }
        )
    except ValueError as e:
        return ToolResult(success=False, output=None, error=str(e))
    except Exception as e:
        logger.error(f"[GetQuoteTool] Error: {e}")
        return ToolResult(success=False, output=None, error=f"获取实时行情失败: {str(e)}")
    finally:
        if api:
            api.close()


class QueryQuotesTool(BaseTool):
    name = "query_quotes"
    description = "根据条件查询期货/期权合约代码。支持按合约类型、交易所、品种、是否下市、是否有夜盘等条件筛选"

    async def execute(self, **kwargs) -> ToolResult:
        ins_class = kwargs.get("ins_class")
        exchange_id = kwargs.get("exchange_id")
        product_id = kwargs.get("product_id")
        expired = kwargs.get("expired", False)
        has_night = kwargs.get("has_night")

        return await asyncio.to_thread(
            _run_query_quotes, ins_class, exchange_id, product_id, expired, has_night
        )

    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "ins_class": {
                    "type": "string",
                    "description": "合约类型，如 FUTURE（期货）、OPTION（期权）、INDEX（指数）、STOCK（股票）等"
                },
                "exchange_id": {
                    "type": "string",
                    "description": "交易所代码，如 SHFE（上期所）、DCE（大商所）、CZCE（郑商所）、CFFEX（中金所）、INE（能源中心）、SSE（上交所）、SZSE（深交所）等"
                },
                "product_id": {
                    "type": "string",
                    "description": "品种代码，如 rb（螺纹钢）、cu（铜）、au（黄金）等。股票和期权不能通过此参数筛选"
                },
                "expired": {
                    "type": "boolean",
                    "description": "是否已下市，默认为 false（仅查询未下市合约）"
                },
                "has_night": {
                    "type": "boolean",
                    "description": "是否有夜盘交易，可选 true/false"
                }
            },
            "required": []
        }


class GetQuoteTool(BaseTool):
    name = "get_quote"
    description = "获取期货/期权合约的实时行情数据，包括最新价、买卖盘口、成交量、持仓量等。支持同时查询多个合约"

    async def execute(self, **kwargs) -> ToolResult:
        symbols = kwargs.get("symbols", "")

        if not symbols or not symbols.strip():
            return ToolResult(success=False, output=None, error="请提供至少一个合约代码")

        return await asyncio.to_thread(_run_get_quote, symbols)

    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "string",
                    "description": "合约代码，多个合约用英文逗号分隔。如 'SHFE.rb2501,DCE.m2505' 或 'SHFE.au2506'"
                }
            },
            "required": ["symbols"]
        }


tool_registry.register(QueryQuotesTool())
tool_registry.register(GetQuoteTool())
