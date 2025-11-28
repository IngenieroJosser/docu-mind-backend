import os
import json
import asyncio
import traceback
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import List, Dict, Any
import aiofiles

from app.models.schemas import (
    AnalysisResponse, 
    AnalysisStatusResponse, 
    CustomAnalysisRequest,
    Document,
    DocumentStatus,
    DocumentType
)
from app.services.document_processor import DocumentProcessor
from app.services.ai_agent import AIAgent
from app.services.template_manager import TemplateManager, get_template_context
from app.utils.file_handlers import ensure_directories, generate_job_id, save_upload_file
from app.core.config import settings

router = APIRouter()

# Almacenamiento en memoria para los trabajos
jobs: Dict[str, Dict[str, Any]] = {}

# Instancias de servicios
document_processor = DocumentProcessor()
ai_agent = AIAgent()
template_manager = TemplateManager()

@router.post("/analyze-documents", response_model=AnalysisResponse)
async def analyze_documents(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...)):
    """Endpoint para subir y analizar documentos"""
    print(f"📥 Recibida solicitud para analizar {len(files)} archivos")
    
    try:
        # Validar archivos
        if len(files) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 files allowed")
        
        for file in files:
            print(f"📄 Procesando archivo: {file.filename}")
            if not document_processor.is_supported_format(file.filename):
                raise HTTPException(status_code=400, detail=f"Unsupported file format: {file.filename}")
        
        # Crear job ID
        job_id = generate_job_id()
        print(f"🆕 Job creado: {job_id}")
        
        # Inicializar job
        jobs[job_id] = {
            "status": DocumentStatus.PROCESSING,
            "documents": [],
            "consolidated_pdf": None,
            "error": None
        }
        
        # Procesar en segundo plano
        background_tasks.add_task(process_documents, job_id, files)
        
        return AnalysisResponse(
            job_id=job_id,
            status=DocumentStatus.PROCESSING,
            documents=[],
            consolidated_pdf=None
        )
        
    except Exception as e:
        print(f"❌ Error en analyze_documents: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/analysis-status/{job_id}", response_model=AnalysisStatusResponse)
async def get_analysis_status(job_id: str):
    """Obtiene el estado de un trabajo de análisis"""
    print(f"📊 Consultando estado del job: {job_id}")
    
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    return AnalysisStatusResponse(
        job_id=job_id,
        status=job["status"],
        documents=job["documents"],
        consolidated_pdf=job["consolidated_pdf"],
        error=job.get("error")
    )

@router.post("/custom-analysis")
async def custom_analysis(request: CustomAnalysisRequest):
    """Análisis personalizado con prompt específico"""
    if request.job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[request.job_id]
    if job["status"] != DocumentStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Analysis not completed")
    
    # Generar análisis personalizado
    analysis_result = await ai_agent.custom_analysis(job["documents"], request.custom_prompt)
    
    return {
        "job_id": request.job_id,
        "custom_prompt": request.custom_prompt,
        "analysis_result": analysis_result,
        "message": "Custom analysis completed successfully"
    }

# Función de fondo para procesar documentos
async def process_documents(job_id: str, files: List[UploadFile]):
    """Procesa los documentos en segundo plano"""
    print(f"🔍 Iniciando procesamiento del job: {job_id}")
    
    try:
        ensure_directories()
        processed_documents = []
        
        for file in files:
            print(f"📖 Procesando: {file.filename}")
            
            try:
                # Guardar archivo temporalmente
                file_path = await save_upload_file(file, settings.UPLOAD_DIR)
                print(f"💾 Archivo guardado en: {file_path}")
                
                # Extraer texto
                text = await document_processor.extract_text(file_path)
                print(f"📝 Texto extraído: {len(text)} caracteres")
                
                # Clasificar documento
                doc_type = document_processor.classify_document(text, file.filename)
                print(f"🏷️ Documento clasificado como: {doc_type}")
                
                # Generar resumen con IA
                summary = await ai_agent.generate_summary(text, doc_type)
                print(f"🤖 Resumen generado: {len(summary)} caracteres")
                
                # Crear objeto documento
                doc_data = {
                    "id": generate_job_id(),
                    "name": file.filename,
                    "type": doc_type,
                    "status": "completed",
                    "summary": summary,
                    "size": f"{os.path.getsize(file_path) / 1024 / 1024:.1f} MB"
                }
                processed_documents.append(doc_data)
                
                # Limpiar archivo temporal
                try:
                    os.remove(file_path)
                    print(f"🧹 Archivo temporal eliminado: {file_path}")
                except Exception as e:
                    print(f"⚠️ No se pudo eliminar archivo temporal: {e}")
                    
            except Exception as file_error:
                print(f"❌ Error procesando archivo {file.filename}: {file_error}")
                print(traceback.format_exc())
                continue
        
        # Generar PDF consolidado si hay documentos procesados
        if processed_documents:
            output_pdf_path = os.path.join(settings.OUTPUT_DIR, f"{job_id}.pdf")
            print(f"📄 Generando PDF en: {output_pdf_path}")
            
            try:
                # Verificar que el template manager funcione
                print("🔄 Iniciando generación de PDF...")
                
                # Asegurar que el directorio existe
                os.makedirs(os.path.dirname(output_pdf_path), exist_ok=True)
                
                # Generar PDF con el nuevo TemplateManager
                template_manager.generate_pdf(
                    documents=processed_documents,
                    output_path=output_pdf_path,
                    title="Resumen Consolidado - DocuMind AI"
                )
                
                # Verificar que el PDF se creó y no está vacío
                if os.path.exists(output_pdf_path):
                    pdf_size = os.path.getsize(output_pdf_path)
                    print(f"✅ PDF generado exitosamente. Tamaño: {pdf_size} bytes")
                    
                    if pdf_size == 0:
                        raise Exception("Generated PDF file is empty")
                    
                    # Actualizar job con ruta absoluta para debug
                    pdf_url = f"/api/download-pdf/{job_id}"
                    jobs[job_id].update({
                        "status": "completed",
                        "documents": processed_documents,
                        "consolidated_pdf": pdf_url
                    })
                    print(f"✅ Job {job_id} completado exitosamente. PDF URL: {pdf_url}")
                    
                    # Debug: información sobre el tipo de template usado
                    template_type = template_manager.determine_template_type(processed_documents)
                    scientific_count = sum(1 for doc in processed_documents if doc.get("type") == "scientific")
                    general_count = len(processed_documents) - scientific_count
                    print(f"📊 Resumen del análisis:")
                    print(f"   - Total documentos: {len(processed_documents)}")
                    print(f"   - Científicos: {scientific_count}")
                    print(f"   - Generales: {general_count}")
                    print(f"   - Template usado: {template_type.upper()}")
                    
                else:
                    raise Exception("PDF file was not created")
                
            except Exception as pdf_error:
                print(f"❌ Error generando PDF: {pdf_error}")
                print(traceback.format_exc())
                jobs[job_id].update({
                    "status": "error",
                    "error": f"Error generando PDF: {str(pdf_error)}",
                    "consolidated_pdf": None
                })
        else:
            print(f"⚠️ No hay documentos procesados para el job {job_id}")
            jobs[job_id].update({
                "status": "error",
                "error": "No se pudieron procesar los documentos",
                "consolidated_pdf": None
            })
        
    except Exception as e:
        print(f"❌ Error crítico en process_documents: {str(e)}")
        print(traceback.format_exc())
        jobs[job_id].update({
            "status": "error",
            "error": f"Error procesando documentos: {str(e)}",
            "consolidated_pdf": None
        })

