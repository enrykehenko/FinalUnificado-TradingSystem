# BingXServices/TradingService/data_models.py

from __future__ import annotations

import logging
from collections import deque
from decimal import Decimal
from typing import Deque, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from .trading_types import (
    ZERO,
    MultiTimeframeLiteralType,
    PartialImpulseLiteralPhasesType,
    SideLiteralType,
    TimeframeLiteralType,
)

logger = logging.getLogger(__name__)

# --- MODELOS DE MÉTRICAS BASE (La "Genética" de cada Período) ---

class BasePeriodMetrics(BaseModel):
    """
    Métricas cinemáticas y de estado para un período.
    Actúa como un monitor Holter, registrando valores actuales y picos.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore")
    
    # --- Cinemática del Precio ---
    price_velocity: Decimal = ZERO
    price_acceleration: Decimal = ZERO
    price_jerk: Decimal = ZERO
    
    # --- Picos de Cinemática del Precio ---
    peak_price_velocity: Decimal = ZERO
    peak_price_acceleration: Decimal = ZERO
    peak_price_jerk: Decimal = ZERO
    
    # --- Métricas de Estado del Precio ---
    net_price_change: Decimal = ZERO
    net_price_change_side: SideLiteralType = ""
    price_variacion_neta_absoluta: Decimal = ZERO
    absolute_max_price: Decimal = ZERO
    absolute_min_price: Decimal = ZERO

class MicroTimeframeMetrics(BasePeriodMetrics):
    """Métricas adicionales exclusivas para el timeframe de 1m (Nivel Micro)."""
    
    # --- Cinemática del MACD ---
    macd_velocity: Decimal = ZERO
    macd_acceleration: Decimal = ZERO
    macd_jerk: Decimal = ZERO
    
    # --- Picos de Cinemática del MACD ---
    peak_macd_velocity: Decimal = ZERO
    peak_macd_acceleration: Decimal = ZERO
    peak_macd_jerk: Decimal = ZERO

    macd_slope: Decimal = ZERO
    macd_to_zero_distance: Decimal = ZERO
    peak_macd_to_zero_distance: Decimal = ZERO
    
    # --- Métricas de Estado del MACD ---
    absolute_max_macd: Decimal = ZERO
    absolute_min_macd: Decimal = ZERO

class MacroTimeframeMetrics(BasePeriodMetrics):
    """Métricas para timeframes superiores, con análisis cinemático completo de la EMA200."""
    
    
    # --- Cinemática de la EMA200 ---
    ema200_velocity: Decimal = ZERO
    ema200_acceleration: Decimal = ZERO
    ema200_jerk: Decimal = ZERO
    
    # --- Picos de Cinemática de la EMA200 ---
    peak_ema200_velocity: Decimal = ZERO
    peak_ema200_acceleration: Decimal = ZERO
    peak_ema200_jerk: Decimal = ZERO

    # --- Métricas Relacionales Precio-EMA ---
    ema200_slope: Decimal = ZERO
    price_to_ema200_distance: Decimal = ZERO
    peak_price_to_ema200_distance: Decimal = ZERO
    
    # --- Métricas de Estado de la EMA200 ---
    absolute_max_ema200: Decimal = ZERO
    absolute_min_ema200: Decimal = ZERO


class PeriodData(BaseModel):
    """
    Clase base para todos los contenedores de datos de períodos.
    Contiene el estado y los historiales comunes a todos.
    """
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore")
    
    # --- Estado del Ciclo de Vida ---
    active: bool = False
    side: SideLiteralType = "indefinido"
    entry_ts: int = 0
    exit_ts: int = 0
    entry_price: Decimal = ZERO
    exit_price: Decimal = ZERO
    
    # --- Historiales Crudos ---
    timestamps: List[int] = Field(default_factory=list)
    price_history: List[Decimal] = Field(default_factory=list)

class MicroPeriodData(PeriodData):
    """Clase base para períodos en el timeframe de 1m."""
    metrics: MicroTimeframeMetrics = Field(default_factory=MicroTimeframeMetrics)
    # NO se repiten campos de PeriodData. La herencia los incluye.
    # Se añaden solo los campos específicos de 1m.
    entry_macd: Decimal = ZERO
    exit_macd: Decimal = ZERO
    macd_history: List[Decimal] = Field(default_factory=list)
    ema200_history: List[Decimal] = Field(default_factory=list) # EMA200 también es relevante en 1m

class MacroPeriodData(PeriodData):
    """Clase base para períodos en timeframes superiores."""
    metrics: MacroTimeframeMetrics = Field(default_factory=MacroTimeframeMetrics)
    # NO se repiten campos de PeriodData.
    # Se añaden solo los campos específicos de >1m.
    entry_ema200: Decimal = ZERO
    exit_ema200: Decimal = ZERO
    ema200_history: List[Decimal] = Field(default_factory=list)
    
# --- Implementación Específica por Período ---
# Nivel 1: La "Ola"
class PartialPhaseData(BaseModel):
    """Nivel 1: "La Ola" - Fluctuación más inmediata."""
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore")
    symbol: str = ""
    phase_name: PartialImpulseLiteralPhasesType = ""
    active: bool = False
    metrics: MicroTimeframeMetrics = Field(default_factory=MicroTimeframeMetrics)

class PartialImpulseData(BaseModel):
    """Nivel 2: "La Marea Parcial" - Impulso corto compuesto de Olas."""
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore")
    symbol: str = ""
    active: bool = False
    side: SideLiteralType = ""
    phase_history: Deque[PartialPhaseData] = Field(default_factory=lambda: deque(maxlen=20))
    metrics: MicroTimeframeMetrics = Field(default_factory=MicroTimeframeMetrics)

# Nivel 3: La "Lucha de Mareas"
class MacdCycleData(PeriodData):
    """Nivel 3: "La Lucha de Mareas" - Ciclo completo alcista + bajista."""
    metrics: MicroTimeframeMetrics = Field(default_factory=MicroTimeframeMetrics)
    impulso_alcista: Optional[PartialImpulseData] = None
    impulso_bajista: Optional[PartialImpulseData] = None
    predicted_dominance_side: SideLiteralType = "indefinido"
    macd_history: List[Decimal] = Field(default_factory=list) 

class TotalImpulseData(BaseModel):
    """Nivel 4: "La Corriente Oceánica" - Dirección principal del momentum en 1m."""
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore")
    symbol: str
    timeframe: TimeframeLiteralType = "1m"
    active: bool = False
    side: SideLiteralType = ""
    metrics: MicroTimeframeMetrics = Field(default_factory=MicroTimeframeMetrics)
    macd_cycle_history: Deque[MacdCycleData] = Field(default_factory=lambda: deque(maxlen=50))

class TotalTrendData(BaseModel):
    """Nivel 5: "La Fuerza Terrestre" - Tendencia estructural en 1m."""
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore")
    symbol: str
    timeframe: TimeframeLiteralType = "1m"
    active: bool = False
    side: SideLiteralType = ""
    metrics: MacroTimeframeMetrics = Field(default_factory=MacroTimeframeMetrics)
    total_impulse_history: Deque[TotalImpulseData] = Field(default_factory=lambda: deque(maxlen=50)) # Solo para 1

class GlobalTotalImpulseData(BaseModel):
    """
    Niveles 6-9: Las Fuerzas Cósmicas de Impulso
    - Nivel 6: La Fuerza Lunar (5m) - Primera influencia gravitacional externa
    - Nivel 7: La Fuerza Solar (15m) - Influencia dominante intradiaria  
    - Nivel 8: La Fuerza del Sistema Solar (1h) - Estructura de sesión completa
    - Nivel 9: La Fuerza de la Vía Láctea (4h) - Momentum estructural a medio plazo
    """
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore")
    symbol: str
    timeframe: MultiTimeframeLiteralType
    active: bool = False
    side: SideLiteralType = ""
    metrics: MacroTimeframeMetrics = Field(default_factory=MacroTimeframeMetrics)
    total_impulse_history: Deque[TotalImpulseData] = Field(default_factory=lambda: deque(maxlen=50))

class GlobalTotalTrendData(BaseModel):
    """
    Niveles 10-13: Las Tendencias Maestras
    - Nivel 10: La Fuerza del Grupo Local (5m) - Tendencia estructural Lunar
    - Nivel 11: La Fuerza del Cúmulo de Virgo (15m) - Tendencia estructural Solar
    - Nivel 12: La Fuerza de Andrómeda (1h) - Tendencia estructural del Sistema Solar
    - Nivel 13: La Fuerza del Universo (4h) - La Tendencia Maestra, contexto absoluto
    """
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore")
    symbol: str
    timeframe: MultiTimeframeLiteralType
    active: bool = False
    side: SideLiteralType = ""
    metrics: MacroTimeframeMetrics = Field(default_factory=MacroTimeframeMetrics)
    global_total_impulse_history: Deque[GlobalTotalImpulseData] = Field(default_factory=lambda: deque(maxlen=50))
    total_trend_history: Deque[TotalTrendData] = Field(default_factory=lambda: deque(maxlen=50))

class TimeframeSpecificImpulseData(BaseModel):
    """Datos de impulso específicos para un timeframe superior."""
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore")
    timeframe: MultiTimeframeLiteralType
    active: bool = False
    side: SideLiteralType = ""
    metrics: MacroTimeframeMetrics = Field(default_factory=MacroTimeframeMetrics)
    entry_ts: int = 0
    exit_ts: int = 0
    entry_price: Decimal = ZERO
    exit_price: Decimal = ZERO
    entry_ema200: Decimal = ZERO
    exit_ema200: Decimal = ZERO

class TimeframeSpecificTrendData(BaseModel):
    """Datos de tendencia específicos para un timeframe superior."""
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore")
    timeframe: MultiTimeframeLiteralType
    active: bool = False
    side: SideLiteralType = ""
    metrics: MacroTimeframeMetrics = Field(default_factory=MacroTimeframeMetrics)
    entry_ts: int = 0
    exit_ts: int = 0
    entry_price: Decimal = ZERO
    exit_price: Decimal = ZERO
    entry_ema200: Decimal = ZERO
    exit_ema200: Decimal = ZERO
    impulse_history: Deque[TimeframeSpecificImpulseData] = Field(default_factory=lambda: deque(maxlen=50))

# --- MODELOS DE DATOS ANALÍTICOS ---

class AlignmentData(BaseModel):
    """El "Electrocardiograma" del Símbolo, calculado por MIGUEL."""
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore")
    symbol: Optional[str] = None
    last_update_ts: int = 0
    
    # Matrices
    intra_period_matrix: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    weighted_intra_period_matrix: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    inter_period_matrix: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    weighted_inter_period_matrix: Dict[str, Dict[str, float]] = Field(default_factory=dict)
    
    # Scores Agregados
    period_health_scores: Dict[str, float] = Field(default_factory=dict)
    global_alignment_score: float = 0.0
    final_signal_quality_score: float = 0.0
    
    # ✅ SCORES GLOBALES POR CATEGORÍA (Restaurados para análisis y feedback loop)
    global_directional_power_score: Decimal = ZERO
    global_impulse_vs_trend_score: Decimal = ZERO
    global_short_vs_long_tf_score: Decimal = ZERO
    global_side_consistency_score: Decimal = ZERO

class TradeSimulationData(BaseModel):
    """La "Profecía" de RAFAEL."""
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore")
    expected_profit_usd: Decimal = ZERO
    expected_usdt_time_ratio: Decimal = ZERO
    projected_exit_ts: int = 0

class TradeAutopsyReport(BaseModel):
    """El "Informe Forense" para el feedback loop de ZADKIEL."""
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore")
    symbol: str
    order_id: str
    realized_pnl: Decimal
    initial_simulation: TradeSimulationData
    final_simulation: TradeSimulationData
    accuracy_ratio: float
    alignment_matrix_snapshot: Dict[str, Dict[str, float]]

class TimeframeMetrics(BaseModel):
    """Métricas específicas por timeframe para análisis técnico."""
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore")
    
    symbol: str
    timeframe: str
    price: Decimal = ZERO
    ema200_slope: Decimal = ZERO
    macd_slope: Decimal = ZERO
    velocity: Decimal = ZERO
    acceleration: Decimal = ZERO
    variation: Decimal = ZERO
    jerk: Decimal = ZERO
    price_ema200_distance: Decimal = ZERO
    
    def update_price_metrics(self, price: Decimal, ema200_distance: Decimal, ema200_slope: Decimal) -> None:
        """Actualiza las métricas de precio."""
        self.price = price
        self.price_ema200_distance = ema200_distance
        self.ema200_slope = ema200_slope

class SymbolRankingMetrics(BaseModel):
    """El "Dossier del Atleta" que se entrega a ZADKIEL."""
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="ignore")
    symbol: str
    topsis_score: Decimal = ZERO
    # ✅ NUEVO: Score re-escalado para el dashboard
    display_score: float = 0.0
    rank_position: Optional[int] = None
    alignment_data: AlignmentData = Field(default_factory=AlignmentData)
    pre_trade_simulation: TradeSimulationData = Field(default_factory=TradeSimulationData)

__all__ = [
    "BasePeriodMetrics",
    "MicroTimeframeMetrics",
    "MacroTimeframeMetrics",
    "PeriodData",
    "MicroPeriodData",
    "MacroPeriodData",
    "PartialPhaseData",
    "PartialImpulseData",
    "TotalImpulseData",
    "TotalTrendData",
    "GlobalTotalImpulseData",
    "GlobalTotalTrendData",
    "TimeframeSpecificImpulseData",
    "TimeframeSpecificTrendData",
    "TimeframeMetrics",
    "AlignmentData",
    "TradeSimulationData",
    "TradeAutopsyReport",
    "SymbolRankingMetrics"
]