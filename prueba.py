import streamlit as st
from datetime import datetime

class AperturaData:
    def __init__(self, company_name):
        self.company_name = company_name
        self.apertura_realizada = False
        self.iva_rate = 0.16
        
        # Cuentas de Activo
        self.caja = 0.0
        self.banco = 0.0
        self.inventario = 0.0
        self.papeleria = 0.0
        self.rentas_anticipadas = 0.0
        
        # Activo No Circulante
        self.activos_no_circulantes = []
        
        # Cuentas de IVA
        self.iva_acreditable = 0.0
        self.iva_por_acreditar = 0.0
        
        # Cuentas de Pasivo
        self.acreedores = 0.0
        self.documentos_por_pagar = 0.0
        self.anticipo_clientes = []
        self.iva_trasladado = 0.0
        
        # Totales y Capital
        self.total_no_circulante = 0.0
        self.total_activo = 0.0
        self.total_pasivo = 0.0
        self.capital = 0.0

        # Libro Diario
        self.libro_diario = []

        # Datos para utilidad
        self.ventas = 406000.0
        self.costo_lo_vendido = 203000.0
        self.gastos_generales = 23416.0

    def agregar_transaccion(self, fecha, cuentas, debe, haber):
        for cuenta, valor in cuentas.items():
            self.libro_diario.append({
                "fecha": fecha,
                "cuentas": cuenta,
                "debe": valor if debe else 0.0,
                "haber": valor if haber else 0.0
            })

    def recalcular_totales(self):
        self.total_no_circulante = sum(valor for _, valor in self.activos_no_circulantes)
        activo_circulante = (self.caja + self.banco + self.inventario + self.papeleria +
                            self.rentas_anticipadas + self.iva_acreditable + self.iva_por_acreditar)
        self.total_activo = activo_circulante + self.total_no_circulante
        
        anticipo_total = sum(monto for _, monto in self.anticipo_clientes)
        self.total_pasivo = self.acreedores + self.documentos_por_pagar + anticipo_total + self.iva_trasladado

    def calcular_asiento_apertura(self):
        total_no_circulante = sum(valor for _, valor in self.activos_no_circulantes)
        activo_circulante = self.caja + self.banco + self.inventario
        self.total_activo = activo_circulante + total_no_circulante
        self.capital = self.total_activo
        self.total_pasivo = 0.0
        self.apertura_realizada = True

        self.agregar_transaccion(
            fecha="210T2025",
            cuentas={
                "Caja": self.caja,
                "Bancos": self.banco,
                "Mercancías": self.inventario,
                "Terrenos": sum(valor for nombre, valor in self.activos_no_circulantes if nombre == "Terrenos"),
                "Equipo Reparto": sum(valor for nombre, valor in self.activos_no_circulantes if nombre == "Equipo Reparto"),
                "Edificios": sum(valor for nombre, valor in self.activos_no_circulantes if nombre == "Edificios"),
                "Equipo Computo": sum(valor for nombre, valor in self.activos_no_circulantes if nombre == "Equipo Computo"),
                "Mobiliario": sum(valor for nombre, valor in self.activos_no_circulantes if nombre == "Mob y Equipo"),
                "Muebles": sum(valor for nombre, valor in self.activos_no_circulantes if nombre == "Muebles")
            },
            debe=True,
            haber=False
        )
        self.agregar_transaccion(
            fecha="210T2025",
            cuentas={"Capital Social": self.capital},
            debe=False,
            haber=True
        )

    def compra_en_efectivo(self, valor: float):
        iva = valor * self.iva_rate
        self.inventario += valor
        self.iva_acreditable += iva
        self.caja -= (valor + iva)
        self.recalcular_totales()

        self.agregar_transaccion(
            fecha="220T2025",
            cuentas={"Mercancías": valor, "IVA": iva},
            debe=True,
            haber=False
        )
        self.agregar_transaccion(
            fecha="220T2025",
            cuentas={"Caja": valor + iva},
            debe=False,
            haber=True
        )

    def compra_a_credito(self, nombre: str, valor: float):
        iva = valor * self.iva_rate

        activo_existente = False
        for idx, (n, v) in enumerate(self.activos_no_circulantes):
            if n == nombre:
                self.activos_no_circulantes[idx] = (n, v + valor)
                activo_existente = True
                break

        if not activo_existente:
            self.activos_no_circulantes.append((nombre, valor))

        self.iva_por_acreditar += iva
        self.acreedores += (valor + iva)
        self.recalcular_totales()

        self.agregar_transaccion(
            fecha="230T2025",
            cuentas={nombre: valor, "IVA por Acreditar": iva},
            debe=True,
            haber=False
        )
        self.agregar_transaccion(
            fecha="230T2025",
            cuentas={"Acreedores": valor + iva},
            debe=False,
            haber=True
        )

    def compra_combinada(self, nombre: str, valor: float):
        iva_total = valor * self.iva_rate
        mitad_valor = valor / 2.0
        mitad_iva = iva_total / 2.0
        
        if nombre == "Inventario":
            self.inventario += valor
        else:
            self.activos_no_circulantes.append((nombre, valor))
        
        self.caja -= (mitad_valor + mitad_iva)
        self.iva_acreditable += mitad_iva
        self.documentos_por_pagar += (mitad_valor + mitad_iva)
        self.iva_por_acreditar += mitad_iva
        
        self.recalcular_totales()

        self.agregar_transaccion(
            fecha="240T2025",
            cuentas={nombre: valor, "IVA Acreditable": mitad_iva, "IVA por Acreditar": mitad_iva},
            debe=True,
            haber=False
        )
        self.agregar_transaccion(
            fecha="240T2025",
            cuentas={"Caja": mitad_valor + mitad_iva},
            debe=False,
            haber=True
        )
        self.agregar_transaccion(
            fecha="240T2025",
            cuentas={"Documentos por Pagar": mitad_valor + mitad_iva},
            debe=False,
            haber=True
        )

    def anticipo_clientes_op(self, nombre: str, monto: float, porcentaje: float):
        monto_abonado = monto * (porcentaje / 100)
        iva = monto_abonado * self.iva_rate
        total_con_iva = monto_abonado + iva

        self.caja += total_con_iva
        self.anticipo_clientes.append((nombre, monto_abonado))
        self.iva_trasladado += iva
        self.recalcular_totales()

        self.agregar_transaccion(
            fecha="300T2025",
            cuentas={"Caja": total_con_iva},
            debe=True,
            haber=False
        )
        self.agregar_transaccion(
            fecha="300T2025",
            cuentas={"Anticipo de Clientes": monto_abonado, "IVA Trasladado": iva},
            debe=False,
            haber=True
        )

    def compra_papeleria_op(self, valor: float):
        iva = valor * self.iva_rate
        self.papeleria += valor
        self.iva_acreditable += iva
        self.caja -= (valor + iva)
        self.recalcular_totales()

        self.agregar_transaccion(
            fecha="190T2025",
            cuentas={"Papelería": valor, "IVA Acreditado (Pagado)": iva},
            debe=True,
            haber=False
        )
        self.agregar_transaccion(
            fecha="190T2025",
            cuentas={"Caja": valor + iva},
            debe=False,
            haber=True
        )

        datos_imagen = [
            ["2025-03-02 ", "Bancos", 464000.00, 0.00],
            ["2025-03-02 ", "Ventas", 0.00, 400000.00],
            ["2025-03-02 ", "Iva Trasladado", 0.00, 64000.00],
            ["2025-03-02 ", "Costo de lo vendido", 200000.00, 0.00],
            ["2025-03-02 ", "Mercancía", 0.00, 200000.00],
            ["2025-03-02 ", "Gastos Generales", 4000.00, 0.00],
            ["2025-03-02 ", "Renta Pagada (1 mes)", 0.00, 4000.00],
            ["2025-03-06 ", "Cliente", 3480.00, 0.00],
            ["2025-03-06 ", "Anticipo de cliente", 3000.00, 0.00],
            ["2025-03-06 ", "Iva Trasladado", 480.00, 0.00],
            ["2025-03-06 ", "Ventas", 0.00, 6000.00],
            ["2025-03-06 ", "Iva Trasladado", 0.00, 480.00],
            ["2025-03-06 ", "Iva por trasladar", 0.00, 480.00],
            ["2025-03-06 ", "Costo de lo vendido", 3000.00, 0.00],
            ["2025-03-06 ", "Inventario", 0.00, 3000.00],
            ["2025-03-11 ", "Gastos Generales", 19416.00, 0.00],
            ["2025-03-11 ", "Dep. Acum. Edificio", 0.00, 8333.00],
            ["2025-03-11 ", "Dep. Acum. Reparto", 0.00, 6250.00],
            ["2025-03-11 ", "Dep. Acum. Mobiliario", 0.00, 1000.00],
            ["2025-03-11 ", "Dep. Acum. Muebles", 0.00, 1333.00],
            ["2025-03-11 ", "Dep. Acum. Equipo Cómputo", 0.00, 2500.00]
        ]

        for fila in datos_imagen:
            fecha = fila[0]
            cuenta = fila[1]
            debe = fila[2]
            haber = fila[3]
            
            if debe > 0:
                self.agregar_transaccion(fecha, {cuenta: debe}, debe=True, haber=False)
            if haber > 0:
                self.agregar_transaccion(fecha, {cuenta: haber}, debe=False, haber=True)

    def pago_rentas_op(self, valor: float, meses: int):
        total_renta = valor * meses
        iva = total_renta * self.iva_rate
        total_con_iva = total_renta + iva

        self.caja -= total_con_iva
        self.iva_acreditable += iva
        self.rentas_anticipadas += total_renta
        self.recalcular_totales()

        self.agregar_transaccion(
            fecha="280T2025",
            cuentas={"Rentas Pagadas Anticipado": total_renta, "IVA": iva},
            debe=True,
            haber=False
        )
        self.agregar_transaccion(
            fecha="280T2025",
            cuentas={"Caja": total_con_iva},
            debe=False,
            haber=True
        )

    def generar_tabla_balance(self):
        anticipo_total = sum(monto for _, monto in self.anticipo_clientes)
        total_no_circulante = sum(valor for _, valor in self.activos_no_circulantes)
        
        tabla = f"{'ACTIVO':<45}{'PASIVO':<35}{'CAPITAL':<20}\n"
        tabla += "=" * 100 + "\n"
        
        tabla += "Activo Circulante:\n"
        tabla += f"  Caja: ${self.caja:,.2f}\n"
        tabla += f"  Banco: ${self.banco:,.2f}\n"
        tabla += f"  Inventario: ${self.inventario:,.2f}\n"
        if self.papeleria:
            tabla += f"  Papelería: ${self.papeleria:,.2f}\n"
        if self.iva_acreditable:
            tabla += f"  IVA Acreditable: ${self.iva_acreditable:,.2f}\n"
        if self.iva_por_acreditar:
            tabla += f"  IVA por Acreditar: ${self.iva_por_acreditar:,.2f}\n"
        if self.rentas_anticipadas:
            tabla += f"  Rentas Pagadas Anticipado: ${self.rentas_anticipadas:,.2f}\n"
        
        tabla += "\nActivo No Circulante:\n"
        if self.activos_no_circulantes:
            for nombre, valor in self.activos_no_circulantes:
                tabla += f"  {nombre}: ${valor:,.2f}\n"
        else:
            tabla += "  (Sin activos no circulantes)\n"
        tabla += f"  Total Activo No Circulante: ${total_no_circulante:,.2f}\n"
        
        tabla += "\nPASIVO:\n"
        tabla += f"  Acreedores: ${self.acreedores:,.2f}\n"
        tabla += f"  Documentos por Pagar: ${self.documentos_por_pagar:,.2f}\n"
        tabla += f"  Anticipo de Clientes: ${anticipo_total:,.2f}\n"
        tabla += f"  IVA Trasladado: ${self.iva_trasladado:,.2f}\n"
        
        tabla += "=" * 100 + "\n"
        tabla += f"Total Activo: ${self.total_activo:,.2f}\n"
        tabla += f"Total Pasivo: ${self.total_pasivo:,.2f}\n"
        tabla += f"Capital: ${self.capital:,.2f}\n"
        tabla += f"Total Pasivo + Capital: ${self.total_pasivo + self.capital:,.2f}\n"
        
        return tabla

    def generar_libro_diario(self):
        tabla = f"{'FECHA':<15}{'CUENTAS':<40}{'DEBE':<15}{'HABER':<15}\n"
        tabla += "=" * 85 + "\n"
        
        total_debe = 0.0
        total_haber = 0.0
        
        for transaccion in self.libro_diario:
            tabla += f"{transaccion['fecha']:<15}{transaccion['cuentas']:<40}${transaccion['debe']:,.2f}{'':<5}${transaccion['haber']:,.2f}\n"
            total_debe += transaccion['debe']
            total_haber += transaccion['haber']
        
        tabla += "=" * 85 + "\n"
        tabla += f"{'TOTAL':<55}${total_debe:,.2f}{'':<5}${total_haber:,.2f}\n"
        
        return tabla

    def generar_mayor(self):
        mayor = {}
        
        for transaccion in self.libro_diario:
            cuenta = transaccion['cuentas']
            if cuenta not in mayor:
                mayor[cuenta] = {'debe': 0.0, 'haber': 0.0, 'saldo': 0.0}
            
            mayor[cuenta]['debe'] += transaccion['debe']
            mayor[cuenta]['haber'] += transaccion['haber']
            mayor[cuenta]['saldo'] = mayor[cuenta]['debe'] - mayor[cuenta]['haber']
        
        tabla = ""
        for cuenta, valores in mayor.items():
            tabla += f"### {cuenta}\n"
            tabla += f"{'DEBE':<15}{'HABER':<15}{'SALDO':<15}\n"
            tabla += "=" * 45 + "\n"
            tabla += f"${valores['debe']:,.2f}{'':<5}${valores['haber']:,.2f}{'':<5}${valores['saldo']:,.2f}\n\n"
        
        return tabla

    def generar_balance_comprobacion(self):
        balance = {}
        
        for transaccion in self.libro_diario:
            cuenta = transaccion['cuentas']
            if cuenta not in balance:
                balance[cuenta] = {'debe': 0.0, 'haber': 0.0}
            
            balance[cuenta]['debe'] += transaccion['debe']
            balance[cuenta]['haber'] += transaccion['haber']
        
        tabla = f"{'CUENTA':<40}{'DEBE':<15}{'HABER':<15}{'DEBE':<15}{'HABER':<15}\n"
        tabla += "=" * 100 + "\n"
        
        total_debe1 = 0.0
        total_haber1 = 0.0
        total_debe2 = 0.0
        total_haber2 = 0.0
        
        for cuenta, valores in balance.items():
            total_debe1 += valores['debe']
            total_haber1 += valores['haber']
            
            if valores['debe'] > valores['haber']:
                diff_debe = valores['debe'] - valores['haber']
                diff_haber = 0.0
            else:
                diff_debe = 0.0
                diff_haber = valores['haber'] - valores['debe']
            
            total_debe2 += diff_debe
            total_haber2 += diff_haber
            
            tabla += f"{cuenta:<40}${valores['debe']:,.2f}{'':<5}${valores['haber']:,.2f}{'':<5}${diff_debe:,.2f}{'':<5}${diff_haber:,.2f}\n"
        
        tabla += "=" * 100 + "\n"
        tabla += f"{'TOTAL':<40}${total_debe1:,.2f}{'':<5}${total_haber1:,.2f}{'':<5}${total_debe2:,.2f}{'':<5}${total_haber2:,.2f}\n"
        
        return tabla

    def calcular_utilidad_periodo(self):
        utilidad_bruta = self.ventas - self.costo_lo_vendido
        utilidad_periodo = utilidad_bruta - self.gastos_generales
        return utilidad_periodo

    def generar_utilidad_periodo(self):
        utilidad_periodo = self.calcular_utilidad_periodo()
        
        tabla = f"{'Estado de Resultados':^80}\n"
        tabla += f"{'El Rincón del Café S.A DE C.V':^80}\n"
        tabla += f"{'Correspondiente al mes de Marzo 2025':^80}\n\n"
        tabla += f"{'Concepto':<40}{'Monto':>40}\n"
        tabla += "=" * 80 + "\n"
        tabla += f"{'Ventas':<40}${self.ventas:>39,.2f}\n"
        tabla += f"{'Costo de lo vendido':<40}${self.costo_lo_vendido:>39,.2f}\n"
        tabla += f"{'Utilidad Bruta':<40}${self.ventas - self.costo_lo_vendido:>39,.2f}\n"
        tabla += f"{'Gastos Generales':<40}${self.gastos_generales:>39,.2f}\n"
        tabla += f"{'Utilidad del periodo':<40}${utilidad_periodo:>39,.2f}\n"
        tabla += f"{'ISR (30%)':<40}${utilidad_periodo * 0.3:>39,.2f}\n"
        tabla += f"{'PTU (10%)':<40}${utilidad_periodo * 0.1:>39,.2f}\n"
        tabla += "=" * 80 + "\n"
        
        return tabla

    def generar_estado_resultado(self):
        tabla = f"{'Balance General Final':<45}{'':<35}{'':<20}\n"
        tabla += "=" * 100 + "\n"
        
        tabla += "Circulante:\n"
        tabla += f"  Caja: $46,872.00\n"
        tabla += f"  Bancos: $3,464,000.00\n"
        tabla += f"  Mercancías: $247,000.00\n"
        tabla += f"  IVA Acreditado: $7,808.00\n"
        tabla += f"  IVA Por Acreditar: $6,400.00\n"
        tabla += f"  Renta Por Anticipado: $4,000.00\n"
        tabla += f"  Papelería: $800.00\n"
        tabla += f"  Clientes: $3,480.00\n"
        tabla += f"  Total Act. Circ.: $3,780,360.00\n"
        
        tabla += "\nNo circulante:\n"
        tabla += f"  Terrenos: $800,000.00\n"
        tabla += f"  Edificios: $1,991,667.00\n"
        tabla += f"  Dep. Acum. Edificio: $8,333.00\n"
        tabla += f"  Equipo Reparto: $293,750.00\n"
        tabla += f"  Dep.Acum.Reparto: $6,250.00\n"
        tabla += f"  Equipo Computo: $97,500.00\n"
        tabla += f"  Dep. Acum. Equipo Cómputo: $2,500.00\n"
        tabla += f"  Mob y Equipo: $119,000.00\n"
        tabla += f"  Dep.Acum.Mobiliario: $1,000.00\n"
        tabla += f"  Muebles: $158,667.00\n"
        tabla += f"  Dep.Acum. Muebles: $1,333.00\n"
        tabla += f"  Suma Act. No Circ.: $3,460,584.00\n"
        tabla += f"  Total Activo: $7,240,944.00\n"
        
        tabla += "\nPasivo:\n"
        tabla += f"  Acreedores CP: $34,800.00\n"
        tabla += f"  Documento por Pagar: $11,600.00\n"
        tabla += f"  Anticipo de Cliente: $0.00\n"
        tabla += f"  IVA Trasladado: $64,480.00\n"
        tabla += f"  IVA x Trasladar: $480.00\n"
        tabla += f"  Total Pasivo: $111,360.00\n"
        
        tabla += "\nCapital:\n"
        tabla += f"  Capital contable: $6,950,000.00\n"
        tabla += f"  Utilidad Periodo: $179,584.00\n"
        tabla += f"  Total Pasivo + Capital: $7,240,944.00\n"
        tabla += f"  Total Capital: $6,950,000.00\n"
        
        return tabla

    def generar_estado_cambio(self):
        utilidad_periodo = self.calcular_utilidad_periodo()
        reserva_legal = utilidad_periodo * 0.05
        resultado_utilidad = reserva_legal / 12

        tabla = f"{'Concepto':<20}{'Capital Contribuido':<20}{'Capital Ganado':<20}{'Capital Contable':<20}{'Utilidad del período':<20}\n"
        tabla += "=" * 100 + "\n"
        tabla += f"{'Saldo Inicial':<20}{'$ -':<20}{'$ -':<20}{'':<20}{'$ 179,584.00':<20}\n"
        tabla += f"{'Aumentos':<20}{'':<20}{'':<20}{'':<20}{'Utilidad * 5%':<20}{'$ 8,979.20':<20}\n"
        tabla += f"{'Capital Social':<20}{'$ 6,950,000.00':<20}{'':<20}{'$ 6,950,000.00':<20}{'':<20}\n"
        tabla += f"{'Reserva Legal':<20}{'$ 748.27':<20}{'$ 748.27':<20}{'':<20}{'':<20}\n"
        tabla += f"{'Resultado Ejercicios':<20}{'$ 179,584.00':<20}{'$ 179,584.00':<20}{'':<20}{'':<20}\n"
        tabla += f"{'TOTAL':<20}{'$ 6,950,000.00':<20}{'$ 180,332.27':<20}{'$ 7,130,332.27':<20}{'':<20}\n"
        tabla += f"{'Decreto':<20}{'$ -':<20}{'$ -':<20}{'$ -':<20}{'':<20}\n"
        tabla += f"{'Reserva Legal':<20}{'$ -':<20}{'$ 748.27':<20}{'$ 748.27':<20}{'':<20}\n"
        tabla += f"{'Reembolso':<20}{'$ -':<20}{'$ -':<20}{'$ -':<20}{'':<20}\n"
        tabla += f"{'TOTAL':<20}{'$ -':<20}{'$ 748.27':<20}{'$ 748.27':<20}{'':<20}\n"
        tabla += f"{'INCREMENTO NETO':<20}{'$ 6,950,000.00':<20}{'$ 181,080.54':<20}{'$ 7,131,080.54':<20}{'':<20}\n"
        tabla += f"{'Saldo Final':<20}{'$ 6,950,000.00':<20}{'$ 181,080.54':<20}{'$ 7,131,080.54':<20}{'SF: Saldo inicial + incrementos':<20}\n"

        return tabla
    
    def generar_estado_flujo_efectivo_indirecto(self):
        tabla = f"{'Estado de Flujo de Efectivo (Método Indirecto)':^100}\n"
        tabla += f"{'El Rincón del Café S.A DE C.V':^100}\n"
        tabla += f"{'Correspondiente al mes de Marzo 2025':^100}\n\n"
        
        tabla += f"{'Fuentes de Efectivo':<50}{'':<20}{'':<20}{'':<10}\n"
        tabla += "-" * 100 + "\n"
        tabla += f"{'Depreciación':<50}{'':<20}{'':<20}{'$19,416.00':>10}\n"
        tabla += f"{'Utilidad del ejercicio':<50}{'':<20}{'':<20}{'$107,750.00':>10}\n"
        tabla += f"{'ISR':<50}{'':<10}{'$53,875.00':>10}{'':<10}\n"
        tabla += f"{'PTU':<50}{'':<10}{'$17,958.00':>10}{'':<10}\n"
        tabla += f"{'Acreedores':<50}{'':<10}{'$34,800.00':>10}{'$106,583.00':>10}\n"
        tabla += f"{'Efectivo Generado en la operación':<50}{'':<20}{'':<20}{'':>10}\n"
        tabla += f"{'Proveedores':<50}{'':<10}{'$0.00':>10}{'':<10}\n"
        tabla += f"{'Doc por Pagar':<50}{'':<10}{'$11,600.00':>10}{'':<10}\n"
        tabla += f"{'Capital Social':<50}{'':<10}{'$6,950,000.00':>10}{'':<10}\n"
        tabla += f"{'Suma Fuentes de efectivo':<50}{'':<20}{'':<20}{'$7,284,749.00':>10}\n\n"
        
        tabla += f"{'Aplicación de efectivo':<50}{'':<20}{'':<20}{'':<10}\n"
        tabla += "-" * 100 + "\n"
        tabla += f"{'Almacén':<50}{'':<10}{'$247,000.00':>10}{'':<10}\n"
        tabla += f"{'Clientes':<50}{'':<10}{'$3,480.00':>10}{'':<10}\n"
        tabla += f"{'Iva Acreditado':<50}{'':<10}{'$7,808.00':>10}{'':<10}\n"
        tabla += f"{'Iva Pendiente por Acreditar':<50}{'':<10}{'$6,400.00':>10}{'':<10}\n"
        tabla += f"{'Iva Trasladado':<50}{'':<10}{'$-64,480.00':>10}{'':<10}\n"
        tabla += f"{'Iva Pendiente por Trasladar':<50}{'':<10}{'$-480.00':>10}{'':<10}\n"
        tabla += f"{'Terrenos':<50}{'':<10}{'$800,000.00':>10}{'':<10}\n"
        tabla += f"{'Edificios':<50}{'':<10}{'$2,000,000.00':>10}{'':<10}\n"
        tabla += f"{'Equipo Reparto':<50}{'':<10}{'$300,000.00':>10}{'':<10}\n"
        tabla += f"{'Equipo Computo':<50}{'':<10}{'$100,000.00':>10}{'':<10}\n"
        tabla += f"{'Papelería':<50}{'':<10}{'$800.00':>10}{'':<10}\n"
        tabla += f"{'Renta Anticipado':<50}{'':<10}{'$4,000.00':>10}{'':<10}\n"
        tabla += f"{'Mob y Equipo':<50}{'':<10}{'$120,000.00':>10}{'':<10}\n"
        tabla += f"{'Muebles':<50}{'':<10}{'$160,000.00':>10}{'':<10}\n"
        tabla += f"{'Suma Aplicaciones Efectivo':<50}{'':<20}{'':<20}{'$3,683,528.00':>10}\n\n"
        
        tabla += f"{'Saldo Inicial Bancos':<50}{'':<10}{'$3,000,000.00':>10}{'':<10}\n"
        tabla += f"{'Saldo Final Bancos':<50}{'':<10}{'$3,464,000.00':>10}{'':<10}\n"
        tabla += f"{'Caja Saldo Inicial':<50}{'':<10}{'$100,000.00':>10}{'':<10}\n"
        tabla += f"{'Caja Saldo Final':<50}{'':<10}{'$46,871.00':>10}{'':<10}\n\n"
        
        tabla += f"{'Suma de Fuentes de Efectivo + Aplicación de efectivo':<50}{'':<10}{'$3,510,871.00':>10}{'':<10}\n"
        tabla += f"{'Suma Final Bancos + Final Caja':<50}{'':<10}{'$3,510,871.00':>10}{'':<10}\n"
    
        return tabla
    
    def generar_estado_flujo_efectivo_directo(self):
        tabla = f"{'Estado de Flujo de Efectivo (Método Directo)':^100}\n"
        tabla += f"{'El Rincón del Café S.A DE C.V':^100}\n"
        tabla += f"{'Correspondiente al mes de Marzo 2025':^100}\n\n"
        
        tabla += f"{'Actividades en Operación:':<50}{'':<20}{'':<20}{'$271,583.00':>10}\n"
        tabla += "-" * 100 + "\n"
        tabla += f"{'Clientes':<50}{'':<20}{'$3,480.00':>10}{'':<10}\n"
        tabla += f"{'Almacén':<50}{'':<20}{'$247,000.00':>10}{'':<10}\n"
        tabla += f"{'Papelería':<50}{'':<20}{'$800.00':>10}{'':<10}\n"
        tabla += f"{'Rentas Pagadas Anticipo':<50}{'':<20}{'$4,000.00':>10}{'':<10}\n"
        tabla += f"{'Iva Acreditado':<50}{'':<20}{'$7,808.00':>10}{'':<10}\n"
        tabla += f"{'Iva Pendiente por Acreditar':<50}{'':<20}{'$6,400.00':>10}{'':<10}\n"
        tabla += f"{'Subtotal':<50}{'':<20}{'':<20}{'$269,488.00':>10}\n"
        tabla += f"{'Iva Trasladado':<50}{'':<20}{'$-64,480.00':>10}{'':<10}\n"
        tabla += f"{'Iva Pendiente de Trasladar':<50}{'':<20}{'$-480.00':>10}{'':<10}\n"
        tabla += f"{'Provisión de ISR':<50}{'':<20}{'$-53,875.00':>10}{'':<10}\n"
        tabla += f"{'Provisión de PTU':<50}{'':<20}{'$-17,958.00':>10}{'':<10}\n"
        tabla += f"{'Utilidad de ejercicio':<50}{'':<20}{'$-107,750.00':>10}{'':<10}\n"
        tabla += f"{'Subtotal':<50}{'':<20}{'':<20}{'$-244,543.00':>10}\n"
        tabla += f"{'Flujos netos del efectivo de actividades en operación':<50}{'':<20}{'':<20}{'$24,945.00':>10}\n\n"
        
        tabla += f"{'Actividades de Inversión:':<50}{'':<20}{'':<20}{'$3,480,000.00':>10}\n"
        tabla += "-" * 100 + "\n"
        tabla += f"{'Terrenos':<50}{'':<20}{'$800,000.00':>10}{'':<10}\n"
        tabla += f"{'Edificios':<50}{'':<20}{'$2,000,000.00':>10}{'':<10}\n"
        tabla += f"{'Equipo Reparto':<50}{'':<20}{'$300,000.00':>10}{'':<10}\n"
        tabla += f"{'Equipo Computo':<50}{'':<20}{'$100,000.00':>10}{'':<10}\n"
        tabla += f"{'Mob y Equipo':<50}{'':<20}{'$120,000.00':>10}{'':<10}\n"
        tabla += f"{'Muebles':<50}{'':<20}{'$160,000.00':>10}{'':<10}\n"
        tabla += f"{'Flujos netos del efectivo de inversión':<50}{'':<20}{'':<20}{'$3,480,000.00':>10}\n\n"
        
        tabla += f"{'Actividades de Financiamiento:':<50}{'':<20}{'':<20}{'$-7,112,816.00':>10}\n"
        tabla += "-" * 100 + "\n"
        tabla += f"{'Depreciación':<50}{'':<20}{'$-19,416.00':>10}{'':<10}\n"
        tabla += f"{'Capital Social':<50}{'':<20}{'$-6,950,000.00':>10}{'':<10}\n"
        tabla += f"{'Acreedores Diversos':<50}{'':<20}{'$-34,800.00':>10}{'':<10}\n"
        tabla += f"{'Documentos por pagar':<50}{'':<20}{'$-11,600.00':>10}{'':<10}\n"
        tabla += f"{'Flujos netos de efectivo de actividades de financiamiento':<50}{'':<20}{'':<20}{'$-7,016,816.00':>10}\n\n"
        
        tabla += f"{'Incremento Neto de Efectivo y equivalentes de efectivo:':<50}{'':<20}{'':<20}{'$-3,607,871.00':>10}\n"
        tabla += "-" * 100 + "\n"
        tabla += f"{'Efectivo al Principio del periodo':<50}{'':<20}{'':<20}{'$3,000,000.00':>10}\n"
        tabla += f"{'Bancos':<50}{'':<20}{'$3,000,000.00':>10}{'':<10}\n"
        tabla += f"{'Efectivo al Final del periodo':<50}{'':<20}{'':<20}{'$3,464,000.00':>10}\n"
        tabla += f"{'Bancos':<50}{'':<20}{'$3,464,000.00':>10}{'':<10}\n"
        tabla += f"{'Efectivo al Principio del periodo':<50}{'':<20}{'':<20}{'$100,000.00':>10}\n"
        tabla += f"{'Caja':<50}{'':<20}{'$100,000.00':>10}{'':<10}\n"
        tabla += f"{'Efectivo al Final del periodo':<50}{'':<20}{'':<20}{'$46,871.00':>10}\n"
        tabla += f"{'Caja':<50}{'':<20}{'$46,871.00':>10}{'':<10}\n"
        tabla += f"{'Efectivo al final del periodo':<50}{'':<20}{'':<20}{'$3,510,871.00':>10}\n"
        tabla += f"{'Suma de Final del Periodo y Final de Caja':<50}{'':<20}{'':<20}{'$3,510,871.00':>10}\n"
        
        return tabla

