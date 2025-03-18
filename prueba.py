import streamlit as st
from datetime import datetime

# Función para crear una tabla con bordes usando HTML y CSS
def crear_tabla_con_bordes(datos, titulo):
    # Crear el HTML para la tabla con bordes
    html = f"""
    <div style="border: 1px solid #e0e0e0; padding: 10px; margin-bottom: 20px; border-radius: 10px; background-color: #f9f9f9;">
        <h3 style="color: #2c3e50; font-weight: bold;">{titulo}</h3>
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr>
                    {"".join(f"<th style='border: 1px solid #e0e0e0; padding: 8px; background-color: #2c3e50; color: white;'>{header}</th>" for header in datos[0].keys())}
                </tr>
            </thead>
            <tbody>
                {"".join(
                    f"<tr>{''.join(f'<td style="border: 1px solid #e0e0e0; padding: 8px;">{valor}</td>' for valor in fila.values())}</tr>"
                    for fila in datos
                )}
            </tbody>
        </table>
    </div>
    """
    # Mostrar la tabla en Streamlit
    st.markdown(html, unsafe_allow_html=True)

# ==========================
# LÓGICA CONTABLE (Dominio)
# ==========================
class AperturaData:
    """
    Maneja la información contable y las operaciones:
      - Asiento de Apertura
      - Compra en Efectivo
      - Compra a Crédito
      - Compra Combinada
      - Anticipo de Clientes
      - Compra de Papelería
      - Pago de Rentas Pagadas por Anticipado
    """
    def __init__(self, company_name):
        # Nombre de la empresa (definido por el usuario)
        self.company_name = company_name
        self.apertura_realizada = False
        
        # Tasa de IVA
        self.iva_rate = 0.16
        
        # Cuentas de Activo (iniciales y transaccionales)
        self.caja = 0.0                     # Activo Circulante: Caja
        self.banco = 0.0                    # Activo Circulante: Banco
        self.inventario = 0.0               # Activo Circulante: Inventario
        self.papeleria = 0.0                # Compras de papelería (base)
        self.rentas_anticipadas = 0.0       # Rentas pagadas por anticipado (activo)
        
        # Activo No Circulante (compras iniciales, compras a crédito, combinadas)
        self.activos_no_circulantes = []    # Lista de tuplas: (nombre, valor)
        
        # Cuentas de IVA (se registran en activo circulante)
        self.iva_acreditable = 0.0          # Por compras en efectivo y papelería
        self.iva_por_acreditar = 0.0        # Por compras a crédito o su parte en combinadas
        
        # Cuentas de Pasivo (se registran cuando hay compras a crédito, combinadas o anticipos)
        self.acreedores = 0.0               # Por compras a crédito
        self.documentos_por_pagar = 0.0     # Por parte de compra combinada (crédito)
        self.anticipo_clientes = []         # Lista de (nombre, monto)
        self.iva_trasladado = 0.0           # IVA Trasladado (Pasivo)
        
        # Totales y Capital (el capital se fija en el asiento de apertura)
        self.total_no_circulante = 0.0
        self.total_activo = 0.0
        self.total_pasivo = 0.0
        self.capital = 0.0

        # Lista para almacenar las transacciones del libro diario
        self.libro_diario = []

    def agregar_transaccion(self, fecha, cuentas, debe, haber):
        """
        Agrega una transacción al libro diario.
        """
        for cuenta, valor in cuentas.items():
            self.libro_diario.append({
                "fecha": fecha,
                "cuentas": cuenta,
                "debe": valor if debe else 0.0,
                "haber": valor if haber else 0.0
            })

    def recalcular_totales(self):
        # Suma de activos no circulantes (se acumulan las compras que van a esa categoría)
        self.total_no_circulante = sum(valor for _, valor in self.activos_no_circulantes)
        # Activo Circulante incluye: caja, banco, inventario, papelería, rentas anticipadas, IVA (ambos)
        activo_circulante = (self.caja + self.banco + self.inventario + self.papeleria +
                            self.rentas_anticipadas + self.iva_acreditable + self.iva_por_acreditar)
        self.total_activo = activo_circulante + self.total_no_circulante
        
        # Suma de pasivos: acreedores, documentos por pagar, anticipo de clientes y IVA Trasladado
        anticipo_total = sum(monto for _, monto in self.anticipo_clientes)
        self.total_pasivo = self.acreedores + self.documentos_por_pagar + anticipo_total + self.iva_trasladado

    def calcular_asiento_apertura(self):
        """
        Asiento de Apertura:
         - Se ingresa el monto inicial de Caja, Banco e Inventario.
         - Se pueden agregar activos no circulantes (compras iniciales).
         - No hay pasivos; el Capital se fija como (Caja + Banco + Inventario + activos no circulantes).
        """
        total_no_circulante = sum(valor for _, valor in self.activos_no_circulantes)
        activo_circulante = self.caja + self.banco + self.inventario  # Se considera Caja, Banco e Inventario en el activo circulante
        self.total_activo = activo_circulante + total_no_circulante
        self.capital = self.total_activo
        self.total_pasivo = 0.0
        self.apertura_realizada = True

        # Registrar el asiento de apertura en el libro diario
        self.agregar_transaccion(
            fecha="210T2025",
            cuentas={
                "Caja": self.caja,
                "Bancos": self.banco,
                "Mercancías": self.inventario,
                "Terrenos": sum(valor for nombre, valor in self.activos_no_circulantes if nombre == "Terrenos"),
                "Equipo Reparto": sum(valor for nombre, valor in self.activos_no_circulantes if nombre == "Equipo Reparto"),
                "Edificios": sum(valor for nombre, valor in self.activos_no_circulantes if nombre == "Edificios"),
                "computo": sum(valor for nombre, valor in self.activos_no_circulantes if nombre == "computo"),
                "Mobiliario": sum(valor for nombre, valor in self.activos_no_circulantes if nombre == "Mob"),
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
        """
        Registra una compra en efectivo:
         - Se suma el valor de la compra a Inventario.
         - Se calcula y suma el IVA a la cuenta IVA Acreditable.
         - Se descuenta de Caja la suma de (valor + IVA).
         - Recalcula totales.
        """
        iva = valor * self.iva_rate
        self.inventario += valor
        self.iva_acreditable += iva
        self.caja -= (valor + iva)
        self.recalcular_totales()

        # Registrar la transacción en el libro diario
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
        """
        Registra una compra a crédito:
         - Si el activo ya existe, se suma el valor al activo existente.
         - Si no existe, se agrega como un nuevo activo.
         - Se calcula y suma el IVA a la cuenta IVA por Acreditar.
         - Se incrementa el pasivo (Acreedores) en (valor + IVA).
         - Recalcula totales.
        """
        iva = valor * self.iva_rate

        # Buscar si el activo ya existe
        activo_existente = False
        for idx, (n, v) in enumerate(self.activos_no_circulantes):
            if n == nombre:
                # Sumar el valor al activo existente
                self.activos_no_circulantes[idx] = (n, v + valor)
                activo_existente = True
                break

        # Si no existe, agregar como nuevo activo
        if not activo_existente:
            self.activos_no_circulantes.append((nombre, valor))

        # Actualizar IVA y pasivo
        self.iva_por_acreditar += iva
        self.acreedores += (valor + iva)
        self.recalcular_totales()

        # Registrar la transacción en el libro diario
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
        """
        Registra una compra combinada (mitad en efectivo y mitad a crédito):
         - Se agrega la compra completa a lo que se haya seleccionado.
         - Se reparte el IVA y el valor en dos mitades.
         - La mitad en efectivo se descuenta de Caja y suma su IVA a IVA Acreditable.
         - La mitad a crédito se suma a Documentos por Pagar y su IVA a IVA por Acreditar.
         - Recalcula totales.
        """
        iva_total = valor * self.iva_rate
        mitad_valor = valor / 2.0
        mitad_iva = iva_total / 2.0
        
        # Agregar la compra completa al activo seleccionado
        if nombre == "Inventario":
            self.inventario += valor
        else:
            self.activos_no_circulantes.append((nombre, valor))
        
        # Efectivo:
        self.caja -= (mitad_valor + mitad_iva)
        self.iva_acreditable += mitad_iva
        
        # Crédito:
        self.documentos_por_pagar += (mitad_valor + mitad_iva)
        self.iva_por_acreditar += mitad_iva
        
        self.recalcular_totales()

        # Registrar la transacción en el libro diario
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
        """
        Registra un anticipo de clientes:
         - El usuario ingresa la cantidad que el cliente va a abonar.
         - Se selecciona un porcentaje (50% en este caso).
         - Se calcula el 50% de la cantidad ingresada.
         - Se calcula el IVA sobre ese 50%.
         - Se suma el total con IVA a la caja.
         - Se registra el anticipo de cliente y el IVA trasladado en el pasivo.
         - Recalcula totales.
        """
        monto_abonado = monto * (porcentaje / 100)
        iva = monto_abonado * self.iva_rate
        total_con_iva = monto_abonado + iva

        # Aumentar la caja con el total con IVA
        self.caja += total_con_iva

        # Registrar el anticipo de cliente
        self.anticipo_clientes.append((nombre, monto_abonado))

        # Registrar el IVA trasladado en el pasivo
        self.iva_trasladado += iva

        # Recalcular totales
        self.recalcular_totales()

        # Registrar la transacción en el libro diario
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
        """
        Registra la compra de papelería en efectivo:
         - Se calcula el IVA y se suma a IVA Acreditable.
         - Se suma el valor de papelería a la cuenta respectiva.
         - Se descuenta de Caja la suma de (valor + IVA).
         - Recalcula totales.
        """
        iva = valor * self.iva_rate
        self.papeleria += valor
        self.iva_acreditable += iva
        self.caja -= (valor + iva)
        self.recalcular_totales()

        # Registrar la transacción en el libro diario
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

    def pago_rentas_op(self, valor: float, meses: int):
        """
        Registra el pago de rentas pagadas por anticipado:
         - El usuario ingresa el valor de la renta de un mes y la cantidad de meses a anticipar.
         - Se calcula el total de la renta y el IVA correspondiente.
         - Se descuenta el total de Caja.
         - Se suma el IVA a IVA Acreditable.
         - Se suma el total de la renta a Rentas Pagadas Anticipado.
         - Recalcula totales.
        """
        total_renta = valor * meses
        iva = total_renta * self.iva_rate
        total_con_iva = total_renta + iva

        # Actualizar cuentas
        self.caja -= total_con_iva
        self.iva_acreditable += iva
        self.rentas_anticipadas += total_renta
        self.recalcular_totales()

        # Registrar la transacción en el libro diario
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
        """
        Genera una tabla de texto con la estructura:
         - Encabezados: ACTIVO, PASIVO y CAPITAL.
         - Bajo ACTIVO se separan los activos circulantes y no circulantes.
         - Se listan las cuentas y se muestran los totales.
        """
        anticipo_total = sum(monto for _, monto in self.anticipo_clientes)
        total_no_circulante = sum(valor for _, valor in self.activos_no_circulantes)
        
        tabla = f"{'ACTIVO':<45}{'PASIVO':<35}{'CAPITAL':<20}\n"
        tabla += "=" * 100 + "\n"
        
        # Activo Circulante
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
        
        # Activo No Circulante
        tabla += "\nActivo No Circulante:\n"
        if self.activos_no_circulantes:
            for nombre, valor in self.activos_no_circulantes:
                tabla += f"  {nombre}: ${valor:,.2f}\n"
        else:
            tabla += "  (Sin activos no circulantes)\n"
        tabla += f"  Total Activo No Circulante: ${total_no_circulante:,.2f}\n"
        
        # Pasivo
        tabla += "\nPASIVO:\n"
        tabla += f"  Acreedores: ${self.acreedores:,.2f}\n"
        tabla += f"  Documentos por Pagar: ${self.documentos_por_pagar:,.2f}\n"
        tabla += f"  Anticipo de Clientes: ${anticipo_total:,.2f}\n"
        tabla += f"  IVA Trasladado: ${self.iva_trasladado:,.2f}\n"
        
        # Totales y Capital
        tabla += "=" * 100 + "\n"
        tabla += f"Total Activo: ${self.total_activo:,.2f}\n"
        tabla += f"Total Pasivo: ${self.total_pasivo:,.2f}\n"
        tabla += f"Capital: ${self.capital:,.2f}\n"
        tabla += f"Total Pasivo + Capital: ${self.total_pasivo + self.capital:,.2f}\n"
        
        return tabla

    def generar_libro_diario(self):
        """
        Genera una tabla de texto con el libro diario.
        """
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
        """
        Genera una tabla de texto con el mayor de cada cuenta.
        """
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

# ========================
# INTERFAZ EN STREAMLIT
# ========================
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
                                 "BC"))
        
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
        elif menu == "Libro Diario":
            st.subheader("Libro Diario")
            st.code(data.generar_libro_diario())
        elif menu == "Mayor":
            st.subheader("Mayor")
            st.code(data.generar_mayor())
        elif menu == "BC":
            mostrar_bc(data)

