import os
from datetime import datetime
from pathlib import Path
import jinja2
from fpdf import FPDF
import html
import re

class TemplateManager:
    def __init__(self):
        self.template_dir = Path("templates")
        
        # Configurar Jinja2 para cargar plantillas
        self.template_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_dir),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )

    def determine_template_type(self, documents: list) -> str:
        """Determina si usar template científico o general basado en los documentos"""
        if not documents:
            return "general"
            
        scientific_count = sum(1 for doc in documents if doc.get("type") == "scientific")
        total_documents = len(documents)
        
        # Si más del 50% son científicos o hay al menos 2 científicos, usar template científico
        if scientific_count >= 2 or (scientific_count / total_documents) >= 0.5:
            return "scientific"
        else:
            return "general"

    def generate_pdf(self, documents: list, output_path: str, title: str = "Resumen Consolidado"):
        """Genera PDF usando la plantilla HTML adecuada según el tipo de documentos"""
        try:
            # Determinar qué template usar
            template_type = self.determine_template_type(documents)
            template_file = f"{template_type}_template.html"
            
            print(f"🎨 Usando template: {template_file} para {len(documents)} documentos")
            
            # Cargar y renderizar la plantilla
            template = self.template_env.get_template(template_file)
            
            # Preparar el contexto para la plantilla
            context = {
                "title": title,
                "documents": documents,
                "total_documents": len(documents),
                "summary_date": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            
            # Renderizar HTML
            html_content = template.render(context)
            
            # Generar PDF usando FPDF mejorado con soporte básico para HTML
            self._generate_pdf_with_fpdf(html_content, documents, output_path, title, template_type)
            
            print(f"✅ PDF generado exitosamente en: {output_path}")
            print(f"📊 Tipo de template usado: {template_type.upper()}")
            
            return output_path
            
        except Exception as e:
            print(f"❌ Error en generate_pdf: {str(e)}")
            # Fallback a PDF básico
            self._generate_fallback_pdf(documents, output_path, title)
            return output_path

    def _generate_pdf_with_fpdf(self, html_content: str, documents: list, output_path: str, title: str, template_type: str):
        """Genera PDF usando FPDF con diseño mejorado que simula las plantillas HTML"""
        try:
            pdf = EnhancedPDF(template_type)
            pdf.create_pdf(documents, output_path, title)
            
        except Exception as e:
            print(f"❌ Error con FPDF mejorado: {e}")
            # Fallback al método básico
            self._generate_fallback_pdf(documents, output_path, title)

    def _generate_fallback_pdf(self, documents: list, output_path: str, title: str):
        """Genera un PDF básico como fallback usando FPDF"""
        try:
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            
            # Título
            pdf.set_font('Arial', 'B', 16)
            pdf.cell(0, 10, title, 0, 1, 'C')
            pdf.ln(10)
            
            # Información
            pdf.set_font('Arial', '', 12)
            pdf.cell(0, 10, f'Fecha: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1)
            pdf.cell(0, 10, f'Total documentos: {len(documents)}', 0, 1)
            pdf.ln(10)
            
            # Documentos
            for i, doc in enumerate(documents, 1):
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, f'Documento {i}: {doc["name"]}', 0, 1)
                pdf.set_font('Arial', 'I', 10)
                pdf.cell(0, 10, f"Tipo: {doc['type']} | Tamaño: {doc.get('size', 'N/A')}", 0, 1)
                pdf.set_font('Arial', '', 10)
                
                # Procesar resumen para PDF
                summary = self._clean_text_for_pdf(doc.get('summary', 'Sin resumen disponible'))
                pdf.multi_cell(0, 8, summary)
                pdf.ln(5)
                
                if i < len(documents):
                    pdf.ln(5)
            
            pdf.output(output_path)
            print(f"✅ PDF de fallback generado en: {output_path}")
        except Exception as e:
            print(f"❌ Error en fallback PDF: {e}")
            raise

    def _clean_text_for_pdf(self, text: str) -> str:
        """Limpia texto para compatibilidad con PDF"""
        if not text:
            return ""
        
        # Reemplazar caracteres problemáticos
        replacements = {
            '📄': '[DOC]', '📊': '[CHART]', '📝': '[TEXT]', '🤖': '[AI]',
            '🔬': '[SCIENCE]', '📖': '[BOOK]', '💾': '[SAVE]', '🧹': '[CLEAN]',
            '⚠️': '[WARNING]', '✅': '[OK]', '❌': '[ERROR]', '🔍': '[SEARCH]',
            '🏷️': '[TAG]', '📥': '[DOWNLOAD]', '🌐': '[WEB]', '🚀': '[ROCKET]',
            '💡': '[IDEA]', '🔧': '[TOOL]', '📈': '[GRAPH]', '🔒': '[LOCK]',
            '⭐': '[STAR]', '🔥': '[FIRE]', '🎯': '[TARGET]', '✨': '[SPARKLE]',
            '‘': "'", '’': "'", '“': '"', '”': '"', '–': '-', '—': '-'
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        # Remover HTML tags si existen
        text = re.sub(r'<[^>]+>', '', text)
        
        return text

    def get_template_for_type(self, doc_type: str) -> str:
        """Método de compatibilidad para mantener la interfaz existente"""
        return doc_type

class EnhancedPDF(FPDF):
    """Generador de PDF mejorado que simula el diseño de las plantillas HTML"""
    
    def __init__(self, template_type: str):
        super().__init__()
        self.template_type = template_type
        self.set_auto_page_break(auto=True, margin=15)
        self.set_margins(20, 20, 20)
        
    def create_pdf(self, documents: list, output_path: str, title: str):
        """Crea el PDF completo con diseño mejorado"""
        self.add_page()
        
        # Configurar colores según el tipo de template
        if self.template_type == "scientific":
            primary_color = (30, 58, 138)    # Azul oscuro científico
            secondary_color = (124, 58, 237) # Púrpura científico
            accent_color = (139, 92, 246)    # Púrpura claro
        else:
            primary_color = (59, 130, 246)   # Azul general
            secondary_color = (37, 99, 235)  # Azul oscuro general
            accent_color = (96, 165, 250)    # Azul claro
        
        # Header style
        self.set_fill_color(*primary_color)
        self.rect(0, 0, 210, 60, 'F')
        
        # Título principal
        self.set_xy(20, 20)
        self.set_font('Arial', 'B', 20)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, title, 0, 1, 'L')
        
        # Subtítulo
        self.set_xy(20, 35)
        self.set_font('Arial', 'I', 14)
        self.set_text_color(255, 255, 255)
        if self.template_type == "scientific":
            self.cell(0, 10, "Reporte Científico Consolidado", 0, 1, 'L')
        else:
            self.cell(0, 10, "Inteligencia de Documentos Reimaginada", 0, 1, 'L')
        
        # Información de generación
        self.set_xy(20, 80)
        self.set_font('Arial', '', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, f'Fecha de generación: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1)
        self.cell(0, 6, f'Total de documentos procesados: {len(documents)}', 0, 1)
        
        # Estadísticas
        scientific_count = sum(1 for doc in documents if doc.get("type") == "scientific")
        general_count = len(documents) - scientific_count
        self.cell(0, 6, f'Documentos científicos: {scientific_count} | Documentos generales: {general_count}', 0, 1)
        self.cell(0, 6, f'Tipo de análisis: {self.template_type.upper()}', 0, 1)
        self.ln(12)
        
        # Resumen ejecutivo
        self.set_font('Arial', 'B', 14)
        self.set_text_color(*primary_color)
        self.cell(0, 10, "RESUMEN EJECUTIVO", 0, 1)
        
        self.set_font('Arial', '', 10)
        self.set_text_color(0, 0, 0)
        if self.template_type == "scientific":
            summary_text = f"Este reporte contiene el análisis consolidado de {len(documents)} documentos científicos procesados mediante inteligencia artificial. Cada documento ha sido analizado y se ha generado un resumen ejecutivo con los puntos más relevantes, metodologías, hallazgos y conclusiones."
        else:
            summary_text = f"Este reporte contiene el análisis consolidado de {len(documents)} documentos procesados mediante inteligencia artificial. Cada documento ha sido clasificado automáticamente y se ha generado un resumen ejecutivo con los puntos más relevantes."
        
        self.multi_cell(0, 6, summary_text)
        self.ln(10)
        
        # Contenido de cada documento
        for i, doc in enumerate(documents, 1):
            self.add_document_section(doc, i, accent_color, secondary_color)
            if i < len(documents):  # No agregar salto después del último
                self.ln(8)
        
        # Footer
        self.set_y(-30)
        self.set_font('Arial', 'I', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, "DocuMind AI - Análisis Inteligente de Documentos", 0, 1, 'C')
        self.cell(0, 6, f"Generado automáticamente el {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1, 'C')
        
        # Guardar PDF
        self.output(output_path)
        print(f"✅ PDF mejorado creado exitosamente: {output_path}")
        return output_path
    
    def add_document_section(self, doc: dict, doc_number: int, accent_color: tuple, secondary_color: tuple):
        """Agrega una sección para cada documento con diseño mejorado"""
        # Encabezado del documento con fondo de color
        if doc["type"] == "scientific":
            self.set_fill_color(230, 240, 255)  # Azul claro para científicos
            self.set_text_color(70, 90, 160)    # Azul oscuro
        else:
            self.set_fill_color(240, 255, 240)  # Verde claro para generales
            self.set_text_color(60, 140, 60)    # Verde oscuro
            
        # Título del documento
        safe_title = self.safe_text(f'Documento {doc_number}: {doc["name"]}')
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, safe_title, 1, 1, 'L', True)
        
        # Metadatos
        self.set_font('Arial', '', 10)
        self.set_text_color(0, 0, 0)
        
        # Tipo de documento con badge
        if doc["type"] == "scientific":
            self.set_fill_color(*accent_color)
        else:
            self.set_fill_color(*secondary_color)
            
        self.set_text_color(255, 255, 255)
        
        type_text = "CIENTÍFICO" if doc["type"] == "scientific" else "GENERAL"
        self.cell(30, 6, type_text, 1, 0, 'C', True)
        
        self.set_text_color(0, 0, 0)
        self.cell(10, 6, '', 0, 0)  # Espacio
        
        if doc.get('size'):
            self.set_font('Arial', 'I', 9)
            self.cell(0, 6, f'Tamaño: {doc["size"]}', 0, 1)
        else:
            self.cell(0, 6, '', 0, 1)  # Nueva línea
        
        self.ln(4)
        
        # Resumen
        self.set_font('Arial', 'B', 12)
        self.set_text_color(44, 62, 80)
        self.cell(0, 8, 'RESUMEN:', 0, 1)
        
        self.set_font('Arial', '', 10)
        self.set_text_color(0, 0, 0)
        
        # Usar texto seguro para el resumen
        summary = doc.get('summary', 'No hay resumen disponible para este documento.')
        safe_summary = self.safe_text(summary)
        
        # Procesar el resumen para el PDF
        self.multi_cell(0, 5, safe_summary)
        
        # Sección especial para documentos científicos
        if doc["type"] == "scientific" and self.template_type == "scientific":
            self.ln(3)
            self.set_font('Arial', 'I', 9)
            self.set_text_color(100, 100, 100)
            self.multi_cell(0, 4, "Metodología de análisis: Este documento ha sido procesado utilizando técnicas de análisis científico especializado, incluyendo identificación de hipótesis, metodologías de investigación, resultados clave y conclusiones académicas.")
        
        # Línea separadora
        self.ln(6)
        self.set_draw_color(200, 200, 200)
        self.cell(0, 0, '', 'T', 1)
        self.ln(2)

    def safe_text(self, text: str) -> str:
        """Convierte texto a formato seguro para PDF"""
        if not text:
            return ""
        
        # Reemplazar emojis y caracteres problemáticos
        replacements = {
            '📄': '[DOC]', '📊': '[CHART]', '📝': '[TEXT]', '🤖': '[AI]',
            '🔬': '[SCIENCE]', '📖': '[BOOK]', '💾': '[SAVE]', '🧹': '[CLEAN]',
            '⚠️': '[WARNING]', '✅': '[OK]', '❌': '[ERROR]', '🔍': '[SEARCH]',
            '🏷️': '[TAG]', '📥': '[DOWNLOAD]', '🌐': '[WEB]', '🚀': '[ROCKET]',
            '💡': '[IDEA]', '🔧': '[TOOL]', '📈': '[GRAPH]', '🔒': '[LOCK]',
            '⭐': '[STAR]', '🔥': '[FIRE]', '🎯': '[TARGET]', '✨': '[SPARKLE]',
            '‘': "'", '’': "'", '“': '"', '”': '"', '–': '-', '—': '-',
            'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
            'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
            'ñ': 'n', 'Ñ': 'N'
        }
        
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        # Remover cualquier otro carácter no ASCII
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()

def get_template_context(documents: list, title: str = "Resumen Consolidado"):
    """Contexto común para todas las plantillas"""
    return {
        "title": title,
        "documents": documents,
        "total_documents": len(documents),
        "summary_date": datetime.now().strftime("%Y-%m-%d %H:%M")
    }