import pandas as pd
import streamlit as st
import plotly.express as px
import sqlite3 as sql
from fpdf import FPDF
import tempfile
from datetime import datetime

conexion = sql.connect('Northwind.db')

df = pd.read_sql_query('''
SELECT p.ProductName, SUM(o.Quantity) AS TotalVendido
FROM Products p
JOIN OrderDetails o ON p.ProductID = o.ProductID
GROUP BY p.ProductName
ORDER BY TotalVendido DESC
LIMIT 10;
''', conexion)

df2 = pd.read_sql_query('''
SELECT FirstName || " " || LastName as employee, COUNT(*) as total
FROM Orders o
JOIN Employees e
on e.EmployeeID = o.EmployeeID
GROUP BY o.EmployeeID
ORDER BY total DESC
''', conexion)

conexion.close()

st.set_page_config(page_title='DASBHOARD EMPRESARIAL', layout='wide')

st.title('Analisis de ventas')

col1 = st.columns(1)[0]

with col1:
    st.metric('Total de ventas sumado', df['TotalVendido'].sum(), '12%')

fig1 = px.line(df, x='ProductName', y='TotalVendido',
               title='Productos mas Vendidos')
st.plotly_chart(fig1, use_container_width=True)

fig2 = px.bar(df2, x='employee', y='total',
              title='Empleados con mas ventas')
st.plotly_chart(fig2, use_container_width=True)

fig3 = px.pie(df, values='TotalVendido', names='ProductName',
              title='Ventas por Producto')
st.plotly_chart(fig3, use_container_width=True)

st.sidebar.header('Filtros')

select = st.sidebar.multiselect('Selecciona un producto', df['ProductName'].unique())
if select:
    filtro = df[df['ProductName'].isin(select)]
    st.dataframe(filtro, use_container_width=True)


def generar_pdf(df, df2, fig1, fig2, fig3):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    total = df['TotalVendido'].sum()
    top_producto = df.iloc[0]['ProductName']
    top_empleado = df2.iloc[0]['employee']


    pdf.add_page()
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 12, "REPORTE DE VENTAS", ln=True, align="C")

    pdf.set_font("Arial", "", 11)
    fecha = datetime.now().strftime("%d/%m/%Y")
    pdf.cell(0, 8, f"Fecha: {fecha}", ln=True, align="C")

    pdf.ln(10)


    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Indicadores", ln=True)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Total ventas: {total}", ln=True)
    pdf.cell(0, 8, f"Top producto: {top_producto}", ln=True)
    pdf.cell(0, 8, f"Top empleado: {top_empleado}", ln=True)

    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Top Productos", ln=True)

    pdf.set_font("Arial", "B", 11)
    pdf.cell(120, 8, "Producto", border=1)
    pdf.cell(40, 8, "Ventas", border=1, ln=True)

    pdf.set_font("Arial", "", 10)
    for _, row in df.iterrows():
        pdf.cell(120, 8, str(row['ProductName'])[:40], border=1)
        pdf.cell(40, 8, str(row['TotalVendido']), border=1, ln=True)


    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Empleados", ln=True)

    pdf.set_font("Arial", "B", 11)
    pdf.cell(120, 8, "Empleado", border=1)
    pdf.cell(40, 8, "Ventas", border=1, ln=True)

    pdf.set_font("Arial", "", 10)
    for _, row in df2.iterrows():
        pdf.cell(120, 8, str(row['employee'])[:40], border=1)
        pdf.cell(40, 8, str(row['total']), border=1, ln=True)


    tmp1 = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp2 = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp3 = tempfile.NamedTemporaryFile(suffix=".png", delete=False)

    with open(tmp1.name, "wb") as f:
        f.write(fig1.to_image(format="png", scale=3))

    with open(tmp2.name, "wb") as f:
        f.write(fig2.to_image(format="png", scale=3))

    with open(tmp3.name, "wb") as f:
        f.write(fig3.to_image(format="png", scale=3))

   
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Productos mas vendidos", ln=True)
    pdf.image(tmp1.name, x=15, w=180)

    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Empleados", ln=True)
    pdf.image(tmp2.name, x=15, w=180)

    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Distribucion", ln=True)
    pdf.image(tmp3.name, x=15, w=180)

    pdf_path = "reporte.pdf"
    pdf.output(pdf_path)

    return pdf_path


if st.button("Generar reporte PDF"):
    pdf_file = generar_pdf(df, df2, fig1, fig2, fig3)

    with open(pdf_file, "rb") as f:
        st.download_button(
            "Descargar PDF",
            f,
            file_name="reporte_ventas.pdf",
            mime="application/pdf"
        )
