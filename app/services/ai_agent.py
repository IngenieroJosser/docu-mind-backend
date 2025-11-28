import os
import asyncio
import aiohttp
import json
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class AIAgent:
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = settings.DEEPSEEK_BASE_URL
        self.model = settings.DEEPSEEK_MODEL
        self.max_tokens = settings.MAX_TOKENS
        self.timeout = settings.TIMEOUT
        
    async def generate_summary(self, text: str, doc_type: str) -> str:
        """Genera un resumen real del documento usando DeepSeek"""
        if not self.api_key:
            logger.warning("DeepSeek API key no configurada - usando resumen simulado")
            return await self._generate_fallback_summary(text, doc_type)
        
        try:
            # Limitar el texto para evitar exceder límites de tokens
            truncated_text = self._truncate_text(text, 4000)
            
            prompt = self._build_summary_prompt(truncated_text, doc_type)
            summary = await self._call_deepseek_api(prompt)
            
            logger.info(f"✅ Resumen generado con DeepSeek para tipo: {doc_type}")
            return summary
            
        except Exception as e:
            logger.error(f"❌ Error llamando a DeepSeek API: {str(e)}")
            # Fallback a resumen simulado
            return await self._generate_fallback_summary(text, doc_type)
    
    async def _call_deepseek_api(self, prompt: str) -> str:
        """Llama a la API de DeepSeek"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "Eres un asistente especializado en análisis y resumen de documentos. Proporciona resúmenes concisos, precisos y bien estructurados."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "max_tokens": self.max_tokens,
            "temperature": 0.3,
            "stream": False
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    return data["choices"][0]["message"]["content"].strip()
                else:
                    error_text = await response.text()
                    raise Exception(f"API Error {response.status}: {error_text}")
    
    def _build_summary_prompt(self, text: str, doc_type: str) -> str:
        """Construye el prompt para el resumen según el tipo de documento"""
        
        if doc_type == "scientific":
            return f"""Analiza el siguiente documento científico y genera un resumen estructurado que incluya:

1. OBJETIVO PRINCIPAL: ¿Cuál es la pregunta de investigación o hipótesis principal?
2. METODOLOGÍA: ¿Cómo se realizó la investigación?
3. RESULTADOS CLAVE: ¿Qué descubrieron los investigadores?
4. CONCLUSIONES: ¿Cuáles son las implicaciones principales?
5. CONTRIBUCIÓN: ¿Qué aporta este trabajo al campo de estudio?

Documento:
{text}

Proporciona un resumen conciso pero completo en español, usando terminología académica apropiada."""
        
        else:  # general
            return f"""Analiza el siguiente documento y genera un resumen ejecutivo que incluya:

1. PROPÓSITO PRINCIPAL: ¿Cuál es el objetivo del documento?
2. PUNTOS CLAVE: ¿Cuáles son las ideas o información más importante?
3. DATOS RELEVANTES: ¿Qué datos, estadísticas o información concreta se presentan?
4. CONCLUSIONES O RECOMENDACIONES: ¿Qué se concluye o recomienda?
5. APLICACIÓN PRÁCTICA: ¿Cómo puede usarse esta información?

Documento:
{text}

Proporciona un resumen claro y conciso en español, destacando la información más relevante."""
    
    def _truncate_text(self, text: str, max_chars: int) -> str:
        """Trunca el texto para no exceder límites de tokens"""
        if len(text) <= max_chars:
            return text
        
        # Truncar en un punto lógico (fin de párrafo)
        truncated = text[:max_chars]
        last_period = truncated.rfind('.')
        last_newline = truncated.rfind('\n')
        
        cutoff = max(last_period, last_newline)
        if cutoff > max_chars * 0.8:  # Solo cortar si encontramos un punto razonable
            return truncated[:cutoff + 1] + "\n\n[Documento truncado para el análisis...]"
        else:
            return truncated + "\n\n[Documento truncado para el análisis...]"
    
    async def _generate_fallback_summary(self, text: str, doc_type: str) -> str:
        """Genera un resumen de fallback cuando DeepSeek no está disponible"""
        await asyncio.sleep(0.1)  # Simular procesamiento
        
        # Extraer primeras líneas para contexto
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        preview = '\n'.join(lines[:8]) if len(lines) > 8 else text[:500]
        
        if doc_type == "scientific":
            return f"""RESUMEN CIENTÍFICO (ANÁLISIS AUTOMÁTICO)