def mostrar_asiento_apertura(data: AperturaData):
    st.subheader("Asiento de Apertura")
    if data.apertura_realizada:
        st.info("El asiento de apertura ya fue realizado.")
        st.code(data.generar_tabla_balance())
        return

    # Ingreso inicial de Caja, Banco e Inventario
    nuevo_monto_caja = st.number_input("Ingrese el monto inicial de Caja (Activo Circulante):", min_value=0.0, step=1000.0)
    nuevo_monto_banco = st.number_input("Ingrese el monto inicial de Banco (Activo Circulante):", min_value=0.0, step=1000.0)
    nuevo_monto_inventario = st.number_input("Ingrese el monto inicial de Inventario (Activo Circulante):", min_value=0.0, step=1000.0)
    
    if st.button("Actualizar Montos Iniciales"):
        data.caja = nuevo_monto_caja
        data.banco = nuevo_monto_banco
        data.inventario = nuevo_monto_inventario
        st.success("Montos iniciales actualizados.")

    # Agregar activos no circulantes (compras iniciales)
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

def mostrar_compra_efectivo(data: AperturaData):
    st.subheader("Compra en Efectivo")
    
    # Seleccionar si se desea mover un activo circulante o no circulante
    tipo_activo = st.selectbox("Seleccione el tipo de activo:", ["Activo Circulante", "Activo No Circulante"])
    
    if tipo_activo == "Activo Circulante":
        # Seleccionar un activo circulante (solo Inventario)
        st.write("Seleccione un activo circulante:")
        activo_circulante = st.selectbox("Activo Circulante", ["Inventario"])
        
        valor = st.number_input("Valor de la Compra", min_value=0.0, step=1000.0, key="efectivo_valor")
        if st.button("Agregar Compra en Efectivo"):
            if activo_circulante == "Inventario":
                data.compra_en_efectivo(valor)
                st.success(f"Compra en efectivo por ${valor:,.2f} registrada en Inventario.")
            st.code(data.generar_tabla_balance())
    
    elif tipo_activo == "Activo No Circulante":
        # Seleccionar un activo no circulante existente o escribir uno nuevo
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

