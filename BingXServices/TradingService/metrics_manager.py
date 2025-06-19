# BingXServices/TradingService/metrics_manager.py
from __future__ import annotations

import logging
import time
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

import numpy as np

from .data_models import MacroPeriodData, MicroPeriodData, PeriodData
from .trading_types import (
    ONE,
    SAFE_DIVISION_THRESHOLD,
    SIDE_ALCISTA,
    SIDE_BAJISTA,
    SIDE_INDEFINIDO,
    ZERO,
)

if TYPE_CHECKING:
    from .config.config_loader import AppConfig
    from .trading_position_state import TradingPositionState

logger = logging.getLogger(__name__)

class MetricsManager:
    """
    El Arcángel MIGUEL (Oculus_Hyperion): Comandante Analítico (v.Sismógrafo).
    Calcula el "electrocardiograma" completo del mercado, incluyendo el SideStruggleScore
    y sus derivadas para detectar "supernovas".
    
    ESTADO ACTUAL:
    - Ponderación ESTÁTICA basada en jerarquía cósmica
    - 13 niveles de análisis temporal
    - Matrices de alineamiento intra e inter-período
    - Sismógrafo de supernovas (derivadas del SideStruggleScore)
    
    PENDIENTE DE IMPLEMENTAR:
    - Context Modulator con ponderación DINÁMICA
    - Factores ADX, ATR normalizado y Volumen
    - Auto-aprendizaje basado en correlación histórica reciente
    """
    def __init__(self, app_config: "AppConfig"):
        self.app_config = app_config
        self.ranking_params = app_config.services.trading_service.ranking_params
        
        # PONDERACIÓN ESTÁTICA ACTUAL (ADN inicial del sistema)
        self.log_weights = {
            "1m": Decimal("1.0"), 
            "5m": Decimal("0.693"), 
            "15m": Decimal("0.405"), 
            "1h": Decimal("0.223"), 
            "4h": Decimal("0.095")
        }
        
        # Historial para calcular derivadas del SideStruggleScore
        self.struggle_score_history: Dict[str, List[Tuple[int, float]]] = {}
        
        # TODO: Implementar Context Modulator para ponderación dinámica
        # self.context_modulator = ContextModulator()

    def update_all_metrics(self, ps: "TradingPositionState"):
        """Punto de entrada principal. Orquesta todos los análisis de Miguel."""
        all_periods = self._collect_all_periods(ps)
        if not all_periods: return

        # 1. Calcular cinemática base
        self._calculate_and_store_all_kinematics(all_periods)
        
        # 2. Calcular matrices y salud interna
        intra_matrices, health_scores = self._calculate_all_intra_period_matrices(all_periods)
        inter_matrix, weighted_inter_matrix = self._calculate_inter_period_matrices(health_scores, all_periods)
        
        # 3. Calcular scores finales, incluyendo el sismógrafo de supernovas
        final_scores = self._calculate_final_scores(ps.symbol, weighted_inter_matrix, health_scores)

        # 4. Poblar el objeto AlignmentData con todos los resultados
        alignment_data = ps.ranking_metrics.alignment_data
        alignment_data.intra_period_matrix = intra_matrices
        alignment_data.weighted_intra_period_matrix = intra_matrices # Placeholder para la ponderación intra
        alignment_data.inter_period_matrix = inter_matrix
        alignment_data.weighted_inter_period_matrix = weighted_inter_matrix
        alignment_data.period_health_scores = health_scores
        
        # Poblar todos los scores calculados
        for key, value in final_scores.items():
            setattr(alignment_data, key, value)
            
        alignment_data.last_update_ts = int(time.time() * 1000)
        
        logger.debug(f"[{ps.symbol}] Matrices y scores de Miguel calculados. Supernova Accel: {final_scores.get('struggle_score_acceleration', 0.0):.4f}")

    def _collect_all_periods(self, ps: "TradingPositionState") -> Dict[str, PeriodData]:
        """Reúne a TODOS los 'soldados' (períodos activos) para el análisis de los 13 niveles cósmicos."""
        periods: Dict[str, PeriodData] = {}

        # === JERARQUÍA CÓSMICA DE 13 NIVELES ===
        
        # Nivel 1: La Ola (PartialPhaseData)
        if hasattr(ps, 'partial_phase_orchestrator') and ps.partial_phase_orchestrator.current_phase:
            if ps.partial_phase_orchestrator.current_phase.active:
                periods["Ola"] = ps.partial_phase_orchestrator.current_phase
        
        # Nivel 2: La Marea (PartialImpulseData)
        if hasattr(ps, 'partial_impulse_orchestrator') and ps.partial_impulse_orchestrator.current_impulse:
            if ps.partial_impulse_orchestrator.current_impulse.active:
                periods["Marea"] = ps.partial_impulse_orchestrator.current_impulse
        
        # Nivel 3: La Lucha de Mareas (MacdCycleData)
        if hasattr(ps, 'macd_cycle_orchestrator') and ps.macd_cycle_orchestrator.current_cycle:
            if ps.macd_cycle_orchestrator.current_cycle.active:
                periods["LuchaMareas"] = ps.macd_cycle_orchestrator.current_cycle

        # Nivel 4: La Corriente Oceánica 1m (TotalImpulseData)
        if hasattr(ps, 'total_impulse_orchestrator') and ps.total_impulse_orchestrator.current_impulse:
            if ps.total_impulse_orchestrator.current_impulse.active:
                periods["Corriente1m"] = ps.total_impulse_orchestrator.current_impulse

        # Nivel 5: La Fuerza Terrestre 1m (TotalTrendData)
        if hasattr(ps, 'total_trend_orchestrator') and ps.total_trend_orchestrator.current_trend:
            if ps.total_trend_orchestrator.current_trend.active:
                periods["Tierra1m"] = ps.total_trend_orchestrator.current_trend

        # === NIVELES 6-13: FUERZAS CÓSMICAS ===
        # Acceso a través del CosmicHierarchyMasterOrchestrator
        if hasattr(ps, 'cosmic_hierarchy_orchestrator'):
            cosmic = ps.cosmic_hierarchy_orchestrator
            
            # Nivel 6: La Fuerza Lunar 5m (GlobalTotalImpulseData)
            if cosmic.lunar_force.current_global_impulse and cosmic.lunar_force.current_global_impulse.active:
                periods["Luna5m"] = cosmic.lunar_force.current_global_impulse
            
            # Nivel 7: La Fuerza Solar 15m (GlobalTotalImpulseData)
            if cosmic.solar_force.current_global_impulse and cosmic.solar_force.current_global_impulse.active:
                periods["Sol15m"] = cosmic.solar_force.current_global_impulse
            
            # Nivel 8: La Fuerza del Sistema Solar 1h (GlobalTotalImpulseData)
            if cosmic.solar_system_force.current_global_impulse and cosmic.solar_system_force.current_global_impulse.active:
                periods["SistemaSolar1h"] = cosmic.solar_system_force.current_global_impulse
            
            # Nivel 9: La Fuerza de la Vía Láctea 4h (GlobalTotalImpulseData)
            if cosmic.milky_way_force.current_global_impulse and cosmic.milky_way_force.current_global_impulse.active:
                periods["ViaLactea4h"] = cosmic.milky_way_force.current_global_impulse
            
            # Nivel 10: La Fuerza del Grupo Local 5m (GlobalTotalTrendData)
            if cosmic.local_group_trend.current_global_trend and cosmic.local_group_trend.current_global_trend.active:
                periods["GrupoLocal5m"] = cosmic.local_group_trend.current_global_trend
            
            # Nivel 11: La Fuerza del Cúmulo de Virgo 15m (GlobalTotalTrendData)
            if cosmic.virgo_cluster_trend.current_global_trend and cosmic.virgo_cluster_trend.current_global_trend.active:
                periods["CumuloVirgo15m"] = cosmic.virgo_cluster_trend.current_global_trend
            
            # Nivel 12: La Fuerza de Andrómeda 1h (GlobalTotalTrendData)
            if cosmic.andromeda_trend.current_global_trend and cosmic.andromeda_trend.current_global_trend.active:
                periods["Andromeda1h"] = cosmic.andromeda_trend.current_global_trend
            
            # Nivel 13: La Fuerza del Universo 4h (GlobalTotalTrendData)
            if cosmic.universe_trend.current_global_trend and cosmic.universe_trend.current_global_trend.active:
                periods["Universo4h"] = cosmic.universe_trend.current_global_trend

        logger.debug(f"[{ps.symbol}] Recolectados {len(periods)} períodos activos de la jerarquía cósmica: {list(periods.keys())}")
        return periods

    def _calculate_derivatives(self, history: List[Decimal], timestamps: List[int]) -> Tuple[Decimal, Decimal, Decimal]:
        """Calcula velocidad, aceleración y jerk para un historial de datos."""
        if len(history) < 4: return ZERO, ZERO, ZERO
        try:
            dt1 = Decimal(timestamps[-1] - timestamps[-2]) / 1000
            dt2 = Decimal(timestamps[-2] - timestamps[-3]) / 1000
            dt3 = Decimal(timestamps[-3] - timestamps[-4]) / 1000
            if dt1 <= SAFE_DIVISION_THRESHOLD or dt2 <= SAFE_DIVISION_THRESHOLD or dt3 <= SAFE_DIVISION_THRESHOLD:
                return ZERO, ZERO, ZERO

            v_now = (history[-1] - history[-2]) / dt1
            v_prev = (history[-2] - history[-3]) / dt2
            v_before_prev = (history[-3] - history[-4]) / dt3

            a_now = (v_now - v_prev) / dt2
            a_prev = (v_prev - v_before_prev) / dt3
            
            jerk = (a_now - a_prev) / dt3
            return v_now, a_now, jerk
        except (IndexError, TypeError, ZeroDivisionError):
            return ZERO, ZERO, ZERO

    def _calculate_and_store_all_kinematics(self, all_periods: Dict[str, PeriodData]):
        """
        Calcula y guarda las métricas cinemáticas y sus picos para todos los períodos.
        """
        for period_data in all_periods.values():
            # --- Cinemática del Precio ---
            v, a, j = self._calculate_derivatives(period_data.price_history, period_data.timestamps)
            period_data.metrics.price_velocity = v
            period_data.metrics.price_acceleration = a
            period_data.metrics.price_jerk = j
            
            # --- Variación Neta Absoluta del Precio ---
            if len(period_data.price_history) >= 2:
                price_start = period_data.price_history[0]
                price_end = period_data.price_history[-1]
                period_data.metrics.price_variacion_neta_absoluta = abs(price_end - price_start)
            
            # Actualizar picos (se compara el valor absoluto)
            if abs(v) > abs(period_data.metrics.peak_price_velocity): period_data.metrics.peak_price_velocity = v
            if abs(a) > abs(period_data.metrics.peak_price_acceleration): period_data.metrics.peak_price_acceleration = a
            if abs(j) > abs(period_data.metrics.peak_price_jerk): period_data.metrics.peak_price_jerk = j

            # --- Cinemática del MACD (solo para Nivel Micro) ---
            if isinstance(period_data, MicroPeriodData):
                v_m, a_m, j_m = self._calculate_derivatives(period_data.macd_history, period_data.timestamps)
                period_data.metrics.macd_velocity = v_m
                period_data.metrics.macd_acceleration = a_m
                period_data.metrics.macd_jerk = j_m
                # Actualizar picos
                if abs(v_m) > abs(period_data.metrics.peak_macd_velocity): period_data.metrics.peak_macd_velocity = v_m
                if abs(a_m) > abs(period_data.metrics.peak_macd_acceleration): period_data.metrics.peak_macd_acceleration = a_m
                if abs(j_m) > abs(period_data.metrics.peak_macd_jerk): period_data.metrics.peak_macd_jerk = j_m

            # --- Cinemática de la EMA200 (solo para Nivel Macro) ---
            if isinstance(period_data, MacroPeriodData):
                v_e, a_e, j_e = self._calculate_derivatives(period_data.ema200_history, period_data.timestamps)
                period_data.metrics.ema200_velocity = v_e
                period_data.metrics.ema200_acceleration = a_e
                period_data.metrics.ema200_jerk = j_e
                # Actualizar picos
                if abs(v_e) > abs(period_data.metrics.peak_ema200_velocity): period_data.metrics.peak_ema200_velocity = v_e
                if abs(a_e) > abs(period_data.metrics.peak_ema200_acceleration): period_data.metrics.peak_ema200_acceleration = a_e
                if abs(j_e) > abs(period_data.metrics.peak_ema200_jerk): period_data.metrics.peak_ema200_jerk = j_e

    def _calculate_all_intra_period_matrices(self, all_periods: Dict[str, PeriodData]) -> Tuple[Dict, Dict]:
        """Calcula la matriz de alineamiento interno y el score de salud para cada período de la jerarquía cósmica."""
        intra_matrices, health_scores = {}, {}
        
        # Pesos cósmicos según la jerarquía de 13 niveles
        cosmic_level_weights = {
            "Ola": 0.8,
            "Marea": 1.0,
            "LuchaMareas": 1.2,
            "Corriente1m": 1.5,
            "Tierra1m": 1.8,
            "Luna5m": 2.0,
            "Sol15m": 2.5,
            "SistemaSolar1h": 3.0,
            "ViaLactea4h": 3.5,
            "GrupoLocal5m": 4.0,
            "CumuloVirgo15m": 4.2,
            "Andromeda1h": 4.5,
            "Universo4h": 5.0
        }

        for period_name, period_data in all_periods.items():
            metrics_to_align = period_data.metrics.model_dump()
            metric_names = [k for k, v in metrics_to_align.items() if isinstance(v, Decimal) and v != ZERO]
            if not metric_names: continue

            matrix = {name: {} for name in metric_names}
            total_weighted_alignment, total_weight = 0.0, 0.0
            
            # Peso cósmico del nivel actual
            cosmic_weight = cosmic_level_weights.get(period_name, 1.0)

            for i in range(len(metric_names)):
                for j in range(i, len(metric_names)):
                    name1, name2 = metric_names[i], metric_names[j]
                    val1, val2 = Decimal(str(metrics_to_align[name1])), Decimal(str(metrics_to_align[name2]))
                    
                    direction = 1.0 if (val1 > 0 and val2 > 0) or (val1 < 0 and val2 < 0) else -1.0
                    norm_mag1 = min(abs(val1) * 1000, ONE)
                    norm_mag2 = min(abs(val2) * 1000, ONE)
                    magnitude = float(norm_mag1 * norm_mag2)
                    score = direction * magnitude
                    
                    matrix[name1][name2] = matrix[name2][name1] = score
                    
                    if i != j:
                        # Aplicar peso cósmico a la métrica
                        combined_weight = cosmic_weight
                        total_weighted_alignment += score * combined_weight
                        total_weight += combined_weight
            
            intra_matrices[period_name] = matrix
            health_scores[period_name] = (total_weighted_alignment / total_weight) if total_weight > 0 else 0.0
        
        return intra_matrices, health_scores

    def _is_contained(self, period_A: PeriodData, period_B: PeriodData) -> bool:
        """
        Determina si el período A está temporalmente contenido dentro del período B.
        Ej: ¿Está este IT_1m dentro de la TT_1m actual?
        """
        if not period_A.active or not period_B.active:
            return False
        return period_B.entry_ts <= period_A.entry_ts and period_B.exit_ts >= period_A.exit_ts

    def _calculate_inter_period_matrices(self, health_scores: Dict[str, float], all_periods: Dict[str, PeriodData]) -> Tuple[Dict, Dict]:
        """
        Calcula el "Confluenciograma" (matrices inter-período) de la jerarquía cósmica,
        aplicando ponderación multifactorial que incluye la relevancia temporal.
        """
        inter_matrix: Dict[str, Dict[str, float]] = {}
        weighted_matrix: Dict[str, Dict[str, float]] = {}
        period_names = list(health_scores.keys())
        
        # Obtener los pesos cósmicos del config
        cosmic_weights = self.ranking_params.cosmic_weights

        for i in range(len(period_names)):
            for j in range(i, len(period_names)):
                name1, name2 = period_names[i], period_names[j]
                period_A, period_B = all_periods[name1], all_periods[name2]
                
                # --- 1. Cálculo del Score de Alineamiento Base ---
                direction = 1.0 if period_A.side == period_B.side and period_A.side != "indefinido" else -1.0 if period_A.side != period_B.side and period_A.side != "indefinido" and period_B.side != "indefinido" else 0.0
                magnitude = abs(health_scores.get(name1, 0.0) * health_scores.get(name2, 0.0))
                base_alignment_score = round(direction * magnitude, 4)
                
                # Rellenar la matriz de alineamiento puro
                inter_matrix.setdefault(name1, {})[name2] = base_alignment_score
                inter_matrix.setdefault(name2, {})[name1] = base_alignment_score
                
                # --- 2. Cálculo del Peso Multifactorial Dinámico ---
                
                # Factor 1: Peso Cósmico (la importancia intrínseca del período)
                cosmic_w1 = cosmic_weights.get(name1, 1.0)
                cosmic_w2 = cosmic_weights.get(name2, 1.0)
                cosmic_w = cosmic_w1 * cosmic_w2

                # Factor 2: Relevancia Temporal (¿qué fracción de B es A?)
                duration_A = (period_A.exit_ts - period_A.entry_ts) if period_A.exit_ts > period_A.entry_ts else 0
                duration_B = (period_B.exit_ts - period_B.entry_ts) if period_B.exit_ts > period_B.entry_ts else 0
                
                temporal_relevance = 1.0 # Por defecto, no hay reducción
                if self._is_contained(period_A, period_B) and duration_B > 0:
                    temporal_relevance = duration_A / duration_B
                elif self._is_contained(period_B, period_A) and duration_A > 0:
                    temporal_relevance = duration_B / duration_A
                
                # Factor 3: Feedback Loop (placeholder para el futuro)
                feedback_w = 1.0
                
                # --- 3. Cálculo del Score Ponderado Final ---
                final_weight = cosmic_w * temporal_relevance * feedback_w
                weighted_score = round(base_alignment_score * final_weight, 4)
                
                # Rellenar la matriz ponderada
                weighted_matrix.setdefault(name1, {})[name2] = weighted_score
                weighted_matrix.setdefault(name2, {})[name1] = weighted_score
                
        return inter_matrix, weighted_matrix

    def _calculate_final_scores(self, symbol: str, weighted_matrix: Dict, health_scores: Dict) -> Dict[str, Any]:
        """
        Calcula los scores finales, incluyendo el sismógrafo de supernovas.
        """
        results = {
            "global_alignment_score": 0.0,
            "final_signal_quality_score": 0.0,
            "side_struggle_score": 0.0,
            "struggle_score_velocity": 0.0,
            "struggle_score_acceleration": 0.0
        }
        if not weighted_matrix: return results
            
        # 1. Calcular Global Alignment y Final Signal Quality
        all_scores = [score for row in weighted_matrix.values() for score in row.values()]
        global_alignment_score = float(np.mean(all_scores)) if all_scores else 0.0
        
        health_values = [s for s in health_scores.values() if s > 0]
        health_score_prod = float(np.prod(health_values)) if health_values else 0.0
        
        final_signal_quality_score = global_alignment_score * health_score_prod
        
        # 2. Calcular el Side Struggle Score (-100 a +100)
        # Es el mismo global_alignment_score, pero re-escalado.
        side_struggle_score = global_alignment_score * 100.0

        # 3. Calcular Derivadas del Struggle Score (El Sismógrafo)
        now_ts = int(time.time() * 1000)
        if symbol not in self.struggle_score_history:
            self.struggle_score_history[symbol] = []
        
        history = self.struggle_score_history[symbol]
        history.append((now_ts, side_struggle_score))
        # Mantener solo los últimos N puntos para el cálculo (ej. 10)
        if len(history) > 10:
            history.pop(0)

        # Usamos la misma función de derivadas, pero con floats
        score_values = [Decimal(str(s[1])) for s in history]
        score_ts = [s[0] for s in history]
        
        v, a, _ = self._calculate_derivatives(score_values, score_ts)

        results.update({
            "global_alignment_score": global_alignment_score,
            "final_signal_quality_score": final_signal_quality_score,
            "side_struggle_score": side_struggle_score,
            "struggle_score_velocity": float(v),
            "struggle_score_acceleration": float(a)
        })
        
        return results

__all__ = [ 
    "MetricsManager"
]