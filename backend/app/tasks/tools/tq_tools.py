import os
import time
import math
import uuid
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from app.tasks.tools import BaseTool, ToolResult, tool_registry
from app.config import settings
from app.services.room_session import RoomSessionManager

logger = logging.getLogger(__name__)

TQ_RESOURCE_KEY = "tq_api"
FILES_DIR = Path("storage/agent_files")

session_manager = RoomSessionManager.get_instance()


def _get_tq_auth():
    from tqsdk import TqAuth
    account = getattr(settings, "TQ_ACCOUNT_NAME", "") or os.getenv("TQ_ACCOUNT_NAME", "")
    password = getattr(settings, "TQ_PASSWORD", "") or os.getenv("TQ_PASSWORD", "")
    if not account or not password:
        raise ValueError("天勤账户未配置，请在 .env 中设置 TQ_ACCOUNT_NAME 和 TQ_PASSWORD")
    return TqAuth(account, password)


def _ensure_tq_api(resources: dict):
    if TQ_RESOURCE_KEY not in resources:
        from tqsdk import TqApi
        auth = _get_tq_auth()
        api = TqApi(auth=auth)
        resources[TQ_RESOURCE_KEY] = api
        logger.info("[TqTools] TqApi instance created for room session")
    return resources[TQ_RESOURCE_KEY]


def _safe(value: Any) -> Any:
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


def _quote_to_dict(quote: Any) -> Dict[str, Any]:
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


def _do_query_quotes(resources: dict, ins_class, exchange_id, product_id, expired, has_night):
    try:
        api = _ensure_tq_api(resources)

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
        if TQ_RESOURCE_KEY in resources:
            try:
                resources[TQ_RESOURCE_KEY].close()
            except Exception:
                pass
            del resources[TQ_RESOURCE_KEY]
        return ToolResult(success=False, output=None, error=f"查询合约代码失败: {str(e)}")


def _do_query_options(resources: dict, underlying_symbol, option_class, exercise_year, exercise_month, strike_price, expired, has_A, has_MS):
    try:
        api = _ensure_tq_api(resources)

        query_kwargs = {"underlying_symbol": underlying_symbol}
        if option_class is not None:
            query_kwargs["option_class"] = option_class
        if exercise_year is not None:
            query_kwargs["exercise_year"] = exercise_year
        if exercise_month is not None:
            query_kwargs["exercise_month"] = exercise_month
        if strike_price is not None:
            query_kwargs["strike_price"] = strike_price
        if expired is not None:
            query_kwargs["expired"] = expired
        if has_A is not None:
            query_kwargs["has_A"] = has_A
        if has_MS is not None:
            query_kwargs["has_MS"] = has_MS

        result = api.query_options(**query_kwargs)

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
        logger.error(f"[QueryOptionsTool] Error: {e}")
        if TQ_RESOURCE_KEY in resources:
            try:
                resources[TQ_RESOURCE_KEY].close()
            except Exception:
                pass
            del resources[TQ_RESOURCE_KEY]
        return ToolResult(success=False, output=None, error=f"查询期权合约失败: {str(e)}")


def _do_get_quote(resources: dict, symbols):
    try:
        api = _ensure_tq_api(resources)

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
        if TQ_RESOURCE_KEY in resources:
            try:
                resources[TQ_RESOURCE_KEY].close()
            except Exception:
                pass
            del resources[TQ_RESOURCE_KEY]
        return ToolResult(success=False, output=None, error=f"获取实时行情失败: {str(e)}")