@router.get("/download-pdf/{job_id}")
async def download_pdf(job_id: str):
    """Descarga el PDF consolidado"""
    print(f"📥 Solicitud de descarga para job: {job_id}")
    
    if job_id not in jobs:
        print(f"❌ Job no encontrado: {job_id}")
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job["status"] != DocumentStatus.COMPLETED:
        print(f"❌ Job no completado: {job_id}, estado: {job['status']}")
        raise HTTPException(status_code=400, detail="Analysis not completed")
    
    pdf_path = os.path.join(settings.OUTPUT_DIR, f"{job_id}.pdf")
    print(f"🔍 Buscando PDF en: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF no encontrado en ruta: {pdf_path}")
        # Listar archivos en el directorio para debug
        try:
            files = os.listdir(settings.OUTPUT_DIR)
            print(f"📁 Archivos en output dir: {files}")
        except Exception as e:
            print(f"❌ Error listando directorio: {e}")
        
        raise HTTPException(status_code=404, detail="PDF file not found on server")
    
    # Verificar que el PDF no esté vacío
    file_size = os.path.getsize(pdf_path)
    print(f"✅ PDF encontrado, tamaño: {file_size} bytes")
    
    if file_size == 0:
        print(f"❌ PDF está vacío: {pdf_path}")
        raise HTTPException(status_code=500, detail="PDF file is empty")
    
    # Información adicional para debug
    job_info = jobs[job_id]
    scientific_count = sum(1 for doc in job_info["documents"] if doc.get("type") == "scientific")
    general_count = len(job_info["documents"]) - scientific_count
    template_type = template_manager.determine_template_type(job_info["documents"])
    
    print(f"📊 Información del PDF a descargar:")
    print(f"   - Job ID: {job_id}")
    print(f"   - Documentos totales: {len(job_info['documents'])}")
    print(f"   - Científicos: {scientific_count}")
    print(f"   - Generales: {general_count}")
    print(f"   - Template usado: {template_type.upper()}")
    print(f"   - Tamaño archivo: {file_size} bytes")
    
    # Usar FileResponse con headers para descarga
    return FileResponse(
        pdf_path,
        media_type='application/pdf',
        filename=f"documento-consolidado-{job_id}.pdf",
        headers={
            "Content-Disposition": f"attachment; filename=documento-consolidado-{job_id}.pdf",
            "Access-Control-Allow-Origin": "*",
        }
    )

@router.get("/job-info/{job_id}")
async def get_job_info(job_id: str):
    """Endpoint adicional para obtener información detallada del job (debug)"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    documents = job.get("documents", [])
    
    scientific_count = sum(1 for doc in documents if doc.get("type") == "scientific")
    general_count = len(documents) - scientific_count
    template_type = template_manager.determine_template_type(documents)
    
    return {
        "job_id": job_id,
        "status": job["status"],
        "total_documents": len(documents),
        "scientific_documents": scientific_count,
        "general_documents": general_count,
        "template_type": template_type,
        "documents": [
            {
                "name": doc["name"],
                "type": doc["type"],
                "size": doc.get("size", "N/A")
            }
            for doc in documents
        ],
        "pdf_available": job.get("consolidated_pdf") is not None,
        "error": job.get("error")
    }

@router.get("/health")
async def health_check():
    """Endpoint de health check"""
    return {
        "status": "healthy",
        "service": "DocuMind AI Backend",
        "version": "1.0.0",
        "features": {
            "template_system": "active",
            "document_processing": "active",
            "ai_analysis": "active"
        }
    }

@router.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str):
    """Manejar preflight requests para CORS"""
    return {"message": "OK"}