def mostrar_compra_credito(data: AperturaData):
    st.subheader("Compra a Crédito")
    
    # Seleccionar si se desea mover un activo circulante o no circulante
    tipo_activo = st.selectbox("Seleccione el tipo de activo:", ["Activo Circulante", "Activo No Circulante"])
    
    if tipo_activo == "Activo Circulante":
        # Seleccionar un activo circulante (solo Inventario)
        st.write("Seleccione un activo circulante:")
        activo_circulante = st.selectbox("Activo Circulante", ["Inventario"])
        
        valor = st.number_input("Valor de la Compra a Crédito", min_value=0.0, step=1000.0, key="credito_valor")
        if st.button("Agregar Compra a Crédito"):
            if activo_circulante == "Inventario":
                data.compra_en_efectivo(valor)
                st.success(f"Compra en efectivo por ${valor:,.2f} registrada en Inventario.")
            st.code(data.generar_tabla_balance())
    
    elif tipo_activo == "Activo No Circulante":
        # Seleccionar un activo no circulante existente o escribir uno nuevo
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

def mostrar_compra_combinada(data: AperturaData):
    st.subheader("Compra Combinada")
    
    # Seleccionar si se desea mover un activo circulante o no circulante
    tipo_activo = st.selectbox("Seleccione el tipo de activo:", ["Activo Circulante", "Activo No Circulante"])
    
    if tipo_activo == "Activo Circulante":
        # Seleccionar un activo circulante (solo Inventario)
        st.write("Seleccione un activo circulante:")
        activo_circulante = st.selectbox("Activo Circulante", ["Inventario"])
        
        valor = st.number_input("Valor de la Compra Combinada", min_value=0.0, step=1000.0, key="combinada_valor")
        if st.button("Agregar Compra Combinada"):
            if activo_circulante == "Inventario":
                data.compra_combinada("Inventario", valor)
                st.success(f"Compra combinada por ${valor:,.2f} registrada en Inventario.")
            st.code(data.generar_tabla_balance())
    
    elif tipo_activo == "Activo No Circulante":
        # Seleccionar un activo no circulante existente o escribir uno nuevo
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