def _do_get_klines(resources: dict, symbols, duration_seconds, length, room_id, user_id):
    try:
        import pandas as pd
    except ImportError:
        return ToolResult(success=False, output=None, error="pandas 未安装，请运行 pip install pandas")

    try:
        duration_seconds = int(duration_seconds)
        length = int(length)
    except (ValueError, TypeError):
        return ToolResult(success=False, output=None, error="duration_seconds 和 length 必须是整数")

    if not (1 <= duration_seconds <= 86400):
        return ToolResult(success=False, output=None, error="K线周期必须在 1~86400 秒之间")

    symbol_list = [s.strip() for s in symbols.split(',') if s.strip()]
    if not symbol_list:
        return ToolResult(success=False, output=None, error="合约代码不能为空")

    try:
        api = _ensure_tq_api(resources)

        kline_refs = {}
        for sym in symbol_list:
            try:
                kline_refs[sym] = api.get_kline_serial(sym, duration_seconds, data_length=length)
            except Exception as e:
                logger.warning(f"[GetKlinesTool] 订阅合约 {sym} 失败: {e}")

        if not kline_refs:
            return ToolResult(success=False, output=None, error="所有合约订阅均失败，请检查合约代码是否有效")

        deadline = time.time() + 10
        api.wait_update(deadline=deadline)

        result = {}
        for sym, df in kline_refs.items():
            try:
                if df.empty:
                    logger.warning(f"[GetKlinesTool] {sym} K线数据为空")
                    continue
                df_out = df.copy()
                df_out['datetime'] = pd.to_datetime(df_out['datetime'], unit='ns')
                df_out = df_out.reset_index(drop=True)
                result[sym] = df_out
            except Exception as e:
                logger.warning(f"[GetKlinesTool] 解析合约 {sym} K线失败: {e}")

        if not result:
            return ToolResult(success=False, output=None, error="未获取到任何K线数据")

        outputs_dir = FILES_DIR / str(user_id) / room_id / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)

        file_id = str(uuid.uuid4())[:8]
        saved_files = []
        for sym, df_out in result.items():
            safe_name = sym.replace('.', '_')
            filename = f"klines_{safe_name}_{file_id}.csv"
            file_path = outputs_dir / filename
            df_out.to_csv(str(file_path), index=False)
            file_size = file_path.stat().st_size
            saved_files.append({
                "symbol": sym,
                "filename": filename,
                "file_size": file_size,
                "relative_path": file_path.relative_to(FILES_DIR).as_posix(),
                "folder": "outputs",
                "rows": len(df_out),
            })

        return ToolResult(
            success=True,
            output={
                "symbols": list(result.keys()),
                "count": len(result),
                "duration_seconds": duration_seconds,
                "length": length,
                "files": saved_files,
                "file_created": saved_files[0] if len(saved_files) == 1 else None,
            }
        )
    except ValueError as e:
        return ToolResult(success=False, output=None, error=str(e))
    except Exception as e:
        logger.error(f"[GetKlinesTool] Error: {e}")
        if TQ_RESOURCE_KEY in resources:
            try:
                resources[TQ_RESOURCE_KEY].close()
            except Exception:
                pass
            del resources[TQ_RESOURCE_KEY]
        return ToolResult(success=False, output=None, error=f"获取K线数据失败: {str(e)}")


def _bs_calc_impv(S, C, K, r, init_v, t, option_class):
    import numpy as np
    from scipy.stats import norm

    if t <= 0 or S <= 0 or K <= 0 or C <= 0:
        return float('nan')

    o = 1 if option_class == "CALL" else -1
    lower_limit = o * (S - K * math.exp(-r * t))
    if C < lower_limit:
        return float('nan')

    v = init_v if init_v and init_v > 0 else 0.3
    for _ in range(100):
        d1 = (math.log(S / K) + (r + 0.5 * v * v) * t) / (v * math.sqrt(t))
        d2 = d1 - v * math.sqrt(t)
        bs_price = o * (S * norm.cdf(o * d1) - K * math.exp(-r * t) * norm.cdf(o * d2))
        vega = S * math.sqrt(t) * norm.pdf(d1)
        if vega < 1e-8:
            break
        diff = (C - bs_price) / vega
        if abs(diff) < 1e-8:
            break
        if diff > v / 2:
            v = v * 1.5
        elif diff < -v / 2:
            v = v / 2
        else:
            v = v + diff
        if v <= 0:
            v = 0.001
    return v


def _bs_calc_greeks(S, K, r, v, t, option_class):
    import numpy as np
    from scipy.stats import norm

    if v <= 0 or t <= 0 or S <= 0 or K <= 0:
        return {"delta": float('nan'), "gamma": float('nan'), "theta": float('nan'), "vega": float('nan'), "rho": float('nan')}

    o = 1 if option_class == "CALL" else -1
    sqrt_t = math.sqrt(t)
    d1 = (math.log(S / K) + (r + 0.5 * v * v) * t) / (v * sqrt_t)
    d2 = d1 - v * sqrt_t

    delta = o * norm.cdf(o * d1)
    gamma = norm.pdf(d1) / (S * v * sqrt_t)
    theta_annual = (-v * S * norm.pdf(d1) / (2 * sqrt_t) - o * r * K * math.exp(-r * t) * norm.cdf(o * d2))
    theta_daily = theta_annual / 365.0
    vega = S * sqrt_t * norm.pdf(d1) / 100.0
    rho = o * K * t * math.exp(-r * t) * norm.cdf(o * d2) / 100.0

    return {
        "delta": delta,
        "gamma": gamma,
        "theta": theta_daily,
        "vega": vega,
        "rho": rho,
    }