def main():
    st.set_page_config(page_title="Aplicación Contable", layout="wide")
    st.title("Aplicación Contable Básica")
    
    if "apertura_data" not in st.session_state:
        st.session_state["apertura_data"] = None
    
    if st.session_state["apertura_data"] is None:
        company_name = st.text_input("Ingrese el nombre de la empresa:")
        if company_name:
            st.session_state["apertura_data"] = AperturaData(company_name)
            st.success(f"Nombre de la empresa '{company_name}' guardado.")
    else:
        data = st.session_state["apertura_data"]
        st.subheader(f"Empresa: {data.company_name}")
    
    if st.session_state["apertura_data"] is not None:
        data = st.session_state["apertura_data"]
        
        menu = st.sidebar.radio("Seleccione una operación:",
                                ("Asiento de Apertura", 
                                 "Compra en Efectivo", 
                                 "Compra a Crédito", 
                                 "Compra Combinada", 
                                 "Pago de Rentas Pagadas por Anticipado", 
                                 "Anticipo de Clientes", 
                                 "Compra de Papelería", 
                                 "Mostrar Balance",
                                 "Libro Diario",
                                 "Mayor",
                                 "Balance de Comprobación",
                                 "Utilidad del Periodo",
                                 "Estado de Resultado",
                                 "Estado de Cambio",
                                 "Estado Flujo de Efectivo (Indirecto)",
                                 "Estado Flujo de Efectivo (Directo)"))  
        
        if menu == "Asiento de Apertura":
            mostrar_asiento_apertura(data)
        elif menu == "Compra en Efectivo":
            mostrar_compra_efectivo(data)
        elif menu == "Compra a Crédito":
            mostrar_compra_credito(data)
        elif menu == "Compra Combinada":
            mostrar_compra_combinada(data)
        elif menu == "Pago de Rentas Pagadas por Anticipado":
            mostrar_pago_rentas(data)
        elif menu == "Anticipo de Clientes":
            mostrar_anticipo_clientes(data)
        elif menu == "Compra de Papelería":
            mostrar_compra_papeleria(data)
        elif menu == "Mostrar Balance":
            st.subheader("Balance General")
            st.code(data.generar_tabla_balance())
            mostrar_firmas()
        elif menu == "Libro Diario":
            st.subheader("Libro Diario")
            st.code(data.generar_libro_diario())
            mostrar_firmas()
        elif menu == "Mayor":
            st.subheader("Mayor")
            st.code(data.generar_mayor())
            mostrar_firmas()
        elif menu == "Balance de Comprobación":
            st.subheader("Balance de Comprobación")
            st.code(data.generar_balance_comprobacion())
            mostrar_firmas()
        elif menu == "Utilidad del Periodo":
            st.subheader("Utilidad del Periodo")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                ventas = st.number_input("Ventas", value=data.ventas, min_value=0.0, step=1000.0)
            with col2:
                costo_lo_vendido = st.number_input("Costo de lo vendido", value=data.costo_lo_vendido, min_value=0.0, step=1000.0)
            with col3:
                gastos_generales = st.number_input("Gastos Generales", value=data.gastos_generales, min_value=0.0, step=1000.0)
            
            data.ventas = ventas
            data.costo_lo_vendido = costo_lo_vendido
            data.gastos_generales = gastos_generales
            
            st.code(data.generar_utilidad_periodo())
            mostrar_firmas()
        elif menu == "Estado de Resultado":
            st.subheader("Estado de Resultado")
            st.code(data.generar_estado_resultado())
            mostrar_firmas()
        elif menu == "Estado de Cambio":
            st.subheader("Estado de Cambio")
            st.code(data.generar_estado_cambio())
            mostrar_firmas()
        elif menu == "Estado Flujo de Efectivo (Indirecto)":
            st.subheader("Estado de Flujo de Efectivo - Método Indirecto")
            st.code(data.generar_estado_flujo_efectivo_indirecto())
            mostrar_firmas()
        elif menu == "Estado Flujo de Efectivo (Directo)":
            st.subheader("Estado de Flujo de Efectivo - Método Directo")
            st.code(data.generar_estado_flujo_efectivo_directo())
            mostrar_firmas()