def mostrar_anticipo_clientes(data: AperturaData):
    st.subheader("Anticipo de Clientes")
    
    # Ingresar el nombre del cliente
    nombre_cliente = st.text_input("Nombre del Cliente")
    
    # Ingresar la cantidad que el cliente va a abonar
    monto = st.number_input("Monto que el cliente va a abonar", min_value=0.0, step=1000.0, key="anticipo_monto")
    
    # Seleccionar el porcentaje a abonar (50% en este caso)
    porcentaje = st.selectbox("Porcentaje a abonar", [50])
    
    if st.button("Registrar Anticipo de Clientes"):
        if nombre_cliente.strip() != "" and monto > 0:
            data.anticipo_clientes_op(nombre_cliente, monto, porcentaje)
            st.success(f"Anticipo de cliente '{nombre_cliente}' por ${monto * (porcentaje / 100):,.2f} registrado.")
            st.code(data.generar_tabla_balance())
        else:
            st.warning("Ingrese un nombre válido y un monto mayor a 0.")

def mostrar_compra_papeleria(data: AperturaData):
    st.subheader("Compra de Papelería")
    
    # Ingresar el monto a pagar en papelería
    valor = st.number_input("Monto a pagar en papelería", min_value=0.0, step=1000.0, key="papeleria_valor")
    
    if st.button("Registrar Compra de Papelería"):
        if valor > 0:
            data.compra_papeleria_op(valor)
            st.success(f"Compra de papelería por ${valor:,.2f} registrada.")
            st.code(data.generar_tabla_balance())
        else:
            st.warning("Ingrese un monto válido para la papelería.")