def _do_query_option_greeks(resources: dict, symbols, v, r):
    try:
        api = _ensure_tq_api(resources)

        symbol_list = [s.strip() for s in symbols.split(",") if s.strip()]
        if not symbol_list:
            return ToolResult(success=False, output=None, error="合约代码不能为空")

        v_list = None
        if v is not None:
            v_list = [float(x.strip()) for x in str(v).split(",") if x.strip()]
            if len(v_list) != len(symbol_list):
                return ToolResult(
                    success=False, output=None,
                    error=f"波动率数量({len(v_list)})与合约数量({len(symbol_list)})不一致"
                )

        quotes = {}
        underlying_quotes = {}
        for sym in symbol_list:
            quotes[sym] = api.get_quote(sym)
        deadline = time.time() + 10
        api.wait_update(deadline=deadline)

        for sym in symbol_list:
            q = quotes[sym]
            underlying_sym = getattr(q, 'underlying_symbol', None)
            if underlying_sym and underlying_sym not in underlying_quotes:
                underlying_quotes[underlying_sym] = api.get_quote(underlying_sym)
        if underlying_quotes:
            deadline = time.time() + 10
            api.wait_update(deadline=deadline)

        greeks_list = []
        for i, sym in enumerate(symbol_list):
            q = quotes[sym]
            if not q.instrument_id:
                greeks_list.append({"instrument_id": sym, "error": "合约不存在或已过期"})
                continue

            ins_class = getattr(q, 'ins_class', '')
            if not ins_class.endswith("OPTION"):
                greeks_list.append({"instrument_id": sym, "error": f"不是期权合约（类型: {ins_class}）"})
                continue

            S = float('nan')
            underlying_sym = getattr(q, 'underlying_symbol', None)
            if underlying_sym and underlying_sym in underlying_quotes:
                uq = underlying_quotes[underlying_sym]
                for attr in ('last_price', 'pre_close', 'open', 'bid_price1', 'ask_price1', 'settlement'):
                    val = getattr(uq, attr, float('nan'))
                    if isinstance(val, (int, float)) and not math.isnan(val) and val > 0:
                        S = val
                        break
            elif hasattr(q, 'underlying_quote') and q.underlying_quote:
                uq = q.underlying_quote
                for attr in ('last_price', 'pre_close', 'open', 'bid_price1', 'ask_price1', 'settlement'):
                    val = getattr(uq, attr, float('nan'))
                    if isinstance(val, (int, float)) and not math.isnan(val) and val > 0:
                        S = val
                        break

            C = float('nan')
            for attr in ('last_price', 'pre_close', 'open', 'bid_price1', 'ask_price1', 'settlement'):
                val = getattr(q, attr, float('nan'))
                if isinstance(val, (int, float)) and not math.isnan(val) and val > 0:
                    C = val
                    break
            K = getattr(q, 'strike_price', float('nan'))
            option_class = getattr(q, 'option_class', '')
            expire_rest_days = getattr(q, 'expire_rest_days', 0)
            expire_datetime = getattr(q, 'expire_datetime', 0)

            t = expire_rest_days / 360.0 if expire_rest_days and expire_rest_days > 0 else 0

            if math.isnan(S) or math.isnan(C) or math.isnan(K) or t <= 0:
                greeks_list.append({
                    "instrument_id": _safe(q.instrument_id),
                    "instrument_name": _safe(q.instrument_name),
                    "option_class": _safe(option_class),
                    "underlying_symbol": _safe(underlying_sym),
                    "strike_price": _safe(K),
                    "expire_rest_days": _safe(expire_rest_days),
                    "underlying_price": _safe(S),
                    "option_price": _safe(C),
                    "iv": None,
                    "delta": None,
                    "gamma": None,
                    "theta": None,
                    "vega": None,
                    "rho": None,
                    "error": "数据不完整（标的价格/期权价格/行权价/到期时间可能缺失）",
                })
                continue

            if v_list is not None:
                iv = v_list[i]
            else:
                iv = _bs_calc_impv(S, C, K, r, 0.3, t, option_class)

            greeks = _bs_calc_greeks(S, K, r, iv, t, option_class)

            greeks_list.append({
                "instrument_id": _safe(q.instrument_id),
                "instrument_name": _safe(q.instrument_name),
                "option_class": _safe(option_class),
                "underlying_symbol": _safe(underlying_sym),
                "strike_price": _safe(K),
                "expire_rest_days": _safe(expire_rest_days),
                "expire_datetime": _safe(expire_datetime),
                "underlying_price": _safe(S),
                "option_price": _safe(C),
                "iv": round(iv, 6) if not math.isnan(iv) else None,
                "iv_percent": round(iv * 100, 2) if not math.isnan(iv) else None,
                **{k: round(v, 6) if not math.isnan(v) else None for k, v in greeks.items()},
            })

        return ToolResult(
            success=True,
            output={
                "greeks": greeks_list,
                "count": len(greeks_list),
                "risk_free_rate": r,
                "volatility_source": "implied" if v is None else "user_specified",
            }
        )
    except ValueError as e:
        return ToolResult(success=False, output=None, error=str(e))
    except Exception as e:
        import traceback
        logger.error(f"[QueryOptionGreeksTool] Error: {e}\n{traceback.format_exc()}")
        if TQ_RESOURCE_KEY in resources:
            try:
                resources[TQ_RESOURCE_KEY].close()
            except Exception:
                pass
            del resources[TQ_RESOURCE_KEY]
        return ToolResult(success=False, output=None, error=f"查询期权Greeks失败: {repr(e)}")