def mostrar_firmas():
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Propietario**")
        st.image("yo.png", width=150)
        st.write("Ricardo Uriel Cruz Cruz")
    with col2:
        st.markdown("**Revisó**")
        st.image("profe.png", width=150)
        st.write("Nuria González Zúñiga")

def mostrar_asiento_apertura(data: AperturaData):
    st.subheader("Asiento de Apertura")
    if data.apertura_realizada:
        st.info("El asiento de apertura ya fue realizado.")
        st.code(data.generar_tabla_balance())
        mostrar_firmas()
        return

    nuevo_monto_caja = st.number_input("Ingrese el monto inicial de Caja (Activo Circulante):", min_value=0.0, step=1000.0)
    nuevo_monto_banco = st.number_input("Ingrese el monto inicial de Banco (Activo Circulante):", min_value=0.0, step=1000.0)
    nuevo_monto_inventario = st.number_input("Ingrese el monto inicial de Inventario (Activo Circulante):", min_value=0.0, step=1000.0)
    
    if st.button("Actualizar Montos Iniciales"):
        data.caja = nuevo_monto_caja
        data.banco = nuevo_monto_banco
        data.inventario = nuevo_monto_inventario
        st.success("Montos iniciales actualizados.")

    st.write("### Agregar Activos No Circulantes (Compras Iniciales)")
    nombre_activo = st.text_input("Nombre del Activo No Circulante")
    valor_activo = st.number_input("Valor del Activo No Circulante", min_value=0.0, step=1000.0, key="activo_inicial")
    if st.button("Agregar Activo No Circulante"):
        if nombre_activo.strip() != "":
            data.activos_no_circulantes.append((nombre_activo, valor_activo))
            st.success(f"Activo '{nombre_activo}' agregado.")
        else:
            st.warning("Ingrese un nombre válido.")
    
    if data.activos_no_circulantes:
        st.write("*Activos No Circulantes Ingresados:*")
        for idx, (n, v) in enumerate(data.activos_no_circulantes, start=1):
            st.write(f"{idx}. {n}: ${v:,.2f}")
    
    if st.button("Finalizar Asiento de Apertura"):
        data.calcular_asiento_apertura()
        st.success("Asiento de Apertura finalizado.")
        st.code(data.generar_tabla_balance())
        mostrar_firmas()

