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

st.set_page_config(page_title='DASHBOARD EMPRESARIAL', layout='wide')
st.title('Analisis de ventas')

st.metric('Total de ventas', f"${df['TotalVendido'].sum()}", "12%")


fig1 = px.line(
    df,
    x='ProductName',
    y='TotalVendido',
    title='Productos más vendidos',
    markers=True,
    color_discrete_sequence=["#1f77b4"]
)

fig2 = px.bar(
    df2,
    x='employee',
    y='total',
    title='Empleados con más ventas',
    color='total',
    color_continuous_scale='Blues'
)

fig3 = px.pie(
    df,
    values='TotalVendido',
    names='ProductName',
    title='Ventas por producto',
    color_discrete_sequence=px.colors.qualitative.Set3
)

st.plotly_chart(fig1, use_container_width=True)
st.plotly_chart(fig2, use_container_width=True)
st.plotly_chart(fig3, use_container_width=True)


st.sidebar.header('Filtros')

select = st.sidebar.multiselect(
    'Selecciona un producto',
    df['ProductName'].unique()
)

if select:
    filtro = df[df['ProductName'].isin(select)]
    st.dataframe(filtro, use_container_width=True)



class PDF(FPDF):
    def header(self):
        self.set_fill_color(30, 60, 114)
        self.rect(0, 0, 210, 20, 'F')

        self.set_text_color(255, 255, 255)
        self.set_font("Arial", "B", 14)
        self.cell(0, 10, "REPORTE DE VENTAS", 0, 1, "C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Pagina {self.page_no()}", 0, 0, "C")


def generar_pdf(df, df2, fig1, fig2, fig3):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    total = df['TotalVendido'].sum()
    top_producto = df.iloc[0]['ProductName']
    top_empleado = df2.iloc[0]['employee']

    pdf.add_page()

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 18)
    pdf.cell(0, 10, "Dashboard de Analisis", ln=True, align="C")

    pdf.set_font("Arial", "", 11)
    fecha = datetime.now().strftime("%d/%m/%Y")
    pdf.cell(0, 8, f"Fecha: {fecha}", ln=True, align="C")

    pdf.ln(10)

    pdf.set_font("Arial", "B", 12)

    pdf.set_fill_color(220, 230, 241)
    pdf.cell(60, 20, f"Total\n{total}", 0, 0, "C", True)

    pdf.set_fill_color(198, 224, 180)
    pdf.cell(60, 20, f"Top Producto\n{top_producto[:15]}", 0, 0, "C", True)

    pdf.set_fill_color(255, 217, 102)
    pdf.cell(60, 20, f"Top Empleado\n{top_empleado[:15]}", 0, 1, "C", True)

    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Top Productos", ln=True)

    pdf.set_fill_color(30, 60, 114)
    pdf.set_text_color(255, 255, 255)

    pdf.cell(120, 8, "Producto", 1, 0, "C", True)
    pdf.cell(40, 8, "Ventas", 1, 1, "C", True)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "", 10)

    for i, row in df.iterrows():
        fill = (i % 2 == 0)
        if fill:
            pdf.set_fill_color(240, 240, 240)

        pdf.cell(120, 8, str(row['ProductName'])[:40], 1, 0, fill=fill)
        pdf.cell(40, 8, str(row['TotalVendido']), 1, 1, fill=fill)


    fig1.update_layout(paper_bgcolor="white", plot_bgcolor="white")
    fig2.update_layout(paper_bgcolor="white", plot_bgcolor="white")
    fig3.update_layout(paper_bgcolor="white", plot_bgcolor="white")

    tmp1 = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp2 = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp3 = tempfile.NamedTemporaryFile(suffix=".png", delete=False)

    with open(tmp1.name, "wb") as f:
        f.write(fig1.to_image(format="png", scale=4))

    with open(tmp2.name, "wb") as f:
        f.write(fig2.to_image(format="png", scale=4))

    with open(tmp3.name, "wb") as f:
        f.write(fig3.to_image(format="png", scale=4))

    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Productos más vendidos", ln=True)
    pdf.image(tmp1.name, x=15, w=180)

    pdf.add_page()
    pdf.cell(0, 10, "Empleados", ln=True)
    pdf.image(tmp2.name, x=15, w=180)

    pdf.add_page()
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
