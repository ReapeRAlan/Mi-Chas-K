#!/usr/bin/env python3
"""
Script de debug para la función de adaptación
"""

import sys
import os
sys.path.insert(0, os.getcwd())

from database.connection_adapter import DatabaseAdapter
from decimal import Decimal

def main():
    adapter = DatabaseAdapter()

    # Test data exactamente como en el test
    test_data = {
        'precio': Decimal('25.50'),
        'cantidad': True,
        'descuento': Decimal('0.00'),
        'activo': False,
        'stock_reduction': 5,
        'nombre': 'Producto Test'
    }

    print('📋 Datos originales:')
    for k, v in test_data.items():
        print(f'  {k}: {v} ({type(v).__name__})')

    print('\n🔄 Adaptando para detalle_ventas...')
    adapted = adapter._adapt_data_for_remote(test_data, 'detalle_ventas')

    print('\n📋 Datos adaptados:')
    for k, v in adapted.items():
        print(f'  {k}: {v} ({type(v).__name__})')

    # Verificar condiciones del test
    print('\n🧪 Verificaciones:')
    print(f'stock_reduction eliminado: {"stock_reduction" not in adapted}')
    print(f'cantidad es int: {isinstance(adapted.get("cantidad"), int)}')
    print(f'precio es float: {isinstance(adapted.get("precio"), float)}')
    
    # Test de limpieza JSON
    print('\n🧪 Test limpieza JSON:')
    cleaned = adapter._clean_data_for_json(test_data)
    print('📋 Datos limpiados para JSON:')
    for k, v in cleaned.items():
        print(f'  {k}: {v} ({type(v).__name__})')

if __name__ == '__main__':
    main()
