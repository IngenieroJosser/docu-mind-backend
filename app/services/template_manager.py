import os
import json
from datetime import datetime
from pathlib import Path
from fastapi import HTTPException
from app.core.config import settings

try:
    from xhtml2pdf import pisa
    from io import BytesIO
    import logging
    # Configurar logging para xhtml2pdf
    logging.getLogger("xhtml2pdf").setLevel(logging.ERROR)
    XHTML2PDF_AVAILABLE = True
except ImportError as e:
    XHTML2PDF_AVAILABLE = False
    print(f"❌ xhtml2pdf no está disponible: {e}")
    print("Instala: pip install xhtml2pdf reportlab")

class TemplateManager:
    def __init__(self):
        self.templates_dir = Path("templates")
        self.ensure_templates_exist()
    
    def ensure_templates_exist(self):
        """Asegura que los templates existan en el filesystem"""
        self.templates_dir.mkdir(exist_ok=True)
        
        # Verificar y crear templates si no existen
        templates_to_check = {
            "general_template.html": self.get_default_general_template(),
            "scientific_template.html": self.get_default_scientific_template()
        }
        
        for template_name, default_content in templates_to_check.items():
            template_path = self.templates_dir / template_name
            if not template_path.exists():
                print(f"⚠️ Template no encontrado, creando: {template_path}")
                template_path.write_text(default_content, encoding='utf-8')
                print(f"✅ Template creado: {template_path}")
            else:
                print(f"✅ Template encontrado: {template_path}")
    
    def get_default_general_template(self):
        """Template general por defecto - Compatible con xhtml2pdf"""
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
    <style>
        /* Estilos optimizados para xhtml2pdf */
        body {
            font-family: Helvetica, Arial, sans-serif;
            font-size: 12px;
            line-height: 1.4;
            color: #333;
            margin: 0;
            padding: 0;
        }
        
        .page-container {
            width: 100%;
            max-width: 210mm;
            margin: 0 auto;
            padding: 15mm;
        }
        
        .header {
            background: linear-gradient(135deg, #2563eb 0%, #7c3aed 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 25px;
            text-align: center;
        }
        
        .badge {
            display: inline-block;
            background: rgba(255, 255, 255, 0.2);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: bold;
            margin-bottom: 15px;
        }
        
        .title {
            font-size: 24px;
            font-weight: 300;
            margin: 10px 0;
        }
        
        .subtitle {
            font-size: 16px;
            opacity: 0.9;
            margin: 10px 0;
        }
        
        .description {
            font-size: 14px;
            margin: 15px 0;
            opacity: 0.9;
        }
        
        .stats {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
        }
        
        .stat-item {
            text-align: center;
        }
        
        .stat-value {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-label {
            font-size: 11px;
            opacity: 0.8;
        }
        
        .content {
            margin: 20px 0;
        }
        
        .summary-section {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 25px;
        }
        
        .summary-title {
            font-size: 16px;
            font-weight: bold;
            color: #1e293b;
            margin-bottom: 10px;
            border-left: 4px solid #3b82f6;
            padding-left: 10px;
        }
        
        .documents-grid {
            display: block;
        }
        
        .document-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 20px;
            page-break-inside: avoid;
        }
        
        .document-card.scientific {
            border-left: 4px solid #8b5cf6;
            background: #faf5ff;
        }
        
        .document-card.general {
            border-left: 4px solid #3b82f6;
            background: #eff6ff;
        }
        
        .document-header {
            display: flex;
            align-items: flex-start;
            margin-bottom: 15px;
        }
        
        .document-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 16px;
            margin-right: 15px;
            flex-shrink: 0;
        }
        
        .document-info {
            flex: 1;
        }
        
        .document-name {
            font-size: 16px;
            font-weight: bold;
            color: #1e293b;
            margin-bottom: 8px;
        }
        
        .document-meta {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        
        .document-type {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: bold;
            text-transform: uppercase;
        }
        
        .document-type.scientific {
            background: #8b5cf6;
            color: white;
        }
        
        .document-type.general {
            background: #3b82f6;
            color: white;
        }
        
        .document-size {
            font-size: 11px;
            color: #64748b;
            background: #f1f5f9;
            padding: 4px 8px;
            border-radius: 6px;
        }
        
        .document-summary {
            color: #475569;
            line-height: 1.5;
            white-space: pre-line;
            font-size: 12px;
        }
        
        .footer {
            background: #f8fafc;
            border-top: 1px solid #e2e8f0;
            padding: 20px;
            text-align: center;
            margin-top: 30px;
            font-size: 11px;
            color: #64748b;
        }
        
        .footer-content {
            display: flex;
            justify-content: center;
            gap: 15px;
            flex-wrap: wrap;
        }
        
        .page-break {
            page-break-before: always;
            height: 0;
        }
        
        /* Estilos de impresión */
        @media print {
            body {
                margin: 0;
                padding: 0;
            }
            .page-container {
                padding: 15mm;
                margin: 0;
            }
            .document-card {
                page-break-inside: avoid;
            }
        }
    </style>
</head>
<body>
    <div class="page-container">
        <!-- Header Section -->
        <div class="header">
            <div class="badge">ANÁLISIS CON IA</div>
            <h1 class="title">{{ title }}</h1>
            <div class="subtitle">Inteligencia de Documentos Reimaginada</div>
            <p class="description">
                Resumen consolidado generado automáticamente con análisis de inteligencia artificial
            </p>
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-value">{{ total_documents }}</div>
                    <div class="stat-label">DOCUMENTOS</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{{ summary_date }}</div>
                    <div class="stat-label">FECHA</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">DocuMind AI</div>
                    <div class="stat-label">PLATAFORMA</div>
                </div>
            </div>
        </div>

        <!-- Content Section -->
        <div class="content">
            <!-- Summary Section -->
            <div class="summary-section">
                <h2 class="summary-title">Resumen Ejecutivo</h2>
                <p>
                    Este reporte contiene el análisis consolidado de {{ total_documents }} documentos procesados 
                    mediante inteligencia artificial. Cada documento ha sido clasificado automáticamente y se ha 
                    generado un resumen ejecutivo con los puntos más relevantes.
                </p>
            </div>

            <!-- Documents Grid -->
            <div class="documents-grid">
                {% for document in documents %}
                <div class="document-card {{ document.type }}">
                    <div class="document-header">
                        <div class="document-icon">📄</div>
                        <div class="document-info">
                            <h3 class="document-name">{{ document.name }}</h3>
                            <div class="document-meta">
                                <span class="document-type {{ document.type }}">
                                    {{ document.type.upper() }}
                                </span>
                                {% if document.size %}
                                <span class="document-size">{{ document.size }}</span>
                                {% endif %}
                            </div>
                        </div>
                    </div>
                    <div class="document-summary">{{ document.summary }}</div>
                </div>
                {% if loop.index % 2 == 0 %}
                <div class="page-break"></div>
                {% endif %}
                {% endfor %}
            </div>
        </div>

        <!-- Footer -->
        <div class="footer">
            <div class="footer-content">
                <span>DocuMind AI</span>
                <span>•</span>
                <span>Análisis Inteligente de Documentos</span>
                <span>•</span>
                <span>Generado automáticamente</span>
            </div>
        </div>
    </div>
</body>
</html>"""
    
    def get_default_scientific_template(self):
        """Template científico por defecto - Compatible con xhtml2pdf"""
        return """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{{ title }} - Scientific Analysis</title>
    <style>
        /* Estilos optimizados para xhtml2pdf */
        body {
            font-family: Helvetica, Arial, sans-serif;
            font-size: 12px;
            line-height: 1.4;
            color: #333;
            margin: 0;
            padding: 0;
        }
        
        .page-container {
            width: 100%;
            max-width: 210mm;
            margin: 0 auto;
            padding: 15mm;
        }
        
        .header {
            background: linear-gradient(135deg, #1e3a8a 0%, #7c3aed 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 25px;
            text-align: center;
        }
        
        .scientific-badge {
            display: inline-block;
            background: rgba(255, 255, 255, 0.2);
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: bold;
            margin-bottom: 15px;
            text-transform: uppercase;
        }
        
        .title {
            font-size: 24px;
            font-weight: 300;
            margin: 10px 0;
        }
        
        .subtitle {
            font-size: 16px;
            opacity: 0.9;
            margin: 10px 0;
        }
        
        .description {
            font-size: 14px;
            margin: 15px 0;
            opacity: 0.9;
            max-width: 600px;
            margin-left: auto;
            margin-right: auto;
        }
        
        .research-stats {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        
        .stat-item {
            text-align: center;
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 6px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            min-width: 100px;
        }
        
        .stat-value {
            font-size: 16px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        
        .stat-label {
            font-size: 10px;
            opacity: 0.9;
            text-transform: uppercase;
        }
        
        .content {
            margin: 20px 0;
        }
        
        .executive-summary {
            background: #f1f5f9;
            border-left: 4px solid #1e3a8a;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 25px;
            position: relative;
        }
        
        .summary-title {
            font-size: 16px;
            font-weight: bold;
            color: #1e3a8a;
            margin-bottom: 10px;
        }
        
        .methodology {
            background: white;
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            padding: 15px;
            margin: 15px 0;
        }
        
        .methodology-title {
            font-size: 14px;
            font-weight: bold;
            color: #0d9488;
            margin-bottom: 8px;
        }
        
        .documents-grid {
            display: block;
        }
        
        .document-card {
            background: white;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #7c3aed;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 20px;
            page-break-inside: avoid;
        }
        
        .document-header {
            display: flex;
            align-items: flex-start;
            margin-bottom: 15px;
        }
        
        .document-icon {
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #1e3a8a 0%, #7c3aed 100%);
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 16px;
            margin-right: 15px;
            flex-shrink: 0;
        }
        
        .document-info {
            flex: 1;
        }
        
        .document-name {
            font-size: 16px;
            font-weight: bold;
            color: #1e293b;
            margin-bottom: 8px;
        }
        
        .document-meta {
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }
        
        .document-type {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: bold;
            text-transform: uppercase;
            background: #7c3aed;
            color: white;
        }
        
        .document-size {
            font-size: 11px;
            color: #1e3a8a;
            background: #eff6ff;
            padding: 4px 8px;
            border-radius: 6px;
            font-weight: bold;
        }
        
        .document-summary {
            color: #475569;
            line-height: 1.5;
            white-space: pre-line;
            font-size: 12px;
            background: #f8fafc;
            padding: 15px;
            border-radius: 6px;
            border-left: 4px solid #d97706;
        }
        
        .key-findings {
            background: #fffbeb;
            border: 1px solid #fef3c7;
            border-radius: 6px;
            padding: 15px;
            margin-top: 15px;
        }
        
        .findings-title {
            color: #d97706;
            font-size: 13px;
            font-weight: bold;
            margin-bottom: 8px;
        }
        
        .findings-list {
            list-style: none;
            padding: 0;
            margin: 0;
        }
        
        .finding-item {
            padding: 6px 0;
            border-bottom: 1px solid #fef3c7;
            display: flex;
            align-items: flex-start;
        }
        
        .finding-item:last-child {
            border-bottom: none;
        }
        
        .finding-item::before {
            content: "→";
            color: #d97706;
            font-weight: bold;
            margin-right: 8px;
            margin-top: 1px;
        }
        
        .footer {
            background: #0f172a;
            color: white;
            padding: 20px;
            text-align: center;
            margin-top: 30px;
            border-radius: 6px;
        }
        
        .footer-content {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
        }
        
        .footer-logo {
            display: flex;
            align-items: center;
            gap: 10px;
            font-weight: bold;
            font-size: 14px;
        }
        
        .logo-icon {
            width: 30px;
            height: 30px;
            background: linear-gradient(135deg, #7c3aed 0%, #0d9488 100%);
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
        }
        
        .footer-meta {
            display: flex;
            gap: 15px;
            font-size: 11px;
            opacity: 0.9;
            flex-wrap: wrap;
            justify-content: center;
        }
        
        .ai-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            font-size: 10px;
            font-weight: bold;
        }
        
        .page-break {
            page-break-before: always;
            height: 0;
        }
        
        /* Estilos de impresión */
        @media print {
            body {
                margin: 0;
                padding: 0;
            }
            .page-container {
                padding: 15mm;
                margin: 0;
            }
            .document-card {
                page-break-inside: avoid;
            }
        }
    </style>
</head>
<body>
    <div class="page-container">
        <!-- Scientific Header -->
        <div class="header">
            <div class="scientific-badge">Scientific Analysis</div>
            <h1 class="title">{{ title }}</h1>
            <div class="subtitle">Academic Research Consolidation</div>
            <p class="description">
                Comprehensive scientific analysis generated through advanced AI processing of academic documents, 
                research papers, and scholarly publications with specialized domain understanding.
            </p>
            <div class="research-stats">
                <div class="stat-item">
                    <div class="stat-value">{{ total_documents }}</div>
                    <div class="stat-label">Research Papers</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">{{ summary_date }}</div>
                    <div class="stat-label">Analysis Date</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">AI-Powered</div>
                    <div class="stat-label">Methodology</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">Academic</div>
                    <div class="stat-label">Focus</div>
                </div>
            </div>
        </div>

        <!-- Scientific Content -->
        <div class="content">
            <!-- Executive Summary -->
            <div class="executive-summary">
                <h2 class="summary-title">Executive Summary</h2>
                <p>
                    This scientific report consolidates analysis of <strong>{{ total_documents }} academic documents</strong> 
                    processed through specialized AI algorithms. Each document has been automatically classified, 
                    analyzed for key research components, and summarized to highlight methodological approaches, 
                    findings, and academic significance.
                </p>
                <div class="methodology">
                    <h3 class="methodology-title">Analysis Methodology</h3>
                    <p>
                        Documents were processed using natural language processing and machine learning algorithms 
                        specifically trained on academic corpora. Analysis includes: research question identification, 
                        methodology classification, results extraction, and conclusion synthesis.
                    </p>
                </div>
            </div>

            <!-- Research Documents -->
            <div class="documents-grid">
                {% for document in documents %}
                <div class="document-card">
                    <div class="document-header">
                        <div class="document-icon">📚</div>
                        <div class="document-info">
                            <h3 class="document-name">{{ document.name }}</h3>
                            <div class="document-meta">
                                <span class="document-type">{{ document.type.upper() }}</span>
                                {% if document.size %}
                                <span class="document-size">{{ document.size }}</span>
                                {% endif %}
                            </div>
                        </div>
                    </div>
                    <div class="document-summary">{{ document.summary }}</div>
                    <div class="key-findings">
                        <h4 class="findings-title">Key Research Insights</h4>
                        <ul class="findings-list">
                            <li class="finding-item">Methodological approach identified and categorized</li>
                            <li class="finding-item">Primary research questions extracted</li>
                            <li class="finding-item">Statistical findings and conclusions highlighted</li>
                            <li class="finding-item">Academic contribution significance assessed</li>
                        </ul>
                    </div>
                </div>
                {% if loop.index % 2 == 0 %}
                <div class="page-break"></div>
                {% endif %}
                {% endfor %}
            </div>
        </div>

        <!-- Scientific Footer -->
        <div class="footer">
            <div class="footer-content">
                <div class="footer-logo">
                    <div class="logo-icon">🧪</div>
                    DocuMind AI Research
                </div>
                <div class="footer-meta">
                    <span>Academic Document Analysis</span>
                    <span>•</span>
                    <span>AI-Powered Research Synthesis</span>
                    <span>•</span>
                    <div class="ai-badge">
                        <span>🤖</span>
                        SCIENTIFIC AI
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""

    def generate_pdf(self, documents: list, output_path: str, title: str = "Resumen Consolidado"):
        """Genera PDF usando xhtml2pdf (compatible con Windows)"""
        if not XHTML2PDF_AVAILABLE:
            raise RuntimeError(
                "xhtml2pdf no está disponible. "
                "Instala: pip install xhtml2pdf reportlab"
            )
        
        try:
            # Determinar el tipo de template
            has_scientific = any(doc.get('type') == 'scientific' for doc in documents)
            template_name = "scientific_template.html" if has_scientific else "general_template.html"
            template_path = self.templates_dir / template_name
            
            print(f"🎨 Usando template: {template_name}")
            print(f"📁 Ruta del template: {template_path}")
            
            if not template_path.exists():
                raise FileNotFoundError(f"Template no encontrado: {template_path}")
            
            # Leer template desde archivo
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Preparar contexto
            context = {
                "title": title,
                "documents": documents,
                "total_documents": len(documents),
                "summary_date": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            
            # Renderizar template simple (sin Jinja2 complejo)
            html_content = template_content
            
            # Reemplazar variables del contexto
            for key, value in context.items():
                placeholder = "{{ " + key + " }}"
                html_content = html_content.replace(placeholder, str(value))
            
            # Procesar documentos manualmente (sin loops Jinja2)
            documents_html = ""
            for i, doc in enumerate(documents, 1):
                # Escapar caracteres especiales para HTML
                doc_name = str(doc.get('name', 'Documento sin nombre')).replace('"', '&quot;')
                doc_type = str(doc.get('type', 'general'))
                doc_size = str(doc.get('size', ''))
                doc_summary = str(doc.get('summary', 'No hay resumen disponible para este documento.')).replace('\n', '<br>')
                
                doc_html = f"""
                <div class="document-card {doc_type}">
                    <div class="document-header">
                        <div class="document-icon">📄</div>
                        <div class="document-info">
                            <h3 class="document-name">{doc_name}</h3>
                            <div class="document-meta">
                                <span class="document-type {doc_type}">
                                    {doc_type.upper()}
                                </span>
                """
                
                if doc_size:
                    doc_html += f'<span class="document-size">{doc_size}</span>'
                
                doc_html += f"""
                            </div>
                        </div>
                    </div>
                    <div class="document-summary">{doc_summary}</div>
                </div>
                """
                
                # Añadir salto de página cada 2 documentos
                if i % 2 == 0:
                    doc_html += '<div class="page-break"></div>'
                
                documents_html += doc_html
            
            # Reemplazar el contenido de documentos en el template
            html_content = html_content.replace("{% for document in documents %}", "")
            html_content = html_content.replace("{% endfor %}", "")
            html_content = html_content.replace('{% if loop.index % 2 == 0 %}page-break{% endif %}', '')
            
            # Buscar y reemplazar el bloque de documentos
            start_marker = '<!-- Documents Grid -->'
            end_marker = '<!-- /Documents Grid -->'
            
            start_idx = html_content.find(start_marker)
            end_idx = html_content.find(end_marker)
            
            if start_idx != -1 and end_idx != -1:
                # Encontrar el div que contiene los documentos
                grid_start = html_content.find('<div class="documents-grid">', start_idx, end_idx)
                grid_end = html_content.find('</div>', grid_start) + 6
                
                if grid_start != -1 and grid_end != -1:
                    html_content = (
                        html_content[:grid_start] + 
                        f'<div class="documents-grid">{documents_html}</div>' + 
                        html_content[grid_end:]
                    )
            else:
                # Fallback: reemplazar simple
                html_content = html_content.replace('<div class="documents-grid">', f'<div class="documents-grid">{documents_html}')
            
            # Asegurar que el directorio de salida existe
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Generar PDF con xhtml2pdf
            print(f"🔄 Generando PDF en: {output_path}")
            
            with open(output_path, "wb") as pdf_file:
                pisa_status = pisa.CreatePDF(
                    html_content,
                    dest=pdf_file,
                    encoding='utf-8'
                )
            
            if pisa_status.err:
                raise Exception(f"Error generando PDF: {pisa_status.err}")
            
            # Verificar que el PDF se creó
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                if file_size > 0:
                    print(f"✅ PDF generado exitosamente: {output_path} ({file_size} bytes)")
                    return output_path
                else:
                    raise Exception("El archivo PDF se creó pero está vacío")
            else:
                raise Exception("El archivo PDF no se creó")
                
        except Exception as e:
            print(f"❌ Error generando PDF: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Limpiar archivo vacío si existe
            if os.path.exists(output_path) and os.path.getsize(output_path) == 0:
                try:
                    os.remove(output_path)
                    print("🧹 Archivo vacío eliminado")
                except:
                    pass
            raise

    def get_template_for_type(self, doc_type: str) -> str:
        return "scientific_template.html" if doc_type == "scientific" else "general_template.html"

def get_template_context(documents: list, title: str = "Resumen Consolidado"):
    return {
        "title": title,
        "documents": documents,
        "total_documents": len(documents),
        "summary_date": datetime.now().strftime("%Y-%m-%d %H:%M")
    }