CONTENIDO ANALIZADO:
El documento presenta características de investigación académica o científica.

INFORMACIÓN IDENTIFICADA:
{preview[:400]}...

ESTRUCTURA DETECTADA:
- Contenido especializado con terminología técnica
- Posible metodología de investigación
- Hallazgos o resultados presentados

RECOMENDACIÓN:
Configure DEEPSEEK_API_KEY en el archivo .env para obtener resúmenes completos con IA avanzada.

---
Resumen generado automáticamente - Para análisis completo configure API de DeepSeek"""
        
        else:
            return f"""RESUMEN GENERAL (ANÁLISIS AUTOMÁTICO)

CONTENIDO PRINCIPAL:
{preview[:600]}...

INFORMACIÓN RELEVANTE IDENTIFICADA:
- Documento de propósito general
- Datos y contenido procesable
- Estructura de documento estándar

SIGUIENTES PASOS:
Configure DEEPSEEK_API_KEY para habilitar análisis automático con inteligencia artificial avanzada.

---
Resumen generado automáticamente - Configure API para análisis con DeepSeek"""

    async def custom_analysis(self, documents_data: list, custom_prompt: str) -> str:
        """Realiza análisis personalizado usando DeepSeek"""
        if not self.api_key:
            return await self._generate_fallback_custom_analysis(documents_data, custom_prompt)
        
        try:
            # Preparar contexto de documentos
            context = self._build_custom_analysis_context(documents_data)
            prompt = self._build_custom_prompt(context, custom_prompt)
            
            analysis = await self._call_deepseek_api(prompt)
            logger.info("✅ Análisis personalizado generado con DeepSeek")
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Error en análisis personalizado: {str(e)}")
            return await self._generate_fallback_custom_analysis(documents_data, custom_prompt)
    
    def _build_custom_analysis_context(self, documents_data: list) -> str:
        """Construye el contexto para análisis personalizado"""
        context = f"Se han analizado {len(documents_data)} documentos:\n\n"
        
        for i, doc in enumerate(documents_data, 1):
            context += f"DOCUMENTO {i}:\n"
            context += f"- Nombre: {doc['name']}\n"
            context += f"- Tipo: {doc['type']}\n"
            context += f"- Tamaño: {doc.get('size', 'N/A')}\n"
            context += f"- Resumen: {doc.get('summary', 'No disponible')}\n\n"
        
        return context
    
    def _build_custom_prompt(self, context: str, custom_prompt: str) -> str:
        """Construye el prompt para análisis personalizado"""
        return f"""Basándote en el siguiente conjunto de documentos analizados, responde a la solicitud personalizada del usuario.

CONTEXTO DE DOCUMENTOS:
{context}

SOLICITUD DEL USUARIO:
"{custom_prompt}"

Por favor, proporciona un análisis detallado y específico que:
1. Se base directamente en el contenido de los documentos
2. Sea relevante para la solicitud del usuario
3. Incluya ejemplos concretos cuando sea posible
4. Mantenga un tono profesional y útil

Responde en español con un formato claro y bien estructurado."""
    
    async def _generate_fallback_custom_analysis(self, documents_data: list, custom_prompt: str) -> str:
        """Fallback para análisis personalizado"""
        doc_count = len(documents_data)
        scientific_count = sum(1 for doc in documents_data if doc.get('type') == 'scientific')
        general_count = doc_count - scientific_count
        
        return f"""ANÁLISIS PERSONALIZADO SOLICITADO

SU SOLICITUD:
"{custom_prompt}"

DOCUMENTOS ANALIZADOS:
- Total: {doc_count} documentos
- Científicos: {scientific_count}
- Generales: {general_count}

ANÁLISIS PRELIMINAR:
Basado en la clasificación automática, los documentos contienen información relevante para su solicitud.

RECOMENDACIÓN:
Para un análisis detallado y específico según su prompt, configure DEEPSEEK_API_KEY en el archivo .env

PROXIMOS PASOS:
1. Obtenga una API key de DeepSeek
2. Configúrela en el archivo .env
3. Vuelva a ejecutar el análisis

---
Análisis personalizado disponible con configuración de API de DeepSeek"""