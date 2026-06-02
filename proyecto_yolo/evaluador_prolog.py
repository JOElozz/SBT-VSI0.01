from pyswip import Prolog

class EvaluadorProlog:
    def __init__(self, ruta_reglas):
        self.prolog = Prolog()
        self.prolog.consult(ruta_reglas)

    def evaluar_fase(self, zona, detectados):
        """
        Pregunta a Prolog si la fase fue aprobada.
        zona      : string  — 'cabeza', 'torso', 'manos', 'botas'
        detectados: lista   — ['helmet', 'glass']
        Retorna   : (bool, lista de faltantes)
        """
        # Convertir zona y detectados al formato Prolog
        zona_pl = zona.lower()
        detectados_pl = "[" + ",".join(detectados) + "]"

        query = f"fase_aprobada({zona_pl}, {detectados_pl})"

        try:
            resultado = list(self.prolog.query(query))
            if resultado:
                return True, []
            else:
                # Calcular qué falta
                faltantes = self._obtener_faltantes(zona_pl, detectados)
                return False, faltantes
        except Exception as e:
            print(f"Error Prolog: {e}")
            return False, []

    def _obtener_faltantes(self, zona, detectados):
        """Consulta a Prolog qué EPP se requiere y calcula la diferencia"""
        query = f"epp_requerido({zona}, Requeridos)"
        resultados = list(self.prolog.query(query))
        if resultados:
            requeridos = resultados[0]["Requeridos"]
            return [r for r in requeridos if r not in detectados]
        return []