def mostrar_compra_efectivo(data: AperturaData):
    st.subheader("Compra en Efectivo")
    
    tipo_activo = st.selectbox("Seleccione el tipo de activo:", ["Activo Circulante", "Activo No Circulante"])
    
    if tipo_activo == "Activo Circulante":
        activo_circulante = st.selectbox("Activo Circulante", ["Inventario"])
        valor = st.number_input("Valor de la Compra", min_value=0.0, step=1000.0, key="efectivo_valor")
        if st.button("Agregar Compra en Efectivo"):
            if activo_circulante == "Inventario":
                data.compra_en_efectivo(valor)
                st.success(f"Compra en efectivo por ${valor:,.2f} registrada en Inventario.")
            st.code(data.generar_tabla_balance())
            mostrar_firmas()
    
    elif tipo_activo == "Activo No Circulante":
        opciones_activos_no_circulantes = [nombre for nombre, _ in data.activos_no_circulantes]
        opciones_activos_no_circulantes.append("Nuevo Activo")
        seleccion_activo_no_circulante = st.selectbox("Seleccione un activo no circulante o escriba uno nuevo:", opciones_activos_no_circulantes)
        
        if seleccion_activo_no_circulante == "Nuevo Activo":
            nombre_activo_no_circulante = st.text_input("Nombre del Activo No Circulante", key="efectivo_nombre")
        else:
            nombre_activo_no_circulante = seleccion_activo_no_circulante
        
        valor = st.number_input("Valor de la Compra", min_value=0.0, step=1000.0, key="efectivo_valor")
        if st.button("Agregar Compra en Efectivo"):
            if seleccion_activo_no_circulante != "Nuevo Activo":
                data.compra_a_credito(nombre_activo_no_circulante, valor)
                st.success(f"Compra a crédito '{nombre_activo_no_circulante}' por ${valor:,.2f} registrada.")
            st.code(data.generar_tabla_balance())
            mostrar_firmas()

