"""
LÓGICA CORRECTA PARA EL DASHBOARD - BASADA EN DATOS REALES

Según el análisis de datos reales del 2025-06-13:
- Ventas: $2521.00
- Gastos: $2467.00
- Dinero inicial: $0.00
- Dinero final: $1960.00
- Diferencia registrada: $2301.00 (INCORRECTA)

FÓRMULA CORRECTA:
Sistema: Ingresos - Gastos = $2521 - $2467 = $54
Caja: (Final - Inicial) - Gastos = ($1960 - $0) - $2467 = -$507
Diferencia: Sistema - Caja = $54 - (-$507) = $561

La diferencia registrada ($2301) está incorrecta por $1740.
"""

def calcular_logica_correcta_dashboard(ventas_totales, gastos_totales, dinero_inicial, dinero_final):
    """
    Calcula la lógica correcta del dashboard basada en principios contables
    
    Args:
        ventas_totales: Total de ventas del sistema
        gastos_totales: Total de gastos del sistema  
        dinero_inicial: Dinero con el que inició la caja
        dinero_final: Dinero físico al final del día
    
    Returns:
        dict con los resultados del análisis
    """
    
    # LADO SISTEMA: Lo que debería haber según las operaciones registradas
    resultado_sistema = ventas_totales - gastos_totales
    
    # LADO CAJA: Lo que realmente pasó con el dinero físico
    # (Dinero final - Dinero inicial) representa el incremento/decremento real de la caja
    # Luego restamos los gastos porque estos salen de la caja
    incremento_caja = dinero_final - dinero_inicial
    resultado_caja = incremento_caja - gastos_totales
    
    # DIFERENCIA: Sistema vs Realidad
    diferencia = resultado_sistema - resultado_caja
    
    return {
        'sistema': {
            'ingresos': ventas_totales,
            'gastos': gastos_totales,
            'resultado': resultado_sistema
        },
        'caja': {
            'inicial': dinero_inicial,
            'final': dinero_final,
            'incremento': incremento_caja,
            'gastos': gastos_totales,
            'resultado': resultado_caja
        },
        'diferencia': diferencia,
        'analisis': {
            'estado': 'perfecto' if abs(diferencia) < 0.01 else 'sobra' if diferencia > 0 else 'falta',
            'magnitud': abs(diferencia),
            'descripcion': get_descripcion_diferencia(diferencia)
        }
    }

def get_descripcion_diferencia(diferencia):
    """Descripción de la diferencia encontrada"""
    if abs(diferencia) < 0.01:
        return "✅ Caja perfectamente cuadrada"
    elif diferencia > 0:
        return f"⚠️ Falta dinero en caja: ${diferencia:.2f}"
    else:
        return f"💰 Sobra dinero en caja: ${abs(diferencia):.2f}"

# EJEMPLO CON DATOS REALES:
if __name__ == "__main__":
    # Datos del 2025-06-13
    resultado = calcular_logica_correcta_dashboard(
        ventas_totales=2521.00,
        gastos_totales=2467.00, 
        dinero_inicial=0.00,
        dinero_final=1960.00
    )
    
    print("ANÁLISIS CON DATOS REALES 2025-06-13:")
    print("=" * 50)
    print(f"SISTEMA: ${resultado['sistema']['ingresos']:.2f} - ${resultado['sistema']['gastos']:.2f} = ${resultado['sistema']['resultado']:.2f}")
    print(f"CAJA: (${resultado['caja']['final']:.2f} - ${resultado['caja']['inicial']:.2f}) - ${resultado['caja']['gastos']:.2f} = ${resultado['caja']['resultado']:.2f}")
    print(f"DIFERENCIA: ${resultado['diferencia']:.2f}")
    print(f"ANÁLISIS: {resultado['analisis']['descripcion']}")
