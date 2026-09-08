"""
MÓDULO DE COMBOS - SISTEMA DE PRODUCCIÓN INTEGRAL (SPI DESPIECE)
Contiene la definición del catálogo de combos, gramajes nominales por corte,
cálculo de bandejas estimativas, control estricto de tolerancias (+/- 5%)
y validaciones de completitud antes del cierre de proceso.
"""

from typing import Dict, List, Any, Optional, Tuple

TOLERANCIA_DEFECTO_PCT = 5.0  # Tolerancia estándar de porcionado (+/- 5.0%)

CATALOGO_COMBOS: Dict[str, Dict[str, Any]] = {
    "ASADO_3KG": {
        "id": "ASADO_3KG",
        "nombre": "1. Asado (3 kg)",
        "nombre_corto": "Asado (3 kg)",
        "codigo_producto": "01030002",
        "descripcion_csv": "Asado",
        "peso_nominal": 3.00,
        "cortes": {
            "Tapa de asado": {"peso_unitario": 1.10, "codigo": "01030055"},
            "Costeleta al traves": {"peso_unitario": 0.50, "codigo": "01030024"},
            "Costilla - Pechito": {"peso_unitario": 0.89, "codigo": "01030025"},
            "Chorizo de cerdo": {"peso_unitario": 0.29, "codigo": "01040006"},
            "Morcilla bombon": {"peso_unitario": 0.23, "codigo": "01050005"},
        }
    },
    "ASADO_PREMIUM_4KG": {
        "id": "ASADO_PREMIUM_4KG",
        "nombre": "2. Asado premium (4 Kg.)",
        "nombre_corto": "Asado premium (4 Kg.)",
        "codigo_producto": "01030003",
        "descripcion_csv": "Asado premium",
        "peso_nominal": 4.00,
        "cortes": {
            "Matambre de cerdo": {"peso_unitario": 0.90, "codigo": "01030035"},
            "Tapa de asado": {"peso_unitario": 1.10, "codigo": "01030055"},
            "Costilla - Pechito": {"peso_unitario": 1.00, "codigo": "01030025"},
            "Costeleta al traves": {"peso_unitario": 0.45, "codigo": "01030024"},
            "Chorizo de cerdo": {"peso_unitario": 0.35, "codigo": "01040006"},
            "Morcilla bombon": {"peso_unitario": 0.20, "codigo": "01050005"},
        }
    },
    "OFERTA_ASADO_2_5KG": {
        "id": "OFERTA_ASADO_2_5KG",
        "nombre": "3. Oferta asado 2 (2.5 kg)",
        "nombre_corto": "Oferta asado 2 (2.5 kg)",
        "codigo_producto": "01030039",
        "descripcion_csv": "Oferta asado 2",
        "peso_nominal": 2.50,
        "cortes": {
            "Chuleta de paleta": {"peso_unitario": 2.00, "codigo": "01030018"},
            "Chorizo de cerdo": {"peso_unitario": 0.50, "codigo": "01040006"},
        }
    },
    "OFERTA_ASADO_2KG": {
        "id": "OFERTA_ASADO_2KG",
        "nombre": "4. Oferta asado 2Kg. (2 kg)",
        "nombre_corto": "Oferta asado 2Kg. (2 kg)",
        "codigo_producto": "01030038",
        "descripcion_csv": "Oferta asado 2Kg.",
        "peso_nominal": 2.00,
        "cortes": {
            "Costilla - Pechito": {"peso_unitario": 1.50, "codigo": "01030025"},
            "Chorizo de cerdo": {"peso_unitario": 0.50, "codigo": "01040006"},
        }
    },
    "COMBO_SEMANAL_4KG": {
        "id": "COMBO_SEMANAL_4KG",
        "nombre": "5. Combo semanal (4 Kg.)",
        "nombre_corto": "Combo semanal (4 Kg.)",
        "codigo_producto": "01030021",
        "descripcion_csv": "Combo semanal",
        "peso_nominal": 4.005,
        "cortes": {
            "Milanesa de cerdo": {"peso_unitario": 0.700, "codigo": "01040012"},
            "Costeleta": {"peso_unitario": 0.700, "codigo": "01030023"},
            "Picada especial": {"peso_unitario": 1.000, "codigo": "01030047"},
            "Chuleta de cerdo con cuero": {"peso_unitario": 1.605, "codigo": "01030016"},
        }
    },
    "COMBO_LOCRO_3KG": {
        "id": "COMBO_LOCRO_3KG",
        "nombre": "6. Combo locro (3 kg)",
        "nombre_corto": "Combo locro (3 kg)",
        "codigo_producto": "01030020",
        "descripcion_csv": "Combo locro ",
        "peso_nominal": 3.000,
        "cortes": {
            "Chuleta de paleta": {"peso_unitario": 1.000, "codigo": "01030018"},
            "Caracu": {"peso_unitario": 1.000, "codigo": "01030013"},
            "Chorizo de cerdo": {"peso_unitario": 1.000, "codigo": "01040006"},
        }
    },
    "COMBO_LOCRO_PREMIUM_3_5KG": {
        "id": "COMBO_LOCRO_PREMIUM_3_5KG",
        "nombre": "7. Locro Premium (3.5 kg)",
        "nombre_corto": "Locro Premium (3.5 kg)",
        "codigo_producto": "01030086",
        "descripcion_csv": "Combo locro Premium",
        "peso_nominal": 3.500,
        "cortes": {
            "Chuleta de paleta": {"peso_unitario": 1.500, "codigo": "01030018"},
            "Caracu": {"peso_unitario": 1.000, "codigo": "01030013"},
            "Chorizo de cerdo": {"peso_unitario": 0.500, "codigo": "01040006"},
            "Panceta": {"peso_unitario": 0.500, "codigo": "01030043"},
        }
    }
}


