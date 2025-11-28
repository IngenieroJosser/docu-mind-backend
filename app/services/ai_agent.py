import os
from app.core.config import settings

try:
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_openai import ChatOpenAI
    from langchain_community.chat_models import ChatDatabricks
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

class AIAgent:
    def __init__(self):
        self.llm = self._initialize_llm()
        
    def _initialize_llm(self):
        """Inicializa el modelo de lenguaje"""
        if LANGCHAIN_AVAILABLE:
            return self._initialize_langchain_llm()
        else:
            return MockLLM()
    
    def _initialize_langchain_llm(self):
        """Inicializa con LangChain si está disponible"""
        try:
            if settings.OPENAI_API_KEY:
                return ChatOpenAI(
                    model_name=settings.LLM_MODEL,
                    openai_api_key=settings.OPENAI_API_KEY,
                    temperature=0.1
                )
            elif settings.DATABRICKS_HOST and settings.DATABRICKS_TOKEN:
                return ChatDatabricks(
                    target_uri=settings.DATABRICKS_HOST,
                    token=settings.DATABRICKS_TOKEN,
                    endpoint="databricks-llama-2-70b-chat"
                )
            else:
                return MockLLM()
        except Exception:
            return MockLLM()
    
    async def generate_summary(self, text: str, doc_type: str) -> str:
        """Genera un resumen del documento según su tipo"""
        try:
            if hasattr(self.llm, 'invoke'):
                # Usar LangChain
                return await self._generate_with_langchain(text, doc_type)
            else:
                # Usar mock
                return await self._generate_mock_summary(text, doc_type)
        except Exception as e:
            return f"Error generando resumen: {str(e)}"
    
    async def _generate_with_langchain(self, text: str, doc_type: str) -> str:
        """Genera resumen usando LangChain"""
        if doc_type == "scientific":
            system_prompt = """Eres un asistente académico especializado en resumir artículos científicos. 
            Genera un resumen estructurado que incluya:
            - Objetivo principal del estudio
            - Metodología utilizada  
            - Resultados clave
            - Conclusiones principales
            
            Mantén el resumen conciso pero informativo."""
        else:
            system_prompt = """Eres un asistente especializado en resumir documentos generales.
            Genera un resumen claro que incluya:
            - Puntos principales del documento
            - Información relevante
            - Conclusiones o recomendaciones
            
            Sé conciso pero cubre todos los aspectos importantes."""
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Por favor, resume el siguiente documento:\n\n{text[:6000]}")
        ]
        
        response = self.llm.invoke(messages)
        return response.content
    
    async def _generate_mock_summary(self, text: str, doc_type: str) -> str:
        """Genera resumen mock para desarrollo"""
        preview = text[:800] + "..." if len(text) > 800 else text
        
        if doc_type == "scientific":
            return f"""🔬 RESUMEN CIENTÍFICO (Mock)

Este es un resumen de ejemplo. Para resúmenes reales, configure su API key de OpenAI.

Contenido preview:
{preview}

[Configure OPENAI_API_KEY en .env para análisis con IA real]"""
        else:
            return f"""📄 RESUMEN GENERAL (Mock)

Este es un resumen de ejemplo. Para resúmenes reales, configure su API key de OpenAI.

Contenido preview:  
{preview}

[Configure OPENAI_API_KEY en .env para análisis con IA real]"""

    async def custom_analysis(self, documents_data: list, custom_prompt: str) -> str:
        """Realiza análisis personalizado"""
        if hasattr(self.llm, 'invoke'):
            return await self._custom_analysis_langchain(documents_data, custom_prompt)
        else:
            return await self._custom_analysis_mock(documents_data, custom_prompt)
    
    async def _custom_analysis_langchain(self, documents_data: list, custom_prompt: str) -> str:
        """Análisis personalizado con LangChain"""
        system_prompt = "Eres un analista de documentos experto. Analiza según las instrucciones del usuario."
        
        docs_text = "\n\n".join([
            f"Documento: {doc['name']}\nTipo: {doc['type']}\nContenido: {doc.get('content', '')[:1500]}..."
            for doc in documents_data
        ])
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Instrucciones: {custom_prompt}\n\nDocumentos:\n{docs_text}")
        ]
        
        response = self.llm.invoke(messages)
        return response.content
    
    async def _custom_analysis_mock(self, documents_data: list, custom_prompt: str) -> str:
        """Análisis personalizado mock"""
        return f"""🤖 ANÁLISIS PERSONALIZADO (Mock)

Solicitud: {custom_prompt}

Documentos analizados: {len(documents_data)}

Esta funcionalidad requiere configuración de API de IA.

Configure OPENAI_API_KEY en .env para habilitar análisis personalizado con IA real."""

class MockLLM:
    """LLM simulado para cuando no hay configuración de IA"""
    def invoke(self, messages):
        class MockResponse:
            @property
            def content(self):
                return "Resumen generado con LLM simulado. Configure OPENAI_API_KEY para análisis real."
        return MockResponse()