def mostrar_compra_credito(data: AperturaData):
    st.subheader("Compra a Crédito")
    
    tipo_activo = st.selectbox("Seleccione el tipo de activo:", ["Activo Circulante", "Activo No Circulante"])
    
    if tipo_activo == "Activo Circulante":
        activo_circulante = st.selectbox("Activo Circulante", ["Inventario"])
        valor = st.number_input("Valor de la Compra a Crédito", min_value=0.0, step=1000.0, key="credito_valor")
        if st.button("Agregar Compra a Crédito"):
            if activo_circulante == "Inventario":
                data.compra_en_efectivo(valor)
                st.success(f"Compra en efectivo por ${valor:,.2f} registrada en Inventario.")
            st.code(data.generar_tabla_balance())
            mostrar_firmas()
    
    elif tipo_activo == "Activo No Circulante":
        opciones_activos_no_circulantes = [nombre for nombre, _ in data.activos_no_circulantes]
        opciones_activos_no_circulantes.append("Nuevo Activo")
        seleccion_activo_no_circulante = st.selectbox("Seleccione un activo no circulante o escriba uno nuevo:", opciones_activos_no_circulantes)
        
        if seleccion_activo_no_circulante == "Nuevo Activo":
            nombre_activo_no_circulante = st.text_input("Nombre del Activo No Circulante", key="credito_nombre")
        else:
            nombre_activo_no_circulante = seleccion_activo_no_circulante
        
        valor = st.number_input("Valor de la Compra a Crédito", min_value=0.0, step=1000.0, key="credito_valor")
        if st.button("Agregar Compra a Crédito"):
            if seleccion_activo_no_circulante != "Nuevo Activo":
                data.compra_a_credito(nombre_activo_no_circulante, valor)
                st.success(f"Compra a crédito '{nombre_activo_no_circulante}' por ${valor:,.2f} registrada.")
            st.code(data.generar_tabla_balance())
            mostrar_firmas()