def mostrar_pago_rentas(data: AperturaData):
    st.subheader("Pago de Rentas Pagadas por Anticipado")
    
    # Ingresar el valor de la renta de un mes
    valor_renta = st.number_input("Valor de la renta por un mes:", min_value=0.0, step=1000.0, key="rentas_valor")
    
    # Seleccionar la cantidad de meses a anticipar
    meses = st.selectbox("Seleccione la cantidad de meses a anticipar:", [2, 3, 4])
    
    if st.button("Registrar Pago de Rentas"):
        if valor_renta > 0:
            data.pago_rentas_op(valor_renta, meses)
            st.success(f"Pago de rentas por {meses} meses (${valor_renta * meses:,.2f} + IVA) registrado.")
            st.code(data.generar_tabla_balance())
        else:
            st.warning("Ingrese un valor válido para la renta.")

def mostrar_bc(data: AperturaData):
    st.subheader("Balance de Comprobación (BC)")
    
    # Crear una tabla para que el usuario ingrese los datos
    st.write("Ingrese los datos para el Balance de Comprobación:")
    
    # Definir las columnas de la tabla
    columnas = ["Cuenta", "Debe 1", "Haber 1", "Debe 2", "Haber 2"]
    
    # Crear un DataFrame vacío para almacenar los datos
    datos_bc = []
    
    # Permitir al usuario agregar filas a la tabla
    num_filas = st.number_input("Número de filas", min_value=1, value=1, step=1)
    
    for i in range(num_filas):
        st.write(f"Fila {i + 1}")
        cuenta = st.text_input(f"Cuenta {i + 1}", key=f"cuenta_{i}")
        debe1 = st.number_input(f"Debe 1 {i + 1}", min_value=0.0, key=f"debe1_{i}")
        haber1 = st.number_input(f"Haber 1 {i + 1}", min_value=0.0, key=f"haber1_{i}")
        debe2 = st.number_input(f"Debe 2 {i + 1}", min_value=0.0, key=f"debe2_{i}")
        haber2 = st.number_input(f"Haber 2 {i + 1}", min_value=0.0, key=f"haber2_{i}")
        datos_bc.append({"Cuenta": cuenta, "Debe 1": debe1, "Haber 1": haber1, "Debe 2": debe2, "Haber 2": haber2})
    
    # Mostrar la tabla ingresada por el usuario
    st.write("### Tabla de Balance de Comprobación")
    st.table(datos_bc)
    
    # Calcular totales
    total_debe1 = sum(fila["Debe 1"] for fila in datos_bc)
    total_haber1 = sum(fila["Haber 1"] for fila in datos_bc)
    total_debe2 = sum(fila["Debe 2"] for fila in datos_bc)
    total_haber2 = sum(fila["Haber 2"] for fila in datos_bc)
    
    st.write(f"**Total Debe 1:** ${total_debe1:,.2f}")
    st.write(f"**Total Haber 1:** ${total_haber1:,.2f}")
    st.write(f"**Total Debe 2:** ${total_debe2:,.2f}")
    st.write(f"**Total Haber 2:** ${total_haber2:,.2f}")
    
    if total_debe1 == total_haber1 and total_debe2 == total_haber2:
        st.success("El balance de comprobación está equilibrado.")
    else:
        st.error("El balance de comprobación no está equilibrado.")

if __name__ == "__main__":
    main()