class QueryQuotesTool(BaseTool):
    name = "query_quotes"
    description = "根据条件查询期货/期权合约代码。支持按合约类型、交易所、品种、是否下市、是否有夜盘等条件筛选"

    async def execute(self, **kwargs) -> ToolResult:
        room_id = kwargs.get("room_id", "default")
        ins_class = kwargs.get("ins_class")
        exchange_id = kwargs.get("exchange_id")
        product_id = kwargs.get("product_id")
        expired = kwargs.get("expired", False)
        has_night = kwargs.get("has_night")

        session = session_manager.get_session(room_id)
        try:
            return await session.submit_async(
                lambda res: _do_query_quotes(res, ins_class, exchange_id, product_id, expired, has_night),
                timeout=30.0,
            )
        except Exception as e:
            logger.error(f"[QueryQuotesTool] Session error: {e}")
            return ToolResult(success=False, output=None, error=f"查询合约代码失败: {str(e)}")

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
        room_id = kwargs.get("room_id", "default")
        symbols = kwargs.get("symbols", "")

        if not symbols or not symbols.strip():
            return ToolResult(success=False, output=None, error="请提供至少一个合约代码")

        session = session_manager.get_session(room_id)
        try:
            return await session.submit_async(
                lambda res: _do_get_quote(res, symbols),
                timeout=30.0,
            )
        except Exception as e:
            logger.error(f"[GetQuoteTool] Session error: {e}")
            return ToolResult(success=False, output=None, error=f"获取实时行情失败: {str(e)}")

    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "string",
                    "description": "合约代码，多个合约用英文逗号分隔。如 'SHFE.rb2501,DCE.m2505' 或 'DCE.jd2607-C-4200'"
                }
            },
            "required": ["symbols"]
        }


tool_registry.register(QueryQuotesTool())
tool_registry.register(GetQuoteTool())


class QueryOptionsTool(BaseTool):
    name = "query_options"
    description = "根据标的合约查询期权合约代码。支持按期权类型（看涨/看跌）、行权年份、行权月份、行权价格等条件筛选"

    async def execute(self, **kwargs) -> ToolResult:
        room_id = kwargs.get("room_id", "default")
        underlying_symbol = kwargs.get("underlying_symbol", "")
        option_class = kwargs.get("option_class")
        exercise_year = kwargs.get("exercise_year")
        exercise_month = kwargs.get("exercise_month")
        strike_price = kwargs.get("strike_price")
        expired = kwargs.get("expired")
        has_A = kwargs.get("has_A")
        has_MS = kwargs.get("has_MS")

        if not underlying_symbol or not underlying_symbol.strip():
            return ToolResult(success=False, output=None, error="请提供标的合约代码（underlying_symbol）")

        session = session_manager.get_session(room_id)
        try:
            return await session.submit_async(
                lambda res: _do_query_options(res, underlying_symbol, option_class, exercise_year, exercise_month, strike_price, expired, has_A, has_MS),
                timeout=30.0,
            )
        except Exception as e:
            logger.error(f"[QueryOptionsTool] Session error: {e}")
            return ToolResult(success=False, output=None, error=f"查询期权合约失败: {str(e)}")

    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "underlying_symbol": {
                    "type": "string",
                    "description": "标的合约代码，如 'SHFE.cu2501'、'CZCE.SR501'"
                },
                "option_class": {
                    "type": "string",
                    "enum": ["CALL", "PUT"],
                    "description": "期权类型：CALL（看涨期权）、PUT（看跌期权）"
                },
                "exercise_year": {
                    "type": "integer",
                    "description": "最后行权日年份，如 2025"
                },
                "exercise_month": {
                    "type": "integer",
                    "description": "最后行权日月份，如 1-12"
                },
                "strike_price": {
                    "type": "number",
                    "description": "行权价格"
                },
                "expired": {
                    "type": "boolean",
                    "description": "是否已下市，默认为 false（仅查询未下市合约）"
                },
                "has_A": {
                    "type": "boolean",
                    "description": "是否含有A，True代表只含A的期权，False代表不含A的期权，默认不做区分"
                },
                "has_MS": {
                    "type": "boolean",
                    "description": "是否含有MS系列，True代表只含MS系列期权，False代表排除MS系列期权，默认不做区分"
                }
            },
            "required": ["underlying_symbol"]
        }