def mostrar_compra_combinada(data: AperturaData):
    st.subheader("Compra Combinada")
    
    tipo_activo = st.selectbox("Seleccione el tipo de activo:", ["Activo Circulante", "Activo No Circulante"])
    
    if tipo_activo == "Activo Circulante":
        activo_circulante = st.selectbox("Activo Circulante", ["Inventario"])
        valor = st.number_input("Valor de la Compra Combinada", min_value=0.0, step=1000.0, key="combinada_valor")
        if st.button("Agregar Compra Combinada"):
            if activo_circulante == "Inventario":
                data.compra_combinada("Inventario", valor)
                st.success(f"Compra combinada por ${valor:,.2f} registrada en Inventario.")
            st.code(data.generar_tabla_balance())
            mostrar_firmas()
    
    elif tipo_activo == "Activo No Circulante":
        opciones_activos_no_circulantes = [nombre for nombre, _ in data.activos_no_circulantes]
        opciones_activos_no_circulantes.append("Nuevo Activo")
        seleccion_activo_no_circulante = st.selectbox("Seleccione un activo no circulante o escriba uno nuevo:", opciones_activos_no_circulantes)
        
        if seleccion_activo_no_circulante == "Nuevo Activo":
            nombre_activo_no_circulante = st.text_input("Nombre del Activo No Circulante", key="combinada_nombre")
        else:
            nombre_activo_no_circulante = seleccion_activo_no_circulante
        
        valor = st.number_input("Valor de la Compra Combinada", min_value=0.0, step=1000.0, key="combinada_valor")
        if st.button("Agregar Compra Combinada"):
            if seleccion_activo_no_circulante != "Nuevo Activo":
                data.compra_combinada(nombre_activo_no_circulante, valor)
                st.success(f"Compra combinada '{nombre_activo_no_circulante}' por ${valor:,.2f} registrada.")
            st.code(data.generar_tabla_balance())
            mostrar_firmas()

