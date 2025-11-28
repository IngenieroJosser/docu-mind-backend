import os
from datetime import datetime
from pathlib import Path
import jinja2
from fpdf import FPDF

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
        """Genera PDF usando la plantilla adecuada según el tipo de documentos"""
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
            
            # Generar PDF usando FPDF (fallback por ahora)
            pdf_generator = PDFGenerator()
            pdf_generator.create_pdf(documents, output_path, title, template_type)
            
            print(f"✅ PDF generado exitosamente en: {output_path}")
            print(f"📊 Tipo de template usado: {template_type.upper()}")
            
            return output_path
            
        except Exception as e:
            print(f"❌ Error en generate_pdf: {str(e)}")
            # Fallback a PDF básico
            self._generate_fallback_pdf(documents, output_path, title)
            return output_path

    def _generate_fallback_pdf(self, documents: list, output_path: str, title: str):
        """Genera un PDF básico como fallback"""
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
            for doc in documents:
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, doc['name'], 0, 1)
                pdf.set_font('Arial', 'I', 10)
                pdf.cell(0, 10, f"Tipo: {doc['type']} | Tamaño: {doc.get('size', 'N/A')}", 0, 1)
                pdf.set_font('Arial', '', 10)
                pdf.multi_cell(0, 8, doc.get('summary', 'Sin resumen disponible'))
                pdf.ln(5)
            
            pdf.output(output_path)
            print(f"✅ PDF de fallback generado en: {output_path}")
        except Exception as e:
            print(f"❌ Error en fallback PDF: {e}")
            raise

    def get_template_for_type(self, doc_type: str) -> str:
        """Método de compatibilidad para mantener la interfaz existente"""
        return doc_type

class PDFGenerator(FPDF):
    """Generador de PDF mejorado"""
    
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self.set_margins(20, 20, 20)
        
    def create_pdf(self, documents: list, output_path: str, title: str, template_type: str):
        """Crea el PDF completo"""
        self.add_page()
        
        # Configurar colores según el tipo
        if template_type == "scientific":
            title_color = (30, 58, 138)  # Azul académico
            accent_color = (124, 58, 237)  # Púrpura científico
        else:
            title_color = (59, 130, 246)  # Azul general
            accent_color = (139, 92, 246)  # Púrpura general
            
        # Título principal
        self.set_font('Arial', 'B', 20)
        self.set_text_color(*title_color)
        self.cell(0, 15, title, 0, 1, 'C')
        self.ln(8)
        
        # Información de generación
        self.set_font('Arial', 'I', 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 6, f'Fecha de generación: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1)
        self.cell(0, 6, f'Total de documentos procesados: {len(documents)}', 0, 1)
        
        # Estadísticas
        scientific_count = sum(1 for doc in documents if doc.get("type") == "scientific")
        general_count = len(documents) - scientific_count
        self.cell(0, 6, f'Documentos científicos: {scientific_count} | Documentos generales: {general_count}', 0, 1)
        self.cell(0, 6, f'Tipo de análisis: {template_type.upper()}', 0, 1)
        self.ln(12)
        
        # Contenido de cada documento
        for i, doc in enumerate(documents, 1):
            self.add_document_section(doc, i, accent_color)
            if i < len(documents):  # No agregar salto después del último
                self.ln(8)
        
        # Guardar PDF
        self.output(output_path)
        print(f"✅ PDF creado exitosamente: {output_path}")
        return output_path
    
    def add_document_section(self, doc: dict, doc_number: int, accent_color: tuple):
        """Agrega una sección para cada documento"""
        # Encabezado del documento
        self.set_font('Arial', 'B', 14)
        
        # Color diferente según el tipo de documento
        if doc["type"] == "scientific":
            self.set_fill_color(230, 240, 255)  # Azul claro para científicos
            self.set_text_color(70, 90, 160)    # Azul oscuro
        else:
            self.set_fill_color(240, 255, 240)  # Verde claro para generales
            self.set_text_color(60, 140, 60)    # Verde oscuro
            
        # Título del documento
        safe_title = self.safe_text(f'Documento {doc_number}: {doc["name"]}')
        self.cell(0, 10, safe_title, 1, 1, 'L', True)
        
        # Metadatos
        self.set_font('Arial', '', 10)
        self.set_text_color(0, 0, 0)
        
        # Tipo de documento con badge
        type_color = accent_color if doc["type"] == "scientific" else (52, 152, 219)
        self.set_fill_color(*type_color)
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
            '⭐': '[STAR]', '🔥': '[FIRE]', '🎯': '[TARGET]', '✨': '[SPARKLE]'
        }
        
        for emoji, replacement in replacements.items():
            text = text.replace(emoji, replacement)
        
        # Remover cualquier otro carácter no ASCII
        import re
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