tool_registry.register(QueryOptionsTool())


class GetKlinesTool(BaseTool):
    name = "get_klines"
    description = "获取期货/期权合约的K线历史数据并保存为CSV文件。支持多合约同时查询，每个合约生成独立的CSV文件"

    async def execute(self, **kwargs) -> ToolResult:
        room_id = kwargs.get("room_id", "default")
        user_id = kwargs.get("user_id", 0)
        symbols = kwargs.get("symbols", "")
        duration_seconds = kwargs.get("duration_seconds", 60)
        length = kwargs.get("length", 100)

        if not symbols or not symbols.strip():
            return ToolResult(success=False, output=None, error="请提供至少一个合约代码")

        session = session_manager.get_session(room_id)
        try:
            return await session.submit_async(
                lambda res: _do_get_klines(res, symbols, duration_seconds, length, room_id, user_id),
                timeout=30.0,
            )
        except Exception as e:
            logger.error(f"[GetKlinesTool] Session error: {e}")
            return ToolResult(success=False, output=None, error=f"获取K线数据失败: {str(e)}")

    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "string",
                    "description": "合约代码，多个合约用英文逗号分隔。如 'SHFE.rb2501,DCE.m2505'"
                },
                "duration_seconds": {
                    "type": "integer",
                    "description": "K线周期（秒），常见值：60（1分钟）、300（5分钟）、900（15分钟）、1800（30分钟）、3600（1小时）、86400（日线）。默认60",
                    "default": 60
                },
                "length": {
                    "type": "integer",
                    "description": "获取的K线根数，默认100",
                    "default": 100
                }
            },
            "required": ["symbols"]
        }


tool_registry.register(GetKlinesTool())


class QueryOptionGreeksTool(BaseTool):
    name = "query_option_greeks"
    description = "查询期权的希腊字母（Delta/Gamma/Theta/Vega/Rho）和隐含波动率。支持单个或多个期权合约同时查询。不传波动率时默认使用隐含波动率计算"

    async def execute(self, **kwargs) -> ToolResult:
        room_id = kwargs.get("room_id", "default")
        symbols = kwargs.get("symbols", "")
        v = kwargs.get("v")
        r = kwargs.get("r", 0.025)

        if not symbols or not symbols.strip():
            return ToolResult(success=False, output=None, error="请提供至少一个期权合约代码")

        session = session_manager.get_session(room_id)
        try:
            return await session.submit_async(
                lambda res: _do_query_option_greeks(res, symbols, v, r),
                timeout=30.0,
            )
        except Exception as e:
            logger.error(f"[QueryOptionGreeksTool] Session error: {e}")
            return ToolResult(success=False, output=None, error=f"查询期权Greeks失败: {str(e)}")

    def get_parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "string",
                    "description": "期权合约代码，多个合约用英文逗号分隔。如 'SHFE.cu2501C72000,DCE.jd2607-C-4200'"
                },
                "v": {
                    "type": "string",
                    "description": "指定波动率（可选）。多个时用逗号分隔，数量必须与合约数量一致。不传则使用隐含波动率计算"
                },
                "r": {
                    "type": "number",
                    "description": "无风险利率，默认0.025（2.5%）",
                    "default": 0.025
                }
            },
            "required": ["symbols"]
        }


tool_registry.register(QueryOptionGreeksTool())