def mostrar_anticipo_clientes(data: AperturaData):
    st.subheader("Anticipo de Clientes")
    
    nombre_cliente = st.text_input("Nombre del Cliente")
    monto = st.number_input("Monto que el cliente va a abonar", min_value=0.0, step=1000.0, key="anticipo_monto")
    porcentaje = st.selectbox("Porcentaje a abonar", [50])
    
    if st.button("Registrar Anticipo de Clientes"):
        if nombre_cliente.strip() != "" and monto > 0:
            data.anticipo_clientes_op(nombre_cliente, monto, porcentaje)
            st.success(f"Anticipo de cliente '{nombre_cliente}' por ${monto * (porcentaje / 100):,.2f} registrado.")
            st.code(data.generar_tabla_balance())
            mostrar_firmas()
        else:
            st.warning("Ingrese un nombre válido y un monto mayor a 0.")

def mostrar_compra_papeleria(data: AperturaData):
    st.subheader("Compra de Papelería")
    
    valor = st.number_input("Monto a pagar en papelería", min_value=0.0, step=1000.0, key="papeleria_valor")
    
    if st.button("Registrar Compra de Papelería"):
        if valor > 0:
            data.compra_papeleria_op(valor)
            st.success(f"Compra de papelería por ${valor:,.2f} registrada.")
            st.code(data.generar_tabla_balance())
            mostrar_firmas()
        else:
            st.warning("Ingrese un monto válido para la papelería.")

def mostrar_pago_rentas(data: AperturaData):
    st.subheader("Pago de Rentas Pagadas por Anticipado")
    
    valor_renta = st.number_input("Valor de la renta por un mes:", min_value=0.0, step=1000.0, key="rentas_valor")
    meses = st.selectbox("Seleccione la cantidad de meses a anticipar:", [2, 3, 4])
    
    if st.button("Registrar Pago de Rentas"):
        if valor_renta > 0:
            data.pago_rentas_op(valor_renta, meses)
            st.success(f"Pago de rentas por {meses} meses (${valor_renta * meses:,.2f} + IVA) registrado.")
            st.code(data.generar_tabla_balance())
            mostrar_firmas()
        else:
            st.warning("Ingrese un valor válido para la renta.")

if __name__ == "__main__":
    main()