class ComboManager:
    """Gestiona cálculos de bandejas, tolerancias y validaciones de recetas de combos."""

    ALIASES = {
        "ASADO_ECONOMICO_2_5KG": "OFERTA_ASADO_2_5KG",
        "ASADO_2KG": "OFERTA_ASADO_2KG",
    }

    @staticmethod
    def get_combo(combo_id: str) -> Optional[Dict[str, Any]]:
        real_id = ComboManager.ALIASES.get(combo_id, combo_id)
        return CATALOGO_COMBOS.get(real_id)

    @staticmethod
    def get_lista_combos() -> List[Dict[str, Any]]:
        return list(CATALOGO_COMBOS.values())

    @staticmethod
    def calcular_bandejas_estimadas(combo_id: str, corte_nombre: str, peso_pesado: float) -> int:
        combo = ComboManager.get_combo(combo_id)
        if not combo:
            return 0

        corte_info = combo["cortes"].get(corte_nombre)
        if not corte_info:
            return 0

        peso_unitario = corte_info["peso_unitario"]
        if peso_unitario <= 0 or peso_pesado <= 0:
            return 0

        # Las bandejas siempre deben ser un número redondo (entero)
        bandejas_calc = peso_pesado / peso_unitario
        return max(1, int(round(bandejas_calc)))

    @staticmethod
    def calcular_pesos_esperados(combo_id: str, bandejas: float) -> Dict[str, float]:
        combo = ComboManager.get_combo(combo_id)
        if not combo:
            return {}

        resultado = {}
        # Asegurar número entero redondo de bandejas para que el peso teórico
        # siempre sea un múltiplo exacto del valor de la fórmula
        bandejas_redondas = int(round(bandejas))
        for corte, info in combo["cortes"].items():
            resultado[corte] = round(bandejas_redondas * info["peso_unitario"], 2)
        return resultado

    @staticmethod
    def evaluar_tolerancia(
        peso_real: float,
        peso_esperado: float,
        tolerancia_pct: float = TOLERANCIA_DEFECTO_PCT
    ) -> Dict[str, Any]:
        if peso_esperado <= 0:
            return {
                "en_tolerancia": True,
                "desvio_pct": 0.0,
                "diferencia_kg": 0.0,
                "alerta": False,
                "mensaje": "Peso esperado es cero."
            }

        diferencia_kg = round(peso_real - peso_esperado, 2)
        desvio_pct = round((diferencia_kg / peso_esperado) * 100.0, 2)
        desvio_abs = abs(desvio_pct)
        en_tolerancia = desvio_abs <= tolerancia_pct

        if en_tolerancia:
            mensaje = f"Dentro de tolerancia ({desvio_pct:+.1f}% | {diferencia_kg:+.2f} kg)"
        else:
            if desvio_pct < 0:
                mensaje = f"⚠️ FALTANTE EXCESIVO ({desvio_pct:.1f}% | Faltan {abs(diferencia_kg):.2f} kg)"
            else:
                mensaje = f"⚠️ EXCESO DE MATERIA ({desvio_pct:+.1f}% | Sobran {diferencia_kg:.2f} kg)"

        return {
            "en_tolerancia": en_tolerancia,
            "desvio_pct": desvio_pct,
            "diferencia_kg": diferencia_kg,
            "alerta": not en_tolerancia,
            "mensaje": mensaje
        }

    @staticmethod
    def validar_completitud(combo_id: str, cortes_pesados: Dict[str, float]) -> Tuple[bool, List[str]]:
        combo = ComboManager.get_combo(combo_id)
        if not combo:
            return False, []

        cortes_requeridos = set(combo["cortes"].keys())
        cortes_registrados = {c for c, p in cortes_pesados.items() if p > 0}
        faltantes = list(cortes_requeridos - cortes_registrados)

        return len(faltantes) == 0, sorted(faltantes)

    @staticmethod
    def validar_finalizacion(
        combo_id: str,
        bandejas_estimadas: float,
        pesajes: Dict[str, float],
        tolerancia_pct: float = TOLERANCIA_DEFECTO_PCT
    ) -> Dict[str, Any]:
        completo, faltantes = ComboManager.validar_completitud(combo_id, pesajes)
        if not completo:
            return {
                "puede_finalizar": False,
                "motivo": "FALTAN_CORTES",
                "mensaje": f"No se pesó la totalidad de cortes del combo. Faltan: {', '.join(faltantes)}",
                "cortes_faltantes": faltantes,
                "cortes_fuera_tolerancia": [],
                "requiere_supervisor": False
            }

        pesos_esperados = ComboManager.calcular_pesos_esperados(combo_id, bandejas_estimadas)
        fuera_tolerancia = []

        for corte, peso_real in pesajes.items():
            peso_esp = pesos_esperados.get(corte, 0.0)
            res_tol = ComboManager.evaluar_tolerancia(peso_real, peso_esp, tolerancia_pct)
            if not res_tol["en_tolerancia"]:
                fuera_tolerancia.append({
                    "corte": corte,
                    "peso_real": peso_real,
                    "peso_esperado": peso_esp,
                    "desvio_pct": res_tol["desvio_pct"],
                    "diferencia_kg": res_tol["diferencia_kg"],
                    "mensaje": res_tol["mensaje"]
                })

        if fuera_tolerancia:
            mensajes_detalles = [f"• {item['corte']}: {item['mensaje']}" for item in fuera_tolerancia]
            return {
                "puede_finalizar": False,
                "motivo": "FUERA_DE_TOLERANCIA",
                "mensaje": "Diferencia excesiva respecto a la fórmula del combo:\n" + "\n".join(mensajes_detalles),
                "cortes_faltantes": [],
                "cortes_fuera_tolerancia": fuera_tolerancia,
                "requiere_supervisor": True
            }

        return {
            "puede_finalizar": True,
            "motivo": "OK",
            "mensaje": f"Combo verificado con éxito. Total bandejas: {int(round(bandejas_estimadas))}",
            "cortes_faltantes": [],
            "cortes_fuera_tolerancia": [],
            "requiere_supervisor": False
        }
