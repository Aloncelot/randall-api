"""
Respuestas sin IA (modo FAQ).
Se usan cuando no hay LLM_API_KEY o cuando el proveedor de IA falla, para que Randall nunca se quede mudo.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class Topic:
    keywords: tuple[str, ...]
    mood: str
    es: str
    en: str
    weight: float = 1.0  # temas prioritarios (ej. precios) ganan aunque coincidan menos palabras


TOPICS: tuple[Topic, ...] = (
    Topic(
        ("hola", "buenas", " hey ", "hello", " hi ", "saludos", "que tal"),
        "happy",
        "¡Hola! Soy Randall, el asistente de Quasar Devs. Puedo contarte de nuestros [servicios](#servicios), [proyectos](#proyectos) o cómo [cotizar](#contacto). ¿Qué te interesa?",
        "Hi! I'm Randall, Quasar Devs' assistant. I can tell you about our [services](#servicios), [projects](#proyectos) or how to [get a quote](#contacto). What are you interested in?",
    ),
    Topic(
        ("quien eres", "que eres", "randall", "who are you", "are you a bot", "eres un bot"),
        "wink",
        "Soy Randall, un pequeño robot pixelado y el asistente virtual de Quasar Devs. ¡También soy una muestra de los [chatbots con IA](#software) que construimos!",
        "I'm Randall, a little pixel robot and Quasar Devs' virtual assistant. I'm also a sample of the [AI chatbots](#software) we build!",
    ),
    Topic(
        ("precio", "costo", "cuanto", "cotiz", "contratar", "contratarlos", "hire", "presupuesto", "tarifa", "price", "cost", "quote", "budget", "how much", " rate "),
        "happy",
        "Cada proyecto se cotiza según su alcance: primero hacemos un diagnóstico y luego una propuesta con plan, tiempos y costo claros. Escríbenos en el [formulario de contacto](#contacto) y te respondemos con una propuesta inicial.",
        "Each project is quoted by scope: we start with an assessment, then send a proposal with a clear plan, timeline and cost. Write to us through the [contact form](#contacto) and we'll reply with an initial proposal.",
        weight=3.0,
    ),
    Topic(
        ("chatbot", "bot", " ia ", "inteligencia artificial", " rag ", "llm", "asistente", " ai ", "artificial intelligence", "assistant"),
        "happy",
        "Creamos chatbots e IA que responden con la información de tu empresa (RAG): atención a clientes, consulta de inventario y soporte interno, con Python y APIs de LLM. [Ver software](#software)",
        "We build AI chatbots that answer with your company's own information (RAG): customer service, inventory lookups and internal support, using Python and LLM APIs. [See software](#software)",
    ),
    Topic(
        ("wms", "gestion de almacen", "warehouse management", "licitacion", "tender", "bidding", "proveedor", "vendor",
         "montacarga", "forklift", "rack", "estanteria", "almacenamiento", "storage system", "mezzanine",
         "sorter", "conveyor", "banda", "transportador", "as/rs", "asrs", "shuttle", "equipo", "equipment"),
        "happy",
        "No vendemos WMS ni equipo: te acompañamos como asesores en la licitación de WMS, montacargas, sistemas de almacenamiento, sorters, conveyors, AS/RS y otros servicios logísticos. Definimos requerimientos, comparamos proveedores y damos seguimiento hasta la entrega y puesta en marcha. [Ver supply chain](#supply-chain)",
        "We don't sell WMS or equipment: we advise you through the tender for WMS, forklifts, storage systems, sorters, conveyors, AS/RS and other logistics services. We define requirements, compare vendors and follow up through delivery and go-live. [See supply chain](#supply-chain)",
        weight=2.0,
    ),
    Topic(
        ("automatiz", "robot", "automation", "automate", "robotics", "roi", "retorno"),
        "surprised",
        "Evaluamos si te conviene automatizar (AS/RS, shuttles, robótica) con análisis de retorno de inversión, y si decides hacerlo te acompañamos en la licitación hasta la puesta en marcha. [Ver supply chain](#supply-chain)",
        "We assess whether automation pays off for you (AS/RS, shuttles, robotics) with ROI analysis, and if you go ahead we support you from the tender through go-live. [See supply chain](#supply-chain)",
        weight=2.0,
    ),
    Topic(
        ("layout", "almacen", "bodega", "cedis", "cross dock", "crossdock", "warehouse", "distribution center"),
        "happy",
        "Diseñamos layouts de almacenes, bodegas, cross docks y CEDIS: capacidad, flujos, andenes, zonas de picking y crecimiento futuro, con entregables listos para decidir e invertir. [Ver supply chain](#supply-chain)",
        "We design warehouse, storage, cross dock and DC layouts: capacity, flows, docks, picking zones and future growth, with deliverables ready for decisions and investment. [See supply chain](#supply-chain)",
    ),
    Topic(
        ("supply", "cadena de suministro", "logistica", "logistics", "consultoria", "consulting", "proceso logistico", "kpi"),
        "happy",
        "En supply chain llevamos 8 años: layouts de almacén y CEDIS, optimización de procesos, dashboards y acompañamiento en licitaciones de WMS, montacargas, sistemas de almacenamiento y automatización hasta la puesta en marcha. [Ver supply chain](#supply-chain)",
        "8 years in supply chain: warehouse and DC layouts, process optimization, dashboards, and support in tenders for WMS, forklifts, storage systems and automation through go-live. [See supply chain](#supply-chain)",
    ),
    Topic(
        ("dashboard", "tablero", "analitica", "analytics", "excel", "sheets", "reporte"),
        "happy",
        "Hacemos dashboards de operación con tus propios datos (Excel, Google Sheets, SQL, Firebase) para decidir con información al día. [Ver servicios](#servicios)",
        "We build operations dashboards with your own data (Excel, Google Sheets, SQL, Firebase) so you decide with up-to-date information. [See services](#servicios)",
    ),
    Topic(
        (".net", "c#", "csharp", "dotnet"),
        "wink",
        "Sí cubrimos proyectos en C# / .NET junto con un equipo aliado de desarrolladores, así no tienes que buscar otro proveedor.",
        "Yes, we cover C# / .NET projects together with a partner team of developers, so you don't need another vendor.",
    ),
    Topic(
        ("pagina web", "sitio", "landing", "frontend", "web", " app", "movil", "flutter", "react", "next", "website", "mobile"),
        "happy",
        "Hacemos sitios, landing pages, apps web y móviles rápidas y con diseño a medida (React, Next.js, TypeScript, Tailwind, Flutter). [Ver software](#software)",
        "We build fast, custom-designed websites, landing pages, web and mobile apps (React, Next.js, TypeScript, Tailwind, Flutter). [See software](#software)",
    ),
    Topic(
        ("backend", " api", "base de datos", "database", "integracion", "integration", "full stack", "fullstack", "sistema", "portal"),
        "happy",
        "Desarrollamos backend, APIs y aplicaciones full stack: paneles, portales de clientes y herramientas internas en la nube (Node.js, SQL, Supabase, Firestore, AWS, Azure, Google Cloud). [Ver software](#software)",
        "We build backends, APIs and full stack apps: dashboards, client portals and internal tools in the cloud (Node.js, SQL, Supabase, Firestore, AWS, Azure, Google Cloud). [See software](#software)",
    ),
    Topic(
        ("servicio", "que hacen", "que ofrecen", "service", "what do you do", "offer"),
        "happy",
        "Tenemos dos rutas:\n- [Software](#software): frontend, backend, full stack y chatbots con IA.\n- [Supply chain](#supply-chain): layouts de almacén y CEDIS, optimización de procesos y acompañamiento en licitaciones de WMS y equipo logístico.",
        "We have two tracks:\n- [Software](#software): frontend, backend, full stack and AI chatbots.\n- [Supply chain](#supply-chain): warehouse and DC layouts, process optimization and support in WMS and logistics equipment tenders.",
    ),
    Topic(
        ("proyecto", "portafolio", "portfolio", "project", "trabajos", "ejemplo", "example"),
        "surprised",
        "Algunos proyectos en órbita: Nutrición JV, Quasar Logistic (dashboards logísticos), VibeFit Store (e-commerce), Task Manager y Cost Estimator (próximamente). [Ver proyectos](#proyectos)",
        "Some projects in orbit: Nutrición JV, Quasar Logistic (logistics dashboards), VibeFit Store (e-commerce), Task Manager and Cost Estimator (coming soon). [See projects](#proyectos)",
    ),
    Topic(
        ("proceso", "como trabajan", "pasos", "metodologia", "process", "how do you work", "steps"),
        "happy",
        "Trabajamos en 4 pasos: 1) diagnóstico, 2) propuesta con plan, tiempos y costo, 3) implementación por etapas, 4) despegue y soporte. [Ver proceso](#proceso)",
        "We work in 4 steps: 1) assessment, 2) proposal with plan, timeline and cost, 3) staged implementation, 4) launch and support. [See process](#proceso)",
    ),
    Topic(
        ("alonso", "fundador", "quien esta", "experiencia", "founder", "experience", "behind"),
        "wink",
        "Detrás está Alonso Correa: 8 años en supply chain, 5 en desarrollo full stack y 1 en IA con RAG. Entiende el código y también el almacén donde se usa. [Sobre mí](#sobre-mi)",
        "Behind it is Alonso Correa: 8 years in supply chain, 5 in full stack development and 1 in AI with RAG. He understands both the code and the warehouse where it runs. [About](#sobre-mi)",
    ),
    Topic(
        ("contacto", "correo", "email", "mail", "linkedin", "github", "contact", "llamada", " call", "agendar"),
        "happy",
        "Escríbenos por el [formulario de contacto](#contacto) o a aloncelot@gmail.com. También estamos en LinkedIn y GitHub.",
        "Reach us through the [contact form](#contacto) or at aloncelot@gmail.com. We're also on LinkedIn and GitHub.",
    ),
    Topic(
        ("donde", "ubicacion", "ciudad", "mexico", "remoto", "where", "location", "remote"),
        "happy",
        "Estamos en la Ciudad de México y trabajamos con clientes en México y de forma remota, en español, inglés y alemán.",
        "We're based in Mexico City and work with clients in Mexico and remotely, in Spanish, English and German.",
    ),
    Topic(
        ("privacidad", "cookies", " datos ", "privacy", " data "),
        "idle",
        "El sitio solo guarda en tu navegador el idioma y el aviso; no usamos cookies de rastreo ni publicidad. Tus datos del formulario solo se usan para responderte.",
        "The site only stores your language and the notice in your browser; no tracking or ad cookies. Form data is only used to reply to you.",
    ),
    Topic(
        ("gracias", "thank", "genial", "excelente", "perfecto", "great", "awesome"),
        "wink",
        "¡Con gusto! Si quieres avanzar, cuéntanos tu proyecto en [contacto](#contacto). 🚀",
        "My pleasure! If you'd like to move forward, tell us about your project in [contact](#contacto). 🚀",
    ),
    Topic(
        ("adios", "bye", "hasta luego", "nos vemos", "see you"),
        "wink",
        "¡Hasta pronto! Aquí estaré flotando en la esquina si me necesitas.",
        "See you soon! I'll be floating in the corner if you need me.",
    ),
)

DEFAULT = {
    "es": "Mmm, eso no lo tengo en mis circuitos. Puedo contarte de [servicios](#servicios), [proyectos](#proyectos) o el [proceso](#proceso). Para algo específico, escríbenos en [contacto](#contacto).",
    "en": "Hmm, that's not in my circuits. I can tell you about [services](#servicios), [projects](#proyectos) or our [process](#proceso). For anything specific, write to us in [contact](#contacto).",
}


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " " + re.sub(r"[¿?¡!,;:()\"']", " ", text) + " "


def answer(question: str, lang: str) -> tuple[str, str]:
    """Devuelve (respuesta, ánimo) eligiendo el tema con más coincidencias."""
    text = _normalize(question)
    best: Topic | None = None
    best_score = 0.0
    for topic in TOPICS:
        score = sum(len(k) for k in topic.keywords if k in text) * topic.weight
        if score > best_score:
            best, best_score = topic, score
    if best is None:
        return DEFAULT[lang], "thinking"
    return (best.es if lang == "es" else best.en), best.mood
